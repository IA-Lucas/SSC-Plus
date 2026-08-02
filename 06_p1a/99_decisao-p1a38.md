---
id: SSC-DEC-P1A38
titulo: Registro e Decisao da Missao SSC+ P1-A.3.8 — remedicao sob a regra dura e montagem do pacote
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-02
---

# Registro e Decisao — Missao SSC+ P1-A.3.8

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhuma decisao ou relatorio historico
> foi editado. **Quem corrige nao certifica — nenhum defeito fecha
> aqui.** Este registro descreve o que foi feito e o que ficou aberto;
> nao e atestado de aprovacao.

## DECISAO: **CONCLUIDA-COM-PULADOS**

Todo item das quatro fases tem resultado ou bloqueio registrado. Fica
pulado, por ordem expressa do ato, **a troca do mecanismo vivo do
ACHADO 4**; e ficam registrados com remedio especificado, sem correcao,
os **20 guardas** que nao sobrevivem inteiros a regra dura.

## SUMARIO — 10 linhas

1. **Os dois defeitos vivos tratados**: a seq booleana ganhou prova **no
   caminho do EventLog** (a anterior exercia so `_tipo`/`validate` — o
   vizinho); o terceiro ramo do `AdaptadorAssinatura` foi **medido,
   declarado correto** e o defeito VIVO ao lado dele foi corrigido.
2. **Defeito vivo achado na FASE 1**: nada prendia `CHAVES_PROIBIDAS` —
   remover `GOOGLE_APPLICATION_CREDENTIALS` deixava **793/793 verdes**.
   A lista da P0 passou a ser presa por corpus de **outra camada**.
3. **FASE 2 — o numero do ato estava errado e esta corrigido**: dos 26
   guardas tocados pela P1-A.3.7, so **15** estavam entre os 64. Logo
   restavam **49**, nao 38. Os 49 foram remedidos, um a um.
4. **Distribuicao mudou de 49 `EXERCE` indiferenciados para
   29 PLENO · 19 PARCIAL · 1 AFIRMA.** Vinte nao sobrevivem inteiros, e
   quatro mecanismos nomeados respondem por todos (F = 11, N = 9).
5. **FASE 3 — `P0-21` foi de 27/57 para 50/57 ramos alcancados**, em
   seis commits: **23 exercidos** pelo caso que ocorre e **5 medidos
   como INALCANCAVEIS** com a inducao escrita. Os 2 restantes sao
   `raise` nus (REPROPAGACAO), que a propria varredura nao conta.
6. **FASE 4 — o remedio do MAJOR #5 NAO reproduzia, e isso so apareceu
   ao executar a prova**: sem `-text`, o `git checkout` convertia o
   gerador para CRLF e o hash do pacote mudava (`c2505a41` contra
   `8f5efac7`). Corrigido, com guarda.
7. **Pacote montado e PRONTO, nao enviado**:
   `b315d3387cc7542801eba17730b2a86fb8c37daffe3b0fe353d8aad3ce986493`,
   88.511 bytes, ancorado em `bd055b9`.
8. **As tres provas do pacote passaram**: dois descartaveis
   independentes com bytes identicos; regeneracao em **clone limpo com
   checkout de outro commit** com hash identico; e **arvore mutada de
   proposito** com hash inalterado.
9. **Suites no HEAD final: P0 293/293, P1-A 568/568, prova central
   18/18** (20 eventos). Chamadas de provedor **0**; custo variavel
   **0**.
10. Arvore limpa, sem tag e sem remoto; lease `p1a38-ops`, fence **1**,
    pid 135928, vivo do inicio ao fim.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Medido |
|---|---|
| HEAD de abertura | `9cb1a798ba594539a6476629940cbab5ffffb485` |
| Arvore | limpa |
| Branch / tag / remoto | `master` / nenhuma / nenhum |
| Lease desta missao | `p1a38-ops`, fence **1**, pid 135928, adquirido **antes da primeira escrita** |
| P0 / P1-A / prova central | **238/238 · 555/555 · 18/18** (20 eventos) |

