# game/config.py
# Valores iniciais (podes alterar desired_width/desired_height)
DESIRED_SCREEN_WIDTH = 900
DESIRED_SCREEN_HEIGHT = 600

# grelha pretendida (quantas colunas/linhas lógica: 900/20=45, 600/20=30)
GRID_COLS = 45
GRID_ROWS = 30

def fit_screen_to_grid(desired_w, desired_h, cols=GRID_COLS, rows=GRID_ROWS):
    """
    Ajusta largura/altura e escolhe BLOCK_SIZE inteiro máximo que cabe em ambas as dimensões.
    Retorna (SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE).
    """
    # block máximo que cabe em largura e altura
    block_from_w = desired_w // cols
    block_from_h = desired_h // rows
    block = min(block_from_w, block_from_h)
    if block < 4:
        # fallback mínimo para não ficar ridículo
        block = 4
    screen_w = cols * block
    screen_h = rows * block
    return screen_w, screen_h, block

# calcula valores finais (executa ao importar config)
SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE = fit_screen_to_grid(
    DESIRED_SCREEN_WIDTH, DESIRED_SCREEN_HEIGHT, GRID_COLS, GRID_ROWS
)

# constantes que podes usar normalmente
FPS = 10
WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (0,255,0)
RED = (255,0,0)
BLUE = (0,0,255)

# Para debug: imprime apenas quando corre localmente (opcional)
if __name__ == "__main__":
    print("Final screen:", SCREEN_WIDTH, SCREEN_HEIGHT, "BLOCK_SIZE:", BLOCK_SIZE)
