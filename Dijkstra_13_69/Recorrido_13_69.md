# Dijkstra: 13 → 69

Ruta: 13 → 16 → 17 → 69
Costo: 14

Orden de nodos fijados: 13 → 16 → 12 → 17 → 78 → 1 → 666 → 23 → 27 → 69

El algoritmo se detiene al fijar el destino. Las otras distancias
solo son definitivas si el nodo está fijado.

## Secuencia

000. Todo empieza en el origen. La distancia de 13 a sí mismo es 0. Los demás nodos comienzan en infinito.
     d[13] = 0    ·    resto = ∞
001. Fijamos el nodo 13. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[13] = 0
002. Exploramos 13 → 12. Sumamos la distancia hasta 13 y el peso 9 de esta arista.
     0 + 9 = 9
003. Mejor camino hacia 12. La distancia pasa de ∞ a 9. Guardamos 13 como su predecesor.
     9 < ∞   →   actualizar
004. Exploramos 13 → 16. Sumamos la distancia hasta 13 y el peso 3 de esta arista.
     0 + 3 = 3
005. Mejor camino hacia 16. La distancia pasa de ∞ a 3. Guardamos 13 como su predecesor.
     3 < ∞   →   actualizar
006. Exploramos 13 → 666. Sumamos la distancia hasta 13 y el peso 777 de esta arista.
     0 + 777 = 777
007. Mejor camino hacia 666. La distancia pasa de ∞ a 777. Guardamos 13 como su predecesor.
     777 < ∞   →   actualizar
008. Fijamos el nodo 16. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[16] = 3
009. Exploramos 16 → 12. Sumamos la distancia hasta 16 y el peso 3 de esta arista.
     3 + 3 = 6
010. Mejor camino hacia 12. La distancia pasa de 9 a 6. Guardamos 16 como su predecesor.
     6 < 9   →   actualizar
011. Exploramos 16 → 12. Sumamos la distancia hasta 16 y el peso 16 de esta arista.
     3 + 16 = 19
012. Conservamos la distancia de 12. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     19 ≥ 6   →   conservar
013. El nodo 13 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[13] = 0  ·  definitiva
014. Exploramos 16 → 17. Sumamos la distancia hasta 16 y el peso 7 de esta arista.
     3 + 7 = 10
015. Mejor camino hacia 17. La distancia pasa de ∞ a 10. Guardamos 16 como su predecesor.
     10 < ∞   →   actualizar
016. Exploramos 16 → 23. Sumamos la distancia hasta 16 y el peso 11 de esta arista.
     3 + 11 = 14
017. Mejor camino hacia 23. La distancia pasa de ∞ a 14. Guardamos 16 como su predecesor.
     14 < ∞   →   actualizar
018. Fijamos el nodo 12. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[12] = 6
019. Exploramos 12 → 1. Sumamos la distancia hasta 12 y el peso 7 de esta arista.
     6 + 7 = 13
020. Mejor camino hacia 1. La distancia pasa de ∞ a 13. Guardamos 12 como su predecesor.
     13 < ∞   →   actualizar
021. Exploramos 12 → 8. Sumamos la distancia hasta 12 y el peso 9 de esta arista.
     6 + 9 = 15
022. Mejor camino hacia 8. La distancia pasa de ∞ a 15. Guardamos 12 como su predecesor.
     15 < ∞   →   actualizar
023. El nodo 13 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[13] = 0  ·  definitiva
024. El nodo 16 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[16] = 3  ·  definitiva
025. El nodo 16 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[16] = 3  ·  definitiva
026. Exploramos 12 → 78. Sumamos la distancia hasta 12 y el peso 4 de esta arista.
     6 + 4 = 10
027. Mejor camino hacia 78. La distancia pasa de ∞ a 10. Guardamos 12 como su predecesor.
     10 < ∞   →   actualizar
028. Exploramos 12 → 666. Sumamos la distancia hasta 12 y el peso 7 de esta arista.
     6 + 7 = 13
029. Mejor camino hacia 666. La distancia pasa de 777 a 13. Guardamos 12 como su predecesor.
     13 < 777   →   actualizar
030. Fijamos el nodo 17. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[17] = 10
031. Exploramos 17 → 2. Sumamos la distancia hasta 17 y el peso 5 de esta arista.
     10 + 5 = 15
032. Mejor camino hacia 2. La distancia pasa de ∞ a 15. Guardamos 17 como su predecesor.
     15 < ∞   →   actualizar
033. El nodo 16 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[16] = 3  ·  definitiva
034. Exploramos 17 → 69. Sumamos la distancia hasta 17 y el peso 4 de esta arista.
     10 + 4 = 14
035. Mejor camino hacia 69. La distancia pasa de ∞ a 14. Guardamos 17 como su predecesor.
     14 < ∞   →   actualizar
036. Exploramos 17 → 70. Sumamos la distancia hasta 17 y el peso 6 de esta arista.
     10 + 6 = 16
