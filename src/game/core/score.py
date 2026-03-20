# src/game/core/score.py


class Score:
    """Gestao simples de pontuacao com multiplicador de dificuldade."""

    def __init__(self, multiplicador=1.0):
        self.pontos       = 0
        self.multiplicador = multiplicador

    def adicionar_pontos(self, quantidade):
        self.pontos += int(quantidade * self.multiplicador)

    def resetar(self):
        self.pontos = 0

    def obter_pontuacao(self):
        return self.pontos
