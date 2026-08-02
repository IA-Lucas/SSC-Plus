---
id: SSC-REM-P1A38
titulo: Remedicao dos guardas EXERCE sob a REGRA DURA — SSC+ P1-A.3.8, Fase 2
tipo: registro-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-02
---

# Remedicao sob a regra dura — SSC+ P1-A.3.8, Fase 2

> Laboratorio experimental. Nada aqui e norma. Registro **aditivo**:
> nenhum relatorio historico foi editado. **Quem corrige nao certifica**
> — este documento mede e registra; nao fecha nada. Lease `p1a38-ops`,
> fence **1**, adquirido antes da primeira escrita.

## 0. A regra dura, e o que ela pergunta

`EXERCE` exige **exercer o caso que OCORRE em operacao**, nao alcance de
linha. A pergunta de cada linha desta tabela e sempre a mesma:

> *o teste exerce o caminho que a operacao percorre, ou um vizinho dele?*

Cinco classes: **EXERCE PLENO**, **EXERCE PARCIAL**, **AFIRMA**,
**INALCANCAVEL**, **INDETERMINADO**.

## 1. O conjunto medido — e a correcao do numero do ato

O ato desta missao diz *"a varredura classificou 64 guardas como EXERCE
… a P1-A.3.7 remediu 26 … os demais seguem NAO REMEDIDOS"*, o que
sugere 38 restantes. **O numero medido e outro, e a diferenca esta
declarada em vez de silenciosa.**

| Passo | Medido | De onde sai |
|---|---|---|
| `EXERCE` na ABERTURA da varredura | **49** | Anexo A da `99_varredura-guardas-p1a35.md`, contado linha a linha |
| `EXERCE` no FECHAMENTO da P1-A.3.5 | **64** | §4 da `99_decisao-p1a35.md` |
| Promovidos pela P1-A.3.5 | **15** | 13 de SEM-TESTE (26→13), 1 de AFIRMA (9→8), 1 de INALCANCAVEL (1→0) |
| Guardas "tocados" pela P1-A.3.7 | **26** | §3.1 da `99_decisao-p1a37.md` |
| **Desses 26, quantos estao DENTRO dos 64** | **15** | os outros 11 nao eram `EXERCE`: 7 eram `SEM-TESTE` da P0, 2 sao guardas NOVOS (`leitores_config`, `escritor_repositorio`), 1 e `INDETERMINADO` (`P1A-58`), 1 e o rotulo de `enforcement_kimi`, que nao tem linha no Anexo A |
| **Restantes a remedir** | **49** | 64 − 15 |

Os 15 ja remedidos sob a regra dura pela P1-A.3.7: `P0-02`, `P0-05`,
`P0-15`, `P0-16`, `P0-17`, `P0-19`, `P0-21`, `P0-25`, `P0-26`,
`P1A-08`, `P1A-17`, `P1A-18`, `P1A-33`, `P1A-50`, `P1A-57`.

**Esta fase remede os 49 restantes.** Nenhum foi convertido por
inferencia: cada linha da §3 aponta o teste que a sustenta.

## 2. O instrumento — e o erro que ele cometeu, declarado

O alcance foi medido com `coverage` 7.15.2 sob **contexto dinamico por
funcao de teste**, o que da, para cada linha de guarda, **o conjunto
nominal de testes que a executam** — nao so "foi executada". Os pontos
sao ancorados por **AST** (nome da funcao/classe), nunca por numero de
linha: os numeros do Anexo A sao do HEAD `6a8c843` e ja se deslocaram.

**Erro cometido e corrigido no meio da medicao.** A primeira corrida da
suite P1-A nao incluiu `07_p1b` no `--source`, e `preflight_atual.py`
apareceu como *"arquivo com zero linha executada"* — o que teria
produzido dois achados falsos (`P1A-19` e `P1A-37`). A corrida foi
refeita com `07_p1b` incluido e os dois pontos aparecem alcancados.
Registrado porque instrumento que erra em silencio e pior que instrumento
que nao existe — e a propria P1-A.3.5 declarou um erro equivalente no seu.

O instrumento **nao foi acrescentado ao acervo**, pelo mesmo motivo da
P1-A.3.5: um `.py` novo sem teste seria mais um caso do achado C.

