---
id: SSC-DEC-P1A33
titulo: Registro e Decisao da Missao SSC+ P1-A.3.3 — revisao independente do estado corrigido (BLOCKED)
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-31
---

# Registro e Decisao — Missao SSC+ P1-A.3.3

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo** sobre o HEAD `ac03f3a`.
> `99_decisao-p1a3.md`, `99_decisao-p1a31.md` e `99_decisao-p1a32.md`
> NAO foram tocadas. `NVIDIA_API_KEY` global/HKCU jamais removida,
> alterada ou persistida.

## DECISAO: **BLOCKED** — nenhum veredito obtido; os DOIS provedores sem quota

Nenhum revisor produziu revisao. O portao (zero CRITICAL e zero MAJOR
nos dois vereditos) **nao foi alcancado** — nao por reprovacao, mas por
inexistencia de veredito. A P1-B-02 permanece **FECHADA** e nenhum
atestado foi emitido.

Duas causas independentes, cada uma suficiente por si:

1. **Codex sem quota.** A chamada unica retornou
   `You've hit your usage limit ... try again at Aug 5th, 2026 9:29 AM`.
   A unica via imediata oferecida e **comprar creditos** — via paga,
   proibida pelo ato (custo variavel maximo zero). Somente o
   proprietario renova; a missao nao tentou nenhuma via paga, nenhuma
   segunda chamada e nenhum provider substituto.
2. **Kimi nao chegou a ser chamado.** O CLI **recusou os proprios
   argumentos** que o codigo corrigido monta (§4). Zero chamada de
   modelo, zero rede: a quota do kimi permanece **NAO RESOLVIDA**, e nao
   se afirma aqui que esteja disponivel nem que esteja esgotada.

A pre-condicao do ato e explicita — *"sem declaracao valida ou sem
quota: BLOCKED, nunca renovacao automatica"*. E o que se aplica.

**Achado desta missao, de classe MAJOR, que exige alteracao de codigo
(§4): a correcao do MAJOR #3 da P1-A.3.2 e inexecutavel.** Por forca do
ato ("nao corrigir dentro desta missao"), **nada foi corrigido**. Ele
fica registrado como item ADJUST da proxima missao.

## 1. Identidade e pre-condicoes (verificadas na abertura)

| Item | Resultado medido |
|---|---|
| HEAD exigido (P1-A.3.2) | OK — `ac03f3a43a8ad5e1d2f54151450318b00ff7b859` |
| Pai | OK — `029ff443f38da2ac2c8f89e08c2cf1a1a59b27c9` |
| Base da correcao (HEAD da P1-A.3.1) | `30107bd1ef30b07ab575ff5991e90d70345d702a` |
| Ancestralidade | OK — `30107bd` e `029ff44` sao ancestrais de `ac03f3a` (`merge-base --is-ancestor`) |
| Tree | `a77c6e9d3362a46c3fa3a55bbf328e1c0a55a9ec` |
| Arvore limpa | OK |
| Sem tag e sem remoto | OK — `git tag -l` e `git remote -v` vazios |
| Copia datada | `SSC-Plus_copia-p1a33-20260731-125347` — **2866 de 2867** arquivos; o unico ausente e `locks/p1a33-ops.lock`, sob lock do SO desta propria sessao |

### 1.1 Locks — medidos pelo protocolo, nenhum removido a mao

Sete leases no diretorio. **Cinco vencidos e dois NAO vencidos** — e os
dois nao vencidos tinham **titular morto**:

| Lease | PID titular | Vencido | Titular vivo | Leitura |
|---|---|---|---|---|
| `p1-ops` | 121600 | nao (restavam ~700 s) | **nao** | titular morto com lease ainda na janela |
| `p1a32-ops` | 121416 | nao (restavam ~100 s) | morreu **durante** a medicao | renovador da P1-A.3.2, encerrado as 15:45Z |
| `p1b-ops` | 105464 | sim | **PID reciclado** (`svchost.exe`, criado 12:36) | armadilha: checar so "PID vivo" daria falso positivo |
| `p1a2-ops`, `p1a3-ops`, `p1a31-ops`, `repo-p1a1` | 91064, 78412, 70536, 79508 | sim | nao | mortos |

