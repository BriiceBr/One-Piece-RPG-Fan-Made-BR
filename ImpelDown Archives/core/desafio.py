"""Desafio de combate por dano médio da party (One Piece RPG).

Modelo pedido pelo Mestre:
* dano por jogador conforme o patamar do Nível (12/20/32/60);
* dano da party = dano por jogador × jogadores;
* rodadas = HP total dos inimigos ÷ dano da party;
* classificação pelo número inteiro de rodadas:
  1–2 Muito Fácil, 3–4 Desafiador, 5+ Mortal.
"""

from __future__ import annotations

import math

from core.paleta import DIFICULDADE_DIFICIL, DIFICULDADE_FACIL, DIFICULDADE_MEDIA

#: (nível máximo da faixa, dano por jogador/rodada, patamar)
FAIXAS: tuple[tuple[int, int, str], ...] = (
    (3, 12, "Básica"),
    (7, 20, "Média"),
    (11, 32, "Forte"),
    (10**9, 60, "Suprema"),
)

MUITO_FACIL = "Muito Fácil"
DESAFIADOR = "Desafiador"
MORTAL = "Mortal"


def dano_por_jogador(nivel: int) -> tuple[int, str]:
    """Dano médio esperado por jogador/rodada e o patamar correspondente."""
    try:
        nivel = max(1, int(str(nivel).strip()))
    except (TypeError, ValueError):
        nivel = 1
    for limite, dano, patamar in FAIXAS:
        if nivel <= limite:
            return dano, patamar
    return 60, "Suprema"


def classificar(rodadas: int) -> tuple[str, str]:
    """Rótulo e cor para o número inteiro de rodadas."""
    if rodadas <= 2:
        return MUITO_FACIL, DIFICULDADE_FACIL
    if rodadas <= 4:
        return DESAFIADOR, DIFICULDADE_MEDIA
    return MORTAL, DIFICULDADE_DIFICIL


def analisar(jogadores: int, nivel_medio: int, hp_total: int) -> dict:
    """Calcula rodadas, classificação, texto e sugestões de ajuste."""
    jogadores = max(1, int(jogadores))
    hp_total = max(0, int(hp_total))
    dano_jogador, patamar = dano_por_jogador(nivel_medio)
    dano_party = dano_jogador * jogadores

    if hp_total <= 0:
        return {
            "patamar": patamar,
            "dano_jogador": dano_jogador,
            "dano_party": dano_party,
            "hp_total": 0,
            "rodadas": 0.0,
            "rodadas_inteiras": 0,
            "rotulo": "Sem HP",
            "cor": "#8b8c8f",
            "resumo": "Sem HP informado nos inimigos.",
            "sugestoes": [],
        }

    rodadas = hp_total / dano_party
    rodadas_inteiras = max(1, math.ceil(rodadas))
    rotulo, cor = classificar(rodadas_inteiras)

    sugestoes: list[str] = []
    if rodadas_inteiras <= 2:
        sugestoes.append(
            f"Rápido: para 3 rodadas são ~{dano_party * 3} de HP total "
            f"(+{dano_party * 3 - hp_total})."
        )
    elif rodadas_inteiras >= 5:
        sugestoes.append(
            f"Letal: para 4 rodadas são ~{dano_party * 4} de HP total "
            f"(-{hp_total - dano_party * 4})."
        )
    else:
        sugestoes.append("Faixa desejada (3–4 rodadas).")

    return {
        "patamar": patamar,
        "dano_jogador": dano_jogador,
        "dano_party": dano_party,
        "hp_total": hp_total,
        "rodadas": rodadas,
        "rodadas_inteiras": rodadas_inteiras,
        "rotulo": rotulo,
        "cor": cor,
        "resumo": f"{rotulo} — {rodadas_inteiras} rodada(s) ({hp_total} HP ÷ {dano_party}/rodada)",
        "sugestoes": sugestoes,
    }
