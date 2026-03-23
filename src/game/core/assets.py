# src/game/core/assets.py
import os
import pygame
from game.core.caminhos import caminho_recurso


class GestorAssets:
    """
    Gestor de recursos com cache e Singleton.
    Usa caminho_recurso() para localizar assets dentro do .exe.
    """
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self):
        if self._inicializado:
            return
        self._inicializado = True

        self.pasta_base   = caminho_recurso("assets")
        self.pasta_imagens = os.path.join(self.pasta_base, "images")
        self.pasta_sons    = os.path.join(self.pasta_base, "sounds")
        self.pasta_fontes  = os.path.join(self.pasta_base, "fonts")

        self._imagens = {}
        self._sons    = {}
        self._fontes  = {}

    def obter_imagem(self, nome: str, tamanho: tuple = None):
        chave = (nome, tamanho)
        if chave not in self._imagens:
            surf = pygame.image.load(
                os.path.join(self.pasta_imagens, nome)
            ).convert_alpha()
            if tamanho:
                surf = pygame.transform.scale(surf, tamanho)
            self._imagens[chave] = surf
        return self._imagens[chave]

    def obter_som(self, nome: str):
        if nome not in self._sons:
            self._sons[nome] = pygame.mixer.Sound(
                os.path.join(self.pasta_sons, nome)
            )
        return self._sons[nome]

    def obter_fonte(self, nome: str, tamanho: int):
        chave = (nome, tamanho)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.Font(
                os.path.join(self.pasta_fontes, nome), tamanho
            )
        return self._fontes[chave]

    def obter_fonte_sistema(self, nome: str, tamanho: int):
        chave = (f"sys_{nome}", tamanho)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont(nome, tamanho)
        return self._fontes[chave]

    # Aliases retrocompativeis — o resto do codigo usa os nomes em ingles
    def get_image(self, nome, tamanho=None):  return self.obter_imagem(nome, tamanho)
    def get_sound(self, nome):                return self.obter_som(nome)
    def get_font(self, nome, tamanho):        return self.obter_fonte(nome, tamanho)
    def get_sysfont(self, nome, tamanho):     return self.obter_fonte_sistema(nome, tamanho)


# Alias retrocompativel
AssetsManager = GestorAssets