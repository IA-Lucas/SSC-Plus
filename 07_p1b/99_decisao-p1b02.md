---
id: SSC-DEC-P1B02
titulo: Registro da redeclaracao de tier do proprietario e da corrida de preflight sob capsula
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-01
---

# Registro — redeclaracao de tier e recorrida do preflight

> Laboratorio experimental. Nada aqui e norma. Registro **aditivo**: as
> evidencias anteriores, inclusive `preflight-20260801T221451Z.json` e o
> veredito BLOCKED de 30/07, permanecem intactas e continuam verdadeiras
> sobre as corridas que as produziram. Nenhum provider foi invocado para
> tarefa produtiva: **zero chamada de modelo, custo variavel zero**. A
> P1-B nao foi executada, a P2 nao foi iniciada, nenhuma politica foi
> alterada e as tres divergencias registradas na P1-B.01 seguem com
> remedio e sem missao.

## 0. Medicao de partida

| Item | Medido |
|---|---|
| HEAD na abertura | `e33400fa03550b300942a87f68052c07e8e40825` |
| `git status --porcelain` na abertura | vazio (arvore limpa) |
| Suite `05_p0/tests` na abertura | **100/100 OK** |
| Suite `06_p1a/tests` na abertura | **424/424 OK** |
| Escritor unico | `p1b02-ops`, fence **1**, pid 131096 |

Lease de **nome proprio desta missao**, adquirido por
`06_p1a/evidencias/renovador_lock.py p1b02-ops` e renovado a cada 30 s.
Nenhum `.lease`/`.fence` anterior foi reusado; nenhum lock foi removido.
Excecao declarada: a copia de seguranca datada de
`06_p1a/tiers_declarados.json` (item 1) foi gravada ANTES da aquisicao do
lease — e backup, nao evidencia, e precede por regra o ato de sobrescrita.

## 1. O ato do proprietario

O bloco recebido chegou com `[preencher o tier]` **literal** nas duas
linhas. A sessao NAO preencheu por conta propria: `preflight/sombra.py:8`
diz que a declaracao e ato humano, "nunca inferida pelo codigo", e o
proprio bloco proibia renovacao automatica. Os dois valores foram
confirmados pelo proprietario antes da escrita: `codex` = **ChatGPT Pro
5x**, `kimi` = **Allegretto**.

Copia de seguranca antes de sobrescrever:
`06_p1a/evidencias/backups/tiers_declarados-2026-08-01-pre-redeclaracao.json`.

Gravacao pelo mecanismo vigente, **sem alterar formato nem leitor**: o
unico campo modificado foi `declarado_em_utc` nas duas declaracoes,
`2026-07-31T01:31:00Z` -> `2026-08-01T23:54:41Z` (`git diff`: 2 linhas
inseridas, 2 removidas, um so arquivo). Nenhuma chave criada ou removida;
`validade_horas` permanece 24 e `declarado_por` permanece `proprietario`.

Verificacao pelo leitor canonico (`06_p1a/leitor_tiers.py` ->
`preflight.sombra`), antes de rodar o preflight:

| provedor | tier | `declaracao_valida` | expira em | portao comercial | teto |
|---|---|---|---|---|---|
| codex | `ChatGPT Pro 5x` | True | 2026-08-02T23:54:41Z | True | ELIGIBLE |
| kimi | `Allegretto` | True | 2026-08-02T23:54:41Z | True | ELIGIBLE |

## 2. A corrida

Comando unico, dentro da capsula, sob o lease desta missao:

```
SSC_LOCK_SESSAO=p1b02-ops python 06_p1a/capsula.py python 07_p1b/preflight_atual.py
```

Evidencia datada: `07_p1b/evidencias/preflight-20260801T235521Z.json`.

Por provedor, **medido nesta corrida** (nao esperado pela especificacao):

| provedor | resultado | sondas medidas | modelos | erro observado |
|---|---|---|---|---|
| codex | **SHADOW_ELIGIBLE** | 3 | `gpt-5.6-sol` | nenhum |
| kimi | **SHADOW_ELIGIBLE** | 3 | `kimi-code/k3` | nenhum |
| claude | SUPERVISED | 2 | — (descoberta desativada) | nenhum |
| google | SUPERVISED | **0** | — | nenhum |
| grok | SUPERVISED | **0** | — | nenhum |

Sumario: `ELIGIBLE: []`, `SHADOW_ELIGIBLE: ['codex','kimi']`,
`SUPERVISED: ['claude','google','grok']`, `BLOCKED: []`, total 5+0 de 5.

## 3. Comparacao com `preflight-20260801T221451Z.json`

### Mudou

