# src/game/ui/hud.py
from __future__ import annotations

import math
from typing import Any, Dict, Tuple

import pygame

import game.config as C

# ── Constantes de layout ──────────────────────────────────────────────────────
_PAD:          int   = 12
_SEC_GAP:      int   = 10
_POP_DURATION: float = 0.40
_BAR_H:        int   = 6
_BAR_RADIUS:   int   = 3
_BOOST_SLOT_H: int   = 38


class HUD:
    """Painel HUD lateral direito."""

    HUD_HEIGHT: int = 0

    def __init__(self, jogador: str = "Jogador",
                 modo: str = "OG Snake",
                 dificuldade: str = "Normal",
                 jogador2: str = "Jogador 2") -> None:
        self.jogador     = jogador
        self.jogador2    = jogador2
        self.modo        = modo
        self.dificuldade = dificuldade

        self._score:  int   = 0
        self._pop_t:  float = _POP_DURATION

        self._f_label: pygame.font.Font | None = None
        self._f_value: pygame.font.Font | None = None
        self._f_big:   pygame.font.Font | None = None
        self._f_name:  pygame.font.Font | None = None
        self._f_mini:  pygame.font.Font | None = None

    # ── API pública ───────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._pop_t < _POP_DURATION:
            self._pop_t += dt

    def set_score(self, pts: int) -> None:
        if pts != self._score:
            self._pop_t = 0.0
        self._score = pts

    def atualizar_pontuacao(self, nova: int) -> None:
        self.set_score(nova)

    def atualizar_info(self, jogador=None, modo=None, dificuldade=None, nome_p2=None) -> None:
        if jogador:     self.jogador     = jogador
        if modo:        self.modo        = modo
        if dificuldade: self.dificuldade = dificuldade
        if nome_p2:     self.jogador2    = nome_p2

    def draw_sidebar(self, surface: pygame.Surface,
                     info: Dict[str, Any], modo: str) -> None:
        self._init_fonts()

        sw = C.SIDEBAR_W
        sh = surface.get_height()
        sx = surface.get_width() - sw

        pygame.draw.rect(surface, C.HUD_SIDEBAR_BG,
                         pygame.Rect(sx, 0, sw, sh))
        pygame.draw.line(surface, C.HUD_SIDEBAR_SEP,
                         (sx, 0), (sx, sh), 2)

        if modo == C.MODO_1V1:
            self._draw_1v1(surface, sx, sw, sh, info)
        elif modo == C.MODO_VS_AI:
            self._draw_vsai(surface, sx, sw, sh, info)
        else:
            self._draw_og(surface, sx, sw, sh, info)

    # ── Renderers por modo ────────────────────────────────────────────────────

    def _draw_og(self, surface, sx, sw, sh, info: dict) -> None:
        y = 0
        y = self._section_header(surface, sx, y, sw, "JOGADOR",
                                 self.jogador, C.SNAKE1_HEAD)
        y = self._section_score(surface, sx, y, sw,
                                info.get("score", self._score))
        y = self._section_length(surface, sx, y, sw,
                                 info.get("length", 1),
                                 info.get("max_length", 60),
                                 C.SNAKE1_HEAD, label="COMPRIMENTO")
        self._section_mode(surface, sx, y, sw)

    def _draw_vsai(self, surface, sx, sw, sh, info: dict) -> None:
        y = 0
        y = self._section_header(surface, sx, y, sw, "JOGADOR",
                                 self.jogador, C.SNAKE1_HEAD)
        y = self._section_score(surface, sx, y, sw,
                                info.get("score", self._score))

        y = self._section_divider(surface, sx, y, sw, "COMPRIMENTO")
        p_len = info.get("length",     1)
        b_len = info.get("bot_length", 1)
        mx    = max(p_len, b_len, 20)
        y = self._draw_mini_length_row(surface, sx, y, sw,
                                       self.jogador, p_len, mx, C.SNAKE1_HEAD)
        y = self._draw_mini_length_row(surface, sx, y, sw,
                                       "Bot", b_len, mx, (200, 60, 60))
        y += 8

        vel_t   = info.get("boost_vel_ticks",   0)
        imune_t = info.get("boost_imune_ticks", 0)
        fps_ref = info.get("fps_ref", 7)
        y = self._section_divider(surface, sx, y, sw, "BOOSTS")
        y = self._draw_boost_slot(surface, sx, y, sw,
                                  "VEL", (255, 200, 40),
                                  vel_t, 90, fps_ref)
        y = self._draw_boost_slot(surface, sx, y, sw,
                                  "IMU", (60, 180, 255),
                                  imune_t, 60, fps_ref)
        y += 6
        self._section_mode(surface, sx, y, sw)

    def _draw_1v1(self, surface, sx, sw, sh, info: dict) -> None:
        mid = sh // 2

        self._draw_1v1_half(surface, sx, 0, sw, mid,
                            player_label="P1 · WASD",
                            name=info.get("p1_name", "P1"),
                            length=info.get("p1_length", 1),
                            max_len=info.get("max_length", 60),
                            color=C.SNAKE1_HEAD,
                            is_ready=info.get("p1_ready", False))

        pygame.draw.line(surface, C.HUD_SIDEBAR_SEP,
                         (sx + 6, mid), (sx + sw - 6, mid), 2)

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
        p  = _PAD
        cy = top + 14

        lbl = self._f_mini.render(player_label.upper(), True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, cy))
        cy += lbl.get_height() + 3

        nm = self._f_name.render(name, True, color)
        surface.blit(nm, (sx + p, cy))
        cy += nm.get_height() + 10

        pygame.draw.line(surface, C.HUD_SECTION_LINE,
                         (sx + p, cy), (sx + sw - p, cy), 1)
        cy += 8

        lbl2 = self._f_mini.render("COMPRIMENTO", True, C.HUD_LABEL)
        surface.blit(lbl2, (sx + p, cy))
        cy += lbl2.get_height() + 4
        bar_w  = sw - p * 2
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

        if is_ready:
            dot_col = (80, 200, 100)
            status  = "PRONTO"
        else:
            dot_col = (180, 80, 80)
            status  = "ESPERA..."
        pygame.draw.circle(surface, dot_col, (sx + p + 5, cy + 6), 4)
        st = self._f_mini.render(status, True, dot_col)
        surface.blit(st, (sx + p + 14, cy))

    # ── Secções reutilizáveis ─────────────────────────────────────────────────

    def _section_header(self, surface, sx, y, sw,
                        label: str, name: str, color) -> int:
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
        p   = _PAD
        lbl = self._f_mini.render("PONTUAÇÃO", True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y += lbl.get_height() + 4

        t     = min(1.0, self._pop_t / _POP_DURATION)
        scale = 1.0 + 0.55 * (1.0 - _ease_out_cubic(t))
        color = _lerp_color(C.WHITE, C.HUD_SCORE, t)

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
        p    = _PAD
        lbl  = self._f_mini.render(label, True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        y += lbl.get_height() + 4

        bar_w  = sw - p * 2
        filled = max(1, int(bar_w * min(length, max_len) / max(max_len, 1)))

        pygame.draw.rect(surface, C.HUD_SECTION_LINE,
                         pygame.Rect(sx + p, y, bar_w, _BAR_H),
                         border_radius=_BAR_RADIUS)
        pygame.draw.rect(surface, color,
                         pygame.Rect(sx + p, y, filled, _BAR_H),
                         border_radius=_BAR_RADIUS)

        num = self._f_label.render(str(length), True, color)
        surface.blit(num, (sx + sw - p - num.get_width(), y - 1))
        y += _BAR_H + _SEC_GAP

        pygame.draw.line(surface, C.HUD_SECTION_LINE,
                         (sx + p, y), (sx + sw - p, y), 1)
        return y + _SEC_GAP + 2

    def _section_mode(self, surface, sx, y, sw) -> int:
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
        p   = _PAD
        lbl = self._f_mini.render(label, True, C.HUD_LABEL)
        surface.blit(lbl, (sx + p, y))
        return y + lbl.get_height() + 4

    # ── Widgets auxiliares ────────────────────────────────────────────────────

    def _draw_mini_length_row(self, surface, sx, y, sw,
                              name: str, length: int,
                              max_len: int, color) -> int:
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
        p      = _PAD
        ativo  = ticks > 0
        slot_h = _BOOST_SLOT_H

        cor_fundo = (32, 36, 50) if ativo else (22, 24, 32)
        pygame.draw.rect(surface, cor_fundo,
                         pygame.Rect(sx + p, y, sw - p * 2, slot_h),
                         border_radius=5)

        cor_borda = cor if ativo else (38, 42, 58)
        pygame.draw.rect(surface, cor_borda,
                         pygame.Rect(sx + p, y, sw - p * 2, slot_h),
                         1, border_radius=5)

        cor_texto = cor if ativo else (55, 60, 80)
        tn = self._f_label.render(nome, True, cor_texto)
        surface.blit(tn, (sx + p + 6, y + 6))

        if ativo:
            segs = max(0, ticks // max(fps, 1))
            ts   = self._f_mini.render(f"{segs}s", True, (200, 210, 225))
            surface.blit(ts, (sx + sw - p - ts.get_width() - 4, y + 7))

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

    # ── Inicialização de fontes ───────────────────────────────────────────────

    def _init_fonts(self) -> None:
        if self._f_label is not None:
            return
        self._f_mini  = pygame.font.SysFont("Consolas", 13)
        self._f_label = pygame.font.SysFont("Consolas", 15)
        self._f_value = pygame.font.SysFont("Consolas", 18)
        self._f_name  = pygame.font.SysFont("Consolas", 20, bold=True)
        self._f_big   = pygame.font.SysFont("Consolas", 36, bold=True)

    # ── Compatibilidade com chamadas antigas ──────────────────────────────────

    def draw(self, surface, score=None, modo_override=None,
             pts_p1=None, pts_p2=None) -> None:
        """Stub de compatibilidade — o engine novo chama draw_sidebar()."""
        pass


# ── Utilitários ───────────────────────────────────────────────────────────────

def _lerp_color(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3