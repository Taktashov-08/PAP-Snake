import pygame
import sys
import re
from game.engine import Game
from game.records import RecordsManager
from game.config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, GREEN, RED, BLUE

pygame.init()

class Button:
    """Classe simples de botão"""
    def __init__(self, text, x, y, w, h, color, hover_color, action=None):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.font = pygame.font.SysFont(None, 40)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.action:
                self.action()


class Menu:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake Menu")
        self.running = True
        self.bg_color = (30, 30, 30)
        self.font = pygame.font.SysFont(None, 60)

        # cria os botões principais
        self.buttons = [
            Button("Jogar", 300, 200, 200, 60, BLUE, (0, 150, 255), self.jogar),
            Button("Recordes", 300, 280, 200, 60, GREEN, (0, 200, 100), self.recordes),
            Button("Ajuda", 300, 360, 200, 60, (255, 165, 0), (255, 200, 0), self.ajuda),
            Button("Sair", 300, 440, 200, 60, RED, (255, 100, 100), self.sair)
        ]

    def desenhar_titulo(self):
        titulo = self.font.render("🐍 Snake Game 🐍", True, WHITE)
        rect = titulo.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(titulo, rect)

    # ---------------------- Ações dos botões -----------------------

    def jogar(self):
        """Ecrã para introdução do nome do jogador (com validação)"""
        nome = ""
        fonte = pygame.font.SysFont(None, 40)
        aviso_font = pygame.font.SysFont(None, 28)
        ativo = True
        aviso = ""

        while ativo:
            self.screen.fill((30, 30, 30))

            # Título
            titulo = fonte.render("Insere o teu nome (máx. 10):", True, (255, 255, 255))
            self.screen.blit(titulo, (180, 150))

            # Caixa de texto
            caixa_rect = pygame.Rect(250, 220, 300, 50)
            pygame.draw.rect(self.screen, (100, 100, 100), caixa_rect, border_radius=8)
            texto_nome = fonte.render(nome, True, (255, 255, 255))
            self.screen.blit(texto_nome, (caixa_rect.x + 10, caixa_rect.y + 10))

            # Aviso (erro de validação)
            if aviso:
                aviso_text = aviso_font.render(aviso, True, (255, 100, 100))
                self.screen.blit(aviso_text, (250, 280))

            # Instrução
            instru = aviso_font.render("Pressiona ENTER para continuar", True, (180, 180, 180))
            self.screen.blit(instru, (200, 340))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    ativo = False
                    self.running = False
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # validação do nome
                        if len(nome) == 0:
                            aviso = "⚠️ O nome não pode estar vazio."
                        elif not re.match(r"^[A-Za-z0-10]{1,11}$", nome):
                            aviso = "⚠️ Use apenas letras e números (sem acentos)."
                        else:
                            ativo = False
                            self.player_name = nome
                            self.escolher_dificuldade()
                            return
                    elif event.key == pygame.K_BACKSPACE:
                        nome = nome[:-1]
                    else:
                        # só aceitar caracteres válidos e limitar a 10
                        if len(nome) < 11 and re.match(r"[A-Za-z0-10]", event.unicode):
                            nome += event.unicode

    def escolher_dificuldade(self):
        escolher = True
        dif_font = pygame.font.SysFont(None, 40)
        opcoes = [("Normal", 1.0), ("Rápido", 1.5), ("Muito Rápido", 2.0)]
        while escolher:
            self.screen.fill(self.bg_color)
            txt = dif_font.render("Escolhe a Dificuldade:", True, WHITE)
            self.screen.blit(txt, (220, 150))

            y = 250
            for nome, mult in opcoes:
                rect = pygame.Rect(300, y, 200, 50)
                pygame.draw.rect(self.screen, BLUE, rect, border_radius=10)
                label = dif_font.render(nome, True, WHITE)
                self.screen.blit(label, label.get_rect(center=rect.center))
                y += 80

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    escolher = False
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse = event.pos
                    if 300 <= mouse[0] <= 500:
                        if 250 <= mouse[1] <= 300:
                            dificuldade = ("Normal", 1.0)
                            escolher = False
                        elif 330 <= mouse[1] <= 380:
                            dificuldade = ("Rápido", 1.5)
                            escolher = False
                        elif 410 <= mouse[1] <= 460:
                            dificuldade = ("Muito Rápido", 2.0)
                            escolher = False
            pygame.time.Clock().tick(30)

        if self.running:
            self.iniciar_jogo(dificuldade)

    def iniciar_jogo(self, dificuldade):
        jogador = getattr(self, "player_name", "Jogador")
        modo = "OG Snake"
        nome_dif, mult = dificuldade
        game = Game(player_name=jogador, modo=modo, dificuldade=nome_dif, velocidade_mult=mult)
        game.run()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake Menu")


    def recordes(self):
        """Mostra o ecrã de recordes visualmente"""
        manager = RecordsManager()
        pontuacoes = manager.ler_pontuacoes()

        voltar_font = pygame.font.SysFont(None, 36)
        titulo_font = pygame.font.SysFont(None, 60)
        texto_font = pygame.font.SysFont(None, 28)

        voltar_rect = pygame.Rect(300, 520, 200, 50)
        mostrando = True

        while mostrando:
            self.screen.fill((20, 20, 20))

            # título
            titulo = titulo_font.render("🏆 Recordes 🏆", True, (255, 255, 0))
            self.screen.blit(titulo, titulo.get_rect(center=(400, 60)))

            # tabela
            y = 130
            cabecalho = texto_font.render("     nome      | Modo         | Dificuldade | Pontos | Data", True, (200, 200, 200))
            self.screen.blit(cabecalho, (80, y))
            y += 30

            if not pontuacoes:
                vazio = texto_font.render("Nenhum recorde registado ainda.", True, (255, 255, 255))
                self.screen.blit(vazio, (200, 300))
            else:
                for i, p in enumerate(pontuacoes[:10]):
                    linha = f"{p['nome']:<10} | {p['modo']:<12} | {p['dificuldade']:<10} | {p['pontuacao']:>5} | {p['data']}"
                    texto = texto_font.render(linha, True, (255, 255, 255))
                    self.screen.blit(texto, (80, y))
                    y += 30

            # botão voltar
            mouse = pygame.mouse.get_pos()
            cor_botao = (100, 100, 255) if voltar_rect.collidepoint(mouse) else (0, 0, 180)
            pygame.draw.rect(self.screen, cor_botao, voltar_rect, border_radius=10)
            label_voltar = voltar_font.render("Voltar", True, (255, 255, 255))
            self.screen.blit(label_voltar, label_voltar.get_rect(center=voltar_rect.center))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    mostrando = False
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if voltar_rect.collidepoint(event.pos):
                        mostrando = False

            pygame.time.Clock().tick(30)

    def ajuda(self):
        print("Abrir ecrã de ajuda (para implementar depois).")

    def sair(self):
        print("A sair do jogo...")
        self.running = False

    # ---------------------- Loop principal -----------------------
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                for btn in self.buttons:
                    btn.check_click(event)

            self.screen.fill(self.bg_color)
            self.desenhar_titulo()
            for btn in self.buttons:
                btn.draw(self.screen)

            pygame.display.flip()
            pygame.time.Clock().tick(60)

        pygame.quit()
        sys.exit()
