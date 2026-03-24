# src/game/core/engine.py
import pygame
import game.config as cfg

from game.config             import FPS
from game.core.records       import RecordsManager
from game.ui.hud             import HUD
from game.core.score         import Score
from game.maps.map           import Mapas
from game.core.assets        import AssetsManager
from game.modes.og_snake     import OgSnake
from game.modes.modo_1v1     import Modo1v1
from game.maps.map_renderer  import MapRenderer
from game.modes.player_vs_ai import PlayerVsAI
from game.ui                 import ui_utils
from game.ui.ecras           import ecra_fim_jogo, ecra_fim_1v1, ecra_fim_vsai


class Game:
    """Orquestra a janela, o loop principal e os modos de jogo."""

    def __init__(self, player_name="Player", modo=cfg.MODO_OG_SNAKE,
                 dificuldade="Normal", velocidade_mult=1.0,
                 mapa_tipo=1, player2_name="Player 2"):
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

        mult          = cfg.DIFICULDADES.get(dificuldade, 1.0)
        self.score    = Score(multiplicador=mult)
        self.base_fps = FPS

        if   self.modo == cfg.MODO_1V1:   self.modo_atual = Modo1v1(self)
        elif self.modo == cfg.MODO_VS_AI: self.modo_atual = PlayerVsAI(self)
        else:                             self.modo_atual = OgSnake(self)

    # ── Loop principal ────────────────────────────────────────────────────────
    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False; return
            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False; return
            self.modo_atual.handle_event(ev)

    def update(self):
        self.modo_atual.update()

    def draw_logical(self):
        self.surface.fill(cfg.BG_DARK)
        for x in range(0, self.logical_w, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE, (x, 0), (x, self.logical_h))
        for y in range(0, self.logical_h, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE, (0, y), (0, self.logical_h))
        self.map_renderer.draw(self.surface)
        self.modo_atual.draw(self.surface)

        if self.modo == cfg.MODO_1V1:
            ht = f"1v1  |  {self.player_name} (WASD)  vs  {self.player2_name} (Setas)"
            self.hud.draw(self.surface, modo_override=ht)
        elif self.modo == cfg.MODO_VS_AI:
            ht = f"Batalha IA  |  {self.player_name} vs {self.player2_name}"
            self.hud.draw(self.surface, modo_override=ht)
        else:
            self.hud.draw(self.surface, score=self.score.obter_pontuacao())

    def run(self):
        while self.running:
            events = pygame.event.get()
            self.handle_events(events)
            self.update()
            self.draw_logical()
            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)
            self.clock.tick(int(self.base_fps * self.velocidade_mult))
        try:
            pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        except Exception:
            pass
        return self.jogar_de_novo

    # ── Fim de jogo ───────────────────────────────────────────────────────────
    def game_over(self):
        try:
            self.records.guardar_pontuacao(
                self.hud.jogador, self.hud.modo,
                self.hud.dificuldade, self.score.obter_pontuacao()
            )
        except Exception:
            pass
        pts      = self.score.obter_pontuacao()
        snapshot = self.surface.copy()
        self.jogar_de_novo = ecra_fim_jogo(
            self.screen, self.surface, self._logical_size,
            "Fim de Jogo",
            f"{self.player_name}  —  {pts} pontos",
            fundo=snapshot
        )
        self.running = False

    def game_over_1v1(self, res):
        snapshot = self.surface.copy()
        self.jogar_de_novo = ecra_fim_1v1(
            self.screen, self.surface, self._logical_size,
            res, fundo=snapshot
        )
        self.running = False

    def game_over_vsai(self, resultado, pts_jogador, pts_bot):
        try:
            self.records.guardar_pontuacao(
                self.player_name, "Vs AI", self.dificuldade, pts_jogador)
        except Exception:
            pass
        self.jogar_de_novo = ecra_fim_vsai(
            self.screen, self.surface, self._logical_size,
            resultado, self.player_name, pts_jogador, pts_bot
        )
        self.running = False