`05_p0/saidas/prova_central.json` foi reescrito pela corrida da prova
central (UUIDs novos a cada execucao) e restaurado por `git checkout --`
antes da primeira escrita — ruido conhecido, como nas missoes anteriores.

**Condicao operativa declarada.** Enquanto o ACHADO 4 nao for corrigido
NO MECANISMO VIVO, a exclusao mutua entre missoes nao existe; o escritor
unico desta missao foi garantido **por ordem do Fundador**, nunca pelo
mecanismo.

## 2. FASE 1 — os dois defeitos vivos

| # | O que se fez | Teste que prova (caso que OCORRE) | Reversao vermelha | O que NAO cobre | Commit |
|---|---|---|---|---|---|
| 1 | `bool` por `int` na seq: a correcao ja existia em `_tipo`; **faltava a prova no caminho da operacao** | `test_p0_seq_booleana_p1a38.py` — linha canonica com `"seq":true` no disco, `EventLog.verificar`, `EventLog.__init__` e `anexar` | guarda de `bool` fora de `_tipo` => **4 vermelhos em 6** (P0 inteira: 10, contra 6 antes) | seq do **checkpoint** (medida como nao alcancavel); `float` onde se pede `int`; durabilidade e concorrencia | `d5303ed` |
| 2 | terceiro ramo do `AdaptadorAssinatura`: **medido e declarado correto**; corrigido o defeito vivo ao lado | `test_chaves_proibidas_p1a38.py` — corpus de OUTRA camada exercendo a **construcao do adaptador** | (A) chave fora de `CHAVES_PROIBIDAS` => **3 em 8**; (B) chave fora de `CHAVES_PAYG_CONHECIDAS` => **3 em 8**. Antes, a reversao (A) dava **ZERO em 793** | encolhimento SIMULTANEO das duas listas; nao se afirma que as 8 chaves sejam as certas | `1d9afba` |

### 2.1 Por que a prova anterior da seq era vizinha

`test_p0_tipo_p1a37.py` exerce `_tipo(...)` e `evento.validate()` — a
primitiva e o metodo que a chama. Medido revertendo o guarda: **6
vermelhos, todos naquele arquivo, nenhum passando pelo `EventLog`**. A
afirmacao do registro da P1-A.3.7 e sobre o EventLog, e o EventLog nao
era exercido. Achado N4 na letra.

Medido com o guarda revertido, e nao suposto: uma linha
`{"...","seq":true,...}` escrita **canonicamente** no log e aceita por
`EventLog.verificar`, `seq_atual()` vira `True` e `proxima_seq()` vira 2.
`evento.seq != i` e falso porque `True == 1`. O teste inclui
**discriminador**: a linha injetada E a serializacao canonica do proprio
evento, de modo que o guarda de "linha nao canonica" nao a pegaria —
quem recusa e o guarda de tipo.

### 2.2 O terceiro ramo esta correto, e a evidencia

O predicado do guarda (`CHAVES_PROIBIDAS`) e **subconjunto proprio** do
predicado do sanitizador (`CHAVES_PROIBIDAS` ∪ padrao de sufixo), que
roda na linha anterior. Exaustao sobre as oito chaves: **0 de 8**
sobrevivem. Torna-lo bloqueio exigiria conferir o ambiente **recebido**,
e o modulo declara o contrario — *"o ambiente global do usuario NAO e
modificado"*. Numa estacao que exporte chave PAYG, toda construcao
legitima passaria a levantar. Medido tambem: `AdaptadorAssinatura` **nao
tem chamador de producao** em `05_p0/ssc_p0`.

**O defeito vivo que a medicao encontrou** e da familia do MAJOR #3: a
reauditoria quantifica sobre a MESMA lista que o sanitizador usa, de
modo que um encolhimento e invisivel — e **nada prendia a lista**.
Medido: removida `GOOGLE_APPLICATION_CREDENTIALS`, as duas suites ficam
**793/793 VERDES**. Das oito chaves, **sete tambem casam** o padrao de
sufixo; ela e a **unica** protegida so pela lista.

## 3. FASE 2 — os 49 remedidos sob a regra dura

Registro integral em **`99_remedicao-guardas-p1a38.md`**; commit
`3e318e1`. O essencial:

