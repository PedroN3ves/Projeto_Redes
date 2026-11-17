"""Testes unitarios do jogo.py.

Como rodar (na pasta do projeto):
    python -m unittest discover -s testes -v
"""

import itertools
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from jogo import EMPATE, LINHAS_VENCEDORAS, Jogo, JogadaInvalida  # noqa: E402


def jogar_todas(jogo, lances):
    for simbolo, posicao in lances:
        jogo.jogar(simbolo, posicao)


def lances_de_vitoria(linha, vencedor):
    """Monta uma partida valida em que `vencedor` completa `linha` no ultimo lance."""
    alvo = [i + 1 for i in linha]
    resto = [p for p in range(1, 10) if p not in alvo]
    # Jogadas do perdedor que nao formam uma linha vencedora.
    quantidade = 2 if vencedor == "X" else 3
    for fora in itertools.combinations(resto, quantidade):
        if tuple(p - 1 for p in fora) not in LINHAS_VENCEDORAS:
            break

    lances = []
    if vencedor == "X":
        for i in range(3):
            lances.append(("X", alvo[i]))
            if i < 2:
                lances.append(("O", fora[i]))
    else:
        for i in range(3):
            lances.append(("X", fora[i]))
            lances.append(("O", alvo[i]))
    return lances


class TestEstadoInicial(unittest.TestCase):
    def test_tabuleiro_comeca_vazio(self):
        self.assertEqual(Jogo().tabuleiro_str(), "---------")

    def test_sem_vencedor_no_inicio(self):
        jogo = Jogo()
        self.assertIsNone(jogo.vencedor())
        self.assertFalse(jogo.terminou())

    def test_x_comeca(self):
        self.assertEqual(Jogo().vez, "X")


class TestJogadasEVez(unittest.TestCase):
    def test_jogada_valida_marca_a_casa(self):
        jogo = Jogo()
        self.assertTrue(jogo.jogar("X", 1))
        self.assertEqual(jogo.tabuleiro_str(), "X--------")

    def test_posicao_9_vai_para_a_ultima_casa(self):
        jogo = Jogo()
        jogo.jogar("X", 9)
        self.assertEqual(jogo.tabuleiro_str(), "--------X")

    def test_vez_alterna_entre_x_e_o(self):
        jogo = Jogo()
        jogo.jogar("X", 1)
        self.assertEqual(jogo.vez, "O")
        jogo.jogar("O", 2)
        self.assertEqual(jogo.vez, "X")

    def test_aceita_posicao_como_texto(self):
        jogo = Jogo()
        jogo.jogar("X", "5")
        self.assertEqual(jogo.tabuleiro_str(), "----X----")

    def test_sem_vencedor_durante_o_jogo(self):
        jogo = Jogo()
        jogar_todas(jogo, [("X", 1), ("O", 2), ("X", 5)])
        self.assertIsNone(jogo.vencedor())
        self.assertFalse(jogo.terminou())


class TestVitoria(unittest.TestCase):
    def test_existem_8_combinacoes_vencedoras(self):
        self.assertEqual(len(LINHAS_VENCEDORAS), 8)

    def test_x_vence_em_todas_as_8_combinacoes(self):
        for linha in LINHAS_VENCEDORAS:
            with self.subTest(linha=[i + 1 for i in linha]):
                lances = lances_de_vitoria(linha, "X")
                jogo = Jogo()
                jogar_todas(jogo, lances[:-1])
                self.assertIsNone(jogo.vencedor())
                jogo.jogar(*lances[-1])
                self.assertEqual(jogo.vencedor(), "X")
                self.assertTrue(jogo.terminou())

    def test_o_vence_em_todas_as_8_combinacoes(self):
        for linha in LINHAS_VENCEDORAS:
            with self.subTest(linha=[i + 1 for i in linha]):
                lances = lances_de_vitoria(linha, "O")
                jogo = Jogo()
                jogar_todas(jogo, lances[:-1])
                self.assertIsNone(jogo.vencedor())
                jogo.jogar(*lances[-1])
                self.assertEqual(jogo.vencedor(), "O")
                self.assertTrue(jogo.terminou())

    def test_vitoria_na_ultima_casa_nao_e_empate(self):
        # Tabuleiro final: X O X / O X O / O X X  (X completa 1-5-9 no 9o lance)
        jogo = Jogo()
        jogar_todas(jogo, [
            ("X", 1), ("O", 2), ("X", 3), ("O", 4), ("X", 8),
            ("O", 6), ("X", 5), ("O", 7), ("X", 9),
        ])
        self.assertEqual(jogo.tabuleiro_str(), "XOXOXOOXX")
        self.assertEqual(jogo.vencedor(), "X")


