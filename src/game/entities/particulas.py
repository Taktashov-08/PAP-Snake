# src/game/entities/particulas.py
"""
Sistema de partículas leve para efeitos visuais dinâmicos.

Emissores disponíveis:
  emit_food_burst   — explosão ao comer comida
  emit_boost_pickup — anel ao apanhar boost
  emit_death        — explosão distribuída ao morrer

O sistema é criado uma vez no Engine e partilhado por todos os modos.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

Color = Tuple[int, int, int]

# ── Dataclass de partícula individual ─────────────────────────────────────────

@dataclass
class _Particle:
    """Estado de uma partícula — uso interno ao módulo."""
    x:       float
    y:       float
    vx:      float          # velocidade horizontal (px/s)
    vy:      float          # velocidade vertical   (px/s)
    life:    float          # 1.0 → 0.0 (morta quando < 0)
    decay:   float          # diminuição de life por segundo
    radius:  float          # raio base em píxeis
    color:   Color
    gravity: float = 0.0   # aceleração vertical adicional (px/s²)


# ── Sistema público ────────────────────────────────────────────────────────────

class ParticleSystem:
    """
    Gestor central de partículas com limite de segurança (_MAX).

    Exemplo de uso no engine::

        self.particles = ParticleSystem()
        # em eventos de jogo:
        self.particles.emit_food_burst(pos, color, block)
        # no loop visual (60 fps):
        self.particles.update(dt)
        self.particles.draw(surface)
    """

    _MAX: int = 500  # limite para evitar lag em casos extremos

    def __init__(self) -> None:
        self._pool: List[_Particle] = []

    # ── Emissores ─────────────────────────────────────────────────────────────

    def emit_food_burst(self, pos_px: Tuple[int, int], color: Color,
                        block: int, count: int = 14) -> None:
        """Explosão radial ao comer comida."""
        cx, cy = pos_px[0] + block // 2, pos_px[1] + block // 2
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(55, 165)
            self._emit(_Particle(
                x=float(cx), y=float(cy),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=1.0,
                decay=random.uniform(2.0, 3.5),
                radius=random.uniform(2.0, max(3.0, block / 4.0)),
                color=color,
                gravity=95.0,
            ))

    def emit_boost_pickup(self, pos_px: Tuple[int, int], color: Color,
                          block: int) -> None:
        """Anel de partículas ao apanhar um boost."""
        cx, cy = pos_px[0] + block // 2, pos_px[1] + block // 2
        n = 18
        for i in range(n):
            angle = (math.tau / n) * i
            speed = random.uniform(70, 120)
            self._emit(_Particle(
                x=float(cx), y=float(cy),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=1.0,
                decay=random.uniform(1.5, 2.5),
                radius=random.uniform(2.0, 4.0),
                color=color,
                gravity=0.0,
            ))

    def emit_death(self, segments: list, color: Color, block: int) -> None:
        """Explosão distribuída ao longo do corpo da cobra."""
        step = max(1, len(segments) // 18)   # máx ~18 origens de emissão
        for seg in segments[::step]:
            cx, cy = seg[0] + block // 2, seg[1] + block // 2
            for _ in range(5):
                angle = random.uniform(0, math.tau)
                speed = random.uniform(30, 105)
                self._emit(_Particle(
                    x=float(cx), y=float(cy),
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    life=1.0,
                    decay=random.uniform(1.2, 2.2),
                    radius=random.uniform(2.0, max(3.0, block / 3.0)),
                    color=color,
                    gravity=130.0,
                ))

    # ── Loop visual ───────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Avança física de todas as partículas e remove as expiradas."""
        friction = 1.0 - 4.5 * dt    # atrito suave independente de FPS
        live: List[_Particle] = []
        for p in self._pool:
            p.x    += p.vx * dt
            p.y    += p.vy * dt
            p.vy   += p.gravity * dt
            p.vx   *= friction
            p.life -= p.decay * dt
            if p.life > 0.0:
                live.append(p)
        self._pool = live

    def draw(self, surface: pygame.Surface) -> None:
        """
        Renderiza partículas na surface.
        A cor é escurecida proporcionalmente à vida (fade → preto),
        o que funciona nativamente em fundos escuros sem precisar de
        superfícies alpha separadas — muito mais rápido.
        """
        for p in self._pool:
            t   = max(0.0, p.life)
            r   = max(1, int(p.radius * (0.35 + 0.65 * t)))
            col = (int(p.color[0] * t),
                   int(p.color[1] * t),
                   int(p.color[2] * t))
            pygame.draw.circle(surface, col, (int(p.x), int(p.y)), r)

    def clear(self) -> None:
        """Remove todas as partículas — útil ao reiniciar a sessão."""
        self._pool.clear()

    @property
    def count(self) -> int:
        """Número de partículas activas (útil para debug/profiling)."""
        return len(self._pool)

    # ── Interno ───────────────────────────────────────────────────────────────

    def _emit(self, p: _Particle) -> None:
        if len(self._pool) < self._MAX:
            self._pool.append(p)