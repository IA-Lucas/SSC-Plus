---
id: SSC-DEC-P1A7
titulo: Registro e Decisao da Missao SSC+ P1-A.7 — ordem 6, a varredura de segredo que este repositorio nunca teve, antes do primeiro push
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-05
---

# ORDEM 6 — VARREDURA DE SEGREDO, ANTES DO PUSH

> **DECISAO DA ORDEM 6: `PUSH LIBERADO`.**
> **Nenhuma credencial real foi encontrada em nada que o push transmite.**
> Todos os 39 casamentos nao-hex da carga do push sao **fixture sintetica
> do proprio detector de segredo do acervo**, nomeados um a um na §5. O
> unico material de chave REAL da estacao — `chave_selo.bin`, 32 bytes,
> entropia 4,875 — **nunca entrou na historia** e **nao viaja**, medido e
> nao suposto (§6).

## 0. POR QUE ESTE ARQUIVO EXISTE, E O QUE ELE NAO E

O despacho manda **acrescentar ao final da P1-A.7**. Nao havia registro
de P1-A.7 neste repositorio quando esta ordem abriu — o acervo terminava
na P1-A.6 (`1f45fdd`). Este arquivo e criado, portanto, **contendo
somente a ordem 6**. As ordens 1 a 5 da P1-A.7, se existirem, **nao estao
neste registro**, e afirmar o contrario seria inventar conteudo: o que
esta escrito aqui e o que esta ordem mediu.

Vale tambem o que este documento **nao** e. Ele nao certifica nada, e a
regra **QUEM CORRIGE NAO CERTIFICA** se aplica com um agravante proprio:
quem escreveu o varredor foi quem o rodou e quem le o resultado. O que
sustenta a leitura nao e a assinatura — e a **reprodutibilidade**: o
varredor esta versionado, e deterministico, e qualquer terceiro roda

```
python 06_p1a/evidencias/varredura_segredo_p1a7.py --reduzido saida.json
```

sobre o mesmo estado da arvore e obtem os mesmos numeros.

## 1. A PERGUNTA QUE NUNCA HAVIA SIDO FEITA

Este repositorio **nunca foi varrido por detector de credencial**. Nao e
suposicao: e questao de fato, e ela se mede em duas linhas.

O que existia sob o nome de "portao" e a **contencao**
(`06_p1a/evidencias/contencao.py`) — e a funcao canonica dela,
`redigir`, faz **exatamente tres coisas**: troca a forma longa do nome
do usuario, troca a forma 8.3 do mesmo nome, e troca prefixos de caminho
local. Ela **nao procura chave, token, senha nem material de chave
privada**, e o docstring dela nunca afirmou o contrario. O gerador de
pacote, por sua vez, so olha `.py`, `.md`, `.json` e `.txt`
(`pacote_p1a37.py:55`).

Ha um detector de segredo no acervo — `escanear_segredos`, em
`05_p0/ssc_p0/kernel.py:63-65` —, mas ele guarda o **conteudo que entra
no kernel da P0 em runtime**, com quatro padroes (`AKIA`, `ghp_`, `sk-`,
`api_key:`). Ele nunca foi apontado para a **arvore** nem para a
**historia**. A pergunta *"ha credencial no que vai ser publicado?"*
estava, ate esta ordem, **sem medicao**.

## 2. O QUE FOI VARRIDO, E COM QUE ALCANCE

Instrumento: `06_p1a/evidencias/varredura_segredo_p1a7.py` (novo).
Evidencia: `06_p1a/evidencias/p1a7-varredura-segredo-20260805T210650Z.json`.
Estado varrido: HEAD `1f45fddf82ff02fb7a66ce7c5d8fcde786d63451`, **148
commits**.

**34 regras**, das quais 5 existem *somente* na passagem crua — sao
exatamente as cegueiras que o despacho nomeia (§7).

| Passagem | O que ela le | Numeros medidos |
|---|---|---|
| **(a) do PORTAO** | so a arvore de HEAD, so `.py/.md/.json/.txt`, bloco cercado de markdown pulado, `backups/` ignorado, palavra-chave so em ingles, nome de arquivo nao consultado | **338 arquivos lidos**, de **361 rastreados**; 18 pulados por extensao; 5 pulados por diretorio; **7 achados** |
| **(b) CRUA** | **todo** o banco de objetos (alcancavel **e** inalcancavel) mais **toda** a arvore de trabalho, inclusive o que o `.gitignore` esconde; binarios byte a byte (`latin-1`) | **617 blobs** (8 inalcancaveis) + **736 arquivos em disco**; **15.817.872 bytes lidos**; **1.714 achados** |
| **(c) CARGA DO PUSH** | o clone de `git bundle create --all` — o conjunto que `git push` transmite, sem inalcancavel nenhum | **609 blobs**, **0 inalcancaveis**, 361 arquivos; **11.220.503 bytes lidos**; **1.586 achados** |

