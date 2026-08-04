---
id: SSC-DEC-P1A4
titulo: Registro e Decisao da Missao SSC+ P1-A.4 — revisao independente do estado atual
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-04
---

# Registro e Decisao — Missao SSC+ P1-A.4

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhuma decisao ou relatorio historico
> foi editado. Missao **probatoria** — nao corrigiu nenhum achado. Duas
> linhas de registro de teste foram tocadas, e **so** para registrar o
> proprio instrumento desta missao; a §7 mede e declara exatamente o
> que foram, por que o repositorio as exigiu e por que isso nao e
> correcao.

## DECISAO: **STOP**

Nao por escolha desta missao: **pelo criterio de parada gravado no
`CLAUDE.md` da raiz**, que disparou na condicao **(a)**.

O revisor independente devolveu **SEIS MAJOR NOVOS** — exatamente o
limiar de *"SEIS OU MAIS defeitos NOVOS"*. Disparado o criterio, o ato
manda **nao abrir nova missao de correcao** e **retornar ao Fundador com
a medicao e a classificacao por familia**. E o que este registro faz.

O portao da missao (*zero CRITICAL e zero MAJOR nos DOIS vereditos*)
falhou nas duas metades, por causas independentes: o codex REPROVOU, e o
kimi nao produziu veredito. Fechar uma nao abre a outra.

**Nao e BLOCKED**, e a §4.1 dispoe disso formalmente: a quota nao e
afericao do portao de pre-condicoes (o preflight devolve `desconhecida`
para os cinco provedores), o proprietario decidiu medir na chamada em vez
de parar antes, ha precedente identico na P1-A.3.6 — e, sobretudo,
BLOCKED significa *"nao houve medicao"*, quando houve medicao completa.

## SUMARIO — 10 linhas

1. Pacote **NOVO** sobre o HEAD atual: `a36471a3…`, **1.312.291 bytes**,
   BASE `6a3a3f8` (ALVO do ultimo pacote efetivamente julgado), ALVO
   `3f24085`, **96 commits** entre os dois.
2. **Quatro geracoes, um so hash** — duas em descartaveis independentes,
   uma em clone limpo com checkout de **outro** commit, e uma com dois
   arquivos julgados **deliberadamente mutados** na arvore.
3. **codex: veredito REPROVADO**, 448,182 s, modelo `gpt-5.6-sol`, com
   os dois SHA-256 conferidos pelo proprio revisor.
4. **kimi: sem veredito** — `403 You've reached your usage limit for this
   billing cycle`. **Quarta** falha consecutiva do kimi.
5. Dos doze MAJOR, o revisor **FECHOU NOVE** (1, 2, 3, 4, 5, N2, N3, N4,
   N6) e manteve **TRES abertos** (6, N1, N5).
6. Os **quatro achados da P2 (A, B, C, D) seguem NAO-FECHADOS**, o A
   inclusive — quem corrige nao certifica, e o revisor nao certificou.
7. `DEFEITO-NOVO: **SIM**` — vazamento de `mkdtemp` por tentativa em
   `provedor_assinatura.py` e um guarda falso em
   `test_config_real_p1a39.py`.
8. **SEIS MAJOR novos**, com familia atribuida pelo revisor: **(F) = 2**,
   **(N) = 1**, **fora de ambas = 3**. Criterio (a) DISPAROU; criterio
   (b) **nao** disparou.
9. **Achado desta missao contra o proprio instrumento, pela segunda
   vez**: a contencao acusou mutacao fora do descartavel na corrida do
   codex, e a causa foi **esta sessao**. A corrida do kimi, sob silencio,
   devolveu `violada: false` — controle positivo no mesmo instrumento.
10. Zero linha de producao alterada. Custo variavel **0**; sem tag e sem
    remoto; lease `p1a4-ops` vivo do inicio ao fim.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Medido |
|---|---|
| HEAD de abertura | `3f24085bc473c1dac575befd027e9775baac6150` |
| Arvore | limpa (`git status --porcelain` vazio) |
| Branch / tag / remoto | `master` / nenhuma / nenhum |
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** — nenhum mutante esquecido |
| Lease desta missao | `p1a4-ops`, fence **1**, pid 58184, renovado a 30 s |
| Suite `05_p0/tests` | **344 passed, 256 subtests** |
| Suite `06_p1a/tests` | **894 passed, 1201 subtests** |
| Prova central | **18 assercoes, 20 eventos** |

