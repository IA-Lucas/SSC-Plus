---
id: SSC-DEC-P1A32
titulo: Registro e Decisao da Missao SSC+ P1-A.3.2 — correcao dos seis MAJOR (ADJUST)
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-31
---

# Registro e Decisao — Missao SSC+ P1-A.3.2

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo** sobre o HEAD `30107bd`.
> `99_decisao-p1a3.md` e `99_decisao-p1a31.md` NAO foram tocadas.
> `NVIDIA_API_KEY` global/HKCU jamais removida, alterada ou persistida.

## DECISAO: **ADJUST** — seis MAJOR corrigidos e provados; tres pontos exigem decisao soberana

Os seis MAJOR foram corrigidos, e cada correcao foi **demonstrada por
reversao ou mutacao**, nao afirmada (§3). Nenhum atestado foi emitido,
nenhum pacote foi enviado a revisor, a P1-B nao foi executada e a
P1-B-02 permanece FECHADA.

A decisao e ADJUST — nao READY-FOR-REVIEW — porque tres pontos
levantados por esta missao **pertencem ao Soberano, nao a ela** (§5):

1. a salvaguarda do gerador foi **relaxada** de "HEAD igual ao alvo"
   para "commit alvo existe e a paternidade confere" — consequencia
   necessaria da ancoragem exigida, mas ainda assim afrouxamento de um
   guarda que a P1-A.3.1 registrou como funcionando;
2. o isolamento do kimi entregue e **parcial mais deteccao integral**,
   nao isolamento equivalente ao do codex — o CLI nao oferece sandbox de
   filesystem, e isso e limite medido, nao escolha;
3. **achado novo, NAO corrigido** (fora dos seis): existe uma decisao
   sobre o veredito fora do classificador em `07_p1b/preflight_atual.py`
   — area que esta missao esta proibida de tocar.

## 1. Identidade e pre-condicoes (verificadas na abertura)

| Item | Resultado medido |
|---|---|
| HEAD exigido | OK — `30107bd1ef30b07ab575ff5991e90d70345d702a` |
| Arvore limpa | OK |
| Sem tag e sem remoto | OK — `git tag -l` e `git remote -v` vazios |
| Locks pelo protocolo | 6 leases no diretorio, **todos vencidos**; os 6 PIDs titulares (121120, 91064, 78412, 70536, 105464, 79508) **todos mortos**. Nenhum lock removido a mao. |
| Outra sessao viva | nenhuma — a missao NAO e BLOCKED por concorrencia |
| Lease e fencing desta missao | `p1a32-ops`, fence **1**, pid 114556, lease 120 s renovado a 30 s por `evidencias/renovador_lock.py`, adquirido **antes da primeira escrita** e vivo ate a pos-verificacao |
| Copia datada | `SSC-Plus_copia-p1a32-20260731-115307` — 2733 de 2734 arquivos; o unico ausente e `locks/p1a32-ops.lock`, sob lock do SO desta propria sessao |

### 1.1 Linha de base MEDIDA no HEAD, antes de tocar qualquer arquivo

| Suite | Resultado medido |
|---|---|
| P0 | **100/100 OK** |
| P1-A | **306/307 FAILED** |
| Prova central | **18/18 OK** (20 eventos) |

A P1-A **ja abria vermelha**, exatamente como a §4.2 da
`99_decisao-p1a31.md` previu. A falha unica era o sentinela anti-P2
acusando `evidencias/pacote_p1a31.py` — arquivo que apenas *menciona* o
literal no enunciado de uma pergunta. Registrado pelo numero medido: a
missao **nao** encontrou 307/307.

O JSON da prova central contem UUIDs por corrida; o arquivo versionado
foi restaurado apos cada reexecucao — a arvore permaneceu limpa.

## 2. Registro por correcao

### ITEM 0 — sentinela anti-P2 (achado #6, §4.2)

**Alvo:** `06_p1a/tests/test_emendas_p1a3.py`,
`test_shadow_eligible_nao_tem_consumidor_de_execucao`.

**O que mudou.** O corpo comparava o CONJUNTO DE CAMINHOS que contem o
literal com uma allowlist fixa de 6 arquivos. Nome e corpo divergiam: o
nome afirma ausencia de consumidor de execucao; o corpo verificava uma
lista. Passou a medir comportamento por AST, em duas metades:

- **(A)** fora do classificador (`preflight/pipeline.py`), nenhum
  arquivo do pacote P1-A **decide** sobre o veredito (comparacao,
  `in`/`not in`, `match`/`case`);
