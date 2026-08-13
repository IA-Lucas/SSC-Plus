# P1-A.11 — segunda rodada de revisao independente sobre 6/P1A4-2/P1A4-4

> Registro da missao que despachou a revisao. Quem corrige nao
> certifica; os fechamentos abaixo sao **do revisor**, nao do autor. Os
> DOIS pareceres chegaram na mesma sessao de despacho — nao ha parecer
> pendente nesta rodada. **A palavra final sobre os divididos e do
> Fundador**, com os dois pareceres na mao — esta missao NAO arbitra.

## O que mudou desde a P1-A.10

A P1-A.10 julgou nove ids por dois revisores; cinco fecharam por
consenso, P1A4-6 fechou pela regra de um revisor, N5 ficou aberto por
decisao do Fundador, e **6/P1A4-2/P1A4-4 ficaram divididos** — o codex
os leu NAO-FECHADO contra o pacote que tinha diante de si, o kimi os
leu FECHADO **lendo correcoes que vieram DEPOIS do ALVO daquele
pacote** (`99_correcao-residuos-p1a10.md`). O Fundador arbitrou:
aguardam o proximo ciclo, com as correcoes ja prontas para um revisor
ver o estado atual.

Esta missao e esse proximo ciclo. Pacote: BASE `f799883` (o mesmo ALVO
julgado na P1-A.10) → ALVO `3ff94e6` (HEAD desta missao), 8 commits, 74
caminhos no diff (17+2 lidos, 55 ancorados, 0 sobra — portao de
cobertura passou sem nova divergencia). `pacote_p1a10.py` foi reusado
sem edicao. `sha256` do pacote: `175b04f1...898a27c7`.

## Os tres ids, pelos dois pareceres

| id | codex | kimi | Consenso |
|---|---|---|---|
| **6** | NAO-FECHADO | NAO-FECHADO | **NAO-FECHADO por ambos** |
| **P1A4-2** | NAO-FECHADO | NAO-FECHADO | **NAO-FECHADO por ambos** |
| **P1A4-4** | NAO-FECHADO | FECHADO (no mecanismo) | dividido |

**6 e P1A4-2 continuam abertos, pelos dois revisores, com diagnostico
mais preciso do que antes.** Os dois apontam a MESMA lacuna, por
angulos complementares:

- **codex**: `x = "".join(partes); if resposta == x:` — construtor
  atribuido a variavel ANTES da comparacao continua invisivel; o
  despacho sem `ast.Compare` e maior do que o registro declarou.
- **kimi**: a deteccao so cobre construtor DIRETO e `.decode`/`.format`/
  `.join` sobre `ast.Constant`; `nome.decode()`, `base64.b64decode(...)`
  e construtor aninhado em ARGUMENTO de chamada atravessam — dois dos
  tres vetores que o proprio registro de residuo nomeia (base64, dado
  externo) seguem sem negacao no ponto de decisao.

Os dois leem o MESMO defeito: a correcao da P1-A.10 (`9b44025`) fechou
a fatia literal do buraco e deixou aberta a fatia que passa por
variavel, atributo ou argumento — exatamente a classe que o proprio
residuo dizia ter fechado.

**P1A4-4 divide OTRA VEZ, na MESMA direcao da P1-A.10**: codex le o
teste da ancora cruzada como "concordancia sintetica" (quem escreve o
manifesto pode escrever o recibo com o mesmo hash — a ancora detecta
DIVERGENCIA, nao fabricacao conjunta) e cobra a corrida real ponta a
ponta que ainda nao aconteceu; kimi aceita o mecanismo com os limites
declarados (export por etapa fiado no diff, ancora testada nos dois
sentidos) como fechamento valido, com a corrida real como pendencia
declarada e aceitavel.

## Os tres itens do registro de residuos (`99_correcao-residuos-p1a10.md`)

| item | O que | codex | kimi |
|---|---|---|---|
| 1 | TOCTOU do snapshot | NAO-SUSTENTADO — teste exerce vizinho (junction estatica), nao a troca concorrente | SUSTENTADO — mesma primitiva do runner, limite honesto declarado |
| 2 | Negacao no ponto de decisao (6/P1A4-2) | NAO-SUSTENTADO | NAO-SUSTENTADO — cobertura real menor que a declarada |
| 3 | Fluxo exporta + ancora cruzada (P1A4-4) | NAO-SUSTENTADO | SUSTENTADO |

**Item 2 e NAO-SUSTENTADO pelos DOIS** — e o unico dos tres com
consenso negativo, e e exatamente o que sustenta 6/P1A4-2 continuarem
abertos.

## O commit fora de escopo (`3ff94e6`, guardas de infraestrutura de CI)

