---
id: SSC-DEC-P1A9
titulo: Registro e Decisao da Missao SSC+ P1-A.9 — fixar o fim de linha, e as tres que sobram
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-08
---

# Registro e Decisao — Missao SSC+ P1-A.9

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Esta missao **corrige** — ao contrario da P1-A.8, que so
> classificou — e por isso **nao certifica nada do que corrigiu**:
> `QUEM CORRIGE NAO CERTIFICA`. Registro aditivo, um commit por ordem.

**PLATAFORMA DE TODA MEDICAO DESTE REGISTRO**, na forma que o
`CLAUDE.md` passa a exigir na ORDEM 5:

> **Python 3.11.9 · pytest 9.1.1 · `core.autocrlf=true` · usuario
> `lucas` · base `e769439`**

## ORDEM 1 — A DECISAO DE FIM DE LINHA

### 1.1 A medicao que decide, e ela nao foi por gosto

Dos **dois** estados de checkout limpo que existem, mediu-se quantas das
cinco receitas cada um reproduz:

| Estado | `execution.py` | `estados.py` | `eventlog.py` | Receitas divergentes | Reproduz |
|---|---|---|---|---|---|
| **CRLF** (`autocrlf=true`) | 13 778 B | 2 987 B | 6 184 B | **1** — `p22-a` | **4 de 5** |
| **LF** (`autocrlf=false`) | 13 508 B | 2 898 B | 6 184 B | **2** — `p22-c`, `p22-c-repeticao` | **3 de 5** |

> **CRLF reproduz mais: 4 de 5 contra 3 de 5. E, como a P1-A.8 ja havia
> medido, NENHUM DOS DOIS reproduz as cinco.**

**A regra fixada**, em `05_p0/ssc_p0/.gitattributes`, uma linha:

    * text eol=crlf

O diretorio e o certo porque **todos os insumos recontados hoje vivem
nele**. O limite disso esta declarado no proprio arquivo e na ORDEM 5.

### 1.2 A alternativa que reproduzia MAIS, e por que foi RECUSADA

Existe um terceiro arranjo, e ele e melhor por todo criterio ingenuo:
pinar `execution.py` em **LF** e `estados.py` em **CRLF**. Medido:

    5 receita(s); 0 divergente(s)

**As cinco conferem. E foi recusado.**

A razao nao e estetica. Esse arranjo **e exatamente a arvore mista** que
a P1-A.8 mediu e nomeou como causa — `execution.py` em LF e
`estados.py` em CRLF **ao mesmo tempo**. Ela existiu por **acidente**
numa estacao, e grava-la em `.gitattributes` a tornaria **permanente e
oficial**. Seria escolher a regra para caber no numero, quando o
despacho manda o contrario em letra:

> *"Se a escolha mudar valor publicado, o valor publicado e que estava
> errado — ele saiu de arvore que nao existe em checkout limpo."*

Ela tambem nao seria **UM estado**, que e o que a ordem pede: seria dois
estados convivendo, escolhidos arquivo a arquivo pelo numero que cada um
faz fechar.

**Fica registrada com a medicao ao lado para que o Fundador possa
discordar com a conta na mao**, e nao por falta de informacao. O preco
da recusa esta na ORDEM 2, e e um valor publicado.

### 1.3 As duas provas

**(a) Independencia de estacao — o que a regra existe para dar.** A
mesma arvore, clonada duas vezes com `core.autocrlf` oposto:

| | `autocrlf=true` | `autocrlf=false` |
|---|---|---|
| **COM a regra** | 13 778 / 2 987 / 6 184 B — **1 divergente** | 13 778 / 2 987 / 6 184 B — **1 divergente** |
| **SEM a regra** | 13 778 / 2 987 / 6 184 B — **1 divergente** | 13 508 / 2 898 / 6 184 B — **2 divergentes** |

**Com a regra, as duas colunas sao identicas — bytes e veredito.** Sem
ela, a mesma arvore devolve resultados diferentes conforme a
configuracao da maquina, que e o defeito.

