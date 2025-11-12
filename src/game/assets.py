import os

class AssetsManager:
    """
    olá é o gustavo
    Classe responsável por gerir os ficheiros de recursos (imagens, sons, etc.)
    """
    def __init__(self, base_path="assets"):
        self.base_path = base_path
        self.image_path = os.path.join(base_path, "images")
        self.sound_path = os.path.join(base_path, "sounds")
        self.ensure_directories()

    def ensure_directories(self):
        """Cria as pastas de assets se ainda não existirem"""
        os.makedirs(self.image_path, exist_ok=True)
        os.makedirs(self.sound_path, exist_ok=True)

    def listar_imagens(self):
        """Lista os ficheiros de imagem dentro da pasta"""
        if os.path.exists(self.image_path):
            return os.listdir(self.image_path)
        return []

    def listar_sons(self):
        """Lista os ficheiros de som dentro da pasta"""
        if os.path.exists(self.sound_path):
            return os.listdir(self.sound_path)
        return []



