# P1-A.10 — revisao independente das correcoes de 2026-08-11/12

> Registro da missao que despachou a revisao. Quem corrige nao
> certifica; os fechamentos abaixo sao **do revisor**, nao do autor.
> Ate agora ha **UM** parecer (codex/GPT-5); o do kimi esta BLOQUEADO
> por quota do ciclo (`STOP_WAIT_RESET`) e sera anexado quando o ciclo
> renovar — as evidencias das tentativas estao em `revisao-p1a10/`.

## O que o revisor fechou — os primeiros MAJOR fechados do acervo

| id | Veredito | Justificativa do revisor (resumo) |
|---|---|---|
| **N1** | **FECHADO** | mutex efetivo no entry point do runner |
| **P1A4-1** | **FECHADO** | mesmo defeito do N1 |
| **P1A4-3** | **FECHADO** | recibo declara o alcance em vez de afirmar ausencia global |
| **P1A4-5** | **FECHADO** | recibo atomico antes do relato, com teste do relator que falha |
| **P1A4-6** | **FECHADO** | guardas novos exercem a interface operacional |
| 6 / N5 / P1A4-2 | NAO-FECHADO | a negacao depende de fragmento do vocabulario; construcao sem fragmento continua invisivel — o residuo que a propria correcao declarou |
| P1A4-4 | NAO-FECHADO | reconta-se so o redigido; originais seguem declaracao, e o fluxo nao exporta |

**CONTAGEM-DISTINTA: 6** — a pergunta reaberta SEM numero, como o
handoff ordenou, foi respondida: 6/N5/P1A4-2 fundidos, N1/P1A4-1
fundidos, os demais separados. E o primeiro parecer de revisor obtido
com a pergunta neutra.

## Os registros de hoje: OITO de oito SUSTENTADOS

P1A9-a, P1A9-b, 103, 104, 105, 106, 107 e 108 — todos SUSTENTADOS, com
a ressalva correta no 105 ("mitigacao, nao garantia", que e o que o
proprio registro declara). Os quatro achados declarados contra o autor
(a–d): todos CONFIRMADOS, com familia e estreia declaradas.

## Achados novos do revisor

| Nivel | Onde | O que | Familia | Area |
|---|---|---|---|---|
| MAJOR | `contexto_workspace.py:montar_snapshot` | janela TOCTOU entre islink/getsize e open — symlink trocado pode incluir arquivo externo no snapshot | fora-de-ambas | **estreia** (arquivo nasceu em 11/08) |
| MAJOR | `sentinela_antip2.py` | o portao de vocabulario nao fecha o contorno geral | (N) | ja revisada |
| MAJOR | `medidor.py:exportar_bruto` | originais permanecem testemunhais; fluxo nao exporta | fora-de-ambas | ja revisada |
| MINOR | `provedor_assinatura.py:normalizar_saida` | `num_turns=True` passa como int (bool e subclasse de int) | fora-de-ambas | **estreia** |
| MINOR | `99_correcao-p1a9a.md` (errata: a primeira publicacao desta tabela grafou p1a9b) | o registro afirma que `--rapido` incluiu a prova central — e `--rapido` a OMITE; alcance descrito maior que o exercido | **(F)** | registro novo |

`DEFEITO-NOVO: SIM` (o TOCTOU). `VEREDITO: REPROVADO` — o acervo
continua reprovado, e continuar reprovado com cinco fechamentos e
exatamente o que um revisor honesto devolve quando dois MAJOR seguem
abertos e um novo aparece.

## O criterio de parada, medido sob esta rodada

| Condicao | Limiar | Medido | Dispara? |
|---|---|---|---|
| (a) novos em area JA revisada | 6+ | **3** (sentinela, medidor, e o MINOR do registro — os dois de estreia declararam o pacote que nao os continha) | nao |
| (b) familia do MAJOR #3 (F) | 4+ | **1** | nao |
| (c) saldo nos MAJOR de origem | nao-positivo | **+5** (cinco fechados, zero reabertos) | nao |

**A trilha de correcao PODE continuar.** Fila da proxima rodada, na
ordem de risco: TOCTOU do snapshot (MAJOR, toca conteudo enviado a
provedor), bool-como-int no parser (MINOR mecanico), errata do
registro p1a9b (F — corrigir a frase, nunca o numero medido), e os dois
NAO-FECHADO remanescentes, que exigem decisao de desenho (negacao sem
portao inunda; originais nao-redigidos violam ZeroPii — os limites
foram declarados de proposito e o revisor os julgou insuficientes).

## Limites desta rodada, declarados

- parecer de UM revisor; o kimi entra quando a quota renovar;
- o codex revisou por STDIN com hashes DECLARADOS (sem ferramentas — o
  sandbox de tool-use do codex esta quebrado nesta estacao,
  `codex-windows-sandbox-setup.exe` ausente, achado desta rodada);
