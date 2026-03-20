# src/game/modes/og_snake.py
import pygame
from game.entities.snake  import Snake
from game.entities.food   import Food
from game.modes.base_mode import BaseModo

# Mapeamento de tecla -> (dx, dy)
_KEYS = {
    pygame.K_w: (0, -1), pygame.K_UP:    (0, -1),
    pygame.K_s: (0,  1), pygame.K_DOWN:  (0,  1),
    pygame.K_a: (-1, 0), pygame.K_LEFT:  (-1, 0),
    pygame.K_d: (1,  0), pygame.K_RIGHT: (1,  0),
}


class OgSnake(BaseModo):
    """Modo classico de um jogador."""

    def __init__(self, engine):
        super().__init__(engine)
        spawn = self.engine.mapa.obter_spawn_player(1)
        self.snake = Snake(start_pos=spawn, block_size=self.engine.block)
        obst = set(self.engine.mapa.obstaculos_pixels())
        f = Food(self.engine.play_rect, self.engine.block)
        f.spawn(set(self.snake.segments), obst)
        self.foods = [f]

    def _segmentos_ocupados(self):
        return set(self.snake.segments)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in _KEYS:
            self.snake.set_direction(*_KEYS[event.key])
            self.started = True

    def update(self):
        if not self.started:
            return
        self.snake.update()
        head = self.snake.head_pos()
        res  = self.engine.mapa.verificar_colisao(head)
        if res is True:
            self.engine.game_over(); return
        if isinstance(res, tuple):
            self.snake.set_head_pos(res)
        if self.snake.collides_self():
            self.engine.game_over(); return
        for comida in self.foods:
            if head == comida.pos:
                self.snake.grow()
                self.engine.score.adicionar_pontos(10)
                self.engine.hud.atualizar_pontuacao(self.engine.score.obter_pontuacao())
                self.food_spawn_safe(comida, self.foods)

    def draw(self, surface):
        self.snake.draw(surface)
        for f in self.foods:
            try: f.draw(surface)
            except Exception: pass
