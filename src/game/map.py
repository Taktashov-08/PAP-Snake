# src/game/map.py
import os
import random
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE

class Mapas:
    """
    Classe para carregar mapas de ficheiro .txt ou gerar por tipo.
    - Guarda obstáculos como lista de (bx, by) em blocos.
    - self.block = tamanho do bloco em px (p.ex. 20)
    - verificar_colisao(pos_px) recebe coordenadas em pixels (x,y)
      e devolve:
         - True  -> colisão fatal (Game Over)
         - (x_px,y_px) -> nova posição (teleporte em mapas borderless)
         - False -> nada (sem colisão; pos fica igual)
    """
    def __init__(self, path_or_tipo, block_size=None, auto_scale=True):
        self.tipo = path_or_tipo      # pode ser int (tipo) ou path string
        self.obstaculos = []          # lista de (bx, by) em blocos
        self.spawn_snake_block = None
        self.spawn_food_block = None

        # init grid dims (cols x rows) — defaults para 45x30 se não lido do ficheiro
        self.cols = SCREEN_WIDTH // (block_size or BLOCK_SIZE)
        self.rows = SCREEN_HEIGHT // (block_size or BLOCK_SIZE)

        # block size em px (pode ser ajustado por regra de 3)
        self.block = block_size

        if isinstance(path_or_tipo, str) and os.path.exists(path_or_tipo):
            self._load_from_file(path_or_tipo)
        else:
            # se for int ou não existe ficheiro, gerar por tipo (mantém compatibilidade)
            self._generate_by_type(path_or_tipo)

        # se block não definido, calcula pelo ecrã (auto-scale)
        if self.block is None and auto_scale and self.cols > 0 and self.rows > 0:
            bw = SCREEN_WIDTH // self.cols
            bh = SCREEN_HEIGHT // self.rows
            self.block = min(bw, bh) or BLOCK_SIZE

        if self.block is None:
            self.block = BLOCK_SIZE

    # ------------------ loader .txt ------------------
    def _load_from_file(self, filepath):
        """
        Espera ficheiro com linhas, símbolos:
         '#' -> obstáculo
         '.' -> livre
         'S' -> spawn da cobra (opcional)
         'F' -> spawn comida (opcional)
        """
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = [line.rstrip("\n") for line in f if line.rstrip("\n") != "" and not line.lstrip().startswith(";")]

        if not raw_lines:
            raise ValueError("Ficheiro de mapa vazio: " + filepath)

        maxw = max(len(l) for l in raw_lines)
        grid = [list(l.ljust(maxw, ".")) for l in raw_lines]

        self.rows = len(grid)
        self.cols = maxw

        self.obstaculos = []
        self.spawn_snake_block = None
        self.spawn_food_block = None

        for gy, row in enumerate(grid):
            for gx, ch in enumerate(row):
                if ch == "#":
                    self.obstaculos.append((gx, gy))
                elif ch == "S":
                    self.spawn_snake_block = (gx, gy)
                elif ch == "F":
                    self.spawn_food_block = (gx, gy)
        # marca tipo como 'file' para distinguir
        self.tipo = "file:" + os.path.basename(filepath)

    # ------------------ generator simple (compatibilidade) ------------------
    def _generate_by_type(self, tipo):
        """
        Se tipo for um int (1,2,3) gera obstaculos programaticamente.
        Mantém implementações anteriores se necessário.
        """
        t = tipo if isinstance(tipo, int) else 1
        self.obstaculos = []
        # por defeito: grid 45x30
        self.cols = SCREEN_WIDTH // (self.block or BLOCK_SIZE)
        self.rows = SCREEN_HEIGHT // (self.block or BLOCK_SIZE)
        if t == 1:
            # vazio
            pass
        elif t == 2:
            # exemplo simples (pode ser substituído)
            for x in range(5, 15):
                self.obstaculos.append((x, 8))
        elif t == 3:
            # bordas
            for x in range(self.cols):
                self.obstaculos.append((x, 0))
                self.obstaculos.append((x, self.rows - 1))
            for y in range(self.rows):
                self.obstaculos.append((0, y))
                self.obstaculos.append((self.cols - 1, y))

        # spawn center por defeito
        self.spawn_snake_block = (self.cols // 2, self.rows // 2)

    # ------------------ utilitários ------------------
    def obstaculos_pixels(self):
        """Retorna set de (x_px, y_px) das posiçoes dos obstáculos (top-left de cada bloco)."""
        return {(bx * self.block, by * self.block) for (bx, by) in self.obstaculos}

    def spawn_seguro(self, ocupados_pixels):
        """
        Devolve posição segura em pixels (x_px, y_px) para spawn.
        ocupados_pixels: conjunto de posições em pixels já ocupadas (cobra)
        Estratégia: usar S se definido; senão centro; senão procurar célula livre.
        """
        def block_to_px(b):
            return (b[0] * self.block, b[1] * self.block)

        obst_px = self.obstaculos_pixels()

        # 1) spawn definido no ficheiro
        if self.spawn_snake_block:
            px = block_to_px(self.spawn_snake_block)
            if px not in ocupados_pixels and px not in obst_px:
                return px

        # 2) centro
        centro_b = (self.cols // 2, self.rows // 2)
        centro_px = block_to_px(centro_b)
        if centro_px not in ocupados_pixels and centro_px not in obst_px:
            return centro_px

        # 3) procurar por todas células livres
        livres = []
        for gx in range(self.cols):
            for gy in range(self.rows):
                ppx = (gx * self.block, gy * self.block)
                if ppx not in ocupados_pixels and ppx not in obst_px:
                    livres.append(ppx)

        if livres:
            return random.choice(livres)

        # fallback
        return (0, 0)

    # ------------------ colisões ------------------
    def verificar_colisao(self, pos_px):
        """
        pos_px: (x_px, y_px) posição actual da cabeça (em pixels, top-left)
        Retorna:
          - True => colisão fatal
          - (x_px, y_px) => nova posição (teleporte aplicado)
          - False => sem colisão (manter posição)
        """
        x, y = pos_px
        bx = x // self.block
        by = y // self.block

        # se for mapa com bordas explícitas (detecta se há bloqueios nas bordas)
        # Heurística: se existem obstáculos nas bordas completas, consideramos 'arena' (bordas sólidas)
        left_border = (0, 0) in [(0,0)]  # dummy para leitura; vamos verificar realmente abaixo

        # verifica colisão com obstáculos simples
        if (bx, by) in self.obstaculos:
            return True

        # Detectar se este mapa tem bordas sólidas: se existirem obstáculos cobrindo toda a linha y=0 e y=rows-1 e col x=0 e x=cols-1
        top_full = all(((x,0) in self.obstaculos) for x in range(self.cols))
        bottom_full = all(((x,self.rows-1) in self.obstaculos) for x in range(self.cols))
        left_full = all(((0,y) in self.obstaculos) for y in range(self.rows))
        right_full = all(((self.cols-1,y) in self.obstaculos) for y in range(self.rows))

        has_full_borders = top_full and bottom_full and left_full and right_full

        if has_full_borders:
            # colisão se fora dos limites ou se em obstáculo (já verificado)
            if bx < 0 or bx >= self.cols or by < 0 or by >= self.rows:
                return True
            # se chegou aqui, não é obstáculo e não saiu -> sem colisão
            return False
        else:
            # borderless: aplicar teleporte se saiu do ecrã
            cols = self.cols
            rows = self.rows
            changed = False
            if bx < 0:
                bx = cols - 1
                changed = True
            elif bx >= cols:
                bx = 0
                changed = True
            if by < 0:
                by = rows - 1
                changed = True
            elif by >= rows:
                by = 0
                changed = True

            # após teleporte, verificar se a nova célula é obstáculo
            if (bx, by) in self.obstaculos:
                return True

            if changed:
                return (bx * self.block, by * self.block)

            # sem teleporte e sem colisão
            return False
