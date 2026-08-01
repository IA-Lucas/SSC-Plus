---
id: SSC-DEC-P1A35
titulo: Registro e Decisao da Missao SSC+ P1-A.3.5 — varredura de guardas e correcoes
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-01
---

# Registro e Decisao — Missao SSC+ P1-A.3.5

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhuma decisao ou relatorio historico
> foi editado. O unico arquivo alheio tocado e `test_correcoes_p1a32.py`,
> que e **codigo de teste** e recebeu uma ressalva aditiva — no
> precedente da propria P1-A.3.4.

## DECISAO: **CONCLUIDA-COM-PULADOS**

Todos os itens tem resultado ou bloqueio registrado. Oito correcoes
fechadas com as duas provas exigidas; cinco frentes registradas e
puladas, cada uma com a correcao especificada e o motivo.

## SUMARIO — 10 linhas

1. **86 guardas** enumerados por descoberta no codigo e classificados com evidencia apontavel; residuo da particao **zero**.
2. Classes na abertura: **EXERCE 49 · SEM-TESTE 26 · AFIRMA 9 · INALCANCAVEL 1 · INDETERMINADO 1**.
3. Classes no fechamento: **EXERCE 64 · SEM-TESTE 13 · AFIRMA 8 · INALCANCAVEL 0 · INDETERMINADO 1**.
4. A classe dominante de defeito nao era guarda testado fraco — era **guarda nao testado**: 26 dos 86.
5. **8 correcoes**, uma por commit, cada uma com teste que exerce a coisa real **e** reversao vermelha medida.
6. **9 achados novos**, numerados 7 a 15; tres deles sao o mesmo mecanismo: a copia que ninguem exercita fica para tras.
7. **Nao resta ramo de recusa nao alcancado em `06_p1a` nem em `07_p1b`** — os 16 restantes sao todos da P0.
8. **5 frentes puladas**: argv da prova minima (exige CLI real), P0 (volume), ACHADO 4 (politica), achado B (INDETERMINADO), 6 guardas de runners de revisao (exigem provider).
9. Suites no HEAD final: **P0 100/100 · P1-A 401/401 · prova central 18/18** (20 eventos). Contagem medida, nunca meta.
10. **Zero chamada de modelo, custo variavel zero**, arvore limpa, sem tag e sem remoto, lease `p1a35-ops` vivo do inicio ao fim.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Medido |
|---|---|
| HEAD de abertura | `6a8c843be75f13507b969c9aa28e91beaf9997db` |
| Arvore | limpa |
| Tag / remoto | nenhuma / nenhum |
| Sessao viva | **nenhuma** — 12 leases, todos vencidos, nenhum PID titular vivo |
| Lease desta missao | `p1a35-ops`, fence **1**, pid 133432, renovado a 30 s, adquirido **antes da primeira escrita** |
| P0 / P1-A / prova central | **100/100 · 346/346 · 18/18** |

**Condicao operativa declarada** (§7 da `99_achados-governanca-20260731.md`):
enquanto o ACHADO 4 nao for corrigido, a exclusao mutua entre missoes
**nao existe**; o escritor unico desta missao e garantido **por ordem do
Fundador**, nunca pelo mecanismo.

## 2. Fase 1 — o metodo, e o que ele revelou

Registrada por inteiro em `99_varredura-guardas-p1a35.md`. O essencial:

- o conjunto de arquivos vem de `git ls-files` (**66** arquivos, **66**
  parseados, zero ilegiveis), nunca de lista a mao;
- **cinco colheitas** mecanicas por AST — recusa, filtragem/redacao,
  construcao restrita, residente em teste e deteccao —, porque uma so
  nao alcanca as outras quatro. Uma sexta foi tentada e **colapsada com
  o motivo declarado**;
- as **167** recusas foram particionadas por regra, com balde
  `RESIDUO` **vazio**;
- **446** metodos de teste colhidos = **446** testes executados;
- o alcance de cada linha de guarda foi **medido** sob `sys.monitoring`,
  nao inferido — e o instrumento foi corrigido no meio do caminho, com
  a nota de que nenhuma conclusao mudou.

**O achado central da Fase 1 nao estava no ato.** O ato apontava para
`AFIRMA`; a medicao mostrou que o problema dominante e **SEM-TESTE** —
26 dos 86 guardas, quase um terco. Guarda testado fraco era o que a
auditoria dos seis MAJOR via porque olhava so os seis.

## 3. Fase 2 — as oito correcoes

Cada uma com **as duas provas**: teste que exerce a coisa real, e
reversao que fica vermelha. As reversoes estao medidas commit a commit.

