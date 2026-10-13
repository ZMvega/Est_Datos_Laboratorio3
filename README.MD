# Laboratorio 3: Sistema de búsqueda de estudiantes - Lista vs ABB vs B+

**Estudiante:** Zareth Mariana Vega Sanchez

**Curso:** Estructuras de Datos y Laboratorio

---

## 1. Objetivo y pregunta central

Estudiar de forma experimental cómo cambia el tiempo de ejecución de un sistema de búsqueda de estudiantes cuando cambian tres cosas:

1. **La estructura de datos** que lo sostiene: Lista, Árbol Binario de Búsqueda (ABB) y Árbol B+.
2. **El tamaño de los datos N** (número de estudiantes).
3. **El orden de inserción de los IDs**: aleatorio u ordenado.

El sistema debe permitir tres operaciones: buscar un estudiante por ID, insertar un estudiante nuevo y listar todos en orden ascendente de ID. Las conclusiones se sustentan en mediciones y en análisis estadístico, no solo en la complejidad teórica.

---

## 2. Contenido del repositorio

| Archivo o carpeta     | Qué contiene |
|-----------------------|---|
| `estructuras.py`      | El registro `Estudiante` y las tres estructuras (Lista, ABB, B+) con la misma interfaz. |
| `test_estructuras.py` | 20 pruebas unitarias de correctitud, incluidas las invariantes del árbol B+. |
| `experimento.py`      | Generación de datos y búsquedas, cronometraje y estadística. Produce `crudo.csv`, `resumen.csv` y `entorno.json`. |
| `graficas.py`         | Lee `resumen.csv` y produce las gráficas y la tabla `pendientes.csv`. |
| `resultados/`         | Salida real de `experimento.py` (se agrega tras correr el experimento). |
| `graficas/`           | PNG y `pendientes.csv` generados por `graficar.py`. Se versionan para no tener que repetir el experimento. |
| `README.md`           | Este documento. |
| `CODIGO_DE_HONOR.md`  | 1.3.1 MBA Honor Code MBA. (s. f.). Harvard Business School. https://www-hbs-edu.translate.goog/mba/handbook/standards-of-conduct/academic/honor-code?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=es&_x_tr_pto=tc&_x_tr_hist=true |

---

## 3. Cómo reproducir

**Requisitos:** Python 3.8 o superior. Para graficar: `matplotlib` y `numpy`. Opcional: `psutil` (solo sirve para registrar la RAM en Windows y macOS).

```bash
pip install matplotlib numpy psutil     # psutil es opcional

python -m unittest -v test_estructuras                   # 1) las estructuras son correctas
python experimento.py --perfil rapido --salida prueba    # 2) prueba piloto (segundos), NO se usa para las conclusiones
python experimento.py --perfil completo --salida resultados   # 3) el experimento real
python graficas.py --entrada resultados --salida graficas     # 4) gráficas
```

- En la corrida local, el perfil `completo` tardó **1247,8 s (unos 21 minutos)** y produjo **135 grupos** de resultados.
- Los datos son reproducibles (misma `--semilla` genera los mismos estudiantes y búsquedas), pero **los tiempos dependen de la máquina**: otra persona obtendrá valores distintos con las mismas tendencias.
- Para medir bien: cerrar otros programas, conectar el equipo a la corriente, no usar Google Colab (entorno compartido con variabilidad) y evitar que otros programas lean o escriban disco durante la corrida.

---

## 4. Entorno de ejecución del experimento

`experimento.py` registra todo esto automáticamente en `resultados/entorno.json`. Los siguientes valores son los obtenidos durante la ejecución y registrados en el archivo mencionado:

| Dato                        | Valor                                             |
|-----------------------------|---------------------------------------------------|
| Sistema operativo           | Windows-11-10.0.26200-SP0                         |
| CPU                         | AMD64 Family 25 Model 68 Stepping 1, AuthenticAMD |
| Núcleos lógicos             | 16                                                |
| RAM total (GB)              | 15.25                                             |
| Python                      | 3.14.5  [MINGW GCC UCRT 16.1.0 64 bit (AMD64)]    |
| Fecha de la corrida         | 2026-10-1                                         |
| Carga del sistema al inicio | 0                                                 |
| Duración total              | 1247,8 s                                          |

---

## 5. Metodología experimental

### 5.1 Variables

