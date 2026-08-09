---
id: SSC-DEC-P1A8
titulo: Registro e Decisao da Missao SSC+ P1-A.8 — as nove falhas sao do ambiente ou do codigo?
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-08
---

# Registro e Decisao — Missao SSC+ P1-A.8

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Esta missao **classifica** e **nao corrige**: nenhuma das
> nove falhas foi consertada, e nenhum MAJOR foi tocado. Registro
> aditivo, uma secao por ordem.

## A RESPOSTA CURTA, antes das contas

**As nove NAO sao do ambiente.** A hipotese que abriu a missao — *"se as
nove forem de ambiente, o SSC+ so se mede na principal"* — foi medida e
**nao se sustenta**. O resultado e o outro ramo que o despacho previu:

> **A maquina principal e que estava mascarando.**

Duas coisas foram provadas, e nenhuma delas depende desta estacao:

1. **As duas guardas de conteudo** (`ZeroPiiNosArtefatos`,
   `ZeroSegredoNosArtefatos`) casam **literais escritos no proprio
   teste** e **regex literais** — nao leem a estacao. Elas ficaram
   vermelhas quando a **ordem 6 commitou tres arquivos**, e estariam
   vermelhas na principal **no mesmo instante**. A principal nunca as
   viu porque a ordem 6 **declarou que nao rodou a suite**.
2. **As seis do `test_p2_receita_medidor_p24`** falham nos **DOIS**
   estados de checkout limpo que existem. Isso nao e diferenca entre
   estacoes: e **numero publicado a partir de arvore MISTA**, que
   **nenhum checkout limpo reproduz** — nem aqui, nem la.

## ORDEM 1 — AS NOVE, CLASSIFICADAS

Legenda: **AMBIENTE** = versao de Python, dependencia ausente, caminho de
usuario, fim de linha, ou qualquer coisa que a principal nao teria.
**CODIGO** = falharia em qualquer lugar.

| # | Falha | Classe | Como se mediu |
|---|---|---|---|
| **1** | `test_estabilizacao_p1a1.py::ZeroPiiNosArtefatos` | **CODIGO** | os alvos sao **literais no proprio teste** (`"IA " + "Lucas"`, `"IA" + "LUCA"`), sem uma linha que leia a estacao |
| **2** | `test_isolamento.py::ZeroSegredoNosArtefatos` | **CODIGO** | **71** casamentos de **regex literal** (`sk-`, `xai-`, `AIza`, `AKIA`, atribuicao), atribuidos **66/4/1** aos tres arquivos da ordem 6 |
| **3** | `p24::OComandoExiste::test_uma_receita_por_id` | **CODIGO** | ver §1.2 — exaustao dos dois checkouts limpos |
| **4** | `p24::OComandoExiste::test_todas_as_receitas_reproduzem…` | **CODIGO** | idem |
| **5** | `p24::OComandoExiste::test_json_da_corrida_pode_ser_gravado…` | **CODIGO** | idem |
| **6** | `p24::ReproduzOsNumerosPublicados::test_as_razoes_publicadas…` | **CODIGO** | idem |
| **7** | `p24::ReproduzOsNumerosPublicados::test_toda_receita_confere…` (subtest) | **CODIGO** | idem |
| **8** | `p24::ControlePositivo::test_UM_byte_a_mais_no_turno_interno…` | **CODIGO** | idem |
| **9** | `test_pii_artefatos_p1a39.py::ZeroPiiNasTresRaizes` (subtest `06_p1a`) | **MISTA** — metade AMBIENTE, metade CODIGO | simulacao do usuario nos dois valores; **falha nos dois**, por **arquivos diferentes** (§1.3) |

**Zero falhas na classe NAO DETERMINADO.** Cada uma tem causa medida.

### 1.1 As duas guardas de conteudo — por que sao CODIGO e nao estacao

`ZeroPiiNosArtefatos` **nao pergunta o nome do usuario a ninguem**. O
corpo do teste monta os alvos por concatenacao, para o proprio arquivo
nao casar consigo mesmo:

    usuario = "IA " + "Lucas"
    usuario_curto = "IA" + "LUCA"

Um literal nao muda de estacao. A varredura acha, **em qualquer
maquina**:

| Casamentos de `IA Lucas` | Arquivo | Quem escreveu |
|---|---|---|
| **3** | `06_p1a/99_decisao-p1a7.md` | 2 da **ordem 6** (§6.2, ao transcrever o blob orfao) + **1 da P1-A.7 ordens 1-5** |
| **1** | `06_p1a/evidencias/p1a7-cobertura-pacote-…json` | **P1-A.7 ordens 1-5** |

