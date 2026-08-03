---
id: SSC-REG-P23-99
titulo: Registro da missao SSC+ P2.3 — a protecao no mecanismo
tipo: registro-experimental (NAO e atestado)
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Registro — Missao SSC+ P2.3

> Laboratorio experimental. Registro **aditivo**: nenhum documento
> anterior foi aberto para escrita. O registro de achados de 2026-08-03
> (`99_achados-divergencias-20260803.md`) permanece intacto e continua
> verdadeiro sobre o codigo que o produziu.
>
> **Este documento NAO e atestado de aprovacao.** O achado A segue
> **ABERTO**: quem corrige nao fecha o proprio conserto.

## 0. Medicao de partida e de fechamento

| Item | Abertura | Fechamento |
|---|---|---|
| HEAD | `db68151` | este commit |
| `git status --porcelain` | vazio | vazio |
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** (lido antes de qualquer medicao) | ausente (apagado apos reverter os 5 mutantes) |
| Suite `05_p0/tests` | **344/344 OK** | **344/344 OK** |
| Suite `06_p1a/tests` | **838/838 OK** | **866/866 OK** (838 + 28) |
| `05_p0/cenarios/prova_central.py` | OK, 18 assercoes / 20 eventos | idem |
| Escritor unico | — | `p23-ops`, fence **1**, pid 54736 |
| Chamadas **pagas** de modelo nesta missao | — | **ZERO** |
| Declaracao de tier | **nao renovada** | **nao renovada** |

As duas suites continuam medidas **em separado**, pela colisao de
`apoio.py` descrita no §0 do registro da P2.1.

## 1. O que passou a restringir

O achado A mediu que a protecao read-only vivia no texto. O remedio ja
existia neste acervo — `06_p1a/evidencias/prova_minima.py:46` e os quatro
`revisao_p1a*.py` —, e esta missao o levou ao caminho de producao. Nada
foi inventado.

| elo | antes (achado A) | agora |
|---|---|---|
| argv do codex | `<codex.exe> exec <tarefa>` | `<codex.exe> exec --sandbox read-only --cd <descartavel> --skip-git-repo-check --ephemeral <tarefa>` |
| argv do kimi | `<kimi> -p <tarefa>` | **igual** — e o rotulo diz por que (§4) |
| `cwd` do filho do CLI | ausente ⇒ herdava o runner | o **descartavel** da invocacao |
| `cwd` do filho da capsula | `None` ⇒ herdava o terminal | a **raiz do repositorio**, declarada |
| vigilancia da arvore | zero usos em `08_p2/` | `Vigilancia` abre e fecha **em volta da invocacao** |
| `efeito_externo` | `"nenhum"` por declaracao | **medido** por manifesto SHA-256 antes/depois |

A restricao vive na especificacao (`EspecProvedor.restricao_headless`) e
nao no montador de argv: o marcador `<DESCARTAVEL>` e trocado no momento
da invocacao. Assim a especificacao continua sem carregar caminho local —
a decisao da rodada 3 da revisao P1-A.3 — e o montador continua sem saber
a posicao das flags de nenhum CLI.

## 2. As quatro provas da ORDEM 3

Todas em `06_p1a/tests/test_p2_protecao_no_mecanismo_p23.py` (28 testes).
Cada uma responde a pergunta obrigatoria da REGRA DE PROVA — *o teste
exerce o caminho que a operacao percorre, ou um vizinho?*

### (a) A invocacao com sandbox

Duas metades, porque duas coisas diferentes precisavam de prova.

**A metade que este repositorio controla — o `cwd`.** Exercida com
SUBPROCESSO DE VERDADE (`sys.executable` no lugar do CLI, zero franquia),
escrevendo em **caminho RELATIVO**, que e a forma pela qual um filho cai
sobre o acervo. O byte vai parar no descartavel, e nao na raiz. O vizinho
recusado foi afirmar que `subprocess.run` recebeu `cwd=...`: isso mede a
fiacao, e o achado e o destino do byte.

**A metade que o CLI externo controla — as flags.** Exercida contra o
**codex 0.145.0 de verdade** (`CliRealDoCodex`), com `CODEX_HOME`, `HOME`
e `USERPROFILE` apontando para diretorios VAZIOS. Tres medicoes:

1. o argv de producao e **aceito**, e o proprio CLI ecoa `sandbox:
   read-only` e o descartavel como `workdir:` no cabecalho;
2. o valor e **validado** pelo CLI: `--sandbox read-onlyX` e recusado com
   `[possible values: read-only, workspace-write, danger-full-access]` —
   entao `read-only` nao e string ignorada;
3. flag inexistente e recusada **antes** do cabecalho (`unexpected
   argument`), que e a fronteira que torna a prova 1 falseavel.

