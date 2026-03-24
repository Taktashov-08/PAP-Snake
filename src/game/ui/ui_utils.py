# src/game/ui/ui_utils.py
"""
Utilitários de UI partilhados entre Menu e Engine.

Funções:
  draw_bg          — fundo escuro com grelha decorativa
  draw_panel       — card translúcido com bordas arredondadas
  draw_btn         — botão flat com highlight 3D e hover
  draw_fade_overlay— overlay preto semi-transparente (útil em pausas/game-over)
  window_to_logical— converte coordenadas janela → superfície lógica
  blit_scaled      — escala superfície lógica para a janela (letterbox)
"""
from __future__ import annotations

import pygame
import game.config as C


def draw_bg(surface: pygame.Surface, w: int, h: int) -> None:
    """Fundo escuro com grelha decorativa subtil."""
    surface.fill(C.BG_DARK)
    for x in range(0, w, 20):
        pygame.draw.line(surface, C.GRID_LINE, (x, 0), (x, h))
    for y in range(0, h, 20):
        pygame.draw.line(surface, C.GRID_LINE, (0, y), (w, y))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               radius: int = 10) -> None:
    """Card translúcido com borda subtil arredondada."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*C.BG_PANEL, 245), s.get_rect(), border_radius=radius)
    pygame.draw.rect(s, (*C.UI_BORDER, 200), s.get_rect(), 1, border_radius=radius)
    surface.blit(s, rect.topleft)


def draw_btn(surface: pygame.Surface, rect: pygame.Rect,
             base, hover, is_hover: bool,
             text: str, font: pygame.font.Font,
             radius: int = 8) -> None:
    """
    Botão flat com:
      - Cor muda ao hover
      - Linha de highlight no topo (efeito 3D subtil)
      - Borda levemente mais escura
    """
    col = hover if is_hover else base
    pygame.draw.rect(surface, col, rect, border_radius=radius)
    # Linha de highlight superior
    hi = tuple(min(c + 30, 255) for c in col)
    pygame.draw.line(surface, hi,
                     (rect.x + radius, rect.y + 1),
                     (rect.right - radius, rect.y + 1))
    # Borda exterior
    pygame.draw.rect(surface, tuple(max(c - 20, 0) for c in col),
                     rect, 1, border_radius=radius)
    # Texto centrado
    txt = font.render(text, True, C.WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))


def draw_fade_overlay(surface: pygame.Surface, alpha: int = 140) -> None:
    """
    Overlay preto semi-transparente sobre toda a surface.
    Útil para pausas, contagens decrescentes, e fundos de ecrãs de fim.

    `alpha`: 0 = totalmente transparente, 255 = totalmente preto.
    """
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, max(0, min(255, alpha))))
    surface.blit(overlay, (0, 0))


def window_to_logical(screen: pygame.Surface,
                      logical_size: tuple,
                      pos: tuple) -> tuple:
    """
    Converte coordenadas da janela física para a superfície lógica.
    Devolve (-1, -1) se o ponto estiver fora da área de renderização (letterbox).
    """
    win_w, win_h = screen.get_size()
    log_w, log_h = logical_size
    if not all([log_w, log_h, win_w, win_h]):
        return (-1, -1)
    scale = min(win_w / log_w, win_h / log_h)
    sw    = int(log_w * scale)
    sh    = int(log_h * scale)
    ox    = (win_w - sw) // 2
    oy    = (win_h - sh) // 2
    xw, yw = pos
    if not (ox <= xw < ox + sw and oy <= yw < oy + sh):
        return (-1, -1)
    return (
        max(0, min(log_w - 1, int((xw - ox) / scale))),
        max(0, min(log_h - 1, int((yw - oy) / scale))),
    )


def blit_scaled(screen: pygame.Surface, surface: pygame.Surface,
                logical_size: tuple) -> None:
    """
    Escala a superfície lógica para a janela física com letterbox.
    Usa smoothscale quando possível para melhor qualidade.
    """
    win_w, win_h = screen.get_size()
    if win_w < 32 or win_h < 32:
        pygame.event.pump()
        pygame.time.wait(100)
        return
    log_w, log_h = logical_size
    scale = min(win_w / log_w, win_h / log_h)
    sw = max(1, int(log_w * scale))
    sh = max(1, int(log_h * scale))
    try:
        scaled = pygame.transform.smoothscale(surface, (sw, sh))
    except Exception:
        scaled = pygame.transform.scale(surface, (sw, sh))
    ox = (win_w - sw) // 2
    oy = (win_h - sh) // 2
    screen.fill(C.BLACK)
    screen.blit(scaled, (ox, oy))
    pygame.display.flip()