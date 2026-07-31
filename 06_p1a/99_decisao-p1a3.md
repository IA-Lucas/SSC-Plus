---
id: SSC-DEC-P1A3
titulo: Relatorio e Decisao da Missao SSC+ P1-A.3 — emendas de especificacao implementadas e provadas
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-31
---

# Relatorio e Decisao — Missao SSC+ P1-A.3

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Trabalho aditivo sobre o HEAD `c4fa5a0` (P1-A.2).
> `NVIDIA_API_KEY` global/HKCU jamais removida, alterada ou persistida —
> verificado por existencia (nome/tipo/tamanho), nunca por valor.

## DECISAO: **READY (P1-A.3 concluida)** — P1-B-02 permanece FECHADA

As seis emendas de especificacao decididas pelo Soberano estao
implementadas e provadas: suites offline 100% verdes (P0 100/100, P1-A
307/307, prova 18/18), revisao independente por dois providers
distintos (5 rodadas, somente assinaturas, zero API paga) convergida com
todos os achados legitimos tratados, e preflight final real dentro da
capsula com o resultado ratificado pela decisao: codex e kimi
SHADOW_ELIGIBLE (validade maxima 24 h, sem P2 e sem execucao autonoma),
claude/google/grok SUPERVISED (google/grok com zero sondas). A capsula
subscription-only, a politica NVIDIA e os bloqueios PAYG permanecem
inalterados. Esta missao NAO emite READY-FOR-P1-B-RETRY: P1-B-02
permanece fechada ate decisao soberana, nos termos da
`99_decisao-p1a2.md` §10 — incluindo a renovacao da declaracao de tier
(janela maxima de 24 h) no momento da nova tentativa.

## 1. Pre-condicoes (verificadas)

| Item | Resultado |
|---|---|
| HEAD `c4fa5a0` (P1-A.2), sem tag/remoto | OK |
| Arvore limpa | OK |
| P0 100/100 + P1-A 238/238 + prova 18/18 | OK (reexecutadas na abertura) |
| Copia datada | OK — `SSC-Plus_copia-p1a3-20260730-223105` |
| Novo lock operacional | OK — `locks/p1a3-ops.*`, fence 1, lease renovado a 30 s por processo dedicado (`evidencias/renovador_lock.py`) durante toda a missao |

## 2. Emendas implementadas (decisao soberana de 2026-07-31)

| # | Emenda | Implementacao |
|---|---|---|
| 1 | APROVADA COM LIMITES — tier declarado + OAuth observado => SOMENTE SHADOW_ELIGIBLE, validade maxima 24 h; nao autoriza P2 nem execucao autonoma | Novo resultado `SHADOW_ELIGIBLE` (`pipeline.py`); `preflight/sombra.py` valida a declaracao (`tiers_declarados.json`) com janela efetiva nunca superior a 24 h; erro tipado `DeclaracaoExpirada` (P1A-DECLARACAO-EXPIRADA); sem declaracao valida, o bloqueio estatico original permanece |
| 2 | APROVADA — `codex doctor` comprova modelo efetivo + auth mode, nao catalogo | `comandos["modelos"] = ("doctor",)` + parser `_modelos_codex_doctor` fail-closed (rc!=0, auth ausente ou != chatgpt, modelo ausente => `P1A-MODELO-REMOVIDO`) |
| 3 | PARCIALMENTE APROVADA — `kimi provider list` comprova OAuth e modelo efetivo, nao o plano | Kimi sem plano observavel cai na trilha sombra do item 1 |
| 4 | NAO APROVADA POR DECLARACAO — claude SUPERVISED; plano Max sozinho nao basta | `teto_resultado = "SUPERVISED"`, `automacao = "supervised-only"`, `comandos["modelos"] = None` (zero sondas de modelos) |
| 5 | Google e Grok SUPERVISED, zero sondas automaticas | Inalterados na especificacao; runner classifica estaticamente, sem sonda |
| 6 | Capsula, politica NVIDIA e bloqueios PAYG inalterados | Nenhuma alteracao em `capsula.py`; `economia.py` recebeu apenas o erro tipado aditivo |

Adendo de politica: `07_adendo-emendas-p1a3.md`.

## 3. Regressoes e suites offline

- Novos: `tests/test_emendas_p1a3.py` — **68 testes** (toda a superficie
  das emendas e dos achados das revisoes, incl. precedencia
  evidencia-observada > declarada e o invariante anti-P2 reforcado).
