#!/usr/bin/env python3

import argparse
import csv
import json
import math
import os

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ESTRUCTURAS = ("Lista", "ABB", "B+")
ESCENARIOS = ("aleatorio", "ordenado")
TXT_ESC = {"aleatorio": "IDs aleatorios", "ordenado": "IDs ordenados"}
COLORES = {"Lista": "#c0392b", "ABB": "#2e86c1", "B+": "#27ae60"}
MARCAS = {"Lista": "o", "ABB": "s", "B+": "^"}
ESTILO_ESC = {"aleatorio": "-", "ordenado": "--"}
MARCA_ESC = {"aleatorio": "o", "ordenado": "s"}

CAMPOS_NUMERICOS = ["tam_operacion", "n_ejecuciones", "media_s", "desv_std_s", "mediana_s", "min_s",
                    "max_s", "ic95_s", "n_atipicos", "media_sin_atipicos_s",
                    "desv_std_sin_atipicos_s", "media_us_por_op", "desv_std_us_por_op",
                    "ic95_us_por_op", "altura_media", "pasos_promedio"]

plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
                     "legend.fontsize": 9, "axes.grid": True, "grid.alpha": 0.3})


#lectura de datos
def cargar_resumen(ruta):
    filas = []
    with open(ruta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["N"] = int(r["N"])
            for campo in CAMPOS_NUMERICOS:
                r[campo] = float(r[campo]) if r[campo] != "" else float("nan")
            filas.append(r)
    return filas


def cargar_info(carpeta):
    ruta = os.path.join(carpeta, "entorno.json")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return {}


def serie(filas, escenario, estructura, operacion):
    return sorted((r for r in filas
                   if r["escenario"] == escenario and r["estructura"] == estructura
                   and r["operacion"] == operacion), key=lambda r: r["N"])


def col(s, campo):
    return np.array([r[campo] for r in s], dtype=float)


def err(s, campo):
    return np.nan_to_num(col(s, campo), nan=0.0)


def etiqueta(estructura, info, escenario=None):
    orden = info.get("argumentos_cli", {}).get("orden", "?")
    base = {"Lista": "Lista (búsqueda secuencial)",
            "ABB": "ABB (sin balanceo)",
            "B+": f"Árbol B+ (orden {orden})"}[estructura]
    return f"{base}, IDs {escenario}s" if escenario else base


def pie(info, extra=""):
    p = info.get("parametros", {})
    r = p.get("repeticiones", "R")
    m = p.get("busquedas")
    m_txt = f"{m:,}".replace(",", ".") if isinstance(m, int) else "M"
    texto = (f"Cada punto: media de R = {r} repeticiones; barras de error = IC 95 % de la media (t de Student). "
             f"Búsquedas por medición: M = {m_txt} (Lista y ABB con IDs ordenados usan menos; ver tam_operacion en resumen.csv).")
    return texto + (" " + extra if extra else "")


def guardar(fig, carpeta, nombre, info, extra=""):
    fig.text(0.5, 0.008, pie(info, extra), ha="center", va="bottom", fontsize=7.5, color="#444444", wrap=True)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    ruta = os.path.join(carpeta, nombre)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print("  ", ruta)


def formato_n(n):
    return f"{int(n):,}".replace(",", ".")


def ejes_n(ax, ns):
    ns = sorted({int(n) for n in ns})
    ax.set_xscale("log")
    ax.set_xticks(ns)
    ax.set_xticklabels([formato_n(n) for n in ns], rotation=45 if len(ns) > 5 else 0)
    ax.minorticks_off()
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())


def leyenda(ax):
    #curvas medidas
    handles, etiquetas = ax.get_legend_handles_labels()
    pares = sorted(zip(handles, etiquetas), key=lambda p: p[1].startswith(("Referencia", "Igual")))
    ax.legend([p[0] for p in pares], [p[1] for p in pares])


def referencia(ax, ns, n0, y0, tipo, texto):
    ns = np.asarray(ns, dtype=float)
    if tipo == "lineal":
        y = y0 * ns / n0
    elif tipo == "log":
        y = y0 * np.log(ns) / math.log(n0)
    else:
        y = y0 * (ns / n0) ** 2
    ax.plot(ns, y, color="#7f8c8d", linestyle=":", linewidth=1.4, label=texto)



#graficas
def grafica_busqueda(filas, escenario, info, carpeta):
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ancla = {}
    for est in ESTRUCTURAS:
        s = serie(filas, escenario, est, "buscar")
        if not s:
            continue
        ax.errorbar(col(s, "N"), col(s, "media_us_por_op"), yerr=err(s, "ic95_us_por_op"),
                    color=COLORES[est], marker=MARCAS[est], capsize=3, linewidth=1.8,
                    label=etiqueta(est, info))
        ancla[est] = (col(s, "N")[0], col(s, "media_us_por_op")[0])
    todos_n = sorted({r["N"] for r in filas})
    if "Lista" in ancla:
        referencia(ax, todos_n, *ancla["Lista"], "lineal", "Referencia O(N) (escalada al menor N de la Lista)")
    if "B+" in ancla:
        referencia(ax, todos_n, *ancla["B+"], "log", "Referencia O(log N) (escalada al menor N del B+)")
    ejes_n(ax, todos_n)
    ax.set_yscale("log")
    ax.set_xlabel("Tamaño de entrada N (número de estudiantes)")
    ax.set_ylabel("Tiempo por búsqueda (µs)")
    ax.set_title(f"Tiempo de búsqueda por ID vs N — {TXT_ESC[escenario]}")
    leyenda(ax)
    guardar(fig, carpeta, f"busqueda_{escenario}.png", info)


