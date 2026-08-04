---
id: SSC-DEC-P1A51
titulo: Registro e Decisao da Missao SSC+ P1-A.5.1 — o par que virou fracao, o cache fora da arvore, e a porta que fica registrada
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-04
---

# Registro e Decisao — Missao SSC+ P1-A.5.1

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**. Missao curta, de **duas correcoes e um
> registro** — e por isso ela **nao certifica nada**.

## DECISAO: **CONCLUIDO**

As tres ordens executadas. Nada ficou por fazer, e nada foi construido
alem do ordenado: **a porta nao foi construida**, e `icacls` nao foi
usado nesta missao.

## SUMARIO — 10 linhas

1. **`18/20` corrigido** no `06_p1a/99_decisao-p1a5.md:63`, com nota de
   correcao no proprio documento. Nenhum outro historico foi tocado.
2. Medido antes de corrigir: `prova_central.py` tem **um commit em toda
   a historia** e blob identico ao da baseline — **nenhuma assercao
   apareceu**. `18` e `20` sao **duas grandezas**, nunca uma fracao.
3. A regra entrou no **`CLAUDE.md` da raiz**, onde toda sessao le, com o
   fundamento medido e a forma correta: o par, com o nome de cada um.
4. **Cache fora da arvore vigiada**: `pytest.ini` (`-p
   no:cacheprovider`) e `conftest.py` da raiz (`sys.pycache_prefix`).
5. Prova com invocacao **simples** — sem env e sem flag extra, de modo
   que so funciona se a configuracao estiver **aplicada**: **0 mutacoes**
   nas quatro condicoes, pelo `contencao.manifesto`.
6. **Reversao vermelha (M7)**: desfeita a configuracao, voltam **3**
   mutacoes `.pyc` nas mesmas quatro condicoes, mais **2** do
   `.pytest_cache` numa corrida que falha — **cinco** ao todo.
7. As duas escolhas foram **medidas, nao estilizadas**: relocar o cache
   do pytest exigiria caminho absoluto em arquivo versionado, e caminho
   absoluto carrega o nome do usuario local.
8. **Tres das quatro** mutacoes da P1-A.4 eram **subproduto**, e somem
   sem porta nenhuma. A **quarta** — a sessao editando um fonte — nao e
   alcancada por realocacao e continua aberta.
9. **A porta fica REGISTRADA como possivel** (§3), com mecanismo medido,
   custo, o que quebraria, o novo modo de falha e a ressalva: ela
   **impede**, nao **atribui**.
10. Custo variavel **0**; nenhuma chamada a provedor; suites **344+256**
    e **914+1241**, identicas as de antes da configuracao.

## 1. ORDEM 1 — o par que virou fracao

Commit **`3c23f20`**.

### 1.1 O que estava errado, e o que nao estava

O sumario da P1-A.5 escrevia *"Prova central **18/20**"*. O **mesmo
documento**, catorze linhas abaixo, registrava `18 assercoes, 20 eventos`
— a forma correta. Ele se contradizia consigo mesmo.

**Nao e erro de digitacao, e e pior que um.** A fracao inventa um
denominador que nao existe e faz o par ler como *"vinte assercoes, duas
falhando"* — isto e, transforma um relatorio verde num relatorio com duas
falhas silenciosas.

### 1.2 A apuracao, antes da correcao

| Pergunta | Medido |
|---|---|
| Quantas assercoes a prova tem hoje? | **18** — `assercoes` e lista de 18 no JSON de saida |
| Quantos eventos? | **20** — `eventos` e lista de 20, lidos do ledger; **outra grandeza** |
| Quantas tinha antes? | **18** — o fonte imprime `len(assercoes)` e `len(eventos)` |
| Quais duas apareceram? | **nenhuma** |
| Em qual commit, por qual missao? | `05_p0/cenarios/prova_central.py` tem **um unico commit em toda a historia** (`33bc963`, 2026-07-30, *experimental baseline*), e o blob no HEAD (`3787ba44…`) e **byte a byte igual** ao daquele commit |

O par `18 assercoes, 20 eventos` esta registrado assim desde a P1-A
(`04_suite-preflight-e-correcoes.md`), e igual na P1-B.00, na P2.3, na
P2.4 e na P1-A.4. O `18/18` que aparece em dezoito arquivos e a **fracao
de aprovacao** — *dezoito de dezoito passaram* —, esta correto, e **nao
foi tocado**.

E `18/20` aparecia **uma unica vez em todo o acervo**: naquela linha,
introduzida pelo commit `c83839a`, da propria P1-A.5.

### 1.3 O que foi corrigido, e o que nao

Corrigida **so a linha 63**, que e desta trilha e estava errada, com uma
nota de correcao no proprio documento declarando o que dizia antes e por
que mudou. **Nenhum historico de outro documento foi reescrito.**