**(b) Reversao vermelha.** A celula inferior-direita **e** a reversao:
removida a regra, sob `autocrlf=false`, a divergencia **volta** e passa
de 1 para 2 receitas. A mutacao viveu em **clone descartavel** — a
arvore vigiada nao foi tocada —, e por isso **nao houve registro em
`scratchpad/MUTANTE-ATIVO.txt`**, pelo mesmo criterio da P1-A.6 §6.3:
aquele registro existe para que uma retomada apos queda encontre mutante
esquecido na arvore **vigiada**, e apontar para uma arvore intacta
enganaria a sucessora.

### 1.4 A testemunha nao quebrou — conferido nas QUATRO celulas

O despacho e explicito: *"o p21 e a testemunha: blob ja CRLF, confere nos
dois. Ele nao pode quebrar."*

**`p21` CONFERE nas quatro combinacoes** de (com regra / sem regra) ×
(`autocrlf=true` / `false`), e o `eventlog.py` sai com **6 184 B** em
todas — identico ao blob.

**A regra foi escolhida para nao quebra-lo**, e isso teve consequencia
sobre o desenho: uma regra que normalizasse os blobs (`* text=auto
eol=crlf` na raiz) **renormalizaria 60 blobs**, incluindo o do proprio
`eventlog.py`. Foi medido e **recusado** por isso.

**Conferido tambem que nao ha dupla conversao:** com `* text eol=crlf` e
`autocrlf=false`, o `eventlog.py` — cujo blob **ja** carrega CRLF — sai
com **6 184 B**, e nao com 6 340. O git nao converte duas vezes, e isso
foi **medido**, nao suposto a partir da documentacao.

### 1.5 Nenhum blob mudou hoje — e a fragilidade que isso deixa, declarada

A regra **nao reescreveu blob nenhum**: so `05_p0/ssc_p0/.gitattributes`
entra no commit desta ordem. Os **9 blobs que ja estao em CRLF**
(`kernel.py`, `eventlog.py`, `contratos.py`, `frota.py`, `router.py`,
`cas.py`, `catalogo.py`, `judge.py`, `writelock.py`) continuam como
estao.

**Mas a regra fica load-bearing, e isso foi medido por acidente durante
a propria prova.** Um clone em que os blobs **haviam** sido
renormalizados (`git add` com a regra ativa baixa os 9 para LF) e do qual
a regra foi depois **removida** devolveu, sob `autocrlf=false`:

    eventlog.py 6 028 B   ->   5 receita(s); 3 divergente(s): p21, p22-c, p22-c-repeticao

**O `p21` quebrou nesse cenario.** Ele nao quebra hoje porque o blob
dele ainda e CRLF; passara a depender da regra assim que alguem
reescrever o arquivo por qualquer motivo.

**A leitura correta disso nao e "a regra e perigosa" — e "a regra passa a
ser obrigatoria".** Uma vez que os blobs normalizem, remove-la volta a
tornar os numeros dependentes de estacao, agora inclusive os do `p21`.
Fica registrado para que ninguem a remova achando que e cosmetica.

### 1.6 O que a ORDEM 1 NAO fez

- **nao alterou nenhum byte da arvore de trabalho desta estacao.** Com
  `autocrlf=true` os tres arquivos ja saiam em CRLF; a regra **fixa** o
  que ja acontecia aqui e muda o que acontecia **noutra** maquina;
- **nao renormalizou blobs**, e nao rodou `git add --renormalize`;
- **nao corrigiu o `p22-a`.** O valor publicado dele passa a divergir por
  decisao desta ordem, e o recarimbo e a ORDEM 2;
- **nao pinou nada fora de `05_p0/ssc_p0/`.**

## ORDEM 2 — RECARIMBAR AS RECEITAS

### 2.1 Uma receita mudou de valor. Uma, e so uma.

Com o fim de linha fixado, as cinco foram remedidas: **5 receitas, 0
divergentes**. O carimbo vigente, com a plataforma na mesma linha, esta
em **[`08_p2/MEDIDAS.md`](../08_p2/MEDIDAS.md)**.

| receita | razao vigente | mudou? |
|---|---|---|
| `p21` | **8,776** | nao |
| **`p22-a`** | **19,907** | **SIM** — era **19,558** |
| `p22-b` | **2,766** | nao |
| `p22-c` | **6,737** | nao |
| `p22-c-repeticao` | **6,464** | nao |