| Tipo | Variable | Valores |
|---|---|---|
| Independiente | Estructura | Lista, ABB, B+ |
| Independiente | Escenario (orden de inserción) | IDs aleatorios, IDs ordenados |
| Independiente | Tamaño de entrada N | 1.000, 2.000, 5.000, 10.000, 20.000, 50.000, 100.000, 200.000 |
| Dependiente | Tiempo de insertar N, de buscar M y de listar | Segundos (y µs por operación) |
| Dependiente | Altura del árbol y pasos por búsqueda | Niveles, nodos o elementos examinados |
| Controlada | Repeticiones R, búsquedas M, orden del B+, semilla, hardware | R = 10, M = 1.000.000, orden 64, semilla `lab3` |

### 5.2 Generación de los datos

- Cada estudiante tiene ID, nombre, edad (16 a 35) y promedio (0,00 a 5,00, escala nacional).
- Los IDs son únicos y se toman al azar del rango `[1, 10N]`. El rango es 10 veces mayor que N para que existan IDs inexistentes y no sean números consecutivos.
- En el escenario **ordenado** se usan exactamente la misma clase de IDs, pero ordenados de menor a mayor antes de insertarlos. **La única diferencia entre escenarios es el orden de inserción.**
- Cada repetición usa una semilla distinta (`lab3-<escenario>-<N>-<repetición>`), así que la desviación estándar incluye la variación entre conjuntos de datos.

### 5.3 Generación de las búsquedas

- Se generan M IDs al azar entre los IDs existentes (con reemplazo). Por defecto todas las búsquedas son exitosas (`--frac-fallidas 0`).
- **Las tres estructuras reciben los mismos datos y las mismas búsquedas** en cada repetición (diseño pareado).
- Si una búsqueda cuesta O(N) (Lista, y ABB con IDs ordenados), se reduce M con la regla `min(M, max(50, presupuesto // N))`, con un presupuesto de 50 millones de pasos. Sin esto, buscar 1.000.000 de veces en una lista de 200.000 elementos tardaría horas. **Por eso todas las gráficas comparan microsegundos por búsqueda y no el tiempo total.** El M realmente usado queda en `entorno.json` (`busquedas_por_medicion`) y en la columna `tam_operacion` de `resumen.csv`.

### 5.4 Medición

- Reloj: `time.perf_counter()` (tiempo de pared, monótono, de alta resolución).
- El recolector de basura se desactiva durante cada medición (`gc.disable`) y se fuerza una recolección justo antes (`gc.collect`), para que una pausa del recolector no contamine un tiempo.
- Se cronometran por separado: construir la estructura insertando los N estudiantes, hacer las M búsquedas y listar todo en orden.
- Antes de medir se hace un calentamiento corto que no se registra.
- El orden en que se ejecutan las tres estructuras dentro de cada repetición se baraja, para que ninguna se beneficie siempre de ejecutarse primero o último.
- Nada se escribe a disco mientras se cronometra: los resultados se guardan entre mediciones.
- Fuera del cronómetro se comprueba que cada estructura responde correctamente (listado ordenado y completo, y búsquedas contra un diccionario de referencia).

### 5.5 Estadística

Por cada grupo (escenario, N, estructura, operación) se calculan sobre las R = 10 repeticiones:

| Estadístico | Cómo se calcula | Por qué |
|---|---|---|
| Media | Promedio aritmético de los tiempos | Resumen central |
| Desviación estándar | Muestral (divide por n-1) | Las 10 repeticiones son una muestra, no toda la población |
| Mediana, mínimo, máximo | Directos | Mediana resiste valores extremos; min y max muestran el rango |
| IC 95 % de la media | `t(0,975; n-1) * s / raíz(n)` con t de Student | Con pocas repeticiones, t es más correcto que la normal |
| Valores atípicos | Regla de Tukey: fuera de `[Q1 - 1,5 IQR, Q3 + 1,5 IQR]` | Regla estándar, sin supuestos de distribución |
| Media sin atípicos | Media después de quitar los atípicos | Se reporta aparte para ver cuánto influyen |

**Los atípicos no se descartan de las estadísticas principales:** se cuentan (`n_atipicos`) y se reporta aparte la media sin ellos. Así no es posible decir que se maquillaron los datos.

Además, `graficar.py` calcula la **pendiente log-log** de cada curva (`pendientes.csv`): si el tiempo crece como `N^k`, la pendiente estimada es `k`. Sirve para comparar el escalamiento observado con el teórico.

### 5.6 Limitaciones del experimento

