"""Convierte una carpeta de capturas en diapositivas PDF y PowerPoint.

Cada captura ocupa una diapositiva completa: la imagen ya contiene el grafo
y la explicación del paso. El texto que cada proyecto guarda dentro del PNG
(acción, explicación, operación…) pasa a las notas del orador del PowerPoint.

Uso: python diapositivas.py <carpeta de capturas> [--formato pdf|pptx|ambos]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PySide6.QtCore import QMarginsF, QRectF, QSizeF
from PySide6.QtGui import QGuiApplication, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter

ANCHO_PULGADAS = 13.333  # Ancho de una diapositiva panorámica estándar.
FONDO = "0C0D0F"         # El mismo fondo del tema, por si una imagen no llena la diapositiva.
# Claves de texto que guardan los proyectos, en el orden en que se leen.
CLAVES_TEXTO = ("Acción", "Explicación", "Operación", "Pregunta", "Comparación",
                "Respuesta", "Proceso")
MAX_CAMBIOS = 20
# Más diapositivas que esto deja de ser una presentación (y pesa cientos de MB).
LIMITE = 300


def capturas_de(carpeta: Path) -> list[Path]:
    """Solo las capturas numeradas; los nombres con ceros a la izquierda dan el orden."""
    return sorted(Path(carpeta).glob("captura_*.png"))


def _json(valor: str):
    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return valor


def notas(imagen: QImage) -> str:
    """Texto legible a partir de los metadatos del PNG, sea cual sea el proyecto."""
    lineas = []
    paso = _json(imagen.text("Paso"))
    if paso not in ("", None):
        lineas.append(f"Paso {paso}")
    for clave in CLAVES_TEXTO:
        valor = imagen.text(clave).strip()
        if valor and valor != "—":  # Bellman-Ford usa «—» para un campo sin contenido.
            lineas.append(f"{clave}: {valor}")
    # Floyd-Warshall guarda el intermedio y los cambios de la matriz como JSON.
    if imagen.text("Intermedio"):
        k = _json(imagen.text("Intermedio"))
        lineas.append("Nodo intermedio: " + ("ninguno (inicialización)" if k is None else f"k = {k}"))
    cambios = _json(imagen.text("Cambios")) if imagen.text("Cambios") else []
    if isinstance(cambios, list) and cambios:
        lineas.append(f"Cambios en la matriz D ({len(cambios)}):")
        for i, j, anterior, izquierda, derecha, nuevo in cambios[:MAX_CAMBIOS]:
            lineas.append(f"  D[{i}][{j}]: {anterior} → {nuevo}  ({izquierda} + {derecha})")
        if len(cambios) > MAX_CAMBIOS:
            lineas.append(f"  … y {len(cambios)-MAX_CAMBIOS} más")
    return "\n".join(lineas)


def _escribir(destino: Path, escribir):
    """Escribe en un temporal y reemplaza: un archivo abierto no queda a medias."""
    temporal = destino.with_name(destino.stem + ".tmp" + destino.suffix)
    try:
        escribir(temporal)
        temporal.replace(destino)
    except PermissionError as exc:
        temporal.unlink(missing_ok=True)
        raise PermissionError(f"No se pudo escribir {destino.name}. ¿Está abierto en otro programa?") from exc
    except BaseException:
        temporal.unlink(missing_ok=True)
        raise
    return destino


def crear_pdf(imagenes: list[Path], destino: Path) -> Path:
    def escribir(ruta):
        writer = QPdfWriter(str(ruta))
        writer.setTitle(destino.parent.name)
        writer.setResolution(144)
        painter = None
        try:
            for n, archivo in enumerate(imagenes):
                imagen = QImage(str(archivo))
                if imagen.isNull():
                    raise ValueError(f"No se pudo leer {archivo.name}")
                # Cada página tiene la proporción de su imagen: sin bandas vacías.
                alto = ANCHO_PULGADAS * imagen.height() / imagen.width()
                pagina = QPageLayout(QPageSize(QSizeF(ANCHO_PULGADAS, alto), QPageSize.Unit.Inch, "captura"),
                                     QPageLayout.Orientation.Portrait, QMarginsF())
                writer.setPageLayout(pagina)
                if painter is None:
                    painter = QPainter(writer)
                else:
                    writer.newPage()
                painter.drawImage(QRectF(0, 0, writer.width(), writer.height()), imagen)
        finally:
            if painter is not None:
                painter.end()

    return _escribir(destino, escribir)


def crear_pptx(imagenes: list[Path], destino: Path) -> Path:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches

    primera = QImage(str(imagenes[0]))
    if primera.isNull():
        raise ValueError(f"No se pudo leer {imagenes[0].name}")
    presentacion = Presentation()
    presentacion.core_properties.title = destino.parent.name
    presentacion.slide_width = Inches(ANCHO_PULGADAS)
    presentacion.slide_height = int(presentacion.slide_width * primera.height() / primera.width())
    ancho, alto = presentacion.slide_width, presentacion.slide_height
    vacia = presentacion.slide_layouts[6]
    for archivo in imagenes:
        imagen = QImage(str(archivo))
        if imagen.isNull():
            raise ValueError(f"No se pudo leer {archivo.name}")
        diapositiva = presentacion.slides.add_slide(vacia)
        diapositiva.background.fill.solid()
        diapositiva.background.fill.fore_color.rgb = RGBColor.from_string(FONDO)
        # Ajustar sin deformar y centrar, por si alguna imagen tiene otra proporción.
        escala = min(ancho / imagen.width(), alto / imagen.height())
        w, h = int(imagen.width()*escala), int(imagen.height()*escala)
        diapositiva.shapes.add_picture(str(archivo), (ancho-w)//2, (alto-h)//2, w, h)
        diapositiva.notes_slide.notes_text_frame.text = notas(imagen)
    return _escribir(destino, lambda ruta: presentacion.save(str(ruta)))


def crear_diapositivas(carpeta: Path | str, formatos=("pdf", "pptx")) -> list[Path]:
    """Crea `diapositivas.pdf` y/o `diapositivas.pptx` dentro de la carpeta."""
    carpeta = Path(carpeta)
    imagenes = capturas_de(carpeta)
    if not imagenes:
        raise ValueError(f"No hay capturas en {carpeta}")
    creados = []
    if "pdf" in formatos:
        creados.append(crear_pdf(imagenes, carpeta / "diapositivas.pdf"))
    if "pptx" in formatos:
        creados.append(crear_pptx(imagenes, carpeta / "diapositivas.pptx"))
    return creados


def pptx_disponible() -> bool:
    try:
        import pptx  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Crea diapositivas a partir de una carpeta de capturas")
    parser.add_argument("carpeta", help="Carpeta de una sesión, por ejemplo AStar_13_69/capturas/<fecha>_13-69")
    parser.add_argument("--formato", choices=("pdf", "pptx", "ambos"), default="ambos")
    args = parser.parse_args()
    formatos = ("pdf", "pptx") if args.formato == "ambos" else (args.formato,)
    if "pptx" in formatos and not pptx_disponible():
        print("Falta python-pptx: python -m pip install -r requirements.txt")
        if args.formato == "pptx":
            return 1
        formatos = ("pdf",)
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])  # QPainter lo necesita.
    try:
        creados = crear_diapositivas(args.carpeta, formatos)
    except (ValueError, OSError) as exc:
        print(exc)
        return 1
    for ruta in creados:
        print(ruta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
