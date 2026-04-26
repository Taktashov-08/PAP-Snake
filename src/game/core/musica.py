# src/game/core/musica.py
"""
Gestor de música e efeitos sonoros.

Singleton — uma única instância partilhada por todo o jogo.
Usa pygame.mixer para música (streaming) e pygame.mixer.Sound para SFX.

Mapeamento dificuldade → faixa:
  Normal       → musica/normal.ogg
  Rapido       → musica/rapido.ogg
  Muito Rapido → musica/muito_rapido.ogg
  (menu)       → musica/menu.ogg
"""

from __future__ import annotations
import os
import pygame

from game.core.caminhos import caminho_recurso
from game.core.configuracoes import Configuracoes

# Mapeamento dificuldade → nome do ficheiro (sem extensão)
_MUSICA_JOGO: dict[str, str] = {
    "Normal": "Plasticine_(Remastered)",
    "Rapido": "General_Release",
    "Muito Rapido": "Kore",
}

_FADE_TROCA_MS: int = 600  # fade-out antes de trocar de faixa (ms)


class GestorMusica:
    """Singleton que controla música de fundo e SFX."""

    _instancia: "GestorMusica | None" = None

    def __new__(cls) -> "GestorMusica":
        if cls._instancia is None:
            inst = super().__new__(cls)
            inst._inicializado = False
            cls._instancia = inst
        return cls._instancia

    def __init__(self) -> None:
        if self._inicializado:
            return

        self._inicializado = True
        self._cfg = Configuracoes()
        self._faixa_actual = ""
        self._sfx_cache: dict[str, pygame.mixer.Sound] = {}

        # Caminhos base
        self._pasta_music = caminho_recurso("assets/musica")
        self._pasta_sfx = caminho_recurso("assets/efeitos_sonoros")

        # Aplicar volume inicial
        self._aplicar_volume_musica()

    # ─────────────────────────────
    # API pública — música
    # ─────────────────────────────

    def tocar_menu(self) -> None:
        """Toca a música do menu."""
        self._tocar("Monochrome_LCD")

    def tocar_jogo(self, dificuldade: str) -> None:
        """Toca música consoante a dificuldade."""
        nome = _MUSICA_JOGO.get(dificuldade, "normal")
        self._tocar(nome)

    def fade_out(self, ms: int = 800) -> None:
        """Fade-out suave."""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(ms)

    def parar(self) -> None:
        """Para imediatamente."""
        pygame.mixer.music.stop()
        self._faixa_actual = ""

    def set_volume_musica(self, v: float) -> None:
        """Define volume da música."""
        self._cfg.musica_volume = v
        self._cfg.guardar()
        self._aplicar_volume_musica()

    def set_volume_sfx(self, v: float) -> None:
        """Define volume dos efeitos."""
        self._cfg.sfx_volume = v
        self._cfg.guardar()

        for som in self._sfx_cache.values():
            som.set_volume(v)

    def set_musica_ativa(self, ativa: bool) -> None:
        """Liga/desliga música."""
        self._cfg.musica_ativa = ativa
        self._cfg.guardar()

        if not ativa:
            self.parar()
        else:
            if self._faixa_actual:
                self._tocar_caminho(self._faixa_actual)

    # ─────────────────────────────
    # API pública — SFX
    # ─────────────────────────────

    def tocar_sfx(self, nome: str) -> None:
        """Toca um efeito sonoro."""
        if self._cfg.sfx_volume <= 0.0:
            return

        som = self._carregar_sfx(nome)
        if som:
            som.play()

    # ─────────────────────────────
    # Internos
    # ─────────────────────────────

    def _tocar(self, nome: str) -> None:
        """Toca música pelo nome."""
        caminho = os.path.join(self._pasta_music, f"{nome}.ogg")

        # DEBUG (podes remover depois)
        # print("A tentar tocar:", caminho)

        if not os.path.exists(caminho):
            print(f"[ERRO] Música não encontrada: {caminho}")
            return

        if caminho == self._faixa_actual and pygame.mixer.music.get_busy():
            return

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(_FADE_TROCA_MS)

        self._tocar_caminho(caminho)

    def _tocar_caminho(self, caminho: str) -> None:
        """Toca música por caminho absoluto."""
        if not self._cfg.musica_ativa:
            self._faixa_actual = caminho
            return

        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(self._cfg.musica_volume)
            pygame.mixer.music.play(loops=-1)
            self._faixa_actual = caminho
        except pygame.error as e:
            print(f"[ERRO pygame] {e}")

    def _aplicar_volume_musica(self) -> None:
        """Aplica volume atual."""
        try:
            volume = self._cfg.musica_volume if self._cfg.musica_ativa else 0.0
            pygame.mixer.music.set_volume(volume)
        except pygame.error:
            pass

    def _carregar_sfx(self, nome: str) -> "pygame.mixer.Sound | None":
        """Carrega e guarda em cache."""
        if nome in self._sfx_cache:
            return self._sfx_cache[nome]

        caminho = os.path.join(self._pasta_sfx, f"{nome}.ogg")

        if not os.path.exists(caminho):
            print(f"[ERRO] SFX não encontrado: {caminho}")
            return None

        try:
            som = pygame.mixer.Sound(caminho)
            som.set_volume(self._cfg.sfx_volume)
            self._sfx_cache[nome] = som
            return som
        except pygame.error as e:
            print(f"[ERRO pygame SFX] {e}")
            return None