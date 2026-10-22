"""Testes de regras, combate e encontros do ImpelDown Archives."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from core.combate import (  # noqa: E402
    calcular_dificuldade_encontro,
    classificar,
    multiplicador_horda,
    poder_do_grupo,
)
from core.regras import calcular_atributos_derivados  # noqa: E402
from core.desafio import analisar as analisar_desafio  # noqa: E402
from utils.encontros import encontrar_para_alvo, sugerir_encontros  # noqa: E402


class TestRegras(unittest.TestCase):
    def test_pv_nivel_1(self) -> None:
        res = calcular_atributos_derivados(1, 4, 2, 1, 2, 2, 0)
        self.assertEqual(res["pv"], 16)

    def test_pv_por_nivel(self) -> None:
        res = calcular_atributos_derivados(3, 4, 2, 1, 2, 2, 0)
        self.assertEqual(res["pv"], (12 + 4) + 2 * (6 + 4))

    def test_pe(self) -> None:
        res = calcular_atributos_derivados(5, 3, 2, 5, 1, 0, 0)
        self.assertEqual(res["pe"], 4 + 5 + 5)

    def test_defesas_e_cd(self) -> None:
        res = calcular_atributos_derivados(6, 4, 3, 1, 1, 2, 1, 1, 2, 3, 4)
        self.assertEqual(res["passiva"], 10 + 3 + 1)
        self.assertEqual(res["bloqueio"], 10 + 4 + 2 * 2 + 2)
        self.assertEqual(res["esquiva"], 10 + 3 + 2 * 1 + 3)
        self.assertEqual(res["cd"], 10 + 4 + (6 // 2) + 4)

    def test_bonus_de_pv_e_pe(self) -> None:
        normal = calcular_atributos_derivados(3, 4, 2, 1, 2, 2, 0)
        extra = calcular_atributos_derivados(3, 4, 2, 1, 2, 2, 0, bonus_pv=10, bonus_pe=4)
        self.assertEqual(extra["pv"], normal["pv"] + 10)
        self.assertEqual(extra["pe"], normal["pe"] + 4)

    def test_nivel_invalido_vira_1(self) -> None:
        res = calcular_atributos_derivados("abc", 1, 1, 1, 1, 0, 0)
        self.assertEqual(res["pv"], 13)


class TestCombate(unittest.TestCase):
    def test_faixas(self) -> None:
        self.assertEqual(classificar(0.60)[0], "Fácil")
        self.assertEqual(classificar(0.61)[0], "Médio")
        self.assertEqual(classificar(1.00)[0], "Médio")
        self.assertEqual(classificar(1.01)[0], "Difícil")
        self.assertEqual(classificar(1.41)[0], "Mortal")

    def test_horda(self) -> None:
        self.assertAlmostEqual(multiplicador_horda(4, 4), 1.0)
        self.assertAlmostEqual(multiplicador_horda(6, 4), 1.3)
        self.assertAlmostEqual(multiplicador_horda(100, 4), 2.0)

    def test_poder_do_grupo_tolera_texto(self) -> None:
        self.assertEqual(poder_do_grupo("4", "5"), 20)
        self.assertEqual(poder_do_grupo("x", None), 4)

    def test_ficha_duplicada_nao_infla(self) -> None:
        banco = {"a": {"nivel": 4}, "b": {"nivel": 2}}
        texto, _cor = calcular_dificuldade_encontro([{"id": "a"}, {"id": "a"}], banco, 4, 5)
        self.assertIn("Inimigos 4", texto)

    def test_inimigos_diferentes_contam_por_linha(self) -> None:
        banco = {"m1": {"nivel": 2}, "m2": {"nivel": 2}}
        texto, _cor = calcular_dificuldade_encontro([{"id": "m1"}, {"id": "m2"}], banco, 4, 5)
        self.assertIn("Inimigos 4", texto)

    def test_sem_inimigos(self) -> None:
        self.assertEqual(calcular_dificuldade_encontro([], {}), ("Sem Inimigos", "#8b8c8f"))


class TestEncontros(unittest.TestCase):
    def test_cada_sugestao_bate_com_o_rotulo(self) -> None:
        for jogadores, nivel in ((4, 1), (4, 5), (5, 10)):
            for sugestao in sugerir_encontros(jogadores, nivel):
                self.assertEqual(sugestao.classificacao, sugestao.rotulo)
                self.assertGreaterEqual(sugestao.chefe_nivel, 1)
                self.assertGreaterEqual(sugestao.lacaios, 0)
                self.assertGreater(sugestao.hp_total, 0)
                self.assertGreaterEqual(sugestao.rodadas, 1)

    def test_alvo_encontrado(self) -> None:
        sugestao = encontrar_para_alvo(4, 5, "Desafiador")
        self.assertIsNotNone(sugestao)
        self.assertEqual(sugestao.classificacao, "Desafiador")

    def test_rodadas_por_classe(self) -> None:
        faixas = {"Fácil": (1, 2), "Desafiador": (3, 4), "Mortal": (5, 99)}
        for sugestao in sugerir_encontros(4, 5):
            minimo, maximo = faixas[sugestao.rotulo]
            self.assertGreaterEqual(sugestao.rodadas, minimo)
            self.assertLessEqual(sugestao.rodadas, maximo)


class TestDesafioPorDano(unittest.TestCase):
    def test_dano_por_patamar(self) -> None:
        self.assertEqual(analisar_desafio(4, 2, 100)["dano_jogador"], 12)
        self.assertEqual(analisar_desafio(4, 5, 100)["dano_jogador"], 20)
        self.assertEqual(analisar_desafio(4, 10, 100)["dano_jogador"], 32)
        self.assertEqual(analisar_desafio(4, 15, 100)["dano_jogador"], 60)

    def test_rodadas_e_classes(self) -> None:
        # 4 jogadores Nv 5 = 80 de dano por rodada
        self.assertEqual(analisar_desafio(4, 5, 160)["rodadas_inteiras"], 2)
        self.assertEqual(analisar_desafio(4, 5, 160)["rotulo"], "Fácil")
        self.assertEqual(analisar_desafio(4, 5, 320)["rotulo"], "Desafiador")
        self.assertEqual(analisar_desafio(4, 5, 480)["rotulo"], "Mortal")

    def test_sugestoes_para_faixa(self) -> None:
        rapido = analisar_desafio(4, 5, 80)
        self.assertIn("Rápido", rapido["sugestoes"][0])
        letal = analisar_desafio(4, 5, 800)
        self.assertIn("Letal", letal["sugestoes"][0])
        ok = analisar_desafio(4, 5, 280)
        self.assertIn("Faixa desejada", ok["sugestoes"][0])

    def test_sem_hp(self) -> None:
        dados = analisar_desafio(4, 5, 0)
        self.assertEqual(dados["rotulo"], "Sem HP")
        self.assertEqual(dados["rodadas_inteiras"], 0)


if __name__ == "__main__":
    unittest.main()