A passagem (c) nao estava no despacho e foi acrescentada porque a
pergunta da ordem 6 nao e *"ha segredo no disco?"* e sim **"ha segredo no
que viaja?"**. As duas nao coincidem, e a §6 mostra o caso concreto em
que divergem.

**Nao confunda as grandezas.** Achado e casamento de regra; arquivo e
arquivo; blob e blob. Os tres numeros de cada linha acima sao **tres
medidas distintas** e nao se escrevem como fracao entre si.

## 3. O QUE A DIFERENCA ENTRE (a) E (b) MEDE

O portao devolveu **7 achados**; a crua devolveu **1.714**. A diferenca
**nao** e "o portao deixou passar 1.707 segredos" — e o tamanho do
**campo de visao**, e e essa a leitura:

- o portao le **338 arquivos**; a crua le **736 arquivos em disco mais
  617 blobs de historia**;
- o portao le **zero** dos **8 blobs inalcancaveis** — e e num deles que
  mora o unico vazamento real de PII do repositorio (§6.2);
- o portao le **zero** dos **375 arquivos que o git nao rastreia** — e e
  entre eles que mora o unico material de chave real da estacao (§6.1);
- o portao **nao tem regra de nome de arquivo**: `chave_selo.bin` nao
  seria visto por ele **nem se estivesse rastreado**;
- o portao **nao tem a palavra portuguesa**: os **16 casamentos**
  `atribuicao_pt` sao invisiveis para ele.

**O portao nao errou: ele nao foi construido para esta pergunta.** O
achado desta ordem nao e "o portao falhou", e sim **"nunca houve guarda
de credencial neste repositorio, e a primeira publicacao seria a primeira
vez que isso importaria"**.

## 4. CLASSIFICACAO POR FAMILIA — OBRIGATORIA

O acervo exige classificacao por familia em todo relatorio, sem a qual o
criterio (b) de parada nao pode ser aferido. Esta ordem produziu **um**
achado de metodo, e ele se classifica:

| Achado | Familia | Razao |
|---|---|---|
| **Nao existe guarda de credencial sobre arvore nem sobre historia.** `escanear_segredos` guarda o conteudo do kernel em runtime; `redigir` cobre PII e caminho local. Entre os dois ha uma classe inteira sem guarda: *o que esta versionado.* | **(N)** | Classe que a varredura dos 86 guardas **nao media**. O eixo daquela varredura era alcance de linha em guardas existentes; um guarda **que nunca foi escrito** nao tem linha para alcancar. Nao e (F): (F) e o guarda que **afirma** em vez de **exercer** — aqui nao ha guarda que afirme coisa alguma. |

**Nenhum achado (F) e nenhum achado fora-de-ambas nesta ordem.** Os 74
casamentos nao-hex da passagem crua **nao sao achados**: sao fixtures
identificadas, e estao na §5 pelo nome.

## 5. FIXTURE SINTETICA CONTRA CREDENCIAL REAL — ITEM A ITEM

Sao **74 casamentos nao-hex** na passagem crua, que se reduzem a **48
combinacoes distintas** de (regra, arquivo, valor) e a **nove familias de
fixture**, todas nomeadas. O criterio de separacao e um so, e nao e
aparencia: **fixture e o valor que existe para ser RECUSADO por um teste
do proprio acervo, e cujo teste esta versionado ao lado**.