**Custo zero por CONSTRUCAO, nao por promessa**, e verificado dentro do
proprio teste: sem credencial alcancavel a corrida morre em **401
Unauthorized**. Um 401 e chamada RECUSADA — nao ha turno de modelo. E a
mesma excecao declarada que a P1-A.3.4 abriu para o kimi, pela mesma
razao: afirmar o que uma interface externa aceita nao e medi-la.

### (b) Desfazer a restricao e a suite acusar

Cinco mutantes, **um por vez**, cada um registrado em
`scratchpad/MUTANTE-ATIVO.txt` ANTES de aplicar e revertido em seguida.
Medido sobre a suite `06_p1a/tests` (866 testes):

| # | mutante | arquivo:linha | testes vermelhos |
|---|---|---|---|
| **R1** | `restricao_headless` do codex vira `()` | `06_p1a/preflight/frota_real.py:103` | **6** |
| **R2** | `cwd=cwd` sai da chamada de `subprocess.run` | `08_p2/provedor_assinatura.py:152` | **2** |
| **R3** | a medicao para de decidir o efeito | `08_p2/provedor_assinatura.py:215` | **3** |
| **R4** | o achado da `Vigilancia` e descartado | `08_p2/provedor_assinatura.py:321` | **2** |
| **R5** | `cwd=RAIZ` sai do entry point da capsula | `06_p1a/capsula.py:124` | **1** |

Nomes dos testes que caem, por mutante, para que a medicao seja
auditavel e nao um numero solto:

- **R1**: `..._recebe_as_QUATRO_restricoes_antes_do_prompt`,
  `..._valor_de_cd_e_o_cwd_do_filho_e_o_diretorio_EXISTE`,
  `..._rotulo_do_codex_cita_as_flags_QUE_SERAO_EMITIDAS`,
  `..._registro_traz_uma_medicao_por_invocacao`, e os **dois de CLI
  real** — `..._ACEITA_o_argv_de_producao_e_ecoa_a_restricao` e
  `..._VALIDA_o_valor_de_sandbox`. Os dois ultimos ficam vermelhos
  porque o **CLI de verdade** deixa de ecoar `sandbox: read-only`:
  nenhum mock mediu essa queda;
- **R2**: `..._escrita_relativa_do_filho_NAO_cai_na_raiz_do_repositorio`
  e `..._filho_confirma_o_proprio_cwd`;
- **R3**: `..._escrita_plantada_no_descartavel_e_REGISTRADA_no_recibo`,
  `..._escrita_plantada_FORA_do_descartavel_e_REGISTRADA` e
  `..._falha_com_escrita_medida_nao_vira_nao_aplicado`;
- **R4**: `..._vigilancia_dispara_sobre_escrita_na_arvore_vigiada` e
  `..._escrita_plantada_FORA_do_descartavel_e_REGISTRADA`;
- **R5**: `..._filho_da_capsula_corre_na_raiz_do_repositorio`.

R5 derruba **um** teste, e isso e propriedade da correcao, nao fraqueza
da prova: ha um caminho so — o entry point — e ele e exercido de verdade,
lancando `python 06_p1a/capsula.py` de um diretorio que nao e a raiz.

**O mutante R2 escreve na arvore viva.** O teste que ele derruba planta
`PROVA-P23-ESCRITA-RELATIVA.txt`, e com o mutante aplicado esse arquivo
nasce na RAIZ do repositorio. O proprio teste o remove no `cleanup` — a
limpeza foi escrita junto com o mutante em mente, e a arvore foi
conferida vazia depois da campanha.

### (c) O recibo pega escrita plantada

`SensorQueEscreve` planta um arquivo conhecido e a medicao o registra:

- plantado **no descartavel** ⇒ `mutacoes_no_descartavel = ["criado:
  escrita-plantada.txt"]` e `efeito_externo = "aplicado"`;
- plantado **fora dele**, na arvore vigiada ⇒
  `mutacoes_fora_do_descartavel` traz o caminho, e o efeito tambem vira
  `aplicado` — porque a fotografia do descartavel, sozinha, nao ve o que
  cai fora dele. Foi exatamente por isso que a P1-A.3.2 precisou da
  `Vigilancia`;
- **nada plantado** ⇒ `nenhum`, agora como fotografia vazia.

Ha um guarda contra a volta do defeito por omissao:
`classificar` **exige** a lista de mutacoes (`TypeError` sem ela). Um
default deixaria um chamador esquecido devolvendo `nenhum` sem medir —
que e o achado A de novo, calado.

E ha o guarda do sentido inverso: falha transitoria **com** escrita
medida NAO devolve `nao-aplicado`. `nao-aplicado` autoriza retry (IR-1),
e autorizar retry sobre efeito que ja ocorreu seria pior que o defeito
original.

