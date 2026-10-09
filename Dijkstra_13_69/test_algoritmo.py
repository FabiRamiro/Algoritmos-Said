"""Verificación independiente. Ejecuta: python -m unittest -v"""
import unittest
from dataclasses import replace
from math import inf
from pathlib import Path

from algoritmo import Arista, Grafo, dijkstra


class DijkstraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = Grafo.cargar(Path(__file__).with_name("grafo.json"))

    def test_ruta_de_la_fotografia(self):
        r = dijkstra(self.g, 13, 69)
        self.assertEqual(r.ruta, [13, 16, 17, 69])
        self.assertEqual(r.costo, 14)
        self.assertEqual([self.g.por_id[e].peso for e in r.aristas_ruta], [3, 7, 4])

    def test_contra_floyd_warshall_para_todos_los_pares(self):
        # Otro algoritmo, basado en programación dinámica, sin heap ni
        # predecesores. Detecta errores en relajaciones y aristas paralelas.
        nodos = list(self.g.posiciones)
        m = {(u,v): (0 if u == v else inf) for u in nodos for v in nodos}
        for a in self.g.aristas:
            m[a.u,a.v] = m[a.v,a.u] = min(m[a.u,a.v], a.peso)
        for k in nodos:
            for u in nodos:
                for v in nodos:
                    m[u,v] = min(m[u,v], m[u,k]+m[k,v])
        for u in nodos:
            for v in nodos:
                r = dijkstra(self.g,u,v)
                self.assertEqual(r.costo,m[u,v],(u,v))
                self.assertEqual(sum(self.g.por_id[e].peso for e in r.aristas_ruta),r.costo)

    def test_pesos_borrosos_no_cambian_esta_ruta(self):
        menor = Grafo(self.g.posiciones,[replace(a,peso=0) if a.dudosa else a for a in self.g.aristas])
        self.assertEqual(dijkstra(menor,13,69).costo,14)
        # La ruta de costo 14 no usa aristas dudosas. Como ponerlas a cero
        # ya es su cota inferior, cualquier peso no negativo mantiene 14.
        r = dijkstra(self.g,13,69)
        self.assertFalse(any(self.g.por_id[e].dudosa for e in r.aristas_ruta))

    def test_paralelas_conservan_identidad(self):
        r = dijkstra(self.g,12,16)
        self.assertEqual(r.costo,3)
        self.assertEqual(len(r.aristas_ruta),1)
        self.assertEqual(self.g.por_id[r.aristas_ruta[0]].peso,3)

    def test_origen_igual_a_destino(self):
        r = dijkstra(self.g,13,13)
        self.assertEqual(r.ruta,[13])
        self.assertEqual(r.costo,0)
        self.assertEqual(r.aristas_ruta,[])

    def test_desconectado(self):
        g = Grafo({1:(0,0),2:(1,1)},[])
        r = dijkstra(g,1,2)
        self.assertEqual(r.costo,inf)
        self.assertEqual(r.ruta,[])
        self.assertEqual(r.pasos[-1].tipo,"sin_ruta")

    def test_cero_y_empates(self):
        g = Grafo({n:(n,0) for n in range(4)},[
            Arista("a",0,1,0),Arista("b",0,2,0),
            Arista("c",1,2,0),Arista("d",1,3,2),Arista("e",2,3,2)])
        r = dijkstra(g,0,3)
        self.assertEqual(r.ruta,[0,1,3])
        self.assertEqual(r.costo,2)

    def test_validacion(self):
        for w in [-1,inf,float("nan")]:
            with self.assertRaises(ValueError):
                Grafo({1:(0,0),2:(1,1)},[Arista("a",1,2,w)])
        with self.assertRaises(ValueError):
            dijkstra(self.g,999,69)

    def test_invariantes_de_las_instantaneas(self):
        r = dijkstra(self.g,13,69)
        fijos = set()
        dist_prev = {n:inf for n in self.g.posiciones}
        for p in r.pasos:
            self.assertTrue(fijos.issubset(p.fijos))
            self.assertEqual(p.frontera,tuple(sorted(p.frontera)))
            self.assertTrue(all(n not in p.fijos for d,n in p.frontera))
            for n,d in p.distancias.items():
                self.assertLessEqual(d,dist_prev[n])
                if n in fijos:
                    self.assertEqual(d,dist_prev[n])
            fijos,dist_prev = set(p.fijos),p.distancias
        self.assertEqual(r.pasos[0].distancias[69],inf)
        self.assertEqual(r.pasos[0].fijos,frozenset())
        self.assertEqual(r.pasos[-1].distancias[69],14)

    def test_micro_pasos_separan_calculo_comparacion_y_cambios(self):
        g = Grafo({1:(0,0), 2:(1,1)}, [Arista("a",1,2,3)])
        r = dijkstra(g,1,2)
        i = next(i for i,p in enumerate(r.pasos) if p.tipo == "examinar")
        bloque = r.pasos[i:i+6]
        self.assertEqual([p.tipo for p in bloque],
                         ["examinar","comparar","mejorar","predecesor","encolar","volver"])
        self.assertEqual(bloque[1].distancias[2],inf)
        self.assertEqual(bloque[2].distancias[2],3)
        self.assertNotIn(2,bloque[2].anteriores)
        self.assertEqual(bloque[3].anteriores[2],(1,"a"))
        for anterior,actual in zip(r.pasos,r.pasos[1:]):
            cambios = sum(anterior.distancias[n] != actual.distancias[n] for n in g.posiciones)
            self.assertLessEqual(cambios,1)
            if cambios:
                self.assertIn(actual.tipo,("origen","mejorar"))

    def test_cada_arista_tiene_atencion_y_comprobacion(self):
        r = dijkstra(self.g,13,69)
        for i,p in enumerate(r.pasos):
            if p.tipo == "arista":
                self.assertEqual(r.pasos[i-1].tipo,"vecino")
                self.assertIsNone(r.pasos[i-1].arista)
                self.assertEqual(r.pasos[i+1].tipo,"comprobar")
                self.assertEqual(r.pasos[i+1].arista,p.arista)
            if p.tipo == "omitir":
                self.assertIn(p.vecino,p.fijos)
                self.assertEqual(r.pasos[i+1].tipo,"volver")

    def test_entrada_obsoleta_es_visible(self):
        g = Grafo({n:(n,0) for n in range(4)},[
            Arista("a",0,1,9), Arista("b",0,2,1),
            Arista("c",2,1,1), Arista("d",1,3,20)])
        r = dijkstra(g,0,3)
        descartes = [p for p in r.pasos if p.tipo == "obsoleto"]
        self.assertEqual(len(descartes),1)
        self.assertEqual(descartes[0].actual,1)
        self.assertEqual(r.costo,22)

    def test_reconstruccion_por_predecesores(self):
        r = dijkstra(self.g,13,69)
        regreso = [p for p in r.pasos if p.tipo == "retroceder"]
        self.assertEqual(regreso[-1].ruta,tuple(reversed(r.ruta)))
        self.assertEqual(regreso[-1].aristas_ruta,tuple(reversed(r.aristas_ruta)))
        self.assertEqual([len(p.ruta) for p in regreso],list(range(1,len(r.ruta)+1)))


if __name__ == "__main__":
    unittest.main()
