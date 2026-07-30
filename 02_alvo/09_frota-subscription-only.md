---
id: SSC-ALVO-09
titulo: Frota subscription-only do SSC+ (ADENDO)
tipo: contrato-experimental
versao: 0.1.0
status: ativo
origem: adendo-obrigatorio-2026-07-30
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Frota subscription-only do SSC+ (ADENDO)

> Evolução experimental do SSC+. NÃO reescreve nem invalida 0.1/0.2/0.2.1.
> Nada aqui é promovido automaticamente ao LucaX Enterprise OS canônico.

## 1. Frota inicial (cinco assinaturas)

| provider_id | assinatura | perfil inicial (PREFERÊNCIA, não papel fixo) |
|---|---|---|
| `codex` | OpenAI Codex via ChatGPT Pro 5x | implementação principal e operação de repositório |
| `claude` | Claude Code via Claude Max 5x | arquitetura, Specs e revisão profunda |
| `kimi` | Kimi Code via Allegretto | engenharia reversa, contexto extenso e volume |
| `google` | Google Antigravity via Google AI Pro | multimodalidade e julgamento transversal |
| `grok` | Grok Build via SuperGrok | pesquisa atual, X/web, red team e coding alternativo |

Toda escolha ocorre por **WorkUnit/ExecutionAttempt** dentro do mesmo
`SessionEnvelope`. Nenhum provedor fica vinculado à sessão inteira.

## 2. Contrato `FleetEntry` (ssc_p0/contratos.py)

Campos: `provider_id`, `model_id` (descoberto, nunca presumido),
`capability_profile`, `auth_mode`, `billing_mode`, `quota_state` +
`quota_reset` (reset conhecido), `automation_permission`, `terms_profile`,
`variable_cost`, `papeis_preferidos` (preferências), `canal_oficial`.

`RoutingDecision` ganha `papel` (autor/revisor/juiz) e
`independencia_evidencia`; `motivo` e `aprovacao_custo.fallback_autorizado`
já existiam. Enums fechados: `AUTH_MODES`, `BILLING_MODES`, `QUOTA_STATES`,
`AUTOMATION_PERMISSIONS`, `PAPEIS_FROTA`.

## 3. Política econômica imutável (`POLITICA_ECONOMICA`, MappingProxyType)

```
external_variable_cost_cap = 0
subscription_oauth = ALLOW
local_model = ALLOW
payg_api = DENY
extra_usage = DENY
auto_topup = DENY
unknown_billing_mode = DENY
```

Bloqueio ANTES da invocação (`verificar_economia` +
`AdaptadorAssinatura`): billing desconhecido/PAYG/pré-pago/extra-usage,
auth `payg-api` ou desconhecido, ou `variable_cost > 0` =
`PoliticaEconomicaViolada`, zero chamadas ao provider.

## 4. Ambiente sanitizado

`ambiente_sanitizado(env)` devolve CÓPIA do ambiente sem
`OPENAI_API_KEY`, `CODEX_API_KEY`, `ANTHROPIC_API_KEY`,
`ANTHROPIC_AUTH_TOKEN`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`,
`GOOGLE_APPLICATION_CREDENTIALS`, `XAI_API_KEY` e qualquer sufixo
`_API_KEY`/`_AUTH_TOKEN`/`_ACCESS_TOKEN`/`_API_SECRET`/`_SECRET_KEY`.
As credenciais globais **não são apagadas nem alteradas** — apenas não
entram no processo SSC+. **API key presente nunca substitui OAuth**:
sem `terms_profile.oauth_profile`, a invocação é bloqueada mesmo com
chave PAYG no host.

## 5. Regras de canal e autonomia

- **Grok**: somente Grok Build autenticado pela assinatura — cached token,
  headless ou ACP; **nunca `api.x.ai`**; `canal_oficial` obrigatório.
  `GROK_SUPERVISED = ALLOW`; `GROK_UNATTENDED = TERMS_REVIEW_REQUIRED`.
- **Google**: somente canal oficial da assinatura; OAuth não é reutilizado
  em cliente incompatível; automação **condicional**
  (`terms-review-required`) até prova do canal permitido.

## 6. QUOTA_EXHAUSTED

`falha-quota` tipada → estado `esgotada` registrado na frota (com
`quota_reset` conhecido) → sessão, WorkUnit, memória e causalidade
preservados (mecanismo 0.2.1) → **nova RoutingDecision** para outra
assinatura capaz (fallback 0.2.1-6, dentro do envelope) → nenhuma
disponível = **STOP_WAIT_RESET**. Migrar para API paga, créditos extras
ou saldo pré-pago é **PROIBIDO** (garantido por `verificar_economia`).

## 7. Independência em trabalho crítico

Autor, revisor e juiz independentes: `Frota.verificar_independencia`
exige provider E modelo distintos e produz a evidência registrada na
decisão (`independencia_evidencia`); soma-se ao IV-1/IV-2 do Juiz (0.2).

## 8. Rastreabilidade (adendo → contrato → código → teste)

| Exigência do adendo | Código | Teste |
|---|---|---|
| API key não substitui OAuth | `AdaptadorAssinatura`, `ambiente_sanitizado` | `test_api_key_presente_nao_substitui_oauth` |
| Billing desconhecido bloqueia pré-invocacao | `verificar_economia` | `test_billing_desconhecido_bloqueia_antes_da_invocacao` |
| Quota → nova decisão, linhagem preservada | `executar_com_frota`, `registrar_quota_exhausted` | `test_quota_esgotada_troca_provedor_preserva_linhagem` |
| Sem provedor = STOP_WAIT_RESET, nunca PAYG | `elegiveis`, `STOP_WAIT_RESET` | `test_sem_provedor_stop_wait_reset_nunca_payg` |
| Autor não aprova própria entrega | `verificar_independencia` | `test_autor_nao_aprova_propria_entrega_critica` |
| Grok cached/ACP, nunca api.x.ai | `verificar_canal` | `test_grok_cached_token_acp_sem_xai_key` |
| Google/Grok níveis de autonomia | `verificar_automacao`, `GROK_AUTOMATION` | `test_google_grok_respeitam_nivel_de_autonomia` |
| Descoberta de modelos, sem aliases | `Frota.descobrir`, `catalogo_de_frota` | `test_catalogo_descobre_modelos_sem_aliases_permanentes` |
| Campos do contrato | `FleetEntry`, `RoutingDecision.papel/independencia_evidencia` | `test_fleetentry_roundtrip_e_enums_fechados` |
