# src/game/core/caminhos.py
"""
Utilitario central de resolucao de caminhos.
Usado por todos os modulos que abrem ficheiros — garante que
o jogo funciona tanto em desenvolvimento como dentro de um .exe
gerado pelo PyInstaller.

Regra simples:
  - Ficheiros SÓ de leitura  (assets, mapas, sons) → caminho_recurso()
  - Ficheiros de escrita/leitura (records, saves)   → caminho_dados_utilizador()
"""
import os
import sys


def caminho_recurso(caminho_relativo: str) -> str:
    """
    Resolve o caminho absoluto de um recurso apenas de leitura.

    Em desenvolvimento: parte da raiz do projecto.
    Em .exe (PyInstaller): parte de sys._MEIPASS, onde os assets
    sao extraidos temporariamente.
    """
    if hasattr(sys, "_MEIPASS"):
        # Dentro do .exe — o PyInstaller extrai tudo para esta pasta
        base = sys._MEIPASS
    else:
        # Em desenvolvimento — sobe 3 niveis a partir deste ficheiro
        # src/game/core/caminhos.py → src/game/core → src/game → src → raiz
        base = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
    return os.path.normpath(os.path.join(base, caminho_relativo))


def caminho_dados_utilizador(nome_ficheiro: str) -> str:
    """
    Resolve o caminho de um ficheiro que o jogo precisa de ESCREVER
    (recordes, configuracoes, saves).

    Dentro de um .exe nao e possivel escrever junto ao executavel,
    por isso guardamos numa pasta do utilizador:
      Windows : %APPDATA%\\Snake\\
      Linux/Mac: ~/.snake/

    A pasta e criada automaticamente se nao existir.
    """
    if sys.platform == "win32":
        pasta_base = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")),
            "Snake"
        )
    else:
        pasta_base = os.path.join(os.path.expanduser("~"), ".snake")

    os.makedirs(pasta_base, exist_ok=True)
    return os.path.join(pasta_base, nome_ficheiro)