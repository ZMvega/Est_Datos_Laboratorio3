"""
Ejecutar:  python -m unittest -v test_estructuras

Antes de medir tiempos hay que demostrar que las tres implementaciones
responden lo mismo; si una estuviera mal, sus tiempos no significarian nada.
"""

import random
import unittest

from estructuras import (
    ArbolBMas,
    ArbolBinarioBusqueda,
    Estudiante,
    ListaEstudiantes,
)


def est(i):
    return Estudiante(i, f"Estudiante {i}", 20 + i % 10, round((i % 50) / 10, 1))


FABRICAS = {
    "Lista": ListaEstudiantes,
    "ABB": ArbolBinarioBusqueda,
    "B+ orden 3": lambda: ArbolBMas(orden=3),
    "B+ orden 4": lambda: ArbolBMas(orden=4),
    "B+ orden 5": lambda: ArbolBMas(orden=5),
    "B+ orden 64": lambda: ArbolBMas(orden=64),
}


def construir(fabrica, ids):
    estructura = fabrica()
    for i in ids:
        estructura.insertar(est(i))
    return estructura

#funcionalidades a cumplir
class PruebasComunes(unittest.TestCase):

    def test_estructura_vacia(self):
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = fabrica()
                self.assertEqual(len(e), 0)
                self.assertIsNone(e.buscar(5))
                self.assertEqual(e.listar(), [])

    def test_insertar_y_buscar_todos(self):
        rng = random.Random(1)
        ids = rng.sample(range(1, 5000), 1000)
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = construir(fabrica, ids)
                self.assertEqual(len(e), 1000)
                for i in ids:
                    self.assertEqual(e.buscar(i), est(i))

    def test_buscar_inexistente(self):
        ids = list(range(0, 2000, 2))  # solo pares
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = construir(fabrica, ids)
                for i in (-1, 1, 3, 1999, 2000, 10**9):
                    self.assertIsNone(e.buscar(i))

    def test_listar_ordenado_con_ids_aleatorios(self):
        rng = random.Random(2)
        ids = rng.sample(range(1, 100000), 2000)
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = construir(fabrica, ids)
                self.assertEqual([x.id for x in e.listar()], sorted(ids))

    def test_listar_ordenado_con_ids_ascendentes_y_descendentes(self):
        for nombre, fabrica in FABRICAS.items():
            for etiqueta, ids in (("asc", range(500)), ("desc", range(499, -1, -1))):
                with self.subTest(f"{nombre} {etiqueta}"):
                    e = construir(fabrica, ids)
                    self.assertEqual([x.id for x in e.listar()], list(range(500)))

    def test_id_duplicado_en_arboles(self):
        for nombre, fabrica in FABRICAS.items():
            if nombre == "Lista":
                continue
            with self.subTest(nombre):
                e = construir(fabrica, [5, 3, 8])
                self.assertFalse(e.insertar(est(3)))
                self.assertEqual(len(e), 3)
                self.assertEqual(len(e.listar()), 3)

    def test_id_duplicado_en_lista_con_validacion(self):
        lista = ListaEstudiantes()
        self.assertTrue(lista.insertar(est(1), validar_duplicado=True))
        self.assertFalse(lista.insertar(est(1), validar_duplicado=True))
        self.assertEqual(len(lista), 1)

    def test_insertar_despues_de_construir(self):
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = construir(fabrica, range(0, 1000, 2))
                self.assertIsNone(e.buscar(501))
                e.insertar(est(501))
                self.assertEqual(e.buscar(501), est(501))
                ids = [x.id for x in e.listar()]
                self.assertEqual(ids, sorted(ids))
                self.assertIn(501, ids)

    def test_pasos_busqueda_positivo(self):
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = construir(fabrica, range(100))
                self.assertGreaterEqual(e.pasos_busqueda(50), 1)


class PruebasABB(unittest.TestCase):
    def test_altura_degenerada_con_ids_ordenados(self):
        e = construir(ArbolBinarioBusqueda, range(300))
        self.assertEqual(e.altura(), 300)

    def test_altura_logaritmica_con_ids_aleatorios(self):
        ids = random.Random(3).sample(range(1, 10**6), 1000)
        altura = construir(ArbolBinarioBusqueda, ids).altura()
        self.assertLess(altura, 50)  # log2(1000) ~ 10; un ABB aleatorio tipico ronda 20-25

    def test_no_usa_recursion(self):
        e = construir(ArbolBinarioBusqueda, range(3000))
        self.assertEqual(e.buscar(2999), est(2999))
        self.assertEqual(len(e.listar()), 3000)
        self.assertEqual(e.altura(), 3000)

    def test_pasos_en_arbol_degenerado(self):
        e = construir(ArbolBinarioBusqueda, range(100))
        self.assertEqual(e.pasos_busqueda(0), 1)
        self.assertEqual(e.pasos_busqueda(99), 100)


