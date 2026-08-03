---
id: SSC-REG-P21-99
titulo: Registro da missao SSC+ P2.1 — medir a tese
tipo: registro-experimental (NAO e atestado)
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Registro — Missao SSC+ P2.1

> Laboratorio experimental. Registro **aditivo**: nenhum documento
> anterior foi aberto para escrita. O registro da P2.0 permanece intacto
> e continua verdadeiro sobre as corridas que o produziram.
>
> **Este documento NAO e atestado de aprovacao.** Quem construiu nao
> certifica.

## 0. Medicao de partida e de fechamento

| Item | Abertura | Fechamento |
|---|---|---|
| HEAD | `7033d36` | este commit |
| `git status --porcelain` | vazio | vazio |
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** (lido antes de qualquer medicao) | ausente |
| Suite `05_p0/tests` | **344/344 OK** | **344/344 OK** |
| Suite `06_p1a/tests` | **799/799 OK** | **831/831 OK** (799 + 32) |
| Escritor unico | `p21-ops`, fence **1**, pid 2260 | mesmo lease, mesmo fence |
| Declaracao de tier | valida ate 2026-08-04T01:52:54Z | idem, **nao renovada** |
| Chamadas de modelo na historia do laboratorio | **3** | **5** (2 nesta missao) |

As duas suites sao medidas **em separado**. Rodadas juntas, a coleta
quebra com 21 erros: ha um `apoio.py` em cada diretorio de testes e o
pytest colide os nomes. Nao e defeito desta missao; fica escrito porque
a medicao conjunta pareceria uma regressao a quem a tentasse.

## 1. O problema, e o que ele tinha de diferente

A P2.0 fechou dizendo, no §6.4, que a economia de token era
**inferencia, nao medicao**. Essa e a tese central do projeto — despachar
para a assinatura poupa token de outro canal — e ela estava, ate aqui,
declarada e nunca aferida.

O obstaculo e concreto: **nenhum dos dois CLIs reporta contagem de
token**. Nao ha numero para ler. Uma missao de medicao que comecasse
inventando o numero teria produzido exatamente o defeito que este acervo
passou tres missoes caçando.

## 2. Quatro ordens, cinco commits

| # | Ordem | O que entregou |
|---|---|---|
| 1 | construir a medicao | `08_p2/medidor.py` + 29 testes; proxy declarada com os proprios limites embutidos |
| 2 | corrida comparada | uma tarefa real despachada duas vezes; os dois numeros |
| 3 | os tres defeitos | reversao vermelha dos tres; **dois buracos achados e fechados** (2 commits) |
| 4 | registrar o limite | os tres limites no TOPO do README da P2, com data e evidencia |

## 3. O instrumento: a proxy de CARGA DE FRONTEIRA

Sem contador, resta proxy. A definida e implementada conta o que
**atravessa a fronteira** de um canal, nos dois sentidos, em duas
unidades (`bytes_utf8` e `caracteres` — duas, porque escolher uma
sozinha esconderia a escolha).

**Tres numeros, nunca dois.** O terceiro e o que quase todo argumento de
economia omite:

| numero | o que e |
|---|---|
| `assinatura` | tudo que atravessou a fronteira do CLI, somando **TODAS** as tentativas |
| `alternativo` | o que o outro canal ingeriria e emitiria fazendo a MESMA tarefa |
| `residual_do_despachante` | o que o outro canal **continua pagando** ao despachar: redige o prompt, le a resposta |

    poupanca = alternativo - residual_do_despachante

Tratar despacho como gratuito faria a tese fechar **por construcao** — e
seria o guarda que afirma em vez de exercer. O instrumento tem teste que
prende o outro lado: quando o despacho custa mais, ele DIZ que custou
mais (`test_despacho_mais_caro_sai_como_MAIS_e_nao_como_economia`).

Do lado da assinatura os numeros saem da **cadeia verificada** (EventLog
+ CAS via `EvidencePlane`), nunca da memoria do processo que executou.

### 3.1 O que a proxy NAO captura — e por que viaja embutido

Oito limites, cada um com o `porque` por escrito, **dentro** de toda
saida de `comparar`. Nao e paragrafo de README que alguem esquece de
ler: quem quiser citar a economia carrega junto o que ela nao mede.

Os dois mais importantes: **byte nao e token** (tokenizador nao e linear
em byte, e os dois canais nem usam o mesmo) e **raciocinio nao e
emitido** — o token de raciocinio e cobrado e nunca cruza a fronteira, e
e justamente onde a economia deveria estar.

**Reversao vermelha da lista, membro a membro** (corolario do
`CLAUDE.md`: remover so o ultimo prova que AQUELE nao prende, jamais que
a lista esta solta): **8/8 prendem, 1 vermelho cada => PRESA**. A lista
esperada esta escrita A MAO no teste; compara-la com `NAO_CAPTURA`
importada seria tautologia.

