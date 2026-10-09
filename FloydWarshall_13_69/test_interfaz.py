import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase,QImage
from PySide6.QtCore import QPointF
from algoritmo import Grafo,Arista,floyd_warshall
from dibujo import Lienzo
from capturas import SesionCapturas
from interfaz import Ventana

APP=QApplication.instance() or QApplication([])
APP.setStyle('Fusion')
for nombre in ('segoeui.ttf','seguisb.ttf','consola.ttf'):
    QFontDatabase.addApplicationFont(str(Path('C:/Windows/Fonts')/nombre))


class InterfazTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.g=Grafo({0:(0,0),1:(150,80),2:(300,0)},[Arista('a',0,1,-2),Arista('b',1,2,5)],0,2,True)
        self.r=floyd_warshall(self.g)
        self.l=Lienzo(self.g,self.r.vista_grafo(self.r.pasos[0],0,2)); self.addCleanup(self.l.close)
        self.s=SesionCapturas(self.g,self.r,self.l.dibujar,0,2,self.tmp.name)

    def test_png_matrices_completas_y_guardado_sin_duplicar(self):
        ruta=self.s.guardar(2); img=QImage(str(ruta))
        self.assertFalse(img.isNull())
        self.assertEqual(json.loads(img.text('D')),[['0','-2','3'],['∞','0','5'],['∞','∞','0']])
        self.assertEqual(json.loads(img.text('R'))[0][2],1)
        self.assertEqual(len(json.loads(img.text('Cambios'))),1)
        modificado=ruta.stat().st_mtime_ns
        self.s.guardar(2); self.assertEqual(modificado,ruta.stat().st_mtime_ns)

    def test_captura_limpia_y_fallo_de_escritura(self):
        imagen=self.s.imagen(2)
        self.l.zoom=3; self.l.pan=QPointF(400,-100); self.l.elegido=1
        self.l.establecer(self.r.vista_grafo(self.r.pasos[-1],0,2))
        self.assertEqual(imagen,self.s.imagen(2))
        with patch.object(self.s,'imagen',side_effect=OSError('sin espacio')):
            with self.assertRaises(OSError): self.s.guardar(0)
        self.assertFalse(self.s.guardados)

    def test_navegacion_salto_consulta_y_exportacion(self):
        with patch.object(Grafo,'cargar',return_value=self.g):
            w=Ventana(capturar=False,carpeta_capturas=self.tmp.name)
        self.addCleanup(w.close)
        self.assertEqual(w.tabla_d.rowCount(),3)
        with patch.object(w.capturas,'guardar',side_effect=lambda i:w.capturas.guardados.add(i)):
            w.automatico.setChecked(True); w.ir_a(4)
            while w.lote_pendientes: w.procesar_captura()
            w.procesar_captura()
            self.assertEqual(w.capturas.guardados,set(range(5)))
            self.assertIn('Costo 3',w.resultado_texto.text())
            w.ir_a(2); w.inspeccionar_par(0,2)
            self.assertIn('-2 + 5 = 3',w.par.text())
        w.automatico.setChecked(False)
        recorrido=w.recorrido; carpeta=w.capturas.carpeta
        w.origen.setCurrentText('2')
        self.assertIs(w.recorrido,recorrido)
        self.assertNotEqual(w.capturas.carpeta,carpeta)
        self.assertIn('Costo 0',w.resultado_texto.text())
        with patch.object(w.capturas,'guardar',side_effect=lambda i:w.capturas.guardados.add(i)):
            w.exportar_todo()
            while w.lote_pendientes: w.procesar_captura()
            w.procesar_captura()
            self.assertEqual(w.capturas.guardados,set(range(5)))

    def test_ciclo_negativo_no_muestra_ruta(self):
        g=Grafo(self.g.posiciones,self.g.aristas,0,2,False)
        with patch.object(Grafo,'cargar',return_value=g):
            w=Ventana(capturar=False,carpeta_capturas=self.tmp.name)
        self.addCleanup(w.close); w.ir_a(len(w.recorrido.pasos)-1)
        self.assertIn('Sin mínimo finito',w.resultado_texto.text())
        self.assertEqual(w.tabla_d.item(0,2).text(),'−∞')
        self.assertEqual(w.tabla_r.item(0,2).text(),'—')


if __name__=='__main__': unittest.main()
