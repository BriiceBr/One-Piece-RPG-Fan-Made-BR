"""Sugestão de composição de encontros balanceados por dano/rodada.

Sem tabela fixa de HP: o PV de cada inimigo é estimado pela fórmula oficial
(PV = PV de Raça + Nível × Físico + 5 × (Nível − 1)), usando os mesmos
arquétipos que a ficha gera. A classificação usa o dano da party por rodada
(core.desafio), não a antiga soma de níveis.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.desafio import analisar as analisar_desafio
from core.regras import calcular_atributos_derivados

#: Ajuste de PV dado ao chefe na criação do encontro.
BONUS_PV_CHEFE = 10


def perfil_lacaio(nivel: int, arquetipo: str = "Esquadrão Balanceado",
                  indice: int = 1) -> dict[str, int]:
    """Atributos/Graus coerentes com o Nível, moldados pelo arquétipo."""
    nivel = max(1, int(nivel))
    maior = min(5, 2 + (nivel - 1) // 3)
    secundario = min(4, 1 + (nivel - 1) // 5)
    grau = min(3, (nivel - 1) // 3)

    if arquetipo == "Bando de Atiradores":
        return {
            "fis": max(0, secundario - 1), "agi": maior, "intel": secundario,
            "inst": max(1, secundario), "luta": max(0, grau - 1), "acro": grau,
        }
    if arquetipo == "Vanguarda Pesada":
        return {
            "fis": maior, "agi": secundario, "intel": 1,
            "inst": secundario, "luta": grau, "acro": 0,
        }
    troca = indice % 2 == 0
    return {
        "fis": maior if troca else secundario,
        "agi": secundario if troca else maior,
        "intel": max(1, secundario - 1),
        "inst": secundario,
        "luta": grau,
        "acro": max(0, grau - 1) if troca else grau,
    }


def pv_do_arquetipo(nivel: int, arquetipo: str = "Esquadrão Balanceado",
                    indice: int = 1, bonus_pv: int = 0) -> int:
    """PV estimado de um inimigo gerado com esse arquétipo."""
    perfil = perfil_lacaio(nivel, arquetipo, indice)
    res = calcular_atributos_derivados(
        nivel, perfil["fis"], perfil["agi"], perfil["intel"], perfil["inst"],
        perfil["luta"], perfil["acro"], bonus_pv=bonus_pv,
    )
    return res["pv"]


@dataclass(frozen=True)
class Sugestao:
    rotulo: str
    chefe_nivel: int
    lacaios: int
    lacaio_nivel: int
    hp_total: int
    rodadas: int
    rodadas_exatas: float
    classificacao: str

    @property
    def resumo(self) -> str:
        plural = "lacaio" if self.lacaios == 1 else "lacaios"
        return (
            f"{self.rotulo}: 1 chefe Nv {self.chefe_nivel} + "
            f"{self.lacaios} {plural} Nv {self.lacaio_nivel} → "
            f"{self.classificacao} ({self.rodadas} rodada(s), {self.hp_total} HP)"
        )


def hp_da_composicao(chefe_nivel: int, lacaios: int, lacaio_nivel: int) -> int:
    """Soma o PV estimado do chefe e dos lacaios de uma composição."""
    hp = pv_do_arquetipo(chefe_nivel, "Vanguarda Pesada", 1, BONUS_PV_CHEFE)
    for indice in range(1, max(0, lacaios) + 1):
        hp += pv_do_arquetipo(lacaio_nivel, "Esquadrão Balanceado", indice)
    return hp


def avaliar_composicao(jogadores: int, nivel_medio: int, chefe_nivel: int,
                       lacaios: int, lacaio_nivel: int, rotulo: str = "") -> Sugestao:
    """Calcula HP, rodadas e classificação de uma composição específica."""
    hp_total = hp_da_composicao(max(1, chefe_nivel), max(0, lacaios), max(1, lacaio_nivel))
    dados = analisar_desafio(jogadores, nivel_medio, hp_total)
    return Sugestao(
        rotulo=rotulo or dados["rotulo"],
        chefe_nivel=max(1, chefe_nivel),
        lacaios=max(0, lacaios),
        lacaio_nivel=max(1, lacaio_nivel),
        hp_total=hp_total,
        rodadas=dados["rodadas_inteiras"],
        rodadas_exatas=dados["rodadas"],
        classificacao=dados["rotulo"],
    )


def sugerir_encontros(jogadores: int = 4, nivel_medio: int = 1) -> list[Sugestao]:
    """Busca composições para Fácil, Desafiador e Mortal (por rodadas)."""
    nivel = max(1, nivel_medio)
    centros = {"Fácil": 1.5, "Desafiador": 3.5, "Mortal": 5.5}
    candidatas: list[Sugestao] = []

    for lacaios in (0, 1, 2, 3, 4, 6, 8):
        for chefe in range(max(1, nivel - 3), nivel + 7):
            for lacaio_nivel in range(max(1, nivel - 3), nivel + 5):
                candidatas.append(
                    avaliar_composicao(jogadores, nivel, chefe, lacaios, lacaio_nivel)
                )

    escolhidas: list[Sugestao] = []
    for rotulo, centro in centros.items():
        opcoes = [s for s in candidatas if s.classificacao == rotulo]
        if not opcoes:
            opcoes = sorted(candidatas, key=lambda s: abs(s.rodadas - centro))[:1]
        melhor = min(
            opcoes,
            key=lambda s: (abs(s.rodadas_exatas - centro), s.hp_total, s.lacaios),
        )
        escolhidas.append(Sugestao(
            rotulo=rotulo,
            chefe_nivel=melhor.chefe_nivel,
            lacaios=melhor.lacaios,
            lacaio_nivel=melhor.lacaio_nivel,
            hp_total=melhor.hp_total,
            rodadas=melhor.rodadas,
            rodadas_exatas=melhor.rodadas_exatas,
            classificacao=melhor.classificacao,
        ))
    return escolhidas


def encontrar_para_alvo(jogadores: int, nivel_medio: int, alvo: str) -> Sugestao | None:
    """Devolve a sugestão cuja classificação bate com o alvo."""
    normalizado = str(alvo).strip().lower()
    aliases = {"facil": "fácil", "fácil": "fácil", "medio": "desafiador",
               "médio": "desafiador", "dificil": "desafiador", "difícil": "desafiador",
               "mortal": "mortal"}
    normalizado = aliases.get(normalizado, normalizado)
    for sugestao in sugerir_encontros(jogadores, nivel_medio):
        if sugestao.classificacao.lower() == normalizado:
            return sugestao
    return None
