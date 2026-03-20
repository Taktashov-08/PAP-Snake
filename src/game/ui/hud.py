# src/game/ui/hud.py
import pygame
import game.config as cfg


class HUD:
    """Barra HUD no topo — fundo solido com linha separadora fina."""
    HUD_HEIGHT = 28

    def __init__(self, jogador="Jogador", modo="OG Snake", dificuldade="Normal"):
        self.jogador     = jogador
        self.modo        = modo
        self.dificuldade = dificuldade
        self.pontuacao   = 0
        self._font_sm    = None
        self._font_md    = None

    def atualizar_pontuacao(self, nova):
        self.pontuacao = nova

    def atualizar_info(self, jogador=None, modo=None, dificuldade=None):
        if jogador:     self.jogador     = jogador
        if modo:        self.modo        = modo
        if dificuldade: self.dificuldade = dificuldade

    def _fonts(self):
        if self._font_sm is None:
            self._font_sm = pygame.font.SysFont("Consolas", 16)
            self._font_md = pygame.font.SysFont("Consolas", 17)

    def draw(self, surface, score=None, modo_override=None):
        self._fonts()
        w  = surface.get_width()
        h  = self.HUD_HEIGHT
        cy = h // 2
        pygame.draw.rect(surface, cfg.HUD_BG, (0, 0, w, h))
        pygame.draw.line(surface, cfg.HUD_BORDER, (0, h-1), (w, h-1), 1)
        pontos = score if score is not None else self.pontuacao
        if modo_override:
            txt = self._font_sm.render(modo_override, True, cfg.HUD_TEXT)
            surface.blit(txt, txt.get_rect(center=(w // 2, cy)))
        else:
            info_str  = f"  {self.jogador}  ·  {self.modo}  ·  {self.dificuldade}"
            score_str = f"Score  {pontos}"
            left  = self._font_sm.render(info_str,  True, cfg.HUD_TEXT)
            right = self._font_md.render(score_str, True, cfg.HUD_SCORE)
            surface.blit(left,  left.get_rect(midleft=(8, cy)))
            surface.blit(right, right.get_rect(midright=(w - 10, cy)))