As duas suites **nao coletam juntas** (`21 errors during collection`):
sao rodadas separadamente, como sempre foram neste repositorio. Nao e
achado desta missao; e a forma de invocacao do acervo.

### 1.1 O ato do proprietario

O bloco recebido chegou com **`[preencher o tier]` literal** nas duas
linhas, e a declaracao em disco havia **vencido** — `2026-08-03T01:52:54Z`
mais 24 h contra `2026-08-04T02:37Z` medido na abertura, cerca de 45 min
de atraso.

A sessao **nao preencheu por conta propria**, pelo mesmo fundamento
registrado na P1-B.02 §1: `preflight/sombra.py` diz que a declaracao e
ato humano, *"nunca inferida pelo codigo"*, e o proprio bloco proibia
renovacao automatica. Os dois valores foram **confirmados pelo
proprietario antes da escrita**: `codex` = **ChatGPT Pro 5x**, `kimi` =
**Allegretto** — os mesmos ja declarados por ele em 01/08 e 03/08.

Copia de seguranca antes de sobrescrever, gravada **antes** da aquisicao
do lease (backup precede por regra o ato de sobrescrita, e nao e
evidencia): `06_p1a/evidencias/backups/tiers_declarados-2026-08-04-pre-p1a4.json`.

Gravacao pelo mecanismo vigente, **sem alterar formato nem leitor**: o
unico campo modificado foi `declarado_em_utc` nas duas declaracoes
(`git diff`: 2 linhas inseridas, 2 removidas, um so arquivo). Nenhuma
chave criada ou removida.

Verificacao pelo leitor canonico (`06_p1a/leitor_tiers.py` ->
`preflight.sombra`), e depois pelo portao de cada chamada:

| provedor | tier | declarado_por | expira em UTC | valido no instante |
|---|---|---|---|---|
| codex | `ChatGPT Pro 5x` | proprietario | 2026-08-05T02:40:33Z | **sim** |
| kimi | `Allegretto` | proprietario | 2026-08-05T02:40:33Z | **sim** |

### 1.2 Preflight dentro da capsula

`07_p1b/evidencias/preflight-20260804T024301Z.json`, rodado como
`python 06_p1a/capsula.py python 07_p1b/preflight_atual.py` com
`SSC_LOCK_SESSAO=p1a4-ops`:

    codex   SHADOW_ELIGIBLE  sombra=ChatGPT Pro 5x
    kimi    SHADOW_ELIGIBLE  sombra=Allegretto
    claude / google / grok   SUPERVISED

Zero chamada de modelo no preflight.

## 2. Pacote — NOVO sobre o HEAD atual

| Item | Valor |
|---|---|
| **SHA-256** | `a36471a34284cbcfc82efb669b3235fb57fd3dccc0aae4b024d0e9d5ca052c27` |
| Bytes / linhas | **1.312.291** / 28.546 |
| Gerador | `06_p1a/evidencias/pacote_p1a37.py`, **reusado sem uma linha alterada** |
| BASE | `6a3a3f8` |
| ALVO | `3f24085` |
| Commits entre BASE e ALVO | **96** |
| `.py` modificados (entram como diff) | 28 |
| `.py` novos (entram inteiros) | 74 |
| registros/evidencias (entram como SHA-256) | 89 |

Reproduzivel por terceiro com
`python 06_p1a/evidencias/pacote_p1a37.py 6a3a3f8 3f24085 <saida>`. O
pacote **nao foi versionado**: e funcao exclusiva de commits, e as quatro
geracoes da §2.2 mostram que qualquer um o reproduz byte a byte.

### 2.1 Por que o BASE e `6a3a3f8`

Porque **`6a3a3f8` e o ALVO do ultimo pacote que um revisor efetivamente
julgou** (P1-A.3.6). Tudo depois dele nunca passou por revisao
independente: as tres missoes de correcao P1-A.3.7/3.8/3.9 e a fase P2
inteira. O pacote da P1-A.3.8 (`b315d338…`, ALVO `bd055b9`) ficou
**PRONTO e NAO ENVIADO** — nao conta como estado julgado.