Prova de que **nenhuma sessao estava viva**: dois manifestos dos leases
tomados com 40 s de intervalo mostraram `expira_em` **inalterado em
todos os sete** — nenhum renovador ativo —, e nenhum processo
`renovador_lock.py` existia. O `p1b-ops` mostra por que a liveness nao
pode ser inferida do PID: 105464 estava vivo, mas como `svchost.exe`
criado muito depois do lease.

A P1-A.3.2 deixou o proprio renovador rodando ~15 min apos o commit; ele
encerrou sozinho no inicio desta missao. Nenhum lock foi removido a mao.

| Lease e fencing desta missao | `p1a33-ops`, fence **1**, pid 91384, lease 120 s renovado a 30 s por `evidencias/renovador_lock.py`, adquirido **antes da primeira escrita** |
|---|---|

### 1.2 Declaracao de tier — valida, medida no instante

| Provider | Tier declarado | Declarado em (UTC) | Expira (UTC) | Idade na abertura |
|---|---|---|---|---|
| codex | ChatGPT Pro 5x | `2026-07-31T01:31:00Z` | `2026-08-01T01:31:00Z` | **14,22 h** |
| kimi | Allegretto | `2026-07-31T01:31:00Z` | `2026-08-01T01:31:00Z` | **14,22 h** |

Ambas por `declarado_por: proprietario`, dentro da janela de 24 h, e
revalidadas pelo runner **no instante de cada chamada**
(`valido_no_instante: true` nas duas evidencias). Nenhuma renovacao
automatica de tier.

### 1.3 Quota — o que e observavel e o que nao e

Medido, nao presumido: **o CLI do kimi 0.30.0 nao expoe quota em
subcomando algum**. `kimi --help` lista `export`, `provider`, `acp`,
`web`, `server`, `login`, `doctor`, `vis`, `migrate`, `upgrade`; e
`kimi provider --help` mostra que `provider` gerencia **configuracao
local** (`add`/`remove`/`list`/`catalog`), nao consumo. A quota so se
revela na propria chamada.

`kimi provider list` (descoberta autorizada pela emenda 3 do Soberano,
zero chamada de modelo) devolveu:

```
managed:kimi-code  type=kimi  models=4  source=oauth
Default model: kimi-code/k3
```

Ou seja: **o canal de assinatura esta vivo** (`source=oauth`) e o modelo
padrao e observavel. Isso **nao** comprova quota — a propria emenda 3 diz
que `provider list` nao comprova o plano comercial.

Consequencia registrada: a pre-condicao "quota do kimi disponivel" **nao
e verificavel ex ante** com o CLI instalado. Nesta missao ela nao chegou
sequer a ser testada, porque a chamada morreu antes da rede (§4).

### 1.4 Os seis MAJOR — correcao e teste de falha registrados

