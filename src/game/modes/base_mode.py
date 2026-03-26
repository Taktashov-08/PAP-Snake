# src/game/modes/base_mode.py
"""
Classe base para todos os modos de jogo.

Centraliza:
  - Countdown com renderização
  - Spawn seguro com zona de exclusão por distância Manhattan
  - Hook visual_update(dt) para animações a 60 fps
  - Morte com flash antes do game_over
  - hud_info() → dict com dados para o HUD lateral
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pygame

_DEATH_DELAY_TICKS: int = 4
_SPAWN_MIN_DIST:    int = 4


class BaseModo:
    """
    Superclasse de OgSnake, Modo1v1 e PlayerVsAI.

    Subclasses devem sobrepor:
        _segmentos_ocupados() → set
        _snake_heads()        → list
        hud_info()            → dict
        visual_update(dt)
        handle_event(event)
        update()
        draw(surface)
    """

    def __init__(self, engine) -> None:
        self.engine    = engine
        self.started   = False
        self.terminado = False

        self.countdown_active: bool = False
        self.countdown_val:    int  = 3
        self.last_tick:        int  = 0

        self._dying:       bool = False
        self._death_timer: int  = 0

    # ── Countdown ─────────────────────────────────────────────────────────────

    def _iniciar_countdown(self) -> None:
        self.countdown_active = True
        self.last_tick = pygame.time.get_ticks()

    def _tick_countdown(self) -> None:
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
        f   = pygame.font.SysFont(None, 80)
        cx  = surface.get_width()  // 2
        cy  = surface.get_height() // 2
        num = f.render(str(self.countdown_val), True, (255, 200, 0))
        surface.blit(num, num.get_rect(center=(cx, cy)))

    # ── Morte com flash ────────────────────────────────────────────────────────

    def _iniciar_morte(self, cobra) -> None:
        if self._dying:
            return
        self._dying       = True
        self._death_timer = 0
        cobra.start_death_flash()

    def _tick_morte(self, cobra, callback) -> None:
        if not self._dying:
            return
        done = cobra.tick_death_flash()
        self._death_timer += 1
        if done or self._death_timer >= _DEATH_DELAY_TICKS:
            self._dying    = False
            self.terminado = True
            callback()

    # ── Spawn seguro ──────────────────────────────────────────────────────────

    def _segmentos_ocupados(self) -> set:
        raise NotImplementedError

    def _snake_heads(self) -> List[Tuple[int, int]]:
        return []

    def _zona_exclusao(self) -> set:
        """Blocos a menos de _SPAWN_MIN_DIST Manhattan de qualquer cabeça."""
        b    = self.engine.block
        dist = _SPAWN_MIN_DIST
        zona: set = set()
        for hx, hy in self._snake_heads():
            for dx in range(-dist, dist + 1):
                for dy in range(-dist, dist + 1):
                    if abs(dx) + abs(dy) <= dist:
                        zona.add((hx + dx * b, hy + dy * b))
        return zona

    def food_spawn_safe(self, food_obj, foods_list) -> None:
        """Spawn que evita cobras, zona de exclusão, outros itens e obstáculos."""
        occupied  = self._segmentos_ocupados()
        occupied |= self._zona_exclusao()
        for f in foods_list:
            if f is not food_obj and f.pos:
                occupied.add(f.pos)
        food_obj.spawn(occupied, set(self.engine.mapa.obstaculos_pixels()))

    # ── HUD info ──────────────────────────────────────────────────────────────

    def hud_info(self) -> Dict[str, Any]:
        """
        Devolve um dicionário com toda a informação que o HUD lateral precisa.
        Subclasses sobrepõem com os dados do seu estado.

        Chaves comuns:
          score         int   — pontuação do jogador
          length        int   — comprimento da cobra do jogador
          max_length    int   — comprimento máximo esperado (escala da barra)
          fps_ref       int   — fps de referência para calcular segundos de boost
        """
        return {
            "score":      self.engine.score.obter_pontuacao(),
            "length":     1,
            "max_length": 60,
            "fps_ref":    max(1, int(self.engine.base_fps
                                     * self.engine.velocidade_mult)),
        }

    # ── Hooks de subclasse ────────────────────────────────────────────────────

    def visual_update(self, dt: float) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass