# src/game/entities/snake.py
import pygame
from game.config import BLOCK_SIZE, SNAKE1_HEAD, SNAKE1_BODY, SNAKE1_BORDER


class Snake:
    """Cobra com visual dark-clean: fade no corpo, olho discreto na cabeca."""

    def __init__(self, start_pos=(100, 100), block_size=BLOCK_SIZE,
                 color=None, head_color=None, border_color=None):
        self.block        = block_size
        self.head_color   = head_color   or (color and _brighten(color, 35)) or SNAKE1_HEAD
        self.body_color   = color        or SNAKE1_BODY
        self.border_color = border_color or SNAKE1_BORDER
        self.segments     = [start_pos]
        self.direction    = (1, 0)
        self.grow_next    = 0

    def set_direction(self, dx, dy):
        if len(self.segments) > 1:
            hx, hy = self.segments[0]
            if (hx + dx * self.block, hy + dy * self.block) == self.segments[1]:
                return
        self.direction = (dx, dy)

    def update(self):
        hx, hy = self.segments[0]
        dx, dy = self.direction
        self.segments.insert(0, (hx + dx * self.block, hy + dy * self.block))
        if self.grow_next > 0:
            self.grow_next -= 1
        else:
            self.segments.pop()

    def grow(self, amount=1):
        self.grow_next += amount

    def collides_self(self):
        return self.segments[0] in self.segments[1:]

    def collides_rect(self, rect):
        hx, hy = self.segments[0]
        x, y, w, h = rect
        return not (x <= hx < x + w and y <= hy < y + h)

    def head_pos(self):
        return self.segments[0]

    def set_head_pos(self, pos):
        self.segments[0] = pos

    def draw(self, surface):
        total = max(len(self.segments), 1)
        b     = self.block
        pad   = max(1, b // 8)
        for i, (x, y) in enumerate(self.segments):
            inner = pygame.Rect(x + pad, y + pad, b - pad*2, b - pad*2)
            if i == 0:
                pygame.draw.rect(surface, self.head_color, inner, border_radius=3)
                _draw_eye(surface, x, y, b, self.direction)
            else:
                t   = 1.0 - (i / total) * 0.40
                col = tuple(max(0, int(c * t)) for c in self.body_color)
                pygame.draw.rect(surface, col, inner, border_radius=2)
            pygame.draw.rect(surface, self.border_color, pygame.Rect(x, y, b, b), 1)


def _brighten(color, amt):
    return tuple(min(c + amt, 255) for c in color)

def _draw_eye(surface, x, y, b, direction):
    dx, dy = direction
    cx, cy = x + b // 2, y + b // 2
    offset = b // 3
    ex = cx + dx * offset
    ey = cy + dy * offset
    r  = max(1, b // 7)
    pygame.draw.rect(surface, (200, 230, 210),
                     pygame.Rect(ex - r, ey - r, r*2, r*2), border_radius=1)