| # | Fixture, com o valor literal | Onde nasce | Por que e fixture, e nao credencial |
|---|---|---|---|
| **1** | `AKIA1234567890ABCDEF` | `05_p0/tests/test_seguranca.py:34` | Corpo de `test_ic4_segredo_em_evento_recusado`, dentro de `assertRaises(SegredoDetectado)`. O digito e sequencial: `1234567890`. Nenhuma conta AWS existe neste laboratorio. |
| **2** | `-----BEGIN PRIVATE KEY-----\nabc` | `05_p0/tests/test_seguranca.py:50` | O bloco tem **tres bytes de corpo** (`abc`). Nao ha chave: ha o cabecalho que o detector procura. |
| **3** | `api_key: "abcdefgh12345678"` e `sk-` + `a`*32 | `05_p0/tests/test_p0_kernel_p1a37.py:169-172` | Montados em `for texto in (...)` para exercer `escanear_segredos`; o alfabeto e literalmente `abcdefgh`. |
| **4** | `sk-teste-payg-nao-usar-123456` | `05_p0/tests/test_frota.py:59,65` | O valor **diz o que e**: `teste-payg-nao-usar`. O teste prova que `ambiente_sanitizado` **retira** `OPENAI_API_KEY` do processo filho. |
| **5** | `xai-nao-usar-123456` | `05_p0/tests/test_frota.py:160` | Mesma familia do #4, para `XAI_API_KEY`; o teste prova que a chave fica **fora** do adaptador. |
| **6** | `sk-`+`a`*24, `xai-`+`b`*24, `AIza`+`c`*24, `ghp_`+`d`*24, `Bearer `+`e`*24, `api_key: "`+`f`*24`"` | `06_p1a/tests/test_isolamento.py:173-176` | Seis amostras **construidas por concatenacao em runtime**; cada uma e uma letra repetida 24 vezes. |
| **7** | `sk-segredo-que-jamais-deve-vazar-123456` | `06_p1a/tests/test_preflight.py:36` | Montado por concatenacao **de proposito**, e o proprio arquivo declara a razao em comentario (linhas 33-35): *"assim o valor existe em memoria para os testes, mas NENHUMA linha do arquivo casa com o padrao de chave real"*. |
| **8** | `chave: "valor-ficticio"` | `05_p0/tests/test_p0_adaptador_assinatura_p1a37.py:115` | `chave` e a **variavel de laco** sobre `CHAVES_PROIBIDAS`; o valor e literalmente `valor-ficticio`. |
| **9** | `chave: "https://api.anthropic.com/v1"` e `chave: "https://api.openai.com/v1"` | `06_p1a/tests/test_estabilizacao_p1a1.py:159-172` | `chave` e a variavel de laco sobre **grafias de nome de campo** (`base_url`, `baseUrl`, `apiEndpoint`...). O valor casado e um **endpoint publico**, nao uma credencial. Este e o falso positivo por construcao da regra portuguesa — e ele fica: a regra que o produz e a mesma que pegaria `chave: "<valor real>"`. |

**Os demais casamentos sao os mesmos nove valores vistos de outro
angulo**, e nao terceiros itens:

- em **`.pyc` sob `__pycache__/`** (10 arquivos): a compilacao **dobra as
  concatenacoes** dos #6 e #7, de modo que o `.pyc` carrega o literal que
  o `.py` nao carrega. Nenhum e rastreado; `__pycache__/` esta no
  `.gitignore` e **nenhum `.pyc` jamais entrou na historia** (medido: a
  historia inteira tem so `.py .json .md .txt .sha256 .patch .diff .sh
  .ini .gitattributes .gitignore`);
- em **`logs/diff-0.2.1-hardening.patch`** e **`logs/diff-0.3-frota.patch`**:
  sao *diffs dos proprios testes acima* — o `-----BEGIN PRIVATE KEY-----`
  da linha 2946 e o contexto do `test_ic4_segredo_em_contexto_recusado`,
  conferido linha a linha;
- em **`06_p1a/evidencias/revisao-p1a31/pacote-p1a31.txt`**: e o pacote de
  revisao que **embute o fonte** de `test_estabilizacao_p1a1.py`;
- em **`06_p1a/evidencias/varredura_segredo_p1a7.py`**: e **este
  varredor**, que cita `sk-teste-payg-nao-usar-123456` no proprio
  comentario que explica por que a regra so-alfanumerica nao bastava.

**Os 1.640 `hex_sem_contexto` sao 281 valores distintos**, todos de
tamanho 32, 40, 63 ou 64, e todos sao **hash ou identificador**, nao
chave: SHA-1 de objeto git (54 de tamanho 40 — `HEAD`, `PAI`, ALVO de
pacote), SHA-256 de artefato e de pacote (1.215 de tamanho 64 — os cinco
manifestos `.sha256` do canonico sozinhos respondem por 906, e
`artefato_ref`/`entrada_ref` das evidencias da P0 e da P2 pelo grosso do
resto), e UUID4 em hexa (369 de tamanho 32 — id de lab, de sessao e de
lock). Os **2 de tamanho 63** sao ruido de `.pyc`: bytes `0x30` repetidos dentro
de uma amostra de `test_p0_cas_classe_p1a37`, e nao chegam a existir em
fonte nenhum.

