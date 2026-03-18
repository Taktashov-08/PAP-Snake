# Descrição: Gere a criação (spawn) e a renderização da comida no tabuleiro.
# Estética: Círculos com um pequeno brilho (highlight) para um aspeto polido.
# src/game/food.py
import random
import pygame
from game.config import FOOD_COLOR, FOOD_BORDER, FOOD_HIGHLIGHT


class Food:
    """
    Representa a comida no jogo — um círculo com um brilho discreto.
    Estilo visual focado em clareza, sem efeitos de néon excessivos.
    """

    def __init__(self, area_rect, block_size, color=None, border_color=None):
        self.area         = area_rect  # Retângulo que define o limite do campo de jogo
        self.block        = block_size # Tamanho de cada "quadrado" da grelha
        self.color        = color        or FOOD_COLOR
        self.border_color = border_color or FOOD_BORDER
        self.pos          = None       # Posição (x, y) atual da comida
        self.spawn([])                 # Tenta colocar a comida no mapa ao iniciar

    # ── Lógica de Posicionamento ──────────────────────────────────────────────
    def spawn(self, occupied_positions, obstaculos_pixels=None):
        """
        Encontra uma posição aleatória na grelha que não esteja ocupada.
        
        Args:
            occupied_positions: Lista/Set de coordenadas ocupadas pelas cobras.
            obstaculos_pixels: Lista/Set de coordenadas das paredes/obstáculos.
        """
        if obstaculos_pixels is None:
            obstaculos_pixels = []
            
        x0, y0, w, h = self.area
        # Calcula o número de colunas e linhas disponíveis com base no tamanho do bloco
        cols, rows = w // self.block, h // self.block
        
        attempts = 0
        while True:
            # Gera uma coordenada alinhada com a grelha
            x = x0 + random.randint(0, cols - 1) * self.block
            y = y0 + random.randint(0, rows - 1) * self.block
            
            # Verifica se a posição está livre
            if (x, y) not in occupied_positions and (x, y) not in obstaculos_pixels:
                self.pos = (x, y)
                return
            
            # Limite de tentativas para evitar loops infinitos caso o mapa esteja cheio
            attempts += 1
            if attempts > 500:
                self.pos = (x, y)
                return

    # ── Renderização ──────────────────────────────────────────────────────────
    def draw(self, surface):
        """Desenha a comida como uma elipse com efeitos de luz simples."""
        if self.pos is None:
            return

        x, y = self.pos
        b    = self.block
        m    = max(1, b // 6)   # Margem para a comida não tocar nos limites do bloco

        # Retângulo que define o corpo principal da comida
        outer = pygame.Rect(x + m, y + m, b - m * 2, b - m * 2)

        # 1. Desenha o corpo da comida (Círculo preenchido)
        pygame.draw.ellipse(surface, self.color, outer)

        # 2. Highlight (Ponto de luz no canto superior esquerdo para dar volume)
        hs = max(2, b // 4) # Tamanho do brilho proporcional ao bloco
        hi_rect = pygame.Rect(x + m + 1, y + m + 1, hs, hs)
        pygame.draw.ellipse(surface, FOOD_HIGHLIGHT, hi_rect)

        # 3. Desenha a borda fina para melhor contraste com o fundo
        pygame.draw.ellipse(surface, self.border_color, outer, 1)