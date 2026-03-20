# src/game/core/assets.py
import os
import sys
import pygame


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(base, relative_path)


class AssetsManager:
    """Gestor de recursos com cache e Singleton."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.base_path  = resource_path("assets")
        self.image_path = os.path.join(self.base_path, "images")
        self.sound_path = os.path.join(self.base_path, "sounds")
        self.font_path  = os.path.join(self.base_path, "fonts")
        self._images = {}
        self._sounds = {}
        self._fonts  = {}

    def get_image(self, nome, tamanho=None):
        chave = (nome, tamanho)
        if chave not in self._images:
            surf = pygame.image.load(os.path.join(self.image_path, nome)).convert_alpha()
            if tamanho:
                surf = pygame.transform.scale(surf, tamanho)
            self._images[chave] = surf
        return self._images[chave]

    def get_sound(self, nome):
        if nome not in self._sounds:
            self._sounds[nome] = pygame.mixer.Sound(os.path.join(self.sound_path, nome))
        return self._sounds[nome]

    def get_font(self, nome, tamanho):
        chave = (nome, tamanho)
        if chave not in self._fonts:
            self._fonts[chave] = pygame.font.Font(os.path.join(self.font_path, nome), tamanho)
        return self._fonts[chave]

    def get_sysfont(self, nome, tamanho):
        chave = (f"sys_{nome}", tamanho)
        if chave not in self._fonts:
            self._fonts[chave] = pygame.font.SysFont(nome, tamanho)
        return self._fonts[chave]
