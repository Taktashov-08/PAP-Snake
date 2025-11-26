# src/game/menu.py
import pygame
import sys
import re
import game.config as cfg

from game.engine import Game
from game.records import RecordsManager
from game.config import WHITE, BLACK, GREEN, RED, BLUE

pygame.init()

# Logical surface size (fixed game logic resolution)
LOGICAL_W = cfg.SCREEN_WIDTH
LOGICAL_H = cfg.SCREEN_HEIGHT


class Button:
    """Botão que trabalha em coordenadas lógicas (colocado em blocos/px lógicos)."""
    def __init__(self, text, x, y, w, h, color, hover_color, action=None, font_size=36):
        # x,y,w,h são em coordenadas lógicas (px)
        self.text = text
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.font = pygame.font.SysFont(None, font_size)

    def draw(self, surface, mouse_pos_logical=None):
        """Desenha o botão na surface lógica. mouse_pos_logical é (x,y) lógico."""
        if mouse_pos_logical is None:
            mouse_pos_logical = (-1, -1)
        is_hover = self.rect.collidepoint(mouse_pos_logical)
        color = self.hover_color if is_hover else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_click(self, mouse_pos_logical):
        """Verifica clique usando coords lógicas. Retorna True se executou action."""
        if self.rect.collidepoint(mouse_pos_logical):
            if self.action:
                self.action()
            return True
        return False


