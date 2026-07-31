# SSC+ P1-A — Preflight da frota real (experimental, sem autoridade)

Modulo **experimental** de diagnostico read-only dos 5 CLIs de assinatura
(codex, claude, kimi, gemini, grok). Sem autoridade: nada aqui executa,
roteia ou decide pelo SSC+ — apenas mede e classifica.

O preflight **nunca** executa chamada produtiva a modelo, **nunca**
solicita pagamento e **nunca** altera arquivos do projeto. Toda execucao
externa passa por um *sensor* injetavel (`sensor(argv, env) ->
(returncode, stdout, stderr)`); nos testes, sensores falsos substituem
qualquer subprocesso. O sensor padrao (`sensor_subprocess`) so roda em
operacao real, com ambiente sanitizado, timeout e captura de saida.

## Fluxo (`pipeline.executar_preflight`)

1. Auditoria de ambiente (`economia.auditar_ambiente`): variaveis PAYG,
   comparacao **case-insensitive** (Windows), nunca retorna valores.
2. Auditoria de config persistida (`economia.auditar_config`): chave de
   API substituindo OAuth, endpoint PAYG, auto top-up / extra usage.
3. Status economico estatico (`economia.auditar_status`): billing
   `subscription`, `variable_cost == 0`, auth nao-PAYG; auth presente mas
   desconhecida = DENY (nunca ELIGIBLE por inferencia).
4. Deteccao do CLI + versao + status de login via sensores.
5. Descoberta de modelos — **somente** com economia/auth verdes.
6. Classificacao: `ELIGIBLE` | `SHADOW_ELIGIBLE` | `SUPERVISED` |
   `BLOCKED` com erros tipados.

Qualquer violacao economica ou de auth bloqueia **antes** de qualquer
sensor de modelo. Google e Grok nunca passam de `SUPERVISED`
(`teto_resultado` na especificacao). Chave PAYG do provedor com login
OAuth ativo e `ConflitoAmbienteLogin` — a chave nunca vence o OAuth.

Erros tipados (todos derivam de `ErroPreflight`, com `codigo` estavel):
`ChavePaygDetectada` (P1A-PAYG-ENV), `ConfigPaygPersistida`
(P1A-PAYG-CONFIG), `OAuthAusente` (P1A-OAUTH-AUSENTE),
`PlanoNaoReconhecido` (P1A-PLANO-DESCONHECIDO), `QuotaEsgotada`
(P1A-QUOTA-ESGOTADA), `BillingDesconhecido` (P1A-BILLING-DESCONHECIDO),
`CliIndisponivel` (P1A-CLI-INDISPONIVEL), `ModeloRemovido`
(P1A-MODELO-REMOVIDO), `ConflitoAmbienteLogin` (P1A-CONFLITO-ENV-LOGIN),
`DeclaracaoExpirada` (P1A-DECLARACAO-EXPIRADA — P1-A.3).

## Rodar os testes

```bash
python -m unittest discover -s 06_p1a/tests -v
```

O pacote `preflight/` e autonomo: nao importa `ssc_p0`, apenas espelha a
POLITICA_ECONOMICA da P0. O `escritor.py` (P1-A.1) e o runner
`evidencias/prova_minima.py` usam o writelock da P0
(`ssc_p0.writelock.LockSessao`) para garantir escritor unico com lease +
fencing no ponto de entrada das operacoes P1; o estado de lock vive em
`locks/` (runtime, ignorado pelo Git). Estabilizacao P1-A.1:
`05_relatorio-estabilizacao-p1a1.md`.

P1-A.2: `capsula.py` (ambiente-filho subscription-only — o SSC+ nasce sem
nenhuma credencial de modelo; o ambiente global/HKCU nunca e modificado),
`preflight_capsula.py` (preflight diagnostico real dentro da capsula) e
`evidencias/revisao_p1a2.py` (revisao read-only por provider distinto,
uma chamada). Adendo de politica: `06_adendo-capsula-p1a2.md`; decisao:
`99_decisao-p1a2.md` (ADJUST — bloqueios factuais de especificacao nos
portoes de plano/descoberta headless).

P1-A.3 (emendas decididas pelo Soberano sobre a P1-A.2): trilha
`SHADOW_ELIGIBLE` — tier declarado pelo proprietario
(`tiers_declarados.json`, validade maxima 24 h) + OAuth observado; NAO
autoriza P2 nem execucao autonoma (`preflight/sombra.py`). Descoberta
codex via `codex doctor` (modelo efetivo + auth mode; nao catalogo).
Kimi comprova OAuth e modelo efetivo via `provider list`, nao o plano
(trilha sombra). Claude permanece SUPERVISED, sem sonda de modelos, ate
modelo exato observado por fonte oficial nao interativa. Google e Grok
SUPERVISED, zero sondas automaticas. Capsula, politica NVIDIA e
bloqueios PAYG inalterados. Revisao independente por 2 providers:
`evidencias/revisao_p1a3.py`. Adendo: `07_adendo-emendas-p1a3.md`;
decisao: `99_decisao-p1a3.md`.
