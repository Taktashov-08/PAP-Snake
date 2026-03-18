# Descrição: Lógica do modo "OG Snake" (Clássico).
# Este modo foca-se na jogabilidade tradicional de um jogador com sistema de pontuação.
# TipoDeJogo/OgSnake.py
import pygame
from game.snake import Snake
from game.food import Food

class OgSnake:
    def __init__(self, engine):
        self.engine = engine # Referência ao motor principal para aceder ao mapa, HUD e score
        self.started = False
        
        # Conjunto de pixéis ocupados para evitar spawns inválidos no início
        ocupado_pixels = set()
        
        # ── Configuração do Jogador ───────────────────────────────
        spawn_p1 = self.engine.mapa.obter_spawn_player(1)
        self.snake = Snake(start_pos=spawn_p1, block_size=self.engine.block)
        self.snake.color = (0, 255, 0) # Cor Verde clássica
        ocupado_pixels.update(self.snake.segments)
        
        # ── Configuração da Comida ────────────────────────────────
        self.foods = []
        # No modo clássico, apenas uma comida aparece de cada vez
        f = Food(self.engine.play_rect, self.engine.block)
        obstaculos_pix = set(self.engine.mapa.obstaculos_pixels())
        
        # Garante que a primeira comida não nasce em cima da cobra ou de paredes
        f.spawn(ocupado_pixels, obstaculos_pix)
        self.foods.append(f)

    def handle_event(self, event):
        """Gere os controlos da cobra e inicia o movimento ao carregar numa tecla."""
        if event.type == pygame.KEYDOWN:
            # O jogo só começa "de facto" quando o jogador prime uma tecla de direção
            if event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                self.started = True
            
            # Atualização da direção da cobra
            if event.key == pygame.K_w: self.snake.set_direction(0, -1)
            elif event.key == pygame.K_s: self.snake.set_direction(0, 1)
            elif event.key == pygame.K_a: self.snake.set_direction(-1, 0)
            elif event.key == pygame.K_d: self.snake.set_direction(1, 0)

    def update(self):
        """Atualiza o movimento, verifica colisões e gere a pontuação."""
        if not self.started:
            return

        self.snake.update()

        # ── Verificação de Colisões ──
        head1 = self.snake.head_pos()
        res1 = self.engine.mapa.verificar_colisao(head1)

        # Se o resultado for True, atingiu uma parede ou obstáculo letal
        if res1 is True:
            self.engine.running = False
            self.engine.game_over()
            return
        
        # Se o resultado for um tuplo, o jogador entrou num portal (Teleporte)
        elif isinstance(res1, tuple):
            self.snake.set_head_pos(res1)

        # Colisão com o próprio corpo (Auto-canibalismo)
        if self.snake.collides_self():
            self.engine.running = False
            self.engine.game_over()
            return

        # ── Lógica de Alimentação ──
        for comida in self.foods:
            if head1 == comida.pos:
                self.snake.grow()
                # Adiciona 10 pontos e atualiza a interface (HUD)
                self.engine.score.adicionar_pontos(10)
                self.engine.hud.atualizar_pontuacao(self.engine.score.obter_pontuacao())
                # Faz spawn de uma nova comida num local seguro
                self.food_spawn_safe(comida)

    def food_spawn_safe(self, food_object):
        """Garante que a nova comida não aparece dentro do corpo da cobra ou em paredes."""
        occupied = set(self.snake.segments)
        # Considera outras comidas (caso o modo fosse alterado para ter várias)
        for f in self.foods:
            if f != food_object and f.pos:
                occupied.add(f.pos)
        
        obstaculos = set(self.engine.mapa.obstaculos_pixels())
        food_object.spawn(occupied, obstaculos)

    def draw(self, surface):
        """Renderiza os elementos específicos deste modo de jogo."""
        self.snake.draw(surface)
        for f in self.foods:
            try: 
                f.draw(surface)
            except: 
                pass