| Classe | Antes | Depois |
|---|---|---|
| EXERCE **PLENO** | — | **29** |
| EXERCE **PARCIAL** | — | **19** |
| **AFIRMA** | — | **1** |
| `EXERCE` indiferenciado | **49** | — |

Quatro mecanismos produzem os 20 que caem: **(a)** primitiva exercida e
ponto de chamada nao (9, familia **N**); **(b)** corpus derivado do
proprio dado protegido (2, **F**); **(c)** sem controle positivo ou
escopo menor que a propriedade (5, **F**); **(d)** propriedade depende
de algo nao exercido (4, **F**). **F = 11, N = 9.**

Achados que so a regra dura viu: `P1A-30` (redacao de
`preflight_capsula` sem cobertura comportamental **nem** estrutural),
`P1A-45` (`ZeroPiiNosArtefatos` **sem controle positivo**, enquanto o
irmao tem dois), `P1A-53` (**AFIRMA** puro: verbos declarados, nenhum
CLI), `P0-28` (o `os.walk` percorre so `base`), `P1A-51` (afirma o TEXTO
do `.gitignore`, nao o efeito), `P1A-54` (classe vazia com o nome certo
satisfaz).

**O instrumento errou e o erro esta declarado**: a primeira corrida
deixou `07_p1b` fora do `--source` e `preflight_atual.py` apareceu com
zero linha executada — dois achados falsos que a segunda corrida
desfez.

## 4. FASE 3 — `P0-21`, de 27/57 para 50/57

| # | Familia | Ramos | Reversao vermelha | Commit |
|---|---|---|---|---|
| 1 | ciclos do grafo | 2 **INALCANCAVEIS** | recusa por `depende_de desconhecido` fora => 3 em 7 | `a2a9aa1` |
| 2 | RoutingDecision | 4 exercidos | 4 ramos fora => 6 em 8 | `b9d85cc` |
| 3 | ExecutionAttempt | 5 exercidos | 5 ramos fora => 10 falhas (4 metodos + 6 subtests) em 8 | `5a81367` |
| 4 | `registrar_veredito` | 5 exercidos + 2 **INALCANCAVEIS** | 5 ramos fora => 6 em 9 | `75cf9fd` |
| 5 | `montar_contexto` | 2 exercidos | 2 ramos fora => 5 em 8 | `14394a7` |
| 6 | retomada e integridade | 7 exercidos + 1 **INALCANCAVEL** | 7 ramos fora => 7 em 9 | `ddeea98` |

**Medicao de fechamento**, com o mesmo instrumento da FASE 2:
`SessionKernel` passou de **27/57** para **50/57** ramos de recusa
alcancados. Os 7 que restam sao, um a um: `L330`/`L340` (ciclo),
`L621`/`L625` (veredito), `L817` (checkpoint) — os **cinco
INALCANCAVEIS**, com a inducao escrita — e `L392`/`L869`, que sao
`raise` nus e caem no balde **REPROPAGACAO** da propria varredura, nao
sendo guardas.

**Correcao de um numero que ficou errado no commit `ddeea98`.** A
mensagem daquele commit diz *"22 exercidos, 6 INALCANCAVEIS"* e enumera
`L621`/`L625` como se fossem alem dos "2 de veredito" — dupla contagem.
O numero medido, e o que vale, e **23 exercidos e 5 inalcancaveis**,
conferido pelo instrumento (50 − 27 = 23) e pela lista dos 7 restantes
acima. O registro historico nao foi editado; a correcao fica aqui.

Duas medicoes da FASE 3 que separam medir de supor:

- **os ciclos sao inalcancaveis por inducao**, e a reversao prova a
  camada: removida a recusa por `depende_de desconhecido`, quem passa a
  recusar e `_checar_ciclo`, com a mensagem de ciclo. A segunda linha
  funciona quando chamada — o que nenhum teste do acervo mostrava;
- **`L963` so e alcancado com o checkpoint RE-SELADO**. Sem re-selar,
  quem recusa e o selo, que e outro guarda. A chave de selo e local, de
  modo que re-selar e o que um adversario com o disco faria.

## 5. FASE 4 — o pacote, e o defeito que a prova revelou

