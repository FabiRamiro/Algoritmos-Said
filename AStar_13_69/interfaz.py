"""Interfaz de escritorio dibujada con Qt. No usa NetworkX ni un navegador."""
from __future__ import annotations

from dataclasses import replace
from math import hypot, inf
from pathlib import Path
import sys

# Permite usar la pantalla compartida al ejecutar este proyecto por separado.
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
from pantalla_carga import TemporizadorCapturas
import json
import time

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, QUrl
from PySide6.QtGui import (QColor, QFont, QPainter, QPainterPath, QPen,
                           QKeySequence,
                           QShortcut, QCursor, QPixmap, QDesktopServices)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider,
    QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QMessageBox, QFileDialog, QScrollArea, QSizePolicy, QToolTip, QMenu, QListWidget, QSplitter)

from algoritmo import Grafo, Paso, a_estrella, numero
from capturas import SesionCapturas

BASE = Path(__file__).resolve().parent
from tema import BG, PANEL, LINE, INK, MUTED, CYAN, GOLD, VIOLET, GREEN, STYLE, aplicar_paleta


def font(size=13, bold=False, mono=False):
    f = QFont("Consolas" if mono else QApplication.font().family())
    f.setPixelSize(size)
    f.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    return f


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(alpha)
    return c


def label(text, size=13, tint=INK, bold=False):
    w = QLabel(text)
    w.setStyleSheet(f"color: {tint}; font-size: {size}px; font-weight: {600 if bold else 400};")
    return w


def eyebrow(text):
    w = QLabel(text)
    w.setObjectName("eyebrow")
    return w


def button(text, callback, kind="", tip=""):
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.clicked.connect(callback)
    if tip:
        b.setToolTip(tip)
    return b


def card():
    w = QFrame()
    w.setObjectName("card")
    return w


def table(headers):
    w = QTableWidget(0, len(headers))
    w.setHorizontalHeaderLabels(headers)
    w.verticalHeader().hide()
    w.setShowGrid(False)
    w.setAlternatingRowColors(True)
    w.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    w.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    w.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    w.verticalHeader().setDefaultSectionSize(32)
    w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return w


