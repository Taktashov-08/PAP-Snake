import random
import pygame

class Food:
    def __init__(self, area_rect, block_size, color=(200,0,0)):
        """
        area_rect: (x,y,width,height) área jogável onde spawna a comida
        """
        self.area = area_rect
        self.block = block_size
        self.color = color
        self.pos = None
        self.spawn([])

    def spawn(self, occupied_positions):
        x0, y0, w, h = self.area
        cols = w // self.block
        rows = h // self.block
        attempts = 0
        while True:
            gx = random.randint(0, cols - 1)
            gy = random.randint(0, rows - 1)
            x = x0 + gx * self.block
            y = y0 + gy * self.block
            if (x, y) not in occupied_positions:
                self.pos = (x, y)
                return
            attempts += 1
            if attempts > 500:
                # fallback: place anywhere ignoring occupied
                self.pos = (x, y)
                return

    def draw(self, surface):
        if self.pos is None:
            return
        r = pygame.Rect(self.pos[0], self.pos[1], self.block, self.block)
        pygame.draw.ellipse(surface, self.color, r)
        pygame.draw.rect(surface, (0,0,0), r, 1)
