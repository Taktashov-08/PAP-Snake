# src/game/core/setup_mapas.py
"""
Gerador automático de mapas.

Chamado por main.py antes de arrancar o jogo.
Cria todos os ficheiros em assets/mapas/ se não existirem,
usando sempre caminhos absolutos (funciona de qualquer directório
e dentro de um .exe gerado pelo PyInstaller).

Mapas gerados:
  assets/mapas/campo_livre.txt   — campo aberto sem obstáculos
  assets/mapas/obstaculos.txt    — campo com paredes interiores (sem bordas)
  assets/mapas/arena.txt         — arena fechada com paredes interiores
  assets/mapas/1v1_mapa1.txt     — cruzamentos
  assets/mapas/1v1_mapa2.txt     — labirinto
  assets/mapas/1v1_mapa3.txt     — corredores

Uso::

    from game.core.setup_mapas import garantir_mapas
    garantir_mapas()   # no-op se todos os ficheiros já existirem
"""
from __future__ import annotations

import os
from typing import List

from game.core.caminhos import caminho_recurso

# ── Dimensões da grelha (devem coincidir com config.py) ──────────────────────
COLS: int = 45
ROWS: int = 30

# Directório de destino — resolvido com caminho_recurso para ser independente
# do directório de trabalho
_PASTA_MAPAS: str = caminho_recurso("assets/mapas")


# ── Utilitários de construção de grelha ───────────────────────────────────────

def _vazio() -> List[List[str]]:
    """Grelha COLS×ROWS preenchida com '.'."""
    return [["." for _ in range(COLS)] for _ in range(ROWS)]


def _h(grid: List[List[str]], y: int, x1: int, x2: int) -> None:
    """Traça uma parede horizontal de x1 a x2 na linha y."""
    for x in range(x1, x2 + 1):
        if 0 <= y < ROWS and 0 <= x < COLS:
            grid[y][x] = "#"


def _v(grid: List[List[str]], x: int, y1: int, y2: int) -> None:
    """Traça uma parede vertical de y1 a y2 na coluna x."""
    for y in range(y1, y2 + 1):
        if 0 <= y < ROWS and 0 <= x < COLS:
            grid[y][x] = "#"


def _bordas(grid: List[List[str]]) -> None:
    """Preenche as 4 bordas exteriores com '#'."""
    for x in range(COLS):
        grid[0][x]      = "#"
        grid[ROWS-1][x] = "#"
    for y in range(ROWS):
        grid[y][0]      = "#"
        grid[y][COLS-1] = "#"


