"""Explorador oscuro con grafo, matrices completas e iteraciones de Floyd."""
from pathlib import Path
import sys

# Permite usar la pantalla compartida al ejecutar este proyecto por separado.
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
from pantalla_carga import TemporizadorCapturas
from dataclasses import replace
import json
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QLabel,QPushButton,QComboBox,QSplitter,QTableWidget,QTableWidgetItem,QAbstractItemView,
    QSlider,QCheckBox,QTabWidget,QListWidget,QFileDialog,QMessageBox,QDialog,
    QDialogButtonBox,QDoubleSpinBox,QHeaderView)
from algoritmo import Grafo, floyd_warshall, numero
from dibujo import Lienzo
from capturas import SesionCapturas
from excel import guardar_excel
from tema import STYLE, INK, MUTED, PANEL, aplicar_paleta

BASE = Path(__file__).resolve().parent


def label(texto, tam=13, bold=False):
    w = QLabel(texto); w.setWordWrap(True)
    w.setStyleSheet(f'font-size: {tam}px; font-weight: {600 if bold else 400};')
    return w


def boton(texto, accion):
    w = QPushButton(texto); w.clicked.connect(accion)
    return w


class Ventana(QMainWindow):
    def __init__(self, ruta=None, capturar=False, carpeta_capturas=None):
        super().__init__()
        self.grafo = Grafo.cargar(ruta or BASE/'grafo.json')
        self.recorrido = floyd_warshall(self.grafo)
        self.indice = 0
        self.carpeta_capturas = carpeta_capturas
        self.lote_pendientes = []
        self.error_captura = False
        self.setWindowTitle('Floyd–Warshall · Explorador de todos los pares')
        self.resize(1540,1000); self.setMinimumSize(1160,760)
        aplicar_paleta(QApplication.instance()); self.setStyleSheet(STYLE)
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(18,12,18,12)
        cabecera = QHBoxLayout()
        marca=label('F L O Y D – W A R S H A L L',21,True)
        marca.setWordWrap(False)
        cabecera.addWidget(marca); cabecera.addStretch()
        self.origen, self.destino = QComboBox(), QComboBox()
        for nombre, combo in [('Origen',self.origen),('Destino',self.destino)]:
            cabecera.addWidget(label(nombre)); cabecera.addWidget(combo)
        cabecera.addWidget(boton('Editar pesos',self.editar_pesos))
        cabecera.addWidget(boton('Abrir JSON',self.abrir_json))
        cabecera.addWidget(boton('Guardar JSON',self.guardar_json))
        root.addLayout(cabecera)
        self.resumen = label(''); root.addWidget(self.resumen)
        self.divisor = QSplitter(Qt.Orientation.Horizontal)
        izquierda = QWidget(); izq = QVBoxLayout(izquierda); izq.setContentsMargins(0,0,10,0)
        inicial = self.recorrido.vista_grafo(self.recorrido.pasos[0],self.grafo.origen,self.grafo.destino)
        self.lienzo = Lienzo(self.grafo,inicial)
        izq.addWidget(self.lienzo,1)
        izq.addWidget(label('Número exterior: nodo · Interior: distancia desde el origen seleccionado',11))
        opciones = QHBoxLayout()
        opciones.addWidget(boton('Encuadrar',self.lienzo.encuadrar))
        opciones.addWidget(label('Rueda: zoom · Arrastrar: mover',11)); izq.addLayout(opciones)
        self.titulo = label('',18,True); izq.addWidget(self.titulo)
        self.explicacion = label(''); izq.addWidget(self.explicacion)
        self.resultado_texto = label('',14,True); izq.addWidget(self.resultado_texto)
        self.divisor.addWidget(izquierda)
        derecha = QWidget(); der = QVBoxLayout(derecha); der.setContentsMargins(0,0,0,0)
        self.matrices = QSplitter(Qt.Orientation.Vertical)
        self.tabla_d, self.tabla_r = QTableWidget(), QTableWidget()
        for tabla, titulo in [(self.tabla_d,'DISTANCIAS D · Costo entre cada par'),
                              (self.tabla_r,'RECORRIDOS R · Último intermedio (o destino directo)')]:
            bloque = QWidget(); lay = QVBoxLayout(bloque); lay.setContentsMargins(0,0,0,0)
            lay.addWidget(label(titulo,12,True)); lay.addWidget(tabla)
            tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            tabla.cellClicked.connect(self.inspeccionar_par)
            self.matrices.addWidget(bloque)
        der.addWidget(self.matrices,1)
        der.addWidget(label('Negritas: cambios · Fondo de fila/columna: k · Clic: explicar un par',11))
        self.par = label(''); der.addWidget(self.par)
        self.divisor.addWidget(derecha); self.divisor.setSizes([720,780]); root.addWidget(self.divisor,1)
        tabs = QTabWidget(); tabs.setMaximumHeight(175)
        self.cambios = QListWidget(); tabs.addTab(self.cambios,'Cambios de la iteración')
        self.historial = QListWidget(); self.historial.currentRowChanged.connect(self.ir_a)
        tabs.addTab(self.historial,'Secuencia')
        codigo = label('Inicializar D con 0, pesos directos o ∞.\n'
                       'Para cada k: para cada i,j, comparar D[i,j] con D[i,k] + D[k,j].\n'
                       'Si mejora: actualizar D y guardar k en R. Al final: revisar D[k,k] < 0.\n'
                       'Un par i,j afectado por un ciclo negativo queda en −∞ y sin recorrido.')
        tabs.addTab(codigo,'Algoritmo'); root.addWidget(tabs)
        fila = QHBoxLayout(); self.contador = label(''); fila.addWidget(self.contador)
        self.timeline = QSlider(Qt.Orientation.Horizontal); self.timeline.valueChanged.connect(self.ir_a)
        fila.addWidget(self.timeline,1); root.addLayout(fila)
        fila = QHBoxLayout()
        fila.addWidget(boton('Inicio',lambda:self.ir_a(0)))
        fila.addWidget(boton('Anterior',lambda:self.ir_a(self.indice-1)))
        self.play = boton('Reproducir',self.alternar); fila.addWidget(self.play)
        fila.addWidget(boton('Siguiente',lambda:self.ir_a(self.indice+1)))
        fila.addWidget(boton('Resultado',lambda:self.ir_a(len(self.recorrido.pasos)-1)))
        self.velocidad = QComboBox()
        for valor in [.5,1,2,4]: self.velocidad.addItem(f'{valor:g}×',valor)
        self.velocidad.setCurrentIndex(1); fila.addWidget(self.velocidad)
        self.automatico = QCheckBox('Capturar iteraciones'); self.automatico.setChecked(capturar)
        self.automatico.toggled.connect(self.cambiar_capturas); fila.addWidget(self.automatico)
        fila.addStretch(); fila.addWidget(boton('Guardar PNG actual',self.guardar_png))
        self.todos = boton('Guardar todos',self.exportar_todo); fila.addWidget(self.todos)
        fila.addWidget(boton('Carpeta PNG',self.abrir_capturas)); root.addLayout(fila)
        pie = QHBoxLayout()
        self.estado = label('',11); pie.addWidget(self.estado,1)
        self.excel_btn = boton('Guardar Excel',self.exportar_excel)
        self.excel_btn.setToolTip('Todas las iteraciones: matrices D y R lado a lado, más el resultado. No requiere PNG.')
        pie.addWidget(self.excel_btn); root.addLayout(pie)
        self.automatico.setToolTip('Guardar PNG al avanzar puede ralentizar la navegación. También puedes usar Guardar todos al terminar.')
        self.reloj = QTimer(self); self.reloj.timeout.connect(self.avanzar)
        self.lote_timer = TemporizadorCapturas(self)
        self.llenar_selectores()
        self.origen.currentIndexChanged.connect(self.cambiar_consulta)
        self.destino.currentIndexChanged.connect(self.cambiar_consulta)
        self.preparar(); self.aplicar(0)

    def llenar_selectores(self):
        for combo, valor in [(self.origen,self.grafo.origen),(self.destino,self.grafo.destino)]:
            combo.blockSignals(True); combo.clear()
            for n in self.recorrido.nodos: combo.addItem(str(n),n)
            combo.setCurrentText(str(valor)); combo.blockSignals(False)

    def preparar(self):
        self.pausar(); self.lote_timer.stop(); self.lote_pendientes=[]; self.error_captura=False
        self.lienzo.grafo=self.grafo
        self.lienzo.origen,self.lienzo.destino=self.origen.currentData(),self.destino.currentData()
        self.capturas=SesionCapturas(self.grafo,self.recorrido,self.lienzo.dibujar,
                                    self.lienzo.origen,self.lienzo.destino,self.carpeta_capturas)
        self.todos.setText('Guardar todos')
        nodos=self.recorrido.nodos
        self.resumen.setText(f'{len(nodos)} nodos · {len(self.grafo.aristas)} aristas · '
                            +('dirigido' if self.grafo.dirigido else 'no dirigido, ambos sentidos')+
                            ' · Todos los pares; origen y destino solo eligen la consulta')
        for tabla in (self.tabla_d,self.tabla_r):
            tabla.setRowCount(len(nodos)); tabla.setColumnCount(len(nodos))
            tabla.setHorizontalHeaderLabels(list(map(str,nodos)))
            tabla.setVerticalHeaderLabels(list(map(str,nodos)))
            tabla.horizontalHeader().setDefaultSectionSize(78)
            tabla.verticalHeader().setDefaultSectionSize(28)
            # Reutilizar las celdas evita crear y destruir dos matrices en cada paso.
            for i in range(len(nodos)):
                for j in range(len(nodos)):
                    if tabla.item(i,j) is None:
                        item=QTableWidgetItem()
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        tabla.setItem(i,j,item)
        self.historial.blockSignals(True); self.historial.clear()
        self.historial.addItems([f'{i+1:02d} · {p.titulo}' for i,p in enumerate(self.recorrido.pasos)])
        self.historial.blockSignals(False)
        self.timeline.blockSignals(True); self.timeline.setRange(0,len(self.recorrido.pasos)-1); self.timeline.blockSignals(False)
        self.indice=0

    def aplicar(self, indice):
        anterior=self.indice
        self.indice=max(0,min(indice,len(self.recorrido.pasos)-1))
        paso=self.recorrido.pasos[self.indice]; nodos=self.recorrido.nodos
        origen,destino=self.origen.currentData(),self.destino.currentData()
        self.lienzo.establecer(self.recorrido.vista_grafo(paso,origen,destino))
        self.titulo.setText(paso.titulo); self.explicacion.setText(paso.texto)
        self.contador.setText(f'Captura {self.indice+1} / {len(self.recorrido.pasos)}')
        self.timeline.blockSignals(True); self.timeline.setValue(self.indice); self.timeline.blockSignals(False)
        self.historial.blockSignals(True); self.historial.setCurrentRow(self.indice); self.historial.blockSignals(False)
        modificados={(c.i,c.j) for c in paso.cambios}
        for tabla,matriz,dist in [(self.tabla_d,paso.distancias,True),(self.tabla_r,paso.recorridos,False)]:
            tabla.setUpdatesEnabled(False)
            tabla.blockSignals(True)
            for i,fila in enumerate(matriz):
                for j,v in enumerate(fila):
                    valor=numero(v) if dist else '—' if v is None else str(v)
                    item=tabla.item(i,j)
                    if item.text()!=valor: item.setText(valor)
                    f=item.font(); f.setBold((i,j) in modificados); item.setFont(f)
                    item.setForeground(QColor(INK if (i,j) in modificados else MUTED))
                    if (i,j) in modificados: item.setBackground(QColor('#31532b'))
                    elif paso.k in (nodos[i],nodos[j]): item.setBackground(QColor('#20372c'))
                    else: item.setBackground(QColor(PANEL))
                    item.setToolTip(f'{nodos[i]} → {nodos[j]}: {valor}')
            tabla.blockSignals(False)
            tabla.setUpdatesEnabled(True)
            if paso.k is not None:
                k=nodos.index(paso.k)
                tabla.scrollToItem(tabla.item(k,k),QAbstractItemView.ScrollHint.PositionAtCenter)
        self.cambios.clear()
        self.cambios.addItems([f'{nodos[c.i]} → {nodos[c.j]} por {paso.k}: '
                              f'{numero(c.izquierda)} + {numero(c.derecha)} = {numero(c.nuevo)} < {numero(c.anterior)}; '
                              f'R = {paso.k}' for c in paso.cambios])
        if not paso.cambios: self.cambios.addItem('Sin cambios de relajación en este estado.')
        i,j=nodos.index(origen),nodos.index(destino)
        ruta,_=self.recorrido.ruta(paso,origen,destino)
        if (i,j) in paso.afectados:
            resultado='Sin mínimo finito: un ciclo negativo afecta el par elegido.'
        elif ruta:
            resultado=('Ruta final: ' if paso.tipo=='fin' else 'Ruta provisional: ')+ ' → '.join(map(str,ruta))
            resultado+=f' · Costo {numero(paso.distancias[i][j])}'
        else: resultado='Sin camino al destino en este estado.'
        self.resultado_texto.setText(resultado); self.inspeccionar_par(i,j)
        if self.indice==len(self.recorrido.pasos)-1: self.pausar()
        if self.automatico.isChecked() and not self.error_captura:
            try:
                self.capturas.guardar(self.indice)
                pendientes=set(self.lote_pendientes)
                pendientes.update(k for k in range(anterior+1,self.indice) if k not in self.capturas.guardados)
                self.lote_pendientes=sorted(pendientes)
                if pendientes: self.lote_timer.start(20); self.todos.setText('Pausar exportación')
            except (OSError,ValueError) as exc: self.fallo(exc)
        self.estado_guardado()

    def inspeccionar_par(self,i,j):
        paso=self.recorrido.pasos[self.indice]; nodos=self.recorrido.nodos
        cambio=next((c for c in paso.cambios if (c.i,c.j)==(i,j)),None)
        if cambio:
            texto=f'{numero(cambio.izquierda)} + {numero(cambio.derecha)} = {numero(cambio.nuevo)} < {numero(cambio.anterior)}: SÍ mejora.'
        elif (i,j) in paso.afectados:
            texto='Un ciclo negativo afecta este par: no hay mínimo finito.'
        elif paso.k is not None:
            k=nodos.index(paso.k); previa=self.recorrido.pasos[self.indice-1].distancias
            texto=f'{numero(previa[i][k])} + {numero(previa[k][j])}: NO mejora {numero(previa[i][j])}.'
        else: texto=f'D = {numero(paso.distancias[i][j])}; R = {paso.recorridos[i][j] if paso.recorridos[i][j] is not None else "—"}.'
        self.par.setText(f'{nodos[i]} → {nodos[j]} · {texto}')

    def ir_a(self,indice):
        self.pausar(); self.aplicar(indice)

    def pausar(self):
        if hasattr(self,'reloj'): self.reloj.stop()
        self.play.setText('Reproducir')

    def alternar(self):
        if self.reloj.isActive(): self.pausar(); return
        if self.indice==len(self.recorrido.pasos)-1: self.aplicar(0)
        self.reloj.start(int(1400/self.velocidad.currentData())); self.play.setText('Pausar')

    def avanzar(self):
        self.aplicar(self.indice+1)

    def cambiar_consulta(self):
        # Floyd ya calculó todos los pares; no hay que repetir el algoritmo.
        actual=self.indice; self.preparar(); self.aplicar(actual)

    def cambiar_capturas(self,activo):
        if not hasattr(self,'capturas'): return
        if activo: self.error_captura=False; self.aplicar(self.indice)
        else: self.lote_timer.stop(); self.lote_pendientes=[]; self.todos.setText('Guardar todos')
        self.estado_guardado()

    def estado_guardado(self):
        self.estado.setText(f'{len(self.capturas.guardados)} / {len(self.recorrido.pasos)} PNG guardados'
                            + (' · exportando…' if self.lote_timer.isActive() else ''))
        self.estado.setToolTip(str(self.capturas.carpeta))

    def exportar_todo(self):
        self.pausar()
        if self.lote_timer.isActive():
            self.lote_timer.stop(); self.todos.setText('Continuar exportación'); self.estado_guardado(); return
        self.error_captura=False
        self.lote_pendientes=[i for i in range(len(self.recorrido.pasos)) if i not in self.capturas.guardados]
        if self.lote_pendientes: self.lote_timer.start(20); self.todos.setText('Pausar exportación')
        self.estado_guardado()

    def procesar_captura(self):
        if not self.lote_pendientes:
            self.lote_timer.stop(); self.todos.setText('Todos guardados'); self.estado_guardado(); return
        try:
            self.capturas.guardar(self.lote_pendientes[0]); self.lote_pendientes.pop(0)
        except (OSError,ValueError) as exc: self.fallo(exc)
        self.estado_guardado()

    def fallo(self,exc):
        self.lote_timer.stop(); self.error_captura=True; self.todos.setText('Reintentar exportación')
        QMessageBox.warning(self,'No se pudo guardar',str(exc))

    def abrir_capturas(self):
        self.capturas.carpeta.mkdir(parents=True,exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.capturas.carpeta)))

    def guardar_png(self):
        ruta,_=QFileDialog.getSaveFileName(self,'Guardar captura',self.capturas.nombre(self.indice),'PNG (*.png)')
        if ruta and not self.capturas.imagen(self.indice).save(ruta,'PNG'):
            QMessageBox.warning(self,'No se pudo guardar','Revisa los permisos y el espacio disponible.')

    def exportar_excel(self):
        self.pausar()
        ruta,_=QFileDialog.getSaveFileName(self,'Guardar matrices de Floyd–Warshall',
                                          str(BASE/'floyd_warshall.xlsx'),'Excel (*.xlsx)')
        if not ruta: return
        destino=Path(ruta)
        if destino.suffix.lower()!='.xlsx': destino=destino.with_suffix('.xlsx')
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            guardar_excel(self.recorrido,destino,self.origen.currentData(),self.destino.currentData())
        except (OSError,ValueError) as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self,'No se pudo guardar Excel',
                                f'{exc}\n\nSi el archivo está abierto en Excel, ciérralo y vuelve a intentarlo.')
            return
        QApplication.restoreOverrideCursor()
        QMessageBox.information(self,'Excel guardado',f'Se guardaron todas las iteraciones y el resultado en:\n{destino}')

    def cargar_grafo(self,grafo):
        self.grafo=grafo; self.recorrido=floyd_warshall(grafo)
        self.llenar_selectores(); self.preparar(); self.lienzo.encuadrar(); self.aplicar(0)

    def abrir_json(self):
        self.pausar()
        ruta,_=QFileDialog.getOpenFileName(self,'Abrir grafo','','JSON (*.json)')
        if not ruta: return
        try:
            g=Grafo.cargar(ruta)
            if g.origen not in g.posiciones or g.destino not in g.posiciones:
                raise ValueError('Origen y destino deben existir.')
            self.cargar_grafo(g)
        except (ValueError,KeyError,TypeError,OSError) as exc:
            QMessageBox.warning(self,'Grafo inválido',str(exc))

    def guardar_json(self):
        ruta,_=QFileDialog.getSaveFileName(self,'Guardar grafo','grafo_floyd_warshall.json','JSON (*.json)')
        if not ruta: return
        data=self.grafo.datos(); data.update(source=self.origen.currentData(),target=self.destino.currentData())
        try: Path(ruta).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        except OSError as exc: QMessageBox.warning(self,'No se pudo guardar',str(exc))

    def editar_pesos(self):
        self.pausar(); dialog=QDialog(self); dialog.setWindowTitle('Pesos del grafo · Floyd–Warshall'); dialog.resize(760,640)
        lay=QVBoxLayout(dialog)
        lay.addWidget(label('Pesos negativos admitidos. En un grafo no dirigido, una arista negativa forma un ciclo negativo.'))
        dirigido=QCheckBox('Dirigido: usar solo el sentido u → v de cada registro'); dirigido.setChecked(self.grafo.dirigido)
        lay.addWidget(dirigido)
        tabla=QTableWidget(len(self.grafo.aristas),4); tabla.setHorizontalHeaderLabels(['ID','u','v','Peso'])
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        controles=[]
        for i,a in enumerate(self.grafo.aristas):
            for col,v in enumerate((a.id,a.u,a.v)): tabla.setItem(i,col,QTableWidgetItem(str(v)))
            spin=QDoubleSpinBox(); spin.setRange(-1e9,1e9); spin.setDecimals(3); spin.setValue(a.peso)
            tabla.setCellWidget(i,3,spin); controles.append(spin)
        lay.addWidget(tabla)
        botones=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(dialog.accept); botones.rejected.connect(dialog.reject); lay.addWidget(botones)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            g=Grafo(dict(self.grafo.posiciones),[replace(a,peso=controles[i].value()) for i,a in enumerate(self.grafo.aristas)],
                    self.origen.currentData(),self.destino.currentData(),dirigido.isChecked())
            self.cargar_grafo(g)

    def closeEvent(self,event):
        self.reloj.stop(); self.lote_timer.stop(); super().closeEvent(event)


def ejecutar(ruta=None):
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion'); fuente=QFont('Segoe UI'); fuente.setPixelSize(13); app.setFont(fuente)
    ventana=Ventana(ruta); ventana.show()
    return app.exec()
