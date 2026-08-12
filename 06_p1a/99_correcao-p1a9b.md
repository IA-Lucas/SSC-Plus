# Registro de correcao — P1A9-b (2026-08-12)

> Missao de correcao, experimental e sem autoridade. **Quem corrige nao
> certifica**: o achado `P1A9-b` permanece ABERTO ate revisor
> independente. Familia de origem: **(F)**.

## O achado, como a P1-A.9 o deixou

A regra dos **quatro campos de plataforma** (interpretador, `pytest`,
`core.autocrlf`, usuario da estacao) era regra de processo e **nenhum
teste a impunha** — afirmar a propriedade sem exercer a interface, a
familia do MAJOR #3, dentro da propria regra que a denuncia.

## A correcao

O instrumento canonico (`scripts/verificar.py`) ja emitia a linha
`plataforma:` com os quatro campos — emissao sem guarda. O guarda novo e
`06_p1a/tests/test_plataforma_quatro_campos_p1a9b.py`, e ele **exerce a
porta da operacao**: roda `python scripts/verificar.py --rapido` em
subprocesso, num esqueleto descartavel com suites triviais, usando os
bytes REAIS do script no momento do teste. Exige:

1. a linha `plataforma:` unica, com os **quatro campos nomeados e com
   valor**;
2. a linha **antes** de qualquer numero de suite — plataforma emoldura
   numero, nunca vem depois;
3. dois valores **medidos, nao afirmados**: o interpretador tem de ser o
   Python que executou; o usuario tem de ser o da estacao (comparado por
   `getpass`, nunca escrito literal — os guardas `ZeroPii` derivam o
   alvo dele).

## Reversao vermelha — a lista classificada membro a membro

Corolario da varredura de listas (P1-A.3.9): lista se classifica mutando
**cada membro isoladamente**. Medido em clone descartavel (arvore viva
nunca mutada):

| Mutante em `verificar.py` | Resultado do guarda |
|---|---|
| linha de plataforma inteira removida | **3 failed** |
| sem `interpretador=` | **2 failed** |
| sem `pytest=` | **1 failed** |
| sem `core.autocrlf=` | **1 failed** |
| sem `usuario=` | **2 failed** |
| controle pos-restauracao | 4 passed, 4 subtests |

**Todos os quatro membros prendem: lista PRESA.**

## O que o guarda NAO cobre, declarado

- **numero publicado em prosa** (missao, atestado, tabela) continua sem
  guarda — cobrir prosa exigiria heuristica de varredura, e o guarda
  afirmaria mais do que mede. O criterio de publicacao segue sendo
  processo, agora com o instrumento vigiado;
- o esqueleto tem suites triviais: a contagem real de testes nao e
  objeto do guarda, so a moldura de plataforma;
- o esqueleto nao e repositorio git: prova a PRESENCA do campo
  `core.autocrlf`, com valor "nao definido" — o valor real desta arvore
  e medido pelas corridas reais, nao pelo esqueleto.

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, declarado por descricao;
o literal reprovaria nos guardas `ZeroPii`, como este proprio ciclo
mediu em `99_correcao-p1a9a.md`).

Suite completa apos a correcao, medida e nao somada:
`python scripts/verificar.py --rapido` → **OK**, P0 com **347 testes** e
P1-A/P2 com **991 testes** (o instrumento agora carrega a plataforma na
mesma corrida que produz esses numeros).