def grafica_abb_orden(filas, info, carpeta):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6))
    for est in ("ABB", "B+"):
        for esc in ESCENARIOS:
            s = serie(filas, esc, est, "buscar")
            if not s:
                continue
            ax1.errorbar(col(s, "N"), col(s, "media_us_por_op"), yerr=err(s, "ic95_us_por_op"),
                         color=COLORES[est], linestyle=ESTILO_ESC[esc], marker=MARCA_ESC[esc],
                         capsize=3, label=etiqueta(est, info, esc))
            ax2.plot(col(s, "N"), col(s, "altura_media"), color=COLORES[est],
                     linestyle=ESTILO_ESC[esc], marker=MARCA_ESC[esc], label=etiqueta(est, info, esc))
    todos_n = np.array(sorted({r["N"] for r in filas}), dtype=float)
    ax2.plot(todos_n, np.log2(todos_n), color="#7f8c8d", linestyle=":", label="Referencia log₂(N)")
    ax2.plot(todos_n, todos_n, color="#bdc3c7", linestyle=":", label="Referencia N")
    for ax in (ax1, ax2):
        ejes_n(ax, todos_n)
        ax.set_yscale("log")
        ax.set_xlabel("Tamaño de entrada N (número de estudiantes)")
        leyenda(ax)
    ax1.set_ylabel("Tiempo por búsqueda (µs)")
    ax1.set_title("Tiempo de búsqueda: efecto del orden de inserción")
    ax2.set_ylabel("Altura del árbol (niveles)")
    ax2.set_title("Altura del árbol: efecto del orden de inserción")
    guardar(fig, carpeta, "abb_aleatorio_vs_ordenado.png", info)


def grafica_altura_vs_tiempo(filas, info, carpeta):
    fig, ax = plt.subplots(figsize=(8.5, 6))
    for est in ("ABB", "B+"):
        for esc in ESCENARIOS:
            s = serie(filas, esc, est, "buscar")
            if not s:
                continue
            x, y = col(s, "altura_media"), col(s, "media_us_por_op")
            ax.scatter(x, y, color=COLORES[est], marker=MARCA_ESC[esc], s=55,
                       label=etiqueta(est, info, esc), zorder=3)
            for r in s:
                ax.annotate(f"N={r['N']:,}".replace(",", "."), (r["altura_media"], r["media_us_por_op"]),
                            fontsize=6.5, xytext=(4, 3), textcoords="offset points", color="#555555")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Altura media del árbol (niveles)")
    ax.set_ylabel("Tiempo por búsqueda (µs)")
    ax.set_title("Relación entre la altura del árbol y el tiempo de búsqueda")
    ax.legend()
    guardar(fig, carpeta, "altura_vs_tiempo.png", info,
            "Cada punto es un tamaño N; las etiquetas indican N.")


def grafica_total(filas, operacion, titulo, ylabel, nombre, info, carpeta):
    fig, ejes = plt.subplots(1, 2, figsize=(13, 5.6), sharey=True)
    for ax, esc in zip(ejes, ESCENARIOS):
        for est in ESTRUCTURAS:
            s = serie(filas, esc, est, operacion)
            if not s:
                continue
            ax.errorbar(col(s, "N"), col(s, "media_s"), yerr=err(s, "ic95_s"), color=COLORES[est],
                        marker=MARCAS[est], capsize=3, linewidth=1.8, label=etiqueta(est, info))
        ejes_n(ax, [r["N"] for r in filas])
        ax.set_yscale("log")
        ax.set_xlabel("Tamaño de entrada N (número de estudiantes)")
        ax.set_title(TXT_ESC[esc])
        leyenda(ax)
    ejes[0].set_ylabel(ylabel)
    fig.suptitle(titulo, fontsize=13)
    guardar(fig, carpeta, nombre, info)


