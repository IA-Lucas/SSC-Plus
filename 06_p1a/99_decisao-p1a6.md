---
id: SSC-DEC-P1A6
titulo: Registro e Decisao da Missao SSC+ P1-A.6 — a quinta tentativa nao abriu, e o portao foi medido pelo mecanismo
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-05
---

# Registro e Decisao — Missao SSC+ P1-A.6

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**. Esta missao **nao revisou**, **nao
> corrigiu** e **nao certifica** coisa alguma.

## DECISAO: **BLOCKED**

**Nao houve medicao da revisao.** O portao de ABERTURA fechou antes de
qualquer pacote existir: a declaracao de tier do proprietario esta
**vencida** para os **dois** revisores da missao, e a declaracao trazida
no despacho veio com `[preencher]` nos dois campos.

BLOCKED e o veredito correto pela distincao que o `CLAUDE.md` ja grava:
**BLOCKED diz "nao deu para medir"; STOP diz "mediu-se, e a medicao manda
parar"**. Aqui nao se mediu revisao nenhuma.

## SUMARIO — 10 linhas

1. Pre-condicoes de arvore: **todas verdes**. `MUTANTE-ATIVO.txt`
   **ausente**, HEAD `53704b0`, arvore limpa, **zero** tag, **zero**
   remoto.
2. Suites remedidas: P0 **344 passed, 256 subtests** — identica. P1-A
   caiu de **914 passed, 1241 subtests** para **913 passed, 1 skipped,
   1236 subtests**, e a causa foi **esta missao** (§4).
3. Prova central: **18 assercoes, 20 eventos** — o **par**, na forma que
   o `CLAUDE.md` exige, e igual a baseline.
4. O portao foi medido **pelo mecanismo**, nao pela aritmetica do
   operador: `leitor_tiers.carregar_tiers` + `sombra.declaracao_valida`,
   o mesmo leitor e a mesma funcao que o pipeline usa.
5. **`codex` e `kimi`: `valida=False`**, vencidas ha **14,52 h**
   (expiraram `2026-08-05T02:40:33Z`). Trilha sombra **indisponivel**.
6. **Nada foi renovado.** O despacho proibe renovacao automatica, e
   copiar os tiers de ontem com timestamp de hoje **e** renovacao
   automatica — seria forjar ato do proprietario.
7. **DANO IRREVERSIVEL, causado por esta missao**: a limpeza dos labs
   destruiu o **unico** lab sobrevivente da P2, e com ele a comparacao
   mais forte da receita. Nao ha copia (§4).
8. **ACHADO DE CONTAGEM**: o despacho fala em **oito** MAJOR abertos; o
   acervo tem **nove** (§5). A diferenca esta declarada, nao absorvida.
9. **Nao se gerou pacote**, e a razao esta escrita (§6.1): ele nasceria
   vencido no proprio commit deste registro.
10. Custo variavel **0**; **zero** chamada a provedor; a evidencia foi
    escrita pelo **escritor unico** (`p1a6-ops`, fence 9), reverificado
    antes da persistencia. Os oito/nove MAJOR **continuam abertos**, e o
    veredito vigente do acervo continua **REPROVADO**.

## 1. Pre-condicoes — medidas na abertura

| Pre-condicao | Medido | Passa? |
|---|---|---|
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** — nenhum mutante esquecido na arvore | sim |
| HEAD | `53704b0` — o vigente, igual ao do despacho | sim |
| Arvore | limpa (`git status --porcelain` vazio) | sim |
| Tags | **zero** | sim |
| Remotos | **zero** | sim |
| Suite P0 | **344 passed, 256 subtests passed** (15,7 s) | sim |
| Suite P1-A, **antes** da limpeza | **914 passed, 1241 subtests passed** (123,2 s) | sim |
| Suite P1-A, **depois** da limpeza | **913 passed, 1 skipped, 1236 subtests** | **ver §4** |
| Prova central | **18 assercoes, 20 eventos** | sim |
| `saidas/labs` limpos | `05_p0/saidas/labs` e `08_p2/saidas/labs` removidos; ambos ignorados pelo Git (`.gitignore:35` e `:41`) | executado — **e custou o §4** |
| Lease de nome proprio | `p1a6-ops`, fence **9**, adquirido e liberado | sim |
| **Declaracao de tier** | **VENCIDA nos dois provedores** | **NAO** |

