# A*, recorrido visual

## Ejecutar y usar

Desde la carpeta de este proyecto:

```powershell
python main.py
```

Si falta la dependencia:

```powershell
python -m pip install -r requirements.txt
```

1. Selecciona origen y destino. El caso de la tarea usa **13 y 69**.
2. Deja seleccionado **Cada micro paso** para ver cada acción por separado.
3. Usa **Siguiente**, **Anterior** o **Reproducir**. La velocidad regula el tiempo entre pasos.
4. La secuencia de la izquierda contiene todos los pasos y permite saltar a cualquier acción.
5. Usa la rueda para ampliar el grafo, arrastra para desplazarlo y pulsa **Encuadrar** para restablecerlo. Un clic en un nodo muestra su `g`, `h`, `f` y su predecesor.
6. **Guardar todos** genera todas las capturas sin cambiar el paso que estás mirando. Puedes pausar y continuar esta exportación.
7. **Carpeta PNG** abre la carpeta de la sesión.

Atajos: espacio reproduce o pausa; flechas izquierda/derecha cambian el paso; R reinicia; Inicio vuelve al primer paso; Fin muestra el resultado; F11 activa pantalla completa; Escape sale de ella.

La interfaz, la edición de pesos, la fotografía original y la importación/exportación de JSON son las mismas del proyecto de Dijkstra. Lo nuevo de A* aparece en el grafo (etiquetas `g= f=` y `h=`), en las tablas **Frontera** y **Distancias**, y en el pseudocódigo.

## Cómo se guardan las capturas

Mientras avanzas, las decisiones importantes se guardan automáticamente en una subcarpeta de `capturas`, junto al programa:

```text
capturas/
  fecha_hora_origen-destino/
    captura_0001_heuristica.png
    captura_0002_origen.png
    captura_0003_fijar.png
    ...
```

- Se guardan la heurística, la inicialización, cada nodo fijado, cada conexión hacia un vecino no fijado (con la suma de `g`, la comparación, la nueva `f` y el predecesor) y el resultado.
- Con el grafo y los extremos predeterminados se guardan **33 capturas**. Ya hay una sesión completa generada en `capturas/`.
- Cada imagen tiene **1920 × 1240 píxeles**: el grafo completo arriba y la explicación abajo, sin controles, cursor ni zoom.
- Cambiar origen, destino o pesos, o cargar otro grafo, crea una sesión nueva. Las capturas anteriores se conservan.

## La idea de A*

A* es Dijkstra con una brújula. Dijkstra elige siempre el nodo con menor costo acumulado `g(n)` y por eso se expande en todas direcciones. A* elige el nodo con menor

```text
f(n) = g(n) + h(n)
```

- `g(n)`: costo real del mejor camino conocido desde el origen hasta `n`.
- `h(n)`: estimación de lo que falta desde `n` hasta el destino.
- `f(n)`: costo estimado de un camino completo que pase por `n`.

Si `h` nunca sobreestima el costo real (**admisible**) y además cumple `h(u) ≤ peso(u,v) + h(v)` en cada arista (**consistente**), A* encuentra el mismo costo mínimo que Dijkstra y un nodo fijado ya no vuelve a cambiar.

### La heurística de este proyecto

El grafo no trae una heurística; solo tiene las posiciones del dibujo de la fotografía. Usamos la distancia en línea recta hasta el destino, multiplicada por una escala:

```text
escala = mínimo de peso / longitud entre todas las aristas
h(n)   = escala · distancia_euclidiana(n, destino)
```

Con esa escala, cada arista cumple `peso ≥ escala · longitud`. Por la desigualdad triangular, ningún camino puede ser más barato que `h`, y la heurística resulta consistente. El valor se trunca hacia abajo a dos decimales para que se lea fácilmente sin perder esa propiedad.