Mutacoes de logica: residual contando todas as tentativas -> 1 vermelho;
entrada contada uma vez so -> 1; saida de tentativa falhada ignorada -> 3.

## 4. Os dois numeros da corrida comparada

Tarefa: ler `05_p0/ssc_p0/eventlog.py` e responder em ate 8 linhas como
a cadeia encadeia cada evento e o que a verificacao recusa. Prompt
identico nos dois lados, byte a byte. O arquivo foi escolhido por ser um
que o canal alternativo **ainda nao tinha lido** — medir com o arquivo ja
em contexto seria razonete desonesto.

| | bytes utf-8 |
|---|---|
| assinatura absorveu | **872** (233 entrada + 639 saida, 1 attempt) |
| canal alternativo sozinho | **7.653** (233 prompt + 6.184 leitura + 1.236 resposta) |
| residual do despachante | **872** |
| **poupanca** | **6.781** — razao **8,78x** |

A poupanca e, quase inteira, o **turno interno**: os 6.184 B do arquivo
que a assinatura leu por conta propria.

### 4.1 A segunda corrida, com fallback — a proxy demonstrada

A sonda de franquia do kimi (§6) produziu, de quebra, o dado que separa
os dois conceitos em operacao real:

| | bytes utf-8 |
|---|---|
| assinatura absorveu | **391** (prompt DUAS vezes = 74, mais 310 do erro de quota e 7 da resposta) |
| residual do despachante | **44** (37 prompt + 7 resposta final) |

A tentativa perdida fica com a assinatura. Um contador ingenuo, que
somasse um prompt e uma resposta, teria dito 44 nos dois lugares.

## 5. Achados desta missao

### 5.1 O teto de custo zero seguia DECLARADO — familia (F)

A reversao vermelha do defeito 4.1 da P2.0 saiu com as duas metades em
forcas muito diferentes:

    runner sem `custo_previsto` (estado pre-correcao) .. 15 vermelhos
    `teto_custo` do Lab afrouxado de 0.0 para 1.0 ......  0 vermelhos

Os 15 provam que o portao de orcamento esta vivo. O zero prova que o
**valor** do teto nao estava preso a lugar nenhum: trocar `0.0` por `1.0`
passava sem vermelho, e a P2 admitiria custo variavel externo positivo,
contra `external_variable_cost_cap = 0`.

E a **mesma familia (F)** que o achado 4.1 dizia ter fechado. A correcao
de la prendeu o custo PREVISTO; o TETO continuou declarado.

Remedio: dois testes que ligam o teto a `POLITICA_ECONOMICA` — fonte
independente que o runner nao controla —, lendo o envelope PERSISTIDO
pela corrida real. Reversao vermelha: **0 -> 1** em cada um dos dois
lugares que declaram teto. Nenhuma linha de producao mudou.

### 5.2 A codificacao prendia a primitiva e NAO o ponto de chamada — familia (N)

    `decodificar()` revertida a utf-8 fixo ............ 1 vermelho
    `sensor_subprocess` decodificando por conta propria 0 vermelhos

O ponto de chamada — por onde a operacao passa — podia voltar ao estado
pre-correcao sem que nada acusasse.

**Por que o teste de ponta a ponta nao pegava, medido:** ele escreve
bytes UTF-8, e utf-8 fixo decodifica utf-8 sem erro nenhum. Ele exercia o
**vizinho**. O achado 4.3 nasceu de um CLI escrevendo na page de codigo
do Windows, e cp1252 e exatamente o que utf-8 estrito NAO decodifica.

E a licao **N4** da P1-A.3.7 paga de novo: *primitiva corrigida nao cobre
ponto de chamada*. Classificada (N) porque o eixo das varreduras
anteriores era alcance de linha, e este teste **alcancava** a linha sem
discriminar o caso.

Remedio: teste que invoca o subprocesso real fazendo o CLI escrever
cp1252. Reversao vermelha: **0 -> 1**. Producao intocada.

### 5.3 O eco da capsula corrompe acento — fora de ambas as familias

Na primeira corrida real desta missao o console mostrou `canÃ´nico`.
`iniciar_em_capsula` captura o filho com `text=True`, que decodifica na
locale (cp1252) enquanto o runner escreve utf-8.

**NAO e o achado 4.3.** O artefato no CAS foi verificado byte a byte e
esta **integro** (`canônico`, sem U+FFFD e sem mojibake). Dano de
exibicao, nao perda gravada. Registrado, **nao corrigido**: e codigo da
capsula ratificada da P1-A.2, e esta missao nao fecha o proprio conserto
nem o dos outros.