**O delta e exatamente +270 B**, que sao as **270 linhas** de
`05_p0/ssc_p0/execution.py` — um `\r` por linha, contado porque o medidor
le o disco em binario. Nao e ruido nem mudanca de formula: e o mesmo
arquivo, lido na forma que a ordem 1 fixou.

Os campos que **nao** se moveram sao a prova de que so o insumo de
arquivo mudou: `residual` **773 B**, `saida da assinatura` **547 B**,
prompt **226 B** e resposta do canal alternativo **1 384 B** — todos
identicos ao publicado.

### 2.2 O antigo nao foi apagado — foi carimbado como superado

O recarimbo foi feito **dentro do proprio arquivo publicado**, com o
valor antigo preservado campo a campo no bloco `recarimbo`:

    "valores_superados": {
      "razao_alternativo_sobre_residual": 19.558,
      "alternativo_total_bytes_utf8": 15118,
      "poupanca_bytes_utf8": 14345,
      "execution_py_bytes_utf8": 13508,
      "nota": "medidos em 2026-08-03 sob plataforma NAO declarada, com
               `execution.py` lido em LF. ..."
    }

**Por que no proprio arquivo, e nao numa copia nova — a primeira tentativa
foi a errada, e um guarda do acervo a pegou.** O desenho inicial criava
`medicao-p22-a-recarimbada-p1a9.json` e apontava a receita para ele,
deixando o datado intacto. Ao rodar a suite,
`test_toda_medicao_publicada_TEM_receita` **reprovou**: ele exige que
**toda** medicao publicada tenha receita que a produza, e o arquivo
original ficara **orfao** — publicado sem receita, que e exatamente o
**achado C** que aquele guarda existe para impedir.

O guarda estava certo e o desenho estava errado. **Fica registrado que a
correcao veio de teste vermelho, e nao de bom senso** — se a suite nao
tivesse sido rodada, o acervo teria ganhado um numero publicado sem
receita **na mesma missao que veio consertar reprodutibilidade**.

### 2.3 O que NAO foi recarimbado, e por que

| Item | Situacao |
|---|---|
| `08_p2/99_registro-p22.md`, `99_registro-p24.md` | **intocados.** Registros **datados** de missoes encerradas. Seguem citando `19,558`, que e o que se mediu naquele dia naquela arvore. O acervo carimba o superado; nao reescreve registro |
| Coluna *"razao com a MESMA resposta nos dois lados"* (`18,475`) | **NAO recarimbada, e declarado no proprio README.** Aparece **uma unica vez em todo o acervo** e **nenhum instrumento versionado a calcula** — nao ha de onde remedi-la sem refazer a analise que a produziu |
| A corrida | **nada refeito.** `sessao_id`, `attempt_id`, `executor` e as duas testemunhas seguem identicos. **Zero chamada a provedor**, custo variavel **zero** |

### 2.4 Onde o numero novo entrou

| Arquivo | O que mudou |
|---|---|
| `08_p2/evidencias/medicao-p22-a-20260803T130947Z.json` | 11 campos + bloco `recarimbo` com a plataforma, o motivo e os valores superados |
| `08_p2/README.md` | 4 trechos: a tabela, a leitura da razao, a lista de numeros e o `19,56x` -> `19,91x`. A coluna nao recarimbada ficou **marcada como tal** |
| `08_p2/MEDIDAS.md` | **novo** — o carimbo vigente das cinco, com plataforma |
| `06_p1a/tests/test_p2_receita_medidor_p24.py` | duas constantes: `19.558` -> `19.907` e o controle positivo `15119` -> `15389` |

**O controle positivo continua sendo controle.** Ele afirma *"um byte a
mais no insumo ja aparece no total"*; o que mudou foi a **base** sobre a
qual o byte e somado (15 388 + 1), nao a propriedade afirmada. Trocar a
base sem trocar a assercao e recarimbo; trocar a assercao seria afrouxar
o guarda.

### 2.5 A medicao depois da ordem 2

**Plataforma: Python 3.11.9 · pytest 9.1.1 · `core.autocrlf=true` ·
usuario `lucas`.** Suites com os arquivos staged:

