# src/game/core/nomes.py
from game.core.caminhos import caminho_dados_utilizador

_FICHEIRO = "nomes.txt"
_MAX      = 20


class GestorNomes:
    """Persiste nomes de jogadores para reutilização entre sessões."""

    def __init__(self, ficheiro=_FICHEIRO):
        # Usa caminho_dados_utilizador para funcionar correctamente dentro do .exe
        self.ficheiro = caminho_dados_utilizador(ficheiro)

    def carregar(self):
        """Devolve lista de nomes (mais recente primeiro)."""
        try:
            with open(self.ficheiro, "r", encoding="utf-8") as f:
                return [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            return []

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