# Dijkstra, recorrido visual

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
4. La pestaña **Pasos** contiene toda la secuencia y permite saltar a cualquier acción.
5. Usa la rueda para ampliar el grafo, arrastra para desplazarlo y pulsa **Encuadrar** para restablecerlo. Un clic en un nodo muestra su información.
6. **Guardar todos los pasos** genera toda la secuencia sin cambiar el paso que estás mirando. Puedes pausar y continuar esta exportación.
7. **Abrir capturas** abre la carpeta de la sesión. Espera a que el contador llegue al total antes de cerrar si quieres la secuencia completa.

Atajos: espacio reproduce o pausa; flechas izquierda/derecha cambian el paso; R reinicia; Inicio vuelve al primer paso; Fin muestra el resultado; F11 activa pantalla completa; Escape sale de ella. En ventanas bajas, el panel de detalles tiene desplazamiento vertical.

Se conservan la edición de pesos, la fotografía original, la importación/exportación de JSON, las tablas de frontera y distancias, el pseudocódigo y la exportación de la explicación.

## Cómo se guardan las capturas

Las decisiones seleccionadas se guardan automáticamente en una subcarpeta de `capturas`, junto al programa. Los micropasos siguen disponibles en pantalla, pero no generan un PNG automático cada uno:

```text
capturas/
  fecha_hora_origen-destino/
    captura_0001_origen.png
    captura_0002_fijar.png
    ...
```

- Se conservan la inicialización completa, cada nodo fijado y el resultado. Cada conexión hacia un vecino no fijado genera una captura con la suma del costo, la comparación, la distancia anterior y resultante, y el predecesor que queda guardado. Esto permite entender la decisión sin buscar otra imagen.
- Seleccionar, extraer, validar, calcular, encolar, volver, omitir vecinos fijados y reconstruir cada segmento no generan capturas automáticas separadas. **Guardar todos** usa el mismo criterio. La exportación manual del paso actual sigue disponible para cualquier micropaso.
- Con el grafo y los extremos predeterminados, se guardan **39 capturas** (antes eran 72 en la primera reducción y 374 originalmente). El número cambia al modificar el grafo o los extremos.
- Cada imagen tiene **1920 × 1240 píxeles**. Conserva el diseño del grafo y el pie con la acción, la explicación y la operación.
- Las imágenes no incluyen los controles, el cursor, el zoom o la selección del usuario. El dibujo representa un estado exacto, sin colores a mitad de una transición.
- Retroceder o repetir un paso reutiliza su archivo. No hay un límite artificial de capturas.
- Saltar hacia adelante, avanzar por nodos o mostrar el resultado también programa el guardado de las decisiones intermedias seleccionadas. El contador indica cuánto falta y las capturas se numeran sin saltos.
- Cambiar origen, destino o pesos, o cargar otro grafo crea una sesión nueva. Las capturas ya guardadas de la anterior permanecen. Si hay una exportación pendiente, termínala antes de cambiar el grafo para obtener todos sus pasos.
- La exportación por lotes avanza con un temporizador de Qt: procesa una imagen y devuelve el control a la interfaz para que siga respondiendo.
- Si no se puede escribir una imagen, aparece un aviso y no se cuenta como guardada. Corrige permisos o espacio disponible y usa **Reintentar guardar todos**.

## Primero entendamos el problema

Hay dos problemas relacionados: encontrar un camino de menor costo y explicar visualmente cómo se encuentra. El resultado correcto no basta para enseñar: necesitamos conservar los estados intermedios, incluidos aquellos en los que la decisión es no cambiar nada.

**Entradas:** nodos, posiciones, aristas con peso, origen y destino. El grafo es no dirigido; una conexión se puede recorrer en ambos sentidos. Las aristas paralelas tienen identificadores distintos para no confundir sus pesos.

**Proceso:** Dijkstra mantiene la mejor distancia conocida para cada nodo, el nodo desde el que se llegó y una cola de candidatos. Cada acción registra una copia del estado.

**Salidas:** camino mínimo, costo total, lista de pasos, representación visual y evidencias PNG numeradas.

Los pesos deben ser finitos y no negativos. En la fotografía hay cinco pesos provisionales, marcados con `*`. Se conservan y se pueden corregir desde **Ver / editar grafo**. Para los datos actuales, la ruta mínima no utiliza esas aristas.

