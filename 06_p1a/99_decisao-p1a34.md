---
id: SSC-DEC-P1A34
titulo: Registro e Decisao da Missao SSC+ P1-A.3.4 — contencao real do kimi e auditoria dos seis testes
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-31
---

# Registro e Decisao — Missao SSC+ P1-A.3.4

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**. `99_decisao-p1a3.md`,
> `99_decisao-p1a31.md`, `99_decisao-p1a32.md` e `99_decisao-p1a33.md`
> **NAO foram tocadas**. `NVIDIA_API_KEY` global/HKCU jamais removida,
> alterada ou persistida.

## DECISAO: **READY-FOR-REVIEW**

O Item 0 fechou pelo caminho forte: `contencao.argv_kimi` corrigido, com
teste que **invoca o CLI real do kimi** e reprova quando a correcao e
desfeita — sem consumir uma unica chamada de modelo. O Item 1 entregou a
classificacao dos seis com evidencia apontavel, e produziu **tres
achados**, um deles um `AFIRMA` de mesma classe que o do MAJOR #3.

Isto e prontidao para **revisao**, nao aprovacao: nenhum revisor falou
nesta missao tampouco, e a assimetria da §9.3 da `99_decisao-p1a33.md`
continua valendo — esta missao **corrigiu**, e por isso menos ainda pode
certificar. Nenhum dos seis MAJOR fechou. `P1-B-02` permanece **FECHADA**.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Resultado **medido** |
|---|---|
| HEAD **exigido pelo ato** | `ba10be2` |
| HEAD **medido** | **`8bbac04dfa1acfecf23ac74909b39a81fcd36758`** — divergente |
| Pai do HEAD medido | `ba10be202d67f7663b2fd1c3f87b9e499d680a7c` = o HEAD exigido |
| Arvore limpa na abertura | OK |
| Sem tag e sem remoto | OK — `git tag -l` e `git remote -v` vazios |
| Branch | `master` |
| Copia datada | `SSC-Plus_copia-p1a34-20260731-134901` — **2968 de 2968** arquivos |

### 1.1 A divergencia de HEAD — registrada, nao contornada

O ato manda confirmar `ba10be2`. O HEAD medido e `8bbac04`, cujo **pai e
exatamente `ba10be2`**. A causa esta no proprio acervo: `8bbac04` e o
commit da §10 da `99_decisao-p1a33.md` — a verificacao independente
pos-fechamento —, feito **depois** da redacao deste ato. Nao e sessao
concorrente nem escrita de terceiro.

Registrado pelo **numero medido, nunca pelo esperado**, como o ato
manda. Consequencia material: **nenhuma**. `8bbac04` altera um unico
arquivo (`06_p1a/99_decisao-p1a33.md`, +125 linhas, aditivo) e **zero
linha de codigo** — de modo que toda afirmacao de codigo herdada de
`ba10be2` continua valendo em `8bbac04`. A missao prossegue sobre o HEAD
medido, que e o unico que existe.

### 1.2 Locks — medidos pelo protocolo dos dois manifestos

Oito leases. Medicao feita **antes de qualquer suite** desta missao,
justamente para nao fabricar o artefato que a §10.2 da
`99_decisao-p1a33.md` descreve:

| Lease | PID titular | Vencido | Titular vivo |
|---|---|---|---|
| `p1-ops` | 111396 | **nao** | **nao** |
| `p1a2-ops`, `p1a3-ops`, `p1a31-ops`, `p1a32-ops`, `p1a33-ops`, `p1b-ops`, `repo-p1a1` | 91064, 78412, 70536, 121416, 122904, 105464, 79508 | sim | nao |

**Prova de que nenhuma sessao estava viva:** dois manifestos tomados a
**105 s** de intervalo com `expira_em` **inalterado nos oito**, e nenhum
processo `renovador_lock.py` em execucao. Nenhum lock removido a mao.

**Confirmacao independente do achado da §10.2.** O `p1-ops` nao vencido
com titular morto reapareceu com **pid novo (111396) e token novo (59)** —
a §10.2 mediu pid 122000/token 58. Duas corridas de suite, dois pids,
mesmo artefato: o mecanismo la descrito esta **reproduzido**, nao
inferido. Quem avaliasse a pre-condicao *"Outra sessao viva: BLOCKED"*
por vencimento de lease teria parado aqui em falso positivo.