def grafica_aceleracion(filas, info, carpeta):
    fig, ejes = plt.subplots(1, 2, figsize=(13, 5.6), sharey=True)
    for ax, esc in zip(ejes, ESCENARIOS):
        base = {r["N"]: r["media_us_por_op"] for r in serie(filas, esc, "Lista", "buscar")}
        for est in ("ABB", "B+"):
            s = [r for r in serie(filas, esc, est, "buscar") if r["N"] in base]
            if not s:
                continue
            ax.plot(col(s, "N"), [base[r["N"]] / r["media_us_por_op"] for r in s], color=COLORES[est],
                    marker=MARCAS[est], linewidth=1.8, label=etiqueta(est, info))
        ax.axhline(1.0, color="#7f8c8d", linestyle=":", label="Igual de rápido que la Lista (=1)")
        ejes_n(ax, [r["N"] for r in filas])
        ax.set_yscale("log")
        ax.set_xlabel("Tamaño de entrada N (número de estudiantes)")
        ax.set_title(TXT_ESC[esc])
        leyenda(ax)
    ejes[0].set_ylabel("Aceleración respecto a la Lista (veces; >1 = más rápido)")
    fig.suptitle("¿Desde qué N se notan las diferencias? Tiempo por búsqueda de la Lista ÷ tiempo de la estructura",
                 fontsize=12)
    guardar(fig, carpeta, "aceleracion_vs_lista.png", info)



def referencia_teorica(operacion, estructura, escenario):
    t = {
        ("buscar", "Lista"): "1 (O(N))",
        ("buscar", "ABB", "aleatorio"): "cercano a 0 (O(log N))",
        ("buscar", "ABB", "ordenado"): "1 (O(N))",
        ("buscar", "B+"): "cercano a 0 (O(log N))",
        ("insertar", "Lista"): "1 (N appends: O(N) total)",
        ("insertar", "ABB", "aleatorio"): "un poco mayor que 1 (O(N log N))",
        ("insertar", "ABB", "ordenado"): "2 (O(N^2))",
        ("insertar", "B+"): "un poco mayor que 1 (O(N log N))",
        ("listar", "Lista", "aleatorio"): "un poco mayor que 1 (ordenar: O(N log N))",
        ("listar", "Lista", "ordenado"): "1 (Timsort sobre datos ya ordenados)",
        ("listar", "ABB"): "1 (O(N))",
        ("listar", "B+"): "1 (O(N))",
    }
    return t.get((operacion, estructura, escenario)) or t.get((operacion, estructura), "")


def tabla_comparativa(filas, carpeta):
    ruta = os.path.join(carpeta, "comparativa.csv")
    campos = ["escenario", "estructura", "operacion", "metrica", "n_puntos", "N_min", "N_max",
              "pendiente_empirica", "r2", "pendiente_teorica_aprox"]
    salida = []
    for esc in ESCENARIOS:
        for est in ESTRUCTURAS:
            for op in ("buscar", "insertar", "listar"):
                s = serie(filas, esc, est, op)
                if len(s) < 3:
                    continue
                x = np.log10(col(s, "N"))
                campo, metrica = (("media_us_por_op", "µs por búsqueda") if op == "buscar"
                                  else ("media_s", "s totales de la operación"))
                y = np.log10(col(s, campo))
                pendiente, intercepto = np.polyfit(x, y, 1)
                residuo = y - (pendiente * x + intercepto)
                ss_tot = float(np.sum((y - y.mean()) ** 2))
                r2 = 1 - float(np.sum(residuo ** 2)) / ss_tot if ss_tot > 0 else float("nan")
                salida.append({"escenario": esc, "estructura": est, "operacion": op, "metrica": metrica,
                               "n_puntos": len(s), "N_min": int(s[0]["N"]), "N_max": int(s[-1]["N"]),
                               "pendiente_empirica": round(float(pendiente), 3), "r2": round(r2, 4),
                               "pendiente_teorica_aprox": referencia_teorica(op, est, esc)})
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(salida)
    print("\nPendientes log-log (exponente empírico: tiempo ~ N^pendiente)")
    print(f"{'escenario':10s} {'estructura':10s} {'operación':9s} {'pendiente':>9s} {'R²':>7s}  teórica aprox.")
    for r in salida:
        print(f"{r['escenario']:10s} {r['estructura']:10s} {r['operacion']:9s} "
              f"{r['pendiente_empirica']:9.3f} {r['r2']:7.4f}  {r['pendiente_teorica_aprox']}")
    print("   ", ruta)


def main():
    p = argparse.ArgumentParser(description="Gráficas del Laboratorio 3")
    p.add_argument("--entrada", default="resultados", help="carpeta con resumen.csv y entorno.json")
    p.add_argument("--salida", default="graficas", help="carpeta donde guardar los PNG")
    args = p.parse_args()

    filas = cargar_resumen(os.path.join(args.entrada, "resumen.csv"))
    info = cargar_info(args.entrada)
    os.makedirs(args.salida, exist_ok=True)

    print("Generando gráficas:")
    for esc in ESCENARIOS:
        grafica_busqueda(filas, esc, info, args.salida)
    grafica_abb_orden(filas, info, args.salida)
    grafica_altura_vs_tiempo(filas, info, args.salida)
    grafica_total(filas, "insertar", "Tiempo total de construir la estructura insertando N estudiantes",
                  "Tiempo total de inserción de N estudiantes (s)", "insercion.png", info, args.salida)
    grafica_total(filas, "listar", "Tiempo de listar todos los estudiantes en orden ascendente de ID",
                  "Tiempo de listado completo (s)", "listado.png", info, args.salida)
    grafica_aceleracion(filas, info, args.salida)
    tabla_comparativa(filas, args.salida)


if __name__ == "__main__":
    main()
