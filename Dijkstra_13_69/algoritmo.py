"""Dijkstra desde cero: heapq, listas de adyacencia e instantáneas independientes.

No depende de Qt ni de ninguna biblioteca de grafos. Las aristas paralelas
conservan su identidad, para explicar cuál se examina y cuál forma la ruta.
"""
from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf, isfinite
import json
from pathlib import Path


def numero(value: float) -> str:
    if value == inf:
        return "∞"
    return str(int(value)) if value == int(value) else f"{value:.6g}"


@dataclass(frozen=True)
class Arista:
    id: str
    u: int
    v: int
    peso: float
    curva: float = 0
    etiqueta_t: float = .5
    dudosa: bool = False
    nota: str = ""


@dataclass
class Grafo:
    posiciones: dict[int, tuple[float, float]]
    aristas: list[Arista]
    origen: int = 13
    destino: int = 69

    def __post_init__(self):
        self.adyacencia = {n: [] for n in self.posiciones}
        self.por_id = {}
        for a in self.aristas:
            if a.id in self.por_id:
                raise ValueError(f"Identificador de arista repetido: {a.id}")
            if a.u not in self.posiciones or a.v not in self.posiciones:
                raise ValueError(f"Extremo inexistente en la arista {a.id}")
            if not isfinite(a.peso) or a.peso < 0:
                raise ValueError("Dijkstra requiere pesos finitos, mayores o iguales a cero.")
            self.por_id[a.id] = a
            self.adyacencia[a.u].append((a.v, a.peso, a.id))
            self.adyacencia[a.v].append((a.u, a.peso, a.id))
        for vecinos in self.adyacencia.values():
            vecinos.sort(key=lambda item: (item[0], item[1], item[2]))

    @classmethod
    def cargar(cls, ruta: Path):
        data = json.loads(ruta.read_text(encoding="utf-8"))
        if data.get("directed", False):
            raise ValueError("Esta transcripción representa un grafo no dirigido.")
        posiciones = {n["id"]: (n["x"], n["y"]) for n in data["nodes"]}
        if len(posiciones) != len(data["nodes"]):
            raise ValueError("Hay identificadores de nodo repetidos.")
        aristas = [Arista(e["id"], e["u"], e["v"], float(e["weight"]),
                          e.get("curve", 0), e.get("label_t", .5),
                          e.get("uncertain", False), e.get("note", ""))
                   for e in data["edges"]]
        return cls(posiciones, aristas, data.get("source", 13), data.get("target", 69))


@dataclass(frozen=True)
class Paso:
    tipo: str
    titulo: str
    texto: str
    formula: str
    distancias: dict[int, float]
    anteriores: dict[int, tuple[int, str]]
    fijos: frozenset[int]
    orden: tuple[int, ...]
    frontera: tuple[tuple[float, int], ...]
    actual: int | None = None
    vecino: int | None = None
    arista: str | None = None
    ruta: tuple[int, ...] = ()
    aristas_ruta: tuple[str, ...] = ()
    linea: int = 0


@dataclass
class Recorrido:
    pasos: list[Paso]
    ruta: list[int]
    aristas_ruta: list[str]
    costo: float
    origen: int
    destino: int

    def resumen(self) -> str:
        final = self.pasos[-1]
        lineas = [f"# Dijkstra: {self.origen} → {self.destino}", "",
                  f"Ruta: {' → '.join(map(str, self.ruta)) or 'No existe'}",
                  f"Costo: {numero(self.costo)}", "",
                  "Orden de nodos fijados: " + " → ".join(map(str, final.orden)), "",
                  "El algoritmo se detiene al fijar el destino. Las otras distancias",
                  "solo son definitivas si el nodo está fijado.", "", "## Secuencia", ""]
        for i, p in enumerate(self.pasos, 1):
            lineas += [f"{i:03d}. {p.titulo}. {p.texto}"]
            if p.formula:
                lineas += [f"     {p.formula}"]
        return "\n".join(lineas) + "\n"


