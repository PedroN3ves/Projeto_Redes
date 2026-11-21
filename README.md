Jogo da Velha em Rede

Universidade Federal de Alagoas (UFAL)
Disciplina: Redes de Computadores, 2026.1
Equipe: Ana Letícia, Arthur Carvalho, Geovana Maria, Otávio Fernandes e Pedro Neves

Jogo da velha para dois jogadores em computadores diferentes, em Python, usando sockets TCP e threads. Um servidor recebe os jogadores, forma os pares automaticamente e controla cada partida. Vários pares podem jogar ao mesmo tempo.

Como rodar

Baixe o projeto e entre na pasta:

git clone https://github.com/PedroN3ves/Projeto_Redes.git
cd Projeto_Redes
1. Iniciar o servidor

Em um terminal, dentro da pasta do projeto:

python servidor.py

Deve aparecer Servidor ouvindo na porta 5000. Ctrl+C para encerrar. Deixe esse terminal aberto: ele mostra as conexões que chegam e saem.

Para usar outra porta, passe o número depois do nome do arquivo, por exemplo python servidor.py 6000. Para encerrar o servidor, use Ctrl+C.

2. Iniciar os dois jogadores

Abra dois novos terminais (um para cada jogador), entre na pasta do projeto em cada um e rode:

python cliente.py

O programa pergunta, nesta ordem:

Pergunta	O que digitar
Digite o IP do servidor:	o IP do computador que roda o servidor (veja abaixo)
Digite a porta do servidor:	5000 (ou a porta que você passou ao servidor)
Seu nome:	o nome que aparece para o adversário

O primeiro jogador a entrar vê Aguardando um adversario.... Quando o segundo entra, a partida começa sozinha.

Tudo no mesmo computador (para testar)

Use três terminais: um com o servidor e dois com cliente.py. Em cada cliente, digite o IP 127.0.0.1.

Em dois ou mais computadores
No computador do servidor, descubra o IP na rede:
Windows: ipconfig e procure o Endereço IPv4 (algo como 192.168.0.12)
Linux: hostname -I
macOS: ipconfig getifaddr en0
Inicie o servidor nesse computador (python servidor.py).
Nos outros computadores, rode python cliente.py e digite esse IP.

O servidor aceita conexões de qualquer computador da rede (0.0.0.0). Se os clientes não conseguirem conectar, o motivo mais comum é o firewall do computador do servidor. No Windows, libere a porta 5000 abrindo o PowerShell como administrador e rodando:

netsh advfirewall firewall add rule name="Jogo da Velha" dir=in action=allow protocol=TCP localport=5000

Ou, na janela de aviso do Windows que aparece na primeira execução do servidor, clique em Permitir acesso.

Como jogar

O X começa. As casas do tabuleiro são numeradas de 1 a 9, e as casas vazias mostram o próprio número:

 1 | 2 | 3
---+---+---
 4 | 5 | 6
---+---+---
 7 | 8 | 9
Quando for a sua vez, aparece Sua jogada (1 a 9, ou 'sair'):. Digite o número da casa e aperte Enter.
Se for a vez do adversário, aparece Vez do adversario. Aguarde....
Ganha quem completar uma linha, uma coluna ou uma diagonal. Se o tabuleiro encher sem vencedor, é empate.
Digite sair na sua vez para abandonar a partida. O adversário é avisado.
A partida termina com Voce venceu!, Voce perdeu. ou Deu empate., e o programa do cliente encerra. Para jogar de novo, rode python cliente.py outra vez (o servidor continua ligado).

Se você digitar uma jogada inválida (casa ocupada, número fora de 1 a 9), o jogo avisa e pede de novo, sem perder a vez.

Testes

Na pasta do projeto:

python -m unittest discover -s testes -p "test_jogo.py" -v

Roda os 23 testes das regras do jogo (as 8 combinações vencedoras, empate e jogadas inválidas). No fim deve aparecer OK.

python testes/teste_integracao.py