- **(B)** em nenhum arquivo do repositorio uma decisao sobre o veredito
  **governa execucao** — nem dentro do proprio classificador.

Mencao documental deixou de contar **por construcao**: so conta o
`Constant` cujo valor e EXATAMENTE um termo do vocabulario, ou um nome
ligado a um deles no mesmo arquivo. Um docstring ou texto de prompt que
cite `SHADOW_ELIGIBLE` no meio de uma frase nunca e igual ao termo.

**Por que.** Sem isto a missao colidiria na primeira escrita de
evidencia sob `06_p1a` — e colidiu: a linha de base media 306/307.

**Qual teste prova.** O proprio teste reescrito. **Prova por mutacao**
(§3.1): tres consumidores de execucao reais injetados em tres arquivos
da allowlist antiga; nos tres, o sentinela antigo ficou **cego**
(conjunto de caminhos identico) e o novo **acusou**.

**Limite declarado.** A analise e estatica e por arquivo; nao segue
dataflow entre modulos. Cobre o consumidor escrito no fonte, que e a
forma pela qual o invariante seria burlado.

### MAJOR #1 — atalho PAYG de google/grok

**Alvo:** `06_p1a/preflight_capsula.py`.

**O que mudou.** O laco montava a mao um relatorio
`{"resultado": "SUPERVISED"}` para google/grok e seguia com `continue`,
sem chamar `executar_preflight` nem `_config_persistida`. A frota
inteira passou a sair de `executar_preflight`, pela nova funcao
`classificar_frota(env, tiers, config_de=None, sensor_de=None)`.

**Por que.** O atalho pulava as auditorias de ambiente e de config: com
`GEMINI_API_KEY` no ambiente, endpoint PAYG ou `auto_topup` persistido,
o resultado era SUPERVISED — os bloqueios economicos nao eram sequer
consultados. A zero-sonda que motivava o atalho **nao depende dele**: e
propriedade declarada na especificacao (`sondas_automaticas=False`) e o
pipeline ja a respeita, classificando no teto sem invocar sensor algum.

**Qual teste prova.** `test_correcoes_p1a32.AtalhoPaygGoogleGrok` — 7
testes. Cinco exigem BLOCKED onde o atalho devolvia SUPERVISED; um exige
que ambiente limpo mantenha SUPERVISED com **contador de sondas em
zero** (a correcao nao pode reintroduzir o risco de pendura via Git
Bash); um exige que todo relatorio seja `RelatorioPreflight`.

### MAJOR #2 — regexes de quota esgotada

**Alvo:** `06_p1a/preflight/adaptadores.py`.

**O que mudou.** Introduzido `_ZERO`, o zero como NUMERO
(`(?<![\d.,])0(?:[.,]0+)?(?![\d.,])`), e reescritas as regexes de
esgotamento sobre ele, com sinal de porcentagem opcional e a forma
`<nome> [:=] 0`.

**Por que.** O padrao anterior exigia `\b0` seguido de espaco. Assim
`0.0 tokens available` e `0% quota available` — as duas formas citadas
no achado — nao casavam regex de esgotamento **alguma** e caiam no sinal
positivo `\bavailable\b`: quota zerada classificada como disponivel,
fail-open. As duas ancoras de `_ZERO` sao necessarias e nao simetricas:
sem a de tras, `10.0 tokens available` casaria pelo `0` depois do ponto
e bloquearia franquia disponivel; sem a da frente, `0.5 calls left`
bloquearia meia franquia.

**Qual teste prova.**
`test_correcoes_p1a32.QuotaEsgotadaZeroDecimalEPercentual` — 4 testes,
11 formas que devem esgotar e 6 que **nao podem** esgotar, mais dois
casos fim a fim pelo pipeline (BLOCKED com `P1A-QUOTA-ESGOTADA`).

### MAJOR #3 — isolamento do kimi

**Alvo:** `06_p1a/evidencias/revisao_p1a3.py`,
`06_p1a/evidencias/revisao_p1a31.py`, e o novo modulo compartilhado
`06_p1a/evidencias/contencao.py`.

**O que mudou.** Duas metades:

1. **Restricao real pelo CLI.** `kimi --help` foi medido (sonda de
   diagnostico, zero chamada de modelo, custo zero): **nao existe**
   `--sandbox read-only` equivalente ao do codex. O que existe passou a
   ser usado — `--plan` (modo mais restritivo do CLI) e `--skills-dir`
   apontado para um diretorio VAZIO — e o que existe e perigoso passou a
   ser explicitamente ausente: `-y`, `--yolo` e `--auto`, que
   auto-aprovariam chamadas de ferramenta.