| Lease e fencing desta missao | `p1a34-ops`, fence **1**, pid 116204, lease 120 s renovado a 30 s por `evidencias/renovador_lock.py`, adquirido **antes da primeira escrita** |
|---|---|

## 2. ITEM 0 — a contencao do kimi, agora exercida

### 2.1 O defeito, remedido na propria interface

```
$ kimi --plan --skills-dir <vazio> -p "ping"
error: Cannot combine --prompt with --plan.
```

Reproduzido nesta missao, com o CLI **0.30.0** instalado. `--plan` nunca
foi restricao: ele **impedia a corrida inteira**. Desde a P1-A.3.2
nenhuma chamada headless ao kimi era possivel por esta ferramenta.

### 2.2 A correcao

`06_p1a/evidencias/contencao.py`:

```python
# antes
return [executavel, "--plan", "--skills-dir", dir_skills, "-p", prompt]
# depois
return [executavel, "--skills-dir", dir_skills, "-p", prompt]
```

`enforcement_kimi()` foi **reetiquetado** junto: o rotulo dizia
`restricao PARCIAL por --plan + --skills-dir vazio`, e afirmar uma
restricao que o CLI recusa e pior do que nao te-la. O rotulo novo declara
`sem plan mode em headless (o CLI recusa --plan com -p)`.

**O que resta de restricao real, medido e nao presumido.** Plan mode nao
tem substituto headless em 0.30.0 — `--plan` e eixo de sessao
interativa. O binario declara os modos de permissao existentes:

```
"session.permission_mode_invalid": { action: "Use one of: yolo / manual / auto." }
```

`-y/--yolo` e `--auto` sao justamente os dois **nao** restritivos. Nao
passa-los e, portanto, a restricao que sobra pelo CLI — e ela e
verificada por teste. **Nao se afirma** que o kimi exija aprovacao
interativa em modo headless: isso exigiria uma chamada de modelo para
observar, e nao foi medido.

Duas alternativas foram **sondadas e descartadas, com o motivo**:
`--sandbox read-only` → `error: unknown option '--sandbox'` (nao existe
no kimi); `--agent <perfil>` → `error: --agent/--agent-file are only
available with the v2 engine` (exigiria motor experimental). Uma terceira,
`permission_mode` em `config.toml`, **nao foi adotada**: o arquivo vive
em `~/.kimi-code/`, **fora da fronteira** desta missao.

### 2.3 O teste — por que ele exerce, e por que custa zero

`06_p1a/tests/test_cli_real_p1a34.py`, 4 testes, **invocam o binario**.

O que torna a prova possivel sem gastar chamada: o kimi 0.30.0 tem
**duas classes de erro distinguiveis na saida**.

| Classe | Exemplo | Quando ocorre |
|---|---|---|
| validacao de argv | `error: Cannot combine --prompt with --plan.` | **antes** de qualquer trabalho |
| pos-parsing | `error: failed to run prompt: No model configured` | **so depois** de o parser aprovar o argv inteiro |

A segunda e **prova positiva de aceitacao**. E ela e alcancada com custo
zero por construcao — nao por promessa:

1. `HOME`/`USERPROFILE` do filho apontam para um diretorio temporario
   **vazio**: nenhuma credencial OAuth do usuario e alcancavel;
2. o ambiente do filho e montado por **allowlist** (`PATH`, `SYSTEMROOT`,
   `TEMP`, `TMP`, `COMSPEC`, `PATHEXT`) — nenhum `KIMI_*` sobrevive, de
   modo que nenhum modelo pode ser configurado por variavel;
3. o teste **asserta** `No model configured` na saida: se o isolamento
   falhasse, o teste reprova em vez de gastar.

O teste vai por `revisao_p1a33.COMANDOS["kimi"]`, **nao** direto por
`argv_kimi`: `argv_kimi` correto com chamador errado continuaria
quebrado, e a fiacao do chamador precisa entrar no escopo.

### 2.4 Prova por reversao — contra a realidade, nao contra o codigo

Com `--plan` reintroduzido em `argv_kimi`, medido:

```
FAIL: test_o_cli_real_aceita_o_argv_de_producao
AssertionError: 'failed to run prompt' not found in
  'error: Cannot combine --prompt with --plan.\n'
```

