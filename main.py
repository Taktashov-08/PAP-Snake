import sys, os

# Garante que o caminho é sempre absoluto, independente de como o script é chamado
_raiz = os.path.abspath(os.path.dirname(__file__))
_src  = os.path.join(_raiz, "src")

if _src not in sys.path:
    sys.path.insert(0, _src)

from game.ui.menu import Menu

if __name__ == "__main__":
    menu = Menu()
    menu.run()