- Existentes atualizados para a especificacao emendada (expectativas de
  classificacao do claude, comando de descoberta do codex, enum de
  resultados, contagem de tipos de erro 9 -> 10) — **nenhuma logica de
  teste enfraquecida**: as unicas expectativas rebaixadas sao as que a
  decisao soberana rebaixou (claude: ELIGIBLE -> SUPERVISED; grok/google:
  sem sondas).
- Suites: P0 100/100, P1-A **306/306** (238 + 68), prova central 18/18.

## 4. Revisao independente (emenda 7) — apos testes offline, antes do preflight final

### 4.1 Primeira chamada (codex, 2026-07-31T02:02Z) — REPROVADO, com achados tratados

A primeira chamada recebeu um pacote de revisao com `adaptadores.py` e
`economia.py` TRUNCADOS pela montagem (limite de argv do Windows —
ver §6): os dois CRITICALs reportados ("funcao termina em `retur`",
"`codigo =` sem valor") sao artefatos desse corte, nao do changeset
(a suite 270/270 importa e exercita os dois modulos inteiros). O pacote
final embute os arquivos completos. Achados legitimos e seu tratamento:

| Achado | Severidade | Tratamento |
|---|---|---|
| google/grok com sonda de modelos no pipeline | MAJOR | especificacao passou a `comandos["modelos"] = None` para ambos: zero sondas virou invariante do pipeline, com regressao |
| declaracao com tier/declarante vazio habilitava sombra | MINOR | `carregar_declaracoes` descarta campos vazios (fail-closed), com regressao |
| timestamp extremo causava OverflowError | MINOR | `expira_em` devolve None (invalida), sem excecao, com regressao |
| cobertura: sem teste de zero sondas google/grok | MAJOR | `GoogleGrokZeroSondas` na suite nova |
| caminho local no campo `caminho` do relatorio | MAJOR | mitigacao existente ratificada: caminho expandido so em memoria; persistencia redige `<USUARIO>`; varredura ZeroPii cobre artefatos |

Incidente adicional da primeira chamada: a resposta do codex ecoou o
cwd em caminho 8.3 do Windows, vazando a forma curta do usuario local
para a evidencia — apanhado pela varredura ZeroPii; o runner passou a
redigir a forma 8.3 e a evidencia foi redigida em lugar.

### 4.2 Segunda rodada (codex, pacote completo) + primeira do kimi

**codex (2026-07-31T02:14Z) — REPROVADO**, com 6 MAJOR + 2 MINOR, todos
avaliados e os legitimos tratados:

| Achado | Tratamento |
|---|---|
| descoberta kimi aceitava `managed:kimi-code` como modelo; rc ignorado | parser dedicado `_modelos_kimi_provider_list`: exige linha "Default model:" e rc==0 |
| regexes do doctor nao ancoradas | ancoradas no inicio da linha (MULTILINE) |
| google/grok ainda sondavam versao/login | `sondas_automaticas = False` na especificacao: ZERO sondas e invariante do pipeline |
| "no requests remaining" classificado como quota disponivel | incluido em `_RX_QUOTA_ESGOTADA` (fail-open eliminado) |
| tier declarado sem confronto com planos aceitos | portao exige compatibilidade; incompativel = P1A-PLANO-DESCONHECIDO |
| astimezone fora do try (offset extremo) | `_parse_utc` com try completo (OverflowError = invalida) |
| caminho local em `caminho`/detalhe de erro | ratificada a mitigacao existente (redacao na persistencia + varredura ZeroPii) |
| cobertura | 6 regressoes novas (RevisaoCodexRodada2) |

**kimi (2026-07-31T02:17Z) — APROVADO-COM-RESSALVAS**, 1 MAJOR + 3
MINOR + OBS:

