---
id: SSC-REG-P22-99
titulo: Registro da missao SSC+ P2.2 — onde a tese vale, e onde nao
tipo: registro-experimental (NAO e atestado)
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Registro — Missao SSC+ P2.2

> Laboratorio experimental. Registro **aditivo**: nenhum documento
> anterior foi aberto para escrita. Os registros da P2.0 e da P2.1
> permanecem intactos e continuam verdadeiros sobre as corridas que os
> produziram.
>
> **Este documento NAO e atestado de aprovacao.** Quem construiu nao
> certifica, e quem corrige nao fecha o proprio conserto.

## 0. Medicao de partida e de fechamento

| Item | Abertura | Fechamento |
|---|---|---|
| HEAD | `372d701` | este commit |
| `git status --porcelain` | vazio | vazio |
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** (lido antes de qualquer medicao) | ausente (apagado apos reverter os 4 mutantes) |
| Suite `05_p0/tests` | **344/344 OK** | **344/344 OK** |
| Suite `06_p1a/tests` | **831/831 OK** | **838/838 OK** (831 + 7) |
| Escritor unico | `p22-ops`, fence **1**, pid 39588 | mesmo lease, mesmo fence |
| Declaracao de tier | valida ate 2026-08-04T01:52:54Z, **nao renovada** | idem |
| Chamadas de modelo na historia do laboratorio | **5** | **9** (4 nesta missao) |

As duas suites continuam medidas **em separado**, pela colisao de
`apoio.py` descrita no §0 do registro da P2.1.

## 1. A premissa do despacho estava errada, e isso e medicao

O despacho desta missao dizia: *"Declaracao de tier vence
2026-08-04T01:52:54Z — vencida, BLOCKED."*

Medido as **2026-08-03T13:02:13Z**, a declaracao tinha ~12 h 50 min de
validade restante. Nao e leitura de calendario: o **preflight** corrido as
13:06:05Z devolveu `codex` e `kimi` em **SHADOW_ELIGIBLE**
(`07_p1b/evidencias/preflight-20260803T130605Z.json`). Vencida a
declaracao, o mecanismo devolveria `P1A-DECLARACAO-EXPIRADA` e a frota
voltaria a BLOCKED sozinha — e a missao teria parado ali.

A missao correu com a declaracao **existente** e **nada foi renovado**,
como a restricao mandava. A premissa e apontada aqui porque uma missao que
tivesse aceito o BLOCKED declarado teria parado sem medir, e o motivo da
parada seria uma suposicao — exatamente o que este acervo nao aceita.

## 2. O desenho: tres prompts que diferem em UMA coisa

A ORDEM 1 pedia tres classes. O que separa esta medicao de repetir o
numero bom e que os tres prompts tem **forma identica** — mesmo pedido de
saida (`no maximo 8 linhas`, duas perguntas, a segunda pedindo o que o
objeto **nao** impede) — e diferem **somente** no turno interno exigido:

| classe | prompt | turno interno |
|---|---|---|
| (a) | ler `05_p0/ssc_p0/execution.py` e responder | **13.508 B** |
| (c) | ler `05_p0/ssc_p0/estados.py` e responder | **2.987 B** |
| (b) | responder **sem consultar arquivo nenhum** | **0 B** |

Os prompts sairam com 226, 224 e 213 B — a diferenca e o nome do arquivo.
Cada um foi despachado byte a byte identico nos dois canais; do lado
alternativo a tarefa foi **feita de verdade**, com a leitura do arquivo
real medida por `item_de_arquivo` e a resposta medida como texto.

Nenhuma media entre classes, como a ordem mandava.

## 3. Os tres numeros de cada classe

Quatro corridas novas; a quinta linha e a corrida da P2.1, na tabela
porque e da mesma classe (a) e e o que mostra a razao se mover.

| corrida | turno interno | assinatura | alternativo | **residual do despachante** | poupanca | razao |
|---|---|---|---|---|---|---|
| (a) P2.2 | `execution.py` 13.508 B | 773 | 15.118 | **773** | 14.345 | **19,558** |
| (a) P2.1 | `eventlog.py` 6.184 B | 872 | 7.653 | **872** | 6.781 | **8,776** |
| (c) P2.2 #1 | `estados.py` 2.987 B | 662 | 4.460 | **662** | 3.798 | **6,737** |
| (c) P2.2 #2 | `estados.py` 2.987 B | 690 | 4.460 | **690** | 3.770 | **6,464** |
| (b) P2.2 | nenhum | 504 | 1.394 | **504** | 890 | **2,766** |

