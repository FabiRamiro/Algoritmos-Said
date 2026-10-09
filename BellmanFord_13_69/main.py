"""Iniciar con: python main.py"""
import argparse
import sys

def main():
    parser=argparse.ArgumentParser(description='Bellman–Ford visual, paso a paso')
    parser.add_argument('--grafo',help='Ruta opcional a otro archivo JSON')
    args=parser.parse_args()
    try:
        from interfaz import ejecutar
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith('PySide6'):
            print('Instala PySide6 con: python -m pip install -r requirements.txt')
            return 1
        raise
    return ejecutar(args.grafo)

if __name__=='__main__':
    sys.exit(main())