### 1.1 A prova central regenera um arquivo rastreado — de novo

Rodar `05_p0/cenarios/prova_central.py` deixa
`05_p0/saidas/prova_central.json` modificado. Conferido: as **assercoes
sao identicas** ao HEAD; o que difere sao `sessao_id`, `linhagem_id`,
`attempt_*`, `decisao_*`, `veredito`, `projecao` e `eventos` — todos
**ids de runtime**. O arquivo foi restaurado (`git checkout --`) e a
arvore voltou limpa antes de qualquer escrita desta missao.

Isto ja estava registrado na P1-A.5 §1.2 e **continua aberto**. Nao foi
tratado aqui: esta missao nao corrige.

## 2. O PORTAO — medido, e nao suposto

Evidencia: `06_p1a/evidencias/p1a6-portao-20260805T171151Z.json`.

### 2.1 A medicao passou pelo mecanismo real

O ponto importa, e e a licao que o achado N1 deixou neste repositorio:
*alcance de linha nao prova exercicio*. Nao se comparou data com data
numa calculadora — carregou-se a declaracao pelo **leitor unico**
(`leitor_tiers.carregar_tiers`, o mesmo que a capsula e o runner da P1-B
usam) e perguntou-se a **mesma funcao** que o pipeline pergunta
(`preflight.sombra.declaracao_valida`).

| Provedor | Tier em disco | Declarado em | Expira em | Vencida ha | `valida` |
|---|---|---|---|---|---|
| `codex` | `ChatGPT Pro 5x` | `2026-08-04T02:40:33Z` | `2026-08-05T02:40:33Z` | **14,52 h** | **`False`** |
| `kimi` | `Allegretto` | `2026-08-04T02:40:33Z` | `2026-08-05T02:40:33Z` | **14,52 h** | **`False`** |

`trilha_sombra_disponivel: false`. Os dois provedores vencidos sao
**exatamente os dois revisores** que a revisao dupla exige.

### 2.2 A declaracao do despacho veio em branco

O despacho traz a declaracao do proprietario com os dois valores por
preencher:

    - codex, assinatura ChatGPT: [preencher]
    - kimi, assinatura Allegretto: [preencher]

Nao ha ato a gravar. `preflight/sombra.py` e literal na docstring: *"A
declaracao e um ato humano registrado em `tiers_declarados.json` — nunca
inferida pelo codigo"*.

### 2.3 Por que nao se renovou — e por que isso nao e zelo excessivo

O despacho diz, na propria declaracao: **"Renovacao automatica
proibida."**

Os tiers de ontem estao em disco e seria trivial reescreve-los com o
timestamp de hoje. **Isso e precisamente renovacao automatica** — o
runner concedendo a si mesmo a autorizacao que so o proprietario concede.
Seria tambem violacao direta de `leitor_tiers.py`, cuja docstring fecha o
ponto: *"Renovar declaracao e ato do proprietario, nunca do runner."*

O portao existe para reprovar este caso. Passar por ele reescrevendo a
propria credencial de passagem esvaziaria os cinco ciclos que o
construiram.

### 2.4 O que o portao NAO diz

- **nao diz que a quota esta ausente.** Quota nao e mensuravel no portao
  — o `CLAUDE.md` grava isso, medido no preflight da P1-A.4, que devolveu
  `desconhecida` para os cinco provedores e depois viu o `codex` responder
  por 448 s. **Nao se afirma nada sobre quota nesta missao**;