- **Python es interpretado.** Los tiempos absolutos no son los de C o Java, y las constantes (costo de cada paso del intérprete) pesan más. Las tendencias sí son comparables.
- **Una sola máquina y un solo sistema operativo.** No se controla la frecuencia de la CPU ni los procesos de segundo plano; por eso se repite 10 veces.
- **Ventaja de constante del B+:** dentro de cada nodo usa `bisect`, que corre en C, mientras el ABB compara en Python. Parte de la ventaja medida del B+ sobre el ABB es de implementación, no solo de algoritmo.
- **La lista busca con un bucle de Python** a propósito (no `list.index`, que corre en C), para que las tres estrategias paguen el mismo costo por paso. Una lista con `list.index` sería varias veces más rápida en términos absolutos, aunque con la misma pendiente.
- **El ABB con IDs ordenados solo se mide hasta N = 20.000.** Construirlo cuesta O(N²) (unos 200 millones de pasos por construcción con N = 20.000, repetidos 10 veces). Para N mayores el resultado se conoce por la teoría, pero no se midió.
- **El orden del B+ (64) no se optimizó.** Se eligió un valor razonable; `--orden` permite estudiar otros.
- **Solo se miden búsquedas exitosas** en la corrida principal. `--frac-fallidas` permite estudiar el caso con IDs inexistentes.
- **Algunas mediciones de búsqueda en árboles con N pequeño duran menos de 1 s.** Con M = 1.000.000 y N = 1.000, cada árbol hace un millón de búsquedas muy rápidas. Es un tiempo suficientemente grande frente a la resolución del reloj, pero menor que el rango ideal de 1 s a 5 min que sugiere la guía del curso.
- **La lista se ordena en `listar` sobre una copia.** Con IDs ya ordenados, el ordenamiento de Python (Timsort) detecta que los datos ya vienen ordenados y es mucho más rápido que con IDs aleatorios. Es un efecto real del algoritmo, no un error.

## 6. Resultados y análisis

> Todos los valores de esta sección salen de `resultados/resumen.csv` (135 grupos, cada uno con 10 repeticiones), `resultados/entorno.json` y `graficas/comparativa.csv`, medidos en el equipo de la sección 4 con el perfil `completo`. Las tablas se generaron directamente desde esos archivos. Los tiempos absolutos son de Python en ese equipo: lo que se compara son las **tendencias entre estructuras**, no los valores absolutos.

### 6.1 Gráficas generadas

| Archivo en `graficas/` | Qué muestra | Pregunta del enunciado que ayuda a responder |
|---|---|---|
| `busqueda_aleatorio.png` | Tiempo por búsqueda vs N con IDs aleatorios, con referencias O(N) y O(log N). | ¿Los resultados se comportan como predice la complejidad teórica? |
| `busqueda_ordenado.png` | Lo mismo con IDs ordenados. | ¿Qué ocurre cuando los datos se insertan ordenadamente? |
| `abb_aleatorio_vs_ordenado.png` | Tiempo de búsqueda y altura del ABB y del B+ en ambos escenarios. | ¿En qué situaciones el árbol binario deja de comportarse como O(log N)? ¿Qué diferencias aparecen entre los casos aleatorios y ordenados? |
| `altura_vs_tiempo.png` | Altura media del árbol vs tiempo por búsqueda. | ¿Qué relación existe entre la altura del árbol y el tiempo de búsqueda? |
| `insercion.png` | Tiempo total de construir la estructura. | Costo de la operación 2 (insertar) y efecto del orden. |
| `listado.png` | Tiempo de listar en orden ascendente. | Costo de la operación 3 (listar). |
| `aceleracion_vs_lista.png` | Cuántas veces más rápido que la Lista es cada árbol, según N. | ¿A partir de qué tamaño son visibles las diferencias? ¿Hay costos constantes que igualen algoritmos de distinta complejidad? |
| `comparativa.csv` | Exponente empírico (pendiente log-log) de cada curva frente al esperado. | ¿Los resultados se comportan como predice la complejidad teórica? (evidencia cuantitativa) |

### 6.2 Resultados medidos

**Tabla 1. Tiempo por búsqueda (µs), media de 10 repeticiones.** `--` significa que no se midió: el ABB con IDs ordenados solo llega a N = 20.000. Gráficas: `busqueda_aleatorio.png` y `busqueda_ordenado.png`.