| | Antes da P1-A.9 | Depois da ordem 2 |
|---|---|---|
| P0 | 344 passed, 256 subtests | **344 passed, 256 subtests** |
| P1-A | **9 failed**, 909 passed, 6 skipped, 1208 subtests | **3 failed**, **914 passed**, 6 skipped, **1209 subtests** |
| Receitas | 4 CONFERE / 1 DIVERGE | **5 CONFERE / 0 DIVERGE** |

**As seis falhas do `p24` fecharam.** As tres que sobram sao exatamente
as guardas de conteudo — ordens 3 e 4.

**Coincidencia que NAO e reproducao, e fica dita para nao virar numero
herdado:** o `914 passed` desta linha bate por acaso com o `914 passed`
que o acervo registrou em `53704b0`. **Nao sao a mesma medicao** — outro
commit, outra estacao, outro interpretador, outra versao de `pytest`, e
uma delas tem 6 skipped e 3 failed. Numero igual nao e numero
reproduzido.

## ORDEM 3 — AS DUAS GUARDAS DE CONTEUDO

### 3.1 O defeito, na frase do despacho

As duas sao **CODIGO**: montam os alvos dentro do proprio teste
(`"IA " + "Lucas"`, `"IA" + "LUCA"`) e casam regex literais. Ficaram
vermelhas em `f4399e4` e estariam vermelhas na principal — que nunca as
viu porque a ordem 6 declarou nao ter rodado a suite.

E o agravante que o despacho nomeia: **o guarda denuncia 11 ocorrencias
e conta 7 das proprias**. Instrumento que se conta a si mesmo — a
**sexta** vez que este acervo encontra o padrao.

### 3.2 A distincao que faltava, e que agora esta em codigo

Havia **duas coisas diferentes** debaixo de *"PII num arquivo"*, e a
guarda tratava as duas como uma so:

| | O que e | Politica correta |
|---|---|---|
| **Artefato gerado** que carrega PII | vazamento — pacote, evidencia, log escrito por um escritor | **REDIGIR**. Tolerancia **zero** |
| **Registro** que CITA a PII | o oposto de vazamento: e o acervo dizendo o que achou | **DECLARAR** a citacao, com motivo |

Redigir o registro destruiria a unica explicacao que o Fundador tem do
defeito — que e **a mesma razao pela qual a ordem 6 recusou redigir os
valores casados** na propria evidencia de varredura. A politica que
faltava nao era mais rigor: era **a separacao**.

O modulo novo e `06_p1a/tests/citacoes_declaradas.py`, e ele aplica a
**mesma doutrina** que a P1-A.7 pos no gerador de pacote: *exclusao so
existe se NOMEADA, com motivo*.

### 3.3 Uma ocorrencia nao foi declarada — foi REDIGIDA

Das 11, uma estava em `06_p1a/evidencias/p1a7-cobertura-pacote-….json`,
que e **artefato gerado**, e nao registro. Pela distincao da §3.2 ela
nao tinha direito a declaracao: **foi redigida** para
`<USUARIO-HISTORICO>`, com a razao no proprio campo.

**Fica registrado que a ocorrencia era minha**, escrita pela P1-A.7
ordens 1-5 ao descrever a regressao da ordem 6. A missao que denunciou o
padrao o repetiu, e a correcao dela e apagar o proprio rastro do lugar
onde ele nao devia estar — nao declara-lo.

### 3.4 As tres propriedades que impedem a declaracao de virar tapete

1. **arquivo nao declarado com uma so ocorrencia REPROVA** — o default
   continua sendo zero, e ha controle positivo para isso nas duas
   guardas;
2. **declaracao que nao casa mais REPROVA** (`declaracoes_mortas`): um
   caminho que sumiu, ou que existe e ja nao contem o token, e
   **decoracao**. E a classe dos achados 7, 10 e 14 da P1-A.3.5 — *a
   copia que ninguem exercita fica para tras*;
3. **o motivo e obrigatorio**, e vai no dicionario, nao num comentario.

