# src/game/engine.py
import pygame
import sys
import game.config as cfg

from game.config import BLOCK_SIZE, FPS, BLACK, WHITE, BLUE, GREEN, RED
from game.records import RecordsManager
from game.hud import HUD
from game.score import Score
from game.map import Mapas
from game.assets import AssetsManager
from game.TipoDeJogo.OgSnake import OgSnake
from game.TipoDeJogo.Modo1v1 import Modo1v1
from game.RenderizadorDeMapas import MapRenderer
from game.TipoDeJogo.PlayerVsAI import PlayerVsAI


class Game:
    """Classe central que orquestra a janela, o loop principal e a transição de estados/modos."""

    def __init__(self, player_name="Player", modo="OG Snake", dificuldade="Normal",
                 velocidade_mult=1.0, mapa_tipo=1, player2_name="Player 2"):
        self.player_name  = player_name
        self.player2_name = player2_name
        self.modo         = modo
        self.dificuldade  = dificuldade
        self.velocidade_mult = velocidade_mult

        pygame.init()

        # ── Janela física ──────────────────────────────────────────────
        try:
            cur = pygame.display.get_surface()
            current_w, current_h = cur.get_size() if cur else (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        except Exception:
            current_w, current_h = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        self.screen = pygame.display.set_mode((current_w, current_h), pygame.RESIZABLE)

        # ── Superfície lógica (tamanho fixo) ──────────────────────────
        self.logical_w = cfg.SCREEN_WIDTH
        self.logical_h = cfg.SCREEN_HEIGHT
        self.surface   = pygame.Surface((self.logical_w, self.logical_h))
        self.block     = cfg.BLOCK_SIZE
        self.play_rect = (0, 0, self.logical_w, self.logical_h)

        self.clock   = pygame.time.Clock()
        self.running = True

        # ── Managers ──────────────────────────────────────────────────
        self.records    = RecordsManager()
        self.hud        = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.mapa       = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)

        pygame.init()
        pygame.mixer.init()
        self.assets = AssetsManager()

        # ── Pontuação ─────────────────────────────────────────────────
        mult = 1.0
        if dificuldade in ("Rápido", "Rapido"):   mult = 1.5
        elif dificuldade == "Muito Rápido":        mult = 2.0
        self.score = Score(multiplicador=mult)

        self.base_fps = FPS

        # ── Modo de jogo ──────────────────────────────────────────────
        if self.modo == "1v1":
            self.modo_atual = Modo1v1(self)
        elif self.modo == "Vs AI":
            self.modo_atual = PlayerVsAI(self)
        else:
            self.modo_atual = OgSnake(self)

    # ------------------------------------------------------------------ #
    #  LOOP PRINCIPAL                                                      #
    # ------------------------------------------------------------------ #
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
                return
            self.modo_atual.handle_event(event)

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

        if self.modo == "1v1":
            hud_text = f"1v1  |  {self.player_name} (WASD)  vs  {self.player2_name} (Setas)"
            self.hud.draw(self.surface, modo_override=hud_text)
        elif self.modo == "Vs AI":
            hud_text = f"Batalha IA  |  {self.player_name} vs {self.player2_name}"
            self.hud.draw(self.surface, modo_override=hud_text)
        else:
            self.hud.draw(self.surface, score=self.score.obter_pontuacao())

    def _blit_scaled(self):
        """Escala a superfície lógica para a janela física (letterbox)."""
        win_w, win_h = self.screen.get_size()
        if win_w < 32 or win_h < 32:
            pygame.time.wait(100)
            return

        scale  = min(win_w / self.logical_w, win_h / self.logical_h)
        new_w  = int(self.logical_w * scale)
        new_h  = int(self.logical_h * scale)

        try:    scaled = pygame.transform.smoothscale(self.surface, (new_w, new_h))
        except: scaled = pygame.transform.scale(self.surface, (new_w, new_h))

        ox = (win_w - new_w) // 2
        oy = (win_h - new_h) // 2
        self.screen.fill(BLACK)
        self.screen.blit(scaled, (ox, oy))
        pygame.display.flip()

    def run(self):
        while self.running:
            events = pygame.event.get()
            self.handle_events(events)
            self.update()
            self.draw_logical()
            self._blit_scaled()
            self.clock.tick(int(self.base_fps * self.velocidade_mult))

        try:
            pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  ECRÃS DE FIM DE JOGO                                               #
    # ------------------------------------------------------------------ #
    def game_over(self):
        """Fim de jogo genérico (OG Snake / morte do jogador no Vs AI)."""
        try:
            self.records.guardar_pontuacao(
                self.hud.jogador, self.hud.modo,
                self.hud.dificuldade, self.score.obter_pontuacao()
            )
        except Exception:
            pass
        print("Game Over")
        self.running = False

    def game_over_1v1(self, res):
        """Fim de jogo no modo 1v1."""
        print(f"Fim 1v1: {res}")
        self.running = False

    def game_over_vsai(self, resultado, pontuacao_jogador, pontuacao_bot):
        """
        Ecrã final do modo Vs AI.

        resultado: "vitoria" | "derrota" | "empate"
        Mostra o resultado, os scores e dá opção de voltar ao menu.
        """
        # Guardar pontuação do jogador
        try:
            self.records.guardar_pontuacao(
                self.player_name, "Vs AI",
                self.dificuldade, pontuacao_jogador
            )
        except Exception:
            pass

        # ── Fontes ────────────────────────────────────────────────────
        f_titulo  = pygame.font.SysFont("Consolas", 62, bold=True)
        f_sub     = pygame.font.SysFont("Consolas", 28)
        f_info    = pygame.font.SysFont("Consolas", 22)
        f_btn     = pygame.font.SysFont("Consolas", 26)

        # ── Cores e textos consoante o resultado ──────────────────────
        if resultado == "vitoria":
            titulo_txt = "Vitória!"
            titulo_cor = (80, 220, 120)
            sub_txt    = f"Derrotaste o Bot, {self.player_name}!"
        elif resultado == "derrota":
            titulo_txt = "Derrota"
            titulo_cor = (220, 80, 80)
            sub_txt    = "O Bot ganhou desta vez..."
        else:
            titulo_txt = "Empate"
            titulo_cor = (220, 180, 60)
            sub_txt    = "Ficaram empatados!"

        cx = self.logical_w // 2
        cy = self.logical_h // 2

        # Botão "Voltar ao Menu"
        btn_w, btn_h = 260, 52
        btn_rect = pygame.Rect(cx - btn_w // 2, cy + 120, btn_w, btn_h)

        clock = pygame.time.Clock()

        while True:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                        self.running = False
                        return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self._window_to_logical(ev.pos)
                    if btn_rect.collidepoint(mpos):
                        self.running = False
                        return

            # ── Fundo (reutiliza a superfície lógica) ─────────────────
            self.surface.fill(cfg.BG_DARK)
            for x in range(0, self.logical_w, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE, (x, 0), (x, self.logical_h))
            for y in range(0, self.logical_h, self.block):
                pygame.draw.line(self.surface, cfg.GRID_LINE, (0, y), (0, self.logical_h))

            # ── Painel central ────────────────────────────────────────
            panel = pygame.Rect(cx - 280, cy - 180, 560, 340)
            s = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
            pygame.draw.rect(s, (20, 24, 20, 240), s.get_rect(), border_radius=14)
            pygame.draw.rect(s, (80, 100, 80, 180), s.get_rect(), 1, border_radius=14)
            self.surface.blit(s, panel.topleft)

            # ── Título (Vitória / Derrota / Empate) ───────────────────
            t = f_titulo.render(titulo_txt, True, titulo_cor)
            self.surface.blit(t, t.get_rect(center=(cx, cy - 120)))

            # ── Subtítulo ─────────────────────────────────────────────
            sub = f_sub.render(sub_txt, True, (200, 210, 200))
            self.surface.blit(sub, sub.get_rect(center=(cx, cy - 55)))

            # ── Scores ────────────────────────────────────────────────
            sep_y = cy - 20
            pygame.draw.line(self.surface, (60, 80, 60),
                             (cx - 200, sep_y), (cx + 200, sep_y), 1)

            s1 = f_info.render(f"{self.player_name}:  {pontuacao_jogador} pts", True, (120, 220, 140))
            s2 = f_info.render(f"Bot:  {pontuacao_bot} pts", True, (220, 100, 100))
            self.surface.blit(s1, s1.get_rect(center=(cx, cy + 20)))
            self.surface.blit(s2, s2.get_rect(center=(cx, cy + 55)))

            # ── Botão "Voltar ao Menu" ────────────────────────────────
            mpos_log = self._window_to_logical(pygame.mouse.get_pos())
            is_hover = btn_rect.collidepoint(mpos_log)
            btn_col  = (50, 120, 70) if is_hover else (35, 90, 50)
            pygame.draw.rect(self.surface, btn_col, btn_rect, border_radius=8)
            pygame.draw.rect(self.surface, (80, 160, 100), btn_rect, 1, border_radius=8)
            bt = f_btn.render("Voltar ao Menu", True, WHITE)
            self.surface.blit(bt, bt.get_rect(center=btn_rect.center))

            # ── Hint teclado ──────────────────────────────────────────
            hint = f_info.render("ENTER / ESC  ·  voltar", True, (90, 100, 90))
            self.surface.blit(hint, hint.get_rect(center=(cx, btn_rect.bottom + 28)))

            self._blit_scaled()
            clock.tick(60)

    def _window_to_logical(self, pos):
        """Converte coordenadas do rato na janela física para a superfície lógica."""
        win_w, win_h = self.screen.get_size()
        scale  = min(win_w / self.logical_w, win_h / self.logical_h)
        sw, sh = int(self.logical_w * scale), int(self.logical_h * scale)
        ox, oy = (win_w - sw) // 2, (win_h - sh) // 2
        xw, yw = pos
        if not (ox <= xw < ox + sw and oy <= yw < oy + sh):
            return (-1, -1)
        return (int((xw - ox) / scale), int((yw - oy) / scale))