# src/game/ui/menu.py
"""
Menu principal com animações visuais:
  - Título com bob sinusoidal e pulso de cor
  - Botões com entrada deslizante (slide-in) na primeira exibição
  - Transições com fade entre ecrãs
"""
from __future__ import annotations

import math
import sys
import re

import pygame

import game.config as cfg
import game.config as C
from game.core.engine   import Game
from game.core.records  import RecordsManager
from game.core.nomes    import GestorNomes
from game.ui            import ui_utils

pygame.init()

LOGICAL_W = cfg.SCREEN_WIDTH
LOGICAL_H = cfg.SCREEN_HEIGHT

# ── Parâmetros de animação do título ──────────────────────────────────────────
_TITLE_BOB_AMP   = 5.0    # amplitude do bob vertical em píxeis
_TITLE_BOB_SPEED = 1.2    # ciclos por segundo
_TITLE_COL_A     = C.TITLE_COLOR           # cor base
_TITLE_COL_B     = (160, 220, 170)         # cor de destaque (leve verde)

# ── Parâmetros do slide-in dos botões ─────────────────────────────────────────
_SLIDE_DURATION = 0.35    # segundos por botão
_SLIDE_STAGGER  = 0.06    # atraso entre botões (s)


def _lerp_color(a, b, t):
    """Interpolação linear entre duas cores."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def draw_title(surface, font_big, w, y_base, t: float = 0.0):
    """
    Título animado com bob vertical e pulso de cor suave.
    `t` é o tempo acumulado em segundos.
    """
    bob   = math.sin(t * _TITLE_BOB_SPEED * math.tau) * _TITLE_BOB_AMP
    pulse = (math.sin(t * 0.8 * math.tau) + 1.0) / 2.0   # 0 → 1
    color = _lerp_color(_TITLE_COL_A, _TITLE_COL_B, pulse * 0.4)
    text  = font_big.render("Snake", True, color)
    surface.blit(text, text.get_rect(center=(w // 2, int(y_base + bob))))


# ── Botão ─────────────────────────────────────────────────────────────────────

class Button:
    """
    Botão com:
      - Animação de entrada deslizante (slide desde a esquerda)
      - Hover reactivo
      - Callback opcional
    """

    def __init__(self, text: str, x: int, y: int, w: int, h: int,
                 color, hover_color, action=None, font_size: int = 30,
                 slide_delay: float = 0.0) -> None:
        self.text        = text
        self._target_x   = int(x)
        self.rect        = pygame.Rect(int(x), int(y), int(w), int(h))
        self.color       = color
        self.hover_color = hover_color
        self.action      = action
        self.font        = pygame.font.SysFont("Consolas", font_size)
        # Animação de slide
        self._slide_t    = 0.0          # 0 → não animado, 1 → posição final
        self._slide_delay = slide_delay # segundos antes de começar
        self._elapsed    = 0.0

    def advance(self, dt: float) -> None:
        """Avança a animação de slide-in."""
        self._elapsed += dt
        if self._elapsed < self._slide_delay:
            return
        progress = min(1.0, (self._elapsed - self._slide_delay) / _SLIDE_DURATION)
        self._slide_t = _ease_out_cubic(progress)

    def draw(self, surface: pygame.Surface, mouse_pos=None) -> None:
        if mouse_pos is None:
            mouse_pos = (-1, -1)
        # Offset de slide: entra da esquerda
        offset = int((1.0 - self._slide_t) * -(LOGICAL_W + self.rect.w))
        draw_rect = self.rect.move(offset, 0)
        hover     = draw_rect.collidepoint(mouse_pos) and self._slide_t >= 1.0
        ui_utils.draw_btn(surface, draw_rect, self.color, self.hover_color,
                          hover, self.text, self.font)

    def check_click(self, mouse_pos) -> bool:
        """Só responde a cliques quando a animação de slide terminou."""
        if self._slide_t < 1.0:
            return False
        if self.rect.collidepoint(mouse_pos):
            if self.action:
                self.action()
            return True
        return False


# ── Fade de transição ─────────────────────────────────────────────────────────

def _fade_out(screen, logical_surface, logical_size,
              duration: float = 0.25, clock=None) -> None:
    """Fade a preto sobre o ecrã actual."""
    if clock is None:
        clock = pygame.time.Clock()
    elapsed = 0.0
    snap    = logical_surface.copy()
    overlay = pygame.Surface(logical_size, pygame.SRCALPHA)
    while elapsed < duration:
        dt      = clock.tick(60) / 1000.0
        elapsed += dt
        alpha   = int(min(255, (elapsed / duration) * 255))
        overlay.fill((0, 0, 0, alpha))
        logical_surface.blit(snap, (0, 0))
        logical_surface.blit(overlay, (0, 0))
        ui_utils.blit_scaled(screen, logical_surface, logical_size)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def _fade_in(screen, logical_surface, logical_size,
             duration: float = 0.20, clock=None) -> None:
    """Fade de preto para o conteúdo actual."""
    if clock is None:
        clock = pygame.time.Clock()
    elapsed = 0.0
    snap    = logical_surface.copy()
    overlay = pygame.Surface(logical_size, pygame.SRCALPHA)
    while elapsed < duration:
        dt      = clock.tick(60) / 1000.0
        elapsed += dt
        alpha   = int(max(0, 255 - (elapsed / duration) * 255))
        overlay.fill((0, 0, 0, alpha))
        logical_surface.blit(snap, (0, 0))
        logical_surface.blit(overlay, (0, 0))
        ui_utils.blit_scaled(screen, logical_surface, logical_size)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()


# ── Menu principal ────────────────────────────────────────────────────────────

class Menu:
    """Menu principal com título animado e botões com slide-in."""

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(
            (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE
        )
        pygame.display.set_caption("Snake")

        self.running         = True
        self.logical_size    = (LOGICAL_W, LOGICAL_H)
        self.logical_surface = pygame.Surface(self.logical_size)
        self.font_title = pygame.font.SysFont("Consolas", 52, bold=True)
        self.font_big   = pygame.font.SysFont("Consolas", 30)
        self.font_sm    = pygame.font.SysFont("Consolas", 18)
        self.gestor_nomes = GestorNomes()

        self._title_t: float  = 0.0    # acumulador de tempo para animação
        self._btn_elapsed: float = 0.0  # tempo desde que os botões apareceram
        self.recenter_buttons()

    def _wl(self, pos):
        return ui_utils.window_to_logical(self.screen, self.logical_size, pos)

    def _blit(self):
        ui_utils.blit_scaled(self.screen, self.logical_surface, self.logical_size)

    def txt_center(self, text, font, color, y):
        s = font.render(text, True, color)
        self.logical_surface.blit(s, s.get_rect(center=(LOGICAL_W // 2, y)))

    # ── Acções ────────────────────────────────────────────────────────────────

    def action_jogar(self):
        modo = self._menu_selecao("Modo de jogo", [
            ("OG Snake",        cfg.MODO_OG_SNAKE, C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Humano vs IA",    cfg.MODO_VS_AI,    C.BTN_MODE_B, C.BTN_MODE_B_HOV),
            ("1v1 Multiplayer", cfg.MODO_1V1,      C.BTN_MODE_B, C.BTN_MODE_B_HOV),
        ])
        if not modo or not self.running:
            return

        if modo == cfg.MODO_1V1:
            p1 = self._input_nome("Nome Player 1 (WASD):", "P1")
            if not p1 or not self.running: return
            p2 = self._input_nome("Nome Player 2 (Setas):", "P2", excluir=[p1])
            if not p2 or not self.running: return
            mapa = self._menu_selecao("Arena 1v1:", [
                ("Mapa 1 - Cruzamentos", "assets/mapas/1v1_mapa1.txt"),
                ("Mapa 2 - Labirinto",   "assets/mapas/1v1_mapa2.txt"),
                ("Mapa 3 - Corredores",  "assets/mapas/1v1_mapa3.txt"),
            ], C.BTN_MODE_B, C.BTN_MODE_B_HOV)
            if not mapa or not self.running: return
            self._iniciar(p1, modo, ("Normal", 1.0), mapa, p2)

        elif modo == cfg.MODO_VS_AI:
            p1 = self._input_nome("O teu nome:", "Player")
            if not p1 or not self.running: return
            dif = self._menu_dif()
            if not dif or not self.running: return
            mapa = self._menu_selecao("Escolhe a Arena:", [
                ("Campo Livre",    "assets/mapas/campo_livre.txt"),
                ("Obstáculos",     "assets/mapas/obstaculos.txt"),
                ("Arena (bordas)", "assets/mapas/arena.txt"),
            ])
            if not mapa or not self.running: return
            self._iniciar(p1, modo, dif, mapa, p2="IA_Bot")

        else:
            p1 = self._input_nome("O teu nome:", "Player")
            if not p1 or not self.running: return
            dif = self._menu_dif()
            if not dif or not self.running: return
            mapa = self._menu_selecao("Mapa:", [
                ("Campo Livre",    "assets/mapas/campo_livre.txt"),
                ("Obstáculos",     "assets/mapas/obstaculos.txt"),
                ("Arena (bordas)", "assets/mapas/arena.txt"),
            ])
            if not mapa or not self.running: return
            self._iniciar(p1, modo, dif, mapa)

    def action_recordes(self):
        self._ecra_recordes()

    def action_ajuda(self):
        self._ecra_texto("Ajuda", [
            "WASD / Setas  —  mover",
            "ENTER         —  confirmar",
            "ESC           —  voltar",
            "",
            "Come a comida para crescer.",
            "Não batas nas paredes nem em ti.",
        ])

    def action_sair(self):
        self.running = False

    # ── Menus internos ────────────────────────────────────────────────────────

    def _menu_dif(self):
        return self._menu_selecao("Velocidade", [
            ("Normal",       ("Normal",       1.0), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Rápido",       ("Rapido",       1.5), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Muito Rápido", ("Muito Rapido", 2.0), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
        ])

    def _menu_selecao(self, titulo, itens, cor_base=None, cor_hover=None,
                      btn_w=400, btn_h=52, gap=70):
        d_base  = cor_base  or C.BTN_MODE_A
        d_hover = cor_hover or C.BTN_MODE_A_HOV
        cx      = LOGICAL_W // 2
        rects   = []
        for i, item in enumerate(itens):
            label = item[0]; valor = item[1]
            b = item[2] if len(item) > 2 else d_base
            h = item[3] if len(item) > 3 else d_hover
            rects.append((
                pygame.Rect(cx - btn_w // 2, 200 + i * gap, btn_w, btn_h),
                valor, b, h, label,
            ))

        clock = pygame.time.Clock()
        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False; return None
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self._wl(ev.pos)
                    for rect, val, _, _, _ in rects:
                        if rect.collidepoint(mpos):
                            return val
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return None

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            panel = pygame.Rect(cx - btn_w // 2 - 40, 140,
                                btn_w + 80, 80 + len(itens) * gap)
            ui_utils.draw_panel(self.logical_surface, panel, radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 175)
            mlog = self._wl(pygame.mouse.get_pos())
            for rect, _, base, hov, label in rects:
                ui_utils.draw_btn(self.logical_surface, rect, base, hov,
                                  rect.collidepoint(mlog), label, self.font_big)
            self._blit()
            clock.tick(60)

    def _input_nome(self, titulo, default="Player", excluir=None):
        """Caixa de texto para inserir nome com sugestões de sessões anteriores."""
        excluir   = excluir or []
        guardados = [n for n in self.gestor_nomes.carregar()
                     if n not in excluir][:4]

        nome, aviso = "", ""
        tique  = 0
        clock  = pygame.time.Clock()
        cx     = LOGICAL_W // 2
        box    = pygame.Rect(cx - 190, 220, 380, 48)
        sug_rects = [
            (pygame.Rect(cx - 190, 334 + i * 44, 380, 36), n)
            for i, n in enumerate(guardados)
        ]
        panel_h = 175 if not sug_rects else 199 + len(sug_rects) * 44
        painel  = pygame.Rect(cx - 220, 155, 440, panel_h)

        while self.running:
            tique += 1
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False; return None
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN:
                        n = nome.strip()
                        if not n:
                            aviso = "O nome não pode estar vazio."
                        elif not re.match(r"^[A-Za-z0-9]{1,12}$", n):
                            aviso = "Apenas letras/números, máx 12."
                        elif n in excluir:
                            aviso = "Nome já em uso pelo outro jogador."
                        else:
                            self.gestor_nomes.guardar(n)
                            return n
                    elif ev.key == pygame.K_BACKSPACE:
                        nome = nome[:-1]; aviso = ""
                    elif ev.key == pygame.K_ESCAPE:
                        return None
                    else:
                        if len(nome) < 12 and re.match(r"[A-Za-z0-9]",
                                                        ev.unicode or ""):
                            nome += ev.unicode; aviso = ""
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self._wl(ev.pos)
                    for rect, n in sug_rects:
                        if rect.collidepoint(mpos):
                            self.gestor_nomes.guardar(n)
                            return n

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            ui_utils.draw_panel(self.logical_surface, painel, radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 190)

            pygame.draw.rect(self.logical_surface, C.BG_INPUT, box, border_radius=6)
            pygame.draw.rect(self.logical_surface, C.UI_BORDER, box, 1, border_radius=6)
            cursor = "|" if (tique // 28) % 2 == 0 else " "
            ts = self.font_big.render(nome + cursor, True, C.WHITE)
            self.logical_surface.blit(ts, (box.x + 12, box.y + 10))

            self.txt_center("ENTER confirmar  ·  ESC voltar",
                            self.font_sm, C.HUD_TEXT, box.bottom + 16)

            if sug_rects:
                self.txt_center("— Nomes anteriores —", self.font_sm, C.HUD_TEXT, 314)
                mlog = self._wl(pygame.mouse.get_pos())
                for rect, n in sug_rects:
                    hover  = rect.collidepoint(mlog)
                    cor_b  = C.BTN_RECORDS_HOV if hover else C.BTN_RECORDS
                    pygame.draw.rect(self.logical_surface, cor_b, rect, border_radius=6)
                    pygame.draw.rect(self.logical_surface, C.UI_BORDER, rect, 1,
                                     border_radius=6)
                    tn = self.font_sm.render(n, True, C.WHITE)
                    self.logical_surface.blit(tn, tn.get_rect(center=rect.center))

            if aviso:
                self.txt_center(aviso, self.font_sm, (200, 90, 90), painel.bottom - 18)

            self._blit()
            clock.tick(60)

    # ── Ecrã de recordes ──────────────────────────────────────────────────────

    def _ecra_recordes(self):
        MODOS      = ["Todos", cfg.MODO_OG_SNAKE, cfg.MODO_VS_AI, cfg.MODO_1V1]
        filtro     = "Todos"
        btn_voltar = pygame.Rect(LOGICAL_W // 2 - 90, LOGICAL_H - 62, 180, 42)
        btn_w_f, btn_gap = 108, 8
        total_bw  = len(MODOS) * btn_w_f + (len(MODOS) - 1) * btn_gap
        botoes_f  = [
            (pygame.Rect(LOGICAL_W // 2 - total_bw // 2 + i * (btn_w_f + btn_gap),
                         130, btn_w_f, 30), m)
            for i, m in enumerate(MODOS)
        ]
        clock = pygame.time.Clock()
        while self.running:
            mf     = None if filtro == "Todos" else filtro
            scores = RecordsManager().ler_pontuacoes(modo_filtrar=mf)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False; return
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self._wl(ev.pos)
                    if btn_voltar.collidepoint(mpos): return
                    for rect, m in botoes_f:
                        if rect.collidepoint(mpos): filtro = m

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            ui_utils.draw_panel(self.logical_surface,
                                pygame.Rect(50, 80, LOGICAL_W - 100, LOGICAL_H - 168),
                                radius=12)
            self.txt_center("Recordes", self.font_big, C.HUD_ACCENT, 108)

            mlog = self._wl(pygame.mouse.get_pos())
            for rect, m in botoes_f:
                ativo  = filtro == m
                cor_b  = (55, 110, 175) if ativo else (
                    C.BTN_MODE_A_HOV if rect.collidepoint(mlog) else C.BTN_MODE_A
                )
                ui_utils.draw_btn(self.logical_surface, rect, cor_b, cor_b,
                                  False, m, self.font_sm)

            if not scores:
                self.txt_center("Sem recordes para este modo.",
                                self.font_sm, C.HUD_TEXT, 210)
            else:
                cab = f"  # {'Nome':<12} {'Modo':<13} {'Dif':<13} {'Pts':>5}"
                self.logical_surface.blit(
                    self.font_sm.render(cab, True, C.HUD_TEXT_MAIN), (80, 172)
                )
                pygame.draw.line(self.logical_surface, C.UI_BORDER,
                                 (80, 192), (LOGICAL_W - 80, 192), 1)
                for i, p in enumerate(scores[:10]):
                    linha = (f"{i+1:>3} {p['nome']:<12} {p['modo']:<13}"
                             f" {p['dificuldade']:<13} {p['pontuacao']:>5}")
                    cor   = C.HUD_SCORE if i == 0 else C.HUD_TEXT
                    self.logical_surface.blit(
                        self.font_sm.render(linha, True, cor), (80, 198 + i * 26)
                    )

            ui_utils.draw_btn(self.logical_surface, btn_voltar,
                              C.BTN_PLAY, C.BTN_PLAY_HOV,
                              btn_voltar.collidepoint(mlog), "Voltar", self.font_sm)
            self._blit()
            clock.tick(30)

    # ── Iniciar jogo ──────────────────────────────────────────────────────────

    def _iniciar(self, p1, modo, dif, mapa, p2=None):
        nome_dif, mult = dif
        saved  = self.screen.get_size()
        clock  = pygame.time.Clock()
        # Fade out antes de iniciar
        _fade_out(self.screen, self.logical_surface, self.logical_size,
                  duration=0.22, clock=clock)
        repetir = True
        while repetir and self.running:
            repetir = Game(
                player_name=p1, player2_name=p2, modo=modo,
                dificuldade=nome_dif, velocidade_mult=mult, mapa_tipo=mapa,
            ).run()
        try:
            self.screen = pygame.display.set_mode(saved, pygame.RESIZABLE)
        except Exception:
            self.screen = pygame.display.set_mode(
                (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE
            )
        self.recenter_buttons()
        # Fade in de regresso ao menu
        _fade_in(self.screen, self.logical_surface, self.logical_size,
                 duration=0.20, clock=clock)

    # ── Ecrã de texto (ajuda, etc.) ───────────────────────────────────────────

    def _ecra_texto(self, titulo, linhas, cor_titulo=None):
        cor_titulo = cor_titulo or C.HUD_TEXT_MAIN
        btn   = pygame.Rect(LOGICAL_W // 2 - 90, LOGICAL_H - 72, 180, 42)
        clock = pygame.time.Clock()
        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn.collidepoint(self._wl(ev.pos)):
                        return

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            ui_utils.draw_panel(self.logical_surface,
                                pygame.Rect(50, 80, LOGICAL_W - 100, LOGICAL_H - 180),
                                radius=12)
            self.txt_center(titulo, self.font_big, cor_titulo, 110)
            for i, linha in enumerate(linhas):
                self.txt_center(linha, self.font_sm, C.HUD_TEXT, 148 + i * 28)
            mlog = self._wl(pygame.mouse.get_pos())
            ui_utils.draw_btn(self.logical_surface, btn,
                              C.BTN_PLAY, C.BTN_PLAY_HOV,
                              btn.collidepoint(mlog), "Voltar", self.font_sm)
            self._blit()
            clock.tick(30)

    # ── Setup dos botões ──────────────────────────────────────────────────────

    def recenter_buttons(self) -> None:
        """Recria os botões com animação de slide-in escalonada."""
        labels  = ["Jogar", "Recordes", "Ajuda", "Sair"]
        actions = [self.action_jogar, self.action_recordes,
                   self.action_ajuda,  self.action_sair]
        colors  = [C.BTN_PLAY,     C.BTN_RECORDS,     C.BTN_HELP,     C.BTN_QUIT]
        hovers  = [C.BTN_PLAY_HOV, C.BTN_RECORDS_HOV, C.BTN_HELP_HOV, C.BTN_QUIT_HOV]
        self.buttons = [
            Button(
                lab,
                LOGICAL_W // 2 - 140,
                LOGICAL_H // 2 - 110 + i * 78,
                280, 58,
                colors[i], hovers[i], actions[i], 28,
                slide_delay=i * _SLIDE_STAGGER,   # entrada escalonada
            )
            for i, lab in enumerate(labels)
        ]
        self._btn_elapsed = 0.0

    # ── Loop principal ────────────────────────────────────────────────────────

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            dt      = clock.tick(60) / 1000.0
            dt      = min(dt, 0.1)
            events  = pygame.event.get()

            self._title_t    += dt
            self._btn_elapsed += dt
            for btn in self.buttons:
                btn.advance(dt)

            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (ev.w, ev.h), pygame.RESIZABLE
                    )

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            draw_title(
                self.logical_surface, self.font_title,
                LOGICAL_W, LOGICAL_H // 2 - 175,
                t=self._title_t,
            )
            sep_y = LOGICAL_H // 2 - 130
            pygame.draw.line(
                self.logical_surface, C.UI_BORDER,
                (LOGICAL_W // 2 - 140, sep_y), (LOGICAL_W // 2 + 140, sep_y), 1,
            )

            mlog = self._wl(pygame.mouse.get_pos())
            for btn in self.buttons:
                btn.draw(self.logical_surface, mlog)

            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    ml = self._wl(ev.pos)
                    if ml != (-1, -1):
                        for btn in self.buttons:
                            if btn.check_click(ml):
                                break

            self._blit()

        pygame.quit()
        sys.exit()