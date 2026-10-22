"""Gerador local de histórias para fichas do ImpelDown Archives.

Não usa internet nem modelo de linguagem: monta um texto de apresentação
combinando os dados da ficha (Atributos, Graus de Perícia, Nível e recompensa)
com bancos de frases. Cada chamada sorteia frases diferentes, então gerar de
novo produz uma variação.
"""

from __future__ import annotations

import random
import re

MAPA_DE_ATRIBUTOS: tuple[tuple[str, str], ...] = (
    ("fis", "Físico"),
    ("agi", "Agilidade"),
    ("int", "Intelecto"),
    ("inst", "Instinto"),
)

MARCOS = ["East Blue", "West Blue", "North Blue", "South Blue", "Grand Line", "Novo Mundo"]

ORIGENS = [
    "um vilarejo de pescadores esquecido pelos mapas",
    "um porto de contrabandistas onde a lei nunca chegou",
    "as docas podres de um arquipélago de corsários",
    "uma caravana de mercadores que cruzava o mar sem escolta",
    "uma ilha de ferreiros que vendia lâminas para qualquer bandeira",
    "as ruas de um orfanato comandado por um velho pirata aposentado",
    "as minas de sal de uma ilha comprada por um Nobre do Mar",
    "um navio-hospital que afundou numa tempestade",
    "uma vila de pescadores que pagava tributo a um capitão local",
    "um circo itinerante que navegava entre ilhas",
]

DETALHES_DE_ORIGEM = [
    "Cresceu ouvindo que o mar devolve o que a gente joga nele.",
    "Aprendeu a nadar antes de andar e a mentir antes de ler.",
    "Foi criado por gente que confundia coragem com teimosia.",
    "Nunca teve nome de família, só um apelido que pegou.",
    "Saiu de casa com uma faca, um mapa errado e muita pressa.",
    "Passou a infância consertando redes em troca de comida.",
    "Viu o primeiro navio de guerra antes de ver a primeira escola.",
    "Foi o único sobrevivente de algo que não gosta de contar.",
]

APARENCIAS = [
    "Alto e largo como uma porta de armazém, com as mãos cheias de cicatrizes antigas.",
    "Magro, de passos largos e olhos que nunca param quietos.",
    "Carrega no rosto a marca de um ferro em brasa que nunca explicou.",
    "Veste um casaco grande demais, herdado de alguém que não voltou.",
    "Pequeno o bastante para passar despercebido e forte o bastante para não precisar disso.",
    "Tem a pele marcada pelo sal e o cabelo sempre úmido de maresia.",
    "Anda calçado com botas de oficial, roubadas em circunstâncias que variam conforme o ouvinte.",
    "Fala baixo e olha nos olhos por tempo demais, o que incomoda quase todo mundo.",
]

MARCAS = [
    "Tem uma cicatriz que atravessa a sobrancelha e some no cabelo.",
    "Fuma um cachimbo de osso e nunca acende dois no mesmo dia.",
    "Usa um colar de dentes de peixe que jura ser de um Rei do Mar.",
    "Manqueja da perna esquerda quando o tempo fecha.",
    "Perdeu dois dentes e conta a história de um jeito diferente a cada vez.",
    "Tatuou o próprio nome no antebraço para não esquecer de quem é.",
    "Nunca solta uma moeda antiga que carrega no bolso.",
]

PERSONALIDADES = {
    "Físico": [
        "Não discute: resolve. Prefere a honestidade brutal de um soco à delicadeza de uma promessa.",
        "Tem paciência curta e lealdade longa — desde que ninguém toque no que é dele.",
        "Acredita que todo problema tem uma solução direta, e que quase toda solução direta cabe na mão.",
    ],
    "Agilidade": [
        "Fala rápido, some mais rápido ainda e quase sempre volta pelo lado que ninguém vigiava.",
        "Prefere rir de um perigo a encará-lo de frente. Quando encara, já tem um plano de fuga.",
        "Não suporta ficar parado. Acha que estar em movimento é a única forma honesta de viver.",
    ],
    "Intelecto": [
        "Gosta de vencer antes do primeiro golpe. Se puder, vence antes do primeiro encontro.",
        "Anota tudo em cadernos que ninguém tem permissão de ler, e cobra caro pelo que sabe.",
        "Trata uma briga como um problema de logística: entra tarde, sai primeiro, gasta menos.",
    ],
    "Instinto": [
        "Confia no próprio estômago mais do que em qualquer mapa ou autoridade.",
        "Sente quando o vento vai virar e quando o sorriso do outro é mentira.",
        "Não explica como sabe das coisas. Só avisa, e costuma estar certo.",
    ],
}

OBJETIVOS = [
    "Quer o mapa que o avô queimou antes de morrer.",
    "Persegue o homem que afundou o navio onde cresceu.",
    "Junta dinheiro para comprar a liberdade de alguém.",
    "Procura a ilha que só aparece numa canção de bêbados.",
    "Quer provar que o mar não tem dono.",
    "Está atrás de uma fruta que, dizem, foi enterrada com um capitão.",
    "Precisa limpar o nome que sujou para proteger uma irmã.",
    "Cobra uma dívida antiga de alguém que hoje usa uniforme branco.",
]