Escolher um BASE mais recente encolheria o pacote e esconderia
exatamente o trabalho que se pede para julgar.

**O gerador foi reusado de proposito.** Ele ja carrega as duas correcoes
que o MAJOR-5/N6 exigia (auto-inclusao do proprio fonte com SHA-256, e
portao que recusa o pacote **antes** de ele virar arquivo) e ja esta
marcado `-text` em `06_p1a/.gitattributes` — a correcao do defeito de
CRLF que a P1-A.3.8 achou ao executar. Gerador novo nasceria sem esse
historico. O revisor confirmou o efeito: **MAJOR-5 e MAJOR-N6 FECHADOS**.

### 2.2 Prova de ancoragem — executada ANTES do envio

| # | Prova | Resultado |
|---|---|---|
| 1 | Determinismo: duas geracoes em descartaveis **independentes** | `cmp` sem diferenca; mesmo SHA-256; mesmos 1.312.291 B |
| 2 | Ancoragem por commit: regeneracao em **clone limpo** com checkout de **outro** commit (`bd055b9`) | hash **identico** |
| 3 | Independencia da arvore: `05_p0/ssc_p0/contratos.py` (entra como diff) e `README.md` (entra como SHA-256) mutados de proposito | hash **inalterado** |

**A prova 3 falhou vazia na primeira tentativa, e isso fica registrado.**
Os dois arquivos escolhidos de inicio (`08_p2/medidor.py` e
`08_p2/README.md`) **nao existem** no commit em que o clone estava, e o
`>>` devolveu *No such file or directory*. O `cmp` passou verde sobre
**nenhuma mutacao**: prova vazia, do tipo que este repositorio classifica
como *alcance nao prova exercicio*. Foi refeita com dois arquivos que
existem no checkout **e** que o pacote julga, e so entao valeu.

### 2.3 Conteudo — varrido, nao prometido

**0** ocorrencias de: usuario local (forma longa e 8.3), caminho local
`E:\LucasIA`, UUID canonico, chave `sk-`/`xai-`/`AIza`, token `Bearer`.

O que **ha**, com o arquivo de cada um medido, e por que nenhum e
artefato da geracao:

| Ocorrencia | Onde | O que e |
|---|---|---|
| `C:/Users/<USUARIO>/.kimi-code/...` | `tests/test_p2_provedor_real_p2.py` | literal **ja redigido** dentro de fixture de teste |
| hex de 32 (`4bf725b0…`) | `tests/test_p2_receita_medidor_p24.py` | id da sessao do unico lab sobrevivente, literal no fonte julgado |
| `.coverage` | `tests/test_gitignore_efetivo_p1a39.py` | string de padrao, dentro do teste que mede o `.gitignore` |
| `2026-08-02T23:54:41Z` e outros 7 ISO | `evidencias/pacote_p1a36.py` e testes | literais **fixos** no fonte — e por serem fixos que o pacote reproduz |

Nenhum e carimbo do momento da geracao. As 79 mencoes a
`.lock/.lease/.fence` e as 9 a `__pycache__` sao constantes e padroes
**dentro** do codigo julgado, nao arquivos embarcados.

## 3. As duas chamadas — mesmos bytes, mesmos dois hashes

Os dois revisores receberam **os mesmos bytes**, copiados verbatim para o
descartavel de cada um, sem remontagem:

| Arquivo | SHA-256 | Bytes |
|---|---|---|
| `pacote-revisao.txt` | `a36471a3…` | 1.312.291 |
| `declaracoes-obrigatorias.txt` | `f31ad1b1…` | 7.602 |

**Por que as declaracoes vao em arquivo separado, e nao dentro do
pacote.** O pacote e funcao exclusiva de commits — e essa e a correcao do
MAJOR-5. As declaracoes sao ato **desta** missao, posterior ao ALVO;
embuti-las faria o pacote deixar de ser funcao dos commits e desfaria a
propria ancoragem. Elas vivem no fonte de
`06_p1a/evidencias/revisao_p1a4.py`, com SHA-256 registrado na evidencia
e **conferido pelo proprio revisor** — o codex ecoou os dois hashes
corretos.

