# A escolha de ferramenta do modelo, e o ponteiro que tira o terminal do cardapio — 2026-08-12

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica.

## O que a quarta recusa do dia ensinou

Com o `--add-dir` do registro 103 aplicado (confirmado no argv publico do
recibo `fluxo-20260812T132848206296Z-recusado.json`), o fluxo real passou
**quatro etapas** — Kimi, Codex (plano e implementacao), Claude — e caiu
de novo no julgamento do Google: `falha-contrato`, resposta vazia.

A bisseccao por sonda mediu que **nao e limiar de tamanho**:

| Sonda | Arquivo | Pedido | Resultado |
|---|---|---|---|
| 100/200/256/300/350 KB | trivial (*"responda com a linha"*) | leitura nativa, resposta correta | |
| 400 KB | trivial | **tambem passou** | |
| 400 KB (sonda F) | **julgamento transversal** | `command` auto-negada, `SUCCESS` **vazio** | |

O modelo escolhe a ferramenta pela **complexidade do pedido**: tarefa
analitica sobre arquivo grande o seduz para o terminal (grep/cat), que o
headless auto-nega, e o turno morre vazio. O modo de falha e
**probabilistico por natureza** — a mesma escala passa com pedido
trivial e cai com pedido de julgamento.

## A mitigacao, e o que ela e

O ponteiro generico do contrato semantico
(`provedor_assinatura.invocar`) passa a dizer, alem do que ja dizia:
*"use somente a leitura nativa de arquivos; comandos de terminal estao
bloqueados neste modo e deixariam a resposta vazia; se alguma ferramenta
for negada, ainda assim escreva a resposta do contrato com o que tiver
lido"*.

**Sonda G**, o caso exato que falhava (julgamento sobre 400 KB, argv de
producao): contrato completo de volta — `SSC_STATUS: SUCESSO`, resposta
com a contagem correta do conteudo (8204 funcoes) e
`SSC_JULGAMENTO: APROVADO`. E a resposta veio com `SSC_RESPOSTA:`
**inline**: sem a correcao do registro 104 este sucesso teria sido
recusado pelo parser.

**Isto e mitigacao por instrucao, nao garantia mecanica** — declarado.
O modelo pode ainda ignorar a instrucao; quando ignorar, o fail-closed
recusa como sempre. A alternativa mecanica (allow-rule de `command` no
settings do agy) amplia a contencao ratificada e fica com o Fundador,
junto com a decisao do `--mode plan` inerte (registro 103).

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).

Custo das sondas desta frente: 8 turnos reais do agy, o maior com ~29k
tokens totais reportados no `usage` do proprio CLI.
