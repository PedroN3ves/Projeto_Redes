"""
Protocolo do jogo da velha em rede

Cada mensagem é uma linha de texto (UTF-8) terminada em "\\n"
O formato é: COMANDO, um espaço e o argumento (quando existe)

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
    """Mensagem corrompida ou comando desconhecido"""


def montar(comando, argumento=""):
    if argumento == "":
        return comando + "\n"
    return comando + " " + str(argumento) + "\n"


def enviar(sock, mensagem):
    sock.sendall(mensagem.encode("utf-8"))


def interpretar(linha):
    """
    Recebe uma linha (sem o "\\n") e devolve (comando, argumento)

    O argumento depende do comando:
        NOME, ERRO              -> texto
        JOGAR                   -> inteiro de 1 a 9
        INICIO                  -> (simbolo, adversario)
        TABULEIRO, VEZ, FIM     -> texto já validado
        SAIR, AGUARDE, SAIU     -> None

    Lança ErroProtocolo se a linha for malformada
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
    """Junta os bytes recebidos do socket e devolve uma linha por vez"""

    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def ler_linha(self):
        """
        Devolve a próxima linha (sem o "\\n") ou None se a conexão fechou
        Lança ErroProtocolo se a linha for grande demais ou não for UTF-8
        """
        while b"\n" not in self.buffer and len(self.buffer) <= TAMANHO_MAXIMO:
            dados = self.sock.recv(1024)
            if not dados:
                return None
            self.buffer += dados

        linha, separador, resto = self.buffer.partition(b"\n")
        if len(linha) > TAMANHO_MAXIMO:
            self.buffer = b""
            raise ErroProtocolo("linha grande demais")
        self.buffer = resto

        try:
            texto = linha.decode("utf-8")
        except UnicodeDecodeError:
            raise ErroProtocolo("linha nao esta em UTF-8")
        return texto.rstrip("\r")