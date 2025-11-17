import pygame
import sys
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE, FPS, BLACK, WHITE
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
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"Snake - {modo}")

        self.clock = pygame.time.Clock()
        self.running = True

        # área de jogo (para referência)
        self.play_rect = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        # managers
        self.records = RecordsManager()
        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)

        # mapa (mantém compatibilidade: Mapas pode receber int tipo ou caminho)
        self.mapa = Mapas(mapa_tipo)

        # usar block size do mapa se existir, senão usar BLOCK_SIZE do config
        self.block = getattr(self.mapa, "block", BLOCK_SIZE) or BLOCK_SIZE

        # multiplicador de pontuação (mantém a tua lógica)
        mult = 1.0
        if dificuldade in ("Rápido", "Rapido"):
            mult = 1.5
        elif dificuldade == "Muito Rápido":
            mult = 2.0
        self.score = Score(multiplicador=mult)

        # --- entidades (spawn seguro) ---
        ocupado_pixels = set()  # conjunto de posições em pixels já ocupadas

        # cobra (spawn seguro, longe de obstáculos)
        spawn_snake = self.mapa.spawn_seguro(ocupado_pixels)
        # garantir que spawn_snake está em múltiplo do block (Mapas já devolve assim)
        self.snake = Snake(start_pos=spawn_snake, block_size=self.block)
        # Snake.segments contém posições em pixels (conforme a tua implementação)
        ocupado_pixels.update(self.snake.segments)

        # comida (spawn seguro, sem colisão com cobra nem obstáculos)
        obstaculos_pix = set(self.mapa.obstaculos_pixels())
        self.food = Food(self.play_rect, self.block)
        # spawn inicial: passar obstáculos para garantir comida fora deles
        self.food.spawn(ocupado_pixels, obstaculos_pix)

        # parâmetros do jogo
        self.base_fps = FPS

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.snake.set_direction(0, -1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.snake.set_direction(0, 1)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.snake.set_direction(-1, 0)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.snake.set_direction(1, 0)
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        self.snake.update()

        # --- verificar colisões com bordas / obstáculos usando o mapa ---
        resultado = self.mapa.verificar_colisao(self.snake.head_pos())

        if resultado is True:
            # colisão fatal
            self.running = False
            self.game_over()
            return
        elif isinstance(resultado, tuple):
            # teleporte (mapa borderless) - resultado já em coords px
            self.snake.set_head_pos(resultado)

        # --- verificar colisão consigo mesma ---
        if self.snake.collides_self():
            self.running = False
            self.game_over()
            return

        # --- verificar colisão com comida ---
        if self.snake.head_pos() == self.food.pos:
            self.snake.grow()
            self.score.adicionar_pontos(10)
            self.hud.atualizar_pontuacao(self.score.obter_pontuacao())

            # preparar novos ocupados + obstáculos em pixels e respawn seguro
            occupied = set(self.snake.segments)
            obstaculos_pix = set(self.mapa.obstaculos_pixels())
            self.food.spawn(occupied, obstaculos_pix)

    def draw(self):
        self.screen.fill(BLACK)

        # desenhar obstáculos (usar block do mapa)
        cor_obst = (120, 120, 120) if getattr(self.mapa, "tipo", 0) == 2 else (80, 80, 80)
        for bx, by in self.mapa.obstaculos:
            pygame.draw.rect(
                self.screen,
                cor_obst,
                (bx * self.block, by * self.block, self.block, self.block)
            )

        # draw play area border (opcional)
        pygame.draw.rect(self.screen, (40, 40, 40), pygame.Rect(*self.play_rect), 2)

        # desenhar comida e cobra (ambas usam mesmo block)
        self.food.draw(self.screen)
        self.snake.draw(self.screen)

        # draw HUD (text)
        self.draw_hud()
        pygame.display.flip()

    def draw_hud(self):
        font = pygame.font.SysFont(None, 24)
        txt = f"{self.hud.jogador} | {self.hud.modo} | {self.hud.dificuldade} | Score: {self.score.obter_pontuacao()} | Map: {getattr(self.mapa, 'tipo', 'custom')}"
        surf = font.render(txt, True, WHITE)
        self.screen.blit(surf, (10, 10))

    def run(self):
        self.running = True
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            # tick com block-based multiplicador de velocidade
            self.clock.tick(int(self.base_fps * self.velocidade_mult))

    def game_over(self):
        # save record
        self.records.guardar_pontuacao(self.hud.jogador, self.hud.modo, self.hud.dificuldade, self.score.obter_pontuacao())
        print("Game Over! Pontuação salva.")