### (d) A Vigilancia dispara

Nao basta estar importada, e por isso ha tres testes:

1. ela **acusa** escrita plantada na arvore que declara vigiar;
2. **sem injecao**, o executor constroi a vigilancia REAL — mais de 300
   arquivos fotografados e as **seis** fontes de config de
   `contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO` entre as raizes. Sem
   este teste, a injecao que a suite usa por custo seria o interruptor
   que apaga o mecanismo em producao sem ninguem ver;
3. o lease do renovador e **ATRIBUIDO** e nao vira efeito do provedor —
   a separacao entre deteccao e atribuicao do §6 da P1-A.3.6. Sem ela,
   toda corrida longa pareceria escrita externa, e o recibo perderia o
   poder de acusar a de verdade.

## 3. O que a medicao NAO cobre

Declarado aqui porque a REGRA DE PROVA obriga, e porque o achado A nasceu
justamente de uma propriedade afirmada alem do mecanismo.

- **O que `--sandbox read-only` FAZ dentro do turno do modelo.** Mede-se
  que o CLI aceita a flag, valida o valor e ecoa o modo. Que ele recuse
  uma escrita pedida pelo modelo e propriedade do CLI externo e exigiria
  invocacao **com credencial** — **NAO MEDIDO**, e a ordem proibiu
  queimar franquia para isto;
- **`codex sandbox`**, o subcomando que roda comando sob token restrito
  do Windows, **nao foi usado**: ele exige `--permission-profile <NAME>`
  resolvido da pilha de configuracao, e o `~/.codex/config.toml` desta
  estacao nao tem tabela `[permissions]` (`default_permissions refers to
  undefined profile`). Definir um perfil seria escrever **fora deste
  repositorio**, que e precisamente o que o achado A registra como fora
  do controle do SSC+;
- **a medicao ve DISCO**, dentro das raizes vigiadas. Efeito do outro
  lado da rede — escrita que o provedor faca no proprio servico — nao
  aparece em fotografia nenhuma. Por isso `nao-aplicado` (transitorio) e
  `incerto` (timeout) seguem sendo afirmacoes sobre o lado REMOTO, e a
  medicao local **nao** os sobrescreve;
- **as nove corridas anteriores** rodaram sem fotografia de antes e
  depois. Nao ha como afirmar nem negar que alguma escreveu. Nada nesta
  missao autoriza dizer que o passado esta limpo;
- **a config real do codex** (`~/.codex/config.toml`, fora deste
  repositorio) segue **NAO MEDIDA** quanto ao efeito sobre `exec`. Os
  testes de CLI real usam `CODEX_HOME` isolado exatamente para nao
  depender dela — o que tambem significa que eles **nao** medem o que
  ela faz numa corrida de operacao;
- **o kimi nao ganhou restricao de filesystem**, porque o CLI nao a
  oferece (`unknown option '--sandbox'`, medido na P1-A.3.4). O que ele
  tem agora e o descartavel como `cwd` e a `Vigilancia`. O rotulo diz
  isso por extenso e ha teste proibindo as palavras `sandbox`,
  `read-only`, `somente leitura` e `isolad` nesse rotulo;
- **`--ephemeral` nao impede escrita em `CODEX_HOME`.** Medido durante
  esta missao: com `CODEX_HOME` isolado, uma corrida recusada por 401
  deixou `state_*.sqlite`, `logs_*.sqlite`, `installation_id` e outros no
  diretorio. Fora das seis fontes vigiadas, essa escrita **nao e
  detectada** por este mecanismo — limite conhecido, nao propriedade.

## 4. Um rotulo que nao pode exceder o mecanismo

`rotulo_restricao` e **construido** a partir de `restricao_headless`, o
mesmo objeto que o executor emite — e ha teste que retira uma flag da
especificacao e exige que ela suma do rotulo. E a licao do achado N3
aplicada ao outro rotulo do acervo: foi por a frase e o mecanismo serem
objetos independentes que um pode ter passado o outro.

## 5. Classificacao por familia

Obrigatoria pelo `CLAUDE.md` da raiz. Esta missao **nao produziu
achados** — ela corrige um. Para constar, o que ela fecha do lado do
codigo:

| achado | familia | estado |
|---|---|---|
| **A** | **(F)** — afirmava a propriedade em vez de exerce-la | **corrigido no mecanismo, NAO fechado**: falta revisao independente |
| B, C, D | fora de ambas | **intocados**, por ordem expressa |

Nenhum criterio de parada foi disparado nesta missao, porque nenhuma
revisao independente correu aqui.

## 6. O que esta missao NAO e

Nao e revisao independente e nao e atestado. O achado A permanece
**ABERTO** ate que um revisor que nao escreveu este codigo diga que
fechou. Quem corrige nao certifica.