| N | Lista, aleatorio | ABB, aleatorio | B+, aleatorio | Lista, ordenado | ABB, ordenado | B+, ordenado |
|---|---|---|---|---|---|---|
| 1.000 | 16,8 | 0,432 | 0,318 | 18,4 | 16,8 | 0,345 |
| 2.000 | 52,4 | 0,813 | 0,385 | 36,9 | 32,3 | 0,374 |
| 5.000 | 97,4 | 0,676 | 0,480 | 104,7 | 92,4 | 0,490 |
| 10.000 | 207,6 | 0,778 | 0,553 | 249,5 | 234,3 | 0,721 |
| 20.000 | 484,4 | 0,901 | 0,612 | 529,5 | 474,0 | 0,773 |
| 50.000 | 1.678 | 1,18 | 0,831 | 2.196 | -- | 0,965 |
| 100.000 | 7.488 | 1,72 | 1,19 | 6.308 | -- | 1,37 |
| 200.000 | 9.754 | 2,31 | 1,73 | 14.886 | -- | 1,74 |

**Tabla 2. Trabajo por búsqueda: pasos promedio / altura del árbol.** Un "paso" es un elemento examinado (Lista) o un nodo visitado (ABB y B+). La Lista no tiene altura.

| Serie (pasos / altura) | N = 1.000 | N = 20.000 | N = 200.000 |
|---|---|---|---|
| Lista, aleatorio | 500,8 | 10.045 | 99.275 |
| ABB, aleatorio | 11,9 / 22,0 | 17,9 / 34,5 | 22,6 / 43,7 |
| B+, aleatorio | 2,00 / 2,00 | 3,00 / 3,00 | 4,00 / 4,00 |
| Lista, ordenado | 502,3 | 10.054 | 100.518 |
| ABB, ordenado | 502,3 / 1.000 | 10.054 / 20.000 | -- |
| B+, ordenado | 2,00 / 2,00 | 3,00 / 3,00 | 4,00 / 4,00 |

**Tabla 3. Costo por paso (ns) = tiempo por búsqueda ÷ pasos promedio.**

| Serie (ns por paso) | N = 1.000 | N = 20.000 | N = 200.000 |
|---|---|---|---|
| Lista, aleatorio | 33,6 | 48,2 | 98,3 |
| ABB, aleatorio | 36,4 | 50,3 | 102,4 |
| B+, aleatorio | 158,9 | 204,0 | 432,2 |
| Lista, ordenado | 36,5 | 52,7 | 148,1 |
| ABB, ordenado | 33,5 | 47,1 | -- |
| B+, ordenado | 172,7 | 257,7 | 435,6 |

**Tabla 4. Tiempo total de insertar N estudiantes (ms).** Gráfica: `insercion.png`.

| N | Lista, aleatorio | ABB, aleatorio | B+, aleatorio | Lista, ordenado | ABB, ordenado | B+, ordenado |
|---|---|---|---|---|---|---|
| 1.000 | 0,103 | 0,607 | 0,783 | 0,155 | 19,4 | 0,596 |
| 2.000 | 0,187 | 1,76 | 1,92 | 0,191 | 71,2 | 1,32 |
| 5.000 | 0,415 | 4,31 | 4,45 | 0,443 | 493,7 | 3,52 |
| 10.000 | 0,829 | 9,97 | 9,38 | 0,902 | 2.437 | 8,90 |
| 20.000 | 1,57 | 22,7 | 20,6 | 1,55 | 9.924 | 15,8 |
| 50.000 | 3,84 | 65,2 | 55,0 | 4,17 | -- | 41,7 |
| 100.000 | 8,14 | 191,5 | 151,7 | 7,58 | -- | 85,2 |
| 200.000 | 16,6 | 531,8 | 344,3 | 15,3 | -- | 191,8 |

**Tabla 5. Tiempo de listar todos los estudiantes en orden ascendente (ms).** Gráfica: `listado.png`.

| N | Lista, aleatorio | ABB, aleatorio | B+, aleatorio | Lista, ordenado | ABB, ordenado | B+, ordenado |
|---|---|---|---|---|---|---|
| 1.000 | 0,161 | 0,135 | 0,031 | 0,087 | 0,146 | 0,038 |
| 2.000 | 0,373 | 0,256 | 0,044 | 0,112 | 0,226 | 0,045 |
| 5.000 | 1,09 | 0,552 | 0,080 | 0,236 | 0,582 | 0,093 |
| 10.000 | 2,02 | 1,35 | 0,131 | 1,06 | 1,13 | 0,151 |
| 20.000 | 4,29 | 2,85 | 0,278 | 1,72 | 2,04 | 0,235 |
| 50.000 | 15,5 | 9,18 | 0,780 | 5,87 | -- | 0,901 |
| 100.000 | 54,5 | 25,0 | 3,37 | 16,1 | -- | 2,03 |
| 200.000 | 94,7 | 57,0 | 8,13 | 35,8 | -- | 5,39 |

