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
