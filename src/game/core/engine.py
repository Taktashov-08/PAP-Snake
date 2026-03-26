# src/game/core/engine.py
from __future__ import annotations

import random
import sys

import pygame
import game.config as cfg

from game.config              import BLOCK_SIZE, FPS, BLACK, WHITE
from game.core.records        import RecordsManager
from game.ui.hud              import HUD
from game.core.score          import Score
from game.maps.map            import Mapas
from game.core.assets         import AssetsManager
from game.entities.particulas import ParticleSystem
from game.modes.og_snake      import OgSnake
from game.modes.modo_1v1      import Modo1v1
from game.maps.map_renderer   import MapRenderer
from game.modes.player_vs_ai  import PlayerVsAI
from game.ui                  import ui_utils

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
            if cur is not None:
                cw, ch = cur.get_size()
            else:
                cw, ch = cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT
        except Exception:
            cw, ch = cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT
        
        try:
            self.screen = pygame.display.set_mode((cw, ch), pygame.RESIZABLE)
        except Exception:
            self.screen = pygame.display.set_mode(
        (cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)

        # A superfície lógica inclui a sidebar
        self.logical_w     = cfg.SCREEN_WIDTH + cfg.SIDEBAR_W
        self.logical_h     = cfg.SCREEN_HEIGHT
        self._logical_size = (self.logical_w, self.logical_h)
        self.surface       = pygame.Surface(self._logical_size)
        self.block         = cfg.BLOCK_SIZE
        # A área de jogo NÃO inclui a sidebar
        self.play_rect     = (0, 0, cfg.SCREEN_WIDTH, self.logical_h)
        self.clock         = pygame.time.Clock()
        self.running       = True

        self.records      = RecordsManager()
        self.mapa         = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)
        self.assets       = AssetsManager()
        self.particles    = ParticleSystem()
        self.shake        = ScreenShake()

        mult = cfg.DIFICULDADES.get(dificuldade, 1.0)
        self.score     = Score(multiplicador=mult)
        self.score_bot = Score(multiplicador=1.0)
        self.base_fps  = FPS

        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.hud.atualizar_info(nome_p2=player2_name)

        if   self.modo == cfg.MODO_1V1:   self.modo_atual = Modo1v1(self)
        elif self.modo == cfg.MODO_VS_AI: self.modo_atual = PlayerVsAI(self)
        else:                             self.modo_atual = OgSnake(self)

    # ── API pública para os modos ─────────────────────────────────────────────

    def trigger_shake(self, intensity: float = 8.0, duration: float = 0.35) -> None:
        self.shake.trigger(intensity, duration)

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

        # Grelha apenas na área de jogo (não sobre a sidebar)
        area_jogo_w = cfg.SCREEN_WIDTH
        for x in range(0, area_jogo_w, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (x, 0), (x, self.logical_h))
        for y in range(0, self.logical_h, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (0, y), (area_jogo_w, y))

        self.map_renderer.draw(self.surface)
        self.modo_atual.draw(self.surface)

        # Partículas por cima das entidades, antes do HUD
        self.particles.draw(self.surface)

        # HUD sidebar — adaptativo por modo
        if self.modo == cfg.MODO_1V1:
            info = {
                "p1_name":   self.player_name,
                "p2_name":   self.player2_name,
                "p1_length": len(self.modo_atual.snake.segments)  if hasattr(self.modo_atual, "snake")  else 1,
                "p2_length": len(self.modo_atual.snake2.segments) if hasattr(self.modo_atual, "snake2") else 1,
                "max_length": 60,
                "p1_ready":  getattr(self.modo_atual, "p1_ready", False),
                "p2_ready":  getattr(self.modo_atual, "p2_ready", False),
            }
            self.hud.draw_sidebar(self.surface, info, self.modo)

        elif self.modo == cfg.MODO_VS_AI:
            info = {
                "score":             self.score.obter_pontuacao(),
                "length":            len(self.modo_atual.snake.segments) if hasattr(self.modo_atual, "snake") else 1,
                "bot_length":        len(self.modo_atual.bot.segments)   if hasattr(self.modo_atual, "bot")   else 1,
                "max_length":        60,
                "boost_vel_ticks":   self.modo_atual.boosts_jogador.get("velocidade", 0) if hasattr(self.modo_atual, "boosts_jogador") else 0,
                "boost_imune_ticks": self.modo_atual.boosts_jogador.get("imunidade",  0) if hasattr(self.modo_atual, "boosts_jogador") else 0,
                "fps_ref":           self.base_fps,
            }
            self.hud.draw_sidebar(self.surface, info, self.modo)

        else:
            info = {
                "score":      self.score.obter_pontuacao(),
                "length":     len(self.modo_atual.snake.segments) if hasattr(self.modo_atual, "snake") else 1,
                "max_length": 60,
            }
            self.hud.draw_sidebar(self.surface, info, self.modo)

    def run(self):
        """
        Loop com separação lógica/visual:
          - Visual a TARGET_VFX_FPS (60 fps) — partículas, shake, animações
          - Lógica a base_fps × velocidade_mult — movimento da cobra
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

            # Visuais e efeitos a cada frame (60 fps)
            self.particles.update(dt)
            self.shake.update(dt)
            self.hud.update(dt)

            # visual_update opcional nos modos (nem todos têm)
            if hasattr(self.modo_atual, "visual_update"):
                self.modo_atual.visual_update(dt)

            self.draw_logical()
            self._blit_with_shake()

        try:
            pygame.display.set_mode(
                (cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        except Exception:
            pass

        return self.jogar_de_novo

    def _blit_with_shake(self) -> None:
        """Escala a superfície lógica para a janela com offset de screen shake."""
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

    def game_over(self):
        try:
            self.records.guardar_pontuacao(
                self.hud.jogador, self.hud.modo,
                self.hud.dificuldade, self.score.obter_pontuacao()
            )
        except Exception:
            pass
        self.running = False

    def game_over_1v1(self, resultado):
        pts_p1 = (len(self.modo_atual.snake.segments) - 1) * 10 \
                 if hasattr(self.modo_atual, "snake") else 0
        pts_p2 = (len(self.modo_atual.snake2.segments) - 1) * 10 \
                 if hasattr(self.modo_atual, "snake2") else 0

        try:
            self.records.guardar_pontuacao(
                self.player_name,  "1v1", self.dificuldade, pts_p1)
            self.records.guardar_pontuacao(
                self.player2_name, "1v1", self.dificuldade, pts_p2)
        except Exception:
            pass

        self._ecra_fim_1v1(resultado, pts_p1, pts_p2)

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
            titulo_txt, titulo_cor = "Vitória!", (80, 220, 120)
            sub_txt = f"Derrotaste o Bot, {self.player_name}!"
        elif resultado == "derrota":
            titulo_txt, titulo_cor = "Derrota", (220, 80, 80)
            sub_txt = "O Bot ganhou desta vez..."
        else:
            titulo_txt, titulo_cor = "Empate", (220, 180, 60)
            sub_txt = "Ficaram empatados!"

        cx, cy   = self.logical_w // 2, self.logical_h // 2
        btn_rect = pygame.Rect(cx - 130, cy + 120, 260, 52)
        clock    = pygame.time.Clock()

        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key in (
                        pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.running = False; return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos_log = ui_utils.window_to_logical(
                        self.screen, self._logical_size, ev.pos)
                    if btn_rect.collidepoint(pos_log):
                        self.running = False; return

            self.surface.fill(cfg.BG_DARK)
            for x in range(0, self.logical_w, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE,
                                 (x, 0), (x, self.logical_h))
            for y in range(0, self.logical_h, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE,
                                 (0, y), (self.logical_w, y))

            panel = pygame.Rect(cx - 280, cy - 180, 560, 340)
            ps    = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
            pygame.draw.rect(ps, (20, 24, 20, 240), ps.get_rect(), border_radius=14)
            pygame.draw.rect(ps, (80, 100, 80, 180), ps.get_rect(), 1, border_radius=14)
            self.surface.blit(ps, panel.topleft)

            t = f_titulo.render(titulo_txt, True, titulo_cor)
            self.surface.blit(t, t.get_rect(center=(cx, cy - 120)))
            sub = f_sub.render(sub_txt, True, (200, 210, 200))
            self.surface.blit(sub, sub.get_rect(center=(cx, cy - 55)))
            pygame.draw.line(self.surface, (60, 80, 60),
                             (cx - 200, cy - 20), (cx + 200, cy - 20), 1)
            s1 = f_info.render(
                f"{self.player_name}:  {pts_jogador} pts", True, (120, 220, 140))
            s2 = f_info.render(
                f"Bot:  {pts_bot} pts", True, (220, 100, 100))
            self.surface.blit(s1, s1.get_rect(center=(cx, cy + 20)))
            self.surface.blit(s2, s2.get_rect(center=(cx, cy + 55)))

            mlog = ui_utils.window_to_logical(
                self.screen, self._logical_size, pygame.mouse.get_pos())
            bc = (50, 120, 70) if btn_rect.collidepoint(mlog) else (35, 90, 50)
            pygame.draw.rect(self.surface, bc, btn_rect, border_radius=8)
            pygame.draw.rect(self.surface, (80, 160, 100), btn_rect, 1, border_radius=8)
            bt = f_btn.render("Voltar ao Menu", True, WHITE)
            self.surface.blit(bt, bt.get_rect(center=btn_rect.center))
            hint = f_info.render("ENTER / ESC  ·  voltar", True, (90, 100, 90))
            self.surface.blit(hint, hint.get_rect(center=(cx, btn_rect.bottom + 28)))

            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)
            clock.tick(60)

    # ── Ecrã de fim 1v1 ───────────────────────────────────────────────────────

    def _ecra_fim_1v1(self, resultado, pts_p1, pts_p2):
        f_titulo = pygame.font.SysFont("Consolas", 56, bold=True)
        f_sub    = pygame.font.SysFont("Consolas", 26)
        f_info   = pygame.font.SysFont("Consolas", 20)
        f_btn    = pygame.font.SysFont("Consolas", 24)

        if "P2" in resultado or (
                self.player2_name and self.player2_name in resultado):
            titulo_txt = f"Vitória {self.player2_name}!"
            titulo_cor = cfg.SNAKE2_HEAD
        elif self.player_name in resultado or "P1" in resultado:
            titulo_txt = f"Vitória {self.player_name}!"
            titulo_cor = cfg.SNAKE1_HEAD
        else:
            titulo_txt = "Empate!"
            titulo_cor = (220, 180, 60)

        cx, cy   = self.logical_w // 2, self.logical_h // 2
        btn_rect = pygame.Rect(cx - 130, cy + 120, 260, 52)
        clock    = pygame.time.Clock()

        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key in (
                        pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    self.running = False; return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos_log = ui_utils.window_to_logical(
                        self.screen, self._logical_size, ev.pos)
                    if btn_rect.collidepoint(pos_log):
                        self.running = False; return

            self.surface.fill(cfg.BG_DARK)
            for x in range(0, self.logical_w, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE,
                                 (x, 0), (x, self.logical_h))
            for y in range(0, self.logical_h, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE,
                                 (0, y), (self.logical_w, y))

            panel = pygame.Rect(cx - 280, cy - 180, 560, 340)
            ps    = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
            pygame.draw.rect(ps, (18, 20, 30, 240), ps.get_rect(), border_radius=14)
            pygame.draw.rect(ps, (60, 70, 100, 200), ps.get_rect(), 1, border_radius=14)
            self.surface.blit(ps, panel.topleft)

            t = f_titulo.render(titulo_txt, True, titulo_cor)
            self.surface.blit(t, t.get_rect(center=(cx, cy - 120)))
            pygame.draw.line(self.surface, (50, 55, 75),
                             (cx - 200, cy - 60), (cx + 200, cy - 60), 1)

            s1 = f_info.render(
                f"{self.player_name}  {pts_p1} pts", True, cfg.SNAKE1_HEAD)
            s2 = f_info.render(
                f"{self.player2_name}  {pts_p2} pts", True, cfg.SNAKE2_HEAD)
            self.surface.blit(s1, s1.get_rect(center=(cx - 110, cy - 20)))
            self.surface.blit(s2, s2.get_rect(center=(cx + 110, cy - 20)))

            vs = f_sub.render("vs", True, (80, 80, 100))
            self.surface.blit(vs, vs.get_rect(center=(cx, cy - 20)))
            pygame.draw.line(self.surface, (50, 55, 75),
                             (cx - 200, cy + 20), (cx + 200, cy + 20), 1)

            mlog = ui_utils.window_to_logical(
                self.screen, self._logical_size, pygame.mouse.get_pos())
            bc = (40, 90, 160) if btn_rect.collidepoint(mlog) else (30, 65, 120)
            pygame.draw.rect(self.surface, bc, btn_rect, border_radius=8)
            pygame.draw.rect(self.surface, (70, 130, 210), btn_rect, 1, border_radius=8)
            bt = f_btn.render("Voltar ao Menu", True, WHITE)
            self.surface.blit(bt, bt.get_rect(center=btn_rect.center))
            hint = f_info.render("ENTER / ESC  ·  voltar", True, (80, 90, 110))
            self.surface.blit(hint,
                              hint.get_rect(center=(cx, btn_rect.bottom + 28)))

            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)
            clock.tick(60)