**E a contraprova de que a separacao nao absolve por aparencia:** o item
da §6.1 **tem cara de fixture** — mora sob `saidas/labs/`, num diretorio
de corrida de teste, com nome em portugues — e **e chave real**. Ele nao
foi absolvido. Foi medido.

## 6. O QUE E REAL NESTE REPOSITORIO, E O QUE ACONTECE COM ISSO

### 6.1 `chave_selo.bin` — material de chave REAL, e nao viaja

`05_p0/saidas/labs/prova_central/chave_selo.bin`, **32 bytes**, entropia
de Shannon **4,875** sobre 32 bytes — e a chave HMAC de selo do
laboratorio. **E chave real**, nao fixture, e o `.gitignore` a trata como
tal desde sempre (linhas 10 e 35: `chave_selo.bin` e `05_p0/saidas/labs/`).

Tres medicoes, nao uma declaracao:

| Pergunta | Comando | Resposta |
|---|---|---|
| Esta ignorada agora? | `git check-ignore -v` | **sim** — `.gitignore:35` |
| Esteve alguma vez na historia? | `git rev-list --objects --all --reflog \| grep chave_selo` | **nunca** — zero linhas |
| Entra na carga do push? | varredura da carga (§2c), campo `nomes_de_arquivo_suspeitos` | **lista vazia** |

Reforco independente: a historia inteira **nao tem um unico arquivo
`.bin`** — as onze extensoes que ja existiram estao listadas na §5.

Sublinhe-se o que isso custa ao portao: **so a regra de NOME DE ARQUIVO
encontrou este item.** Nenhuma regra de conteudo o pegaria — 32 bytes
aleatorios nao casam com `sk-`, com `AKIA`, nem com base64 de entropia
alta, porque nao sao base64. A cegueira "nome de arquivo" que o despacho
mandou declarar foi **a unica que produziu resultado**.

### 6.2 O nome de usuario real num blob INALCANCAVEL — e tambem nao viaja

A varredura de PII sobre **toda** a historia (617 blobs) devolveu **zero
enderecos de e-mail** e **12 formas distintas de caminho de usuario**,
das quais **onze ja estao redigidas** (`C:\Users\<USUARIO>`,
`C:\Users\alguem`). Sobra **uma**, e ela e real:

