# src/game/core/engine.py
"""
Orquestrador principal do jogo.

Mudanças desta versão (HUD lateral):
  - logical_w  = SCREEN_WIDTH + SIDEBAR_W  (área de jogo + painel)
  - play_rect  = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)  — apenas área de jogo
  - Sem barra de topo (HUD_HEIGHT = 0)
  - hud.update(dt) chamado no loop visual
  - draw_logical chama hud.draw_sidebar(surface, info, modo)
  - ScreenShake integrado
"""
from __future__ import annotations

import random

import pygame

import game.config as cfg
from game.config             import FPS
from game.core.records       import RecordsManager
from game.ui.hud             import HUD
from game.core.score         import Score
from game.maps.map           import Mapas
from game.core.assets        import AssetsManager
from game.entities.particulas import ParticleSystem
from game.modes.og_snake     import OgSnake
from game.modes.modo_1v1     import Modo1v1
from game.maps.map_renderer  import MapRenderer
from game.modes.player_vs_ai import PlayerVsAI
from game.ui                 import ui_utils
from game.ui.ecras           import ecra_fim_jogo, ecra_fim_1v1, ecra_fim_vsai

TARGET_VFX_FPS: int = 60


# ── Screen Shake ──────────────────────────────────────────────────────────────

class ScreenShake:
    """Vibração da câmara com decaimento linear."""

    def __init__(self) -> None:
        self._intensity: float = 0.0
        self._duration:  float = 0.0
        self._elapsed:   float = 0.0

    def trigger(self, intensity: float = 8.0, duration: float = 0.35) -> None:
        self._intensity = intensity
        self._duration  = duration
        self._elapsed   = 0.0

    def update(self, dt: float) -> None:
        if self._elapsed < self._duration:
            self._elapsed += dt

    @property
    def offset(self):
        if self._elapsed >= self._duration or self._intensity <= 0:
            return (0, 0)
        t   = 1.0 - (self._elapsed / self._duration)
        mag = max(1, int(self._intensity * t))
        return (random.randint(-mag, mag), random.randint(-mag, mag))


# ── Engine ────────────────────────────────────────────────────────────────────