Todos em bytes utf-8. As duas unidades e os oito — hoje nove — limites
viajam dentro de cada `08_p2/evidencias/medicao-p22-*.json`.

### 3.1 A identidade que separa economia de ilusao

A poupanca **decompoe**, e a decomposicao fecha nas cinco corridas:

    poupanca = turno_interno + (resposta_do_alternativo - resposta_da_assinatura)

O segundo termo saiu **597, 783, 811, 837 e 890 B** — praticamente
constante e **indiferente a classe**. Ele nao vem de despachar: vem de um
canal responder mais curto que o outro. Nas tres corridas da P2.2 o codex
usou **3 ou 4** das 8 linhas permitidas; o canal alternativo usou **8**.

Qual das duas respostas presta, a proxy **nao diz** — o limite
`qualidade-nao-e-medida` ja estava declarado desde a P2.1, e agora tem
consequencia numerica.

### 3.2 A razao e propriedade do ARQUIVO, nao da classe

`8,776` e `19,558` sao a **mesma classe de tarefa** com arquivos de 6.184
e 13.508 B. Repetir "8,78x" e repetir a escolha do arquivo. Foi por isso
que a ordem mandou medir a fronteira em vez do numero bom, e a medicao
confirma o motivo da ordem.

## 4. A FRONTEIRA, declarada (ORDEM 2)

Escrita no `README.md` da P2 numa secao **acima** dos tres limites da P2.1
e **acima** dos comandos, porque quem chega pelo passo-a-passo pode nunca
rolar ate o fim.

**Poupa** quando o turno interno e grande diante do termo de ~800 B: na
corrida (a) o turno interno foi **94%** da poupanca.

**Nao poupa** em pergunta autocontida. Medindo com a **mesma resposta nos
dois lados**, a razao da classe (b) e **1,000 exatos**: poupanca
estrutural **zero**. Os `2,766` que o instrumento anuncia sao,
integralmente, os 890 B de verbosidade — **890 de 890**.

**Custa mais** quando a assinatura responde mais longo que o alternativo
responderia (o instrumento diz `MAIS`, e tem teste desde a P2.1). E custa
**uma tentativa perdida** pedir capacidade que puxa o kimi enquanto a
franquia dele estiver esgotada — tentativa que fica com a **assinatura**,
nao com o despachante, e que por isso **nao aparece** na proxy de
fronteira de quem despacha. A proxy mede a fronteira do despachante,
jamais a queima total da frota.

## 5. Achados desta missao

### 5.1 O nono limite faltava, e dominava a classe que ninguem havia corrido — familia (F)

`NAO_CAPTURA` tinha oito membros, cada um com o `porque`, e um guarda que
compara a lista com uma copia **escrita a mao** no teste — desenho correto,
e a P2.1 mediu 8/8 prendendo. O que nenhum dos dois lados podia ver e que
**faltava um membro**: a diferenca de verbosidade entre os canais entra na
poupanca e nao vem de despachar.

E familia **(F)** porque o objeto e uma **lista que afirma** a propria
completude: a saida de `comparar` declara os limites da proxy, e nada
exercia a classe de tarefa em que o limite ausente era 100% do numero. A
P2.1 correu duas tarefas, as duas com turno interno pesado, onde esse termo
era ~6% e passava por ruido.

Remedio: nono membro, com os cinco valores medidos escritos no `porque`; e
**dois guardas novos** que exercem a fronteira em vez de afirma-la —
`test_sem_turno_interno_e_resposta_IGUAL_a_poupanca_e_ZERO` (poupanca 0,
razao 1,0, veredito de empate) e
`test_a_poupanca_decompoe_em_turno_interno_MAIS_verbosidade`.

Reversao vermelha:

    M3 nono limite removido de NAO_CAPTURA .................. 1 vermelho
    M4 residual sem a leitura de volta (despacho gratuito) .. 3 vermelhos

O segundo guarda existe por causa da ORDEM 2: a frase da fronteira ia para
o README, e frase no README sem guarda que a exerca **e** a familia (F).

### 5.2 A docstring afirmava o contrario do que a classe (b) mede — familia (F)

`medir_alternativo` dizia, por escrito: *"Razonete sem nenhum deles nao
prova ausencia de economia, so nao a mediu."*

A classe (b) e o contraexemplo medido. Quando a tarefa **nao tem** turno
interno, a ausencia e o fato da tarefa, e a poupanca estrutural e zero — e
o aviso `sem-turno-interno-declarado` **nao distingue** os dois casos
(razonete que omitiu, tarefa que nao tem). Familia (F): a docstring afirma
uma propriedade que a interface real nao sustenta.