| # | Commit | Alvo | Reversao medida |
|---|---|---|---|
| 1 | `1d62be9` | **MAJOR #1** — leitor cego para grok | 5 de 7 metodos vermelhos; as 2 contraprovas seguem verdes |
| 2 | `350933c` | **achado C** — `pacote_p1a33.py` sem teste | 4 vermelhos (leitura de disco) + 1 (portao de ancestralidade) |
| 3 | `507a19e` | **achado A** — `_config_persistida` sem cobertura | 2 vermelhos (allowlist do codex) + 14 (binding padrao desligado) |
| 4 | `516d90c` | **achado 7** — MAJOR #4 na copia da P1-B | 2 vermelhos (sem reverificacao) + 1 (fence ignorado) |
| 5 | `a650513` | **achado 10** — nove redacoes em tres forcas | 9 vermelhos (sem 8.3) + 10 (sem caminho local) |
| 6 | `e16fe29` | **achado 9** — portao de tier nunca exercido | 1 (teto) + 3 (PARADA) + 2 (achado 15) |
| 7 | `238f54b` | leitor de config em duas copias | 1 vermelho (copia propria devolvida a P1-B) |
| 8 | `e6277ce` | ultimos ramos de recusa de P1-A/P1-B | 1 erro (try do fence) + 1 falha (copia local) |

### 3.1 O que as correcoes revelaram, e que nao estava previsto

**O mesmo mecanismo apareceu tres vezes: a copia que ninguem exercita
fica para tras.** MAJOR #4 corrigido na P1-A e nao na P1-B (achado 7);
a redacao com nove copias em tres forcas, e as tres mais fracas
justamente nos arquivos sem teste (achado 10); e o leitor de config, que
esta propria missao corrigiu de um lado e deixou intacto do outro ate a
correcao 7 — **o defeito reproduzido pela missao que o descrevia**.

**Dois achados sairam de EXERCER o instrumento, nunca de le-lo.** O
achado 14 (allowlist de duas chaves no codex, quando a justificativa
escrita ao lado pedia uma unica exclusao) apareceu porque um teste novo
reprovou. O achado 15 (`revisao_p1a31` omitia `declarado_por` da
evidencia) apareceu porque o teste exercia os **dois** runners de uma
vez. Nenhum dos dois seria visto por leitura.

### 3.2 Medicoes de seguranca, feitas e nao presumidas

| O que | Medido |
|---|---|
| Ampliacao da auditoria do codex produz violacao nova? | **Nao** — os cinco provedores dao zero violacao na estacao real, medido depois da troca (somente nomes de campo) |
| A redacao unificada move o SHA-256 dos pacotes publicados? | **Nao** — `c17b730f…` e `87f41503…` INALTERADOS, verificados apos cada correcao |
| A forma 8.3 do usuario vaza em artefato versionado? | **Nao** — zero arquivos, medido antes da correcao |

O segundo item merece nota: os dois pacotes reproduzem **byte a byte**
a partir do HEAD desta missao, oito commits depois de terem sido
gerados. E a propriedade do MAJOR #5 demonstrada viva, nao afirmada.

## 4. Resultado medido

| Classe | Abertura | Fechamento |
|---|---|---|
| EXERCE | 49 | **64** |
| SEM-TESTE | 26 | **13** |
| AFIRMA | 9 | **8** |
| INALCANCAVEL | 1 | **0** |
| INDETERMINADO | 1 | 1 |
| **Total** | 86 | 86 |

**Nao resta ramo de recusa nao alcancado em `06_p1a` nem em `07_p1b`.**
Dos 42 pontos de imposicao por recusa, 26 tem todas as linhas
alcancadas; os 16 com lacuna sao **todos** da P0.

## 5. Pulados — cada um com a correcao especificada

Conforme a parada granular: registrado e pulado, nunca abandonado.

| # | Frente | Por que foi pulada | Correcao especificada |
|---|---|---|---|
| P1 | **Achado 11** — argv de `prova_minima.COMANDOS` (codex, claude, kimi) afirmado so pela forma | Exige **invocar os CLIs reais** de codex e claude; as RESTRICOES desta missao vedam invocar provider | Repetir a construcao de `test_cli_real_p1a34.py`: HOME vazio, ambiente por allowlist, assercao da classe de erro **pos-parsing** que prova aceitacao sem gastar chamada. Antes, sondar se os dois CLIs distinguem as duas classes de erro como o kimi 0.30.0 distingue |
| P2 | **6 guardas SEM-TESTE** em runners de revisao — `COMANDOS` e `ambiente_capsula()` de `revisao_p1a2/p1a3/p1a31` | Exercita-los exige rodar `main()` daqueles runners, que invoca provider | O padrao ja existe e e mecanico: `test_correcoes_p1a32.py:308` roda `revisao_p1a31.main()` com reviewer FALSO. Replicar para os outros dois |
| P3 | **P0 — 16 pontos com ramo de recusa nao alcancado**, entre eles 37 de 53 ramos do `SessionKernel` | Volume incompativel com esta missao | Missao propria de cobertura da P0, na mesma disciplina: alcance medido sob `sys.monitoring`, um teste por ramo, contraprova por ponto |
| P4 | **ACHADO 4** — o escritor unico nao exclui entre missoes | **Exige mudanca de politica**: lock por nome de sessao e materia 4 da missao de politica (§9 da `99_achados-governanca-20260731.md`) | Lock unico do repositorio, e `liberar()` que expire o lease que concedeu |
| P5 | **Achado B** — 9 das 11 formas de `ESGOTADAS` sao autorais | Exige saida real de CLI com quota esgotada, indisponivel | Permanece **INDETERMINADO**, e nao se converte |