**Registro contra mim mesmo:** das quatro ocorrencias, **duas nasceram
na P1-A.7 ordens 1-5** — a missao que documentou a regressao da ordem 6
**repetiu a armadilha da ordem 6**, escrevendo o nome literal ao
descreve-lo. O mecanismo e o mesmo que a P1-A.7 §II.1.1 apontou no
antecessor, e ele nao poupa quem o denuncia.

`ZeroSegredoNosArtefatos` e o mesmo caso por outro eixo: as cinco regras
sao expressoes literais e **nenhuma consulta a estacao**. Remedido
agora: **71**, atribuidos **66** a `p1a7-varredura-segredo-…json`, **4**
a `99_decisao-p1a7.md`, **1** a `varredura_segredo_p1a7.py` — os
**mesmos tres arquivos** da ordem 6, e **zero** acrescimo da P1-A.7
ordens 1-5 nesta guarda.

**Nenhum dos 71 e credencial, e nenhuma das 4 e vazamento novo.** O
defeito nao e vazamento: e **guarda versionada vermelha**, e ela ficaria
vermelha na principal exatamente no commit `f4399e4`.

### 1.2 As seis do `p24` — provadas por EXAUSTAO, e o resultado surpreende

A suspeita inicial era fim de linha, e ela **estava certa pela metade**.
A medicao foi feita nos **dois** estados de checkout limpo que existem,
cada um num clone independente:

| Checkout | Como se obteve | Receitas divergentes |
|---|---|---|
| **CRLF** (`core.autocrlf=true`, o desta estacao) | arvore de trabalho vigente | **1** — `p22-a` |
| **LF** (`core.autocrlf=false`) | `git clone` com a opcao, `checkout -f` | **2** — `p22-c` e `p22-c-repeticao` |

A aritmetica fecha **exatamente**, e e ela que prova o mecanismo:

| Arquivo recontado | Blob | Disco CRLF | Delta | Linhas |
|---|---|---|---|---|
| `05_p0/ssc_p0/execution.py` (usado por `p22-a`) | 13 508 B, **CR=0** | 13 778 B | **+270** | **270** |
| `05_p0/ssc_p0/estados.py` (usado por `p22-c` e `-repeticao`) | 2 898 B, **CR=0** | 2 987 B | **+89** | **89** |
| `05_p0/ssc_p0/eventlog.py` (usado por `p21`) | 6 184 B, **CR=156** | 6 184 B | **0** | 156 |

Um byte por linha, e o `medidor.item_de_arquivo` le **em binario**
(`open(caminho, "rb")`) — logo conta o `\r`.

**E aqui esta o achado.** Os numeros publicados de `p22-a` **exigem
leitura LF**; os de `p22-c` e `p22-c-repeticao` **exigem leitura CRLF**:

| Receita | Publicado | Recalculado em CRLF | Recalculado em LF |
|---|---|---|---|
| `p22-a` | razao **19.558** | 19.907 ✗ | **19.558** ✓ |
| `p22-c` | razao **6.737** | **6.737** ✓ | 6.603 ✗ |
| `p22-c-repeticao` | razao **6.464** | **6.464** ✓ | 6.335 ✗ |

Os **dois** arquivos sao **LF puro no blob** (`CR=0`) e **nenhum** tem
regra em `.gitattributes` (`git check-attr text` devolve `unspecified`
para os dois). Portanto um checkout limpo os entrega **os dois em LF**
ou **os dois em CRLF** — nunca um de cada.

> **Conclusao, por exaustao dos dois unicos estados limpos possiveis:
> nenhum checkout limpo reproduz as cinco receitas. Os numeros
> publicados da P2 sairam de uma arvore de trabalho MISTA, e nao sao
> reproduziveis em estacao nenhuma — nem nesta, nem na principal.**

Isso **nao e ambiente**. Ambiente seria *"aqui falha, la passa"*. O que
se mediu e *"falha nos dois estados possiveis, e o estado que o
produziu nao e um estado limpo"*.

**O `p21` e a testemunha que fecha o argumento:** o blob dele **ja
carrega CRLF** (`CR=156`), entao disco e blob coincidem em qualquer
`autocrlf`, e ele **confere nos dois checkouts**. Quando o byte nao
depende do checkout, o numero reproduz. E exatamente a propriedade que
faltou aos outros dois.

**Consequencia para o acervo, declarada e nao suavizada:** isto e
evidencia dura para o MAJOR **`P1A4-4`** — *"a receita recompoe numeros
com insumos testemunhais; nao permite recontar"*. A missao **nao o
fecha nem o move**: so mostra que o defeito e maior do que o enunciado
dizia. Nao e apenas que parte dos insumos e testemunho; e que **a parte
recontavel tambem nao reconta**, porque o numero publicado depende de um
estado de arvore que ninguem registrou.

### 1.3 A nona — a unica com metade de ambiente