As sete declaracoes obrigatorias transmitidas: ACHADO A (corrigido no
mecanismo a partir de `abc75e8`, **aberto**), ACHADO C (receita
versionada desde a P2.4, cobertura declarada — classe (a) 89,7 %
recontada, classe (b) 17,3 %), ACHADOS B e D intocados, as nove corridas
anteriores sem fotografia, `--ephemeral` nao impede escrita em
`CODEX_HOME`, os doze MAJOR com o remedio de cada, e o que mais o acervo
nao estabelece.

### 3.1 codex — o veredito, integral

`06_p1a/evidencias/revisao-p1a4/codex-20260804T025106Z.json` —
returncode **0**, **448,182 s**, modelo `gpt-5.6-sol`, uma chamada,
custo variavel zero.

**Os doze MAJOR, um a um:**

| MAJOR | Pronunciamento | Justificativa do revisor (resumo fiel) |
|---|---|---|
| 1 | **FECHADO** | le SQLite por copia incluindo WAL/SHM, propaga leitura impossivel como `P1A-CONFIG-NAO-LIDA` e exercita o caminho operacional |
| 2 | **FECHADO** | captura e interpreta numericamente `.0`, `00`, `0.00` e `0,0`, com contraprovas positivas e teste fim a fim no pipeline |
| 3 | **FECHADO** | remove a exclusao de `locks/`, separa deteccao de atribuicao, amplia a vigilancia e retira o rotulo de alcance integral |
| 4 | **FECHADO** | reverifica o mesmo fence no caminho real de `revisao_p1a2.main`, antes de `write_text` |
| 5 | **FECHADO** | inclui o fonte do gerador executado e o seu SHA-256, mantendo o resto ancorado nos blobs |
| 6 | **NAO-FECHADO** | `%`, `.format`, `join`, importacao dinamica e `getattr` ainda contornam a sentinela **sem gerar negacao** |
| N1 | **NAO-FECHADO** | declara e testa que o lock unico novo **nao esta em uso**; o mecanismo vivo continua permitindo escritores de nomes distintos |
| N2 | **FECHADO** | distingue fonte vazia de ausente, ilegivel, invalida ou truncada, e falha fechada em qualquer profundidade |
| N3 | **FECHADO** | o rotulo declara alcance efetivo, alvos vigiados, atribuicao e o restante nao vigiado, sem afirmar deteccao integral |
| N4 | **FECHADO** | redige `dir_descartavel`, `argv_publico` e o JSON integral nos cinco runners, com exercicio comportamental do caso real |
| N5 | **NAO-FECHADO** | a resolucao cobre os contornos enumerados, mas ha formas deliberadas ainda invisiveis e **nao negadas** |
| N6 | **FECHADO** | vincula pedido de julgamento, fonte auto-incluido e hash, recusando o pacote antes da criacao quando o objeto falta |

**Nove fechados, tres abertos.** Os tres que restam — 6, N1 e N5 — sao
**dois objetos**: a sentinela que contorna sem negar (6/N5) e o escritor
unico que existe mas nao foi adotado (N1). Continuam com contagem
separada, pela mesma regra da P1-A.3.6 §9.4.

**Os quatro achados da P2:**

| Achado | Pronunciamento | Justificativa do revisor (resumo fiel) |
|---|---|---|
| A | **NAO-FECHADO** | ha escrita em `CODEX_HOME` fora das fontes vigiadas, e o recibo ainda publica `efeito_externo: nenhum` quando apenas o alcance parcial ficou imovel |
| B | **NAO-FECHADO** | o README continua prometendo codex e kimi, e o kimi nunca completou uma corrida |
| C | **NAO-FECHADO** | a aritmetica recalcula, mas 21 % dos bytes seguem testemunho, nenhuma resposta alternativa foi gravada e uma corrida nao tem recibo |
| D | **NAO-FECHADO** | o indice da raiz ainda omite os registros P2.1 e P2.2 usados pelos numeros publicados |

**`DEFEITO-NOVO: SIM`** — `08_p2/provedor_assinatura.py:invocar` cria um
`mkdtemp` por tentativa e **nunca o remove**; e
`06_p1a/tests/test_config_real_p1a39.py` introduz um **guarda falso** que
ignora a leitura efetiva de `~/.codex/config.toml`.

