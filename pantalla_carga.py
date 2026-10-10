"""Pantalla compartida para el guardado de capturas de los cuatro algoritmos."""
from pathlib import Path
from copy import copy
from types import MethodType

from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot, QUrl, QEventLoop
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QProgressDialog, QVBoxLayout

RAIZ = Path(__file__).resolve().parent
# Cada MP4 contiene su propio audio. Las rutas relativas parten de esta carpeta.
MULTIMEDIA = {
    "Dijkstra_13_69": "dancing1.mp4",
    "BellmanFord_13_69": "dancing2.mp4",
    "FloydWarshall_13_69": "dancing3.mp4",
    "AStar_13_69": "dancing4.mp4",
}


def algoritmo_de(vista):
    # El módulo conserva __file__ incluso cuando el laboratorio lo importa con un alias.
    return Path(vista.exportar_todo.__func__.__globals__["__file__"]).parent.name


class PantallaCarga(QProgressDialog):
    def __init__(self, total, parent=None, boton="Pausar", algoritmo="Dijkstra_13_69"):
        super().__init__("", boton, 0, total, parent)
        self.setWindowTitle("Guardando capturas")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumDuration(0)
        self.setMinimumWidth(520)
        self.setAutoClose(False)
        self.setAutoReset(False)
        barra = QProgressBar(self)
        barra.setRange(0, total)
        barra.setFormat("%v de %m capturas · %p%")
        self.setBar(barra)
        self.imagen = QLabel()
        self.imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagen.setMinimumSize(480, 270)
        self.setLabel(self.imagen)
        # Un mismo reproductor mantiene sincronizados el video y su pista de audio.
        self.video = QVideoWidget(self.imagen)
        self.video.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        espacio = QVBoxLayout(self.imagen)
        espacio.setContentsMargins(0, 0, 0, 0)
        espacio.addWidget(self.video)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.35)
        self.reproductor = QMediaPlayer(self)
        self.reproductor.setAudioOutput(self.audio)
        self.reproductor.setVideoOutput(self.video)
        self.reproductor.setLoops(QMediaPlayer.Loops.Infinite)
        self.reproductor.errorOccurred.connect(self.error_video)
        self.ruta_video = RAIZ / MULTIMEDIA[algoritmo]
        if self.ruta_video.is_file():
            self.reproductor.setSource(QUrl.fromLocalFile(str(self.ruta_video)))
        else:
            self.video.hide()
            self.imagen.setText(f"Guardando capturas…\n\nVideo no encontrado: {self.ruta_video.name}")
        self.setValue(0)

    def error_video(self, error, mensaje):
        # Un video dañado no debe interrumpir la exportación de capturas.
        self.reproductor.stop()
        self.video.hide()
        self.imagen.setText("Guardando capturas…\n\nNo se pudo reproducir el video.")
        self.imagen.setToolTip(mensaje)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.reproductor.source().isEmpty():
            self.reproductor.play()

    def hideEvent(self, event):
        self.reproductor.stop()
        super().hideEvent(event)


class DibujoCapturas:
    """Datos y funciones de dibujo, sin una ventana QWidget en el hilo de trabajo.

    Estas seis funciones dibujan sobre QImage con rectángulo explícito y limpio=True.
    Así no consultan el tamaño, zoom ni selección del widget original.
    """
    def __init__(self, lienzo):
        self.grafo = lienzo.grafo
        self.origen, self.destino = lienzo.origen, lienzo.destino
        self.pesos = self.distancias = True
        self.elegido = None
        for nombre in ("limites", "transformacion", "punto", "camino", "estado_color", "dibujar"):
            setattr(self, nombre, MethodType(getattr(type(lienzo), nombre), self))


def copiar_sesion(vista):
    """Los datos del recorrido se leen; el conjunto de guardados pertenece al trabajador."""
    sesion = copy(vista.capturas)
    sesion.guardados = set(sesion.guardados)
    dibujante = DibujoCapturas(vista.lienzo)
    if hasattr(sesion, "dibujar_grafo"):
        sesion.dibujar_grafo = dibujante.dibujar
    else:
        sesion.dibujar = dibujante.dibujar
    return sesion