A mensagem que reprova e **do proprio CLI**, nao de um mock. Essa e a
diferenca que o ato pede: reversao vermelha contra um duplo prova
acoplamento; contra o binario, prova realidade. Restaurada a correcao,
4/4 verdes.

### 2.5 Uma regra do proprio acervo foi contrariada — declarado, nao silencioso

`06_p1a/tests/apoio.py:3` diz: *"Regra desta suite: NENHUM subprocesso
real e criado e NENHUM CLI de assinatura e invocado"*. O novo teste a
contraria, e o ato desta missao o ordena explicitamente (*"exercer o CLI
real do kimi"*, *"nunca simular a interface e chamar de exercicio"*).

Registro do tradeoff, em vez de obediencia ou recusa em silencio: o
**proposito** declarado da regra — *"sem gastar um unico token de
assinatura"* — fica **integralmente preservado** (§2.3), e e a **letra**
que cede. A excecao esta escopada a um arquivo, declarada no seu
docstring, e `apoio.py` **nao foi alterado**. A propria frase de
`apoio.py` e a melhor explicacao de como o MAJOR #3 passou quebrado, e
por isso ela recebeu uma ressalva em `test_correcoes_p1a32.py` em vez de
ser apagada.

## 3. ITEM 1 — auditoria dos seis: EXERCE, AFIRMA ou INDETERMINADO

Premissa de partida, conforme §9.2 da `99_decisao-p1a33.md`: **nenhum dos
seis esta fechado**. Esta tabela **nao fecha nenhum** — ela preve quais
reprovariam, para proteger quota.

O eixo e um so: *o teste exerce a interface real, ou afirma a propriedade
contra um modelo?*

| # | MAJOR | Classe | Evidencia apontavel |
|---|---|---|---|
| 1 | atalho PAYG google/grok | **AFIRMA** | `test_correcoes_p1a32.py:89-91` e `:141-143` injetam `config_de=`/`sensor_de=` nas **duas** chamadas; `_config_persistida` **nao e chamada por teste algum** (zero call sites em `tests/`). O caso decisivo: `preflight_capsula.py:158` devolve `{}` **incondicionalmente** para grok, e `test_correcoes_p1a32.py:102` afirma BLOCKED sobre `{"auto_topup": True}` — dicionario que o leitor real **nunca pode produzir**. |
| 2 | regexes de quota | **EXERCE** | `_quota_de` e importado da producao (`:32`) e executado com literais (`:174-182`); `_ZERO` em `adaptadores.py:36` e a regex real. Limite declarado em §3.2. |
| 3 | isolamento do kimi | **AFIRMA → EXERCE** (corrigido nesta missao) | Era AFIRMA: `:271-283` mediam a **forma da lista**, e `:326-328` substituiam o CLI inteiro por `sys.executable -c`. Agora EXERCE por `test_cli_real_p1a34.py` (§2.3). A metade "deteccao" ja era EXERCE: `:337-349` roda `revisao_p1a31.main()` de verdade, com subprocesso que **escreve mesmo** fora do descartavel, e exige `rc == 3`. |
| 4 | lease antes da persistencia | **EXERCE** | `:378-412` exercem `verificar_lock` contra lease/fence **reais** em disco, com `EscritorP1.lease_expirado` real; `:431-478` rodam `preflight_capsula.main()` de verdade e exigem `SystemExit` **e** ausencia de gravacao. Fiacao de producao coberta em `revisao_p1a31.py:144,180`. |
| 5 | ancoragem do pacote no commit | **EXERCE** | `:510-513` roda `git cat-file blob` **de verdade** contra o banco de objetos; `:515-531` **muta o disco** e exige que o gerador ignore. E o exercicio de interface real mais forte da suite. |
| 6 | sentinela anti-P2 | **EXERCE** | `:810` varre os `.py` **reais** do repositorio e `:813` os parseia com `ast` real; mede forma de AST, nunca lista de caminhos. Limite ja declarado no proprio codigo (`:563-565`: sem dataflow entre modulos). |

Nenhum INDETERMINADO na classificacao dos seis — e nenhum silencioso.

### 3.1 Achado A (MAJOR #1, `AFIRMA`) — o leitor real e cego para grok

**O que falta.** Nenhum teste executa `_config_persistida`. Os sete testes
de `AtalhoPaygGoogleGrok` provam que **o pipeline bloqueia** diante de um
dicionario com `auto_topup`/`base_url`/`api_key`; nao provam que **o
leitor real** produza tal dicionario a partir da config em disco.

**Por que isso importa, e nao e teoria.** Para grok, `_config_persistida`
retorna `{}` sempre (`preflight_capsula.py:158`, comentado *"nenhuma
config parseavel localizada na P1-A"*). Logo o caminho que
`test_grok_com_auto_topup_persistido_e_blocked` percorre **e inalcancavel
em operacao**. O MAJOR #1 dizia que *"os bloqueios economicos nao eram
sequer consultados"*; depois da correcao eles **sao** consultados, porem
com um leitor estruturalmente cego para um dos dois provedores que o
MAJOR nomeia. A correcao e real e incompleta — e o teste nao distingue as
duas coisas.

**Teste real faltante, especificado.** Um teste que (a) monte um HOME
descartavel com `~/.gemini/settings.json` e a config do grok em formato
**real**, (b) chame `classificar_frota` **sem injetar `config_de`**,
exercendo o binding padrao de `preflight_capsula.py:181`, e (c) exija
BLOCKED com `P1A-PAYG-CONFIG`. Ele reprovaria hoje para grok, que e
exatamente o ponto. Para google, exige ainda confirmar que a chave lida
de `settings.json` e mesmo `base_url`.

**NAO corrigido nesta missao**, por forca do ato (*"Nao corrigir achado
fora do Item 0"*). Saber o tamanho do problema precede conserta-lo.

### 3.2 Achado B (MAJOR #2, limite do `EXERCE`) — o corpus e autoral

`_quota_de` e exercido de verdade. O que **nao** foi exercido e a
proveniencia das 11 formas de `ESGOTADAS`: duas (`0.0 tokens available`,
`0% quota available`) sao citadas no achado original como observadas; as
outras nove sao **autorais**. Se um provedor emitir uma decima segunda
forma, nenhum teste percebe.

**Estado: INDETERMINADO, e permanece INDETERMINADO.** Resolve-lo exige
capturar saida real de CLI com quota esgotada — indisponivel nesta missao
(codex so restabelece em 5/8/2026 09:29; kimi nao medido). Registrado
como limite conhecido, nao como defeito.

### 3.3 Achado C (cobertura) — os artefatos da P1-A.3.3 nao tem teste

Classe distinta das duas acima: nao e teste fraco, e **ausencia** de
teste sobre o artefato que foi **efetivamente usado**.

| Artefato | Papel | Coberto por teste? |
|---|---|---|
| `evidencias/pacote_p1a31.py` | gerador **testado** (`ALVO 677c5853`) | **sim** — `AncoragemDoPacoteNoCommit` |
| `evidencias/pacote_p1a33.py` | gerador que **produziu o pacote `87f41503` enviado a revisao** (`ALVO ac03f3a`) | **nao** — nenhum teste o carrega |
| `evidencias/revisao_p1a33.py` | runner da revisao da P1-A.3.3 | **so** pelo teste novo desta missao, e apenas quanto ao argv do kimi |

A propriedade do MAJOR #5 vale para `pacote_p1a33.py` **por construcao**
(ele tambem le por `git cat-file blob`, e tem um portao a mais: `BASE`
ancestral de `ALVO`), e foi observada empiricamente na §10.1 da
`99_decisao-p1a33.md`. Mas **construcao e observacao nao sao teste de
regressao**: nada impede que uma edicao futura reintroduza leitura de
disco nesse arquivo sem que a suite perceba.

**Teste real faltante:** parametrizar `AncoragemDoPacoteNoCommit` sobre
os **dois** geradores, ou duplica-la para `pacote_p1a33.py`. **NAO
corrigido** — fora do Item 0.

### 3.4 Observacao sobre o MAJOR #6 — classificado EXERCE, com uma lacuna de sensibilidade

Nao altera a classificacao, e nao seria honesto omitir. As tres
assercoes do sentinela (`:828-838`) sao todas da forma `== []`. Um
detector que devolvesse `[]` **sempre** passaria nas tres. As primitivas
`_portoes_de_execucao` e `_decisoes_sobre_veredito` sao chamadas de **um
unico lugar** (`:821` e `:825`), e nenhum teste lhes apresenta uma fonte
**sabidamente suja** exigindo deteccao.

A *"prova por mutacao (3 arquivos)"* registrada na §1.4 da
`99_decisao-p1a33.md` foi um **ato manual** da P1-A.3.2, nao um teste da
suite — logo nao protege contra regressao futura do detector.

Isto **nao** e AFIRMA no eixo desta auditoria: a interface (arvore de
fontes + `ast`) e real e e exercida. E um controle positivo ausente. Nao
converto uma coisa na outra em nenhuma das direcoes.

## 4. O pacote `87f41503` — invalidado por esta missao

Registro explicito, conforme o ato:

- O pacote `87f415031aa1c7ee6464ac6c74f73b8508912350816fc6402fde6a8e435b87c2`
  (318.389 bytes) e funcao de `30107bd..ac03f3a` e **vale para aquele
  par de commits**;
- a instrucao do item 4 da §8 da `99_decisao-p1a33.md` — *"a proxima
  missao pode enviar os mesmos bytes sem regerar"* — **DEIXA DE VALER**;
- motivo: aquela instrucao se apoiava em o micro-commit da P1-A.3.3 nao
  conter **alteracao de codigo**. Esta missao **altera codigo**
  (`contencao.py` e dois arquivos de teste), e o estado a revisar deixou
  de ser `ac03f3a`;
- consequencia: **a revisao exigira pacote NOVO, gerado sobre o HEAD
  final desta missao**. Reenviar `87f41503` submeteria a revisao um
  estado que nao contem a correcao de `argv_kimi` — precisamente o
  defeito que motivou esta missao.

Nao ha contradicao com a §10.1 da `99_decisao-p1a33.md`: o hash nao se
mover apos commits posteriores e propriedade do **gerador** (ele le de
`ALVO`, nao do checkout). O que muda aqui nao e o hash do pacote — e a
**pergunta**, que passa a ser sobre outro commit.

## 5. Suites — medidas, nunca como meta

| Suite | Resultado (arquivos staged, antes do commit) |
|---|---|
| P0 | **100/100 OK** |
| P1-A | **346/346 OK** |
| Prova central | **18/18 OK** (20 eventos) |

346 = os 342 medidos na P1-A.3.3 **mais os 4** testes de CLI real desta
missao. **Contagem medida, nunca meta.** Os 4 testes novos **nao
skiparam**: o CLI do kimi esta instalado e foi invocado. Invocacoes do
binario por corrida da suite: **3** — uma em
`test_o_cli_real_aceita_o_argv_de_producao`, uma em
`test_o_cli_real_recusa_plan_junto_com_prompt` e uma em
`test_toda_flag_declarada_incompativel_e_recusada_pelo_cli` (uma por
entrada de `FLAGS_INCOMPATIVEIS_COM_PROMPT`, que hoje tem uma).
`test_o_argv_de_producao_nao_carrega_flag_de_auto_aprovacao` nao invoca:
so inspeciona o argv montado.

O novo `.py` sob `06_p1a/tests/` **nao aciona** o sentinela anti-P2 —
`tests` esta em `_DIRS_IGNORADOS` (`test_emendas_p1a3.py:583`).

O JSON da prova central contem UUIDs por corrida; o arquivo versionado
foi **restaurado** apos a reexecucao — a arvore permaneceu limpa
(precedente da §5 da `99_decisao-p1a33.md`).

## 6. Fronteira, custo e ambiente

| Item | Estado **verificado** |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | 3 caminhos de codigo/teste + este registro, mais `locks/` (runtime, gitignorado) |
| Escritas fora do repositorio | duas, ambas exigidas: a copia datada (**irma**, nao dentro) e a sonda descartavel no temp da sessao |
| Escrita em `lucaX` ou `LucaX Enterprise OS` | **nenhuma** |
| Escrita em `~/.kimi-code/` | **nenhuma** — `permission_mode` foi descartado por isso (§2.2) |
| **Chamadas de modelo** | **0** — nenhuma invocacao passou de `No model configured` |
| Custo variavel | **0** — nenhum PAYG, top-up, extra usage ou fallback pago |
| Tier renovado automaticamente | nao |
| Tag, remoto ou push | nenhum |
| Copias datadas | jamais tocadas |

Sondas diagnosticas, **todas sem chamada de modelo**, contadas:

| Sonda | Invocacoes | `HOME` |
|---|---|---|
| `kimi --version`, `kimi --help` | 2 | real (nao ha argv de prompt: nada a chamar) |
| sonda exploratoria de argv (casos A–G) | 7 | 1 real, **6 isolado e vazio** |
| suite `test_cli_real_p1a34.py` | 3 por corrida | isolado e vazio |

A unica invocacao com `HOME` real **e** argv de prompt foi o caso A —
a reproducao do defeito, que morre em `Cannot combine --prompt with
--plan` **antes** de qualquer rede, e por isso nao alcanca credencial.

Todo comando ancorado por caminho absoluto ou `git -C`.

## 7. Micro-commit probatorio

Quatro caminhos: `06_p1a/evidencias/contencao.py` (M),
`06_p1a/tests/test_cli_real_p1a34.py` (A),
`06_p1a/tests/test_correcoes_p1a32.py` (M) e este registro (A).

Staging explicito caminho a caminho, **sem `git add -A`**. Nenhum
documento historico editado; sem runtime, sem segredo, sem tag, sem
remoto, sem push. O identificador do commit e as provas pos-commit ficam
em `locks/registro-commit-p1a34.txt` — este documento e conteudo do
proprio commit e nao pode conter o hash que o inclui.

## 8. O que a proxima missao precisa

1. **Gerar pacote NOVO sobre o HEAD final desta missao** (§4). O
   `87f41503` esta invalidado para fins de revisao.
2. **Revisao independente**, com quota, pelos dois provedores. O codex so
   restabelece em **5/8/2026 09:29** ou por ato do proprietario; a quota
   do kimi permanece **nao medida** — mas agora e *mensuravel*, porque o
   CLI aceita o comando. Esta e a mudanca pratica desta missao.
3. **Achado A** (§3.1): o teste do binding padrao de `_config_persistida`,
   e a cegueira do leitor para grok.
4. **Achado C** (§3.3): cobrir `pacote_p1a33.py`.
5. **Lacuna de sensibilidade do sentinela** (§3.4): um controle positivo.
6. **O achado da §10.2 da `99_decisao-p1a33.md` continua aberto** —
   `liberar()` nao expira o lease que concedeu, e a suite P1-A escreve no
   `locks/` real. Reconfirmado nesta missao com pid e token novos (§1.2).

## 9. Alcance — o que esta missao estabelece e o que NAO estabelece

### 9.1 Estabelecido — medido, e independente de revisor

| Fato | Como |
|---|---|
| O kimi 0.30.0 recusa `--plan` com `-p` | invocacao real; reproduzido |
| O argv que a ferramenta monta agora **e aceito** pelo CLI | invocacao real, morte em `No model configured` |
| Desfazer a correcao reprova, **pela voz do CLI** | reversao medida (§2.4) |
| MAJOR #1 e AFIRMA | `_config_persistida` sem call site em `tests/`; `preflight_capsula.py:158` |
| `pacote_p1a33.py` nao tem teste | nenhum teste o carrega |
| O sentinela nao tem controle positivo | primitivas chamadas de um unico lugar, tres assercoes `== []` |
| Suites no HEAD desta missao | 100/100, 346/346, 18/18 |

### 9.2 NAO estabelecido — e nao se presume

- **Nenhum dos seis MAJOR esta fechado.** Fechar exige revisor
  independente (§9.3 da `99_decisao-p1a33.md`), e esta missao corrigiu —
  *quem corrigiu nao certifica*.
- **Nao se afirma que o kimi seja contido.** Afirma-se restricao
  **parcial** (skills vazio, sem auto-aprovacao) mais **deteccao
  integral** por manifesto. Nao ha sandbox de filesystem, e agora
  tampouco plan mode.
- **Nao se afirma que o kimi exija aprovacao interativa em headless.**
  Nao medido: exigiria chamada de modelo.
- **A quota do kimi permanece NAO MEDIDA.** Nao se afirma disponivel nem
  esgotada.
- **A classificacao dos seis nao e veredito.** E previsao de quais
  reprovariam, feita para proteger quota.
- **O alcance do achado do CLI e a versao instalada** — 0.30.0. Nada se
  afirma sobre outras versoes.
