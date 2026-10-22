"""Gerador de loot por Nível do ImpelDown Archives.

Quanto maior o Nível da ameaça, mais Berries o inimigo carrega, mais itens
aparecem e melhor é a raridade sorteada. O Nível é limitado a 20 para manter a
tabela simples, mesmo que o livro de regras não tenha limite de Nível.

Cada item é uma tupla ``(nome, tipo)``, onde o tipo é apenas descritivo
(arma, equipamento, consumível, navegação, ferramenta ou tesouro).
"""

from __future__ import annotations

import random

#: Acima deste Nível o loot para de crescer.
NIVEL_MAXIMO_LOOT: int = 20

#: (nome do item, tipo do item)
Item = tuple[str, str]

ITENS: dict[str, list[Item]] = {
    "Comum": [
        ("Rações de Viagem (3 dias)", "consumível"),
        ("Cantil de Água Doce", "equipamento"),
        ("Corda de Cânhamo (15 m)", "equipamento"),
        ("Garrafa de Rum Barato", "consumível"),
        ("Vendas e Algemas", "equipamento"),
        ("Tocha Simples", "equipamento"),
        ("Faca de Cozinha", "arma"),
        ("Porrete de Madeira", "arma"),
        ("Funda de Pedras", "arma"),
        ("Rede de Pesca Reforçada", "equipamento"),
        ("Botas de Couro Curtido", "equipamento"),
        ("Kit de Costura de Velas", "ferramenta"),
        ("Saco de Moedas Estrangeiras", "tesouro"),
        ("Pederneira e Isqueiro", "ferramenta"),
    ],
    "Incomum": [
        ("Bússola de Navegação", "navegação"),
        ("Kit de Médicos Simples", "ferramenta"),
        ("Pistola de Pederneira", "arma"),
        ("Mapa do Mar Local", "navegação"),
        ("Luneta de Latão", "ferramenta"),
        ("Sabre de Abordagem", "arma"),
        ("Machado de Marinheiro", "arma"),
        ("Colete de Couro Batido", "equipamento"),
        ("Flauta de Sinais da Marinha", "ferramenta"),
        ("Barril de Pólvora Seca", "consumível"),
        ("Algemas de Aço com Corrente", "equipamento"),
        ("Lanterna de Óleo de Baleia", "equipamento"),
    ],
    "Raro": [
        ("Log Pose Básico", "navegação"),
        ("Lâmina de Aço Dobrado", "arma"),
        ("Kit de Veneno de Serpente", "consumível"),
        ("Carta de Marque da Marinha", "tesouro"),
        ("Pedra de Amolar Especial", "ferramenta"),
        ("Pistola Dupla de Pederneira", "arma"),
        ("Katana de Oficial", "arma"),
        ("Escudo de Aço Batido", "equipamento"),
        ("Rifle de Caça Longo", "arma"),
        ("Sinete Falsificado de Nobre", "tesouro"),
        ("Relógio de Bolso de Navegador", "ferramenta"),
        ("Colete de Malha de Aço", "equipamento"),
    ],
    "Épico": [
        ("Pedaço de Vivre Card", "tesouro"),
        ("Projeto de Canhão Pesado", "tesouro"),
        ("Log Pose Triplo", "navegação"),
        ("Frasco de Essência de Pós de Tritão", "consumível"),
        ("Sabre Serrilhado do Carrasco", "arma"),
        ("Rifle de Precisão com Luneta", "arma"),
        ("Armadura de Placas Parcial", "equipamento"),
        ("Mapa de Rota Secreta do Novo Mundo", "navegação"),
        ("Baú Pequeno de Kairoseki", "tesouro"),
        ("Manual de Esgrima de um Vice-Almirante", "ferramenta"),
    ],
    "Lendário": [
        ("Pistola de Duelo de Almirante", "arma"),
        ("Lâmina de Kairoseki", "arma"),
        ("Diário de um Rei dos Piratas", "tesouro"),
        ("Log Pose do Novo Mundo", "navegação"),
        ("Fragmento de Poneglyph", "tesouro"),
        ("Carta Náutica de Ilha Fantasma", "navegação"),
        ("Moeda de Ouro de Shandora", "tesouro"),
        ("Anel de Coral de Sabaody", "tesouro"),
    ],
}


def _normalizar_nivel(nivel_str: str | int) -> int:
    """Converte o Nível recebido em um inteiro entre 1 e 20."""
    try:
        nivel = int(nivel_str)
    except (TypeError, ValueError):
        return 1
    return max(1, min(NIVEL_MAXIMO_LOOT, nivel))


def calcular_berries(nivel: int, rng: random.Random | None = None) -> int:
    """Berries carregados por uma ameaça do Nível indicado.

    Cresce mais que linearmente: Nível 1 dá algumas centenas, Nível 20 dá
    dezenas de milhares.
    """
    gerador = rng if rng is not None else random
    base = gerador.randint(90, 320)
    return int(base * (nivel ** 1.8))


def pesos_por_raridade(nivel: int) -> dict[str, float]:
    """Probabilidade relativa de cada raridade no Nível indicado."""
    passo = (nivel - 1) / (NIVEL_MAXIMO_LOOT - 1)
    return {
        "Comum": 60.0 - 55.0 * passo,
        "Incomum": 30.0 - 10.0 * passo,
        "Raro": 8.0 + 27.0 * passo,
        "Épico": 2.0 + 28.0 * passo,
        "Lendário": 10.0 * passo,
    }


def _sortear_item(raridade: str, rng: random.Random, usados: set[str]) -> Item:
    """Escolhe um item da raridade evitando repetir os já sorteados."""
    pool = [item for item in ITENS[raridade] if item[0] not in usados]
    if not pool:
        pool = ITENS[raridade]
    escolhido = rng.choice(pool)
    usados.add(escolhido[0])
    return escolhido


def gerar_loot_aleatorio(nivel_str: str | int, rng: random.Random | None = None) -> str:
    """Monta o texto de loot (Berries + itens) para uma ameaça."""
    gerador = rng if rng is not None else random
    nivel = _normalizar_nivel(nivel_str)
    berries = calcular_berries(nivel, gerador)
    quantidade = min(7, 1 + nivel // 3 + gerador.randint(0, 1))

    pesos = pesos_por_raridade(nivel)
    raridades = list(pesos)
    chances = [pesos[r] for r in raridades]

    usados: set[str] = set()
    linhas = [
        f"💰 Berries: {berries:,} B".replace(",", "."),
        f"🎯 Ameaça de Nível {nivel}",
    ]

    for _ in range(quantidade):
        raridade = gerador.choices(raridades, weights=chances, k=1)[0]
        nome, tipo = _sortear_item(raridade, gerador, usados)
        linhas.append(f"• [{raridade}] {nome} ({tipo})")

    return "\n".join(linhas)
