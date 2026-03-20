# src/game/entities/boost.py
import random
import pygame


# Cores e durações por tipo
_TIPOS = {
    "velocidade": {
        "cor":       (255, 200, 40),
        "cor_borda": (180, 140, 20),
        "cor_brilho":(255, 230, 120),
        "duracao":   90,
    },
    "imunidade": {
        "cor":       (60,  180, 255),
        "cor_borda": (30,  110, 180),
        "cor_brilho":(140, 220, 255),
        "duracao":   60,
    },
}


class Boost:
    """
    Item colecionavel no mapa (velocidade ou imunidade).
    Visual: diamante com brilho, distinto da comida redonda.
    """

    def __init__(self, tipo: str, area_rect, block_size):
        if tipo not in _TIPOS:
            raise ValueError(f"Tipo de boost desconhecido: '{tipo}'. Use: {list(_TIPOS)}")

        self.tipo     = tipo
        self.area     = area_rect
        self.block    = block_size
        self.duracao  = _TIPOS[tipo]["duracao"]

        self._cor       = _TIPOS[tipo]["cor"]
        self._cor_borda = _TIPOS[tipo]["cor_borda"]
        self._cor_brilho= _TIPOS[tipo]["cor_brilho"]

        self.pos = None  # (x_px, y_px) — definido pelo spawn

    # ── Posicionamento ────────────────────────────────────────────────────────
    def spawn(self, occupied_positions, obstaculos_pixels=None):
        """Coloca o boost numa posição aleatória livre da grelha."""
        if obstaculos_pixels is None:
            obstaculos_pixels = set()

        x0, y0, w, h = self.area
        cols = w // self.block
        rows = h // self.block

        tentativas = 0
        while True:
            x = x0 + random.randint(0, cols - 1) * self.block
            y = y0 + random.randint(0, rows - 1) * self.block
            if (x, y) not in occupied_positions and (x, y) not in obstaculos_pixels:
                self.pos = (x, y)
                return
            tentativas += 1
            if tentativas > 500:
                self.pos = (x, y)
                return

    # ── Desenho ───────────────────────────────────────────────────────────────
    def draw(self, surface):
        if self.pos is None:
            return

        x, y = self.pos
        b    = self.block
        m    = max(2, b // 6)
        cx   = x + b // 2
        cy   = y + b // 2
        r    = b // 2 - m  # raio do diamante

        # Diamante (4 pontos: cima, direita, baixo, esquerda)
        pontos = [
            (cx,     cy - r),
            (cx + r, cy    ),
            (cx,     cy + r),
            (cx - r, cy    ),
        ]
        pygame.draw.polygon(surface, self._cor, pontos)
        pygame.draw.polygon(surface, self._cor_borda, pontos, 1)

        # Brilho no canto superior
        br = max(1, r // 3)
        pygame.draw.polygon(surface, self._cor_brilho, [
            (cx,      cy - r    ),
            (cx + br, cy - r + br),
            (cx,      cy - r + br * 2),
            (cx - br, cy - r + br),
        ])
