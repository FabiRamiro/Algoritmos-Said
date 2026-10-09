# Algoritmos de caminos mínimos

Visualizador interactivo de cuatro algoritmos clásicos de caminos mínimos: Dijkstra, Bellman-Ford, Floyd-Warshall y A*. Los cuatro trabajan sobre el mismo grafo, transcrito de una fotografía, y buscan el camino del nodo 13 al nodo 69.

Cada algoritmo se ejecuta paso a paso. En cada momento se puede ver qué nodo se está procesando, qué arista se examina, qué distancias cambian y por qué. Los algoritmos están implementados desde cero en Python, sin bibliotecas de grafos, y la interfaz usa PySide6 (Qt).

## Contenido

| Algoritmo | Carpeta | Qué calcula |
| --- | --- | --- |
| Dijkstra | `Dijkstra_13_69/` | Camino mínimo desde un origen con una cola de prioridad. Requiere pesos no negativos. |
| Bellman-Ford | `BellmanFord_13_69/` | Camino mínimo desde un origen mediante rondas de relajación. Admite pesos negativos y detecta ciclos negativos. |
| Floyd-Warshall | `FloydWarshall_13_69/` | Distancias entre todos los pares de nodos mediante programación dinámica. |
| A* | `AStar_13_69/` | Camino mínimo entre un origen y un destino, guiado por una heurística. |

Además, la raíz del repositorio contiene una aplicación que reúne los cuatro algoritmos en una sola ventana.

## El grafo

El grafo tiene 30 nodos y 63 aristas, y no es dirigido: cada conexión se puede recorrer en ambos sentidos. Las posiciones de los nodos reproducen la fotografía original (`grafo_original.jpeg` en cada carpeta). Los datos están en el archivo `grafo.json` de cada proyecto.

Hay dos versiones de los pesos:

- **Dijkstra y A\*** usan pesos no negativos, como exigen ambos algoritmos.
- **Bellman-Ford y Floyd-Warshall** usan una versión en la que ocho aristas tienen peso negativo, para mostrar cómo tratan ese caso.

## Resultados

Con los pesos no negativos, Dijkstra y A* encuentran el mismo camino:

```text
13 → 16 → 17 → 69    costo 3 + 7 + 4 = 14
```

A* llega a ese resultado fijando 7 nodos, frente a los 10 de Dijkstra. Su heurística es la distancia en línea recta hasta el destino, multiplicada por una escala que garantiza que nunca supere el costo real. Así se conserva la garantía de obtener el camino mínimo.

Con la versión de pesos negativos, Bellman-Ford y Floyd-Warshall informan que **no existe un costo mínimo finito**. En un grafo no dirigido, una arista con peso negativo se puede recorrer de ida y vuelta indefinidamente, y cada recorrido reduce el costo. Es decir, cada arista negativa forma un ciclo negativo. Los dos algoritmos detectan esta situación y la muestran en lugar de devolver un valor incorrecto.

## Requisitos

- Python 3 (desarrollado y probado con Python 3.14).
- PySide6 6.10.2.

```bash
python -m pip install -r requirements.txt
```

## Uso

### Aplicación unificada

Desde la raíz del repositorio:

```bash
python main.py
```

Al iniciar aparece una pantalla para elegir el algoritmo. Después se puede cambiar en cualquier momento desde la barra superior o con el teclado:

| Atajo | Acción |
| --- | --- |
| `Ctrl+1` … `Ctrl+4` | Abrir Dijkstra, Bellman-Ford, Floyd-Warshall o A* |
| `Ctrl+0` | Volver a la pantalla de inicio |
| `Espacio` | Reproducir o pausar |
| `←` / `→` | Paso anterior o siguiente |
| `Inicio` / `Fin` | Ir al primer paso o al resultado |
| `F11` / `Esc` | Entrar o salir de pantalla completa |

Cada algoritmo conserva su estado al cambiar a otro, y su reproducción se pausa. Para abrir un algoritmo directamente:

```bash
python main.py --algoritmo astar
```

Los valores aceptados son `dijkstra`, `bellman-ford`, `floyd-warshall` y `astar`.

### Proyectos individuales

Cada carpeta funciona también como un programa independiente:

```bash
python Dijkstra_13_69/main.py
```

Los algoritmos también se pueden ejecutar sin interfaz gráfica. Por ejemplo, este comando imprime el recorrido completo de A* en la consola:

```bash
python AStar_13_69/algoritmo.py --origen 13 --destino 69
```

### Funciones comunes

En todos los programas es posible:

- Elegir el nodo de origen y el de destino.
- Avanzar paso a paso, reproducir automáticamente y ajustar la velocidad.
- Ampliar y desplazar el grafo, y consultar los datos de un nodo con un clic.
- Revisar las tablas de distancias, predecesores y la frontera o las matrices, según el algoritmo.
- Editar los pesos e importar o exportar el grafo en formato JSON.

Dijkstra, Bellman-Ford y A* permiten además ver la fotografía original del grafo.

## Capturas

Mientras se avanza por un recorrido, los pasos importantes se guardan como imágenes PNG en la carpeta `capturas/` del proyecto correspondiente, dentro de una subcarpeta con la fecha, la hora, el origen y el destino. Cada imagen contiene el grafo completo y una explicación del paso. No incluye los controles de la ventana ni depende del zoom. El botón **Guardar todos** genera la secuencia completa de una sola vez.

## Estructura del repositorio

```text
.
├── main.py              Punto de entrada de la aplicación unificada
├── aplicacion.py        Ventana principal y navegación entre algoritmos
├── cargador.py          Importa cada proyecto sin que sus módulos se mezclen
├── test_aplicacion.py   Pruebas de la aplicación unificada
├── Dijkstra_13_69/
├── BellmanFord_13_69/
├── FloydWarshall_13_69/
└── AStar_13_69/
```

Dentro de cada proyecto, las responsabilidades están separadas:

- `algoritmo.py`: el cálculo. No depende de la interfaz y guarda una copia del estado en cada paso.
- `interfaz.py`: la ventana, los controles y las tablas.
- `capturas.py`: la composición y el guardado de las imágenes.
- `tema.py`: los colores y estilos, compartidos por los cuatro programas.
- `grafo.json`: los nodos, las posiciones y las aristas.

La aplicación unificada no duplica código: carga la ventana original de cada proyecto. Por eso, cualquier cambio en un proyecto se refleja también en ella.

## Pruebas

Cada proyecto incluye sus propias pruebas, que se ejecutan desde su carpeta:

```bash
cd AStar_13_69
python -m unittest -v
```

Las pruebas de la aplicación unificada se ejecutan desde la raíz con el mismo comando. En total hay 98 pruebas. Entre otras cosas, comprueban que:

- Los costos coinciden con los de un algoritmo de referencia independiente.
- La heurística de A* es admisible y consistente.
- Los ciclos negativos se detectan.
- Los estados guardados en cada paso son independientes entre sí.
- Las capturas se generan correctamente.
