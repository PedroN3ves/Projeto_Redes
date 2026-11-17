"""Coordena fila, partidas e turnos do jogo da velha.

Este modulo nao cria threads nem aceita sockets. O servidor pode chamar
``receber`` para cada linha recebida e usar ``adicionar`` quando um cliente
enviar seu nome. O estado compartilhado e protegido por ``threading.RLock``,
portanto chamadas vindas de threads diferentes nao podem corromper uma
partida ou a fila.
"""

from collections import deque
from dataclasses import dataclass
from threading import RLock

import protocolo
from jogo import EMPATE, Jogo, JogadaInvalida


@dataclass(frozen=True)
class Jogador:
    """Dados imutaveis de um jogador conectado a uma partida."""

    sock: object
    nome: str
    simbolo: str


class Partida:
    """Uma partida entre exatamente dois sockets."""

    def __init__(self, primeiro, segundo):
        self.lock = RLock()
        self.jogo = Jogo()
        self.jogadores = {
            "X": Jogador(primeiro.sock, primeiro.nome, "X"),
            "O": Jogador(segundo.sock, segundo.nome, "O"),
        }
        self._por_socket = {
            primeiro.sock: self.jogadores["X"],
            segundo.sock: self.jogadores["O"],
        }
        self.encerrada = False

    def iniciar(self):
        """Notifica os dois jogadores e publica o estado inicial."""
        with self.lock:
            if self.encerrada:
                return
            for simbolo, jogador in self.jogadores.items():
                adversario = self.jogadores["O" if simbolo == "X" else "X"]
                self._enviar(jogador.sock, "INICIO", simbolo + " " + adversario.nome)
            self._publicar_estado()

    def jogar(self, sock, posicao):
        """Processa uma jogada e retorna ``True`` quando ela e aceita."""
        with self.lock:
            jogador = self._por_socket.get(sock)
            if jogador is None:
                self._erro(sock, "jogador nao esta nesta partida")
                return False
            if self.encerrada:
                self._erro(sock, "a partida ja terminou")
                return False

            try:
                self.jogo.jogar(jogador.simbolo, posicao)
            except JogadaInvalida as erro:
                self._erro(sock, str(erro))
                return False

            self._publicar_tabuleiro()
            vencedor = self.jogo.vencedor()
            if vencedor is not None:
                self._publicar_fim(vencedor)
                self.encerrada = True
            else:
                self._publicar_vez()
            return True

    def desconectar(self, sock):
        """Encerra a partida e avisa o adversario, se ele ainda estiver ativo."""
        with self.lock:
            jogador = self._por_socket.pop(sock, None)
            if jogador is None:
                return False
            self.encerrada = True
            for outro in self._por_socket.values():
                self._enviar(outro.sock, "SAIU")
            return True

    def contem(self, sock):
        with self.lock:
            return sock in self._por_socket

    def _publicar_estado(self):
        self._publicar_tabuleiro()
        self._publicar_vez()

    def _publicar_tabuleiro(self):
        self._transmitir("TABULEIRO", self.jogo.tabuleiro_str())

    def _publicar_vez(self):
        self._transmitir("VEZ", self.jogo.vez)

    def _publicar_fim(self, vencedor):
        for jogador in self.jogadores.values():
            if vencedor == EMPATE:
                resultado = "EMPATE"
            elif vencedor == jogador.simbolo:
                resultado = "VITORIA"
            else:
                resultado = "DERROTA"
            self._enviar(jogador.sock, "FIM", resultado)

    def _transmitir(self, comando, argumento):
        for jogador in tuple(self.jogadores.values()):
            self._enviar(jogador.sock, comando, argumento)

    @staticmethod
    def _enviar(sock, comando, argumento=None):
        protocolo.enviar(sock, protocolo.montar(comando, argumento or ""))

    def _erro(self, sock, motivo):
        self._enviar(sock, "ERRO", motivo)


@dataclass(frozen=True)
class _Esperando:
    sock: object
    nome: str


class GerenciadorPartidas:
    """Mantem a fila de espera e o conjunto de partidas simultaneas."""

    def __init__(self):
        self.lock = RLock()
        self._espera = deque()
        self._jogadores = {}
        self._partidas = set()

    def adicionar(self, sock, nome):
        """Coloca um jogador na fila ou inicia uma nova partida.

        Retorna a ``Partida`` criada ou ``None`` enquanto o jogador espera.
        """
        nome = str(nome).strip()
        if not nome:
            raise ValueError("o nome nao pode ficar vazio")

        with self.lock:
            if sock in self._jogadores:
                raise ValueError("socket ja esta registrado")
            jogador = _Esperando(sock, nome)
            self._jogadores[sock] = jogador
            if not self._espera:
                self._espera.append(sock)
                self._enviar(sock, "AGUARDE")
                return None

            outro_sock = self._espera.popleft()
            outro = self._jogadores[outro_sock]
            partida = Partida(outro, jogador)
            self._partidas.add(partida)
            self._jogadores[outro_sock] = partida
            self._jogadores[sock] = partida
            partida.iniciar()
            return partida

    def receber(self, sock, linha):
        """Interpreta uma linha de protocolo e executa a operacao solicitada."""
        with self.lock:
            registro = self._jogadores.get(sock)
            try:
                comando, argumento = protocolo.interpretar(linha)
            except protocolo.ErroProtocolo as erro:
                self._enviar(sock, "ERRO", str(erro))
                return False

            if comando == "NOME":
                if registro is not None:
                    self._enviar(sock, "ERRO", "NOME ja foi informado")
                    return False
                self.adicionar(sock, argumento)
                return True

            if registro is None:
                self._enviar(sock, "ERRO", "envie NOME primeiro")
                return False
            if comando == "SAIR":
                self.desconectar(sock)
                return True
            if comando != "JOGAR":
                self._enviar(sock, "ERRO", "comando invalido neste estado")
                return False
            if not isinstance(registro, Partida):
                self._enviar(sock, "ERRO", "aguarde um adversario")
                return False
            return registro.jogar(sock, argumento)

    def desconectar(self, sock):
        """Remove um cliente da fila ou encerra sua partida."""
        with self.lock:
            registro = self._jogadores.pop(sock, None)
            if registro is None:
                return False
            if isinstance(registro, Partida):
                registro.desconectar(sock)
                if not registro.contem(sock):
                    self._partidas.discard(registro)
                    for outro_sock in tuple(registro._por_socket):
                        self._jogadores.pop(outro_sock, None)
            else:
                try:
                    self._espera.remove(sock)
                except ValueError:
                    pass
            return True

    def partidas_ativas(self):
        with self.lock:
            return tuple(self._partidas)

    @staticmethod
    def _enviar(sock, comando, argumento=None):
        protocolo.enviar(sock, protocolo.montar(comando, argumento or ""))

