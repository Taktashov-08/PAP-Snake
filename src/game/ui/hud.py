# src/game/ui/hud.py
"""
HUD como painel lateral direito (SIDEBAR_W px de largura).

Não há barra de topo — a área de jogo é completamente limpa.

Secções por modo:
  OG Snake  → nome · pontuação animada · comprimento · modo/dificuldade
  Vs AI     → nome · pontuação · comprimento (cobra vs bot) · boosts
  1v1       → metade superior = P1 · metade inferior = P2

Animações:
  - Score pop: ao ganhar pontos o número pisca branco e encolhe para o
    tamanho normal ao longo de _POP_DURATION segundos.
  - Barra de comprimento: transição suave entre comprimentos.

API pública:
  hud.update(dt)                — avança animações (60 fps)
  hud.set_score(pts)            — actualiza score e dispara pop
  hud.draw_sidebar(surface, info, modo)  — renderiza o painel
"""
from __future__ import annotations

import math
from typing import Any, Dict, Tuple

import pygame

import game.config as C

# ── Constantes de layout ──────────────────────────────────────────────────────
_PAD:          int   = 12       # padding interno horizontal
_SEC_GAP:      int   = 10       # espaço antes de cada linha divisória
_POP_DURATION: float = 0.40    # segundos do efeito de pop da pontuação
_BAR_H:        int   = 6       # altura das barras de progresso
_BAR_RADIUS:   int   = 3       # arredondamento das barras
_BOOST_SLOT_H: int   = 38      # altura de cada slot de boost


