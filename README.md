# Jogo da Velha em Rede

**Universidade Federal de Alagoas (UFAL)**
**Disciplina:** Redes de Computadores, 2026.1
**Equipe:** Arthur Carvalho, Geovana, Ana Letícia, Otávio Fernandes e Pedro Neves

> **Documento em construção.** Este README descreve apenas o que já
> existe no repositório e será atualizado a cada entrega.

Jogo da velha para dois jogadores em rede, em Python, usando sockets TCP
e threads.

## Requisitos

- Python 3 (sem bibliotecas externas)

## Arquivos

| Arquivo | Responsável | Papel |
|---|---|---|
| `protocolo.py` | Pedro | Monta, interpreta e lê as mensagens da rede |
| `interface.py` | Pedro | Entrada e saída no terminal do jogador |

## Mensagens do protocolo

Cada mensagem é uma linha de texto em UTF-8 terminada em `\n`, com no
máximo 256 bytes: o comando, um espaço e o argumento (quando existe).

| Sentido | Mensagem | Significado |
|---|---|---|
| cliente → servidor | `NOME <nome>` | Identifica o jogador |
| cliente → servidor | `JOGAR <1-9>` | Marca a casa indicada |
| cliente → servidor | `SAIR` | Sai do jogo |
| servidor → cliente | `AGUARDE` | Está esperando adversário |
| servidor → cliente | `INICIO <X\|O> <adversário>` | A partida começou; símbolo de quem recebe |
| servidor → cliente | `TABULEIRO <9 casas>` | Casas 1 a 9: `X`, `O` ou `-` (vazia) |
| servidor → cliente | `VEZ <X\|O>` | De quem é a vez |
| servidor → cliente | `FIM <VITORIA\|DERROTA\|EMPATE>` | Resultado para quem recebe |
| servidor → cliente | `SAIU` | O adversário desconectou |
| servidor → cliente | `ERRO <motivo>` | A última mensagem foi rejeitada |

Numeração das casas:

```
 1 | 2 | 3
---+---+---
 4 | 5 | 6
---+---+---
 7 | 8 | 9
```

## Como usar o `protocolo.py`

```python
import protocolo

protocolo.enviar(sock, protocolo.montar("JOGAR", 5))

leitor = protocolo.LeitorDeLinhas(sock)
while True:
    try:
        linha = leitor.ler_linha()
        if linha is None:           
            break
        comando, argumento = protocolo.interpretar(linha)
    except protocolo.ErroProtocolo as erro:
        protocolo.enviar(sock, protocolo.montar("ERRO", str(erro)))
        continue
```

A função `montar` recebe o comando e, quando houver, o argumento. No
`INICIO`, o argumento é o símbolo e o nome juntos:
`montar("INICIO", "X Ana")`.

O argumento devolvido por `interpretar` já vem validado:

| Comando | Argumento |
|---|---|
| `NOME`, `ERRO` | texto |
| `JOGAR` | inteiro de 1 a 9 |
| `INICIO` | tupla `(símbolo, adversário)` |
| `TABULEIRO`, `VEZ`, `FIM` | texto |
| `SAIR`, `AGUARDE`, `SAIU` | `None` |

Se o erro for "linha grande demais", encerre a conexão em vez de
continuar lendo.

## Como usar o `interface.py`

```python
import interface

nome = interface.ler_nome()
casa = interface.ler_jogada()       

comando, argumento = protocolo.interpretar(linha)
interface.mostrar(comando, argumento)
```

A função `mostrar` trata `AGUARDE`, `INICIO`, `TABULEIRO`, `FIM`, `SAIU`
e `ERRO`. O `VEZ` fica de fora porque depende do símbolo do jogador:
use `mostrar_vez(True)` ou `mostrar_vez(False)`. Para queda de conexão,
há `mostrar_servidor_offline()`.