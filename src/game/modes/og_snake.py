# src/game/modes/og_snake.py
"""Modo clássico de um jogador."""
from __future__ import annotations

import pygame

from game.entities.snake  import Snake
from game.entities.food   import Food
from game.modes.base_mode import BaseModo
from game.config          import FOOD_COLOR

_KEYS: dict = {
    pygame.K_w:     (0, -1), pygame.K_UP:    (0, -1),
    pygame.K_s:     (0,  1), pygame.K_DOWN:  (0,  1),
    pygame.K_a:     (-1, 0), pygame.K_LEFT:  (-1, 0),
    pygame.K_d:     (1,  0), pygame.K_RIGHT: (1,  0),
}


class OgSnake(BaseModo):

    def __init__(self, engine) -> None:
        super().__init__(engine)
        self.snake = Snake(
            start_pos=engine.mapa.obter_spawn_player(1),
            block_size=engine.block,
        )
        obst = set(engine.mapa.obstaculos_pixels())
        f    = Food(engine.play_rect, engine.block)
        f.spawn(set(self.snake.segments), obst)
        self.foods = [f]

    # ── BaseModo ──────────────────────────────────────────────────────────────

    def _segmentos_ocupados(self) -> set:
        return set(self.snake.segments)

    def _snake_heads(self) -> list:
        return [self.snake.head_pos()]

    def hud_info(self) -> dict:
        return {
            "score":      self.engine.score.obter_pontuacao(),
            "length":     len(self.snake.segments),
            "max_length": 60,
            "fps_ref":    max(1, int(self.engine.base_fps
                                     * self.engine.velocidade_mult)),
        }

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in _KEYS:
            self.snake.set_direction(*_KEYS[event.key])
            self.started = True

    # ── Lógica ────────────────────────────────────────────────────────────────

    def update(self) -> None:
        if self._dying:
            self._tick_morte(self.snake, self.engine.game_over)
            return
        if not self.started:
            return

        self.snake.update()
        head = self.snake.head_pos()

        res = self.engine.mapa.verificar_colisao(head)
        if res is True:
            self._on_death(); return
        if isinstance(res, tuple):
            self.snake.set_head_pos(res)

        if self.snake.collides_self():
            self._on_death(); return

        for comida in self.foods:
            if head == comida.pos:
                self.snake.grow()
                pts = self.engine.score.obter_pontuacao() + 10
                self.engine.score.adicionar_pontos(10)
                self.engine.hud.set_score(
                    self.engine.score.obter_pontuacao()
                )
                self.engine.particulas.emit_food_burst(
                    comida.pos, FOOD_COLOR, self.engine.block
                )
                self.food_spawn_safe(comida, self.foods)

    def _on_death(self) -> None:
        self.engine.particulas.emit_death(
            self.snake.segments, self.snake.body_color, self.engine.block
        )
        self.engine.trigger_shake(intensity=7.0, duration=0.32)
        self._iniciar_morte(self.snake)

    def visual_update(self, dt: float) -> None:
        for f in self.foods:
            f.update(dt)

    # ── Desenho ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        self.snake.draw(surface)
        for f in self.foods:
            try:
                f.draw(surface)
            except Exception:
                pass