"""Exporta las matrices de Floyd a Excel sin instalar otra biblioteca.

Un XLSX es un ZIP de documentos XML. Aquí solo escribimos celdas, estilos y
hojas: los cálculos pertenecen a algoritmo.py y se exportan como instantáneas.
Las matrices D y R aparecen juntas, como en el ejemplo del usuario.
"""
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile, ZIP_DEFLATED

from algoritmo import numero

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def columna(indice):
    """Convierte una columna numerada desde 1 a A, B, ..., Z, AA, AB..."""
    letras = ''
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def xml(elemento):
    return tostring(elemento, encoding='utf-8', xml_declaration=True)


def estilos():
    """Estilos compartidos: fondo, encabezado, dato, intermedio y cambio."""
    raiz = Element('styleSheet', xmlns=NS)
    fuentes = SubElement(raiz, 'fonts', count='4')
    for color, negrita, tam in [('000000', False, 11), ('000000', True, 11),
                                 ('000000', True, 11), ('000000', True, 11)]:
        fuente = SubElement(fuentes, 'font')
        SubElement(fuente, 'sz', val=str(tam))
        SubElement(fuente, 'color', rgb='FF' + color)
        SubElement(fuente, 'name', val='Calibri')
        if negrita:
            SubElement(fuente, 'b')
    rellenos = SubElement(raiz, 'fills', count='7')
    for tipo, color in [('none', None), ('gray125', None), ('solid', 'FFFFFF'),
                         ('solid', 'FFFFFF'), ('solid', 'F2F2F2'),
                         ('solid', 'E2F0D9'), ('solid', 'FFFFFF')]:
        patron = SubElement(SubElement(rellenos, 'fill'), 'patternFill', patternType=tipo)
        if color:
            SubElement(patron, 'fgColor', rgb='FF' + color)
            SubElement(patron, 'bgColor', indexed='64')
    bordes = SubElement(raiz, 'borders', count='2')
    for con_borde in (False, True):
        borde = SubElement(bordes, 'border')
        for lado in ('left', 'right', 'top', 'bottom'):
            linea = SubElement(borde, lado, **({'style': 'thin'} if con_borde else {}))
            if con_borde:
                SubElement(linea, 'color', rgb='FFD9D9D9')
        SubElement(borde, 'diagonal')
    base = SubElement(raiz, 'cellStyleXfs', count='1')
    SubElement(base, 'xf', numFmtId='0', fontId='0', fillId='0', borderId='0')
    # Índices usados por Hoja: 0 normal, 1 fondo, 2 título, 3 encabezado,
    # 4 dato, 5 fila/columna k, 6 mejora y 7 explicación.
    formatos = [(0, 0, 0), (0, 2, 0), (3, 2, 0), (1, 6, 1),
                (0, 3, 1), (0, 4, 1), (2, 5, 1), (0, 2, 0)]
    celdas = SubElement(raiz, 'cellXfs', count=str(len(formatos)))
    for indice, (fuente, fondo, borde) in enumerate(formatos):
        formato = SubElement(celdas, 'xf', numFmtId='0', fontId=str(fuente),
                             fillId=str(fondo), borderId=str(borde), xfId='0',
                             applyFont='1', applyFill='1', applyBorder='1', applyAlignment='1')
        SubElement(formato, 'alignment', horizontal='left' if indice in (2, 7) else 'center',
                   vertical='center', wrapText='1')
    nombres = SubElement(raiz, 'cellStyles', count='1')
    SubElement(nombres, 'cellStyle', name='Normal', xfId='0', builtinId='0')
    return xml(raiz)


