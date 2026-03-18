# Descrição: Gestor central de recursos (Assets) com suporte a Singleton e Cache.
import os
import sys
import pygame

def resource_path(relative_path):
    """Resolve caminhos de ficheiros para compatibilidade entre ambiente de dev e PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS  
    else:
        # Define a raiz do projeto subindo dois níveis a partir do diretório atual
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base, relative_path)


class AssetsManager:
    """Gere o carregamento e cache de imagens, sons e fontes para otimizar o desempenho."""
    _instance = None  # Implementação do padrão Singleton

    def __new__(cls):
        """Garante que apenas uma instância do gestor exista durante a execução."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inicializa os mapeamentos de diretórios e estruturas de cache (Dicionários)."""
        if self._initialized:
            return
        self._initialized = True

        self.base_path   = resource_path("assets")
        self.image_path  = os.path.join(self.base_path, "images")
        self.sound_path  = os.path.join(self.base_path, "sounds")
        self.font_path   = os.path.join(self.base_path, "fonts")

        self._images = {}
        self._sounds = {}
        self._fonts  = {}

    def get_image(self, nome, tamanho=None):
        """Carrega, converte para performance e armazena imagens em cache com redimensionamento opcional."""
        chave = (nome, tamanho)
        if chave not in self._images:
            path = os.path.join(self.image_path, nome)
            # convert_alpha() otimiza o rendering da Surface no Pygame
            surf = pygame.image.load(path).convert_alpha()
            if tamanho:
                surf = pygame.transform.scale(surf, tamanho)
            self._images[chave] = surf
        return self._images[chave]

    def get_sound(self, nome):
        """Carrega e armazena efeitos sonoros em cache para evitar acessos repetidos ao disco."""
        if nome not in self._sounds:
            path = os.path.join(self.sound_path, nome)
            self._sounds[nome] = pygame.mixer.Sound(path)
        return self._sounds[nome]

    def get_font(self, nome, tamanho):
        """Carrega fontes TrueType (TTF) personalizadas a partir do diretório de assets."""
        chave = (nome, tamanho)
        if chave not in self._fonts:
            path = os.path.join(self.font_path, nome)
            self._fonts[chave] = pygame.font.Font(path, tamanho)
        return self._fonts[chave]

    def get_sysfont(self, nome, tamanho):
        """Carrega fontes padrão do sistema operativo como fallback (recurso de contingência)."""
        chave = (f"sys_{nome}", tamanho)
        if chave not in self._fonts:
            self._fonts[chave] = pygame.font.SysFont(nome, tamanho)
        return self._fonts[chave]