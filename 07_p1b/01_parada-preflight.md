---
id: SSC-P1B-PARADA-01
titulo: Registro de PARADA IMEDIATA SSC+ P1-B — preflight nao verde / canal economico ambiguo
tipo: parada-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Registro de PARADA IMEDIATA — Missao SSC+ P1-B (pre-coleta)

> A missao PAROU antes do protocolo pre-registrado (nenhuma WorkUnit
> versionada, nenhuma RoutingDecision gerada, nenhuma rerota exercitada).
> Condicao disparada, uma das listadas na missao: **preflight nao verde**,
> com **canal economico ambiguo** associado. Este documento preserva a
> evidencia e devolve o estado real. Nenhum modelo foi invocado na P1-B;
> custo variavel = 0; nenhuma escrita fora do laboratorio (exceto a copia
> datada autorizada como pre-condicao).

## 1. Pre-condicoes cumpridas ANTES da parada

| Item | Resultado |
|---|---|
| HEAD exato `8ba75de176ab0ec25da39e196492958478b8be29`, sem tag/remoto | OK (`git rev-parse HEAD`, `git tag`, `git remote -v` vazios) |
| Arvore limpa no inicio | OK (`git status --porcelain` vazio) |
| Ancestralidade | OK (`git merge-base --is-ancestor 0da9d41 HEAD`) |
| P0 100/100 + P1-A 211/211 + prova central 18/18 | OK — reexecutados nesta sessao; `prova_central.json` rastreado restaurado ao HEAD apos a reexecucao |
| Lock lease+fencing ANTES da primeira escrita | OK — `locks/p1b-ops.{lock,fence,lease}` via `EscritorP1` (sessao `p1b-ops`, fencing token 1, lease renovado a 60 s por processo dedicado); segunda aquisicao recusada (`LockIndisponivel`), prova funcional registrada |
| Copia datada fora do repositorio | OK — `E:/LucasIA/Projetos/SSC-Plus_copia-p1b-20260730-132215`, diff vazio (excluidos `.git`, `locks/`, `__pycache__`) |

## 2. O que aconteceu: preflight ATUAL da frota = BLOCKED x5

Primeira execucao do pipeline ratificado da P1-A/P1-A.1
(`06_p1a/preflight`, sem alteracao de codigo) contra o ambiente real,
pelo runner `07_p1b/preflight_atual.py` (somente sondas de diagnostico
versao/login/modelos; env de subprocesso sempre sanitizado pela canonica
`preflight.economia.ambiente_sanitizado`).

Evidencia oficial: `07_p1b/evidencias/preflight-20260730T163152Z.json`
(uma corrida anterior, `preflight-20260730T162725Z.json`, e preservada
mas esta SUPERSEDIDA — continha um falso positivo do proprio runner,
ver §4).

Resultado por provedor (corrida oficial vigente):

| Provedor | Resultado | Erros |
|---|---|---|
| codex | BLOCKED | P1A-PAYG-ENV (`NVIDIA_API_KEY`) |
| claude | BLOCKED | P1A-PAYG-ENV (`NVIDIA_API_KEY`) |
| kimi | BLOCKED | P1A-PAYG-ENV (`NVIDIA_API_KEY`) |
| google | BLOCKED | P1A-PAYG-ENV (`NVIDIA_API_KEY`) |
| grok | BLOCKED | P1A-PAYG-ENV (`NVIDIA_API_KEY`) |

Unico bloqueador restante: a variavel de ambiente `NVIDIA_API_KEY`,
**presente e persistente** na estacao (valor em `HKCU\Environment` —
somente a existencia e o nome foram verificados; o valor nunca foi
registrado em artefato). `nvidia` consta deliberadamente em
`_FAMILIAS_PROVEDOR` de `06_p1a/preflight/economia.py` (escopo de
BLOQUEIO) — decisao D-2 da P1-A.1, revisada e incorporada:
"`NVIDIA_API_KEY` (fora da frota, familia de provedor de IA) continua
violacao economica e continua sanitizada"
(`06_p1a/04_suite-preflight-e-correcoes.md` §2.2).

## 3. A ambiguidade (por que nao cabe ao orquestrador resolve-la)

Dois artefatos ratificados divergem no efeito pratico:

- **Auditoria humana P1-A** (`06_p1a/02_auditoria-economica.md` §1):
  `NVIDIA_API_KEY` e "fora da frota; nao pertence a nenhum dos 5
  provedores... Nenhuma acao sobre a variavel global — ela apenas nao
  entra no processo". Sob esse julgamento, a frota foi classificada
  ELIGIBLE (codex/claude/kimi) com a variavel presente.
- **Pipeline codificado P1-A.1** (`economia.py` + `04_suite` §2.2):
  `nvidia` e familia de provedor de modelo no escopo de bloqueio —
  `payg_api = DENY`, e o pipeline (que a P1-A nunca executou contra o
  ambiente real; a classificacao foi manual) classifica BLOCKED.

A sanitizacao ja garante que a variavel **nunca entra em nenhum
subprocesso** da frota (prova: `env_sanitizado_remove_nomes` na
evidencia oficial). A questao e exclusivamente de governanca: o canal
economico esta limpo na pratica (nenhum caminho de custo), mas a regra
codificada e ratificada diz DENY pela mera presenca de uma credencial de
provedor de IA tarifavel no ambiente. Remover a variavel global do
usuario ou emendar a regra ratificada sao atos do Soberano, nao do
orquestrador — a missao lista "preflight nao verde" e "canal economico
ambiguo" como parada imediata, e ambos se aplicam.