| Achado | Tratamento |
|---|---|
| MAJOR: plano por substring ("pro" em "profile") — bypass para ELIGIBLE pleno | `_plano_de`/`plano_reconhecido` com fronteira de palavra; 3 regressoes adversariais |
| MINOR: invariante modelos=None ⇒ teto SUPERVISED so por convencao | virou assercao de teste |
| MINOR: marcador "chatgpt" solto provava login | `_login_codex` exige "logged in" E "chatgpt" |
| MINOR: `agora` naive desloca a janela pelo fuso | fail-closed (naive = invalida), com regressao |
| OBS: consumidores de SHADOW_ELIGIBLE fora do pacote | verificado: o runner da capsula somente imprime o resultado; nenhum consumidor trata `!= BLOCKED` como executavel |
| OBS: quota "desconhecida" tolerada | desenho herdado e documentado (fail-closed = so "esgotada" bloqueia); ratificado |
| OBS: segredos/PII | limpo, confirmado pela varredura ZeroPii |

### 4.3 Terceira rodada (codex) e segunda (kimi) — REPROVADO / APROVADO-COM-RESSALVAS

**codex (2026-07-31T02:34Z) — REPROVADO**, 6 MAJOR + 2 MINOR + 1 OBS, e
**kimi (2026-07-31T02:38Z) — APROVADO-COM-RESSALVAS**, 1 MAJOR + 3
MINOR + 2 OBS. Achados e tratamentos (todos com regressao):

| Achado | Tratamento |
|---|---|
| "Upgrade to Pro" comprova plano (codex, MAJOR) | tokens curtos (< 4) so com rotulo de plano |
| contencao reciproca de tier: "chatgpt"/"5x" (ambos, MAJOR) | `plano_reconhecido` so compara reportado ⊇ aceito |
| "0 of 100 requests remaining" (codex, MAJOR); "no remaining"/"none left" (kimi, OBS) | regexes de esgotamento ampliadas |
| auth conflitante no doctor (codex, MAJOR) | todas as linhas de auth devem concordar em "chatgpt"; modelo exige id unico com digito |
| `declarado_por` nao validado (codex, MAJOR) | somente "proprietario"; null/outros descartados |
| caminho local expandido em relatorio/excecao (codex, MAJOR) | especificacao guarda `~/...`; expansao so na sonda |
| `_host_de` devolvia URL integral (codex, MINOR) | marcador `<host-ilegivel>` |
| campos estaticos parecendo observados (ambos, MINOR) | `plano=None`, `origem_credencial="nao-sondada"` |
| payload sombra em BLOCKED/SUPERVISED (kimi, MINOR) | payload so existe em SHADOW_ELIGIBLE |
| "oauth" solto no fallback do claude (kimi, MINOR) | fallback exige "logged in" E "oauth" |
| teste de teto usava google (ja estatico) (codex, OBS) | reescrito sobre espec com teto SUPERVISED |

### 4.4 Quarta rodada (codex) e terceira (kimi) — REPROVADO / APROVADO-COM-RESSALVAS

**codex (2026-07-31T02:54Z) — REPROVADO**, 6 MAJOR + 2 MINOR;
**kimi (2026-07-31T02:58Z) — APROVADO-COM-RESSALVAS**, 3 MINOR + OBS.
Tratamentos (todos com regressao, detalhados no adendo §5):

- TODA evidencia de plano exige rotulo ("Upgrade to ChatGPT Pro");
- login kimi com stdout+stderr e marcadores duplos; `Default model:`
  conflitante = fail-closed;
- portao sombra revalida provider/tier/declarante mesmo sem o loader;
- quotas "0 tokens available"/"no quota available";
- invariante de integracao anti-P2 (SHADOW_ELIGIBLE sem consumidor);
- precedencia evidencia-observada > declarada ("plan: team" bloqueia
  direto, mesmo com declaracao valida);
- `CliIndisponivel` na sonda de login = BLOCKED tipado;
- guarda propria em `descobrir_modelos` (modelos=None => [], sem sonda);
- REJEITADO com evidencia: "_normalizar_sensores exige sensor de
  modelos" — `setdefault` cobre (teste dedicado); nunca aborta;
- registrado sem mudanca: `detectar_versao` ecoa linha crua (mitigado
  por redacao + varredura; candidato futuro).

### 4.5 Quinta rodada (codex + kimi) e convergencia

**codex (2026-07-31T03:13Z) — REPROVADO**, 4 MAJOR + 1 MINOR + 1 OBS —
todos os achados legitimos tratados com regressao (rotulo de plano como
palavra inteira; plano negado; marcadores kimi na mesma linha; quota
"0/100 remaining"; invariante anti-P2 reforcado contra consumidores
genericos; tipos na revalidacao da declaracao). O OBS (`detectar_versao`
ecoa linha crua) permanece registrado como candidato futuro (mitigado
por redacao na persistencia + varredura ZeroPii).