**Uma indeterminacao adicional segue declarada e nao resolvida:** que
`~/.gemini/settings.json` use mesmo a chave `base_url` para endpoint
**nao foi confirmado** — a coleta da P1-A nunca auditou a config do
google. Se for outra chave, nasce um segundo INALCANCAVEL ao lado do que
o grok tinha.

## 6. Fronteira, custo e ambiente

| Item | Estado **verificado** |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | 16 caminhos (14 de codigo/teste, 2 de registro), mais `locks/` (runtime, gitignorado) |
| Escritas fora do repositorio | apenas os instrumentos de medicao, no temp da sessao |
| Copia datada | **nenhuma criada** — pratica encerrada por decisao do Fundador |
| Escrita em `lucaX` ou `LucaX Enterprise OS` | **nenhuma** |
| Store do harness | **nao gravado** |
| **Chamadas de modelo** | **0** |
| Custo variavel | **0** |
| Tag, remoto ou push | nenhum |
| Lock tomado a forca | nenhum |

Leituras fora da fronteira, todas read-only e **somente de nomes**:
`~/.grok/` (listagem), `~/.codex/auth.json` (nomes de campo, para medir
se a ampliacao da auditoria produziria violacao nova). Nenhum valor foi
impresso, gravado ou transmitido.

Os instrumentos da varredura **nao foram acrescentados ao acervo**, por
uma razao que e o proprio objeto da missao: um `.py` novo sem teste seria
mais um caso do achado C.

## 7. Alcance — o que esta missao estabelece e o que NAO estabelece

### 7.1 Estabelecido — medido, e independente de revisor

| Fato | Como |
|---|---|
| A enumeracao e fechada e sem sobra | indice do Git; particao com residuo zero; 446 = 446 |
| O alcance de cada guarda | medido sob `sys.monitoring`, reproduzivel por terceiro |
| SEM-TESTE era a classe dominante | 26 de 86 na abertura |
| Cada correcao esta acoplada ao seu guarda | reversao vermelha medida, por correcao |
| Nenhuma correcao reprova sempre | contraprova presente em cada uma |
| Os pacotes publicados reproduzem | `c17b730f…` e `87f41503…`, oito commits depois |
| Suites no HEAD final | 100/100, 401/401, 18/18 |

### 7.2 NAO estabelecido — e nao se presume

- **Nenhum dos seis MAJOR fechou.** Fechar exige revisor independente
  (§9.3 da `99_decisao-p1a33.md`), e esta missao **corrigiu** — quem
  corrige nao certifica. Vale com mais forca aqui do que na P1-A.3.4:
  esta sessao classificou os guardas **e** alterou catorze arquivos de codigo e teste.
- **EXERCE nao e sinonimo de correto.** Exercer a coisa real e condicao
  necessaria, nunca suficiente; o alcance medido diz que uma linha foi
  executada, nao que a assercao ao redor dela seja forte. A lacuna de
  sensibilidade do sentinela (§3.4 da `99_decisao-p1a34.md`) continua
  sendo o exemplo vivo disso, e **nao foi corrigida**.
- **A exclusao mutua entre missoes continua inexistente.** As correcoes
  4, 7 e 8 unificaram o guarda de escritor unico e o exercitaram; o
  ACHADO 4 e sobre o que ele **verifica**, e isso e materia de politica.
- **Nada se afirma sobre a P1-B em operacao.** Ela **nao foi
  executada**: os testes do seu runner substituem `executar_preflight` e
  isolam o `HOME`.
- **O alcance do achado do CLI e a versao instalada** — kimi 0.30.0.
  Nada se afirma sobre outras versoes nem sobre codex e claude, cujos
  argv permanecem `AFIRMA`.
- **A quota do kimi permanece NAO MEDIDA.**

## 8. O que a proxima missao precisa

1. **Pacote NOVO sobre o HEAD final desta missao.** O `87f41503` vale
   para `ac03f3a` e esta missao alterou catorze arquivos de codigo e
   teste; reenvia-lo submeteria um estado que nao contem nada disto.
2. **Declarar aos revisores o ACHADO 4** (§8 da
   `99_achados-governanca-20260731.md`) e, agora, tambem que a
   classificacao de guardas e as correcoes vieram da mesma sessao.
3. As cinco frentes puladas da §5, na ordem em que estao.
4. **A missao de politica** segue com as quatro materias intactas: esta
   missao nao tocou politica em ponto algum.