- **codex: FORA-DE-ESCOPO NAO-SUSTENTADO** — `GITHUB_ACTIONS=true` +
  nome nominal nao prova ausencia de proprietario, sobretudo em runners
  autohospedados; contas amplas (`root`, `admin`, `user`) podem fazer
  guardas reais pularem por heuristica.
- **kimi: FORA-DE-ESCOPO SUSTENTADO** — as DUAS provas sao exigidas
  juntas, os testes provam que nenhuma sozinha desliga o guarda, o skip
  grava motivo apontavel e o controle positivo continua rodando em CI;
  ressalva de PROCESSO (nao de mecanismo): commit sem registro
  `99_*.md` proprio, justificativa so em docstring.

Dividido. Os dois concordam num ponto que nao estava nas declaracoes
desta missao: o commit nao tem registro proprio.

## Errata do autor — DECLARADO-b, achado real desta rodada

A DECLARACAO desta missao afirmava, na secao 3: *"dois pareceres JA
disseram NAO-FECHADO para os tres ids com a MESMA razao"*.

- **codex: DECLARADO-b NAO-CONFIRMO** — correto. `99_decisao-p1a10.md`
  registra DIVERGENCIA, nao consenso: o codex leu NAO-FECHADO, o kimi
  leu FECHADO (os tres ids) lendo as correcoes pos-ALVO. Nao houve
  "dois pareceres dizendo NAO-FECHADO" — houve um parecer dividido.
- **kimi: DECLARADO-b CONFIRMO** — incorreto. A leitura do kimi (nesta
  rodada) casou a frase com a secao "Estado declarado pelo autor" da
  DECLARACAO da P1-A.10 (que descrevia o estado ANTES de qualquer
  parecer), nao com a tabela de divergencia que registra o voto real do
  kimi anterior.

**Conferido diretamente contra `99_decisao-p1a10.md` linhas 85-87**: o
codex esta certo, a declaracao desta missao estava ERRADA, e o kimi
confirmou uma alegacao falsa. Isto e um achado NOVO contra o autor,
nao antecipado nas declaracoes — a propria missao que escreve
"declaracoes obrigatorias" errou um fato conferivel na primeira fonte
que deveria ter consultado antes de escrever a frase. FAMILIA: **(F)**
— e uma DECLARACAO que AFIRMA (de memoria) em vez de EXERCER (conferir
contra o registro) exatamente o vicio que a familia F nomeia, agora no
proprio autor do pacote e nao num guarda de codigo.

## Defeito novo — os dois dizem SIM, em lugares DIFERENTES

- **codex**: `contencao.py:usuario_e_infraestrutura` — o bypass e amplo
  demais para runner autohospedado legitimo.
