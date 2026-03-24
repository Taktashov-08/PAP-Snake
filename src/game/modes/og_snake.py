# src/game/modes/og_snake.py
"""
Modo clássico de um jogador com efeitos de partículas:
  - Explosão de comida ao comer
  - Flash e explosão de morte antes do game_over
"""
from __future__ import annotations

import pygame

from game.entities.snake  import Snake
from game.entities.food   import Food
from game.modes.base_mode import BaseModo
from game.config          import FOOD_COLOR

# Mapeamento tecla → direcção (dx, dy)
_KEYS: dict = {
    pygame.K_w:     (0, -1), pygame.K_UP:    (0, -1),
    pygame.K_s:     (0,  1), pygame.K_DOWN:  (0,  1),
    pygame.K_a:     (-1, 0), pygame.K_LEFT:  (-1, 0),
    pygame.K_d:     (1,  0), pygame.K_RIGHT: (1,  0),
}


class OgSnake(BaseModo):
    """Modo clássico de um jogador."""

    def __init__(self, engine) -> None:
        super().__init__(engine)
        spawn      = self.engine.mapa.obter_spawn_player(1)
        self.snake = Snake(start_pos=spawn, block_size=self.engine.block)

        obst = set(self.engine.mapa.obstaculos_pixels())
        f    = Food(self.engine.play_rect, self.engine.block)
        f.spawn(set(self.snake.segments), obst)
        self.foods = [f]

    # ── Segmentos ocupados (para spawn seguro de comida) ──────────────────────

    def _segmentos_ocupados(self) -> set:
        return set(self.snake.segments)

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in _KEYS:
            self.snake.set_direction(*_KEYS[event.key])
            self.started = True

    # ── Update de lógica (chamado a FPS de jogo fixo) ─────────────────────────

    def update(self) -> None:
        # Aguardar flash de morte
        if self._dying:
            self._tick_morte(
                self.snake,
                callback=self.engine.game_over,
            )
            return

        if not self.started:
            return

        self.snake.update()
        head = self.snake.head_pos()

        # Colisão com mapa
        res = self.engine.mapa.verificar_colisao(head)
        if res is True:
            self._on_death()
            return
        if isinstance(res, tuple):
            self.snake.set_head_pos(res)

        # Auto-colisão
        if self.snake.collides_self():
            self._on_death()
            return

        # Comer comida
        for comida in self.foods:
            if head == comida.pos:
                self.snake.grow()
                pts = 10
                self.engine.score.adicionar_pontos(pts)
                self.engine.hud.atualizar_pontuacao(
                    self.engine.score.obter_pontuacao()
                )
                # Efeito de partículas
                self.engine.particles.emit_food_burst(
                    comida.pos, FOOD_COLOR, self.engine.block
                )
                self.food_spawn_safe(comida, self.foods)

    def _on_death(self) -> None:
        """Emite partículas de morte e inicia o delay de flash."""
        self.engine.particles.emit_death(
            self.snake.segments, self.snake.body_color, self.engine.block
        )
        self._iniciar_morte(self.snake)

    # ── Update visual (chamado a 60 fps) ──────────────────────────────────────

    def visual_update(self, dt: float) -> None:
        """Anima a comida de forma suave e independente do FPS de lógica."""
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