Para este grafo la escala es **0.002507**. La limita la arista 27–666: es muy larga en el dibujo pero solo pesa 1. Por eso los valores de `h` son pequeños (`h(13) = 1.12`), pero bastan para orientar la búsqueda:

| | Nodos fijados | Pasos |
| --- | --- | --- |
| Dijkstra (equivale a `h = 0`) | 10 | 375 |
| A* | **7** | **294** |

A* deja de fijar 666, 23 y 27, que están lejos de 69.

## Prueba de escritorio

Valores de la heurística en la ruta final: `h(13) = 1.12`, `h(16) = 0.78`, `h(17) = 0.39`, `h(69) = 0`.

| Acción | g | f = g + h |
| --- | --- | --- |
| Partir de 13 | 0 | 0 + 1.12 = 1.12 |
| Evaluar 13 → 16 | 0 + 3 = 3 | 3 + 0.78 = 3.78 |
| Evaluar 16 → 17 | 3 + 7 = 10 | 10 + 0.39 = 10.39 |
| Evaluar 17 → 69 | 10 + 4 = 14 | 14 + 0 = 14 |

Orden en que se fijan los nodos: **13 → 16 → 12 → 17 → 78 → 1 → 69**. Encontrar el destino por primera vez no termina la búsqueda: hay que extraerlo de la cola con una entrada válida y fijarlo.

Predecesores: `69 ← 17 ← 16 ← 13`. Al invertir ese orden obtenemos **13 → 16 → 17 → 69**, con costo **3 + 7 + 4 = 14**, el mismo que con Dijkstra, Bellman-Ford y Floyd-Warshall.

## Pseudocódigo

```text
calcular h(n) para todos los nodos
g de todos los nodos = infinito
g del origen = 0
encolar origen con prioridad f = h(origen)

mientras la cola no esté vacía:
    extraer entrada con menor f (empates: menor h, después menor nodo)
    si está obsoleta:
        registrar descarte y continuar
    fijar nodo actual
    si actual es destino:
        terminar búsqueda
    por cada conexión del nodo actual:
        si vecino está fijado:
            registrar omisión
        en otro caso:
            nueva = g[actual] + peso
            si nueva < g[vecino]:
                g[vecino] = nueva
                previo[vecino] = actual y arista
                encolar vecino con prioridad g[vecino] + h(vecino)
            en otro caso:
                conservar lo que ya conocemos

si se fijó el destino:
    seguir predecesores hasta el origen e invertir la ruta
en otro caso:
    informar que no existe camino
```

## Cómo se organiza el código

- `algoritmo.py`: `heuristica_euclidiana()` calcula `h` y la escala; `a_estrella()` ejecuta el algoritmo y guarda una instantánea (`Paso`) por acción. No depende de Qt.
- `interfaz.py`: ventana, tablas y dibujo del grafo. `Lienzo.dibujar()` se usa tanto en pantalla como en las capturas.
- `capturas.py`: elige qué pasos se guardan, compone cada lámina y escribe los PNG.
- `tema.py`: colores y estilos.
- `main.py`: inicia la aplicación.
- `test_algoritmo.py` y `test_capturas.py`: pruebas.

## Comprobaciones

```powershell
python -m unittest -v
```

Las 29 pruebas comparan el costo de A* con Floyd-Warshall para todos los pares del grafo, comprueban que la heurística sea admisible y consistente para cualquier destino y que A* fije menos nodos que Dijkstra. También cubren aristas paralelas, empates, peso cero, origen igual a destino, nodos desconectados, entradas obsoletas, estados independientes y el guardado de capturas.

Errores que debes evitar al modificar el proyecto:

- Usar una heurística que sobreestime (por ejemplo, la distancia del dibujo sin escalar): A* podría devolver un camino que no es el mínimo.
- Comparar `f` en lugar de `g` al relajar una arista: la heurística solo ordena la cola; el costo real sigue siendo `g`.
- Detenerse al descubrir el destino: su primera `g` puede ser tentativa.
