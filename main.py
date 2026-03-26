import sys
import os

# ── Caminhos absolutos independentes do directório de trabalho ────────────────
_raiz = os.path.abspath(os.path.dirname(__file__))
_src  = os.path.join(_raiz, "src")

if _src not in sys.path:
    sys.path.insert(0, _src)

# ── Garantir que todos os mapas existem antes de arrancar ─────────────────────
from game.core.setup_mapas import garantir_mapas

criados = garantir_mapas()
if criados:
    print(f"[setup] Mapas criados: {', '.join(criados)}")

# ── Arrancar o menu ───────────────────────────────────────────────────────────
from game.ui.menu import Menu

if __name__ == "__main__":
    menu = Menu()
    menu.run()