**Os seis MAJOR novos, com a familia que o revisor atribuiu:**

| # | Objeto | Achado | Familia |
|---|---|---|---|
| P1A4-1 | `06_p1a/escritor_repositorio.py:adocao` | o escritor unico correto existe **so isoladamente**; o mecanismo operacional continua sendo o defeituoso por sessao — falha de **integracao** | fora de ambas |
| P1A4-2 | `06_p1a/tests/sentinela_antip2.py:resolucao` | `%`/`.format`/`join` e imports dinamicos atravessam a varredura sem negacao | **(N)** |
| P1A4-3 | `08_p2/provedor_assinatura.py:efeito-externo` | o recibo afirma `nenhum` apesar do alcance parcial e da escrita conhecida em `CODEX_HOME` | **(F)** |
| P1A4-4 | `08_p2/medidor.py:reprodutibilidade` | a receita recompoe numeros com insumos testemunhais; nao permite recontar as respostas alternativas nem a corrida sem recibo | fora de ambas |
| P1A4-5 | `08_p2/runner_p2.py:persistencia` | `relatar(registro)` permanece **antes** da reverificacao e da gravacao; nova falha de saida pode consumir franquia e perder o recibo outra vez | fora de ambas |
| P1A4-6 | `06_p1a/tests/test_config_real_p1a39.py:acoplamento` | o teste calcula "auditados" so por `FONTES`, embora `config_persistida("codex")` leia e mescle `~/.codex/config.toml`: **afirma um buraco inexistente sem exercer a interface real** | **(F)** |

Mais **tres MINOR** (`provedor_assinatura.py:ciclo-de-vida`, bloqueante
para aprovacao sem ressalvas; `README.md:provedores-produtivos` e
`README.md:indice-P2`, nao bloqueantes isoladamente) e **dois OBS**,
todos `fora de ambas`.

**`VEREDITO: REPROVADO`.**

### 3.2 kimi — cota do ciclo esgotada, pela quarta vez

`06_p1a/evidencias/revisao-p1a4/kimi-20260804T030243Z.json` — returncode
**1**, **5,6 s**, resposta **vazia**:

    error: failed to run prompt: provider.api_error: 403 You've reached
    your usage limit for this billing cycle.

O proprietario declarou, antes do envio, que **nao sabia** se a cota
havia sido renovada, e pediu que se medisse na hora. Mediu-se: **nao
foi**. O erro veio do **provedor**, nao do parser — o argv chega, o
modelo nao responde. `kimi -p` segue **sem nenhum caminho de sucesso
validado**, agora em quatro tentativas.

Nao ha veredito do kimi. A metade do portao que dependia dele falha por
**ausencia de medicao**, e ausencia de medicao nao e ressalva: e o
oposto de um veredito favoravel.

## 4. Portao

| Exigencia do ato | Medido | Passa? |
|---|---|---|
| zero CRITICAL nos dois vereditos | 0 CRITICAL no unico veredito existente | **nao** — falta um veredito |
| zero MAJOR nos dois vereditos | **6 MAJOR novos** + 3 dos doze ainda abertos | **nao** |
| pronunciamento explicito por MAJOR | 12 de 12, um por linha | sim |
| pronunciamento sobre defeito novo | `DEFEITO-NOVO: SIM`, com objeto e lugar | sim |
| classificacao por familia | em **todos** os achados | sim |
| mesmos bytes aos dois revisores | dois hashes identicos, conferidos pelo codex | sim |

**As duas metades falharam por causas independentes**, e fechar uma nao
abre a outra: ainda que o kimi respondesse APROVADO, os seis MAJOR novos
do codex reprovariam o portao; ainda que o codex nao tivesse achado nada,
a ausencia do kimi deixaria o portao com **uma** medicao onde o ato exige
duas.

### 4.1 Por que NAO e BLOCKED — disposicao formal

A leitura contraria existe e precisa de resposta escrita, nao de
silencio: o ato diz, nas PRE-CONDICOES, *"Declaracao vencida ou quota
ausente: BLOCKED"*, e a quota do kimi **estava** ausente. Por que, entao,
a decisao nao e BLOCKED?

