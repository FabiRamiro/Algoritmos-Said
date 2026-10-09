"""Explorador oscuro de Bellman–Ford: cada estado se puede revisar y exportar."""
from dataclasses import replace
from pathlib import Path
import json
import time

from PySide6.QtCore import Qt,QTimer,QUrl
from PySide6.QtGui import QFont,QColor,QShortcut,QKeySequence,QDesktopServices,QPixmap
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,
    QLabel,QPushButton,QComboBox,QCheckBox,QSlider,QSplitter,QTableWidget,QTableWidgetItem,
    QHeaderView,QAbstractItemView,QTabWidget,QListWidget,QScrollArea,QMenu,QFileDialog,
    QMessageBox,QDialog,QDialogButtonBox,QDoubleSpinBox)
from algoritmo import Grafo,bellman_ford,numero
from dibujo import Lienzo
from capturas import SesionCapturas
from tema import BG,PANEL,LINE,INK,MUTED,STYLE,aplicar_paleta

BASE=Path(__file__).resolve().parent


def label(texto='',tam=12,tinta=INK,negrita=False):
    w=QLabel(texto)
    w.setStyleSheet(f'color: {tinta}; font-size: {tam}px; font-weight: {600 if negrita else 400};')
    return w


def boton(texto,accion,estilo=''):
    w=QPushButton(texto)
    w.setObjectName(estilo)
    w.setCursor(Qt.CursorShape.PointingHandCursor)
    w.clicked.connect(accion)
    return w


def tabla(cabeceras):
    w=QTableWidget(0,len(cabeceras))
    w.setHorizontalHeaderLabels(cabeceras)
    w.verticalHeader().hide()
    w.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    w.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    w.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    w.setShowGrid(False)
    w.setAlternatingRowColors(True)
    w.verticalHeader().setDefaultSectionSize(29)
    return w