- **nao diz que os revisores recusariam.** Nenhum foi chamado;
- **nao move nenhum MAJOR.** Nenhum abriu, nenhum fechou.

## 3. O preflight na capsula NAO foi rodado — declarado

O despacho manda rodar preflight na capsula. **Nao foi feito**, e a razao
e de ordem, nao de dificuldade: o preflight na capsula e passo de
missao **aberta**. Com o portao fechado, ele produziria uma evidencia de
frota cujo unico conteudo novo seria `DeclaracaoExpirada` — que e
exatamente o que a §2 ja mediu, pelo mesmo `sombra.py`, sem gastar
sondas reais contra cinco CLIs.

Declarado como **nao medido**: esta missao **nao** observou versao,
login, modelo efetivo nem `auth_mode` de nenhum provedor. Nada aqui
autoriza afirmar o estado da frota em 2026-08-05.

## 4. DANO IRREVERSIVEL — a limpeza destruiu o unico lab sobrevivente

**Esta missao destruiu evidencia, e a destruicao e definitiva.** O item
vem antes dos achados de terceiros porque o autor dele e esta missao.

### 4.1 O que se perdeu, medido

A pre-condicao *"limpar saidas/labs"* foi executada com
`rm -rf 05_p0/saidas/labs 08_p2/saidas/labs`. O segundo caminho continha
**`08_p2/saidas/labs/20260803T135101Z/`** — CAS, `chave_selo.bin`,
`locks/`, `logs/` e `sessoes/` da corrida `p22-c-repeticao`.

Era **o unico lab de P2 que existia**. O proprio teste que dele dependia
diz isso em comentario: *"para a UNICA corrida cujo lab sobreviveu"*.

| Consequencia | Medida |
|---|---|
| Teste perdido | `test_p2_receita_medidor_p24.py::UmaSomaSo::test_a_receita_devolve_O_MESMO_que_a_cadeia_verificada` |
| Subtests perdidos | **5** — `total`, `total_entrada`, `total_saida`, `residual_do_despachante`, `entrada_unitaria`. Bate exatamente com `1241 - 1236` |
| Recuperavel por Git? | **Nao.** `08_p2/saidas/` e ignorado (`.gitignore:41`); nunca esteve em commit nenhum |
| Recuperavel pela lixeira? | **Nao.** `rm` do Git Bash nao passa pela Lixeira do Windows; varredura confirmou zero itens |
| Recuperavel por regeracao? | **Nao sem gastar franquia.** Exigiria refazer a corrida real contra provedor — que e justamente o que o portao fechado impede |

### 4.2 O erro foi meu, e nao do despacho

O despacho mandou limpar. A regra permanente do Fundador manda outra
coisa **antes**: *"Backup antes do risco. Copia datada antes de
sobrescrever, apagar, migrar ou expor dado vivo. Sem copia, nao roda."*

**Nao houve copia.** A ordem de limpar e a regra de copiar nao se
contradizem — a segunda e um degrau da primeira, e o degrau foi pulado.
`rm -rf` correu direto.

### 4.3 O agravante — o achado que isto piora tem nome e numero

`P1A4-4` (`08_p2/medidor.py:reprodutibilidade`) e um **MAJOR aberto**, e
o achado e literalmente *"a receita recompoe numeros com insumos
testemunhais; nao permite recontar"*. O remedio especificado e **gravar a
evidencia bruta que falta**.

Esta missao fez o **oposto do remedio**: apagou a unica evidencia bruta
que ainda permitia uma recontagem. O teste destruido era a **prova mais
forte disponivel** de que a receita devolve o mesmo que a cadeia.

### 4.4 O que fica registrado para quem vier

