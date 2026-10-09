"""Pruebas del generador de diapositivas. Ejecuta: python -m unittest -v"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtGui import QColor, QGuiApplication, QImage
from pptx import Presentation

from diapositivas import capturas_de, crear_diapositivas, notas


def paginas_pdf(ruta):
    return len(re.findall(rb"/Type\s*/Page[^s]", Path(ruta).read_bytes()))


class DiapositivasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.carpeta = Path(self.temp.name)

    def imagen(self, nombre, ancho=1920, alto=1240, **textos):
        imagen = QImage(ancho, alto, QImage.Format.Format_RGB32)
        imagen.fill(QColor("#121315"))
        for clave, valor in textos.items():
            imagen.setText(clave, valor)
        self.assertTrue(imagen.save(str(self.carpeta / nombre), "PNG"))

    def test_una_diapositiva_por_captura_en_orden(self):
        for n in (3, 1, 2):
            self.imagen(f"captura_{n:04d}_fijar.png", Paso=f"{n} / 3", Acción=f"Acción {n}")
        self.imagen("micropaso_0007_elegir.png")  # Exportación manual: no forma parte de la secuencia.
        (self.carpeta / "notas.txt").write_text("otro archivo", encoding="utf-8")
        pdf, pptx = crear_diapositivas(self.carpeta)
        self.assertEqual((pdf.name, pptx.name), ("diapositivas.pdf", "diapositivas.pptx"))
        self.assertEqual(paginas_pdf(pdf), 3)
        presentacion = Presentation(str(pptx))
        self.assertEqual(len(presentacion.slides), 3)
        textos = [s.notes_slide.notes_text_frame.text for s in presentacion.slides]
        self.assertEqual([t.splitlines()[0] for t in textos], ["Paso 1 / 3", "Paso 2 / 3", "Paso 3 / 3"])
        self.assertFalse(list(self.carpeta.glob("*.tmp*")))

    def test_proporcion_de_la_diapositiva_sigue_a_la_captura(self):
        self.imagen("captura_0001_origen.png", 3200, 2000)
        _, pptx = crear_diapositivas(self.carpeta)
        p = Presentation(str(pptx))
        self.assertAlmostEqual(p.slide_width / p.slide_height, 3200 / 2000, places=3)
        imagen = p.slides[0].shapes[0]
        self.assertEqual((imagen.left, imagen.top), (0, 0))
        self.assertAlmostEqual(imagen.width, p.slide_width, delta=2)

    def test_imagen_con_otra_proporcion_se_centra_sin_deformar(self):
        self.imagen("captura_0001_a.png", 1920, 1240)
        self.imagen("captura_0002_b.png", 1000, 1000)
        _, pptx = crear_diapositivas(self.carpeta)
        p = Presentation(str(pptx))
        cuadrada = p.slides[1].shapes[0]
        self.assertEqual(cuadrada.width, cuadrada.height)
        self.assertEqual(cuadrada.top, 0)
        self.assertAlmostEqual(cuadrada.left, (p.slide_width - cuadrada.width) // 2, delta=1)

    def test_notas_de_cada_proyecto(self):
        # Dijkstra y A*.
        self.imagen("captura_0001.png", Paso="2 / 33", Acción="Fijamos el nodo 16",
                    Explicación="Es el candidato con menor f.", Operación="g[16] = 3")
        # Bellman-Ford.
        self.imagen("captura_0002.png", Paso="7 / 90", Pregunta="¿Mejora d[16]?",
                    Comparación="—", Respuesta="SÍ", Proceso="0 + 3 = 3", V=json.dumps([1, 2]))
        # Floyd-Warshall: valores en JSON y una lista de cambios.
        cambios = [[13, 69, "∞", "10", "4", "14"]] * 25
        self.imagen("captura_0003.png", Paso=json.dumps("5"), Intermedio=json.dumps(17),
                    Cambios=json.dumps(cambios, ensure_ascii=False), D=json.dumps([[0]]))
        textos = [notas(QImage(str(p))) for p in capturas_de(self.carpeta)]
        self.assertIn("Acción: Fijamos el nodo 16", textos[0])
        self.assertIn("Operación: g[16] = 3", textos[0])
        self.assertIn("Pregunta: ¿Mejora d[16]?", textos[1])
        self.assertNotIn("[1, 2]", textos[1])
        self.assertNotIn("Comparación", textos[1])  # «—» es un campo vacío.  # Los arreglos completos no van a las notas.
        self.assertTrue(textos[2].startswith("Paso 5"))
        self.assertIn("Nodo intermedio: k = 17", textos[2])
        self.assertIn("D[13][69]: ∞ → 14  (10 + 4)", textos[2])
        self.assertIn("… y 5 más", textos[2])

    def test_intermedio_inicial_de_floyd(self):
        self.imagen("captura_0001.png", Paso=json.dumps("1"), Intermedio="null", Cambios="[]")
        self.assertIn("ninguno", notas(QImage(str(self.carpeta / "captura_0001.png"))))

    def test_solo_pdf_y_regenerar_reemplaza(self):
        self.imagen("captura_0001_a.png")
        (pdf,) = crear_diapositivas(self.carpeta, ("pdf",))
        self.assertFalse((self.carpeta / "diapositivas.pptx").exists())
        self.imagen("captura_0002_b.png")
        crear_diapositivas(self.carpeta, ("pdf",))
        self.assertEqual(paginas_pdf(pdf), 2)

    def test_carpeta_sin_capturas(self):
        with self.assertRaises(ValueError):
            crear_diapositivas(self.carpeta)
        self.assertEqual(list(self.carpeta.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
