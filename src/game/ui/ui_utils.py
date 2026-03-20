# src/game/ui/ui_utils.py
"""
Utilitarios de UI partilhados entre Menu e Engine.
Elimina duplicacao de draw_bg, draw_panel, draw_btn,
window_to_logical e blit_scaled.
"""
import pygame
import game.config as C


def draw_bg(surface, w, h):
    """Fundo escuro com grelha decorativa subtil."""
    surface.fill(C.BG_DARK)
    for x in range(0, w, 20):
        pygame.draw.line(surface, C.GRID_LINE, (x, 0), (x, h))
    for y in range(0, h, 20):
        pygame.draw.line(surface, C.GRID_LINE, (0, y), (w, y))


def draw_panel(surface, rect, radius=10):
    """Painel translucido com bordas arredondadas (estilo Card)."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*C.BG_PANEL, 245), s.get_rect(), border_radius=radius)
    pygame.draw.rect(s, (*C.UI_BORDER, 200), s.get_rect(), 1, border_radius=radius)
    surface.blit(s, rect.topleft)


def draw_btn(surface, rect, base, hover, is_hover, text, font, radius=8):
    """Botao flat com efeito de profundidade 3D e hover reativo."""
    col = hover if is_hover else base
    pygame.draw.rect(surface, col, rect, border_radius=radius)
    hi = tuple(min(c + 30, 255) for c in col)
    pygame.draw.line(surface, hi,
                     (rect.x + radius, rect.y + 1),
                     (rect.right - radius, rect.y + 1))
    pygame.draw.rect(surface, tuple(max(c - 20, 0) for c in col),
                     rect, 1, border_radius=radius)
    txt = font.render(text, True, C.WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))


def window_to_logical(screen, logical_size, pos):
    """Converte coordenadas da janela fisica para a superficie logica."""
    win_w, win_h = screen.get_size()
    log_w, log_h = logical_size
    if not all([log_w, log_h, win_w, win_h]):
        return (-1, -1)
    scale = min(win_w / log_w, win_h / log_h)
    sw, sh = int(log_w * scale), int(log_h * scale)
    ox, oy = (win_w - sw) // 2, (win_h - sh) // 2
    xw, yw = pos
    if not (ox <= xw < ox + sw and oy <= yw < oy + sh):
        return (-1, -1)
    return (max(0, min(log_w - 1, int((xw - ox) / scale))),
            max(0, min(log_h - 1, int((yw - oy) / scale))))


def blit_scaled(screen, surface, logical_size):
    """Escala a superficie logica para a janela (letterbox)."""
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