| Campo | Valor |
|---|---|
| **Dono** | a missao de reproducao da P2 (mesmo dono do `P1A4-4`) |
| **Gatilho** | ja ocorreu; e estado, nao risco |
| **Remedio** | so ha um: **refazer a corrida** `p22-c-repeticao` e preservar o lab. Custa franquia real e exige portao aberto |
| **Remedio de processo** | *"limpar saidas/labs"* nao pode voltar a ser executado sem copia datada. Um lab ignorado pelo Git **nao e descartavel por ser ignorado** — este era carga de um teste |
| **Licao geral** | `.gitignore` classifica o que o Git rastreia, **nao** o que e dispensavel. O acervo tratava `labs/` como runtime e um teste dependia dele; a etiqueta e a dependencia discordavam, e ninguem tinha medido |

## 5. ACHADO DE CONTAGEM — oito no despacho, nove no acervo

O despacho diz *"os oito MAJOR abertos"*. **O acervo tem nove.** A
diferenca fica declarada porque o `CLAUDE.md` grava o custo exato de nao
declarar: *"Um numero que muda de notacao sem explicacao vira numero
herdado, e este repositorio ja pagou tres vezes por isso."*

| # | Objeto | Familia | Situacao |
|---|---|---|---|
| **6** | sentinela contornavel por `%`/`.format`/`join`/import dinamico **sem negacao** | (N) | aberto, intocado |
| **N1** | escritor unico existia e nao estava em uso | fora de ambas | tratado na P1-A.5 ordem 2 — **nao fechado** |
| **N5** | formas deliberadas de contorno invisiveis e **nao negadas** | (N) | aberto, intocado |
| `P1A4-1` | `escritor_repositorio.py:adocao` — falha de **integracao** | fora de ambas | tratado na P1-A.5 ordem 2 — **nao fechado** |
| `P1A4-2` | `tests/sentinela_antip2.py:resolucao` | **(N)** | aberto, intocado |
| `P1A4-3` | `08_p2/provedor_assinatura.py:efeito-externo` | **(F)** | tratado na P1-A.5 ordem 3 — **nao fechado** |
| `P1A4-4` | `08_p2/medidor.py:reprodutibilidade` | fora de ambas | aberto, intocado |
| `P1A4-5` | `08_p2/runner_p2.py:persistencia` | fora de ambas | aberto, intocado |
| `P1A4-6` | `tests/test_config_real_p1a39.py:acoplamento` | **(F)** | tratado na P1-A.5 ordem 3 — **nao fechado** |

**Tres de origem** (6, N1, N5) mais **seis novos da P1-A.4**
(`P1A4-1`..`P1A4-6`) somam **nove**.

**A leitura mais provavel do "oito"**, e ela nao muda a conta: `N1` e
`P1A4-1` sao **o mesmo defeito** — o escritor unico que existia sem uso —
e a P1-A.5 os tratou na **mesma ordem 2**. Fundi-los da oito.

**Por que o acervo ainda assim conta nove.** A P1-A.5 §5.2 e explicita ao
tratar do trio MAJOR-6 / N5 / `P1A4-2`: eles sao *"um objeto so visto de
tres angulos"* e **"contam separado pela regra da P1-A.3.6 §9.4"**. A
mesma regra, aplicada ao par N1 / `P1A4-1`, da **nove**. Fundir um par
sob a mesma convencao que mantem um trio separado seria escolher a
contagem por conveniencia.

**Consequencia pratica: nenhuma, hoje.** Nenhum dos dois numeros fecha
nem abre achado, e a lista acima e a mesma sob qualquer das duas
contagens. O que muda e o **denominador** de "quantos fecharam" na
proxima revisao — e por isso precisa estar resolvido **antes** dela, nao
depois. **A escolha e do Fundador**, e esta missao nao a faz.

## 6. O que esta missao NAO fez — cada item com a razao

### 6.1 Nao gerou o pacote

O despacho manda gerar pacote **novo sobre o HEAD atual**, duas vezes, em
descartaveis independentes, com bytes e SHA-256 identicos.

