# src/game/ui/menu.py
import pygame
import sys
import re
import game.config as cfg
import game.config as C
from game.core.engine   import Game
from game.core.records  import RecordsManager
from game.ui            import ui_utils

pygame.init()

LOGICAL_W = cfg.SCREEN_WIDTH
LOGICAL_H = cfg.SCREEN_HEIGHT


def draw_title(surface, font_big, w, y):
    main = font_big.render("Snake", True, C.TITLE_COLOR)
    surface.blit(main, main.get_rect(center=(w // 2, y)))


class Button:
    def __init__(self, text, x, y, w, h, color, hover_color, action=None, font_size=30):
        self.text        = text
        self.rect        = pygame.Rect(int(x), int(y), int(w), int(h))
        self.color       = color
        self.hover_color = hover_color
        self.action      = action
        self.font        = pygame.font.SysFont("Consolas", font_size)

    def draw(self, surface, mouse_pos=None):
        if mouse_pos is None: mouse_pos = (-1, -1)
        ui_utils.draw_btn(surface, self.rect, self.color, self.hover_color,
                          self.rect.collidepoint(mouse_pos), self.text, self.font)

    def check_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            if self.action: self.action()
            return True
        return False


class Menu:
    def __init__(self):
        self.screen = pygame.display.set_mode(
            (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Snake")
        self.running         = True
        self.logical_size    = (LOGICAL_W, LOGICAL_H)
        self.logical_surface = pygame.Surface(self.logical_size)
        self.font_title = pygame.font.SysFont("Consolas", 52)
        self.font_big   = pygame.font.SysFont("Consolas", 30)
        self.font_sm    = pygame.font.SysFont("Consolas", 18)
        self.recenter_buttons()

    def _wl(self, pos):
        return ui_utils.window_to_logical(self.screen, self.logical_size, pos)

    def _blit(self):
        ui_utils.blit_scaled(self.screen, self.logical_surface, self.logical_size)

    def txt_center(self, text, font, color, y):
        s = font.render(text, True, color)
        self.logical_surface.blit(s, s.get_rect(center=(LOGICAL_W // 2, y)))

    # ── Acoes ─────────────────────────────────────────────────────────────────
    def action_jogar(self):
        modo = self._menu_selecao("Modo de jogo", [
            ("OG Snake",        cfg.MODO_OG_SNAKE,    C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Humano vs IA",    cfg.MODO_VS_AI,       C.BTN_MODE_B, C.BTN_MODE_B_HOV),
            ("Snake Torre",     cfg.MODO_SNAKE_TORRE, C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("1v1 Multiplayer", cfg.MODO_1V1,         C.BTN_MODE_B, C.BTN_MODE_B_HOV),
        ])
        if not modo or not self.running: return

        if modo == cfg.MODO_1V1:
            p1 = self._input_nome("Nome Player 1 (WASD):", "P1")
            if not p1 or not self.running: return
            p2 = self._input_nome("Nome Player 2 (Setas):", "P2")
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
                ("Obstaculos",     "assets/mapas/obstaculos.txt"),
                ("Arena (bordas)", "assets/mapas/arena.txt"),
            ])
            if not mapa or not self.running: return
            self._iniciar(p1, modo, dif, mapa, p2="IA_Bot")

        else:
            p1 = self._input_nome("O teu nome:", "Player")
            if not p1 or not self.running: return
            dif = self._menu_dif()
            if not dif or not self.running: return
            if modo == cfg.MODO_SNAKE_TORRE:
                self._iniciar(p1, modo, dif, "assets/mapas/arena.txt")
            else:
                mapa = self._menu_selecao("Mapa:", [
                    ("Campo Livre",    "assets/mapas/campo_livre.txt"),
                    ("Obstaculos",     "assets/mapas/obstaculos.txt"),
                    ("Arena (bordas)", "assets/mapas/arena.txt"),
                ])
                if not mapa or not self.running: return
                self._iniciar(p1, modo, dif, mapa)

    def action_recordes(self):
        scores = RecordsManager().ler_pontuacoes()
        linhas = (
            [f"{'Nome':<12} {'Modo':<12} {'Pts':>5}", "─" * 32] +
            [f"{p.get('nome','-'):<12} {p.get('modo','-'):<12} {p.get('pontuacao',0):>5}"
             for p in scores[:10]]
        ) if scores else ["Nenhum recorde ainda."]
        self._ecra_texto("Recordes", linhas, C.HUD_ACCENT)

    def action_ajuda(self):
        self._ecra_texto("Ajuda", [
            "WASD / Setas  —  mover",
            "ENTER         —  confirmar",
            "ESC           —  voltar",
            "",
            "Come a comida para crescer.",
            "Nao batas nas paredes nem em ti.",
        ])

    def action_sair(self):
        self.running = False

    # ── Menus internos ────────────────────────────────────────────────────────
    def _menu_dif(self):
        return self._menu_selecao("Velocidade", [
            ("Normal",       ("Normal",       1.0), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Rapido",       ("Rapido",       1.5), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Muito Rapido", ("Muito Rapido", 2.0), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
        ])

    def _menu_selecao(self, titulo, itens, cor_base=None, cor_hover=None,
                      btn_w=400, btn_h=52, gap=70):
        d_base  = cor_base  or C.BTN_MODE_A
        d_hover = cor_hover or C.BTN_MODE_A_HOV
        cx = LOGICAL_W // 2
        rects = []
        for i, item in enumerate(itens):
            label = item[0]; valor = item[1]
            b = item[2] if len(item) > 2 else d_base
            h = item[3] if len(item) > 3 else d_hover
            rects.append((pygame.Rect(cx - btn_w//2, 200 + i*gap, btn_w, btn_h), valor, b, h, label))

        clock = pygame.time.Clock()
        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: self.running = False; return None
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self._wl(ev.pos)
                    for rect, val, _, _, _ in rects:
                        if rect.collidepoint(mpos): return val
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            panel = pygame.Rect(cx - btn_w//2 - 40, 140, btn_w + 80, 80 + len(itens)*gap)
            ui_utils.draw_panel(self.logical_surface, panel, radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 175)
            mlog = self._wl(pygame.mouse.get_pos())
            for rect, _, base, hov, label in rects:
                ui_utils.draw_btn(self.logical_surface, rect, base, hov,
                                  rect.collidepoint(mlog), label, self.font_big)
            self._blit()
            clock.tick(60)

    def _input_nome(self, titulo, default="Player"):
        nome, aviso = "", ""
        box_w, box_h = 380, 48
        cx  = LOGICAL_W // 2
        box = pygame.Rect(cx - box_w//2, 240, box_w, box_h)
        t   = 0
        clock = pygame.time.Clock()
        while self.running:
            t += 1
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: self.running = False; return None
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN:
                        if not nome:
                            aviso = "O nome nao pode estar vazio."
                        elif not re.match(r"^[A-Za-z0-9]{1,12}$", nome):
                            aviso = "Apenas letras/numeros, max 12."
                        else:
                            return nome
                    elif ev.key == pygame.K_BACKSPACE: nome = nome[:-1]; aviso = ""
                    elif ev.key == pygame.K_ESCAPE: return None
                    else:
                        if len(nome) < 12 and re.match(r"[A-Za-z0-9 ]", ev.unicode):
                            nome += ev.unicode; aviso = ""

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            ui_utils.draw_panel(self.logical_surface, pygame.Rect(cx-220, 170, 440, 200), radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 210)
            pygame.draw.rect(self.logical_surface, C.BG_INPUT, box, border_radius=6)
            pygame.draw.rect(self.logical_surface, C.UI_BORDER, box, 1, border_radius=6)
            cursor = "|" if (t // 28) % 2 == 0 else " "
            ts = self.font_big.render(nome + cursor, True, C.WHITE)
            self.logical_surface.blit(ts, (box.x + 12, box.y + 10))
            self.txt_center("ENTER  confirmar  ·  ESC  voltar", self.font_sm, C.HUD_TEXT, box.bottom+28)
            if aviso:
                self.txt_center(aviso, self.font_sm, (200,90,90), box.bottom+54)
            self._blit()
            clock.tick(60)

    def _iniciar(self, p1, modo, dif, mapa, p2=None):
        nome_dif, mult = dif
        saved = self.screen.get_size()
        Game(player_name=p1, player2_name=p2, modo=modo,
             dificuldade=nome_dif, velocidade_mult=mult, mapa_tipo=mapa).run()
        try:    self.screen = pygame.display.set_mode(saved, pygame.RESIZABLE)
        except: self.screen = pygame.display.set_mode(
                    (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        self.recenter_buttons()

    def _ecra_texto(self, titulo, linhas, cor_titulo=None):
        cor_titulo = cor_titulo or C.HUD_TEXT_MAIN
        btn = pygame.Rect(LOGICAL_W//2 - 90, LOGICAL_H - 72, 180, 42)
        clock = pygame.time.Clock()
        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn.collidepoint(self._wl(ev.pos)): return

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            ui_utils.draw_panel(self.logical_surface,
                                pygame.Rect(50, 80, LOGICAL_W-100, LOGICAL_H-180), radius=12)
            self.txt_center(titulo, self.font_big, cor_titulo, 110)
            for i, linha in enumerate(linhas):
                self.txt_center(linha, self.font_sm, C.HUD_TEXT, 148 + i*28)
            mlog = self._wl(pygame.mouse.get_pos())
            ui_utils.draw_btn(self.logical_surface, btn, C.BTN_PLAY, C.BTN_PLAY_HOV,
                              btn.collidepoint(mlog), "Voltar", self.font_sm)
            self._blit()
            clock.tick(30)

    # ── Setup ─────────────────────────────────────────────────────────────────
    def recenter_buttons(self):
        labels  = ["Jogar", "Recordes", "Ajuda", "Sair"]
        actions = [self.action_jogar, self.action_recordes, self.action_ajuda, self.action_sair]
        colors  = [C.BTN_PLAY,     C.BTN_RECORDS,     C.BTN_HELP,     C.BTN_QUIT]
        hovers  = [C.BTN_PLAY_HOV, C.BTN_RECORDS_HOV, C.BTN_HELP_HOV, C.BTN_QUIT_HOV]
        self.buttons = [
            Button(lab, LOGICAL_W//2-140, LOGICAL_H//2-110+i*78,
                   280, 58, colors[i], hovers[i], actions[i], 28)
            for i, lab in enumerate(labels)
        ]

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT: self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)

            ui_utils.draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            draw_title(self.logical_surface, self.font_title, LOGICAL_W, LOGICAL_H//2 - 175)
            sep_y = LOGICAL_H//2 - 130
            pygame.draw.line(self.logical_surface, C.UI_BORDER,
                             (LOGICAL_W//2-140, sep_y), (LOGICAL_W//2+140, sep_y), 1)

            mlog = self._wl(pygame.mouse.get_pos())
            for btn in self.buttons:
                btn.draw(self.logical_surface, mlog)

            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    ml = self._wl(ev.pos)
                    if ml != (-1, -1):
                        for btn in self.buttons:
                            if btn.check_click(ml): break

            self._blit()
            clock.tick(60)
        pygame.quit(); sys.exit()