2. **Deteccao integral.** Manifesto SHA-256 de **toda a arvore** antes e
   depois da chamada. Mutacao fora do descartavel entra na evidencia e
   **reprova a corrida** (returncode 3). Unica exclusao, declarada:
   `locks/`, que o renovador reescreve a cada 30 s por construcao —
   `.git` **entra** no manifesto.

**Por que.** `cwd` descartavel e instrucao textual no prompt nao
restringem o filesystem: o filho herda as permissoes do usuario. E a
lista de "arquivos restantes" so olhava DENTRO do descartavel, de modo
que escrita fora dele nao aparecia em lugar nenhum.

**Qual teste prova.** `test_correcoes_p1a32.ContencaoDoReviewer` — 8
testes: criacao, alteracao e remocao fora do descartavel sao acusadas;
arvore intacta nao gera alarme; `locks` e a unica exclusao e `.git` nao
e ponto cego; o argv usa `--plan`/`--skills-dir` e nunca as flags de
auto-aprovacao; e o rotulo de enforcement **nao pode afirmar** sandbox
que nao existe.

**Limite declarado — ponto para o Soberano (§5.2).** Isto e restricao
parcial mais deteccao integral, **nao** isolamento equivalente ao do
codex. O rotulo de enforcement foi reescrito para dizer exatamente isso;
o texto anterior afirmava que `-p` aplicava "a politica auto com regras
estaticas de deny", afirmacao que o `--help` medido nao sustenta (o
`--auto` e opt-in e assume `false`).

### MAJOR #4 — lease antes da persistencia

**Alvo:** `06_p1a/preflight_capsula.py`,
`06_p1a/evidencias/revisao_p1a3.py`,
`06_p1a/evidencias/revisao_p1a31.py`, via `contencao.verificar_lock`.

**O que mudou.** A verificacao do lease deixou de existir so na abertura
e passou a ocorrer **imediatamente antes de cada persistencia**, agora
tambem com **fence esperado**: fence diferente = titular substituido =
PARADA sem gravar. O fence ilegivel/ausente tambem para.

**Por que.** Entre a abertura e a gravacao correm as sondas reais e as
chamadas de provider, que excedem a janela do lease — 256 s observados
contra 120 s de lease na P1-A.3.1. Verificar so no inicio permitia
gravar com lease morto ou com o escritor ja substituido.

**Qual teste prova.** `test_correcoes_p1a32.LeaseAntesDaPersistencia` —
7 testes. Os dois centrais rodam `preflight_capsula.main()` de verdade
sobre uma raiz temporaria e matam o lease **entre a sonda e a gravacao**
(um por expiracao, outro por troca de fence): ambos exigem `SystemExit`
e **diretorio de evidencias inexistente** — nada gravado. Um terceiro e
a contraprova: com o titular intacto, `main()` grava, devolve 0 e o
documento registra `lock_verificado_antes_da_persistencia: true`. Sem
essa contraprova, um guarda que reprovasse sempre passaria nos dois
primeiros.

### MAJOR #5 — ancoragem do pacote no commit (§4.1)

**Alvo:** `06_p1a/evidencias/pacote_p1a31.py`.

**O que mudou.** Tres coisas:

1. **Leitura exclusivamente via git.** O bloco de hashes de evidencia
   usava `(RAIZ / rel).read_bytes()` — os bytes da ARVORE DE TRABALHO.
   Toda leitura passou para `git cat-file blob <ALVO>:<path>`, que
   devolve o objeto cru, sem filtro de EOL e sem tocar o disco.
2. **Docstring alinhado a implementacao.** O texto anterior afirmava que
   "toda a leitura e via `git show`/`git diff`" — afirmacao **falsa**
   para aquele bloco. O docstring agora descreve o que o codigo faz e
   registra por que.
3. **Portao de identidade re-ancorado.** A constante foi renomeada de
   `HEAD` para `ALVO` e o portao deixou de exigir
   `rev-parse HEAD == ALVO`, passando a exigir que o par ALVO/PAI exista
   no repositorio e que a paternidade confira.

**Por que.** Com `core.autocrlf=true`, os bytes em disco de um arquivo
rastreado sao funcao do historico de checkout, nao do commit — e 4 dos
11 hashes divergiam entre a copia de trabalho e um checkout novo. Quanto
ao portao: exigir HEAD igual ao alvo amarrava o gerador ao ESTADO DO
CHECKOUT, exatamente o que a ancoragem elimina, e impedia qualquer
terceiro de reproduzir o pacote depois de um commit posterior — o que a
missao exige textualmente. **Isto e afrouxamento de um guarda e vai a
decisao soberana (§5.1).**

