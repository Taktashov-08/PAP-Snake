# src/game/modes/base_mode.py
"""
Classe base para todos os modos de jogo.
Centraliza logica partilhada: countdown, food_spawn_safe e estrutura do loop.
"""
import pygame


class BaseModo:
    """
    Herda: OgSnake, Modo1v1, PlayerVsAI.
    Fornece:
      - Gestao de countdown (_iniciar_countdown / _tick_countdown / _draw_countdown)
      - Spawn seguro de comida (food_spawn_safe)
    """

    def __init__(self, engine):
        self.engine        = engine
        self.started       = False
        self.terminado     = False
        # Countdown
        self.countdown_active = False
        self.countdown_val    = 3
        self.last_tick        = 0

    # ── Countdown ────────────────────────────────────────────────────────────
    def _iniciar_countdown(self):
        """Arranca o cronometro decrescente."""
        self.countdown_active = True
        self.last_tick = pygame.time.get_ticks()

    def _tick_countdown(self):
        """Avanca o countdown a cada segundo. Define started=True quando chega a zero."""
        if not self.countdown_active:
            return
        agora = pygame.time.get_ticks()
        if agora - self.last_tick >= 1000:
            self.countdown_val -= 1
            self.last_tick = agora
            if self.countdown_val <= 0:
                self.countdown_active = False
                self.started = True

    def _draw_countdown(self, surface):
        """Desenha o numero do countdown no centro do ecra."""
        f = pygame.font.SysFont(None, 80)
        cx = surface.get_width()  // 2
        cy = surface.get_height() // 2
        num = f.render(str(self.countdown_val), True, (255, 200, 0))
        surface.blit(num, (cx - num.get_width() // 2, cy - num.get_height() // 2))

    # ── Food spawn seguro ─────────────────────────────────────────────────────
    def _segmentos_ocupados(self):
        """Subclasses devem sobrepor: retorna set() com posicoes px de todas as cobras."""
        raise NotImplementedError

    def food_spawn_safe(self, food_obj, foods_list):
        """Spawn seguro: evita cobras, obstaculos e outra comida."""
        occupied = self._segmentos_ocupados()
        for f in foods_list:
            if f is not food_obj and f.pos:
                occupied.add(f.pos)
        food_obj.spawn(occupied, set(self.engine.mapa.obstaculos_pixels()))

    # ── Interface publica (podem ser sobrepostos) ─────────────────────────────
    def handle_event(self, event): pass
    def update(self):              pass
    def draw(self, surface):       pass