## Entidades y datos

| Elemento | Qué representa |
| --- | --- |
| `Grafo` | Los nodos, conexiones y posiciones para dibujarlos. |
| `Arista` | Una conexión, su peso y un identificador único. |
| `dist` | Diccionario que relaciona cada nodo con su mejor distancia conocida. |
| `prev` | Diccionario que guarda el nodo anterior y la arista usada para llegar. |
| `fijos` | Conjunto de nodos cuya distancia ya es definitiva. |
| `cola` | Cola de prioridad: permite extraer la entrada con menor distancia. |
| `Paso` | Una instantánea del algoritmo y la explicación de una sola acción. |
| `Recorrido` | Todos los pasos y el resultado final. |
| `SesionCapturas` | Compone y guarda las imágenes de un recorrido. |

Un **diccionario** permite buscar información por una clave, como `dist[17]`. Un **conjunto** permite comprobar si un nodo ya está fijado. Una **instantánea** es una copia del estado en un momento concreto; funciona como una foto de los datos.

## Lógica paso a paso

1. Inicializar las distancias en infinito: todavía no conocemos ningún camino.
2. Poner la distancia del origen en cero y añadirlo a la cola.
3. Observar el menor candidato y extraer su entrada.
4. Comprobar si sigue vigente. Si está obsoleta, mostrar por qué se descarta.
5. Fijar el nodo válido: su distancia mínima ya es definitiva.
6. Comprobar si es el destino. Si lo es, reconstruir el camino.
7. Observar sus conexiones y seleccionar un vecino.
8. Resaltar la arista y leer su peso.
9. Comprobar si el vecino ya está fijado; en ese caso, omitirlo.
10. Calcular la distancia candidata y, en otro paso, compararla con la registrada.
11. Si mejora: actualizar distancia, guardar predecesor y añadir la entrada a la cola, en pasos separados.
12. Si no mejora: explicar por qué se conserva la distancia.
13. Volver al nodo actual y continuar con otra conexión.
14. Al terminar sus conexiones, volver a elegir el menor candidato.
15. Reconstruir desde el destino siguiendo predecesores; luego mostrar el camino en sentido origen → destino.

## Pseudocódigo

```text
distancia de todos los nodos = infinito
distancia del origen = 0
encolar origen con costo 0

mientras la cola no esté vacía:
    extraer entrada con menor distancia
    si está obsoleta:
        registrar descarte y continuar
    fijar nodo actual
    si actual es destino:
        terminar búsqueda
    por cada conexión del nodo actual:
        observar vecino y arista
        si vecino está fijado:
            registrar omisión
        en otro caso:
            candidata = distancia[actual] + peso
            comparar candidata con distancia[vecino]
            si candidata es menor:
                distancia[vecino] = candidata
                previo[vecino] = actual y arista
                encolar candidata y vecino
            en otro caso:
                conservar lo que ya conocemos

si se fijó el destino:
    seguir predecesores hasta el origen
    invertir la ruta
en otro caso:
    informar que no existe camino
```

Cada acción relevante de este esquema genera su propio `Paso`. No se muestra el funcionamiento interno de la biblioteca `heapq`; sí se muestran todas las extracciones, entradas obsoletas y decisiones de Dijkstra.

## Cómo se organiza el código

- `algoritmo.py`: calcula sin depender de la ventana. `registrar()` guarda copias de los diccionarios y del conjunto de nodos fijados. Así, actualizar una distancia después no altera un paso anterior.
- `interfaz.py`: crea controles, muestra los datos y dibuja el grafo. `aplicar_paso()` selecciona una instantánea, actualiza los componentes y solicita guardar su imagen. `Lienzo.dibujar()` se utiliza tanto en pantalla como en la exportación.
- `tema.py`: concentra colores y estilos. Para cambiar la apariencia no es necesario modificar Dijkstra.
- `capturas.py`: prepara una carpeta por sesión, compone cada lámina y escribe sus archivos. `guardados` es un conjunto de índices para evitar duplicados.
- `main.py`: inicia la aplicación.
- `test_algoritmo.py` y `test_capturas.py`: comprueban el cálculo, la separación de acciones, las imágenes y la navegación.