Remedio: a docstring passa a declarar que o aviso nao distingue os dois
casos, e que quem o le tem de dizer qual e. Sem mudanca de comportamento.

### 5.3 O relato do runner matava a corrida antes de persistir a evidencia — fora de ambas as familias

Na corrida da classe (c) o attempt saiu **sucesso** e o runner morreu:

    UnicodeEncodeError: 'charmap' codec can't encode character '→'
    runner_p2.py:302, em print(registro["saida"])

A persistencia da evidencia esta nas linhas **307-328**, depois do print. A
franquia foi gasta, a cadeia ficou gravada no laboratorio e o artefato de
registro em `08_p2/evidencias/` **nao existiu**. Contra a condicao 5 do ato
soberano — *toda invocacao produtiva e registrada*: ficou registrada na
cadeia; o artefato de registro, nao.

A medicao da classe (c) foi **recuperada da cadeia verificada**
(`EvidencePlane` sobre o lab `20260803T133155Z`), sem re-invocar: re-rodar
teria gasto outra chamada e produzido outra resposta, e a corrida a medir
era a que ocorreu.

Classificada **fora de ambas** por definicao: o objeto — a linha que exibe
a resposta — **nao e guarda do acervo**, e a suite declarava por escrito
que `main()` nao era coberta. Nao e (F), porque uma lacuna declarada nao e
uma afirmacao; nao e (N), porque nao havia guarda cujo eixo a deixasse
passar.

Remedio, com as duas metades medidas em forcas diferentes:

    M1 primitiva crua (`_no_codec_do_console` devolve o texto) .. 3 vermelhos
    M2 ponto de chamada cru, primitiva INTACTA ................... 1 vermelho

**Sob M2 os quatro testes da primitiva ficaram verdes.** E a licao **N4**
da P1-A.3.7 — *primitiva corrigida nao cobre ponto de chamada* — medida de
novo, e nao citada; a P2.1 pagou a mesma licao no §5.2. Por isso ha um
quinto teste, de AST sobre `main`, que fica vermelho se o ponto de chamada
voltar ao `print` cru.

O teste exerce **o caso que ocorre**: `io.TextIOWrapper(encoding="cp1252")`
enforca o codec e levanta igual ao console real. Um `StringIO` aceitaria
qualquer `str` e ficaria **verde sob o defeito** — seria o vizinho.

**Verificado em operacao, o que nenhum teste podia dar.** Primeiro o texto
exato lido do CAS da corrida caida foi passado por `relatar` no console
real da estacao: atravessou. Depois a segunda corrida da classe (c)
trouxe `→` **de novo**, e a evidencia **foi persistida**
(`execucao-20260803T135121Z.json`).

## 6. A primeira repeticao de mesmo prompt do acervo (ORDEM 3)

A segunda corrida da classe (c) usou o **mesmo prompt**, e o lado
alternativo foi mantido identico de proposito — mesmo arquivo, mesma
resposta — para que a variacao medida fosse **so** a da assinatura:

    razao ................. 6,737 -> 6,464   (-4,1 %)
    resposta da assinatura ..  438 -> 466 B   (+6,4 %)
    poupanca .............. 3.798 -> 3.770 B  (-0,7 %)

Uma repeticao da **um delta**, jamais uma dispersao. O que ela mede e que a
razao nao e estavel na casa decimal em que foi escrita: a P2.1 registrou
`8,776`, com tres casas, sobre `n = 1`.

### 6.1 O `n` por classe, e por que nao ha `n` necessario medido

| classe | corridas | repeticoes de MESMO prompt |
|---|---|---|
| (a) turno interno pesado | 2 | **0** — arquivos diferentes |
| (b) turno interno nulo | 1 | **0** |
| (c) intermediaria | 2 | **1** |

**Nenhuma classe tem tendencia estabelecida.** Um `n` justificado sai de
uma estimativa de dispersao, e a dispersao so existe **depois** das
corridas: nenhum numero pode ser deduzido do que esta medido aqui. O que
se afirma sem extrapolar, e rotulado no README como convencao e nao como
medicao:

1. **2 corridas de mesmo prompt por classe** — minimo para existir
   qualquer delta; hoje so a classe (c) tem;
2. **5 por classe** — menor `n` em que existe mediana que um unico outlier
   nao move. Propriedade aritmetica da mediana, **nao** medicao deste
   acervo;
3. **intervalo de confianca segue fora de alcance** ate haver variancia
   estimada, e estima-la exige as corridas: a ordem nao se inverte.

E uma observacao de desenho para quem vier: como a razao acompanha o
tamanho do turno interno, **varrer tamanhos** mede a fronteira, enquanto
repetir o mesmo arquivo mede o ruido da resposta.

