class HUD:
    """
    Classe responsável por apresentar as informações do jogo:
    pontuação, modo, dificuldade e nome do jogador.
    """
    def __init__(self, jogador="Jogador", modo="OG Snake", dificuldade="Normal"):
        self.jogador = jogador
        self.modo = modo
        self.dificuldade = dificuldade
        self.pontuacao = 0

    def atualizar_pontuacao(self, nova_pontuacao):
        """Atualiza o valor da pontuação atual"""
        self.pontuacao = nova_pontuacao

    def atualizar_info(self, jogador=None, modo=None, dificuldade=None):
        """Permite atualizar dados do jogador, modo ou dificuldade"""
        if jogador:
            self.jogador = jogador
        if modo:
            self.modo = modo
        if dificuldade:
            self.dificuldade = dificuldade

    def mostrar_info(self):
        """Mostra as informações atuais (teste no terminal)"""
        print("=== HUD ===")
        print(f"Jogador: {self.jogador}")
        print(f"Modo: {self.modo}")
        print(f"Dificuldade: {self.dificuldade}")
        print(f"Pontuação: {self.pontuacao}")
        print("============\n")


