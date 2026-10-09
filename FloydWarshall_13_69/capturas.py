"""Una imagen completa por inicialización, intermedio k y resultado."""
from datetime import datetime
from pathlib import Path
import json
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QFont
from algoritmo import numero
from tema import BG, PANEL, LINE, INK, MUTED


class SesionCapturas:
    def __init__(self, grafo, recorrido, dibujar, origen, destino, carpeta_base=None):
        self.grafo, self.recorrido, self.dibujar = grafo, recorrido, dibujar
        self.origen, self.destino = origen, destino
        base = Path(carpeta_base) if carpeta_base else Path(__file__).parent/'capturas'
        self.carpeta = base/f'{datetime.now():%Y-%m-%d_%H-%M-%S_%f}_{origen}-{destino}'
        self.guardados = set()

    def nombre(self, indice):
        paso = self.recorrido.pasos[indice]
        return f'captura_{indice+1:03d}_{paso.tipo}_k{paso.k if paso.k is not None else "ninguno"}.png'

    def guardar(self, indice):
        destino = self.carpeta/self.nombre(indice)
        if indice in self.guardados and destino.exists():
            return destino
        self.carpeta.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix('.tmp')
        if not self.imagen(indice).save(str(temporal),'PNG'):
            raise OSError(f'No se pudo escribir {destino}')
        temporal.replace(destino)
        self.guardados.add(indice)
        return destino

    def imagen(self, indice):
        paso = self.recorrido.pasos[indice]
        nodos = self.recorrido.nodos
        n = len(nodos)
        alto_matriz = (n+1)*36
        alto = max(2600,2*alto_matriz+440)
        imagen = QImage(4400,alto,QImage.Format.Format_RGB32)
        imagen.fill(QColor(BG))
        datos = {'Paso':str(indice+1),'Intermedio':str(paso.k),'Nodos':nodos,
                 'Origen':self.origen,'Destino':self.destino,
                 'D':[[numero(v) for v in fila] for fila in paso.distancias],
                 'R':paso.recorridos,'Cambios':[(nodos[c.i],nodos[c.j],numero(c.anterior),
                                              numero(c.izquierda),numero(c.derecha),numero(c.nuevo)) for c in paso.cambios]}
        for clave, valor in datos.items():
            imagen.setText(clave,json.dumps(valor,ensure_ascii=False))
        p = QPainter(imagen)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        def texto(x,y,w,h,contenido,size=26,bold=False,tinta=INK,centrado=False):
            f = QFont('Segoe UI'); f.setPixelSize(size); f.setBold(bold)
            p.setFont(f); p.setPen(QColor(tinta))
            align = Qt.AlignmentFlag.AlignCenter if centrado else Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter
            p.drawText(QRectF(x,y,w,h),align|Qt.TextFlag.TextWordWrap,str(contenido))

        def panel(x,y,w,h):
            p.setPen(QPen(QColor(LINE),1)); p.setBrush(QColor(PANEL))
            p.drawRoundedRect(QRectF(x,y,w,h),12,12)

        def matriz(y, valores, titulo, distancias):
            x, ancho = 1920, 2440
            panel(x-16,y-66,ancho+32,alto_matriz+86)
            texto(x,y-58,ancho,44,titulo,28,True)
            celda = ancho/(n+1)
            cambiados = {(c.i,c.j) for c in paso.cambios}
            for fila in range(n+1):
                for col in range(n+1):
                    xx, yy = x+col*celda,y+fila*36
                    cabecera = fila==0 or col==0
                    activo = not cabecera and (nodos[fila-1]==paso.k or nodos[col-1]==paso.k)
                    cambio = not cabecera and (fila-1,col-1) in cambiados
                    p.fillRect(QRectF(xx,yy,celda,36),QColor('#393d45' if cambio else '#24272d' if activo or cabecera else PANEL))
                    p.setPen(QPen(QColor('#727782' if activo else LINE),1))
                    p.drawRect(QRectF(xx,yy,celda,36))
                    if fila==0:
                        valor = 'i / j' if col==0 else str(nodos[col-1])
                    elif col==0:
                        valor = str(nodos[fila-1])
                    else:
                        v = valores[fila-1][col-1]
                        valor = numero(v) if distancias else '—' if v is None else str(v)
                    f = QFont('Segoe UI'); f.setPixelSize(23); f.setBold(cabecera or cambio)
                    p.setFont(f)
                    while p.fontMetrics().horizontalAdvance(valor)>celda-6 and f.pixelSize()>9:
                        f.setPixelSize(f.pixelSize()-1); p.setFont(f)
                    p.setPen(QColor(INK if cabecera or cambio else MUTED))
                    p.drawText(QRectF(xx+2,yy,celda-4,36),Qt.AlignmentFlag.AlignCenter,valor)

        try:
            texto(32,24,3000,48,'F L O Y D – W A R S H A L L',34,True)
            texto(32,82,3500,50,f'{self.origen} → {self.destino} · {paso.titulo} · Iteración {paso.iteracion}',29,tinta=MUTED)
            texto(3540,30,820,70,f'CAPTURA {indice+1:02d} / {len(self.recorrido.pasos):02d}',30,True)
            panel(32,180,1830,alto-870)
            vista = self.recorrido.vista_grafo(paso,self.origen,self.destino)
            self.dibujar(p,QRectF(48,240,1798,alto-960),paso=vista,limpio=True)
            texto(54,190,1770,34,'NÚMERO EXTERIOR = NODO · INTERIOR = DISTANCIA DESDE EL ORIGEN',21,tinta=MUTED)
            panel(32,alto-650,1830,600)
            y = alto-630
            texto(58,y,1770,50,paso.titulo,32,True)
            texto(58,y+65,1770,135,paso.texto,29,tinta=MUTED)
            ruta,_ = self.recorrido.ruta(paso,self.origen,self.destino)
            i,j = nodos.index(self.origen),nodos.index(self.destino)
            if (i,j) in paso.afectados:
                resultado = 'SIN MÍNIMO FINITO: un ciclo negativo afecta este par.'
            elif ruta:
                resultado = ('Ruta final: ' if paso.tipo=='fin' else 'Ruta provisional: ')+ ' → '.join(map(str,ruta))
                resultado += f' · Costo {numero(paso.distancias[i][j])}'
            else:
                resultado = 'No existe camino.' if paso.tipo=='fin' else 'Todavía no hay un camino para este par.'
            texto(58,y+215,1770,110,resultado,29,True)
            texto(58,y+340,1770,90,
                  f'{len(paso.cambios)} cambios · {len(paso.afectados)} pares afectados por ciclos negativos.',27)
            texto(58,y+445,1770,90,'∞: sin camino · −∞: sin mínimo finito · —: sin recorrido.\n'
                  'R: destino directo o último intermedio k; no es el siguiente salto.',24,tinta=MUTED)
            matriz(220,paso.distancias,'DISTANCIAS D · COSTO ENTRE CADA PAR',True)
            matriz(220+alto_matriz+110,paso.recorridos,'RECORRIDOS R · INTERMEDIOS',False)
            texto(1920,alto-60,2440,40,'Negritas y fondo claro: pares mejorados · Borde: fila y columna de k · Orden numérico de nodos',23,tinta=MUTED)
        finally:
            p.end()
        return imagen
