"""
Servidor do jogo da velha em rede (TCP + threads)

Responsabilidades deste módulo (Pessoa 1):
    - criar o socket do servidor, fazer bind, listen e aceitar clientes em loop
    - criar uma thread para cada cliente
    - ler as mensagens, interpretar os comandos (NOME, JOGAR, SAIR) e
      entregar ao módulo de partidas (partida.GerenciadorPartidas)
    - responder ERRO para comando desconhecido ou malformado
    - encerrar as conexões com limpeza e tratar erros de rede

Este módulo não conhece as regras do jogo nem monta partidas: isso é do
partida.py (e do jogo.py). Ele só cuida de rede e de despachar comandos

Uso:
    python servidor.py [porta]        (porta padrão: 5000)
"""

import socket
import sys
import threading
import time

import protocolo
from partida import GerenciadorPartidas

HOST = "0.0.0.0"
PORTA_PADRAO = 5000

# Mensagem que o protocolo.py usa quando a linha passa de TAMANHO_MAXIMO
LINHA_GRANDE = "linha grande demais"


def log(texto):
    print(texto, flush=True)


def enviar_erro(sock, gerenciador, motivo):
    """
    Envia ERRO <motivo> ao cliente. Devolve False se a conexão caiu

    O envio é feito com o lock do gerenciador porque o partida.py também
    escreve nesse socket (ex.: quando o adversário joga). Sem o lock, duas
    threads poderiam misturar os bytes de duas mensagens
    """
    try:
        with gerenciador.lock:
            protocolo.enviar(sock, protocolo.montar("ERRO", motivo))
        return True
    except OSError:
        return False


def encerrar_cliente(sock, gerenciador, endereco):
    """Tira o cliente da fila/partida e fecha o socket, sem nunca levantar erro"""
    try:
        gerenciador.desconectar(sock)
    except OSError as erro:
        # O adversário já tinha caído ao tentar avisá-lo com SAIU
        log("[!] erro de rede ao desconectar " + str(endereco) + ": " + str(erro))
    except Exception as erro:
        log("[!] falha inesperada ao desconectar " + str(endereco) + ": " + repr(erro))

    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    sock.close()
    log("[-] conexao encerrada: " + str(endereco))


def atender_cliente(sock, endereco, gerenciador):
    """Roda em uma thread própria: lê e despacha as mensagens de um cliente"""
    log("[+] nova conexao: " + str(endereco))
    leitor = protocolo.LeitorDeLinhas(sock)

    try:
        while True:
            # 1) ler uma linha completa (o leitor cuida do buffer)
            try:
                linha = leitor.ler_linha()
            except protocolo.ErroProtocolo as erro:
                enviar_erro(sock, gerenciador, str(erro))
                if str(erro) == LINHA_GRANDE:
                    break  # README do protocolo: encerrar em vez de continuar lendo
                continue

            if linha is None:  # o cliente fechou a conexão
                break

            # 2) interpretar. Comando desconhecido ou malformado vira ERRO
            try:
                comando, _ = protocolo.interpretar(linha)
            except protocolo.ErroProtocolo as erro:
                if not enviar_erro(sock, gerenciador, str(erro)):
                    break
                continue

            # 3) SAIR: o cliente quer ir embora. O finally cuida da limpeza
            if comando == "SAIR":
                break

            # 4) NOME e JOGAR (e o resto) vão para o módulo de partidas
            try:
                gerenciador.receber(sock, linha)
            except ValueError as erro:
                if not enviar_erro(sock, gerenciador, str(erro)):
                    break
            except OSError as erro:
                # Quase sempre é o ADVERSÁRIO que caiu durante o envio.
                # A thread dele vai notar e chamar desconectar. Se o problema
                # for neste cliente, a próxima leitura falha e o laço acaba
                log("[!] erro de rede ao despachar para " + str(endereco) + ": " + str(erro))

    except OSError as erro:
        log("[!] erro de rede com " + str(endereco) + ": " + str(erro))
    except Exception as erro:
        log("[!] erro inesperado com " + str(endereco) + ": " + repr(erro))
    finally:
        encerrar_cliente(sock, gerenciador, endereco)


def iniciar_servidor(porta, gerenciador=None):
    """Cria o socket, aceita clientes em loop e abre uma thread por cliente"""
    if gerenciador is None:
        gerenciador = GerenciadorPartidas()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, porta))
    servidor.listen()
    log("Servidor ouvindo na porta " + str(porta) + ". Ctrl+C para encerrar")

    try:
        while True:
            try:
                sock, endereco = servidor.accept()
            except OSError as erro:
                # Falha passageira no accept (ex.: conexão abortada): segue
                log("[!] erro no accept: " + str(erro))
                time.sleep(0.1)
                continue

            thread = threading.Thread(
                target=atender_cliente,
                args=(sock, endereco, gerenciador),
                daemon=True,
            )
            thread.start()
    except KeyboardInterrupt:
        log("\nEncerrando servidor...")
    finally:
        servidor.close()


def ler_porta(argumentos):
    if len(argumentos) < 2:
        return PORTA_PADRAO
    try:
        porta = int(argumentos[1])
    except ValueError:
        porta = 0
    if not 1 <= porta <= 65535:
        print("Uso: python servidor.py [porta]  (porta de 1 a 65535)")
        sys.exit(1)
    return porta


if __name__ == "__main__":
    porta = ler_porta(sys.argv)
    try:
        iniciar_servidor(porta)
    except OSError as erro:
        print("Nao foi possivel iniciar o servidor na porta " + str(porta) + ": " + str(erro))
        sys.exit(1)