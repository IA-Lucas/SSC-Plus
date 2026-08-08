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
> **Peso que sobe, ja incluidos os dois commits desta ordem: 1,551 MiB
> (1.626.159 B), 150 commits, 364 arquivos rastreados, 613 blobs, zero
> inalcancaveis** — medido em `43577de`, o ultimo commit desta ordem.
> Antes dela: 1,526 MiB, 148 commits, 361 arquivos. **A regressao e
> conhecida e fica declarada:** cada commit muda o proprio numero que ele
> registra, e o unico jeito de fecha-la seria nao registrar nada. O que
> vale para a decisao e a ordem de grandeza — **um MiB e meio** —, nao o
> ultimo digito.
>
> As tres cegueiras que sobrevivem a esta varredura estao na §7, linhas
> 6, 7 e 8, e nenhuma delas se resolve por leitura: exigem instrumento
> que esta ordem nao construiu.

## 12. O PESO FINAL, MEDIDO DEPOIS DO COMMIT — e o efeito colateral que a propria ordem produziu

A §8 mediu `1f45fdd`. Esta secao mede `f4399e4`, o commit desta ordem, e
so pode existir depois dele.

| Grandeza | Em `1f45fdd` | Em `f4399e4` | Delta |
|---|---|---|---|
| Arquivos rastreados em HEAD | 361 | **364** | +3 |
| Bytes da arvore de HEAD | 4.011.134 | **4.110.113** = **3,920 MB** | +98.979 B |
| Blobs em toda a historia | 617 | **620** | +3 |
| **Carga do push** | 1.600.613 B | **1.623.609 B** = **1,548 MiB** | **+22.996 B** |
| Blobs na carga (inalcancaveis) | 609 (0) | **612 (0)** | +3 |

**Os tres arquivos custam 98.979 bytes na arvore e 22.996 bytes na carga
— 22 KiB.** O empacotamento absorve os outros 76 KB porque o JSON
reduzido e texto repetitivo. **O peso do push subiu 1,4%.**

### O efeito colateral, medido e nao escondido

A varredura, ao ser versionada, **virou a maior fonte de casamentos do
repositorio**. Rodada sobre `f4399e4`, a carga do push devolve **365
casamentos nao-hex**, contra 39 em `1f45fdd`. A atribuicao e exata:

| Casamentos nao-hex | Arquivo |
|---|---|
| **304** | `06_p1a/evidencias/p1a7-varredura-segredo-...json` — a evidencia **ecoa cada valor casado** |
| **20** | `06_p1a/99_decisao-p1a7.md` — este documento **cita as nove fixtures pelo nome** (§5) |
| **2** | `06_p1a/evidencias/varredura_segredo_p1a7.py` — o varredor **carrega as 34 regras** |
| **39** | os oito arquivos de sempre, inalterados |

**326 dos 365 nasceram desta ordem.** Nenhum e credencial: sao a fixture
`sk-teste-payg-nao-usar-123456` e as oito irmas dela, agora citadas em
tres lugares a mais. Mas a consequencia e concreta e fica registrada:
**quem rodar esta varredura na proxima vez vera o numero saltar de 39
para 365 sem que nada tenha vazado.** Um varredor de terceiros — o do
GitHub, por exemplo — vai apontar para estes tres arquivos. A resposta
esta escrita aqui, com a atribuicao linha a linha, e nao precisara ser
reconstruida no susto.

**Alternativa que existia e foi recusada:** redigir os valores casados na
evidencia. Ela reduziria os 304 a zero — e destruiria a unica coisa que
faz a evidencia servir: **o valor literal e o que permite a um terceiro
conferir que aquilo e fixture**. Evidencia de varredura que esconde o que
achou pede fe, e este acervo nao trabalha com fe. O preco esta medido
acima: 22 KiB e 326 casamentos explicados.

**Contagem como medida, nunca como meta.** Os numeros deste registro —
34 regras; 7 achados no portao contra 1.714 na crua; 74 casamentos
nao-hex reduzidos a 48 combinacoes e a 9 fixtures; 281 valores hexa
distintos; 1 chave real fora da historia; 1 blob inalcancavel com PII que
nao viaja; 1.600.613 bytes de carga em `1f45fdd` e **1.623.609 bytes em
`f4399e4`** — sao o que foi medido, e valem sobre o estado que os
produziu. Duas medicoes de estados diferentes ficam **com o nome do
estado ao lado de cada uma**, e nunca viram uma so.

---

# PARTE II — ORDENS 1 A 5: O GERADOR QUE DESCARTA EM SILENCIO