GANCHOS = [
    "Pode aparecer em qualquer porto contando uma história que ninguém acredita — até alguém acreditar.",
    "Tem um favor a cobrar de um personagem seu, e escolhe a pior hora possível para cobrar.",
    "É caçado por dois caçadores de recompensas que se odeiam e, por isso, são mais perigosos juntos.",
    "Carrega uma carta selada que prometeu não abrir, e está começando a duvidar da promessa.",
    "Pode ser contratado como guia — pelo preço certo, e o preço certo não é dinheiro.",
    "Sabe onde está algo que os jogadores procuram, e vai querer ir junto.",
    "Foi visto conversando com a Marinha. Ou com piratas. Ou com os dois, na mesma noite.",
]

LEMAS_POR_AMEACA = (
    (3, "Ainda é um nome local: perigoso para um vilarejo, pequeno para um oceano."),
    (7, "Já é conhecido em mais de um porto, e há quem mude de rota para não cruzar com ele."),
    (12, "Seu nome aparece em cartazes de recrutamento e em conversas de taverna da Grand Line."),
    (17, "Poucos o enfrentam de frente; os que enfrentaram raramente contam a história."),
    (20, "É o tipo de ameaça que faz um Almirante escolher outro mar para patrulhar."),
)


def _maior_atributo(perfil: dict) -> tuple[str, int]:
    """Devolve (nome do Atributo, valor) do maior Atributo da ficha."""
    escolhido = ("Físico", 0)
    for chave, nome in MAPA_DE_ATRIBUTOS:
        valor = int(perfil.get(chave, 0) or 0)
        if valor > escolhido[1]:
            escolhido = (nome, valor)
    return escolhido


def _texto_de_combate(perfil: dict, nome: str, arquetipo: str) -> str:
    """Parágrafo de combate usando Graus de Perícia e o maior Atributo."""
    luta = int(perfil.get("luta", 0) or 0)
    acro = int(perfil.get("acro", 0) or 0)
    valor = int(perfil.get(arquetipo_chave(arquetipo), 0) or 0)

    if luta > acro:
        arma = "nas mãos, nos punhos e no que estiver ao alcance"
        estilo = f"Grau {luta} em Luta"
    elif acro > luta:
        arma = "na distância, no ângulo e na velocidade"
        estilo = f"Grau {acro} em Acrobacia"
    else:
        arma = "no terreno e no que der para improvisar"
        estilo = f"Grau {luta} em Luta e Acrobacia"

    return (
        f"Em combate, {nome} aposta em {arma}. "
        f"Com {estilo} e {arquetipo} {valor}, prefere decidir a briga nos primeiros segundos — "
        f"antes que o inimigo entenda o que está acontecendo."
    )


def arquetipo_chave(arquetipo: str) -> str:
    """Converte o nome do Atributo de volta para a chave usada na ficha."""
    for chave, nome in MAPA_DE_ATRIBUTOS:
        if nome == arquetipo:
            return chave
    return "fis"


def _formatar_recompensa(perfil: dict) -> str:
    texto = str(perfil.get("recompensa", "0") or "0")
    digitos = re.sub(r"\D", "", texto)
    valor = int(digitos) if digitos else 0
    if valor <= 0:
        return "Não há recompensa formal pela cabeça — o que, para alguns, é ainda pior."
    return f"A Marinha paga {valor:,} Berries por sua cabeça.".replace(",", ".")


def _lema_de_ameaca(nivel: int) -> str:
    for limite, frase in LEMAS_POR_AMEACA:
        if nivel <= limite:
            return frase
    return LEMAS_POR_AMEACA[-1][1]


def gerar_historia(perfil: dict, rng: random.Random | None = None) -> str:
    """Monta a apresentação do inimigo a partir dos dados da ficha."""
    gerador = rng if rng is not None else random
    nome = str(perfil.get("nome") or "O desconhecido").strip()
    nivel = max(1, int(perfil.get("nivel", 1) or 1))
    arquetipo, valor = _maior_atributo(perfil)

    origem = gerador.choice(ORIGENS)
    detalhe = gerador.choice(DETALHES_DE_ORIGEM)
    aparencia = gerador.choice(APARENCIAS)
    marca = gerador.choice(MARCAS)
    personalidade = gerador.choice(PERSONALIDADES[arquetipo])
    objetivo = gerador.choice(OBJETIVOS)
    gancho = gerador.choice(GANCHOS)

    paragrafos = [
        f"Origem — {nome} veio de {origem}, em {gerador.choice(MARCOS)}. {detalhe}",
        f"Aparência — {aparencia} {marca}",
        f"Personalidade — {personalidade}",
        _texto_de_combate(perfil, nome, arquetipo),
        f"Objetivo — {objetivo}",
        f"Gancho para a mesa — {gancho}",
        f"Ameaça — Nível {nivel}. {_lema_de_ameaca(nivel)} {_formatar_recompensa(perfil)}",
    ]
    return "\n\n".join(paragrafos)
