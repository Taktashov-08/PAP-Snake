import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from game.menu import Menu

if __name__ == "__main__":
    menu = Menu()
    menu.run()
