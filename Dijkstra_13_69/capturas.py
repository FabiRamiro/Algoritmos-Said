"""Capturas oscuras del grafo y una explicación breve del paso actual."""
from datetime import datetime
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QFont, QPen

from tema import BG, PANEL, LINE, INK, MUTED
from algoritmo import numero


class SesionCapturas:
    def __init__(self, grafo, recorrido, dibujar_grafo, carpeta_base=None):
        self.grafo = grafo
        self.recorrido = recorrido
        self.dibujar_grafo = dibujar_grafo
        base = Path(carpeta_base) if carpeta_base else Path(__file__).parent / "capturas"
        sello = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        self.carpeta = base / f"{sello}_{recorrido.origen}-{recorrido.destino}"
        self.guardados = set()
        self.preparada = False
        # Una captura contiene toda la relajación: cálculo, decisión y resultado.
        # Los vecinos fijados y las operaciones de cola quedan en los micropasos.
        tipos = {'origen', 'fijar', 'predecesor', 'mantener', 'fin', 'sin_ruta'}
        self.indices = tuple(i for i, paso in enumerate(recorrido.pasos)
                             if paso.tipo in tipos)
        self.numeros = {indice: n for n, indice in enumerate(self.indices, 1)}
        # Conservar los datos previos permite explicar una mejora aunque el
        # estado que dibujamos ya tenga la distancia y el predecesor nuevos.
        self.antes = {}
        comparacion = None
        for i, paso in enumerate(recorrido.pasos):
            if paso.tipo == 'comparar':
                comparacion = paso
            elif paso.tipo in ('predecesor', 'mantener'):
                self.antes[i] = comparacion

    def etiqueta(self, indice):
        if indice in self.numeros:
            return f'{self.numeros[indice]} / {len(self.indices)}'
        return f'MICROPASO {indice+1} / {len(self.recorrido.pasos)}'

    def paso_presentacion(self, indice):
        paso = self.recorrido.pasos[indice]
        if paso.tipo == 'origen':
            paso = replace(paso, titulo='Inicializamos el recorrido',
                           texto=f'Origen {self.recorrido.origen}; destino {self.recorrido.destino}. '
                                 'El origen comienza en cero, los demás nodos en infinito y los predecesores vacíos.')
        elif paso.tipo in ('predecesor', 'mantener'):
            antes = self.antes[indice]
            u, v = paso.actual, paso.vecino
            peso = self.grafo.por_id[paso.arista].peso
            candidato = antes.distancias[u] + peso
            anterior = antes.distancias[v]
            mejora = paso.tipo == 'predecesor'
            previo = paso.anteriores.get(v, (None,))[0]
            calculo = f'{numero(antes.distancias[u])} + {numero(peso)} = {numero(candidato)}'
            decision = ('Sí mejora: actualizamos distancia y predecesor.' if mejora
                        else 'No mejora: conservamos distancia y predecesor.')
            paso = replace(paso, titulo=f'Examinamos {u} → {v}: '+('actualizar' if mejora else 'sin cambio'),
                           texto=f'Arista {paso.arista}, peso {numero(peso)}. Costo por este camino: {calculo}. '
                                 f'{decision}',
                           formula=f'{numero(candidato)} < {numero(anterior)}: '+('SÍ' if mejora else 'NO')+
                                   f'\nd[{v}]: {numero(anterior)} → {numero(paso.distancias[v])}'
                                   f'\nprevio[{v}] = {previo if previo is not None else "—"}')
        return paso

    def nombre(self, indice):
        prefijo = (f'captura_{self.numeros[indice]:04d}' if indice in self.numeros
                   else f'micropaso_{indice+1:04d}')
        return f"{prefijo}_{self.recorrido.pasos[indice].tipo}.png"

    def preparar(self):
        if self.preparada:
            return
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.preparada = True

    def guardar(self, indice):
        if indice not in self.numeros:
            return None
        if indice in self.guardados:
            return self.carpeta / self.nombre(indice)
        self.preparar()
        destino = self.carpeta / self.nombre(indice)
        temporal = destino.with_suffix(".tmp")
        # Reemplazar solo cuando Qt terminó de escribir la imagen completa.
        if not self.imagen(indice).save(str(temporal), "PNG"):
            raise OSError(f"No fue posible guardar {destino}")
        temporal.replace(destino)
        self.guardados.add(indice)
        return destino

    def imagen(self, indice):
        paso = self.paso_presentacion(indice)
        imagen = QImage(1920, 1240, QImage.Format.Format_RGB32)
        imagen.fill(QColor(PANEL))
        # Los mismos datos visibles quedan disponibles al inspeccionar el PNG.
        imagen.setText("Paso", self.etiqueta(indice))
        imagen.setText("Acción", paso.titulo)
        imagen.setText("Explicación", paso.texto)
        imagen.setText("Operación", paso.formula)
        painter = QPainter(imagen)
        try:
            self.dibujar_grafo(painter, QRectF(24, 16, 1872, 980),
                               paso=paso, limpio=True)
            self.dibujar_explicacion(painter, indice)
        finally:
            painter.end()
        return imagen

    def dibujar_explicacion(self, painter, indice):
        """Pie separado del lienzo: la explicación nunca tapa nodos ni aristas."""
        paso = self.paso_presentacion(indice)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.fillRect(QRectF(0, 1014, 1920, 226), QColor(BG))
        painter.setPen(QPen(QColor(LINE), 1))
        painter.drawLine(36, 1014, 1884, 1014)

        def texto(rect, contenido, size, tinta, bold=False):
            fuente = QFont("Segoe UI")
            fuente.setPixelSize(size)
            fuente.setBold(bold)
            painter.setFont(fuente)
            painter.setPen(QColor(tinta))
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                             | Qt.TextFlag.TextWordWrap, contenido)

        texto(QRectF(42, 1032, 1300, 28),
              f"CAPTURA {self.etiqueta(indice)}", 18, MUTED, True)
        texto(QRectF(42, 1070, 1320, 45), paso.titulo, 31, INK, True)
        texto(QRectF(42, 1126, 1320, 84), paso.texto, 22, MUTED)
        if paso.formula:
            painter.setPen(QPen(QColor(LINE), 1))
            painter.drawLine(1420, 1044, 1420, 1200)
            texto(QRectF(1450, 1050, 425, 146), paso.formula, 24, INK, True)
