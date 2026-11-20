"""
Funções do cliente:

Solicitar o IP e porta do servidor - ok
Estabelece a conexão TCP- ok 
Envia o nome do jogador - ok
Recebe mensagens do servidor em uma thread própria - ok
Permitir que o jogador  envie suas jogadas pelo teclado - ok
Controlar de quem é a vez e encerrar corretamente a conexão - ok
 obs.:  
    - O cliente deve encerrar a conexão quando o servidor enviar a mensagem "FIM" ou "SAIU".
    - O cliente deve encerrar a conexão quando o jogador digitar "sair" no teclado.
"""

import socket 
import protocolo
import interface
import threading

def conectar_servidor(ip, porta): 
    
    """
    Cria o socket TCP e estabelece conexão com o servidor.
    AF_INET: utiliza endereços IPv4.
    SOCK_STREAM: define a comunicação utilizando TCP.

    """

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
       
        cliente.connect((ip, porta)) 
        print("Conectado ao servidor com sucesso!")
        return cliente

    except OSError as erro:
     
        print(f"Não foi possível conectar ao servidor: {erro}")
        cliente.close()
        return None

def  enviar_comando(cliente, comando, argumento=""):
    """ 
    Montagem e envio do comando para o servidor
    
    Utiliza o módulo protocolo para padronizar
    a comunicação entre cliente e servidor.
    """

    mensagem = protocolo.montar(comando, argumento) # Monta a msg no formato def. pelo protocolo.

    protocolo.enviar(cliente, mensagem) # Envia a mensagem pelo socket TCP.

def iniciar_cliente():
   
    """
    Controla o funcionamento do cliente. 
    Solicita os dados e inicia a conexão.
    """

    ip = input("Digite o IP do servidor: ")

    try: 
        porta = int(input("Digite a porta do servidor: "))
    except ValueError:
        print("Certifique-se de digitar um número inteiro.")
        return  

    nome = interface.ler_nome() # Lê o nome do jogador.

    cliente = conectar_servidor(ip, porta) # Estabelece a conexão TCP com o servidor.

    if cliente is None:
        return

    # Controle da comunicação entre threads
    encerrado = threading.Event()
    vez_event = threading.Event()

   
    estado = {
        "simbolo": None,
        "minha_vez": False
    }

    # Inicia a thread responsável por receber as mensagens do servidor.
    thread_recepcao = threading.Thread(
        target=receber_mensagens,
        args=(cliente, estado, encerrado, vez_event)
    )

    try:
     
        enviar_comando(cliente, "NOME", nome)
        print(f"identificação enviada: {nome}")

        # Recepção das mensagens do servidor em uma thread paralela.
        thread_recepcao.start()

        print("Aguardando mensagens do servidor...")

        while not encerrado.is_set():
            
            # Aguarda o sevidor libera a jogada.
            if not vez_event.wait(timeout=0.2):
                continue

            if encerrado.is_set():
                break

            jogada = interface.ler_jogada() # Solicita a posição desejada.

            if jogada is None:
                enviar_comando(cliente, "SAIR")
                encerrado.set()
                break

            vez_event.clear() # Bloaqueia a jogada até que o servidor libere novamente.

            enviar_comando(cliente, "JOGAR", jogada) 

    except KeyboardInterrupt:
        print("\nEncerrando cliente...") # Interrompe o cliente pelo teclado Ctrl+C.

    except Exception as erro:
        print(f"Erro ao enviar identificação: {erro}")

    finally:
        # Sinaliza o encerramento do cliente.
        encerrado.set()
        vez_event.set()
    
    # Encerra a comunicação para liberar a thread de recebimento
    try:
      
        cliente.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass

    cliente.close() # Fecha o socket.

    if thread_recepcao.is_alive(): # Aguarda a finalização da thread de recebimento
        thread_recepcao.join(timeout=1)


def receber_mensagens(cliente, estado, encerrado, vez_event):
    """
    Recebe e interpreta  continuamente as mensagens enviadas pelo servidor.
    Essa função roda em uma thread separada da execução principal
    """

    leitor = protocolo.LeitorDeLinhas(cliente)  # Cria um leitor que identifica mensagens terminadas em quebra de linha

    while not encerrado.is_set():
        try:
            linha = leitor.ler_linha() # Aguada uma mensagem enviada pelo servidor.

            if linha is None: 
                if not encerrado.is_set():

                    interface.mostrar_servidor_offline()

                encerrado.set()
                vez_event.set()
                break

            comando, argumento = protocolo.interpretar(linha) # Separa o comando do argumento da mensagem recebida.

            # Recebe símbolo do jogador e informaçõeas da partida.
            if comando == "INICIO": 

                estado["simbolo"] = argumento[0]
                interface.mostrar(comando, argumento)

            elif comando == "VEZ":

                minha_vez = argumento == estado["simbolo"]

                estado["minha_vez"] = minha_vez 

                interface.mostrar_vez(minha_vez) # Exibe informações do turno.

            # Libera ou bloqueia entrada de jogadas.
                if minha_vez:

                    vez_event.set()

                else:

                    vez_event.clear()


            elif comando == "ERRO":

                interface.mostrar(comando, argumento)
 
                # Nova tentativa se a jogada for inválida e for a vez do jogador.
                if estado["minha_vez"]:
                    vez_event.set()

            else:
                # Encaminha as mensagens para a interface. 
                interface.mostrar(comando, argumento)

            if comando in ("FIM", "SAIU"): # Verfica se acabou a partida ou o adversário saiu do jogo. 

                encerrado.set()
                vez_event.set()
                break

        except (OSError, protocolo.ErroProtocolo) as erro:

            # Trata problemas de comunicação ou msg inválida.
            if not encerrado.is_set():
                print(f"Erro na comunicação: {erro}")

            encerrado.set()
            vez_event.set()
            break


if __name__ == "__main__": #
    iniciar_cliente()

