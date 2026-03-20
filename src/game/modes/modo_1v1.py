# src/game/modes/modo_1v1.py
import pygame
from game.entities.snake  import Snake
from game.entities.food   import Food
from game.modes.base_mode import BaseModo
import game.config as cfg

_KEYS_P1 = {pygame.K_w: (0,-1), pygame.K_s: (0,1), pygame.K_a: (-1,0), pygame.K_d: (1,0)}
_KEYS_P2 = {pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1), pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0)}


class Modo1v1(BaseModo):
    """Modo multijogador local (2 humanos)."""

    def __init__(self, engine):
        super().__init__(engine)
        self.p1_ready = False
        self.p2_ready = False

        ocupado = set()
        self.snake = Snake(
            start_pos=self.engine.mapa.obter_spawn_player(1),
            block_size=self.engine.block
        )
        ocupado.update(self.snake.segments)

        self.snake2 = Snake(
            start_pos=self.engine.mapa.obter_spawn_player(2),
            block_size=self.engine.block,
            color=cfg.SNAKE2_BODY, head_color=cfg.SNAKE2_HEAD, border_color=cfg.SNAKE2_BORDER
        )
        ocupado.update(self.snake2.segments)

        obst = set(self.engine.mapa.obstaculos_pixels())
        self.foods = []
        for _ in range(2):
            f = Food(self.engine.play_rect, self.engine.block)
            outras = {fd.pos for fd in self.foods if fd.pos}
            f.spawn(ocupado | outras, obst)
            self.foods.append(f)

    def _segmentos_ocupados(self):
        return set(self.snake.segments) | set(self.snake2.segments)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in _KEYS_P1:
            self.snake.set_direction(*_KEYS_P1[event.key])
            self.p1_ready = True
        if event.key in _KEYS_P2:
            self.snake2.set_direction(*_KEYS_P2[event.key])
            self.p2_ready = True

    def update(self):
        if self.p1_ready and self.p2_ready and not self.countdown_active and not self.started:
            self._iniciar_countdown()
        self._tick_countdown()
        if not self.started:
            return

        self.snake.update()
        self.snake2.update()
        h1, h2 = self.snake.head_pos(), self.snake2.head_pos()

        r1, r2  = self.engine.mapa.verificar_colisao(h1), self.engine.mapa.verificar_colisao(h2)
        p1_dead = r1 is True
        p2_dead = r2 is True
        if isinstance(r1, tuple): self.snake.set_head_pos(r1)
        if isinstance(r2, tuple): self.snake2.set_head_pos(r2)

        if h1 == h2:
            self.engine.game_over_1v1("Empate (Choque Frontal)"); return
        if h1 in self.snake2.segments: p1_dead = True
        if h2 in self.snake.segments:  p2_dead = True
        if self.snake.collides_self():  p1_dead = True
        if self.snake2.collides_self(): p2_dead = True

        if p1_dead and p2_dead: self.engine.game_over_1v1("Empate")
        elif p1_dead:           self.engine.game_over_1v1("Vitoria P2")
        elif p2_dead:           self.engine.game_over_1v1(f"Vitoria {self.engine.player_name}")
        if not self.engine.running:
            return

        for comida in self.foods:
            if h1 == comida.pos: self.snake.grow();  self.food_spawn_safe(comida, self.foods)
            if h2 == comida.pos: self.snake2.grow(); self.food_spawn_safe(comida, self.foods)

    def draw(self, surface):
        self.snake.draw(surface)
        self.snake2.draw(surface)
        for f in self.foods:
            try: f.draw(surface)
            except Exception: pass

        f_g = pygame.font.SysFont(None, 80)
        f_p = pygame.font.SysFont(None, 30)
        lw  = surface.get_width()
        cx, cy = lw // 2, surface.get_height() // 2

        if not self.p1_ready or not self.p2_ready:
            msg = f_p.render("Escolham a vossa direcao!", True, (255, 255, 255))
            surface.blit(msg, (cx - msg.get_width()//2, cy - 80))
            s1 = f_p.render("PRONTO!" if self.p1_ready else "P1 (WASD): Espera...", True, (0,255,0))
            surface.blit(s1, (lw//4 - s1.get_width()//2, cy + 20))
            p2t = "PRONTO!" if self.p2_ready else f"{self.engine.player2_name} (Setas): Espera..."
            s2 = f_p.render(p2t, True, (0, 150, 255))
            surface.blit(s2, (3*lw//4 - s2.get_width()//2, cy + 20))
        elif self.countdown_active:
            self._draw_countdown(surface)
