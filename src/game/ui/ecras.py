# src/game/ui/ecras.py
"""
Ecrãs de transição (fim de jogo, vitória, derrota).
Completamente separados da lógica do engine.
Cada função recebe a superfície lógica, o ecrã físico e os dados necessários.
Devolve True se o jogador quer repetir, False se quer voltar ao menu.
"""
import pygame
import sys
import game.config as cfg
from game.ui import ui_utils


# ── Utilitário interno ────────────────────────────────────────────────────────
def _render_btn(surface, font, rect, texto, cor_base, cor_hover, cor_texto, mlog):
    cor = cor_hover if rect.collidepoint(mlog) else cor_base
    pygame.draw.rect(surface, cor, rect, border_radius=8)
    pygame.draw.rect(surface, tuple(min(c + 40, 255) for c in cor), rect, 1, border_radius=8)
    t = font.render(texto, True, cor_texto)
    surface.blit(t, t.get_rect(center=rect.center))


def _processar_eventos(screen, logical_size, btn_novo, btn_menu):
    """
    Trata eventos comuns aos três ecrãs.
    Devolve: True (repetir), False (menu) ou None (continuar).
    """
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.VIDEORESIZE:
            pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN: return True
            if ev.key in (pygame.K_ESCAPE, pygame.K_SPACE): return False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            pos = ui_utils.window_to_logical(screen, logical_size, ev.pos)
            if btn_novo.collidepoint(pos): return True
            if btn_menu.collidepoint(pos): return False
    return None


# ── Ecrã genérico (OG Snake / Snake Torre) ────────────────────────────────────
def ecra_fim_jogo(screen, surface, logical_size, titulo,
                  subtitulo="", cor_titulo=(220, 100, 80), fundo=None):
    """
    Overlay escuro sobre o último frame do jogo.
    fundo: Surface com o último frame; se None usa a surface actual.
    """
    f_titulo = pygame.font.SysFont("Consolas", 48, bold=True)
    f_sub    = pygame.font.SysFont("Consolas", 26)
    f_btn    = pygame.font.SysFont("Consolas", 24)
    f_dica   = pygame.font.SysFont("Consolas", 18)

    lw, lh   = logical_size
    cx, cy   = lw // 2, lh // 2
    btn_novo = pygame.Rect(cx - 255, cy + 90, 225, 50)
    btn_menu = pygame.Rect(cx +  30, cy + 90, 225, 50)
    snapshot = fundo.copy() if fundo else surface.copy()
    clock    = pygame.time.Clock()

    while True:
        resultado = _processar_eventos(screen, logical_size, btn_novo, btn_menu)
        if resultado is not None:
            return resultado

        surface.blit(snapshot, (0, 0))

        # Overlay escuro
        escuro = pygame.Surface((lw, lh), pygame.SRCALPHA)
        escuro.fill((0, 0, 0, 160))
        surface.blit(escuro, (0, 0))

        # Painel
        painel = pygame.Rect(cx - 290, cy - 165, 580, 300)
        ps = pygame.Surface((painel.w, painel.h), pygame.SRCALPHA)
        pygame.draw.rect(ps, (20, 22, 30, 245), ps.get_rect(), border_radius=14)
        pygame.draw.rect(ps, (60, 66, 90, 220), ps.get_rect(), 2, border_radius=14)
        surface.blit(ps, painel.topleft)

        t = f_titulo.render(titulo, True, cor_titulo)
        surface.blit(t, t.get_rect(center=(cx, cy - 100)))
        if subtitulo:
            s = f_sub.render(subtitulo, True, (190, 195, 210))
            surface.blit(s, s.get_rect(center=(cx, cy - 40)))

        dica = f_dica.render("ENTER → novo jogo   ESC → menu", True, (100, 105, 120))
        surface.blit(dica, dica.get_rect(center=(cx, cy + 48)))

        mlog = ui_utils.window_to_logical(screen, logical_size, pygame.mouse.get_pos())
        _render_btn(surface, f_btn, btn_novo, "Jogar de Novo",
                    (35, 105, 65), (50, 145, 90), (220, 255, 220), mlog)
        _render_btn(surface, f_btn, btn_menu, "Voltar ao Menu",
                    (105, 40, 40), (140, 55, 55), (255, 220, 220), mlog)

        ui_utils.blit_scaled(screen, surface, logical_size)
        clock.tick(60)


