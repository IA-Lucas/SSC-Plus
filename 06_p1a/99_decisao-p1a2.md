---
id: SSC-DEC-P1A2
titulo: Relatorio e Decisao da Missao SSC+ P1-A.2 — capsula subscription-only e compatibilidade real
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Relatorio e Decisao — Missao SSC+ P1-A.2

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Trabalho aditivo sobre o HEAD `8ba75de…` + commit de parada
> `cf61e0d` (07_p1b preservado byte a byte). `NVIDIA_API_KEY` global/HKCU
> jamais removida, alterada ou persistida — verificado por existencia
> (nome/tipo/tamanho), nunca por valor.

## DECISAO: **ADJUST**

A capsula subscription-only foi entregue e provada; F-1/F-2 estao
corrigidos e cobertos por 27 regressoes; o preflight real dentro da
capsula executou sem violacao economica. Mas o preflight NAO ficou verde:
os tres provedores necessarios bateram em **bloqueios factuais da
especificacao** (§4) — os CLIs nao expoem plano e/ou nao tem descoberta
de modelos headless nos comandos especificados na P1-A. A missao diz
"nao forcar resultado": em vez de afrouxar portoes ratificados por conta
propria, as emendas de especificacao vao propostas ao Soberano (§6).
A revisao por 2 providers (condicionada a preflight verde) fica para o
ciclo das emendas. P1-B-02 NAO abre neste estado.

## 1. Pre-condicoes (verificadas)

| Item | Resultado |
|---|---|
| HEAD `8ba75de…`, sem tag/remoto | OK |
| P1-B-01 encerrada como BLOCKED | OK — renovacao parada, lock do SO livre, sucessor adquiriu `p1b-ops` com fencing **2 > 1** pelas APIs e liberou; nenhum lock apagado manualmente |
| Arvore limpa, ancestralidade | OK |
| P0 100/100 + P1-A 211/211 + prova 18/18 | OK (reexecutadas na abertura) |
| Copia datada | OK — `SSC-Plus_copia-p1a2-20260730-170255`, diff vazio |
| 07_p1b preservado byte a byte | OK — commit exclusivo de parada `cf61e0d`, staging explicito (4 arquivos), sem locks/runtime/segredos |
| Novo lock operacional | OK — `locks/p1a2-ops.*`, lease renovado a 60 s por processo dedicado durante toda a missao |

## 2. Capsula subscription-only (`06_p1a/capsula.py`)

- `ambiente_capsula(env)`: copia do ambiente SEM nenhuma credencial de
  modelo (regra ampla `_nome_payg`: `*_API_KEY`, `*_AUTH_TOKEN`,
  `*_ACCESS_TOKEN`, `*_API_SECRET`, `*_SECRET_KEY`, `*_BEARER_TOKEN`,
  variantes de caixa/separador e chaves conhecidas). Nunca muta o
  ambiente de origem; reauditoria fail-closed apos a filtragem.
- `exigir_capsula_limpa()`: guarda de entrada — credencial visivel no
  processo aborta ANTES de qualquer sonda/escrita.
- `iniciar_em_capsula(argv, ...)`: entry point — argv em LISTA,
  `shell=False`, env-filho fresco; `main()` permite
  `python 06_p1a/capsula.py <argv do SSC+>`.
- Adendo de politica: `06_adendo-capsula-p1a2.md` — a leitura manual da
  P1-A ("NVIDIA fora da frota, so sanitiza") fica SUPERADA pela politica
  estrita P1-A.1 **dentro da capsula**; relatorios historicos nao
  reescritos.

## 3. Correcoes F-1/F-2 (`preflight/adaptadores.py`)

- **F-1**: `_argv` expande SOMENTE o `~` do executavel
  (`os.path.expanduser`) — sem expandvars, sem shell, sem hardcode;
  argumentos preservados em lista; caminho inexistente ->
  `CliIndisponivel`. Cura os falsos `P1A-CLI-INDISPONIVEL` de
  claude/kimi da P1-B-01.
- **F-2**: `_login_codex` avalia stdout+stderr combinados em memoria
  (`codex login status` imprime em stderr). rc!=0 ou marcador negativo
  vence; conflito entre canais -> desconhecido/BLOCKED; saida bruta
  nunca persistida.

Regressoes novas: `tests/test_capsula_p1a2.py` — **27 testes** (capsula,
injecao NVIDIA pre-sonda nos 5 providers, F-1 til/expandvars/espacos/
metacaracteres/inexistente, F-2 stdout/stderr/ambos/rc/negacao/conflito/
quota, zero segredo em erro/excecao/env-filho).

## 4. Preflight real dentro da capsula — resultado factual

Runner: `06_p1a/preflight_capsula.py` (executado via
`python 06_p1a/capsula.py python 06_p1a/preflight_capsula.py`).
Evidencia: `evidencias/p1a2-preflight-20260730T211748Z.json` + sondas
cruas redigidas em `evidencias/p1a2-sondas-cruas.txt`. Somente
version/login/model-list oficiais; **zero prompt/geracao; custo
variavel 0**.

| Provider | Resultado | Causa factual (sonda crua) |
|---|---|---|
| codex | BLOCKED `P1A-PLANO-DESCONHECIDO` | login OK via F-2 ("Logged in using ChatGPT", stderr), mas o CLI **nao expoe o plano**; `codex models` falha: "stdin is not a terminal" (descoberta TTY-only). `codex doctor` expoe o modelo efetivo (`gpt-5.6-sol`) e `stored auth mode chatgpt` — headless |
| claude | BLOCKED `P1A-MODELO-REMOVIDO` | plano `max` OK via `auth status`; `claude models` e **interativo** (timeout headless; `models list` idem) — sem descoberta headless no comando especificado |
| kimi | BLOCKED `P1A-PLANO-DESCONHECIDO` | `provider list` mostra `managed:kimi-code … source=oauth` e `Default model: kimi-code/k3`, mas **nao expoe o plano** (Allegretto e da conta); descoberta de modelos OK |
| google | SUPERVISED | regra da missao (classificacao estatica; sonda nao necessaria — ver §5) |
| grok | SUPERVISED | idem |

