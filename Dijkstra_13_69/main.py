"""Inicia el laboratorio visual. Ejecuta: python main.py"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Dijkstra animado, sin NetworkX")
    parser.add_argument("--grafo", help="Ruta opcional a un grafo JSON exportado")
    args = parser.parse_args()
    try:
        from interfaz import ejecutar
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            print("Falta PySide6. Instala la dependencia con:")
            print(f'  "{sys.executable}" -m pip install -r requirements.txt')
            return 1
        raise
    return ejecutar(args.grafo)


if __name__ == "__main__":
    sys.exit(main())