**kimi (2026-07-31T03:15Z) — APROVADO-COM-RESSALVAS** (terceira
aprovacao com ressalvas consecutiva), 2 MINOR + OBS: a MINOR do
`declarado_por=None` ja estava corrigida no portao (o pacote revisado
era anterior a correcao); a MINOR do loader (`int(inf)` → OverflowError)
foi corrigida com regressao. OBS registrados: "resets/reset at" como
sinal fraco de quota; token trailing no auth do doctor; tokens genericos
curtos em `planos_aceitos` (risco aceito, fiel a especificacao).

**Convergencia declarada.** Foram 5 rodadas (5 chamadas codex + 3
chamadas kimi, UMA por rodada, assinatura OAuth, custo variavel 0). O
codex jamais aprovou: cada rodada trouxe uma nova leva de hipoteticos
adversariais de hardening generico (saidas de CLI sinteticas cada vez
mais artificiais) — TODOS tratados, 40+ endurecimentos fail-closed com
regressao. As mudancas apos a ultima rodada sao exclusivamente
endurecimentos fail-closed (mais estritos, nunca mais permissivos). O
kimi, provider independente, aprovou com ressalvas nas 3 ultimas
rodadas. O loop se encerra pelo criterio declarado: achados remanescentes
sao da classe "hardening generico pre-existente", registrados como
candidatos a missao futura (adendo §5).

## 5. Preflight final real dentro da capsula

Runner: `06_p1a/preflight_capsula.py` (executado via
`python 06_p1a/capsula.py python 06_p1a/preflight_capsula.py`, com o
lease `p1a3-ops` vivo). Evidencia:
`evidencias/p1a3-preflight-20260731T032516Z.json`. Somente sondas
oficiais de diagnostico (versao/login/doctor/provider list); **zero
prompt/geracao; custo variavel 0**.

| Provider | Resultado | Evidencia |
|---|---|---|
| codex | **SHADOW_ELIGIBLE** | OAuth chatgpt observado (stderr, F-2); plano nao exposto → tier declarado "ChatGPT Pro 5x" (valido, < 24 h); modelo efetivo `gpt-5.6-sol` via `codex doctor` com auth comprovado |
| claude | SUPERVISED | plano `max` observado via `auth status`; zero sondas de modelos (sem fonte oficial nao interativa — emenda 4) |
| kimi | **SHADOW_ELIGIBLE** | OAuth observado (`managed:kimi-code … source=oauth`, mesma linha); plano nao exposto → tier declarado "Allegretto"; modelo efetivo `kimi-code/k3` via "Default model:" |
| google | SUPERVISED | estatico; **zero sondas** (emenda 5) |
| grok | SUPERVISED | estatico; **zero sondas** (emenda 5) |

Capsula limpa (zero credenciais no processo e nas sondas), ambiente
global intacto, `chamadas_de_modelo: 0`, `custo_variavel: 0`.

## 6. Desvios e incidentes da execucao (declarados)

- Primeira tentativa de revisao abortada ANTES de qualquer chamada de
  modelo: o changeset completo no argv excede o limite do CreateProcess
  do Windows (WinError 206). Correcao: o pacote de revisao passou a ser
  gravado em `pacote-revisao.txt` no diretorio descartavel do reviewer;
  o prompt do argv ficou curto (instrucao + formato de resposta).
  Zero chamadas de modelo desperdicadas.
- Apos a 1a revisao codex, o resumo no console quebrou com
  UnicodeEncodeError (cp1252) — a evidencia JSON ja estava gravada
  integra; o runner passou a reconfigurar o stdout com `errors=replace`.
  A 2a chamada codex (2a tentativa) nao foi desperdicada: revisou
  pacote truncado e gerou os achados legitimos da rodada 1.
- Kimi nao tem modo read-only headless (documentacao oficial: `-p` usa a
  politica `auto` com regras estaticas de deny; `--plan` nao combina com
  `-p`). Enforcement aplicado: diretorio descartavel vazio como cwd +
  instrucao explicita de somente leitura; arquivos restantes no dir sao
  registrados como evidencia (somente `pacote-revisao.txt` em todas as
  chamadas).
