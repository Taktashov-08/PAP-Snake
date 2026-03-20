# src/game/modes/player_vs_ai.py
import pygame
import heapq
from collections import deque

from game.entities.snake  import Snake
from game.entities.food   import Food
from game.entities.boost  import Boost
from game.modes.base_mode import BaseModo

TODAS_DIRECOES = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# ── Custos A* ─────────────────────────────────────────────────────────────────
CUSTO_NORMAL       = 1.0
CUSTO_BOOST_VEL    = 0.5
CUSTO_BOOST_IMUNE  = 0.3
CUSTO_PAREDE_IMUNE = 0.8

# ── Limiares táticos ──────────────────────────────────────────────────────────
LIMIAR_ATAQUE  = 1.20
LIMIAR_FUGA    = 0.75
DIST_CONFRONTO = 6

# ── Desvio máximo para ir buscar boost ────────────────────────────────────────
DESVIO_MAX_BOOST_VEL   = 4
DESVIO_MAX_BOOST_IMUNE = 6


class PlayerVsAI(BaseModo):
    """Jogador humano contra Bot com IA (A* + Flood Fill + táticas)."""

    def __init__(self, engine):
        super().__init__(engine)

        self._mapa = engine.mapa
        self._obst = self._mapa._obst_set  # set de blocos — lookup O(1)

        # ── Cobras ────────────────────────────────────────────────────
        self.snake = Snake(self._mapa.obter_spawn_player(1), engine.block)
        self.bot   = Snake(self._mapa.obter_spawn_player(2), engine.block)
        self.bot.body_color   = (200, 60,  60)
        self.bot.head_color   = (230, 100, 100)
        self.bot.border_color = (120, 20,  20)

        # ── Itens ─────────────────────────────────────────────────────
        self.food        = Food(engine.play_rect, engine.block)
        self.foods       = [self.food]
        self.boost_vel   = Boost("velocidade", engine.play_rect, engine.block)
        self.boost_imune = Boost("imunidade",  engine.play_rect, engine.block)

        self.food_spawn_safe(self.food, self.foods)
        self._spawn_boost(self.boost_vel)
        self._spawn_boost(self.boost_imune)

        # ── Pontuação do bot ──────────────────────────────────────────
        self.score_bot = 0

        # ── Boosts ativos (ticks restantes) ───────────────────────────
        self.boosts_bot     = {"velocidade": 0, "imunidade": 0}
        self.boosts_jogador = {"velocidade": 0, "imunidade": 0}

        # Sets de blocos dos boosts (internos — não polui o engine)
        self._blocos_boost_vel   = self._boost_para_blocos(self.boost_vel)
        self._blocos_boost_imune = self._boost_para_blocos(self.boost_imune)

        self.p1_ready = False

    # ── Spawn seguro de boosts ────────────────────────────────────────────────
    def _spawn_boost(self, boost):
        ocupados = set(self.snake.segments) | set(self.bot.segments)
        for item in [self.food, self.boost_vel, self.boost_imune]:
            if item is not boost and item.pos:
                ocupados.add(item.pos)
        boost.spawn(ocupados, self._mapa.obstaculos_pixels())

    def _segmentos_ocupados(self):
        return set(self.snake.segments) | set(self.bot.segments)

    # ── Utilitários de grelha ─────────────────────────────────────────────────
    def _bpx(self, pos_px):
        b = self.engine.block
        return (pos_px[0] // b, pos_px[1] // b)

    def _valido(self, bx, by):
        return 0 <= bx < self._mapa.cols and 0 <= by < self._mapa.rows

    def _manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _boost_para_blocos(self, boost):
        if boost.pos is None:
            return set()
        return {self._bpx(boost.pos)}

    def _atualizar_blocos_boosts(self):
        self._blocos_boost_vel   = self._boost_para_blocos(self.boost_vel)
        self._blocos_boost_imune = self._boost_para_blocos(self.boost_imune)

    # ── Estado dos boosts ─────────────────────────────────────────────────────
    def _imune(self):                  return self.boosts_bot["imunidade"]      > 0
    def _com_velocidade(self):         return self.boosts_bot["velocidade"]     > 0
    def _jogador_imune(self):          return self.boosts_jogador["imunidade"]  > 0
    def _jogador_com_velocidade(self): return self.boosts_jogador["velocidade"] > 0

    def _tick_boosts(self):
        for d in (self.boosts_bot, self.boosts_jogador):
            for k in d:
                if d[k] > 0:
                    d[k] -= 1

    def _ativar_boost_bot(self, tipo):
        if tipo == "velocidade": self.boosts_bot[tipo] = self.boost_vel.duracao
        elif tipo == "imunidade": self.boosts_bot[tipo] = self.boost_imune.duracao

    def _ativar_boost_jogador(self, tipo):
        if tipo == "velocidade": self.boosts_jogador[tipo] = self.boost_vel.duracao
        elif tipo == "imunidade": self.boosts_jogador[tipo] = self.boost_imune.duracao

    # ── Input ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        mapa_teclas = {
            pygame.K_w: (0,-1), pygame.K_UP:    (0,-1),
            pygame.K_s: (0, 1), pygame.K_DOWN:  (0, 1),
            pygame.K_a: (-1,0), pygame.K_LEFT:  (-1,0),
            pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0),
        }
        if event.key in mapa_teclas:
            self.snake.set_direction(*mapa_teclas[event.key])
            self.p1_ready = True

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self):
        if self.terminado:
            return
        if self.p1_ready and not self.countdown_active and not self.started:
            self._iniciar_countdown()
        self._tick_countdown()
        if not self.started:
            return

        self._tick_boosts()
        self._logica_bot()
        self.snake.update()
        if self._jogador_com_velocidade():
            self.snake.update()
        self.bot.update()
        self._verificar_colisoes()

    # ── Bloqueios para o bot ──────────────────────────────────────────────────
    def _obter_bloqueios(self):
        b = self.engine.block
        corpos = {
            (s[0] // b, s[1] // b)
            for cobra in (self.bot, self.snake)
            for s in cobra.segments[:-1]
        }
        return corpos if self._imune() else corpos | self._obst

    # ── Lógica do bot ─────────────────────────────────────────────────────────
    def _logica_bot(self):
        bloqueios = self._obter_bloqueios()
        cabeca    = self._bpx(self.bot.head_pos())
        cabeca_p  = self._bpx(self.snake.head_pos())
        comida    = self._bpx(self.food.pos)
        limite_ff = max(4, len(self.bot.segments) // 2)

        tam_bot    = len(self.bot.segments)
        tam_player = len(self.snake.segments)
        perto      = self._manhattan(cabeca, cabeca_p) <= DIST_CONFRONTO

        boost_alvo = self._avaliar_boosts(cabeca, comida, bloqueios,
                                          tam_bot, tam_player, perto)

        if boost_alvo:
            objetivo, modo = boost_alvo, "boost"
        else:
            objetivo, modo = self._decidir_objetivo(
                cabeca, cabeca_p, comida, tam_bot, tam_player, perto, bloqueios)

        caminho = self._astar(cabeca, objetivo, bloqueios)

        if caminho and len(caminho) >= 2:
            prox    = caminho[1]
            direcao = (prox[0] - cabeca[0], prox[1] - cabeca[1])
            if modo in ("ataque", "boost"):
                self.bot.set_direction(*direcao)
                return
            if self._flood_fill(prox, bloqueios, limite_ff) >= limite_ff:
                self.bot.set_direction(*direcao)
                return

        melhor = self._melhor_direcao_sobrevivencia(cabeca, bloqueios, limite_ff)
        if melhor:
            self.bot.set_direction(*melhor)

    # ── Decisor tático ────────────────────────────────────────────────────────
    def _decidir_objetivo(self, cabeca, cabeca_p, comida,
                          tam_bot, tam_player, perto, bloqueios):
        ratio = tam_bot / max(tam_player, 1)
        if perto:
            if self._imune() or ratio >= LIMIAR_ATAQUE:
                return self._alvo_corpo_jogador(), "ataque"
            elif ratio < LIMIAR_FUGA:
                return self._calcular_destino_fuga(cabeca, cabeca_p, bloqueios), "fuga"
        return comida, "comer"

    def _alvo_corpo_jogador(self):
        segs = self.snake.segments
        seg  = segs[1] if len(segs) >= 2 else segs[0]
        return self._bpx(seg)

    def _calcular_destino_fuga(self, cabeca, cabeca_p, bloqueios):
        cols, rows = self._mapa.cols, self._mapa.rows
        dx = cabeca[0] - cabeca_p[0]
        dy = cabeca[1] - cabeca_p[1]
        dest_x  = max(1, min(cols - 2, cabeca[0] + dx * 5))
        dest_y  = max(1, min(rows - 2, cabeca[1] + dy * 5))
        destino = (dest_x, dest_y)
        if destino in bloqueios:
            for raio in range(1, 6):
                for ddx in range(-raio, raio + 1):
                    for ddy in range(-raio, raio + 1):
                        c = (dest_x + ddx, dest_y + ddy)
                        if self._valido(*c) and c not in bloqueios:
                            return c
        return destino

    # ── Avaliador de boosts ───────────────────────────────────────────────────
    def _avaliar_boosts(self, cabeca, comida, bloqueios,
                        tam_bot, tam_player, perto):
        dist_comida  = self._manhattan(cabeca, comida)
        ratio        = tam_bot / max(tam_player, 1)
        melhor_boost = None
        melhor_prio  = -1

        candidatos = [
            (self._blocos_boost_vel,
             self._com_velocidade(),
             perto and ratio < LIMIAR_FUGA,
             DESVIO_MAX_BOOST_VEL, 0),
            (self._blocos_boost_imune,
             self._imune(),
             not ((perto and ratio >= LIMIAR_ATAQUE) or ratio < LIMIAR_FUGA) and not perto,
             DESVIO_MAX_BOOST_IMUNE, 10),
        ]

        for blocos, ja_tem, skip, desvio_max, bonus in candidatos:
            if ja_tem or skip:
                continue
            for pos in blocos:
                if pos in bloqueios:
                    continue
                desvio = (self._manhattan(cabeca, pos)
                          + self._manhattan(pos, comida)
                          - dist_comida)
                if desvio <= desvio_max:
                    p = (desvio_max - desvio) + bonus
                    if p > melhor_prio:
                        melhor_prio  = p
                        melhor_boost = pos

        return melhor_boost

    # ── A* ────────────────────────────────────────────────────────────────────
    def _astar(self, inicio, objetivo, bloqueios):
        cols, rows = self._mapa.cols, self._mapa.rows
        imune      = self._imune()

        def h(pos):
            return abs(pos[0] - objetivo[0]) + abs(pos[1] - objetivo[1])

        def custo(pos):
            if pos in self._obst:
                return CUSTO_PAREDE_IMUNE if imune else None
            if pos in self._blocos_boost_imune: return CUSTO_BOOST_IMUNE
            if pos in self._blocos_boost_vel:   return CUSTO_BOOST_VEL
            return CUSTO_NORMAL

        heap     = [(h(inicio), 0.0, inicio, [inicio])]
        visitado = {}

        while heap:
            f, g, atual, caminho = heapq.heappop(heap)
            if atual == objetivo:
                return caminho
            if atual in visitado and visitado[atual] <= g:
                continue
            visitado[atual] = g
            for dx, dy in TODAS_DIRECOES:
                viz = (atual[0] + dx, atual[1] + dy)
                if not (0 <= viz[0] < cols and 0 <= viz[1] < rows):
                    continue
                if viz in bloqueios and viz not in self._obst:
                    continue
                c = custo(viz)
                if c is None:
                    continue
                ng = g + c
                if viz in visitado and visitado[viz] <= ng:
                    continue
                heapq.heappush(heap, (ng + h(viz), ng, viz, caminho + [viz]))

        return None

    # ── Flood Fill + Sobrevivência ────────────────────────────────────────────
    def _flood_fill(self, inicio, bloqueios, limite):
        if inicio in bloqueios:
            return 0
        visitado = {inicio}
        fila     = deque([inicio])
        contagem = 0
        while fila:
            atual = fila.popleft()
            contagem += 1
            if contagem >= limite:
                return contagem
            for dx, dy in TODAS_DIRECOES:
                viz = (atual[0] + dx, atual[1] + dy)
                if not self._valido(*viz) or viz in bloqueios or viz in visitado:
                    continue
                visitado.add(viz)
                fila.append(viz)
        return contagem

    def _melhor_direcao_sobrevivencia(self, cabeca, bloqueios, limite):
        oposta = (-self.bot.direction[0], -self.bot.direction[1])
        melhor_dir, melhor_esp = None, -1
        for d in TODAS_DIRECOES:
            if d == oposta:
                continue
            prox = (cabeca[0] + d[0], cabeca[1] + d[1])
            if not self._valido(*prox) or prox in bloqueios:
                continue
            esp = self._flood_fill(prox, bloqueios, limite)
            if esp > melhor_esp:
                melhor_esp = esp
                melhor_dir = d
        return melhor_dir

    # ── Colisões ──────────────────────────────────────────────────────────────
    def _verificar_colisoes(self):
        if self.terminado:
            return

        head_p  = self.snake.head_pos()
        head_b  = self.bot.head_pos()
        ocupados = self.snake.segments + self.bot.segments

        # ── Comer (comida normal) ─────────────────────────────────────
        for f in self.foods:
            if head_p == f.pos:
                self.snake.grow()
                self.engine.score.adicionar_pontos(10)
                try: self.engine.assets.get_sound("eat").play()
                except Exception: pass
                self.food_spawn_safe(f, self.foods)
            if head_b == f.pos:
                self.bot.grow()
                self.score_bot += 10
                self.food_spawn_safe(f, self.foods)

        # ── Apanhar boosts ────────────────────────────────────────────
        for boost, tipo in ((self.boost_vel, "velocidade"),
                            (self.boost_imune, "imunidade")):
            if not boost.pos:
                continue
            if head_p == boost.pos:
                self._ativar_boost_jogador(tipo)
                self._spawn_boost(boost)
                self._atualizar_blocos_boosts()
            elif head_b == boost.pos:
                self._ativar_boost_bot(tipo)
                self._spawn_boost(boost)
                self._atualizar_blocos_boosts()

        # ── Teleporte (mapa sem bordas) ───────────────────────────────
        col_p = self._mapa.verificar_colisao(head_p)
        col_b = self._mapa.verificar_colisao(head_b)
        if isinstance(col_p, tuple): self.snake.set_head_pos(col_p)
        if isinstance(col_b, tuple): self.bot.set_head_pos(col_b)

        # ── Morte ─────────────────────────────────────────────────────
        if head_p == head_b:
            vantagem       = len(self.bot.segments) - len(self.snake.segments)
            jogador_morreu = vantagem >= 0
            bot_morreu     = vantagem <= 0
        else:
            jogador_morreu = (
                (col_p is True and not self._jogador_imune())
                or head_p in self.bot.segments
                or self.snake.collides_self()
            )
            bot_morreu = (
                (col_b is True and not self._imune())
                or head_b in self.snake.segments
                or self.bot.collides_self()
            )

        if jogador_morreu or bot_morreu:
            self.terminado = True
            pts = self.engine.score.obter_pontuacao()
            if jogador_morreu and bot_morreu: resultado = "empate"
            elif jogador_morreu:              resultado = "derrota"
            else:                             resultado = "vitoria"
            self.engine.game_over_vsai(resultado, pts, self.score_bot)

    # ── Desenho ───────────────────────────────────────────────────────────────
    def draw(self, surface):
        self.snake.draw(surface)
        self.bot.draw(surface)
        for f in self.foods:
            f.draw(surface)
        self.boost_vel.draw(surface)
        self.boost_imune.draw(surface)

        b  = self.engine.block
        cx = surface.get_width() // 2
        if self._jogador_com_velocidade():
            _draw_boost_hud(surface, cx - 60, 4, b, (255, 200, 40), "V",
                            self.boosts_jogador["velocidade"], self.boost_vel.duracao)
        if self._jogador_imune():
            _draw_boost_hud(surface, cx + 10, 4, b, (60, 180, 255), "I",
                            self.boosts_jogador["imunidade"], self.boost_imune.duracao)

        if self.started:
            return

        f_g = pygame.font.SysFont(None, 80)
        f_p = pygame.font.SysFont(None, 30)
        cx2 = surface.get_width()  // 2
        cy  = surface.get_height() // 2

        if not self.p1_ready:
            msg = f_p.render("Carrega numa direcao para comecar!", True, (255, 255, 255))
            surface.blit(msg, (cx2 - msg.get_width() // 2, cy - 40))
            ctl = f_p.render("WASD ou Setas", True, (180, 180, 180))
            surface.blit(ctl, (cx2 - ctl.get_width() // 2, cy + 10))
        elif self.countdown_active:
            self._draw_countdown(surface)


# ── Helper HUD de boost ───────────────────────────────────────────────────────
def _draw_boost_hud(surface, x, y, block, cor, letra, ticks, duracao):
    w, h, r = 50, max(4, block // 3), 2
    pygame.draw.rect(surface, (40, 40, 50), pygame.Rect(x, y, w, h), border_radius=r)
    fill_w = int(w * max(0.0, ticks / max(duracao, 1)))
    pygame.draw.rect(surface, cor, pygame.Rect(x, y, fill_w, h), border_radius=r)
    fonte = pygame.font.SysFont(None, max(10, block - 2))
    txt   = fonte.render(letra, True, cor)
    surface.blit(txt, (x - txt.get_width() - 3, y - 1))
