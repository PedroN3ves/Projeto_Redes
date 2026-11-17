"""Regras do jogo da velha, sem nenhuma parte de rede.

Este modulo so cuida do tabuleiro: quem pode jogar, se a jogada e valida e
quem ganhou. O servidor/partida chama a classe Jogo e traduz o resultado em
mensagens do protocolo.

Posicoes do tabuleiro (o jogador digita de 1 a 9):

    1 | 2 | 3
    4 | 5 | 6
    7 | 8 | 9
"""

VAZIO = "-"
X = "X"
O = "O"
EMPATE = "EMPATE"

# As 8 combinacoes vencedoras, em indices de 0 a 8 (posicao - 1).
LINHAS_VENCEDORAS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # linhas
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # colunas
    (0, 4, 8), (2, 4, 6),             # diagonais
)


class JogadaInvalida(Exception):
    """Jogada recusada. A mensagem serve de motivo para o ERRO do protocolo."""


class Jogo:
    """Uma partida de jogo da velha. O X sempre comeca."""

    def __init__(self):
        self.casas = [VAZIO] * 9
        self.vez = X
        self._resultado = None  # None, "X", "O" ou "EMPATE"

    def jogar(self, simbolo, posicao):
        """Marca a casa `posicao` (1 a 9) para `simbolo` ("X" ou "O").

        Retorna True se a jogada foi feita. Se for invalida, levanta
        JogadaInvalida e o estado do jogo nao muda.
        Ordem das checagens: fim de jogo, simbolo, vez, posicao, casa ocupada.
        """
        if self._resultado is not None:
            raise JogadaInvalida("a partida ja terminou")
        if simbolo not in (X, O):
            raise JogadaInvalida("simbolo invalido")
        if simbolo != self.vez:
            raise JogadaInvalida("nao e a sua vez")

        indice = self._indice(posicao)
        if self.casas[indice] != VAZIO:
            raise JogadaInvalida("casa ocupada")

        self.casas[indice] = simbolo
        self._atualizar_resultado()
        if self._resultado is None:
            self.vez = O if simbolo == X else X
        return True

    def tabuleiro_str(self):
        """Tabuleiro em 9 caracteres, `-` para casa vazia (ex.: "X-O--X---")."""
        return "".join(self.casas)

    def vencedor(self):
        """Retorna "X", "O", "EMPATE" ou None (partida ainda em andamento)."""
        return self._resultado

    def terminou(self):
        return self._resultado is not None

    @staticmethod
    def _indice(posicao):
        """Converte a posicao (1 a 9) para indice (0 a 8) ou recusa."""
        if isinstance(posicao, str) and posicao.strip().isdecimal():
            posicao = int(posicao)
        if isinstance(posicao, bool) or not isinstance(posicao, int):
            raise JogadaInvalida("a posicao deve ser um numero de 1 a 9")
        if not 1 <= posicao <= 9:
            raise JogadaInvalida("posicao fora do intervalo de 1 a 9")
        return posicao - 1

    def _atualizar_resultado(self):
        for a, b, c in LINHAS_VENCEDORAS:
            if self.casas[a] != VAZIO and self.casas[a] == self.casas[b] == self.casas[c]:
                self._resultado = self.casas[a]
                return
        if VAZIO not in self.casas:
            self._resultado = EMPATE
