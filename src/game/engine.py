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

        # cria a janela real (resizable)
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(f"Snake - {modo}")

        # ---- SINCRONIZAR grelha lógica com o tamanho real da janela no arranque ----
        # Isto garante que, se maximizaste o menu antes de iniciar, o jogo ajusta a grelha
        win_w, win_h = self.screen.get_size()
        nw, nh, nb = cfg.fit_screen_to_grid(win_w, win_h)
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
        # garante que spawn ocorre depois da sincronização do play_rect
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
            # se a classe Snake não permitir, deixamos como está
            pass
    
    def handle_window_resize(self, win_w, win_h):

        # 1) recalcular screen + block
        nw, nh, nb = cfg.fit_screen_to_grid(win_w, win_h)
        cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT, cfg.BLOCK_SIZE = nw, nh, nb
    
        # 2) atualizar superfície lógica
        self.logical_size = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.surface = pygame.Surface(self.logical_size)
        self.play_rect = (0, 0, cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
    
        # 3) atualizar block
        self.block = cfg.BLOCK_SIZE
    
        # 4) ATUALIZAR mapa para a nova grelha
        self.mapa.block = self.block
        self.mapa.cols = cfg.SCREEN_WIDTH // self.block
        self.mapa.rows = cfg.SCREEN_HEIGHT // self.block
    
        # 5) re-gerar mapa
        if isinstance(self.mapa.tipo, str) and "file:" in self.mapa.tipo:
            real_path = "assets/maps/" + self.mapa.tipo.split("file:")[1]
            self.mapa._load_from_file(real_path)
        else:
            self.mapa._generate_by_type(self.mapa.tipo)
    
        # 6) verificar se a snake continua válida
        head = self.snake.head_pos()
        if self.mapa.verificar_colisao(head) is True:
            spawn = self.mapa.spawn_seguro(set())
            self.snake = Snake(start_pos=spawn, block_size=self.block)
    
        # 7) reposicionar comida
        occupied = set(self.snake.segments)
        obstac = set(self.mapa.obstaculos_pixels())
        self.food = Food(self.play_rect, self.block)
        self.food.spawn(occupied, obstac)



    def handle_events(self, events):
        """
        Processa a lista de eventos passada pelo run().
        events: lista retornada por pygame.event.get()
        """
        # debug: imprime teclas (remove depois)
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                print(f"[DEBUG] KEYDOWN: key={ev.key}, unicode={getattr(ev, 'unicode', None)}")

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
                    print("[DEBUG] ESC pressed → terminar jogo")
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
                    # ignorar outras teclas
                    pass

            # Se precisares de converter cliques do rato para coords lógicas aqui, faz aqui.
            # Exemplo (não obrigatório agora):
            # if event.type == pygame.MOUSEBUTTONDOWN:
            #     win_w, win_h = self.screen.get_size()
            #     lx = int(event.pos[0] * self.logical_size[0] / win_w)
            #     ly = int(event.pos[1] * self.logical_size[1] / win_h)
            #     # usar (lx,ly) como coord lógica

    def update(self):
        # Se ainda não começou, não movemos a snake (evita mortes logo ao inicio)
        if self.started:
            self.snake.update()
        else:
            # se a snake tiver direção != (0,0) e started=False, evita mover até o primeiro input
            dx, dy = getattr(self.snake, "direction", (0, 0))
            if dx != 0 or dy != 0:
                # só mover depois de started; assim não fazemos self.snake.update()
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
        for bx, by in self.mapa.obstaculos:
            pygame.draw.rect(
                self.surface,
                cor_obst,
                (bx * self.block, by * self.block, self.block, self.block)
            )

        # draw play area border (opcional)
        pygame.draw.rect(self.surface, (40, 40, 40), pygame.Rect(*self.play_rect), 2)

        # desenhar comida e cobra (ambas usam mesmo block)
        self.food.draw(self.surface)
        self.snake.draw(self.surface)

        # HUD na surface lógica
        self.draw_hud(self.surface)

    def draw_hud(self, surface=None):
        if surface is None:
            surface = self.screen
        font = pygame.font.SysFont(None, 24)
        texto = f"{self.hud.jogador} | {self.hud.modo} | {self.hud.dificuldade} | Score: {self.score.obter_pontuacao()}"
        surf = font.render(texto, True, WHITE)
        surface.blit(surf, (10, 10))

    def run(self):
        self.running = True
        clock = pygame.time.Clock()

        while self.running:
            # recolhe eventos uma única vez
            events = pygame.event.get()

            # PROCESSA resize de forma robusta: procura qualquer mudança da janela ou evento VIDEORESIZE
            win_w, win_h = self.screen.get_size()
            resized_ev = None
            for ev in events:
                if ev.type == pygame.VIDEORESIZE:
                    resized_ev = ev
                    break

            # caso haja event VIDEORESIZE usa as dimensões desse event, senão detecta se a janela actual mudou
            if resized_ev is not None:
                new_w, new_h = resized_ev.w, resized_ev.h
            else:
                # detecta mudança real (por exemplo maximize que não gera VIDEORESIZE em algumas plataformas)
                # compara com um campo guardado last_window_size
                last = getattr(self, "_last_window_size", None)
                if last is None:
                    self._last_window_size = (win_w, win_h)
                    last = self._last_window_size
                if (win_w, win_h) != last:
                    new_w, new_h = win_w, win_h
                else:
                    new_w = new_h = None

            if new_w and new_h:
                # actualiza ultimo tamanho
                self._last_window_size = (new_w, new_h)

                # chama o handler que faz tudo (regenerar mapa, spawn seguro, etc.)
                # recria a janela real também (mantemos RESIZABLE)
                try:
                    self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                except Exception:
                    pass

                # chama o handler para a lógica de resize
                self.handle_window_resize(new_w, new_h)



            # processa eventos (teclas, etc.)
            self.handle_events(events)

            # lógica
            self.update()

            # desenho na superfície lógica
            self.draw_logical()

            # agora escalar a surface lógica para a janela actual mantendo aspect ratio (letterbox)
            win_w, win_h = self.screen.get_size()
            log_w, log_h = self.logical_size

            scale = min(win_w / log_w, win_h / log_h)
            scaled_w = max(1, int(log_w * scale))
            scaled_h = max(1, int(log_h * scale))

            scaled_surf = pygame.transform.smoothscale(self.surface, (scaled_w, scaled_h))

            offset_x = (win_w - scaled_w) // 2
            offset_y = (win_h - scaled_h) // 2

            # limpar janela e blit
            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled_surf, (offset_x, offset_y))

            pygame.display.flip()
            clock.tick(int(self.base_fps * self.velocidade_mult))

        # quando o loop termina, tentamos restaurar a janela do menu para os valores lógicos
        try:
            pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        except Exception:
            pass

    def game_over(self):
        # save record
        self.records.guardar_pontuacao(self.hud.jogador, self.hud.modo, self.hud.dificuldade, self.score.obter_pontuacao())
        print("Game Over! Pontuação salva.")
