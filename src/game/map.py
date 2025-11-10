# src/game/map.py
from game.config import BLOCK_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

class Mapas:
    def __init__(self, tipo):
        self.tipo = tipo
        self.obstaculos = []
        self.gerar_obstaculos()

    def gerar_obstaculos(self):
        """Define os obstáculos com base no tipo de mapa escolhido."""
        cols = SCREEN_WIDTH // BLOCK_SIZE
        rows = SCREEN_HEIGHT // BLOCK_SIZE

        if self.tipo == 1:
            # Mapa 1: Sem obstáculos nem bordas
            self.obstaculos = []

        elif self.tipo == 2:
            # Mapa 2: Sem bordas, mas com obstáculos internos
            self.obstaculos = [
                (x, 5) for x in range(5, 10)
            ] + [
                (x, 10) for x in range(12, 17)
            ] + [
                (3, y) for y in range(7, 13)
            ] + [
                (16, y) for y in range(7, 13)
            ]

        elif self.tipo == 3:
            # Mapa 3: Bordas e obstáculos internos
            self.obstaculos = []

            # Bordas
            for x in range(cols):
                self.obstaculos.append((x, 0))
                self.obstaculos.append((x, rows - 1))
            for y in range(rows):
                self.obstaculos.append((0, y))
                self.obstaculos.append((cols - 1, y))

            # Obstáculos centrais
            self.obstaculos += [(x, 6) for x in range(6, 13)]
            self.obstaculos += [(x, 12) for x in range(6, 13)]
            self.obstaculos += [(5, y) for y in range(7, 11)]
            self.obstaculos += [(13, y) for y in range(7, 11)]
