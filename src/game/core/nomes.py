# src/game/core/nomes.py
import os

_FICHEIRO = "nomes.txt"
_MAX      = 20   # máximo de nomes guardados


class GestorNomes:
    """Persiste nomes de jogadores para reutilização entre sessões."""

    def __init__(self, ficheiro=_FICHEIRO):
        self.ficheiro = ficheiro

    def carregar(self):
        """Devolve lista de nomes (mais recente primeiro)."""
        if not os.path.exists(self.ficheiro):
            return []
        with open(self.ficheiro, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]

    def guardar(self, nome):
        """Guarda nome, movendo-o para o topo se já existir."""
        nomes = self.carregar()
        if nome in nomes:
            nomes.remove(nome)
        nomes.insert(0, nome)
        nomes = nomes[:_MAX]
        with open(self.ficheiro, "w", encoding="utf-8") as f:
            for n in nomes:
                f.write(n + "\n")