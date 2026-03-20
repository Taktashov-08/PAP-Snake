# src/game/core/records.py
import os
from datetime import datetime


class RecordsManager:
    """Guarda e le pontuacoes em ficheiro .txt."""

    def __init__(self, filepath="records.txt"):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                f.write("\tnome\t|\tmodo\t|\tdificuldade\t|\tpontuacao\t|\tdata\t\n")

    def guardar_pontuacao(self, nome, modo, dificuldade, pontuacao):
        data = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.filepath, "a") as f:
            f.write(f"\t{nome}\t|\t{modo}\t|\t{dificuldade}\t|\t{pontuacao}\t|\t{data}\t\n")

    def ler_pontuacoes(self, modo_filtrar=None):
        pontuacoes = []
        if not os.path.exists(self.filepath):
            return pontuacoes
        with open(self.filepath, "r") as f:
            for linha in f.readlines()[1:]:
                partes = [p.strip() for p in linha.split("|")]
                if len(partes) == 5:
                    nome, modo, dificuldade, pontuacao, data = partes
                    if modo_filtrar is None or modo_filtrar == modo:
                        pontuacoes.append({
                            "nome": nome, "modo": modo,
                            "dificuldade": dificuldade,
                            "pontuacao": int(pontuacao), "data": data
                        })
        pontuacoes.sort(key=lambda x: x["pontuacao"], reverse=True)
        return pontuacoes

    def limpar_registos(self):
        with open(self.filepath, "w") as f:
            f.write("\tnome\t|\tmodo\t|\tdificuldade\t|\tpontuacao\t|\tdata\t\n")
