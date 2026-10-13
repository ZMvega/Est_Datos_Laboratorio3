#LABORATORIO 3

from bisect import bisect_left, bisect_right
from operator import attrgetter
from typing import List, NamedTuple, Optional


class Estudiante(NamedTuple):
    id: int
    nombre: str
    edad: int
    promedio: float


_clave_id = attrgetter("id")


#LISTA
class ListaEstudiantes:

    nombre = "Lista"

    def __init__(self):
        self._datos: List[Estudiante] = []

    def __len__(self):
        return len(self._datos)

    def insertar(self, estudiante: Estudiante, validar_duplicado: bool = False) -> bool:
        if validar_duplicado and self.buscar(estudiante.id) is not None:
            return False
        self._datos.append(estudiante)
        return True

    def buscar(self, id_: int) -> Optional[Estudiante]:
        for estudiante in self._datos:
            if estudiante.id == id_:
                return estudiante
        return None

    def listar(self) -> List[Estudiante]:
        return sorted(self._datos, key=_clave_id)

    def altura(self):
        return None

    def pasos_busqueda(self, id_: int) -> int:
        """Elementos examinados hasta encontrar `id_` (o agotar la lista)."""
        pasos = 0
        for estudiante in self._datos:
            pasos += 1
            if estudiante.id == id_:
                break
        return pasos



#ARBOL BINARIO DE BUSQUEDA (ABB)
class _NodoABB:
    __slots__ = ("clave", "valor", "izq", "der")

    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None


class ArbolBinarioBusqueda:

    nombre = "ABB"

    def __init__(self):
        self._raiz: Optional[_NodoABB] = None
        self._n = 0

    def __len__(self):
        return self._n

    def insertar(self, estudiante: Estudiante) -> bool:
        clave = estudiante.id
        if self._raiz is None:
            self._raiz = _NodoABB(clave, estudiante)
            self._n = 1
            return True

        actual = self._raiz
        while True:
            if clave < actual.clave:
                if actual.izq is None:
                    actual.izq = _NodoABB(clave, estudiante)
                    break
                actual = actual.izq
            elif clave > actual.clave:
                if actual.der is None:
                    actual.der = _NodoABB(clave, estudiante)
                    break
                actual = actual.der
            else:
                return False  # ID repetido
        self._n += 1
        return True

    def buscar(self, id_: int) -> Optional[Estudiante]:
        actual = self._raiz
        while actual is not None:
            clave = actual.clave
            if id_ < clave:
                actual = actual.izq
            elif id_ > clave:
                actual = actual.der
            else:
                return actual.valor
        return None

    def listar(self) -> List[Estudiante]:

        resultado = []
        pila = []
        actual = self._raiz
        while pila or actual is not None:
            while actual is not None:
                pila.append(actual)
                actual = actual.izq
            actual = pila.pop()
            resultado.append(actual.valor)
            actual = actual.der
        return resultado

    def altura(self) -> int:
        if self._raiz is None:
            return 0
        maxima = 0
        pila = [(self._raiz, 1)]
        while pila:
            nodo, nivel = pila.pop()
            if nivel > maxima:
                maxima = nivel
            if nodo.izq is not None:
                pila.append((nodo.izq, nivel + 1))
            if nodo.der is not None:
                pila.append((nodo.der, nivel + 1))
        return maxima

    def pasos_busqueda(self, id_: int) -> int:

        pasos = 0
        actual = self._raiz
        while actual is not None:
            pasos += 1
            clave = actual.clave
            if id_ < clave:
                actual = actual.izq
            elif id_ > clave:
                actual = actual.der
            else:
                break
        return pasos


#ARBOL B+
class _NodoBMas:
    __slots__ = ("hoja", "claves", "hijos", "valores", "siguiente")

    def __init__(self, hoja: bool):
        self.hoja = hoja
        self.claves = []

        #solo nodos internos
        self.hijos = None if hoja else []

        #solo hojas - datos reales
        self.valores = [] if hoja else None

        # solo hojas - lista enlazada
        self.siguiente = None


class ArbolBMas:

    nombre = "B+"

    def __init__(self, orden: int = 64):
        if orden < 3:
            raise ValueError("El orden minimo de un arbol B+ es 3")
        self.orden = orden
        self._max_claves = orden - 1
        self._raiz: Optional[_NodoBMas] = None
        self._primera_hoja: Optional[_NodoBMas] = None
        self._n = 0

    def __len__(self):
        return self._n

    def insertar(self, estudiante: Estudiante) -> bool:
        clave = estudiante.id

        if self._raiz is None:
            hoja = _NodoBMas(True)
            hoja.claves.append(clave)
            hoja.valores.append(estudiante)
            self._raiz = hoja
            self._primera_hoja = hoja
            self._n = 1
            return True

        #descender hasta la hoja guardando el camino
        camino = []
        nodo = self._raiz
        while not nodo.hoja:
            i = bisect_right(nodo.claves, clave)
            camino.append((nodo, i))
            nodo = nodo.hijos[i]

        #Insertar ordenadamente en la hoja
        i = bisect_left(nodo.claves, clave)
        if i < len(nodo.claves) and nodo.claves[i] == clave:
            return False  # ID repetido
        nodo.claves.insert(i, clave)
        nodo.valores.insert(i, estudiante)
        self._n += 1

        if len(nodo.claves) <= self._max_claves:
            return True

        #Dividir la hoja desbordada
        mitad = len(nodo.claves) // 2
        derecha = _NodoBMas(True)
        derecha.claves = nodo.claves[mitad:]
        derecha.valores = nodo.valores[mitad:]
        del nodo.claves[mitad:]
        del nodo.valores[mitad:]
        derecha.siguiente = nodo.siguiente
        nodo.siguiente = derecha

        separador = derecha.claves[0]
        hijo_izq, hijo_der = nodo, derecha

        #Propagar hacia arriba mientras los padres se desborden
        while camino:
            padre, idx = camino.pop()
            padre.claves.insert(idx, separador)
            padre.hijos.insert(idx + 1, hijo_der)
            if len(padre.claves) <= self._max_claves:
                return True

            mitad = len(padre.claves) // 2
            sube = padre.claves[mitad]
            nuevo = _NodoBMas(False)
            nuevo.claves = padre.claves[mitad + 1:]
            nuevo.hijos = padre.hijos[mitad + 1:]
            del padre.claves[mitad:]
            del padre.hijos[mitad + 1:]
            separador = sube
            hijo_izq, hijo_der = padre, nuevo

        #dividir la raiz
        raiz = _NodoBMas(False)
        raiz.claves = [separador]
        raiz.hijos = [hijo_izq, hijo_der]
        self._raiz = raiz
        return True

    def buscar(self, id_: int) -> Optional[Estudiante]:
        nodo = self._raiz
        if nodo is None:
            return None
        while not nodo.hoja:
            nodo = nodo.hijos[bisect_right(nodo.claves, id_)]
        i = bisect_left(nodo.claves, id_)
        if i < len(nodo.claves) and nodo.claves[i] == id_:
            return nodo.valores[i]
        return None

    def listar(self) -> List[Estudiante]:

        resultado = []
        hoja = self._primera_hoja
        while hoja is not None:
            resultado.extend(hoja.valores)
            hoja = hoja.siguiente
        return resultado

    def altura(self) -> int:
        nodo = self._raiz
        niveles = 0
        while nodo is not None:
            niveles += 1
            nodo = None if nodo.hoja else nodo.hijos[0]
        return niveles

    def pasos_busqueda(self, id_: int) -> int:
        return self.altura()
