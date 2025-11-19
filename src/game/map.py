# src/game/map.py
import os
import random
import game.config as cfg
from game.config import BLOCK_SIZE

class Mapas:
    """
    Classe para carregar mapas de ficheiro .txt ou gerar por tipo.
    - Guarda obstáculos como lista de (bx, by) em blocos.
    - auto-adapta cols/rows/block quando cfg muda (usar gerar_obstaculos() / update_grid()).
    """

    def __init__(self, path_or_tipo=1, block_size=None, auto_scale=True):
        # path_or_tipo: int (1,2,3) ou path string para ficheiro
        self.source = path_or_tipo
        self.auto_scale = auto_scale

        # block em px: se passado, usa; se não, usa cfg.BLOCK_SIZE (actual quando chamada update_grid)
        self.block = block_size or cfg.BLOCK_SIZE

        # cols/rows iniciais (serão recalculados em update_grid)
        self.cols = max(1, cfg.SCREEN_WIDTH // max(1, self.block))
        self.rows = max(1, cfg.SCREEN_HEIGHT // max(1, self.block))

        # obstáculos em coordenadas de bloco (col, row)
        self.obstaculos = []
        self.spawn_snake_block = None
        self.spawn_food_block = None

        # carregar ou gerar
        if isinstance(path_or_tipo, str) and os.path.exists(path_or_tipo):
            # guarda o path para poder reload mais tarde
            self.filepath = path_or_tipo
            self._load_from_file(self.filepath)
        else:
            self.filepath = None
            # se for int ou invalido -> gerar
            self._generate_by_type(path_or_tipo if isinstance(path_or_tipo, int) else 1)

        # garantir que cols/rows/block condizem com cfg se auto_scale
        if self.auto_scale:
            self.update_grid()

    # ------------------ grid / reload helpers ------------------
    def update_grid(self, block_size=None):
        """
        Recalcula cols/rows e block com base no cfg (e opcional block_size).
        Deve ser chamado quando cfg.SCREEN_WIDTH/HEIGHT ou cfg.BLOCK_SIZE mudam.
        """
        if block_size:
            self.block = block_size
        else:
            # mantem self.block se foi passado antes, mas sincroniza com cfg se default
            self.block = self.block or cfg.BLOCK_SIZE

        # evitar zero
        self.block = max(1, int(self.block))

        self.cols = max(1, cfg.SCREEN_WIDTH // self.block)
        self.rows = max(1, cfg.SCREEN_HEIGHT // self.block)

        # após atualizar grid, regenerar obstáculos segundo a origem
        self.gerar_obstaculos()

    def gerar_obstaculos(self):
        """
        Reconstrói os obstáculos a partir da fonte original (ficheiro ou tipo).
        Mantém spawn_snake_block e spawn_food_block se presentes no ficheiro,
        caso contrário recalcula spawn padrão.
        """
        if self.filepath:
            # recarrega do ficheiro com nova escala de grid
            self._load_from_file(self.filepath)
        else:
            # gera novamente usando o tipo (self.source)
            tipo = self.source if isinstance(self.source, int) else 1
            self._generate_by_type(tipo)

        # garantir spawn default se não definido
        if self.spawn_snake_block is None:
            self.spawn_snake_block = (self.cols // 2, self.rows // 2)
        if self.spawn_food_block is None:
            # joga a spawn comida ao lado do centro
            self.spawn_food_block = (max(1, self.cols // 2 - 1), max(1, self.rows // 2))

    # ------------------ loader .txt ------------------
    def _load_from_file(self, filepath):
        """
        Carrega um mapa simples de texto:
         '#' -> obstáculo
         '.' -> livre
         'S' -> spawn da cobra (em blocos)
         'F' -> spawn comida (em blocos)
        O ficheiro é interpretado como grelha; cols/rows atualizam-se à dimensão do ficheiro.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = [line.rstrip("\n") for line in f if line.rstrip("\n") != "" and not line.lstrip().startswith(";")]

        if not raw_lines:
            raise ValueError("Ficheiro de mapa vazio: " + filepath)

        maxw = max(len(l) for l in raw_lines)
        grid = [list(l.ljust(maxw, ".")) for l in raw_lines]

        self.rows = len(grid)
        self.cols = maxw

        # recalcular block para caber (opcional) - aqui mantemos self.block
        # se quiseres forced-fit podes ativar lógica extra

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

        self.source = filepath  # marca a origem
        self.filepath = filepath

    # ------------------ generator simple (compatibilidade) ------------------
    def _generate_by_type(self, tipo):
        """
        Se tipo for um int (1,2,3) gera obstaculos programaticamente.
        Usa self.cols/self.rows atuais.
        """
        t = tipo if isinstance(tipo, int) else 1
        self.obstaculos = []

        # recalcula cols/rows se ainda não estiverem corretos
        self.cols = max(1, cfg.SCREEN_WIDTH // self.block)
        self.rows = max(1, cfg.SCREEN_HEIGHT // self.block)

        if t == 1:
            # vazio
            pass

        elif t == 2:
            # mapa com obstaculos "espalhados" (exemplo adaptável)
            # ajustado para nunca sair da grelha
            ranges = [
                (4, 16, 7),
                (max(0, self.cols-6), self.cols-1, 4),
                (max(0, self.cols-6), self.cols-1, 10),
            ]
            for start, end, y in ranges:
                for x in range(start, min(end, self.cols-1)):
                    self.obstaculos.append((x, min(y, self.rows-1)))

            # algumas colunas
            for y in range(11, min(self.rows-1, 18)):
                if 8 < self.cols:
                    self.obstaculos.append((8, y))

        elif t == 3:
            # arena: bordas
            for x in range(self.cols):
                self.obstaculos.append((x, 0))
                self.obstaculos.append((x, self.rows - 1))
            for y in range(self.rows):
                self.obstaculos.append((0, y))
                self.obstaculos.append((self.cols - 1, y))

            # exemplo de obstaculos centrais (cruz)
            midx = self.cols // 2
            midy = self.rows // 2
            for x in range(max(1, midx - 6), min(self.cols-1, midx + 7)):
                self.obstaculos.append((x, midy))
            for y in range(max(1, midy - 6), min(self.rows-1, midy + 7)):
                self.obstaculos.append((midx, y))

        # remover duplicados e filtrar válidos
        self.obstaculos = [(x,y) for x,y in dict.fromkeys(self.obstaculos) if 0 <= x < self.cols and 0 <= y < self.rows]

        # spawn center por defeito
        self.spawn_snake_block = (self.cols // 2, self.rows // 2)
        self.spawn_food_block = (max(1, self.cols // 2 - 1), max(1, self.rows // 2))

    # ------------------ utilitários ------------------
    def obstaculos_pixels(self):
        """Retorna set de (x_px, y_px) dos obstáculos (top-left de cada bloco)."""
        return {(bx * self.block, by * self.block) for (bx, by) in self.obstaculos}

    def spawn_seguro(self, ocupados_pixels, tries=2000):
        """
        Devolve posição segura em pixels (x_px, y_px) para spawn.
        ocupados_pixels: conjunto de posições em pixels já ocupadas (cobra)
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

        # 3) procurar por todas células livres (varrer por bloco)
        livres = []
        for gy in range(self.rows):
            for gx in range(self.cols):
                ppx = (gx * self.block, gy * self.block)
                if ppx not in ocupados_pixels and ppx not in obst_px:
                    livres.append(ppx)

        if livres:
            return random.choice(livres)

        # fallback
        return (self.block, self.block)

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

        # colisão com obstáculo
        if (bx, by) in self.obstaculos:
            return True

        # Detectar se este mapa tem bordas sólidas
        top_full = all(((x,0) in self.obstaculos) for x in range(self.cols))
        bottom_full = all(((x,self.rows-1) in self.obstaculos) for x in range(self.cols))
        left_full = all(((0,y) in self.obstaculos) for y in range(self.rows))
        right_full = all(((self.cols-1,y) in self.obstaculos) for y in range(self.rows))

        has_full_borders = top_full and bottom_full and left_full and right_full

        if has_full_borders:
            # colisão se fora dos limites
            if bx < 0 or bx >= self.cols or by < 0 or by >= self.rows:
                return True
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
