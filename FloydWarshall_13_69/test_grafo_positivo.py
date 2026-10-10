"""Contrasta los datos actualizados con Dijkstra y un cálculo independiente."""
import heapq
import json
from math import inf, isfinite
from pathlib import Path
import unittest

from algoritmo import Grafo, floyd_warshall


class GrafoPositivoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafo = Grafo.cargar(Path(__file__).with_name('grafo.json'))
        cls.recorrido = floyd_warshall(cls.grafo)

    def test_pesos_coinciden_con_dijkstra(self):
        datos = json.loads((Path(__file__).parent.parent/'Dijkstra_13_69/grafo.json').read_text(encoding='utf-8'))
        esperado = {(e['id'],e['u'],e['v'],e['weight']) for e in datos['edges']}
        self.assertEqual({(a.id,a.u,a.v,a.peso) for a in self.grafo.aristas},esperado)
        self.assertFalse(self.grafo.dirigido)
        self.assertTrue(all(a.peso>0 for a in self.grafo.aristas))

    def test_los_900_pares_contra_dijkstra_independiente(self):
        nodos = self.recorrido.nodos
        final = self.recorrido.pasos[-1]
        vecinos = {n:[] for n in nodos}
        for a in self.grafo.arcos:
            vecinos[a.u].append((a.v,a.peso))
        for i,origen in enumerate(nodos):
            costos = {n:inf for n in nodos}
            costos[origen] = 0
            cola = [(0,origen)]
            while cola:
                costo,u = heapq.heappop(cola)
                if costo!=costos[u]: continue
                for v,peso in vecinos[u]:
                    if costo+peso<costos[v]:
                        costos[v] = costo+peso
                        heapq.heappush(cola,(costos[v],v))
            self.assertEqual(final.distancias[i],tuple(costos[n] for n in nodos))
        self.assertTrue(all(isfinite(v) for fila in final.distancias for v in fila))
        self.assertFalse(final.afectados)
        self.assertEqual(self.recorrido.ruta(final,13,69)[0],(13,16,17,69))
        self.assertEqual(final.distancias[nodos.index(13)][nodos.index(69)],14)


if __name__=='__main__': unittest.main()
