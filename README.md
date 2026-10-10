# Algoritmos de caminos mínimos

Visualizador interactivo de cuatro algoritmos clásicos de caminos mínimos: Dijkstra, Bellman-Ford, Floyd-Warshall y A*. Trabajan sobre versiones del grafo del ejercicio y consultan el camino del nodo 13 al nodo 69.

Cada algoritmo se ejecuta paso a paso. En cada momento se puede ver qué nodo se está procesando, qué arista se examina, qué distancias cambian y por qué. Los algoritmos están implementados desde cero en Python, sin bibliotecas de grafos, y la interfaz usa PySide6 (Qt).

## Contenido

| Algoritmo | Carpeta | Qué calcula |
| --- | --- | --- |
| Dijkstra | `Dijkstra_13_69/` | Camino mínimo desde un origen con una cola de prioridad. Requiere pesos no negativos. |
| Bellman-Ford | `BellmanFord_13_69/` | Camino mínimo desde un origen mediante rondas de relajación. Admite pesos negativos y detecta ciclos negativos. |
| Floyd-Warshall | `FloydWarshall_13_69/` | Distancias entre todos los pares de nodos mediante programación dinámica. |
| A* | `AStar_13_69/` | Camino mínimo entre un origen y un destino, guiado por una heurística. |

Además, la raíz del repositorio contiene una aplicación que reúne los cuatro algoritmos en una sola ventana.

## Video MP4 con audio durante el guardado

Al pulsar **Guardar todos**, las capturas se dibujan y se escriben en un hilo de
trabajo. La ventana queda libre para reproducir el video a su velocidad original,
mostrar el progreso y permitir pausar. La captura que esté escribiéndose termina
antes de pausar, para no dejar un PNG incompleto. También se usa este mecanismo
al completar capturas para crear diapositivas.

Coloca estos archivos junto al `main.py` de la raíz:

| Algoritmo | Video con su audio incluido |
| --- | --- |
| Dijkstra | `dancing1.mp4` |
| Bellman-Ford | `dancing2.mp4` |
| Floyd-Warshall | `dancing3.mp4` |
| A* | `dancing4.mp4` |

El video y su audio se reproducen juntos en bucle, con volumen inicial del 35 %.
Se detienen al terminar, pausar o fallar el guardado. Al continuar, el video se
reinicia. No se necesita un MP3 separado: se usa la pista de audio del MP4; un
video sin pista de audio se reproduce en silencio. La imagen conserva sus
proporciones. No hace falta instalar otra dependencia: el reproductor utiliza
QtMultimedia y QtMultimediaWidgets, incluidos en PySide6.

Para usar otras rutas o nombres, edita el diccionario `MULTIMEDIA` de
`pantalla_carga.py`. Si falta el MP4 o no puede reproducirse, se muestra un
mensaje de carga y el guardado continúa. Los antiguos GIF y MP3 ya no se usan.

Prueba automatizada: `python -m unittest test_pantalla_carga -v`.

## El grafo

Los datos están en el archivo `grafo.json` de cada proyecto. Todos tienen 30 nodos.

Hay dos versiones del grafo:

- **Dijkstra, A\* y Floyd-Warshall** usan las mismas 63 aristas no dirigidas con pesos positivos.
- **Bellman-Ford** usa las direcciones de la imagen actualizada: 64 arcos, ocho pesos negativos y ningún ciclo negativo. La conexión de peso 3 entre 12 y 16 tiene ambos sentidos; el arco de peso 16 va de 12 a 16. En esta versión el nodo central inferior es 18, en lugar de 78.

## Resultados

Los cuatro algoritmos, cada uno con su versión del grafo, encuentran este camino:

```text
13 → 16 → 17 → 69    costo 3 + 7 + 4 = 14
```

A* llega a ese resultado fijando 7 nodos, frente a los 10 de Dijkstra. Su heurística es la distancia en línea recta hasta el destino, multiplicada por una escala que garantiza que nunca supere el costo real. Así se conserva la garantía de obtener el camino mínimo.

Bellman-Ford conserva pesos negativos, pero las direcciones del nuevo grafo impiden formar ciclos de costo negativo. Una arista negativa por sí sola no significa que exista un ciclo negativo. Floyd-Warshall utiliza ahora pesos positivos y obtiene distancias finitas para los 900 pares. Ambos algoritmos conservan la detección de ciclos negativos para otros grafos importados.