# ── Ecrã 1v1 ─────────────────────────────────────────────────────────────────
def ecra_fim_1v1(screen, surface, logical_size, resultado, fundo=None):
    """resultado: string como 'Vitoria P1', 'Empate', etc."""
    if "Vitoria" in resultado or "Vitória" in resultado:
        cor = (80, 220, 120)
    else:
        cor = (220, 180, 60)
    return ecra_fim_jogo(screen, surface, logical_size,
                         resultado, "Modo 1v1", cor, fundo)


# ── Ecrã Vs IA ────────────────────────────────────────────────────────────────
def ecra_fim_vsai(screen, surface, logical_size,
                  resultado, nome_jogador, pts_jogador, pts_bot):
    """Ecrã dedicado com pontuações dos dois lados."""
    if resultado == "vitoria":
        titulo_txt, titulo_cor = "Vitória!", (80, 220, 120)
        sub_txt = f"Derrotaste o Bot, {nome_jogador}!"
    elif resultado == "derrota":
        titulo_txt, titulo_cor = "Derrota", (220, 80, 80)
        sub_txt = "O Bot ganhou desta vez..."
    else:
        titulo_txt, titulo_cor = "Empate", (220, 180, 60)
        sub_txt = "Ficaram empatados!"

    f_titulo = pygame.font.SysFont("Consolas", 56, bold=True)
    f_sub    = pygame.font.SysFont("Consolas", 26)
    f_info   = pygame.font.SysFont("Consolas", 22)
    f_btn    = pygame.font.SysFont("Consolas", 24)
    f_dica   = pygame.font.SysFont("Consolas", 18)

    lw, lh   = logical_size
    cx, cy   = lw // 2, lh // 2
    btn_novo = pygame.Rect(cx - 265, cy + 120, 230, 52)
    btn_menu = pygame.Rect(cx +  35, cy + 120, 230, 52)
    clock    = pygame.time.Clock()

    while True:
        resultado_loop = _processar_eventos(screen, logical_size, btn_novo, btn_menu)
        if resultado_loop is not None:
            return resultado_loop

        # Fundo com grelha
        surface.fill(cfg.BG_DARK)
        for x in range(0, lw, 20):
            pygame.draw.line(surface, cfg.GRID_LINE, (x, 0), (x, lh))
        for y in range(0, lh, 20):
            pygame.draw.line(surface, cfg.GRID_LINE, (0, y), (0, lh))

        # Painel
        painel = pygame.Rect(cx - 290, cy - 185, 580, 360)
        ps = pygame.Surface((painel.w, painel.h), pygame.SRCALPHA)
        pygame.draw.rect(ps, (20, 24, 20, 240), ps.get_rect(), border_radius=14)
        pygame.draw.rect(ps, (80, 100, 80, 180), ps.get_rect(), 1, border_radius=14)
        surface.blit(ps, painel.topleft)

        t = f_titulo.render(titulo_txt, True, titulo_cor)
        surface.blit(t, t.get_rect(center=(cx, cy - 125)))
        sub = f_sub.render(sub_txt, True, (200, 210, 200))
        surface.blit(sub, sub.get_rect(center=(cx, cy - 65)))
        pygame.draw.line(surface, (60, 80, 60), (cx - 200, cy - 28), (cx + 200, cy - 28), 1)

        s1 = f_info.render(f"{nome_jogador}:  {pts_jogador} pts", True, (120, 220, 140))
        s2 = f_info.render(f"Bot:  {pts_bot} pts",               True, (220, 100, 100))
        surface.blit(s1, s1.get_rect(center=(cx, cy + 10)))
        surface.blit(s2, s2.get_rect(center=(cx, cy + 45)))

        dica = f_dica.render("ENTER → novo jogo   ESC → menu", True, (90, 100, 90))
        surface.blit(dica, dica.get_rect(center=(cx, cy + 85)))

        mlog = ui_utils.window_to_logical(screen, logical_size, pygame.mouse.get_pos())
        _render_btn(surface, f_btn, btn_novo, "Jogar de Novo",
                    (35, 105, 60), (50, 140, 80), (220, 255, 220), mlog)
        _render_btn(surface, f_btn, btn_menu, "Voltar ao Menu",
                    (105, 40, 40), (140, 55, 55), (255, 220, 220), mlog)

        ui_utils.blit_scaled(screen, surface, logical_size)
        clock.tick(60)