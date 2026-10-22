"""Testes da mecânica de rolagem (Poça de d20 e dano) do ImpelDown Archives.

Independem do Tkinter e usam ``random.Random`` injetado para serem
determinísticos.
"""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from core.dados import (  # noqa: E402
    dados_do_grau,
    rolar_dados_seguro,
    rolar_poca_d20,
    rolar_teste_pericia,
)


class TestGraus(unittest.TestCase):
    def test_dados_por_grau(self) -> None:
        self.assertEqual(dados_do_grau(0), 1)
        self.assertEqual(dados_do_grau(1), 2)
        self.assertEqual(dados_do_grau(2), 3)
        self.assertEqual(dados_do_grau(3), 4)

    def test_grau_invalido_falha(self) -> None:
        with self.assertRaises(ValueError):
            dados_do_grau(4)
        with self.assertRaises(ValueError):
            dados_do_grau(-1)


class TestPocaD20(unittest.TestCase):
    def test_quantidade_e_faixa(self) -> None:
        rolagem = rolar_poca_d20(4, random.Random(7))
        self.assertEqual(len(rolagem), 4)
        self.assertTrue(all(1 <= dado <= 20 for dado in rolagem))

    def test_determinista_com_seed(self) -> None:
        a = rolar_poca_d20(5, random.Random(123))
        b = rolar_poca_d20(5, random.Random(123))
        self.assertEqual(a, b)

    def test_quantidade_invalida(self) -> None:
        with self.assertRaises(ValueError):
            rolar_poca_d20(0)


class TestTestePericia(unittest.TestCase):
    def test_maior_resultado_mais_atributo(self) -> None:
        resultado = rolar_teste_pericia(3, grau=1, rng=random.Random(10))
        self.assertEqual(resultado.usado, max(resultado.dados))
        self.assertEqual(resultado.total, max(resultado.dados) + 3)
        self.assertEqual(resultado.modo, "maior")

    def test_vantagem_adiciona_dado(self) -> None:
        resultado = rolar_teste_pericia(0, grau=0, vantagens=2, rng=random.Random(1))
        self.assertEqual(len(resultado.dados), 3)

    def test_desvantagem_ate_zero_usa_menor(self) -> None:
        resultado = rolar_teste_pericia(0, grau=0, desvantagens=1, rng=random.Random(2))
        self.assertEqual(resultado.modo, "menor")
        self.assertEqual(len(resultado.dados), 2)
        self.assertEqual(resultado.usado, min(resultado.dados))

    def test_sucesso_contra_cd(self) -> None:
        resultado = rolar_teste_pericia(4, grau=0, cd=10, rng=random.Random(3))
        self.assertIsNotNone(resultado.sucesso)
        self.assertEqual(resultado.sucesso, resultado.total >= 10)


class TestDano(unittest.TestCase):
    def test_determinista_com_seed(self) -> None:
        a = rolar_dados_seguro("2d6+2", rng=random.Random(5))
        b = rolar_dados_seguro("2d6+2", rng=random.Random(5))
        self.assertEqual(a, b)

    def test_modificador_sozinho(self) -> None:
        self.assertEqual(rolar_dados_seguro("3"), "3 🎲 (3)")

    def test_expressao_invalida(self) -> None:
        with self.assertRaises(ValueError):
            rolar_dados_seguro("abc")
        with self.assertRaises(ValueError):
            rolar_dados_seguro("1d1")


if __name__ == "__main__":
    unittest.main()
