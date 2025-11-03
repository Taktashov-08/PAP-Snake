import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


#2 para testar menu:
#from game.menu import Menu
#if __name__ == "__main__":
#    from game.menu import Menu
#    Menu().mostrar_menu_principal()


#Para testar game:
from game.engine import Game
if __name__ == "__main__":
   # podes personalizar nome/dificuldade aqui ou criar menu prévio (terminal/menu.py)
   g = Game(player_name="Samuel", modo="OG Snake", dificuldade="Muito Rápido")
   g.run()

