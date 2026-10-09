"""Verificación independiente del algoritmo, incluyendo ciclos negativos."""
from math import inf
from pathlib import Path
import random
import unittest
from algoritmo import Arista,Grafo,bellman_ford


def referencia_floyd(g):
    """Floyd–Warshall permite contrastar todos los destinos de cada origen."""
    nodos=list(g.posiciones)
    d={(u,v):(0.0 if u==v else inf) for u in nodos for v in nodos}
    for a in g.arcos: d[a.u,a.v]=min(d[a.u,a.v],a.peso)
    for k in nodos:
        for u in nodos:
            for v in nodos:
                d[u,v]=min(d[u,v],d[u,k]+d[k,v])
    resultado={}
    for s in nodos:
        resultado[s]={v:(-inf if any(d[s,k]<inf and d[k,k]<0 and d[k,v]<inf for k in nodos)
                         else d[s,v]) for v in nodos}
    return resultado


class AlgoritmoTests(unittest.TestCase):
    def grafo(self,aristas,n=4,dirigido=True):
        return Grafo({i:(i*100,0) for i in range(n)},
                     [Arista(str(k),u,v,w) for k,(u,v,w) in enumerate(aristas)],0,n-1,dirigido)

    def test_pesos_negativos_y_destino_descubierto_antes_del_final(self):
        g=self.grafo([(0,1,1),(0,2,2),(2,1,-5),(1,3,1)])
        r=bellman_ford(g,0,3)
        self.assertEqual(r.costo,-2)
        self.assertEqual(r.ruta,[0,2,1,3])
        self.assertFalse(r.afectados)

    def test_ciclo_negativo_alcanzable_y_propagacion(self):
        g=self.grafo([(0,1,1),(1,2,-2),(2,1,-2),(2,3,4)])
        r=bellman_ford(g,0,3)
        self.assertEqual(r.costo,-inf)
        self.assertEqual(r.afectados,frozenset({1,2,3}))
        self.assertEqual(r.pasos[-1].distancias[0],0)
        self.assertEqual(r.ruta,[])
        self.assertTrue(all(n not in r.pasos[-1].anteriores for n in r.afectados))

    def test_ciclo_negativo_no_alcanzable_no_contamina(self):
        g=self.grafo([(0,3,7),(1,2,-3),(2,1,1)])
        r=bellman_ford(g,0,3)
        self.assertEqual(r.costo,7)
        self.assertFalse(r.afectados)
        self.assertEqual(r.pasos[-1].distancias[1],inf)

    def test_ciclo_alcanzable_que_no_afecta_al_destino(self):
        g=self.grafo([(0,3,7),(0,1,1),(1,2,-3),(2,1,1)])
        r=bellman_ford(g,0,3)
        self.assertEqual(r.costo,7)
        self.assertEqual(r.ruta,[0,3])
        self.assertEqual(r.afectados,frozenset({1,2}))

    def test_arista_no_dirigida_negativa_implica_ciclo(self):
        g=self.grafo([(0,1,-2),(1,2,3),(2,3,8)],dirigido=False)
        r=bellman_ford(g,0,3)
        self.assertEqual(len(g.arcos),6)
        self.assertEqual(r.afectados,frozenset(range(4)))

    def test_dirigido_no_inventa_el_arco_inverso(self):
        g=self.grafo([(0,1,-2)],n=2)
        self.assertEqual(len(g.arcos),1)
        self.assertEqual(bellman_ford(g,1,0).costo,inf)

    def test_paralelas_conservan_identidad(self):
        g=self.grafo([(0,1,5),(0,1,-2)],n=2)
        r=bellman_ford(g,0,1)
        self.assertEqual(r.costo,-2)
        self.assertEqual(r.aristas_ruta,['1'])

    def test_un_nodo_con_y_sin_bucle_negativo(self):
        g=self.grafo([],n=1)
        r=bellman_ford(g,0,0)
        self.assertEqual(r.ruta,[0]); self.assertEqual(r.costo,0)
        self.assertEqual(r.pasadas,0)
        g=self.grafo([(0,0,-1)],n=1)
        self.assertEqual(bellman_ford(g,0,0).costo,-inf)

    def test_desconectado_y_empates(self):
        g=self.grafo([(0,1,0),(0,2,0),(1,2,0)])
        self.assertEqual(bellman_ford(g,0,3).costo,inf)
        r=bellman_ford(g,0,2)
        self.assertEqual(r.ruta,[0,2])

    def test_distancia_y_predecesor_son_micro_pasos_independientes(self):
        g=self.grafo([(0,1,-2)],n=2)
        r=bellman_ford(g,0,1)
        i=next(i for i,p in enumerate(r.pasos) if p.tipo=='actualizar')
        self.assertEqual(r.pasos[i-1].distancias[1],inf)
        self.assertEqual(r.pasos[i].distancias[1],-2)
        self.assertNotIn(1,r.pasos[i].anteriores)
        self.assertEqual(r.pasos[i+1].anteriores[1],(0,'0'))
        self.assertEqual(r.pasos[i].respuesta,'SÍ')
        self.assertIn('∞',r.pasos[i].comparacion)
        self.assertEqual(r.pasos[0].distancias[0],inf)

    def test_orden_de_arcos_y_pasadas_sin_corte_prematuro(self):
        g=self.grafo([(2,3,1),(0,1,2),(1,2,-1)])
        r=bellman_ford(g,0,3,False)
        self.assertEqual(r.pasadas,3)
        for pasada in range(1,4):
            self.assertEqual([p.indice_arco for p in r.pasos if p.pasada==pasada and p.tipo=='arco'],list(range(3)))
        optimizado=bellman_ford(g,0,3,True)
        self.assertEqual(r.pasos[-1].distancias,optimizado.pasos[-1].distancias)
        self.assertLess(optimizado.pasadas,r.pasadas)

    def test_grafo_entregado_contra_floyd_para_todos_los_origenes(self):
        g=Grafo.cargar(Path(__file__).with_name('grafo.json'))
        esperado=referencia_floyd(g)
        for origen in g.posiciones:
            with self.subTest(origen=origen):
                r=bellman_ford(g,origen,g.destino)
                self.assertEqual(r.pasos[-1].distancias,esperado[origen])
                if r.ruta:
                    self.assertEqual(sum(g.por_id[e].peso for e in r.aristas_ruta),r.costo)

    def test_grafos_aleatorios_con_y_sin_ciclos_negativos(self):
        rng=random.Random(8145)
        for caso in range(40):
            n=rng.randrange(2,7)
            aristas=[(u,v,rng.randrange(-5,9)) for u in range(n) for v in range(n) if rng.random()<.22]
            g=self.grafo(aristas,n,dirigido=caso%3!=0)
            esperado=referencia_floyd(g)
            for s in range(n):
                with self.subTest(caso=caso,origen=s):
                    self.assertEqual(bellman_ford(g,s,n-1).pasos[-1].distancias,esperado[s])

    def test_validacion(self):
        for peso in (inf,-inf,float('nan')):
            with self.assertRaises(ValueError): self.grafo([(0,1,peso)],2)
        with self.assertRaises(ValueError): bellman_ford(self.grafo([],2),99,1)
        with self.assertRaises(ValueError): Grafo({},[])


if __name__=='__main__':
    unittest.main()
