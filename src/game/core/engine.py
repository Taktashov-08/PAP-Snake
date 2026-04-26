# src/game/core/engine.py
"""
Motor principal do jogo.

Responsabilidades:
  - Gestão da janela e superfície lógica (com sidebar).
  - Loop principal com separação lógica / visual (60 FPS visuais, N FPS lógicos).
  - Screen shake com decaimento linear.
  - Orquestração de modos de jogo, HUD, partículas e música.
"""
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
from game.entities.particulas import SistemaDeParticulas
from game.core.musica         import GestorMusica
from game.modes.og_snake      import OgSnake
from game.modes.modo_1v1      import Modo1v1
from game.maps.map_renderer   import MapRenderer
from game.modes.player_vs_ai  import PlayerVsAI
from game.ui                  import ui_utils

# FPS alvo para o ciclo visual (partículas, shake, animações do HUD)
ALVO_FPS_VISUAIS: int = 60


# ── Screen Shake ──────────────────────────────────────────────────────────────

class TremidaEcra:
    """Vibração da câmara com decaimento linear."""

    def __init__(self) -> None:
        self._intensidade: float = 0.0
        self._duracao:     float = 0.0
        self._decorrido:   float = 0.0

    def disparar(self, intensidade: float = 8.0, duracao: float = 0.35) -> None:
        self._intensidade = intensidade
        self._duracao     = duracao
        self._decorrido   = 0.0

    def actualizar(self, dt: float) -> None:
        if self._decorrido < self._duracao:
            self._decorrido += dt

    @property
    def deslocamento(self) -> tuple[int, int]:
        if self._decorrido >= self._duracao or self._intensidade <= 0:
            return (0, 0)
        t   = 1.0 - (self._decorrido / self._duracao)
        mag = max(1, int(self._intensidade * t))
        return (random.randint(-mag, mag), random.randint(-mag, mag))


# ── Motor principal ───────────────────────────────────────────────────────────

