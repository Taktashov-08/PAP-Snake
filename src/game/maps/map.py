# src/game/maps/map.py
"""
Carregamento e gestao de mapas.
Otimizacoes vs versao original:
  - _obst_set: set() para lookup O(1) em vez de O(n) na lista
  - has_full_borders: propriedade com cache — calcula uma vez, nao por frame
  - obstaculos_pixels(): cache invalidado ao recarregar obstaculos
"""
import os
import random
import game.config as cfg


class Mapas:
    def __init__(self, path_or_tipo=1, block_size=None, auto_scale=True):
        self.tipo       = path_or_tipo
        self.source     = path_or_tipo
        self.auto_scale = auto_scale
        self.block      = block_size or cfg.BLOCK_SIZE
        self.cols       = max(1, cfg.SCREEN_WIDTH  // max(1, self.block))
        self.rows       = max(1, cfg.SCREEN_HEIGHT // max(1, self.block))

        self.obstaculos = []
        self._obst_set           = set()   # lookup O(1)
        self._has_full_borders   = None    # cache
        self._obst_pixels_cache  = None    # cache de pixels

        self.spawn_snake_block   = None
        self.spawn_snake2_block  = None
        self.spawn_food_block    = None

        if isinstance(path_or_tipo, str) and os.path.exists(path_or_tipo):
            self.filepath = path_or_tipo
            self._load_from_file(self.filepath)
        else:
            self.filepath = None
            self._generate_by_type(path_or_tipo if isinstance(path_or_tipo, int) else 1)

        if self.auto_scale:
            self.update_grid()

    # ── Cache ─────────────────────────────────────────────────────────────────
    def _rebuild_cache(self):
        """Reconstroi todos os caches apos alterar self.obstaculos."""
        self._obst_set          = set(self.obstaculos)
        self._has_full_borders  = None
        self._obst_pixels_cache = None

    @property
    def has_full_borders(self):
        """Cache: True se o mapa tem bordas solidas completas em todos os lados."""
        if self._has_full_borders is None:
            s = self._obst_set
            top    = all((x, 0)           in s for x in range(self.cols))
            bottom = all((x, self.rows-1) in s for x in range(self.cols))
            left   = all((0, y)           in s for y in range(self.rows))
            right  = all((self.cols-1, y) in s for y in range(self.rows))
            self._has_full_borders = top and bottom and left and right
        return self._has_full_borders

    # ── Grid / reload helpers ─────────────────────────────────────────────────
    def update_grid(self, block_size=None):
        if block_size:
            self.block = block_size
        self.block = max(1, int(self.block))
        self.cols  = max(1, cfg.SCREEN_WIDTH  // self.block)
        self.rows  = max(1, cfg.SCREEN_HEIGHT // self.block)
        self.gerar_obstaculos()

    def gerar_obstaculos(self):
        if self.filepath:
            self._load_from_file(self.filepath)
        else:
            tipo = self.source if isinstance(self.source, int) else 1
            self._generate_by_type(tipo)

        if self.spawn_snake_block is None:
            self.spawn_snake_block = (self.cols // 2, self.rows // 2)
        if self.spawn_snake2_block is None:
            self.spawn_snake2_block = (max(1, self.cols // 2 + 5), self.rows // 2)
        if self.spawn_food_block is None:
            self.spawn_food_block = (max(1, self.cols // 2 - 1), max(1, self.rows // 2))

    # ── Loader .txt ───────────────────────────────────────────────────────────
    def _load_from_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = [
                line.rstrip("\n")
                for line in f
                if line.rstrip("\n") != "" and not line.lstrip().startswith(";")
            ]
        if not raw_lines:
            raise ValueError("Ficheiro de mapa vazio: " + filepath)

        maxw = max(len(l) for l in raw_lines)
        grid = [list(l.ljust(maxw, ".")) for l in raw_lines]

        self.rows = len(grid)
        self.cols = maxw
        self.obstaculos          = []
        self.spawn_snake_block   = None
        self.spawn_snake2_block  = None
        self.spawn_food_block    = None

        for gy, row in enumerate(grid):
            for gx, ch in enumerate(row):
                if   ch == "#": self.obstaculos.append((gx, gy))
                elif ch == "S": self.spawn_snake_block  = (gx, gy)
                elif ch == "P": self.spawn_snake2_block = (gx, gy)
                elif ch == "F": self.spawn_food_block   = (gx, gy)

        self.source   = filepath
        self.filepath = filepath
        self._rebuild_cache()

    # ── Generator por tipo ────────────────────────────────────────────────────
    def _generate_by_type(self, tipo):
        t = tipo if isinstance(tipo, int) else 1
        self.obstaculos = []
        self.cols = max(1, cfg.SCREEN_WIDTH  // self.block)
        self.rows = max(1, cfg.SCREEN_HEIGHT // self.block)

        if t == 2:
            ranges = [
                (4, 16, 7),
                (max(0, self.cols-6), self.cols-1, 4),
                (max(0, self.cols-6), self.cols-1, 10),
            ]
            for start, end, y in ranges:
                for x in range(start, min(end, self.cols-1)):
                    self.obstaculos.append((x, min(y, self.rows-1)))
            for y in range(11, min(self.rows-1, 18)):
                if 8 < self.cols:
                    self.obstaculos.append((8, y))
        elif t == 3:
            for x in range(self.cols):
                self.obstaculos.append((x, 0))
                self.obstaculos.append((x, self.rows - 1))
            for y in range(self.rows):
                self.obstaculos.append((0, y))
                self.obstaculos.append((self.cols - 1, y))
            midx, midy = self.cols // 2, self.rows // 2
            for x in range(max(1, midx - 6), min(self.cols-1, midx + 7)):
                self.obstaculos.append((x, midy))
            for y in range(max(1, midy - 6), min(self.rows-1, midy + 7)):
                self.obstaculos.append((midx, y))

        self.obstaculos = [
            (x, y) for x, y in dict.fromkeys(self.obstaculos)
            if 0 <= x < self.cols and 0 <= y < self.rows
        ]
        self.spawn_snake_block  = (self.cols // 4,     self.rows // 2)
        self.spawn_snake2_block = (self.cols * 3 // 4, self.rows // 2)
        self.spawn_food_block   = (self.cols // 2,     self.rows // 2)
        self._rebuild_cache()

    # ── Utilitarios ───────────────────────────────────────────────────────────
    def obstaculos_pixels(self):
        """Set (x_px, y_px) dos obstaculos — com cache."""
        if self._obst_pixels_cache is None:
            self._obst_pixels_cache = {
                (bx * self.block, by * self.block) for (bx, by) in self.obstaculos
            }
        return self._obst_pixels_cache

    def obter_spawn_player(self, player_num):
        def bpx(b):
            return (b[0] * self.block, b[1] * self.block) if b else (self.block, self.block)
        return bpx(self.spawn_snake_block if player_num == 1 else self.spawn_snake2_block)

    def spawn_seguro(self, ocupados_pixels, tries=2000):
        obst_px = self.obstaculos_pixels()
        livres = [
            (gx * self.block, gy * self.block)
            for gy in range(self.rows)
            for gx in range(self.cols)
            if (gx * self.block, gy * self.block) not in ocupados_pixels
            and (gx * self.block, gy * self.block) not in obst_px
        ]
        return random.choice(livres) if livres else (self.block, self.block)

    # ── Colisoes ──────────────────────────────────────────────────────────────
    def verificar_colisao(self, pos_px):
        """
        Retorna:
          True          -> colisao fatal (parede / obstaculo)
          (x_px, y_px)  -> nova posicao (teleporte)
          False         -> sem colisao
        """
        x, y = pos_px
        bx = x // self.block
        by = y // self.block

        # Colisao com obstaculo — O(1) gracas ao set
        if (bx, by) in self._obst_set:
            return True

        if self.has_full_borders:
            # Mapa com bordas: fora dos limites = morte (bordas ja sao obstaculos)
            if bx < 0 or bx >= self.cols or by < 0 or by >= self.rows:
                return True
            return False

        # Mapa sem bordas: teleporte
        cols, rows = self.cols, self.rows
        nbx, nby, changed = bx, by, False
        if   bx < 0:       nbx = cols - 1; changed = True
        elif bx >= cols:   nbx = 0;         changed = True
        if   by < 0:       nby = rows - 1; changed = True
        elif by >= rows:   nby = 0;         changed = True

        if (nbx, nby) in self._obst_set:
            return True
        if changed:
            return (nbx * self.block, nby * self.block)
        return False
