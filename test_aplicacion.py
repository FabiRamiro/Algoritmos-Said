"""Pruebas de la aplicación unificada sin abrir una ventana. Ejecuta: python -m unittest -v"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import inspect
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QApplication

import aplicacion
from aplicacion import ALGORITMOS, Laboratorio, RAIZ
from cargador import importar_aislado

ALIAS = {a.clave: f"alg_{a.clave.replace('-', '_')}" for a in ALGORITMOS}


class LaboratorioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.temp = TemporaryDirectory()
        cls.parches = []
        # Las vistas guardan capturas al abrirse: en las pruebas van a una
        # carpeta temporal para no mezclarse con las evidencias reales.
        for a in ALGORITMOS:
            interfaz = importar_aislado(RAIZ / a.carpeta, "interfaz", ALIAS[a.clave])
            original = interfaz.SesionCapturas
            firma = inspect.signature(original.__init__)

            def crear(*args, _original=original, _firma=firma, **kw):
                datos = _firma.bind_partial(None, *args, **kw).arguments
                datos.pop("self")
                datos["carpeta_base"] = cls.temp.name
                return _original(**datos)

            parche = patch.object(interfaz, "SesionCapturas", side_effect=crear)
            parche.start()
            cls.parches.append(parche)

    @classmethod
    def tearDownClass(cls):
        for parche in cls.parches:
            parche.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.w = Laboratorio()
        self.addCleanup(self.w.close)

    def test_inicia_en_la_pantalla_de_eleccion(self):
        self.assertEqual(self.w.actual, "inicio")
        self.assertIs(self.w.pila.currentWidget(), self.w.inicio)
        self.assertEqual(self.w.vistas, {})  # Nada se carga hasta elegirlo.
        self.assertEqual(len(self.w.opciones), 4)

    def test_cada_algoritmo_viene_de_su_propio_proyecto(self):
        for a in ALGORITMOS:
            self.w.mostrar(a.clave)
        for a in ALGORITMOS:
            archivo = Path(type(self.w.vistas[a.clave]).__init__.__code__.co_filename)
            self.assertEqual(archivo, RAIZ / a.carpeta / "interfaz.py")
            self.assertEqual(sys.modules[f"{ALIAS[a.clave]}.algoritmo"].__file__,
                             str(RAIZ / a.carpeta / "algoritmo.py"))
        # Ningún nombre genérico queda ocupado por un proyecto concreto.
        for nombre in ("algoritmo", "interfaz", "capturas", "tema", "dibujo"):
            self.assertNotIn(nombre, sys.modules)

    def test_resultados_de_cada_proyecto(self):
        for clave in ("dijkstra", "astar"):
            self.w.mostrar(clave)
            self.assertEqual(self.w.vistas[clave].recorrido.costo, 14)
            self.assertEqual(self.w.vistas[clave].recorrido.ruta, [13, 16, 17, 69])

    def test_cambiar_pausa_la_vista_anterior_y_conserva_su_paso(self):
        self.w.mostrar("dijkstra")
        d = self.w.vistas["dijkstra"]
        d.mover(1); d.mover(1); d.mover(1)
        d.alternar()
        self.assertTrue(d.reproduciendo)
        self.w.mostrar("astar")
        self.assertFalse(d.reproduciendo)
        self.assertIs(self.w.pila.currentWidget(), self.w.vistas["astar"])
        self.w.mostrar("dijkstra")
        self.assertIs(self.w.vistas["dijkstra"], d)  # No se vuelve a crear.
        self.assertEqual(d.indice, 3)

    def test_solo_la_vista_visible_recibe_atajos(self):
        for a in ALGORITMOS:
            self.w.mostrar(a.clave)
        self.w.mostrar("bellman-ford")
        for clave, vista in self.w.vistas.items():
            for s in vista.findChildren(QShortcut):
                tecla = s.key().toString()
                if tecla in ("F11", "Esc"):
                    self.assertFalse(s.isEnabled(), (clave, tecla))
                else:
                    self.assertEqual(s.isEnabled(), clave == "bellman-ford", (clave, tecla))
        self.w.mostrar("inicio")
        self.assertFalse(any(s.isEnabled() for atajos in self.w.atajos_vista.values() for s in atajos))

    def test_atajos_de_la_ventana_principal(self):
        teclas = {s.key().toString() for s in self.w.atajos}
        self.assertTrue({"Ctrl+0", "Ctrl+1", "Ctrl+2", "Ctrl+3", "Ctrl+4", "F11", "Esc"} <= teclas)
        atajo = next(s for s in self.w.atajos if s.key().toString() == "Ctrl+4")
        atajo.activated.emit()
        self.assertEqual(self.w.actual, "astar")

    def test_titulo_y_navegacion_siguen_a_la_vista(self):
        self.w.mostrar("astar")
        self.assertTrue(self.w.windowTitle().startswith("A*"))
        self.assertTrue(self.w.botones["astar"].isChecked())
        self.w.vistas["astar"].setWindowTitle("A* · otro título")
        self.assertEqual(self.w.windowTitle(), "A* · otro título")
        self.w.mostrar("inicio")
        self.assertEqual(self.w.windowTitle(), "Laboratorio de caminos mínimos")
        self.assertTrue(self.w.botones["inicio"].isChecked())

    def test_tarjeta_y_boton_de_la_barra_abren_el_algoritmo(self):
        self.w.opciones[2].al_elegir()
        self.assertEqual(self.w.actual, "floyd-warshall")
        self.w.botones["dijkstra"].click()
        self.assertEqual(self.w.actual, "dijkstra")

    def test_error_al_cargar_no_rompe_la_aplicacion(self):
        with patch.object(self.w, "cargar", side_effect=RuntimeError("falló")), \
             patch.object(aplicacion.QMessageBox, "critical") as aviso:
            self.w.mostrar("bellman-ford")
        aviso.assert_called_once()
        self.assertEqual(self.w.actual, "inicio")
        self.assertTrue(self.w.botones["inicio"].isChecked())
        self.assertNotIn("bellman-ford", self.w.vistas)
        with self.assertRaises(ValueError):
            self.w.mostrar("prim")

    def test_boton_de_diapositivas_solo_con_un_algoritmo_abierto(self):
        self.assertFalse(self.w.diapositivas_btn.isEnabled())
        self.w.mostrar("astar")
        self.assertTrue(self.w.diapositivas_btn.isEnabled())
        self.w.mostrar("inicio")
        self.assertFalse(self.w.diapositivas_btn.isEnabled())

    def test_crear_diapositivas_completa_la_sesion(self):
        self.w.mostrar("astar")
        vista = self.w.vistas["astar"]
        vista.mover(1); vista.mover(1); vista.mover(1)  # Llega a la primera decisión.
        self.assertTrue(self.w.capturas_faltantes(vista))
        Si = aplicacion.QMessageBox.StandardButton.Yes
        with patch.object(aplicacion.QMessageBox, "question", return_value=Si) as pregunta, \
             patch.object(aplicacion.QMessageBox, "exec", return_value=0):
            self.w.crear_diapositivas()
        pregunta.assert_called_once()
        self.assertEqual(self.w.capturas_faltantes(vista), [])
        carpeta = vista.capturas.carpeta
        self.assertEqual(len(list(carpeta.glob("captura_*.png"))), len(vista.capturas.indices))
        self.assertTrue((carpeta / "diapositivas.pdf").exists())
        self.assertTrue((carpeta / "diapositivas.pptx").exists())
        self.assertFalse(vista.lote_timer.isActive())

    def test_sesion_enorme_usa_solo_las_capturas_recorridas(self):
        self.w.mostrar("bellman-ford")
        vista = self.w.vistas["bellman-ford"]
        self.assertGreater(len(self.w.capturas_faltantes(vista)), aplicacion.diapositivas.LIMITE)
        carpeta = vista.capturas.carpeta
        recorridas = len(list(carpeta.glob("captura_*.png")))  # La vista guarda su primer paso al abrirse.
        self.assertGreater(recorridas, 0)
        with patch.object(aplicacion.QMessageBox, "question") as pregunta, \
             patch.object(aplicacion.QMessageBox, "exec", return_value=0):
            self.w.crear_diapositivas()
        pregunta.assert_not_called()  # No ofrece guardar miles de capturas.
        self.assertEqual(len(list(carpeta.glob("captura_*.png"))), recorridas)
        self.assertTrue((carpeta / "diapositivas.pdf").exists())
        # Sin ninguna captura recorrida, solo explica qué hacer.
        for png in carpeta.glob("captura_*.png"):
            png.unlink()
        (carpeta / "diapositivas.pdf").unlink()
        with patch.object(aplicacion.QMessageBox, "information") as aviso:
            self.w.crear_diapositivas()
        aviso.assert_called_once()
        self.assertFalse((carpeta / "diapositivas.pdf").exists())

    def test_cancelar_no_crea_nada(self):
        self.w.mostrar("dijkstra")
        vista = self.w.vistas["dijkstra"]
        Cancelar = aplicacion.QMessageBox.StandardButton.Cancel
        with patch.object(aplicacion.QMessageBox, "question", return_value=Cancelar):
            self.w.crear_diapositivas()
        self.assertFalse((vista.capturas.carpeta / "diapositivas.pdf").exists())
        self.assertEqual(vista.capturas.guardados, set())

    def test_inicial_desde_la_linea_de_comandos(self):
        w = Laboratorio("floyd-warshall")
        self.addCleanup(w.close)
        self.assertEqual(w.actual, "floyd-warshall")


if __name__ == "__main__":
    unittest.main()
