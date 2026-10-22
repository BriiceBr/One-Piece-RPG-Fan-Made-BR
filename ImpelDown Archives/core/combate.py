"""Dificuldade do encontro no Combat Tracker."""

from __future__ import annotations

from typing import Any

#: Faixas de dificuldade: (limite de Níveis somados, rótulo, cor)
FAIXAS: tuple[tuple[int, str, str], ...] = (
    (3, "Fácil", "#6db35f"),
    (8, "Médio", "#e5b55e"),
    (15, "Difícil", "#e05353"),
)
COR_MORTAL = "#a82020"


def nivel_seguro(valor: Any) -> int:
    """Converte um Nível vindo do banco em inteiro, sem estourar em texto."""
    try:
        return max(0, int(str(valor).strip()))
    except (TypeError, ValueError):
        return 1


def calcular_dificuldade_encontro(tracker_data: list[dict], dados_banco: dict) -> tuple[str, str]:
    """Soma os Níveis das fichas no Tracker e devolve (texto, cor)."""
    if not tracker_data:
        return "Sem Inimigos", "#8b8c8f"

    soma_niveis = 0
    for item in tracker_data:
        item_id = item.get("id")
        dados = dados_banco.get(item_id, {}) if item_id else {}
        soma_niveis += nivel_seguro(dados.get("nivel", 1))

    for limite, rotulo, cor in FAIXAS:
        if soma_niveis <= limite:
            return f"{rotulo} (Nível Total: {soma_niveis})", cor
    return f"Mortal (Nível Total: {soma_niveis})", COR_MORTAL
