# Achados de Governanca — registro transversal, 2026-07-31

> Documento **proprio**, nao emenda de nenhum registro alheio. Os cinco
> achados abaixo nasceram na verificacao pos-fechamento da P1-A.3.3 e na
> tentativa de registra-los; atravessam missoes e por isso nao cabem no
> registro de nenhuma. **Nenhum relatorio historico foi editado** — em
> particular a `99_decisao-p1a34.md` permanece intacta, inclusive seu
> veredito.
>
> Escritor designado por ordem do Fundador, apos a P1-A.3.4 fechar e seu
> titular morrer. Lease `achados-gov-ops` fence **1**, adquirido antes da
> primeira escrita.

## 0. Estado medido na abertura

| Item | Medido |
|---|---|
| HEAD | `9f203be` (P1-A.3.4, 14:02:38) |
| Arvore | limpa |
| Tag / remoto | nenhuma / nenhum |
| Sessao viva | **nenhuma** — nenhum `renovador_lock.py`; `p1a34-ops` com `expira_em` inalterado em duas amostras a 40 s e PID titular 116204 **inexistente** |
| Escritas desta sessao antes desta | `8bbac04` as **13:38:05**, anterior a aquisicao da P1-A.3.4 as **13:49:13** — sem sobreposicao de escritor |

Nenhuma copia datada foi criada para esta escrita: por decisao do
Fundador (2026-07-31) a pratica esta encerrada, e o Git local e a
primeira copia, como o manifesto §7 ja dizia.

**Controle positivo observado, e vale registrar porque e o contraste
exato do ACHADO 4.** A primeira corrida da suite com este documento
staged **reprovou**: `ZeroPiiNosArtefatos.test_nenhum_email_nem_usuario_local_em_06_p1a`
acusou `99_achados-governanca-20260731.md: usuario-local` — o texto
continha o nome do usuario local em um caminho do store. O caminho foi
redigido para `<USUARIO>` e a suite passou a verde. Esse guarda **varre
os arquivos reais da arvore** e por isso pegou o artefato de quem o
estava escrevendo; o guarda do escritor unico (§4) verifica um lease que
ele proprio nomeia, e por isso nao pegaria nada. Mesma suite, duas
qualidades opostas de guarda.

## 1. ACHADO 1 — copias datadas irmas contra o manifesto §2

O manifesto de isolamento (`00_governanca-experimental/02_manifesto-de-isolamento.md`)
e literal:

- **§2** — *"**Proibido gravar:** qualquer caminho fora da raiz, incluindo
  os backups `_backup-*`, `_candidatos-*` e demais **irmaos em
  `E:/LucasIA/Projetos`**."*
- **§7** — *"Copia de seguranca adicional: a criterio do Soberano, espelho
  em `E:/LucasIA/Projetos/_backups` … **nao e criada nesta fase por
  decisao de escopo**."*
- **§4** — a disciplina que ninguem aplicou: *"a missao que a introduzir
  deve atualizar este manifesto **antes** do uso"*.

**Medido, nao estimado.** Antes das remocoes desta sessao havia **nove**
copias irmas, com **sete rotulos de missao distintos** mais uma sem
rotulo:

```
SSC-Plus_copia-20260730-100839        (sem rotulo)
SSC-Plus_copia-p1b-20260730-132142
SSC-Plus_copia-p1b-20260730-132215
SSC-Plus_copia-p1a2-20260730-170255
SSC-Plus_copia-p1a3-20260730-223105
SSC-Plus_copia-p1a31-20260731-074426
SSC-Plus_copia-p1a32-20260731-115307
SSC-Plus_copia-p1a33-20260731-125347
SSC-Plus_copia-p1a34-20260731-134901
```

**Defeito do Goal, nao da sessao.** Os Goals da P1-A.3.3 e da P1-A.3.4
escreveram *"jamais uma das copias datadas"* — formulacao que pressupoe
as copias como artefato legitimo e **normaliza a pratica sem consultar o
manifesto**. A sessao que le o Goal nao tem como suspeitar: o Goal fala
das copias como coisa existente e permitida.