> **Registro aditivo.** A Parte I (ordem 6) **nao foi tocada** — nem uma
> linha. Ela abre dizendo que *"as ordens 1 a 5 da P1-A.7, se existirem,
> nao estao neste registro"*, e aquilo **era verdade quando foi
> escrito**. Deixa de ser verdade a partir desta linha, e a frase fica
> como esta: reescreve-la esconderia que o autor da ordem 6 nao tinha
> como saber o que viria. Esta parte **nao certifica nada** e **nao
> corrigiu MAJOR nenhum**.

## DECISAO DAS ORDENS 1 A 5: **CONCLUIDO-COM-PULADOS**

As cinco ordens foram executadas e medidas. O que ficou pulado esta
nomeado na secao II.8, e nada disso era ordem desta missao: sao
**achados novos**, dois deles **regressao da propria ordem 6**, que o
despacho proibe corrigir aqui.

## SUMARIO — 10 linhas

1. O gerador descartava **por lista de extensao**, e o descarte era
   **mudo**: o caminho nao caia em ramo nenhum e nenhuma linha o
   registrava.
2. Na janela do pacote **que os dois revisores julgaram**, o descarte
   foi **1**: o `pytest.ini`. Na janela do pacote da **P1-A.4**, foram
   **4** — e um deles e o `06_p1a/.gitattributes`, que carrega **o
   remedio do MAJOR #5**.
3. Dos **364** arquivos rastreados, **18** ficam fora das quatro
   extensoes, e **zero** deles e ruido: este repositorio nao rastreia
   lock, cache nem binario gerado. A lista de extensao **so podia
   descartar conteudo**.
4. O criterio novo nao e lista: e **o que o pacote precisa provar** —
   **LIDO**, **ANCORADO** ou **EXCLUIDO NOMEADO**. O **default e
   ancorar, nunca descartar**.
5. A completude passou a ser **exercida** (`conferir_cobertura` levanta)
   em vez de **afirmada** na docstring, que era a familia do MAJOR #3
   dentro do arquivo que o pacote manda julgar.
6. **Reversao vermelha**: o gerador revertido regenera o pacote julgado
   **byte a byte** — `673271a7…`, **141 903 B** —, o `pytest.ini` **some
   sem uma linha de aviso**, e o guarda novo fica **19 vermelho**.
7. **Controle positivo nas duas polaridades**: acha (8 passed, 13
   subtests) e acusa (19 failed); e `conferir_cobertura` **nao** levanta
   quando a cobertura e total — sem essa metade, um `raise`
   incondicional passaria.
8. O mesmo commit hoje produz **153 603 B**, `41533c59…`, **42 de 42**
   caminhos. **Nao foi reenviado.**
9. O lab de P2 **sumiu**: procurado em cinco lugares independentes, zero
   em todos. A regra *"limpar `saidas/labs` exige copia datada antes"*
   esta gravada no `CLAUDE.md`.
10. A contagem **oito ou nove** fica **aberta**, com dono e gatilho — e
    com uma ressalva que esta missao mediu e que muda o peso do parecer
    do `codex` (II.6).

## II.1 PRE-CONDICOES — e a estacao que nao e a mesma

| Pre-condicao | Medido | Reproduz? |
|---|---|---|
| `scratchpad/MUTANTE-ATIVO.txt` na abertura | **ausente** | sim |
| HEAD | `8dd1470`, arvore **limpa** | sim |
| Suite **P0** | **344 passed, 256 subtests** | **sim**, identico |
| **Prova central** | **18 assercoes, 20 eventos** | **sim**, identico |
| Suite **P1-A** | **10 failed, 900 passed, 6 skipped, 1195 subtests** | **NAO** |
| Lease de nome proprio | `p1a7-ordens1a5-ops`, fences **1** e **2** | — |

**A suite P1-A nao reproduz, e a causa foi medida, nao suposta.** Duas
coisas mudaram sob o acervo, e nenhuma delas e codigo:

- **o interpretador.** O acervo registra **Python 3.14.3**
  (`coleta-20260730-092436/00_ambiente.txt`). Esta estacao tem
  **3.11.9**, e **nao tinha `pytest`** — ele foi instalado nesta sessao
  (9.1.1) para que houvesse medicao. Numero de suite comparado entre
  interpretadores diferentes e numero herdado;
- **o usuario.** O acervo foi escrito numa estacao cujo usuario era
  `IA Lucas`; esta e `lucas`. Os guardas de PII **derivam o alvo da
  estacao** de proposito, e o token curto `lucas` casa **dentro** de
  `lucasia` num artefato rastreado. O guarda nao errou: ele mede outra
  coisa aqui.

