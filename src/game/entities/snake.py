# src/game/entities/snake.py
"""
Cobra com visual dark-clean aprimorado:
  - Rasto (ghost trail) de 6 posições atrás da cabeça
  - Cabeça com highlight e borda de acento
  - Corpo com fade gradual
  - Flash de morte antes de desaparecer
  - Olho que segue a direção
"""
from __future__ import annotations

from collections import deque
from typing import Tuple

import pygame

from game.config import BLOCK_SIZE, SNAKE1_HEAD, SNAKE1_BODY, SNAKE1_BORDER

# Número de posições de rasto guardadas
_TRAIL_LEN: int = 6
# Número de ticks de flash ao morrer (alternância visível/invisível)
_DEATH_FLASH_TICKS: int = 6


class Snake:
    """
    Cobra do jogo.

    Parâmetros de cor:
        color        — cor base do corpo
        head_color   — cor da cabeça (por omissão: versão mais clara de `color`)
        border_color — cor da borda de cada segmento
    """

    def __init__(self, start_pos: Tuple[int, int] = (100, 100),
                 block_size: int = BLOCK_SIZE,
                 color=None, head_color=None, border_color=None) -> None:
        self.block        = block_size
        self.head_color   = head_color   or (_brighten(color, 35) if color else SNAKE1_HEAD)
        self.body_color   = color        or SNAKE1_BODY
        self.border_color = border_color or SNAKE1_BORDER

        self.segments:  list             = [start_pos]
        self.direction: Tuple[int, int]  = (1, 0)
        self.grow_next: int              = 0

        # Rasto visual — últimas posições da cabeça
        self._trail: deque = deque(maxlen=_TRAIL_LEN)

        # Estado de flash de morte
        self._dying:       bool = False
        self._flash_tick:  int  = 0
        self._flash_state: bool = True    # True = visível, False = oculto

    # ── Lógica ────────────────────────────────────────────────────────────────

    def set_direction(self, dx: int, dy: int) -> None:
        """Muda de direção; ignora a inversão direta (180°)."""
        if len(self.segments) > 1:
            hx, hy = self.segments[0]
            if (hx + dx * self.block, hy + dy * self.block) == self.segments[1]:
                return
        self.direction = (dx, dy)

    def update(self) -> None:
        """Avança a cobra um bloco; regista a posição anterior no rasto."""
        self._trail.appendleft(self.segments[0])
        hx, hy = self.segments[0]
        dx, dy = self.direction
        self.segments.insert(0, (hx + dx * self.block, hy + dy * self.block))
        if self.grow_next > 0:
            self.grow_next -= 1
        else:
            self.segments.pop()

    def grow(self, amount: int = 1) -> None:
        """Agenda crescimento para os próximos `amount` ticks."""
        self.grow_next += amount

    def collides_self(self) -> bool:
        return self.segments[0] in self.segments[1:]

    def head_pos(self) -> Tuple[int, int]:
        return self.segments[0]

    def set_head_pos(self, pos: Tuple[int, int]) -> None:
        self.segments[0] = pos

    # ── Flash de morte ────────────────────────────────────────────────────────

    def start_death_flash(self) -> None:
        """Inicia a animação de flash; chamado pelo modo quando a cobra morre."""
        self._dying      = True
        self._flash_tick = 0
        self._flash_state = True

    def tick_death_flash(self) -> bool:
        """
        Avança o flash de morte.
        Devolve True quando a animação terminar.
        """
        if not self._dying:
            return False
        self._flash_tick += 1
        self._flash_state = (self._flash_tick % 2 == 0)
        return self._flash_tick >= _DEATH_FLASH_TICKS

    # ── Desenho ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        """Desenha rasto → corpo → cabeça (esconde durante flash ímpar)."""
        if self._dying and not self._flash_state:
            return   # frame de flash "oculto"
        self._draw_trail(surface)
        self._draw_body(surface)
        self._draw_head(surface)

    def _draw_trail(self, surface: pygame.Surface) -> None:
        """
        Rasto de segmentos fantasma que desvanecem rapidamente.
        Usa escurecimento de cor directo (sem Surface alpha) — muito rápido.
        """
        b = self.block
        n = len(self._trail)
        if n == 0:
            return
        for i, (tx, ty) in enumerate(self._trail):
            t    = 1.0 - (i + 1) / (n + 1)   # 1.0 → perto da cabeça, ~0 → longe
            size = max(2, int(b * t * 0.75))
            cx   = tx + b // 2
            cy   = ty + b // 2
            col  = (int(self.head_color[0] * t * 0.55),
                    int(self.head_color[1] * t * 0.55),
                    int(self.head_color[2] * t * 0.55))
            pygame.draw.rect(
                surface, col,
                pygame.Rect(cx - size // 2, cy - size // 2, size, size),
                border_radius=max(1, size // 3),
            )

    def _draw_body(self, surface: pygame.Surface) -> None:
        """Corpo com fade do segmento 1 em diante."""
        b     = self.block
        pad   = max(1, b // 8)
        total = max(len(self.segments), 1)
        for i, (x, y) in enumerate(self.segments[1:], start=1):
            t   = 1.0 - (i / total) * 0.45
            col = tuple(max(0, int(c * t)) for c in self.body_color)
            inner = pygame.Rect(x + pad, y + pad, b - pad * 2, b - pad * 2)
            pygame.draw.rect(surface, col, inner, border_radius=2)
            pygame.draw.rect(surface, self.border_color,
                             pygame.Rect(x, y, b, b), 1)

    def _draw_head(self, surface: pygame.Surface) -> None:
        """Cabeça com highlight superior e olho orientado."""
        b    = self.block
        pad  = max(1, b // 8)
        x, y = self.segments[0]

        inner = pygame.Rect(x + pad, y + pad, b - pad * 2, b - pad * 2)
        # Base da cabeça
        pygame.draw.rect(surface, self.head_color, inner, border_radius=4)
        # Highlight no terço superior
        hi_col  = _brighten(self.head_color, 28)
        hi_rect = pygame.Rect(inner.x, inner.y, inner.w,
                               max(2, inner.h // 3))
        pygame.draw.rect(surface, hi_col, hi_rect, border_radius=4)
        # Borda exterior
        pygame.draw.rect(surface, self.border_color,
                         pygame.Rect(x, y, b, b), 1)
        # Olho
        _draw_eye(surface, x, y, b, self.direction)


# ── Utilitários de módulo ──────────────────────────────────────────────────────

def _brighten(color: tuple, amt: int) -> tuple:
    return tuple(min(c + amt, 255) for c in color)


def _draw_eye(surface: pygame.Surface, x: int, y: int,
              b: int, direction: Tuple[int, int]) -> None:
    """Ponto brilhante que representa o olho, na direcção de movimento."""
    dx, dy = direction
    cx, cy = x + b // 2, y + b // 2
    off = b // 3
    ex, ey = cx + dx * off, cy + dy * off
    r = max(1, b // 7)
    pygame.draw.rect(surface, (200, 232, 212),
                     pygame.Rect(ex - r, ey - r, r * 2, r * 2),
                     border_radius=1)