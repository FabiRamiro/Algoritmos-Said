"""Pruebas del guardado en segundo plano sin abrir ventanas en el escritorio."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import wave
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QMessageBox

from aplicacion import Laboratorio
from pantalla_carga import MULTIMEDIA, PantallaCarga, completar_capturas


class PruebasCarga(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def esperar(self, controlador):
        bucle = QEventLoop()
        limite = QTimer()
        limite.setSingleShot(True)
        limite.timeout.connect(bucle.quit)
        controlador.terminado.connect(bucle.quit)
        limite.start(60000)
        bucle.exec()
        controlador.terminado.disconnect(bucle.quit)
        self.assertFalse(controlador.isActive(), "El trabajador no terminó")
        limite.stop()

    def test_cuatro_algoritmos_y_animacion_durante_guardado(self):
        ventana = Laboratorio()
        try:
            with TemporaryDirectory() as temporal:
                for clave in ("dijkstra", "bellman-ford", "floyd-warshall", "astar"):
                    with self.subTest(algoritmo=clave):
                        vista = ventana.cargar(clave)
                        sesion = vista.capturas
                        sesion.carpeta = Path(temporal) / clave
                        indices = list(getattr(sesion, "indices", range(len(vista.recorrido.pasos))))[:2]
                        esperada = sesion.imagen(indices[0])
                        vista.lote_pendientes = indices.copy()
                        controlador = vista.lote_timer
                        controlador.start()
                        pulsos = []
                        reloj = QTimer()
                        reloj.timeout.connect(lambda: pulsos.append(True))
                        reloj.start(10)
                        self.esperar(controlador)
                        reloj.stop()
                        self.assertTrue(pulsos, "La interfaz debe atender eventos durante el guardado")
                        self.assertIsNone(controlador.pantalla)
                        self.assertTrue(set(indices).issubset(sesion.guardados))
                        obtenida = QImage(str(sesion.carpeta / sesion.nombre(indices[0])))
                        self.assertEqual(obtenida, esperada, "La captura debe conservar su contenido")
        finally:
            for vista in ventana.vistas.values():
                vista.lote_timer.stop()
            ventana.close()

    def test_pausa_reintento_error_y_diapositivas(self):
        ventana = Laboratorio("dijkstra")
        vista = ventana.vistas["dijkstra"]
        try:
            with TemporaryDirectory() as temporal:
                vista.capturas.carpeta = Path(temporal)
                indices = list(vista.capturas.indices)[:3]
                vista.lote_pendientes = indices.copy()
                vista.lote_timer.start()
                vista.lote_timer.pantalla.canceled.emit()
                self.assertFalse(vista.lote_timer.isActive())
                self.assertIsNone(vista.lote_timer.pantalla)
                self.assertTrue(completar_capturas(vista, indices))
                self.assertTrue(set(indices).issubset(vista.capturas.guardados))
                with patch.object(type(vista.capturas), "guardar", side_effect=OSError("sin espacio")):
                    with patch.object(QMessageBox, "warning") as aviso:
                        self.assertFalse(completar_capturas(vista, [indices[-1]]))
                        aviso.assert_called_once()
                self.assertIsNone(vista.lote_timer.pantalla)
                self.assertTrue(completar_capturas(vista, indices))
        finally:
            vista.lote_timer.stop()
            ventana.close()

    def test_multimedia_opcional(self):
        for algoritmo, video in MULTIMEDIA.items():
            pantalla = PantallaCarga(2, algoritmo=algoritmo)
            self.assertEqual(pantalla.ruta_video.name, video)
            self.assertIs(pantalla.reproductor.videoOutput(), pantalla.video)
            self.assertIs(pantalla.reproductor.audioOutput(), pantalla.audio)
            pantalla.close()
        with patch.dict(MULTIMEDIA, {"Dijkstra_13_69": "no-existe.mp4"}):
            pantalla = PantallaCarga(2)
            self.assertTrue(pantalla.reproductor.source().isEmpty())
            self.assertTrue(pantalla.video.isHidden())
            pantalla.close()

    def test_audio_se_reproduce_y_se_detiene(self):
        from PySide6.QtMultimedia import QMediaPlayer
        with TemporaryDirectory() as temporal:
            cancion = Path(temporal) / "silencio.wav"
            with wave.open(str(cancion), "wb") as archivo:
                archivo.setnchannels(1)
                archivo.setsampwidth(2)
                archivo.setframerate(8000)
                archivo.writeframes(b"\x00\x00" * 8000)
            with patch.dict(MULTIMEDIA, {"Dijkstra_13_69": str(cancion)}):
                pantalla = PantallaCarga(2)
                try:
                    bucle = QEventLoop()
                    pantalla.reproductor.playbackStateChanged.connect(bucle.quit)
                    pantalla.show()
                    if pantalla.reproductor.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                        QTimer.singleShot(3000, bucle.quit)
                        bucle.exec()
                    self.assertEqual(pantalla.reproductor.playbackState(), QMediaPlayer.PlaybackState.PlayingState)
                    self.assertEqual(pantalla.reproductor.loops(), QMediaPlayer.Loops.Infinite)
                    pantalla.hide()
                    self.assertEqual(pantalla.reproductor.playbackState(), QMediaPlayer.PlaybackState.StoppedState)
                finally:
                    pantalla.close()
                    pantalla.reproductor.setSource(QUrl())

    def test_video_danado_no_interrumpe_la_carga(self):
        from PySide6.QtMultimedia import QMediaPlayer
        with TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "danado.mp4"
            ruta.write_bytes(b"archivo invalido")
            with patch.dict(MULTIMEDIA, {"Dijkstra_13_69": str(ruta)}):
                pantalla = PantallaCarga(2)
                bucle = QEventLoop()
                limite = QTimer()
                limite.setSingleShot(True)
                limite.timeout.connect(bucle.quit)
                pantalla.reproductor.errorOccurred.connect(bucle.quit)
                pantalla.show()
                limite.start(3000)
                if pantalla.reproductor.error() == QMediaPlayer.Error.NoError:
                    bucle.exec()
                limite.stop()
                self.assertNotEqual(pantalla.reproductor.error(), QMediaPlayer.Error.NoError)
                self.assertTrue(pantalla.video.isHidden())
                pantalla.setValue(1)
                self.assertEqual(pantalla.value(), 1)
                pantalla.close()
                pantalla.reproductor.setSource(QUrl())


if __name__ == "__main__":
    unittest.main()
