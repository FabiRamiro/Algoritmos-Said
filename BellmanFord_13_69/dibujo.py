"""Lienzo compartido por la aplicación y la exportación de capturas."""
from math import hypot, inf
from PySide6.QtCore import Qt,QPointF,QRectF,Signal
from PySide6.QtGui import QColor,QFont,QPainter,QPen,QPainterPath
from PySide6.QtWidgets import QWidget,QSizePolicy,QToolTip,QApplication
from algoritmo import numero
from tema import PANEL,INK,MUTED,CYAN,GOLD,VIOLET,GREEN

def color(value,alpha=255):
    c=QColor(value)
    c.setAlpha(alpha)
    return c

def font(size=13,bold=False,mono=False):
    f=QFont("Consolas" if mono else "Segoe UI")
    f.setPixelSize(size)
    f.setBold(bold)
    return f

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
        if arista.u == arista.v:
            path.cubicTo(a+QPointF(-70,-95),a+QPointF(70,-95),a)
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
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(pen)
            p.drawPath(path)
            # La flecha indica qué dirección se está examinando, incluso en pausa.
            if activo or self.grafo.dirigido:
                fraccion = .72 if not activo or paso.actual == a.u else .28
                punta = path.pointAtPercent(fraccion)
                previo = path.pointAtPercent(fraccion + (-.02 if not activo or paso.actual == a.u else .02))
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
        if self.pesos or limpio:
            for a in sorted(self.grafo.aristas, key=lambda a: a.id != paso.arista):
                path = paths[a.id]
                activo = a.id == paso.arista or a.id in ruta
                texto = numero(a.peso)
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
                p.setPen(color(GREEN if a.id in ruta else GOLD if activo else MUTED))
                p.drawText(box, Qt.AlignmentFlag.AlignCenter, texto)
        for n in self.grafo.posiciones:
            pt = self.punto(n)
            tinta = self.estado_color(n, paso)
            actual, vecino = n == paso.actual, n == paso.vecino
            r = max(25, 14/escala)
            relleno = ("#173f2b" if n in paso.ruta else "#31532b" if actual
                       else "#20372c" if vecino else "#1c1e23" if paso.distancias[n] < inf else PANEL)
            if actual or vecino or (not limpio and n == self.elegido):
                p.setPen(QPen(color(tinta), 1.4, Qt.PenStyle.DashLine if vecino else Qt.PenStyle.SolidLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(pt, r+6, r+6)
            p.setPen(QPen(color(tinta), 2.5 if actual or vecino or n in paso.ruta else 1.6))
            p.setBrush(color(relleno))
            p.drawEllipse(pt, r, r)
            p.setFont(font(max(19, round(12/escala)), True, True))
            p.setPen(color(INK))
            valor = numero(paso.distancias[n]) if self.distancias or limpio else str(n)
            fuente = font(max(18, round(11/escala)), True, True)
            p.setFont(fuente)
            # Pesos grandes no deben desbordar el nodo.
            while p.fontMetrics().horizontalAdvance(valor) > 2*r-6 and fuente.pixelSize() > 9:
                fuente.setPixelSize(fuente.pixelSize()-1)
                p.setFont(fuente)
            p.drawText(QRectF(pt.x()-r, pt.y()-r, r*2, r*2), Qt.AlignmentFlag.AlignCenter, valor)
            if self.distancias or limpio:
                texto = str(n)
                p.setFont(font(max(13, round(9/escala)), True, True))
                ancho = p.fontMetrics().horizontalAdvance(texto)+10
                box = QRectF(pt.x()-ancho/2, pt.y()-r-24, ancho, 21)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(color(PANEL))
                p.drawRoundedRect(box, 3, 3)
                p.setPen(color(tinta))
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
                prev = self.paso.anteriores.get(n, (None,))[0]
                state = "Ciclo negativo" if n in self.paso.afectados else "Final" if self.paso.tipo == "fin" else "Provisional" if d != "∞" else "No alcanzado"
                QToolTip.showText(event.globalPosition().toPoint(),
                    f"Nodo {n}\nDistancia: {d} · {state}\nPredecesor: {prev if prev is not None else '—'}", self)
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