## Requisitos

- Python 3 (desarrollado y probado con Python 3.14).
- PySide6 6.10.2.
- python-pptx 1.0.2, solo para crear presentaciones de PowerPoint. Sin esta biblioteca, las diapositivas se generan únicamente en PDF.

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

La captura automática empieza **desactivada** para que navegar y reproducir no tenga que dibujar y comprimir un PNG de alta resolución en cada paso. Puedes activarla con **Capturar al avanzar**, **Capturar pasos del PDF** o **Capturar iteraciones**, según el algoritmo. El botón **Guardar todos** sigue generando la secuencia completa aunque no hayas activado la captura automática.

Las imágenes se guardan en la carpeta `capturas/` del proyecto correspondiente, dentro de una subcarpeta con la fecha, la hora, el origen y el destino. Cada imagen contiene el grafo completo y una explicación del paso. No incluye los controles de la ventana ni depende del zoom. La exportación de imágenes puede tardar; desactivar la captura automática evita ese trabajo durante la navegación.

## Excel de Floyd–Warshall

Abre Floyd–Warshall y pulsa **Guardar Excel**, en la parte inferior. Elige dónde guardar el `.xlsx`. Funciona también desde el proyecto individual y no necesita Excel instalado ni bibliotecas adicionales.

- **Iteraciones:** matrices D y R lado a lado, con inicialización, cada intermedio y control final colocados hacia abajo, como en la referencia.
- **Resultado:** matrices finales y la consulta origen-destino elegida.
- Formato sencillo: fondo blanco, texto negro y encabezados en negrita. Verde suave indica una mejora; gris claro marca la fila y columna del intermedio. Los encabezados mantienen los identificadores reales de los nodos.

Se exportan valores numéricos y los símbolos `∞`, `−∞` y `—`, conservando los decimales. Son instantáneas del cálculo: para cambiar pesos y recalcular, utiliza el programa y exporta de nuevo. **Guardar Excel** incluye todos los pasos sin generar imágenes primero ni depender de la iteración visible. Si el archivo está abierto en Excel, ciérralo antes de reemplazarlo.

## Diapositivas

Las capturas de una sesión se pueden convertir en una presentación, con una diapositiva por captura y en el mismo orden. Se generan dos archivos dentro de la carpeta de la sesión:

- `diapositivas.pdf`, que se puede presentar en pantalla completa desde cualquier lector de PDF.
- `diapositivas.pptx`, que se puede editar en PowerPoint. Las notas del orador de cada diapositiva contienen la explicación del paso.

El tamaño de las diapositivas sigue la proporción de las capturas, así que las imágenes ocupan toda la página.

En la aplicación unificada, el botón **Crear diapositivas** de la barra superior convierte la sesión del algoritmo abierto. Si faltan capturas, ofrece guardarlas primero para que la presentación muestre el recorrido completo. Cuando una sesión tiene más de 300 pasos para capturar, solo se usan las capturas de los pasos que ya se recorrieron.

También se puede convertir cualquier carpeta de capturas desde la terminal:

```bash
python diapositivas.py AStar_13_69/capturas/<carpeta de la sesión>
```

La opción `--formato pdf` o `--formato pptx` genera solo uno de los dos archivos.

## Estructura del repositorio

```text
.
├── main.py              Punto de entrada de la aplicación unificada
├── aplicacion.py        Ventana principal y navegación entre algoritmos
├── cargador.py          Importa cada proyecto sin que sus módulos se mezclen
├── diapositivas.py      Convierte una carpeta de capturas en PDF y PowerPoint
├── test_aplicacion.py   Pruebas de la aplicación unificada
├── test_diapositivas.py Pruebas del generador de diapositivas
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

Las pruebas de la aplicación unificada y del generador de diapositivas se ejecutan desde la raíz con el mismo comando. En total hay 109 pruebas. Entre otras cosas, comprueban que:

- Los costos coinciden con los de un algoritmo de referencia independiente.
- La heurística de A* es admisible y consistente.
- Los ciclos negativos se detectan.
- Los estados guardados en cada paso son independientes entre sí.
- Las capturas y las diapositivas se generan correctamente.