class Lienzo(QWidget):
    seleccionado = Signal(object)

    def __init__(self, grafo, paso):
        super().__init__()
        self.grafo, self.paso = grafo, paso
        self.setMouseTracking(True)
        self.setMinimumSize(540, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pesos = True
        self.distancias = True
        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.drag = None
        self.movido = False
        self.hover = None
        self.elegido = None
        self.playing = False
        self.origen = 13
        self.destino = 69

    def establecer(self, paso):
        self.paso = paso
        self.update()

    def encuadrar(self):
        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.update()

    def limites(self):
        rect = QRectF()
        for n in self.grafo.posiciones:
            pt = self.punto(n)
            area = QRectF(pt.x()-58, pt.y()-68, 116, 120)
            rect = rect.united(area) if not rect.isNull() else area
        for a in self.grafo.aristas:
            rect = rect.united(self.camino(a).boundingRect().adjusted(-28, -28, 28, 28))
        return rect

    def transformacion(self, rect=None, limpio=False):
        rect = QRectF(self.rect()) if rect is None else rect
        bounds = self.limites()
        escala = min((rect.width()-24)/max(1, bounds.width()),
                     (rect.height()-24)/max(1, bounds.height()))
        escala *= 1 if limpio else self.zoom
        offset = rect.center()-bounds.center()*escala
        return escala, offset + (QPointF() if limpio else self.pan)

    def logica(self, pt):
        s, offset = self.transformacion()
        return QPointF((pt.x()-offset.x())/s, (pt.y()-offset.y())/s)

    def punto(self, nodo):
        return QPointF(*self.grafo.posiciones[nodo]) + QPointF(0, 22)

    def camino(self, arista):
        a, b = self.punto(arista.u), self.punto(arista.v)
        dx, dy = b.x()-a.x(), b.y()-a.y()
        largo = max(1, hypot(dx, dy))
        c = (a+b)*.5 + QPointF(-dy/largo, dx/largo)*arista.curva
        path = QPainterPath(a)
        if arista.id == "e09" and {arista.u, arista.v} == {7, 1}:
            # El arco superior de la foto rodea los nodos centrales.
            path.cubicTo(QPointF(a.x()+230, a.y()-130),
                         QPointF(b.x()+60, b.y()-360), b)
        else:
            path.quadTo(c, b)
        return path

    def estado_color(self, n, paso):
        if n in paso.ruta:
            return GREEN
        if n == paso.actual:
            return GOLD
        if n == paso.vecino:
            return CYAN
        if n in paso.fijos:
            return VIOLET
        if paso.distancias.get(n, inf) < inf:
            return CYAN
        return "#626670"

    def paintEvent(self, event):
        painter = QPainter(self)
        self.dibujar(painter, QRectF(self.rect()))
        painter.end()

    def dibujar(self, p, rect, paso=None, limpio=False):
        """Un mismo dibujo para pantalla y PNG; la captura ignora zoom y selección."""
        paso = paso or self.paso
        p.save()
        p.setClipRect(rect)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.fillRect(rect, color(PANEL))
        escala, offset = self.transformacion(rect, limpio)
        p.translate(offset)
        p.scale(escala, escala)
        arbol = {item[1] for item in paso.anteriores.values()}
        ruta = set(paso.aristas_ruta)
        paths = {a.id: self.camino(a) for a in self.grafo.aristas}
        self.rutas_dibujadas = paths
        orden = sorted(self.grafo.aristas, key=lambda a: (a.id in ruta, a.id == paso.arista))
        for a in orden:
            path = paths[a.id]
            activo = a.id == paso.arista
            tinta = GREEN if a.id in ruta else GOLD if activo else "#87938c" if a.id in arbol else "#626a76"
            ancho = 4.5 if activo or a.id in ruta else 2 if a.id in arbol else 1.5
            pen = QPen(color(tinta), ancho, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            if a.dudosa and not activo and a.id not in ruta:
                pen.setStyle(Qt.PenStyle.DashLine)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(pen)
            p.drawPath(path)
            # La flecha indica qué dirección se está examinando, incluso en pausa.
            if activo:
                fraccion = .72 if paso.actual == a.u else .28
                punta = path.pointAtPercent(fraccion)
                previo = path.pointAtPercent(fraccion + (-.02 if paso.actual == a.u else .02))
                direccion = punta-previo
                largo = max(.001, hypot(direccion.x(), direccion.y()))
                direccion /= largo
                normal = QPointF(-direccion.y(), direccion.x())
                flecha = QPainterPath(punta)
                flecha.lineTo(punta-direccion*14+normal*7)
                flecha.lineTo(punta-direccion*14-normal*7)
                flecha.closeSubpath()
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(color(tinta))
                p.drawPath(flecha)
        # Desplazar etiquetas que chocan con nodos u otros pesos.
        ocupados = [QRectF(self.punto(n).x()-30, self.punto(n).y()-52, 60, 92)
                    for n in self.grafo.posiciones]
        # La etiqueta "g=… f=…" sobre cada nodo es más ancha que el círculo.
        ocupados += [QRectF(self.punto(n).x()-60, self.punto(n).y()-52, 120, 24)
                     for n in self.grafo.posiciones]
        if self.pesos or limpio:
            for a in sorted(self.grafo.aristas, key=lambda a: a.id != paso.arista):
                path = paths[a.id]
                activo = a.id == paso.arista or a.id in ruta
                texto = numero(a.peso) + ("*" if a.dudosa else "")
                p.setFont(font(max(15, round(10/escala)), activo, True))
                ancho = p.fontMetrics().horizontalAdvance(texto)+10
                alto = p.fontMetrics().height()+4
                candidatos = []
                for delta in (0, -.08, .08, -.16, .16):
                    t = max(.12, min(.88, a.etiqueta_t+delta))
                    pt = path.pointAtPercent(t)
                    for dy in (0, -18, 18, -32, 32):
                        box = QRectF(pt.x()-ancho/2, pt.y()-alto/2+dy, ancho, alto)
                        choques = sum(box.intersects(otro) for otro in ocupados)
                        candidatos.append((choques, abs(delta)*40+abs(dy), box, pt))
                _, _, box, ancla = min(candidatos, key=lambda item: item[:2])
                ocupados.append(box.adjusted(-3, -2, 3, 2))
                if abs(box.center().y()-ancla.y()) > 12:
                    p.setPen(QPen(color("#626a76"), 1))
                    p.drawLine(ancla, box.center())
                p.setPen(QPen(color("#86efac" if activo else "#292d34"), .8))
                p.setBrush(color("#243e2c" if activo else PANEL))
                p.drawRoundedRect(box, 4, 4)
                p.setPen(color(GREEN if a.id in ruta else GOLD if activo or a.dudosa else MUTED))
                p.drawText(box, Qt.AlignmentFlag.AlignCenter, texto)
        for n in self.grafo.posiciones:
            pt = self.punto(n)
            tinta = self.estado_color(n, paso)
            actual, vecino = n == paso.actual, n == paso.vecino
            r = max(25, 14/escala)
            relleno = ("#173f2b" if n in paso.ruta else "#31532b" if actual
                       else "#20372c" if vecino else "#20372c" if n in paso.fijos else PANEL)
            if actual or vecino or (not limpio and n == self.elegido):
                p.setPen(QPen(color(tinta), 1.4, Qt.PenStyle.DashLine if vecino else Qt.PenStyle.SolidLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(pt, r+6, r+6)
            p.setPen(QPen(color(tinta), 2.5 if actual or vecino or n in paso.ruta else 1.6))
            p.setBrush(color(relleno))
            p.drawEllipse(pt, r, r)
            p.setFont(font(max(19, round(12/escala)), True, True))
            p.setPen(color(INK))
            p.drawText(QRectF(pt.x()-r, pt.y()-r, r*2, r*2), Qt.AlignmentFlag.AlignCenter, str(n))
            if n in paso.fijos:
                marca = pt + QPointF(r*.72, r*.72)
                p.setBrush(color("#353941"))
                p.setPen(QPen(color("#7f858f"), 1))
                p.drawEllipse(marca, 6, 6)
                p.setPen(QPen(color(INK), 1.4))
                p.drawLine(marca+QPointF(-3,0), marca+QPointF(-1,2))
                p.drawLine(marca+QPointF(-1,2), marca+QPointF(3,-2))
            if self.distancias or limpio:
                # Descubierto: costo real g y prioridad f. Sin descubrir: solo h.
                h = (paso.heuristica or {}).get(n, 0)
                g = paso.distancias[n]
                texto = (f"g={numero(g)} f={numero(g+h)}" if g < inf else f"h={numero(h)}")
                p.setFont(font(max(13, round(9/escala)), g < inf, True))
                ancho = p.fontMetrics().horizontalAdvance(texto)+10
                box = QRectF(pt.x()-ancho/2, pt.y()-r-24, ancho, 21)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(color(PANEL))
                p.drawRoundedRect(box, 3, 3)
                p.setPen(color(tinta if g < inf else "#6f747e"))
                p.drawText(box, Qt.AlignmentFlag.AlignCenter, texto)
            if n in (self.origen, self.destino):
                p.setFont(font(11, True))
                p.setPen(color(MUTED))
                texto = "ORIGEN / META" if self.origen == self.destino else "ORIGEN" if n == self.origen else "DESTINO"
                p.drawText(QRectF(pt.x()-62, pt.y()+r+7, 124, 18), Qt.AlignmentFlag.AlignCenter, texto)
        p.restore()

    def buscar(self, pt):
        pt = self.logica(pt)
        for n in self.grafo.posiciones:
            v = self.punto(n)-pt
            if hypot(v.x(), v.y()) < 33:
                return n
        return None

    def mousePressEvent(self, event):
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self.drag = event.position()
            self.movido = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag is not None:
            delta = event.position()-self.drag
            if hypot(delta.x(), delta.y()) > 2:
                self.movido = True
            self.pan += delta
            self.drag = event.position()
            self.update()
            return
        n = self.buscar(event.position())
        if n != self.hover:
            self.hover = n
            self.setCursor(Qt.CursorShape.PointingHandCursor if n is not None else Qt.CursorShape.OpenHandCursor)
            if n is not None:
                d = numero(self.paso.distancias[n])
                h = (self.paso.heuristica or {}).get(n, 0)
                prev = self.paso.anteriores.get(n, (None,))[0]
                state = "Definitiva" if n in self.paso.fijos else "Tentativa" if d != "∞" else "Sin descubrir"
                QToolTip.showText(event.globalPosition().toPoint(),
                    f"Nodo {n}\ng: {d} · {state}\nh: {numero(h)}  ·  f: {numero(self.paso.distancias[n]+h)}"
                    f"\nPredecesor: {prev if prev is not None else '—'}", self)
            else:
                QToolTip.hideText()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drag is not None and not self.movido:
            self.elegido = self.buscar(event.position())
            self.seleccionado.emit(self.elegido)
        self.drag = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def leaveEvent(self, event):
        self.hover = None
        QToolTip.hideText()
        self.update()

    def wheelEvent(self, event):
        antes = self.logica(event.position())
        self.zoom = max(.65, min(3.0, self.zoom*(1.14 if event.angleDelta().y() > 0 else 1/1.14)))
        s, offset = self.transformacion()
        self.pan += event.position()-(antes*s+offset)
        self.update()
        event.accept()


class Ventana(QMainWindow):
    def __init__(self, ruta=None):
        super().__init__()
        self.ruta_datos = Path(ruta) if ruta else BASE / "grafo.json"
        self.grafo = Grafo.cargar(self.ruta_datos)
        self.recorrido = a_estrella(self.grafo, self.grafo.origen, self.grafo.destino)
        self.indice = 0
        self.reproduciendo = False
        self.ultimo_avance = time.monotonic()
        self.setWindowTitle("A* · 13 → 69 · Laboratorio visual")
        self.setMinimumSize(1120, 710)
        aplicar_paleta(QApplication.instance())
        self.setStyleSheet(STYLE)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.construir_cabecera(root)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(0)
        self.construir_secuencia(cuerpo)
        estudio = QWidget()
        espacio = QVBoxLayout(estudio)
        espacio.setContentsMargins(20, 4, 20, 0)
        espacio.setSpacing(8)
        cuerpo.addWidget(estudio, 1)
        root.addLayout(cuerpo, 1)
        self.construir_info(espacio)
        self.divisor = QSplitter(Qt.Orientation.Vertical)
        self.divisor.setChildrenCollapsible(False)
        self.divisor.setHandleWidth(5)
        espacio.addWidget(self.divisor, 1)
        self.construir_grafo(self.divisor)
        self.construir_lateral(self.divisor)
        self.divisor.setSizes([620, 190])
        self.divisor.setStretchFactor(0, 1)
        self.divisor.setStretchFactor(1, 0)
        self.panel_detalle.hide()
        espacio.addWidget(self.banda_paso)
        self.construir_controles(espacio)
        self.lote_timer = TemporizadorCapturas(self)
        self.lote_pendientes = []
        self.pulso = QTimer(self)
        self.pulso.timeout.connect(self.avanzar_reloj)
        self.pulso.start(25)
        self.atajos = []
        for key, callback in [("Space", self.alternar), ("Right", lambda: self.mover(1)),
                              ("Left", lambda: self.mover(-1)), ("R", self.reiniciar),
                              ("Home", self.reiniciar), ("End", self.resultado),
                              ("F11", self.pantalla_completa), ("Escape", self.salir_pantalla_completa)]:
            atajo = QShortcut(QKeySequence(key), self)
            atajo.activated.connect(callback)
            self.atajos.append(atajo)
        self.nueva_sesion_capturas()
        self.aplicar_paso(0)
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1600, screen.width()-50), min(980, screen.height()-65))

    def construir_cabecera(self, root):
        header = QFrame()
        header.setObjectName("cabecera")
        h = QHBoxLayout(header)
        h.setContentsMargins(22, 10, 22, 10)
        h.setSpacing(12)
        titulo = QVBoxLayout()
        titulo.setSpacing(0)
        titulo.addWidget(label("A *", 17, INK, True))
        titulo.addWidget(label("Explorador de caminos mínimos", 10, MUTED))
        h.addLayout(titulo)
        h.addStretch()
        self.origen_combo, self.destino_combo = QComboBox(), QComboBox()
        for caption, combo, initial in [("Origen", self.origen_combo, self.grafo.origen),
                                       ("Destino", self.destino_combo, self.grafo.destino)]:
            h.addWidget(label(caption, 11, MUTED))
            for n in sorted(self.grafo.posiciones):
                combo.addItem(str(n), n)
            combo.setCurrentText(str(initial))
            combo.setFixedWidth(72)
            combo.currentIndexChanged.connect(self.recalcular)
            h.addWidget(combo)
        h.addSpacing(12)
        h.addWidget(button("Editar grafo", self.editar_grafo, "quiet"))
        self.exportar_btn = button("Archivos", self.menu_exportar, "quiet")
        h.addWidget(self.exportar_btn)
        root.addWidget(header)

    def construir_secuencia(self, cuerpo):
        self.rail = QFrame()
        self.rail.setObjectName("rail")
        self.rail.setFixedWidth(238)
        col = QVBoxLayout(self.rail)
        col.setContentsMargins(16, 22, 12, 14)
        col.setSpacing(12)
        col.addWidget(eyebrow("SECUENCIA DEL RECORRIDO"))
        numeros = QHBoxLayout()
        self.numero_grande = label("001", 38, INK, True)
        self.total_pasos = label("", 12, MUTED)
        numeros.addWidget(self.numero_grande)
        numeros.addWidget(self.total_pasos)
        numeros.addStretch()
        col.addLayout(numeros)
        col.addWidget(label("Selecciona un paso para inspeccionarlo", 10, MUTED))
        self.historial = QListWidget()
        self.historial.setObjectName("secuencia")
        self.historial.setWordWrap(True)
        self.historial.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.historial.currentRowChanged.connect(self.ir_a)
        col.addWidget(self.historial, 1)
        col.addWidget(label("← →  avanzar     Espacio  reproducir", 10, MUTED))
        cuerpo.addWidget(self.rail)

    def construir_info(self, root):
        strip = QFrame()
        strip.setObjectName("metadatos")
        row = QHBoxLayout(strip)
        row.setContentsMargins(0, 3, 0, 3)
        self.nodos_info = label(f"{len(self.grafo.posiciones)} nodos", 11, INK, True)
        self.aristas_info = label(f"   /   {len(self.grafo.aristas)} aristas", 11, MUTED)
        row.addWidget(self.nodos_info)
        row.addWidget(self.aristas_info)
        row.addWidget(label("   /   No dirigido", 11, MUTED))
        self.stat_fijos, self.stat_cola, self.stat_costo = label("", 12, INK, True), label("", 12, CYAN, True), label("", 12, GREEN, True)
        for titulo, valor in [("Fijados", self.stat_fijos), ("Frontera", self.stat_cola), ("Costo", self.stat_costo)]:
            row.addSpacing(16)
            row.addWidget(label(titulo, 10, MUTED))
            row.addWidget(valor)
        row.addStretch()
        self.revisar = button("", self.editar_grafo, "review")
        row.addWidget(self.revisar)
        root.addWidget(strip)
        self.actualizar_aviso()

    def actualizar_aviso(self):
        count = sum(a.dudosa for a in self.grafo.aristas)
        self.revisar.setVisible(bool(count))
        self.revisar.setText(f"*  {count} pesos de la foto por confirmar")

    def construir_grafo(self, body):
        frame = QFrame()
        frame.setObjectName("espacioGrafo")
        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 8, 12, 4)
        v.setSpacing(0)
        row = QHBoxLayout()
        row.setSpacing(10)
        for texto, tinta in [("Pendiente", "#7b7f88"), ("Frontera", CYAN),
                             ("Actual", GOLD), ("Fijado", VIOLET), ("Ruta", GREEN)]:
            row.addWidget(label("●  " + texto, 10, tinta))
        row.addStretch()
        self.check_pesos = QCheckBox("Pesos")
        self.check_pesos.setChecked(True)
        self.check_distancias = QCheckBox("Distancias")
        self.check_distancias.setChecked(True)
        row.addWidget(self.check_pesos)
        row.addWidget(self.check_distancias)
        row.addWidget(button("Encuadrar", lambda: self.lienzo.encuadrar(), "quiet"))
        self.detalle_btn = button("Mostrar tablas", self.alternar_detalle, "quiet")
        row.addWidget(self.detalle_btn)
        row.addWidget(button("Enfocar", self.alternar_secuencia, "quiet", "Ocultar o mostrar la secuencia para ampliar el grafo"))
        v.addLayout(row)
        self.lienzo = Lienzo(self.grafo, self.recorrido.pasos[0])
        self.lienzo.origen, self.lienzo.destino = self.recorrido.origen, self.recorrido.destino
        self.check_pesos.toggled.connect(lambda value: self.cambiar_visual("pesos", value))
        self.check_distancias.toggled.connect(lambda value: self.cambiar_visual("distancias", value))
        self.lienzo.seleccionado.connect(self.inspeccionar)
        v.addWidget(self.lienzo, 1)
        self.inspector = label("", 10, MUTED)
        self.inspector.setContentsMargins(8, 3, 8, 3)
        v.addWidget(self.inspector)
        body.addWidget(frame)

    def alternar_secuencia(self):
        self.rail.setVisible(self.rail.isHidden())

    def alternar_detalle(self):
        visible = not self.panel_detalle.isHidden()
        self.panel_detalle.setVisible(not visible)
        self.detalle_btn.setText("Mostrar tablas" if visible else "Ocultar tablas")

    def cambiar_visual(self, attr, value):
        setattr(self.lienzo, attr, value)
        self.lienzo.update()

    def construir_lateral(self, body):
        self.panel_detalle = QFrame()
        self.panel_detalle.setObjectName("detalle")
        self.panel_detalle.setMinimumHeight(180)
        layout = QVBoxLayout(self.panel_detalle)
        layout.setContentsMargins(24, 0, 24, 4)
        self.banda_paso = QFrame()
        self.banda_paso.setObjectName("detalle")
        accion = QHBoxLayout(self.banda_paso)
        accion.setContentsMargins(4, 6, 4, 4)
        accion.setSpacing(28)
        decision = QWidget()
        box = QVBoxLayout(decision)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(5)
        top = QHBoxLayout()
        top.addWidget(eyebrow("AHORA EN EL RECORRIDO"))
        top.addStretch()
        self.tipo_label = label("", 10, CYAN, True)
        top.addWidget(self.tipo_label)
        box.addLayout(top)
        self.titulo_paso = label("", 20, INK, True)
        self.titulo_paso.setWordWrap(True)
        box.addWidget(self.titulo_paso)
        self.texto_paso = label("", 12, MUTED)
        self.texto_paso.setWordWrap(True)
        box.addWidget(self.texto_paso)
        self.formula = label("", 16, CYAN, True)
        self.formula.setMinimumWidth(230)
        self.formula.setWordWrap(True)
        self.formula.setStyleSheet(f"background: #1c1e23; border: 1px solid #35383f; border-radius: 7px; padding: 12px 14px; color: {INK}; font: 16px 'Consolas';")
        accion.addWidget(decision, 3)
        accion.addWidget(self.formula, 1)
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(450)
        self.tabs.setMinimumHeight(170)
        page = QWidget()
        pv = QVBoxLayout(page)
        pv.setContentsMargins(10, 10, 10, 10)
        pv.setSpacing(7)
        self.cola_nota = label("El próximo candidato está arriba.", 10, MUTED)
        self.cola_nota.setWordWrap(True)
        pv.addWidget(self.cola_nota)
        self.cola_tabla = table(["NODO", "g", "h", "f = g + h", "VÍA"])
        self.cola_tabla.cellClicked.connect(lambda row, col: self.seleccionar_tabla(self.cola_tabla, row))
        pv.addWidget(self.cola_tabla, 1)
        self.cola_empty = label("La frontera está vacía.", 11, MUTED)
        pv.addWidget(self.cola_empty)
        self.tabs.addTab(page, "Frontera")
        page = QWidget()
        pv = QVBoxLayout(page)
        pv.setContentsMargins(10, 10, 10, 10)
        note = label("✓ definitiva  ·  ~ tentativa  ·  ∞ sin descubrir", 9, MUTED)
        pv.addWidget(note)
        self.dist_tabla = table(["NODO", "g", "h", "VÍA", "ESTADO"])
        self.dist_tabla.cellClicked.connect(lambda row, col: self.seleccionar_tabla(self.dist_tabla, row))
        pv.addWidget(self.dist_tabla)
        self.tabs.addTab(page, "Distancias")
        page = QScrollArea()
        page.setWidgetResizable(True)
        code = QWidget()
        cv = QVBoxLayout(code)
        cv.setContentsMargins(10, 12, 10, 12)
        cv.setSpacing(2)
        self.code_lines = []
        lines = ["g[origen] = 0; resto = ∞; h = línea recta", "mientras exista frontera:",
                 "  u = extraer_menor_f(); fijar(u)", "  si u == destino: terminar",
                 "  para v no fijado, vecino de u:", "    nueva = g[u] + peso(u,v)",
                 "    si nueva < g[v]:", "      g[v] = nueva; f[v] = g[v] + h(v)",
                 "      previo[v] = u; encolar(f[v], v)", "ruta = seguir_predecesores()", "mostrar(ruta, g[destino])"]
        for i, text in enumerate(lines):
            w = QLabel(f"{i+1:02d}  {text}")
            w.setMinimumHeight(28)
            self.code_lines.append(w)
            cv.addWidget(w)
        cv.addSpacing(12)
        note = label("h(n) = escala · distancia en línea recta hasta el destino; la escala es el menor peso / longitud, así h nunca supera el costo real. "
                     "Si dos candidatos empatan en f, se elige el de menor h y después el de menor número. Un empate de costo conserva el predecesor.", 10, MUTED)
        note.setWordWrap(True)
        cv.addWidget(note)
        cv.addStretch()
        page.setWidget(code)
        self.tabs.addTab(page, "Algoritmo")
        ruta_page = QWidget()
        ruta_layout = QVBoxLayout(ruta_page)
        self.ruta_label = label("", 20, GREEN, True)
        self.ruta_label.setWordWrap(True)
        self.ruta_sub = label("", 12, MUTED)
        self.ruta_sub.setWordWrap(True)
        ruta_layout.addWidget(self.ruta_label)
        ruta_layout.addWidget(self.ruta_sub)
        ruta_layout.addStretch()
        self.tabs.addTab(ruta_page, "Ruta")
        layout.addWidget(self.tabs)
        body.addWidget(self.panel_detalle)

    def construir_controles(self, root):
        frame = QFrame()
        frame.setObjectName("transporte")
        v = QVBoxLayout(frame)
        v.setContentsMargins(0, 7, 0, 4)
        v.setSpacing(7)
        row = QHBoxLayout()
        self.paso_label = label("", 11, "#e8e9ec", True)
        self.paso_label.setFixedWidth(132)
        row.addWidget(self.paso_label)
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timeline.setRange(0, len(self.recorrido.pasos)-1)
        self.timeline.sliderPressed.connect(self.pausar)
        self.timeline.valueChanged.connect(self.ir_a)
        row.addWidget(self.timeline, 1)
        self.pct = label("", 11, "#b1b5be", True)
        self.pct.setFixedWidth(38)
        row.addWidget(self.pct)
        v.addLayout(row)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(button("Inicio", self.reiniciar, "quiet"))
        self.prev_btn = button("Anterior", lambda: self.mover(-1))
        self.play_btn = button("Reproducir", self.alternar, "primary", "Espacio para reproducir o pausar")
        self.play_btn.setMinimumWidth(130)
        self.next_btn = button("Siguiente", lambda: self.mover(1))
        for b in (self.prev_btn, self.play_btn, self.next_btn):
            row.addWidget(b)
        row.addWidget(button("Resultado", self.resultado, "quiet"))
        row.addStretch()
        self.modo = QComboBox()
        self.modo.addItem("Cada micro paso", "detalle")
        self.modo.addItem("Por nodo fijado", "nodo")
        row.addWidget(self.modo)
        row.addWidget(label("Velocidad", 10, "#a0a4ad"))
        self.velocidad = QComboBox()
        for texto, valor in [("0.5×", .5), ("1×", 1), ("1.5×", 1.5), ("2×", 2), ("4×", 4)]:
            self.velocidad.addItem(texto, valor)
        self.velocidad.setCurrentIndex(1)
        row.addWidget(self.velocidad)
        v.addLayout(row)
        root.addWidget(frame)
        pie = QHBoxLayout()
        pie.setContentsMargins(0, 0, 0, 1)
        self.captura_estado = label("", 10, MUTED)
        pie.addWidget(self.captura_estado)
        pie.addStretch()
        self.automatico = QCheckBox("Capturar al avanzar")
        self.automatico.setToolTip("Guardar PNG al avanzar puede ralentizar la navegación. También puedes usar Guardar todos al terminar.")
        self.automatico.toggled.connect(self.cambiar_capturas)
        pie.addWidget(self.automatico)

        pie.addWidget(button("Carpeta PNG", self.abrir_capturas, "quiet"))
        self.todos_btn = button("Guardar todos", self.exportar_todo, "quiet")
        pie.addWidget(self.todos_btn)
        root.addLayout(pie)

    def nueva_sesion_capturas(self):
        self.lote_timer.stop()
        self.lote_pendientes = []
        self.todos_btn.setText("Guardar todos")
        self.capturas = SesionCapturas(self.grafo, self.recorrido, self.lienzo.dibujar)
        self.error_captura = False
        self.historial.blockSignals(True)
        self.historial.clear()
        self.historial.addItems([f"{i:03d}  {p.titulo}" for i, p in enumerate(self.recorrido.pasos, 1)])
        self.historial.blockSignals(False)

    def mostrar_estado_capturas(self):
        self.captura_estado.setText(
            f"Capturas · {len(self.capturas.guardados)} / {len(self.capturas.indices)} guardados"
            + (" · exportando…" if self.lote_timer.isActive() else ""))
        self.captura_estado.setToolTip(str(self.capturas.carpeta))

    def cambiar_capturas(self, activo):
        if activo:
            self.error_captura = False
            self.guardar_paso_actual()
        else:
            self.lote_timer.stop()
            self.lote_pendientes = []
            self.todos_btn.setText("Guardar todos")
        self.mostrar_estado_capturas()

    def guardar_paso_actual(self):
        if self.error_captura:
            return
        try:
            self.capturas.guardar(self.indice)
            self.mostrar_estado_capturas()
        except (OSError, ValueError) as exc:
            self.fallo_captura(exc)

    def fallo_captura(self, exc):
        self.lote_timer.stop()
        self.error_captura = True
        self.todos_btn.setText("Reintentar guardar todos")
        self.captura_estado.setText("No se pudo guardar · el recorrido sigue disponible")
        self.captura_estado.setToolTip(str(exc))
        QMessageBox.warning(self, "No se pudo guardar la captura",
                            f"{exc}\n\nLibera espacio o revisa los permisos de la carpeta. Puedes reintentar con Guardar todos los pasos.")

    def abrir_capturas(self):
        if self.capturas.carpeta.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.capturas.carpeta)))

    def exportar_todo(self):
        self.pausar()
        if self.lote_timer.isActive():
            self.lote_timer.stop()
            self.todos_btn.setText("Continuar guardando todos")
            self.mostrar_estado_capturas()
            return
        self.error_captura = False
        self.lote_pendientes = [i for i in self.capturas.indices
                                if i not in self.capturas.guardados]
        if self.lote_pendientes:
            self.todos_btn.setText("Pausar exportación")
            self.lote_timer.start(10)
        self.mostrar_estado_capturas()

    def procesar_captura(self):
        if not self.lote_pendientes:
            self.lote_timer.stop()
            self.todos_btn.setText("Todos los pasos guardados")
            self.mostrar_estado_capturas()
            return
        try:
            self.capturas.guardar(self.lote_pendientes.pop(0))
            self.mostrar_estado_capturas()
        except (OSError, ValueError) as exc:
            self.fallo_captura(exc)

    def recalcular(self):
        if not hasattr(self, "lienzo"):
            return
        self.pausar()
        origen, destino = self.origen_combo.currentData(), self.destino_combo.currentData()
        self.recorrido = a_estrella(self.grafo, origen, destino)
        self.lienzo.grafo = self.grafo
        self.lienzo.origen, self.lienzo.destino = origen, destino
        self.timeline.blockSignals(True)
        self.timeline.setMaximum(len(self.recorrido.pasos)-1)
        self.timeline.blockSignals(False)
        self.setWindowTitle(f"A* · {origen} → {destino} · Laboratorio visual")
        self.nodos_info.setText(f"{len(self.grafo.posiciones)} nodos")
        self.aristas_info.setText(f"   /   {len(self.grafo.aristas)} aristas")
        self.actualizar_aviso()
        self.nueva_sesion_capturas()
        self.aplicar_paso(0)

    def aplicar_paso(self, index):
        anterior = self.indice
        self.indice = max(0, min(index, len(self.recorrido.pasos)-1))
        paso = self.recorrido.pasos[self.indice]
        self.lienzo.establecer(paso)
        self.timeline.blockSignals(True)
        self.timeline.setValue(self.indice)
        self.timeline.blockSignals(False)
        total = len(self.recorrido.pasos)-1
        self.paso_label.setText(f"PASO {self.indice+1:03d} / {total+1:03d}")
        self.pct.setText(f"{round(self.indice/max(1,total)*100)}%")
        self.numero_grande.setText(f"{self.indice+1:03d}")
        self.total_pasos.setText(f"/ {total+1:03d} pasos")
        self.titulo_paso.setText(paso.titulo)
        self.texto_paso.setText(paso.texto)
        self.formula.setText(paso.formula or "—")
        kinds = {"inicio":"INICIO", "heuristica":"HEURÍSTICA", "fijar":"FIJAR", "examinar":"EXPLORAR", "mejorar":"ACTUALIZAR", "mantener":"CONSERVAR", "omitir":"OMITIR", "ruta":"RUTA", "fin":"COMPLETO", "sin_ruta":"SIN RUTA"}
        self.tipo_label.setText(kinds.get(paso.tipo, paso.tipo.upper()))
        self.stat_fijos.setText(str(len(paso.fijos)))
        self.stat_cola.setText(str(len(paso.frontera)))
        destino = self.recorrido.destino
        self.stat_costo.setText(numero(paso.distancias[destino]) + ("" if destino in paso.fijos or paso.distancias[destino] == inf else " ~"))
        self.stat_costo.setToolTip("~ indica una distancia tentativa. Solo es definitiva al fijar el destino.")
        heur = paso.heuristica or {}
        for tbl, rows in [(self.cola_tabla, [n for _,n in paso.frontera]),
                          (self.dist_tabla, sorted(self.grafo.posiciones))]:
            scroll = tbl.verticalScrollBar().value()
            tbl.setRowCount(len(rows))
            for row,n in enumerate(rows):
                d = paso.distancias[n]
                h = heur.get(n, 0)
                prev = paso.anteriores.get(n, (None,))[0]
                via = str(prev) if prev is not None else "—"
                if tbl is self.cola_tabla:
                    values = [str(n), numero(d), numero(h), numero(d+h), via]
                else:
                    values = [str(n), numero(d), numero(h), via,
                              "✓ fija" if n in paso.fijos else "~" if d < inf else "∞"]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if n == paso.actual:
                        item.setForeground(color(GOLD))
                    elif n in paso.ruta:
                        item.setForeground(color(GREEN))
                    elif n in paso.fijos:
                        item.setForeground(color(VIOLET))
                    elif d < inf:
                        item.setForeground(color(CYAN))
                    else:
                        item.setForeground(color(MUTED))
                    tbl.setItem(row, col, item)
            tbl.verticalScrollBar().setValue(scroll)
        self.cola_empty.setVisible(not paso.frontera)
        self.cola_nota.setText("Candidatos pendientes; la meta ya está fijada." if paso.tipo in ("fin", "ruta") else "El próximo candidato está arriba.")
        for i, w in enumerate(self.code_lines):
            active = i == paso.linea or (paso.tipo in ("predecesor", "encolar") and i == 8) or (paso.tipo == "fijar" and paso.actual == destino and i == 3)
            w.setStyleSheet(f"font: 10px 'Consolas'; padding: 5px 4px; border-radius: 5px; background: {'#24543a' if active else 'transparent'}; color: {CYAN if active else MUTED};")
        if paso.tipo == "fin":
            self.ruta_label.setText("   →   ".join(map(str, paso.ruta)))
            self.ruta_label.setStyleSheet(f"font-size: 19px; font-weight: 600; color: {GREEN};")
            self.ruta_sub.setText(f"CAMINO MÍNIMO    ·    Costo {numero(self.recorrido.costo)}    ·    {len(paso.aristas_ruta)} aristas    ·    {len(paso.fijos)} nodos fijados")
        elif paso.tipo in ("ruta", "retroceder"):
            self.ruta_label.setText("   →   ".join(map(str, paso.ruta)))
            self.ruta_label.setStyleSheet(f"font-size: 19px; font-weight: 600; color: {GREEN};")
            self.ruta_sub.setText("Reconstruyendo la ruta a partir de los predecesores…")
        else:
            self.ruta_label.setText(f"{self.recorrido.origen}   →   {destino}     /     " + ("Sin conexión" if paso.tipo == "sin_ruta" else "Un camino por descubrir"))
            self.ruta_label.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {INK};")
            self.ruta_sub.setText("El costo óptimo aparece cuando el destino queda fijado.")
        self.prev_btn.setEnabled(self.indice > 0)
        self.next_btn.setEnabled(self.indice < total)
        if self.indice >= total:
            self.pausar()
            self.play_btn.setText("Repetir")
        self.inspeccionar(self.lienzo.elegido)
        self.historial.blockSignals(True)
        self.historial.setCurrentRow(self.indice)
        self.historial.scrollToItem(self.historial.currentItem(), QAbstractItemView.ScrollHint.PositionAtCenter)
        self.historial.blockSignals(False)
        if self.automatico.isChecked():
            self.guardar_paso_actual()
        self.mostrar_estado_capturas()
        # Saltar con la barra, por nodo o al resultado tampoco pierde evidencias.
        # Solo las decisiones seleccionadas se guardan, sin mover la pantalla.
        if self.automatico.isChecked() and self.indice > anterior + 1 and not self.error_captura:
            pendientes = set(self.lote_pendientes)
            pendientes.update(i for i in self.capturas.indices
                              if anterior < i < self.indice and i not in self.capturas.guardados)
            self.lote_pendientes = sorted(pendientes)
            if self.lote_pendientes:
                self.todos_btn.setText("Pausar exportación")
                self.lote_timer.start(10)
                self.mostrar_estado_capturas()

    def inspeccionar(self, n):
        if n is None:
            self.inspector.setText("Clic en un nodo para inspeccionar  ·  Rueda para ampliar  ·  Arrastra para mover")
            return
        paso = self.recorrido.pasos[self.indice]
        d = numero(paso.distancias[n])
        h = (paso.heuristica or {}).get(n, 0)
        prev = paso.anteriores.get(n, (None,))[0]
        estado = "definitiva" if n in paso.fijos else "tentativa" if d != "∞" else "sin descubrir"
        self.inspector.setText(f"NODO {n}    ·    g {d} ({estado})    ·    h {numero(h)}    ·    f {numero(paso.distancias[n]+h)}    ·    Predecesor {prev if prev is not None else '—'}    ·    {len(self.grafo.adyacencia[n])} conexiones")

    def seleccionar_tabla(self, tabla, row):
        item = tabla.item(row, 0)
        if item is not None:
            self.lienzo.elegido = int(item.text())
            self.inspeccionar(self.lienzo.elegido)
            self.lienzo.update()

    def ir_a(self, index):
        self.pausar()
        self.aplicar_paso(index)

    def siguiente_indice(self, delta):
        index = self.indice+delta
        if self.modo.currentData() == "nodo":
            while 0 < index < len(self.recorrido.pasos)-1 and self.recorrido.pasos[index].tipo not in ("fijar", "ruta", "fin"):
                index += delta
        return index

    def mover(self, delta):
        self.pausar()
        self.aplicar_paso(self.siguiente_indice(delta))

    def pausar(self):
        self.reproduciendo = False
        if hasattr(self, "lienzo"):
            self.lienzo.playing = False
        if hasattr(self, "play_btn"):
            self.play_btn.setText("Reproducir")

    def alternar(self):
        if self.reproduciendo:
            self.pausar()
            return
        if self.indice == len(self.recorrido.pasos)-1:
            self.aplicar_paso(0)
        self.reproduciendo = True
        self.lienzo.playing = True
        self.ultimo_avance = time.monotonic()
        self.play_btn.setText("Pausar")

    def avanzar_reloj(self):
        if not self.reproduciendo or QApplication.activeModalWidget() is not None:
            return
        paso = self.recorrido.pasos[self.indice]
        duracion = {"examinar":1.15,"mejorar":1.55,"mantener":1.25,"omitir":.85,"fijar":1.7,"ruta":1.15,"inicio":1.8,"heuristica":2.2}.get(paso.tipo,1.4)
        duracion /= self.velocidad.currentData()
        if time.monotonic()-self.ultimo_avance >= duracion:
            self.aplicar_paso(self.siguiente_indice(1))
            self.ultimo_avance = time.monotonic()

    def reiniciar(self):
        self.pausar()
        self.aplicar_paso(0)

    def resultado(self):
        self.pausar()
        self.aplicar_paso(len(self.recorrido.pasos)-1)

    def pantalla_completa(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def salir_pantalla_completa(self):
        if self.isFullScreen():
            self.showNormal()

    def editar_grafo(self):
        self.pausar()
        dialog = QDialog(self)
        dialog.setWindowTitle("Transcripción de la fotografía · Revisar pesos")
        dialog.resize(920, 660)
        v = QVBoxLayout(dialog)
        v.setContentsMargins(22, 20, 22, 20)
        v.addWidget(label("El grafo, conexión por conexión.", 23, INK, True))
        note = label("Los pesos con * son lecturas provisionales. Puedes corregirlos y marcar «Confirmado». Los cambios recalculan el recorrido desde el inicio.", 12, MUTED)
        note.setWordWrap(True)
        v.addWidget(note)
        v.addWidget(label("Sin flechas: se interpreta no dirigido.  ·  Se mantienen las dos aristas 12–16.  ·  Lectura de 16–17: 7.", 11, CYAN))
        t = table(["ID", "NODOS", "PESO", "CONFIRMADO", "LECTURA / OBSERVACIÓN"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for c,w in [(0,55),(1,125),(2,115),(3,110)]:
            t.setColumnWidth(c,w)
        t.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeMode.Stretch)
        t.setRowCount(len(self.grafo.aristas))
        t.verticalHeader().setDefaultSectionSize(40)
        spins, checks = [], []
        # Orden de la foto; cada arista paralela sigue siendo una fila distinta.
        for row,a in enumerate(self.grafo.aristas):
            for col,text in [(0,a.id),(1,f"{a.u} ↔ {a.v}"),(4,a.nota or ("Arista paralela, peso independiente." if {a.u,a.v} == {12,16} else ""))]:
                item = QTableWidgetItem(text)
                if a.dudosa:
                    item.setForeground(color(GOLD))
                t.setItem(row,col,item)
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setRange(0,1_000_000_000)
            spin.setValue(a.peso)
            t.setCellWidget(row,2,spin)
            spins.append(spin)
            check = QCheckBox("Sí" if not a.dudosa else "Revisar *")
            check.setChecked(not a.dudosa)
            check.toggled.connect(lambda value, c=check: c.setText("Sí" if value else "Revisar *"))
            t.setCellWidget(row,3,check)
            checks.append(check)
        v.addWidget(t,1)
        row = QHBoxLayout()
        photo = button("Ver foto original", self.ver_foto)
        photo.setEnabled((BASE/"grafo_original.jpeg").exists())
        row.addWidget(photo)
        row.addWidget(label("Aplicar cambia esta sesión. Exportar datos guarda una copia.",10,MUTED))
        row.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText("Aplicar y reiniciar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.rejected.connect(dialog.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(dialog.accept)
        row.addWidget(buttons)
        v.addLayout(row)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nuevas = [replace(a,peso=spins[i].value(),dudosa=not checks[i].isChecked()) for i,a in enumerate(self.grafo.aristas)]
            self.grafo = Grafo(dict(self.grafo.posiciones), nuevas, self.recorrido.origen, self.recorrido.destino)
            self.recalcular()

    def ver_foto(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Fotografía original")
        dialog.resize(1120,820)
        v = QVBoxLayout(dialog)
        scroll = QScrollArea()
        img = QLabel()
        pix = QPixmap(str(BASE/"grafo_original.jpeg"))
        img.setPixmap(pix)
        scroll.setWidget(img)
        v.addWidget(scroll)
        v.addWidget(label("La fotografía conserva su resolución. Usa las barras para recorrerla.",11,MUTED))
        dialog.exec()

    def menu_exportar(self):
        self.pausar()
        menu = QMenu(self)
        menu.addAction("Guardar captura limpia del paso", self.exportar_png)
        menu.addAction("Guardar TODOS los pasos en PNG", self.exportar_todo)
        menu.addAction("Abrir carpeta de capturas", self.abrir_capturas)
        menu.addAction("Guardar explicación de los pasos", self.exportar_pasos)
        menu.addAction("Guardar grafo editado (JSON)", self.exportar_datos)
        menu.addAction("Abrir grafo guardado (JSON)", self.abrir_datos)
        menu.exec(self.exportar_btn.mapToGlobal(self.exportar_btn.rect().bottomLeft()))

    def exportar_png(self):
        path,_ = QFileDialog.getSaveFileName(self,"Guardar captura","AStar_captura.png","Imagen PNG (*.png)")
        if path:
            if not self.capturas.imagen(self.indice).save(path,"PNG"):
                QMessageBox.warning(self,"No se pudo guardar","No fue posible escribir la imagen en la ubicación elegida.")

    def exportar_pasos(self):
        path,_ = QFileDialog.getSaveFileName(self,"Guardar explicación","AStar_paso_a_paso.md","Markdown (*.md);;Texto (*.txt)")
        if path:
            try:
                notes = "\n## Pesos provisionales\n\n" + "\n".join(f"- {a.u}–{a.v}: {numero(a.peso)}. {a.nota}" for a in self.grafo.aristas if a.dudosa)
                Path(path).write_text(self.recorrido.resumen()+notes+"\n",encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(self,"No se pudo guardar",str(exc))

    def exportar_datos(self):
        path,_ = QFileDialog.getSaveFileName(self,"Guardar grafo","grafo_editado.json","JSON (*.json)")
        if not path:
            return
        data = {"directed":False,"source":self.recorrido.origen,"target":self.recorrido.destino,
                "nodes":[{"id":n,"x":pos[0],"y":pos[1]} for n,pos in self.grafo.posiciones.items()],
                "edges":[{"id":a.id,"u":a.u,"v":a.v,"weight":a.peso,"curve":a.curva,"label_t":a.etiqueta_t,"uncertain":a.dudosa,"note":a.nota} for a in self.grafo.aristas]}
        try:
            Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self,"No se pudo guardar",str(exc))

    def abrir_datos(self):
        path,_ = QFileDialog.getOpenFileName(self,"Abrir grafo guardado","","JSON (*.json)")
        if not path:
            return
        try:
            nuevo = Grafo.cargar(Path(path))
            # Validar también los puntos de inicio antes de reemplazar el actual.
            a_estrella(nuevo,nuevo.origen,nuevo.destino)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            QMessageBox.warning(self,"No se pudo abrir",str(exc))
            return
        self.grafo = nuevo
        for combo,initial in [(self.origen_combo,nuevo.origen),(self.destino_combo,nuevo.destino)]:
            combo.blockSignals(True)
            combo.clear()
            for n in sorted(nuevo.posiciones):
                combo.addItem(str(n),n)
            combo.setCurrentText(str(initial))
            combo.blockSignals(False)
        self.lienzo.elegido = None
        self.lienzo.hover = None
        self.recalcular()
        self.lienzo.encuadrar()


def ejecutar(ruta=None):
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    f = QFont("Segoe UI" if __import__("sys").platform == "win32" else "DejaVu Sans")
    f.setPixelSize(13)
    app.setFont(f)
    window = Ventana(ruta)
    window.show()
    return app.exec()