def _escrever(grid: List[List[str]], nome: str) -> str:
    """
    Serializa a grelha e escreve o ficheiro.
    Devolve o caminho absoluto do ficheiro escrito.
    """
    os.makedirs(_PASTA_MAPAS, exist_ok=True)
    caminho = os.path.join(_PASTA_MAPAS, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        for row in grid:
            f.write("".join(row) + "\n")
    return caminho


# ── Mapas modo clássico / VS AI ───────────────────────────────────────────────

def _gerar_campo_livre() -> None:
    grid = _vazio()
    grid[15][22] = "S"
    _escrever(grid, "campo_livre.txt")


def _gerar_obstaculos() -> None:
    """Mapa borderless com paredes interiores simétricas."""
    grid = _vazio()

    # Paredes horizontais
    _h(grid,  7,  4, 16); _h(grid,  4, 37, 42)
    _h(grid, 10, 34, 39); _h(grid, 12, 17, 25)
    _h(grid, 14, 30, 39); _h(grid, 18,  8, 11)
    _h(grid, 22,  4,  7); _h(grid, 27, 16, 30)
    _h(grid, 27, 39, 42)

    # Paredes verticais
    _v(grid, 42,  4,  6); _v(grid, 30,  5, 14)
    _v(grid, 34,  5, 10); _v(grid, 21,  8, 16)
    _v(grid,  8, 11, 18); _v(grid,  7, 22, 27)
    _v(grid,  4, 17, 22); _v(grid, 11, 18, 25)
    _v(grid, 35, 20, 27); _v(grid, 42, 20, 27)

    grid[15][22] = "S"
    _escrever(grid, "obstaculos.txt")


def _gerar_arena() -> None:
    """Arena fechada com bordas sólidas e paredes interiores."""
    grid = _vazio()
    _bordas(grid)

    # Paredes interiores horizontais
    _h(grid,  6,  7, 39); _h(grid, 10, 27, 35)
    _h(grid, 21, 10, 19); _h(grid, 25,  7, 39)

    # Paredes interiores verticais
    _v(grid,  7,  6, 13); _v(grid, 14, 10, 16)
    _v(grid, 23,  4, 11); _v(grid, 23, 20, 27)
    _v(grid, 32, 15, 21); _v(grid, 39, 18, 25)

    grid[15][22] = "S"
    _escrever(grid, "arena.txt")


# ── Mapas 1v1 ─────────────────────────────────────────────────────────────────

def _gerar_1v1_mapa1() -> None:
    """Cruzamentos — posições S e P simétricas."""
    grid = _vazio()
    _bordas(grid)

    # Paredes horizontais
    _h(grid,  8,  9, 20); _h(grid,  8, 24, 35)
    _h(grid, 20,  5, 11); _h(grid, 20, 31, 37)

    # Paredes verticais
    _v(grid, 12,  9, 13); _v(grid, 12, 16, 20)
    _v(grid, 21,  6,  8); _v(grid, 21, 20, 28)
    _v(grid, 32,  4,  8); _v(grid, 32, 20, 24)

    # Ilhas centrais
    _h(grid, 13, 18, 22)
    _v(grid, 20, 14, 18)

    grid[26][4]  = "S"   # spawn P1 (WASD)
    grid[3][43]  = "P"   # spawn P2 (Setas)
    _escrever(grid, "1v1_mapa1.txt")


def _gerar_1v1_mapa2() -> None:
    """Labirinto — caminhos estreitos com muitas opções."""
    grid = _vazio()
    _bordas(grid)

    # Estrutura de labirinto
    _v(grid, 16,  3,  3); _h(grid,  3, 16, 16)
    _h(grid,  4,  5,  5); _v(grid,  5,  4,  7)
    _h(grid,  5, 13, 13); _h(grid,  6, 13, 13)
    _h(grid,  7, 13, 13)
    _v(grid,  5, 11, 13); _v(grid, 13, 11, 13)
    _h(grid,  8, 13, 21); _h(grid,  8, 23, 31)
    _h(grid,  8, 33, 38); _h(grid,  8, 40, 43)
    _v(grid, 21,  9, 12); _v(grid, 21, 14, 17)
    _h(grid, 14, 23, 35); _v(grid, 35, 14, 17)
    _v(grid, 39, 11, 17); _h(grid, 17, 17, 25)
    _h(grid, 20,  5,  8); _h(grid, 21, 21, 24)
    _h(grid, 21, 28, 37); _v(grid,  4, 18, 22)
    _h(grid, 22, 12, 17); _v(grid, 12, 17, 22)
    _v(grid, 17, 22, 25); _h(grid, 25,  4,  7)
    _v(grid,  7, 25, 28); _h(grid, 25, 22, 28)
    _h(grid, 21, 28, 37)
    _v(grid, 37, 21, 24); _h(grid, 24, 31, 43)
    _v(grid, 43, 14, 24)
    _h(grid, 25, 39, 42)

    grid[19][15] = "S"
    grid[10][40] = "P"
    _escrever(grid, "1v1_mapa2.txt")


def _gerar_1v1_mapa3() -> None:
    """Corredores — estrutura em anéis com passagens estreitas."""
    grid = _vazio()
    _bordas(grid)

    # Anel exterior
    _h(grid,  4, 26, 34)
    _v(grid, 40,  5,  7); _v(grid, 40, 16, 21)
    _h(grid,  9,  1,  9); _h(grid,  9, 22, 44)
    _v(grid,  5, 13, 25); _v(grid, 39, 19, 25)
    _h(grid, 13,  5,  5); _h(grid, 14,  5, 15)
    _h(grid, 14, 23, 43)
    _h(grid, 15, 23, 23)
    _v(grid,  5, 13, 17); _v(grid,  5, 22, 25)
    _h(grid, 25,  6, 12)
    _v(grid,  6, 25, 28); _h(grid, 25, 40, 43)
    _v(grid, 43, 22, 25)

    # Estruturas centrais
    _h(grid, 19,  9, 43)

    grid[26][37] = "S"
    grid[3][3]   = "P"
    _escrever(grid, "1v1_mapa3.txt")


# ── Ponto de entrada público ──────────────────────────────────────────────────

# Mapeamento: nome do ficheiro → função geradora
_GERADORES = {
    "campo_livre.txt": _gerar_campo_livre,
    "obstaculos.txt":  _gerar_obstaculos,
    "arena.txt":       _gerar_arena,
    "1v1_mapa1.txt":   _gerar_1v1_mapa1,
    "1v1_mapa2.txt":   _gerar_1v1_mapa2,
    "1v1_mapa3.txt":   _gerar_1v1_mapa3,
}


def garantir_mapas(forcar: bool = False) -> list[str]:
    """
    Verifica se cada mapa existe e cria-o se não existir.

    Parâmetros:
        forcar — se True, recria todos os mapas mesmo que já existam
                 (útil para resetar mapas corrompidos ou actualizações)

    Devolve:
        Lista dos nomes dos ficheiros que foram (re)criados.
    """
    os.makedirs(_PASTA_MAPAS, exist_ok=True)
    criados: list[str] = []

    for nome, gerador in _GERADORES.items():
        caminho = os.path.join(_PASTA_MAPAS, nome)
        if forcar or not os.path.exists(caminho):
            gerador()
            criados.append(nome)

    return criados


def recriar_todos() -> list[str]:
    """Atalho para forcar=True — recria todos os mapas."""
    return garantir_mapas(forcar=True)