| Campo | Corrida anterior (22:14:51Z) | Esta corrida (23:55:21Z) |
|---|---|---|
| `codex.resultado` | BLOCKED | **SHADOW_ELIGIBLE** |
| `kimi.resultado` | BLOCKED | **SHADOW_ELIGIBLE** |
| `codex.erros` | `P1A-DECLARACAO-EXPIRADA` | `[]` |
| `kimi.erros` | `P1A-DECLARACAO-EXPIRADA` | `[]` |
| `codex.modelos` | `[]` | `["gpt-5.6-sol"]` |
| `kimi.modelos` | `[]` | `["kimi-code/k3"]` |
| `codex.sombra` / `kimi.sombra` | `null` | payload com tier, declarante e `expira_em_utc` |
| `sondas_medidas.codex` / `.kimi` | 2 / 2 | **3 / 3** |
| `lock_escritor_unico.sessao` | `p1b01-ops` (pid 109072) | `p1b02-ops` (pid 131096) |
| `emenda_p1a3_item_1.tiers_declarados` | mesmos tiers, datados 31/07 01:31Z | mesmos tiers, datados 01/08 23:54:41Z |

**Por qual evidencia codex e kimi sairam de BLOCKED.** Pelo caminho
`pipeline.py:222-260`, e nao por mudanca de codigo — nenhuma linha de
codigo foi tocada nesta missao. Nas duas corridas o plano continua **nao
observavel no CLI** (`plano: null`), que e o bloqueio factual da P1-A.2.
A diferenca esta no unico teste que falhava antes: `declaracao_valida`.
Com a declaracao dentro da janela de 24 h, o portao passa a
`plano_reconhecido(decl.tier, planos_aceitos)`, que ja passava, e o
relatorio ganha o payload `sombra`. Como o teto de codex e kimi e
ELIGIBLE, `pipeline.py:306` converte o resultado em SHADOW_ELIGIBLE.

A **terceira sonda** de cada um e a prova independente de que o portao
foi de fato atravessado: a descoberta de modelos (`codex doctor`,
`kimi provider list`) so roda depois do bloco de erros
(`pipeline.py:266-282`). Na corrida anterior ela nunca foi alcancada —
dai 2 sondas e `modelos: []`. Ambas sao sondas de diagnostico; nenhuma
invoca modelo.

### Nao mudou

- `custo_variavel: 0` e `chamadas_de_modelo: 0` nas duas corridas.
- Capsula: `violacoes_no_env_do_processo: []` e
  `violacoes_no_env_classificado: []` — identicos. Nesta estacao, neste
  momento, o processo pai tambem estava limpo; a demonstracao de trabalho
  real da capsula continua sendo a da P1-B.01 (87 variaveis fora, 86
  dentro), nao esta corrida.
- `violacoes_ambiente_nomes: []` e `env_sanitizado_remove_nomes: []`.
- `plano` de codex e kimi permanece `null`: **nada** foi observado sobre
  o plano no CLI. O que mudou foi a declaracao, nao a observacao.
- `origem_credencial: subscription-oauth` para claude, codex e kimi;
  `nao-sondada` para google e grok.
- claude, google e grok: **SUPERVISED nos dois relatorios**, mesmos
  campos, mesmas contagens de sonda (2 / 0 / 0).
- `quota: desconhecida` nos **cinco** provedores, nas duas corridas.
- `ELIGIBLE: []` nas duas corridas.

## 4. O que esta corrida NAO estabelece

- Ninguem saiu **ELIGIBLE**. SHADOW_ELIGIBLE autoriza, pelo texto do
  proprio payload, "somente observacao-sombra de diagnostico; NAO
  autoriza P2 nem execucao autonoma".
- **google e grok tem 0 sondas**: nada foi observado neles nesta corrida.
  O SUPERVISED dos dois e classificacao estatica da especificacao
  (emenda P1-A.3 item 5), nao medicao.
- **Quota segue desconhecida nos cinco.** Nenhuma corrida ate aqui
  observou franquia disponivel.
- A janela e de **24 h**: as duas declaracoes expiram em
  2026-08-02T23:54:41Z e voltam sozinhas a BLOCKED por
  `P1A-DECLARACAO-EXPIRADA`. Renovar e ato do proprietario.
- O modelo de codex descoberto e `gpt-5.6-sol`; a especificacao espera a
  familia `gpt-5` e o casamento por substring aceitou. Fica **registrado
  como observacao, sem missao**: nao foi verificado se `gpt-5.6-sol` e o
  modelo que a assinatura Pro 5x deveria expor.
- Quem escreveu o codigo e os testes **nao certifica**. Esta sessao
  operou o mecanismo existente; nao houve revisao independente.

## 5. Fechamento

| Item | Medido no fechamento |
|---|---|
| Suite `05_p0/tests` (arquivos staged) | **100/100 OK** |
| Suite `06_p1a/tests` (arquivos staged) | **424/424 OK** |
| Arquivos alterados | `06_p1a/tiers_declarados.json` (2 linhas), evidencia nova, backup, este registro |
| Codigo-fonte alterado | **nenhum** |