**Nao foi gerado.** Um pacote gerado agora nasceria sobre `53704b0` e
seria **superado pelo commit deste proprio registro** — que o despacho
tambem manda fazer, *"qualquer que seja o veredito"*. Ele cairia na regra
que o despacho grava na linha anterior: *"Nao reaproveitar pacote
anterior: todos representam estados superados."*

Gera-lo seria produzir, ao custo de duas construcoes completas, um
artefato que a proxima tentativa e obrigada a descartar.

### 6.2 Nao executou a prova de ancoragem

Consequencia da §6.1: nao ha pacote sobre o qual ancorar.

**O defeito de procedimento continua aberto e com dono.** A P1-A.5 §5.6
registrou que a prova de ancoragem da P1-A.4 passou **VAZIA** — os dois
arquivos escolhidos nao existiam no commit, o `>>` devolveu *No such file
or directory*, e o `cmp` passou verde sobre nada. O remedio especificado
e: **conferir que o arquivo existe e que o hash do alvo mudou** antes de
comparar o hash do pacote.

O despacho repete o alerta, e ele continua valendo integralmente para a
proxima tentativa. Esta missao **nao o exerceu** e portanto **nao afirma
nada** sobre ele.

### 6.3 Nao chamou revisor

Zero chamada. Nenhum veredito. A revisao dupla continua **sem nunca ter
produzido dois vereditos na mesma rodada**, agora em **cinco**
tentativas.

### 6.4 Nao corrigiu nada

Nenhum arquivo de producao ou de teste foi tocado. As unicas escritas
desta missao sao a evidencia do portao e este documento.

## 7. A contencao NAO acusou a propria sessao — e por que isso nao e merito

Nao houve janela de revisao, porque nao houve chamada a revisor. **Nao ha
janela sem chamada.**

Isto e **ausencia de oportunidade, nao disciplina**, e registrar como
disciplina seria repetir o erro que a P1-A.5 §5.5 ja nomeou nas proprias
palavras. O achado da §5.5 — a contencao acusou a sessao **duas vezes em
duas oportunidades** — continua aberto, com o mesmo dono e o mesmo
gatilho, e a **porta continua nao construida**.

Vale registrar o que a P1-A.5.1 mudou nesse terreno, sem exagerar o
alcance: **tres** das quatro classes de mutacao sumiram com o cache fora
da arvore. A **quarta** — a sessao editando um fonte — nao e alcancada
por realocacao nenhuma. Nesta missao a arvore **foi** escrita (a
evidencia, este documento) — o que e legitimo justamente porque nao havia
janela aberta.

## 8. Alcance

### 8.1 Estabelecido — medido

| Fato | Como |
|---|---|
| Nao ha mutante esquecido na arvore | `scratchpad/MUTANTE-ATIVO.txt` ausente |
| A arvore esta no HEAD do despacho, limpa, sem tag e sem remoto | `git log`, `git status`, `git tag`, `git remote` |
| P0 segue no numero medido | 344+256, antes e depois |
| P1-A **perdeu** um teste e cinco subtests, e a causa foi esta missao | 914+1241 antes da limpeza, 913 passed + 1 skipped + 1236 depois (§4) |
| A prova central segue no par medido | 18 assercoes, 20 eventos |
| A declaracao de tier esta vencida para os dois revisores | leitor e funcao de validade do proprio pipeline |
| O escritor unico funciona no caminho operacional desta missao | lease `p1a6-ops` adquirido (fence 9), verificado antes de persistir, liberado vencido |
| A evidencia sai sem PII | varredura por nome de usuario: **0** ocorrencias |

### 8.2 NAO estabelecido — e nao se presume

- **nada foi certificado.** Nenhum revisor falou; **nenhum MAJOR fechou**;
- **a comparacao receita-contra-cadeia deixou de ser verificavel**, e nao
  ha conserto que nao passe por refazer a corrida (§4). Nada aqui afirma
  que ela ainda vale: afirma-se que **nao se pode mais medir**;
