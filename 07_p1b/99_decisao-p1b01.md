---
id: SSC-DEC-P1B01
titulo: Registro e Decisao da Missao SSC+ P1-B.01 — entrada do runner da P1-B pela capsula ratificada
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-01
---

# Registro e Decisao — Missao SSC+ P1-B.01

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: `01_parada-preflight.md` e
> `02_diagnostico-parada-p1b00.md` permanecem intactos, inclusive o
> veredito BLOCKED de 30/07 — que continua verdadeiro sobre o runner que
> o produziu. Nenhum provider foi invocado para tarefa produtiva:
> **zero chamada de modelo, custo variavel zero**. A P1-B nao foi
> executada, a P2 nao foi iniciada, nenhum ato foi emitido e nenhuma
> politica foi alterada.

## 0. Medicao de partida

| Item | Medido |
|---|---|
| HEAD na abertura | `c503b314afdaffccc42056b4058761ab2147c763` |
| `git status --porcelain` na abertura | vazio (arvore limpa) |
| Suite `05_p0/tests` na abertura | **100/100 OK** |
| Suite `06_p1a/tests` na abertura | **401/401 OK** |
| Escritor unico | `p1b01-ops`, fence **1**, pid 109072 |
| HEAD no fechamento | `5d07c60` + commit de evidencia/registro |

Lease de **nome proprio desta missao**, adquirido ANTES da primeira
escrita (`06_p1a/evidencias/renovador_lock.py p1b01-ops`), renovado a
cada 30 s durante toda a missao. Nenhum `.lease` ou `.fence` de missao
anterior foi reusado; nenhum lock foi removido a mao.

**ACHADO 4.1, confirmado de novo.** Rodar `06_p1a/tests` grava
`locks/p1-ops.lease` sobre o `locks/` REAL do repositorio
(`test_estabilizacao_p1a1.py:358-360`). As linhas
`escritor unico: kernel vivo ja detem o lock da sessao ... p1-ops.lock`
aparecem em toda corrida da suite desta missao: sao artefato da propria
suite, nao sessao concorrente. O sinal foi derrotado pelo protocolo
(lease de nome distinto), nunca por remocao de lock.

## 1. Trechos truncados na transmissao — medidos no repositorio

O bloco chegou com numeros de linha de uma versao anterior de
`07_p1b/preflight_atual.py` (o arquivo encolheu nas correcoes 7 e 8 da
P1-A.3.5). **Seguiu-se o repositorio**; as divergencias ficam
registradas:

| Afirmado na transmissao | Medido no repositorio (HEAD `c503b31`) |
|---|---|
| `preflight_atual.py:130` audita `dict(os.environ)` | **`:116`** (`auditar_ambiente`) |
| `preflight_atual.py:135` env por provedor | **`:121`** (`env=dict(os.environ)`) |
| sanitizacao so em um campo de relatorio `:151` | **`:144-145`** (`env_sanitizado_remove_nomes`) |
| `preflight_atual.py:171-172` filtra so ELIGIBLE | **`:165-167`** |
| chamada em `:133-136` omite `tiers_declarados` | **`:119-122`** |
| `sensor_subprocess:9` | docstring em **`adaptadores.py:8`**; o alvo real e **`adaptadores.py:86`** (`ambiente = ambiente_sanitizado(env)` dentro de `sensor_subprocess`, definido em `:79`) |
| `exigir_capsula_limpa` (linha nao informada) | **`capsula.py:71`** |
| `origem_credencial="nao-sondada"` (linha nao informada) | **`pipeline.py:154`** (agora `:161-162`) |

Confirmados **sem divergencia**: `pipeline.py:31` (enum),
`pipeline.py:45-46` (defaults da dataclass), `pipeline.py:97`
(`tiers_declarados=None`), `pipeline.py:126-127` (`env_outras`),
`pipeline.py:138-140` (bloqueio imediato), `capsula.py:3-6` (decisao
sobre o ambiente global), `economia.py:53` (`nvidia` em
`_FAMILIAS_PROVEDOR`), `test_capsula_p1a2.py:128-137` (NVIDIA dentro da
capsula = BLOCKED), `test_estabilizacao_p1a1.py:358-360` (o lock real).

