# Floyd–Warshall: todos los pares

## Ejecutar

Desde la carpeta `Algoritmos`:

```powershell
python .\FloydWarshall_13_69\main.py
```

La dependencia es la misma que utilizan tus otros programas: PySide6. Si no está instalada:

```powershell
python -m pip install -r .\FloydWarshall_13_69\requirements.txt
```

## Qué contiene

Conserva el tema carbón, las fuentes, los controles y el dibujo del grafo de Bellman-Ford.
Añade las dos matrices propias de Floyd–Warshall, visibles en pantalla con desplazamiento
y completas en los PNG:

- **D:** distancia de cada origen (fila) a cada destino (columna).
- **R:** último intermedio `k` que mejoró ese par. Inicialmente contiene el destino
  para una conexión directa, el propio nodo en la diagonal, o `—` si no hay camino.
- **Cambios:** al pie de la ventana, cada mejora muestra los dos sumandos, el resultado,
  el costo anterior y el intermedio. Un clic en cualquier celda explica ese par.
- **Grafo:** muestra las distancias de la fila del origen elegido y su ruta al destino
  cuando se puede reconstruir; las rutas anteriores al resultado son provisionales.

R contiene intermedios, **no predecesores ni siguientes saltos**. La reconstrucción usa
otra matriz interna, `siguiente`, que además permite conservar la arista correcta cuando
hay conexiones paralelas. Las celdas que mejoran se destacan en negritas y con fondo claro;
la fila y la columna de `k` tienen un fondo distinto y borde en la captura.

Se usa orden **numérico** de los identificadores: 0, 1, 2, …, 78, 666. El PDF muestra
orden de texto (0, 1, 10, …); por eso las matrices intermedias pueden diferir, sin cambiar
el resultado final. No se ha renombrado ningún nodo del grafo original.

## Qué capturas se guardan

El criterio del ejemplo es una imagen por estado completo:

1. Inicialización de las matrices.
2. Una imagen después de procesar cada nodo intermedio `k`, incluso si no hubo cambios.
3. Resultado y control de ciclos negativos.

Con 30 nodos son **32 capturas**. No se guardan las 900 comparaciones individuales
por iteración. Los PNG miden 4400 × 2672 píxeles para este grafo y contienen las dos
matrices completas, el grafo, el intermedio, el resumen y la consulta origen-destino.
Las cifras y matrices también quedan en los metadatos del PNG.

`Capturar iteraciones` guarda al avanzar; saltar al resultado encola las intermedias.
`Guardar todos` exporta la sesión completa y permite pausar y continuar. Retroceder
no duplica imágenes. Cambiar la consulta crea otra carpeta y reutiliza las matrices
calculadas; editar pesos o abrir un JSON recalcula el algoritmo.
Las carpetas se crean dentro de `FloydWarshall_13_69/capturas`.

## Pesos negativos confirmados

El grafo es **no dirigido**. Estos pesos se aplican en ambos sentidos, tanto aquí como
en Bellman-Ford; Dijkstra conserva sus datos positivos:

| Conexión | Peso |
| --- | ---: |
| 24–11 | -7 |
| 21–11 | -2 |
| 6–9 | -7 |
| 5–20 | -2 |
| 3–69 | -6 |
| 666–13 | -777 |
| 9–10 | -3 |
| 23–16 | -11 |

Un peso negativo no impide usar Floyd–Warshall. Un **ciclo negativo** sí impide tener
un mínimo finito para los pares que pueden pasar por él. Por ejemplo:

```text
24 → 11 → 24 cuesta -7 + -7 = -14.
Repetirlo dos veces cuesta -28; tres veces, -42; etc.
```

Como el grafo entregado es conexo y no dirigido, sus 900 pares están afectados.
Al finalizar se muestra **D = −∞**, **R = —**, y no se inventa una ruta mínima.
`∞` significa que no hay camino; `−∞` significa que hay recorridos cuyo costo
puede disminuir indefinidamente. Durante las iteraciones se conservan los cálculos
provisionales para estudiar el proceso; la normalización a `−∞` ocurre al final.

## Primero entendamos el problema

**Entradas:** nodos, conexiones, pesos y si las conexiones son dirigidas.
**Proceso:** intentar mejorar todos los pares usando un nuevo nodo intermedio cada vez.
**Salidas:** matriz de costos, información para reconstruir rutas y pares afectados por ciclos.
Origen y destino en la interfaz solo seleccionan qué par consultar: Floyd calcula todos.

La idea es preguntar: «¿De i a j me sale más barato pasar por k?».
Si el costo directo conocido es 8 y pasar por k cuesta 4 + (-3) = 1, se guarda 1.

```text
Inicializar D: 0 en la diagonal, peso mínimo de las aristas directas, ∞ en el resto
Inicializar R y siguiente
Guardar captura inicial
Para cada nodo k:
    Tomar una copia de D antes de la iteración
    Para cada origen i y destino j:
        Si existen los tramos i → k y k → j:
            candidato = D_anterior[i,k] + D_anterior[k,j]
            Si candidato < D_anterior[i,j]:
                Actualizar D[i,j], R[i,j] = k y siguiente[i,j]
                Anotar la mejora
    Guardar una captura de toda la iteración
Detectar ciclos donde D[k,k] < 0
Marcar -∞ los pares que pueden entrar al ciclo y salir hacia su destino
Guardar resultado
```

Las copias de matrices evitan que una captura antigua cambie al seguir calculando.
Leer la matriz de la iteración anterior también hace explícita la recurrencia de Floyd:
se compara el camino anterior con el que permite usar `k`.

## Código y responsabilidades

- `grafo.py`: carga JSON y representa nodos, aristas y los dos sentidos de cada conexión.
- `algoritmo.py`: hace el cálculo sin depender de la ventana. `Cambio` describe una mejora,
  `Paso` contiene matrices de una iteración y `Recorrido` permite consultar rutas.
- `dibujo.py` y `tema.py`: conservan el dibujo y el estilo de los otros programas.
- `interfaz.py`: controla navegación, consulta de pares, edición de pesos y exportación.
- `capturas.py`: dibuja imágenes completas, independientes del zoom y desplazamiento.

## Pruebas

```powershell
python -m unittest discover -s .\FloydWarshall_13_69 -v
```

Se contrasta con una implementación independiente de Bellman-Ford, incluyendo grafos
aleatorios, pesos negativos sin ciclos, ciclos en otra componente, bucles, empates,
aristas paralelas, rutas, ocho pesos solicitados, navegación y metadatos PNG.

**Práctica:** cambia la consulta a dos nodos, selecciona una iteración y explica una
celda en negritas usando sus dos sumandos. Para practicar rutas finitas puedes abrir
una copia de un grafo positivo o un grafo dirigido sin ciclos negativos.

**Prompt de práctica:** «Explícame una iteración de Floyd–Warshall: identifica i, j y k,
calcula el costo candidato y muestra cómo cambian D y R sin saltarte la comparación».