**Primeiro: a quota nao e afericao daquele portao.** A frase esta na
secao PRE-CONDICOES, e o mecanismo que as afere e o preflight. Ele
devolveu, nesta corrida, `quota: "desconhecida"` para **todos os cinco
provedores** — inclusive o codex, que depois respondeu por 448 s. Quota
ausente nao foi medida no portao porque **nao e mensuravel nele**; ela so
aparece quando o provedor responde. Tratar "desconhecida" como "ausente"
reprovaria toda missao ja na abertura, inclusive as que deram certo.

**Segundo: o proprietario decidiu explicitamente o contrario.** Antes do
envio, perguntado se a cota havia sido renovada, ele respondeu *"nao sei
— mede na hora"*, escolhendo entre duas saidas oferecidas: parar por
quota ausente, ou medir na chamada. Ele escolheu medir. A quota foi
medida, e o resultado esta na §3.2.

**Terceiro: ha precedente no proprio repositorio, na mesma situacao.** A
P1-A.3.6 recebeu o kimi recusado por cota de ciclo esgotada, ficou com um
so veredito, e decidiu **ADJUST** — nao BLOCKED. Mais que precedente: o
criterio de parada hoje gravado no `CLAUDE.md` **se funda naquela
medicao**. Se a ausencia do kimi tivesse tornado aquela missao BLOCKED,
o criterio que agora dispara nao existiria.

**Quarto, e decisivo: BLOCKED significa "nao houve medicao", e houve.**
Esta missao obteve um veredito completo — doze pronunciamentos por MAJOR,
quatro por achado, defeito novo, familia em cada achado. Rotular isso
BLOCKED **descartaria a medicao** e, com ela, esconderia que o criterio
de parada disparou. O `CLAUDE.md` diz, com todas as letras, que relatorio
sem classificacao por familia *"equivale a manter a trilha aberta por
falta de medicao, que e exatamente o que este criterio existe para
impedir"*. BLOCKED aqui produziria esse efeito **tendo a medicao em
maos** — o pior dos casos.

**O que o portao da missao registra, e nao se apaga:** ele falhou nas
duas metades, e a §4 mede isso. BLOCKED e STOP nao sao graus do mesmo
eixo — BLOCKED diz *"nao deu para medir"*; STOP diz *"mediu-se, e a
medicao manda parar"*. O segundo e o caso.

**Ambiguidade real do ato, para o Fundador decidir em despachos
futuros.** A frase *"quota ausente: BLOCKED"* pode ser lida como portao
de abertura (a leitura aplicada aqui, e a do precedente) ou como
condicao que vale em qualquer instante da missao. As duas leituras sao
defensaveis pelo texto. Esta missao aplicou a primeira, declara que o
fez, e registra que a segunda existe — quem escreve o proximo ato pode
fecha-la numa frase.

## 5. O criterio de parada do `CLAUDE.md` — medido e classificado

O criterio exige as duas contas. Aqui estao as duas:

| Condicao | Limiar | Medido | Disparou? |
|---|---|---|---|
| **(a)** defeitos NOVOS | **6 ou mais** | **6** MAJOR novos | **SIM** |
| **(b)** familia do MAJOR #3 — afirma em vez de exercer | **4 ou mais** | **2** em (F) | nao |

Classificacao por familia dos seis novos, **atribuida pelo revisor** e
nao por esta sessao: **(F) = 2** (P1A4-3 e P1A4-6), **(N) = 1**
(P1A4-2), **fora de ambas = 3** (P1A4-1, P1A4-4, P1A4-5). Contando
tambem os tres MINOR e os dois OBS, todos `fora de ambas`, o quadro dos
onze achados fica **(F) = 2, (N) = 1, fora de ambas = 8**.

**A condicao (a) disparou no limiar exato.** O ato manda, com essas
palavras: *"nao abrir nova missao de correcao. Retornar ao Fundador com
a medicao e a classificacao por familia."* Por isso a decisao e **STOP**,
e nao ADJUST — ADJUST abriria a proxima rodada de conserto, que e
precisamente o que o criterio existe para impedir.

