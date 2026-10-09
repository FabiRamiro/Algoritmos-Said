"""Importa cada proyecto desde su carpeta sin que sus módulos se mezclen.

Los cuatro proyectos usan los mismos nombres (`algoritmo`, `interfaz`,
`capturas`, `tema`…) y se importan entre sí con `from algoritmo import …`.
Para cargarlos en un mismo proceso, cada importación se hace con la carpeta
al frente de `sys.path` y con esos nombres libres en `sys.modules`. Al
terminar, los módulos se renombran con un prefijo propio: siguen funcionando
porque cada uno ya guarda referencias directas a lo que importó.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


def importar_aislado(carpeta: Path | str, modulo: str, alias: str):
    if f"{alias}.{modulo}" in sys.modules:
        return sys.modules[f"{alias}.{modulo}"]
    carpeta = Path(carpeta).resolve()
    if not (carpeta / f"{modulo}.py").exists():
        raise FileNotFoundError(f"No existe {modulo}.py en {carpeta}")
    locales = {p.stem for p in carpeta.glob("*.py")}
    # Apartar temporalmente los módulos de otro proyecto con el mismo nombre.
    apartados = {n: sys.modules.pop(n) for n in list(sys.modules) if n in locales}
    sys.path.insert(0, str(carpeta))
    try:
        return importlib.import_module(modulo)
    finally:
        sys.path.remove(str(carpeta))
        for nombre in locales:
            cargado = sys.modules.pop(nombre, None)
            if cargado is not None:
                sys.modules[f"{alias}.{nombre}"] = cargado
        sys.modules.update(apartados)
