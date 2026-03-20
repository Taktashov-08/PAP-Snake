# src/game/config.py
# Definicoes globais: dimensoes, grelha, paleta de cores e constantes de modo.

DESIRED_SCREEN_WIDTH  = 900
DESIRED_SCREEN_HEIGHT = 600
GRID_COLS = 45
GRID_ROWS  = 30

def fit_screen_to_grid(desired_w, desired_h, cols=GRID_COLS, rows=GRID_ROWS):
    block_from_w = desired_w // cols
    block_from_h = desired_h // rows
    block = min(block_from_w, block_from_h)
    if block < 4:
        block = 4
    return cols * block, rows * block, block

SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE = fit_screen_to_grid(
    DESIRED_SCREEN_WIDTH, DESIRED_SCREEN_HEIGHT, GRID_COLS, GRID_ROWS
)

FPS = 10

# ── Modos de jogo (constantes) ────────────────────────────────────────────────
MODO_OG_SNAKE    = "OG Snake"
MODO_1V1         = "1v1"
MODO_VS_AI       = "Vs AI"
MODO_SNAKE_TORRE = "Snake Torre"

# ── Dificuldades -> multiplicador de velocidade ───────────────────────────────
DIFICULDADES = {
    "Normal":       1.0,
    "Rapido":       1.5,
    "Muito Rapido": 2.0,
}

# ── Fundo & Superficies ───────────────────────────────────────────────────────
BG_DARK      = (18,  19,  24)
BG_PANEL     = (24,  26,  33)
BG_INPUT     = (30,  32,  40)
GRID_LINE    = (26,  28,  36)

# ── Paredes ───────────────────────────────────────────────────────────────────
WALL_FACE       = (38,  42,  58)
WALL_HIGHLIGHT  = (55,  60,  80)
WALL_SHADOW     = (22,  24,  32)
WALL_CORNER_HI  = (68,  74,  98)
WALL_INNER      = (32,  36,  50)
WALL_OUTER_FACE = (30,  33,  46)
WALL_OUTER_HI   = (48,  53,  72)

# ── Cobra P1 ──────────────────────────────────────────────────────────────────
SNAKE1_HEAD   = (100, 200, 120)
SNAKE1_BODY   = (60,  150,  80)
SNAKE1_BORDER = (30,   70,  40)

# ── Cobra P2 ──────────────────────────────────────────────────────────────────
SNAKE2_HEAD   = (80,  150, 220)
SNAKE2_BODY   = (50,  110, 175)
SNAKE2_BORDER = (25,   55,  95)

# ── Comida ────────────────────────────────────────────────────────────────────
FOOD_COLOR      = (220, 120,  60)
FOOD_BORDER     = (150,  75,  30)
FOOD_HIGHLIGHT  = (240, 160, 100)

# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_BG        = (18,  19,  24)
HUD_BORDER    = (40,  44,  60)
HUD_TEXT      = (170, 175, 192)
HUD_TEXT_MAIN = (215, 220, 232)
HUD_SCORE     = (100, 200, 120)
HUD_ACCENT    = (200, 165,  80)

# ── UI / Menu ─────────────────────────────────────────────────────────────────
WHITE         = (215, 220, 232)
BLACK         = (10,  11,  15)
GREEN         = (80,  170, 100)
RED           = (190,  70,  70)
BLUE          = (70,  120, 200)
UI_BORDER     = (42,  46,  62)

BTN_PLAY        = (40,  95, 175)
BTN_PLAY_HOV    = (55, 115, 200)
BTN_RECORDS     = (45, 130,  80)
BTN_RECORDS_HOV = (60, 155,  98)
BTN_HELP        = (155, 115,  45)
BTN_HELP_HOV    = (180, 138,  60)
BTN_QUIT        = (155,  55,  55)
BTN_QUIT_HOV    = (180,  70,  70)
BTN_MODE_A      = (40,  95, 175)
BTN_MODE_A_HOV  = (55, 115, 200)
BTN_MODE_B      = (120,  55, 155)
BTN_MODE_B_HOV  = (145,  70, 185)

TITLE_COLOR  = (210, 215, 230)
TITLE_ACCENT = (100, 200, 120)
