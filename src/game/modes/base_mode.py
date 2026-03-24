# src/game/modes/base_mode.py
"""
Classe base para todos os modos de jogo.

Centraliza:
  - Countdown com renderização
  - Spawn seguro de comida
  - Hook visual_update(dt) para animações a 60 fps
  - Lógica de morte com flash antes do game_over
"""
from __future__ import annotations

import pygame


# Ticks de lógica aguardados após a morte antes de chamar game_over.
# A 7 FPS base ≈ 0.57 s de animação de flash.
_DEATH_DELAY_TICKS: int = 4


class BaseModo:
    """
    Superclasse de OgSnake, Modo1v1 e PlayerVsAI.

    Fornece:
      _iniciar_countdown / _tick_countdown / _draw_countdown
      food_spawn_safe
      visual_update(dt)          — sobrepor para animar comida/outros
      _iniciar_morte(cobra)      — inicia flash e delay antes do game_over
      _tick_morte()              — deve ser chamado em update() quando em _dying
    """

    def __init__(self, engine) -> None:
        self.engine    = engine
        self.started   = False
        self.terminado = False

        # Countdown
        self.countdown_active: bool = False
        self.countdown_val:    int  = 3
        self.last_tick:        int  = 0

        # Estado de morte com delay
        self._dying:       bool = False
        self._death_timer: int  = 0

    # ── Countdown ─────────────────────────────────────────────────────────────

    def _iniciar_countdown(self) -> None:
        """Arranca o cronómetro decrescente de 3 a 1."""
        self.countdown_active = True
        self.last_tick = pygame.time.get_ticks()

    def _tick_countdown(self) -> None:
        """Avança o countdown; define started=True quando chega a zero."""
        if not self.countdown_active:
            return
        agora = pygame.time.get_ticks()
        if agora - self.last_tick >= 1000:
            self.countdown_val -= 1
            self.last_tick = agora
            if self.countdown_val <= 0:
                self.countdown_active = False
                self.started          = True

    def _draw_countdown(self, surface: pygame.Surface) -> None:
        """Desenha o número do countdown centrado no ecrã."""
        f   = pygame.font.SysFont(None, 80)
        cx  = surface.get_width()  // 2
        cy  = surface.get_height() // 2
        num = f.render(str(self.countdown_val), True, (255, 200, 0))
        surface.blit(num, num.get_rect(center=(cx, cy)))

    # ── Morte com flash ────────────────────────────────────────────────────────

    def _iniciar_morte(self, cobra) -> None:
        """
        Inicia a sequência de morte: flash na cobra + delay antes de game_over.
        `cobra` deve ser uma instância de Snake que suporte start_death_flash().
        """
        if self._dying:
            return   # evita re-entrada
        self._dying       = True
        self._death_timer = 0
        cobra.start_death_flash()

    def _tick_morte(self, cobra, callback) -> None:
        """
        Deve ser chamado em update() enquanto _dying é True.
        Avança o flash da cobra; quando termina chama `callback` (ex: game_over).
        """
        if not self._dying:
            return
        done = cobra.tick_death_flash()
        self._death_timer += 1
        if done or self._death_timer >= _DEATH_DELAY_TICKS:
            self._dying    = False
            self.terminado = True
            callback()

    # ── Spawn seguro de comida ─────────────────────────────────────────────────

    def _segmentos_ocupados(self) -> set:
        """Subclasses devem sobrepor — retorna set de posições px de todas as cobras."""
        raise NotImplementedError

    def food_spawn_safe(self, food_obj, foods_list) -> None:
        """Spawn seguro: evita cobras, obstáculos e outra comida existente."""
        occupied = self._segmentos_ocupados()
        for f in foods_list:
            if f is not food_obj and f.pos:
                occupied.add(f.pos)
        food_obj.spawn(occupied, set(self.engine.mapa.obstaculos_pixels()))

    # ── Hook visual (animações independentes de FPS de lógica) ────────────────

    def visual_update(self, dt: float) -> None:
        """
        Chamado a ~60 fps pelo engine para animar elementos visuais
        (comida, boosts, etc.) de forma independente do FPS de lógica.
        Subclasses devem sobrepor para chamar food.update(dt).
        """
        pass

    # ── Interface pública (sobreposta pelas subclasses) ───────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass