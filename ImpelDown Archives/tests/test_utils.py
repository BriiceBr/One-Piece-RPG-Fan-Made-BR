"""Testes de loot, importação e persistência do ImpelDown Archives."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from utils.arquivos import carregar_banco_sqlite, salvar_banco_sqlite  # noqa: E402
from utils.importacao import ler_lote, validar_ficha  # noqa: E402
from utils.loot import (  # noqa: E402
    chance_de_fruta,
    gerar_loot_aleatorio,
    normalizar_faccao,
)


class TestLoot(unittest.TestCase):
    def test_faccoes(self) -> None:
        self.assertEqual(normalizar_faccao("Marinha"), "marinha")
        self.assertEqual(normalizar_faccao("Vilões"), "pirata")
        self.assertEqual(normalizar_faccao("Monstros"), "fera")
        self.assertEqual(normalizar_faccao("Governo Mundial"), "governo")
        self.assertEqual(normalizar_faccao("Pasta qualquer"), "outros")

    def test_fruta_por_nivel(self) -> None:
        self.assertEqual(chance_de_fruta(11), 0.0)
        self.assertAlmostEqual(chance_de_fruta(12), 0.02)
        self.assertAlmostEqual(chance_de_fruta(20), 0.05)

    def test_loot_tem_berries_e_itens(self) -> None:
        texto = gerar_loot_aleatorio(5, faccao="Piratas")
        self.assertIn("Berries", texto)
        self.assertIn("Nível 5", texto)
        self.assertIn("Facção: Piratas", texto)
        self.assertGreaterEqual(texto.count("• ["), 1)

    def test_arma_favorecida_por_fisico(self) -> None:
        """Com Físico/Luta altos, a proporção de armas deve subir."""
        def contar_armas(dados):
            armas = 0
            for semente in range(200):
                import random
                texto = gerar_loot_aleatorio(10, dados=dados, faccao="Piratas", rng=random.Random(semente))
                armas += texto.count("(arma)")
            return armas

        fraco = contar_armas({"fis": 0, "luta": 0})
        forte = contar_armas({"fis": 5, "luta": 3})
        self.assertGreater(forte, fraco)


class TestImportacao(unittest.TestCase):
    def test_validar_ficha_normaliza(self) -> None:
        ficha = validar_ficha({"nome": " X ", "nivel": "3", "fis": 9, "luta": -2})
        self.assertEqual(ficha["nome"], "X")
        self.assertEqual(ficha["nivel"], "3")
        self.assertEqual(ficha["fis"], 5)
        self.assertEqual(ficha["luta"], -1)

    def test_ficha_sem_nome_falha(self) -> None:
        with self.assertRaises(ValueError):
            validar_ficha({"nome": "  "})

    def test_lote_json_com_erro(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "lote.json")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump([{"nome": "A", "nivel": 2}, {"nivel": 1}], arquivo)
            validas, erros = ler_lote(caminho)
            self.assertEqual([f["nome"] for f in validas], ["A"])
            self.assertEqual(len(erros), 1)

    def test_lote_csv(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "lote.csv")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write("nome,nivel,fis\nPirata,3,4\nMarujo,1,2\n")
            validas, erros = ler_lote(caminho)
            self.assertEqual(len(validas), 2)
            self.assertEqual(validas[0]["fis"], 4)
            self.assertEqual(erros, [])


class TestPersistencia(unittest.TestCase):
    def test_roundtrip_com_config_e_backup(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "cofre.db")
            estrutura = [{"id": "1", "text": " Pasta", "tags": ["pasta"], "open": True, "filhos": []}]
            fichas = {"1": {"nome": "Arlong", "nivel": "3"}}
            config = {"jogadores": 5, "nivel_grupo": 4}

            salvar_banco_sqlite(caminho, estrutura, fichas, config)
            self.assertFalse(os.path.exists(caminho + ".bak"))

            salvar_banco_sqlite(caminho, estrutura, fichas, config)
            self.assertTrue(os.path.exists(caminho + ".bak"))

            lido_estrutura, lido_fichas, lido_config = carregar_banco_sqlite(caminho)
            self.assertEqual(lido_estrutura, estrutura)
            self.assertEqual(lido_fichas, fichas)
            self.assertEqual(lido_config, config)

    def test_banco_antigo_sem_coluna_config(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "antigo.db")
            conn = sqlite3.connect(caminho)
            conn.execute("CREATE TABLE dados_rpg (id INTEGER PRIMARY KEY, estrutura TEXT, fichas TEXT)")
            conn.execute(
                "INSERT INTO dados_rpg (id, estrutura, fichas) VALUES (1, ?, ?)",
                (json.dumps([]), json.dumps({})),
            )
            conn.commit()
            conn.close()

            estrutura, fichas, config = carregar_banco_sqlite(caminho)
            self.assertEqual(estrutura, [])
            self.assertEqual(fichas, {})
            self.assertEqual(config, {})


if __name__ == "__main__":
    unittest.main()
