"""Soundboard leve do ImpelDown Archives.

Toca arquivos da pasta ``sons/`` do projeto. Se o arquivo não existir (ou se o
sistema não for Windows), a chamada simplesmente não faz nada — a mesa nunca
quebra por falta de áudio.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    import winsound
except ImportError:  # pragma: no cover - Linux/macOS
    winsound = None  # type: ignore[assignment]

PASTA_PADRAO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sons"
)

#: (chave, rótulo do botão, nomes de arquivo aceitos)
SLOTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("canhao", "💥 Canhão", ("canhao.wav", "cannon.wav")),
    ("navio", "⚓ Navio", ("navio.wav", "ship.wav")),
    ("impacto", "🛡️ Impacto", ("impacto.wav", "hit.wav")),
    ("haki", "🌪️ Haki", ("haki.wav", "aura.wav")),
)


@dataclass
class Soundboard:
    """Controla os efeitos sonoros e o botão de mudo."""

    pasta: str = PASTA_PADRAO
    mudo: bool = False
    _cache: dict[str, str | None] = field(default_factory=dict, repr=False)

    def caminho(self, chave: str) -> str | None:
        """Caminho do arquivo do slot, ou ``None`` se não houver arquivo."""
        if chave in self._cache:
            return self._cache[chave]
        caminho: str | None = None
        for slot_chave, _, arquivos in SLOTS:
            if slot_chave != chave:
                continue
            for nome in arquivos:
                possivel = os.path.join(self.pasta, nome)
                if os.path.exists(possivel):
                    caminho = possivel
                    break
            break
        self._cache[chave] = caminho
        return caminho

    def tocar(self, chave: str) -> bool:
        """Toca o efeito; devolve ``True`` se algum som realmente tocou."""
        if self.mudo or winsound is None:
            return False
        caminho = self.caminho(chave)
        if not caminho:
            return False
        try:
            winsound.PlaySound(caminho, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except RuntimeError:
            return False

    def alternar_mudo(self) -> bool:
        self.mudo = not self.mudo
        return self.mudo
