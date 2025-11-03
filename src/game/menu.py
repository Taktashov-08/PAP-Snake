from game.hud import HUD
from game.score import Score
from game.records import RecordsManager

class Menu:
    """
    Classe responsável por gerir o menu principal do jogo.
    Esta versão é textual (modo terminal), mas a lógica será a mesma para a versão gráfica.
    """
    def __init__(self):
        self.records = RecordsManager()
        self.hud = None
        self.score = None
        self.jogador = ""
        self.modo = ""
        self.dificuldade = ""

    def mostrar_menu_principal(self):
        """Mostra o menu principal e trata da navegação"""
        while True:
            print("==== MENU PRINCIPAL ====")
            print("1 - Jogar")
            print("2 - Recordes")
            print("3 - Ajuda")
            print("4 - Sair")
            opcao = input("Escolhe uma opção (1-4): ")

            if opcao == "1":
                self.menu_jogo()
            elif opcao == "2":
                self.mostrar_recordes()
            elif opcao == "3":
                self.mostrar_ajuda()
            elif opcao == "4":
                print("A sair do jogo... 👋")
                break
            else:
                print("Opção inválida!\n")

    def menu_jogo(self):
        """Menu para selecionar modo e dificuldade"""
        self.jogador = input("Insere o teu nome: ")

        print("\nEscolhe o modo de jogo:")
        print("1 - OG Snake")
        print("2 - Snake Torre")
        print("3 - 1v1 (duas cobras)")
        modo_opcao = input("Escolha: ")

        modos = {"1": "OG Snake", "2": "Snake Torre", "3": "1v1"}
        self.modo = modos.get(modo_opcao, "OG Snake")

        print("\nEscolhe a dificuldade:")
        print("1 - Normal (x1)")
        print("2 - Rápido (x1.5)")
        print("3 - Muito Rápido (x2)")
        dif_opcao = input("Escolha: ")

        multiplicadores = {"1": 1.0, "2": 1.5, "3": 2.0}
        self.dificuldade = ["Normal", "Rápido", "Muito Rápido"][int(dif_opcao) - 1]
        mult = multiplicadores.get(dif_opcao, 1.0)

        # cria HUD e Score temporários
        self.hud = HUD(jogador=self.jogador, modo=self.modo, dificuldade=self.dificuldade)
        self.score = Score(multiplicador=mult)

        print("\nJogo iniciado!")
        self.simular_jogo()

    def simular_jogo(self):
        """Simulação simples de jogo (sem pygame ainda)"""
        import random, time
        for i in range(5):
            pontos = random.randint(5, 25)
            self.score.adicionar_pontos(pontos)
            self.hud.atualizar_pontuacao(self.score.obter_pontuacao())
            self.hud.mostrar_info()
            time.sleep(1)

        print("Fim do jogo!")
        self.records.guardar_pontuacao(
            self.jogador,
            self.modo,
            self.dificuldade,
            self.score.obter_pontuacao()
        )
        print("Pontuação guardada com sucesso!\n")

    def mostrar_recordes(self):
        """Mostra as pontuações guardadas"""
        print("\n=== RECORDES ===")
        pontuacoes = self.records.ler_pontuacoes()
        if not pontuacoes:
            print("Ainda não há recordes registados.")
        else:
            for p in pontuacoes[:10]:
                print(f"{p['nome']:10} | {p['modo']:12} | {p['dificuldade']:10} | {p['pontuacao']:5} | {p['data']}")
        print("================\n")

    def mostrar_ajuda(self):
        """Explica as regras do jogo"""
        print("\n=== AJUDA ===")
        print("Usa as setas para mover a cobra (na versão gráfica).")
        print("Apanha a comida para ganhar pontos e evita colidir com ti próprio.")
        print("Cada dificuldade tem um multiplicador de pontos.")
        print("================\n")

if __name__ == "__main__":
    menu = Menu()
    menu.mostrar_menu_principal()
