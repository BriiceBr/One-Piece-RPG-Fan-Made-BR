"""Persistência do ImpelDown Archives: Markdown, JSON e SQLite.

A gravação do cofre é atômica (temporário + os.replace) e mantém um backup
rotativo ``.db.bak`` da versão anterior. O cofre também guarda uma linha de
configuração (jogadores, nível médio do grupo etc.).
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from contextlib import closing
from typing import Any

_CREATE_TABELA = (
    "CREATE TABLE IF NOT EXISTS dados_rpg "
    "(id INTEGER PRIMARY KEY, estrutura TEXT, fichas TEXT, config TEXT)"
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


#: Quantos backups rotativos ficam guardados (`.bak`, `.bak.1`, `.bak.2`).
MAX_BACKUPS = 3


def fazer_backup(caminho_db: str) -> str | None:
    """Gira os backups e copia o cofre atual para ``.db.bak``.

    Mantém um pequeno histórico: ``.bak`` (última versão), ``.bak.1`` e
    ``.bak.2`` (versões anteriores). Nunca apaga o cofre original.
    """
    if not os.path.exists(caminho_db):
        return None
    try:
        # .bak.2 <- .bak.1 <- .bak  (o mais novo avança uma posição para baixo)
        for i in range(MAX_BACKUPS - 1, 0, -1):
            origem = f"{caminho_db}.bak.{i - 1}" if i > 1 else f"{caminho_db}.bak"
            destino = f"{caminho_db}.bak.{i}"
            if os.path.exists(origem):
                shutil.copy2(origem, destino)
        destino = f"{caminho_db}.bak"
        shutil.copy2(caminho_db, destino)
        return destino
    except OSError:
        return None


def _garantir_coluna_config(conn: sqlite3.Connection) -> None:
    colunas = {linha[1] for linha in conn.execute("PRAGMA table_info(dados_rpg)")}
    if "config" not in colunas:
        conn.execute("ALTER TABLE dados_rpg ADD COLUMN config TEXT")


def salvar_banco_sqlite(
    caminho_db: str,
    estrutura_arvore: list[dict],
    dados_banco: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> None:
    """Grava o cofre de forma atômica, com backup da versão anterior."""
    estrutura = json.dumps(estrutura_arvore, ensure_ascii=False)
    fichas = json.dumps(dados_banco, ensure_ascii=False)
    config_json = json.dumps(config or {}, ensure_ascii=False)
    temporario = f"{caminho_db}.tmp"

    try:
        with closing(sqlite3.connect(temporario)) as conn:
            conn.execute("PRAGMA busy_timeout = 5000")
            with conn:
                conn.execute(_CREATE_TABELA)
                _garantir_coluna_config(conn)
                conn.execute("DELETE FROM dados_rpg")
                conn.execute(
                    "INSERT INTO dados_rpg (id, estrutura, fichas, config) VALUES (1, ?, ?, ?)",
                    (estrutura, fichas, config_json),
                )
        if os.path.exists(caminho_db):
            fazer_backup(caminho_db)
        os.replace(temporario, caminho_db)
    except Exception:
        if os.path.exists(temporario):
            try:
                os.remove(temporario)
            except OSError:
                pass
        raise


def carregar_banco_sqlite(
    caminho_db: str,
) -> tuple[list[dict] | None, dict[str, Any] | None, dict[str, Any]]:
    """Lê o cofre (estrutura, fichas, configuração) sem alterar o arquivo."""
    if not os.path.exists(caminho_db):
        raise FileNotFoundError(f"Banco não encontrado: {caminho_db}")

    linha = None
    with closing(sqlite3.connect(f"file:{caminho_db}?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            colunas = {col[1] for col in conn.execute("PRAGMA table_info(dados_rpg)")}
        except sqlite3.OperationalError:
            return None, None, {}

        if not {"estrutura", "fichas"} <= colunas:
            return None, None, {}

        selecao = "estrutura, fichas" + (", config" if "config" in colunas else "")
        linha = conn.execute(
            f"SELECT {selecao} FROM dados_rpg WHERE id=1"
        ).fetchone()

    if not linha:
        return None, None, {}

    estrutura = json.loads(linha[0])
    fichas = json.loads(linha[1])
    config: dict[str, Any] = {}
    if len(linha) > 2 and linha[2]:
        try:
            lido = json.loads(linha[2])
            if isinstance(lido, dict):
                config = lido
        except (TypeError, ValueError):
            config = {}

    if not isinstance(estrutura, list) or not isinstance(fichas, dict):
        return None, None, {}
    return estrutura, fichas, config
