# src/game/engine.py
import pygame
import sys
import game.config as cfg

from game.config import BLOCK_SIZE, FPS, BLACK, WHITE
from game.snake import Snake
from game.food import Food
from game.records import RecordsManager
from game.hud import HUD
from game.score import Score
from game.map import Mapas



class Game:
    def __init__(self, player_name="Player", modo="OG Snake", dificuldade="Normal", velocidade_mult=1.0, mapa_tipo=1):
        self.player_name = player_name
        self.modo = modo
        self.dificuldade = dificuldade
        self.velocidade_mult = velocidade_mult

        pygame.init()

        # tenta herdar o tamanho actual da janela (menu). se não existir, usa cfg defaults
        try:
            current_surface = pygame.display.get_surface()
            if current_surface is not None:
                current_w, current_h = current_surface.get_size()
            else:
                current_w, current_h = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
        except Exception:
            current_w, current_h = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        # cria a janela real (resizable) usando o tamanho herdado
        # usar get_surface() em vez de recriar a janela evita minimizar em algumas plataformas
        self.screen = pygame.display.set_mode((current_w, current_h), pygame.RESIZABLE)

        # sincronizar grelha ao tamanho herdado
        nw, nh, nb = cfg.fit_screen_to_grid(current_w, current_h)
        cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT, cfg.BLOCK_SIZE = nw, nh, nb

        # superfície lógica (tudo é desenhado aqui, depois escalado)
        self.logical_size = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.surface = pygame.Surface(self.logical_size)

        # área de jogo lógica
        self.play_rect = (0, 0, cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        self.clock = pygame.time.Clock()
        self.running = True

        # managers
        self.records = RecordsManager()
        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)

        # mapa (aceita int tipo ou path)
        self.mapa = Mapas(mapa_tipo)

        # usar block size do mapa se existir, senão usar cfg.BLOCK_SIZE
        self.block = getattr(self.mapa, "block", cfg.BLOCK_SIZE) or cfg.BLOCK_SIZE

        # multiplicador de pontuação
        mult = 1.0
        if dificuldade in ("Rápido", "Rapido"):
            mult = 1.5
        elif dificuldade == "Muito Rápido":
            mult = 2.0
        self.score = Score(multiplicador=mult)

        # --- entidades (spawn seguro) ---
        ocupado_pixels = set()

        # spawn seguro para a snake
        spawn_snake = self.mapa.spawn_seguro(ocupado_pixels)
        self.snake = Snake(start_pos=spawn_snake, block_size=self.block)
        ocupado_pixels.update(self.snake.segments)

        # comida (spawn seguro, sem colisão com cobra nem obstáculos)
        obstaculos_pix = set(self.mapa.obstaculos_pixels())
        self.food = Food(self.play_rect, self.block)
        self.food.spawn(ocupado_pixels, obstaculos_pix)

        # parametros
        self.base_fps = FPS

        # não iniciar movimento até o jogador pressionar a 1ª tecla de direção
        self.started = False
        # garantir direção neutra até começar
        try:
            self.snake.direction = (0, 0)
        except Exception:
            pass

        # guarda ultimo tamanho da janela para detectar cambios
        self._last_window_size = self.screen.get_size()

    def handle_window_resize(self, win_w, win_h):
        """
        Trata mudança do tamanho da janela.
        Não recria a janela (evita minimizar) — actualiza lógica interna e a surface.
        """
        # Salva o block antigo para escalar posições
        old_block = self.block

        # 1) recalcular screen lógico + block
        nw, nh, nb = cfg.fit_screen_to_grid(win_w, win_h)
        cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT, cfg.BLOCK_SIZE = nw, nh, nb

        # 2) atualizar superfície lógica
        self.logical_size = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.surface = pygame.Surface(self.logical_size)
        self.play_rect = (0, 0, cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        # 3) atualizar block
        self.block = cfg.BLOCK_SIZE

        # 4) actualizar mapa para a nova grelha (cols/rows/block)
        try:
            self.mapa.block = self.block
            self.mapa.cols = cfg.SCREEN_WIDTH // self.block
            self.mapa.rows = cfg.SCREEN_HEIGHT // self.block
        except Exception:
            # se Mapas não tiver esses atributos, ignora (fallback)
            pass

        # 5) re-gerar/ajustar mapa: usa os loaders/generators se existirem
        try:
            if self.mapa.filepath is not None:
                self.mapa._load_from_file(self.mapa.filepath)
            else:
                self.mapa._generate_by_type(self.mapa.tipo)
        except Exception:
            # fallback: recria o mapa
            try:
                self.mapa = Mapas(self.mapa.tipo)
            except Exception:
                # não conseguimos regenerar; deixamos como está
                pass

        # Escalar as posições da snake para o novo block size (preservar coordenadas de grid)
        if old_block > 0 and old_block != self.block:
            new_segments = []
            for x, y in self.snake.segments:
                bx = x // old_block
                by = y // old_block
                new_x = bx * self.block
                new_y = by * self.block
                new_segments.append((new_x, new_y))
            self.snake.segments = new_segments

        # Escalar a posição da food de forma similar (em vez de respawn)
        if old_block > 0 and old_block != self.block:
            fx, fy = self.food.pos
            fbx = fx // old_block
            fby = fy // old_block
            self.food.pos = (fbx * self.block, fby * self.block)

        # 6) verificar se a snake continua válida; se não, respawna
        try:
            head = self.snake.head_pos()
            colisao = self.mapa.verificar_colisao(head)
            obstaculos_pix = set(self.mapa.obstaculos_pixels())
            if colisao is True or head in obstaculos_pix:
                ocupado_pixels = set()
                spawn = self.mapa.spawn_seguro(ocupado_pixels)
                self.snake = Snake(start_pos=spawn, block_size=self.block)
                # também respawn food se snake respawn
                obstaculos_pix = set(self.mapa.obstaculos_pixels())
                self.food.spawn(set(self.snake.segments), obstaculos_pix)
        except Exception:
            # se houver erro ao verificar, reposiciona a snake ao centro
            try:
                ocupado_pixels = set()
                spawn = self.mapa.spawn_seguro(ocupado_pixels)
                self.snake = Snake(start_pos=spawn, block_size=self.block)
                # também respawn food
                obstaculos_pix = set(self.mapa.obstaculos_pixels())
                self.food.spawn(set(self.snake.segments), obstaculos_pix)
            except Exception:
                pass

        # Atualizar blocks das entidades
        try:
            if hasattr(self.snake, "block"):
                self.snake.block = self.block
            if hasattr(self.food, "block"):
                self.food.block = self.block
        except Exception:
            pass


    def handle_events(self, events):
        """
        Processa a lista de eventos passada pelo run().
        events: lista retornada por pygame.event.get()
        """
        # debug: imprime teclas (remove depois)
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                # mantém debug por enquanto
                # print(f"[DEBUG] KEYDOWN: key={ev.key}, unicode={getattr(ev, 'unicode', None)}")
                pass

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return

            # VIDEORESIZE é tratado no run() principal (aqui ignoramos)
            if event.type == pygame.VIDEORESIZE:
                continue

            if event.type == pygame.KEYDOWN:
                # ESC fecha o jogo
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return

                # se tecla de direção — activamos started e definimos direção
                if event.key in (pygame.K_UP, pygame.K_w):
                    if not self.started:
                        self.started = True
                    self.snake.set_direction(0, -1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if not self.started:
                        self.started = True
                    self.snake.set_direction(0, 1)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if not self.started:
                        self.started = True
                    self.snake.set_direction(-1, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if not self.started:
                        self.started = True
                    self.snake.set_direction(1, 0)
                else:
                    pass

            # mouse clicks -> podes converter para coords lógicas aqui se precisares

    def update(self):
        # Se ainda não começou, não movemos a snake (evita mortes logo ao inicio)
        if self.started:
            self.snake.update()
        else:
            # se a snake tiver direção != (0,0) e started=False, evita mover até o primeiro input
            dx, dy = getattr(self.snake, "direction", (0, 0))
            if dx != 0 or dy != 0:
                pass

        # verificar colisões com bordas / obstáculos usando o mapa
        resultado = self.mapa.verificar_colisao(self.snake.head_pos())

        if resultado is True:
            # colisão fatal
            self.running = False
            self.game_over()
            return
        elif isinstance(resultado, tuple):
            # teleporte (mapa borderless) - resultado já em coords px
            self.snake.set_head_pos(resultado)

        # verificar colisão consigo mesma
        if self.snake.collides_self():
            self.running = False
            self.game_over()
            return

        # verificar colisão com comida
        if self.snake.head_pos() == self.food.pos:
            self.snake.grow()
            self.score.adicionar_pontos(10)
            self.hud.atualizar_pontuacao(self.score.obter_pontuacao())

            # preparar novos ocupados + obstáculos em pixels e respawn seguro
            occupied = set(self.snake.segments)
            obstaculos_pix = set(self.mapa.obstaculos_pixels())
            self.food.spawn(occupied, obstaculos_pix)

    def draw_logical(self):
        """Desenha tudo na surface lógica (self.surface)."""
        self.surface.fill(BLACK)

        # desenhar obstáculos (usar self.block)
        cor_obst = (120, 120, 120) if getattr(self.mapa, "tipo", 0) == 2 else (80, 80, 80)
        for bx, by in getattr(self.mapa, "obstaculos", []):
            try:
                pygame.draw.rect(
                    self.surface,
                    cor_obst,
                    (bx * self.block, by * self.block, self.block, self.block)
                )
            except Exception:
                # se não der para desenhar um obstáculo, ignora
                pass

        # draw play area border (opcional)
        try:
            pygame.draw.rect(self.surface, (40, 40, 40), pygame.Rect(*self.play_rect), 2)
        except Exception:
            pass

        # desenhar comida e cobra (ambas usam mesmo block)
        try:
            self.food.draw(self.surface)
        except Exception:
            pass

        try:
            self.snake.draw(self.surface)
        except Exception:
            pass

        # HUD na surface lógica
        self.draw_hud(self.surface)

    def draw_hud(self, surface=None):
        if surface is None:
            surface = self.screen
        font = pygame.font.SysFont(None, 24)
        texto = f"{self.hud.jogador} | {self.hud.modo} | {self.hud.dificuldade} | Score: {self.score.obter_pontuacao()}"
        surf = font.render(texto, True, WHITE)
        try:
            surface.blit(surf, (10, 10))
        except Exception:
            pass

    def run(self):
        self.running = True
        clock = pygame.time.Clock()

        while self.running:
            # recolhe eventos uma única vez
            events = pygame.event.get()

            # PROCESSA resize de forma robusta: procura qualquer evento VIDEORESIZE
            win_w, win_h = self.screen.get_size()
            resized_ev = None
            for ev in events:
                if ev.type == pygame.VIDEORESIZE:
                    resized_ev = ev
                    break

            # detectar nova dimensao (como antes)
            new_w = new_h = None
            if resized_ev is not None:
                new_w, new_h = resized_ev.w, resized_ev.h
            else:
                last = getattr(self, "_last_window_size", None)
                if last is None:
                    self._last_window_size = (win_w, win_h)
                    last = self._last_window_size
                if (win_w, win_h) != last:
                    new_w, new_h = win_w, win_h

            if new_w and new_h:
                # actualiza ultimo tamanho
                self._last_window_size = (new_w, new_h)

                # actualiza referencia de surface (plataformas podem trocar)
                try:
                    self.screen = pygame.display.get_surface() or self.screen
                except Exception:
                    pass

                # chama o handler para a lógica de resize (regenerar mapa, spawn seguro, etc.)
                self.handle_window_resize(new_w, new_h)

            # processa eventos (teclas, etc.)
            self.handle_events(events)

            # lógica
            self.update()

            # desenho na superfície lógica
            self.draw_logical()

            # agora escalar a surface lógica para a janela actual mantendo aspect ratio (LETTERBOX)
            win_w, win_h = self.screen.get_size()

            # --- PROTECÇÃO contra minimizar / tamanhos inválidos ---
            # Se a janela estiver minimizada ou num tamanho muito pequeno, não tentamos blit/scale.
            # Em vez disso, esperamos um pouco e continuamos o loop (assim o programa não crasha).
            if win_w < 32 or win_h < 32:
                # chamar pygame.event.pump() garante que eventos são processados (restaura quando voltar)
                pygame.event.pump()
                # espera curta — reduz CPU enquanto a janela está minimizada
                pygame.time.wait(100)
                clock.tick(10)
                continue

            log_w, log_h = self.logical_size  # ex. 900 x 600

            # proteger contra 0 division (mantemos guardas)
            if log_w == 0 or log_h == 0:
                scale = 1.0
            else:
                scale = min(max(0.0001, win_w / log_w), max(0.0001, win_h / log_h))

            scaled_w = max(1, int(log_w * scale))
            scaled_h = max(1, int(log_h * scale))

            # se scaled for inválido (muito raro devido ao guard), protegemos
            try:
                scaled_surf = pygame.transform.smoothscale(self.surface, (scaled_w, scaled_h))
            except Exception:
                # fallback: usar uma escala mais segura
                try:
                    scaled_surf = pygame.transform.scale(self.surface, (max(1, scaled_w), max(1, scaled_h)))
                except Exception:
                    # não conseguimos escalar, pulamos este frame
                    pygame.time.wait(50)
                    clock.tick(10)
                    continue

            # calcular barras pretas (centrar)
            offset_x = (win_w - scaled_w) // 2
            offset_y = (win_h - scaled_h) // 2

            # limpar janela e desenhar com letterbox
            try:
                self.screen.fill((0, 0, 0))
                self.screen.blit(scaled_surf, (offset_x, offset_y))
                pygame.display.flip()
            except Exception:
                # se a surface da janela for inválida por algum motivo, ignora o blit e espera
                pygame.time.wait(50)

            clock.tick(int(self.base_fps * self.velocidade_mult))

        # quando o loop termina, tentamos restaurar a janela do menu para os valores lógicos
        try:
            pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        except Exception:
            pass


    def game_over(self):
        # save record
        try:
            self.records.guardar_pontuacao(self.hud.jogador, self.hud.modo, self.hud.dificuldade, self.score.obter_pontuacao())
        except Exception:
            pass
        print("Game Over! Pontuação salva.")