- **kimi**: `sentinela_antip2.py:_construtor_direto_nao_resolvido` — a
  subcobertura sintatica do proprio mecanismo introduzido pela
  correcao de residuo (mesmo objeto do item 2 acima, faceta "defeito
  novo" em vez de "correcao nao fechou").

Nao e o MESMO defeito nomeado duas vezes — sao dois objetos distintos.

## Achados novos, catalogados por revisor

**codex** (5, alem do DECLARADO-b ja tratado acima como achado a
parte):
1. `sentinela_antip2.py:comparacoes_nao_resolvidas` — construtor
   atribuido a variavel atravessa. AREA JA REVISADA. FAMILIA (N).
2. `medidor.py`+`executar_fluxo.py:ancora-do-original` — concordancia
   sintetica tratada como independencia. AREA JA REVISADA. FAMILIA (F).
3. `test_contexto_workspace_p2.py:TOCTOU` — teste exerce vizinho.
   AREA JA REVISADA. FAMILIA (F).
4. `contencao.py:usuario_e_infraestrutura` — bypass amplo demais.
   AREA JA REVISADA. FAMILIA (F).
5. `declaracoes-obrigatorias.txt:historico-dos-pareceres` — a errata
   acima. **ESTREIA** (pacote da P1-A.10 nao continha estas
   declaracoes). FAMILIA (F).

**kimi** (4, alem do DEFEITO-NOVO ja tratado acima):
1. `sentinela_antip2.py:comparacoes_nao_resolvidas` — subcobertura
   sintatica (mesmo objeto do #1 do codex, angulo diferente: DIRETO-only
   em vez de "atravessa variavel"). AREA JA REVISADA. FAMILIA
   fora-de-ambas (a leitura do kimi classifica como "mecanismo que
   existe e executa", nao guarda que afirma sem exercer).
2. `99_correcao-residuos-p1a10.md` item 2 — alcance descrito maior que
   o exercido (o registro nomeia so o limite de `ast.Compare`, omite
   DIRETO-only e so-literal). **ESTREIA** (documento nasceu depois do
   ALVO da P1-A.10). FAMILIA (F).
3. `medidor.py:_resolver_insumo` — independencia da ancora e procedural,
   nao verificada (mesmo objeto do #2 do codex, angulo "quem escreve o
   manifesto pode escrever o recibo"). AREA JA REVISADA. FAMILIA
   fora-de-ambas.
4. `test_contexto_workspace_p2.py` — guarda de junction so roda em
   Windows, degrada por `skipTest` fora dele. AREA JA REVISADA. FAMILIA
   fora-de-ambas.

**Candidatos a fusao, que esta missao NAO decide** (a contagem e do
Fundador, como em toda rodada anterior): codex #1 + kimi #1 (mesmo
objeto, mesma raiz — DIRETO-only); codex #2 + kimi #3 (mesmo objeto —
ancora procedural); codex #4 + a ressalva de processo do kimi sobre o
mesmo commit (objetos relacionados, angulos distintos: logica amplas
demais vs. registro ausente).

## Criterio de parada — medido com os DOIS pareceres, sem fusao aplicada

| Condicao | Limiar | Bruto (sem fusao) | Minimo defensavel (com as fusoes obvias acima) |
|---|---|---|---|
| (a) novos em area ja revisada | 6+ | **7** (4 codex + 3 kimi, excluindo as 2 ESTREIA) | **5**, se as duas fusoes de mesmo-objeto (codex#1+kimi#1; codex#2+kimi#3) forem aceitas — cai ABAIXO do limiar |
| (b) familia (F) | 4+ | **5** (codex #2 ancora, #3 TOCTOU, #4 usuario_e_infraestrutura, #5 declaracoes-obrigatorias + kimi #2 residuos-doc) | **4**, fundindo codex#2 com a ressalva de processo do kimi sobre o mesmo commit — a UNICA fusao que localizei dentro da propria familia F. Ainda em cima do limiar |
| (c) saldo nos MAJOR de origem | nao-positivo | **0** — nenhum dos tres ids fechou por consenso nesta rodada; zero e nao-positivo pela propria letra da regra (o fundamento da P1-A.5 nomeia "saldo ZERO" como o caso que (c) existe para pegar) | **0**, a menos que o Fundador invoque para o P1A4-4 a MESMA regra de um revisor que fechou o P1A4-6 na P1-A.10 — nesse caso +1 |

**Corrigi um erro de contagem na primeira passada deste registro**: a
familia (F) bruta e **5**, nao 4 — eu tinha deixado de fora o achado #3
do codex (TOCTOU, tambem FAMILIA F). Com a correcao, **(b) dispara no
bruto E continua disparando no minimo defensavel** — nao encontrei
fusao suficiente para tira-lo do limiar. **(c) tambem dispara no
bruto**, e so deixa de disparar por uma DECISAO do Fundador (nao por
medicao). **Das tres condicoes, (a) e a UNICA que resolve limpa por
fusao razoavel; (b) e (c) permanecem disparadas sob a leitura mais
generosa que consegui construir.**

Isto e diferente de toda rodada anterior desde a P1-A.5: nas anteriores
a folga era clara mesmo bruta (P1-A.10: (a) 3 contra 6, (b) 1 contra
4). Aqui, pela primeira vez desde que o criterio (c) foi criado, **duas
das tres condicoes sobrevivem a fusao**. Pela letra da propria regra do
`CLAUDE.md` — *"Disparado o criterio: nao abrir nova missao de
correcao. Retornar ao Fundador com a medicao e a classificacao por
familia"* — esta missao PARA aqui: nao abre uma P1-A.12 de correcao por
iniciativa propria. A medicao acima e a entrega.

## O que NAO se decide aqui

- se 6/P1A4-2 recebem nova tentativa de correcao ou se o residuo vira
  limite PERMANENTE declarado (como N5 ja e);
- se P1A4-4 fecha pela leitura do kimi ou espera a corrida real que o
  codex cobra;
- se o commit `3ff94e6` fica como esta, ganha registro `99_*.md`
  proprio, ou tem o bypass revisado;
- a fusao exata dos achados novos, e se ela e suficiente para desarmar
  (b) — a medicao acima mostra que NAO chega a desarmar com as fusoes
  que esta missao conseguiu justificar, mas a palavra final sobre
  fusao e do Fundador, nao deste registro;
- se o P1A4-4 fecha pela regra de um revisor (como o P1A4-6 fechou na
  P1-A.10) — essa decisao, se tomada, muda (c) de disparado para
  nao-disparado; sem ela, (c) fica disparado.

## Plataforma — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao). Ambos os
pareceres com contencao limpa (`mutacoes_fora_do_descartavel: []`),
hashes de pacote/declaracoes/registros conferidos pelos dois canais
(codex ecoou os declarados por nao ter ferramenta; kimi computou os
tres com `sha256sum` e todos bateram).
