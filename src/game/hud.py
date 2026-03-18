# Descrição: Gere a interface de utilizador (HUD) no topo do jogo.
# Exibe informações como nome do jogador, modo, dificuldade e pontuação.
# src/game/hud.py
import pygame
import game.config as cfg


class HUD:
    """
    Barra HUD no topo — Interface de utilizador com estilo escuro e limpo.
    Fundo sólido com uma linha separadora fina para distinguir a área de jogo.
    """
    HUD_HEIGHT = 28 # Altura fixa da barra em pixéis

    def __init__(self, jogador="Jogador", modo="OG Snake", dificuldade="Normal"):
        self.jogador     = jogador
        self.modo        = modo
        self.dificuldade = dificuldade
        self.pontuacao   = 0
        self._font_sm    = None # Fonte pequena (lazy loading)
        self._font_md    = None # Fonte média (lazy loading)

    # ── Lógica de Atualização ────────────────────────────────────────────────
    def atualizar_pontuacao(self, nova):
        """Atualiza o valor numérico da pontuação exibida."""
        self.pontuacao = nova

    def atualizar_info(self, jogador=None, modo=None, dificuldade=None):
        """Permite alterar os textos de contexto (ex: ao mudar de nível)."""
        if jogador:     self.jogador     = jogador
        if modo:        self.modo        = modo
        if dificuldade: self.dificuldade = dificuldade

    def mostrar_info(self):
        """Auxiliar de depuração para imprimir o estado no terminal."""
        print(f"[HUD] {self.jogador} | {self.modo} | {self.dificuldade} | {self.pontuacao}")

    # ── Renderização ─────────────────────────────────────────────────────────
    def _fonts(self):
        """Inicializa as fontes apenas quando necessário (otimização)."""
        if self._font_sm is None:
            # Consolas é usada por ser monoespaçada, mantendo o layout estável
            self._font_sm = pygame.font.SysFont("Consolas", 16)
            self._font_md = pygame.font.SysFont("Consolas", 17)

    def draw(self, surface, score=None, modo_override=None):
        """Desenha a barra, o fundo, a linha separadora e os textos."""
        self._fonts()
        w  = surface.get_width()
        h  = self.HUD_HEIGHT
        cy = h // 2 # Centro vertical da barra

        # 1. Desenha o fundo sólido da barra
        pygame.draw.rect(surface, cfg.HUD_BG, (0, 0, w, h))
        
        # 2. Desenha a linha separadora fina na base da HUD (h-1)
        pygame.draw.line(surface, cfg.HUD_BORDER, (0, h - 1), (w, h - 1), 1)

        # Determina qual pontuação usar (se passada por argumento ou a interna)
        pontos = score if score is not None else self.pontuacao

        # Se houver um modo_override (ex: "GAME OVER"), centra esse texto e ignora o resto
        if modo_override:
            txt = self._font_sm.render(modo_override, True, cfg.HUD_TEXT)
            surface.blit(txt, txt.get_rect(center=(w // 2, cy)))
        else:
            # 3. Renderiza Info à Esquerda: jogador · modo · dificuldade
            info_str = f"  {self.jogador}  ·  {self.modo}  ·  {self.dificuldade}"
            left = self._font_sm.render(info_str, True, cfg.HUD_TEXT)
            
            # 4. Renderiza Pontuação à Direita
            score_str = f"Score  {pontos}"
            right = self._font_md.render(score_str, True, cfg.HUD_SCORE)

            # Posicionamento com margens de segurança (8px à esquerda, 10px à direita)
            surface.blit(left,  left.get_rect(midleft=(8, cy)))
            surface.blit(right, right.get_rect(midright=(w - 10, cy)))