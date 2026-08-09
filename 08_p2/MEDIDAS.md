# MEDIDAS DA P2 — os cinco numeros, com a plataforma ao lado

> Laboratorio experimental. Nada aqui e norma. Este arquivo e o
> **carimbo vigente** das cinco receitas da P2. Criado na missao
> **SSC+ P1-A.9, ordem 2**, depois que a ordem 1 fixou o fim de linha.
>
> Ele existe porque o `CLAUDE.md` passou a exigir que **todo numero de
> suite ou de medicao venha com a plataforma na mesma linha**. Antes
> desta missao os cinco numeros circulavam sem ela — e um deles saiu de
> um estado de arvore que **nao existe em checkout limpo**.

## PLATAFORMA DESTA MEDICAO

| Campo | Valor |
|---|---|
| Interpretador | **Python 3.11.9** |
| `pytest` | **9.1.1** |
| `core.autocrlf` da estacao | **true** — e **nao importa mais**: o fim de linha dos insumos esta pinado em `05_p0/ssc_p0/.gitattributes` (`* text eol=crlf`) |
| Usuario da estacao | `lucas` — **nao entra em nenhum destes numeros** |
| Commit | ordem 2 da **P1-A.9** |
| Instrumento | `08_p2/medidor.py --todas` |

**Reproduzir e um comando:**

    python 08_p2/medidor.py --todas

## OS CINCO NUMEROS VIGENTES

| receita | razao | residual (B) | alternativo (B) | poupanca (B) | confere? |
|---|---|---|---|---|---|
| `p21` | **8,776** | 872 | 7 653 | 6 781 | **CONFERE** |
| `p22-a` | **19,907** | 773 | 15 388 | 14 615 | **CONFERE** |
| `p22-b` | **2,766** | 504 | 1 394 | 890 | **CONFERE** |
| `p22-c` | **6,737** | 662 | 4 460 | 3 798 | **CONFERE** |
| `p22-c-repeticao` | **6,464** | 690 | 4 460 | 3 770 | **CONFERE** |

**5 receitas, 0 divergentes.** Antes desta missao eram **4 CONFERE e 1
DIVERGE** sob `autocrlf=true`, e **3 CONFERE e 2 DIVERGE** sob
`autocrlf=false` — a mesma arvore, dois resultados.

## O QUE MUDOU CONTRA O PUBLICADO — uma receita, e so uma

**`p22-a` foi recarimbada. As outras quatro nao mudaram um digito.**

| Campo | Publicado (2026-08-03) | Vigente | Delta |
|---|---|---|---|
| razao | **19,558** | **19,907** | +0,349 |
| `execution.py` recontado | 13 508 B | **13 778 B** | **+270 B** |
| alternativo total | 15 118 B | **15 388 B** | +270 B |
| poupanca | 14 345 B | **14 615 B** | +270 B |
| residual | 773 B | **773 B** | **0** |
| saida da assinatura | 547 B | **547 B** | **0** |

### Por que mudou, e por que o valor novo e o certo

O `+270` **nao e ruido nem correcao de formula**: sao exatamente as
**270 linhas** de `05_p0/ssc_p0/execution.py`. O medidor reconta o
arquivo lendo o disco em binario (`open(caminho, "rb")`), de modo que um
byte `\r` por linha entra na conta.

O valor de 2026-08-03 saiu de uma **arvore de trabalho MISTA**:
`execution.py` lido em **LF** enquanto `estados.py` era lido em **CRLF**.
A P1-A.8 mediu, por exaustao dos dois estados limpos possiveis, que esse
arranjo **nao existe em nenhum checkout limpo** — logo o numero publicado
nao era reproduzivel em estacao nenhuma, nem naquela.

A ordem 1 da P1-A.9 fixou **CRLF** para os insumos, por medicao e nao por
gosto: dos dois estados limpos, CRLF reproduzia **4 de 5** receitas
contra **3 de 5** do LF. Com o pino, `execution.py` passa a 13 778 B em
qualquer estacao, e a razao de `p22-a` a **19,907**.

**A alternativa que reproduziria as cinco foi medida e recusada** — pinar
`execution.py` em LF e `estados.py` em CRLF da `5 receitas, 0
divergentes` **sem** recarimbar nada. Foi recusada porque e a propria
arvore mista, promovida de acidente a regra. O registro da decisao esta
em `06_p1a/99_decisao-p1a9.md` §1.2, com a conta ao lado, para que a
escolha possa ser contestada com dados.

## O QUE **NAO** FOI RECARIMBADO, e por que

| Item | Situacao |
|---|---|
| `08_p2/99_registro-p22.md` e `99_registro-p24.md` | **intocados.** Sao registros **datados** de missoes encerradas, e este acervo nao reescreve registro: carimba o superado e deixa o original legivel. Eles seguem citando `19,558`, que e o que se mediu **naquele dia, naquela arvore** |
| Coluna *"razao com a MESMA resposta nos dois lados"* do `README` (`18,475` para `p22-a`) | **NAO recarimbada, e declarado.** Ela aparece **uma unica vez em todo o acervo** e **nenhum instrumento versionado a calcula** — nao ha de onde remedi-la sem refazer a analise que a produziu. Fica marcada no README como nao recarimbada |
| A corrida em si | **nada foi refeito.** `sessao_id`, `attempt_id`, `executor`, o prompt (226 B) e a resposta do canal alternativo (1 384 B) seguem identicos. **Nenhum provedor foi invocado**, custo variavel **zero** |

O recarimbo foi feito **no proprio arquivo publicado**, e nao numa copia
nova, por exigencia de um guarda do acervo:
`test_toda_medicao_publicada_TEM_receita` exige que **toda** medicao
publicada tenha receita que a produza. Um arquivo novo deixaria o
original **orfao** — publicado sem receita —, que e exatamente o
**achado C** que aquele guarda existe para impedir. O valor antigo nao se
perdeu: esta dentro do proprio JSON, no bloco `recarimbo`, campo a campo.

## O QUE ESTES NUMEROS **NAO** DIZEM

- **nao dizem que a tese central esta medida.** Continua sem medicao em
  token; estes sao bytes de fronteira;
- **nao dizem que a cobertura e total.** A classe (b) segue com **17,3 %**
  recontado do repositorio e o resto em testemunho — o `MAJOR P1A4-4`
  continua **aberto**, e esta missao **nao o fechou**;
- **nao dizem que a repeticao e reproduzivel.** O lab da corrida
  `p22-c-repeticao` foi **destruido** na P1-A.6 e procurado em cinco
  lugares na P1-A.7 sem ser achado. O que confere aqui e a **receita**
  contra o **publicado**, nao contra o lab;
- **nao certificam nada.** Quem recarimbou foi quem mediu, e
  `QUEM CORRIGE NAO CERTIFICA`.