**Qual teste prova.** `test_correcoes_p1a32.AncoragemDoPacoteNoCommit` —
4 testes, com a prova executavel em §3.3.

## 3. Provas executadas (demonstradas, nao afirmadas)

### 3.1 Sentinela — prova por mutacao, em copia descartavel

Consumidor de execucao real injetado, um por vez, em tres arquivos da
allowlist antiga; conjunto de caminhos medido antes e depois:

| Arquivo mutado | Consumidor injetado | Sentinela ANTIGO | Sentinela NOVO |
|---|---|---|---|
| `preflight/pipeline.py` (o proprio classificador, isento do invariante A) | `if resultado == "SHADOW_ELIGIBLE": adaptador.sonda(...)` | **CEGO** — conjunto identico | **ACUSA** `pipeline.py:299 -> sonda()` |
| `preflight/sombra.py` | `if rel.resultado == "SHADOW_ELIGIBLE": subprocess.run(...)` | **CEGO** — conjunto identico | **ACUSA** `sombra.py:80 -> run()` |
| `preflight/economia.py` | variavel intermediaria: `alvo = "SHADOW_ELIGIBLE"` ... `os.system(...)` | **CEGO** — conjunto identico | **ACUSA** `economia.py:317 -> system()` |

Copia descartada apos a prova; sentinela verde de novo ao reverter.

### 3.2 As quatro correcoes do codex — prova por REVERSAO

Cada correcao foi **desfeita** em copia descartavel completa (com
`.git`) e a classe de teste correspondente exigida em VERMELHO:

| Correcao desfeita | Classe de teste | Resultado |
|---|---|---|
| atalho PAYG de volta | `AtalhoPaygGoogleGrok` | **FAILED (5 falhas)** |
| regexes anteriores de volta | `QuotaEsgotadaZeroDecimalEPercentual` | **FAILED (7 falhas)** |
| kimi sem restricao e sem deteccao | `ContencaoDoReviewer` | **FAILED (4 falhas)** |
| lease so na abertura, sem fence | `LeaseAntesDaPersistencia` | **FAILED (3 falhas)** |
| pacote lendo a arvore de trabalho | `AncoragemDoPacoteNoCommit` | **FAILED (9 falhas)** |

Restauradas todas as reversoes: **VERDE**. Teste que continuasse verde
com a correcao desfeita nao provaria a correcao.

### 3.3 Ancoragem — prova por mutacao da arvore e por checkout limpo

Todas as tres geracoes produziram **o mesmo SHA-256 e o mesmo tamanho**:

```
c17b730ff8a060165332b08c35ba305f199021dc8b8cd90a55c53ad1a9141459  447.693 bytes
```

| Geracao | Condicao | SHA-256 |
|---|---|---|
| A | arvore de trabalho intacta | `c17b730f…` |
| B | arvore de trabalho **deliberadamente mutada** (`tiers_declarados.json`, arquivo que esta nas duas listas do gerador) | `c17b730f…` — **inalterado** |
| C | **worktree destacada e limpa em `677c585`** | `c17b730f…` — **identico** |

Conferencia direta contra o banco de objetos: os hashes de evidencia
impressos no pacote batem com `git cat-file blob 677c585:<path>` —
verificado item a item pelo teste, e a mao para dois deles.

Esta e exatamente a prova que **FALHOU** na P1-A.3.1 (§10.2), onde
arvore e commit produziram `c3b5c5…` contra `e1f856e…`.

**O pacote `c3b5c5…` deixa de representar o estado.** O novo hash do
mesmo commit `677c585` e `c17b730f…`: as 4 linhas do bloco de evidencia
que carregavam bytes do disco passaram a carregar os bytes versionados.
O conteudo funcional e o diff permanecem os mesmos.

## 4. Suites — medidas, nunca como meta

| Suite | Abertura (HEAD `30107bd`) | Fecho (arquivos staged) |
|---|---|---|
| P0 | 100/100 OK | **100/100 OK** |
| P1-A | **306/307 FAILED** | **337/337 OK** |
| Prova central | 18/18 OK | **18/18 OK** |

O crescimento de 307 para 337 e a soma dos 30 testes novos desta missao;
**nao e criterio de aceite**. Conforme a §4.2.2 da `99_decisao-p1a31.md`,
`307/307` deixou de ser criterio valido: o criterio e o sentinela medir
comportamento, o que a §3.1 demonstra. As suites foram rodadas **com os
arquivos staged, antes do commit**, conforme a regra prospectiva da §7.