## 2. O que foi mudado, linha a linha

Cinco commits, um por ordem, **jamais um commit unico**. Suites rodadas
com os arquivos **staged** antes de cada commit.

### Ordem 1 — `ecb1ad4` — o runner opera dentro da capsula

`07_p1b/preflight_atual.py`:

- **cabecalho**: passa a declarar o entry point obrigatorio
  (`python 06_p1a/capsula.py python 07_p1b/preflight_atual.py`) e o
  paragrafo do lease deixa de citar `p1b-ops` fixo;
- **`import`**: `from capsula import ambiente_capsula,
  exigir_capsula_limpa, verificar_capsula` — a capsula ratificada da
  P1-A.2 passa a ser importada por este runner pela primeira vez;
- **`_SESSAO_LOCK`**: `"p1b-ops"` -> `os.environ.get("SSC_LOCK_SESSAO",
  "p1b-ops")`, para que a condicao operativa do ACHADO 4 (lease de nome
  proprio por missao) seja exequivel a partir daqui;
- **`main()` primeira linha util**: `exigir_capsula_limpa()`;
- **`main()`**: `ambiente = ambiente_capsula(os.environ)`, usado em
  `auditar_ambiente(ambiente)` (antes `dict(os.environ)`) e em `env=` de
  cada `executar_preflight` (antes `dict(os.environ)`);
- **documento**: novo bloco `capsula` (mecanismo + violacoes por NOME) e
  `env_sanitizado_remove_nomes` medido sobre o ambiente da capsula.

### Ordem 2 — `64837da` — o sumario distingue os quatro resultados

- `from preflight.pipeline import RESULTADOS, executar_preflight`;
- o filtro `if r["resultado"] == "ELIGIBLE"` + `print("ELIGIBLE: ...")`
  vira particao pelos **quatro** resultados, impressos **sempre**,
  inclusive vazios;
- ramo `FORA-DO-ENUM` e linha `total classificado: N+M de T`;
- coluna de resultado `:10s` -> `:15s` e sufixo `sombra=<tier>`
  (`SHADOW_ELIGIBLE` tem 15 caracteres).

### Ordem 3 — `27da226` — campo nao observado nao sai como observacao

`06_p1a/preflight/pipeline.py:139-140` (unico ponto):

```
-        return relatorio("BLOCKED", bloqueio_imediato + env_relacionadas)
+        return relatorio("BLOCKED", bloqueio_imediato + env_relacionadas,
+                         origem_credencial="nao-sondada",
+                         quota="nao-sondada")
```

### Ordem 4 — `049524a` — as declaracoes de tier chegam ao pipeline

- **novo** `06_p1a/leitor_tiers.py`: leitor UNICO
  (`carregar_tiers(caminho=None)`), fail-closed, fora do pacote
  `preflight/` pela mesma razao de `leitores_config.py` (o pacote e
  livre de I/O e `test_isolamento.py` reprova `open(` nele);
- `06_p1a/preflight_capsula.py`: `_carregar_tiers` e `_TIERS_JSON`
  removidos; `_carregar_tiers = leitor_tiers.carregar_tiers`;
- `07_p1b/preflight_atual.py`: `carregar_tiers =
  leitor_tiers.carregar_tiers`, `tiers = carregar_tiers()` em `main()`,
  `tiers_declarados=tiers` na chamada ao pipeline, e bloco
  `emenda_p1a3_item_1` na evidencia.

### Ordem 5 — `5d07c60` — a contagem de sondas passa a ser medida

- `_ContadorDeSondas` envolve o sensor real por provedor; a evidencia
  ganha `sondas_medidas` e o sumario ganha `sondas=N` por provedor.

### Mecanismo da capsula: qual foi usado, e por que

**Os dois, deliberadamente** — e a evidencia registra isso em
`capsula.mecanismo`:

1. **entrada por `iniciar_em_capsula`** (`python 06_p1a/capsula.py
   python 07_p1b/preflight_atual.py`): o ambiente-filho e gerado ANTES
   de o processo existir. E o unico mecanismo que impede a credencial de
   estar visivel em algum instante do processo;