Sobe um servidor, conecta dois clientes e joga uma partida inteira sozinho, mostrando as mensagens trocadas. No fim deve aparecer Teste passou: a partida foi jogada do inicio ao fim. Esse teste usa a porta 5050.

Como funciona

O projeto usa o modelo cliente-servidor sobre TCP, com as funções primitivas do módulo socket (socket, bind, listen, accept, connect, sendall, recv). Não usa WebSocket nem bibliotecas externas.

Servidor: a thread principal aceita conexões (accept) e abre uma thread para cada cliente conectado. Cada thread lê as mensagens do seu cliente e entrega ao módulo de partidas.
Partidas: uma fila de espera junta os jogadores em pares e cria a partida. Fila e partidas são compartilhadas entre as threads e ficam protegidas por Lock, então várias partidas acontecem ao mesmo tempo sem se misturar. O servidor é a autoridade do jogo: valida cada jogada, controla de quem é a vez e decide o resultado.
Cliente: a thread principal lê o teclado (input) e envia as jogadas; uma segunda thread fica recebendo as mensagens do servidor e atualizando a tela (print). A jogada só é pedida quando for a vez do jogador.
Desconexão: se um jogador sai ou cai no meio da partida, o outro recebe SAIU e a partida é encerrada. O servidor continua funcionando.
Arquivos
Arquivo	Papel
servidor.py	Socket do servidor, uma thread por cliente, despacha os comandos
partida.py	Fila de espera, pareamento, partidas simultâneas, turnos e desconexão
jogo.py	Regras do jogo: tabuleiro, validação, vitória e empate
cliente.py	Conexão ao servidor, thread de recepção e entrada do teclado
protocolo.py	Monta, interpreta e lê as mensagens da rede
interface.py	Entrada e saída no terminal do jogador
testes/test_jogo.py	Testes unitários das regras do jogo
testes/teste_integracao.py	Teste automático com servidor e dois clientes
Mensagens do protocolo

Cada mensagem é uma linha de texto em UTF-8 terminada em \n, com no máximo 256 bytes: o comando, um espaço e o argumento (quando existe).

Sentido	Mensagem	Significado
cliente → servidor	NOME <nome>	Identifica o jogador
cliente → servidor	JOGAR <1-9>	Marca a casa indicada
cliente → servidor	SAIR	Sai do jogo
servidor → cliente	AGUARDE	Está esperando adversário
servidor → cliente	INICIO <X|O> <adversário>	A partida começou; símbolo de quem recebe
servidor → cliente	TABULEIRO <9 casas>	Casas 1 a 9: X, O ou - (vazia)
servidor → cliente	VEZ <X|O>	De quem é a vez
servidor → cliente	FIM <VITORIA|DERROTA|EMPATE>	Resultado para quem recebe
servidor → cliente	SAIU	O adversário desconectou
servidor → cliente	ERRO <motivo>	A última mensagem foi rejeitada

Exemplo de uma partida (a partir do NOME dos dois jogadores):

Ana   → servidor: NOME Ana
servidor → Ana:   AGUARDE
Bia   → servidor: NOME Bia
servidor → Ana:   INICIO X Bia          servidor → Bia: INICIO O Ana
servidor → ambos: TABULEIRO ---------
servidor → ambos: VEZ X
Ana   → servidor: JOGAR 5
servidor → ambos: TABULEIRO ----X----
servidor → ambos: VEZ O
...
servidor → Ana:   FIM VITORIA           servidor → Bia: FIM DERROTA
Problemas comuns
Problema	O que fazer
Não foi possível conectar ao servidor	Confira se o servidor está rodando, se o IP e a porta estão certos e se o firewall do computador do servidor libera a porta
Nao foi possivel iniciar o servidor na porta ...	A porta já está em uso (talvez outro servidor aberto). Feche o outro ou use outra porta: python servidor.py 6000
Certifique-se de digitar um número inteiro	A porta deve ser um número, como 5000
O cliente fica em Aguardando um adversario...	É normal: falta o segundo jogador entrar
python não é reconhecido (Windows)	Use py no lugar, ou reinstale o Python marcando Add Python to PATH