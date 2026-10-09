"""Inicia el laboratorio con los cuatro algoritmos. Ejecuta: python main.py"""
import argparse
import sys

CLAVES = ("dijkstra", "bellman-ford", "floyd-warshall", "astar")


def main():
    parser = argparse.ArgumentParser(description="Dijkstra, Bellman-Ford, Floyd-Warshall y A* en una sola aplicación")
    parser.add_argument("--algoritmo", choices=CLAVES,
                        help="Abrir directamente un algoritmo en lugar de la pantalla de inicio")
    args = parser.parse_args()
    try:
        from aplicacion import ejecutar
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            print("Falta PySide6. Instala la dependencia con:")
            print(f'  "{sys.executable}" -m pip install -r requirements.txt')
            return 1
        raise
    return ejecutar(args.algoritmo)


if __name__ == "__main__":
    sys.exit(main())