**Tabla 6. Aceleración de la búsqueda respecto a la Lista (veces; tiempo de la Lista ÷ tiempo de la estructura).** Gráfica: `aceleracion_vs_lista.png`.

| N | ABB, aleatorio | B+, aleatorio | ABB, ordenado | B+, ordenado |
|---|---|---|---|---|
| 1.000 | 39,0 | 53,0 | 1,09 | 53,1 |
| 2.000 | 64,5 | 136,2 | 1,14 | 98,6 |
| 5.000 | 144,1 | 203,2 | 1,13 | 213,7 |
| 10.000 | 267,0 | 375,2 | 1,06 | 346,0 |
| 20.000 | 537,7 | 791,5 | 1,12 | 684,8 |
| 50.000 | 1.419 | 2.019 | -- | 2.276 |
| 100.000 | 4.362 | 6.286 | -- | 4.598 |
| 200.000 | 4.220 | 5.643 | -- | 8.544 |

**Tabla 7. Razón ordenado ÷ aleatorio con N = 20.000** (el mayor N medido en ambos escenarios para las tres estructuras). Un valor mayor que 1 significa que con IDs ordenados tarda más.

| Estructura (N = 20.000) | Buscar (por búsqueda) | Insertar N | Listar |
|---|---|---|---|
| Lista | 1,09 | 0,988 | 0,401 |
| ABB | 526,1 | 437,9 | 0,717 |
| B+ | 1,26 | 0,766 | 0,847 |

**Tabla 8. Exponente empírico de cada curva (`comparativa.csv`).** Si el tiempo crece como `N^k`, la pendiente log-log es `k`. Se ajusta con los ocho tamaños (cinco en el ABB ordenado).

| Escenario | Estructura | Operación | Puntos | Pendiente medida | R² | Esperada (aproximada) |
|---|---|---|---|---|---|---|
| aleatorio | Lista | buscar | 8 | 1,224 | 0,985 | 1 (O(N)) |
| aleatorio | Lista | insertar N | 8 | 0,961 | 0,999 | 1 (N appends: O(N) total) |
| aleatorio | Lista | listar | 8 | 1,219 | 0,994 | un poco mayor que 1 (ordenar: O(N log N)) |
| aleatorio | ABB | buscar | 8 | 0,268 | 0,885 | cercano a 0 (O(log N)) |
| aleatorio | ABB | insertar N | 8 | 1,241 | 0,997 | un poco mayor que 1 (O(N log N)) |
| aleatorio | ABB | listar | 8 | 1,157 | 0,994 | 1 (O(N)) |
| aleatorio | B+ | buscar | 8 | 0,299 | 0,960 | cercano a 0 (O(log N)) |
| aleatorio | B+ | insertar N | 8 | 1,132 | 0,997 | un poco mayor que 1 (O(N log N)) |
| aleatorio | B+ | listar | 8 | 1,062 | 0,957 | 1 (O(N)) |
| ordenado | Lista | buscar | 8 | 1,284 | 0,996 | 1 (O(N)) |
| ordenado | Lista | insertar N | 8 | 0,900 | 0,993 | 1 (N appends: O(N) total) |
| ordenado | Lista | listar | 8 | 1,199 | 0,985 | 1 (Timsort sobre datos ya ordenados) |
| ordenado | ABB | buscar | 5 | 1,140 | 0,997 | 1 (O(N)) |
| ordenado | ABB | insertar N | 5 | 2,106 | 0,999 | 2 (O(N^2)) |
| ordenado | ABB | listar | 5 | 0,909 | 0,996 | 1 (O(N)) |
| ordenado | B+ | buscar | 8 | 0,310 | 0,983 | cercano a 0 (O(log N)) |
| ordenado | B+ | insertar N | 8 | 1,078 | 0,999 | un poco mayor que 1 (O(N log N)) |
| ordenado | B+ | listar | 8 | 0,949 | 0,964 | 1 (O(N)) |

**Cómo leer los exponentes.** Entre N = 1.000 y N = 200.000, una curva puramente logarítmica (log₂ N) tendría pendiente 0,107, y una de tipo N·log₂ N tendría 1,107. Por eso "cercano a 0" en la columna de lo esperado significa alrededor de 0,1, no exactamente 0.

**Tabla 9. Descomposición de la pendiente de la búsqueda.** El tiempo por búsqueda es (pasos) × (costo por paso), así que su pendiente log-log es la suma de las pendientes de ambos factores.

