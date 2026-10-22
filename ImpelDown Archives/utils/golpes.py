"""Gerador de golpes por patamar, alinhado ao modelo de PE do livro.

Os números vêm de ``anotacoes/regras_pe_transmutacao.md`` (decisão registrada
pelo autor):

* Básica   — 0 PE base, até +2 PE extra, nível 1
* Média    — 1 PE base, até +3 PE extra, nível 4
* Forte    — 3 PE base, até +4 PE extra, nível 8
* Suprema  — 5 PE base, até +5 PE extra, nível 12

O dano típico por patamar também é o daquele documento (2, 4 e 6 dados). O
gerador monta o **esqueleto** do golpe com sabor narrativo; nenhuma regra nova é
inventada, e o Mestre continua livre para ajustar o texto.
"""

from __future__ import annotations

import random

PATAMARES: dict[str, dict[str, object]] = {
    "Básica": {
        "custo": "0 PE",
        "limite": "+2 PE",
        "total": "2 PE",
        "nivel": 1,
        "dano": "1 dado de dano (arma ou desarmado) + Atributo",
    },
    "Média": {
        "custo": "1 PE",
        "limite": "+3 PE",
        "total": "4 PE",
        "nivel": 4,
        "dano": "2 dados de dano + Atributo",
    },
    "Forte": {
        "custo": "3 PE",
        "limite": "+4 PE",
        "total": "7 PE",
        "nivel": 8,
        "dano": "4 dados de dano + Atributo",
    },
    "Suprema": {
        "custo": "5 PE",
        "limite": "+5 PE",
        "total": "10 PE",
        "nivel": 12,
        "dano": "6 dados de dano + Atributo",
    },
}

CATEGORIAS: dict[str, dict[str, object]] = {
    "Impacto": {
        "titulos": ["Punho {x}", "Quebra-{x}", "Golpe do {x}", "Ondada de {x}"],
        "efeito": "concentra o corpo em um único impacto curto, feito para abrir guarda",
    },
    "Corte": {
        "titulos": ["Lâmina do {x}", "Corte {x}", "Fio de {x}", "Traço do {x}"],
        "efeito": "desenha um arco de corte que busca a brecha entre armadura e movimento",
    },
    "Área": {
        "titulos": ["Fúria do {x}", "Maré de {x}", "Explosão do {x}", "Vendaval do {x}"],
        "efeito": "espalha o efeito por uma área, alcançando quem estiver perto",
    },
    "Mobilidade": {
        "titulos": ["Passo do {x}", "Salto do {x}", "Corrida do {x}", "Sombra do {x}"],
        "efeito": "usa o terreno para reposicionar antes que o inimigo consiga reagir",
    },
    "Defesa": {
        "titulos": ["Guarda do {x}", "Muralha de {x}", "Escudo do {x}", "Postura do {x}"],
        "efeito": "fecha a guarda e absorve o impacto, comprando tempo para o próximo turno",
    },
}

SABORES: dict[str, dict[str, object]] = {
    "Técnica marcial": {
        "palavras": ["Ferro", "Trovão", "Dragão", "Lua", "Maré", "Osso"],
        "texto": "{nome} respira fundo, planta os pés e executa o movimento até o fim, sem hesitar.",
    },
    "Arma": {
        "palavras": ["Aço", "Gume", "Sangue", "Sombra", "Coral", "Tempestade"],
        "texto": "{nome} gira a arma uma vez e a conduz com o peso do corpo, não só com o braço.",
    },
    "Haki": {
        "palavras": ["Vontade", "Rei", "Armadura", "Presságio", "Silêncio", "Aço Negro"],
        "texto": "{nome} concentra a vontade e deixa o Haki transbordar pelo corpo antes do golpe.",
    },
    "Akuma no Mi": {
        "palavras": ["Chama", "Gelo", "Areia", "Raio", "Sombra", "Vento"],
        "texto": "{nome} desperta o poder da fruta e deixa o efeito tomar forma ao redor do corpo.",
    },
}

ABERTURAS = [
    "Um golpe direto, sem enfeite.",
    "Uma técnica que começa pequena e termina grande.",
    "Um movimento que parece simples até o impacto.",
    "Uma demonstração de controle antes da violência.",
]


def patamares_disponiveis() -> list[str]:
    return list(PATAMARES)


def gerar_golpe(patamar: str = "Média", categoria: str = "Impacto",
                sabor: str = "Técnica marcial", nome_base: str = "Golpe",
                rng: random.Random | None = None) -> dict[str, str]:
    """Monta um golpe pronto para virar bloco de habilidade na ficha."""
    gerador = rng if rng is not None else random
    dados_patamar = PATAMARES.get(patamar, PATAMARES["Média"])
    dados_categoria = CATEGORIAS.get(categoria, CATEGORIAS["Impacto"])
    dados_sabor = SABORES.get(sabor, SABORES["Técnica marcial"])

    palavra = gerador.choice(list(dados_sabor["palavras"]))
    titulo = gerador.choice(list(dados_categoria["titulos"])).format(x=palavra)

    texto = (
        f"{dados_sabor['texto'].format(nome=nome_base)} "
        f"{dados_categoria['efeito'].capitalize()}. "
        f"{gerador.choice(ABERTURAS)}\n\n"
        f"Dano: {dados_patamar['dano']}.\n"
        f"Custo: {dados_patamar['custo']} (base do patamar {patamar}, nível mínimo "
        f"{dados_patamar['nivel']}).\n"
        f"Potencialização: até {dados_patamar['limite']} extras, chegando a "
        f"{dados_patamar['total']} no total."
    )

    alcance = {
        "Impacto": "Corpo a corpo",
        "Corte": "Corpo a corpo",
        "Área": "Área 3 m",
        "Mobilidade": "Pessoal",
        "Defesa": "Pessoal",
    }.get(categoria, "Corpo a corpo")

    return {
        "titulo": titulo,
        "custo": str(dados_patamar["custo"]),
        "limite": str(dados_patamar["limite"]),
        "execucao": "1 Ação",
        "alcance": alcance,
        "conteudo": texto,
    }