## 3. Distribuicao — antes e depois

| Classe | Antes (regra fraca) | Depois (regra dura) |
|---|---|---|
| EXERCE **PLENO** | — | **29** |
| EXERCE **PARCIAL** | — | **19** |
| **AFIRMA** | — | **1** |
| INALCANCAVEL | — | 0 |
| INDETERMINADO | — | 0 |
| `EXERCE` (indiferenciado) | **49** | — |
| **Total** | **49** | **49** |

**Vinte dos 49 nao sobrevivem inteiros a regra dura** — 19 parciais e
1 que so afirma. Nenhum dos 20 foi corrigido nesta fase, por ordem do
ato (*"NAO corrigir os que cairem: registrar com remedio especificado.
Saber o tamanho precede consertar"*).

### 3.1 Os quatro mecanismos que produzem os 20

A queda nao e aleatoria: quatro mecanismos respondem por todos os 20.

| Mecanismo | Quantos | Familia |
|---|---|---|
| **(a) primitiva exercida, ponto de chamada nao** — o teste chama a funcao diretamente; a ORDEM em que `main()` a usa nao e exercida | **9** | **N** (classe que a varredura de alcance nao media) |
| **(b) corpus derivado do proprio dado que o guarda protege** — iterar a lista para provar a lista | **2** | **F** (familia do MAJOR #3) |
| **(c) sem controle positivo / escopo menor que a propriedade afirmada** — o guarda passaria mesmo cego | **5** | **F** |
| **(d) propriedade afirmada depende de algo NAO exercido** (exclusao entre missoes do ACHADO 4; CLI nao invocado; chave nao confirmada) | **4** | **F** |

Contagem por familia do criterio de parada do `CLAUDE.md`: **F = 11**,
**N = 9**. Registrada porque a classificacao por familia e obrigatoria
neste repositorio — ainda que este seja registro de correcao e nao de
revisao independente, e portanto **nao afira** o criterio de parada.

## 4. Os 49, um por linha

Colheitas: **G-A** recusa · **G-B** filtragem/redacao · **G-C**
construcao restrita · **G-D** residente em teste · **G-E** deteccao.

### 4.1 P0 — 12 guardas

| id | ponto | classe | evidencia apontavel |
|---|---|---|---|
| P0-04 | `cas.resolver_contido` | **PLENO** | 2/2 ramos. `test_seguranca.py:81` cria **junction real** e o mesmo caminho atravessa `resolver_contido`, `ler_arquivo_contido` **e** `kernel.montar_contexto` — o ponto de chamada da operacao |
| P0-06 | `contratos.ContratoBase.from_dict` | **PLENO** | 2/2 ramos de guarda alcancados (`test_p0_evento_p1a37` le de disco campo a mais / a menos). O 3.o `raise` da classe e `NotImplementedError` de metodo abstrato, baldeado como METODO_ABSTRATO pela propria varredura — nao e guarda |
| P0-09 | `contratos.RetryEvent.validate` | **PLENO** | 2/2. `test_hardening.test_retry_fora_dos_limites_recusado`, objeto real |
| P0-10 | `contratos.WorkUnit.validate` | **PLENO** | 1/1. Teto de 4000 chars sobre WorkUnit real |
| P0-11 | `contratos._enum` | **PLENO** | 1/1, **7 testes**, todos via `validate()` de `Evento`/`FleetEntry` reais — nunca a primitiva a seco |
| P0-12 | `contratos._obrigatorio` | **PLENO** | 1/1, 3 testes via contratos reais |
| P0-14 | `estados.transitar` | **PLENO** | 1/1, 5 testes; 8 pares ilegais sobre a tabela real |
| P0-22 | `kernel._validar_id` | **PLENO** | 1/1, 2 testes; id que vira caminho |
| P0-23 | `kernel.escanear_segredos` | **PLENO** | 1/1, 4 testes; 4 amostras **+ contraprova**, e alcancado tambem pelo caminho de evento/contexto |
| P0-24 | `policy.PolicyGateway.verificar_orcamento` | **PLENO** | 1/1. `test_recuperacao.py:226` percorre **fim a fim**: exige escalonamento por `orcamento` e **zero attempt novo**. O contraexemplo classico — buscar `OrcamentoEstourado` nos testes devolve zero |
| P0-27 | `frota.ambiente_sanitizado` (G-B) | **PLENO** | 12 testes; corpus autoral, `os.environ` nao mutado. **E a lista que o alimenta passou a ser presa por outra camada nesta missao** (FASE 1.2) |
| P0-28 | `test_seguranca:119` zero escrita fora da raiz (G-D) | **PARCIAL** | **(c)** `os.walk` e real, mas percorre **so `base`** — o proprio pai do lab. Uma escrita FORA de `base` e invisivel, e a propriedade afirmada e "zero escrita externa". *Remedio:* instantaneo SHA-256 de um diretorio-testemunha antes/depois, o padrao que `test_isolamento.VarreduraNaoTocaOSistemaDeArquivos` ja usa |

### 4.2 P1-A e P1-B — 37 guardas

| id | ponto | classe | evidencia apontavel |
|---|---|---|---|
| P1A-01 | `capsula.ambiente_capsula` (G-A) | **PARCIAL** | **(c)** 1/1, mas o unico teste e `test_reauditoria_fail_closed`, que **encena a regressao do filtro**. Em operacao o ramo nunca dispara — mesma estrutura do terceiro ramo do `AdaptadorAssinatura`, medida na FASE 1.2. *Remedio:* prender a lista de proibidos por corpus de outra camada, como a FASE 1.2 fez para a P0 |
| P1A-02 | `capsula.exigir_capsula_limpa` | **PLENO** | 1/1, e alcancado por `test_p1b01_runner` rodando o **runner real**, com a assercao de que o portao vem ANTES do lease |
| P1A-03 | `capsula.iniciar_em_capsula` | **PLENO** | 1/1; `argv` em `str` recusado — o que sustenta `shell=False` |
| P1A-04 | `escritor.EscritorP1.verificar` | **PARCIAL** | **(d)** 1/1: lease vencido recusa escrita, com arquivos reais. Mas a propriedade AFIRMADA e escritor unico **entre missoes**, e essa e o ACHADO 4 — duas missoes de nomes diferentes trancam arquivos diferentes. *Remedio:* trocar para `escritor_repositorio`; entregue na P1-A.3.7 e **nao ligado**, por decisao do Fundador |
| P1A-06 | `pacote_p1a31.montar_pacote` | **PLENO** | 2/2. `git cat-file blob` **real**, disco mutado e ignorado; a constante e que e substituida, o guarda roda contra git de verdade |
| P1A-07 | `pacote_p1a33.montar_pacote` | **PLENO** | 3/3, incluindo o portao de ancestralidade que `pacote_p1a31` nao tem |
| P1A-09 | `revisao_p1a31._verificar_tier` | **PARCIAL** | **(a)** 2/2 ramos, JSON real em disco — porem `test_portao_tier_p1a35` chama `mod._verificar_tier("kimi")` **direto**. Que `main()` o chame ANTES de invocar provedor nao e exercido. *Remedio:* rodar `main()` com reviewer falso e declaracao vencida, exigindo **zero chamada** ao reviewer |
| P1A-10 | `revisao_p1a33._verificar_tier` | **PARCIAL** | **(a)** identico ao P1A-09, mesma suite, mesmo vizinho |
| P1A-11 | `adaptadores.AdaptadorPreflight` | **PLENO** | 2/2, 11 testes; e o caso que ocorre e exercido com **executavel inexistente real** (`test_capsula_p1a2`), nao so com sensor falso |
| P1A-12 | `economia.auditar_ambiente` (G-A) | **PARCIAL** | **(b)** 186 testes tocam a funcao, mas `test_economia:74` prova os "nomes conhecidos" **iterando a propria `CHAVES_PAYG_CONHECIDAS`**: encolher a lista encolhe o corpus. E a familia do MAJOR #3. *Remedio:* o da FASE 1.2 — corpus da outra camada (`frota.CHAVES_PROIBIDAS`), que esta missao ja tornou possivel |
| P1A-13 | `economia.auditar_config` | **PARCIAL** | **(d)** todos os ramos alcancados, mas a indeterminacao declarada na §3.4 da varredura segue viva: **nao esta confirmado** que `~/.gemini/settings.json` use `base_url`. O guarda pode estar auditando uma chave que a config real nao tem. *Remedio:* auditar a config do google e confirmar a chave |
| P1A-14 | `economia.auditar_status` | **PLENO** | 169 testes; grafias de auth/billing exercidas pelo pipeline fim a fim |
| P1A-15 | `pipeline.executar_preflight` | **PLENO** | 129 linhas com execucao, 160 testes; as nove construcoes tipadas alcancadas |
| P1A-19 | `preflight_atual._verificar_lock_vivo` (P1-B) | **PARCIAL** | **(d)** 1/1 alcancado por `test_p1b_lease_p1a35` (lease que some entre as duas leituras). Mesma limitacao do P1A-04: o lease e nomeado pelo proprio verificador |
| P1A-20 | `economia._nome_payg` (G-B) | **PLENO** | 87 testes; o corpus de `test_variantes_de_nome_sao_sanitizadas` e **autoral** (`api_key`, `apiKey`, `api-key`, `OpenAI_Api_Key`, `X_Custom_Secret_Key`), nao derivado da lista |
| P1A-21 | `economia._nome_payg_provedor` (G-B) | **PLENO** | 52 testes, com o **par** que separa os dois escopos: token local sanitiza **sem** bloquear; credencial de provedor sanitiza **E** bloqueia |
| P1A-22 | `economia.ambiente_sanitizado` (G-B) | **PLENO** | 32 testes; 11 variantes autorais, `os.environ` nao mutado, dict recebido nao mutado |
| P1A-23 | `capsula.verificar_capsula` (G-B) | **PLENO** | 37 testes; devolve **somente nomes**, medido |
| P1A-28 | `revisao_p1a31` `ambiente_capsula()` (G-B) | **PLENO** | `test_correcoes_p1a32:308` roda `main()` com ambiente minimo **real** |
| P1A-30 | `preflight_capsula` redacao (G-B) | **PARCIAL** | **(a)** e o pior caso da familia: o `_redigir` local **deixou de existir** (agora chama `contencao.redigir` na linha 203), e o ponto de chamada **nao esta em nenhum dos dois corpora** — nem em `RedacaoDosRunners.RUNNERS`, nem em `test_redacao_call_sites_p1a37.RUNNERS`. Sem cobertura comportamental **nem estrutural**. *Remedio:* incluir `preflight_capsula` nos dois |
| P1A-31 | `pacote_p1a31._redigir` (G-B) | **PARCIAL** | **(a)** so equivalencia de PRIMITIVA com a canonica (`RedacaoDosGeradores`); o ponto de chamada nao e varrido nem por AST |
| P1A-32 | `pacote_p1a33._redigir` (G-B) | **PARCIAL** | **(a)** identico ao P1A-31 |
| P1A-34 | `revisao_p1a3._redigir` (G-B) | **PARCIAL** | **(a)** primitiva comportamental + call-site **ESTRUTURAL (AST)**. O proprio `test_redacao_call_sites_p1a37` declara: *"estrutura nao e comportamento"* |
| P1A-35 | `revisao_p1a31._redigir` (G-B) | **PARCIAL** | **(a)** idem |
| P1A-36 | `revisao_p1a33._redigir` (G-B) | **PARCIAL** | **(a)** idem |
| P1A-37 | `preflight_atual._redigir` (P1-B, G-B) | **PARCIAL** | **(a)** primitiva coberta por teste proprio; o call-site **nao esta** em `test_redacao_call_sites_p1a37.RUNNERS` |
| P1A-38 | `contencao.argv_kimi` (G-C) | **PLENO** | `test_cli_real_p1a34` **invoca o CLI 0.30.0 real**, exige o marcador de argv aceito e prova custo zero pela propria saida do CLI. Limite declarado: vale para a versao instalada |
| P1A-43 | `revisao_p1a33.COMANDOS` (G-C) | **PARCIAL** | **(d)** so a entrada **kimi** e confrontada com o CLI; a entrada **codex nunca e invocada**. *Remedio:* o da frente P1 da P1-A.3.5 — sondar se o CLI do codex distingue erro pre e pos-parsing |
| P1A-45 | `ZeroPiiNosArtefatos` (G-D) | **PARCIAL** | **(c)** varre a arvore real, porem **sem controle positivo**: nao ha teste que plante PII e exija deteccao, nem guarda de "a varredura realmente le arquivos". O irmao `ZeroSegredoNosArtefatos` tem **os dois**. Um padrao quebrado passaria em silencio. *Remedio:* copiar as duas metades do irmao |
| P1A-46 | `ZeroSegredoNosArtefatos` (G-D) | **PLENO** | varredura real **+ controle positivo** (7 amostras por concatenacao) **+** guarda anti-teste-vazio |
| P1A-48 | `VarreduraNaoTocaOSistemaDeArquivos` (G-D) | **PLENO** | instantaneo SHA-256 **real** de `06_p1a` antes/depois da frota inteira |
| P1A-51 | `locks/` fora do Git (G-D) | **PARCIAL** | **(c)** le o `.gitignore` real e exige a substring `locks/`. Afirma o TEXTO da regra, nao o EFEITO: uma regra de desempate posterior no mesmo arquivo tornaria a linha inerte e o teste seguiria verde. *Remedio:* `git check-ignore -q locks/<arquivo>` |
| P1A-52 | `EspelhoDaPoliticaP0` (G-D) | **PLENO** | compara a `POLITICA_ECONOMICA` **importada** das duas camadas e exige imutabilidade — mirror entre camadas, que e o padrao que a FASE 1.2 replicou |
| P1A-53 | `ComandosSaoSomenteDiagnostico` (G-D) | **AFIRMA** | **(d)** itera `ESPECIFICACOES` e confere os verbos **declarados** contra uma lista de permitidos. **Nenhum CLI e invocado**, e o corpus e a propria declaracao. E a familia do MAJOR #3 na forma pura: afirma a propriedade lendo o rotulo. *Remedio:* o de `test_cli_real_p1a34`, aplicado aos demais provedores |
| P1A-54 | `CoberturaDasNoveFalhas` (G-D) | **PARCIAL** | **(c)** metade forte: os nove tipos de erro sao **objetos reais importados**, com codigo estavel e unico. Metade fraca: *"uma classe por falha"* confere **convencao de nome** (`Falha\d{2}\w+`), nao que a falha seja exercida. Uma classe vazia com o nome certo satisfaz. *Remedio:* exigir >= 1 metodo `test_*` por classe |
| P1A-55 | varredura le mesmo arquivos (G-D) | **PLENO** | meta-guarda com alcance real: exige > 10 arquivos e a presenca nominal de `economia.py` |
| P1A-56 | evidencias declaram custo zero (G-D) | **PLENO** | le os JSON **reais** gravados; `assertTrue(self.registros)` impede conjunto vazio |

## 5. Alcance — o que esta fase estabelece e o que NAO estabelece

**Estabelece.** Os 49 guardas restantes foram remedidos **um a um** sob
a regra dura, com o conjunto **nominal** de testes que alcanca cada
ponto medido por contexto dinamico, e o ponto ancorado por AST no HEAD
atual. A distribuicao mudou de 49 `EXERCE` indiferenciados para
**29 PLENO · 19 PARCIAL · 1 AFIRMA**. Cada queda tem mecanismo nomeado,
familia atribuida e remedio especificado.

**NAO estabelece.**

- **Nenhum dos 20 foi corrigido.** Por ordem do ato: saber o tamanho
  precede consertar.
- **PLENO nao e sinonimo de correto.** Exercer o caso que ocorre e
  condicao necessaria, nunca suficiente. Nada aqui afirma que a
  assercao ao redor da linha seja forte o bastante.
- **A classificacao e desta sessao, que tambem corrige.** Quem corrige
  nao certifica: os 49 nao "fecham" aqui, e um revisor independente
  pode reclassificar qualquer linha.
- **Os 15 remedidos pela P1-A.3.7 nao foram reabertos.** Esta fase os
  aceita como estao, o que e uma escolha declarada e nao uma medicao.
- **Os 22 guardas fora dos 64** (13 `SEM-TESTE` do fechamento da
  P1-A.3.5, 8 `AFIRMA`, 1 `INDETERMINADO`) **nao sao objeto desta
  fase** — o ato pediu os `EXERCE`.
