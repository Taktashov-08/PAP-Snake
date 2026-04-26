# src/game/core/configuracoes.py
"""
Configurações persistentes do utilizador.

Guarda e lê um ficheiro JSON com as preferências de áudio.
Singleton — uma única instância partilhada por todo o jogo.

Uso::

    from game.core.configuracoes import Configuracoes
    cfg_user = Configuracoes()
    cfg_user.musica_volume   # float 0.0–1.0
    cfg_user.sfx_volume      # float 0.0–1.0
    cfg_user.musica_ativa    # bool
    cfg_user.guardar()       # persiste para o ficheiro JSON
"""
from __future__ import annotations

import json
import os

from game.core.caminhos import caminho_dados_utilizador

_FICHEIRO = "config_user.json"

# Valores por omissão
_DEFAULTS = {
    "musica_volume": 0.65,
    "sfx_volume":    1.0,
    "musica_ativa":  True,
}


class Configuracoes:
    """Singleton de configurações do utilizador."""

    _instancia: "Configuracoes | None" = None

    def __new__(cls) -> "Configuracoes":
        if cls._instancia is None:
            inst = super().__new__(cls)
            inst._inicializado = False
            cls._instancia = inst
        return cls._instancia

    def __init__(self) -> None:
        if self._inicializado:
            return
        self._inicializado = True
        self._caminho = caminho_dados_utilizador(_FICHEIRO)
        self._dados: dict = dict(_DEFAULTS)
        self._carregar()

    # ── Propriedades ──────────────────────────────────────────────────────────

    @property
    def musica_volume(self) -> float:
        return float(self._dados.get("musica_volume", _DEFAULTS["musica_volume"]))

    @musica_volume.setter
    def musica_volume(self, v: float) -> None:
        self._dados["musica_volume"] = max(0.0, min(1.0, float(v)))

    @property
    def sfx_volume(self) -> float:
        return float(self._dados.get("sfx_volume", _DEFAULTS["sfx_volume"]))

    @sfx_volume.setter
    def sfx_volume(self, v: float) -> None:
        self._dados["sfx_volume"] = max(0.0, min(1.0, float(v)))

    @property
    def musica_ativa(self) -> bool:
        return bool(self._dados.get("musica_ativa", _DEFAULTS["musica_ativa"]))

    @musica_ativa.setter
    def musica_ativa(self, v: bool) -> None:
        self._dados["musica_ativa"] = bool(v)

    # ── Persistência ──────────────────────────────────────────────────────────

    def guardar(self) -> None:
        """Escreve as configurações actuais no ficheiro JSON."""
        try:
            with open(self._caminho, "w", encoding="utf-8") as f:
                json.dump(self._dados, f, indent=2, ensure_ascii=False)
        except OSError:
            pass   # falha silenciosa — não crítico

    def _carregar(self) -> None:
        """Lê o ficheiro JSON; usa defaults para chaves em falta ou ficheiro ausente."""
        if not os.path.exists(self._caminho):
            return
        try:
            with open(self._caminho, "r", encoding="utf-8") as f:
                lido = json.load(f)
            # Aplica apenas chaves conhecidas — ignora lixo
            for chave, default in _DEFAULTS.items():
                if chave in lido:
                    self._dados[chave] = type(default)(lido[chave])
        except (OSError, json.JSONDecodeError, ValueError):
            pass   # ficheiro corrompido → manter defaults

    def resetar(self) -> None:
        """Repõe todos os valores para os defaults e guarda."""
        self._dados = dict(_DEFAULTS)
        self.guardar()