"""Capturas completas: grafo, todos los arcos, V/d/Π y la relajación actual."""
from datetime import datetime
from dataclasses import replace
from math import ceil
from pathlib import Path
import json

from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from algoritmo import numero
from tema import BG,PANEL,LINE,INK,MUTED,GREEN


class SesionCapturas:
    def __init__(self,grafo,recorrido,dibujar_grafo,carpeta_base=None):
        self.grafo,self.recorrido,self.dibujar_grafo=grafo,recorrido,dibujar_grafo
        base=Path(carpeta_base) if carpeta_base else Path(__file__).resolve().parent/'capturas'
        self.carpeta=base/f"{datetime.now():%Y-%m-%d_%H-%M-%S_%f}_{recorrido.origen}-{recorrido.destino}"
        self.guardados=set()
        # El PDF guarda una decisión NO, o dos estados si la respuesta es SÍ:
        # antes y después de actualizar juntos d y Π. No exporta micropasos.
        tipos={'inicio','origen','decision','predecesor','mantener','omitir','verificar','fin'}
        self.indices=tuple(i for i,p in enumerate(recorrido.pasos) if p.tipo in tipos)
        self.numeros={i:n for n,i in enumerate(self.indices,1)}

    def paso_presentacion(self,i):
        """Prepara el contenido de la diapositiva sin alterar el cálculo original."""
        paso=self.recorrido.pasos[i]
        if paso.tipo in ('decision','predecesor','mantener','omitir'):
            paso=replace(paso,titulo=f'Aplicar Relax al arco ({paso.actual}, {paso.vecino})')
        if paso.tipo=='omitir':
            paso=replace(paso,respuesta='NO',proceso='No se hace nada: el nodo de salida aún está en infinito.')
        if paso.tipo=='verificar':
            afectados=self.recorrido.afectados
            paso=replace(paso,titulo='Verificación final de todos los arcos',
                         pregunta='¿d[v] ≤ d[u] + w(u, v) en todos los arcos alcanzables?',
                         comparacion=f'Se revisaron {len(self.grafo.arcos)} arcos sin modificar d ni Π.',
                         respuesta='NO · CICLO NEGATIVO' if afectados else 'SÍ',
                         proceso=('Hay un ciclo negativo alcanzable. Nodos afectados: '+
                                  ', '.join(map(str,sorted(afectados)))) if afectados else 'Las distancias cumplen la condición final.',
                         texto='El resultado siguiente muestra los costos finales y la ruta, cuando existe un mínimo finito.')
        return paso

    def etiqueta(self,i):
        return (f'{self.numeros[i]:05d} / {len(self.indices):05d}' if i in self.numeros
                else f'MICROPASO {i+1:05d}')

    def nombre(self,i):
        p=self.recorrido.pasos[i]
        prefijo=f'captura_{self.numeros[i]:06d}' if i in self.numeros else f'micropaso_{i+1:06d}'
        return f"{prefijo}_p{p.pasada:02d}_a{(p.indice_arco+1) if p.indice_arco is not None else 0:03d}_{p.tipo}.png"

    def guardar(self,i):
        if i not in self.numeros:
            return None
        destino=self.carpeta/self.nombre(i)
        if i in self.guardados and destino.exists():
            return destino
        self.carpeta.mkdir(parents=True,exist_ok=True)
        temporal=destino.with_suffix('.tmp')
        if not self.imagen(i).save(str(temporal),'PNG'):
            raise OSError(f"No se pudo escribir {destino}")
        temporal.replace(destino)
        self.guardados.add(i)
        return destino

    def imagen(self,i):
        paso=self.paso_presentacion(i)
        nodos=sorted(self.grafo.posiciones)
        filas_arcos=max(1,ceil(len(self.grafo.arcos)/3))
        alto_superior=max(1190,filas_arcos*26+92)
        bloques=ceil(len(nodos)/15)
        alto_inferior=max(626,bloques*160+150)
        inferior=128+alto_superior+24
        imagen=QImage(3200,inferior+alto_inferior+32,QImage.Format.Format_RGB32)
        imagen.fill(QColor(BG))
        for clave,valor in {'Paso':self.etiqueta(i),'Código':paso.codigo,
                            'Pregunta':paso.pregunta,'Comparación':paso.comparacion,
                            'Respuesta':paso.respuesta,'Proceso':paso.proceso,
                            'V':json.dumps(nodos),'d':json.dumps([numero(paso.distancias[n]) for n in nodos]),
                            'Π':json.dumps([paso.anteriores.get(n,(None,))[0] for n in nodos]),
                            'Arcos':json.dumps([(a.arista,a.u,a.v,a.peso) for a in self.grafo.arcos])}.items():
            imagen.setText(clave,valor)
        p=QPainter(imagen)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        def texto(x,y,w,h,contenido,size=22,tinta=INK,bold=False,centrado=False):
            f=QFont('Segoe UI'); f.setPixelSize(size); f.setBold(bold)
            p.setFont(f); p.setPen(QColor(tinta))
            alineacion=Qt.AlignmentFlag.AlignCenter if centrado else Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter
            p.drawText(QRectF(x,y,w,h),alineacion|Qt.TextFlag.TextWordWrap,str(contenido))

        def panel(x,y,w,h):
            p.setPen(QPen(QColor(LINE),1)); p.setBrush(QColor(PANEL))
            p.drawRoundedRect(QRectF(x,y,w,h),12,12)

        try:
            texto(32,22,1000,36,'B E L L M A N – F O R D',26,INK,True)
            texto(32,66,2136,38,f'{self.recorrido.origen} → {self.recorrido.destino}  ·  '
                  f'Pasada {paso.pasada}  ·  {paso.titulo}',23,MUTED)
            texto(2340,30,828,58,f'CAPTURA {self.etiqueta(i)}',24,INK,True)
            panel(32,128,2136,alto_superior)
            # El mismo lienzo se dibuja completo, sin heredar zoom, ratón ni selección.
            self.dibujar_grafo(p,QRectF(46,166,2108,alto_superior-76),paso=paso,limpio=True)
            texto(54,136,2070,28,'NÚMERO SOBRE EL NODO = IDENTIFICADOR    ·    VALOR INTERIOR = d[nodo]',16,MUTED)
            panel(2192,128,976,alto_superior)
            texto(2214,141,924,34,f'LISTA COMPLETA DE ARCOS  /  {len(self.grafo.arcos)}',22,INK,True)
            texto(2214,179,924,26,'Orden: salida, llegada e ID · cada sentido se revisa por separado',16,MUTED)
            ancho_col=310
            for k,a in enumerate(self.grafo.arcos):
                col,fila=divmod(k,filas_arcos)
                x=2212+col*ancho_col; y=220+fila*26
                activo=k==paso.indice_arco
                if activo:
                    p.fillRect(QRectF(x-3,y,304,26),QColor('#24543a'))
                    p.fillRect(QRectF(x-3,y,3,26),QColor('#4ade80'))
                marca='›' if activo else ' '
                texto(x+4,y,296,26,f'{marca}{k+1:03d}  ({a.u}, {a.v})  w={numero(a.peso)}  {a.arista}',
                      16,GREEN if activo else MUTED,activo)

            panel(32,inferior,1560,alto_inferior)
            texto(56,inferior+18,1500,40,'ARREGLOS  /  ESTADO DE ESTE PASO',24,INK,True)
            texto(56,inferior+64,1500,34,'V = nodos   ·   d = distancias   ·   Π = predecesores',21,MUTED)
            for bloque in range(bloques):
                subset=nodos[bloque*15:(bloque+1)*15]
                yy=inferior+122+bloque*160
                for fila,etiqueta in enumerate(('V[ ]','d[ ]','Π[ ]')):
                    texto(52,yy+fila*42,84,40,etiqueta,22,INK,True)
                    for col,n in enumerate(subset):
                        x=142+col*95
                        activo=n==paso.vecino
                        if activo:
                            p.fillRect(QRectF(x,yy+fila*42,91,40),QColor('#24543a'))
                        previo=paso.anteriores.get(n,(None,))[0]
                        valor=str(n) if fila==0 else numero(paso.distancias[n]) if fila==1 else str(previo) if previo is not None else '—'
                        # Las cifras extensas se reducen, nunca se sustituyen por puntos.
                        tam=min(22,max(10,130//max(1,len(valor))))
                        texto(x,yy+fila*42,91,40,valor,tam,INK if activo or fila==0 else MUTED,activo,True)
            texto(56,inferior+alto_inferior-78,1496,58,
                  '∞: todavía no alcanzado   ·   −∞: afectado por ciclo negativo\n'
                  'La columna resaltada corresponde al extremo de llegada del arco actual.',18,MUTED)

            panel(1616,inferior,1552,alto_inferior)
            texto(1640,inferior+18,1496,44,f'PASO {paso.codigo}   /   {paso.tipo.upper()}',27,INK,True)
            texto(1640,inferior+82,1490,25,'PREGUNTA',17,MUTED,True)
            texto(1640,inferior+113,1490,51,paso.pregunta,30,INK,True)
            texto(1640,inferior+168,1490,61,paso.comparacion,24,MUTED)
            texto(1640,inferior+234,290,32,'RESPUESTA',17,MUTED,True)
            texto(1970,inferior+224,1138,55,paso.respuesta,30,GREEN,True)
            texto(1640,inferior+296,1490,27,'PROCESO',17,MUTED,True)
            texto(1640,inferior+333,1490,102,paso.proceso,27,INK,True)
            texto(1640,inferior+447,1490,alto_inferior-467,paso.texto,23,MUTED)
        finally:
            p.end()
        return imagen
