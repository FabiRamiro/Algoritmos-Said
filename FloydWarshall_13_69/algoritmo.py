"""Floyd–Warshall para todos los pares, con una instantánea por intermedio.

D[i][j] es el costo; R[i][j] guarda el último intermedio que mejoró el par.
La matriz siguiente permite reconstruir rutas conservando aristas paralelas.
"""
from dataclasses import dataclass
from math import inf
from types import SimpleNamespace
from grafo import Grafo, Arista, numero


@dataclass(frozen=True)
class Cambio:
    i: int
    j: int
    anterior: float
    izquierda: float
    derecha: float
    nuevo: float


@dataclass(frozen=True)
class Paso:
    tipo: str
    titulo: str
    texto: str
    iteracion: int
    k: int | None
    distancias: tuple
    recorridos: tuple
    siguiente: tuple
    cambios: tuple[Cambio, ...] = ()
    afectados: frozenset = frozenset()
    ciclos: tuple = ()


@dataclass
class Recorrido:
    nodos: tuple
    pasos: list[Paso]
    directas: dict

    def ruta(self, paso, origen, destino):
        """Devuelve nodos y aristas; nunca reconstruye un par sin mínimo."""
        i, j = self.nodos.index(origen), self.nodos.index(destino)
        if paso.distancias[i][j] in (inf, -inf) or (i, j) in paso.afectados:
            return (), ()
        ruta, aristas = [origen], []
        actual = i
        while actual != j:
            proximo = paso.siguiente[actual][j]
            if proximo is None or len(ruta) > len(self.nodos):
                return (), ()
            aristas.append(self.directas[actual, proximo])
            ruta.append(self.nodos[proximo])
            actual = proximo
        return tuple(ruta), tuple(aristas)

    def vista_grafo(self, paso, origen, destino):
        """Adapta la fila del origen al mismo lienzo de los otros programas."""
        i = self.nodos.index(origen)
        ruta, aristas = self.ruta(paso, origen, destino)
        return SimpleNamespace(tipo=paso.tipo, ruta=ruta, aristas_ruta=aristas,
                               anteriores={}, arista=None, actual=paso.k, vecino=None,
                               distancias=dict(zip(self.nodos, paso.distancias[i])),
                               afectados=frozenset(self.nodos[j] for a,j in paso.afectados if a==i))


def pares_afectados(d):
    """i → ciclo negativo → j implica que el costo i → j no tiene mínimo."""
    n = len(d)
    ciclos = tuple(k for k in range(n) if d[k][k] < 0)
    afectados = frozenset((i,j) for i in range(n) for j in range(n)
                         if any(d[i][k] < inf and d[k][j] < inf for k in ciclos))
    return ciclos, afectados


def floyd_warshall(grafo: Grafo) -> Recorrido:
    # El orden numérico es estable. No depende del origen elegido para consultar.
    nodos = tuple(sorted(grafo.posiciones))
    indice = {n:i for i,n in enumerate(nodos)}
    n = len(nodos)
    d = [[0.0 if i==j else inf for j in range(n)] for i in range(n)]
    r = [[nodos[j] if i==j else None for j in range(n)] for i in range(n)]
    siguiente = [[i if i==j else None for j in range(n)] for i in range(n)]
    directas = {}
    for arco in grafo.arcos:
        i, j = indice[arco.u], indice[arco.v]
        if arco.peso < d[i][j]:
            d[i][j] = arco.peso
            r[i][j] = nodos[j]
            siguiente[i][j] = j
            directas[i,j] = arco.arista
    pasos = []

    def registrar(tipo, titulo, texto, iteracion, k=None, cambios=()):
        ciclos, afectados = pares_afectados(d)
        pasos.append(Paso(tipo,titulo,texto,iteracion,k,
                          tuple(map(tuple,d)),tuple(map(tuple,r)),tuple(map(tuple,siguiente)),
                          tuple(cambios),afectados,tuple(nodos[c] for c in ciclos)))

    registrar('inicio','Inicializamos todos los pares',
              'Diagonal 0 (salvo bucle negativo), menor conexión directa o ∞. '
              'R contiene el destino directo, el propio nodo o —.',0)
    for k in range(n):
        # Leer la iteración anterior evita mezclar estados: D nueva usa D previa.
        # Es la recurrencia D^k[i,j] = min(D^(k-1)[i,j], D^(k-1)[i,k]+D^(k-1)[k,j]).
        previa = [fila[:] for fila in d]
        saltos_previos = [fila[:] for fila in siguiente]
        cambios = []
        for i in range(n):
            if previa[i][k] == inf:
                continue
            for j in range(n):
                if previa[k][j] == inf:
                    continue
                candidato = previa[i][k] + previa[k][j]
                if candidato < previa[i][j]:
                    cambios.append(Cambio(i,j,previa[i][j],previa[i][k],previa[k][j],candidato))
                    d[i][j] = candidato
                    r[i][j] = nodos[k]
                    siguiente[i][j] = saltos_previos[i][k]
        registrar('iteracion',f'Intermedio k = {nodos[k]}',
                  f'{len(cambios)} pares mejorados. D[i,j] = min(D[i,j], D[i,k] + D[k,j]). '
                  'R guarda k cuando mejora. Los empates conservan el recorrido anterior.',k+1,nodos[k],cambios)

    ciclos, afectados = pares_afectados(d)
    for i,j in afectados:
        d[i][j] = -inf
        r[i][j] = None
        siguiente[i][j] = None
    registrar('fin','Resultado y control de ciclos negativos',
              f'{len(afectados)} pares sin mínimo finito por ciclos negativos: D = −∞, R = —.'
              if afectados else 'No se detectaron ciclos negativos. Las distancias son finales; ∞ indica que no existe camino.',n)
    return Recorrido(nodos,pasos,directas)