**O que a medicao mostra, sem interpretar alem dela.** Esta foi a
primeira rodada com **saldo positivo** nos MAJOR de origem: nove dos doze
fecharam, contra **zero em tres ciclos** anteriores. E, ao mesmo tempo,
seis novos apareceram — e tres deles vivem na fase P2, que **nunca havia
passado por revisao nenhuma**. As duas frases sao verdadeiras juntas, e
nenhuma cancela a outra. Decidir o que fazer com isso e do Fundador; a
missao entrega a medicao.

## 6. Achado desta missao contra o proprio instrumento — pela segunda vez

A contencao acusou mutacao fora do descartavel na corrida do codex:

    "violada": true,
    "mutacoes_fora_do_descartavel": [
      "alterado: repositorio/.pytest_cache/v/cache/lastfailed",
      "alterado: repositorio/06_p1a/__pycache__/leitores_config…pyc",
      "alterado: repositorio/06_p1a/tests/__pycache__/test_redacao…pyc",
      "alterado: repositorio/06_p1a/tests/test_redacao_operacao_p1a39.py"
    ]

**A causa foi esta sessao**, e a atribuicao e certa: enquanto o codex
lia o pacote, a sessao rodava a suite e editava aquele arquivo de teste.
Nao e escrita do revisor — o codex correu com `--sandbox read-only --cd
<descartavel> --skip-git-repo-check --ephemeral`, e os unicos arquivos
restantes no descartavel sao os **dois que a missao pos la**.

**Controle positivo, medido no mesmo instrumento.** A corrida seguinte,
do kimi, correu com a arvore em silencio e devolveu
`mutacoes_fora_do_descartavel: []`, `violada: false`. Mesmo instrumento,
duas corridas, dois resultados opostos conforme a sessao escrevia ou nao:
o guarda **mede o que diz medir**.

**O que agrava: e a segunda ocorrencia, e a primeira ja tinha remedio
escrito.** A P1-A.3.6 §6 registrou o mesmo evento e especificou o
remedio: *"enquanto (a) atribuicao nao existir, a sessao nao escreve no
repositorio durante a janela da chamada, e isso e disciplina de operacao,
nao propriedade do codigo"*. A disciplina foi quebrada nesta missao.
**Disciplina que depende de quem opera nao e guarda** — e essa e a
licao, medida duas vezes.

| Campo | Valor |
|---|---|
| **Dono** | a missao que tratar o MAJOR-3 / `contencao.py:atribuicao` |
| **Gatilho** | proxima revisao independente |
| **Remedio especificado** | atribuicao real do escritor (a pergunta *"quem escreveu?"*, hoje nao respondida), ou porta que **impeca** a sessao de escrever durante a janela — nao mais um aviso a ser lembrado |
| **Corrigido nesta missao?** | **Nao** — missao probatoria |

**Por que o veredito nao foi descartado nem refeito.** A resposta do
codex e alheia a essa mutacao por construcao: ele julgou bytes fixados
**antes** da chamada, ecoou os dois SHA-256 corretos, e nao tinha como
ver — nem nomear — arquivos da arvore de trabalho. Descartar o veredito
gastaria uma segunda chamada da assinatura para reproduzir um julgamento
que a mutacao nao pode ter tocado. O precedente da P1-A.3.6 e o mesmo:
manteve o veredito e registrou a violacao com atribuicao.

## 7. O que esta missao alterou fora do previsto — declarado, nao escondido

O ato diz *"nao altera codigo, teste nem politica"*. Esta missao alterou
**duas linhas, em dois arquivos de teste**, e nenhuma outra:

| Arquivo | Alteracao | Por que o repositorio a exigiu |
|---|---|---|
| `tests/test_redacao_operacao_p1a39.py` | +1 entrada em `_RUNNERS` | a classe `OsRunnersGravamRedigido` roda o `main()` **real** de cada runner registrado e exige que o JSON gravado carregue `<USUARIO>` e `<CAMINHO-LOCAL>` |
| `tests/test_portao_tier_operacao_p1a39.py` | +1 entrada em `RUNNERS_COM_PORTAO` | o corpus descoberto por AST exige que todo runner que define `_verificar_tier` seja exercido por `main()` |

**A causa e um guarda funcionando.** Os dois corpora da P1-A.3.9 sao
**descobertos por AST**, nao listas escritas a mao: no instante em que
`revisao_p1a4.py` nasceu, a suite ficou **vermelha em tres testes**,
porque um modulo novo redigia PII e verificava tier sem ninguem exercer
nenhum dos dois. Deixa-lo de fora seria reintroduzir os achados 7, 10 e
14 — *a copia que ninguem exercita e fica para tras*.