**O lease criou `locks/`, e isso mudou um numero.** O diretorio nao
existia nesta estacao; ao adquirir o escritor unico ele nasceu, e
`test_gitignore_efetivo_p1a39::test_o_diretorio_de_locks_existe_de_fato_nesta_estacao`
**passou a passar**. Fica declarado porque, sem isto, a diferenca entre
10 e 9 falhas pareceria efeito das correcoes — e nao e.

### II.1.1 A ORDEM 6 DEIXOU A SUITE VERMELHA, e nao soube

Medicao **diferencial**, na mesma estacao e no mesmo interpretador —
clone `--no-hardlinks` em `1f45fdd` contra `HEAD`:

| Estado | Resultado |
|---|---|
| `1f45fdd` (**antes** da ordem 6) | **8 failed**, 902 passed, 6 skipped, 1195 subtests |
| `8dd1470` (**depois**) | **10 failed**, 900 passed, 6 skipped, 1195 subtests |

**Os dois testes a mais sao regressao da ordem 6**, causada pelos tres
arquivos que ela commitou:

| Guarda que ficou vermelho | Causa, atribuida arquivo a arquivo |
|---|---|
| `test_isolamento.py::ZeroSegredoNosArtefatos` | **71 casamentos**: **66** em `p1a7-varredura-segredo-*.json`, **4** em `99_decisao-p1a7.md`, **1** em `varredura_segredo_p1a7.py` |
| `test_estabilizacao_p1a1.py::ZeroPiiNosArtefatos` | `99_decisao-p1a7.md` e o **unico** arquivo rastreado do acervo que carrega a forma literal do usuario historico (**2 ocorrencias**), escrita ao documentar o blob orfao na secao 6.2 |

**Nenhum dos 71 e credencial**, e nenhuma das 2 e vazamento novo: sao as
fixtures que a propria ordem 6 nomeou e o nome que ela transcreveu para
registrar. **O defeito nao e vazamento — e guarda versionado vermelho**,
que e o que impede o proximo commit de ser julgado por suite verde.