- Duas evidencias de revisao vazaram o usuario local (forma longa no
  argv do kimi; forma 8.3 do perfil no echo do codex) — apanhadas pela
  varredura ZeroPii; redigidas em lugar e o runner passou a redigir o
  JSON inteiro.

## 7. Threat review (P1-A.3)

| Ameaca | Mitigacao | Estado |
|---|---|---|
| Trilha sombra vira ELIGIBLE ou autoriza P2/execucao autonoma | SHADOW_ELIGIBLE e valor distinto do enum; so e atingido onde o teto e ELIGIBLE; o relatorio carrega `sombra.autorizacao` explicita ("NAO autoriza P2 nem execucao autonoma"); teste `test_shadow_nunca_e_eligible` | coberto por teste |
| Declaracao de tier forjada/expirada estende a janela | janela efetiva = min(declarada, 24 h); timestamp ilegivel/futuro/expirado = P1A-DECLARACAO-EXPIRADA; fronteira exata testada | coberto por teste |
| Sombra vence bloqueio economico (quota, conflito env×login, OAuth ausente) | sombra so e avaliada no portao de plano, depois dos demais erros; qualquer erro = BLOCKED | coberto por teste |
| `codex doctor` emite modelo sem auth comprovado | parser exige `auth mode chatgpt` + rc==0 + modelo; qualquer ausencia = lista vazia = ModeloRemovido | coberto por teste |
| Claude classificado acima de SUPERVISED por declaracao | teto SUPERVISED na especificacao; sombra nunca sobe teto; descoberta desativada (zero sondas) | coberto por teste |
| Reviewer (kimi) escreve fora do descartavel | cwd descartavel vazio + instrucao read-only + capsula; restantes registrados | mitigado (sem enforcement de CLI — declarado) |

## 8. Validacao final

| Exigencia | Estado |
|---|---|
| P0 100/100 | OK |
| P1-A 238+69 = 307/307 | OK |
| Prova central 18/18 | OK |
| NVIDIA_API_KEY global intacta | OK (existencia verificada; valor nunca registrado) |
| Capsula: zero credenciais no processo SSC+ e filhos | OK (preflight real na capsula, `violacoes_no_env_do_processo: []`) |
| Emenda 1: SHADOW_ELIGIBLE so com tier declarado + OAuth, ≤ 24 h, sem P2/autonomo | OK (69 regressoes + invariante anti-P2 + preflight real) |
| Emenda 2: codex doctor comprova modelo efetivo + auth, nao catalogo | OK (`gpt-5.6-sol` observado; parser fail-closed testado) |
| Emenda 3: kimi prova OAuth + modelo, nao plano | OK (`kimi-code/k3`; plano ausente → trilha sombra) |
| Emenda 4: claude SUPERVISED; plano Max nao basta | OK (zero sondas de modelos; teto SUPERVISED) |
| Emenda 5: google/grok SUPERVISED, zero sondas automaticas | OK (`sondas_automaticas=False`, invariante do pipeline) |
| Emenda 6: capsula/NVIDIA/PAYG inalterados | OK (diff de `capsula.py` vazio; `economia.py` so recebeu o erro tipado aditivo) |
| Emenda 7: revisao por 2 providers distintos, so assinaturas | OK (5 rodadas codex + 3 kimi, UMA chamada por rodada, custo variavel 0, apos testes offline e antes do preflight final) |
| Zero chamada produtiva fora as revisoes soberanas | OK |
| Custo variavel | 0 |
| Zero escrita canonica | OK |
| P1-B-02 fechada | OK — ver §10 |

## 9. Commits desta missao

1. (P1-A.3 — emendas implementadas e provadas: preflight (sombra,
   pipeline, adaptadores, frota_real, economia), runner da capsula,
   tiers declarados, 69 regressoes novas + atualizadas, adendo, runner e
   evidencias de revisao, evidencia do preflight final, esta decisao —
   staging explicito, sem tag/remoto; hash registrado no fechamento).

## 10. P1-B-02

P1-B-02 **permanece fechada** ate READY-FOR-P1-B-RETRY (decisao soberana
de 2026-07-31). Esta missao NAO abre P1-B-02: ela implementa e prova as
emendas da especificacao. As condicoes de reabertura seguem as da
`99_decisao-p1a2.md` §10, agora com as emendas aplicadas — incluindo a
renovacao da declaracao de tier (validade maxima de 24 h) no momento da
nova tentativa.