class HUD:
    """Painel HUD lateral direito."""

    # Compatibilidade: o engine antigo verificava HUD_HEIGHT para o top bar.
    # Mantido como 0 — não há barra de topo nesta versão.
    HUD_HEIGHT: int = 0

    def __init__(self, jogador: str = "Jogador",
                 modo: str = "OG Snake",
                 dificuldade: str = "Normal") -> None:
        self.jogador     = jogador
        self.modo        = modo
        self.dificuldade = dificuldade

        # Score animation
        self._score:   int   = 0
        self._pop_t:   float = _POP_DURATION   # "já terminou" no início

        # Fonts — inicializadas preguiçosamente
        self._f_label:  pygame.font.Font | None = None
        self._f_value:  pygame.font.Font | None = None
        self._f_big:    pygame.font.Font | None = None
        self._f_name:   pygame.font.Font | None = None
        self._f_mini:   pygame.font.Font | None = None

    # ── API pública ───────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Avança as animações; chamar a ~60 fps."""
        if self._pop_t < _POP_DURATION:
            self._pop_t += dt

    def set_score(self, pts: int) -> None:
        """Actualiza a pontuação e dispara a animação de pop se mudou."""
        if pts != self._score:
            self._pop_t = 0.0
        self._score = pts

    def atualizar_pontuacao(self, nova: int) -> None:
        """Alias de compatibilidade — equivale a set_score."""
        self.set_score(nova)

    def atualizar_info(self, jogador=None, modo=None, dificuldade=None) -> None:
        if jogador:     self.jogador     = jogador
        if modo:        self.modo        = modo
        if dificuldade: self.dificuldade = dificuldade

    def draw_sidebar(self, surface: pygame.Surface,
                     info: Dict[str, Any], modo: str) -> None:
        """
        Renderiza o painel lateral em surface.

        `info` é o dicionário devolvido por modo_atual.hud_info().
        `modo` é a constante de modo (cfg.MODO_*).
        """
        self._init_fonts()

        sw   = C.SIDEBAR_W
        sh   = surface.get_height()
        sx   = surface.get_width() - sw   # x de início do painel

        # ── Fundo do painel ────────────────────────────────────────────
        pygame.draw.rect(surface, C.HUD_SIDEBAR_BG,
                         pygame.Rect(sx, 0, sw, sh))
        # Linha separadora vertical
        pygame.draw.line(surface, C.HUD_SIDEBAR_SEP,
                         (sx, 0), (sx, sh), 2)

        # ── Despachar para o renderer correcto ─────────────────────────
        if modo == C.MODO_1V1:
            self._draw_1v1(surface, sx, sw, sh, info)
        elif modo == C.MODO_VS_AI:
            self._draw_vsai(surface, sx, sw, sh, info)
        else:
            self._draw_og(surface, sx, sw, sh, info)

    # ── Renderers por modo ────────────────────────────────────────────────────

    def _draw_og(self, surface, sx, sw, sh, info: dict) -> None:
        """OG Snake: nome · pontuação · comprimento · modo/dif."""
        y = 0
        y = self._section_header(surface, sx, y, sw, "JOGADOR",
                                 self.jogador, C.SNAKE1_HEAD)
        y = self._section_score(surface, sx, y, sw,
                                info.get("score", self._score))
        y = self._section_length(surface, sx, y, sw,
                                 info.get("length", 1),
                                 info.get("max_length", 60),
                                 C.SNAKE1_HEAD, label="COMPRIMENTO")
        y = self._section_mode(surface, sx, y, sw)

    def _draw_vsai(self, surface, sx, sw, sh, info: dict) -> None:
        """Vs AI: nome · pontuação · comprimento vs bot · boosts."""
        y = 0
        y = self._section_header(surface, sx, y, sw, "JOGADOR",
                                 self.jogador, C.SNAKE1_HEAD)
        y = self._section_score(surface, sx, y, sw,
                                info.get("score", self._score))

        # Comprimentos lado a lado
        y = self._section_divider(surface, sx, y, sw, "COMPRIMENTO")
        p_len = info.get("length",     1)
        b_len = info.get("bot_length", 1)
        mx    = max(p_len, b_len, 20)
        y = self._draw_mini_length_row(surface, sx, y, sw,
                                       self.jogador, p_len, mx, C.SNAKE1_HEAD)
        y = self._draw_mini_length_row(surface, sx, y, sw,
                                       "Bot", b_len, mx, (200, 60, 60))
        y += 8

        # Boosts
        vel_t   = info.get("boost_vel_ticks",   0)
        imune_t = info.get("boost_imune_ticks", 0)
        fps_ref = info.get("fps_ref", 7)
        if vel_t > 0 or imune_t > 0 or True:   # sempre visível
            y = self._section_divider(surface, sx, y, sw, "BOOSTS")
            y = self._draw_boost_slot(surface, sx, y, sw,
                                      "VEL", (255, 200, 40),
                                      vel_t, C.SIDEBAR_W if hasattr(C, "SIDEBAR_W") else 160,
                                      fps_ref)
            y = self._draw_boost_slot(surface, sx, y, sw,
                                      "IMU", (60, 180, 255),
                                      imune_t, 90,
                                      fps_ref)
            y += 6

        self._section_mode(surface, sx, y, sw)

    def _draw_1v1(self, surface, sx, sw, sh, info: dict) -> None:
        """1v1: metade superior P1, metade inferior P2."""
        mid = sh // 2

        # P1 — metade superior
        self._draw_1v1_half(surface, sx, 0, sw, mid,
                            player_label="P1 · WASD",
                            name=info.get("p1_name", "P1"),
                            length=info.get("p1_length", 1),
                            max_len=info.get("max_length", 60),
                            color=C.SNAKE1_HEAD,
                            is_ready=info.get("p1_ready", False))

        # Separador central
        pygame.draw.line(surface, C.HUD_SIDEBAR_SEP,
                         (sx + 6, mid), (sx + sw - 6, mid), 2)

        # P2 — metade inferior
        self._draw_1v1_half(surface, sx, mid, sw, sh - mid,
                            player_label="P2 · SETAS",
                            name=info.get("p2_name", "P2"),
                            length=info.get("p2_length", 1),
                            max_len=info.get("max_length", 60),
                            color=C.SNAKE2_HEAD,
                            is_ready=info.get("p2_ready", False))

    def _draw_1v1_half(self, surface, sx, top, sw, h,
                       player_label, name, length, max_len, color,
                       is_ready: bool) -> None:
        """Renderiza metade do painel 1v1 para um jogador."""
        p  = _PAD
        cy = top + 14

        # Etiqueta do jogador (P1 · WASD)
        lbl = self._f_mini.render(player_label.upper(), True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, cy))
        cy += lbl.get_height() + 3

        # Nome
        nm = self._f_name.render(name, True, color)
        surface.blit(nm, (sx + p, cy))
        cy += nm.get_height() + 10

        # Linha divisória
        pygame.draw.line(surface, C.HUD_SECTION_LINE,
                         (sx + p, cy), (sx + sw - p, cy), 1)
        cy += 8

        # Comprimento
        lbl2 = self._f_mini.render("COMPRIMENTO", True, C.HUD_LABEL)
        surface.blit(lbl2, (sx + p, cy))
        cy += lbl2.get_height() + 4
        bar_w = sw - p * 2
        filled = max(1, int(bar_w * min(length, max_len) / max(max_len, 1)))
        pygame.draw.rect(surface, C.HUD_SECTION_LINE,
                         pygame.Rect(sx + p, cy, bar_w, _BAR_H),
                         border_radius=_BAR_RADIUS)
        pygame.draw.rect(surface, color,
                         pygame.Rect(sx + p, cy, filled, _BAR_H),
                         border_radius=_BAR_RADIUS)
        num = self._f_label.render(str(length), True, color)
        surface.blit(num, (sx + sw - p - num.get_width(), cy - 1))
        cy += _BAR_H + 10

        # Indicador de pronto / em espera
        if is_ready:
            dot_col = (80, 200, 100)
            status  = "PRONTO"
        else:
            dot_col = (180, 80, 80)
            status  = "ESPERA..."
        pygame.draw.circle(surface, dot_col,
                           (sx + p + 5, cy + 6), 4)
        st = self._f_mini.render(status, True, dot_col)
        surface.blit(st, (sx + p + 14, cy))

    # ── Secções reutilizáveis ──────────────────────────────────────────────────

    def _section_header(self, surface, sx, y, sw,
                        label: str, name: str, color) -> int:
        """Cabeçalho: etiqueta pequena + nome em destaque."""
        p  = _PAD
        y += 14
        lbl = self._f_mini.render(label, True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y += lbl.get_height() + 3
        nm = self._f_name.render(name[:10], True, color)
        surface.blit(nm, (sx + p, y))
        y += nm.get_height() + _SEC_GAP
        pygame.draw.line(surface, C.HUD_SECTION_LINE,
                         (sx + p, y), (sx + sw - p, y), 1)
        return y + _SEC_GAP + 2

    def _section_score(self, surface, sx, y, sw, score: int) -> int:
        """Pontuação com efeito de pop ao ganhar pontos."""
        p   = _PAD
        lbl = self._f_mini.render("PONTUAÇÃO", True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y += lbl.get_height() + 4

        # Animação: t=0 (pop) → t=POP_DURATION (normal)
        t     = min(1.0, self._pop_t / _POP_DURATION)
        scale = 1.0 + 0.55 * (1.0 - _ease_out_cubic(t))   # 1.55 → 1.0
        color = _lerp_color(C.WHITE, C.HUD_SCORE, t)

        # Renderizar numa superficie intermédia para escalar
        base_surf = self._f_big.render(str(score), True, color)
        bw, bh    = base_surf.get_size()
        sw2 = max(1, int(bw * scale))
        sh2 = max(1, int(bh * scale))
        try:
            scaled = pygame.transform.smoothscale(base_surf, (sw2, sh2))
        except Exception:
            scaled = base_surf
        cx = sx + sw // 2 - sw2 // 2
        surface.blit(scaled, (cx, y))
        y += sh2 + _SEC_GAP

        pygame.draw.line(surface, C.HUD_SECTION_LINE,
                         (sx + p, y), (sx + sw - p, y), 1)
        return y + _SEC_GAP + 2

    def _section_length(self, surface, sx, y, sw,
                        length: int, max_len: int,
                        color, label: str = "COMPRIMENTO") -> int:
        """Barra de comprimento com número."""
        p    = _PAD
        lbl  = self._f_mini.render(label, True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y += lbl.get_height() + 4

        bar_w  = sw - p * 2
        filled = max(1, int(bar_w * min(length, max_len) / max(max_len, 1)))

        # Fundo da barra
        pygame.draw.rect(surface, C.HUD_SECTION_LINE,
                         pygame.Rect(sx + p, y, bar_w, _BAR_H),
                         border_radius=_BAR_RADIUS)
        # Preenchimento
        pygame.draw.rect(surface, color,
                         pygame.Rect(sx + p, y, filled, _BAR_H),
                         border_radius=_BAR_RADIUS)

        # Número à direita
        num = self._f_label.render(str(length), True, color)
        surface.blit(num, (sx + sw - p - num.get_width(), y - 1))
        y += _BAR_H + _SEC_GAP

        pygame.draw.line(surface, C.HUD_SECTION_LINE,
                         (sx + p, y), (sx + sw - p, y), 1)
        return y + _SEC_GAP + 2

    def _section_mode(self, surface, sx, y, sw) -> int:
        """Modo e dificuldade no fundo do painel."""
        p   = _PAD
        lbl = self._f_mini.render("MODO", True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y += lbl.get_height() + 3
        mv = self._f_label.render(self.modo, True, C.HUD_TEXT)
        surface.blit(mv, (sx + p, y))
        y += mv.get_height() + 2
        dv = self._f_mini.render(self.dificuldade, True, C.HUD_LABEL)
        surface.blit(dv, (sx + p, y))
        return y + dv.get_height() + _SEC_GAP

    def _section_divider(self, surface, sx, y, sw, label: str) -> int:
        """Linha divisória com etiqueta."""
        p   = _PAD
        lbl = self._f_mini.render(label, True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y  += lbl.get_height() + 4
        return y

    # ── Widgets auxiliares ────────────────────────────────────────────────────

    def _draw_mini_length_row(self, surface, sx, y, sw,
                              name: str, length: int,
                              max_len: int, color) -> int:
        """Linha compacta: nome + mini barra + número (para comparação)."""
        p      = _PAD
        bar_w  = sw - p * 2
        name_s = self._f_mini.render(name[:8], True, C.HUD_TEXT)
        surface.blit(name_s, (sx + p, y))
        by = y + name_s.get_height() + 2
        filled = max(1, int(bar_w * min(length, max_len) / max(max_len, 1)))
        pygame.draw.rect(surface, C.HUD_SECTION_LINE,
                         pygame.Rect(sx + p, by, bar_w, _BAR_H - 1),
                         border_radius=_BAR_RADIUS)
        pygame.draw.rect(surface, color,
                         pygame.Rect(sx + p, by, filled, _BAR_H - 1),
                         border_radius=_BAR_RADIUS)
        num = self._f_mini.render(str(length), True, color)
        surface.blit(num, (sx + sw - p - num.get_width(), by - 1))
        return by + (_BAR_H - 1) + 6

    def _draw_boost_slot(self, surface, sx, y, sw,
                         nome: str, cor,
                         ticks: int, duracao: int,
                         fps: int) -> int:
        """
        Slot de boost: ícone + barra de duração + tempo restante.
        Fundo subtil quando inactivo, borda colorida quando activo.
        """
        p      = _PAD
        ativo  = ticks > 0
        slot_h = _BOOST_SLOT_H

        # Fundo do slot
        cor_fundo = (32, 36, 50) if ativo else (22, 24, 32)
        pygame.draw.rect(surface, cor_fundo,
                         pygame.Rect(sx + p, y, sw - p * 2, slot_h),
                         border_radius=5)

        # Borda colorida quando activo
        cor_borda = cor if ativo else (38, 42, 58)
        pygame.draw.rect(surface, cor_borda,
                         pygame.Rect(sx + p, y, sw - p * 2, slot_h),
                         1, border_radius=5)

        # Nome do boost
        cor_texto = cor if ativo else (55, 60, 80)
        tn = self._f_label.render(nome, True, cor_texto)
        surface.blit(tn, (sx + p + 6, y + 6))

        # Tempo restante (segundos)
        if ativo:
            segs = max(0, ticks // max(fps, 1))
            ts   = self._f_mini.render(f"{segs}s", True, (200, 210, 225))
            surface.blit(ts, (sx + sw - p - ts.get_width() - 4, y + 7))

        # Barra de progresso na base do slot
        bar_y = y + slot_h - 6
        bar_w = sw - p * 2
        pygame.draw.rect(surface, (28, 30, 42),
                         pygame.Rect(sx + p, bar_y, bar_w, 4),
                         border_radius=2)
        if ativo and duracao > 0:
            fill = max(1, int(bar_w * ticks / duracao))
            pygame.draw.rect(surface, cor,
                             pygame.Rect(sx + p, bar_y, fill, 4),
                             border_radius=2)

        return y + slot_h + 6

    # ── Inicialização de fontes ────────────────────────────────────────────────

    def _init_fonts(self) -> None:
        """Inicialização preguiçosa — evita chamar SysFont antes de pygame.init()."""
        if self._f_label is not None:
            return
        self._f_mini  = pygame.font.SysFont("Consolas", 13)
        self._f_label = pygame.font.SysFont("Consolas", 15)
        self._f_value = pygame.font.SysFont("Consolas", 18)
        self._f_name  = pygame.font.SysFont("Consolas", 20, bold=True)
        self._f_big   = pygame.font.SysFont("Consolas", 36, bold=True)

    # ── Compatibilidade com chamadas antigas ──────────────────────────────────

    def draw(self, surface, score=None, modo_override=None) -> None:
        """
        Stub de compatibilidade — o engine novo chama draw_sidebar().
        Mantido para não quebrar código externo que ainda use esta assinatura.
        """
        pass


# ── Utilitários ───────────────────────────────────────────────────────────────

def _lerp_color(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3