## 4. Correcao honesta do runner (falso positivo proprio)

A primeira corrida (`preflight-20260730T162725Z.json`) acusou tambem
`P1A-PAYG-CONFIG tokens.access_token` para o codex. Causa: o runner
alimentava o `~/.codex/auth.json` INTEIRO a `auditar_config`, e
`tokens.access_token` e a **propria credencial OAuth** chatgpt — nao e
chave de API substituindo OAuth (escopo ratificado da auditoria P1-A:
`auth_mode` + `OPENAI_API_KEY`; `02_auditoria-economica.md` §2).
Corrigido em `preflight_atual.py::_config_persistida` (codex: somente
`auth_mode`, `OPENAI_API_KEY` e `config.toml`). O bloqueio por
`NVIDIA_API_KEY` e INDEPENDENTE desta correcao.

## 5. Diagnostico complementar (nao-oficial) — resultado

Para isolar o bloqueador, um diagnostico rotulado NAO-OFICIAL executou o
mesmo pipeline sobre um ambiente hipotetico identico exceto pela remocao
de `NVIDIA_API_KEY` (corrida enxuta: codex/claude/kimi; sondas reais de
diagnostico, timeout 60 s; nenhuma chamada de modelo). Nao gera
classificacao oficial. Resultado — **mesmo sem a variavel, os tres
provedores continuam BLOCKED**, por dois DEFEITOS LATENTES do proprio
pipeline ratificado, revelados agora porque a P1-A nunca executou o
pipeline com sensores reais (a coleta foi via `coletar.sh` em bash; os
testes usam sensores falsos — a mesma licao da P1-A.1: "auditar lendo
confirma; usar revela"):

| # | Defeito | Efeito | Reproducao |
|---|---|---|---|
| F-1 | `AdaptadorPreflight._argv` nao expande `~` de `espec.executavel` (claude: `~/.local/bin/claude`, kimi: `~/.kimi-code/bin/kimi`) | `FileNotFoundError` → `P1A-CLI-INDISPONIVEL` nos 2 | sonda direta com o tilde cru levanta `FileNotFoundError`; o MESMO comando com o caminho expandido responde rc=0 |
| F-2 | `_login_codex` so inspeciona **stdout**, mas `codex login status` imprime "Logged in using ChatGPT" em **stderr** (stdout vazio, rc=0) | login valido lido como ausente → `P1A-OAUTH-AUSENTE` | sonda crua registrada nesta sessao: `rc=0 stdout='' stderr='Logged in using ChatGPT'` |

Consequencia para o destrave: remover `NVIDIA_API_KEY` (caminho 1 do
§7) e NECESSARIO mas NAO SUFICIENTE — F-1 e F-2 precisam de correcao no
codigo ratificado da P1-A.1, com teste e revisao, antes de qualquer
preflight verde. A primeira corrida do diagnostico (frota completa,
timeout de sonda 120 s) foi abortada pelo orquestrador apos ~15 min sem
conclusao (sonda lenta/travada, provavelmente um dos CLIs via Git Bash);
a corrida enxuta acima e a que vale como evidencia.

## 6. Estado preservado

- Lock `p1b-ops` detido e renovado no momento desta parada (lease vivo).
- Arvore de trabalho: apenas `07_p1b/` novo (aditivo); nenhum arquivo
  pre-existente editado; `prova_central.json` no HEAD.
- Zero chamadas de modelo na P1-B; zero custo variavel; zero escrita
  externa (somente a copia datada autorizada); zero segredo/PII em
  artefato (somente NOMES de variaveis/campos registrados).
- Reserva P1-A.1 (revisao por 2 providers distintos) NAO executada:
  invocar providers com o canal economico em parada seria incorreto.
- Protocolo pre-registrado NAO iniciado (nenhuma WorkUnit, nenhuma
  RoutingDecision, nenhum selo, nenhuma rerota).

## 7. Caminhos de destrave (decisao do Soberano)

1. **Remover `NVIDIA_API_KEY`** do ambiente do usuario (ou ao menos da
   sessao de orquestracao), **corrigir F-1/F-2** em
   `06_p1a/preflight/` (com teste de regressao e revisao, como na
   P1-A.1) e re-executar `07_p1b/preflight_atual.py` — a missao retoma
   do ponto de parada.
2. **Emenda ratificada a regra economica** (ex.: tirar `nvidia` do
   escopo de bloqueio, mantendo-o no de sanitizacao), com revisao
   independente e regressao verde — caminho mais lento, altera controle
   ratificado na P1-A.1.
3. **STOP** da linha P1-B, se a presenca da credencial for julgada
   inaceitavel por si.

## 8. Decisao

**BLOCKED** — condicao externa (variavel de ambiente persistente da
estacao em familia de provedor tarifavel) + ambiguidade entre auditoria
humana P1-A e pipeline codificado P1-A.1. A missao NAO avancou alem das
pre-condicoes; nada do aceite foi produzido porque nada podia ser
produzido sem violar as regras de parada.
