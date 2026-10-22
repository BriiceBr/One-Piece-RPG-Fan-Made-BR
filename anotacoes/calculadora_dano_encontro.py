"""Calculadora de desafio por dano da party — One Piece RPG.

Recebe jogadores, nível, quantidade de inimigos e HP médio e responde:
* dano total da party por rodada;
* HP total dos inimigos;
* rodadas médias para zerar o HP;
* classificação (1-2 Muito Fácil, 3-4 Desafiador, 5+ Mortal);
* ajustes de HP ou de número de lacaios para cair na faixa desejada.

Uso:
    py anotacoes/calculadora_dano_encontro.py --jogadores 4 --nivel 5 --inimigos 4 --hp 40
    py anotacoes/calculadora_dano_encontro.py --exemplos
"""

from __future__ import annotations

import argparse
import math

#: (nível máximo da faixa, dano médio por jogador/rodada, patamar)
FAIXAS: tuple[tuple[int, int, str], ...] = (
    (3, 12, "Básica"),
    (7, 20, "Média"),
    (11, 32, "Forte"),
    (10**9, 60, "Suprema"),
)


def dano_por_jogador(nivel: int) -> tuple[int, str]:
    """Dano médio esperado por jogador/rodada e o patamar correspondente."""
    for limite, dano, patamar in FAIXAS:
        if nivel <= limite:
            return dano, patamar
    return 60, "Suprema"


def classificar(rodadas: float) -> str:
    if rodadas <= 2:
        return "Muito Fácil"
    if rodadas <= 4:
        return "Desafiador"
    return "Mortal"


def analisar(jogadores: int, nivel: int, inimigos: int, hp_medio: int) -> dict:
    """Calcula o encontro e devolve números, classificação e sugestões."""
    if min(jogadores, nivel, inimigos, hp_medio) <= 0:
        raise ValueError("Todos os valores precisam ser maiores que zero.")

    dano_jogador, patamar = dano_por_jogador(nivel)
    dano_party = dano_jogador * jogadores
    hp_total = inimigos * hp_medio
    rodadas = hp_total / dano_party
    rodadas_inteiras = max(1, math.ceil(rodadas))
    classe = classificar(rodadas_inteiras)

    sugestoes: list[str] = []
    if rodadas_inteiras < 3:
        hp_alvo = math.ceil(dano_party * 3 / inimigos)
        inimigos_alvo = math.ceil(dano_party * 3 / hp_medio)
        sugestoes.append(
            f"Combate rápido demais: para chegar a 3 rodadas, suba o HP médio para {hp_alvo} "
            f"ou use {inimigos_alvo} inimigos (hoje {inimigos})."
        )
    elif rodadas_inteiras > 4:
        hp_alvo = max(1, math.floor(dano_party * 4 / inimigos))
        inimigos_alvo = max(1, math.floor(dano_party * 4 / hp_medio))
        sugestoes.append(
            f"Combate letal: para cair para 4 rodadas, reduza o HP médio para {hp_alvo} "
            f"ou use {inimigos_alvo} inimigos."
        )
    else:
        sugestoes.append("Faixa desejada: o encontro está entre 3 e 4 rodadas.")
        if rodadas < 3.5:
            sugestoes.append("Se quiser mais tensão, +1 lacaio ou +10% de HP.")
        else:
            sugestoes.append("Se estiver pesado, -1 lacaio ou -10% de HP.")

    return {
        "dano_jogador": dano_jogador,
        "patamar": patamar,
        "dano_party": dano_party,
        "hp_total": hp_total,
        "rodadas": rodadas,
        "rodadas_inteiras": rodadas_inteiras,
        "classificacao": classe,
        "sugestoes": sugestoes,
    }


def resumo(dados: dict) -> str:
    return (
        f"Dano por jogador ({dados['patamar']}): {dados['dano_jogador']}\n"
        f"Dano total da party/rodada: {dados['dano_party']}\n"
        f"HP total dos inimigos: {dados['hp_total']}\n"
        f"Rodadas médias: {dados['rodadas']:.1f} (arredonda para {dados['rodadas_inteiras']})\n"
        f"Classificação: {dados['classificacao']}\n"
        + "\n".join(f"• {s}" for s in dados["sugestoes"])
    )


EXEMPLOS = [
    ("Party 4×Nv 2 contra 3 lacaios de 20 HP", 4, 2, 3, 20),
    ("Party 4×Nv 5 contra 4 inimigos de 40 HP", 4, 5, 4, 40),
    ("Party 4×Nv 10 contra 6 inimigos de 80 HP", 4, 10, 6, 80),
    ("Party 4×Nv 15 contra 3 chefes de 200 HP", 4, 15, 3, 200),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculadora de desafio por dano da party")
    parser.add_argument("--jogadores", type=int)
    parser.add_argument("--nivel", type=int)
    parser.add_argument("--inimigos", type=int)
    parser.add_argument("--hp", type=int, dest="hp_medio")
    parser.add_argument("--exemplos", action="store_true")
    args = parser.parse_args()

    if args.exemplos or not all((args.jogadores, args.nivel, args.inimigos, args.hp_medio)):
        for titulo, jogadores, nivel, inimigos, hp in EXEMPLOS:
            dados = analisar(jogadores, nivel, inimigos, hp)
            print(f"=== {titulo} ===")
            print(resumo(dados))
            print()
        return

    dados = analisar(args.jogadores, args.nivel, args.inimigos, args.hp_medio)
    print(resumo(dados))


if __name__ == "__main__":
    main()
