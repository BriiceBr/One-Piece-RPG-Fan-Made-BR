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

#: Itens exclusivos por facção, organizados pela mesma raridade do loot base.
ITENS_FACCAO: dict[str, dict[str, list[Item]]] = {
    "pirata": {
        "Comum": [("Garrafa de Rum Pirata", "consumível"), ("Moeda Saqueada", "tesouro")],
        "Incomum": [("Mapa Rasgado de Abordagem", "navegação"), ("Pistola Enferrujada", "arma")],
        "Raro": [("Log Pose de Corsário", "navegação"), ("Sabre de Abordagem Gravado", "arma")],
        "Épico": [("Pedaço de Vivre Card do Capitão", "tesouro")],
        "Lendário": [("Diário de um Capitão Lendário", "tesouro")],
    },
    "marinha": {
        "Comum": [("Uniforme da Marinha", "equipamento"), ("Algemas Regulamentares", "equipamento")],
        "Incomum": [("Den Den Mushi de Campo", "ferramenta"), ("Sinalizador de Emergência", "ferramenta")],
        "Raro": [("Pequeno Bloco de Kairoseki", "tesouro"), ("Carta de Corso Assinada", "tesouro")],
        "Épico": [("Rifle de Precisão da Marinha", "arma")],
        "Lendário": [("Carta de Recomendação de Almirante", "tesouro")],
    },
    "fera": {
        "Comum": [("Presa de Fera", "tesouro"), ("Pele Curtida de Animal", "tesouro")],
        "Incomum": [("Escamas de Peixe Gigante", "tesouro"), ("Garras Afiadas", "tesouro")],
        "Raro": [("Núcleo de Fera Marinha", "tesouro"), ("Couro Resistente de Couraça", "equipamento")],
        "Épico": [("Chifre de Rei dos Mares", "tesouro")],
        "Lendário": [("Olho de Dragão Marinho", "tesouro")],
    },
    "governo": {
        "Comum": [("Selo do Governo Mundial", "tesouro"), ("Moeda de Ouro Oficial", "tesouro")],
        "Incomum": [("Certificado de Autoridade", "tesouro"), ("Convite para Nobres", "tesouro")],
        "Raro": [("Documento Secreto do Governo", "tesouro")],
        "Épico": [("Planta de Operação Naval", "tesouro")],
        "Lendário": [("Fragmento de Poneglyph Catalogado", "tesouro")],
    },
}

#: Rótulos exibidos no cabeçalho do loot.
NOME_FACCAO: dict[str, str] = {
    "pirata": "Piratas",
    "marinha": "Marinha",
    "fera": "Feras",
    "governo": "Governo Mundial",
    "outros": "",
}

_PALAVRAS_FACCAO: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("marinha", ("marinha", "marine", "fuzileiro", "almirante", "oficial")),
    ("pirata", ("pirata", "vilões", "viloes", "bando", "corsário", "corsario", "contrabando")),
    ("fera", ("monstro", "fera", "besta", "animal", "criatura")),
    ("governo", ("governo", "mundo", "nobre", "tenryuubito", "cp")),
)


def normalizar_faccao(faccao: str | None) -> str:
    """Descobre a facção a partir do nome da pasta (ou devolve ``outros``)."""
    texto = (faccao or "").strip().lower()
    for chave, palavras in _PALAVRAS_FACCAO:
        if any(palavra in texto for palavra in palavras):
            return chave
    return "outros"


def _preferencias(dados: dict | None) -> tuple[float, float]:
    """Pesos para armas e para itens de estudo, conforme os Atributos."""
    if not dados:
        return 1.0, 1.0

    def valor(chave: str) -> int:
        try:
            return max(0, int(dados.get(chave, 0) or 0))
        except (TypeError, ValueError):
            return 0

    peso_arma = min(3.0, 1.0 + (valor("fis") + 2 * valor("luta")) / 4.0)
    peso_estudo = min(3.0, 1.0 + (valor("int") + valor("inst")) / 4.0)
    return peso_arma, peso_estudo


def chance_de_fruta(nivel: int) -> float:
    """Chance de dropar uma Akuma no Mi desconhecida (2% a 5%, Nível 12+)."""
    if nivel < 12:
        return 0.0
    return min(0.05, 0.02 + (nivel - 12) * 0.005)


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


def _candidatos(raridade: str, faccao: str) -> list[Item]:
    """Itens base da raridade + os exclusivos da facção."""
    return list(ITENS[raridade]) + list(ITENS_FACCAO.get(faccao, {}).get(raridade, []))


def _sortear_item(
    raridade: str,
    faccao: str,
    dados: dict | None,
    rng: random.Random,
    usados: set[str],
) -> Item:
    """Sorteia item da raridade, favorecendo armas ou estudo conforme a ficha."""
    pool = [item for item in _candidatos(raridade, faccao) if item[0] not in usados]
    if not pool:
        pool = _candidatos(raridade, faccao)

    peso_arma, peso_estudo = _preferencias(dados)
    pesos: list[float] = []
    for _nome, tipo in pool:
        peso = 1.0
        if tipo == "arma":
            peso *= peso_arma
        elif tipo in {"navegação", "ferramenta", "tesouro"}:
            peso *= peso_estudo
        pesos.append(peso)

    escolhido = rng.choices(pool, weights=pesos, k=1)[0]
    usados.add(escolhido[0])
    return escolhido


def gerar_loot_aleatorio(
    nivel_str: str | int,
    dados: dict | None = None,
    faccao: str | None = None,
    rng: random.Random | None = None,
) -> str:
    """Monta o texto de loot considerando Nível, ficha e facção.

    ``dados`` é o dicionário da ficha (Atributos/Graus) e ``faccao`` é o nome da
    pasta onde ela está (ex.: "Piratas", "Marinha", "Monstros"). Sem esses
    parâmetros o comportamento continua igual ao antigo.
    """
    gerador = rng if rng is not None else random
    nivel = _normalizar_nivel(nivel_str)
    faccao_normalizada = normalizar_faccao(faccao)
    berries = calcular_berries(nivel, gerador)
    quantidade = min(8, 1 + nivel // 3 + gerador.randint(0, 1))

    pesos = pesos_por_raridade(nivel)
    raridades = list(pesos)
    chances = [pesos[r] for r in raridades]

    rotulo_faccao = NOME_FACCAO.get(faccao_normalizada, "")
    cabecalho = f"🎯 Ameaça de Nível {nivel}"
    if rotulo_faccao:
        cabecalho += f" • Facção: {rotulo_faccao}"

    usados: set[str] = set()
    linhas = [
        f"💰 Berries: {berries:,} B".replace(",", "."),
        cabecalho,
    ]

    for _ in range(quantidade):
        raridade = gerador.choices(raridades, weights=chances, k=1)[0]
        nome, tipo = _sortear_item(raridade, faccao_normalizada, dados, gerador, usados)
        linhas.append(f"• [{raridade}] {nome} ({tipo})")

    if gerador.random() < chance_de_fruta(nivel):
        linhas.append("")
        linhas.append("• [Lendário] Akuma no Mi Desconhecida (fruta do diabo)")
        linhas.append("  ↳ O Mestre define o poder; nenhuma regra é aplicada automaticamente.")

    return "\n".join(linhas)