## 7. O que esta missao NAO estabelece

1. **nao estabelece a tese.** A economia de **token** segue nao medida.
   Tudo aqui e proxy de bytes, e a proxy declara nove coisas que nao
   captura — entre elas raciocinio, contexto reenviado e cache, que e onde
   a economia de verdade mora;
2. **nao estabelece tendencia em nenhuma classe.** Ver §6;
3. **nao estabelece qualidade.** Nenhum juiz-llm foi acionado. O codex usou
   3-4 das 8 linhas permitidas e o canal alternativo usou 8; a proxy conta
   a diferenca como poupanca e **nao** diz qual resposta presta;
4. **nao estabelece que o razonete do canal alternativo seja completo.**
   Esse canal nao grava cadeia. A omissao conhecida — enquadramento da
   ferramenta de leitura — **subestima** o alternativo, entao empurra o
   resultado para "nao houve economia", e e conservadora;
5. **nao estabelece nada novo sobre o kimi.** Nenhuma corrida desta missao
   pediu `--capacidade volume`; a franquia esgotada e medicao **herdada**
   da P2.1, nao remedida aqui. `kimi -p` continua sem caminho de sucesso
   validado;
6. **nao estabelece que a ordem entre relatar e persistir esteja segura.**
   O relato deixou de poder derrubar a corrida por codificacao; nada prova
   que a evidencia seja gravada se outra coisa levantar antes da
   persistencia. Exercitar isso exige `main` com lease vivo e invocacao
   real, e mudanca de producao sem prova e o que este acervo passou tres
   missoes pagando;
7. **nao estabelece que os demais guardas do acervo estejam inteiros.** A
   pergunta que a P2.1 deixou aberta continua aberta;
8. **nao estabelece que os labs medidos sejam reauditaveis por terceiros.**
   `08_p2/saidas/labs/` fica fora do Git e foi limpo antes de cada corrida,
   como a ordem mandava. As copias vivem fora do repositorio, nesta sessao;
   o que um revisor independente tera sao os `medicao-p22-*.json`, que
   carregam os numeros mas nao a cadeia que os produziu.

## 8. Criterio de parada da trilha de correcao

Classificacao obrigatoria pelo `CLAUDE.md` da raiz — sem ela o criterio
(b) nao pode ser aferido.

| familia | quantos | quais |
|---|---|---|
| **(F)** afirma em vez de exercer | **2** | 5.1 (lista de limites sem o membro que dominava a classe nao corrida), 5.2 (docstring contradita pela classe (b)) |
| **(N)** classe que a varredura nao media | **0** | — |
| fora de ambas | **1** | 5.3 (o relato do runner nao e guarda do acervo, e a lacuna estava declarada) |

**Total de achados novos: 3. Nenhum criterio de parada foi disparado**
— (a) exige 6+, (b) exige 4+ em (F).

**Esta missao nao e revisao independente**, e o criterio fala da proxima
revisao independente. Ainda assim, um numero que o Fundador deveria ver:
as duas missoes que **construiram** a P2 acharam, sozinhas, **quatro
achados de familia (F)** — dois na P2.1 (§8) e dois aqui. Se uma revisao
independente devolvesse essa mesma contagem, o criterio (b) estaria
**exatamente no limiar**. Nao e o disparo do criterio; e a medida de quanto
a familia (F) continua produzindo neste acervo mesmo depois de tres ciclos
com saldo zero nos MAJOR originais.

O aviso proprio desta missao, mais estreito e mais duro que a contagem:
**os dois achados (F) sao do instrumento que a missao anterior construiu
para medir com honestidade**, e nenhum dos dois apareceu por releitura.
Apareceram por **correr uma classe de tarefa que a missao anterior nao
correu**. A pergunta que a proxima revisao deste acervo deveria fazer por
padrao ganha uma terceira forma, ao lado das duas que a P2.1 deixou:

1. o remedio protege o **valor**, ou so o caminho? (P2.1 §5.1)
2. o remedio cobre o **ponto de chamada**, ou so a primitiva? (P2.1 §5.2)
3. a declaracao de limites foi exercida na classe de entrada em que o
   limite **domina**, ou so onde ele passa por ruido? (P2.2 §5.1)

## 9. Quem constroi nao certifica

Esta sessao mediu as quatro corridas, achou os tres defeitos, corrigiu
dois deles com reversao vermelha medida, escreveu a fronteira no README e
escreveu este registro. Ela **nao emite atestado de aprovacao** e nao fecha
nenhum achado por conta propria. A verificacao independente da P2.0, da
P2.1 e da P2.2 segue **pendente**.