2. **`exigir_capsula_limpa()` no processo**: sozinho, o item 1 e uma
   convencao de invocacao — nada obriga o operador a usar o entry point.
   O guarda transforma "esqueceu do entry point" de degradacao silenciosa
   em PARADA;
3. **`ambiente_capsula()` em processo**: com 1 e 2, o `os.environ` ja e
   comprovadamente limpo e esta derivacao e identidade. Ela existe para
   que a propriedade (a) seja verdadeira **por construcao** e testavel
   isoladamente do portao — sem ela, a unica prova de (a) seria a
   confianca em (2), e o acervo ja tem tres achados sobre guardas que
   valiam so por confianca.

**Copia do leitor de ambiente — verificado ANTES de alterar**, como a
ordem exige. Nao havia copia: os canonicos sao `capsula.ambiente_capsula`
(`capsula.py:52`) e `economia.ambiente_sanitizado`
(`economia.py:213`). O defeito era **ausencia de chamada**, nao
divergencia de copia — diferente do leitor de config, que tinha DUAS
implementacoes. Ja o **leitor de tiers** tinha uma implementacao no
runner da P1-A e a ordem 4 ia criar a segunda: por isso ele foi
extraido para `leitor_tiers.py` em vez de copiado. Dois testes amarram
os vinculos (`assertIs` contra `capsula` e contra `leitor_tiers`), de
modo que uma copia local nao possa reaparecer sem reprovar.

## 3. A corrida — o que foi MEDIDO

Duas corridas reais **dentro da capsula**, com lease `p1b01-ops` vivo e
fence 1 verificado imediatamente antes de cada persistencia:

- `07_p1b/evidencias/preflight-20260801T221207Z.json` — quatro ordens
  aplicadas, sem contagem de sondas;
- `07_p1b/evidencias/preflight-20260801T221451Z.json` — **corrida de
  referencia**, com a contagem medida.

| provedor | resultado | sondas (MEDIDAS) | erro observado |
|---|---|---|---|
| codex | BLOCKED | **2** | `P1A-DECLARACAO-EXPIRADA` (tier `ChatGPT Pro 5x`, declarado 2026-07-31T01:31:00Z) |
| claude | SUPERVISED | **2** | — |
| kimi | BLOCKED | **2** | `P1A-DECLARACAO-EXPIRADA` (tier `Allegretto`, declarado 2026-07-31T01:31:00Z) |
| google | SUPERVISED | **0** | — |
| grok | SUPERVISED | **0** | — |

Outros campos medidos na corrida de referencia: `custo_variavel: 0`,
`chamadas_de_modelo: 0`, `violacoes_ambiente_nomes: []`,
`capsula.violacoes_no_env_do_processo: []`,
`capsula.violacoes_no_env_classificado: []`, versao observada em codex
(`0.145.0`), claude (`2.1.220`) e kimi (`0.30.0`), `plano: "max"`
observado somente em claude, `quota: "desconhecida"` nos cinco.

**A capsula filtrou algo de verdade nesta estacao.** Medido fora da
capsula, no processo pai: **1** nome reprovado por `_nome_payg` entre 87
variaveis (86 dentro da capsula), e esse mesmo nome produz **1 violacao
de provedor** em `auditar_ambiente`. Medido provedor a provedor, fora da
capsula esse nome cairia em `env_outras` para **os cinco** — bloqueio
imediato dos cinco. Dentro da capsula: **zero**. O portao nao passou em
branco por falta de material.

**Tier vencido reportado como esta.** As declaracoes em disco sao de
2026-07-31T01:31:00Z com validade de 24 h, vencidas na data da corrida.
Nenhuma foi renovada, editada ou silenciada — renovar e ato do
proprietario. Elas atravessam o leitor, chegam ao pipeline e saem como
`DeclaracaoExpirada` no relatorio.

## 4. O que a corrida ESTABELECE

1. O runner da P1-B executa **dentro da capsula ratificada** e o
   ambiente que o pipeline audita e classifica e o da capsula: nenhum
   nome reprovado por `_nome_payg` chegou a `env_outras` — medido, com
   material real para filtrar.
2. Executar o runner **fora** da capsula aborta com `ViolacaoCapsula`
   antes do lease, antes da primeira sonda e antes de qualquer escrita —
   exercido por teste, inclusive o discriminador de ordem (sem lease
   nenhum, o portao da capsula fala antes do escritor unico).
