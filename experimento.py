#!/usr/bin/env python3

import argparse
import csv
import gc
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from datetime import datetime

from estructuras import ArbolBMas, ArbolBinarioBusqueda, Estudiante, ListaEstudiantes

# Configuracion
PERFILES = {
    #comprobar que el pipeline funciona
    "rapido": dict(
        tamanos=[200, 1_000, 5_000],
        repeticiones=3,
        busquedas=1_000,
        n_max_abb_ordenado=5_000,
    ),

    "completo": dict(
        tamanos=[1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000],
        repeticiones=10,
        busquedas=1_000_000,         # M grande: cada medicion dura del orden de 1 s, no solo overhead
        n_max_abb_ordenado=20_000,   # construir un ABB degenerado cuesta O(N^2)
    ),
}

ESCENARIOS = ("aleatorio", "ordenado")
ESTRUCTURAS = ("Lista", "ABB", "B+")
OPERACIONES = ("insertar", "buscar", "listar")

M_MIN_LINEAL = 50

NOMBRES = ["Ana", "Carlos", "María", "Luis", "Sofía", "Juan", "Valentina", "Andrés",
           "Camila", "Daniel", "Laura", "Mateo", "Isabella", "Santiago", "Mariana",
           "Felipe", "Daniela", "Sebastián", "Paula", "Nicolás"]
APELLIDOS = ["Gómez", "Rodríguez", "Martínez", "López", "García", "Hernández", "Pérez",
             "Sánchez", "Ramírez", "Torres", "Vargas", "Castro", "Ortiz", "Rojas", "Mejía"]

CAMPOS_CRUDO = ["escenario", "N", "estructura", "operacion", "repeticion", "semilla",
                "tam_operacion", "tiempo_s", "tiempo_us_por_op", "altura", "pasos_promedio"]

CAMPOS_RESUMEN = ["escenario", "N", "estructura", "operacion", "n_ejecuciones",
                  "tam_operacion", "media_s", "desv_std_s", "mediana_s", "min_s", "max_s",
                  "ic95_s", "n_atipicos", "media_sin_atipicos_s", "desv_std_sin_atipicos_s",
                  "media_us_por_op", "desv_std_us_por_op", "ic95_us_por_op",
                  "altura_media", "pasos_promedio"]


def fabricas(orden):
    return {
        "Lista": ListaEstudiantes,
        "ABB": ArbolBinarioBusqueda,
        "B+": lambda: ArbolBMas(orden=orden),
    }



#generando datos y de busquedas
def generar_estudiantes(n, rng, ordenado):

    espacio = 10 * n
    ids = rng.sample(range(1, espacio + 1), n)
    if ordenado:
        ids.sort()
    estudiantes = [
        Estudiante(i,
                   f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}",
                   rng.randint(16, 35),
                   round(rng.uniform(0.0, 5.0), 2))
        for i in ids
    ]
    return estudiantes, espacio


def generar_busquedas(estudiantes, espacio, m, frac_fallidas, rng):

    ids = [e.id for e in estudiantes]
    existentes = set(ids)
    n_fallidas = round(m * frac_fallidas)
    claves = rng.choices(ids, k=m - n_fallidas)
    while n_fallidas > 0:
        candidato = rng.randint(1, espacio)
        if candidato not in existentes:
            claves.append(candidato)
            n_fallidas -= 1
    rng.shuffle(claves)
    return claves


def es_costo_lineal(estructura, escenario):
    return estructura == "Lista" or (estructura == "ABB" and escenario == "ordenado")