class Hoja:
    def __init__(self, ancho):
        self.ancho = ancho
        self.filas = {}
        self.uniones = []
        self.alturas = {}

    def celda(self, fila, col, valor, estilo=4):
        self.filas.setdefault(fila, {})[col] = (valor, estilo)

    def titulo(self, fila, col, ancho, texto, estilo=2, altura=22):
        self.celda(fila, col, texto, estilo)
        if ancho > 1:
            self.uniones.append(f'{columna(col)}{fila}:{columna(col + ancho - 1)}{fila}')
        self.alturas[fila] = max(altura, self.alturas.get(fila, 0))

    def contenido(self):
        raiz = Element('worksheet', xmlns=NS)
        vistas = SubElement(raiz, 'sheetViews')
        vista = SubElement(vistas, 'sheetView', workbookViewId='0', showGridLines='1', zoomScale='100')
        SubElement(vista, 'pane', xSplit='1', ySplit='9', topLeftCell='B10',
                   activePane='bottomRight', state='frozen')
        SubElement(raiz, 'sheetFormatPr', defaultRowHeight='20')
        columnas = SubElement(raiz, 'cols')
        SubElement(columnas, 'col', min='1', max=str(self.ancho), width='15',
                   customWidth='1', style='1')
        datos = SubElement(raiz, 'sheetData')
        for numero_fila, celdas in sorted(self.filas.items()):
            fila = SubElement(datos, 'row', r=str(numero_fila),
                              ht=str(self.alturas.get(numero_fila, 20)), customHeight='1')
            for col, (valor, estilo) in sorted(celdas.items()):
                celda = SubElement(fila, 'c', r=f'{columna(col)}{numero_fila}', s=str(estilo))
                if isinstance(valor, (int, float)) and isfinite(valor):
                    # Conservar números como números permite seleccionarlos y calcular en Excel.
                    SubElement(celda, 'v').text = str(valor)
                else:
                    celda.set('t', 'inlineStr')
                    texto = numero(valor) if isinstance(valor, (int, float)) else '—' if valor is None else str(valor)
                    SubElement(SubElement(celda, 'is'), 't').text = texto
        uniones = SubElement(raiz, 'mergeCells', count=str(len(self.uniones)))
        for referencia in self.uniones:
            SubElement(uniones, 'mergeCell', ref=referencia)
        return xml(raiz)


def matrices(hoja, fila, paso, nodos):
    """D a la izquierda y R a la derecha; la siguiente iteración va debajo."""
    n = len(nodos)
    cambios = {(c.i, c.j) for c in paso.cambios}
    for col, matriz, nombre in [(1, paso.distancias, 'Matriz de distancias D'),
                                (n + 3, paso.recorridos, 'Matriz de recorridos R')]:
        etapa = 'Inicial' if paso.tipo == 'inicio' else 'Final' if paso.tipo == 'fin' else f'Iteración {paso.iteracion}'
        hoja.titulo(fila, col, n + 1, f'{etapa} — {nombre}')
        hoja.titulo(fila + 1, col, n + 1,
                    f'k = {paso.k if paso.k is not None else "—"} · Cambios: {len(cambios)}',
                    estilo=7, altura=20)
        hoja.celda(fila + 2, col, 'i / j', 3)
        for j, nodo in enumerate(nodos):
            hoja.celda(fila + 2, col + 1 + j, nodo, 5 if nodo == paso.k else 3)
            hoja.celda(fila + 3 + j, col, nodo, 5 if nodo == paso.k else 3)
        for i, valores in enumerate(matriz):
            for j, valor in enumerate(valores):
                estilo = 6 if (i, j) in cambios else 5 if paso.k in (nodos[i], nodos[j]) else 4
                hoja.celda(fila + 3 + i, col + 1 + j, valor, estilo)