**STOP — decisao, nunca ausencia de violacao.** A Carta §8 lista quatro
condicoes de encerramento; a terceira e *"qualquer escrita fora do
isolamento"*. O Fundador **decidiu nao declarar STOP**, sabendo que a
regra como escrita aponta para la. Registra-se aqui **como decisao dele**,
e nao como constatacao de que nao houve violacao — sao coisas
diferentes, e confundi-las apagaria o rastro. Das outras tres: 1
(sucesso) e 2 (inutilidade) nao ocorreram; 4 (encerramento por decisao)
nao foi exercida.

**Nao emendado.** A correcao e do manifesto, e alterar politica esta fora
de qualquer missao em curso. E materia da missao de politica (§8).

## 2. ACHADO 2 — o store do harness e canal de influencia sem auditoria

`C:\Users\<USUARIO>\.claude\` fica **fora do escopo do manifesto por
rito** — declaracao a ser feita pela missao de politica —, e **nao** por
interpretacao do §3 (que fala de `memory/` do canonico e `kb/` do
legado) sobre o §2.

**Inventario medido:**

| Area | Medida |
|---|---|
| `projects/` | **3.089 arquivos, 1.105,32 MB** |
| `file-history/` | **4.710 arquivos, 100,32 MB** |
| `tasks/` | 234 arquivos |
| `plans/` | 49 arquivos |
| `projects/E--LucasIA-Projetos-SSC-Plus` | **6 transcricoes, todas de 30/07** — e **nenhum diretorio `memory/`** |
| `projects/E--LucasIA-Projetos-lucaX/memory` | 25 arquivos |
| `projects/E--LucasIA-Projetos-LucaX-Enterprise-OS/memory` | 21 arquivos, **12 gravados em 31/07** |

Os doze de hoje, com hora: `filtro-de-ir-03` 08:18, `instante-nao-data`
08:18, `ancoragem-no-commit-nao-na-copia` 09:46,
`denylist-mede-a-arvore-errada` 10:26, `lista-a-mao-omite-em-silencio`
10:26, `estado-do-acervo-lucax` 11:00, `suite-com-arquivos-staged` 11:03,
`prova-por-reversao-da-correcao` 12:31, `escalar-sem-prova-e-hedge`
12:45, `guarda-de-argv-precisa-rodar` 13:13,
`escrita-autorizada-nao-se-devolve` 13:39, `MEMORY.md` 13:39.

**A origem do ACHADO 1 — encontrada, e nao e uma licao isolada.** Nao
existe licao dizendo "faca copia datada no SSC+". O mecanismo e
estrutural e pior:

1. O SSC+ **nao tem store proprio** — o diretorio existe, mas sem
   `memory/`, e suas transcricoes pararam em 30/07.
2. As sessoes das missoes SSC+ rodam com cwd em `LucaX Enterprise OS` e
   portanto carregam o store **daquele** projeto.
3. Naquele store, copia datada em `_backups` e a pratica **correta**, e
   aparece em quatro memorias: `estado-do-acervo-lucax`,
   `onde-vivem-os-candidatos`, `classificar-o-conjunto-de-mudanca`,
   `denylist-mede-a-arvore-errada`.
4. Somada a regra global do Fundador — *"Backup antes do risco … Sem
   copia, nao roda"* —, a sessao SSC+ herda uma disciplina correta **no
   projeto de origem** e proibida **no projeto de destino**.

**A disciplina de um projeto vaza para outro por um caminho que ninguem
audita.** O store esta fora do Git, fora do acervo, sem revisao, e dirige
comportamento de missoes futuras.

**O caso mais limpo do achado foi produzido pela propria P1-A.3.3:** as
13:39 ela gravou `escrita-autorizada-nao-se-devolve.md`, cujo corpo
codifica *"executar pelo protocolo (backup datado, lease antes da
primeira escrita…)"* — reforcando o vetor horas depois de ele ter
produzido a violacao. E o canal seguiu em uso depois disso: a P1-A.3.4
gravou `provar-argv-aceito-sem-gastar-chamada.md`.

**Nao corrigido e nao apagado**, por ordem do Fundador: inventariar e
registrar. Corrigir licao e materia da missao de politica.

## 3. ACHADO 3 — a ancora de proveniencia esta mal desenhada, nao desatualizada

Manifesto §3 e D3 §1 ancoram o legado `lucaX` em HEAD
`bf8a407c2d2fbd492f4ba4abeed522d345b5b786` com 334 arquivos modificados.
**Medido em 31/07: `95f4933f80ac5dcb8065bb2c62364572df6aa413`, com 410
modificados.** Mudanca externa ao laboratorio.

**Nao reancorar.** Hash de arvore do `lucaX` e ancora inviavel: o
repositorio tem sessao viva e centenas de arquivos sem commit; reancorar
refaz a ancora que acabou de quebrar, e quebrara de novo. O defeito nao e
o numero — e **o desenho**.

**Substituicao, uma ancora por pergunta:**

| Pergunta | Ancora correta |
|---|---|
| O laboratorio contaminou a fonte? | **Janela de tempo** — mtime dos arquivos alterados contra o inicio da sessao |
| O que foi lido, e em que estado? | **Hash por arquivo**, so dos efetivamente consumidos, congelado no instante da leitura |

Hash de arvore inteira nao responde nenhuma das duas. A primeira ja foi
exercida: em `LucaX Enterprise OS` os **15** arquivos com mtime de
31/07 param as **10:59**, e a sessao da P1-A.3.3 comecou as **13:20** —
nenhuma escrita do laboratorio.

**Premissa a corrigir no proximo tratamento:** D3 §1 ancora os hashes do
SuperCondutor, fonte da engenharia reversa que fundou o SSC+. A
dependencia e **futura, nao inexistente**; tratar como registro
historico dispensavel seria erro. Hashes novos do SuperCondutor **nao**
foram medidos aqui — e escopo da missao de politica.

## 4. ACHADO 4 — o "escritor unico" nao exclui entre missoes

Candidato a **setimo MAJOR**. Produzido ao verificar se esta sessao podia
escrever com a P1-A.3.4 viva.

`LockSessao` (`05_p0/ssc_p0/writelock.py`) tranca o arquivo que recebe no
construtor — `msvcrt.locking` no Windows, `fcntl.flock` no POSIX —
chaveado por `os.path.normcase(os.path.realpath(caminho_lock))`. E
`escritor.py:46-49` monta esse caminho como:

```
locks/{sessao}.lock      e      locks/{sessao}.fence
```

Como **cada missao usa um nome proprio** — `p1a2-ops`, `p1a3-ops`,
`p1a31-ops`, `p1a32-ops`, `p1a33-ops`, `p1a34-ops`, `achados-gov-ops` —,
duas missoes concorrentes trancam **arquivos diferentes** e nenhuma
bloqueia a outra. **A exclusao mutua entre missoes nao existe.**

A docstring de `escritor.py` afirma: *"Uma segunda sessao falha na
aquisicao (LockIndisponivel) — antes de escrever um byte ou invocar
qualquer provedor."* Isso vale **somente** para segunda sessao com o
**mesmo nome**. O teste que sustenta a afirmacao,
`test_runner_segunda_sessao_retorna_3_sem_invocar_nada`
(`test_estabilizacao_p1a1.py`), usa `"p1-ops"` nos **dois** lados:
exercita o unico caso que funciona e nunca o caso que ocorre em
operacao.

**Demonstracao, nao teoria.** Se a P1-A.3.3 tivesse assumido pelo
protocolo de sucessao, teria segurado `p1a33-ops` fence 6 com
`p1a34-ops` fence 1 vivo, e **os dois `verificar_lock` teriam passado** —
cada um conferindo apenas o proprio lease e o proprio fence. Foi ordem do
Fundador, e nao o controle, que impediu a escrita concorrente.

E a mesma classe do achado #6, da §4 da `99_decisao-p1a33.md` e da §10.2
dela: **guarda exercido onde vale, nunca onde e usado.** A P1-A.3.4
classificou os seis nesse mesmo eixo (EXERCE/AFIRMA); este achado diz que
o eixo alcanca tambem o escritor unico, que nao estava entre os seis.

**Classificar junto, nao corrigir.**

### 4.1 Corolario ja observado tres vezes — o lease sobrevive ao titular

`liberar()` (`escritor.py:82-84`) solta apenas o lock do SO; o arquivo
`.lease` sobrevive com `expira_em = aquisicao + 900 s` (ou 120 s pelo
renovador). Consequencia medida em tres sessoes consecutivas: `p1-ops`,
`p1a33-ops` e `p1a34-ops` leem como **"nao vencido, titular morto"**
depois do fechamento. E a suite P1-A **fabrica** o artefato a cada
corrida, porque `test_estabilizacao_p1a1.py:359` adquire sobre o
`locks/` **real** do repositorio, nao um `tmpdir`.

So o protocolo dos dois manifestos derrota o falso positivo. Ja
registrado na §10.2 da `99_decisao-p1a33.md`; repetido aqui porque e o
mesmo mecanismo do ACHADO 4 e a missao de politica os corrige juntos.

## 5. ACHADO 5 — decisao que vive so na conversa nao alcanca sessao nenhuma

Prova viva do ACHADO 2, produzida durante esta propria sequencia.

Linha do tempo medida:

| Hora | Fato |
|---|---|
| ~13:36 | Fundador decide **encerrar** a pratica de copias datadas |
| 13:38:05 | P1-A.3.3 commita `8bbac04` e libera o escritor |
| **13:49:01** | **P1-A.3.4 cria `SSC-Plus_copia-p1a34-20260731-134901`** |
| 13:49:13 | P1-A.3.4 adquire `p1a34-ops` |
| 14:02:38 | P1-A.3.4 commita `9f203be` em `READY-FOR-REVIEW` |

A P1-A.3.4 criou a copia **treze minutos depois** da decisao que a
proibia. **Nao e falha dela:** a decisao vivia apenas na conversa de
outra sessao. Nao estava no acervo, nao estava no manifesto, nao estava
no Goal dela e nao estava no store que ela carrega — os quatro canais que
uma sessao efetivamente le.

O registro dela reafirma a pratica por escrito: `99_decisao-p1a34.md:348`
declara *"Escritas fora do repositorio | duas, ambas exigidas: a copia
datada (**irma**, nao dentro) …"*. Chamar de **exigida** o que o §2
proibe e exatamente a normalizacao descrita no ACHADO 1.

**Licao operativa:** decisao do Fundador so vincula missao futura se
entrar em canal que a missao le — acervo, manifesto, Goal ou store. Dizer
em conversa nao basta, e a prova disso e que nao bastou.

## 6. Remocoes executadas, com verificacao

| Copia | Criada por | Estado |
|---|---|---|
| `SSC-Plus_copia-p1a33b-20260731-133402` | P1-A.3.3, 13:34:02 | **REMOVIDA** — `existe_antes=True` → `existe_depois=False` |
| `SSC-Plus_copia-p1a34-20260731-134901` | P1-A.3.4, 13:49:01 | **REMOVIDA** — `existe_antes=True` → `existe_depois=False` |

Restam **8** copias irmas, todas anteriores a decisao do Fundador.
**Historico nao se apaga:** elas ficam onde estao.

Antes de remover a copia da P1-A.3.4 foi verificado que seu conteudo
rastreado e reproduzivel do acervo: a copia esta em `8bbac04`, que
`git merge-base --is-ancestor` confirma ser **ancestral do HEAD**, e ela
nao continha trabalho nao commitado proprio.

### 6.1 Duas referencias penduradas, nomeadas

A remocao acima tem efeito colateral que **nao se conserta apagando** e
por isso se registra:

- `99_decisao-p1a34.md:44` — *"Copia datada | `SSC-Plus_copia-p1a34-20260731-134901` — **2968 de 2968** arquivos"*
- `99_decisao-p1a34.md:348` — *"Escritas fora do repositorio | duas, ambas exigidas: a copia datada (**irma**, nao dentro) …"*

As duas citam como evidencia conferida um diretorio que **nao existe
mais**. O registro da P1-A.3.4 **nao foi editado** — relatorio historico
alheio nao se edita. Quem ler aquelas linhas encontra aqui a razao.

## 7. Condicao operativa vigente — escritor unico por ordem, nao por mecanismo

**Enquanto o ACHADO 4 nao for corrigido:**

> A exclusao mutua entre missoes **nao existe**. O escritor unico e
> garantido **por ordem do Fundador** — uma sessao de escrita por vez,
> decidida por ele, nunca pelo mecanismo.

Isto nao e recomendacao: e a condicao sob a qual esta propria escrita
ocorre. O lease `achados-gov-ops` nao impediria uma segunda sessao com
outro nome de escrever ao mesmo tempo. Missao que assumir o escritor deve
declarar esta condicao no proprio atestado ate que ela caia.

## 8. Consequencia para o pacote de revisao — o ACHADO 4 e do escopo dos revisores

O ato manda cada revisor avaliar, entre doze eixos, **"escritor unico"**.
O pacote enviado a Codex e Kimi afirmava esse controle sem saber do
ACHADO 4.

**O proximo pacote deve declarar o ACHADO 4 aos dois revisores**, como ja
se faz com o achado aberto de `07_p1b/preflight_atual.py:172`. Julgar
"escritor unico" sem saber que a exclusao mutua entre missoes nao existe
e **julgar contra premissa falsa** — e um veredito assim nao vale, tenha
ele aprovado ou reprovado.

O veredito `READY-FOR-REVIEW` da P1-A.3.4 **nao e reaberto aqui**. O que
se registra e que o pacote que for a revisao precisa carregar este
achado.

## 9. A missao de politica cobre quatro materias, nao tres

As quatro nasceram do mesmo defeito — **regra escrita num lugar,
comportamento decidido em outro, sem canal entre os dois**:

1. **Manifesto §2/§7** — copias datadas: autorizar com forma e local, ou
   proibir e fazer valer. Hoje o texto proibe e a pratica cria.
2. **Store do harness** — declarar escopo por rito, e tratar o vazamento
   entre projetos: o SSC+ carrega o store do `LucaX Enterprise OS`.
3. **Ancora de proveniencia** — substituir hash de arvore por janela de
   tempo (nao-contaminacao) e hash por arquivo consumido (proveniencia).
4. **Lock por nome de sessao** — exclusao mutua real entre missoes, e
   `liberar()` que expire o lease que concedeu.

**Nenhuma delas e emendada aqui.** Alterar politica exige missao propria
com decisao do Fundador.

## 10. Alcance — o que este registro estabelece e o que NAO estabelece

**Estabelece.** Os cinco achados sao afirmacoes de existencia, e cada um
tem contraexemplo verificavel por terceiro: o texto do manifesto contra a
lista de nove copias; o inventario do store contra a ausencia de
`memory/` no SSC+; os dois HEADs do `lucaX`; o caminho do lock em
`escritor.py:46-49` contra a docstring; e a linha do tempo de treze
minutos. Abrir defeito basta um contraexemplo — por isso valem
integralmente, embora produzidos por quem os registra.

**Nao estabelece.** Nenhum MAJOR fechou; nenhum abriu formalmente — o
ACHADO 4 e **candidato** a setimo MAJOR, e quem classifica MAJOR e
revisor, nao esta sessao (`99_decisao-p1a33.md` §9.3: fechar e afirmacao
universal, e nenhuma execucao a demonstra). Nao se afirma que a P1-A.3.4
errou: ela agiu com os canais que tinha. Nao se afirma que houve, ou que
nao houve, violacao da Carta §8.3 — registra-se que o Fundador decidiu
nao declarar STOP. Nao se afirma nada sobre P1-B sombra.

**Nao alterado.** Zero linha de codigo, teste, politica ou relatorio
historico. O unico caminho novo e este documento.
