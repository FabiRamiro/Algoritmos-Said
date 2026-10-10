"""Una sola ventana para los cuatro algoritmos.

Cada algoritmo conserva su proyecto completo (cálculo, interfaz, capturas y
pruebas). Esta ventana solo los carga la primera vez que se eligen, los aloja
en un QStackedWidget y coordina lo que antes hacía cada ventana por su cuenta:
título, atajos de teclado y pantalla completa.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget)

from cargador import importar_aislado
import diapositivas
from pantalla_carga import completar_capturas

RAIZ = Path(__file__).resolve().parent
tema = importar_aislado(RAIZ / "Dijkstra_13_69", "tema", "tema_comun")
BG, PANEL, LINE, INK, MUTED = tema.BG, tema.PANEL, tema.LINE, tema.INK, tema.MUTED

ESTILO = tema.STYLE + f"""
QPushButton#nav {{ background: transparent; border: none; color: {MUTED}; padding: 7px 14px; font-size: 12px; }}
QPushButton#nav:hover {{ background: #1c1e22; color: {INK}; }}
QPushButton#nav:checked {{ background: #193c2a; color: {tema.GREEN}; font-weight: 600; }}
QFrame#opcion {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 10px; }}
QFrame#opcion:hover {{ border-color: {tema.GREEN}; background: #16171a; }}
"""


@dataclass(frozen=True)
class Algoritmo:
    clave: str
    nombre: str
    carpeta: str
    descripcion: str
    detalle: str


ALGORITMOS = (
    Algoritmo("dijkstra", "Dijkstra", "Dijkstra_13_69",
              "Fija nodos de menor a mayor distancia desde el origen usando una cola de prioridad. "
              "Requiere pesos no negativos.",
              "Un origen  ·  O((V + E) log V)"),
    Algoritmo("bellman-ford", "Bellman-Ford", "BellmanFord_13_69",
              "Relaja todas las aristas en rondas sucesivas. Admite pesos negativos y "
              "detecta ciclos negativos alcanzables.",
              "Un origen  ·  O(V · E)"),
    Algoritmo("floyd-warshall", "Floyd-Warshall", "FloydWarshall_13_69",
              "Programación dinámica sobre una matriz: prueba cada nodo como intermedio "
              "y obtiene las distancias entre todos los pares.",
              "Todos los pares  ·  O(V³)"),
    Algoritmo("astar", "A*", "AStar_13_69",
              "Dijkstra guiado por una heurística h(n) hacia el destino. Ordena por "
              "f = g + h y explora menos nodos.",
              "Origen y destino  ·  heurística admisible"),
)
POR_CLAVE = {a.clave: a for a in ALGORITMOS}


def texto(contenido, size=13, tinta=INK, bold=False):
    w = QLabel(contenido)
    w.setWordWrap(True)
    w.setStyleSheet(f"color: {tinta}; font-size: {size}px; font-weight: {600 if bold else 400};")
    return w


class Opcion(QFrame):
    """Tarjeta de la pantalla de inicio; toda la superficie es clicable."""

    def __init__(self, algoritmo, atajo, al_elegir):
        super().__init__()
        self.setObjectName("opcion")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.al_elegir = lambda: al_elegir(algoritmo.clave)
        v = QVBoxLayout(self)
        v.setContentsMargins(26, 22, 26, 22)
        v.setSpacing(10)
        fila = QHBoxLayout()
        detalle = texto(algoritmo.detalle.upper(), 10, MUTED, True)
        detalle.setWordWrap(False)
        fila.addWidget(detalle)
        fila.addStretch()
        fila.addWidget(texto(atajo, 10, "#6f747e", True))
        v.addLayout(fila)
        v.addWidget(texto(algoritmo.nombre, 24, INK, True))
        v.addWidget(texto(algoritmo.descripcion, 13, MUTED))
        v.addStretch()
        abrir = QPushButton(f"Abrir {algoritmo.nombre}")
        abrir.setObjectName("primary")
        abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        abrir.clicked.connect(self.al_elegir)
        v.addWidget(abrir, 0, Qt.AlignmentFlag.AlignLeft)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.al_elegir()


class Laboratorio(QMainWindow):
    def __init__(self, inicial=None):
        super().__init__()
        tema.aplicar_paleta(QApplication.instance())
        self.setStyleSheet(ESTILO)
        self.vistas: dict[str, QMainWindow] = {}
        self.atajos_vista: dict[str, list[QShortcut]] = {}
        self.actual = "inicio"
        central = QWidget()
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self.construir_barra())
        self.pila = QStackedWidget()
        self.inicio = self.construir_inicio()
        self.pila.addWidget(self.inicio)
        raiz.addWidget(self.pila, 1)
        self.setCentralWidget(central)
        # Atajos propios: cambiar de algoritmo y pantalla completa de la ventana real.
        self.atajos = []
        for tecla, accion in [("Ctrl+0", lambda: self.mostrar("inicio")),
                              ("F11", self.pantalla_completa),
                              ("Escape", self.salir_pantalla_completa)]:
            self.atajos.append(self.atajo(tecla, accion))
        for i, a in enumerate(ALGORITMOS, 1):
            self.atajos.append(self.atajo(f"Ctrl+{i}", lambda clave=a.clave: self.mostrar(clave)))
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1720, screen.width()-40), min(1050, screen.height()-55))
        self.mostrar(inicial or "inicio")

    def atajo(self, tecla, accion):
        s = QShortcut(QKeySequence(tecla), self)
        s.activated.connect(accion)
        return s

    def construir_barra(self):
        barra = QFrame()
        barra.setObjectName("cabecera")
        h = QHBoxLayout(barra)
        h.setContentsMargins(22, 8, 22, 8)
        h.setSpacing(6)
        titulo = QVBoxLayout()
        titulo.setSpacing(0)
        titulo.addWidget(texto("L A B O R A T O R I O", 15, INK, True))
        subtitulo = texto("Caminos mínimos · 13 → 69", 10, MUTED)
        subtitulo.setWordWrap(False)
        titulo.addWidget(subtitulo)
        h.addLayout(titulo)
        h.addStretch()
        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(True)
        self.botones = {}
        for i, (clave, nombre) in enumerate([("inicio", "Inicio")] +
                                            [(a.clave, a.nombre) for a in ALGORITMOS]):
            b = QPushButton(nombre)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(f"Ctrl+{i}")
            b.clicked.connect(lambda _=False, clave=clave: self.mostrar(clave))
            self.grupo.addButton(b)
            self.botones[clave] = b
            h.addWidget(b)
        h.addSpacing(14)
        self.diapositivas_btn = QPushButton("Crear diapositivas")
        self.diapositivas_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.diapositivas_btn.setToolTip("PDF y PowerPoint con las capturas del algoritmo abierto")
        self.diapositivas_btn.clicked.connect(self.crear_diapositivas)
        h.addWidget(self.diapositivas_btn)
        return barra

    def construir_inicio(self):
        pagina = QWidget()
        exterior = QHBoxLayout(pagina)
        exterior.addStretch(1)
        columna = QVBoxLayout()
        columna.setSpacing(14)
        columna.addStretch(1)
        columna.addWidget(texto("ELIGE UN ALGORITMO", 11, MUTED, True))
        columna.addWidget(texto("¿Con qué algoritmo quieres recorrer el grafo?", 30, INK, True))
        columna.addWidget(texto("Los cuatro recorren el grafo de la fotografía, de 13 a 69. Dijkstra y A* usan "
                                "los pesos no negativos; Bellman-Ford y Floyd-Warshall, la versión con pesos "
                                "negativos. Cambia en cualquier momento desde la barra superior o con "
                                "Ctrl+1 … Ctrl+4: cada algoritmo conserva su paso actual al volver.", 14, MUTED))
        columna.addSpacing(18)
        rejilla = QGridLayout()
        rejilla.setSpacing(16)
        self.opciones = []
        for i, a in enumerate(ALGORITMOS):
            tarjeta = Opcion(a, f"CTRL+{i+1}", self.mostrar)
            tarjeta.setMinimumHeight(210)
            self.opciones.append(tarjeta)
            rejilla.addWidget(tarjeta, i // 2, i % 2)
        columna.addLayout(rejilla)
        columna.addStretch(2)
        contenedor = QWidget()
        contenedor.setLayout(columna)
        contenedor.setMaximumWidth(1080)
        exterior.addWidget(contenedor, 6)
        exterior.addStretch(1)
        return pagina

    def cargar(self, clave):
        """Importa el proyecto y aloja su ventana como un widget más."""
        a = POR_CLAVE[clave]
        interfaz = importar_aislado(RAIZ / a.carpeta, "interfaz", f"alg_{clave.replace('-', '_')}")
        vista = interfaz.Ventana()
        vista.setWindowFlags(Qt.WindowType.Widget)
        # La pantalla completa ahora pertenece a la ventana principal.
        propios = []
        for s in vista.findChildren(QShortcut):
            if s.key().toString() in ("F11", "Esc"):
                s.setEnabled(False)
            else:
                propios.append(s)
        vista.windowTitleChanged.connect(lambda _t, clave=clave: self.actualizar_titulo(clave))
        self.pila.addWidget(vista)
        self.vistas[clave] = vista
        self.atajos_vista[clave] = propios
        return vista

    def mostrar(self, clave):
        if clave != "inicio" and clave not in POR_CLAVE:
            raise ValueError(f"Algoritmo desconocido: {clave}")
        anterior = self.vistas.get(self.actual)
        if anterior is not None and clave != self.actual:
            anterior.pausar()
        if clave == "inicio":
            destino = self.inicio
        else:
            destino = self.vistas.get(clave)
            if destino is None:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    destino = self.cargar(clave)
                except Exception as exc:  # El resto de la aplicación sigue disponible.
                    QApplication.restoreOverrideCursor()
                    QMessageBox.critical(self, "No se pudo abrir el algoritmo",
                                         f"{POR_CLAVE[clave].nombre}: {exc}")
                    self.botones[self.actual].setChecked(True)
                    return
                QApplication.restoreOverrideCursor()
        # Solo la vista visible responde a espacio, flechas, Inicio, Fin…
        for otra, atajos in self.atajos_vista.items():
            for s in atajos:
                s.setEnabled(otra == clave)
        self.actual = clave
        self.pila.setCurrentWidget(destino)
        self.botones[clave].setChecked(True)
        self.diapositivas_btn.setEnabled(clave != "inicio")
        self.actualizar_titulo(clave)

    def capturas_faltantes(self, vista):
        """Pasos de la sesión que se capturarían con «Guardar todos» y aún no tienen PNG."""
        sesion = vista.capturas
        esperadas = getattr(sesion, "indices", range(len(vista.recorrido.pasos)))
        return [i for i in esperadas if i not in sesion.guardados]

    def completar_capturas(self, vista, faltan):
        return completar_capturas(vista, faltan)

    def crear_diapositivas(self):
        vista = self.vistas.get(self.actual)
        if vista is None:
            return
        vista.pausar()
        faltan = self.capturas_faltantes(vista)
        guardadas = len(diapositivas.capturas_de(vista.capturas.carpeta))
        total = len(faltan) + len(vista.capturas.guardados)
        if total > diapositivas.LIMITE:
            # Bellman-Ford con ciclos negativos supera las 5000 capturas: completarla
            # tardaría mucho y produciría archivos de varios GB.
            if guardadas == 0:
                QMessageBox.information(
                    self, "Crear diapositivas",
                    f"Esta sesión tiene {total} pasos para capturar, demasiados para una presentación.\n\n"
                    "Activa la captura automática, avanza por los pasos que quieras mostrar y vuelve a pulsar el botón.")
                return
            if guardadas > diapositivas.LIMITE and QMessageBox.question(
                    self, "Crear diapositivas",
                    f"Hay {guardadas} capturas guardadas. La presentación será muy grande.\n\n¿Crearla de todos modos?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            faltan = []  # Solo las capturas de los pasos recorridos.
        if faltan:
            respuesta = QMessageBox.question(
                self, "Crear diapositivas",
                f"Esta sesión tiene {total - len(faltan)} de {total} capturas guardadas.\n\n"
                "¿Guardar las que faltan para que la presentación muestre el recorrido completo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if respuesta == QMessageBox.StandardButton.Cancel:
                return
            try:
                if respuesta == QMessageBox.StandardButton.Yes and not self.completar_capturas(vista, faltan):
                    return
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "No se pudieron guardar las capturas", str(exc))
                return
        formatos = ("pdf", "pptx") if diapositivas.pptx_disponible() else ("pdf",)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            creados = diapositivas.crear_diapositivas(vista.capturas.carpeta, formatos)
        except (OSError, ValueError) as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "No se pudieron crear las diapositivas", str(exc))
            return
        QApplication.restoreOverrideCursor()
        mensaje = (f"Se crearon {len(diapositivas.capturas_de(vista.capturas.carpeta))} diapositivas en:\n\n"
                   + "\n".join(p.name for p in creados) + f"\n\nCarpeta: {vista.capturas.carpeta}")
        if "pptx" not in formatos:
            mensaje += "\n\nPara crear también el PowerPoint instala python-pptx:\npython -m pip install -r requirements.txt"
        caja = QMessageBox(QMessageBox.Icon.Information, "Diapositivas creadas", mensaje,
                           QMessageBox.StandardButton.Close, self)
        abrir = caja.addButton("Abrir carpeta", QMessageBox.ButtonRole.ActionRole)
        caja.exec()
        if caja.clickedButton() is abrir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(vista.capturas.carpeta)))

    def actualizar_titulo(self, clave):
        if clave != self.actual:
            return
        if clave == "inicio":
            self.setWindowTitle("Laboratorio de caminos mínimos")
        else:
            self.setWindowTitle(self.vistas[clave].windowTitle())

    def pantalla_completa(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def salir_pantalla_completa(self):
        if self.isFullScreen():
            self.showNormal()

    def closeEvent(self, event):
        # Cada vista detiene sus temporizadores, como al cerrar su ventana original.
        for vista in self.vistas.values():
            vista.pausar()
            vista.close()
        super().closeEvent(event)


def ejecutar(inicial=None):
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    fuente = QFont("Segoe UI" if sys.platform == "win32" else "DejaVu Sans")
    fuente.setPixelSize(13)
    app.setFont(fuente)
    ventana = Laboratorio(inicial)
    ventana.show()
    return app.exec()