class Game:
    """Orquestra a janela, o loop principal e os modos de jogo."""

    def __init__(self, player_name: str = "Player",
                 modo: str = cfg.MODO_OG_SNAKE,
                 dificuldade: str = "Normal",
                 velocidade_mult: float = 1.0,
                 mapa_tipo=1,
                 player2_name: str = "Player 2") -> None:

        self.player_name     = player_name
        self.player2_name    = player2_name
        self.modo            = modo
        self.dificuldade     = dificuldade
        self.velocidade_mult = velocidade_mult
        self.jogar_de_novo   = False

        pygame.init()
        pygame.mixer.init()

        try:
            cur = pygame.display.get_surface()
            cw, ch = cur.get_size() if cur else (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        except Exception:
            cw, ch = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        # ── Dimensões lógicas ─────────────────────────────────────────────
        # A superfície lógica inclui a área de jogo + painel lateral.
        # O mapa e as entidades usam apenas play_rect (sem sidebar).
        self.logical_w     = cfg.SCREEN_WIDTH + cfg.SIDEBAR_W
        self.logical_h     = cfg.SCREEN_HEIGHT
        self._logical_size = (self.logical_w, self.logical_h)

        # Ajustar tamanho da janela para incluir a sidebar
        win_w = cw + cfg.SIDEBAR_W if cw == cfg.SCREEN_WIDTH else cw
        self.screen = pygame.display.set_mode((win_w, ch), pygame.RESIZABLE)

        self.surface   = pygame.Surface(self._logical_size)
        self.block     = cfg.BLOCK_SIZE
        # Área de jogo: apenas a porção esquerda (sem sidebar)
        self.play_rect = (0, 0, cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.clock     = pygame.time.Clock()
        self.running   = True

        self.records      = RecordsManager()
        self.hud          = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.mapa         = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)
        self.assets       = AssetsManager()
        self.particles    = ParticleSystem()
        self.shake        = ScreenShake()

        mult          = cfg.DIFICULDADES.get(dificuldade, 1.0)
        self.score    = Score(multiplicador=mult)
        self.base_fps = FPS

        if   self.modo == cfg.MODO_1V1:   self.modo_atual = Modo1v1(self)
        elif self.modo == cfg.MODO_VS_AI: self.modo_atual = PlayerVsAI(self)
        else:                             self.modo_atual = OgSnake(self)

    # ── API pública ───────────────────────────────────────────────────────────

    def trigger_shake(self, intensity: float = 8.0, duration: float = 0.35) -> None:
        self.shake.trigger(intensity, duration)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def handle_events(self, events: list) -> None:
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False; return
            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (ev.w, ev.h), pygame.RESIZABLE
                )
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False; return
            self.modo_atual.handle_event(ev)

    def update(self) -> None:
        self.modo_atual.update()

    def draw_logical(self) -> None:
        """
        Renderiza:
          1. Grelha + mapa + entidades na área de jogo (0 … SCREEN_WIDTH)
          2. Partículas por cima
          3. Painel lateral (SCREEN_WIDTH … SCREEN_WIDTH + SIDEBAR_W)
        """
        self.surface.fill(cfg.BG_DARK)

        # Grelha decorativa (apenas na área de jogo)
        for x in range(0, cfg.SCREEN_WIDTH, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (x, 0), (x, cfg.SCREEN_HEIGHT))
        for y in range(0, cfg.SCREEN_HEIGHT, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (0, y), (cfg.SCREEN_WIDTH, y))

        self.map_renderer.draw(self.surface)
        self.modo_atual.draw(self.surface)
        self.particles.draw(self.surface)

        # Painel lateral — passa o dict de info do modo actual
        self.hud.draw_sidebar(
            self.surface,
            self.modo_atual.hud_info(),
            self.modo,
        )

    # ── Loop principal ────────────────────────────────────────────────────────

    def run(self) -> bool:
        """
        Loop com separação lógica/visual.
          Visual  → TARGET_VFX_FPS (60 fps) — partículas, shake, HUD animado
          Lógica  → base_fps × velocidade_mult (acumulador de timestep fixo)
        """
        logic_interval: float = 1000.0 / max(
            1.0, self.base_fps * self.velocidade_mult
        )
        accumulator: float = 0.0

        while self.running:
            dt_ms = self.clock.tick(TARGET_VFX_FPS)
            dt    = min(dt_ms / 1000.0, 0.1)

            events = pygame.event.get()
            self.handle_events(events)
            if not self.running:
                break

            # Lógica a timestep fixo
            accumulator += dt_ms
            while accumulator >= logic_interval and self.running:
                self.update()
                accumulator -= logic_interval

            # Visuais a cada frame
            self.particles.update(dt)
            self.shake.update(dt)
            self.hud.update(dt)                      # ← animação do score pop
            self.modo_atual.visual_update(dt)

            self.draw_logical()
            self._blit_with_shake()

        try:
            pygame.display.set_mode(
                (cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT),
                pygame.RESIZABLE,
            )
        except Exception:
            pass

        return self.jogar_de_novo

    def _blit_with_shake(self) -> None:
        """Escala e blita a superfície lógica com offset de screen shake."""
        win_w, win_h = self.screen.get_size()
        if win_w < 32 or win_h < 32:
            pygame.event.pump()
            pygame.time.wait(100)
            return

        log_w, log_h = self._logical_size
        scale = min(win_w / log_w, win_h / log_h)
        sw    = max(1, int(log_w * scale))
        sh    = max(1, int(log_h * scale))
        try:
            scaled = pygame.transform.smoothscale(self.surface, (sw, sh))
        except Exception:
            scaled = pygame.transform.scale(self.surface, (sw, sh))

        ox = (win_w - sw) // 2
        oy = (win_h - sh) // 2
        sox, soy = self.shake.offset
        ox += sox
        oy += soy

        self.screen.fill(cfg.BLACK)
        self.screen.blit(scaled, (ox, oy))
        pygame.display.flip()

    # ── Fim de jogo ───────────────────────────────────────────────────────────

    def game_over(self) -> None:
        try:
            self.records.guardar_pontuacao(
                self.hud.jogador, self.hud.modo,
                self.hud.dificuldade, self.score.obter_pontuacao(),
            )
        except Exception:
            pass
        pts      = self.score.obter_pontuacao()
        snapshot = self.surface.copy()
        self.jogar_de_novo = ecra_fim_jogo(
            self.screen, self.surface, self._logical_size,
            "Fim de Jogo",
            f"{self.player_name}  —  {pts} pontos",
            fundo=snapshot,
        )
        self.running = False

    def game_over_1v1(self, res: str) -> None:
        snapshot = self.surface.copy()
        self.jogar_de_novo = ecra_fim_1v1(
            self.screen, self.surface, self._logical_size,
            res, fundo=snapshot,
        )
        self.running = False

    def game_over_vsai(self, resultado: str,
                       pts_jogador: int, pts_bot: int) -> None:
        try:
            self.records.guardar_pontuacao(
                self.player_name, "Vs AI",
                self.dificuldade, pts_jogador,
            )
        except Exception:
            pass
        self.jogar_de_novo = ecra_fim_vsai(
            self.screen, self.surface, self._logical_size,
            resultado, self.player_name, pts_jogador, pts_bot,
        )
        self.running = False