def guardar_excel(recorrido, destino, origen, objetivo):
    """Guarda todas las iteraciones y el resultado, aunque no existan PNG.

    El archivo anterior solo se reemplaza después de terminar el nuevo ZIP.
    Si Excel lo mantiene bloqueado, el llamador recibe un OSError.
    """
    nodos = recorrido.nodos
    if not nodos or not recorrido.pasos:
        raise ValueError('No hay matrices para exportar.')
    if origen not in nodos or objetivo not in nodos:
        raise ValueError('El origen y el destino deben pertenecer al recorrido.')
    n = len(nodos)
    if 2 * n + 3 > 16384 or 7 + len(recorrido.pasos) * (n + 5) > 1048576:
        raise ValueError('Las matrices superan los límites de filas o columnas de Excel.')
    final = recorrido.pasos[-1]
    ruta, _ = recorrido.ruta(final, origen, objetivo)
    i, j = nodos.index(origen), nodos.index(objetivo)
    consulta = f'Consulta {origen} → {objetivo}. Costo: {numero(final.distancias[i][j])}. '
    if (i, j) in final.afectados:
        consulta += 'Sin mínimo finito por un ciclo negativo.'
    elif ruta:
        consulta += 'Ruta: ' + ' → '.join(map(str, ruta))
    else:
        consulta += 'No existe camino.'
    hojas = []
    for nombre, pasos in [('Iteraciones', recorrido.pasos), ('Resultado', [final])]:
        hoja = Hoja(2 * n + 3)
        hoja.titulo(1, 1, hoja.ancho, f'Floyd–Warshall · {nombre}')
        hoja.titulo(2, 1, hoja.ancho, consulta, 7, 22)
        hoja.titulo(3, 1, hoja.ancho, '∞ = sin camino. −∞ = sin mínimo finito. — = sin recorrido.', 7)
        hoja.titulo(4, 1, hoja.ancho, 'R: último intermedio; al inicio, destino directo. Verde: mejora. Gris: fila y columna k.', 7)
        hoja.titulo(5, 1, hoja.ancho, 'Para recalcular, cambia los pesos en el programa y exporta de nuevo.', 7)
        for indice, paso in enumerate(pasos):
            matrices(hoja, 7 + indice * (n + 5), paso, nodos)
        hojas.append((nombre, hoja))

    libro = Element('workbook', xmlns=NS, **{'xmlns:r': REL})
    lista = SubElement(libro, 'sheets')
    relaciones = Element('Relationships', xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
    tipos = Element('Types', xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
    SubElement(tipos, 'Default', Extension='rels', ContentType='application/vnd.openxmlformats-package.relationships+xml')
    SubElement(tipos, 'Default', Extension='xml', ContentType='application/xml')
    prefijo = 'application/vnd.openxmlformats-officedocument.spreadsheetml.'
    SubElement(tipos, 'Override', PartName='/xl/workbook.xml', ContentType=prefijo + 'sheet.main+xml')
    SubElement(tipos, 'Override', PartName='/xl/styles.xml', ContentType=prefijo + 'styles+xml')
    for indice, (nombre, _) in enumerate(hojas, 1):
        SubElement(lista, 'sheet', name=nombre, sheetId=str(indice), **{'r:id': f'rId{indice}'})
        SubElement(relaciones, 'Relationship', Id=f'rId{indice}', Type=REL + '/worksheet', Target=f'worksheets/sheet{indice}.xml')
        SubElement(tipos, 'Override', PartName=f'/xl/worksheets/sheet{indice}.xml', ContentType=prefijo + 'worksheet+xml')
    SubElement(relaciones, 'Relationship', Id='styles', Type=REL + '/styles', Target='styles.xml')
    raiz = Element('Relationships', xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
    SubElement(raiz, 'Relationship', Id='workbook', Type=REL + '/officeDocument', Target='xl/workbook.xml')

    destino = Path(destino)
    temporal = None
    try:
        with NamedTemporaryFile(dir=destino.parent, suffix='.tmp.xlsx', delete=False) as archivo:
            temporal = Path(archivo.name)
        with ZipFile(temporal, 'w', ZIP_DEFLATED) as archivo:
            archivo.writestr('[Content_Types].xml', xml(tipos))
            archivo.writestr('_rels/.rels', xml(raiz))
            archivo.writestr('xl/workbook.xml', xml(libro))
            archivo.writestr('xl/_rels/workbook.xml.rels', xml(relaciones))
            archivo.writestr('xl/styles.xml', estilos())
            for indice, (_, hoja) in enumerate(hojas, 1):
                archivo.writestr(f'xl/worksheets/sheet{indice}.xml', hoja.contenido())
        temporal.replace(destino)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
    return destino
