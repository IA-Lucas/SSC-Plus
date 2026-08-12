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
| MINOR | `99_correcao-p1a9b.md` | o registro afirma que `--rapido` incluiu a prova central — e `--rapido` a OMITE; alcance descrito maior que o exercido | **(F)** | registro novo |

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

## Plataforma — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