037. Mejor camino hacia 70. La distancia pasa de ∞ a 16. Guardamos 17 como su predecesor.
     16 < ∞   →   actualizar
038. Fijamos el nodo 78. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[78] = 10
039. Exploramos 78 → 4. Sumamos la distancia hasta 78 y el peso 5 de esta arista.
     10 + 5 = 15
040. Mejor camino hacia 4. La distancia pasa de ∞ a 15. Guardamos 78 como su predecesor.
     15 < ∞   →   actualizar
041. El nodo 12 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[12] = 6  ·  definitiva
042. Exploramos 78 → 666. Sumamos la distancia hasta 78 y el peso 6 de esta arista.
     10 + 6 = 16
043. Conservamos la distancia de 666. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     16 ≥ 13   →   conservar
044. Fijamos el nodo 1. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[1] = 13
045. Exploramos 1 → 0. Sumamos la distancia hasta 1 y el peso 2 de esta arista.
     13 + 2 = 15
046. Mejor camino hacia 0. La distancia pasa de ∞ a 15. Guardamos 1 como su predecesor.
     15 < ∞   →   actualizar
047. Exploramos 1 → 2. Sumamos la distancia hasta 1 y el peso 3 de esta arista.
     13 + 3 = 16
048. Conservamos la distancia de 2. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     16 ≥ 15   →   conservar
049. Exploramos 1 → 7. Sumamos la distancia hasta 1 y el peso 20 de esta arista.
     13 + 20 = 33
050. Mejor camino hacia 7. La distancia pasa de ∞ a 33. Guardamos 1 como su predecesor.
     33 < ∞   →   actualizar
051. Exploramos 1 → 8. Sumamos la distancia hasta 1 y el peso 7 de esta arista.
     13 + 7 = 20
052. Conservamos la distancia de 8. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     20 ≥ 15   →   conservar
053. Exploramos 1 → 10. Sumamos la distancia hasta 1 y el peso 5 de esta arista.
     13 + 5 = 18
054. Mejor camino hacia 10. La distancia pasa de ∞ a 18. Guardamos 1 como su predecesor.
     18 < ∞   →   actualizar
055. El nodo 12 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[12] = 6  ·  definitiva
056. Exploramos 1 → 15. Sumamos la distancia hasta 1 y el peso 8 de esta arista.
     13 + 8 = 21
057. Mejor camino hacia 15. La distancia pasa de ∞ a 21. Guardamos 1 como su predecesor.
     21 < ∞   →   actualizar
058. Exploramos 1 → 23. Sumamos la distancia hasta 1 y el peso 7 de esta arista.
     13 + 7 = 20
059. Conservamos la distancia de 23. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     20 ≥ 14   →   conservar
060. Fijamos el nodo 666. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[666] = 13
061. El nodo 12 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[12] = 6  ·  definitiva
062. El nodo 13 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[13] = 0  ·  definitiva
063. Exploramos 666 → 27. Sumamos la distancia hasta 666 y el peso 1 de esta arista.
     13 + 1 = 14
064. Mejor camino hacia 27. La distancia pasa de ∞ a 14. Guardamos 666 como su predecesor.
     14 < ∞   →   actualizar
065. El nodo 78 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[78] = 10  ·  definitiva
066. Fijamos el nodo 23. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[23] = 14
067. El nodo 1 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[1] = 13  ·  definitiva
068. Exploramos 23 → 2. Sumamos la distancia hasta 23 y el peso 3 de esta arista.
     14 + 3 = 17
069. Conservamos la distancia de 2. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     17 ≥ 15   →   conservar
070. El nodo 16 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[16] = 3  ·  definitiva
071. Fijamos el nodo 27. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[27] = 14
072. Exploramos 27 → 4. Sumamos la distancia hasta 27 y el peso 3 de esta arista.
     14 + 3 = 17
073. Conservamos la distancia de 4. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     17 ≥ 15   →   conservar
074. Exploramos 27 → 10. Sumamos la distancia hasta 27 y el peso 9 de esta arista.
     14 + 9 = 23
075. Conservamos la distancia de 10. Este camino no mejora el que ya conocemos. El predecesor se conserva.
     23 ≥ 18   →   conservar
076. El nodo 666 ya está fijado. Esta conexión no puede mejorar una distancia definitiva.
     d[666] = 13  ·  definitiva
077. Fijamos el nodo 69. Es el candidato con menor distancia. Su distancia ya es definitiva.
     d[69] = 14
078. Conectamos el camino mínimo. La ruta se reconstruye con los predecesores y se ilumina desde el origen.
     13 → 16
079. Conectamos el camino mínimo. La ruta se reconstruye con los predecesores y se ilumina desde el origen.
     13 → 16 → 17
080. Conectamos el camino mínimo. La ruta se reconstruye con los predecesores y se ilumina desde el origen.
     13 → 16 → 17 → 69
081. Llegamos por el camino mínimo. De 13 a 69, con costo total 14 y 3 conexiones.
     3 + 7 + 4 = 14
