# src/game/core/engine.py
import pygame
import sys
import game.config as cfg

from game.config           import BLOCK_SIZE, FPS, BLACK, WHITE
from game.core.records     import RecordsManager
from game.ui.hud           import HUD
from game.core.score       import Score
from game.maps.map         import Mapas
from game.core.assets      import AssetsManager
from game.modes.og_snake   import OgSnake
from game.modes.modo_1v1   import Modo1v1
from game.maps.map_renderer import MapRenderer
from game.modes.player_vs_ai import PlayerVsAI
from game.ui               import ui_utils


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

        # Uma unica chamada a pygame.init()
        pygame.init()
        pygame.mixer.init()

        try:
            cur = pygame.display.get_surface()
            cw, ch = cur.get_size() if cur else (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        except Exception:
            cw, ch = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        self.screen = pygame.display.set_mode((cw, ch), pygame.RESIZABLE)

        self.logical_w    = cfg.SCREEN_WIDTH
        self.logical_h    = cfg.SCREEN_HEIGHT
        self._logical_size = (self.logical_w, self.logical_h)
        self.surface      = pygame.Surface(self._logical_size)
        self.block        = cfg.BLOCK_SIZE
        self.play_rect    = (0, 0, self.logical_w, self.logical_h)
        self.clock        = pygame.time.Clock()
        self.running      = True

        self.records      = RecordsManager()
        self.hud          = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.mapa         = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)
        self.assets       = AssetsManager()

        mult = cfg.DIFICULDADES.get(dificuldade, 1.0)
        self.score = Score(multiplicador=mult)
        self.base_fps = FPS

        if   self.modo == cfg.MODO_1V1:    self.modo_atual = Modo1v1(self)
        elif self.modo == cfg.MODO_VS_AI:  self.modo_atual = PlayerVsAI(self)
        else:                              self.modo_atual = OgSnake(self)

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

    # ── Fim de jogo ───────────────────────────────────────────────────────────
    def game_over(self):
        try:
            self.records.guardar_pontuacao(
                self.hud.jogador, self.hud.modo,
                self.hud.dificuldade, self.score.obter_pontuacao()
            )
        except Exception:
            pass
        self.running = False

    def game_over_1v1(self, res):
        print(f"Fim 1v1: {res}")
        self.running = False

    def game_over_vsai(self, resultado, pts_jogador, pts_bot):
        try:
            self.records.guardar_pontuacao(
                self.player_name, "Vs AI", self.dificuldade, pts_jogador)
        except Exception:
            pass

        f_titulo = pygame.font.SysFont("Consolas", 62, bold=True)
        f_sub    = pygame.font.SysFont("Consolas", 28)
        f_info   = pygame.font.SysFont("Consolas", 22)
        f_btn    = pygame.font.SysFont("Consolas", 26)

        if resultado == "vitoria":
            titulo_txt, titulo_cor = "Vitoria!", (80, 220, 120)
            sub_txt = f"Derrotaste o Bot, {self.player_name}!"
        elif resultado == "derrota":
            titulo_txt, titulo_cor = "Derrota", (220, 80, 80)
            sub_txt = "O Bot ganhou desta vez..."
        else:
            titulo_txt, titulo_cor = "Empate", (220, 180, 60)
            sub_txt = "Ficaram empatados!"

        cx, cy = self.logical_w // 2, self.logical_h // 2
        btn_rect = pygame.Rect(cx - 130, cy + 120, 260, 52)
        clock = pygame.time.Clock()

        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.running = False; return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn_rect.collidepoint(ui_utils.window_to_logical(
                            self.screen, self._logical_size, ev.pos)):
                        self.running = False; return

            self.surface.fill(cfg.BG_DARK)
            for x in range(0, self.logical_w, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE, (x,0), (x, self.logical_h))
            for y in range(0, self.logical_h, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE, (0,y), (0, self.logical_h))

            panel = pygame.Rect(cx-280, cy-180, 560, 340)
            ps = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
            pygame.draw.rect(ps, (20,24,20,240), ps.get_rect(), border_radius=14)
            pygame.draw.rect(ps, (80,100,80,180), ps.get_rect(), 1, border_radius=14)
            self.surface.blit(ps, panel.topleft)

            t = f_titulo.render(titulo_txt, True, titulo_cor)
            self.surface.blit(t, t.get_rect(center=(cx, cy-120)))
            sub = f_sub.render(sub_txt, True, (200,210,200))
            self.surface.blit(sub, sub.get_rect(center=(cx, cy-55)))
            pygame.draw.line(self.surface, (60,80,60), (cx-200, cy-20), (cx+200, cy-20), 1)
            s1 = f_info.render(f"{self.player_name}:  {pts_jogador} pts", True, (120,220,140))
            s2 = f_info.render(f"Bot:  {pts_bot} pts", True, (220,100,100))
            self.surface.blit(s1, s1.get_rect(center=(cx, cy+20)))
            self.surface.blit(s2, s2.get_rect(center=(cx, cy+55)))

            mlog = ui_utils.window_to_logical(self.screen, self._logical_size, pygame.mouse.get_pos())
            bc = (50,120,70) if btn_rect.collidepoint(mlog) else (35,90,50)
            pygame.draw.rect(self.surface, bc, btn_rect, border_radius=8)
            pygame.draw.rect(self.surface, (80,160,100), btn_rect, 1, border_radius=8)
            bt = f_btn.render("Voltar ao Menu", True, WHITE)
            self.surface.blit(bt, bt.get_rect(center=btn_rect.center))
            hint = f_info.render("ENTER / ESC  ·  voltar", True, (90,100,90))
            self.surface.blit(hint, hint.get_rect(center=(cx, btn_rect.bottom+28)))

            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)
            clock.tick(60)
