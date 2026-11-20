"""
Teste de integração
Sobe o servidor, conecta dois clientes e joga uma partida inteira sozinho

Uso, a partir da pasta do projeto:
    python testes/teste_integracao.py
"""

import os
import socket
import subprocess
import sys
import time

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PASTA_PROJETO)

import protocolo

PORTA = 5050


def conectar(nome):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(("127.0.0.1", PORTA))
    protocolo.enviar(sock, protocolo.montar("NOME", nome))
    return sock, protocolo.LeitorDeLinhas(sock)


def esperar(leitor, nome, comando_esperado):
    """Lê a próxima mensagem e confere se é o comando esperado"""
    linha = leitor.ler_linha()
    if linha is None:
        raise Exception(nome + ": o servidor fechou a conexao")
    print(nome + " recebeu: " + linha)

    comando, argumento = protocolo.interpretar(linha)
    if comando != comando_esperado:
        raise Exception(nome + ": esperava " + comando_esperado + " e chegou " + comando)
    return argumento


def conferir(valor, esperado, descricao):
    if valor != esperado:
        raise Exception(descricao + ": esperava " + str(esperado) + " e veio " + str(valor))


def jogar_partida():
    # O primeiro a entrar fica na fila e vira o X
    sock_x, leitor_x = conectar("Pedro")
    esperar(leitor_x, "Pedro", "AGUARDE")

    sock_o, leitor_o = conectar("Leticia")

    simbolo, adversario = esperar(leitor_x, "Pedro", "INICIO")
    conferir(simbolo, "X", "simbolo do Pedro")
    conferir(adversario, "Leticia", "adversario do Pedro")

    simbolo, adversario = esperar(leitor_o, "Leticia", "INICIO")
    conferir(simbolo, "O", "simbolo da Leticia")
    conferir(adversario, "Pedro", "adversario da Leticia")

    for leitor, nome in ((leitor_x, "Pedro"), (leitor_o, "Leticia")):
        conferir(esperar(leitor, nome, "TABULEIRO"), "---------", "tabuleiro inicial")
        conferir(esperar(leitor, nome, "VEZ"), "X", "primeira vez")

    # X joga 1, 2 e 3 e ganha na primeira linha. O joga 4 e 5
    jogadas = [
        (sock_x, "X", 1, "X--------"),
        (sock_o, "O", 4, "X--O-----"),
        (sock_x, "X", 2, "XX-O-----"),
        (sock_o, "O", 5, "XX-OO----"),
        (sock_x, "X", 3, "XXXOO----"),
    ]

    for i in range(len(jogadas)):
        sock, simbolo, casa, tabuleiro_esperado = jogadas[i]
        print("\n" + simbolo + " joga na casa " + str(casa))
        protocolo.enviar(sock, protocolo.montar("JOGAR", casa))

        for leitor, nome in ((leitor_x, "Pedro"), (leitor_o, "Leticia")):
            conferir(esperar(leitor, nome, "TABULEIRO"), tabuleiro_esperado, "tabuleiro")
            if i < len(jogadas) - 1:
                proximo = "O" if simbolo == "X" else "X"
                conferir(esperar(leitor, nome, "VEZ"), proximo, "vez")

    print()
    conferir(esperar(leitor_x, "Pedro", "FIM"), "VITORIA", "resultado do Pedro")
    conferir(esperar(leitor_o, "Leticia", "FIM"), "DERROTA", "resultado da Leticia")

    sock_x.close()
    sock_o.close()


def main():
    caminho_servidor = os.path.join(PASTA_PROJETO, "servidor.py")
    servidor = subprocess.Popen(
        [sys.executable, caminho_servidor, str(PORTA)],
        stdout=subprocess.DEVNULL,
    )
    time.sleep(1)  # tempo para o servidor comecar a ouvir

    try:
        jogar_partida()
        print("\nTeste passou: a partida foi jogada do inicio ao fim")
        resultado = 0
    except Exception as erro:
        print("\nTeste falhou: " + str(erro))
        resultado = 1
    finally:
        servidor.terminate()
        servidor.wait()

    sys.exit(resultado)


if __name__ == "__main__":
    main()
