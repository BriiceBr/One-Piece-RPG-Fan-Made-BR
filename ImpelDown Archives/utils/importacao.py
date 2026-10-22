"""Importação em lote de fichas (JSON ou CSV) com validação mínima.

Regras de validação:
* precisa ter ``nome`` não vazio (JSON: objeto ou lista de objetos; CSV: coluna nome);
* Nível vira inteiro >= 1;
* Atributos ficam entre 0 e 5 e Graus entre 0 e 3;
* campos desconhecidos são preservados (para não perder conteúdo futuro).
"""

from __future__ import annotations

import csv
import json
from typing import Any

ATRIBUTOS = ("fis", "agi", "int", "inst")
GRAUS = ("luta", "acro")


def _inteiro(valor: Any, padrao: int = 0) -> int:
    try:
        return int(float(str(valor).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return padrao


def validar_ficha(dados: dict[str, Any]) -> dict[str, Any]:
    """Normaliza uma ficha vinda de arquivo; levanta ValueError se inválida."""
    if not isinstance(dados, dict):
        raise ValueError("a ficha precisa ser um objeto")
    ficha = dict(dados)
    nome = str(ficha.get("nome", "") or "").strip()
    if not nome:
        raise ValueError("ficha sem nome")
    ficha["nome"] = nome
    ficha["nivel"] = str(max(1, _inteiro(ficha.get("nivel", 1), 1)))
    for campo in ATRIBUTOS:
        ficha[campo] = max(0, min(5, _inteiro(ficha.get(campo, 1), 1)))
    for campo in GRAUS:
        ficha[campo] = max(0, min(3, _inteiro(ficha.get(campo, 0), 0)))
    return ficha


def _ler_json(caminho: str) -> list[Any]:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        conteudo = json.load(arquivo)
    if isinstance(conteudo, dict):
        # Aceita tanto uma ficha quanto {"fichas": [...]}
        if isinstance(conteudo.get("fichas"), list):
            return conteudo["fichas"]
        return [conteudo]
    if isinstance(conteudo, list):
        return conteudo
    raise ValueError("JSON precisa ser uma ficha ou uma lista de fichas")


def _ler_csv(caminho: str) -> list[dict[str, Any]]:
    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        amostra = arquivo.read(4096)
        arquivo.seek(0)
        try:
            dialeto = csv.Sniffer().sniff(amostra, delimiters=",;")
        except csv.Error:
            dialeto = csv.excel
        leitor = csv.DictReader(arquivo, dialect=dialeto)
        return [dict(linha) for linha in leitor]


def ler_lote(caminho: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Lê e valida um lote; devolve (fichas válidas, mensagens de erro)."""
    if caminho.lower().endswith(".csv"):
        brutos = _ler_csv(caminho)
    else:
        brutos = _ler_json(caminho)

    validas: list[dict[str, Any]] = []
    erros: list[str] = []
    for indice, bruto in enumerate(brutos, start=1):
        try:
            validas.append(validar_ficha(bruto))
        except ValueError as erro:
            erros.append(f"Item {indice}: {erro}")
    return validas, erros
