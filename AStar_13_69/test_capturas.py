"""Pruebas de capturas y navegación sin abrir una ventana en el escritorio."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QFontDatabase, QImage, QPainter, QColor
from PySide6.QtWidgets import QApplication

from algoritmo import Arista, Grafo, a_estrella
from capturas import SesionCapturas
from interfaz import Lienzo, Ventana
from tema import PANEL, BG


class CapturaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        # Qt offscreen en Windows necesita registrar fuentes para dibujar texto.
        for nombre in ("segoeui.ttf", "seguisb.ttf", "consola.ttf"):
            ruta = Path("C:/Windows/Fonts") / nombre
            if ruta.exists():
                QFontDatabase.addApplicationFont(str(ruta))
        cls.g = Grafo({1:(0,0),2:(200,120)},[Arista("a",1,2,3)],1,2)
        cls.r = a_estrella(cls.g,1,2)

    def setUp(self):
        base = Path(__file__).resolve().parent / "work"
        base.mkdir(exist_ok=True)
        self.temp = TemporaryDirectory(dir=base)
        # Confirmar el destino antes de la limpieza recursiva de TemporaryDirectory.
        assert Path(self.temp.name).resolve().is_relative_to(base.resolve())
        self.addCleanup(self.temp.cleanup)
        self.lienzo = Lienzo(self.g,self.r.pasos[0])
        self.lienzo.origen, self.lienzo.destino = 1,2
        self.addCleanup(self.lienzo.close)
        self.s = SesionCapturas(self.g,self.r,self.lienzo.dibujar,self.temp.name)

    def test_png_con_explicacion_sin_duplicados_ni_archivos_adicionales(self):
        # Basta probar un estado intermedio y el resultado, no exportar un lote.
        intermedio = next(i for i in self.s.indices if self.r.pasos[i].tipo == 'predecesor')
        for i in (intermedio,len(self.r.pasos)-1):
            salida = self.s.guardar(i)
            imagen = QImage(str(salida))
            self.assertFalse(imagen.isNull())
            self.assertEqual((imagen.width(),imagen.height()),(1920,1240))
            self.assertEqual(imagen.text('Paso'),self.s.etiqueta(i))
            self.assertEqual(imagen.text('Explicación'),self.s.paso_presentacion(i).texto)
        archivo = self.s.guardar(intermedio)
        fecha = archivo.stat().st_mtime_ns
        self.s.guardar(intermedio)
        self.assertEqual(archivo.stat().st_mtime_ns,fecha)
        self.assertEqual(len(list(self.s.carpeta.iterdir())),2)
        self.assertTrue(all(p.suffix == '.png' for p in self.s.carpeta.iterdir()))

    def test_grafo_completo_y_explicacion_fuera_del_grafo(self):
        esperado = QImage(1920,1240,QImage.Format.Format_RGB32)
        esperado.fill(QColor(PANEL))
        painter = QPainter(esperado)
        self.lienzo.dibujar(painter,QRectF(24,16,1872,980),paso=self.r.pasos[-1],limpio=True)
        painter.end()
        salida = self.s.imagen(len(self.r.pasos)-1)
        self.assertEqual(salida.copy(0,0,1920,1014),esperado.copy(0,0,1920,1014))
        self.assertEqual(salida.pixelColor(0,1220),QColor(BG))
        # El pie contiene tinta real (texto), no solo metadatos del archivo.
        self.assertTrue(any(salida.pixelColor(x,y).lightness()>110
                            for y in range(1032,1210,3) for x in range(42,1300,3)))

    def test_captura_independiente_de_zoom_seleccion_y_paso_visible(self):
        indice = next(i for i,p in enumerate(self.r.pasos) if p.tipo == "comparar")
        antes = self.s.imagen(indice)
        self.lienzo.zoom = 2.5
        self.lienzo.pan = QPointF(400,-200)
        self.lienzo.elegido = 2
        self.lienzo.pesos = False
        self.lienzo.distancias = False
        self.lienzo.establecer(self.r.pasos[-1])
        despues = self.s.imagen(indice)
        self.assertEqual(antes,despues)
        self.assertIs(self.lienzo.paso,self.r.pasos[-1])
        self.assertEqual(self.lienzo.zoom,2.5)

    def test_error_de_escritura_no_marca_como_guardado(self):
        with patch.object(self.s,"imagen") as imagen:
            imagen.return_value.save.return_value = False
            with self.assertRaises(OSError):
                self.s.guardar(self.s.indices[0])
        self.assertEqual(self.s.guardados,set())

    def test_sesiones_no_sobrescriben_capturas(self):
        otra = SesionCapturas(self.g,self.r,self.lienzo.dibujar,self.temp.name)
        self.assertNotEqual(self.s.carpeta,otra.carpeta)

    def test_saltar_exportar_retroceder_y_recalcular(self):
        def crear(grafo,recorrido,dibujar):
            return SesionCapturas(grafo,recorrido,dibujar,self.temp.name)
        with patch("interfaz.SesionCapturas",side_effect=crear), patch("interfaz.Grafo.cargar",return_value=self.g):
            w = Ventana()
            self.addCleanup(w.close)
            w.resultado()
            w.lote_timer.stop()
            while w.lote_pendientes:
                w.procesar_captura()
            w.procesar_captura()
            self.assertEqual(w.capturas.guardados,set(w.capturas.indices))
            self.assertEqual(w.indice,len(w.recorrido.pasos)-1)
            w.mover(-1)
            self.assertEqual(w.capturas.guardados,set(w.capturas.indices))
            anterior = w.capturas.carpeta
            w.origen_combo.setCurrentText("2")
            self.assertNotEqual(anterior,w.capturas.carpeta)
            self.assertEqual(w.recorrido.costo,0)
            self.assertEqual(w.indice,0)

    def test_no_guarda_micropasos_y_numeracion_es_continua(self):
        self.assertEqual(self.r.pasos[3].tipo,'encolar')
        self.assertIsNone(self.s.guardar(3))  # Encolar no necesita otra imagen.
        self.assertFalse(self.s.carpeta.exists())
        for numero, indice in enumerate(self.s.indices, 1):
            self.assertTrue(self.s.nombre(indice).startswith(f'captura_{numero:04d}_'))

    def test_decisiones_con_y_sin_mejora_y_vecino_fijado(self):
        g = Grafo({i:(0,0) for i in range(4)},
                  [Arista('a',0,1,2),Arista('b',0,2,1),Arista('c',2,1,5)],0,3)
        r = a_estrella(g,0,3)
        s = SesionCapturas(g,r,self.lienzo.dibujar,self.temp.name)
        pasos = [r.pasos[i] for i in s.indices]
        self.assertEqual([p.tipo for p in pasos],
                         ['heuristica','origen','fijar','predecesor','predecesor',
                          'fijar','mantener','fijar','sin_ruta'])
        mejora = s.paso_presentacion(s.indices[3])
        self.assertIn('0 + 2 = 2',mejora.texto)
        self.assertIn('2 < ∞: SÍ',mejora.formula)
        self.assertIn('g[1]: ∞ → 2',mejora.formula)
        self.assertIn('previo[1] = 0',mejora.formula)
        sin_cambio = s.paso_presentacion(s.indices[6])
        self.assertIn('1 + 5 = 6',sin_cambio.texto)
        self.assertIn('6 < 2: NO',sin_cambio.formula)
        self.assertIn('g[1]: 2 → 2',sin_cambio.formula)
        self.assertEqual(sin_cambio.anteriores[1],(0,'a'))

    def test_exportar_todo_usa_solo_decisiones(self):
        def crear(grafo,recorrido,dibujar):
            return SesionCapturas(grafo,recorrido,dibujar,self.temp.name)
        with patch('interfaz.SesionCapturas',side_effect=crear), patch('interfaz.Grafo.cargar',return_value=self.g):
            w = Ventana()
            self.addCleanup(w.close)
            w.exportar_todo()
            w.lote_timer.stop()
            self.assertEqual(w.lote_pendientes,list(w.capturas.indices))
            while w.lote_pendientes:
                w.procesar_captura()
            self.assertEqual(w.capturas.guardados,set(w.capturas.indices))

    def test_mejora_finita_y_empate_con_aristas_paralelas(self):
        g = Grafo({i:(0,0) for i in range(4)},
                  [Arista('a',0,1,9),Arista('b',0,2,1),
                   Arista('c',2,1,2),Arista('d',2,1,2)],0,3)
        r = a_estrella(g,0,3)
        s = SesionCapturas(g,r,self.lienzo.dibujar,self.temp.name)
        decisiones = [s.paso_presentacion(i) for i in s.indices
                      if r.pasos[i].actual == 2 and r.pasos[i].vecino == 1]
        mejora, empate = decisiones
        self.assertIn('1 + 2 = 3',mejora.texto)
        self.assertIn('3 < 9: SÍ',mejora.formula)
        self.assertIn('g[1]: 9 → 3',mejora.formula)
        self.assertEqual(mejora.anteriores[1],(2,'c'))
        self.assertIn('3 < 3: NO',empate.formula)
        self.assertEqual(empate.anteriores[1],(2,'c'))

    def test_origen_igual_destino_conserva_resultado(self):
        r = a_estrella(self.g,1,1)
        s = SesionCapturas(self.g,r,self.lienzo.dibujar,self.temp.name)
        self.assertEqual([r.pasos[i].tipo for i in s.indices],['heuristica','origen','fijar','fin'])
        self.assertEqual(r.costo,0)

    def test_panel_inferior_se_oculta_y_conserva_la_navegacion(self):
        with patch("interfaz.SesionCapturas"), patch("interfaz.Grafo.cargar",return_value=self.g):
            w = Ventana()
            self.addCleanup(w.close)
            self.assertEqual(w.divisor.count(),2)
            self.assertTrue(w.panel_detalle.isHidden())
            w.alternar_detalle()
            self.assertFalse(w.panel_detalle.isHidden())
            self.assertEqual(w.historial.count(),len(w.recorrido.pasos))
            self.assertIsNot(w.historial.parent(),w.tabs)
            w.alternar_secuencia()
            self.assertTrue(w.rail.isHidden())
            w.alternar_secuencia()
            self.assertFalse(w.rail.isHidden())
            w.alternar_detalle()
            self.assertTrue(w.panel_detalle.isHidden())
            w.mover(1)
            self.assertEqual(w.indice,1)
            w.alternar_detalle()
            self.assertFalse(w.panel_detalle.isHidden())

    def test_decision_muestra_heuristica_y_prioridad(self):
        # 0 -- 1 -- 2 en línea recta: escala = 1/100 y h(1) = 1.
        g = Grafo({0:(0,0),1:(100,0),2:(200,0)},
                  [Arista('a',0,1,1),Arista('b',1,2,1)],0,2)
        r = a_estrella(g,0,2)
        self.assertEqual(r.heuristica,{0:2,1:1,2:0})
        s = SesionCapturas(g,r,self.lienzo.dibujar,self.temp.name)
        mejora = s.paso_presentacion(next(i for i in s.indices if r.pasos[i].tipo == 'predecesor'))
        self.assertIn('g = 0 + 1 = 1',mejora.texto)
        self.assertIn('f = 1 + 1 = 2',mejora.texto)
        self.assertIn('f[1] = 2',mejora.formula)
        self.assertEqual(r.pasos[s.indices[0]].tipo,'heuristica')


if __name__ == "__main__":
    unittest.main()