Este reparto de responsabilidades es la refactorización principal: cálculo, dibujo y guardado tienen trabajos distintos y se pueden comprobar por separado.

### Ejemplo de una mejora

La operación central es:

```python
candidato = du + peso
anterior = dist[v]
if candidato < anterior:
    dist[v] = candidato
    # Se registra este cambio antes de modificar el predecesor.
```

`du` es la distancia hasta el nodo actual, `peso` es el costo de la arista y `v` es el vecino. La condición pregunta si llegar por esa conexión es mejor. En el programa completo hay llamadas a `registrar()` entre el cálculo, la comparación, el cambio de distancia, el guardado del predecesor y la actualización de la cola.

`heappush()` añade una entrada a la cola de prioridad y `heappop()` extrae la menor. Son funciones de `heapq`, incluida en Python. La tabla **Frontera** muestra los candidatos lógicos sin duplicados; la cola interna puede conservar entradas antiguas que se descartan al extraerlas. No son exactamente la misma lista.

## Prueba de escritorio

Para el camino que finalmente resulta mínimo:

| Acción | Operación | Distancia guardada |
| --- | --- | --- |
| Partir de 13 | 0 | `d[13] = 0` |
| Evaluar 13 → 16 | 0 + 3 | `d[16] = 3` |
| Evaluar 16 → 17 | 3 + 7 | `d[17] = 10` |
| Evaluar 17 → 69 | 10 + 4 | `d[69] = 14` |

Dijkstra también examina otras ramas; esta tabla solo resume las mejoras que componen la ruta final. Encontrar por primera vez el destino no termina la búsqueda: hay que extraerlo con una entrada válida y fijarlo.

Predecesores: `69 ← 17 ← 16 ← 13`. Al invertir ese orden obtenemos **13 → 16 → 17 → 69**, con costo **3 + 7 + 4 = 14**.

Con los datos actuales se generan **374 pasos**, cada uno con su propia imagen al exportar todo. Si cambian los pesos o los extremos, también puede cambiar la cantidad de pasos.

## Comprobaciones y errores comunes

Ejecuta:

```powershell
python -m unittest -v
```

Las 18 pruebas incluyen comparación de costos con Floyd–Warshall para todos los pares del grafo, aristas paralelas, empates, peso cero, origen igual a destino, nodos desconectados, entradas obsoletas, estados independientes, guardado sin duplicados, errores de escritura y capturas que no dependen del zoom.

Errores que debes evitar al modificar el proyecto:

- Guardar `dist` directamente en cada paso sin copiarlo: los pasos anteriores terminarían mostrando las modificaciones posteriores.
- Detenerse al descubrir el destino: su primera distancia puede ser tentativa.
- Cambiar una distancia cuando el nuevo costo es igual: este proyecto conserva el predecesor anterior para resolver empates de forma estable.
- Confundir la visita visual con una distancia definitiva: un vecino puede estar bajo evaluación sin estar fijado.
- Capturar la ventana completa: introduce controles y puede cortar el grafo si hay zoom. La exportación usa un dibujo completo independiente.
- Cerrar o cambiar el grafo antes de terminar un lote: los PNG guardados quedan intactos, pero faltarán los pendientes.

Los archivos originales de resultados de la carpeta se conservan como referencia. Las evidencias nuevas están en la carpeta de cada sesión.

## Resumen y práctica

Aprendiste a separar un algoritmo de su representación visual y a convertir operaciones agrupadas en estados observables. Los conceptos clave son diccionarios, conjuntos, cola de prioridad, predecesores, instantáneas, temporizadores y separación de responsabilidades.

Practica cambiando el peso de 16–17: antes de reproducir, intenta predecir qué distancias cambiarán. Luego crea un grafo pequeño de cuatro nodos y escribe a mano las primeras comparaciones.

Un prompt más preciso para esta tarea sería: «Modifica mi visualizador de Dijkstra en Python conservando sus datos y funciones. Usa un diseño minimalista con prioridad al grafo; separa cada selección, comprobación, cálculo y actualización en pasos individuales. Guarda automáticamente cada estado como PNG limpio, numerado y explicado, permite exportar toda la secuencia y comprueba que el costo mínimo no cambie. Explícame la arquitectura y cómo probarlo».