| Serie (búsqueda) | Pendiente del tiempo | = Pendiente de los pasos | + Pendiente del costo por paso |
|---|---|---|---|
| Lista, aleatorio | 1,224 | 1,001 | 0,223 |
| ABB, aleatorio | 0,268 | 0,123 | 0,145 |
| B+, aleatorio | 0,299 | 0,107 | 0,192 |
| Lista, ordenado | 1,284 | 1,000 | 0,284 |
| ABB, ordenado | 1,140 | 0,999 | 0,140 |
| B+, ordenado | 0,310 | 0,130 | 0,180 |

### 6.3 Respuestas a las preguntas del enunciado

**1. ¿Los resultados se comportan como predice la complejidad teórica?**

Sí en el trabajo que hace cada algoritmo, y solo parcialmente en el tiempo. Los **pasos** por búsqueda crecen con exponente 1,00 en la Lista y 1,00 en el ABB con IDs ordenados (O(N)), 0,107 en el B+ (idéntico al 0,107 que da log₂ N en este rango) y 0,123 en el ABB con IDs aleatorios (O(log N)). El **tiempo**, en cambio, crece más que los pasos: 1,22 y 1,28 en la Lista, 0,27 en el ABB aleatorio y 0,30 a 0,31 en el B+ (Tabla 9). La diferencia, entre 0,14 y 0,28, es exactamente el crecimiento del costo por paso (Tabla 3). Para la construcción, el ABB con IDs ordenados tiene exponente 2,106 (esperado 2), la Lista 0,96 y 0,90 (esperado 1), el B+ 1,13 y 1,08 y el ABB aleatorio 1,24 (esperado un poco más de 1) (Tabla 8). **La clase de complejidad se cumple; las desviaciones son de constante.**

*Nota sobre el ABB aleatorio:* su pendiente de búsqueda tiene el R² más bajo (0,886). La causa es el punto N = 2.000, donde dos repeticiones atípicas inflaron la media a 0,813 µs (0,531 µs sin ellas). Con las medias sin atípicos la pendiente pasa de 0,268 a 0,303 (R² 0,974), muy cercana a la del B+ (0,300).

**2. ¿En qué situaciones el árbol binario deja de comportarse como O(log N)?**

Cuando los IDs se insertan **ordenados**. El ABB se convierte en una lista enlazada: su altura es exactamente N (1.000, 2.000, ..., 20.000), cada búsqueda recorre en promedio N/2 nodos (502,3 con N = 1.000 y 10.054 con N = 20.000), el tiempo por búsqueda pasa de 16,8 µs a 474,0 µs y es prácticamente igual al de la Lista (aceleración de 1,1 en los cinco tamaños, Tabla 6). Con IDs aleatorios sí se mantiene logarítmico: la altura media pasa de 22,0 a 43,7 niveles y los pasos de 11,9 a 22,6 al ir de N = 1.000 a N = 200.000. No se midieron casos intermedios (datos parcialmente ordenados), que degradarían el árbol de forma parcial. Gráfica: `abb_aleatorio_vs_ordenado.png`.

**3. ¿Qué relación existe entre la altura del árbol y el tiempo de búsqueda?**

*Dentro de una misma estructura*, más altura significa más tiempo: en el ABB ordenado la altura se multiplica por 20 (de 1.000 a 20.000 niveles) y el tiempo por 28,2; en el ABB aleatorio la altura media se multiplica por 1,99 y el tiempo por 5,35. *Entre estructuras*, la altura sola no predice el tiempo: el B+ tiene entre 2 y 4 niveles y tarda 0,318 a 1,73 µs, mientras el ABB aleatorio tiene 22 a 44 niveles y tarda 0,432 a 2,31 µs: unas 10 veces menos niveles y solo ~1,4 veces menos tiempo. La razón es el **costo por nivel**: un paso del B+ cuesta 158,9 a 432,2 ns (hay una búsqueda binaria dentro de un nodo de hasta 63 claves) y uno del ABB 36,4 a 102,4 ns (Tabla 3). Además, la altura es el camino más largo; lo que realmente se recorre en promedio ("pasos") es aproximadamente la mitad en el ABB aleatorio (22,6 frente a 43,7 con N = 200.000). Gráfica: `altura_vs_tiempo.png`.

**4. ¿Qué ocurre cuando los datos se insertan ordenadamente?**

Depende de la estructura (Tabla 7):