**A propriedade (2) foi exercida DUAS vezes durante esta propria ordem,
e nenhuma por encomenda.** Declarei `99_decisao-p1a9.md` como autorizado
a citar, e a suite reprovou **as duas vezes**:

    99_decisao-p1a9.md: ja nao casa — declaracao decorativa

A primeira reprovacao foi porque a secao ainda nao existia. **A segunda
foi a interessante:** mesmo escrita, esta secao **nao contem o literal**
— ela explica a guarda escrevendo o alvo na forma **concatenada**,
`"IA " + "Lucas"`, que e exatamente como o proprio teste o monta para
nao casar consigo mesmo.

**A declaracao foi entao REMOVIDA**, porque era falsa. E dai sai a licao
mais util desta ordem, que vale mais que o mecanismo:

> **Documentar a guarda sem reproduzir o token e possivel — e quando e
> possivel, e melhor que declarar a citacao.**

A tecnica ja estava no acervo desde a P1-A.1, dentro do proprio teste, e
ninguem a havia aplicado aos REGISTROS. Se a ordem 6 e a P1-A.7 a
tivessem usado, **nenhuma das duas guardas teria ficado vermelha** e esta
ordem nao existiria. A declaracao continua no acervo para o caso em que
a concatenacao **nao** resolve — por exemplo, quando o valor precisa
aparecer literal para um terceiro conferir, que e o caso dos tres
artefatos de fixture.

### 3.5 O que a correcao NAO afrouxa, declarado

- **nao afrouxa a redacao de artefato gerado.** Os guardas
  comportamentais dos escritores (`test_redacao_operacao_p1a39`,
  `test_redacao_geradores_p1a39`) seguem intactos e **nao leem** o
  modulo novo. Nenhum escritor passa a poder gravar PII;
- **nao conta ocorrencias dentro de arquivo declarado.** Autoriza a
  **citacao**, nao um numero. **Um vazamento real escondido dentro de um
  registro declarado passaria** — o preco esta declarado aqui em vez de
  descoberto depois. A contencao e que a lista e **curta, nominal e so
  contem registros de decisao**: tres para PII, tres para fixture;
- **nao muda nenhum alvo.** Os literais e as sete regex continuam onde
  estavam. O que mudou foi **quem julga o achado**, nao o que a
  varredura acha;
- **nao toca a guarda da nona** — `ZeroPiiNasTresRaizes` e a ORDEM 4.

### 3.6 A medicao

**Plataforma: Python 3.11.9 · pytest 9.1.1 · `core.autocrlf=true` ·
usuario `lucas`.**

| Guarda | Antes | Depois |
|---|---|---|
| `ZeroPiiNosArtefatos` | **vermelha** — 11 ocorrencias, 7 delas do registro que a explicava | **verde**, com 3 registros declarados e 1 ocorrencia redigida |
| `ZeroSegredoNosArtefatos` | **vermelha** — 71 casamentos em 3 arquivos | **verde**, com os 3 artefatos de varredura declarados |
| Testes novos | — | **6**: dois de declaracao-morta, dois de controle positivo, e as duas assercoes principais |

## ORDEM 4 — A NONA, MISTA

### 4.1 A separacao, medida antes de corrigir

`ZeroPiiNasTresRaizes` falhava **nos dois usuarios**, por arquivos
diferentes. A P1-A.8 mediu isso por simulacao; aqui a medicao vira a
divisao do trabalho:

| Achado | E do CODIGO ou do USUARIO? | Destino nesta ordem |
|---|---|---|
| `evidencias/p1a1-estabilizacao/03_testes_p1a.txt` | **CODIGO** — casava porque a varredura usava **substring crua**, e o token curto desta estacao cai dentro de `lucasia`, o prefixo de caminho local em minuscula | **CORRIGIDO** — fronteira |
| `99_decisao-p1a7.md`, `-p1a8.md`, `-p1a9.md` | **CODIGO** — citacao forense tratada como vazamento, o mesmo defeito da ordem 3 | **CORRIGIDO** — declaracao |
| *o alvo mudar conforme quem roda* | **USUARIO** | **NAO se corrige. Fica declarado** (§4.4) |

### 4.2 A parte de codigo, frente 1 — fronteira em vez de substring

