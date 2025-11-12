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
        import pygame
        from game.map import Mapas

        self.player_name = player_name
        self.modo = modo
        self.dificuldade = dificuldade
        self.velocidade_mult = velocidade_mult
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"Snake - {modo}")

        self.clock = pygame.time.Clock()
        self.running = True

        # área de jogo (para referência)
        self.play_rect = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        # managers
        self.records = RecordsManager()
        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)

        # mapa
        self.mapa = Mapas(mapa_tipo)

        # multiplicador de pontuação
        mult = 1.0
        if dificuldade in ("Rápido", "Rapido"):
            mult = 1.5
        elif dificuldade == "Muito Rápido":
            mult = 2.0
        self.score = Score(multiplicador=mult)

        # --- entidades (spawn seguro) ---
        ocupado = set()

        # cobra (spawn seguro, longe de obstáculos)
        spawn_snake = self.mapa.spawn_seguro(ocupado)
        self.snake = Snake(start_pos=spawn_snake, block_size=BLOCK_SIZE)
        ocupado.update(self.snake.segments)

        # comida (spawn seguro, sem colisão com cobra nem obstáculos)
        spawn_food = self.mapa.spawn_seguro(ocupado)
        self.food = Food(self.play_rect, BLOCK_SIZE)
        self.food.pos = spawn_food

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

        # --- verificar colisões com bordas / obstáculos ---
        resultado = self.mapa.verificar_colisao(self.snake.head_pos())

        if resultado is True:
            self.running = False
            self.game_over()
            return
        elif isinstance(resultado, tuple):
            # aplica teleporte no modo borderless
            self.snake.set_head_pos(resultado)

        # --- verificar colisão consigo mesma ---
        if self.snake.collides_self():
            self.running = False
            self.game_over()
            return

        # --- verificar colisão com comida ---
        # --- verificar colisão com comida ---
        if self.snake.head_pos() == self.food.pos:
            self.snake.grow()
            self.score.adicionar_pontos(10)
            self.hud.atualizar_pontuacao(self.score.obter_pontuacao())

            occupied = set(self.snake.segments)
            obstaculos_pix = set(self.mapa.obstaculos_pixels())  # evita spawn na parede/obstáculo
            self.food.spawn(occupied, obstaculos_pix)



    def draw(self):
        self.screen.fill(BLACK)
        for x, y in self.mapa.obstaculos:
            pygame.draw.rect(self.screen, (100, 100, 100),
                     (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
            
        # desenhar obstáculos
        cor_obst = (100, 100, 100) if self.mapa.tipo == 2 else (60, 60, 60)
        for x, y in self.mapa.obstaculos:
            pygame.draw.rect(self.screen, cor_obst,
                     (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

            
        # draw play area border (optional)
        pygame.draw.rect(self.screen, (40,40,40), pygame.Rect(*self.play_rect), 2)

        # draw map obstacles
        for x, y in self.mapa.obstaculos:
            pygame.draw.rect(self.screen, (100, 100, 100), (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))


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