- **ABB:** se degenera. Buscar pasa a O(N) y construir a O(N²): 9,92 s con N = 20.000 frente a 0,023 s con IDs aleatorios, es decir, 437,9 veces más. Por eso no se midió más allá de N = 20.000.
- **B+:** no se degrada en la búsqueda (0,345–1,74 µs frente a 0,318–1,73 µs) y construirlo es incluso más rápido (191,8 ms frente a 344,3 ms con N = 200.000; es coherente con que cada inserción cae en la última hoja, una zona de memoria recién usada). El costo es de espacio: con inserción ascendente las hojas quedan ocupadas al 51 % (frente a ~70 % con IDs aleatorios), así que con N = 100.000 el árbol ordenado tiene 4 niveles y el aleatorio 3 (Tabla 2 y comprobación abajo).
- **Lista:** insertar no cambia, y listar es 2,65 veces más rápido (35,8 ms frente a 94,7 ms con N = 200.000), porque el ordenamiento de Python aprovecha que los datos ya vienen ordenados.

*Comprobación estructural (reproducible, no depende de la máquina):* con orden 64 y N = 100.000, la inserción ascendente produce 3.125 hojas ocupadas al 51 % y 4 niveles; la aleatoria, unas 2.270 hojas al 70 % y 3 niveles.

```python
import random
from estructuras import ArbolBMas, Estudiante

def hojas(ids):
    t = ArbolBMas(orden=64)
    for i in ids:
        t.insertar(Estudiante(i, "x", 20, 3.0))
    n, total, h = 0, 0, t._primera_hoja
    while h:
        n += 1; total += len(h.claves); h = h.siguiente
    return t.altura(), n, round(total / n / 63 * 100)   # altura, hojas, % de ocupación

ids = random.Random(1).sample(range(1, 1_000_001), 100_000)
print("aleatorio:", hojas(ids))
print("ordenado: ", hojas(sorted(ids)))
```

**5. ¿Qué diferencias aparecen entre los casos aleatorios y ordenados?**

Resumidas en la Tabla 7 y en las gráficas de búsqueda, inserción y listado: el orden de inserción es decisivo para el ABB (búsqueda ~526,1 veces más lenta y construcción ~437,9 veces más lenta con N = 20.000), casi irrelevante para el B+ (razones entre 0,8 y 1,3) y relevante solo en el listado de la Lista (razón 0,401, por el ordenamiento adaptativo de Python).

**6. ¿A partir de qué tamaño de entrada comienzan a ser claramente visibles las diferencias?**
Desde el menor tamaño medido. Con IDs aleatorios y N = 1.000 la Lista ya es 39,0 veces más lenta que el ABB y 53,0 veces más lenta que el B+, y la brecha crece hasta ~4.200 y ~5.600 veces con N = 200.000 (Tabla 6). El ABB con IDs ordenados nunca se separa de la Lista (1,1 veces en todos los tamaños). Como no se midió ningún N menor que 1.000, **estos datos no muestran dónde se cruzan**. Extrapolando el costo por paso de N = 1.000 (33,6 ns) frente a los 0,318–0,432 µs de los árboles, el cruce estaría entre unos 19 y 26 elementos, pero esa cifra está fuera del rango medido y debe comprobarse (por ejemplo con `--tamanos 10 20 50 100 200 500`). Gráfica: `aceleracion_vs_lista.png`.

**7. ¿Existen costos constantes que hagan que dos algoritmos con distinta complejidad tengan tiempos similares con entradas pequeñas?**

Sí, y se ven en tres lugares:

1. **Construcción con IDs aleatorios:** el ABB y el B+ tardan casi lo mismo mientras N es pequeño. La razón ABB ÷ B+ (menor que 1 significa que el ABB construye más rápido) es 0,78 con N = 1.000, 0,97 con 5.000 y 1,10 con 20.000; solo con N = 200.000 el B+ gana con claridad (1,54).
2. **Búsqueda ABB aleatorio vs B+:** el B+ solo es entre 1,34 y 1,47 veces más rápido (sin contar N = 2.000, afectado por atípicos), aunque tiene unas 10 veces menos niveles, porque cada nivel del B+ cuesta 4 o 5 veces más que un paso del ABB.
3. **ABB ordenado y Lista:** son estructuras distintas pero tienen tiempos casi idénticos (Tabla 6), porque el ABB degenerado es una lista.

Además, el costo por paso de todas las estructuras **crece 3 o 4 veces** al pasar de N = 1.000 a N = 200.000 (Tabla 3), así que las constantes no son constantes: dependen de N.

### 6.4 Hallazgos principales

