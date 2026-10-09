"""Modelo del grafo: nodos, aristas y arcos; independiente de la interfaz.

Una arista no dirigida produce dos arcos. Las conexiones paralelas conservan
su identidad, y los pesos negativos se aceptan para analizarlos en Floyd.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import inf, isfinite
from pathlib import Path
import json


def numero(valor):
    if valor == inf:
        return "∞"
    if valor == -inf:
        return "−∞"
    return str(int(valor)) if valor == int(valor) else f"{valor:.6g}"


@dataclass(frozen=True, slots=True)
class Arista:
    id: str
    u: int
    v: int
    peso: float
    curva: float = 0
    etiqueta_t: float = .5


@dataclass(frozen=True, slots=True)
class Arco:
    arista: str
    u: int
    v: int
    peso: float


@dataclass
class Grafo:
    posiciones: dict[int, tuple[float, float]]
    aristas: list[Arista]
    origen: int = 13
    destino: int = 69
    dirigido: bool = False

    def __post_init__(self):
        if not self.posiciones:
            raise ValueError("El grafo debe contener al menos un nodo.")
        if any(not all(isfinite(v) for v in xy) for xy in self.posiciones.values()):
            raise ValueError("Las posiciones deben ser finitas.")
        self.por_id = {}
        self.adyacencia = {n: [] for n in self.posiciones}
        arcos = []
        for a in self.aristas:
            if a.id in self.por_id:
                raise ValueError(f"Identificador de arista repetido: {a.id}")
            if a.u not in self.posiciones or a.v not in self.posiciones:
                raise ValueError(f"Extremo inexistente: {a.id}")
            if not isfinite(a.peso) or not isfinite(a.curva) or not 0 <= a.etiqueta_t <= 1:
                raise ValueError("Los pesos y curvas deben ser finitos; label_t debe estar entre 0 y 1.")
            self.por_id[a.id] = a
            arcos.append(Arco(a.id,a.u,a.v,a.peso))
            if not self.dirigido and a.u != a.v:
                arcos.append(Arco(a.id,a.v,a.u,a.peso))
        # Identidad de arista preservada, incluso cuando hay conexiones paralelas.
        self.arcos = tuple(sorted(arcos,key=lambda a:(a.u,a.v,a.arista)))
        for a in self.arcos:
            self.adyacencia[a.u].append(a.v)

    @classmethod
    def cargar(cls,ruta):
        data = json.loads(Path(ruta).read_text(encoding="utf-8-sig"))
        posiciones = {n['id']:(float(n['x']),float(n['y'])) for n in data['nodes']}
        if len(posiciones) != len(data['nodes']):
            raise ValueError("Hay identificadores de nodo repetidos.")
        if any(type(n) is not int for n in posiciones):
            raise ValueError("Los identificadores de nodo deben ser enteros.")
        return cls(posiciones,[Arista(e['id'],e['u'],e['v'],float(e['weight']),
                                     float(e.get('curve',0)),float(e.get('label_t',.5)))
                              for e in data['edges']],data['source'],data['target'],bool(data.get('directed',False)))

    def datos(self):
        return {"title":"Floyd–Warshall · Grafo confirmado", "directed":self.dirigido,
                "source":self.origen,"target":self.destino,
                "nodes":[{"id":n,"x":p[0],"y":p[1]} for n,p in self.posiciones.items()],
                "edges":[{"id":a.id,"u":a.u,"v":a.v,"weight":a.peso,
                          "curve":a.curva,"label_t":a.etiqueta_t} for a in self.aristas]}