A regra entrou no `CLAUDE.md` da raiz, secao *"Duas grandezas nunca viram
fracao"*, para que toda sessao a leia sem precisar achar este registro.

## 2. ORDEM 2 — o cache sai da arvore vigiada

Commit **`f4b0a5a`**.

### 2.1 O que se aplicou, e por que nao e politica

| Arquivo | O que faz |
|---|---|
| `pytest.ini` | `addopts = -p no:cacheprovider` — o pytest para de escrever `.pytest_cache/` |
| `conftest.py` (raiz) | `sys.pycache_prefix` aponta o bytecode para fora da arvore |

**Nao muda politica, nem guarda, nem criterio.** Bytecode e cache de
teste sao subproduto: o fonte e a verdade, e nada no acervo le `.pyc`.
As suites devolveram **exatamente os mesmos numeros** de antes —
**344+256** e **914+1241**.

### 2.2 As duas escolhas foram medidas, e nao estilizadas

**Por que DESLIGAR o cache do pytest em vez de reloca-lo.** Relocar exige
`cache_dir` com caminho **absoluto** (um caminho relativo cairia dentro
da arvore, que e o que se quer evitar). Caminho absoluto neste arquivo
versionado carregaria o **nome do usuario local** — exatamente o que a
redacao de PII do acervo existe para impedir. Desligar nao escreve
caminho nenhum.

**Por que o destino do bytecode e calculado em tempo de execucao.** Pela
mesma razao: `tempfile.gettempdir()` pergunta ao SO; um literal gravaria
o caminho local no fonte versionado.

**Por que `conftest.py` na RAIZ.** `sys.pycache_prefix` vale para os
modulos importados **depois** de ser atribuido. O `conftest.py` da raiz e
carregado pelo pytest antes de qualquer modulo de teste ou modulo do
acervo — que sao exatamente os que apareciam no manifesto.

### 2.3 A prova — invocacao simples, quatro condicoes

A invocacao e `python -m pytest <alvo> -q`, **sem env extra e sem flag
extra**. Isso e deliberado: se a configuracao nao estivesse **aplicada no
repositorio**, ela nao teria efeito nenhum aqui. E a diferenca entre
aplicar e documentar.

| Condicao | Config aplicada | Mutante M7 (config desfeita) |
|---|---|---|
| A. regime estavel | **0** | 0 |
| B. apos tocar o fonte do alvo | **0** | **1** (`.pyc` do teste) |
| C. outro arquivo de teste em sequencia | **0** | **1** (`.pyc` de `leitores_config`) |
| D. apos tocar um fonte NAO-teste | **0** | **1** (`.pyc` de `leitores_config`) |
| **total** | **0** | **3** |

*"Tocar"* aqui e reescrever o arquivo com **conteudo identico**: so o
mtime muda, e o manifesto — que hasheia conteudo — nao ve o fonte. O que
ele ve e o `.pyc` recompilado.

### 2.4 A classe do `.pytest_cache`, medida a parte

As quatro condicoes acima **nao** provocaram mutacao no `.pytest_cache`,
e a razao e medida: o manifesto hasheia **conteudo**, e uma corrida verde
que repete a anterior nao muda o conteudo do cache. A P1-A.4 mudou —
porque a sessao rodava suites **com falhas** enquanto o codex lia o
pacote.

Provocada de proposito, sem tocar em nenhum arquivo do repositorio (um
teste que falha, num arquivo **fora** da arvore, com `--rootdir` apontado
para ca):

| Condicao | Mutacoes |
|---|---|
| E. corrida que FALHA, **sem** a configuracao | **2** — `.pytest_cache/v/cache/lastfailed` e `.../nodeids` |
| F. mesma corrida, **com** `-p no:cacheprovider` | **0** |

`lastfailed` e literalmente uma das quatro linhas que a contencao acusou
na P1-A.4. **Cinco mutacoes ao todo** voltam quando se desfaz a
configuracao — tres `.pyc` e duas do cache do pytest.

### 2.5 Custo declarado

`--lf`, `--ff` e `--sw` deixam de funcionar, porque dependem do cache.
**Medido:** nenhum ponto do acervo os usa — as unicas mencoes a
`lastfailed` em todo o repositorio sao os **registros da propria
violacao**. O custo e real e hoje e zero; se alguem passar a depender
deles, esta linha e o lugar onde a troca fica registrada.

### 2.6 O que isto NAO faz

- **nao e a porta.** A quarta mutacao da P1-A.4 — a sessao editando
  `test_redacao_operacao_p1a39.py` enquanto o codex lia o pacote — nao e
  subproduto e **nenhuma realocacao a alcanca**;
- **nao alcanca processo que nao passe pelo pytest.** Um `python`
  invocado direto volta a compilar dentro da arvore. Limite do mecanismo,
  nao propriedade dele;