**O tradeoff foi levado ao proprietario antes de qualquer edicao**, com
as tres saidas possiveis (registrar; deixar a suite vermelha; manter o
instrumento fora do acervo). Ele escolheu **registrar**.

**Nenhum criterio de guarda foi alterado, nenhuma linha de producao foi
tocada, e nenhum achado foi corrigido.** As duas entradas **nao entram no
pacote**: sao posteriores ao ALVO `3f24085`, entao nada do que o revisor
julgou depende delas. Depois das duas, as suites voltaram verdes:
**344 + 256** e **894 + 1217** — 16 subtests a mais que na abertura, que
sao exatamente o instrumento novo sendo exercido.

## 8. Alcance — o que esta missao estabelece e o que NAO estabelece

### 8.1 Estabelecido — medido

| Fato | Como |
|---|---|
| O estado `3f24085` foi submetido a revisao independente | pacote `a36471a3…`, 1.312.291 B, quatro geracoes com um so hash |
| Nove dos doze MAJOR fecharam | pronunciamento explicito, um por linha, com localizacao apontavel no pacote |
| Tres dos doze seguem abertos (6, N1, N5) | idem |
| Os quatro achados da P2 seguem abertos, o A inclusive | idem |
| Seis MAJOR novos, com familia | atribuidos **pelo revisor**, nao por esta sessao |
| O criterio (a) do `CLAUDE.md` disparou; o (b) nao | 6 novos contra limiar 6; 2 em (F) contra limiar 4 |
| O instrumento de contencao mede o que diz medir | duas corridas, dois resultados opostos, mesma janela |

### 8.2 NAO estabelecido — e nao se presume

- **Nada foi certificado.** Um veredito REPROVADO nao e atestado de
  aprovacao de nada, e os nove MAJOR "fechados" o foram por **um**
  revisor, num **unico** pronunciamento;
- **o kimi nao disse nada** — nem a favor, nem contra. Quatro tentativas,
  zero vereditos. Nao se sabe o que um segundo revisor acharia;
- **os seis MAJOR novos nao foram verificados por esta sessao.** Sao o
  que o revisor afirma; conferi-los seria julgar o proprio julgamento, e
  esta missao nao corrige nem confere achado;
- **a P2 continua sem certificacao**, e agora com tres MAJOR abertos
  sobre ela;
- **as nove corridas anteriores a `abc75e8` seguem sem fotografia** —
  nada aqui alcanca o passado;
- **a tese central segue nao medida em token.**

## 9. ATESTADO

**Esta missao nao corrigiu nada, e por isso podia submeter.** As
correcoes sob julgamento vieram das missoes P1-A.3.7, P1-A.3.8 e
P1-A.3.9, e da fase P2; nenhuma delas emitiu atestado de fechamento.
O revisor falou: fechou nove, manteve tres, abriu seis novos e reprovou.

**O que seria falha, e nao foi feito:** corrigir aqui para o portao
passar; encolher o pacote escolhendo um BASE mais recente para caber;
tratar a ausencia do kimi como ressalva; esconder que a contencao acusou
a propria sessao; ou omitir as duas linhas de teste da §7.

**O que ficou aquem, e esta escrito:** a disciplina de nao escrever no
repositorio durante a janela da chamada foi quebrada — segunda ocorrencia
do mesmo evento, com remedio ja especificado desde a P1-A.3.6. E a prova
de ancoragem 3 passou vazia na primeira tentativa e so foi valida na
segunda; se nao tivesse sido reconferida, teria entrado neste registro
como prova.

**Contagem como medida, nunca como meta.** Os numeros deste atestado —
9 fechados de 12, 6 novos, 2 em (F), 4 falhas consecutivas do kimi — sao
o que foi medido. Nenhum e alvo a perseguir.

**DECISAO: STOP**, pelo criterio (a) do `CLAUDE.md` da raiz. Nao abrir
nova missao de correcao. A medicao e a classificacao por familia estao
nas §3.1 e §5, e a decisao sobre o que fazer com elas e do Fundador.
