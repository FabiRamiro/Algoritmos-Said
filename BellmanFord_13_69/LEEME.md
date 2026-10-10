# Bellman-Ford: grafo dirigido actualizado

El archivo `grafo.json` sigue las flechas y posiciones de la imagen dirigida
compartida el 9 de octubre de 2026. Tiene 30 nodos y 64 arcos.
El nodo que antes figuraba como 78 ahora es 18, como en la nueva imagen.

La conexión de peso 3 entre 12 y 16 admite ambos sentidos, confirmados por el usuario:
`e33` es 12 → 16 y `e64` es 16 → 12. Además, `e32` conserva 12 → 16 con peso 16.
Se dibujan por separado para distinguir sus flechas y pesos.

Los ocho arcos negativos son:

| Arco | Peso |
| --- | ---: |
| 11 → 21 | -2 |
| 11 → 24 | -7 |
| 6 → 9 | -7 |
| 9 → 10 | -3 |
| 666 → 13 | -777 |
| 3 → 69 | -6 |
| 23 → 16 | -11 |
| 5 → 20 | -2 |

No se detectan ciclos negativos, tampoco fuera del origen seleccionado.
La ruta de 13 a 69 es **13 → 16 → 17 → 69**, con costo **14**.

## Cómo se interpreta

En un grafo dirigido, un registro con `u=11`, `v=24` y `weight=-7` solo permite
ir de 11 a 24. El regreso necesita otro arco explícito. `directed: true` indica
al programa que respete esa regla. Un peso negativo por sí solo no crea un ciclo
negativo: debe existir un recorrido que vuelva al mismo nodo y cuya suma sea negativa.

La interfaz y las nuevas capturas leen este archivo. La opción de fotografía
inicial conserva la foto antigua, que ya no representa las direcciones actuales.

Ejecuta `python BellmanFord_13_69/main.py` desde la raíz o elige Bellman-Ford
en `python main.py`. Reinicia la aplicación para cargar los datos actualizados.

**Práctica:** suma el ciclo 11 → 24 → 21 → 29 → 7 → 11. Aunque incluye -7,
su costo total es 8, por lo que no es un ciclo negativo.