class TestEmpate(unittest.TestCase):
    def test_empate_com_tabuleiro_cheio(self):
        # Tabuleiro final: X O X / X O O / O X X
        jogo = Jogo()
        jogar_todas(jogo, [
            ("X", 1), ("O", 2), ("X", 3), ("O", 5), ("X", 4),
            ("O", 6), ("X", 8), ("O", 7), ("X", 9),
        ])
        self.assertEqual(jogo.tabuleiro_str(), "XOXXOOOXX")
        self.assertEqual(jogo.vencedor(), EMPATE)
        self.assertTrue(jogo.terminou())


class TestJogadasInvalidas(unittest.TestCase):
    def setUp(self):
        self.jogo = Jogo()

    def recusa(self, simbolo, posicao, trecho):
        with self.assertRaises(JogadaInvalida) as contexto:
            self.jogo.jogar(simbolo, posicao)
        self.assertIn(trecho, str(contexto.exception))

    def test_casa_ocupada(self):
        self.jogo.jogar("X", 5)
        self.recusa("O", 5, "ocupada")

    def test_jogar_na_propria_casa_ja_ocupada(self):
        self.jogo.jogar("X", 5)
        self.jogo.jogar("O", 1)
        self.recusa("X", 5, "ocupada")

    def test_fora_do_intervalo(self):
        for posicao in (0, 10, -1, 99):
            with self.subTest(posicao=posicao):
                self.recusa("X", posicao, "intervalo")

    def test_posicao_que_nao_e_numero_inteiro(self):
        for posicao in ("abc", "", None, 1.5, True, [1]):
            with self.subTest(posicao=posicao):
                self.recusa("X", posicao, "numero")

    def test_fora_da_vez_no_primeiro_lance(self):
        self.recusa("O", 1, "vez")

    def test_mesmo_jogador_duas_vezes_seguidas(self):
        self.jogo.jogar("X", 1)
        self.recusa("X", 2, "vez")

    def test_simbolo_invalido(self):
        self.recusa("Z", 1, "simbolo")

    def test_jogar_depois_do_fim_da_partida(self):
        jogar_todas(self.jogo, [("X", 1), ("O", 4), ("X", 2), ("O", 5), ("X", 3)])
        self.assertEqual(self.jogo.vencedor(), "X")
        self.recusa("O", 9, "terminou")

    def test_jogada_recusada_nao_muda_o_estado(self):
        self.jogo.jogar("X", 1)
        antes = (self.jogo.tabuleiro_str(), self.jogo.vez, self.jogo.vencedor())
        for simbolo, posicao in (("O", 1), ("X", 2), ("O", 0), ("O", "abc"), ("Z", 3)):
            with self.assertRaises(JogadaInvalida):
                self.jogo.jogar(simbolo, posicao)
        depois = (self.jogo.tabuleiro_str(), self.jogo.vez, self.jogo.vencedor())
        self.assertEqual(antes, depois)

    def test_vez_continua_a_mesma_depois_de_jogada_recusada(self):
        self.jogo.jogar("X", 1)
        with self.assertRaises(JogadaInvalida):
            self.jogo.jogar("O", 1)
        self.assertTrue(self.jogo.jogar("O", 2))


if __name__ == "__main__":
    unittest.main()
