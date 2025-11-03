class Score:
    """
    Classe simples para gerir a pontuação do jogador.
    Controla o valor atual, o multiplicador de dificuldade e o reset.
    """
    def __init__(self, multiplicador=1.0):
        self.pontos = 0
        self.multiplicador = multiplicador

    def adicionar_pontos(self, quantidade):
        """Adiciona pontos considerando o multiplicador"""
        pontos_adicionados = int(quantidade * self.multiplicador)
        self.pontos += pontos_adicionados
        print(f"+{pontos_adicionados} pontos (Total: {self.pontos})")

    def resetar(self):
        """Reinicia a pontuação"""
        self.pontos = 0
        print("Pontuação resetada para 0.")

    def obter_pontuacao(self):
        """Devolve o valor atual da pontuação"""
        return self.pontos