class Ventana(QMainWindow):
    def __init__(self,ruta=None,capturar=False,carpeta_capturas=None):
        super().__init__()
        self.grafo=Grafo.cargar(ruta or BASE/'grafo.json')
        self.recorrido=bellman_ford(self.grafo,self.grafo.origen,self.grafo.destino)
        self.indice=0
        self.carpeta_capturas=carpeta_capturas
        self.reproduciendo=False
        self.ultimo_avance=time.monotonic()
        self.lote_pendientes=[]
        self.error_captura=False
        self.setWindowTitle('Bellman–Ford · Explorador de relajaciones')
        self.setMinimumSize(1160,760)
        aplicar_paleta(QApplication.instance())
        self.setStyleSheet(STYLE)
        central=QWidget(); self.setCentralWidget(central)
        root=QVBoxLayout(central); root.setContentsMargins(18,12,18,6); root.setSpacing(9)
        self.cabecera(root)
        self.divisor=QSplitter(Qt.Orientation.Vertical)
        self.divisor.setChildrenCollapsible(False)
        self.divisor.setHandleWidth(6)
        root.addWidget(self.divisor,1)
        self.construir_grafo()
        self.construir_detalle()
        self.divisor.setSizes([620,240])
        self.divisor.setStretchFactor(0,1)
        self.divisor.setStretchFactor(1,0)
        self.controles(root,capturar)
        self.lote_timer=QTimer(self)
        self.lote_timer.timeout.connect(self.procesar_captura)
        self.reloj=QTimer(self)
        self.reloj.setInterval(35)
        self.reloj.timeout.connect(self.tick)
        self.reloj.start()
        self.atajos=[]
        for tecla,accion in [('Space',self.alternar),('Left',lambda:self.mover(-1)),
                            ('Right',lambda:self.mover(1)),('Home',lambda:self.ir_a(0)),
                            ('End',self.resultado),('F11',self.pantalla_completa)]:
            atajo=QShortcut(QKeySequence(tecla),self); atajo.activated.connect(accion)
            self.atajos.append(atajo)
        self.preparar_sesion()
        self.aplicar(0)
        screen=QApplication.primaryScreen().availableGeometry()
        self.resize(min(1720,screen.width()-40),min(1050,screen.height()-55))

    def cabecera(self,root):
        fila=QHBoxLayout()
        titulo=QVBoxLayout(); titulo.setSpacing(2)
        titulo.addWidget(label('B E L L M A N – F O R D',19,INK,True))
        self.resumen_grafo=label('',10,MUTED); titulo.addWidget(self.resumen_grafo)
        fila.addLayout(titulo); fila.addStretch()
        self.origen=QComboBox(); self.destino=QComboBox()
        for nombre,combo,valor in [('Origen',self.origen,self.grafo.origen),('Destino',self.destino,self.grafo.destino)]:
            fila.addWidget(label(nombre,11,MUTED))
            for n in sorted(self.grafo.posiciones): combo.addItem(str(n),n)
            combo.setCurrentText(str(valor)); combo.setFixedWidth(75)
            combo.currentIndexChanged.connect(self.recalcular)
            fila.addWidget(combo)
        self.optimizar=QCheckBox('Detener al converger'); self.optimizar.setChecked(True)
        self.optimizar.setToolTip('Detener después de una pasada completa sin mejoras. Desactiva para realizar las |V|−1 pasadas.')
        self.optimizar.toggled.connect(self.recalcular)
        fila.addWidget(self.optimizar)
        fila.addWidget(boton('Editar pesos',self.editar_pesos,'quiet'))
        self.archivos_btn=boton('Archivos',self.archivos,'quiet'); fila.addWidget(self.archivos_btn)
        root.addLayout(fila)

    def construir_grafo(self):
        superior=QSplitter(Qt.Orientation.Horizontal)
        superior.setChildrenCollapsible(False)
        panel=QFrame(); panel.setObjectName('espacioGrafo')
        col=QVBoxLayout(panel); col.setContentsMargins(10,6,10,3)
        fila=QHBoxLayout()
        fila.addWidget(label('Identificador arriba · distancia d dentro del nodo',10,MUTED)); fila.addStretch()
        self.pesos=QCheckBox('Pesos'); self.pesos.setChecked(True)
        self.distancias=QCheckBox('Distancias'); self.distancias.setChecked(True)
        fila.addWidget(self.pesos); fila.addWidget(self.distancias)
        fila.addWidget(boton('Encuadrar',lambda:self.lienzo.encuadrar(),'quiet'))
        col.addLayout(fila)
        self.lienzo=Lienzo(self.grafo,self.recorrido.pasos[0])
        self.pesos.toggled.connect(lambda b:self.visual('pesos',b))
        self.distancias.toggled.connect(lambda b:self.visual('distancias',b))
        self.lienzo.seleccionado.connect(self.inspeccionar)
        col.addWidget(self.lienzo,1)
        self.inspector=label('Rueda: zoom · arrastrar: mover · clic: inspeccionar',10,MUTED)
        col.addWidget(self.inspector)
        superior.addWidget(panel)
        lateral=QWidget(); lateral.setMinimumWidth(290)
        c=QVBoxLayout(lateral); c.setContentsMargins(8,4,0,0)
        c.addWidget(label('LISTA DE ARCOS',12,INK,True))
        self.arco_estado=label('',10,MUTED); c.addWidget(self.arco_estado)
        self.arcos_tabla=tabla(['#','(u, v)','w','ID'])
        self.arcos_tabla.cellClicked.connect(self.saltar_arco)
        self.arcos_tabla.setToolTip('Clic para ir a este arco en la pasada actual.')
        c.addWidget(self.arcos_tabla,1)
        c.addWidget(label('Orden estable: u, v e identificador',10,MUTED))
        superior.addWidget(lateral)
        superior.setSizes([1200,310])
        superior.setStretchFactor(0,1); superior.setStretchFactor(1,0)
        self.divisor.addWidget(superior)

    def construir_detalle(self):
        self.detalle=QSplitter(Qt.Orientation.Horizontal)
        self.detalle.setChildrenCollapsible(False)
        self.detalle.setMinimumHeight(245)
        self.tabs=QTabWidget(); self.tabs.setMinimumWidth(390)
        self.vector=QTableWidget(3,0)
        self.vector.setVerticalHeaderLabels(['V[ ]','d[ ]','Π[ ]'])
        self.vector.horizontalHeader().hide()
        self.vector.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vector.setShowGrid(False)
        self.vector.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        p=QWidget(); v=QVBoxLayout(p); v.setContentsMargins(8,8,8,8)
        v.addWidget(label('V: nodos · d: distancias · Π: predecesores',11,MUTED))
        v.addWidget(self.vector,1)
        v.addWidget(label('Las distancias pueden cambiar en cualquier pasada.',10,MUTED))
        self.tabs.addTab(p,'Arreglos')
        self.historial=QListWidget(); self.historial.setObjectName('secuencia')
        self.historial.currentRowChanged.connect(self.ir_a)
        self.tabs.addTab(self.historial,'Micro pasos')
        codigo=QLabel('d[origen] = 0; resto = ∞; Π = vacío\n\n'
                      'repetir hasta |V| − 1 pasadas:\n'
                      '  para cada arco (u, v):\n'
                      '    si d[u] ≠ ∞ y d[v] > d[u] + w(u,v):\n'
                      '      d[v] = d[u] + w(u,v)\n'
                      '      Π[v] = u\n\n'
                      'revisar otra vez: detectar ciclos negativos\n'
                      'seguir Π para reconstruir la ruta')
        codigo.setStyleSheet('font: 12px Consolas; padding: 12px;')
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(codigo)
        self.tabs.addTab(scroll,'Algoritmo')
        self.ruta=label('',16,INK,True); self.ruta.setWordWrap(True)
        self.ruta.setContentsMargins(12,12,12,12)
        self.tabs.addTab(self.ruta,'Resultado')
        self.detalle.addWidget(self.tabs)
        decision=QFrame(); decision.setObjectName('card')
        b=QVBoxLayout(decision); b.setContentsMargins(16,10,16,10); b.setSpacing(5)
        self.etapa=label('',11,MUTED,True); b.addWidget(self.etapa)
        self.titulo=label('',17,INK,True); self.titulo.setWordWrap(True); b.addWidget(self.titulo)
        fila=QHBoxLayout(); fila.addWidget(label('PREGUNTA',10,MUTED,True))
        self.pregunta=label('',15,INK,True); self.pregunta.setWordWrap(True); fila.addWidget(self.pregunta,1)
        b.addLayout(fila)
        self.comparacion=label('',12,MUTED); self.comparacion.setWordWrap(True); b.addWidget(self.comparacion)
        fila=QHBoxLayout(); fila.addWidget(label('RESPUESTA',10,MUTED,True))
        self.respuesta=label('',15,INK,True); fila.addWidget(self.respuesta,1); b.addLayout(fila)
        self.proceso=label('',13,INK); self.proceso.setWordWrap(True); b.addWidget(self.proceso)
        self.explicacion=label('',11,MUTED); self.explicacion.setWordWrap(True); b.addWidget(self.explicacion)
        self.detalle.addWidget(decision)
        self.detalle.setSizes([650,850])
        self.divisor.addWidget(self.detalle)

    def controles(self,root,capturar):
        fila=QHBoxLayout()
        self.contador=label('',11,INK,True); self.contador.setMinimumWidth(225); fila.addWidget(self.contador)
        self.timeline=QSlider(Qt.Orientation.Horizontal)
        self.timeline.sliderPressed.connect(self.pausar); self.timeline.valueChanged.connect(self.ir_a)
        fila.addWidget(self.timeline,1); root.addLayout(fila)
        fila=QHBoxLayout()
        fila.addWidget(boton('Inicio',lambda:self.ir_a(0),'quiet'))
        self.anterior_btn=boton('Anterior',lambda:self.mover(-1)); fila.addWidget(self.anterior_btn)
        self.play_btn=boton('Reproducir',self.alternar,'primary'); self.play_btn.setMinimumWidth(124); fila.addWidget(self.play_btn)
        self.siguiente_btn=boton('Siguiente',lambda:self.mover(1)); fila.addWidget(self.siguiente_btn)
        fila.addWidget(boton('Resultado',self.resultado,'quiet')); fila.addStretch()
        self.modo=QComboBox()
        for nombre,valor in [('Cada micro paso','micro'),('Por arco','arco'),('Por pasada','pasada'),('Pasos del PDF','pdf')]:
            self.modo.addItem(nombre,valor)
        self.modo.setCurrentIndex(3)
        fila.addWidget(self.modo)
        self.velocidad=QComboBox()
        for valor in [.5,1,2,4]: self.velocidad.addItem(f'{valor:g}×',valor)
        self.velocidad.setCurrentIndex(1); fila.addWidget(self.velocidad)
        root.addLayout(fila)
        fila=QHBoxLayout()
        self.automatico=QCheckBox('Capturar pasos del PDF'); self.automatico.setChecked(capturar)
        self.automatico.setToolTip('Guardar PNG al avanzar puede ralentizar la navegación. También puedes usar Guardar todos al terminar.')
        self.automatico.toggled.connect(self.cambiar_capturas); fila.addWidget(self.automatico)
        self.estado_capturas=label('',10,MUTED); fila.addWidget(self.estado_capturas,1)
        fila.addWidget(boton('Carpeta PNG',self.abrir_capturas,'quiet'))
        self.todos_btn=boton('Guardar todos',self.exportar_todo,'quiet'); fila.addWidget(self.todos_btn)
        root.addLayout(fila)

    def preparar_sesion(self):
        self.lote_timer.stop(); self.lote_pendientes=[]; self.error_captura=False
        self.capturas=SesionCapturas(self.grafo,self.recorrido,self.lienzo.dibujar,self.carpeta_capturas)
        self.todos_btn.setText('Guardar todos')
        self.lienzo.grafo=self.grafo
        self.lienzo.origen,self.lienzo.destino=self.recorrido.origen,self.recorrido.destino
        self.lienzo.elegido=None; self.lienzo.hover=None
        self.lienzo.encuadrar()
        self.timeline.blockSignals(True); self.timeline.setRange(0,len(self.recorrido.pasos)-1); self.timeline.blockSignals(False)
        self.historial.blockSignals(True); self.historial.clear()
        self.historial.addItems([f'{i+1:05d}  ·  {p.codigo}  ·  {p.titulo}' for i,p in enumerate(self.recorrido.pasos)])
        self.historial.blockSignals(False)
        self.indices_arco={(p.pasada,p.indice_arco):i for i,p in enumerate(self.recorrido.pasos) if p.tipo=='arco'}
        self.arcos_tabla.setRowCount(len(self.grafo.arcos))
        for i,a in enumerate(self.grafo.arcos):
            for col,valor in enumerate([str(i+1),f'({a.u}, {a.v})',numero(a.peso),a.arista]):
                item=QTableWidgetItem(valor); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.arcos_tabla.setItem(i,col,item)
        self.nodos=sorted(self.grafo.posiciones); self.vector.setColumnCount(len(self.nodos))
        for col in range(len(self.nodos)): self.vector.setColumnWidth(col,62)
        self.resumen_grafo.setText(f'{len(self.nodos)} nodos · {len(self.grafo.aristas)} aristas · {len(self.grafo.arcos)} arcos · '
                                   + ('dirigido' if self.grafo.dirigido else 'no dirigido, ambos sentidos'))
        self.indice=0
        self.estado_guardado()

    def recalcular(self,*args):
        if not hasattr(self,'lote_timer'): return
        self.pausar()
        self.recorrido=bellman_ford(self.grafo,self.origen.currentData(),self.destino.currentData(),self.optimizar.isChecked())
        self.preparar_sesion(); self.aplicar(0)

    def aplicar(self,i):
        anterior=self.indice
        self.indice=max(0,min(i,len(self.recorrido.pasos)-1)); p=self.capturas.paso_presentacion(self.indice)
        self.lienzo.establecer(p)
        self.timeline.blockSignals(True); self.timeline.setValue(self.indice); self.timeline.blockSignals(False)
        self.contador.setText(f'Paso {p.codigo}  ·  {self.capturas.etiqueta(self.indice)}')
        self.etapa.setText(f'PASADA {p.pasada}  /  {max(0,len(self.nodos)-1)}   ·   MEJORAS EN ESTA PASADA: {p.cambios}')
        self.titulo.setText(p.titulo); self.pregunta.setText(p.pregunta)
        self.comparacion.setText('Valores previos: '+p.comparacion if p.indice_arco is not None else p.comparacion)
        self.respuesta.setText(p.respuesta); self.proceso.setText('PROCESO  ·  '+p.proceso)
        self.explicacion.setText(p.texto)
        if p.indice_arco is not None:
            self.arcos_tabla.selectRow(p.indice_arco)
            self.arcos_tabla.scrollToItem(self.arcos_tabla.item(p.indice_arco,0),QAbstractItemView.ScrollHint.PositionAtCenter)
            self.arco_estado.setText(f'› Actual: {p.indice_arco+1} / {len(self.grafo.arcos)} · {p.arista}')
        else:
            self.arcos_tabla.clearSelection(); self.arco_estado.setText(f'{len(self.grafo.arcos)} arcos por pasada')
        for col,n in enumerate(self.nodos):
            prev=p.anteriores.get(n,(None,))[0]
            for row,valor in enumerate([str(n),numero(p.distancias[n]),str(prev) if prev is not None else '—']):
                item=QTableWidgetItem(valor); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QColor(INK if n in (p.actual,p.vecino) else MUTED))
                if n==p.vecino: item.setBackground(QColor('#24543a'))
                self.vector.setItem(row,col,item)
        if p.vecino in self.nodos:
            self.vector.scrollToItem(self.vector.item(1,self.nodos.index(p.vecino)))
        self.historial.blockSignals(True); self.historial.setCurrentRow(self.indice); self.historial.blockSignals(False)
        if p.tipo=='fin':
            self.ruta.setText(p.titulo+'\n\n'+p.proceso+f'\n\nCosto: {numero(self.recorrido.costo)} · Pasadas: {self.recorrido.pasadas}')
        else:
            self.ruta.setText('El resultado aparece al terminar las pasadas y el control de ciclos negativos.')
        self.anterior_btn.setEnabled(self.indice>0)
        self.siguiente_btn.setEnabled(self.indice<len(self.recorrido.pasos)-1)
        if self.indice==len(self.recorrido.pasos)-1: self.pausar()
        self.inspeccionar(self.lienzo.elegido)
        if self.automatico.isChecked() and not self.error_captura:
            self.guardar_actual()
            if self.indice>anterior+1 and not self.error_captura:
                pendientes=set(self.lote_pendientes)
                pendientes.update(k for k in self.capturas.indices if anterior<k<self.indice and k not in self.capturas.guardados)
                self.lote_pendientes=sorted(pendientes)
                if self.lote_pendientes:
                    self.lote_timer.start(20); self.todos_btn.setText('Pausar exportación'); self.estado_guardado()

    def ir_a(self,i):
        self.pausar(); self.aplicar(i)

    def proximo(self,delta):
        i=self.indice+delta
        modo=self.modo.currentData()
        if modo=='pdf':
            while 0<i<len(self.recorrido.pasos)-1 and i not in self.capturas.numeros: i+=delta
            return i
        tipos=('arco','verificar_arco','fin') if modo=='arco' else ('pasada','verificar','fin')
        if modo!='micro':
            while 0<i<len(self.recorrido.pasos)-1 and self.recorrido.pasos[i].tipo not in tipos: i+=delta
        return i

    def mover(self,delta):
        self.ir_a(self.proximo(delta))

    def resultado(self):
        self.ir_a(len(self.recorrido.pasos)-1)

    def pausar(self):
        self.reproduciendo=False
        if hasattr(self,'play_btn'): self.play_btn.setText('Reproducir')

    def alternar(self):
        if self.reproduciendo: self.pausar(); return
        if self.indice==len(self.recorrido.pasos)-1: self.aplicar(0)
        self.reproduciendo=True; self.ultimo_avance=time.monotonic(); self.play_btn.setText('Pausar')

    def tick(self):
        if self.reproduciendo and QApplication.activeModalWidget() is None and time.monotonic()-self.ultimo_avance>1.35/self.velocidad.currentData():
            self.aplicar(self.proximo(1)); self.ultimo_avance=time.monotonic()

    def pantalla_completa(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def saltar_arco(self,row,col):
        p=self.recorrido.pasos[self.indice]
        i=self.indices_arco.get((max(1,p.pasada),row))
        if i is not None: self.ir_a(i)

    def visual(self,atributo,valor):
        setattr(self.lienzo,atributo,valor); self.lienzo.update()

    def inspeccionar(self,n):
        if n is None:
            self.inspector.setText('Rueda: zoom · arrastrar: mover · clic: inspeccionar'); return
        p=self.recorrido.pasos[self.indice]; prev=p.anteriores.get(n,(None,))[0]
        self.inspector.setText(f'NODO {n}  ·  d = {numero(p.distancias[n])}  ·  Π = {prev if prev is not None else "—"}')

    def cambiar_capturas(self,activo):
        if not hasattr(self,'lote_timer'): return
        if activo: self.error_captura=False; self.guardar_actual()
        else:
            self.lote_timer.stop(); self.lote_pendientes=[]; self.todos_btn.setText('Guardar todos')
        self.estado_guardado()

    def estado_guardado(self):
        self.estado_capturas.setText(f'{len(self.capturas.guardados):,} PNG guardados'+(' · exportando…' if self.lote_timer.isActive() else ''))
        self.estado_capturas.setToolTip(str(self.capturas.carpeta))

    def guardar_actual(self):
        if self.indice not in self.capturas.numeros: return
        try:
            self.capturas.guardar(self.indice); self.estado_guardado()
        except (OSError,ValueError) as exc: self.error_guardado(exc)

    def error_guardado(self,exc):
        self.lote_timer.stop(); self.error_captura=True
        self.todos_btn.setText('Reintentar exportación'); self.estado_capturas.setText('No se pudo guardar')
        QMessageBox.warning(self,'No se pudo guardar',str(exc))

    def exportar_todo(self):
        self.pausar()
        if self.lote_timer.isActive():
            self.lote_timer.stop(); self.todos_btn.setText('Continuar exportación'); self.estado_guardado(); return
        self.error_captura=False
        self.lote_pendientes=[i for i in self.capturas.indices if i not in self.capturas.guardados]
        if self.lote_pendientes: self.lote_timer.start(20); self.todos_btn.setText('Pausar exportación')
        self.estado_guardado()

    def procesar_captura(self):
        if not self.lote_pendientes:
            self.lote_timer.stop(); self.todos_btn.setText('Todos guardados'); self.estado_guardado(); return
        try:
            self.capturas.guardar(self.lote_pendientes.pop(0)); self.estado_guardado()
        except (OSError,ValueError) as exc: self.error_guardado(exc)

    def abrir_capturas(self):
        self.capturas.carpeta.mkdir(parents=True,exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.capturas.carpeta)))

    def archivos(self):
        self.pausar(); menu=QMenu(self)
        menu.addAction('Guardar captura actual',self.guardar_png)
        menu.addAction('Guardar todos los pasos',self.exportar_todo)
        menu.addAction('Abrir grafo JSON',self.abrir_json)
        menu.addAction('Guardar grafo JSON',self.guardar_json)
        menu.addAction('Ver fotografía original',self.ver_foto)
        menu.exec(self.archivos_btn.mapToGlobal(self.archivos_btn.rect().bottomLeft()))

    def guardar_png(self):
        ruta,_=QFileDialog.getSaveFileName(self,'Guardar captura',self.capturas.nombre(self.indice),'PNG (*.png)')
        if ruta and not self.capturas.imagen(self.indice).save(ruta,'PNG'):
            QMessageBox.warning(self,'No se pudo guardar','Revisa la carpeta seleccionada.')

    def abrir_json(self):
        ruta,_=QFileDialog.getOpenFileName(self,'Abrir grafo','','JSON (*.json)')
        if not ruta: return
        try:
            g=Grafo.cargar(ruta); bellman_ford(g,g.origen,g.destino)
        except (ValueError,KeyError,TypeError,OSError) as exc:
            QMessageBox.warning(self,'Grafo inválido',str(exc)); return
        self.grafo=g
        for combo,valor in [(self.origen,g.origen),(self.destino,g.destino)]:
            combo.blockSignals(True); combo.clear()
            for n in sorted(g.posiciones): combo.addItem(str(n),n)
            combo.setCurrentText(str(valor)); combo.blockSignals(False)
        self.recalcular()

    def guardar_json(self):
        ruta,_=QFileDialog.getSaveFileName(self,'Guardar grafo','grafo_bellman_ford.json','JSON (*.json)')
        if not ruta: return
        data=self.grafo.datos(); data.update(source=self.recorrido.origen,target=self.recorrido.destino)
        try: Path(ruta).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        except OSError as exc: QMessageBox.warning(self,'No se pudo guardar',str(exc))

    def editar_pesos(self):
        self.pausar(); dialog=QDialog(self); dialog.setWindowTitle('Pesos del grafo · Bellman–Ford'); dialog.resize(760,640)
        c=QVBoxLayout(dialog)
        info=label('Bellman–Ford admite pesos negativos. En un grafo no dirigido, una arista negativa permite un ciclo negativo.',12,MUTED)
        info.setWordWrap(True); c.addWidget(info)
        dirigido=QCheckBox('Grafo dirigido (usar solo el sentido u → v de cada registro)'); dirigido.setChecked(self.grafo.dirigido)
        c.addWidget(dirigido)
        t=tabla(['ID','u','v','Peso']); t.setRowCount(len(self.grafo.aristas)); controles=[]
        for i,a in enumerate(self.grafo.aristas):
            for col,texto in enumerate([a.id,str(a.u),str(a.v)]): t.setItem(i,col,QTableWidgetItem(texto))
            spin=QDoubleSpinBox(); spin.setRange(-1e9,1e9); spin.setDecimals(3); spin.setValue(a.peso)
            t.setCellWidget(i,3,spin); controles.append(spin)
        c.addWidget(t,1)
        botones=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(dialog.accept); botones.rejected.connect(dialog.reject); c.addWidget(botones)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            self.grafo=Grafo(dict(self.grafo.posiciones),[replace(a,peso=controles[i].value()) for i,a in enumerate(self.grafo.aristas)],
                             self.origen.currentData(),self.destino.currentData(),dirigido.isChecked())
            self.recalcular()

    def ver_foto(self):
        dialog=QDialog(self); dialog.setWindowTitle('Grafo original'); dialog.resize(1050,750)
        v=QVBoxLayout(dialog); scroll=QScrollArea(); img=QLabel(); img.setPixmap(QPixmap(str(BASE/'grafo_original.jpeg')))
        scroll.setWidget(img); v.addWidget(scroll); dialog.exec()


def ejecutar(ruta=None):
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion'); f=QFont('Segoe UI'); f.setPixelSize(13); app.setFont(f)
    ventana=Ventana(ruta); ventana.show()
    return app.exec()