`ZeroPiiNasTresRaizes` **deriva o alvo da estacao** de proposito
(`contencao._USUARIO_LOCAL`, que e `os.path.basename(os.path.expanduser("~"))`).
Foi medida **simulando os dois usuarios**, com a mesma funcao real de
varredura:

| Usuario simulado | Alvos | Achados | Onde |
|---|---|---|---|
| `lucas` (esta estacao) | `lucas`, `LUCAS~1`, `LUCAS` | **2** | `99_decisao-p1a7.md` (**7** ocorrencias de `lucas`, todas da P1-A.7 ordens 1-5) e `p1a1-estabilizacao/03_testes_p1a.txt` (**1**, dentro de `e:\lucasia\…`) |
| `IA Lucas` (principal) | `IA Lucas`, `IALUCA~1`, `IALUCA` | **2** | `99_decisao-p1a7.md` e `p1a7-cobertura-pacote-…json` |

**Falha nas duas estacoes, por arquivos diferentes** — por isso a classe
e **MISTA**, e nao AMBIENTE:

- **a metade AMBIENTE**: o casamento em `03_testes_p1a.txt` existe
  **so aqui**, porque o token desta estacao (`lucas`) e curto e cai
  **dentro** de `lucasia` — que e o prefixo de caminho local
  `E:\LucasIA` em minuscula. Na principal, `IA Lucas` nao casa ali;
- **a metade CODIGO**: o casamento em `99_decisao-p1a7.md` existe nas
  **duas**, e o do JSON de evidencia tambem.

O guarda **afirma** *"zero PII"* e o que ele **exerce** e *"zero
ocorrencias da substring"* — o achado `P1A7-b` da missao anterior,
agora com a medicao dos dois lados. **Continua aberto e nao foi
corrigido aqui.**

### 1.4 Os seis `skipped` — todos de ambiente, e nenhum silencioso

| Quantos | Motivo declarado pelo proprio skip |
|---|---|
| **3** | CLI do `codex` ausente nesta estacao |
| **2** | `~/.gemini/settings.json` ausente |
| **1** | **lab da corrida `c-repeticao` ausente** — o lab que a P1-A.6 destruiu |

Os seis sao **AMBIENTE**, e nenhum e disfarce: cada `skipReason` diz, em
letra, *"o skip existe para dizer isso alto, nunca para dar a suite por
verde"*. O sexto e o unico irreversivel — e o dano da P1-A.6, que a
P1-A.7 procurou em cinco lugares e nao achou.

### 1.5 A ARMADILHA ESTRUTURAL — este registro tambem cai nela

**Medido antes de escrever, e declarado antes de commitar.** As contagens
acima foram conferidas contra o commit `8dd1470`, que continha **so** a
ordem 6:

| Arquivo | `IA Lucas` | `lucas` | Quem acrescentou |
|---|---|---|---|
| `99_decisao-p1a7.md` em `8dd1470` | **2** | **0** | ordem 6 |
| `99_decisao-p1a7.md` hoje | **3** | **7** | P1-A.7 ordens 1-5: **+1** e **+7** |
| **`99_decisao-p1a8.md` — ESTE arquivo** | **4** | **6** | **P1-A.8**, e mais **2** de `IALUCA` |

**Este registro, ao explicar por que a guarda esta vermelha, fica
vermelho pela mesma razao que explica.** Nao ha redacao que escape: a
guarda procura a **substring literal**, e um documento que nomeie o
token contem o token. A ordem 6 caiu nisso; a P1-A.7 caiu ao descrever a
queda da ordem 6; esta missao cai ao descrever as duas.

**Isso nao e descuido acumulado — e propriedade do guarda**, e vale
registrar na forma geral:

> **Uma guarda que varre a arvore inteira por substring literal torna o
> acervo incapaz de documentar a propria guarda.** Todo registro que a
> discuta e, por construcao, uma violacao dela.

**O que esta missao NAO faz com isso:** nao corrige, nao redige o token,
nao acrescenta excecao. Redigir o token destruiria a legibilidade do
registro — que e a mesma razao pela qual a ordem 6 recusou redigir os
valores casados na propria evidencia (§12 da Parte I da P1-A.7), e a
razao continua valendo. **Fica como achado, na ORDEM 4**, com o remedio
que o dono pode escolher.

### 1.6 O que a ORDEM 1 NAO mediu

- **nao se rodou a suite na maquina principal.** As conclusoes sobre ela
  sao **deducoes de mecanismo** — literal nao muda de estacao; blob LF
  sem `.gitattributes` so tem dois checkouts limpos —, **nao** medicao
  remota. Onde a deducao e o que sustenta, esta dito;
- **nao se corrigiu nenhuma das nove**, por ordem expressa;
- **nao se afirma que a principal esteja vermelha hoje**: afirma-se que
  **ficaria** vermelha ao rodar a suite sobre este commit, e que a
  ordem 6 declarou nao te-la rodado.
