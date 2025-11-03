class InputHandler:
    """
    Classe que vai tratar das entradas do utilizador (teclas, eventos, etc.)
    """
    def __init__(self):
        self.last_input = None

    def registar_input(self, comando):
        """Guarda o último comando recebido (temporário para testes)"""
        self.last_input = comando
        print(f"Comando recebido: {comando}")

    def obter_ultimo_input(self):
        """Devolve o último comando"""
        return self.last_input

