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
DIST_CORTE     = 10

# ── Desvio máximo para ir buscar boost ────────────────────────────────────────
DESVIO_MAX_BOOST_VEL   = 4
DESVIO_MAX_BOOST_IMUNE = 6

# ── Duração dos boosts (ticks) ────────────────────────────────────────────────
DURACAO_BOOST_VEL   = 90
DURACAO_BOOST_IMUNE = 60


class PlayerVsAI(BaseModo):
    """Jogador humano contra Bot com IA (A* + Flood Fill + táticas)."""

    def __init__(self, engine):
        super().__init__(engine)

        self._mapa = engine.mapa
        self._obst = self._mapa._obst_set

        # ── Cobras ────────────────────────────────────────────────────
        self.cobra       = Snake(self._mapa.obter_spawn_player(1), engine.block)
        self.bot         = Snake(self._mapa.obter_spawn_player(2), engine.block)
        self.bot.body_color   = (200, 60,  60)
        self.bot.head_color   = (230, 100, 100)
        self.bot.border_color = (120, 20,  20)

        # ── Itens ─────────────────────────────────────────────────────
        self.comida      = Food(engine.play_rect, engine.block)
        self.comidas     = [self.comida]
        self.boost_vel   = Boost("velocidade", engine.play_rect, engine.block)
        self.boost_imune = Boost("imunidade",  engine.play_rect, engine.block)

        self.food_spawn_safe(self.comida,  self.comidas)
        self._spawn_item(self.boost_vel)
        self._spawn_item(self.boost_imune)

        # ── Pontuação do bot ──────────────────────────────────────────
        self.pontos_bot = 0

        # ── Boosts ativos (ticks restantes) ───────────────────────────
        self.boosts_bot     = {"velocidade": 0, "imunidade": 0}
        self.boosts_jogador = {"velocidade": 0, "imunidade": 0}

        # Sets locais dos boosts
        self._blocos_boost_vel   = self._boost_para_blocos(self.boost_vel)
        self._blocos_boost_imune = self._boost_para_blocos(self.boost_imune)

        # Contador para velocidade 1.5x (movimento extra em 2 de cada 3 ticks)
        self._vel_tick = 0

        self.p1_pronto = False

    # ── Spawn seguro ──────────────────────────────────────────────────────────
    def _segmentos_ocupados(self):
        return set(self.cobra.segments) | set(self.bot.segments)

    def _spawn_item(self, item):
        ocupados = self._segmentos_ocupados()
        for outro in [self.comida, self.boost_vel, self.boost_imune]:
            if outro is not item and getattr(outro, "pos", None):
                ocupados.add(outro.pos)
        item.spawn(ocupados, self._mapa.obstaculos_pixels())

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
        duracoes = {"velocidade": DURACAO_BOOST_VEL, "imunidade": DURACAO_BOOST_IMUNE}
        if tipo in duracoes:
            self.boosts_bot[tipo] = duracoes[tipo]

    def _ativar_boost_jogador(self, tipo):
        duracoes = {"velocidade": DURACAO_BOOST_VEL, "imunidade": DURACAO_BOOST_IMUNE}
        if tipo in duracoes:
            self.boosts_jogador[tipo] = duracoes[tipo]

    # ── Input ─────────────────────────────────────────────────────────────────
    _TECLAS = {
        pygame.K_w: (0,-1), pygame.K_UP:    (0,-1),
        pygame.K_s: (0, 1), pygame.K_DOWN:  (0, 1),
        pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0),
        pygame.K_d: (1,  0), pygame.K_RIGHT:(1,  0),
    }

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in self._TECLAS:
            self.cobra.set_direction(*self._TECLAS[event.key])
            self.p1_pronto = True

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self):
        if self.terminado:
            return

        if self.p1_pronto and not self.countdown_active and not self.started:
            self._iniciar_countdown()
        self._tick_countdown()
        if not self.started:
            return

        self._tick_boosts()
        self._logica_bot()

        # Movimento da cobra do jogador
        self.cobra.update()

        # Velocidade 1.5x: movimento extra em 2 de cada 3 ticks
        # _colisao_fatal_jogador() garante que nao atravessa paredes
        if self._jogador_com_velocidade():
            self._vel_tick = (self._vel_tick + 1) % 3
            if self._vel_tick != 0 and not self._colisao_fatal_jogador():
                self.cobra.update()

        self.bot.update()
        self._verificar_colisoes()

    def _colisao_fatal_jogador(self):
        """Verificacao leve antes do segundo movimento do boost de velocidade.
        Devolve True se o passo atual mataria a cobra — sem imunidade ativa."""
        cabeca = self.cobra.head_pos()
        col    = self._mapa.verificar_colisao(cabeca)
        if isinstance(col, tuple):
            self.cobra.set_head_pos(col)   # teleporte aceite
            return False
        if col is True and not self._jogador_imune():
            return True   # bate na parede sem imunidade
        if self.cobra.collides_self():
            return True
        return False

    # ── Bloqueios para o A* ───────────────────────────────────────────────────
    def _obter_bloqueios(self):
        b      = self.engine.block
        corpos = {
            (s[0] // b, s[1] // b)
            for cobra in (self.bot, self.cobra)
            for s in cobra.segments[:-1]
        }
        return corpos if self._imune() else corpos | self._obst

    # ── Logica do bot ─────────────────────────────────────────────────────────
    def _logica_bot(self):
        bloqueios   = self._obter_bloqueios()
        cabeca      = self._bpx(self.bot.head_pos())
        cabeca_p    = self._bpx(self.cobra.head_pos())
        comida      = self._bpx(self.comida.pos)
        limite_ff   = max(4, len(self.bot.segments) // 2)

        tam_bot     = len(self.bot.segments)
        tam_jogador = len(self.cobra.segments)
        perto       = self._manhattan(cabeca, cabeca_p) <= DIST_CONFRONTO

        boost_alvo = self._avaliar_boosts(
            cabeca, comida, bloqueios, tam_bot, tam_jogador, perto
        )

        if boost_alvo:
            objetivo, modo = boost_alvo, "boost"
        else:
            objetivo, modo = self._decidir_objetivo(
                cabeca, cabeca_p, comida,
                tam_bot, tam_jogador, perto, bloqueios
            )

        caminho = self._astar(cabeca, objetivo, bloqueios)

        if caminho and len(caminho) >= 2:
            prox    = caminho[1]
            direcao = (prox[0] - cabeca[0], prox[1] - cabeca[1])

            if modo in ("ataque", "boost"):
                espaco = self._flood_fill(prox, bloqueios, limite_ff)
                if espaco >= max(2, limite_ff // 2):
                    self.bot.set_direction(*direcao)
                    return
            else:
                if self._flood_fill(prox, bloqueios, limite_ff) >= limite_ff:
                    self.bot.set_direction(*direcao)
                    return

        melhor = self._melhor_direcao_sobrevivencia(cabeca, bloqueios, limite_ff)
        if melhor:
            self.bot.set_direction(*melhor)

    # ── Decisor tatico ────────────────────────────────────────────────────────
    def _decidir_objetivo(self, cabeca, cabeca_p, comida,
                          tam_bot, tam_jogador, perto, bloqueios):
        ratio = tam_bot / max(tam_jogador, 1)

        if perto:
            if self._imune() or ratio >= LIMIAR_ATAQUE:
                alvo = self._calcular_intercecao(cabeca, cabeca_p, bloqueios)
                return alvo, "ataque"
            elif ratio < LIMIAR_FUGA:
                return self._calcular_destino_fuga(cabeca, cabeca_p, bloqueios), "fuga"
        elif ratio >= LIMIAR_ATAQUE and self._manhattan(cabeca, cabeca_p) <= DIST_CORTE:
            alvo = self._calcular_intercecao(cabeca, cabeca_p, bloqueios)
            return alvo, "ataque"

        return comida, "comer"

    def _calcular_intercecao(self, cabeca_bot, cabeca_jogador, bloqueios):
        dx, dy = self.cobra.direction
        passos = max(2, self._manhattan(cabeca_bot, cabeca_jogador) // 2)
        alvo_x = max(1, min(self._mapa.cols - 2, cabeca_jogador[0] + dx * passos))
        alvo_y = max(1, min(self._mapa.rows - 2, cabeca_jogador[1] + dy * passos))
        alvo   = (alvo_x, alvo_y)
        if alvo in bloqueios:
            segs = self.cobra.segments
            return self._bpx(segs[1] if len(segs) >= 2 else segs[0])
        return alvo

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
                        tam_bot, tam_jogador, perto):
        dist_comida  = self._manhattan(cabeca, comida)
        ratio        = tam_bot / max(tam_jogador, 1)
        melhor_boost = None
        melhor_prio  = -1

        candidatos = [
            (self._blocos_boost_vel,   self._com_velocidade(),
             perto and ratio < LIMIAR_FUGA,
             DESVIO_MAX_BOOST_VEL,   0),
            (self._blocos_boost_imune, self._imune(),
             perto and ratio >= LIMIAR_ATAQUE,
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

    # ── Flood Fill + Sobrevivencia ────────────────────────────────────────────
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

    # ── Colisoes ──────────────────────────────────────────────────────────────
    def _verificar_colisoes(self):
        if self.terminado:
            return

        cabeca_j = self.cobra.head_pos()
        cabeca_b = self.bot.head_pos()

        # ── Comer comida ──────────────────────────────────────────────
        for f in self.comidas:
            if cabeca_j == f.pos:
                self.cobra.grow()
                self.engine.score.adicionar_pontos(10)
                try: self.engine.assets.get_sound("eat").play()
                except Exception: pass
                self.food_spawn_safe(f, self.comidas)
            if cabeca_b == f.pos:
                self.bot.grow()
                self.pontos_bot += 10
                self.food_spawn_safe(f, self.comidas)

        # ── Apanhar boosts ────────────────────────────────────────────
        for boost, tipo in ((self.boost_vel, "velocidade"),
                            (self.boost_imune, "imunidade")):
            if not boost.pos:
                continue
            if cabeca_j == boost.pos:
                self._ativar_boost_jogador(tipo)
                self._spawn_item(boost)
                self._atualizar_blocos_boosts()
            elif cabeca_b == boost.pos:
                self._ativar_boost_bot(tipo)
                self._spawn_item(boost)
                self._atualizar_blocos_boosts()

        # ── Teleporte (mapa sem bordas) ───────────────────────────────
        col_j = self._mapa.verificar_colisao(cabeca_j)
        col_b = self._mapa.verificar_colisao(cabeca_b)
        if isinstance(col_j, tuple): self.cobra.set_head_pos(col_j)
        if isinstance(col_b, tuple): self.bot.set_head_pos(col_b)

        # ── Morte ─────────────────────────────────────────────────────
        if cabeca_j == cabeca_b:
            vantagem       = len(self.bot.segments) - len(self.cobra.segments)
            jogador_morreu = vantagem >= 0
            bot_morreu     = vantagem <= 0
        else:
            jogador_morreu = (
                (col_j is True and not self._jogador_imune())
                or cabeca_j in self.bot.segments
                or self.cobra.collides_self()
            )
            bot_morreu = (
                (col_b is True and not self._imune())
                or cabeca_b in self.cobra.segments
                or self.bot.collides_self()
            )

        if jogador_morreu or bot_morreu:
            self.terminado = True
            pts = self.engine.score.obter_pontuacao()
            if jogador_morreu and bot_morreu: resultado = "empate"
            elif jogador_morreu:              resultado = "derrota"
            else:                             resultado = "vitoria"
            self.engine.game_over_vsai(resultado, pts, self.pontos_bot)

    # ── Desenho ───────────────────────────────────────────────────────────────
    def draw(self, surface):
        self.cobra.draw(surface)
        self.bot.draw(surface)
        for f in self.comidas:
            f.draw(surface)
        self.boost_vel.draw(surface)
        self.boost_imune.draw(surface)

        self._desenhar_painel_boosts(surface)

        if self.started:
            return

        f_p = pygame.font.SysFont(None, 30)
        cx  = surface.get_width()  // 2
        cy  = surface.get_height() // 2

        if not self.p1_pronto:
            msg = f_p.render("Carrega numa direcao para comecar!", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width() // 2, cy - 40))
            ctl = f_p.render("WASD ou Setas", True, (180, 180, 180))
            surface.blit(ctl, (cx - ctl.get_width() // 2, cy + 10))
        elif self.countdown_active:
            self._draw_countdown(surface)

    # ── Painel de boosts do jogador ───────────────────────────────────────────
    def _desenhar_painel_boosts(self, surface):
        """Painel fixo no canto inferior esquerdo com os dois slots de boost."""
        fps       = max(1, int(self.engine.base_fps * self.engine.velocidade_mult))
        fonte_sm  = pygame.font.SysFont("Consolas", 13)
        fonte_ico = pygame.font.SysFont("Consolas", 15, bold=True)

        larg_slot = 100
        alt_slot  = 32
        gap       = 6
        x_base    = 8
        y_base    = surface.get_height() - alt_slot - 8

        dados = [
            ("VEL", (255, 200, 40),  self.boosts_jogador["velocidade"], DURACAO_BOOST_VEL),
            ("IMU", (60,  180, 255), self.boosts_jogador["imunidade"],  DURACAO_BOOST_IMUNE),
        ]

        for i, (nome, cor, ticks, duracao) in enumerate(dados):
            x     = x_base + i * (larg_slot + gap)
            y     = y_base
            ativo = ticks > 0

            # Fundo do slot
            cor_fundo = (35, 38, 52) if ativo else (20, 22, 30)
            pygame.draw.rect(surface, cor_fundo,
                             pygame.Rect(x, y, larg_slot, alt_slot), border_radius=5)

            # Barra de progresso na base do slot
            alt_barra = 4
            y_barra   = y + alt_slot - alt_barra
            pygame.draw.rect(surface, (28, 30, 42),
                             pygame.Rect(x, y_barra, larg_slot, alt_barra), border_radius=2)
            if ativo:
                fill = max(1, int(larg_slot * ticks / max(duracao, 1)))
                pygame.draw.rect(surface, cor,
                                 pygame.Rect(x, y_barra, fill, alt_barra), border_radius=2)

            # Borda colorida quando ativo
            cor_borda = cor if ativo else (40, 44, 60)
            pygame.draw.rect(surface, cor_borda,
                             pygame.Rect(x, y, larg_slot, alt_slot), 1, border_radius=5)

            # Nome do boost (esquerda)
            cor_texto = cor if ativo else (55, 60, 80)
            txt_nome  = fonte_ico.render(nome, True, cor_texto)
            surface.blit(txt_nome, (x + 6, y + 7))

            # Tempo restante em segundos (direita) — so quando ativo
            if ativo:
                segs      = max(0, ticks // fps)
                txt_tempo = fonte_sm.render(f"{segs}s", True, (200, 205, 220))
                surface.blit(txt_tempo,
                             (x + larg_slot - txt_tempo.get_width() - 6, y + 9))