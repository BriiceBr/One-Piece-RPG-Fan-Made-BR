"""Condições do sistema novo, conforme o capítulo de Condições do livro.

As condições são as mesmas para personagens e inimigos. Cada entrada guarda:
``(ícone, nome, resumo)``. O resumo é uma versão curta do efeito, usada nos
tooltips do Combat Tracker.

Texto base: capítulo "Condições" (páginas 28 a 31 do livro novo).
"""

from __future__ import annotations

#: chave -> (ícone, nome, resumo)
CONDICOES: dict[str, tuple[str, str, str]] = {
    "agarrado": (
        "🔗",
        "Agarrado",
        "Deslocamento 0 e não pode se afastar voluntariamente da fonte.",
    ),
    "amedrontado": (
        "😨",
        "Amedrontado",
        "Desvantagem em Testes e ataques contra a fonte do medo; não se aproxima dela.",
    ),
    "atordoado": (
        "💫",
        "Atordoado",
        "Sem Reações e Deslocamento 0; ataques contra ela possuem Vantagem.",
    ),
    "caido": (
        "▼",
        "Caído",
        "Ataques corpo a corpo contra ela possuem Vantagem; os dela, Desvantagem.",
    ),
    "cego": (
        "🙈",
        "Cego",
        "Falha em Testes que dependam de visão; Desvantagem contra alvos que não percebe.",
    ),
    "congelado": (
        "🧊",
        "Congelado",
        "Deslocamento 0 e Desvantagem em Agilidade quando o gelo atrapalha.",
    ),
    "confuso": (
        "😵",
        "Confuso",
        "Desvantagem em Testes de Intelecto e Instinto.",
    ),
    "envenenado": (
        "☠️",
        "Envenenado",
        "Sofre os efeitos do veneno: dano periódico, Desvantagem ou perda de Atributo.",
    ),
    "exausto": (
        "🥵",
        "Exausto",
        "5 níveis cumulativos: Cansado, Fadigado, Exausto, Debilitado e Colapso.",
    ),
    "incapacitado": (
        "🚫",
        "Incapacitado",
        "Não pode realizar Ações, Ações Extras nem Reações.",
    ),
    "incendiado": (
        "♨",
        "Incendiado",
        "Sofre dano de fogo no início de cada um dos seus Turnos.",
    ),
    "inconsciente": (
        "💤",
        "Inconsciente",
        "Incapacitado, Caído, Deslocamento 0 e não percebe o que acontece ao redor.",
    ),
    "paralisado": (
        "🪨",
        "Paralisado",
        "Deslocamento 0, sem Reações; ataques contra ela possuem Vantagem.",
    ),
    "sangrando": (
        "🩸",
        "Sangrando",
        "Sofre dano contínuo até o ferimento ser tratado.",
    ),
    "surdo": (
        "🙉",
        "Surdo",
        "Falha em Testes de audição e não percebe sons, ordens ou avisos.",
    ),
}


def icone(chave: str) -> str:
    """Ícone curto da condição (string vazia se a chave não existir)."""
    return CONDICOES.get(chave, ("", "", ""))[0]


def nome(chave: str) -> str:
    """Nome legível da condição."""
    return CONDICOES.get(chave, ("", chave, ""))[1]


def resumo(chave: str) -> str:
    """Resumo do efeito, para tooltips."""
    return CONDICOES.get(chave, ("", "", ""))[2]