### 5.4 A suite da P0 e cega ao teto do envelope da frota

Sob o mutante que troca `envelope_de_frota`'s `teto_custo` de `0.0` para
`1.0`, a suite da P0 seguiu **344/344**. Ela monta laboratorio com
`teto_custo=1.0` (`test_frota.py:47`) e por isso nunca enxergou o teto do
envelope — a mesma cegueira que o achado 4.1 descreveu, ainda de pe do
lado da P0. Registrado, nao corrigido: e codigo P0 ratificado.

### 5.5 A sentinela anti-P2 pegou o proprio instrumento desta missao

O script de varredura deixou copias de `runner_p2.py`,
`adaptadores.py` e `provedor_assinatura.py` num `scratchpad/backup-ordem3/`
DENTRO do repositorio. A sentinela acusou a copia de `runner_p2.py` como
**consumidor do veredito nao declarado**, em 4 testes, e a verificacao de
sanidade da varredura recusou medir com a arvore suja.

Nao e defeito: e o guarda funcionando contra quem o estava exercendo, e
exatamente contra a propriedade que ele existe para garantir — **P2 por
acidente**. O instrumento foi movido para fora do repositorio.

## 6. A sonda de franquia do kimi

`--capacidade volume` puxa o kimi primeiro. Em **2026-08-03T11:56Z** ele
devolveu `falha-quota` e a maquina rerroteou sozinha para o codex, que
concluiu. Segunda vez na historia do laboratorio que o fallback atravessa
uma falha **real**, nao programada por `FakeProvider`.

A sonda existiu para nao escrever no README uma afirmacao herdada: sem
ela, "a frota e codex-only" seria repeticao da medicao de 02:38Z, e nao
uma medicao.

## 7. O que esta missao NAO estabelece

1. **nao estabelece a tese.** A economia de TOKEN segue nao medida. O que
   ha e uma proxy de bytes, com `n = 1`, e a proxy declara que nao
   alcanca raciocinio, contexto reenviado nem cache — que e onde a
   economia de verdade mora;
2. **nao estabelece tendencia.** Duas corridas, tarefas diferentes.
   Nenhuma media, nenhuma extrapolacao;
3. **nao estabelece qualidade.** Nenhum juiz-llm foi acionado. A resposta
   do canal alternativo saiu quase o dobro da do codex e a proxy nao diz
   qual presta;
4. **nao estabelece que o razonete do canal alternativo seja completo.**
   Esse canal nao grava cadeia; o razonete e declarado item a item. A
   omissao conhecida (enquadramento da ferramenta de leitura) **subestima**
   o canal alternativo, entao empurra o resultado para "nao houve
   economia" — e conservadora;
5. **nao estabelece que os demais guardas do acervo estejam inteiros.**
   Dois dos tres defeitos reverificados estavam pela metade. Quantos
   outros estao na mesma condicao **nao foi medido**, e essa e a pergunta
   que esta missao deixa aberta;
6. **nao estabelece nada sobre `kimi -p` num caminho de sucesso.**

## 8. Criterio de parada da trilha de correcao

O `CLAUDE.md` manda classificar por familia todo achado, e parar a trilha
se uma revisao independente devolver **6+ defeitos novos** ou **4+ na
familia (F)**.

Esta missao **nao e revisao independente** — e a missao que construiu o
instrumento e mediu. Ainda assim, a classificacao, para que a proxima
revisao a tenha:

| familia | quantos | quais |
|---|---|---|
| **(F)** afirma em vez de exercer | **2** | 5.1 (teto zero afrouxavel sem vermelho), 5.4 (suite da P0 cega ao mesmo teto) |
| **(N)** classe que a varredura nao media | **1** | 5.2 (guarda alcanca a linha sem discriminar o caso) |
| fora de ambas | **1** | 5.3 (eco da capsula — nao e guarda do acervo) |

**Nenhum criterio de parada foi disparado.**

O aviso que esta missao deixa a proxima revisao e mais estreito e mais
duro que a contagem: **dois dos tres defeitos que a P2.0 declarou
corrigidos estavam pela metade**, e os dois so apareceram porque alguem
reverteu o guarda em vez de reler o registro. A P2.0 mediu reversao
vermelha dos proprios remedios e nao mediu **o valor que o remedio
protegia** (5.1) nem **o ponto de chamada** (5.2). Sao as duas perguntas
que a proxima reversao vermelha deste acervo deveria fazer por padrao.

## 9. Quem constroi nao certifica

Esta sessao escreveu o medidor, os testes, as correcoes, as duas corridas
e este registro. Ela **nao emite atestado de aprovacao** e nao fecha
nenhum achado por conta propria. A verificacao independente da P2.0 e da
P2.1 segue **pendente**.
