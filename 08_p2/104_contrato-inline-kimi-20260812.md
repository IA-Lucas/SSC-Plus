# O marcador que a extracao comia — contrato semantico inline (2026-08-12)

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica.

## A cadeia de tres recusas do dia, cada uma com causa propria

| Recibo | Recusa | Causa medida |
|---|---|---|
| `fluxo-20260812T125405...` | contextualizar, `falha-contrato` | **mutacao concorrente**: a propria sessao commitou registros na arvore DURANTE a invocacao, e a vigilancia fail-closed invalidou a resposta — deteccao correta, atribuicao ao verdadeiro autor feita aqui. Licao operacional: **arvore quieta durante fluxo real** |
| `fluxo-20260812T130953...` | `SSC_CONTEXTO deve aparecer exatamente uma vez; observado=[]` | **assimetria do parser**, abaixo |
| sonda isolada (mesma tarde) | `sucesso sem SSC_RESPOSTA` | a mesma assimetria, capturada com a transcricao integral |

## A causa raiz da segunda e da terceira

O contrato semantico instrui: *"responda com a primeira linha exata
`SSC_STATUS: SUCESSO`, depois `SSC_RESPOSTA:` e a resposta"* — texto que
permite duas leituras: marcador sozinho na linha, ou
`SSC_RESPOSTA: <resposta>` inline. O `kimi-code/k3` real usou a inline.
O parser aceitava **so a primeira** — enquanto o ramo de `SSC_MOTIVO`,
no mesmo modulo, **ja aceitava as duas**. A recusa da extracao levava
junto o `SSC_CONTEXTO: PRONTO`, presente e limpo na ultima linha da
resposta real.

## A correcao, e a prova

1. `normalizar_resultado_semantico` espelha o ramo de MOTIVO:
   `SSC_RESPOSTA:` sozinho ou seguido de texto, fail-closed preservado
   (status exato e unico; resposta vazia continua recusada);
2. o prompt do fluxo ganha uma frase unica de formato: *"todo marcador
   SSC_* em linha propria, sem negrito, sem crase, sem bloco de
   codigo"* — endurece o lado do modelo sem afrouxar o do parser;
3. teste novo com a **transcricao verbatim** do kimi real
   (`test_resposta_na_mesma_linha_do_marcador_e_aceita`), exigindo que o
   marcador de etapa sobreviva a extracao em linha propria; e o teste de
   que marcador sozinho sem resposta **continua recusado**.

**Reversao vermelha, medida em clone descartavel** (arvore viva nunca
mutada): parser revertido a exigir marcador sozinho → **1 failed** (o
teste da transcricao real); restaurado → 54 passed, 29 subtests.

**Suite completa** apos a correcao: `verificar.py --rapido` → **OK**.

## O que NAO esta coberto, declarado

- o modelo pode ainda violar o formato de outros jeitos (negrito no
  marcador, marcador dentro de bloco de codigo): a frase de formato
  reduz, nao elimina; o parser continua estrito nesses casos e a recusa
  e o comportamento desenhado;
- a recusa de 13:09 nao teve o conteudo persistido (redacao): a causa e
  atribuida por mecanismo reproduzido em sonda, nao por leitura daquela
  resposta especifica.

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
