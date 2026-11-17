"""
Terminal do jogador
Só usa print() e input(), não conhece sockets
"""


def desenhar_tabuleiro(casas):
    """Casas vazias mostram o seu número, para o jogador saber o que digitar"""
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


def ler_nome():
    while True:
        nome = input("Seu nome: ").strip()
        if nome != "":
            return nome
        print("O nome nao pode ficar vazio.")


def ler_jogada():
    """Devolve um número de 1 a 9, ou None se o jogador digitar 'sair'"""
    while True:
        texto = input("Sua jogada (1 a 9, ou 'sair'): ").strip().lower()
        if texto == "sair":
            return None
        if texto in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            return int(texto)
        print("Jogada invalida. Digite um numero de 1 a 9")


def mostrar(comando, argumento=None):
    """Mostra o aviso de uma mensagem do servidor, já interpretada"""
    if comando == "AGUARDE":
        print("Aguardando um adversario...")
    elif comando == "INICIO":
        simbolo, adversario = argumento
        print("Partida iniciada contra " + adversario + ". Voce e o " + simbolo + ".")
    elif comando == "TABULEIRO":
        desenhar_tabuleiro(argumento)
    elif comando == "FIM":
        if argumento == "VITORIA":
            print("Voce venceu!")
        elif argumento == "DERROTA":
            print("Voce perdeu.")
        else:
            print("Deu empate.")
    elif comando == "SAIU":
        print("O adversario saiu. A partida foi encerrada")
    elif comando == "ERRO":
        print("Erro: " + argumento)


def mostrar_vez(minha_vez):
    if minha_vez:
        print("E a sua vez.")
    else:
        print("Vez do adversario. Aguarde...")


def mostrar_servidor_offline():
    print("Nao foi possivel falar com o servidor. Conexao encerrada")