A ordem 6 **declarou** que nao rodou a suite (secao 10, *"Nao rodou a
suite"*). A razao dada era defensavel — *"nao alterou codigo de
producao"* — e a medicao mostra o buraco dela: **os guardas deste acervo
varrem a ARVORE, nao o codigo**. Acrescentar documento **e** alterar o
que eles medem. Ironia registrada e nao suavizada: a ordem que mediu o
repositorio inteiro em busca de segredo foi a que deixou o guarda de
segredo vermelho.

**Esta missao nao corrige isso** — e achado novo, e o despacho proibe.
Fica na secao II.8 com dono e gatilho.

## II.2 ORDEM 1 — O QUE FICOU DE FORA, NOMINALMENTE

O gerador vigente ate aqui roteava por **lista de extensao**
(`EXTENSOES_HASHEADAS`, linha 55): `.py` para diff ou integra,
`.md`/`.json`/`.txt` para SHA-256, removidos para linha de remocao.
**Todo o resto caia fora dos dois ramos e nao era registrado em lugar
nenhum.**

### II.2.1 Por janela de pacote real

| Janela | Caminhos no diff | Descartados | Nominalmente |
|---|---|---|---|
| **P1-A.4** `6a3a3f8..3f24085` | 195 | **4** | `.gitignore`; `06_p1a/.gitattributes`; `revisao-p1a36/.gitattributes`; `revisao-p1a38/.gitattributes` |
| **P1-A.6** `3f24085..0a40667` — *o pacote julgado* | 42 | **1** | `pytest.ini` |
| **HEAD** `3f24085..8dd1470` | 48 | **1** | `pytest.ini` |

**O pior descarte nao e o `pytest.ini`.** E o `06_p1a/.gitattributes` da
janela da P1-A.4, e a razao esta no conteudo dele:

    /evidencias/pacote_p1a37.py -text

Essa linha entrou em `bd055b9` — *"o remedio do MAJOR #5 nao reproduzia:
medido e corrigido"*. Ela e **o que faz o pacote reproduzir byte a
byte**, marcando o fonte do proprio gerador contra normalizacao de EOL.
**O pacote da P1-A.4 pedia julgamento sobre a sua reprodutibilidade e
descartou, em silencio, o arquivo que a produz.**

### II.2.2 Conteudo ou ruido? — a resposta e que nao havia ruido

Dos **364** arquivos rastreados em HEAD, **18** ficam fora das quatro
extensoes: 5 `.sha256` (manifestos do canonico), 3 `.patch`, 2 `.diff`,
5 `.gitattributes`, `.gitignore`, `pytest.ini` e `coletar.sh`.

**Zero e ruido.** E nao por generosidade de classificacao: este
repositorio **nao rastreia** lock, cache, bytecode nem binario gerado —
todos estao no `.gitignore`. Entre arquivos rastreados **nao existe
descartavel**, e por isso o filtro por extensao **so podia descartar
conteudo**. E o argumento mais forte contra a lista: ela nao distinguia
nada, porque nao havia nada a distinguir.

## II.3 ORDEM 2 — O FILTRO NOVO

### II.3.1 (a) O criterio, declarado por escrito

Esta na docstring do gerador e no cabecalho de todo pacote. A pergunta
deixa de ser *"a extensao esta na lista?"* e passa a ser **o que o
pacote precisa provar**:

| Disposicao | Quem cai aqui | Como entra |
|---|---|---|
| **LIDO** | o revisor precisa **LER** para julgar se a correcao fecha o que diz fechar: o que **executa** (`.py`, `.sh`) e o que alguma **ferramenta consulta** para decidir comportamento (`pytest.ini`, `conftest.py`, `.gitattributes`, `.gitignore`, `setup.cfg`, `pyproject.toml`, `tox.ini`, `.editorconfig`) | modificado, como diff; novo, inteiro |
| **ANCORADO** | o revisor precisa **ANCORAR**, nao ler inteiro: registro, evidencia, corpus, binario — **e toda extensao que o gerador nao conhece** | SHA-256 do blob |
| **EXCLUIDO** | so existe se **NOMEADO** em `EXCLUSOES_NOMEADAS`, com motivo | linha declarada. **Lista vazia hoje** |

**A propriedade que importa: o default e ANCORAR, nunca DESCARTAR.** A
extensao deixou de ser o portao e passou a decidir apenas *quanto* do
arquivo o revisor ve. Errar a classificacao custa **detalhe**; nunca
mais custa **silencio**. Um `.parquet` que ninguem previu entra com o
seu hash em vez de evaporar — e ha teste para isso.

E a completude passou a ser **exercida**: `conferir_cobertura` levanta
`CoberturaIncompleta` se sobrar um so caminho do `git diff
--name-status`. A docstring anterior **afirmava** *"EXCLUSOES, todas
declaradas e nenhuma silenciosa"* enquanto o codigo descartava — a
familia do **MAJOR #3**, dentro do arquivo que o pacote manda julgar.

### II.3.2 (b) O descartado sai DECLARADO no manifesto

Toda saida agora carrega, antes do conteudo:

    === MANIFESTO DE COBERTURA — todo caminho do diff, com motivo ===
    caminhos no diff: 42  =  lidos 21+4  ancorados 17  removidos 0  excluidos 0
      LIDO      pytest.ini  — configuracao de mecanismo (pytest.ini)
      ANCORADO  06_p1a/99_decisao-p1a5.md  — registro, evidencia ou ...

O revisor **confere a conta** em vez de acreditar nela, e o total do
manifesto e comparado ao `git diff` por teste.

### II.3.3 As duas provas

**Reversao vermelha, com o mutante registrado antes** em
`scratchpad/MUTANTE-ATIVO.txt`, conforme a P1-A.3.9:

| Medicao | Com o filtro NOVO | Com o gerador REVERTIDO |
|---|---|---|
| `pytest.ini` no pacote | **presente**, como `LIDO` | **ausente** |
| aviso na saida do gerador | — | **nenhum** — so `pacote/sha256/bytes` |
| guarda `test_cobertura_pacote_p1a7` | **8 passed, 13 subtests** | **19 failed, 2 passed** |
| suite P1-A inteira | 9 pre-existentes | **28 failed** = 19 do guarda + 9 pre-existentes |

**A reversao mede o objeto certo, e isso foi provado e nao suposto:** o
gerador revertido regenerou o pacote da P1-A.6 com **SHA-256
`673271a79bebd603a327aa58f435ea69c488e5e6e569a89dd98bbb1aeeb2cc9f`** e
**141 903 bytes** — **identicos** ao que a secao 12.2 da P1-A.6
registrou e ao `pacote_sha256` que **os dois revisores conferiram e
ecoaram** (medido tambem no JSON cru dos dois vereditos). Nao e um
pacote parecido: e o mesmo.

E a unica ocorrencia da string `pytest.ini` no pacote revertido esta na
**linha 2828**, dentro da **docstring** do `conftest.py` — exatamente o
que a P1-A.6 secao 13.4 havia medido. O arquivo nunca esteve la.

**Controle positivo nas duas polaridades**, porque um guarda que so sabe
dizer "esta tudo certo" nao distingue arvore sa de varredura quebrada:

- **acha o que deve achar** — `pytest.ini` no pacote do par real, com
  disposicao, motivo **e os bytes** (`addopts = -p no:cacheprovider`),
  para que constar do manifesto sem viajar nao passe por inclusao;
- **acusa quando o defeito volta** — `conferir_cobertura` recebe caminho
  fora das tres disposicoes e **levanta**, com a funcao REAL e dado
  REAL, sem duble;
- **e nao levanta quando a cobertura e total** — sem esta terceira
  metade, um `raise` incondicional passaria no teste anterior e o guarda
  nao mediria nada.

**O caso que OCORRE, e nao o vizinho dele.** O par `(3f24085, 0a40667)`
nao e exemplo: e o par exato do pacote julgado. O vizinho recusado —
afirmar que `disposicao("pytest.ini")` devolve `"lido"` — exerceria a
**primitiva**, e o achado **N4** deste acervo existe porque primitiva
corrigida **nao cobre ponto de chamada**.

### II.3.4 O que o guarda NAO cobre, declarado

- **nao prova que a classificacao LIDO/ANCORADO esteja CERTA** para cada
  arquivo — prova que ela e **TOTAL**. Um `.md` ancorado quando o
  revisor precisaria le-lo continua sendo perda de **detalhe**; o que se
  fechou foi a perda **silenciosa**;
- **nao cobre renomeacao.** O parser trata `R` como modificacao, e nada
  aqui afirma que renomeacao esteja bem tratada;
- **nao mede tamanho de pacote nem se ele cabe em revisor algum**;
- **nao reabre nenhuma linha `FECHADO`** da P1-A.6.

## II.4 ORDEM 3 — O QUE OS DOIS VEREDITOS NAO VIRAM

Mesmo commit, `3f24085..0a40667`:

| | Julgado pelos dois revisores | Regerado agora |
|---|---|---|
| SHA-256 | `673271a7...` | `41533c59...` |
| Bytes | **141 903** | **153 603** |
| Caminhos cobertos | **41** de 42 | **42** de 42 |
| `pytest.ini` | **ausente** | **LIDO**, com bytes |

**O unico arquivo que faltava era o `pytest.ini`** (1 578 B). Os outros
11 700 bytes de diferenca sao o criterio declarado, o manifesto e a
docstring maior do proprio gerador, que se auto-inclui.

### II.4.1 Ele toca um MAJOR aberto? — sim, a familia; e nao, nao o fecha

O `pytest.ini` e o **mecanismo** da correcao da P1-A.5.1: `addopts = -p
no:cacheprovider`, que tirou o cache da arvore vigiada e fez sumir
**tres das quatro** classes de mutacao que a contencao acusava.

Ele toca a familia de **dois itens abertos**: o achado novo do `kimi`
`08_p2/saidas:quarta-classe-de-mutacao` e o item da **P1-A.5 secao 5.5**
(a porta que continua nao construida).

**E nao fecha nenhum dos dois** — e aqui a precisao importa mais que a
conveniencia. A **quarta** classe, *a sessao editando um fonte*, e
justamente a que o `pytest.ini` **nao alcanca**, e a propria P1-A.5.1 diz
isso em letra (*"nao e a porta"*). Portanto **nao houve revisor
apontando defeito que a correcao ja resolvia**: o `kimi` apontou
exatamente o que continua aberto.

**E nenhuma linha `FECHADO` dependia do arquivo ausente.** Os quatro
MAJOR que os dois fecharam — `N1`, `P1A4-1`, `P1A4-3`, `P1A4-6` — tratam
do escritor unico e do acoplamento; nenhum trata do cache. **A omissao
nao fabricou fechamento falso**, e isso limita o dano de forma aferivel.

**O que se perdeu, entao, foi outra coisa, e nao e pequena:** os dois
revisores tiveram de aceitar **por afirmacao do registro** que tres
classes de mutacao sumiram, em vez de **ler as tres linhas do mecanismo
que as faz sumir**. Num acervo cuja doutrina inteira e *exercer, nao
afirmar*, a omissao transferiu para os revisores exatamente a postura
que este repositorio recusa — e eles **nao tinham como detecta-la**. O
`kimi` chegou a registrar o gerador como *"na leitura, sem defeito"*.

**Nao foi reenviado.** O despacho proibe, e o pacote novo existe apenas
como medicao.

## II.5 ORDEM 4 — A EVIDENCIA DESTRUIDA

`08_p2/saidas/labs/20260803T135101Z/` (corrida `p22-c-repeticao`).
**Procurado em cinco lugares independentes:**

| Onde | Resultado |
|---|---|
| Banco de objetos + `--reflog` | **zero** ocorrencias |
| Lixeira de `E:` | **zero** (busca por `20260803`, `p22-c`, `chave_selo`, `labs`) |
| `06_p1a/evidencias/backups/` | so `tiers_declarados` e `prova_central` |
| `%TEMP%` | **zero** |
| Varredura de `E:` por nome | o unico `chave_selo.bin` e o lab de **P0**, regenerado hoje |

**Nao ha copia. O lab sumiu**, e isto confirma por medicao independente
o que a P1-A.6 secao 4.1 ja declarava contra si.

**Nao checado, e declarado:** copias de sombra (**VSS**) exigem elevacao
que esta sessao nao tem — `vssadmin` recusou por permissao. E a **unica**
porta que continua fechada por falta de privilegio, e nao por medicao.
Quem tiver console elevado pode conferir com `vssadmin list shadows`; a
probabilidade e baixa (o volume e `E:`, e a exclusao foi ha tres dias),
mas **baixa nao e zero**, e afirmar "irrecuperavel" sem essa checagem
seria afirmar mais do que se mediu.

**A regra foi gravada no `CLAUDE.md`**, na secao *"LIMPAR `saidas/labs`
EXIGE COPIA DATADA ANTES (P1-A.7)"*. Ela nao cria regra nova: torna
legivel, onde toda sessao le, a regra permanente que **existia e nao
impediu o dano porque nao estava la**.

## II.6 ORDEM 5 — A CONTAGEM OITO OU NOVE (nao decidida)

**O `kimi`**, na frase dele, do JSON cru:

> *"CONTAGEM: julgo NOVE a contagem correta. A regra do acervo
> (P1-A.3.6 §9.4) mantem separado o trio 6/N5/P1A4-2 precisamente para
> que a fusao nao produza aparencia de progresso; aplicada com simetria
> ao par N1/P1A4-1, da nove. Fundir um par e nao o outro seria
> assimetrico; fundir os dois daria seis objetos, e a contagem deixaria
> de medir o que ela existe para medir. Ficam nove linhas."*

**O `codex`** respondeu as nove linhas **sem contestar a contagem**.

### II.6.1 A ressalva que esta missao mediu, e que muda o peso

Os dois receberam o **mesmo prompt** — `prompt_sha256` identico,
`0a029c37...` — e esse prompt **dizia o numero antes de perguntar**:

> *"**NOVE** linhas, uma por MAJOR (...) **NAO funda** N1 com P1A4-1,
> nem o trio 6/N5/P1A4-2: sao nove linhas. Se julgar que a contagem
> correta e outra, diga-o em linha separada, com o motivo."*

**Consequencia, declarada e nao suavizada:** o silencio do `codex` e
**evidencia fraca** — o instrumento pediu nove linhas e **antecipou a
fusao** que a pergunta deveria testar. O parecer do `kimi` e **mais
forte**, porque traz razao propria (a simetria), mas foi dado **dentro
do mesmo enquadramento**.

A P1-A.6 secao 13.3 escreveu que *"a questao que a secao 5 deixou aberta
ao Fundador tem, agora, resposta de revisor independente"*. Isso
continua verdadeiro para o `kimi` e **mais fragil do que parecia** para
o `codex`. **Esta missao nao decide**, e registra a fragilidade para que
a decisao nao se apoie num consenso que o proprio instrumento ajudou a
produzir.

| Campo | Valor |
|---|---|
| **Dono** | **Fundador** |
| **Gatilho** | **antes da proxima revisao independente** — a contagem e o **denominador** de *"quantos fecharam"* |
| **Recomendacao de metodo** | se a questao for reaberta, perguntar **sem** dizer o numero no prompt |

## II.7 ATENCAO — OS NUMEROS QUE NAO REPRODUZEM

Remedidos **neste disco**, em `8dd1470`, por `git grep`. **Nao herdei
numero nenhum.**

| Termo | Ocorrencias aqui | Leitura |
|---|---|---|
| `oito MAJOR` | **1** | `99_decisao-p1a6.md:282` — e **citacao de um despacho, refutada na mesma frase** (*"O acervo tem nove"*). Como **afirmacao do acervo: zero** |
| `quarto ciclo` | **0** | o acervo escreve `quatro ciclos` (**1**) e `tres ciclos` (**5**). A forma ordinal-singular **nunca existiu** |
| `P1A5-1` | **0** | **nao ha familia `P1A5-*`.** Os **unicos** ids de achado do acervo sao `P1A4-1..6` |

**Os tres zeros da F30 REPRODUZEM**, com um so ajuste: `oito MAJOR` tem
**uma** ocorrencia citada e refutada, e **zero** como afirmacao propria.

**E o zero de `P1A5-1` tem razao estrutural, nao tipografica** — o que
importa mais que o numero. Nao existe achado `P1A5-*` porque a **P1-A.5
foi missao de CORRECAO**, e correcao **nao emite achado**: e a regra
*"quem corrige nao certifica"* aparecendo na forma dos identificadores.
`P1-A.5.1` (27 ocorrencias) e rotulo de **missao**, nunca de achado.
Procurar `P1A5-1` e procurar uma classe de objeto que este acervo, por
construcao, nao produz.

## II.8 O QUE ESTA MISSAO **NAO** FEZ

- **nao corrigiu MAJOR nenhum.** Os nove seguem como estavam;
- **nao enviou pacote, nao invocou provedor** — **zero** chamada paga,
  **zero** custo variavel;
- **nao renovou cota nem tier**, e nao leu declaracao de tier;
- **nao reescreveu Parte I** de registro nenhum;
- **nao decidiu** a contagem oito-ou-nove;
- **nao reexaminou** nenhuma das quatro linhas `FECHADO` da P1-A.6 sob o
  limite do `pytest.ini` ausente;
- **nao corrigiu a regressao da ordem 6** (II.1.1), nem os guardas de
  PII sensiveis a estacao. **Sao achados novos**, e o despacho proibe
  corrigir aqui.

### Os achados novos que esta missao devolve ao Fundador

| # | Achado | Familia | Dono | Gatilho |
|---|---|---|---|---|
| **P1A7-a** | A ordem 6 deixou **dois guardas versionados vermelhos** (`ZeroSegredoNosArtefatos`, `ZeroPiiNosArtefatos`) ao commitar evidencia que ecoa fixtures e transcreve o usuario historico | **(N)** — classe que a varredura dos 86 guardas nao media: guarda que fica vermelho por **conteudo de documento**, nao por codigo | missao que tratar a varredura de segredo | **imediato**: enquanto durar, "suite verde" nao e aferivel na P1-A |
| **P1A7-b** | Os guardas de PII casam por **substring** sobre um token derivado da estacao; `lucas` casa dentro de `lucasia`. Numa estacao de nome curto o guarda acusa operacao normal | **(F)** — o guarda **afirma** *"zero PII"* e o que ele exerce e *"zero ocorrencias da substring"* | missao que tratar contencao/PII | ja ocorreu nesta estacao |
| **P1A7-c** | `test_p2_receita_medidor_p24` falha em **6 pontos** nesta estacao, com `p22-a` recalculando **19,907** contra **19,558** publicados — e falha **tambem em `1f45fdd`**, logo **nao** e regressao da ordem 6 nem desta missao | fora de ambas | missao de reproducao da P2 (mesmo dono do `P1A4-4`) | ja ocorreu; agrava o `P1A4-4` |

**Nenhum dos tres foi corrigido aqui**, e nenhum e certificado por esta
missao.


## II.9 A SUITE MEDIDA DEPOIS DO COMMIT — e a conta que fecha

A secao II.1 mediu `8dd1470`, **antes** dos arquivos desta missao. Esta
secao mede `4410e90`, o commit delas, e **so pode existir depois dele** —
medir antes seria estimativa, e estimativa nao e medicao. E o mesmo
procedimento que a ordem 6 usou na Parte I.

O degrau importa por uma razao mecanica: `test_ancoragem_gerador_p1a38`
compara os bytes do gerador **em disco** com os bytes do blob em
**`HEAD`**, nao no indice. Com o gerador alterado e **nao commitado**,
ele fica vermelho **por construcao** — e ficou, e foi assim que se
descobriu que *"suites com arquivos staged"* nao basta para este guarda
em particular. Ele fecha no commit, nao no `git add`.

| Grandeza | `8dd1470` (antes) | `4410e90` (depois) | Delta |
|---|---|---|---|
| failed | **10** | **9** | **-1** |
| passed | 900 | **909** | **+9** |
| skipped | 6 | **6** | 0 |
| subtests passed | 1195 | **1208** | **+13** |

**A conta fecha, e cada unidade tem dono:**

- **-1 failed e +1 dos 9 passed**: `test_gitignore_efetivo_p1a39` deixou
  de falhar porque o **lease criou `locks/`**, que nao existia nesta
  estacao. **Nao e efeito da correcao** — e efeito de adquirir o
  escritor unico, e ja estava declarado na II.1;
- **+8 dos 9 passed e os +13 subtests**: sao o guarda novo
  `test_cobertura_pacote_p1a7`, inteiro.

**A correcao do gerador, sozinha, nao move nenhuma linha vermelha** — e
isso e o esperado, nao uma decepcao: ela conserta um **instrumento**, e o
que ela produz e um guarda novo verde, nao a cura de falha antiga.

### As 9 que ficam, com a causa separada por medicao

| Quantas | Quais | Causa | Regressao da ordem 6? |
|---|---|---|---|
| **2** | `ZeroSegredoNosArtefatos`, `ZeroPiiNosArtefatos` | os tres arquivos que a ordem 6 commitou | **SIM** (II.1.1) |
| **6** | `test_p2_receita_medidor_p24` (5 + 1 subtest) | estacao; falha **tambem** em `1f45fdd` | nao |
| **1** | `ZeroPiiNasTresRaizes` (subtest `06_p1a`) | `lucas` casando dentro de `lucasia` | nao |

**A suite P1-A nao esta verde, e esta missao nao a deixou verde.** As
nove estao nomeadas, com dono e gatilho, na II.8. Nenhuma delas foi
corrigida aqui, porque nenhuma era ordem desta missao — e corrigir
achado novo sem despacho e exatamente o que este acervo chama de
progresso aparente.
## II.10 ATESTADO DA PARTE II

**Esta missao mediu um defeito de instrumento e o corrigiu; ela nao
certifica a propria correcao.** Quem disser que o
`pacote_p1a37.py:cobertura-do-diff` fechou tera de ser revisor
independente — e o proximo pacote que for a revisao ja nascera com o
manifesto que permite conferir isso **sem** confiar nesta assinatura.

**O que seria falha, e nao foi feito:** medir a suite e chamar de verde
o que esta vermelho; atribuir a esta missao as 9 falhas pre-existentes,
ou atribuir a estacao as 2 que sao regressao da ordem 6 — as duas contas
foram separadas por **medicao diferencial em clone**, nao por
julgamento; declarar a reversao vermelha sem comprovar que ela regenera
**o mesmo artefato** que os revisores leram; trocar o descarte
silencioso por um descarte **declarado** e chamar isso de correcao,
motivo pelo qual ha teste exigindo os **bytes** do `pytest.ini` e nao so
o nome dele; escrever o guarda contra a **primitiva** (`disposicao`) em
vez do **ponto de chamada** (`montar_pacote`), que e o achado `N4`;
afirmar o lab *"irrecuperavel"* sem declarar que o **VSS nao pode ser
checado** nesta sessao; e registrar o parecer do `codex` sobre a
contagem **sem** dizer que o prompt lhe entregou o numero.

**O que ficou aquem, e esta escrito:** a suite P1-A **nao esta verde** e
nao ficou verde com esta missao — 9 falhas pre-existentes continuam de
pe, e duas delas sao regressao da ordem 6 que esta missao **mediu e nao
podia corrigir**. O interpretador desta estacao **nao e o do acervo**, e
por isso nenhum numero de suite daqui deve ser comparado com os
registros anteriores sem essa ressalva ao lado. E os dois vereditos da
P1-A.6 **continuam limitados** pela falta do `pytest.ini`: esta missao
mediu o tamanho exato da falta, e **nao reabriu** nenhuma das linhas.

**Contagem como medida, nunca como meta.** Os numeros desta parte — 364
rastreados e 18 fora das quatro extensoes, **zero** deles ruido; 4
descartados na janela da P1-A.4 e **1** na da P1-A.6; 141 903 B e
`673271a7...` reproduzidos byte a byte pela reversao contra 153 603 B e
`41533c59...` do pacote corrigido; 42 de 42 caminhos cobertos; 8 passed
e 13 subtests numa polaridade contra 19 failed na outra; 28 = 19 + 9 na
suite sob mutante; 8 failed em `1f45fdd` contra 10 em `8dd1470`; 71
casamentos atribuidos 66/4/1; e os tres zeros de `oito MAJOR` (como
afirmacao), `quarto ciclo` e `P1A5-1` — sao o que foi medido, e valem
sobre o estado e a **estacao** que os produziu.

**DECISAO DAS ORDENS 1 A 5: CONCLUIDO-COM-PULADOS.**