class Menu:
    def __init__(self):
        # janela real (redimensionável) — mas a lógica é fixa LOGICAL_W x LOGICAL_H
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Snake Menu")
        self.running = True
        self.bg_color = (30, 30, 30)

        # superfície lógica onde desenhamos sempre
        self.logical_size = (LOGICAL_W, LOGICAL_H)
        self.logical_surface = pygame.Surface(self.logical_size)

        # fontes
        self.title_font = pygame.font.SysFont(None, 60)
        self.big_font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 24)
        # fallback para fontes monoespaçadas em todas as plataformas
        try:
            self.mono_font = pygame.font.SysFont("Consolas", 24)
        except Exception:
            self.mono_font = pygame.font.SysFont(None, 24)

        # estado
        self.player_name = "Player"

        # cria botões (recenter calcula posições lógicas)
        self.recenter_buttons()

    # ---------- helpers ----------
    def window_to_logical(self, pos):
        """
        Converte pos (window coords) -> logical coords (inteiros) usando letterbox (centering).
        Se a posição estiver nas barras pretas devolve (-1,-1).
        """
        win_w, win_h = self.screen.get_size()
        log_w, log_h = self.logical_size

        # proteção
        if log_w == 0 or log_h == 0 or win_w == 0 or win_h == 0:
            return (-1, -1)

        scale = min(win_w / log_w, win_h / log_h)
        scaled_w = int(log_w * scale)
        scaled_h = int(log_h * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        xw, yw = pos
        # verificar se clicou dentro da área lógica
        if xw < offset_x or xw >= offset_x + scaled_w or yw < offset_y or yw >= offset_y + scaled_h:
            return (-1, -1)

        lx = int((xw - offset_x) / scale)
        ly = int((yw - offset_y) / scale)
        # clamp
        lx = max(0, min(log_w - 1, lx))
        ly = max(0, min(log_h - 1, ly))
        return (lx, ly)

    def logical_to_window(self, pos):
        """
        Converte pos lógica -> window (centering/letterbox).
        Retorna (wx, wy) inteiros.
        """
        win_w, win_h = self.screen.get_size()
        log_w, log_h = self.logical_size

        if log_w == 0 or log_h == 0 or win_w == 0 or win_h == 0:
            return (0, 0)

        scale = min(win_w / log_w, win_h / log_h)
        scaled_w = int(log_w * scale)
        scaled_h = int(log_h * scale)
        offset_x = (win_w - scaled_w) // 2
        offset_y = (win_h - scaled_h) // 2

        lx, ly = pos
        wx = int(offset_x + lx * scale)
        wy = int(offset_y + ly * scale)
        return (wx, wy)

    def safe_scale_and_blit(self, source_surface):
        """
        Escala source_surface para a janela atual aplicando letterbox/centering
        e protege contra janelas minimizadas / tamanhos inválidos.
        Retorna True se fez blit com sucesso, False se pulou (minimizado).
        """
        win_w, win_h = self.screen.get_size()

        # Proteção contra janelas muito pequenas/minimizadas
        if win_w < 32 or win_h < 32:
            # processa eventos para permitir que a janela volte a restaurar
            pygame.event.pump()
            pygame.time.wait(100)
            return False

        log_w, log_h = self.logical_size
        if log_w == 0 or log_h == 0:
            return False

        scale = min(win_w / log_w, win_h / log_h)
        scaled_w = max(1, int(log_w * scale))
        scaled_h = max(1, int(log_h * scale))

        # tenta smoothscale e faz fallback seguro
        try:
            scaled = pygame.transform.smoothscale(source_surface, (scaled_w, scaled_h))
        except Exception:
            try:
                scaled = pygame.transform.scale(source_surface, (scaled_w, scaled_h))
            except Exception:
                # não conseguimos escalar — pulamos frame
                pygame.time.wait(50)
                return False

        offset_x = (win_w - scaled.get_width()) // 2
        offset_y = (win_h - scaled.get_height()) // 2
        try:
            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled, (offset_x, offset_y))
            pygame.display.flip()
            return True
        except Exception:
            # caso a surface da janela seja inválida momentaneamente
            pygame.time.wait(50)
            return False

    # ---------- desenhos gerais ----------
    def draw_title(self):
        t = self.title_font.render("🐍 Snake Game 🐍", True, WHITE)
        self.logical_surface.blit(t, t.get_rect(center=(self.logical_size[0] // 2, 100)))

    # ---------- ações dos botões (encaminham para submenus) ----------
    def action_jogar(self):
        self.jogar()

    def action_recordes(self):
        self.recordes()

    def action_ajuda(self):
        self.ajuda()

    def action_sair(self):
        self.sair()

    # ---------- Submenus (todos usam logical_surface) ----------
    def jogar(self):
        """Input do nome (centralizado, validado)."""
        nome = ""
        aviso = ""
        ativo = True
        clock = pygame.time.Clock()

        # input box pos lógica
        box_w, box_h = 400, 60
        box_x = self.logical_size[0] // 2 - box_w // 2
        box_y = 240

        while ativo and self.running:
            # eventos primeiro (permitir fechar)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if len(nome) == 0:
                            aviso = "⚠️ O nome não pode estar vazio."
                        elif not re.match(r"^[A-Za-z0-9]{1,12}$", nome):
                            aviso = "⚠️ Use apenas letras e números (sem acentos)."
                        else:
                            self.player_name = nome
                            ativo = False
                            # segue para dificuldade
                            self.escolher_dificuldade()
                            return
                    elif event.key == pygame.K_BACKSPACE:
                        nome = nome[:-1]
                    else:
                        if len(nome) < 12 and re.match(r"[A-Za-z0-9]", event.unicode):
                            nome += event.unicode
                elif event.type == pygame.VIDEORESIZE:
                    # actualiza apenas a janela real; lógica é fixa
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # desenhar na lógica
            self.logical_surface.fill(self.bg_color)
            titulo = self.big_font.render("Insere o teu nome (máx. 12):", True, WHITE)
            self.logical_surface.blit(titulo, titulo.get_rect(center=(self.logical_size[0]//2, 150)))

            caixa_rect = pygame.Rect(box_x, box_y, box_w, box_h)
            pygame.draw.rect(self.logical_surface, (100,100,100), caixa_rect, border_radius=8)
            texto_nome = self.big_font.render(nome, True, WHITE)
            self.logical_surface.blit(texto_nome, (caixa_rect.x + 12, caixa_rect.y + 12))

            instr = self.small_font.render("Pressiona ENTER para continuar", True, (180,180,180))
            self.logical_surface.blit(instr, instr.get_rect(center=(self.logical_size[0]//2, box_y + box_h + 40)))

            if aviso:
                aviso_s = self.small_font.render(aviso, True, (255,100,100))
                self.logical_surface.blit(aviso_s, aviso_s.get_rect(center=(self.logical_size[0]//2, box_y + box_h + 80)))

            # escala e blit com proteção
            self.safe_scale_and_blit(self.logical_surface)
            clock.tick(60)

    def escolher_dificuldade(self):
        """Menu de dificuldades (3 opções) - desenhado e centrado na lógica."""
        difs = [("Normal", 1.0), ("Rápido", 1.5), ("Muito Rápido", 2.0)]
        # layout lógico
        start_y = 200
        btn_w, btn_h = 360, 60
        spacing = 90
        rects = []
        for i, (name, mult) in enumerate(difs):
            bx = self.logical_size[0]//2 - btn_w//2
            by = start_y + i*spacing
            rects.append((pygame.Rect(bx, by, btn_w, btn_h), (name, mult)))

        clock = pygame.time.Clock()
        escolhendo = True
        while escolhendo and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # converte mouse coords -> lógica
                    mpos = self.window_to_logical(event.pos)
                    if mpos == (-1, -1):
                        # clique fora da área lógica: ignora
                        continue
                    for rect, data in rects:
                        if rect.collidepoint(mpos):
                            dificuldade = data
                            escolhendo = False
                            self.escolher_mapa(dificuldade)
                            break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    escolhendo = False

            # draw
            self.logical_surface.fill(self.bg_color)
            title = self.big_font.render("Escolhe a Dificuldade:", True, WHITE)
            self.logical_surface.blit(title, title.get_rect(center=(self.logical_size[0]//2, 120)))

            mpos_log = self.window_to_logical(pygame.mouse.get_pos())
            for rect, (name, mult) in rects:
                color = BLUE if rect.collidepoint(mpos_log) else (0,90,180)
                pygame.draw.rect(self.logical_surface, color, rect, border_radius=10)
                label = self.big_font.render(name, True, WHITE)
                self.logical_surface.blit(label, label.get_rect(center=rect.center))

            # safe blit
            self.safe_scale_and_blit(self.logical_surface)
            clock.tick(60)

    def escolher_mapa(self, dificuldade):
        """Escolha do mapa (3 opções). dificuldade é (nome, mult)."""
        opcoes = [
            ("Mapa 1 - Campo Livre", "assets/maps/arena.txt"),
            ("Mapa 2 - Obstáculos (borderless)", "assets/maps/obstaculos.txt"),
            ("Mapa 3 - Arena (bordas)", "assets/maps/arena.txt"),
        ]
        start_y = 180
        btn_w, btn_h = 520, 56
        spacing = 84
        rects = []
        for i, (label, path) in enumerate(opcoes):
            bx = self.logical_size[0]//2 - btn_w//2
            by = start_y + i*spacing
            rects.append((pygame.Rect(bx, by, btn_w, btn_h), (label, path)))

        clock = pygame.time.Clock()
        escolhendo = True
        while escolhendo and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mpos = self.window_to_logical(event.pos)
                    if mpos == (-1, -1):
                        continue
                    for rect, (label, path) in rects:
                        if rect.collidepoint(mpos):
                            escolhendo = False
                            # inicia o jogo com o mapa escolhido
                            jogador = getattr(self, "player_name", "Jogador")
                            nome_dif, mult = dificuldade

                            # guarda o tamanho atual da janela para restaurar depois
                            saved_win_size = self.screen.get_size()

                            # assegura que a display surface actual está definida para o tamanho atual
                            self.screen = pygame.display.set_mode(saved_win_size, pygame.RESIZABLE)

                            game = Game(player_name=jogador, modo="OG Snake", dificuldade=nome_dif, velocidade_mult=mult, mapa_tipo=path)
                            game.run()

                            # quando volta, restaura a janela exatamente como estava antes
                            try:
                                self.screen = pygame.display.set_mode(saved_win_size, pygame.RESIZABLE)
                            except Exception:
                                # fallback para cfg valores
                                self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)

                            self.recenter_buttons()
                            return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    escolhendo = False

            # draw
            self.logical_surface.fill(self.bg_color)
            title = self.big_font.render("Escolhe o mapa:", True, WHITE)
            self.logical_surface.blit(title, title.get_rect(center=(self.logical_size[0]//2, 120)))

            mpos_log = self.window_to_logical(pygame.mouse.get_pos())
            for rect, (label, path) in rects:
                color = (0,120,220) if rect.collidepoint(mpos_log) else (0,90,180)
                pygame.draw.rect(self.logical_surface, color, rect, border_radius=8)
                label_s = self.big_font.render(label, True, WHITE)
                self.logical_surface.blit(label_s, label_s.get_rect(center=rect.center))

            # safe blit
            self.safe_scale_and_blit(self.logical_surface)
            clock.tick(60)

    def recordes(self):
        manager = RecordsManager()
        scores = manager.ler_pontuacoes()

        clock = pygame.time.Clock()
        mostrando = True
        while mostrando and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    mostrando = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # botão voltar
                    mpos = self.window_to_logical(event.pos)
                    if self.back_rect.collidepoint(mpos):
                        mostrando = False

            # draw
            self.logical_surface.fill(self.bg_color)
            title = self.big_font.render("🏆 Recordes 🏆", True, (255,255,0))
            self.logical_surface.blit(title, title.get_rect(center=(self.logical_size[0]//2, 60)))

            # cabeçalho
            y = 120
            cols_labels = ["Nome", "Modo", "Dificuldade", "Pontos", "Data"]
            x_pos = [40, 220, 420, 540, 660]
            for i, c in enumerate(cols_labels):
                self.logical_surface.blit(self.mono_font.render(c, True, (200,200,200)), (x_pos[i], y))
            y += 36

            if not scores:
                self.logical_surface.blit(self.big_font.render("Nenhum recorde registado ainda.", True, WHITE), (180, 260))
            else:
                for p in scores[:12]:
                    values = [
                        p.get("nome", "---"),
                        p.get("modo", "---"),
                        p.get("dificuldade", "---"),
                        str(p.get("pontuacao", 0)),
                        p.get("data", "---")
                    ]
                    for j, v in enumerate(values):
                        self.logical_surface.blit(self.mono_font.render(v, True, WHITE), (x_pos[j], y))
                    y += 28

            # botão voltar (em lógica)
            self.back_rect = pygame.Rect(self.logical_size[0]//2 - 100, self.logical_size[1] - 80, 200, 50)
            mouse_log = self.window_to_logical(pygame.mouse.get_pos())
            cor = (100,100,255) if self.back_rect.collidepoint(mouse_log) else (0,0,180)
            pygame.draw.rect(self.logical_surface, cor, self.back_rect, border_radius=8)
            lab = self.small_font.render("Voltar", True, WHITE)
            self.logical_surface.blit(lab, lab.get_rect(center=self.back_rect.center))

            # safe blit
            self.safe_scale_and_blit(self.logical_surface)
            clock.tick(30)

    def ajuda(self):
        clock = pygame.time.Clock()
        mostrando = True
        while mostrando and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    mostrando = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mpos = self.window_to_logical(event.pos)
                    if self.back_rect.collidepoint(mpos):
                        mostrando = False

            self.logical_surface.fill(self.bg_color)
            lines = [
                "Ajuda - Controles e Regras",
                "",
                "- WASD ou setas para mover a cobra",
                "- ENTER para confirmar nos formulários",
                "- ESC para voltar",
                "- Não use acentos no nome; máximo 12 caracteres"
            ]
            y = 120
            for l in lines:
                self.logical_surface.blit(self.small_font.render(l, True, WHITE), (60, y))
                y += 36

            # botão voltar
            self.back_rect = pygame.Rect(self.logical_size[0]//2 - 100, self.logical_size[1] - 80, 200, 50)
            mouse_log = self.window_to_logical(pygame.mouse.get_pos())
            cor = (100,100,255) if self.back_rect.collidepoint(mouse_log) else (0,0,180)
            pygame.draw.rect(self.logical_surface, cor, self.back_rect, border_radius=8)
            lab = self.small_font.render("Voltar", True, WHITE)
            self.logical_surface.blit(lab, lab.get_rect(center=self.back_rect.center))

            # safe blit
            self.safe_scale_and_blit(self.logical_surface)
            clock.tick(30)

    def sair(self):
        self.running = False

    # ---------- construção / layout dos botões do menu principal ----------
    def recenter_buttons(self):
        btn_w, btn_h = 300, 64
        center_x = self.logical_size[0]//2 - btn_w//2
        start_y = self.logical_size[1]//2 - 150
        spacing = 92
        labels = ["Jogar", "Recordes", "Ajuda", "Sair"]
        actions = [self.action_jogar, self.action_recordes, self.action_ajuda, self.action_sair]
        colors = [BLUE, GREEN, (255,165,0), RED]
        hcolors = [(0,150,255), (0,200,100), (255,200,0), (255,100,100)]
        self.buttons = []
        for i, lab in enumerate(labels):
            bx = center_x
            by = start_y + i*spacing
            b = Button(lab, bx, by, btn_w, btn_h, colors[i], hcolors[i], actions[i], font_size=40)
            self.buttons.append(b)

    # ---------- loop principal do menu ----------
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            # recolhe eventos e processa apenas eventos globais (quit/resize)
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False
                if ev.type == pygame.VIDEORESIZE:
                    # mantemos a lógica fixa; apenas recriamos janela real. O layout seguir-se-á automaticamente
                    self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)

            # desenha tudo na logical surface
            self.logical_surface.fill(self.bg_color)
            self.draw_title()

            # calcula mouse lógico
            mouse_log = self.window_to_logical(pygame.mouse.get_pos())

            # desenha botões e trata hover
            for btn in self.buttons:
                btn.draw(self.logical_surface, mouse_pos_logical=mouse_log)

            # processa clique do rato (transformado em lógico)
            # se um evento MOUSEBUTTONDOWN ocorreu, processa aqui
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    ml = self.window_to_logical(ev.pos)
                    if ml == (-1, -1):
                        # click fora da área lógica (letterbox) -> ignora
                        continue
                    for btn in self.buttons:
                        if btn.check_click(ml):
                            # action foi chamada dentro de check_click
                            break

            # safe blit for menu
            self.safe_scale_and_blit(self.logical_surface)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()
