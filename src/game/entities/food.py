# src/game/entities/food.py
import random
import pygame
from game.config import FOOD_COLOR, FOOD_BORDER, FOOD_HIGHLIGHT


class Food:
    """Comida — circulo com brilho discreto."""

    def __init__(self, area_rect, block_size, color=None, border_color=None):
        self.area         = area_rect
        self.block        = block_size
        self.color        = color        or FOOD_COLOR
        self.border_color = border_color or FOOD_BORDER
        self.pos          = None
        self.spawn([])

    def spawn(self, occupied_positions, obstaculos_pixels=None):
        if obstaculos_pixels is None:
            obstaculos_pixels = []
        x0, y0, w, h = self.area
        cols, rows = w // self.block, h // self.block
        attempts = 0
        while True:
            x = x0 + random.randint(0, cols - 1) * self.block
            y = y0 + random.randint(0, rows - 1) * self.block
            if (x, y) not in occupied_positions and (x, y) not in obstaculos_pixels:
                self.pos = (x, y)
                return
            attempts += 1
            if attempts > 500:
                self.pos = (x, y)
                return

    def draw(self, surface):
        if self.pos is None:
            return
        x, y = self.pos
        b    = self.block
        m    = max(1, b // 6)
        outer  = pygame.Rect(x+m, y+m, b-m*2, b-m*2)
        pygame.draw.ellipse(surface, self.color, outer)
        hs = max(2, b // 4)
        pygame.draw.ellipse(surface, FOOD_HIGHLIGHT, pygame.Rect(x+m+1, y+m+1, hs, hs))
        pygame.draw.ellipse(surface, self.border_color, outer, 1)
