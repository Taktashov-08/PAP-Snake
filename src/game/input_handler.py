# Descrição: Trata da abstração dos inputs do utilizador.
# Permite separar a deteção física da tecla (Pygame) da intenção lógica do jogador.
# src/game/input_handler.py

class InputHandler:
    """
    Classe responsável por gerir as entradas do utilizador (teclas, eventos, etc.).
    Funciona como uma ponte entre o hardware e a lógica do jogo.
    """
    def __init__(self):
        # Armazena o comando mais recente para ser consultado pela Engine
        self.last_input = None

    def registar_input(self, comando):
        """
        Guarda o último comando recebido e imprime no terminal para testes.
        
        Args:
            comando (str): O nome do comando ou tecla premida.
        """
        self.last_input = comando
        # Útil durante o desenvolvimento para verificar se as teclas estão a responder
        print(f"Comando recebido: {comando}")

    def obter_ultimo_input(self):
        """
        Devolve o último comando guardado.
        
        Returns:
            str: O último input registado.
        """
        return self.last_input