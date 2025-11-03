class Snake:
    """
    Classe que representa a cobra do jogo.
    Contém a posição do corpo, direção e métodos de movimento.
    """
    def __init__(self, pos_inicial=(100, 100), tamanho_bloco=20):
        self.tamanho_bloco = tamanho_bloco
        self.corpo = [pos_inicial]
        self.direcao = "RIGHT"  # Direção inicial
        self.crescer = False

    def mover(self):
        """Move a cobra na direção atual"""
        x, y = self.corpo[0]

        if self.direcao == "UP":
            y -= self.tamanho_bloco
        elif self.direcao == "DOWN":
            y += self.tamanho_bloco
        elif self.direcao == "LEFT":
            x -= self.tamanho_bloco
        elif self.direcao == "RIGHT":
            x += self.tamanho_bloco

        nova_cabeca = (x, y)
        self.corpo.insert(0, nova_cabeca)

        if not self.crescer:
            self.corpo.pop()
        else:
            self.crescer = False  # consome o sinal de crescimento

    def mudar_direcao(self, nova_direcao):
        """Muda a direção da cobra, evitando movimentos opostos imediatos"""
        direcoes_opostas = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if nova_direcao != direcoes_opostas.get(self.direcao):
            self.direcao = nova_direcao

    def aumentar(self):
        """Sinaliza para aumentar o corpo na próxima atualização"""
        self.crescer = True

    def colisao_corpo(self):
        """Verifica se a cabeça colidiu com o corpo"""
        return self.corpo[0] in self.corpo[1:]

    def obter_cabeca(self):
        """Devolve as coordenadas da cabeça"""
        return self.corpo[0]

    def __str__(self):
        """Representação textual (para testes sem pygame)"""
        return "Cobra: " + " -> ".join(str(pos) for pos in self.corpo)