| Item | Medido |
|---|---|
| Arquivo | `06_p1a/evidencias/revisao-p1a38/pacote-p1a38.txt` |
| SHA-256 | `b315d3387cc7542801eba17730b2a86fb8c37daffe3b0fe353d8aad3ce986493` |
| Bytes / linhas | **88.511** / 1.895 |
| ALVO ancorado | `bd055b9d39ca0d7323ba285dfbc25c77fb4c0049` |
| BASE | `9cb1a798ba594539a6476629940cbab5ffffb485` |
| Estado | **PRONTO, NAO ENVIADO** |

### 5.1 O defeito, achado ao executar e nao ao ler

A primeira tentativa de prova de ancoragem **falhou**:

```
geracao no repositorio de trabalho   sha256 c2505a41…  82110 bytes
geracao em CHECKOUT LIMPO do commit  sha256 8f5efac7…  82110 bytes
```

Mesmo tamanho, **uma** linha diferente: a do SHA-256 do proprio gerador.
Causa medida — blob no Git **8.277 bytes com 191 LF**; arquivo no
checkout limpo **8.468 bytes com 191 CRLF**. O **blob e identico** nos
dois repositorios (`892479a7…`); o que difere e o que `git checkout`
escreve no disco com `core.autocrlf=true` e sem atributo.

`pacote_p1a37.py` hasheia os bytes **de disco** — decisao declarada e
correta, o objeto sob julgamento e o gerador que rodou. O efeito nao
previsto e que o hash do pacote deixava de ser funcao do commit.

**O precedente ja existia e nao foi estendido:** `06_p1a/.gitattributes`
marca `pacote_p1a31.py` e `revisao_p1a31.py` como `-text` por este exato
motivo. O gerador novo nasceu sem a linha — o mecanismo do achado 10
outra vez. Familia **F**: o remedio **afirmava** reproduzir e nao
reproduzia. Corrigido em `bd055b9`, com guarda
(`test_ancoragem_gerador_p1a38.py`) que exige o **atributo**, e nao so a
igualdade de bytes: nesta estacao os bytes **ja** coincidem, e um teste
que so os comparasse passaria verde com o defeito vivo — foi assim que
ele sobreviveu.

### 5.2 As tres provas, executadas

1. **Determinismo** — duas geracoes em descartaveis independentes:
   `cmp` sem diferenca, mesmo SHA-256, mesmos 88.511 bytes.
2. **Ancoragem por commit** — regenerado em **clone limpo** com checkout
   de **outro** commit (`9cb1a79`): hash **identico**.
3. **Independencia da arvore de trabalho** — dois arquivos rastreados
   mutados de proposito (um `.py` que entra inteiro no pacote e um `.md`
   hasheado): hash **inalterado**. Arvore restaurada em seguida.

*Nuance declarada:* mutar o **proprio gerador** mudaria o hash, e isso e
desenho. A prova 3 vale para todo arquivo julgado, nao para o gerador.

### 5.3 Conteudo varrido — medido, nao prometido

**0** ocorrencias de: usuario local (forma longa e 8.3), caminho local,
caminho de perfil de usuario, UUID, chave `sk-`/`xai-`/`AIza`, token
`Bearer`, arquivo `.lock`/`.lease`/`.fence`, `__pycache__`/`.pyc`,
`.coverage`/`htmlcov`.

**1** timestamp ISO: `ts="2026-08-01T00:00:00Z"`, literal **fixo** dentro
do fonte de um teste — nao e carimbo de geracao, e e por ser fixo que o
pacote reproduz.

## 6. Fronteira, custo e ambiente

| Item | Estado **verificado** |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | codigo, teste, registro e pacote desta missao; nada fora |
| Escritas fora do repositorio | descartaveis dos testes, instrumentos e clones de prova, no temp da sessao |
| Copia datada | **nenhuma criada** — pratica encerrada por decisao do Fundador |
| Store do harness | **nao gravado** |
| **Chamadas de provedor / de modelo** | **0** |
| Custo variavel | **0** |
| Tag, remoto ou push | nenhum |
| Pacote enviado | **nenhum** |
| Lock tomado a forca | nenhum |
| HKCU / variavel persistente | **nao tocada** |
| Mecanismo de lock | **nao trocado** |
| Politica | **nao alterada** |
| Registro historico | **nao editado** |

