"""Persistência do ImpelDown Archives: Markdown, JSON e SQLite.

A gravação do cofre é atômica: escreve em um arquivo temporário e só troca o
original quando tudo deu certo, para uma queda no meio do processo não deixar o
banco pela metade.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from typing import Any

_CREATE_TABELA = (
    "CREATE TABLE IF NOT EXISTS dados_rpg "
    "(id INTEGER PRIMARY KEY, estrutura TEXT, fichas TEXT)"
)


def exportar_ficha_markdown(caminho: str, dados: dict[str, Any]) -> None:
    """Gera a ficha em Markdown, no formato usado nas anotações de mesa."""
    recompensa = str(dados.get("recompensa", "") or "").strip()
    bounty = f"{recompensa} Berries" if recompensa else "0 Berries"

    linhas = [
        f"# {dados.get('nome', 'Inimigo')}",
        f"Nível: {dados.get('nivel', '1')} | Recompensa: {bounty}",
        f"PV: {dados.get('pv', 0)} / {dados.get('pv_max', dados.get('pv', 0))} | "
        f"PE: {dados.get('pe', 0)} / {dados.get('pe_max', dados.get('pe', 0))}",
        "",
        "## Atributos",
        f"- Físico: {dados.get('fis', 0)} | Agilidade: {dados.get('agi', 0)} | "
        f"Intelecto: {dados.get('int', 0)} | Instinto: {dados.get('inst', 0)}",
        f"- Grau Luta: {dados.get('luta', 0)} | Grau Acro: {dados.get('acro', 0)}",
        "",
        "## Loot e Drops",
        str(dados.get("loot", "")),
        "",
        "## Habilidades",
    ]
    for hab in dados.get("habilidades", []):
        linhas.append(f"### {hab.get('titulo', 'Habilidade')}")
        linhas.append(
            f"Custo: {hab.get('custo', '-')} | Limite: {hab.get('limite', '-')} | "
            f"Execução: {hab.get('execucao', '-')} | Alcance: {hab.get('alcance', '-')}"
        )
        linhas.append(str(hab.get("conteudo", "")))
        linhas.append("")

    linhas += ["## Notas e História", str(dados.get("historia", ""))]

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))


def exportar_ficha_json(caminho: str, dados: dict[str, Any]) -> None:
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)


def importar_ficha_json(caminho: str) -> dict[str, Any]:
    """Lê uma ficha em JSON e garante que o conteúdo é um objeto."""
    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if not isinstance(dados, dict):
        raise ValueError("O arquivo não contém uma ficha válida.")
    return dados


def salvar_banco_sqlite(
    caminho_db: str,
    estrutura_arvore: list[dict],
    dados_banco: dict[str, Any],
) -> None:
    """Grava o cofre inteiro de forma atômica (temporário + os.replace)."""
    estrutura = json.dumps(estrutura_arvore, ensure_ascii=False)
    fichas = json.dumps(dados_banco, ensure_ascii=False)
    temporario = f"{caminho_db}.tmp"

    try:
        with closing(sqlite3.connect(temporario)) as conn:
            with conn:
                conn.execute(_CREATE_TABELA)
                conn.execute("DELETE FROM dados_rpg")
                conn.execute(
                    "INSERT INTO dados_rpg (id, estrutura, fichas) VALUES (1, ?, ?)",
                    (estrutura, fichas),
                )
        os.replace(temporario, caminho_db)
    except Exception:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass
        raise


def carregar_banco_sqlite(caminho_db: str) -> tuple[list[dict] | None, dict[str, Any] | None]:
    """Lê o cofre sem alterar o arquivo original (modo somente leitura)."""
    if not os.path.exists(caminho_db):
        raise FileNotFoundError(f"Banco não encontrado: {caminho_db}")

    try:
        with closing(sqlite3.connect(f"file:{caminho_db}?mode=ro", uri=True)) as conn:
            linha = conn.execute(
                "SELECT estrutura, fichas FROM dados_rpg WHERE id=1"
            ).fetchone()
    except sqlite3.OperationalError:
        return None, None

    if not linha:
        return None, None

    estrutura = json.loads(linha[0])
    fichas = json.loads(linha[1])
    if not isinstance(estrutura, list) or not isinstance(fichas, dict):
        return None, None
    return estrutura, fichas
