# tools/generate_maps.py
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

# ---------- MAPA ARENA ----------
arena = make_empty()

# borda externa (limite)
for x in range(COLS):
    arena[0][x] = '#'
    arena[ROWS-1][x] = '#'
for y in range(ROWS):
    arena[y][0] = '#'
    arena[y][COLS-1] = '#'

# linhas horizontais (user)
def h(grid, y, x1, x2):
    for x in range(x1, x2+1):
        if 0 <= x < COLS and 0 <= y < ROWS:
            grid[y][x] = '#'

h(arena, 6, 7, 39)
h(arena, 10, 27, 35)
h(arena, 21, 10, 19)
h(arena, 25, 7, 39)

# linhas verticais (user)
def v(grid, x, y1, y2):
    for y in range(y1, y2+1):
        if 0 <= x < COLS and 0 <= y < ROWS:
            grid[y][x] = '#'

v(arena, 7, 6, 13)
v(arena, 14, 10, 16)
v(arena, 23, 4, 11)
v(arena, 23, 20, 27)
v(arena, 32, 15, 21)
v(arena, 39, 18, 25)

# spawn (centro aproximado)
spawn_x, spawn_y = 22, 15
arena[spawn_y][spawn_x] = 'S'

# ---------- MAPA OBSTACULOS (borderless) ----------
obs = make_empty()

# horizontais
h(obs, 7, 4, 16)
h(obs, 4, 37, 42)
h(obs, 10, 34, 39)
h(obs, 12, 17, 25)
h(obs, 14, 30, 39)
h(obs, 18, 8, 11)
h(obs, 22, 4, 7)
h(obs, 27, 16, 30)
h(obs, 27, 39, 42)

# verticais
v(obs, 42, 4, 6)
v(obs, 30, 5, 14)
v(obs, 34, 5, 10)
v(obs, 21, 8, 16)
v(obs, 8, 11, 18)
v(obs, 7, 22, 27)
v(obs, 4, 17, 22)
v(obs, 11, 18, 25)
v(obs, 35, 20, 27)
v(obs, 42, 20, 27)  # note: x=42 appears twice in input; ok (idempotent)

# spawn no centro também
obs[spawn_y][spawn_x] = 'S'

# write files
write_map(arena, 'assets/maps/arena.txt')
write_map(obs,   'assets/maps/obstaculos.txt')

print("Maps gerados em assets/maps/ (arena.txt e obstaculos.txt)")