Os instrumentos de medicao (`coverage` com contexto por teste, consultas
por AST) **nao foram acrescentados ao acervo**, pelo motivo da P1-A.3.5:
um `.py` novo sem teste seria mais um caso do achado C.

## 7. Alcance — o que esta missao estabelece e o que NAO estabelece

### 7.1 Estabelecido — medido

| Fato | Como |
|---|---|
| A seq booleana e recusada no caminho da operacao | log real em disco, `verificar`/`__init__`/`anexar`, com discriminador de canonicidade |
| O terceiro ramo do adaptador nao dispara | exaustao 0 de 8 sobre a lista |
| `CHAVES_PROIBIDAS` passou a ter guarda | reversao que antes dava 0 em 793 hoje da 3 em 8 |
| Os 49 `EXERCE` restantes foram remedidos | um por linha, com o conjunto nominal de testes medido por contexto dinamico |
| `P0-21` foi de 27/57 a 50/57 | mesmo instrumento, antes e depois |
| Cada correcao esta acoplada ao seu guarda | reversao vermelha medida em **todas as onze** correcoes |
| Nenhuma correcao reprova sempre | contraprova em cada uma, verde sob a propria reversao |
| O pacote e funcao dos commits | tres provas independentes, incluindo clone limpo |
| Suites no HEAD final | P0 293/293, P1-A 568/568, prova central 18/18 |

### 7.2 NAO estabelecido — e nao se presume

- **Nada fecha.** Quem corrige nao certifica; fechar depende de revisor
  independente, e esta missao nao o convocou.
- **Os 20 guardas que caem na regra dura NAO foram corrigidos** —
  registrados com remedio especificado, por ordem do ato.
- **PLENO nao e sinonimo de correto.** Exercer o caso que ocorre e
  condicao necessaria, nunca suficiente.
- **Os 15 guardas remedidos pela P1-A.3.7 nao foram reabertos** — e uma
  escolha declarada, nao uma medicao.
- **Os 22 guardas fora dos 64** (13 `SEM-TESTE`, 8 `AFIRMA`, 1
  `INDETERMINADO`) nao foram objeto desta missao.
- **A troca do mecanismo do ACHADO 4 nao foi feita**, por ordem
  expressa: segue decisao atendida do Fundador.
- **`P0-21` nao esta fechado**: 7 ramos seguem nao alcancados, 5 deles
  declarados inalcancaveis com inducao — e inducao escrita nao e teste.
- **O achado B (`P1A-58`) segue INDETERMINADO.**
- **O pacote NAO foi enviado**, nenhum provedor foi invocado, nenhuma
  cota ou tier foi renovada, e a metade (b) do portao da P1-A.3.6 —
  dois vereditos — continua intocada.
- **Nada aqui afere o criterio de parada** do `CLAUDE.md`: ele exige
  medicao de **revisao independente**, e esta e missao de correcao. A
  classificacao por familia dos achados desta missao esta registrada
  para que a proxima revisao possa aferi-lo.

## 8. O que a proxima missao precisa

1. **Revisao independente sobre `bd055b9`**, com o pacote
   `b315d338…`, e **classificacao por familia obrigatoria** — sem ela o
   criterio de parada nao pode ser aferido.
2. **Aplicar o criterio de parada** gravado no `CLAUDE.md`.
3. **Os 20 guardas da FASE 2 que nao sobrevivem a regra dura**, na
   ordem dos quatro mecanismos — o **(a)** e o mais barato: nove
   pontos de chamada de redacao e de portao de tier.
4. **Decidir a troca do escritor unico** para `escritor_repositorio`.
5. **Os 5 ramos inalcancaveis de `P0-21`**: decidir se defesa em
   profundidade sem teste fica, ou se sai.

> Onze correcoes, onze reversoes vermelhas medidas, tres defeitos vivos
> achados ao exercer — e zero defeitos fechados. Fechar nao e trabalho
> de quem corrige.