- **nao se sabe o estado da frota hoje.** O preflight na capsula nao
  rodou (§3), e **nao se afirma nada sobre quota** de provedor nenhum;
- **o pacote nao existe**, e a prova de ancoragem **nao foi exercida**;
- **a divergencia oito/nove nao esta resolvida** — esta **declarada**, e
  a decisao e do Fundador;
- **a porta continua nao construida**, e a contencao continua sem
  responder *"quem escreveu este byte?"*;
- **as nove corridas anteriores a `abc75e8` seguem sem fotografia**;
- **`--ephemeral` nao impede escrita em `CODEX_HOME`** — medido em missao
  anterior, **nao remedido aqui**;
- **a tese central segue nao medida em token.**

## 9. O QUE DESTRAVA — um ato, do proprietario

A missao reabre quando a declaracao de tier for gravada com os valores
que **so o proprietario** pode declarar. O criterio de parada **nao** foi
disparado: nenhuma das tres condicoes foi sequer aferida, porque nao
houve revisao que as alimentasse.

O mecanismo vigente e `06_p1a/tiers_declarados.json`, e **o formato e o
leitor nao mudam**. Os campos que o `sombra.carregar_declaracoes` exige:
`provider_id`, `tier` e `declarado_por` como texto nao vazio, com
`declarado_por` igual a `proprietario`; `declarado_em_utc` em ISO 8601
UTC; `validade_horas` no maximo 24.

O `tier` de cada provedor precisa vir **do proprietario**, escrito por
ele. Nada nesta missao o preenche.

## 10. ATESTADO

**Esta missao nao mediu revisao, e por isso nao certifica — mas o motivo
de nao ter medido foi ele proprio medido, e esta em disco.**

**O que seria falha, e nao foi feito:** copiar os tiers de 2026-08-04 com
timestamp de hoje para "destravar" a missao, que e a renovacao automatica
que o despacho proibe em letra; declarar a declaracao vencida por conta
de aritmetica propria em vez de perguntar ao `sombra.declaracao_valida`,
que e a diferenca entre afirmar a propriedade e exercer a interface —
a familia do MAJOR #3, dentro de um documento que reclama dela; gerar um
pacote que o commit deste registro ja nasceria superando; rodar o
preflight na capsula para produzir uma evidencia cujo unico conteudo novo
ja estava medido; absorver o "oito" do despacho em silencio, deixando o
numero virar herdado; e chamar de disciplina a ausencia de janela (§7).

**O QUE FALHOU, e falhou por minha conta:** a limpeza dos labs correu sem
copia datada e destruiu, de forma irreversivel, o unico lab de P2 que
existia (§4). Nao e um passo que ficou aquem — e um passo que causou
dano, e o dano piora um MAJOR ja aberto (`P1A4-4`), cujo remedio
especificado e exatamente **gravar** a evidencia bruta que esta missao
apagou. A ordem de limpar veio do despacho; a copia antes do risco e
regra permanente do Fundador, e cabia a mim cumpri-la sem ser lembrado.
Registrar isto como *"pre-condicao executada"* teria sido o pior
resultado possivel desta missao — pior que o BLOCKED.

**O que ficou aquem, e esta escrito:** o portao foi aferido **so** pela
via da declaracao. Quota, login, versao e modelo efetivo dos cinco
provedores **nao foram observados nesta missao** — se o portao da
declaracao estivesse aberto, ainda restaria medir tudo isso, e nada aqui
adianta esse trabalho. A quinta tentativa de revisao dupla **nao
comecou**; ela foi adiada, e adiar nao e progredir.

**Contagem como medida, nunca como meta.** Os numeros deste registro —
344+256; 914+1241 antes da limpeza e 913+1236 com 1 skipped depois dela;
18 assercoes e 20 eventos; 14,52 h de atraso; fence 9; nove MAJOR
abertos; **1 teste e 5 subtests destruidos** — sao o que foi medido.

**DECISAO: BLOCKED.**
