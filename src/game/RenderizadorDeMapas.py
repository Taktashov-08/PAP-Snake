# src/game/map_renderer.py
"""
Renderizador de mapas — estilo dark UI clean.
Paredes com efeito 3D discreto: highlight em cima/esquerda, sombra em baixo/direita.
"""

import pygame
import game.config as cfg


class MapRenderer:
    """
    Renderiza obstáculos com visual moderno.
    Usa cache — só reconstrói se o mapa mudar.
    """

    def __init__(self, mapa, block_size=None):
        self.mapa      = mapa
        self.block     = block_size or mapa.block
        self._surface  = None
        self._last_key = None

    def _cache_key(self):
        return (id(self.mapa), len(self.mapa.obstaculos), self.block)

    def _rebuild(self):
        key = self._cache_key()
        if key == self._last_key:
            return
        self._last_key = key

        obst_set = set(self.mapa.obstaculos)
        w = self.mapa.cols * self.block
        h = self.mapa.rows * self.block

        self._surface = pygame.Surface((w, h), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 0))

        for (bx, by) in self.mapa.obstaculos:
            self._draw_block(self._surface, bx, by, obst_set)

    def draw(self, target, offset=(0, 0)):
        self._rebuild()
        target.blit(self._surface, offset)

    def invalidate(self):
        self._last_key = None

    # ── Desenho de um bloco ───────────────────────────────────────────────────
    def _draw_block(self, surf, bx, by, obst):
        b  = self.block
        x  = bx * b
        y  = by * b

        cols = self.mapa.cols
        rows = self.mapa.rows

        is_outer = (bx == 0 or bx == cols - 1 or by == 0 or by == rows - 1)

        # Vizinhos
        top    = (bx,     by - 1) in obst
        bottom = (bx,     by + 1) in obst
        left   = (bx - 1, by    ) in obst
        right  = (bx + 1, by    ) in obst
        tl     = (bx - 1, by - 1) in obst
        tr     = (bx + 1, by - 1) in obst
        bl     = (bx - 1, by + 1) in obst
        br     = (bx + 1, by + 1) in obst

        face = cfg.WALL_OUTER_FACE if is_outer else cfg.WALL_FACE
        hi   = cfg.WALL_OUTER_HI   if is_outer else cfg.WALL_HIGHLIGHT

        # 1. Face base
        pygame.draw.rect(surf, face, (x, y, b, b))

        # 2. Brilho interno — rectângulo 1px menor em cada lado
        pygame.draw.rect(surf, cfg.WALL_INNER,
                         (x + 1, y + 1, b - 2, b - 2))

        thick = max(1, b // 5)

        # 3. Highlight (topo e esquerda) — só nas faces expostas
        if not top:
            pygame.draw.rect(surf, hi, (x, y, b, thick))
        if not left:
            pygame.draw.rect(surf, hi, (x, y, thick, b))

        # 4. Sombra (baixo e direita) — só nas faces expostas
        if not bottom:
            pygame.draw.rect(surf, cfg.WALL_SHADOW,
                             (x, y + b - thick, b, thick))
        if not right:
            pygame.draw.rect(surf, cfg.WALL_SHADOW,
                             (x + b - thick, y, thick, b))

        # 5. Canto superior-esquerdo brilhante (onde luz de topo + esquerda se encontram)
        cs = max(2, b // 4)
        if not top and not left:
            pygame.draw.rect(surf, cfg.WALL_CORNER_HI, (x, y, cs, cs))

        # 6. Cantos interiores côncavos (suaviza encontro de paredes)
        ic = max(1, b // 6)
        if top and left and not tl:
            pygame.draw.rect(surf, cfg.WALL_CORNER_HI, (x, y, ic, ic))
        if top and right and not tr:
            pygame.draw.rect(surf, cfg.WALL_CORNER_HI, (x + b - ic, y, ic, ic))
        if bottom and left and not bl:
            pygame.draw.rect(surf, cfg.WALL_CORNER_HI, (x, y + b - ic, ic, ic))
        if bottom and right and not br:
            pygame.draw.rect(surf, cfg.WALL_CORNER_HI, (x + b - ic, y + b - ic, ic, ic))