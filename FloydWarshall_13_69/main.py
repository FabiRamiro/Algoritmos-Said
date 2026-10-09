"""Ejecutar: python main.py [--grafo archivo.json]."""
import argparse
import sys


def main():
    parser=argparse.ArgumentParser(description='Floyd–Warshall visual, todos los pares')
    parser.add_argument('--grafo',help='Grafo JSON opcional')
    args=parser.parse_args()
    from interfaz import ejecutar
    return ejecutar(args.grafo)


if __name__=='__main__':
    sys.exit(main())