Leitura honesta: NAO e regressao da capsula nem de F-1/F-2 (esses
funcionam: login codex lido do stderr, tils resolvidos, zero violacao
economica). E a **especificacao estatica da P1-A** exigindo dos CLIs
evidencia que eles nao emitem headless: plano observavel (codex, kimi) e
listagem de modelos nao interativa (codex, claude). A P1-A classificou
ELIGIBLE com plano DECLARADO pelo humano; o pipeline codificado exige
plano observavel — mesma classe de divergencia humano×codigo da
NVIDIA_API_KEY, resolvida la pela politica estrita + capsula, e aqui
pendente de emenda de especificacao.

## 5. Desvios e incidentes da execucao (declarados)

- Duas corridas de preflight full-fleet (5 providers) abortadas: sondas
  de google/grok via Git Bash **penduram** — netos node/npm herdam o
  pipe e o timeout do subprocess nao mata a arvore (uma na P1-B-01, uma
  nesta missao). Decisao: google/grok classificados estaticamente
  SUPERVISED (a missao os declara "nao necessarios"); sondas reais so
  para codex/claude/kimi. Lacuna registrada: timeout nao mata arvore de
  processos — candidata a correcao futura no sensor.
- `prova_central.json` regenerado pelas reexecucoes foi restaurado ao
  HEAD (identificadores nao-deterministicos), como nas missoes anteriores.

## 6. Emendas propostas ao Soberano (NAO aplicadas nesta missao)

1. **Plano**: admitir `plano=desconhecido-no-cli` com OAuth/chatgpt
   comprovado + declaracao humana registrada (como a P1-A fez), em vez
   de BLOCKED — ou manter o portao e aceitar que codex/kimi so
   elegiveis com atestado humano renovado por execucao.
2. **Descoberta codex**: trocar a sonda de modelos para `codex doctor`
   (headless; expoe `model gpt-5.6-sol` e auth mode).
3. **Descoberta claude**: substituir `claude models` (interativo) por
   evidencia headless alternativa (ex.: modelo efetivo via `auth status`
   ou declaracao registrada), ou aceitar ausencia de descoberta com
   plano observado.
4. Cada emenda com teste de regressao + revisao independente (2
   providers, max 1 chamada cada, custo variavel 0) antes de novo
   preflight.

## 7. Threat review (P1-A.2)

| Ameaca | Mitigacao | Estado |
|---|---|---|
| Credencial global vaza para o processo SSC+ | capsula gera env-filho; guarda de entrada aborta; reauditoria fail-closed | coberto por teste |
| SSC+ altera o ambiente global/HKCU | capsula nunca muta a origem (teste); nenhuma escrita fora do lab | verificado |
| Valor de segredo em artefato/teste/excecao | so NOMES em erros; varredura de padroes; SENTINELA ficticia nos testes; redacao `<USUARIO>` | coberto por teste + varredura |
| Metacaracteres/espacos no executavel (F-1) | argv-lista + shell=False; expanduser so no executavel; sem expandvars | coberto por teste |
| Login por inferencia no codex (F-2) | rc!=0/negacao vencem; conflito de canais -> BLOCKED | coberto por teste |
| Timeout nao mata arvore de processos (npm/gitbash) | mitigado por escopo (google/grok estaticos); **lacuna aberta** (§5) | aberto (nao bloqueante) |

## 8. Validacao final

| Exigencia | Estado |
|---|---|
| P0 100/100 | OK |
| P1-A 211+27 = 238/238 | OK |
| Prova central 18/18 | OK |
| NVIDIA_API_KEY global intacta | OK (existencia verificada; valor nunca registrado) |
| Capsula: NVIDIA_API_KEY ausente no processo SSC+ e filhos | OK (teste + preflight real na capsula) |
| Injecao NVIDIA na capsula bloqueia pre-sonda | OK (teste, 5 providers, 0 sondas) |
| Zero chamada produtiva de modelo | OK — somente sondas de diagnostico; nenhuma revisao invocada (condicionada a preflight verde) |
| Custo variavel | 0 |
| Zero escrita canonica | OK |
| Commit curado por staging explicito, sem tag/remoto | OK — ver §9 |

## 9. Commits desta missao

1. `cf61e0d` — parada P1-B-01 (07_p1b preservado byte a byte).
2. (correcoes P1-A.2 — staging explicito: capsula, adaptadores, testes,
   adendo, runner de preflight da capsula, runner de revisao, evidencias)
   — hash registrado no fechamento (nao pode constar no proprio commit).

## 10. Condicoes para P1-B-02 (quando as emendas forem decididas)

- Aplicar as emendas de especificacao decididas (§6) com regressao e
  revisao independente; preflight na capsula verde para codex/claude/kimi
  (ou bloqueio factual aceito e ratificado).
- P1-B-02 abre repetindo TODAS as precondicoes sob novo HEAD, novo lock
  (fencing superior) e nova tentativa; reutiliza apenas a evidencia
  imutavel da parada P1-B-01.
- Resolver a lacuna do timeout que nao mata arvore de processos antes de
  qualquer sonda futura em google/grok.
