"""Bellman–Ford didáctico, sin bibliotecas de grafos ni dependencia de Qt.

Una pasada recorre todos los arcos en un orden estable. Los cambios de
distancia se usan inmediatamente en los siguientes arcos de la misma pasada.
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
        return {"title":"Bellman–Ford · Grafo confirmado", "directed":self.dirigido,
                "source":self.origen,"target":self.destino,
                "nodes":[{"id":n,"x":p[0],"y":p[1]} for n,p in self.posiciones.items()],
                "edges":[{"id":a.id,"u":a.u,"v":a.v,"weight":a.peso,
                          "curve":a.curva,"label_t":a.etiqueta_t} for a in self.aristas]}


@dataclass(frozen=True, slots=True)
class Paso:
    tipo: str
    titulo: str
    texto: str
    distancias: dict[int,float]
    anteriores: dict[int,tuple[int,str]]
    pasada: int = 0
    indice_arco: int | None = None
    actual: int | None = None
    vecino: int | None = None
    arista: str | None = None
    pregunta: str = "—"
    comparacion: str = "—"
    respuesta: str = "PENDIENTE"
    proceso: str = "—"
    cambios: int = 0
    ruta: tuple[int,...] = ()
    aristas_ruta: tuple[str,...] = ()
    afectados: frozenset[int] = frozenset()

    @property
    def codigo(self):
        if self.tipo in ("inicio","origen"):
            return "INICIO"
        if self.tipo.startswith("verificar") or self.tipo == "ciclo":
            return f"CONTROL.{(self.indice_arco or 0)+1:03d}" if self.indice_arco is not None else "CONTROL"
        if self.indice_arco is not None:
            return f"{self.pasada}.{self.indice_arco+1:03d}"
        return f"PASADA {self.pasada}" if self.tipo in ("pasada","cierre") else "RESULTADO"


@dataclass
class Recorrido:
    pasos: list[Paso]
    ruta: list[int]
    aristas_ruta: list[str]
    costo: float
    origen: int
    destino: int
    pasadas: int
    afectados: frozenset[int]


def bellman_ford(grafo: Grafo, origen: int, destino: int, detener_sin_cambios=True) -> Recorrido:
    """Registra cada relajación y comprueba ciclos negativos alcanzables.

    Nunca fija nodos ni termina al descubrir el destino. Un costo igual
    conserva el predecesor anterior. −∞ solo se asigna a nodos alcanzables
    desde un ciclo negativo al que se pueda llegar desde el origen.
    """
    if origen not in grafo.posiciones or destino not in grafo.posiciones:
        raise ValueError("El origen y el destino deben existir.")
    dist = {n:inf for n in grafo.posiciones}
    prev = {}
    pasos = []
    cambios, pasada = 0, 0

    def registrar(tipo,titulo,texto,indice=None,pregunta="—",comparacion="—",respuesta="PENDIENTE",proceso="—",ruta=(),aristas=(),afectados=frozenset()):
        arco = grafo.arcos[indice] if indice is not None else None
        pasos.append(Paso(tipo,titulo,texto,dict(dist),dict(prev),pasada,indice,
                          arco.u if arco else None,arco.v if arco else None,arco.arista if arco else None,
                          pregunta,comparacion,respuesta,proceso,cambios,tuple(ruta),tuple(aristas),afectados))

    registrar("inicio","Inicializamos los arreglos","Cada distancia comienza en infinito y cada predecesor queda vacío.",
              proceso="V = nodos ordenados · d[V] = ∞ · Π[V] = —")
    dist[origen] = 0.0
    registrar("origen",f"Establecemos el origen {origen}","La distancia del origen a sí mismo es cero.",
              respuesta="INICIALIZADO",proceso=f"d[{origen}] = 0; Π[{origen}] = —")
    for pasada in range(1,len(grafo.posiciones)):
        cambios = 0
        registrar("pasada",f"Comienza la pasada {pasada}",
                  f"Recorreremos los {len(grafo.arcos)} arcos en el mismo orden. Las mejoras se usan de inmediato.",
                  proceso=f"Pasada {pasada} de un máximo de {len(grafo.posiciones)-1}")
        for i,a in enumerate(grafo.arcos):
            du, dv = dist[a.u], dist[a.v]
            candidato = du+a.peso if du < inf else inf
            pregunta = f"¿d[{a.v}] > d[{a.u}] + w({a.u}, {a.v})?"
            comparacion = f"¿{numero(dv)} > {numero(du)} + ({numero(a.peso)}) = {numero(candidato)}?"
            def evento(tipo,titulo,texto,respuesta="PENDIENTE",proceso="—"):
                registrar(tipo,titulo,texto,i,pregunta,comparacion,respuesta,proceso)
            evento("arco",f"Seleccionamos el arco ({a.u}, {a.v})",
                   f"Arco {i+1} de {len(grafo.arcos)} · {a.arista} · peso {numero(a.peso)}.",
                   proceso=f"Leer d[{a.u}] y d[{a.v}] antes de relajar")
            evento("alcance",f"¿Podemos partir de {a.u}?",
                   "Primero comprobamos si el extremo de salida tiene distancia finita.",
                   proceso=f"d[{a.u}] = {numero(du)}")
            if du == inf:
                evento("omitir",f"El nodo {a.u} aún no es alcanzable",
                       "No se puede mejorar otra distancia desde infinito. Continuamos con el siguiente arco.",
                       "NO APLICA",f"d[{a.v}] = {numero(dv)}; Π[{a.v}] no cambia")
                continue
            evento("calcular",f"Calculamos llegar a {a.v} desde {a.u}",
                   "Sumamos la distancia al extremo de salida y el peso de este arco.",
                   proceso=f"candidata = {numero(du)} + ({numero(a.peso)}) = {numero(candidato)}")
            evento("comparar",f"Comparamos la distancia de {a.v}",
                   "La pregunta usa los valores anteriores a la relajación. Solo una mejora estricta cambia el arreglo.",
                   proceso=f"Antes: d[{a.v}] = {numero(dv)}; candidata = {numero(candidato)}")
            if candidato < dv:
                evento("decision",f"Sí: encontramos una distancia menor para {a.v}",
                       "La condición se cumple. A continuación actualizaremos la distancia y su predecesor.",
                       "SÍ",f"Se aplicará d[{a.v}] ← {numero(candidato)}; Π[{a.v}] ← {a.u}")
                dist[a.v] = candidato
                cambios += 1
                evento("actualizar",f"Actualizamos d[{a.v}]",
                       "El arreglo de distancias ya contiene la mejora; el predecesor se guarda en el siguiente micro paso.",
                       "SÍ",f"d[{a.v}]: {numero(dv)} → {numero(candidato)}")
                prev[a.v] = (a.u,a.arista)
                evento("predecesor",f"Guardamos Π[{a.v}] = {a.u}",
                       "Guardamos también la identidad de la arista para distinguir conexiones paralelas.",
                       "SÍ",f"d[{a.v}] = {numero(candidato)}; Π[{a.v}] = {a.u} ({a.arista})")
            else:
                evento("mantener",f"No cambiamos d[{a.v}]",
                       "El nuevo costo es mayor o igual al que ya conocemos. La distancia y el predecesor se conservan.",
                       "NO",f"d[{a.v}] = {numero(dv)}; Π[{a.v}] no cambia")
        registrar("cierre",f"Termina la pasada {pasada}",
                  f"Se produjeron {cambios} mejoras en esta pasada.",respuesta="SIN CAMBIOS" if not cambios else "CONTINUAR",
                  proceso="No hubo mejoras: las distancias alcanzables convergieron." if not cambios
                  else "Una distancia todavía puede mejorar en la siguiente pasada.")
        if not cambios and detener_sin_cambios:
            break

    # Una revisión adicional no modifica las distancias mientras busca evidencia.
    semillas = set()
    registrar("verificar","Comprobamos ciclos negativos",
              "Si aún puede relajarse un arco alcanzable tras la búsqueda, existe un ciclo de costo negativo alcanzable.",
              proceso="Revisar todos los arcos una vez más, sin actualizar d ni Π")
    for i,a in enumerate(grafo.arcos):
        candidato = dist[a.u]+a.peso if dist[a.u] < inf else inf
        mejora = dist[a.u] < inf and candidato < dist[a.v]
        if mejora:
            semillas.add(a.v)
        registrar("verificar_arco",f"Control del arco ({a.u}, {a.v})",
                  "Esta comparación pertenece al control final de ciclos negativos.",i,
                  f"¿d[{a.v}] > d[{a.u}] + w({a.u}, {a.v})?",
                  f"¿{numero(dist[a.v])} > {numero(dist[a.u])} + ({numero(a.peso)}) = {numero(candidato)}?",
                  "SÍ" if mejora else "NO" if dist[a.u] < inf else "NO APLICA",
                  "Hay evidencia de un ciclo negativo alcanzable." if mejora else "No se modifica d ni Π en esta revisión.")
    afectados = set(semillas)
    pendientes = list(semillas)
    while pendientes:
        for v in grafo.adyacencia[pendientes.pop()]:
            if v not in afectados:
                afectados.add(v)
                pendientes.append(v)
    afectados = frozenset(afectados)
    if afectados:
        # En un grafo no dirigido podemos mostrar una evidencia concreta:
        # recorrer una arista negativa y regresar por ella reduce el costo.
        if not grafo.dirigido:
            indices = {(a.arista,a.u,a.v):i for i,a in enumerate(grafo.arcos)}
            for a in grafo.aristas:
                if a.peso >= 0 or dist[a.u] == inf:
                    continue
                ruta_ciclo = (a.u,a.v,a.u) if a.u != a.v else (a.u,a.u)
                costo_ciclo = a.peso * (2 if a.u != a.v else 1)
                for u,v in ((a.u,a.v),(a.v,a.u)) if a.u != a.v else ((a.u,a.u),):
                    registrar("verificar_ciclo",f"Ciclo negativo: {' → '.join(map(str,ruta_ciclo))}",
                              "Ambos sentidos pertenecen a la misma arista no dirigida. Repetir este recorrido disminuye el costo sin límite.",
                              indices[(a.id,u,v)],pregunta="¿El costo total del recorrido cerrado es negativo?",
                              comparacion=f"{numero(costo_ciclo)} < 0",respuesta="SÍ · CICLO NEGATIVO",
                              proceso=f"{' → '.join(map(str,ruta_ciclo))} · costo {numero(costo_ciclo)}",
                              ruta=ruta_ciclo,aristas=(a.id,))
        for n in afectados:
            dist[n] = -inf
            prev.pop(n,None)
        registrar("ciclo","Detectamos un ciclo negativo alcanzable",
                  "Los nodos afectados no tienen un costo mínimo finito: se puede disminuir indefinidamente.",
                  respuesta="CICLO NEGATIVO",proceso="d = −∞ para: " + ", ".join(map(str,sorted(afectados))),afectados=afectados)

    ruta, ruta_aristas = [], []
    if dist[destino] not in (inf,-inf):
        n = destino
        ruta = [n]
        registrar("ruta",f"Reconstruimos desde {destino}","Seguimos los predecesores hacia el origen.",
                  respuesta="RUTA",proceso=str(n),ruta=ruta,afectados=afectados)
        while n != origen:
            if len(ruta) > len(grafo.posiciones) or n not in prev:
                raise RuntimeError("Cadena de predecesores inconsistente.")
            hijo = n
            n,eid = prev[n]
            ruta.append(n)
            ruta_aristas.append(eid)
            registrar("ruta",f"Π[{hijo}] = {n}","Añadimos una conexión a la reconstrucción inversa.",
                      respuesta="RUTA",proceso=" ← ".join(map(str,ruta)),ruta=ruta,aristas=ruta_aristas,afectados=afectados)
        ruta.reverse()
        ruta_aristas.reverse()
    titulo = "Camino mínimo encontrado" if ruta else "El destino está afectado por un ciclo negativo" if destino in afectados else "No existe camino al destino"
    registrar("fin",titulo,
              f"Origen {origen} · destino {destino} · costo {numero(dist[destino])}."
              + (" Hay otros nodos afectados por un ciclo negativo." if afectados and destino not in afectados else ""),
              respuesta="SIN MÍNIMO" if destino in afectados else "COMPLETO",
              proceso=" → ".join(map(str,ruta)) if ruta else "No se reconstruye una ruta finita.",
              ruta=ruta,aristas=ruta_aristas,afectados=afectados)
    return Recorrido(pasos,ruta,ruta_aristas,dist[destino],origen,destino,pasada,afectados)
