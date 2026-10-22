"""Sugestão de composição de encontros balanceados.

Usa o mesmo cálculo do Combat Tracker (poder do grupo x poder dos inimigos +
multiplicador de horda) para montar opções de chefe + lacaios.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.combate import classificar, multiplicador_horda, poder_do_grupo


@dataclass(frozen=True)
class Sugestao:
    rotulo: str
    chefe_nivel: int
    lacaios: int
    lacaio_nivel: int
    poder_inimigos: float
    razao: float
    classificacao: str

    @property
    def resumo(self) -> str:
        plural = "lacaio" if self.lacaios == 1 else "lacaios"
        return (
            f"{self.rotulo}: 1 chefe Nv {self.chefe_nivel} + "
            f"{self.lacaios} {plural} Nv {self.lacaio_nivel} → "
            f"{self.classificacao} ({self.razao:.0%})"
        )


def avaliar_composicao(jogadores: int, nivel_medio: int, chefe_nivel: int,
                       lacaios: int, lacaio_nivel: int, rotulo: str = "") -> Sugestao:
    """Calcula a classificação de uma composição específica."""
    poder_grupo = poder_do_grupo(jogadores, nivel_medio)
    total_inimigos = 1 + lacaios
    soma = max(0, chefe_nivel) + max(0, lacaios) * max(0, lacaio_nivel)
    poder = soma * multiplicador_horda(total_inimigos, jogadores)
    razao = poder / poder_grupo
    classificacao, _cor = classificar(razao)
    return Sugestao(
        rotulo=rotulo or classificacao,
        chefe_nivel=max(1, chefe_nivel),
        lacaios=max(0, lacaios),
        lacaio_nivel=max(1, lacaio_nivel),
        poder_inimigos=poder,
        razao=razao,
        classificacao=classificacao,
    )


def sugerir_encontros(jogadores: int = 4, nivel_medio: int = 1) -> list[Sugestao]:
    """Busca composições que caiam em cada faixa desejada.

    Em vez de chutar níveis fixos, testa combinações de chefe/lacaios e escolhe
    a que fica mais perto do centro de cada faixa (Fácil 50%, Médio 85%,
    Difícil 120%, Mortal 160%).
    """
    nivel = max(1, nivel_medio)
    centros = {"Fácil": 0.5, "Médio": 0.85, "Difícil": 1.2, "Mortal": 1.6}
    candidatas: list[Sugestao] = []

    for lacaios in (0, 1, 2, 3, 4, 6, 8):
        for chefe in range(max(1, nivel - 3), nivel + 7):
            for lacaio_nivel in range(max(1, nivel - 3), nivel + 5):
                sugestao = avaliar_composicao(jogadores, nivel, chefe, lacaios, lacaio_nivel)
                candidatas.append(sugestao)

    escolhidas: list[Sugestao] = []
    for rotulo, centro in centros.items():
        opcoes = [s for s in candidatas if s.classificacao == rotulo]
        if not opcoes:
            opcoes = sorted(candidatas, key=lambda s: abs(s.razao - centro))[:1]
        melhor = min(opcoes, key=lambda s: (abs(s.razao - centro), s.lacaios, s.chefe_nivel))
        escolhidas.append(Sugestao(
            rotulo=rotulo,
            chefe_nivel=melhor.chefe_nivel,
            lacaios=melhor.lacaios,
            lacaio_nivel=melhor.lacaio_nivel,
            poder_inimigos=melhor.poder_inimigos,
            razao=melhor.razao,
            classificacao=melhor.classificacao,
        ))
    return escolhidas


def encontrar_para_alvo(jogadores: int, nivel_medio: int, alvo: str) -> Sugestao | None:
    """Devolve a sugestão cuja classificação bate com o alvo (ex.: "Médio")."""
    for sugestao in sugerir_encontros(jogadores, nivel_medio):
        if sugestao.classificacao.lower() == alvo.lower():
            return sugestao
    return None
