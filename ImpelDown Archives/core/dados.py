"""Motores de rolagem do ImpelDown Archives.

O módulo tem dois motores independentes:

* :func:`rolar_dados_seguro` — expressões somadas, no formato ``2d8+3``.
  Continua sendo o motor de **dano** e de **ataques**.
* :func:`rolar_teste_pericia` — Poça de d20 do sistema novo. Rola de 1 a 4 d20
  conforme o grau da Perícia e usa o **maior** resultado. Vantagem acrescenta
  1 dado e Desvantagem remove 1 dado. Se a poça chegar a 0 dados ou menos,
  rola 2d20 e usa o **menor**.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Literal

#: Grau máximo de uma Perícia (0 Leigo, 1 Treinado, 2 Especialista, 3 Mestre).
GRAU_MAXIMO: int = 3

#: Quantos d20 cada grau rola, antes de Vantagens e Desvantagens.
DADOS_POR_GRAU: dict[int, int] = {0: 1, 1: 2, 2: 3, 3: 4}

#: Nome do grau, para exibir nos registros e nas fichas.
NOME_DO_GRAU: dict[int, str] = {0: "Leigo", 1: "Treinado", 2: "Especialista", 3: "Mestre"}

#: Limite de segurança de dados em uma rolagem somada.
MAX_DADOS_EXPRESSAO: int = 100


def rolar_dados_seguro(expressao: str, rng: random.Random | None = None) -> str:
    """Rola uma expressão somada (ex.: ``2d8+3``) e devolve o total detalhado.

    Usado para dano e ataques. Não confundir com :func:`rolar_teste_pericia`,
    que é a Poça de d20 dos Testes de Perícia.
    """
    gerador = rng if rng is not None else random
    texto = re.sub(r"\s+", "", expressao).lower()
    if not texto:
        raise ValueError("Informe uma expressão de dados.")
    termos = re.findall(r"[+-]?[^+-]+", texto)
    if "".join(termos) != texto:
        raise ValueError("Expressão inválida.")

    total = 0
    detalhes: list[str] = []

    for termo in termos:
        sinal = -1 if termo.startswith("-") else 1
        corpo = termo.lstrip("+-")
        if not corpo:
            continue

        if "d" in corpo:
            partes = re.fullmatch(r"(\d*)d(\d+)", corpo)
            if not partes:
                raise ValueError(f"Formato inválido: {termo}")
            qtd = int(partes.group(1) or "1")
            lados = int(partes.group(2))
            if not 1 <= qtd <= MAX_DADOS_EXPRESSAO:
                raise ValueError(f"Limite: 1 a {MAX_DADOS_EXPRESSAO} dados.")
            if not 2 <= lados <= 1000:
                raise ValueError("Limite: dados de 2 a 1000 faces.")

            rolagens = [gerador.randint(1, lados) for _ in range(qtd)]
            total += sum(rolagens) * sinal
            sinal_texto = "-" if sinal < 0 else "+"
            detalhes.append(f"{sinal_texto}({'+'.join(map(str, rolagens))})")
        else:
            if not re.fullmatch(r"\d+", corpo):
                raise ValueError(f"Modificador inválido: {termo}")
            valor = int(corpo) * sinal
            total += valor
            detalhes.append(f"{valor:+d}")

    return f"{total} 🎲 ({' '.join(detalhes).lstrip('+ ')})"


def dados_do_grau(grau: int) -> int:
    """Devolve quantos d20 o grau rola, antes de Vantagens e Desvantagens."""
    if grau not in DADOS_POR_GRAU:
        raise ValueError(
            f"Grau inválido: {grau}. Use de 0 (Leigo) a {GRAU_MAXIMO} (Mestre)."
        )
    return DADOS_POR_GRAU[grau]


def rolar_poca_d20(quantidade: int, rng: random.Random | None = None) -> list[int]:
    """Rola ``quantidade`` d20 e devolve todos os resultados, na ordem em que saíram."""
    if quantidade < 1:
        raise ValueError("A poça precisa de pelo menos 1 dado.")
    if quantidade > 20:
        raise ValueError("Limite: 20 dados na poça.")
    gerador = rng if rng is not None else random
    return [gerador.randint(1, 20) for _ in range(quantidade)]


@dataclass(frozen=True)
class ResultadoTeste:
    """Resultado de um Teste de Perícia com Poça de d20.

    O total é ``maior dado + Atributo + bônus fixo`` (ou o menor dado, quando a
    poça é reduzida a zero por Desvantagem).
    """

    dados: tuple[int, ...]
    usado: int
    atributo: int
    bonus_extra: int
    grau: int
    vantagens: int
    desvantagens: int
    cd: int | None = None
    modo: Literal["maior", "menor"] = "maior"

    @property
    def total(self) -> int:
        """Total do Teste, pronto para comparar com a CD."""
        return self.usado + self.atributo + self.bonus_extra

    @property
    def sucesso(self) -> bool | None:
        """``True``/``False`` se houver CD; ``None`` quando a CD não foi informada."""
        if self.cd is None:
            return None
        return self.total >= self.cd

    @property
    def resumo(self) -> str:
        """Linha curta para a ficha, ex.: ``maior(14, 8) = 14 +3 Atributo = 17``."""
        regra = "maior" if self.modo == "maior" else "menor"
        lista = ", ".join(str(d) for d in self.dados)
        partes = [f"{regra}({lista}) = {self.usado}"]
        if self.atributo:
            partes.append(f"{self.atributo:+d} Atributo")
        if self.bonus_extra:
            partes.append(f"{self.bonus_extra:+d} bônus")
        texto = " ".join(partes) + f" = {self.total}"
        if self.cd is not None:
            texto += f" | CD {self.cd} → {'Sucesso' if self.sucesso else 'Falha'}"
        return texto

    @property
    def detalhamento(self) -> str:
        """Versão completa para o registro de combate, com grau e ajustes."""
        ajustes: list[str] = []
        if self.vantagens:
            ajustes.append(f"+{self.vantagens} Vantagem")
        if self.desvantagens:
            ajustes.append(f"-{self.desvantagens} Desvantagem")
        sufixo = f", {', '.join(ajustes)}" if ajustes else ""
        grau = NOME_DO_GRAU.get(self.grau, str(self.grau))
        base = DADOS_POR_GRAU.get(self.grau, 1)
        return f"{grau} ({base}d20{sufixo}) • {self.resumo}"


def rolar_teste_pericia(
    atributo: int,
    grau: int,
    vantagens: int = 0,
    desvantagens: int = 0,
    bonus_extra: int = 0,
    cd: int | None = None,
    rng: random.Random | None = None,
) -> ResultadoTeste:
    """Rola um Teste de Perícia na Poça de d20 do sistema novo.

    Args:
        atributo: valor do Atributo somado ao resultado (bônus fixo, 0 não penaliza).
        grau: de 0 (Leigo, 1d20) a 3 (Mestre, 4d20).
        vantagens: quantas fontes de Vantagem (cada uma dá +1 dado).
        desvantagens: quantas fontes de Desvantagem (cada uma tira 1 dado).
        bonus_extra: bônus fixo de Origem/Raça/item (±2, no máximo +3 de item).
        cd: Classe de Dificuldade opcional, só para já dizer se houve sucesso.
        rng: gerador alternativo, usado nos testes automatizados.

    Returns:
        Um :class:`ResultadoTeste` imutável.
    """
    grau = int(grau)
    base = dados_do_grau(grau)
    vantagens = max(0, int(vantagens))
    desvantagens = max(0, int(desvantagens))

    quantidade = base + vantagens - desvantagens

    if quantidade <= 0:
        dados = rolar_poca_d20(2, rng)
        usado = min(dados)
        modo: Literal["maior", "menor"] = "menor"
    else:
        dados = rolar_poca_d20(quantidade, rng)
        usado = max(dados)
        modo = "maior"

    return ResultadoTeste(
        dados=tuple(dados),
        usado=usado,
        atributo=int(atributo),
        bonus_extra=int(bonus_extra),
        grau=grau,
        vantagens=vantagens,
        desvantagens=desvantagens,
        cd=cd,
        modo=modo,
    )
