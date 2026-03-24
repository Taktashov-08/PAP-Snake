# src/game/core/engine.py
"""
Orquestrador principal do jogo.

Separação de responsabilidades:
  - Lógica de jogo   : timestep fixo a (FPS × mult) Hz
  - Visuais / efeitos: loop a TARGET_VFX_FPS Hz, guiado por delta time
  - Partículas       : instância única partilhada por todos os modos
"""
from __future__ import annotations

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

# FPS visual independente da velocidade de lógica
TARGET_VFX_FPS: int = 60


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

        # Reutilizar tamanho actual da janela se já existir
        try:
            cur = pygame.display.get_surface()
            cw, ch = cur.get_size() if cur else (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        except Exception:
            cw, ch = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        self.screen = pygame.display.set_mode((cw, ch), pygame.RESIZABLE)

        self.logical_w     = cfg.SCREEN_WIDTH
        self.logical_h     = cfg.SCREEN_HEIGHT
        self._logical_size = (self.logical_w, self.logical_h)
        self.surface       = pygame.Surface(self._logical_size)
        self.block         = cfg.BLOCK_SIZE
        self.play_rect     = (0, 0, self.logical_w, self.logical_h)
        self.clock         = pygame.time.Clock()
        self.running       = True

        self.records      = RecordsManager()
        self.hud          = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.mapa         = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)
        self.assets       = AssetsManager()
        self.particles    = ParticleSystem()   # ← sistema de partículas global

        mult       = cfg.DIFICULDADES.get(dificuldade, 1.0)
        self.score = Score(multiplicador=mult)
        self.base_fps = FPS

        # Instanciar o modo de jogo
        if   self.modo == cfg.MODO_1V1:   self.modo_atual = Modo1v1(self)
        elif self.modo == cfg.MODO_VS_AI: self.modo_atual = PlayerVsAI(self)
        else:                             self.modo_atual = OgSnake(self)

    # ── Handlers ─────────────────────────────────────────────────────────────

    def handle_events(self, events: list) -> None:
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
                return
            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (ev.w, ev.h), pygame.RESIZABLE
                )
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False
                return
            self.modo_atual.handle_event(ev)

    def update(self) -> None:
        """Passo de lógica de jogo (chamado a FPS fixo)."""
        self.modo_atual.update()

    def draw_logical(self) -> None:
        """Renderiza um frame completo na superfície lógica."""
        self.surface.fill(cfg.BG_DARK)

        # Grelha decorativa
        for x in range(0, self.logical_w, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (x, 0), (x, self.logical_h))
        for y in range(0, self.logical_h, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (0, y), (self.logical_w, y))

        self.map_renderer.draw(self.surface)
        self.modo_atual.draw(self.surface)

        # Partículas por cima de tudo (antes do HUD)
        self.particles.draw(self.surface)

        # HUD
        if self.modo == cfg.MODO_1V1:
            ht = (f"1v1  |  {self.player_name} (WASD)"
                  f"  vs  {self.player2_name} (Setas)")
            self.hud.draw(self.surface, modo_override=ht)
        elif self.modo == cfg.MODO_VS_AI:
            ht = f"Batalha IA  |  {self.player_name} vs {self.player2_name}"
            self.hud.draw(self.surface, modo_override=ht)
        else:
            self.hud.draw(self.surface, score=self.score.obter_pontuacao())

    # ── Loop principal ────────────────────────────────────────────────────────

    def run(self) -> bool:
        """
        Loop principal com separação lógica/visual:
          - Visual a TARGET_VFX_FPS (60 fps) — partículas e animações suaves
          - Lógica a base_fps × velocidade_mult — movimento da cobra
        Devolve True se o jogador quiser repetir.
        """
        logic_interval: float = 1000.0 / max(
            1.0, self.base_fps * self.velocidade_mult
        )
        accumulator: float = 0.0

        while self.running:
            # ── Delta time (capado a 100 ms para evitar spiral-of-death) ──
            dt_ms = self.clock.tick(TARGET_VFX_FPS)
            dt    = min(dt_ms / 1000.0, 0.1)

            # ── Eventos ───────────────────────────────────────────────────
            events = pygame.event.get()
            self.handle_events(events)
            if not self.running:
                break

            # ── Lógica a timestep fixo ────────────────────────────────────
            accumulator += dt_ms
            while accumulator >= logic_interval and self.running:
                self.update()
                accumulator -= logic_interval

            # ── Visuais a cada frame ──────────────────────────────────────
            self.particles.update(dt)
            self.modo_atual.visual_update(dt)

            self.draw_logical()
            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)

        # Restaurar resolução base após jogo
        try:
            pygame.display.set_mode(
                (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE
            )
        except Exception:
            pass

        return self.jogar_de_novo

    # ── Fim de jogo ───────────────────────────────────────────────────────────

    def game_over(self) -> None:
        """Guarda pontuação e apresenta ecrã de fim para modo clássico."""
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
        """Apresenta ecrã de resultado 1v1."""
        snapshot = self.surface.copy()
        self.jogar_de_novo = ecra_fim_1v1(
            self.screen, self.surface, self._logical_size,
            res, fundo=snapshot,
        )
        self.running = False

    def game_over_vsai(self, resultado: str,
                       pts_jogador: int, pts_bot: int) -> None:
        """Guarda pontuação e apresenta ecrã de resultado Vs IA."""
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