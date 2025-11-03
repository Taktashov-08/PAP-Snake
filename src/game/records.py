import os
from datetime import datetime

class RecordsManager:
    """
    Classe responsável por guardar e ler pontuações do jogo em ficheiros .txt
    """
    def __init__(self, filepath="records.txt"):
        self.filepath = filepath
        # cria o ficheiro se não existir
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as file:
                file.write("nome | modo | dificuldade | pontuacao | data\n")

    def guardar_pontuacao(self, nome, modo, dificuldade, pontuacao):
        """
        Guarda uma nova pontuação no ficheiro .txt
        """
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.filepath, "a") as file:
            file.write(f"{nome} | {modo} | {dificuldade} | {pontuacao} | {data_atual}\n")

    def ler_pontuacoes(self, modo_filtrar=None):
        """
        Lê todas as pontuações e devolve uma lista de dicionários
        """
        pontuacoes = []
        if not os.path.exists(self.filepath):
            return pontuacoes

        with open(self.filepath, "r") as file:
            linhas = file.readlines()[1:]  # ignora o cabeçalho
            for linha in linhas:
                partes = [p.strip() for p in linha.split("|")]
                if len(partes) == 5:
                    nome, modo, dificuldade, pontuacao, data = partes
                    if modo_filtrar is None or modo_filtrar == modo:
                        pontuacoes.append({
                            "nome": nome,
                            "modo": modo,
                            "dificuldade": dificuldade,
                            "pontuacao": int(pontuacao),
                            "data": data
                        })
        pontuacoes.sort(key=lambda x: x["pontuacao"], reverse=True)
        return pontuacoes

    def limpar_registos(self):
        """
        Apaga todos os registos e recria o ficheiro vazio
        """
        with open(self.filepath, "w") as file:
            file.write("nome | modo | dificuldade | pontuacao | data\n")