def dijkstra(grafo: Grafo, origen: int, destino: int) -> Recorrido:
    """Genera una instantánea para cada decisión; nunca recalcula al retroceder.

    Empates: primero menor distancia, después menor identificador de nodo.
    En una igualdad de costo se conserva el predecesor que ya existía.
    Se detiene cuando el destino sale de la cola con su distancia mínima.
    """
    if origen not in grafo.posiciones or destino not in grafo.posiciones:
        raise ValueError("El origen y el destino deben existir en el grafo.")
    dist = {n: inf for n in grafo.posiciones}
    prev: dict[int, tuple[int, str]] = {}
    fijos: set[int] = set()
    orden: list[int] = []
    cola = []
    pasos: list[Paso] = []
    ruta: list[int] = []
    ruta_aristas: list[str] = []

    def registrar(tipo, titulo, texto, formula="", actual=None, vecino=None,
                  arista=None, linea=0, ruta_actual=(), aristas_actuales=()):
        # Frontera lógica: una entrada por nodo. Los registros obsoletos del
        # heap se descartan al extraerlos, y no se muestran como candidatos.
        frontera = tuple(sorted((d, n) for n, d in dist.items()
                                if n not in fijos and d < inf))
        pasos.append(Paso(tipo, titulo, texto, formula, dict(dist), dict(prev),
                          frozenset(fijos), tuple(orden), frontera, actual, vecino,
                          arista, tuple(ruta_actual), tuple(aristas_actuales), linea))

    registrar("inicio", "Preparamos las distancias",
              "Todos los nodos comienzan en infinito: todavía no conocemos un camino hacia ellos.",
              "distancias = ∞  ·  predecesores = vacíos", linea=0)
    dist[origen] = 0.0
    registrar("origen", f"Nos situamos en el nodo {origen}",
              "Llegar del origen a sí mismo no cuesta nada. Solo su distancia cambia a cero.",
              f"d[{origen}] = 0", actual=origen, linea=0)
    heappush(cola, (0.0, origen))
    registrar("encolar", f"Añadimos {origen} a la cola",
              "La cola de prioridad permite extraer primero la menor distancia guardada.",
              f"encolar(0, {origen})", actual=origen, linea=8)
    while cola:
        registrar("elegir", "Buscamos el menor candidato",
                  "La cola ordena por distancia y, en caso de empate, por número de nodo.",
                  f"Primera entrada: nodo {cola[0][1]}, distancia {numero(cola[0][0])}", linea=1)
        du, u = heappop(cola)
        registrar("extraer", f"Extraemos el nodo {u}",
                  "Retiramos la primera entrada de la cola. Aún debemos comprobar si sigue vigente.",
                  f"distancia extraída = {numero(du)}", actual=u, linea=2)
        if u in fijos or du != dist[u]:
            registrar("obsoleto", f"Descartamos la entrada antigua de {u}",
                      "El nodo ya está fijado o esta entrada fue superada por un camino más corto.",
                      f"extraída = {numero(du)}  ·  registrada = {numero(dist[u])}", actual=u, linea=2)
            continue
        registrar("validar", f"La entrada de {u} es válida",
                  "Su distancia coincide con la registrada y el nodo todavía no está fijado.",
                  f"{numero(du)} = d[{u}]  ·  no fijado", actual=u, linea=2)
        fijos.add(u)
        orden.append(u)
        registrar("fijar", f"Fijamos el nodo {u}",
                  "Es el candidato con menor distancia. Su distancia ya es definitiva.",
                  f"d[{u}] = {numero(du)}", actual=u, linea=2)
        registrar("destino", f"¿El nodo {u} es el destino?",
                  "Sí. Su distancia mínima es definitiva; podemos reconstruir la ruta."
                  if u == destino else "No. Debemos revisar sus conexiones antes de elegir otro nodo.",
                  f"{u} {'=' if u == destino else '≠'} {destino}", actual=u, linea=3)
        if u == destino:
            break
        registrar("vecinos", f"Observamos las conexiones de {u}",
                  "Las revisamos una por una, incluyendo las aristas paralelas y los vecinos fijados.",
                  f"{len(grafo.adyacencia[u])} conexiones", actual=u, linea=4)
        for v, peso, eid in grafo.adyacencia[u]:
            registrar("vecino", f"Miramos el vecino {v}",
                      f"Estamos en {u} y dirigimos la atención al nodo {v}.",
                      f"actual = {u}  ·  vecino = {v}", actual=u, vecino=v, linea=4)
            registrar("arista", f"Seguimos la arista {u} → {v}",
                      "Identificamos la conexión y leemos su peso; aún no cambiamos distancias.",
                      f"{eid}: peso = {numero(peso)}", u, v, eid, 4)
            registrar("comprobar", f"¿El vecino {v} ya está fijado?",
                      "Sí. Su distancia ya es definitiva." if v in fijos
                      else "No. Podemos calcular cuánto costaría llegar por esta conexión.",
                      f"{v}: {'fijado' if v in fijos else 'pendiente'}", u, v, eid, 4)
            if v in fijos:
                registrar("omitir", f"El nodo {v} ya está fijado",
                          "Esta conexión no puede mejorar una distancia definitiva.",
                          f"d[{v}] = {numero(dist[v])}  ·  definitiva", u, v, eid, 4)
                registrar("volver", f"Volvemos al nodo {u}",
                          "Terminamos esta conexión y continuamos la revisión.", actual=u, linea=4)
                continue
            candidato = du + peso
            anterior = dist[v]
            registrar("examinar", f"Exploramos {u} → {v}",
                      f"Sumamos la distancia hasta {u} y el peso {numero(peso)} de esta arista.",
                      f"{numero(du)} + {numero(peso)} = {numero(candidato)}", u, v, eid, 5)
            registrar("comparar", f"Comparamos las dos distancias de {v}",
                      "Solo una distancia estrictamente menor reemplaza a la registrada. Un empate conserva el camino anterior.",
                      f"¿{numero(candidato)} < {numero(anterior)}?  {'Sí' if candidato < anterior else 'No'}", u, v, eid, 6)
            if candidato < anterior:
                dist[v] = candidato
                registrar("mejorar", f"Mejor camino hacia {v}",
                          f"La distancia pasa de {numero(anterior)} a {numero(candidato)}. El siguiente paso guardará el predecesor.",
                          f"{numero(candidato)} < {numero(anterior)}   →   actualizar", u, v, eid, 7)
                prev[v] = (u, eid)
                registrar("predecesor", f"Guardamos de dónde llegamos a {v}",
                          f"Registramos el nodo {u} y la arista {eid}. Esta información permitirá reconstruir la ruta.",
                          f"previo[{v}] = {u}  ·  arista = {eid}", u, v, eid, 8)
                heappush(cola, (candidato, v))
                registrar("encolar", f"Añadimos el candidato {v} a la cola",
                          "Guardamos la nueva distancia. Si hay una entrada antigua, se descartará cuando salga de la cola.",
                          f"encolar({numero(candidato)}, {v})", u, v, eid, 8)
            else:
                registrar("mantener", f"Conservamos la distancia de {v}",
                          "Este camino no mejora el que ya conocemos. El predecesor se conserva.",
                          f"{numero(candidato)} ≥ {numero(anterior)}   →   conservar", u, v, eid, 6)
            registrar("volver", f"Volvemos al nodo {u}",
                      "La decisión sobre esta arista terminó. Continuamos con la siguiente conexión.", actual=u, linea=4)
        registrar("cerrar", f"Terminamos las conexiones de {u}",
                  "Ya revisamos todos sus vecinos. Volvemos a buscar la menor distancia en la cola.", actual=u, linea=1)

    if destino in fijos:
        n = destino
        ruta = [n]
        registrar("retroceder", f"Reconstruimos desde el destino {n}",
                  "Seguiremos los predecesores hacia atrás hasta llegar al origen.",
                  str(n), actual=n, linea=9, ruta_actual=ruta)
        while n != origen:
            hijo = n
            n, eid = prev[n]
            ruta.append(n)
            ruta_aristas.append(eid)
            registrar("retroceder", f"El predecesor de {hijo} es {n}",
                      "Añadimos esta conexión al camino. Estamos leyendo la ruta del destino hacia el origen.",
                      f"previo[{hijo}] = {n}", hijo, n, eid, 9, ruta, ruta_aristas)
        ruta.reverse()
        ruta_aristas.reverse()
        for k in range(1, len(ruta)):
            registrar("ruta", "Conectamos el camino mínimo",
                      "La ruta se reconstruye con los predecesores y se ilumina desde el origen.",
                      " → ".join(map(str, ruta[:k+1])), ruta[k-1], ruta[k], ruta_aristas[k-1], 9,
                      ruta[:k+1], ruta_aristas[:k])
        registrar("fin", "Llegamos por el camino mínimo",
                  f"De {origen} a {destino}, con costo total {numero(dist[destino])} y "
                  f"{len(ruta_aristas)} conexiones.",
                  " + ".join(numero(grafo.por_id[e].peso) for e in ruta_aristas)
                  + (" = " if ruta_aristas else "") + numero(dist[destino]),
                  actual=destino, linea=10, ruta_actual=ruta, aristas_actuales=ruta_aristas)
    else:
        registrar("sin_ruta", "No hay una ruta disponible",
                  "La frontera quedó vacía antes de alcanzar el destino.", linea=10)
    return Recorrido(pasos, ruta, ruta_aristas, dist[destino], origen, destino)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dijkstra sin interfaz y sin NetworkX")
    parser.add_argument("--origen", type=int, default=13)
    parser.add_argument("--destino", type=int, default=69)
    args = parser.parse_args()
    g = Grafo.cargar(Path(__file__).with_name("grafo.json"))
    print(dijkstra(g, args.origen, args.destino).resumen())
