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