class GuardadorCapturas(QThread):
    avance = Signal(int)

    def __init__(self, sesion, indices, parent=None):
        super().__init__(parent)
        self.sesion = sesion
        self.indices = tuple(indices)
        self.error = None
        self.completadas = 0

    def run(self):
        try:
            for indice in self.indices:
                if self.isInterruptionRequested():
                    break
                self.sesion.guardar(indice)
                self.completadas += 1
                self.avance.emit(self.completadas)
        except Exception as exc:
            self.error = exc


class TemporizadorCapturas(QObject):
    """Mantiene start/stop/isActive para las vistas, pero exporta en otro hilo."""
    terminado = Signal(bool)

    def __init__(self, vista):
        super().__init__(vista)
        self.vista = vista
        self.pantalla = None
        self.trabajador = None
        self.ultimo_error = None
        QApplication.instance().aboutToQuit.connect(self.stop)

    def start(self, intervalo=0):
        self.stop()
        self.vista.pausar()
        self.total = len(self.vista.lote_pendientes)
        if not self.total:
            return
        self.ultimo_error = None
        self.vista.error_captura = False
        self.sesion_original = self.vista.capturas
        self.trabajador = GuardadorCapturas(copiar_sesion(self.vista), self.vista.lote_pendientes, self)
        self.trabajador.avance.connect(self.actualizar)
        self.trabajador.finished.connect(self.finalizar)
        self.pantalla = PantallaCarga(self.total, self.vista.window(), algoritmo=algoritmo_de(self.vista))
        self.pantalla.canceled.connect(self.vista.exportar_todo)
        self.pantalla.show()
        self.trabajador.start()

    def isActive(self):
        return self.trabajador is not None

    def stop(self):
        trabajador = self.trabajador
        if trabajador is not None:
            trabajador.requestInterruption()
            # Terminar el PNG en curso antes de permitir reintentos sobre el mismo archivo.
            trabajador.wait()
            self.recoger_resultado(trabajador)
            self.trabajador = None
            trabajador.deleteLater()
        if self.pantalla is not None:
            self.pantalla.hide()
            self.pantalla.deleteLater()
            self.pantalla = None
        if trabajador is not None:
            self.terminado.emit(False)

    def recoger_resultado(self, trabajador):
        self.sesion_original.guardados.update(trabajador.sesion.guardados)
        self.vista.lote_pendientes = [i for i in self.vista.lote_pendientes
                                     if i not in self.sesion_original.guardados]

    def estado(self):
        if hasattr(self.vista, "mostrar_estado_capturas"):
            self.vista.mostrar_estado_capturas()
        else:
            self.vista.estado_guardado()

    @Slot(int)
    def actualizar(self, completadas):
        trabajador = self.sender()
        if trabajador is not self.trabajador:
            return  # Una señal antigua puede llegar después de pausar y reintentar.
        self.sesion_original.guardados.update(trabajador.indices[:completadas])
        if self.pantalla is not None:
            self.pantalla.setValue(completadas)
        self.estado()

    @Slot()
    def finalizar(self):
        trabajador = self.sender()
        if trabajador is not self.trabajador:
            return
        trabajador.wait()
        self.recoger_resultado(trabajador)
        self.ultimo_error = trabajador.error
        self.trabajador = None
        trabajador.deleteLater()
        self.pantalla.hide()
        self.pantalla.deleteLater()
        self.pantalla = None
        boton = getattr(self.vista, "todos_btn", None)
        if boton is None:
            boton = self.vista.todos
        boton.setText("Todos los pasos guardados" if self.ultimo_error is None else "Reintentar exportación")
        self.estado()
        self.terminado.emit(self.ultimo_error is None)
        if self.ultimo_error is not None:
            for nombre in ("fallo_captura", "error_guardado", "fallo"):
                if hasattr(self.vista, nombre):
                    getattr(self.vista, nombre)(self.ultimo_error)
                    break


def completar_capturas(vista, indices):
    """Espera el resultado permitiendo que Qt siga animando y atendiendo eventos."""
    controlador = vista.lote_timer
    controlador.stop()
    vista.lote_pendientes = list(indices)
    if not indices:
        return True
    bucle = QEventLoop()
    resultado = []

    def terminado(exito):
        resultado.append(exito)
        bucle.quit()

    controlador.terminado.connect(terminado)
    try:
        controlador.start()
        bucle.exec()
    finally:
        controlador.terminado.disconnect(terminado)
    return bool(resultado and resultado[-1])