3. O sumario distingue os quatro resultados do enum. A leitura de 30/07
   ("`ELIGIBLE: []`" = nenhum provedor passou) nao volta a ocorrer:
   hoje se le `SUPERVISED: ['claude', 'google', 'grok']` e
   `BLOCKED: ['codex', 'kimi']`, com o total conferido na propria saida.
4. No caminho de bloqueio imediato, `origem_credencial` e `quota` saem
   como `nao-sondada` — o relatorio deixa de afirmar credencial que
   ninguem olhou.
5. A trilha SHADOW_ELIGIBLE ficou **alcancavel** a partir deste runner:
   as declaracoes sao carregadas e repassadas, e o teste de ponta a
   ponta produz `SHADOW_ELIGIBLE` com declaracao valida (e `BLOCKED` por
   `P1A-PLANO-DESCONHECIDO` sem ela — o comportamento anterior do
   runner).
6. **codex e kimi tem OAuth de assinatura observado** (`versao` medida,
   `origem_credencial: subscription-oauth`) e plano **nao observavel no
   CLI**: o unico obstaculo medido hoje e a validade da declaracao.
7. O escritor unico foi verificado na abertura E imediatamente antes de
   cada persistencia, com o mesmo fence (1) — o conserto do MAJOR #4
   vale para esta copia.

## 5. O que a corrida NAO estabelece

1. **Nao reverte o veredito BLOCKED de 30/07.** Aquele registro descreve
   fielmente o que o runner daquela data media: com o ambiente CRU
   auditado, os cinco eram BLOCKED por `P1A-PAYG-ENV` — e a medicao de
   hoje reproduz exatamente esse mecanismo fora da capsula. Mudou o
   ambiente auditado, nao a realidade da estacao.
2. **Nao estabelece elegibilidade de ninguem para trabalho.** Nenhum
   provedor saiu ELIGIBLE nem SHADOW_ELIGIBLE. SUPERVISED e teto de
   especificacao, nao autorizacao.
3. **Nao estabelece nada sobre google e grok por observacao.** Zero
   sondas medidas: o SUPERVISED deles e classificacao estatica da emenda
   P1-A.3 item 5. Nao ha versao, login, plano ou modelo observados —
   `origem_credencial: nao-sondada` diz isso no proprio relatorio.
4. **Nao estabelece catalogo de modelos de ninguem.** `modelos: []` nos
   cinco: claude tem descoberta desativada por especificacao (emenda
   item 4), codex e kimi bloquearam antes da descoberta, google e grok
   nao sondam.
5. **Nao estabelece franquia disponivel.** `quota: "desconhecida"` nos
   cinco, por ausencia de sinal positivo. Nao convertido por inferencia.
6. **Nao estabelece que codex/kimi seriam SHADOW_ELIGIBLE hoje.** Isso
   exigiria declaracao valida do proprietario, que nao existe — e
   produzi-la nao e ato do runner nem desta missao.
7. **Nao estabelece cobertura da P0.** As lacunas registradas na
   P1-A.3.5 seguem como estavam; esta missao nao as tocou.

## 6. O que segue INDETERMINADO

1. **`quota` no caminho de zero sondas.** Depois da ordem 3, o bloqueio
   imediato reporta `quota: "nao-sondada"`, mas o caminho de zero sondas
   (`pipeline.py:163-164`) continua com `"desconhecida"` — embora ali
   tambem nada tenha sido sondado. Mudar contradiria teste ratificado
   (`test_pipeline.py:36`, que exige `"desconhecida"` para os cinco no
   caminho verde) e esta fora desta ordem. **Assimetria registrada, nao
   corrigida por conta propria.** Decisao do proprietario.
2. **O laco de classificacao do runner da P1-B.** `main()` mantem o
   proprio laco sobre `frota_real()`, com a mesma forma de
   `preflight_capsula.classificar_frota`. Unifica-los quebraria a
   garantia de custo zero de `test_p1b_lease_p1a35.py`, que substitui
   `executar_preflight` NO MODULO da P1-B — sem atualizar o teste, a
   suite passaria a invocar os CLIs reais. Fora do escopo ordenado;
   **registrado como divergencia medida**, com o remedio especificado:
   extrair a classificacao para modulo partilhado E reapontar o mock.
