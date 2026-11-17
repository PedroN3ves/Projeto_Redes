"""
Interface de terminal do jogo da velha.

Este módulo só usa print() e input(). Ele não conhece sockets:
quem deve ligar a interface à rede é o cliente.py.
"""


def desenhar_tabuleiro(casas):
    """
    Desenha o tabuleiro a partir do texto de 9 casas do protocolo
    (X, O ou - para vazia). Casas vazias mostram o seu número,
    para o jogador saber o que digitar.
    """
    visiveis = []
    for i in range(9):
        if casas[i] == "-":
            visiveis.append(str(i + 1))
        else:
            visiveis.append(casas[i])

    print()
    print(" " + visiveis[0] + " | " + visiveis[1] + " | " + visiveis[2])
    print("---+---+---")
    print(" " + visiveis[3] + " | " + visiveis[4] + " | " + visiveis[5])
    print("---+---+---")
    print(" " + visiveis[6] + " | " + visiveis[7] + " | " + visiveis[8])
    print()


def ler_jogada():
    """
    Pede uma jogada até o jogador digitar um número de 1 a 9.
    Devolve o número, ou None se o jogador digitar "sair".
    """
    while True:
        texto = input("Sua jogada (1 a 9, ou 'sair'): ").strip().lower()
        if texto == "sair":
            return None
        if texto in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            return int(texto)
        print("Jogada invalida. Digite um numero de 1 a 9.")


def ler_nome():
    """Pede o nome até o jogador digitar algo."""
    while True:
        nome = input("Seu nome: ").strip()
        if nome != "":
            return nome
        print("O nome nao pode ficar vazio.")


def mostrar_aguarde():
    print("Aguardando um adversario...")


def mostrar_inicio(simbolo, adversario):
    print("Partida iniciada contra " + adversario + ". Voce e o " + simbolo + ".")


def mostrar_vez(minha_vez):
    if minha_vez:
        print("E a sua vez.")
    else:
        print("Vez do adversario. Aguarde...")


def mostrar_fim(resultado):
    if resultado == "VITORIA":
        print("Voce venceu!")
    elif resultado == "DERROTA":
        print("Voce perdeu.")
    else:
        print("Deu empate.")


def mostrar_adversario_saiu():
    print("O adversario saiu. A partida foi encerrada.")


def mostrar_erro(motivo):
    print("Erro: " + motivo)


def mostrar_servidor_offline():
    print("Nao foi possivel falar com o servidor. Conexao encerrada.")