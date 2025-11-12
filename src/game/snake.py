import pygame
from game.config import BLOCK_SIZE

class Snake:
    """
    Versão Pygame da Snake.
    Mantém segmentos como lista de (x,y) e desenha retângulos.
    """
    def __init__(self, start_pos=(100, 100), block_size=BLOCK_SIZE, color=(0,200,0)):
        self.block = block_size
        self.color = color
        self.segments = [start_pos]  # head is index 0
        self.direction = (1, 0)  # right
        self.grow_next = 0

    def set_direction(self, dx, dy):
        # evita inverter 180 graus
        if len(self.segments) > 1:
            hx, hy = self.segments[0]
            nx = hx + dx * self.block
            ny = hy + dy * self.block
            # se nova cabeca igual ao 2º segmento, ignora (inversão)
            if (nx, ny) == self.segments[1]:
                return
        self.direction = (dx, dy)

    def update(self):
        # move head
        hx, hy = self.segments[0]
        dx, dy = self.direction
        new_head = (hx + dx * self.block, hy + dy * self.block)
        self.segments.insert(0, new_head)
        if self.grow_next > 0:
            self.grow_next -= 1
        else:
            self.segments.pop()

    def grow(self, amount=1):
        self.grow_next += amount

    def collides_self(self):
        return self.segments[0] in self.segments[1:]

    def collides_rect(self, rect):
        # rect: (x,y,w,h) check if head outside rect -> used for wall collision
        hx, hy = self.segments[0]
        x, y, w, h = rect
        return not (x <= hx < x + w and y <= hy < y + h)

    def head_pos(self):
        return self.segments[0]
    
    def set_head_pos(self, pos):
        """Atualiza manualmente a posição da cabeça (usado em mapas borderless)."""
        self.segments[0] = pos


    def draw(self, surface):
        for i, (x, y) in enumerate(self.segments):
            r = pygame.Rect(x, y, self.block, self.block)
            # head slightly brighter
            if i == 0:
                pygame.draw.rect(surface, (min(self.color[0]+30,255), min(self.color[1]+30,255), min(self.color[2]+30,255)), r)
            else:
                pygame.draw.rect(surface, self.color, r)
            pygame.draw.rect(surface, (20,20,20), r, 1)  # border
