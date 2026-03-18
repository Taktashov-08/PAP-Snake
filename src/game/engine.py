# Descrição: Motor principal (Engine) que gere o ciclo de vida do jogo, eventos, renderização e delega a lógica para o modo ativo.
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

class Game:
    """Classe central que orquestra a janela, o loop principal e a transição de estados/modos."""
    
    def __init__(self, player_name="Player", modo="OG Snake", dificuldade="Normal", velocidade_mult=1.0, mapa_tipo=1, player2_name="Player 2"):
        self.player_name = player_name
        self.player2_name = player2_name  
        self.modo = modo
        self.dificuldade = dificuldade
        self.velocidade_mult = velocidade_mult
        
        pygame.init()

        # ── Configuração da Janela Física ──────────────────────────
        try:
            current_surface = pygame.display.get_surface()
            if current_surface:
                current_w, current_h = current_surface.get_size()
            else:
                current_w, current_h = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
        except:
            current_w, current_h = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        # Define a janela como redimensionável
        self.screen = pygame.display.set_mode((current_w, current_h), pygame.RESIZABLE)

        # ── Configuração da Superfície Lógica (Tamanho Fixo) ───────
        # Toda a renderização é feita aqui, sendo depois escalada para a janela física
        self.logical_w = cfg.SCREEN_WIDTH  
        self.logical_h = cfg.SCREEN_HEIGHT 
        self.surface = pygame.Surface((self.logical_w, self.logical_h))
        self.block = cfg.BLOCK_SIZE 
        self.play_rect = (0, 0, self.logical_w, self.logical_h)

        self.clock = pygame.time.Clock()
        self.running = True

        # ── Instanciação dos Gestores (Managers) ───────────────────
        self.records = RecordsManager()
        self.hud = HUD(jogador=player_name, modo=modo, dificuldade=dificuldade)
        self.mapa = Mapas(mapa_tipo, block_size=self.block, auto_scale=False)
        self.map_renderer = MapRenderer(self.mapa, block_size=self.block)
        
        pygame.init()
        pygame.mixer.init()          
        self.assets = AssetsManager()

        # ── Sistema de Pontuação ───────────────────────────────────
        mult = 1.0
        if dificuldade in ("Rápido", "Rapido"): mult = 1.5
        elif dificuldade == "Muito Rápido": mult = 2.0
        self.score = Score(multiplicador=mult)

        self.base_fps = FPS

        # ── Seleção Dinâmica do Modo de Jogo (Padrão Strategy) ─────
        if self.modo == "1v1":
            self.modo_atual = Modo1v1(self)
        else:
            self.modo_atual = OgSnake(self)

    def handle_events(self, events):
        """Processa eventos globais e delega os controlos específicos para o modo ativo."""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Atualiza o tamanho da janela física caso o utilizador a redimensione
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return

            # Passa o evento de input (ex: WASD/Setas) para a lógica do modo selecionado
            self.modo_atual.handle_event(event)

    def update(self):
        """Atualiza a lógica de jogo delegando-a para o modo atual."""
        self.modo_atual.update()

    def draw_logical(self):
        """Renderiza todo o jogo na superfície lógica (resolução fixa)."""
        self.surface.fill(cfg.BG_DARK)          
    
        # Desenha a grelha de fundo
        for x in range(0, self.logical_w, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE, (x, 0), (x, self.logical_h))
        for y in range(0, self.logical_h, self.block):
            pygame.draw.line(self.surface, cfg.GRID_LINE, (0, y), (self.logical_w, y))
    
        # Desenha as paredes e obstáculos do mapa
        self.map_renderer.draw(self.surface)
    
        # Desenha entidades específicas do modo (Cobras e Comida)
        self.modo_atual.draw(self.surface)
    
        # Renderiza o cabeçalho (HUD)
        if self.modo == "1v1":
            hud_text = f"1v1  |  {self.player_name} (WASD)  vs  {self.player2_name} (Setas)"
            self.hud.draw(self.surface, modo_override=hud_text)
        else:
            self.hud.draw(self.surface, score=self.score.obter_pontuacao())

    def draw_hud(self, surface):
        """Método alternativo para desenhar o HUD com texto simples."""
        font = self.assets.get_sysfont(None, 24)
        if self.modo == "1v1":
            texto = f"1v1 | {self.player_name} (WASD) vs {self.player2_name} (Setas)"
        else:
            texto = f"{self.hud.jogador} | {self.hud.modo} | {self.hud.dificuldade} | Score: {self.score.obter_pontuacao()}"
        surf = font.render(texto, True, WHITE)
        surface.blit(surf, (10, 10))

    def run(self):
        """Ciclo principal de jogo (Game Loop)."""
        while self.running:
            events = pygame.event.get()
            
            # 1. Processar Inputs
            self.handle_events(events)
            
            # 2. Atualizar Lógica e Renderizar (Superfície Lógica)
            self.update()
            self.draw_logical()

            # 3. Escalar para a Janela Real (Letterboxing)
            win_w, win_h = self.screen.get_size()
            
            # Evita erros se a janela for minimizada ou estiver demasiado pequena
            if win_w < 32 or win_h < 32:
                pygame.time.wait(100)
                continue

            # Calcula a escala mantendo a proporção (Aspect Ratio)
            scale = min(win_w / self.logical_w, win_h / self.logical_h)
            new_w = int(self.logical_w * scale)
            new_h = int(self.logical_h * scale)

            try:
                # Tenta redimensionamento com suavização
                scaled_surf = pygame.transform.smoothscale(self.surface, (new_w, new_h))
            except:
                # Fallback para redimensionamento rápido
                scaled_surf = pygame.transform.scale(self.surface, (new_w, new_h))

            # Calcula as margens (barras pretas) para centrar o ecrã
            ox = (win_w - new_w) // 2
            oy = (win_h - new_h) // 2

            self.screen.fill(BLACK)
            self.screen.blit(scaled_surf, (ox, oy))
            
            # 4. Apresenta a frame desenhada no ecrã
            pygame.display.flip()

            # 5. Controla o ritmo de jogo (Framerate) de acordo com a velocidade
            self.clock.tick(int(self.base_fps * self.velocidade_mult))
        
        # Repõe o modo de vídeo padrão ao sair do loop
        try:
            pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.RESIZABLE)
        except: pass

    def game_over(self):
        """Trata o fim do jogo num jogador, registando a pontuação."""
        try:
            self.records.guardar_pontuacao(self.hud.jogador, self.hud.modo, self.hud.dificuldade, self.score.obter_pontuacao())
        except: pass
        print("Game Over")

    def game_over_1v1(self, res):
        """Trata o fim do jogo no modo multijogador competitivo."""
        print(f"Fim 1v1: {res}")
        self.running = False