- quem despachou e quem corrigiu — conflito declarado na primeira
  secao das DECLARACOES que o revisor leu.

## ANEXO (2026-08-13) — o segundo parecer chegou: kimi, APROVADO-COM-RESSALVAS

O parecer do kimi (484,8 s, contencao limpa, hashes COMPUTADOS por ele
e conferidos, `kimi-20260813T*.json`) julgou o MESMO pacote. O mapa dos
dois revisores:

| id | codex | kimi | Consenso |
|---|---|---|---|
| N1 | FECHADO | FECHADO | **FECHADO por ambos** |
| P1A4-1 | FECHADO | FECHADO | **FECHADO por ambos** |
| P1A4-3 | FECHADO | FECHADO | **FECHADO por ambos** |
| P1A4-5 | FECHADO | FECHADO | **FECHADO por ambos** |
| 6 | nao-fechado | FECHADO | dividido |
| P1A4-2 | nao-fechado | FECHADO | dividido |
| P1A4-4 | nao-fechado | FECHADO (no mecanismo) | dividido |
| P1A4-6 | FECHADO | nao-fechado (fora do diff, nao conferivel) | dividido |
| N5 | nao-fechado | nao-fechado | **ABERTO por ambos** (residuo declarado) |

**CONTAGEM-DISTINTA: 6 pelos DOIS revisores, com as MESMAS fusoes**
(6/N5/P1A4-2 e N1/P1A4-1). A pergunta que o handoff mandou reabrir sem
numero esta respondida por convergencia independente: **seis**.

Divergencias registradas, nao absorvidas: o kimi fechou 6/P1A4-2 e
P1A4-4 lendo as correcoes desta missao; o codex os manteve abertos pelo
residuo. O kimi nao fechou P1A4-6 por honestidade de escopo (o
tratamento e da P1-A.5, fora do diff). **A palavra final sobre os
divididos e do Fundador**, com os dois pareceres na mao. Nota: os
residuos que motivaram os nao-fechados do codex foram corrigidos APOS o
ALVO deste pacote (`99_correcao-residuos-p1a10.md`) e entram no proximo
ciclo.

Registros: kimi sustenta 7 de 8 — o 105 saiu NAO-SUSTENTADO como
correcao ("mitigacao por instrucao sem instrumento", que e exatamente o
que o proprio registro declara). DEFEITO-NOVO: NAO pelo kimi (o TOCTOU
do codex ja estava corrigido apos o ALVO). Achados novos do kimi, para
a fila: marcador `stdout.index("==")` fragil no guarda dos quatro
campos (MINOR, estreia), reconversao `eol: crlf` do ramo `commit` do
medidor sem limite declarado (MINOR, estreia), envelope do pacote sem
cabecalhos de protocolo (OBS, estreia), evidencia de sondas nao
versionada (MINOR, ja revisada).

**Criterio de parada, remedido com os DOIS pareceres:** (a) novos em
area ja revisada ≈ 4 contra limiar 6; (b) familia F = 1 contra limiar
4; (c) saldo de consenso **+4** (quatro fechados por ambos, zero
reabertos). **Nenhum dispara; a trilha pode continuar.**

## ARBITRAGEM DO FUNDADOR (2026-08-13) — os quatro divididos

Decisao do Fundador, com os dois pareceres na mao:

| id | Decisao | Fundamento |
|---|---|---|
| **6** e **P1A4-2** | **aguardam o proximo ciclo** | o codex julgou um residuo que ja foi corrigido DEPOIS do ALVO (`99_correcao-residuos-p1a10.md`); o fechamento sai mais forte quando um revisor vir o estado atual |
| **P1A4-4** | **aguarda o proximo ciclo** | mesmo fundamento — ancora cruzada e export do fluxo sao pos-ALVO |
| **P1A4-6** | **FECHADO** | a regra do acervo exige UM revisor independente dizendo que fechou, e o codex o disse no merito; o kimi nao contradisse o merito — declarou o proprio escopo ("fora do diff, nao conferivel"), e a ressalva fica anotada |
| **N5** | **mantido ABERTO por decisao** | o residuo final (decisao sem comparacao, dado externo) e indecidivel por analise estatica; N5 permanece como lembrete permanente de que a sentinela e deteccao, nunca impedimento |

Com isto o placar de origem fica: **CINCO fechados** (N1, P1A4-1,
P1A4-3, P1A4-5 por consenso; P1A4-6 pela regra de um revisor), **tres
aguardando o proximo ciclo** ja com as correcoes prontas, **um aberto
por decisao**. A fila menor do kimi foi autorizada e corrigida na
mesma data (marcador do guarda, limite do `eol`, sondas versionadas).

## Plataforma — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