- **nao apaga o `.pytest_cache` e o `__pycache__` que ja existem** na
  arvore. Eles ficam parados, e parados nao mutam — o manifesto so acusa
  mudanca.

## 3. ORDEM 3 — a porta, REGISTRADA e NAO construida

**Nada nesta secao foi construido. `icacls` nao foi usado nesta missao.**
O que esta aqui foi medido na apuracao anterior, em diretorio
descartavel, e fica registrado para a missao que decidir constru-la.

### 3.1 O que a porta seria

Impedir que a **propria sessao** escreva na arvore enquanto a
`Vigilancia` esta aberta — a janela entre `vigilancia.abrir()` e
`vigilancia.fechar()`, que e o tempo da chamada ao revisor.

### 3.2 Por que ela e arquitetonicamente possivel — medido

Entre `abrir()` e `fechar()`, o runner faz **uma unica coisa**: o
`subprocess.run` do revisor. Medido em `revisao_p1a4.main()`:

    linha  29 | vigilancia.abrir()
    linha  32 | proc = subprocess.run(
    linha  40 | contencao_medida = vigilancia.fechar()
    linha  70 | SAIDA.mkdir(parents=True, exist_ok=True)
    linha  72 | (SAIDA / f"...json").write_text(

A gravacao da evidencia acontece **trinta linhas depois** do fechamento.
O descartavel do revisor e o `mkdtemp` vivem em `TEMP`, fora da arvore. O
**unico** escritor legitimo dentro da arvore durante a janela e o
renovador do lease, em `locks/`.

### 3.3 O mecanismo medido

Negacao de escrita por ACL na raiz do repositorio, com **isencao
explicita** para `locks/`, aplicada durante a janela e removida no fim.

| O que se mediu, em diretorio descartavel | Resultado |
|---|---|
| criar arquivo novo com a porta fechada | **BLOQUEADO** |
| acrescentar a arquivo existente | **BLOQUEADO** |
| **ler** qualquer arquivo | **preservado** |
| renovador escrevendo em `locks/` (isencao explicita) | **passa** — a permissao explicita no filho vence a negacao herdada do pai |
| aplicar e remover **sem elevacao** | **funciona**, e a remocao devolve a arvore ao estado anterior |

**A armadilha que a medicao pegou, e ela sozinha justifica este
registro:** a forma ingenua da negacao — o direito **generico** de
escrita — bloqueia **tambem a leitura**, porque o mapeamento generico
inclui `SYNCHRONIZE`, e negar `SYNCHRONIZE` nega qualquer abertura de
arquivo. Quem construir a porta com a forma generica **quebra o runner**,
que precisa ler os fontes. So a forma **especifica** — negar escrita de
dados, acrescimo e exclusao, e mais nada — preserva a leitura.

### 3.4 O custo e o que quebraria

| Item | Medido / declarado |
|---|---|
| **A negacao e por USUARIO, nao por processo** | ela prende o runner junto. Compativel, porque o runner nao escreve na janela (§3.2) — mas e compatibilidade **medida**, nao garantida por desenho |
| **Nao prende outro usuario nem processo elevado** | a porta vale para quem corre sob a mesma conta |
| **`.git` esta dentro da arvore** | nenhum comando `git` roda durante a janela. Commit, `add`, `checkout`: todos falham enquanto a porta estiver fechada |
| **A estrutura precisa existir ANTES** | a isencao de `locks/` so pode ser dada a um diretorio que ja exista; com a porta fechada, nem o diretorio se cria |
| **Elevacao** | nao e necessaria: o dono do diretorio altera a propria lista de permissoes |

### 3.5 O NOVO MODO DE FALHA — e ele nao e hipotetico

**Morte do processo entre fechar a porta e reverte-la deixa a arvore
inescrevivel.** Nao ha reversao automatica: a permissao e estado do
sistema de arquivos, nao do processo, e sobrevive a ele.

**O PC do Fundador desligou duas vezes esta semana.** E este repositorio
ja registra o precedente exato dessa classe: a queda de energia no meio
da P1-A.3.9 deixou **dois mutantes** aplicados na arvore viva, e foi essa
queda que fez nascer a regra do `scratchpad/MUTANTE-ATIVO.txt`.

**Consequencia, para quem construir:** a porta exige o **mesmo** desenho
que a reversao vermelha ja exige — registro em disco, em caminho
relativo a raiz do repositorio, gravado **antes** de fechar a porta e
apagado **depois** de reverte-la, contendo o comando exato da reversao.
Sem esse registro, a retomada apos queda encontra uma arvore que nao
aceita escrita e nenhuma pista do porque.

**E ha uma assimetria contra a porta, que precisa estar escrita:** um
mutante esquecido deixa a arvore **alterada mas funcional**, e a suite o
denuncia. Uma porta esquecida deixa a arvore **intacta e travada** — e
nenhuma suite roda para denunciar coisa alguma, porque o proprio pytest
nao consegue escrever. O instrumento de deteccao morre junto com o
acesso.

### 3.6 A RESSALVA — a porta impede, nao atribui

A porta **nao responde** a pergunta do MAJOR #3, *"quem escreveu este
byte?"*. Ela a torna **irrelevante dentro da janela** — se ninguem pode
escrever, nao ha o que atribuir — e a deixa **exatamente como esta** fora
dela.

Isso importa por duas razoes: o remedio especificado do MAJOR #3 admite
**ou** a atribuicao real **ou** a porta, e escolher a porta e escolher
**nao** ter a atribuicao; e a P1-A.5 fortaleceu a atribuicao (ela passou
a exigir **titular**, e nao so caminho) sem que isso resolvesse o achado
— fortalecer a atribuicao nao e criar a porta, e criar a porta nao e
fazer a atribuicao.

### 3.7 Dono e gatilho

| Campo | Valor |
|---|---|
| **Dono** | a missao que **refizer a revisao independente** |
| **Gatilho** | **se a quarta mutacao voltar a aparecer** — isto e, se a contencao acusar mutacao fora do descartavel que **nao** seja subproduto de cache. As tres primeiras classes ja nao podem voltar (§2) |
| **Remedio** | o mecanismo da §3.3, na forma **especifica** (§3.3, armadilha), com isencao explicita de `locks/`, e com o registro em disco da §3.5 gravado antes de fechar |
| **Alternativa que nao foi medida** | atribuicao real por auditoria do SO. Nao foi medida nesta missao e **nao se afirma nada sobre ela** |
| **Construida?** | **Nao.** O ato desta missao proibe, e a proibicao foi respeitada |

## 4. Alcance — o que esta missao estabelece e o que NAO estabelece

### 4.1 Estabelecido — medido

| Fato | Como |
|---|---|
| A prova central nunca mudou | um commit em toda a historia; blob identico ao da baseline |
| `18/20` existiu uma vez em todo o acervo, e era erro desta trilha | varredura do repositorio inteiro |
| A suite nao escreve mais na arvore vigiada | 0 mutacoes em quatro condicoes, invocacao simples |
| A configuracao e o que produz esse zero | mutante M7: voltam 3 `.pyc`, mais 2 do cache numa corrida que falha |
| A configuracao nao altera a suite | mesmos 344+256 e 914+1241 |
| A porta e possivel, e a forma ingenua dela quebraria a leitura | medicao em diretorio descartavel, na apuracao anterior |

### 4.2 NAO estabelecido — e nao se presume

- **nada foi certificado.** Esta missao corrigiu; quem corrige nao fecha
  o proprio achado;
- **a porta nao existe.** Ela esta registrada como possivel, com custo
  medido — e possivel nao e construida, e construida nao e provada;
- **a quarta mutacao continua aberta.** A sessao pode escrever na arvore
  durante a janela, hoje, exatamente como antes;
- **a atribuicao continua sem responder "quem escreveu?"**;
- **nao se afirma que a realocacao de cache impeca a contencao de acusar
  a sessao.** Ela remove **tres classes de subproduto**; a acusacao volta
  no instante em que a sessao editar um arquivo;
- **nada aqui foi medido em outra estacao.** A realocacao usa o
  diretorio temporario do SO, e o comportamento noutro sistema de
  arquivos nao foi observado;
- **a tese central segue nao medida em token.**

## 5. ATESTADO

**Esta missao corrigiu, e por isso NAO certifica.**

**O que seria falha, e nao foi feito:** reescrever o `18/18` dos outros
dezoito documentos para "uniformizar" — eles estao certos; corrigir a
linha 63 sem declarar no proprio documento o que ela dizia antes;
relocar o cache do pytest com um caminho absoluto, gravando o nome do
usuario local num arquivo versionado; provar a realocacao com variaveis
de ambiente na linha de comando, o que provaria a variavel e nao a
configuracao; e construir a porta, que o ato proibiu e que a §3.5 mostra
ter um modo de falha pior que o problema que resolve, enquanto nao tiver
o registro em disco.

**O que ficou aquem, e esta escrito:** a classe do `.pytest_cache` nao
aparece nas quatro condicoes da prova principal, e so foi medida porque
se provocou uma falha de proposito. Se a medicao tivesse parado nas
quatro condicoes, este registro afirmaria que a configuracao remove tres
classes tendo exercido **duas**.

**Contagem como medida, nunca como meta.** Os numeros deste atestado —
0 nas quatro condicoes, 3 e 2 na reversao, 18 assercoes e 20 eventos —
sao o que foi medido.

**DECISAO: CONCLUIDO.**