## 5. Pontos que exigem decisao soberana (motivo do ADJUST)

### 5.1 Afrouxamento do portao de identidade do gerador

O portao passou de "HEAD igual ao alvo" para "commit alvo existe e a
paternidade confere". A P1-A.3.1 registrou o portao antigo como
"salvaguarda funcionando" (§10.2), e ele de fato impedia o gerador de
rodar na arvore principal apos um commit. A troca e **consequencia
necessaria** de duas exigencias textuais desta missao — ancorar o pacote
no commit e permitir que "um terceiro reproduza o pacote a partir do
commit" —, mas continua sendo relaxamento de um guarda. **Ratificar ou
reverter e decisao do Soberano.**

### 5.2 O isolamento do kimi e parcial por limite da plataforma

O CLI do kimi nao oferece sandbox de filesystem. O entregue e restricao
parcial (`--plan`, `--skills-dir` vazio, sem auto-aprovacao) somada a
deteccao integral por manifesto. Se o padrao exigido for isolamento
equivalente ao do codex, **nenhuma configuracao do CLI atual o entrega**
— seria preciso decidir por outro mecanismo (conteiner, usuario
restrito) ou aceitar o par restricao-parcial-mais-deteccao. **Decisao do
Soberano.**

### 5.3 Achado novo, fora dos seis, NAO corrigido

O invariante (A) do sentinela vale para o pacote P1-A; o invariante (B)
vale para o repositorio inteiro. Medindo o repositorio inteiro,
encontrei **uma decisao sobre o veredito fora do classificador**:

```
07_p1b/preflight_atual.py:172
    elegiveis = [r["provider_id"] for r in relatorios
                 if r["resultado"] == "ELIGIBLE"]
```

Ela **nao** governa execucao — o corpo apenas coleta identificadores
para impressao —, e por isso o invariante (B) passa. Mas e uma decisao
sobre elegibilidade fora do classificador, o tipo de construcao que
antecede um consumidor. **Nao foi corrigida**: esta fora dos seis, e
`07_p1b` esta fora da fronteira desta missao. Fica registrada para
decisao.

## 6. Fronteira, custo e ambiente

| Item | Estado verificado |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | o changeset inteiro |
| Escritas fora do repositorio | duas, ambas exigidas: a copia datada (§1) e as copias descartaveis das provas, em diretorio temporario da sessao — descartadas |
| Escrita em `lucaX` ou `LucaX Enterprise OS` | **nenhuma** |
| Chamadas de modelo | **0** |
| Custo variavel | **0** — nenhum PAYG, top-up, extra usage ou fallback pago |
| Sondas de CLI executadas | 1 (`kimi --help`), diagnostica, sem chamada de modelo |
| Tier renovado automaticamente | nao |
| Tag, remoto ou push | nenhum |
| `NVIDIA_API_KEY` global/HKCU | intocada |

## 7. Restricoes respeitadas

Nenhum pacote enviado a revisor; nenhuma revisao reaberta; nenhum
atestado de aprovacao emitido; P1-B nao executada; P2 nao iniciada;
nada promovido ao canonico. `99_decisao-p1a3.md`, `99_decisao-p1a31.md`
e demais historicos **nao foram editados**. Nenhum achado fora dos seis
foi corrigido — o de §5.3 foi registrado, nao consertado.

## 8. O que a proxima missao precisa

1. **Decidir os tres pontos do §5** — sem isso o eixo de ancoragem e o
   de isolamento ficam ratificados por omissao.
2. **Novo pacote sobre o novo HEAD.** O pacote `c17b730f…` revisa
   `677c585`; o commit desta missao e posterior e **nao esta nele**. Um
   pacote do novo estado exige atualizar `ALVO`/`PAI` e as listas do
   gerador — trabalho da proxima missao, nao desta.
3. **Nova revisao dupla** sobre esse novo pacote: o codex precisa rever
   o estado corrigido, e o kimi precisa de **quota renovada pelo
   proprietario** (o ciclo estava esgotado — 403 — e somente o
   proprietario renova).
4. **P1-B-02 permanece FECHADA** ate `READY-FOR-P1-B-RETRY` emitido
   sobre um HEAD efetivamente revisado por dois providers com zero
   CRITICAL/MAJOR.

O identificador do commit e as provas pos-commit estao em
`locks/registro-commit-p1a32.txt` — este documento e conteudo do proprio
commit e nao pode conter o hash que o inclui.
