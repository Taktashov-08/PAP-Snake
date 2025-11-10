import pygame
import sys
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE, FPS, BLACK, WHITE
from game.snake import Snake
from game.food import Food
from game.records import RecordsManager
from game.hud import HUD
from game.score import Score


class Game: 
    def __init__(self, player_name="Player", modo="OG Snake", dificuldade="Normal", velocidade_mult=1.0, mapa_tipo=1):
        self.player_name = player_name
        self.modo = modo
        self.dificuldade = dificuldade
        self.velocidade_mult = velocidade_mult  # 👈 agora o menu pode enviar este valor
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.clock = pygame.time.Clock()
        self.running = True

        # área de jogo
        self.play_rect = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        # managers
        self.records = RecordsManager()
        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)

        from game.map import Mapas
        self.mapa = Mapas(mapa_tipo)

        # multiplicador de pontuação (mantém a tua lógica interna)
        mult = 1.0
        if dificuldade in ("Rápido", "Rapido"):
            mult = 2.0
        elif dificuldade == "Muito Rápido":
            mult = 3.0

        self.score = Score(multiplicador=mult)

        # entidades
        start = (BLOCK_SIZE * 5, BLOCK_SIZE * 5)
        self.snake = Snake(start_pos=start, block_size=BLOCK_SIZE)
        self.food = Food(self.play_rect, BLOCK_SIZE)

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

        # check wall collision
        if self.snake.collides_rect(self.play_rect):
            self.running = False
            self.game_over()
            return

        # check self collision
        if self.snake.collides_self():
            self.running = False
            self.game_over()
            return

        # check food collision
        if self.snake.head_pos() == self.food.pos:
            self.snake.grow()
            self.score.adicionar_pontos(10)  # base points
            self.hud.atualizar_pontuacao(self.score.obter_pontuacao())
            occupied = set(self.snake.segments)
            self.food.spawn(occupied)

    def draw(self):
        self.screen.fill(BLACK)
        for x, y in self.mapa.obstaculos:
            pygame.draw.rect(self.screen, (100, 100, 100),
                     (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
            
        # draw play area border (optional)
        pygame.draw.rect(self.screen, (40,40,40), pygame.Rect(*self.play_rect), 2)

        self.food.draw(self.screen)
        self.snake.draw(self.screen)
        # draw HUD (text)
        self.draw_hud()
        pygame.display.flip()

    def draw_hud(self):
        font = pygame.font.SysFont(None, 24)
        txt = f"{self.hud.jogador} | {self.hud.modo} | {self.hud.dificuldade} | Score: {self.score.obter_pontuacao()}"
        surf = font.render(txt, True, WHITE)
        self.screen.blit(surf, (10, 10))

    def run(self):
        self.running = True
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            # FPS scaled by multiplier? use base fps for simplicity
            self.clock.tick(int(self.base_fps * self.velocidade_mult))
        
    def game_over(self):
        # save record
        self.records.guardar_pontuacao(self.hud.jogador, self.hud.modo, self.hud.dificuldade, self.score.obter_pontuacao())
        print("Game Over! Pontuação salva.")