class PruebasListaPasos(unittest.TestCase):
    def test_pasos_lista(self):
        e = construir(ListaEstudiantes, range(100))
        self.assertEqual(e.pasos_busqueda(0), 1)
        self.assertEqual(e.pasos_busqueda(99), 100)
        self.assertEqual(e.pasos_busqueda(1000), 100)  # inexistente: recorre todo


class PruebasBMas(unittest.TestCase):
    def verificar_invariantes(self, arbol):
        orden = arbol.orden
        max_claves = orden - 1
        min_hoja = orden // 2
        min_interno = (orden + 1) // 2 - 1
        niveles_hojas = set()

        def recorrer(nodo, nivel, inferior, superior, es_raiz):
            self.assertLessEqual(len(nodo.claves), max_claves)
            self.assertEqual(nodo.claves, sorted(nodo.claves))
            for c in nodo.claves:
                if inferior is not None:
                    self.assertGreaterEqual(c, inferior)
                if superior is not None:
                    self.assertLess(c, superior)
            if nodo.hoja:
                niveles_hojas.add(nivel)
                self.assertEqual(len(nodo.claves), len(nodo.valores))
                if not es_raiz:
                    self.assertGreaterEqual(len(nodo.claves), min_hoja)
            else:
                self.assertEqual(len(nodo.hijos), len(nodo.claves) + 1)
                if not es_raiz:
                    self.assertGreaterEqual(len(nodo.claves), min_interno)
                limites = [inferior] + nodo.claves + [superior]
                for k, hijo in enumerate(nodo.hijos):
                    recorrer(hijo, nivel + 1, limites[k], limites[k + 1], False)

        recorrer(arbol._raiz, 1, None, None, True)
        self.assertEqual(len(niveles_hojas), 1, "todas las hojas deben estar al mismo nivel")

        hoja, previa, total = arbol._primera_hoja, None, 0
        while hoja is not None:
            for c in hoja.claves:
                if previa is not None:
                    self.assertGreater(c, previa)
                previa = c
                total += 1
            hoja = hoja.siguiente
        self.assertEqual(total, len(arbol))

    def test_invariantes_con_distintos_ordenes_y_secuencias(self):
        rng = random.Random(4)
        for orden in (3, 4, 5, 6, 7, 16, 64):
            secuencias = {
                "aleatoria": rng.sample(range(1, 20000), 1500),
                "ascendente": list(range(1500)),
                "descendente": list(range(1499, -1, -1)),
            }
            for etiqueta, ids in secuencias.items():
                with self.subTest(f"orden={orden} {etiqueta}"):
                    arbol = ArbolBMas(orden=orden)
                    for i in ids:
                        arbol.insertar(est(i))
                    self.verificar_invariantes(arbol)

    def test_altura_pequena(self):
        arbol = construir(lambda: ArbolBMas(orden=64), random.Random(5).sample(range(1, 10**6), 10000))
        self.assertLessEqual(arbol.altura(), 4)

    def test_altura_no_depende_del_orden_de_insercion(self):
        asc = construir(lambda: ArbolBMas(orden=16), range(5000))
        rnd = construir(lambda: ArbolBMas(orden=16), random.Random(6).sample(range(5000), 5000))
        self.assertLessEqual(abs(asc.altura() - rnd.altura()), 1)

    def test_orden_invalido(self):
        with self.assertRaises(ValueError):
            ArbolBMas(orden=2)

    def test_pasos_igual_a_altura(self):
        arbol = construir(lambda: ArbolBMas(orden=8), range(1000))
        self.assertEqual(arbol.pasos_busqueda(500), arbol.altura())


class PruebaContraReferencia(unittest.TestCase):

    def test_mezcla_aleatoria(self):
        rng = random.Random(7)
        for nombre, fabrica in FABRICAS.items():
            with self.subTest(nombre):
                e = fabrica()
                referencia = {}
                for _ in range(1500):
                    i = rng.randint(1, 600)
                    if i not in referencia:
                        self.assertTrue(e.insertar(est(i)) if nombre != "Lista"
                                        else e.insertar(est(i), validar_duplicado=True))
                        referencia[i] = est(i)
                    else:
                        resultado = (e.insertar(est(i)) if nombre != "Lista"
                                     else e.insertar(est(i), validar_duplicado=True))
                        self.assertFalse(resultado)
                for i in range(0, 700):
                    self.assertEqual(e.buscar(i), referencia.get(i))
                self.assertEqual([x.id for x in e.listar()], sorted(referencia))


if __name__ == "__main__":
    unittest.main(verbosity=2)
