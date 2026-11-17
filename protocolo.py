"""
Protocolo do jogo da velha em rede.

Cada mensagem é uma linha de texto (UTF-8) terminada em "\\n".
O formato é: COMANDO, um espaço e o argumento (quando existe).

Cliente -> servidor
    NOME <nome>               nome do jogador (pode ter espaços)
    JOGAR <1-9>               casa escolhida
    SAIR                      sair do jogo

Servidor -> cliente
    AGUARDE                   está na fila esperando adversário
    INICIO <X|O> <adversário> a partida começou; símbolo de quem recebe
    TABULEIRO <9 casas>       casas 1 a 9 em ordem: X, O ou - (vazia)
    VEZ <X|O>                 de quem é a vez
    FIM <VITORIA|DERROTA|EMPATE>  resultado para quem recebe
    SAIU                      o adversário desconectou
    ERRO <motivo>             comando inválido ou jogada inválida
"""

TAMANHO_MAXIMO = 256 

SIMBOLOS = ("X", "O")
RESULTADOS = ("VITORIA", "DERROTA", "EMPATE")


class ErroProtocolo(Exception):
    """Mensagem malformada ou comando desconhecido."""


# Montar

def montar_nome(nome):
    return "NOME " + nome + "\n"


def montar_jogar(casa):
    return "JOGAR " + str(casa) + "\n"


def montar_sair():
    return "SAIR\n"


def montar_aguarde():
    return "AGUARDE\n"


def montar_inicio(simbolo, adversario):
    return "INICIO " + simbolo + " " + adversario + "\n"


def montar_tabuleiro(casas):
    return "TABULEIRO " + casas + "\n"


def montar_vez(simbolo):
    return "VEZ " + simbolo + "\n"


def montar_fim(resultado):
    return "FIM " + resultado + "\n"


def montar_saiu():
    return "SAIU\n"


def montar_erro(motivo):
    return "ERRO " + motivo + "\n"


def enviar(sock, mensagem):
    """Envia uma mensagem já montada pelo socket."""
    sock.sendall(mensagem.encode("utf-8"))


# Interpretar

def interpretar(linha):
    """
    Recebe uma linha (sem o "\\n") e devolve (comando, argumento).

    O argumento depende do comando:
        NOME, ERRO              -> texto
        JOGAR                   -> inteiro de 1 a 9
        INICIO                  -> (simbolo, adversario)
        TABULEIRO, VEZ, FIM     -> texto já validado
        SAIR, AGUARDE, SAIU     -> None

    Lança ErroProtocolo se a linha for malformada.
    """
    partes = linha.strip().split(" ", 1)
    comando = partes[0]
    if len(partes) == 2:
        resto = partes[1].strip()
    else:
        resto = ""

    if comando in ("SAIR", "AGUARDE", "SAIU"):
        if resto != "":
            raise ErroProtocolo(comando + " nao recebe argumento")
        return comando, None

    if comando in ("NOME", "ERRO"):
        if resto == "":
            raise ErroProtocolo(comando + " precisa de um texto")
        return comando, resto

    if comando == "JOGAR":
        if resto not in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            raise ErroProtocolo("JOGAR precisa de uma casa de 1 a 9")
        return comando, int(resto)

    if comando == "INICIO":
        dados = resto.split(" ", 1)
        if len(dados) != 2 or dados[0] not in SIMBOLOS:
            raise ErroProtocolo("INICIO precisa de simbolo e adversario")
        return comando, (dados[0], dados[1])

    if comando == "TABULEIRO":
        if len(resto) != 9:
            raise ErroProtocolo("TABULEIRO precisa de 9 casas")
        for casa in resto:
            if casa not in ("X", "O", "-"):
                raise ErroProtocolo("casa invalida no TABULEIRO")
        return comando, resto

    if comando == "VEZ":
        if resto not in SIMBOLOS:
            raise ErroProtocolo("VEZ precisa de X ou O")
        return comando, resto

    if comando == "FIM":
        if resto not in RESULTADOS:
            raise ErroProtocolo("resultado invalido no FIM")
        return comando, resto

    raise ErroProtocolo("comando desconhecido")



class LeitorDeLinhas:
    """
    O TCP entrega um fluxo de bytes, não mensagens separadas: um recv()
    pode trazer meia mensagem ou várias de uma vez. O leitor guarda os
    bytes recebidos em um buffer e só devolve uma linha quando ela
    está completa.
    """

    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def ler_linha(self):
        """
        Devolve a próxima linha (sem o "\\n") ou None se a conexão fechou.
        Lança ErroProtocolo se a linha for grande demais ou não for UTF-8.
        """
        while b"\n" not in self.buffer:
            if len(self.buffer) > TAMANHO_MAXIMO:
                self.buffer = b""
                raise ErroProtocolo("linha grande demais")
            dados = self.sock.recv(1024)
            if not dados:
                return None
            self.buffer += dados

        linha, self.buffer = self.buffer.split(b"\n", 1)

        if len(linha) > TAMANHO_MAXIMO:
            raise ErroProtocolo("linha grande demais")
        try:
            texto = linha.decode("utf-8")
        except UnicodeDecodeError:
            raise ErroProtocolo("linha nao esta em UTF-8")
        return texto.rstrip("\r")