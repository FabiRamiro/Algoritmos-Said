"""Contraste independiente con Bellman–Ford y reconstrucción de caminos."""
from pathlib import Path
from math import inf
import random
import unittest
from algoritmo import Grafo,Arista,floyd_warshall


def referencia(g,origen):
    # Bellman–Ford independiente: no usa matrices ni la recurrencia de Floyd.
    d={n:inf for n in g.posiciones}; d[origen]=0
    for _ in range(len(d)-1):
        for a in g.arcos:
            if d[a.u]<inf and d[a.u]+a.peso<d[a.v]: d[a.v]=d[a.u]+a.peso
    afectados={a.v for a in g.arcos if d[a.u]<inf and d[a.u]+a.peso<d[a.v]}
    for _ in range(len(d)):
        afectados.update(a.v for a in g.arcos if a.u in afectados)
    return {n:-inf if n in afectados else valor for n,valor in d.items()}


class FloydTests(unittest.TestCase):
    def grafo(self,aristas,n=4,dirigido=True):
        return Grafo({i:(i*100,0) for i in range(n)},
                     [Arista(str(i),u,v,w) for i,(u,v,w) in enumerate(aristas)],0,n-1,dirigido)

    def comprobar(self,g):
        r=floyd_warshall(g); final=r.pasos[-1]
        for i,u in enumerate(r.nodos):
            esperado=referencia(g,u)
            for j,v in enumerate(r.nodos):
                self.assertEqual(final.distancias[i][j],esperado[v],(u,v))
                ruta,aristas=r.ruta(final,u,v)
                if esperado[v] in (inf,-inf):
                    self.assertEqual(ruta,())
                    self.assertIsNone(final.recorridos[i][j])
                else:
                    self.assertEqual((ruta[0],ruta[-1]),(u,v))
                    self.assertEqual(sum(g.por_id[e].peso for e in aristas),esperado[v])
                    for a,b,eid in zip(ruta,ruta[1:],aristas):
                        self.assertTrue(any(a==e.u and b==e.v and eid==e.arista for e in g.arcos))
        return r

    def test_negativos_sin_ciclo_y_matriz_de_intermedios(self):
        g=self.grafo([(0,1,4),(0,2,8),(1,2,-3),(2,3,2)])
        r=self.comprobar(g)
        self.assertEqual(r.pasos[-1].distancias[0][3],3)
        self.assertEqual(r.ruta(r.pasos[-1],0,3)[0],(0,1,2,3))
        self.assertEqual(r.pasos[2].recorridos[0][2],1)
        self.assertEqual(r.pasos[0].distancias[0][2],8)

    def test_ciclo_no_contamina_otra_componente(self):
        g=self.grafo([(0,1,3),(2,3,-2),(3,2,1)])
        r=self.comprobar(g)
        self.assertEqual(r.pasos[-1].distancias[0][1],3)
        self.assertEqual(r.pasos[-1].distancias[0][2],inf)
        self.assertEqual(r.pasos[-1].distancias[2][3],-inf)

    def test_propagacion_directed_no_afecta_todos_los_pares(self):
        self.comprobar(self.grafo([(0,1,1),(1,2,-2),(2,1,1),(2,3,5)],n=5))

    def test_paralelas_empates_ceros_y_bucles(self):
        self.comprobar(self.grafo([(0,1,9),(0,1,2),(0,2,2),(1,2,0),(2,1,0),(2,3,1)]))
        self.comprobar(self.grafo([],1))
        self.comprobar(self.grafo([(0,0,-2)],1))
        self.comprobar(self.grafo([(0,0,5)],1))

    def test_una_captura_por_k_incluso_sin_cambios(self):
        r=floyd_warshall(self.grafo([],3))
        self.assertEqual([p.tipo for p in r.pasos],['inicio','iteracion','iteracion','iteracion','fin'])
        self.assertEqual([p.k for p in r.pasos[1:-1]],[0,1,2])
        self.assertTrue(all(not p.cambios for p in r.pasos))

    def test_recurrencia_de_cada_cambio_y_estado_no_mutado(self):
        r=floyd_warshall(self.grafo([(0,1,2),(1,2,-1),(2,3,4)]))
        for anterior,paso in zip(r.pasos,r.pasos[1:-1]):
            k=r.nodos.index(paso.k)
            for c in paso.cambios:
                self.assertEqual(c.anterior,anterior.distancias[c.i][c.j])
                self.assertEqual(c.nuevo,anterior.distancias[c.i][k]+anterior.distancias[k][c.j])
                self.assertEqual(paso.distancias[c.i][c.j],c.nuevo)
                self.assertEqual(paso.recorridos[c.i][c.j],paso.k)
        self.assertEqual(r.pasos[0].distancias[0][3],inf)

    def test_grafos_aleatorios(self):
        rng=random.Random(5901)
        for caso in range(70):
            n=rng.randrange(1,8)
            edges=[(u,v,rng.randrange(-4,9)) for u in range(n) for v in range(n) if rng.random()<.2]
            with self.subTest(caso=caso): self.comprobar(self.grafo(edges,n,caso%3!=0))

    def test_grafos_entregados_y_ocho_pesos_exactos(self):
        base=Path(__file__).resolve().parent
        esperados={frozenset((24,11)):-7,frozenset((21,11)):-2,frozenset((6,9)):-7,
                   frozenset((5,20)):-2,frozenset((3,69)):-6,frozenset((666,13)):-777,
                   frozenset((9,10)):-3,frozenset((23,16)):-11}
        for carpeta in (base,base.parent/'BellmanFord_13_69'):
            g=Grafo.cargar(carpeta/'grafo.json')
            self.assertFalse(g.dirigido)
            self.assertEqual({frozenset((a.u,a.v)):a.peso for a in g.aristas if a.peso<0},esperados)
        r=self.comprobar(g)
        self.assertEqual(len(r.pasos),32)
        self.assertEqual(len(r.pasos[-1].afectados),900)
        positivo=Grafo.cargar(base.parent/'Dijkstra_13_69'/'grafo.json')
        self.assertTrue(all(a.peso>=0 for a in positivo.aristas))
        self.comprobar(positivo)


if __name__=='__main__': unittest.main()
