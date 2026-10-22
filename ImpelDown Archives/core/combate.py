"""Dificuldade do encontro no Combat Tracker.

A conta agora é relativa ao grupo: compara o "poder" dos inimigos com o poder
da party (jogadores × nível médio) e classifica por porcentagem. Também aplica
um multiplicador de horda quando há mais inimigos do que jogadores.
"""

from __future__ import annotations

from typing import Any

from core.paleta import (
    DIFICULDADE_DIFICIL,
    DIFICULDADE_FACIL,
    DIFICULDADE_MEDIA,
    DIFICULDADE_MORTAL,
    DIFICULDADE_SEM_INIMIGOS,
)

#: (limite superior da razão, rótulo, cor)
FAIXAS: tuple[tuple[float, str, str], ...] = (
    (0.60, "Fácil", DIFICULDADE_FACIL),
    (1.00, "Médio", DIFICULDADE_MEDIA),
    (1.40, "Difícil", DIFICULDADE_DIFICIL),
)
COR_MORTAL = DIFICULDADE_MORTAL
COR_SEM_INIMIGOS = DIFICULDADE_SEM_INIMIGOS

#: Acréscimo de poder por inimigo acima do número de jogadores.
BONUS_HORDA = 0.15
#: Teto do multiplicador de horda.
HORDA_MAXIMA = 2.0


def nivel_seguro(valor: Any) -> int:
    """Converte um Nível vindo do banco em inteiro, sem estourar em texto."""
    try:
        return max(0, int(str(valor).strip()))
    except (TypeError, ValueError):
        return 1


def poder_do_grupo(jogadores: int, nivel_medio: int) -> int:
    """Poder Total da Party = Número de Jogadores × Nível Médio."""
    try:
        jogadores = max(1, int(str(jogadores).strip()))
    except (TypeError, ValueError):
        jogadores = 4
    try:
        nivel_medio = max(1, int(str(nivel_medio).strip()))
    except (TypeError, ValueError):
        nivel_medio = 1
    return jogadores * nivel_medio


def multiplicador_horda(inimigos: int, jogadores: int) -> float:
    """Cresce quando os inimigos passam do número de jogadores (máx. 2.0)."""
    try:
        jogadores = max(1, int(str(jogadores).strip()))
    except (TypeError, ValueError):
        jogadores = 4
    try:
        inimigos = max(0, int(str(inimigos).strip()))
    except (TypeError, ValueError):
        inimigos = 0
    excedente = max(0, inimigos - jogadores)
    return min(HORDA_MAXIMA, 1.0 + BONUS_HORDA * excedente)


def poder_dos_inimigos(tracker_data: list[dict], dados_banco: dict[str, Any],
                       jogadores: int = 4) -> float:
    """Soma dos Níveis dos inimigos, ajustada pelo multiplicador de horda.

    Inimigos "de verdade" repetidos (mesma ficha adicionada duas vezes) contam
    uma vez só; lacaios genéricos (id "bando"/"chefe") continuam contando cada
    linha, porque são criaturas diferentes.
    """
    soma = 0
    vistos: set[str] = set()
    for item in tracker_data:
        item_id = item.get("id")
        dados = dados_banco.get(item_id, {}) if item_id else {}
        if item_id and item_id in dados_banco:
            if item_id in vistos:
                continue
            vistos.add(item_id)
        soma += nivel_seguro(dados.get("nivel", 1))
    return soma * multiplicador_horda(len(tracker_data), jogadores)


def classificar(razao: float) -> tuple[str, str]:
    """Rótulo e cor para a razão poder-inimigos / poder-do-grupo."""
    for limite, rotulo, cor in FAIXAS:
        if razao <= limite:
            return rotulo, cor
    return "Mortal", COR_MORTAL


def calcular_dificuldade_encontro(
    tracker_data: list[dict],
    dados_banco: dict[str, Any],
    jogadores: int = 4,
    nivel_medio: int = 1,
) -> tuple[str, str]:
    """Devolve (texto, cor) da dificuldade relativa ao grupo."""
    if not tracker_data:
        return "Sem Inimigos", COR_SEM_INIMIGOS

    try:
        jogadores = max(1, int(str(jogadores).strip()))
    except (TypeError, ValueError):
        jogadores = 4
    try:
        nivel_medio = max(1, int(str(nivel_medio).strip()))
    except (TypeError, ValueError):
        nivel_medio = 1

    poder_inimigos = poder_dos_inimigos(tracker_data, dados_banco, jogadores)
    poder_grupo = poder_do_grupo(jogadores, nivel_medio)
    razao = poder_inimigos / poder_grupo
    rotulo, cor = classificar(razao)

    fator = multiplicador_horda(len(tracker_data), jogadores)
    detalhe_horda = f" ×{fator:.2f} horda" if fator > 1.0 else ""
    texto = (
        f"{rotulo} — Inimigos {poder_inimigos:.0f}{detalhe_horda} "
        f"vs Grupo {poder_grupo} ({razao:.0%})"
    )
    return texto, cor