| # | MAJOR | Alvo da correcao | Teste que prova | Prova por reversao |
|---|---|---|---|---|
| 1 | atalho PAYG de google/grok | `preflight_capsula.py` (`classificar_frota`) | `AtalhoPaygGoogleGrok` (7) | FAILED (5) |
| 2 | regexes de quota esgotada | `preflight/adaptadores.py` (`_ZERO`) | `QuotaEsgotadaZeroDecimalEPercentual` (4) | FAILED (7) |
| 3 | isolamento do kimi | `evidencias/contencao.py` + 2 runners | `ContencaoDoReviewer` (8) | FAILED (4) |
| 4 | lease antes da persistencia | `contencao.verificar_lock` + chamadores | `LeaseAntesDaPersistencia` (7) | FAILED (3) |
| 5 | ancoragem do pacote no commit | `evidencias/pacote_p1a31.py` | `AncoragemDoPacoteNoCommit` (4) | FAILED (9) |
| 6 | sentinela anti-P2 (achado #6) | `tests/test_emendas_p1a3.py` | o proprio teste, por AST | prova por mutacao (3 arquivos) |

Os seis tem correcao e teste de falha registrados. **O item 3 tem o
teste, mas o teste nao cobre a propriedade que falhou** — §4.

### 1.5 A "reconciliacao 8x9" — o que existe e o que nao existe

Registro honesto: **nenhum artefato do acervo se chama "reconciliacao
8x9"**. Busca por `reconcil`, `8x9`, `8/9`, `8 de 9`, `oito…nove` em
todo o repositorio: zero ocorrencia. Procurei tambem pela *funcao*, nao
so pelo termo. Os dois candidatos medidos que tem a forma 8 x 9:

- **Contagem de arquivos dos commits probatorios.** `dc19e8c`
  (P1-A.3.1) = **8 arquivos**; `029ff44` (P1-A.3.2) = **9 arquivos**. Os
  8 de `dc19e8c` reconciliam exatamente com o escopo declarado na §10 da
  `99_decisao-p1a31.md`: 4 caminhos autorizados (um deles um diretorio
  que expande para 4 arquivos) + 1 `.gitattributes` escopado + 1
  `.gitattributes` de extensao declarada = 8. **Fechada.**
- **Tabela de aceite da §9 da `99_decisao-p1a31.md`** = **8 criterios**.
  Dela, 5 estavam OK; os 3 restantes ("mesmo pacote/hash nos dois
  revisores", "zero CRITICAL/MAJOR", "suites verdes") dependiam da
  correcao e da nova revisao. **"Suites verdes" fechou** (342/342 em
  checkout limpo, §5). Os outros dois dependem justamente da revisao
  dupla que esta missao nao conseguiu obter — **permanecem abertos**.

A reconciliacao **substantiva** — cada achado da P1-A.3.1 contra a
disposicao dada pela P1-A.3.2 — esta na §1.4 e esta completa: 6 MAJOR
com correcao e teste, 1 MINOR superado pelos fatos (§4.2 da
`99_decisao-p1a31.md`), 1 achado fora dos seis registrado e nao
corrigido (`07_p1b/preflight_atual.py:172`).

Nao se afirma aqui que este seja o objeto que o ato chamou de "8x9": o
rotulo nao existe no acervo, e inventar-lhe um referente seria pior do
que registrar a ausencia.

## 2. Pacote — duas geracoes independentes, bytes e hash identicos

| Item | Valor |
|---|---|
| **SHA-256** | `87f415031aa1c7ee6464ac6c74f73b8508912350816fc6402fde6a8e435b87c2` |
| Bytes | **318.389** |
| Gerador | `06_p1a/evidencias/pacote_p1a33.py` (novo; ferramenta desta missao) |
| Alvo | `ac03f3a`; diff publicado e `30107bd..ac03f3a` — a correcao INTEIRA, nao so o segundo commit |

Duas geracoes em diretorios descartaveis **independentes**: mesmo
tamanho, mesmo SHA-256, e comparacao **byte a byte** sem diferenca.

**Ordem, normalizacao e exclusoes declaradas** (no docstring do gerador e
no proprio pacote): secoes em sequencia fixa; `ARQUIVOS_COMPLETOS` em
ordem literal; evidencias em `sorted()`; fonte unica sao os blobs (LF por
construcao); saida UTF-8. Nao entram timestamp, UUID, caminho absoluto,
valor de ambiente, credencial, lock, cache nem runtime; as evidencias
entram **somente como hashes**; usuario local (forma longa e 8.3) e
prefixo de caminho local sao redigidos.

### 2.1 Prova de ancoragem — executada ANTES do envio, e PASSOU

Foi este exato defeito que reprovou a P1-A.3.1 (§10.2: `c3b5c5…` da
arvore contra `e1f856e…` do commit). Cinco geracoes, **todas identicas**:

| Geracao | Condicao | SHA-256 |
|---|---|---|
| A | arvore de trabalho intacta | `87f41503…` |
| B | segundo diretorio descartavel, independente | `87f41503…` |
| C | **worktree destacada e limpa em `ac03f3a`** | `87f41503…` |
| D | **worktree destacada e limpa em `30107bd`** (checkout de OUTRO commit) | `87f41503…` |
| E | arvore de trabalho **deliberadamente mutada** | `87f41503…` — **inalterado** |

A geracao E mutou `06_p1a/tiers_declarados.json` — arquivo presente nas
**duas** listas do gerador —, e o git confirmou a arvore suja no
instante da geracao. O hash nao se moveu. A geracao D e a mais forte:
o pacote reproduz identico a partir de um checkout de commit
**diferente** do alvo, o que so e possivel porque toda leitura vem de
`git cat-file blob <ALVO>:<path>` e nao do disco.

Arquivo restaurado apos a prova; arvore limpa reconferida; worktrees
removidas e `worktree prune` executado.

## 3. As duas chamadas — uma por provedor, mesmos bytes, mesmo hash

Os **mesmos bytes** foram copiados para os dois descartaveis, sem
remontagem. As duas evidencias registram `pacote_sha256` identico:
`87f41503…`, 318.389 bytes.

| Campo | codex | kimi |
|---|---|---|
| Evidencia | `revisao-p1a33/codex-20260731T160049Z.json` | `revisao-p1a33/kimi-20260731T155932Z.json` |
| Canal | assinatura OAuth (ChatGPT Pro 5x) | assinatura OAuth (Allegretto) |
| Tier valido no instante | sim | sim |
| Enforcement | `--sandbox read-only --ephemeral` | restricao parcial + deteccao integral |
| Modelo efetivo observado | **`gpt-5.6-sol`** (banner do CLI) | **DESCONHECIDO** — nao exposto pelo CLI |
| returncode | 1 | 1 |
| Duracao | 5,7 s | 0,667 s |
| Chamada de modelo consumida | nenhuma resposta produzida | **nenhuma — nao houve chamada** |
| Custo variavel | 0 | 0 |
| Contencao violada | **nao** (0 mutacoes fora do descartavel, 2842 arquivos no manifesto) | **nao** (0 mutacoes, 2841 arquivos) |
| Lease reverificado antes de persistir | sim, fence 1 | sim, fence 1 |
| **Veredito** | **inexistente** | **inexistente** |

Modelo efetivo registrado quando observavel; **desconhecido permanece
desconhecido** — o CLI do kimi nao expoe o modelo na saida de erro, e
nada foi inferido do `Default model` visto na descoberta.

### 3.1 Codex — limite de uso do ciclo

```
ERROR: You've hit your usage limit. Visit
https://chatgpt.com/codex/settings/usage to purchase more credits
or try again at Aug 5th, 2026 9:29 AM.
```

O CLI iniciou normalmente (`model: gpt-5.6-sol`, `provider: openai`,
`sandbox: read-only`, `approval: never`, `reasoning effort: high`) e o
servico recusou por limite de uso. As duas saidas oferecidas —
**comprar creditos** ou **esperar 5 de agosto** — estao ambas fora do
alcance desta missao: a primeira e via paga, proibida; a segunda excede
qualquer janela desta missao e depende do proprietario.

## 4. ACHADO MAJOR DESTA MISSAO — a correcao do MAJOR #3 e inexecutavel

**`06_p1a/evidencias/contencao.py`, `argv_kimi`.** O comando montado
pela correcao **nao roda**:

```
error: Cannot combine --prompt with --plan.
```

`argv_kimi` devolve `[exe, "--plan", "--skills-dir", <dir>, "-p", <prompt>]`.
O kimi 0.30.0 trata `--plan` e `--prompt/-p` como **mutuamente
exclusivos** e aborta na validacao de argumentos, antes de qualquer
rede. Consequencia direta: **desde a P1-A.3.2, o kimi nao pode mais ser
chamado por esta ferramenta em modo headless** — o unico modo que a
missao usa.

**Por que os testes nao pegaram.** Os dois testes de argv da
`ContencaoDoReviewer` medem a **forma da lista**, nunca a execucao:

- `test_argv_do_kimi_usa_a_restricao_que_o_cli_oferece` — verifica que
  `--plan` e `--skills-dir` estao presentes e que os dois ultimos
  elementos sao `["-p", "revise"]`;
- `test_argv_do_kimi_nunca_auto_aprova_ferramenta` — verifica ausencia
  de `-y/--yolo/--auto`.

E o teste fim a fim **substitui o CLI inteiro** por
`sys.executable -c <corpo>` via `mock.patch.object(modulo, "COMANDOS", …)`:
o argv real do kimi nunca e executado por teste algum.

Isto e **exatamente a classe de defeito que a P1-A.3.1 nomeou no achado
#6**: um guarda que compara uma lista em vez de medir comportamento. A
P1-A.3.2 corrigiu essa falha no sentinela anti-P2 e a **reintroduziu na
propria correcao do MAJOR #3** — a `kimi --help` foi medida (as flags
existem, isoladamente), mas a **combinacao** nunca foi exercida.

**Efeito sobre o fechamento do MAJOR #3:** a metade "restricao real pelo
CLI" nao esta em vigor — ela impede toda a corrida. A metade "deteccao
integral por manifesto" continua valida e foi exercida nesta missao
(2841 arquivos, zero mutacao). O MAJOR #3 **nao pode ser dado por
fechado**.

**Nao foi corrigido**, por forca do ato: achado que exige alteracao de
codigo nao se conserta dentro desta missao. Fica como item **ADJUST** da
proxima.

Registro de honestidade: nao se tentou contornar o defeito chamando o
kimi com argumentos diferentes dos que o codigo produz. Uma revisao
obtida por um comando que o repositorio nao implementa nao seria revisao
**deste** estado — seria uma afirmacao falsa dentro da evidencia.

## 5. Suites — medidas, nunca como meta

| Suite | Resultado (arquivos staged, antes do commit) |
|---|---|
| P0 | **100/100 OK** |
| P1-A | **342/342 OK** |
| Prova central | **18/18 OK** (20 eventos) |

Os dois arquivos `.py` novos desta missao sob `06_p1a/` **nao acionaram
o sentinela anti-P2** — confirmacao independente de que o sentinela
reescrito mede comportamento e nao mais lista de caminhos, que era
justamente o achado #6. Sob o sentinela antigo, esta missao teria aberto
vermelha como a P1-A.3.2 abriu.

O JSON da prova central contem UUIDs por corrida; o arquivo versionado
foi restaurado apos a reexecucao — a arvore permaneceu limpa. A contagem
e **medida**, nunca meta.

## 6. Fronteira, custo e ambiente

| Item | Estado verificado |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | 4 caminhos novos (§7) mais `locks/` (runtime, gitignorado) |
| Escritas fora do repositorio | duas, ambas exigidas: a copia datada (irma, nao dentro) e os descartaveis das provas, no temp da sessao — descartados |
| Escrita em `lucaX` ou `LucaX Enterprise OS` | **nenhuma** |
| Chamadas de modelo com resposta | **0** |
| Custo variavel | **0** — nenhum PAYG, top-up, extra usage ou fallback pago |
| Creditos comprados | **nenhum**, embora o codex os tenha oferecido explicitamente |
| Sondas diagnosticas (sem chamada de modelo) | `kimi --help`, `kimi provider --help`, `kimi provider list`, `codex --version`, `kimi --version` |
| Tier renovado automaticamente | nao |
| Tag, remoto ou push | nenhum |
| `NVIDIA_API_KEY` global/HKCU | **intocada** (presente em `HKCU:\Environment`; removida apenas do env-filho pela capsula) |
| Env removidas do filho | `NVIDIA_API_KEY`, `VSCODE_GIT_IPC_AUTH_TOKEN` |

Todo comando foi ancorado por caminho absoluto ou `git -C`. O cwd da
sessao **retornou sozinho** para fora do alvo duas vezes durante a
missao (observado apos as suites) — a ancoragem absoluta impediu que
qualquer comando aterrissasse no lugar errado.

## 7. Micro-commit probatorio

Escritas autorizadas pelo ato: evidencias, atestado e micro-commit
probatorio. **Nenhum atestado de aprovacao foi emitido** — a condicao
(dois vereditos verdes) nao foi satisfeita. O **registro**, ao contrario,
existe independentemente do veredito, e o ato manda commita-lo
"qualquer que seja o veredito, inclusive ADJUST e BLOCKED".

Quatro caminhos, todos **novos**:

```
06_p1a/99_decisao-p1a33.md                (este registro)
06_p1a/evidencias/pacote_p1a33.py         (gerador do pacote)
06_p1a/evidencias/revisao_p1a33.py        (runner da revisao)
06_p1a/evidencias/revisao-p1a33/          (2 evidencias das chamadas)
```

Staging explicito caminho a caminho (**sem `git add -A`**); zero arquivo
rastreado modificado ou removido; zero alteracao de codigo, teste,
politica ou documento historico; sem runtime, sem segredo, sem tag, sem
remoto, sem push. O identificador do commit e as provas pos-commit estao
em `locks/registro-commit-p1a33.txt` — este documento e conteudo do
proprio commit e nao pode conter o hash que o inclui.

### 7.1 Preservacao de bytes — o portao fraco e o portao forte

O portao `git hash-object` vs `--no-filters` aprovou os seis caminhos.
**Ele e insuficiente**: testa a idempotencia do lado *clean* (LF que
entra continua LF), nao o round-trip. O git avisou, no proprio staging,
`LF will be replaced by CRLF the next time Git touches it` em tres
caminhos — sinal que o portao nao capta.

Aplicado o teste forte da §10.0 da `99_decisao-p1a31.md` — recheckout do
indice por `git checkout-index` e comparacao byte a byte:

| Caminho | disco | recheckout | round-trip |
|---|---|---|---|
| `99_decisao-p1a33.md` | 19.573 B | 19.964 B | **nao** |
| `evidencias/pacote_p1a33.py` | 17.620 B | 17.956 B | **nao** |
| `evidencias/revisao_p1a33.py` | 10.649 B | 10.885 B | **nao** |
| `evidencias/revisao-p1a33/.gitattributes` | 8 B | 8 B | sim |
| `evidencias/revisao-p1a33/codex-…json` | 3.772 B | 3.772 B | sim |
| `evidencias/revisao-p1a33/kimi-…json` | 2.183 B | 2.183 B | sim |

**Extensao de escopo declarada, uma so:** foi criado
`06_p1a/evidencias/revisao-p1a33/.gitattributes` (conteudo `* -text`),
escopado ao diretorio de evidencias desta missao, espelhando o
precedente do `revisao-p1a31/`. Sem ele, as duas evidencias das chamadas
**nao** preservavam bytes. `core.autocrlf` permanece `true`, inalterado;
nenhum `.gitattributes` da raiz foi criado.

**Os tres caminhos restantes NAO receberam `-text`, e a escolha e
deliberada.** Faze-lo exigiria editar `06_p1a/.gitattributes`, que hoje
e **arquivo rastreado** — a P1-A.3.1 pode cria-lo no mesmo commit, esta
missao teria de modifica-lo. Em vez disso, **todo hash publicado por
esta missao e do blob**, reproduzivel por qualquer terceiro com
`git cat-file blob <commit>:<caminho>`. Essa e a forma correta depois do
MAJOR #5: o `-text` era contorno para um gerador que lia o disco, e esse
gerador foi corrigido. Nenhum hash de bytes-de-disco e publicado, de modo
que a divergencia de round-trip nao torna afirmacao alguma irreproduzivel
— ela fica **registrada**, nao escondida.

## 8. O que a proxima missao precisa

1. **Quota, pelo proprietario, nos dois provedores.** O codex so
   restabelece em **5 de agosto de 2026, 09:29** por decurso de ciclo, ou
   antes disso por ato do proprietario. A do kimi permanece **nao
   medida** — e so sera mensuravel depois do item 2.
2. **Corrigir `contencao.argv_kimi` (§4) — item ADJUST.** `--plan` e
   `-p` sao mutuamente exclusivos no kimi 0.30.0. E o teste que
   acompanhar a correcao precisa **exercer o CLI real**, ainda que so
   para validar argumentos: teste de forma de lista foi exatamente o que
   deixou este defeito passar.
3. **Estender a licao do achado #6 aos proprios controles.** O achado #6
   valeu para o sentinela anti-P2; a §4 mostra que a mesma classe de
   defeito sobreviveu dentro da correcao do MAJOR #3. Todo guarda que
   afirma restringir um processo externo deveria ser exercido contra o
   processo externo, nao contra uma lista.
4. **Reaproveitar o pacote `87f41503…`.** Ele e funcao de
   `30107bd..ac03f3a` e de mais nada — provado por cinco geracoes,
   inclusive de checkouts limpos de dois commits distintos. O
   micro-commit desta missao **nao move um byte dele**, pelo mesmo
   argumento da §10.1 da `99_decisao-p1a31.md`: as tres fontes do
   gerador sao listas literais e um diff de par historico fixo, e nenhum
   dos 4 caminhos novos entra em qualquer delas. A proxima missao pode
   enviar **os mesmos bytes** sem regerar.
5. **P1-B-02 permanece FECHADA** ate `READY-FOR-P1-B-RETRY` emitido
   sobre um HEAD efetivamente revisado por dois providers com zero
   CRITICAL/MAJOR. Esta missao nao produziu veredito algum: nao houve
   aprovacao **nem** reprovacao do estado corrigido.

## 9. Alcance — o que esta missao estabelece e o que NAO estabelece

O ato manda registrar o **alcance**. Sem ele, um leitor futuro tende a
ler "suites verdes + ancoragem provada" como se fosse aprovacao. Nao e.

### 9.1 Estabelecido — medido, e independente de qualquer revisor

Estes fatos nao dependem de veredito e sobrevivem a esta missao:

| Fato | Como foi estabelecido | Reproduzivel por terceiro? |
|---|---|---|
| O pacote e funcao dos commits, nao do checkout | 5 geracoes identicas, incluindo worktree limpa em **outro** commit e arvore deliberadamente mutada | sim — `git cat-file blob` + o gerador |
| As suites passam no HEAD revisado e no HEAD desta missao | 100/100, 342/342, 18/18 em checkout limpo | sim |
| O sentinela anti-P2 mede comportamento, nao lista | dois `.py` novos sob `06_p1a` **nao** o acionaram; sob o sentinela antigo teriam acionado | sim |
| A metade "deteccao" do MAJOR #3 funciona | exercida nas duas corridas: manifesto de 2.841 e 2.842 arquivos, zero mutacao fora do descartavel | sim |
| A verificacao de lease do MAJOR #4 funciona | exercida de verdade antes das duas persistencias, com fence conferido | sim |
| **A metade "restricao pelo CLI" do MAJOR #3 esta QUEBRADA** | o CLI recusou o argv que o codigo monta (§4) | sim — basta invocar |

### 9.2 NAO estabelecido — e nao se presume

- **Nenhum dos seis MAJOR esta fechado.** Fechamento, no sentido do ato,
  e pronunciamento de revisor independente. Nenhum revisor falou. Os
  cinco MAJOR restantes (#1, #2, #4, #5, #6) tem correcao e teste de
  falha registrados — o que os torna **candidatos a fechamento**, nunca
  fechados.
- **O estado corrigido nao foi aprovado nem reprovado.** A ausencia de
  reprovacao nao e aprovacao, e a ausencia de veredito nao e ressalva.
- **A quota do kimi nao foi medida.** Nao se afirma disponivel nem
  esgotada; a chamada morreu antes da rede.
- **Nada foi estabelecido sobre autorizacao de P1-B em modo sombra.** O
  eixo (12) das perguntas nunca foi respondido por ninguem.
- **O alcance do proprio achado da §4 e limitado ao que foi exercido:**
  o kimi recusa `--plan` junto com `-p` na versao 0.30.0 instalada.
  Nao se afirma nada sobre outras versoes do CLI.

### 9.3 A assimetria entre abrir e fechar um defeito

Vale registrar, porque governa a leitura do achado da §4: **abrir** um
defeito e **fechar** um defeito nao exigem a mesma autoridade.

Abrir e afirmacao de existencia, e um contraexemplo basta: o CLI recusou
o comando, e isso e fato verificavel por quem repetir a invocacao — nao
importa quem descobriu. Por isso o achado da §4 vale integralmente
embora tenha sido produzido pela propria missao.

Fechar e afirmacao universal — "nao ha mais defeito aqui" — e nenhuma
execucao a demonstra. Por isso o ato exige revisor independente e por
isso *"quem corrigiu nao certifica"*. Esta missao, que nao corrigiu
nada, pode abrir; nao pode fechar.

### 9.4 Por que BLOCKED encerra, com o portao em aberto

O portao ("zero CRITICAL e zero MAJOR nos **dois vereditos**") e a
condicao de `READY-FOR-P1-B-RETRY`, nao condicao de encerrar. Ele e
inalcancavel quando nao existe veredito — e e exatamente para esse caso
que o ato oferece `BLOCKED` no conjunto de decisao e manda *"commitar o
registro qualquer que seja o veredito, inclusive ADJUST e BLOCKED"*.

Exigir o portao fechado antes de encerrar tornaria `BLOCKED`
inalcancavel e obrigaria a missao a fabricar um veredito para poder
terminar — o oposto do que o ato protege. O portao fica **em aberto e
registrado como tal**, que e a unica forma honesta de deixa-lo.
