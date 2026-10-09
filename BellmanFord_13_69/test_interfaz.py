"""Pruebas de capturas limpias y navegación, sin exportar un recorrido completo."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QPointF
from PySide6.QtGui import QFontDatabase,QImage
from PySide6.QtWidgets import QApplication
from algoritmo import Grafo,Arista,bellman_ford
from dibujo import Lienzo
from capturas import SesionCapturas
from interfaz import Ventana

APP=QApplication.instance() or QApplication([])
APP.setStyle('Fusion')
for nombre in ('segoeui.ttf','seguisb.ttf','consola.ttf'):
    ruta=Path('C:/Windows/Fonts')/nombre
    if ruta.exists(): QFontDatabase.addApplicationFont(str(ruta))


class InterfazTests(unittest.TestCase):
    def setUp(self):
        # El directorio de prueba queda dentro de este proyecto.
        self.tmp=tempfile.TemporaryDirectory(prefix='prueba_',dir=Path(__file__).parent)
        self.base=Path(self.tmp.name)
        self.g=Grafo({0:(0,0),1:(160,0)},[Arista('a',0,1,-2)],0,1,False)
        self.r=bellman_ford(self.g,0,1)
        self.l=Lienzo(self.g,self.r.pasos[0])
        self.s=SesionCapturas(self.g,self.r,self.l.dibujar,self.base)

    def tearDown(self):
        self.l.close()
        self.tmp.cleanup()

    def test_captura_no_depende_del_zoom_seleccion_o_paso_visible(self):
        esperado=self.s.imagen(4)
        self.l.zoom=3; self.l.pan=QPointF(500,-200)
        self.l.elegido=1; self.l.hover=0
        self.l.pesos=False; self.l.distancias=False
        self.l.establecer(self.r.pasos[-1])
        self.assertEqual(esperado,self.s.imagen(4))

    def test_png_metadatos_y_guardado_sin_duplicados(self):
        ruta=self.s.guardar(len(self.r.pasos)-1)
        imagen=QImage(str(ruta))
        self.assertEqual(json.loads(imagen.text('d')),['−∞','−∞'])
        self.assertEqual(len(json.loads(imagen.text('Arcos'))),2)
        self.assertEqual(imagen.text('Respuesta'),'SIN MÍNIMO')
        modificado=ruta.stat().st_mtime_ns
        self.s.guardar(len(self.r.pasos)-1)
        self.assertEqual(ruta.stat().st_mtime_ns,modificado)
        self.assertEqual(len(list(self.s.carpeta.glob('*.png'))),1)

    def test_fallo_de_escritura_no_marca_como_guardado(self):
        with patch.object(SesionCapturas,'imagen',side_effect=OSError('Sin espacio')):
            with self.assertRaises(OSError): self.s.guardar(0)
        self.assertFalse(self.s.guardados)

    def test_navegacion_y_capturas_de_pasos_omitidos(self):
        with patch.object(Grafo,'cargar',return_value=self.g):
            w=Ventana(capturar=False,carpeta_capturas=self.base)
        try:
            self.assertFalse(w.capturas.carpeta.exists())
            w.mover(1); self.assertEqual(w.indice,1)
            w.modo.setCurrentIndex(1); w.mover(1)
            self.assertEqual(w.recorrido.pasos[w.indice].tipo,'arco')
            self.assertEqual(w.pregunta.text(),w.recorrido.pasos[w.indice].pregunta)
            # Simular escritura para verificar la cola sin crear cientos de PNG.
            with patch.object(w.capturas,'guardar',side_effect=lambda i:w.capturas.guardados.add(i)):
                w.ir_a(0); w.automatico.setChecked(True); w.ir_a(7)
                while w.lote_pendientes: w.procesar_captura()
                w.procesar_captura()
                self.assertEqual(w.capturas.guardados,{i for i in w.capturas.indices if i<=7})
                self.assertFalse(w.lote_timer.isActive())
                w.exportar_todo()
                while w.lote_pendientes: w.procesar_captura()
                w.procesar_captura()
                self.assertEqual(w.capturas.guardados,set(w.capturas.indices))
            w.automatico.setChecked(False); w.resultado()
            self.assertIn('ciclo negativo',w.ruta.text())
            self.assertEqual(w.vector.item(1,0).text(),'−∞')
        finally:
            w.reloj.stop(); w.lote_timer.stop(); w.close()

    def test_secuencia_del_ejemplo_pdf_tiene_51_capturas(self):
        # u, v, x, y, z se representan como 0, 1, 2, 3, 4.
        aristas=[(0,1,5),(0,2,8),(0,3,-4),(1,0,-2),(2,1,-3),
                 (2,3,9),(3,1,7),(3,4,2),(4,0,6),(4,2,7)]
        g=Grafo({i:(i*100,0) for i in range(5)},
                [Arista(str(i),u,v,peso) for i,(u,v,peso) in enumerate(aristas)],4,3,True)
        r=bellman_ford(g,4,3,False)
        s=SesionCapturas(g,r,self.l.dibujar,self.base)
        pasos=[s.paso_presentacion(i) for i in s.indices]
        self.assertEqual(len(pasos),51)
        self.assertEqual([p.tipo for p in pasos[:3]],['inicio','origen','omitir'])
        self.assertEqual(pasos[2].respuesta,'NO')
        # Diapositivas 11 y 12: mismo arco; primero decisión, luego d y Π completos.
        antes,despues=pasos[10:12]
        self.assertEqual((antes.tipo,despues.tipo),('decision','predecesor'))
        self.assertEqual(antes.codigo,despues.codigo)
        self.assertEqual(antes.distancias[0],float('inf'))
        self.assertNotIn(0,antes.anteriores)
        self.assertEqual(despues.distancias[0],6)
        self.assertEqual(despues.anteriores[0][0],4)
        self.assertEqual(pasos[-2].tipo,'verificar')
        self.assertEqual(pasos[-2].respuesta,'SÍ')
        self.assertEqual(list(pasos[-1].distancias.values()),[2,4,7,-2,0])
        self.assertTrue(s.nombre(s.indices[11]).startswith('captura_000012_'))

    def test_micropasos_no_se_guardan_y_control_resume_ciclo(self):
        i=next(i for i,p in enumerate(self.r.pasos) if p.tipo=='actualizar')
        self.assertIsNone(self.s.guardar(i))
        self.assertFalse(self.s.carpeta.exists())
        control=next(self.s.paso_presentacion(i) for i in self.s.indices
                     if self.r.pasos[i].tipo=='verificar')
        self.assertEqual(control.respuesta,'NO · CICLO NEGATIVO')
        self.assertIn('0, 1',control.proceso)

    def test_navegacion_pdf_muestra_antes_y_despues(self):
        with patch.object(Grafo,'cargar',return_value=self.g):
            w=Ventana(capturar=False,carpeta_capturas=self.base)
        try:
            self.assertEqual(w.modo.currentData(),'pdf')
            visitados=[w.indice]
            while w.indice<len(w.recorrido.pasos)-1:
                w.mover(1); visitados.append(w.indice)
            self.assertEqual(visitados,list(w.capturas.indices))
            w.mover(-1)
            self.assertEqual(w.indice,w.capturas.indices[-2])
        finally:
            w.reloj.stop(); w.lote_timer.stop(); w.close()

    def test_grafo_entregado_y_evidencias_de_los_ocho_ciclos(self):
        g=Grafo.cargar(Path(__file__).with_name('grafo.json'))
        r=bellman_ford(g,g.origen,g.destino)
        self.assertFalse(g.dirigido)
        self.assertEqual(len(r.afectados),30)
        evidencias=[p for p in r.pasos if p.tipo=='verificar_ciclo']
        self.assertEqual(len(evidencias),16)
        self.assertEqual(len({p.arista for p in evidencias}),8)
        lienzo=Lienzo(g,r.pasos[0])
        imagen=SesionCapturas(g,r,lienzo.dibujar,self.base).imagen(len(r.pasos)-1)
        self.assertEqual((imagen.width(),imagen.height()),(3200,2000))
        self.assertEqual(len(json.loads(imagen.text('V'))),30)
        self.assertEqual(len(json.loads(imagen.text('Arcos'))),126)
        lienzo.close()


if __name__=='__main__': unittest.main()
