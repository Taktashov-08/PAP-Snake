# src/game/core/records.py
import os
from datetime import datetime
from game.core.caminhos import caminho_dados_utilizador


class GestorRecordes:
    """
    Guarda e le pontuacoes num ficheiro .txt na pasta do utilizador.
    Funciona tanto em desenvolvimento como dentro de um .exe.
    """

    def __init__(self, nome_ficheiro: str = "records.txt"):
        # Sempre na pasta do utilizador — nunca junto ao .exe
        self.caminho = caminho_dados_utilizador(nome_ficheiro)

        if not os.path.exists(self.caminho):
            with open(self.caminho, "w", encoding="utf-8") as f:
                f.write("\tnome\t|\tmodo\t|\tdificuldade\t|\tpontuacao\t|\tdata\t\n")

    def guardar_pontuacao(self, nome: str, modo: str, dificuldade: str, pontuacao: int):
        data = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.caminho, "a", encoding="utf-8") as f:
            f.write(f"\t{nome}\t|\t{modo}\t|\t{dificuldade}\t|\t{pontuacao}\t|\t{data}\t\n")

    def ler_pontuacoes(self, filtro_modo: str = None) -> list:
        pontuacoes = []
        if not os.path.exists(self.caminho):
            return pontuacoes

        with open(self.caminho, "r", encoding="utf-8") as f:
            for linha in f.readlines()[1:]:
                partes = [p.strip() for p in linha.split("|")]
                if len(partes) == 5:
                    nome, modo, dificuldade, pontuacao, data = partes
                    if filtro_modo is None or filtro_modo == modo:
                        pontuacoes.append({
                            "nome":        nome,
                            "modo":        modo,
                            "dificuldade": dificuldade,
                            "pontuacao":   int(pontuacao),
                            "data":        data,
                        })

        pontuacoes.sort(key=lambda x: x["pontuacao"], reverse=True)
        return pontuacoes

    def limpar_registos(self):
        with open(self.caminho, "w", encoding="utf-8") as f:
            f.write("\tnome\t|\tmodo\t|\tdificuldade\t|\tpontuacao\t|\tdata\t\n")


# Alias retrocompativel — o resto do codigo usa RecordsManager
RecordsManager = GestorRecordes