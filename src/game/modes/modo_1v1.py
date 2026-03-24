# src/game/modes/modo_1v1.py
"""
Modo multijogador local (2 humanos) com efeitos de partículas
e flash de morte antes do ecrã de resultado.
"""
from __future__ import annotations

import pygame

from game.entities.snake  import Snake
from game.entities.food   import Food
from game.modes.base_mode import BaseModo
from game.config          import FOOD_COLOR
import game.config as cfg

_KEYS_P1: dict = {
    pygame.K_w: (0,-1), pygame.K_s: (0,1),
    pygame.K_a: (-1,0), pygame.K_d: (1,0),
}
_KEYS_P2: dict = {
    pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1),
    pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0),
}


class Modo1v1(BaseModo):
    """Modo multijogador local (2 humanos)."""

    def __init__(self, engine) -> None:
        super().__init__(engine)
        self.p1_ready = False
        self.p2_ready = False
        # Sinaliza qual(ais) jogadores morreu — usado no delay de morte
        self._p1_dead_pending = False
        self._p2_dead_pending = False
        self._death_result    = ""

        ocupado = set()

        self.snake = Snake(
            start_pos=self.engine.mapa.obter_spawn_player(1),
            block_size=self.engine.block,
        )
        ocupado.update(self.snake.segments)

        self.snake2 = Snake(
            start_pos=self.engine.mapa.obter_spawn_player(2),
            block_size=self.engine.block,
            color=cfg.SNAKE2_BODY,
            head_color=cfg.SNAKE2_HEAD,
            border_color=cfg.SNAKE2_BORDER,
        )
        ocupado.update(self.snake2.segments)

        obst = set(self.engine.mapa.obstaculos_pixels())
        self.foods = []
        for _ in range(2):
            f = Food(self.engine.play_rect, self.engine.block)
            outras = {fd.pos for fd in self.foods if fd.pos}
            f.spawn(ocupado | outras, obst)
            self.foods.append(f)

    # ── Segmentos ocupados ────────────────────────────────────────────────────

    def _segmentos_ocupados(self) -> set:
        return set(self.snake.segments) | set(self.snake2.segments)

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in _KEYS_P1:
            self.snake.set_direction(*_KEYS_P1[event.key])
            self.p1_ready = True
        if event.key in _KEYS_P2:
            self.snake2.set_direction(*_KEYS_P2[event.key])
            self.p2_ready = True

    # ── Update lógica ─────────────────────────────────────────────────────────

    def update(self) -> None:
        # Delay de morte em andamento
        if self._dying:
            done1 = self.snake.tick_death_flash()  if self._p1_dead_pending else True
            done2 = self.snake2.tick_death_flash() if self._p2_dead_pending else True
            self._death_timer += 1
            from game.modes.base_mode import _DEATH_DELAY_TICKS
            if (done1 and done2) or self._death_timer >= _DEATH_DELAY_TICKS:
                self._dying    = False
                self.terminado = True
                self.engine.game_over_1v1(self._death_result)
            return

        # Aguardar ambos prontos e countdown
        if self.p1_ready and self.p2_ready and not self.countdown_active and not self.started:
            self._iniciar_countdown()
        self._tick_countdown()
        if not self.started:
            return

        self.snake.update()
        self.snake2.update()
        h1, h2 = self.snake.head_pos(), self.snake2.head_pos()

        r1, r2  = (self.engine.mapa.verificar_colisao(h1),
                   self.engine.mapa.verificar_colisao(h2))
        p1_dead = r1 is True
        p2_dead = r2 is True
        if isinstance(r1, tuple): self.snake.set_head_pos(r1)
        if isinstance(r2, tuple): self.snake2.set_head_pos(r2)

        if h1 == h2:
            self._trigger_death(True, True, "Empate (Choque Frontal)")
            return
        if h1 in self.snake2.segments:  p1_dead = True
        if h2 in self.snake.segments:   p2_dead = True
        if self.snake.collides_self():  p1_dead = True
        if self.snake2.collides_self(): p2_dead = True

        if p1_dead or p2_dead:
            if p1_dead and p2_dead:
                resultado = "Empate"
            elif p1_dead:
                resultado = "Vitoria P2"
            else:
                resultado = f"Vitoria {self.engine.player_name}"
            self._trigger_death(p1_dead, p2_dead, resultado)
            return

        # Comer comida
        for comida in self.foods:
            if h1 == comida.pos:
                self.snake.grow()
                self.engine.particles.emit_food_burst(
                    comida.pos, FOOD_COLOR, self.engine.block
                )
                self.food_spawn_safe(comida, self.foods)
            if h2 == comida.pos:
                self.snake2.grow()
                self.engine.particles.emit_food_burst(
                    comida.pos, FOOD_COLOR, self.engine.block
                )
                self.food_spawn_safe(comida, self.foods)

    def _trigger_death(self, p1: bool, p2: bool, resultado: str) -> None:
        """Emite partículas e inicia delay de morte para um ou ambos os jogadores."""
        self._dying            = True
        self._death_timer      = 0
        self._death_result     = resultado
        self._p1_dead_pending  = p1
        self._p2_dead_pending  = p2

        if p1:
            self.engine.particles.emit_death(
                self.snake.segments, self.snake.body_color, self.engine.block
            )
            self.snake.start_death_flash()
        if p2:
            self.engine.particles.emit_death(
                self.snake2.segments, self.snake2.body_color, self.engine.block
            )
            self.snake2.start_death_flash()

    # ── Update visual ─────────────────────────────────────────────────────────

    def visual_update(self, dt: float) -> None:
        for f in self.foods:
            f.update(dt)

    # ── Desenho ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        self.snake.draw(surface)
        self.snake2.draw(surface)
        for f in self.foods:
            try:
                f.draw(surface)
            except Exception:
                pass

        f_g  = pygame.font.SysFont(None, 80)
        f_p  = pygame.font.SysFont(None, 30)
        lw   = surface.get_width()
        cx   = lw // 2
        cy   = surface.get_height() // 2

        if not self.p1_ready or not self.p2_ready:
            msg = f_p.render("Escolham a vossa direção!", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width() // 2, cy - 80))
            s1 = f_p.render(
                "PRONTO!" if self.p1_ready else "P1 (WASD): Espera...",
                True, (0, 255, 0),
            )
            surface.blit(s1, (lw // 4 - s1.get_width() // 2, cy + 20))
            p2t = ("PRONTO!" if self.p2_ready
                   else f"{self.engine.player2_name} (Setas): Espera...")
            s2 = f_p.render(p2t, True, (0, 150, 255))
            surface.blit(s2, (3 * lw // 4 - s2.get_width() // 2, cy + 20))
        elif self.countdown_active:
            self._draw_countdown(surface)