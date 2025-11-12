# src/game/map.py
from game.config import BLOCK_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

class Mapas:
    def __init__(self, tipo):
        self.tipo = tipo
        self.obstaculos = []
        self.spawn_seguro_xy = None
        self.gerar_obstaculos()

    def gerar_obstaculos(self):
        cols = SCREEN_WIDTH // BLOCK_SIZE
        rows = SCREEN_HEIGHT // BLOCK_SIZE

        if self.tipo == 1:
            # Mapa 1: completamente vazio (borderless)
            self.obstaculos = []
            self.spawn_seguro_xy = (22 * BLOCK_SIZE, 15 * BLOCK_SIZE)

        elif self.tipo == 2:
            # Mapa 2: Borderless (sem bordas), com obstáculos internos ajustados (-1 x / -1 y)
            self.obstaculos = []

            # Linhas horizontais (todas movidas 1 bloco para cima e 1 para a esquerda)
            self.obstaculos += [(x - 1, 7 - 1) for x in range(4, 17)]     # y=7 → 6
            self.obstaculos += [(x - 1, 4 - 1) for x in range(37, 43)]    # y=4 → 3
            self.obstaculos += [(x - 1, 10 - 1) for x in range(34, 40)]   # y=10 → 9
            self.obstaculos += [(x - 1, 12 - 1) for x in range(17, 26)]   # y=12 → 11
            self.obstaculos += [(x - 1, 14 - 1) for x in range(30, 40)]   # y=14 → 13
            self.obstaculos += [(x - 1, 18 - 1) for x in range(8, 12)]    # y=18 → 17
            self.obstaculos += [(x - 1, 22 - 1) for x in range(4, 8)]     # y=22 → 21
            self.obstaculos += [(x - 1, 27 - 1) for x in range(16, 31)]   # y=27 → 26
            self.obstaculos += [(x - 1, 27 - 1) for x in range(39, 43)]   # y=27 → 26

            # Linhas verticais (também movidas 1 bloco para cima e 1 para a esquerda)
            self.obstaculos += [(42 - 1, y - 1) for y in range(4, 7)]     # x=42 → 41
            self.obstaculos += [(30 - 1, y - 1) for y in range(5, 15)]    # x=30 → 29
            self.obstaculos += [(34 - 1, y - 1) for y in range(5, 11)]    # x=34 → 33
            self.obstaculos += [(21 - 1, y - 1) for y in range(8, 17)]    # x=21 → 20
            self.obstaculos += [(8 - 1, y - 1) for y in range(11, 19)]    # x=8 → 7
            self.obstaculos += [(7 - 1, y - 1) for y in range(22, 28)]    # x=7 → 6
            self.obstaculos += [(4 - 1, y - 1) for y in range(17, 23)]    # x=4 → 3
            self.obstaculos += [(11 - 1, y - 1) for y in range(18, 26)]   # x=11 → 10
            self.obstaculos += [(35 - 1, y - 1) for y in range(20, 28)]   # x=35 → 34
            self.obstaculos += [(42 - 1, y - 1) for y in range(20, 28)]   # x=42 → 41


            self.spawn_seguro_xy = (22 * BLOCK_SIZE, 15 * BLOCK_SIZE)

        elif self.tipo == 3:
            # Mapa 3: Arena com bordas normais e obstáculos deslocados 1 para cima/esquerda
            self.obstaculos = []

            cols = SCREEN_WIDTH // BLOCK_SIZE
            rows = SCREEN_HEIGHT // BLOCK_SIZE

            # Bordas originais (simétricas, cobrindo todo o perímetro)
            for x in range(cols):
                self.obstaculos.append((x, 0))              # Topo
                self.obstaculos.append((x, rows - 1))       # Fundo
            for y in range(rows):
                self.obstaculos.append((0, y))              # Esquerda
                self.obstaculos.append((cols - 1, y))       # Direita

            # Linhas horizontais (movidas 1 bloco para cima/esquerda)
            self.obstaculos += [(x - 1, 6 - 1) for x in range(7, 40)]    # y=6 → 5
            self.obstaculos += [(x - 1, 10 - 1) for x in range(27, 36)]  # y=10 → 9
            self.obstaculos += [(x - 1, 21 - 1) for x in range(10, 20)]  # y=21 → 20
            self.obstaculos += [(x - 1, 25 - 1) for x in range(7, 40)]   # y=25 → 24

            # Linhas verticais (movidas 1 bloco para cima/esquerda)
            self.obstaculos += [(7 - 1, y - 1) for y in range(6, 14)]     # x=7 → 6
            self.obstaculos += [(14 - 1, y - 1) for y in range(10, 17)]   # x=14 → 13
            self.obstaculos += [(23 - 1, y - 1) for y in range(4, 12)]    # x=23 → 22
            self.obstaculos += [(23 - 1, y - 1) for y in range(20, 28)]   # x=23 → 22
            self.obstaculos += [(32 - 1, y - 1) for y in range(15, 22)]   # x=32 → 31
            self.obstaculos += [(39 - 1, y - 1) for y in range(18, 26)]   # x=39 → 38



            # Spawn no centro do mapa
            self.spawn_seguro_xy = (22 * BLOCK_SIZE, 15 * BLOCK_SIZE)

    # ------------------- COLISÕES -------------------

    def verificar_colisao(self, pos_cabeca):
        x, y = pos_cabeca
        bloco_x = x // BLOCK_SIZE
        bloco_y = y // BLOCK_SIZE
        cols = SCREEN_WIDTH // BLOCK_SIZE
        rows = SCREEN_HEIGHT // BLOCK_SIZE

        if self.tipo == 3:
            # colisão com bordas ou obstáculos
            if (bloco_x < 0 or bloco_x >= cols or bloco_y < 0 or bloco_y >= rows):
                return True
            if (bloco_x, bloco_y) in self.obstaculos:
                return True
            return False

        elif self.tipo in (1, 2):
            # teleport nos limites (borderless)
            if bloco_x < 0:
                bloco_x = cols - 1
            elif bloco_x >= cols:
                bloco_x = 0
            if bloco_y < 0:
                bloco_y = rows - 1
            elif bloco_y >= rows:
                bloco_y = 0
            if (bloco_x, bloco_y) in self.obstaculos:
                return True
            return (bloco_x * BLOCK_SIZE, bloco_y * BLOCK_SIZE)

    # ------------------- FUNÇÕES AUXILIARES -------------------

    def spawn_seguro(self, ocupados):
        """Devolve uma posição segura para spawn (fora de obstáculos)."""
        x, y = self.spawn_seguro_xy
        if (x // BLOCK_SIZE, y // BLOCK_SIZE) in self.obstaculos:
            # fallback se algo errar
            return (BLOCK_SIZE * 10, BLOCK_SIZE * 10)
        return (x, y)

    def obstaculos_pixels(self):
        """Retorna lista de obstáculos em coordenadas de píxeis (para evitar spawn de comida)."""
        return [(x * BLOCK_SIZE, y * BLOCK_SIZE) for (x, y) in self.obstaculos]
