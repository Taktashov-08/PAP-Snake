# ferramentas/gerar_mapas.py
import os

COLS = 45
ROWS = 30

def make_empty():
    return [['.' for _ in range(COLS)] for __ in range(ROWS)]

def write_map(grid, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for row in grid:
            f.write(''.join(row) + '\n')

def h(grid, y, x1, x2):
    for x in range(x1, x2+1):
        if 0 <= x < COLS and 0 <= y < ROWS:
            grid[y][x] = '#'

def v(grid, x, y1, y2):
    for y in range(y1, y2+1):
        if 0 <= x < COLS and 0 <= y < ROWS:
            grid[y][x] = '#'

# ---------- MAPA ARENA ----------
arena = make_empty()

for x in range(COLS):
    arena[0][x] = '#'
    arena[ROWS-1][x] = '#'
for y in range(ROWS):
    arena[y][0] = '#'
    arena[y][COLS-1] = '#'

h(arena, 6, 7, 39);  h(arena, 10, 27, 35)
h(arena, 21, 10, 19); h(arena, 25, 7, 39)
v(arena, 7, 6, 13);  v(arena, 14, 10, 16)
v(arena, 23, 4, 11); v(arena, 23, 20, 27)
v(arena, 32, 15, 21); v(arena, 39, 18, 25)
arena[15][22] = 'S'

# ---------- MAPA OBSTACULOS (borderless) ----------
obs = make_empty()

h(obs, 7, 4, 16);  h(obs, 4, 37, 42)
h(obs, 10, 34, 39); h(obs, 12, 17, 25)
h(obs, 14, 30, 39); h(obs, 18, 8, 11)
h(obs, 22, 4, 7);  h(obs, 27, 16, 30)
h(obs, 27, 39, 42)
v(obs, 42, 4, 6);  v(obs, 30, 5, 14)
v(obs, 34, 5, 10); v(obs, 21, 8, 16)
v(obs, 8, 11, 18); v(obs, 7, 22, 27)
v(obs, 4, 17, 22); v(obs, 11, 18, 25)
v(obs, 35, 20, 27); v(obs, 42, 20, 27)
obs[15][22] = 'S'

# ---------- MAPA CAMPO LIVRE (sem obstaculos) ----------
vazio = make_empty()
vazio[15][22] = 'S'

# ---------- Escrever ficheiros ----------
write_map(arena, 'assets/mapas/arena.txt')
write_map(obs,   'assets/mapas/obstaculos.txt')
write_map(vazio, 'assets/mapas/campo_livre.txt')

print("Mapas gerados em assets/mapas/")
print("  - arena.txt")
print("  - obstaculos.txt")
print("  - campo_livre.txt")