> blob `8dfe6276fca8`, **inalcancavel**, versao pre-redacao de
> `06_p1a/99_achados-governanca-20260731.md`, carregando
> `` `C:\Users\IA Lucas\.claude\` `` em texto claro.

O arquivo **rastreado hoje** ja esta redigido — as 12 ocorrencias de
`C:\Users\<USUARIO>` sao dele. O que sobrou foi o **objeto orfao** da
versao anterior, que o `git` guarda ate podar.

**Medido, e nao suposto, que ele nao viaja:** o bundle `--all` foi
clonado, e no clone —

```
git cat-file -e 8dfe6276fca881890e3988a66dd3a39253528819   ->  NAO existe
git cat-file -e $(git rev-parse HEAD:CLAUDE.md)            ->  existe (controle)
```

O controle importa: sem ele, o "nao existe" tambem seria compativel com
*"o clone esta vazio"*. O clone tem **148 commits** e **1.290 objetos**.

**Consequencia pratica, declarada:** isto e PII de baixa gravidade (nome
de usuario de estacao Windows), **nao e credencial**, e **nao sai daqui
com o push**. Nao ha nada a rotacionar. Se um dia se quiser eliminar o
orfao da estacao local, `git reflog expire --expire=now --all && git gc
--prune=now` o faz — **e nao e requisito do push**, porque o push nao o
carrega.

## 7. O QUE ESTA VARREDURA **NAO** COBRE

Declaracao explicita, como a regra de prova exige. As cinco primeiras sao
as cegueiras que o despacho mandou nomear; as quatro ultimas foram
medidas durante a propria corrida.

| # | Cegueira | Situacao nesta varredura |
|---|---|---|
| 1 | **filtro de extensao** | **coberta** na passagem crua — todo blob e todo arquivo, sem olhar extensao. Continua valendo para o portao (18 arquivos rastreados fora das quatro extensoes). |
| 2 | **bloco cercado** | **coberta** na crua. O portao pula o miolo de ``` em `.md`; a crua le tudo. |
| 3 | **`_backups` ignorado** | **coberta** na crua — os 5 arquivos de `06_p1a/evidencias/backups/` foram lidos. |
| 4 | **palavra portuguesa `chave`/`token`** | **coberta** na crua (`atribuicao_pt`, 16 casamentos). |
| 5 | **nome de arquivo** | **coberta** na crua — e foi a **unica** regra a achar material real (§6.1). |
| 6 | **segredo montado por concatenacao no fonte** | **NAO COBERTA em fonte.** Medida: `test_preflight.py:36` e `test_isolamento.py:173` montam `"sk-" + "..."`, e **nenhuma regra de texto casa com o `.py`**. So o `.pyc` denunciou. Uma credencial real escrita assim escaparia de qualquer varredor de texto — **inclusive deste**. |
| 7 | **segredo cifrado, comprimido ou codificado** | **NAO COBERTA.** Nao ha regra que decodifique base64 aninhado, gzip embutido ou blob cifrado. A regra `entropia_alta_b64` devolveu **zero** casamentos em todo o repositorio, o que e consistente com um acervo de texto — mas *zero achado nao e prova de ausencia*, e sim de que **este** eixo nao encontrou nada. |
| 8 | **provedor sem padrao publico conhecido** | **NAO COBERTA.** As 34 regras cobrem os formatos que se sabe reconhecer; um token de provedor com formato generico (hexa puro, ou alfanumerico sem prefixo) so cairia na rede da entropia ou da palavra-chave. |
| 9 | **submodulos, LFS, hooks e config local** | **NAO SE APLICA, medido:** nao ha `.gitmodules`, nao ha ponteiro LFS, e `.git/hooks/` e `.git/config` **nao entram no push por construcao do protocolo**. |

**O que o "zero credencial real" significa e o que nao significa.** Ele
significa: *nenhuma das 34 regras, sobre 100% dos objetos que o push
transmite e 100% dos bytes da arvore, casou com algo que nao fosse
fixture nomeada*. Ele **nao** significa *"e impossivel haver segredo
ali"* — as linhas 6, 7 e 8 acima sao os caminhos por onde um segredo
passaria sem ser visto, e eles ficam registrados **antes** do push, nao
depois.

## 8. O PESO — QUANTO VIAJA, E POR QUE SE MEDE ANTES

Peso rastreado **viaja para sempre**: o log de tunel de 5,1 MB do
`nxtrack` foi apagado da arvore e continua na historia daquele
repositorio. Por isso a medida vem antes do push, nao depois.

| Grandeza | Medida |
|---|---|
| Arquivos rastreados em HEAD | **361 arquivos** |
| Bytes da arvore de HEAD, descompactada | **4.011.134 B** = **3,825 MB** |
| Blobs em toda a historia | **617 blobs** |
| Soma dos blobs, descompactada | **7.295.110 B** = **6,957 MB** |
| **Carga do push** (`git bundle create --all`) | **1.600.613 B** = **1,526 MiB** |
| Objetos na carga | **1.290 objetos**, em 148 commits |

**Estas seis linhas medem `1f45fdd`, ANTES dos arquivos desta ordem.** O
commit desta ordem acrescenta o varredor e a evidencia reduzida, e o
peso final medido **depois** dele esta na §12 — que so pode existir apos
o commit, porque medir antes seria estimativa, e estimativa nao e
medicao.

**O que o push transmite sao 1,53 MiB**, nao os 6,96 MB da soma crua: o
empacotamento e o delta entre versoes de documento fazem a diferenca — e
este acervo e quase todo texto reescrito muitas vezes, que e o caso
otimo para delta.

**Os cinco maiores em HEAD**, que sao onde qualquer corte futuro teria
efeito:

| Bytes | Caminho |
|---|---|
| 447.693 | `06_p1a/evidencias/revisao-p1a31/pacote-p1a31.txt` |
| 139.986 | `logs/diff-0.2.1-hardening.patch` |
| 88.511 | `06_p1a/evidencias/revisao-p1a38/pacote-p1a38.txt` |
| 75.599 | `logs/diff-0.3-frota.patch` |
| 54.943 | `05_p0/ssc_p0/kernel.py` |

