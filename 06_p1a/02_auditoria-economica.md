---
id: SSC-P1A-02
titulo: Auditoria economica pre-invocação (P1-A)
tipo: evidencia-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Auditoria economica — P1-A

> Executada ANTES de qualquer chamada de modelo. Tres fontes cruzadas:
> ambiente do processo, configuracao persistida dos CLIs e status reportado
> pelo proprio provedor. Comparacao de nomes de variaveis CASE-INSENSITIVE
> (Windows). Nenhum valor de credencial foi lido ou registrado.
> Evidencias: `evidencias/coleta-20260730-090127/04_env_payg_nomes.txt`,
> `11_codex_auth_auditoria.txt`, `12_claude.txt`, `13_kimi.txt`,
> `14_google.txt`.

## 1. Ambiente do processo (nomes, nunca valores)

Varredura case-insensitive por `(API_KEY|AUTH_TOKEN|ACCESS_TOKEN|API_SECRET|SECRET_KEY)`
e prefixos dos 5 provedores:

- `OPENAI_API_KEY` / `CODEX_API_KEY` — **ausentes**
- `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` — **ausentes**
- `GEMINI_API_KEY` / `GOOGLE_API_KEY` / `GOOGLE_APPLICATION_CREDENTIALS` — **ausentes**
- `XAI_API_KEY` — **ausente**
- `KIMI_API_KEY` / `MOONSHOT_API_KEY` — **ausentes**
- `NVIDIA_API_KEY` — **PRESENTE** (fora da frota; casa o padrao PAYG
  `_API_KEY`). Nao pertence a nenhum dos 5 provedores, mas prova que o
  ambiente global contem chave de API: o ambiente sanitizado
  case-insensitive (modulo `preflight/economia.py`) e OBRIGATORIO em
  qualquer subprocesso da frota. Nenhuma acao sobre a variavel global —
  ela apenas nao entra no processo.

## 2. Configuracao persistida dos CLIs

| Provedor | Verificacao | Resultado |
|---|---|---|
| Codex | `~/.codex/auth.json`: `auth_mode = chatgpt`; campo `OPENAI_API_KEY` existe porem **vazio** | OK — OAuth, sem chave persistida |
| Claude | `claude auth status`: `authMethod = claude.ai`, `apiProvider = firstParty` | OK — OAuth, sem chave |
| Kimi | `kimi provider list`: unico provider `managed:kimi-code`, `source = oauth` | OK — OAuth, sem provider PAYG configurado |
| Google | `~/.gemini/settings.json`: `selectedType = oauth-personal`; nenhum campo de API key | OK — OAuth, sem chave persistida |
| Grok | sem `XAI_API_KEY` no ambiente; sem config de API key encontrada; flags `--api-key`/`--batch-api` NAO utilizadas | OK — nenhuma chave; origem do cached token a confirmar pelo humano |

## 3. Status reportado pelo provedor

- Claude: `subscriptionType = max` (assinatura, nao PAYG) — confirmado pelo CLI.
- Codex/Kimi/Google/Grok: CLI nao expoe tier; plano declarado pela conta,
  a confirmar na janela de login humano da prova minima.

## 4. Veredito por item exigido (com nivel de evidencia)

Niveis: **CLI** = reportado pelo proprio provedor; **CONFIG** = verificado
na configuracao persistida; **INF** = inferencia forte (auth OAuth oficial
sem nenhuma chave PAYG); **IND** = indeterminado.

| Item | Estado | Nivel |
|---|---|---|
| billing_mode = subscription | Claude: `subscriptionType=max`; Codex: `auth_mode=chatgpt` + OPENAI_API_KEY vazia; Kimi: `source=oauth`, base_url oficial `api.kimi.com/coding/v1`; Google: `oauth-personal`; Grok: sem chave, auth indeterminada | Claude: CLI; Codex/Kimi/Google: INF; Grok: IND (SUPERVISED) |
| variable_cost = 0 | nenhum endpoint tarifado configurado em nenhum CLI; unica chave do ambiente (`NVIDIA_API_KEY`) e externa a frota e filtrada | INF (5/5) |
| auto top-up desligado | `~/.codex/config.toml`: sem flags `auto_topup`/`extra_usage`; `~/.claude/settings.json`: sem apiKeyHelper/chaves de billing; demais CLIs nao expoem | CONFIG (codex/claude); CLI nao expoe (demais) |
| extra usage desligado | idem item acima | CONFIG (codex/claude); CLI nao expoe (demais) |
| nenhuma API key ativa | ambiente limpo p/ os 5; kimi config.toml tem 3 campos `api_key` TODOS VAZIOS; codex auth.json com OPENAI_API_KEY vazia; gemini sem chave | CONFIG (5/5) |
| nenhum endpoint PAYG | codex: sem `base_url` em config.toml; kimi: `base_url` = `api.kimi.com/coding/v1` (endpoint oficial da assinatura); claude: firstParty; gemini: oauth-personal | CONFIG (4/4 verificaveis); grok: regra da missao proibe api.x.ai |
| nenhuma config persistida substituindo OAuth | verificado nos 4 CLIs com config acessivel (tabela do item 2 + `evidencias/coleta-20260730-092436/20_configs.txt`) | CONFIG |

Evidencias desta segunda rodada: `evidencias/coleta-20260730-092436/`
(20_configs.txt, 21_claims_grok_google_kimi.txt, 22_scan_segredos.txt).

## 5. Regra operacional derivada

Qualquer execucao real da frota (inclusive a prova minima) DEVE rodar com
ambiente sanitizado case-insensitive que remove `_API_KEY|_AUTH_TOKEN|
_ACCESS_TOKEN|_API_SECRET|_SECRET_KEY` e a lista explicita de chaves PAYG.
O ambiente global do usuario NUNCA e modificado.