class Game:
    """Orquestra a janela, o loop principal e os modos de jogo."""

    def __init__(
        self,
        player_name: str    = "Player",
        modo: str           = cfg.MODO_OG_SNAKE,
        dificuldade: str    = "Normal",
        velocidade_mult: float = 1.0,
        mapa_tipo           = 1,
        player2_name: str   = "Player 2",
    ) -> None:
        self.player_name     = player_name
        self.player2_name    = player2_name
        self.modo            = modo
        self.dificuldade     = dificuldade
        self.velocidade_mult = velocidade_mult
        self.jogar_de_novo   = False

        pygame.init()
        pygame.mixer.init()

        # Reutiliza o tamanho da janela existente se possível;
        # verifica None antes de chamar get_size() para evitar crash no arranque.
        cur = pygame.display.get_surface()
        if cur is not None:
            cw, ch = cur.get_size()
        else:
            cw, ch = cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT

        try:
            self.screen = pygame.display.set_mode((cw, ch), pygame.RESIZABLE)
        except Exception:
            self.screen = pygame.display.set_mode(
                (cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT),
                pygame.RESIZABLE,
            )

        # Superfície lógica inclui a sidebar; área de jogo exclui-a.
        self.logical_w     = cfg.SCREEN_WIDTH + cfg.SIDEBAR_W
        self.logical_h     = cfg.SCREEN_HEIGHT
        self._logical_size = (self.logical_w, self.logical_h)
        self.surface       = pygame.Surface(self._logical_size)
        self.block         = cfg.BLOCK_SIZE
        self.play_rect     = (0, 0, cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.clock         = pygame.time.Clock()
        self.running       = True

        self.records      = RecordsManager()
        self.mapa         = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)
        self.assets       = AssetsManager()
        self.particulas   = SistemaDeParticulas()
        self.tremida      = TremidaEcra()
        self.musica       = GestorMusica()   # singleton — partilhado entre sessões

        # ── Aliases de compatibilidade ────────────────────────────────────────
        # Os modos de jogo (player_vs_ai, modo_1v1, og_snake) acedem a estas
        # propriedades pelos nomes em inglês. Os aliases evitam quebrar esses
        # módulos quando o engine usa nomes em português internamente.
        #self.particles = self.particulas
        self.shake     = self.tremida

        mult           = cfg.DIFICULDADES.get(dificuldade, 1.0)
        self.score     = Score(multiplicador=mult)
        self.base_fps  = FPS

        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.hud.atualizar_info(nome_p2=player2_name)

        if   self.modo == cfg.MODO_1V1:   self.modo_atual = Modo1v1(self)
        elif self.modo == cfg.MODO_VS_AI: self.modo_atual = PlayerVsAI(self)
        else:                             self.modo_atual = OgSnake(self)

        # Música de jogo — 1v1 não tem dificuldade, usa "Normal" como fallback.
        dif_musica = dificuldade if modo != cfg.MODO_1V1 else "Normal"
        self.musica.tocar_jogo(dif_musica)

    # ── API pública para os modos ─────────────────────────────────────────────

    def disparar_tremida(self, intensity: float = 8.0, duration: float = 0.35) -> None:
        """Activa o screen shake a partir de qualquer modo de jogo."""
        self.tremida.disparar(intensity, duration)

    def tocar_sfx(self, nome: str) -> None:
        """Atalho para os modos tocarem efeitos sonoros sem importar GestorMusica."""
        self.musica.tocar_sfx(nome)

    # ── Aliases de compatibilidade (nomes antigos usados nalguns modos) ───────
    trigger_shake = disparar_tremida

    # ── Loop principal ────────────────────────────────────────────────────────

    def handle_events(self, eventos: list) -> None:
        for ev in eventos:
            if ev.type == pygame.QUIT:
                self.running = False
                return
            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (ev.w, ev.h), pygame.RESIZABLE)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.running = False
                return
            self.modo_atual.handle_event(ev)

    def actualizar(self) -> None:
        self.modo_atual.update()

    def desenhar_logico(self) -> None:
        """Compõe a superfície lógica: fundo, grelha, mapa, entidades, partículas e HUD."""
        self.surface.fill(cfg.BG_DARK)

        # Grelha apenas na área de jogo (esquerda da sidebar)
        for x in range(0, cfg.SCREEN_WIDTH, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (x, 0), (x, cfg.SCREEN_HEIGHT))
        for y in range(0, cfg.SCREEN_HEIGHT, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE,
                             (0, y), (cfg.SCREEN_WIDTH, y))

        self.map_renderer.draw(self.surface)
        self.modo_atual.draw(self.surface)

        # Partículas por cima das entidades, antes do HUD
        self.particulas.draw(self.surface)

        # HUD sidebar — o modo fornece os dados via hud_info()
        self.hud.draw_sidebar(
            self.surface,
            self.modo_atual.hud_info(),
            self.modo,
        )

    def run(self) -> bool:
        """
        Loop com separação lógica / visual:
          - Visual a ALVO_FPS_VISUAIS (60 fps) — partículas, shake, animações do HUD.
          - Lógica a base_fps × velocidade_mult — movimento da cobra.

        Devolve True se o jogador escolheu jogar de novo.
        """
        intervalo_logico: float = 1000.0 / max(
            1.0, self.base_fps * self.velocidade_mult
        )
        acumulador: float = 0.0

        while self.running:
            dt_ms = self.clock.tick(ALVO_FPS_VISUAIS)
            dt    = min(dt_ms / 1000.0, 0.1)

            eventos = pygame.event.get()
            self.handle_events(eventos)
            if not self.running:
                break

            # Passo lógico a timestep fixo
            acumulador += dt_ms
            while acumulador >= intervalo_logico and self.running:
                self.actualizar()
                acumulador -= intervalo_logico

            # Actualizações visuais a cada frame (60 fps)
            self.particulas.update(dt)
            self.tremida.actualizar(dt)
            self.hud.update(dt)          # pop de pontuação e outras animações do HUD

            # visual_update é opcional — nem todos os modos o implementam
            if hasattr(self.modo_atual, "visual_update"):
                self.modo_atual.visual_update(dt)

            self.desenhar_logico()
            self._blit_com_tremida()

        try:
            pygame.display.set_mode(
                (cfg.SCREEN_WIDTH + cfg.SIDEBAR_W, cfg.SCREEN_HEIGHT),
                pygame.RESIZABLE,
            )
        except Exception:
            pass

        return self.jogar_de_novo

    def _blit_com_tremida(self) -> None:
        """Escala a superfície lógica para a janela física com offset de screen shake."""
        win_w, win_h = self.screen.get_size()
        if win_w < 32 or win_h < 32:
            pygame.event.pump()
            pygame.time.wait(100)
            return

        log_w, log_h = self._logical_size
        escala = min(win_w / log_w, win_h / log_h)
        sw     = max(1, int(log_w * escala))
        sh     = max(1, int(log_h * escala))

        try:
            scaled = pygame.transform.smoothscale(self.surface, (sw, sh))
        except Exception:
            scaled = pygame.transform.scale(self.surface, (sw, sh))

        ox = (win_w - sw) // 2
        oy = (win_h - sh) // 2
        dox, doy = self.tremida.deslocamento
        ox += dox
        oy += doy

        self.screen.fill(cfg.BLACK)
        self.screen.blit(scaled, (ox, oy))
        pygame.display.flip()

    # ── Fim de jogo ───────────────────────────────────────────────────────────

    def game_over(self) -> None:
        """Fim do modo OG Snake: guarda pontuação e encerra o loop."""
        self.musica.tocar_sfx("Morte")
        self.musica.fade_out(600)
        try:
            self.records.guardar_pontuacao(
                self.hud.jogador, self.hud.modo,
                self.hud.dificuldade, self.score.obter_pontuacao(),
            )
        except Exception:
            pass
        self.running = False

    def game_over_1v1(self, resultado: str) -> None:
        """Fim do modo 1v1: guarda pontuações de ambos e mostra ecrã de resultado."""
        self.musica.tocar_sfx("Morte")
        self.musica.fade_out(600)

        pts_p1 = (len(self.modo_atual.snake.segments)  - 1) * 10 \
                 if hasattr(self.modo_atual, "snake")  else 0
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

    def game_over_vsai(self, resultado: str, pts_jogador: int, pts_bot: int) -> None:
        """Fim do modo Vs IA: guarda pontuação do jogador e mostra ecrã de resultado."""
        self.musica.tocar_sfx("Morte")
        self.musica.fade_out(600)
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
            titulo_txt, titulo_cor = "Vitória!", cfg.RESULT_WIN
            sub_txt = f"Derrotaste o Bot, {self.player_name}!"
        elif resultado == "derrota":
            titulo_txt, titulo_cor = "Derrota", cfg.RESULT_LOSS
            sub_txt = "O Bot ganhou desta vez..."
        else:
            titulo_txt, titulo_cor = "Empate", cfg.RESULT_DRAW
            sub_txt = "Ficaram empatados!"

        cx, cy   = self.logical_w // 2, self.logical_h // 2
        btn_rect = pygame.Rect(cx - 130, cy + 120, 260, 52)
        relogio  = pygame.time.Clock()

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

            painel = pygame.Rect(cx - 280, cy - 180, 560, 340)
            ps     = pygame.Surface((painel.w, painel.h), pygame.SRCALPHA)
            pygame.draw.rect(ps, cfg.OVERLAY_PANEL_BG_VSAI,     ps.get_rect(), border_radius=14)
            pygame.draw.rect(ps, cfg.OVERLAY_PANEL_BORDER_VSAI, ps.get_rect(), 1, border_radius=14)
            self.surface.blit(ps, painel.topleft)

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
            dica = f_info.render("ENTER / ESC  ·  voltar", True, (90, 100, 90))
            self.surface.blit(dica, dica.get_rect(center=(cx, btn_rect.bottom + 28)))

            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)
            relogio.tick(60)

    # ── Ecrã de fim 1v1 ───────────────────────────────────────────────────────

    def _ecra_fim_1v1(self, resultado: str, pts_p1: int, pts_p2: int) -> None:
        """Mostra o ecrã de resultado do modo 1v1 e aguarda input do jogador."""
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
            titulo_cor = cfg.RESULT_DRAW

        cx, cy   = self.logical_w // 2, self.logical_h // 2
        btn_rect = pygame.Rect(cx - 130, cy + 120, 260, 52)
        relogio  = pygame.time.Clock()

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

            painel = pygame.Rect(cx - 280, cy - 180, 560, 340)
            ps     = pygame.Surface((painel.w, painel.h), pygame.SRCALPHA)
            pygame.draw.rect(ps, cfg.OVERLAY_PANEL_BG_1V1,     ps.get_rect(), border_radius=14)
            pygame.draw.rect(ps, cfg.OVERLAY_PANEL_BORDER_1V1, ps.get_rect(), 1, border_radius=14)
            self.surface.blit(ps, painel.topleft)

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
            dica = f_info.render("ENTER / ESC  ·  voltar", True, (80, 90, 110))
            self.surface.blit(dica, dica.get_rect(center=(cx, btn_rect.bottom + 28)))

            ui_utils.blit_scaled(self.screen, self.surface, self._logical_size)
            relogio.tick(60)