1. **La complejidad teórica se cumple en el trabajo realizado** (Tabla 9): pasos con pendiente 1,00 (Lista y ABB ordenado), 0,107 (B+) y 0,123 (ABB aleatorio).
2. **El tiempo crece más que el trabajo** porque el costo por paso aumenta 3 o 4 veces con N en todas las estructuras. Una hipótesis coherente con esto es el efecto de la jerarquía de memoria (a más datos, más fallos de caché), pero para asegurar esta afirmación haría falta medir con contadores de hardware o con una prueba controlada.
3. **Un ABB con IDs ordenados es una lista:** altura N, N/2 pasos por búsqueda, rendimiento igual al de la Lista (1,1 veces) y construcción O(N²) (pendiente medida 2,106; 9,92 s con N = 20.000).
4. **El B+ es el más robusto:** casi no cambia entre IDs aleatorios y ordenados. Su costo es de espacio (hojas al 51 % con inserción ascendente, a veces un nivel más).
5. **En memoria y en Python, la ventaja del B+ en búsqueda es modesta** (~1,4 veces frente al ABB aleatorio). Donde más gana es en listar (7,0 veces más rápido que el ABB y 11,7 veces más rápido que la Lista con N = 200.000). Su razón de ser, reducir los accesos a disco (2 a 4 niveles frente a 22 a 44), es una ventaja que en **este laboratorio en memoria no mide**.
6. **La Lista inserta mucho más rápido** (6 a 32 veces más rápido que los árboles con IDs aleatorios), pero buscar en ella es impracticable a gran escala: con N = 200.000 una sola búsqueda tarda 9,8 ms, frente a 1,7 µs en el B+.
7. **Con IDs ordenados, el ABB no aporta ventaja al listar:** en los cinco tamaños medidos, la Lista lista igual o más rápido que el ABB (Tabla 5), porque el ordenamiento de Python es casi lineal con datos ya ordenados.

### 6.5 Limitaciones evidenciadas por los datos

- **Ruido de la medición.** El coeficiente de variación mediano (desviación ÷ media) es 15,5 % en insertar, 12,1 % en buscar y 24,8 % en listar (operaciones muy cortas, de décimas de milisegundo, son más sensibles). Se detectaron 84 valores atípicos de 1.350 (6,2 %): 24 al insertar, 31 al buscar y 29 al listar. Los dos casos más claros son los de N = 2.000 con IDs aleatorios, donde la Lista (+41 %) y el ABB (+53 %) tienen dos atípicos cada uno. Que coincidan las dos estructuras sugiere una perturbación externa (por ejemplo un proceso del sistema) en las mismas repeticiones, ya que cada repetición usa los mismos datos para las tres; se puede comprobar en `crudo.csv` (columna `repeticion`).
- **Pocas búsquedas en la Lista con N grande.** Con N = 100.000 y 200.000 la Lista hizo solo 500 y 250 búsquedas por medición; su costo por paso no es monótono (148 ns con 100.000 frente a 98 ns con 200.000), señal de más ruido. Por eso la pendiente de la Lista (1,22 a 1,28) debe leerse con cautela.
- **Duración de las mediciones.** 24 de los 45 grupos de búsqueda duran menos de 1 s por medición (el mínimo es 0,318 s, en el B+ con N = 1.000); el máximo es 3,74 s (Lista con IDs aleatorios y N = 100.000). La guía del curso sugiere entre 1 s y 5 min.
- **Rango de N.** No se midió N menor que 1.000 (no se ve el cruce entre estructuras) y el ABB ordenado solo llega a 20.000.
- **Entorno.** Windows no ofrece la carga promedio del sistema, así que `carga_sistema_inicio` quedó vacío y no hay registro dado por el sistema de qué más corría en el equipo, más se aclara que tambien se encontraba activo el navegadorn(Edge). Python es una compilación MinGW (3.14.5); no se comparó con otra distribución.

---


## 7. Uso de herramientas de IA

Se usó **Claude y Gemini** como apoyo en este laboratorio, de acuerdo con lo permitido en el enunciado:

- Debugging y revisión del código de `estructuras.py`, `test_estructuras.py`, `experimento.py` y `graficar.py`.
- Sugerencias sobre la metodología experimental y estadística (diseño pareado, intervalo de confianza con t de Student, regla de Tukey, pendiente log-log).
- Revisión y mejora de esta documentación.

**Qué se verificó:** las 20 pruebas unitarias pasan; el experimento se ejecutó de principio a fin en local  (1247,8 s, 135 grupos de resultados).