# Descrição: Interface gráfica do menu principal, gerindo navegação, definições da partida e a transição para o motor de jogo.
# src/game/menu.py
import pygame
import sys
import re
import game.config as cfg
import game.config as C
from game.engine import Game
from game.records import RecordsManager

pygame.init()

LOGICAL_W = cfg.SCREEN_WIDTH
LOGICAL_H = cfg.SCREEN_HEIGHT


# ── Auxiliares de Desenho (Helpers) ───────────────────────────────────────────
def draw_bg(surface, w, h):
    """Desenha o fundo base com uma grelha decorativa subtil."""
    surface.fill(C.BG_DARK)
    for x in range(0, w, 20):
        pygame.draw.line(surface, C.GRID_LINE, (x, 0), (x, h))
    for y in range(0, h, 20):
        pygame.draw.line(surface, C.GRID_LINE, (0, y), (w, y))


def draw_panel(surface, rect, radius=10):
    """Renderiza um painel translúcido com bordas arredondadas (estilo Card)."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*C.BG_PANEL, 245), s.get_rect(), border_radius=radius)
    pygame.draw.rect(s, (*C.UI_BORDER, 200), s.get_rect(), 1, border_radius=radius)
    surface.blit(s, rect.topleft)


def draw_btn(surface, rect, base, hover, is_hover, text, font, radius=8):
    """Desenha um botão com estilo "flat", efeito de profundidade 3D e reativo ao hover do rato."""
    col = hover if is_hover else base
    pygame.draw.rect(surface, col, rect, border_radius=radius)
    
    # Adiciona uma linha mais clara no topo para criar uma ilusão de profundidade
    hi = tuple(min(c + 30, 255) for c in col)
    pygame.draw.line(surface, hi,
                     (rect.x + radius, rect.y + 1),
                     (rect.right - radius, rect.y + 1))
    
    # Borda exterior do botão
    pygame.draw.rect(surface, tuple(max(c - 20, 0) for c in col),
                     rect, 1, border_radius=radius)
                     
    txt = font.render(text, True, C.WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))


def draw_title(surface, font_big, font_small, w, y):
    """Renderiza o título do jogo de forma estática e centrada."""
    main = font_big.render("Snake", True, C.TITLE_COLOR)
    cx   = w // 2
    surface.blit(main, main.get_rect(center=(cx, y)))


# ── Componente de Botão ───────────────────────────────────────────────────────
class Button:
    """Classe que representa um elemento interativo da interface, com deteção de colisão e callbacks."""
    def __init__(self, text, x, y, w, h, color, hover_color, action=None, font_size=30):
        self.text        = text
        self.rect        = pygame.Rect(int(x), int(y), int(w), int(h))
        self.color       = color
        self.hover_color = hover_color
        self.action      = action  # Função a ser executada ao clicar
        self.font        = pygame.font.SysFont("Consolas", font_size)

    def draw(self, surface, mouse_pos=None):
        if mouse_pos is None: mouse_pos = (-1, -1)
        draw_btn(surface, self.rect, self.color, self.hover_color,
                 self.rect.collidepoint(mouse_pos), self.text, self.font)

    def check_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            if self.action: self.action()
            return True
        return False


# ── Gestor do Menu Principal ──────────────────────────────────────────────────
class Menu:
    """Gere os ecrãs iniciais, submenus de configuração e o redimensionamento dinâmico."""
    def __init__(self):
        self.screen = pygame.display.set_mode(
            (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Snake")
        self.running      = True
        self.logical_size = (LOGICAL_W, LOGICAL_H)
        self.logical_surface = pygame.Surface(self.logical_size)

        self.font_title = pygame.font.SysFont("Consolas", 52)
        self.font_big   = pygame.font.SysFont("Consolas", 30)
        self.font_sm    = pygame.font.SysFont("Consolas", 18)

        self.recenter_buttons()

    # ── Sistema de Escala e Resolução (Letterboxing) ──────────────────────────
    def window_to_logical(self, pos):
        """Converte as coordenadas do rato na janela física para as coordenadas da superfície lógica."""
        win_w, win_h = self.screen.get_size()
        log_w, log_h = self.logical_size
        if not all([log_w, log_h, win_w, win_h]): return (-1, -1)
        
        scale  = min(win_w / log_w, win_h / log_h)
        sw, sh = int(log_w * scale), int(log_h * scale)
        ox, oy = (win_w - sw) // 2, (win_h - sh) // 2
        xw, yw = pos
        
        if not (ox <= xw < ox + sw and oy <= yw < oy + sh): return (-1, -1)
        
        return (max(0, min(log_w - 1, int((xw - ox) / scale))),
                max(0, min(log_h - 1, int((yw - oy) / scale))))

    def safe_blit(self, src):
        """Escala a superfície lógica e desenha-a no centro da janela física, preenchendo as margens com preto."""
        win_w, win_h = self.screen.get_size()
        if win_w < 32 or win_h < 32:
            pygame.event.pump(); pygame.time.wait(100); return
            
        log_w, log_h = self.logical_size
        scale  = min(win_w / log_w, win_h / log_h)
        sw, sh = max(1, int(log_w * scale)), max(1, int(log_h * scale))
        
        try:    scaled = pygame.transform.smoothscale(src, (sw, sh))
        except: scaled = pygame.transform.scale(src, (sw, sh))
        
        ox = (win_w - sw) // 2
        oy = (win_h - sh) // 2
        
        self.screen.fill(C.BLACK)
        self.screen.blit(scaled, (ox, oy))
        pygame.display.flip()

    def txt_center(self, text, font, color, y):
        """Auxiliar rápido para centrar texto horizontalmente num eixo Y específico."""
        s = font.render(text, True, color)
        self.logical_surface.blit(s, s.get_rect(center=(LOGICAL_W // 2, y)))

    # ── Ações Principais (Navegação) ──────────────────────────────────────────
    def action_jogar(self):
        """Orquestra o fluxo de configuração do jogo (Modo -> Nomes -> Dificuldade -> Mapa)."""
        modo = self._menu_modo()
        if not modo or not self.running: return

        if modo == "1v1":
            # ... mantém o teu código original do 1v1 aqui ...
            p1 = self._input_nome("Nome Player 1 (WASD):", "P1")
            if not p1 or not self.running: return
            p2 = self._input_nome("Nome Player 2 (Setas):", "P2")
            if not p2 or not self.running: return
            mapa = self._menu_lista("Arena 1v1:", [
                ("Mapa 1 - Cruzamentos", "assets/maps/1v1_mapa1.txt"),
                ("Mapa 2 - Labirinto",   "assets/maps/1v1_mapa2.txt"),
                ("Mapa 3 - Corredores",  "assets/maps/1v1_mapa3.txt"),
            ], C.BTN_MODE_B, C.BTN_MODE_B_HOV)
            if not mapa or not self.running: return
            self._iniciar(p1, modo, ("Normal", 1.0), mapa, p2)

        elif modo == "Vs AI":
            # FLUXO PARA O MODO CONTRA O BOT
            p1 = self._input_nome("O teu nome:", "Player")
            if not p1 or not self.running: return
            
            dif = self._menu_dif() # Escolhe a velocidade da partida
            if not dif or not self.running: return
            
            mapa = self._menu_lista("Escolhe a Arena:", [
                ("Campo Livre",    "assets/maps/arena.txt"),
                ("Obstáculos",     "assets/maps/obstaculos.txt"),
                ("Arena (bordas)", "assets/maps/arena.txt"),
            ])
            if not mapa or not self.running: return
            
            # Iniciamos o jogo passando "Bot" ou "CPU" como nome do Player 2
            self._iniciar(p1, modo, dif, mapa, p2="IA_Bot")

        else:
            # OG Snake e Snake Torre
            p1 = self._input_nome("O teu nome:", "Player")
            if not p1 or not self.running: return
            dif = self._menu_dif()
            if not dif or not self.running: return
            if modo == "Snake Torre":
                self._iniciar(p1, modo, dif, "assets/maps/arena.txt")
            else:
                mapa = self._menu_lista("Mapa:", [
                    ("Campo Livre",    "assets/maps/arena.txt"),
                    ("Obstáculos",     "assets/maps/obstaculos.txt"),
                    ("Arena (bordas)", "assets/maps/arena.txt"),
                ])
                if not mapa or not self.running: return
                self._iniciar(p1, modo, dif, mapa)

    def action_recordes(self):
        """Lê e apresenta a tabela de pontuações mais altas (Top 10)."""
        scores = RecordsManager().ler_pontuacoes()
        linhas = (
            [f"{'Nome':<12} {'Modo':<12} {'Pts':>5}",
             "─" * 32] +
            [f"{p.get('nome','-'):<12} {p.get('modo','-'):<12} {p.get('pontuacao',0):>5}"
             for p in scores[:10]]
        ) if scores else ["Nenhum recorde ainda."]
        self._ecra_texto("Recordes", linhas, C.HUD_ACCENT)

    def action_ajuda(self):
        """Apresenta as instruções de jogo."""
        self._ecra_texto("Ajuda", [
            "WASD / Setas  —  mover",
            "ENTER         —  confirmar",
            "ESC           —  voltar",
            "",
            "Come a comida para crescer.",
            "Nao batas nas paredes nem em ti.",
        ])

    def action_sair(self): 
        """Termina a execução da aplicação."""
        self.running = False

    # ── Lógica de Submenus (Mini-Loops) ───────────────────────────────────────
    def _menu_modo(self):
        modos = [
            ("OG Snake",        "OG Snake",    C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Humano vs IA",    "Vs AI",       C.BTN_MODE_B, C.BTN_MODE_B_HOV), # Novo botão!
            ("Snake Torre",     "Snake Torre", C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("1v1 Multiplayer", "1v1",         C.BTN_MODE_B, C.BTN_MODE_B_HOV),
        ]
        return self._menu_botoes("Modo de jogo", modos)

    def _menu_dif(self):
        difs = [
            ("Normal",       ("Normal",       1.0), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Rápido",       ("Rapido",       1.5), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
            ("Muito Rápido", ("Muito Rapido", 2.0), C.BTN_MODE_A, C.BTN_MODE_A_HOV),
        ]
        return self._menu_botoes("Velocidade", difs)

    def _menu_botoes(self, titulo, itens):
        """Ciclo (loop) genérico temporário para apresentar um submenu interativo. Retorna o valor escolhido."""
        btn_w, btn_h, gap = 360, 52, 74
        cx = LOGICAL_W // 2
        rects = [
            (pygame.Rect(cx - btn_w // 2, 200 + i * gap, btn_w, btn_h), val, base, hov)
            for i, (_, val, base, hov) in enumerate(itens)
        ]
        labels = [label for (label, _, _, _) in itens]
        clock  = pygame.time.Clock()

        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:            self.running = False; return None
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self.window_to_logical(ev.pos)
                    for rect, val, _, _ in rects:
                        if rect.collidepoint(mpos): return val
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None

            draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            panel = pygame.Rect(cx - 210, 140, 420, 80 + len(itens) * gap)
            draw_panel(self.logical_surface, panel, radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 175)

            mlog = self.window_to_logical(pygame.mouse.get_pos())
            for (rect, _, base, hov), label in zip(rects, labels):
                draw_btn(self.logical_surface, rect, base, hov,
                         rect.collidepoint(mlog), label, self.font_big)

            self.safe_blit(self.logical_surface)
            clock.tick(60)

    def _menu_lista(self, titulo, opcoes, cor_base=None, cor_hover=None):
        """Variante do menu de botões para listar mapas e opções com caminhos de ficheiro."""
        cor_base  = cor_base  or C.BTN_MODE_A
        cor_hover = cor_hover or C.BTN_MODE_A_HOV
        btn_w, btn_h, gap = 480, 50, 70
        cx = LOGICAL_W // 2
        rects = [
            (pygame.Rect(cx - btn_w // 2, 200 + i * gap, btn_w, btn_h), path)
            for i, (_, path) in enumerate(opcoes)
        ]
        labels = [label for (label, _) in opcoes]
        clock  = pygame.time.Clock()

        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:            self.running = False; return None
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mpos = self.window_to_logical(ev.pos)
                    for rect, path in rects:
                        if rect.collidepoint(mpos): return path
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None

            draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            panel = pygame.Rect(cx - 260, 140, 520, 80 + len(opcoes) * gap)
            draw_panel(self.logical_surface, panel, radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 175)

            mlog = self.window_to_logical(pygame.mouse.get_pos())
            for (rect, _), label in zip(rects, labels):
                draw_btn(self.logical_surface, rect, cor_base, cor_hover,
                         rect.collidepoint(mlog), label, self.font_big)

            self.safe_blit(self.logical_surface)
            clock.tick(60)

    def _input_nome(self, titulo, default="Player"):
        """Ciclo dedicado à captura de input do teclado (texto) com regras de validação simples."""
        nome, aviso = "", ""
        box_w, box_h = 380, 48
        cx  = LOGICAL_W // 2
        box = pygame.Rect(cx - box_w // 2, 240, box_w, box_h)
        t   = 0
        clock = pygame.time.Clock()

        while self.running:
            t += 1
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:            self.running = False; return None
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
                    elif ev.key == pygame.K_ESCAPE:    return None
                    else:
                        if len(nome) < 12 and re.match(r"[A-Za-z0-9 ]", ev.unicode):
                            nome += ev.unicode; aviso = ""

            draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            panel = pygame.Rect(cx - 220, 170, 440, 200)
            draw_panel(self.logical_surface, panel, radius=12)
            self.txt_center(titulo, self.font_big, C.HUD_TEXT_MAIN, 210)

            # Renderização do campo de texto com cursor a piscar
            pygame.draw.rect(self.logical_surface, C.BG_INPUT, box, border_radius=6)
            pygame.draw.rect(self.logical_surface, C.UI_BORDER, box, 1, border_radius=6)
            cursor = "|" if (t // 28) % 2 == 0 else " "
            ts = self.font_big.render(nome + cursor, True, C.WHITE)
            self.logical_surface.blit(ts, (box.x + 12, box.y + 10))

            self.txt_center("ENTER  confirmar  ·  ESC  voltar",
                            self.font_sm, C.HUD_TEXT, box.bottom + 28)
            if aviso:
                self.txt_center(aviso, self.font_sm, (200, 90, 90), box.bottom + 54)

            self.safe_blit(self.logical_surface)
            clock.tick(60)

    def _iniciar(self, p1, modo, dif, mapa, p2=None):
        """Instancia e arranca a classe Game principal. Ao voltar, restaura o ecrã do menu."""
        nome_dif, mult = dif
        saved = self.screen.get_size()
        
        Game(player_name=p1, player2_name=p2, modo=modo,
             dificuldade=nome_dif, velocidade_mult=mult, mapa_tipo=mapa).run()
             
        try:    self.screen = pygame.display.set_mode(saved, pygame.RESIZABLE)
        except: self.screen = pygame.display.set_mode(
                    (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        self.recenter_buttons()

    def _ecra_texto(self, titulo, linhas, cor_titulo=None):
        """Cria um ecrã para ler informação, como Recordes ou Ajuda, apenas com um botão 'Voltar'."""
        cor_titulo = cor_titulo or C.HUD_TEXT_MAIN
        btn = pygame.Rect(LOGICAL_W // 2 - 90, LOGICAL_H - 72, 180, 42)
        clock = pygame.time.Clock()

        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:   self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn.collidepoint(self.window_to_logical(ev.pos)): return

            draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)
            panel = pygame.Rect(50, 80, LOGICAL_W - 100, LOGICAL_H - 180)
            draw_panel(self.logical_surface, panel, radius=12)
            self.txt_center(titulo, self.font_big, cor_titulo, 110)

            for i, linha in enumerate(linhas):
                self.txt_center(linha, self.font_sm, C.HUD_TEXT, 148 + i * 28)

            mlog = self.window_to_logical(pygame.mouse.get_pos())
            draw_btn(self.logical_surface, btn, C.BTN_PLAY, C.BTN_PLAY_HOV,
                     btn.collidepoint(mlog), "Voltar", self.font_sm)

            self.safe_blit(self.logical_surface)
            clock.tick(30)

    # ── Setup Inicial & Ciclo de Vida do Menu ─────────────────────────────────
    def recenter_buttons(self):
        """Instancia e reposiciona os botões do ecrã inicial."""
        labels  = ["Jogar", "Recordes", "Ajuda", "Sair"]
        actions = [self.action_jogar, self.action_recordes,
                   self.action_ajuda, self.action_sair]
        colors  = [C.BTN_PLAY,     C.BTN_RECORDS,     C.BTN_HELP,     C.BTN_QUIT]
        hovers  = [C.BTN_PLAY_HOV, C.BTN_RECORDS_HOV, C.BTN_HELP_HOV, C.BTN_QUIT_HOV]
        self.buttons = []
        cx = LOGICAL_W // 2
        for i, lab in enumerate(labels):
            self.buttons.append(
                Button(lab, cx - 140, LOGICAL_H // 2 - 110 + i * 78,
                       280, 58, colors[i], hovers[i], actions[i], 28))

    def run(self):
        """Ciclo principal de eventos e renderização do menu inicial."""
        clock = pygame.time.Clock()
        while self.running:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:       self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)

            draw_bg(self.logical_surface, LOGICAL_W, LOGICAL_H)

            # Renderiza o Título do jogo
            draw_title(self.logical_surface, self.font_title, self.font_sm,
                       LOGICAL_W, LOGICAL_H // 2 - 175)

            # Renderiza o separador fino acima dos botões
            sep_y = LOGICAL_H // 2 - 130
            pygame.draw.line(self.logical_surface, C.UI_BORDER,
                             (LOGICAL_W // 2 - 140, sep_y),
                             (LOGICAL_W // 2 + 140, sep_y), 1)

            # Atualiza os estados de hover e desenha os botões
            mlog = self.window_to_logical(pygame.mouse.get_pos())
            for btn in self.buttons:
                btn.draw(self.logical_surface, mlog)

            # Regista os cliques do rato nos botões do ecrã inicial
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    ml = self.window_to_logical(ev.pos)
                    if ml != (-1, -1):
                        for btn in self.buttons:
                            if btn.check_click(ml): break

            self.safe_blit(self.logical_surface)
            clock.tick(60)
            
        pygame.quit(); sys.exit()