`casa_com_fronteira` exige que **nao haja letra nem digito colado** ao
token, dos dois lados. Sete casos conferidos um a um:

| Token | Texto | Casa? | Por que esta certo |
|---|---|---|---|
| curto | `…\lucasia\proj` | **nao** | o token e pedaco de outra palavra — era o falso positivo |
| curto | `C:\Users\<token>\x` | **sim** | vazamento real continua pego |
| curto | `` `<token>` `` | **sim** | citacao em cratese continua pega |
| curto | `x<token>y` | **nao** | nome diferente |
| curto | `<token>/projeto` | **sim** | e a forma do controle positivo |
| 8.3 | `` `<8.3>~1` `` | **sim** | a forma curta continua pega |
| 8.3 sem sufixo | `` `<8.3>~1` `` | **sim** | e prefixo legitimo da forma longa |

**Nao se usou `\b`**, e a razao e tecnica: `\b` depende da classe do
primeiro e do ultimo caractere do token, e estes tokens terminam em `~1`
— `\b` se comportaria de forma diferente para cada forma. A regra
explicita nao tem esse problema.

**O controle positivo nao foi afrouxado.** Ele planta `{token}/projeto`,
e a fronteira **continua detectando** — conferido: os cinco testes de
`AVarreduraDetectaOQuePlanta` seguem verdes, inclusive o que exige que
`<USUARIO>` redigido **nao** seja confundido com PII.

### 4.3 A parte de codigo, frente 2 — e a armadilha caiu sobre mim outra vez

Aplicada a declaracao, a suite reprovou **dois arquivos novos**:

    tests/citacoes_declaradas.py
    tests/test_pii_artefatos_p1a39.py

**O proprio conserto citava o token** — as docstrings que explicavam a
fronteira escreviam o nome isolado para dar o exemplo. **Setima
ocorrencia do padrao**, e desta vez dentro do codigo que existe para
resolve-lo.

**Nao foi declarada: foi reescrita.** As duas docstrings passaram a
descrever o caso **sem o token isolado** — falam do *"usuario desta
estacao"* e citam `lucasia`, que **nao casa** justamente por causa da
fronteira nova. A licao da ordem 3 aplicada a si mesma, e a prova de que
ela funciona: **o texto explica a guarda, e a guarda o aprova**.

### 4.4 A parte de USUARIO — declarada, e exercida para nao ser esquecida

> **Nome de usuario nao e plataforma de medicao.**

O guarda deriva o alvo de `contencao._USUARIO_LOCAL` **de proposito** —
foi a correcao da P1-A.3.9 contra o alvo literal, que ficava cego noutra
maquina. A consequencia e inevitavel e **nao se conserta**: o mesmo
commit devolve **conjuntos de achados diferentes** conforme quem roda.

Isso **nao e defeito**: e o preco de um guarda que acompanha a estacao.
O que esta ordem acrescenta e `test_o_resultado_depende_do_usuario_da_estacao`,
que **exerce** a dependencia — troca o usuario e exige que o alvo mude.
A dependencia deixa de ser folclore e passa a ser propriedade medida.

**Corolario que a ORDEM 5 grava no `CLAUDE.md`:** o usuario entra na
declaracao de plataforma de toda medicao, ao lado de interpretador,
`pytest` e `autocrlf`.

### 4.5 A medicao — a suite fechou

**Plataforma: Python 3.11.9 · pytest 9.1.1 · `core.autocrlf=true` ·
usuario `<o desta estacao>`.**

| Suite | Abertura da P1-A.9 | Depois da ordem 4 |
|---|---|---|
| **P0** | 344 passed, 256 subtests | **344 passed, 256 subtests** |
| **P1-A** | **9 failed**, 909 passed, 6 skipped, 1208 subtests | **0 failed**, **921 passed**, 6 skipped, **1210 subtests** |

**As nove fecharam: seis na ordem 2, duas na ordem 3, uma aqui.**

**O que isso NAO significa**, e a ressalva vale mais que o numero: suite
verde **nao** e acervo certificado. Nenhum MAJOR foi tocado, os nove
seguem abertos, e `QUEM CORRIGE NAO CERTIFICA` vale inteiro — quem
consertou as nove foi quem as mediu.
