---
id: SSC-DEC-04
titulo: Relatorio e Decisao do Adendo — Frota subscription-only (SSC+ 0.3 experimental)
tipo: decisao-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Relatorio e Decisao do Adendo — Frota subscription-only

> Evolucao experimental do SSC+, incorporada ao escopo vigente SEM
> reescrever ou invalidar 0.1/0.2/0.2.1. Offline, isolado, sem provider
> real. **Nada foi promovido ao LucaX Enterprise OS canonico.**

## DECISAO: **REGISTRADO-COMO-EVOLUCAO-EXPERIMENTAL**

Adendo implementado no laboratorio com contratos, politica economica
imutavel, ambiente sanitizado, fluxo QUOTA_EXHAUSTED e os 8 testes
minimos exigidos — tudo verde, sem custo para as garantias da 0.2.1.

## 1. O que foi instituido

- **Contrato `FleetEntry`** (`contratos.py`): provider_id, model_id
  descoberto, capability_profile, auth_mode, billing_mode, quota_state +
  quota_reset, automation_permission, terms_profile, variable_cost,
  papeis_preferidos, canal_oficial. Enums fechados novos (auth, billing,
  quota, automacao, papeis). `RoutingDecision` ganha `papel` e
  `independencia_evidencia`. `SCHEMA_VERSION` → `ssc-p0/1.2`.
- **`ssc_p0/frota.py`**: `POLITICA_ECONOMICA` imutavel (cap 0; OAuth de
  assinatura e local = ALLOW; PAYG/extra/topup/desconhecido = DENY),
  `ambiente_sanitizado` (chaves PAYG fora do processo, ambiente global
  intacto), `verificar_economia/canal/automacao`, `Frota` (descoberta de
  modelos sem aliases permanentes, elegiveis, independencia),
  `AdaptadorAssinatura` (bloqueio pre-invocacao), `executar_com_frota`
  (QUOTA_EXHAUSTED → nova RoutingDecision → outra assinatura →
  STOP_WAIT_RESET, nunca PAYG), `frota_inicial` (as 5 assinaturas com
  perfis iniciais como PREFERENCIAS).
- **Regras Grok/Google**: Grok so Grok Build da assinatura
  (cached-token/headless/ACP; nunca api.x.ai; SUPERVISED=ALLOW,
  UNATTENDED=TERMS_REVIEW_REQUIRED); Google so canal oficial, automacao
  condicional ate prova do canal.
- **Wiring minimo**: `Lab` aceita catalogo/politica/aprovacao derivados
  da frota; `propor_decisao` registra `papel`/`independencia_evidencia`.
  Nenhuma garantia da 0.2.1 foi alterada.

## 2. Testes

- **100 testes, 0 falhas, 0 skips** (91 da 0.2.1 + 9 novos em
  `test_frota.py`: os 8 minimos do adendo + round-trip/enums da
  FleetEntry). Prova central 18/18; corridas TO-1..TO-5 OK; cobertura
  stdlib `trace`: **2590/2590 linhas (100%)** de `ssc_p0`.
- Mapeamento exigencia → teste em `02_alvo/09_frota-subscription-only.md`
  §8.

## 3. Rastreabilidade e evidencia

- Contrato/alvo: `02_alvo/09_frota-subscription-only.md`.
- Diff da evolucao: `logs/diff-0.3-frota.patch`.
- Decisao: este documento. Commit proprio, sem tag, sem remoto, staging
  explicito (mesma disciplina do PORTAO A da 0.2.1).

## 4. Limitacoes declaradas

- Os adaptadores sao **falsos** (nenhum CLI real e invocado na fase
  offline); a sanitizacao e provada por construcao do ambiente efetivo,
  nao por subprocesso real — isso e materia da P1.
- `descobrir()` usa a leitura declarada; o sensor real de descoberta de
  modelos entra com os adaptadores reais.
- `quota_reset` e registrado quando conhecido; nenhuma espera ativa e
  implementada (STOP_WAIT_RESET e um estado terminal da rodada, nao um
  timer).
- Perfis iniciais sao preferencias documentadas; nenhuma rota e forcada
  por perfil.