3. **O runner da P1-A audita `dict(os.environ)` cru**
   (`preflight_capsula.py:161`), verdadeiro apenas **pelo guarda**
   `exigir_capsula_limpa` (`:156`), nao por construcao — a assimetria
   que a ordem 1(a) fechou do lado da P1-B. Codigo ratificado, fora do
   escopo; registrado.
4. **Configuracao do grok em SQLite** e limite ja declarado em
   `leitores_config.py`: nao e alcancada pela leitura atual. Segue
   INDETERMINADO, como estava.
5. **Se ha outros ambientes de operacao** (outra estacao, outro usuario)
   com nomes reprovados diferentes: medido apenas ESTA estacao, AGORA.

### Correcao aditiva a mensagem do commit `27da226`

Aquela mensagem cita o caminho vizinho de zero sondas como
`pipeline.py:161-162`. Medido apos a propria correcao, ele esta em
**`:163-164`** (a correcao acrescentou 12 linhas acima dele). O
historico de commits nao foi reescrito; a citacao correta e esta.

## 7. Regressao final

| Suite | Abertura | Fechamento |
|---|---|---|
| `05_p0/tests` | 100/100 OK | **100/100 OK** |
| `06_p1a/tests` | 401/401 OK | **424/424 OK** (401 + 23 novos) |

Testes novos por ordem, todos em `06_p1a/tests/test_p1b01_runner.py`
(mora na suite que efetivamente roda — `07_p1b/tests/` seria guarda que
ninguem executa, o defeito que estes testes corrigem):

| Ordem | Classe | Testes |
|---|---|---|
| 1 | `Ordem1CapsulaDoRunner` | 6 |
| 2 | `Ordem2SumarioDosQuatroResultados` | 4 |
| 3 | `Ordem3CampoNaoObservadoNoBloqueioImediato` | 4 |
| 4 | `Ordem4DeclaracoesDeTierNoRunner` | 6 |
| 5 | `Ordem5ContagemMedidaDeSondas` | 3 |

Reversoes vermelhas medidas: ordem 3 (campos removidos do `return` ->
7 reprovacoes) e ordem 4 (`tiers_declarados` omitido de novo ->
"tiers_declarados chegou como None"). Contraprova presente em cada
ordem, para que um guarda que reprovasse sempre nao passasse.

## 8. Proibicoes — conferencia

| Proibicao | Cumprimento |
|---|---|
| `HKCU\Environment` / variavel persistente do usuario | **Nao tocada.** Medido: 87 variaveis no pai antes e depois. A capsula filtra a COPIA. |
| `economia.py:53` / nvidia no escopo de bloqueio | **Nao emendado.** `test_capsula_p1a2.py:128-137` segue verde. |
| Registro historico | **Intacto.** `01_parada-preflight.md` e `02_diagnostico-parada-p1b00.md` nao foram abertos para escrita; as evidencias de 30/07 permanecem. |
| VALOR de variavel de ambiente | **Em lugar nenhum.** Codigo, teste, evidencia e log falam so de NOMES; os testes usam valor fabricado e um deles verifica que o contador nao guarda argv, ambiente nem saida. |
| INDETERMINADO por inferencia | **Nao convertido.** Secao 6. |
| Provider para tarefa produtiva / P1-B / P2 / ato / politica | **Nada disso.** Somente sondas de diagnostico; `chamadas_de_modelo: 0`. |
| Copia datada / store do harness | **Nenhuma criada.** |

## 9. Decisao

**CONCLUIDA.**

As cinco ordens foram executadas e medidas; nenhum item foi pulado.
Tres divergencias e uma assimetria ficam **registradas com remedio
especificado** (secao 6) em vez de corrigidas por conta propria: as
duas primeiras porque contradiriam teste ratificado ou quebrariam a
garantia de custo zero de uma suite existente, a terceira porque e
codigo ratificado fora do escopo ordenado.

> Quem classifica e corrige nao certifica. Esta sessao escreveu o codigo
> e os testes que o afirmam; a verificacao independente segue pendente.
