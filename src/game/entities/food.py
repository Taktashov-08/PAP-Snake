# src/game/entities/food.py
"""
Comida com:
  - Pulso sinusoidal do raio (±12 %)
  - Sparkles orbitais (5 pontos que giram e fazem twinkle)

update(dt) deve ser chamado a ~60 fps pelo modo de jogo (visual_update).
"""
from __future__ import annotations

import math
import random
from typing import Optional, Tuple

import pygame

from game.config import FOOD_COLOR, FOOD_BORDER, FOOD_HIGHLIGHT

# ── Constantes visuais ────────────────────────────────────────────────────────
_PULSE_SPEED:   float = 3.2   # ciclos de pulso por segundo
_SPARKLE_COUNT: int   = 5     # número de pontos orbitais
_SPARKLE_SPEED: float = 1.6   # rotações por segundo (rad/s × 2π)
_SPARKLE_ORBIT: float = 0.90  # raio da órbita como fracção de (block/2)
_SPARKLE_ALPHA: float = 0.70  # brilho máximo dos sparkles (0–1)


class Food:
    """
    Item de comida renderizado como elipse pulsante com sparkles orbitais.

    Parâmetros:
        area_rect    — (x, y, w, h) da área de spawn
        block_size   — tamanho de um bloco em píxeis
        color        — cor principal (por omissão: FOOD_COLOR)
        border_color — cor da borda (por omissão: FOOD_BORDER)
    """

    def __init__(self, area_rect, block_size: int,
                 color=None, border_color=None) -> None:
        self.area         = area_rect
        self.block        = block_size
        self.color        = color        or FOOD_COLOR
        self.border_color = border_color or FOOD_BORDER
        self.pos: Optional[Tuple[int, int]] = None

        # Fase de animação — aleatória por instância para variedade visual
        # quando há vários itens de comida em simultâneo
        self._phase: float = random.uniform(0.0, math.tau)
        self.spawn([])

    # ── Posicionamento ────────────────────────────────────────────────────────

    def spawn(self, occupied_positions, obstaculos_pixels=None) -> None:
        """Coloca a comida num bloco livre da grelha."""
        if obstaculos_pixels is None:
            obstaculos_pixels = []
        x0, y0, w, h = self.area
        cols = max(1, w // self.block)
        rows = max(1, h // self.block)
        last = None
        for _ in range(500):
            x    = x0 + random.randint(0, cols - 1) * self.block
            y    = y0 + random.randint(0, rows - 1) * self.block
            last = (x, y)
            if (x, y) not in occupied_positions and (x, y) not in obstaculos_pixels:
                self.pos    = (x, y)
                self._phase = random.uniform(0.0, math.tau)
                return
        self.pos = last   # fallback de segurança

    # ── Animação ──────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """
        Avança a fase de animação do pulso e dos sparkles.
        Chamar a ~60 fps para máxima suavidade.
        """
        self._phase += _SPARKLE_SPEED * math.tau * dt

    # ── Desenho ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if self.pos is None:
            return

        x, y = self.pos
        b    = self.block
        m    = max(1, b // 6)

        # ── Pulso do raio ─────────────────────────────────────────────────
        pulse  = 1.0 + 0.12 * math.sin(self._phase * (_PULSE_SPEED / _SPARKLE_SPEED))
        base_r = max(2.0, b / 2.0 - m)
        r      = max(2, int(base_r * pulse))
        cx, cy = x + b // 2, y + b // 2

        # ── Corpo principal ───────────────────────────────────────────────
        outer = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.ellipse(surface, self.color, outer)

        # Brilho no canto superior esquerdo
        hs = max(2, r // 2)
        pygame.draw.ellipse(surface, FOOD_HIGHLIGHT,
                            pygame.Rect(cx - r // 4 - hs // 2,
                                        cy - r // 4 - hs // 2, hs, hs))
        pygame.draw.ellipse(surface, self.border_color, outer, 1)

        # ── Sparkles orbitais ─────────────────────────────────────────────
        orbit_r = max(3, int(b * _SPARKLE_ORBIT * 0.5))
        for i in range(_SPARKLE_COUNT):
            # Ângulo base + offset por sparkle
            angle  = self._phase + (math.tau / _SPARKLE_COUNT) * i
            sx     = cx + int(math.cos(angle) * orbit_r)
            sy     = cy + int(math.sin(angle) * orbit_r)

            # Twinkle: brilho varia sinusoidalmente por sparkle
            twinkle = (math.sin(angle * 2.0 + self._phase * 0.7) + 1.0) * 0.5
            alpha   = _SPARKLE_ALPHA * (0.35 + 0.65 * twinkle)
            col     = tuple(max(0, min(255, int(c * alpha))) for c in self.color)
            size    = max(1, int(2.5 * (0.5 + 0.5 * twinkle)))

            pygame.draw.circle(surface, col, (sx, sy), size)