def busquedas_efectivas(estructura, escenario, n, m, presupuesto_pasos):
    if es_costo_lineal(estructura, escenario):
        return min(m, max(M_MIN_LINEAL, presupuesto_pasos // n))
    return m


#medicion
def cronometrar(funcion, *args):
    gc.collect()
    gc.disable()
    try:
        inicio = time.perf_counter()
        resultado = funcion(*args)
        duracion = time.perf_counter() - inicio
    finally:
        gc.enable()
    return duracion, resultado


def _construir(fabrica, estudiantes):
    estructura = fabrica()
    insertar = estructura.insertar
    for estudiante in estudiantes:
        insertar(estudiante)
    return estructura


def _buscar_todos(estructura, claves):
    buscar = estructura.buscar
    for clave in claves:
        buscar(clave)


def _listar(estructura):
    return estructura.listar()


def verificar(estructura, estudiantes, por_id, claves):
    ids_esperados = sorted(por_id)
    listado = estructura.listar()
    if [e.id for e in listado] != ids_esperados:
        raise AssertionError(f"{estructura.nombre}: el listado no esta ordenado/completo")
    if len(estructura) != len(estudiantes):
        raise AssertionError(f"{estructura.nombre}: tamaño incorrecto")
    for clave in claves[:200]:
        if estructura.buscar(clave) != por_id.get(clave):
            raise AssertionError(f"{estructura.nombre}: busqueda incorrecta para {clave}")



#estadistica
#valores criticos t de Student (dos colas, 95%) para df = 1..30
_T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def t_critico_95(grados_libertad):
    if grados_libertad < 1:
        return float("nan")
    return _T95[grados_libertad - 1] if grados_libertad <= 30 else 1.96


def resumir(valores):

    n = len(valores)
    media = statistics.fmean(valores)
    desv = statistics.stdev(valores) if n > 1 else 0.0
    ic95 = t_critico_95(n - 1) * desv / math.sqrt(n) if n > 1 else float("nan")

    n_atipicos = 0
    sin_atipicos = valores
    if n >= 5:
        q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
        iqr = q3 - q1
        inf, sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        sin_atipicos = [v for v in valores if inf <= v <= sup]
        n_atipicos = n - len(sin_atipicos)

    return {
        "n_ejecuciones": n,
        "media_s": media,
        "desv_std_s": desv,
        "mediana_s": statistics.median(valores),
        "min_s": min(valores),
        "max_s": max(valores),
        "ic95_s": ic95,
        "n_atipicos": n_atipicos,
        "media_sin_atipicos_s": statistics.fmean(sin_atipicos),
        "desv_std_sin_atipicos_s": statistics.stdev(sin_atipicos) if len(sin_atipicos) > 1 else 0.0,
    }


def resumir_csv(ruta_crudo, ruta_resumen):
    grupos = {}
    with open(ruta_crudo, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            clave = (fila["escenario"], int(fila["N"]), fila["estructura"], fila["operacion"])
            g = grupos.setdefault(clave, {"t": [], "tam": int(fila["tam_operacion"]),
                                          "altura": [], "pasos": []})
            g["t"].append(float(fila["tiempo_s"]))
            if fila["altura"] != "":
                g["altura"].append(float(fila["altura"]))
            if fila["pasos_promedio"] != "":
                g["pasos"].append(float(fila["pasos_promedio"]))

    orden_esc = {e: i for i, e in enumerate(ESCENARIOS)}
    orden_est = {e: i for i, e in enumerate(ESTRUCTURAS)}
    orden_op = {o: i for i, o in enumerate(OPERACIONES)}
    claves_ordenadas = sorted(grupos, key=lambda k: (orden_esc[k[0]], k[1], orden_est[k[2]], orden_op[k[3]]))

    with open(ruta_resumen, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_RESUMEN)
        escritor.writeheader()
        for clave in claves_ordenadas:
            escenario, n, estructura, operacion = clave
            g = grupos[clave]
            fila = {"escenario": escenario, "N": n, "estructura": estructura,
                    "operacion": operacion, "tam_operacion": g["tam"]}
            fila.update(resumir(g["t"]))
            factor = 1e6 / g["tam"]   # segundos totales -> microsegundos por operacion
            fila["media_us_por_op"] = fila["media_s"] * factor
            fila["desv_std_us_por_op"] = fila["desv_std_s"] * factor
            fila["ic95_us_por_op"] = fila["ic95_s"] * factor
            fila["altura_media"] = statistics.fmean(g["altura"]) if g["altura"] else ""
            fila["pasos_promedio"] = statistics.fmean(g["pasos"]) if g["pasos"] else ""
            escritor.writerow(fila)
    return len(claves_ordenadas)



def modelo_cpu():
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for linea in f:
                if linea.lower().startswith("model name"):
                    return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "desconocido"


def memoria_total_gb():
    try:
        import psutil
        return round(psutil.virtual_memory().total / 1024 ** 3, 2)
    except Exception:
        pass
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("MemTotal"):
                    return round(int(linea.split()[1]) / 1024 ** 2, 2)
    except OSError:
        pass
    return None


def carga_sistema():
    try:
        return os.getloadavg()[0]
    except (AttributeError, OSError):
        return None


def en_colab():
    return "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ


def describir_entorno(args, parametros):
    return {
        "fecha_inicio": datetime.now().isoformat(timespec="seconds"),
        "sistema_operativo": platform.platform(),
        "arquitectura": platform.machine(),
        "cpu": modelo_cpu(),
        "nucleos_logicos": os.cpu_count(),
        "ram_total_gb": memoria_total_gb(),
        "python": sys.version.replace("\n", " "),
        "implementacion_python": platform.python_implementation(),
        "reloj": "time.perf_counter (tiempo de pared, monotono)",
        "recolector_basura_durante_medicion": "desactivado (gc.disable)",
        "ejecutado_en_colab": en_colab(),
        "carga_sistema_inicio": carga_sistema(),
        "parametros": parametros,
        "argumentos_cli": vars(args),
    }


#ejecucion
def ejecutar(args, parametros):
    os.makedirs(args.salida, exist_ok=True)
    ruta_crudo = os.path.join(args.salida, "crudo.csv")
    ruta_resumen = os.path.join(args.salida, "resumen.csv")
    ruta_entorno = os.path.join(args.salida, "entorno.json")

    if en_colab():
        print("AVISO: se detecto Google Colab. Los entornos compartidos tienen "
              "variabilidad y recursos limitados; para el estudio use un equipo propio.\n")

    entorno = describir_entorno(args, parametros)
    fabrica_por_nombre = fabricas(args.orden)

    #prueba: carga modulos y llena caches
    rng_calentamiento = random.Random("calentamiento")
    est_cal, esp_cal = generar_estudiantes(500, rng_calentamiento, ordenado=False)
    cl_cal = generar_busquedas(est_cal, esp_cal, 200, 0.0, rng_calentamiento)
    for nombre in ESTRUCTURAS:
        s = _construir(fabrica_por_nombre[nombre], est_cal)
        _buscar_todos(s, cl_cal)
        _listar(s)

    inicio_total = time.perf_counter()
    with open(ruta_crudo, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_CRUDO)
        escritor.writeheader()

        for escenario in ESCENARIOS:
            for n in parametros["tamanos"]:
                activas = list(ESTRUCTURAS)
                if (escenario == "ordenado" and n > parametros["n_max_abb_ordenado"]):
                    activas.remove("ABB")
                    print(f"[{escenario} N={n:,}] ABB omitido: construir un ABB degenerado "
                          f"es O(N^2) (limite --n-max-abb-ordenado={parametros['n_max_abb_ordenado']:,})")

                m_ef = {s: busquedas_efectivas(s, escenario, n, parametros["busquedas"],
                                               args.presupuesto_pasos) for s in activas}

                for rep in range(parametros["repeticiones"]):
                    semilla = f"{args.semilla}-{escenario}-{n}-{rep}"
                    rng = random.Random(semilla)
                    estudiantes, espacio = generar_estudiantes(n, rng, escenario == "ordenado")
                    claves = generar_busquedas(estudiantes, espacio, parametros["busquedas"],
                                               args.frac_fallidas, rng)
                    por_id = {e.id: e for e in estudiantes}
                    orden_ejecucion = activas[:]
                    rng.shuffle(orden_ejecucion)

                    resumen_linea = []
                    for nombre in orden_ejecucion:
                        m = m_ef[nombre]
                        claves_m = claves[:m]

                        t_ins, estructura = cronometrar(_construir, fabrica_por_nombre[nombre], estudiantes)
                        t_bus, _ = cronometrar(_buscar_todos, estructura, claves_m)
                        t_lis, _ = cronometrar(_listar, estructura)

                        # Metricas deterministas, fuera del cronometro
                        altura = estructura.altura()
                        muestra = claves_m[:min(m, 1000)]
                        pasos = statistics.fmean(estructura.pasos_busqueda(c) for c in muestra)
                        if not args.sin_verificar:
                            verificar(estructura, estudiantes, por_id, claves_m)

                        base = {"escenario": escenario, "N": n, "estructura": nombre,
                                "repeticion": rep, "semilla": semilla,
                                "altura": "" if altura is None else altura,
                                "pasos_promedio": pasos}
                        for operacion, tam, t in (("insertar", n, t_ins), ("buscar", m, t_bus),
                                                  ("listar", n, t_lis)):
                            escritor.writerow({**base, "operacion": operacion, "tam_operacion": tam,
                                               "tiempo_s": t, "tiempo_us_por_op": t / tam * 1e6})
                        resumen_linea.append(f"{nombre}: {t_bus / m * 1e6:9.2f} us/busq")
                        del estructura
                    archivo.flush()
                    print(f"[{escenario:9s} N={n:>7,} rep {rep + 1:>2}/{parametros['repeticiones']}] "
                          + " | ".join(resumen_linea))

    entorno["duracion_total_s"] = round(time.perf_counter() - inicio_total, 1)
    entorno["carga_sistema_fin"] = carga_sistema()
    entorno["busquedas_por_medicion"] = {
        f"{esc}/{n}/{s}": busquedas_efectivas(s, esc, n, parametros["busquedas"], args.presupuesto_pasos)
        for esc in ESCENARIOS for n in parametros["tamanos"] for s in ESTRUCTURAS
        if not (esc == "ordenado" and s == "ABB" and n > parametros["n_max_abb_ordenado"])
    }
    with open(ruta_entorno, "w", encoding="utf-8") as f:
        json.dump(entorno, f, indent=2, ensure_ascii=False)

    n_grupos = resumir_csv(ruta_crudo, ruta_resumen)
    print(f"\nListo en {entorno['duracion_total_s']} s. {n_grupos} grupos resumidos.")
    print(f"  {ruta_crudo}\n  {ruta_resumen}\n  {ruta_entorno}")


def construir_parser():
    p = argparse.ArgumentParser(description="Experimento del Laboratorio 3 (Lista vs ABB vs B+)")
    p.add_argument("--perfil", choices=PERFILES, default="completo")
    p.add_argument("--tamanos", type=int, nargs="+", help="valores de N (reemplaza al perfil)")
    p.add_argument("--repeticiones", type=int, help="R, repeticiones por configuracion")
    p.add_argument("--busquedas", type=int, help="M, busquedas aleatorias por medicion")
    p.add_argument("--n-max-abb-ordenado", type=int, help="N maximo para el ABB con IDs ordenados")
    p.add_argument("--orden", type=int, default=64, help="orden del arbol B+ (por defecto 64)")
    p.add_argument("--frac-fallidas", type=float, default=0.0,
                   help="fraccion de busquedas de IDs inexistentes (0 = todas exitosas)")
    p.add_argument("--presupuesto-pasos", type=int, default=50_000_000,
                   help="tope aproximado de pasos por medicion de busqueda en estructuras de costo lineal")
    p.add_argument("--semilla", default="lab3", help="semilla base (reproducibilidad)")
    p.add_argument("--salida", default="resultados", help="carpeta de salida")
    p.add_argument("--sin-verificar", action="store_true", help="omite la verificacion de correctitud")
    p.add_argument("--solo-resumen", action="store_true",
                   help="no mide: re-calcula resumen.csv a partir de crudo.csv existente")
    return p


def main():
    args = construir_parser().parse_args()
    if args.solo_resumen:
        n = resumir_csv(os.path.join(args.salida, "crudo.csv"), os.path.join(args.salida, "resumen.csv"))
        print(f"resumen.csv regenerado ({n} grupos)")
        return

    parametros = dict(PERFILES[args.perfil])
    for nombre_cli, clave in (("tamanos", "tamanos"), ("repeticiones", "repeticiones"),
                              ("busquedas", "busquedas"),
                              ("n_max_abb_ordenado", "n_max_abb_ordenado")):
        valor = getattr(args, nombre_cli)
        if valor is not None:
            parametros[clave] = valor
    parametros["perfil"] = args.perfil
    ejecutar(args, parametros)


if __name__ == "__main__":
    main()
