# src/game/entities/food.py
"""
Comida com animação de pulso suave.
A fase de animação é aleatória por instância para variedade visual
quando existem múltiplos itens de comida em simultâneo.
"""
from __future__ import annotations

import math
import random

import pygame

from game.config import FOOD_COLOR, FOOD_BORDER, FOOD_HIGHLIGHT


class Food:
    """
    Item de comida renderizado como elipse pulsante.

    A animação é avançada por `update(dt)` chamado pelo modo de jogo
    no `visual_update` — não depende do FPS de lógica.
    """

    _PULSE_SPEED: float = 3.2   # ciclos de pulso por segundo

    def __init__(self, area_rect, block_size: int,
                 color=None, border_color=None) -> None:
        self.area         = area_rect
        self.block        = block_size
        self.color        = color        or FOOD_COLOR
        self.border_color = border_color or FOOD_BORDER
        self.pos          = None
        self._phase: float = random.uniform(0.0, math.tau)   # fase inicial aleatória
        self.spawn([])

    # ── Posicionamento ────────────────────────────────────────────────────────

    def spawn(self, occupied_positions, obstaculos_pixels=None) -> None:
        """Coloca a comida num bloco livre da grelha."""
        if obstaculos_pixels is None:
            obstaculos_pixels = []
        x0, y0, w, h = self.area
        cols = w // self.block
        rows = h // self.block
        last = None
        for _ in range(500):
            x = x0 + random.randint(0, cols - 1) * self.block
            y = y0 + random.randint(0, rows - 1) * self.block
            last = (x, y)
            if (x, y) not in occupied_positions and (x, y) not in obstaculos_pixels:
                self.pos = (x, y)
                self._phase = random.uniform(0.0, math.tau)
                return
        self.pos = last   # fallback de segurança

    # ── Animação ──────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Avança a fase de animação; chamar a ~60 fps para suavidade máxima."""
        self._phase += self._PULSE_SPEED * dt

    # ── Desenho ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if self.pos is None:
            return
        x, y = self.pos
        b    = self.block
        m    = max(1, b // 6)

        # Raio oscila ±12 % em torno do valor base
        pulse   = 1.0 + 0.12 * math.sin(self._phase)
        base_r  = max(2.0, (b / 2.0 - m))
        r       = max(2, int(base_r * pulse))

        cx, cy  = x + b // 2, y + b // 2

        # Corpo
        outer = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.ellipse(surface, self.color, outer)

        # Brilho no canto superior esquerdo
        hs  = max(2, r // 2)
        hx  = cx - r // 4
        hy  = cy - r // 4
        pygame.draw.ellipse(surface, FOOD_HIGHLIGHT,
                            pygame.Rect(hx - hs // 2, hy - hs // 2, hs, hs))

        # Borda
        pygame.draw.ellipse(surface, self.border_color, outer, 1)