import pygame
from collections import deque
from game.snake import Snake
from game.food import Food


TODAS_DIRECOES = [(1, 0), (-1, 0), (0, 1), (0, -1)]


class PlayerVsAI:
    def __init__(self, engine):
        self.engine = engine
        self.nome   = "Humano vs IA"

        # ── Cobras ────────────────────────────────────────────────────
        p1_spawn = self.engine.mapa.obter_spawn_player(1)
        p2_spawn = self.engine.mapa.obter_spawn_player(2)

        self.snake = Snake(p1_spawn, self.engine.block)
        self.bot   = Snake(p2_spawn, self.engine.block)
        self.bot.body_color   = (200, 60,  60)
        self.bot.head_color   = (230, 100, 100)
        self.bot.border_color = (120, 20,  20)

        # ── Comida ────────────────────────────────────────────────────
        self.food = Food(self.engine.play_rect, self.engine.block)
        self.food.spawn([], obstaculos_pixels=self.engine.mapa.obstaculos_pixels())
        self.foods = [self.food]

        # ── Pontuação do bot ──────────────────────────────────────────
        self.score_bot = 0

        # ── Cache de bloqueios ────────────────────────────────────────
        # Os obstáculos do mapa nunca mudam — calculamos uma vez e guardamos.
        # Os corpos das cobras são adicionados por cima em _obter_bloqueios().
        b = self.engine.block
        self._obst_blocos = frozenset(
            (px // b, py // b)
            for px, py in self.engine.mapa.obstaculos_pixels()
        )

        # ── Estado ────────────────────────────────────────────────────
        self.terminado = False

        # ── Ready check + Countdown ───────────────────────────────────
        self.p1_ready         = False
        self.countdown_active = False
        self.countdown_val    = 3
        self.last_tick        = 0
        self.started          = False

    # ------------------------------------------------------------------ #
    #  INPUT DO JOGADOR                                                    #
    # ------------------------------------------------------------------ #
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.snake.set_direction(0, -1);  self.p1_ready = True
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.snake.set_direction(0,  1);  self.p1_ready = True
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self.snake.set_direction(-1, 0);  self.p1_ready = True
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.snake.set_direction(1,  0);  self.p1_ready = True

    # ------------------------------------------------------------------ #
    #  UPDATE PRINCIPAL                                                    #
    # ------------------------------------------------------------------ #
    def update(self):
        if self.terminado:
            return

        # 1. Countdown
        if self.p1_ready and not self.countdown_active and not self.started:
            self.countdown_active = True
            self.last_tick = pygame.time.get_ticks()

        if self.countdown_active:
            agora = pygame.time.get_ticks()
            if agora - self.last_tick >= 1000:
                self.countdown_val -= 1
                self.last_tick = agora
                if self.countdown_val <= 0:
                    self.countdown_active = False
                    self.started = True

        if not self.started:
            return

        # 2. Jogo em curso
        self.logica_do_bot()
        self.snake.update()
        self.bot.update()
        self.verificar_colisoes()

    # ------------------------------------------------------------------ #
    #  LÓGICA DO BOT — BFS + FLOOD FILL                                   #
    # ------------------------------------------------------------------ #
    def logica_do_bot(self):
        bloqueios = self._obter_bloqueios()
        cabeca    = self._px_para_bloco(self.bot.head_pos())
        comida    = self._px_para_bloco(self.food.pos)
        limite_ff = max(4, len(self.bot.segments) // 2)

        caminho = self._bfs(cabeca, comida, bloqueios)

        if caminho and len(caminho) >= 2:
            prox_bloco        = caminho[1]
            direcao_candidata = (prox_bloco[0] - cabeca[0],
                                 prox_bloco[1] - cabeca[1])

            # Flood fill com limite — para logo que tiver espaço suficiente
            if self._flood_fill(prox_bloco, bloqueios, limite_ff) >= limite_ff:
                self.bot.set_direction(*direcao_candidata)
                return

            # Pouco espaço no caminho direto — modo sobrevivência
            melhor = self._melhor_direcao_sobrevivencia(cabeca, bloqueios, limite_ff)
            if melhor:
                self.bot.set_direction(*melhor)
            return

        # Sem caminho — modo sobrevivência
        melhor = self._melhor_direcao_sobrevivencia(cabeca, bloqueios, limite_ff)
        if melhor:
            self.bot.set_direction(*melhor)

    # ------------------------------------------------------------------ #
    #  AUXILIARES DO BOT                                                   #
    # ------------------------------------------------------------------ #
    def _px_para_bloco(self, pos_px):
        b = self.engine.block
        return (pos_px[0] // b, pos_px[1] // b)

    def _obter_bloqueios(self):
        """
        Reutiliza o frozenset de obstáculos do mapa (calculado uma vez no __init__)
        e adiciona por cima os corpos atuais das cobras (exceto a calda).
        """
        b = self.engine.block
        # Corpos das cobras sem a calda (ela vai desaparecer no próximo tick)
        corpos = set()
        for seg in self.bot.segments[:-1]:
            corpos.add((seg[0] // b, seg[1] // b))
        for seg in self.snake.segments[:-1]:
            corpos.add((seg[0] // b, seg[1] // b))

        # União do cache fixo com os corpos dinâmicos
        return self._obst_blocos | corpos

    def _bfs(self, inicio, objetivo, bloqueios):
        """BFS — devolve lista de blocos [inicio…objetivo] ou None."""
        cols = self.engine.mapa.cols
        rows = self.engine.mapa.rows

        visitado = {inicio: None}
        fila     = deque([inicio])

        while fila:
            atual = fila.popleft()
            if atual == objetivo:
                caminho, passo = [], objetivo
                while passo is not None:
                    caminho.append(passo)
                    passo = visitado[passo]
                caminho.reverse()
                return caminho
            for dx, dy in TODAS_DIRECOES:
                viz = (atual[0] + dx, atual[1] + dy)
                if not (0 <= viz[0] < cols and 0 <= viz[1] < rows):
                    continue
                if viz in bloqueios or viz in visitado:
                    continue
                visitado[viz] = atual
                fila.append(viz)
        return None

    def _flood_fill(self, inicio, bloqueios, limite):
        """
        Conta células livres acessíveis a partir de `inicio`.
        Para assim que atingir `limite` — não precisa de contar o mapa inteiro.
        """
        cols = self.engine.mapa.cols
        rows = self.engine.mapa.rows

        if inicio in bloqueios:
            return 0

        visitado = {inicio}
        fila     = deque([inicio])
        contagem = 0

        while fila:
            atual = fila.popleft()
            contagem += 1
            if contagem >= limite:      # já chega — para cedo
                return contagem
            for dx, dy in TODAS_DIRECOES:
                viz = (atual[0] + dx, atual[1] + dy)
                if not (0 <= viz[0] < cols and 0 <= viz[1] < rows):
                    continue
                if viz in bloqueios or viz in visitado:
                    continue
                visitado.add(viz)
                fila.append(viz)

        return contagem

    def _melhor_direcao_sobrevivencia(self, cabeca, bloqueios, limite):
        """Escolhe a direção com mais espaço livre. Nunca reverte."""
        cols      = self.engine.mapa.cols
        rows      = self.engine.mapa.rows
        dir_atual = self.bot.direction
        oposta    = (-dir_atual[0], -dir_atual[1])

        melhor_dir, melhor_espaco = None, -1

        for direcao in TODAS_DIRECOES:
            if direcao == oposta:
                continue
            prox = (cabeca[0] + direcao[0], cabeca[1] + direcao[1])
            if not (0 <= prox[0] < cols and 0 <= prox[1] < rows):
                continue
            if prox in bloqueios:
                continue
            espaco = self._flood_fill(prox, bloqueios, limite)
            if espaco > melhor_espaco:
                melhor_espaco = espaco
                melhor_dir    = direcao

        return melhor_dir

    # ------------------------------------------------------------------ #
    #  COLISÕES                                                            #
    # ------------------------------------------------------------------ #
    def verificar_colisoes(self):
        if self.terminado:
            return

        head_p = self.snake.head_pos()
        head_b = self.bot.head_pos()

        ocupados = self.snake.segments + self.bot.segments
        obst_px  = self.engine.mapa.obstaculos_pixels()

        # ── Comer (jogador) ───────────────────────────────────────────
        for f in self.foods:
            if head_p == f.pos:
                self.snake.grow()
                self.engine.score.adicionar_pontos(10)
                try:
                    self.engine.assets.play_sound("eat")
                except Exception:
                    pass
                f.spawn(ocupados, obstaculos_pixels=obst_px)

        # ── Comer (bot) ───────────────────────────────────────────────
        for f in self.foods:
            if head_b == f.pos:
                self.bot.grow()
                self.score_bot += 10
                f.spawn(ocupados, obstaculos_pixels=obst_px)

        # ── Morte ─────────────────────────────────────────────────────
        colisao_p  = self.engine.mapa.verificar_colisao(head_p)
        colisao_b  = self.engine.mapa.verificar_colisao(head_b)

        jogador_morreu = (
            colisao_p is True
            or head_p in self.bot.segments
            or self.snake.collides_self()
        )
        bot_morreu = (
            colisao_b is True
            or head_b in self.snake.segments
            or self.bot.collides_self()
        )

        # ── Teleporte (mapa sem bordas) ───────────────────────────────
        if isinstance(colisao_p, tuple):
            self.snake.set_head_pos(colisao_p)
        if isinstance(colisao_b, tuple):
            self.bot.set_head_pos(colisao_b)

        # ── Ecrã final ────────────────────────────────────────────────
        if jogador_morreu or bot_morreu:
            self.terminado = True
            pts_jogador = self.engine.score.obter_pontuacao()

            if jogador_morreu and bot_morreu:
                resultado = "empate"
            elif jogador_morreu:
                resultado = "derrota"
            else:
                resultado = "vitoria"

            self.engine.game_over_vsai(resultado, pts_jogador, self.score_bot)

    # ------------------------------------------------------------------ #
    #  DESENHO                                                             #
    # ------------------------------------------------------------------ #
    def draw(self, surface):
        self.snake.draw(surface)
        self.bot.draw(surface)
        for f in self.foods:
            f.draw(surface)

        if self.started:
            return

        f_grande  = pygame.font.SysFont(None, 80)
        f_pequena = pygame.font.SysFont(None, 30)
        largura   = surface.get_width()
        altura    = surface.get_height()
        cx, cy    = largura // 2, altura // 2

        if not self.p1_ready:
            msg = f_pequena.render("Carrega numa direção para começar!", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width() // 2, cy - 40))
            controls = f_pequena.render("WASD ou Setas", True, (180, 180, 180))
            surface.blit(controls, (cx - controls.get_width() // 2, cy + 10))

        elif self.countdown_active:
            num = f_grande.render(str(self.countdown_val), True, (255, 200, 0))
            surface.blit(num, (cx - num.get_width() // 2, cy - num.get_height() // 2))