**Nao se recomenda cortar nenhum deles**, e a razao e do proprio acervo:
os pacotes de revisao sao **o objeto que os revisores independentes
julgaram**, e o MAJOR #5 existe justamente porque pacote nao ancorado nao
prova nada. Reescrever historia para emagrecer 0,5 MB destruiria a
ancoragem que custou quatro missoes. **A recomendacao e a inversa: daqui
para frente, evidencia grande nasce reduzida** — foi o que se fez com
esta propria varredura, na §9.

## 9. O PESO DA PROPRIA EVIDENCIA — a regra aplicada a si mesma

O dump integral desta varredura tem **1.510.735 bytes**. Versiona-lo
adicionaria **quase o peso do push inteiro** (1.600.613 B) para registrar
1.714 casamentos dos quais 1.640 sao hashes conhecidos. Seria repetir o
log de tunel, na mesma missao que o cita como licao.

O que se versionou foi a **forma reduzida**, **59.865 bytes**, e o corte
esta declarado dentro do proprio JSON (campo `o_que_se_largou`):

- **preservado integralmente:** os 74 casamentos nao-hex com linha, valor
  e contexto; todas as contagens; `total_de_achados` e `por_regra` das
  tres passagens, **computados antes do corte**;
- **largado:** linha, valor e contexto de cada `hex_sem_contexto`;
- **preservado do que se largou:** total (1.640), valores distintos
  (281), distribuicao por tamanho e contagem por arquivo de origem;
- **como regenerar:** o mesmo script **sem** `--reduzido`, sobre o mesmo
  estado da arvore. A copia integral desta corrida ficou fora do
  repositorio, no scratchpad da sessao.

**Corte declarado nao e corte silencioso** — e a diferenca entre "cobri
tudo" e "cobri tudo e disse o que joguei fora".

## 10. O QUE ESTA ORDEM NAO FEZ

- **Nao corrigiu o achado (N) da §4.** Nao existe, ao fim desta ordem,
  guarda versionado que rode esta varredura em CI ou em pre-commit. O
  instrumento existe e e reprodutivel; **guarda, nao ha**. Quem quiser
  fecha-lo tem de exercer a interface real, nao afirmar a propriedade.
- **Nao rotacionou nada**, porque nada exigia rotacao.
- **Nao podou o orfao** da §6.2, porque podar altera o banco de objetos
  da estacao e **nao e requisito do push** — e a decisao de mexer no
  reflog e do Fundador, nao desta ordem.
- **Nao rodou a suite.** Esta ordem nao alterou codigo de producao: ela
  acrescentou um instrumento de evidencia e dois documentos. Nao houve
  mutante, e `scratchpad/MUTANTE-ATIVO.txt` foi conferido **antes** de
  qualquer medicao, conforme a P1-A.3.9: **ausente**, arvore limpa.
- **Nao emitiu atestado.** O veredito abaixo e sobre **publicacao**, e
  vale sobre o estado `1f45fdd` mais os arquivos desta ordem.

## 11. DECISAO DA ORDEM 6

> ## `PUSH LIBERADO`
>
> **Zero credenciais reais na carga do push.** 609 blobs varridos, 0
> inalcancaveis, 361 arquivos, 11.220.503 bytes lidos byte a byte; os 39
> casamentos nao-hex sao as nove fixtures da §5, todas nomeadas, todas
> com o teste que as recusa versionado ao lado.
>
> A unica chave real da estacao (`chave_selo.bin`) **nunca esteve na
> historia** e **nao esta na carga** — medido por tres caminhos
> independentes. O unico vazamento de PII (`C:\Users\IA Lucas\...`) vive
> num blob **inalcancavel**, e o clone do bundle prova que ele **nao
> viaja**.
>
> **Peso que sobe: 1,53 MiB em 1.290 objetos, 148 commits, 361 arquivos
> rastreados.**
>
> As tres cegueiras que sobrevivem a esta varredura estao na §7, linhas
> 6, 7 e 8, e nenhuma delas se resolve por leitura: exigem instrumento
> que esta ordem nao construiu.

**Contagem como medida, nunca como meta.** Os numeros deste registro —
34 regras; 7 achados no portao contra 1.714 na crua; 74 casamentos
nao-hex reduzidos a 48 combinacoes e a 9 fixtures; 281 valores hexa
distintos; 1 chave real fora da historia; 1 blob inalcancavel com PII que
nao viaja; 1.600.613 bytes de carga — sao o que foi medido, e valem sobre
o estado que os produziu.
