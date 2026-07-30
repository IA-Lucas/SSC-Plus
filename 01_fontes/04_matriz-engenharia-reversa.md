---
id: SSC-DOC-04
titulo: Matriz de Engenharia Reversa do SuperCondutor
tipo: matriz-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D4 — Matriz de Engenharia Reversa

> Classificacao de cada ativo do SuperCondutor legado: **ADAPT | REWRITE |
> REFERENCE | RETIRE**. Insumo: Baseline D3 (hashes e evidencias la citadas).
>
> **Nota de autoridade:** a coluna "Goal consumidor" usa o roteamento da A4
> congelada (`_SAIDA-COMPANY-OS`, evidencia externa **nao normativa**):
> Skills→1.14, Tools & Models→1.15, Commands→1.16, Workflows→1.17, Agents→1.18,
> Execution & Evaluation→1.19, Vertical Proof→1.20, kernel tecnico→Epico 2.
> Indica **destino provisorio da proposta**, nao compromisso do canonico.
>
> **Classes:** ADAPT = conceito aproveitado com ajuste ao alvo · REWRITE =
> comportamento util, implementacao descartada · REFERENCE = lido como evidencia,
> nao reimplementado · RETIRE = nao aproveitar.

## 1. Nucleo de sessao e politica

| Ativo | Classe | Comportamento util | Evidencia | Dependencias | Risco | Destino no SSC+ | Goal consumidor |
|---|---|---|---|---|---|---|---|
| Sessao como objeto central ("a sessao **e** o produto") | REWRITE | Sessao com estado proprio, custo e autonomia como pre-condicao | ADR-054; `sessao/estado.py, contexto.py` | Acoplada a CLI local e repo git alvo | Media: conceito forte, implementacao amarrada a terminal | **Session Kernel** (D6) | Epico 2; 1.18 |
| Portao de custo + autonomia com aprovacao hasheada | ADAPT | Nenhum gasto sem aprovacao sobre resumo hasheado que cobre **modelo** e `pode_editar_arquivos` | ADR-054/121; `sessao/portao.py`; `test_portao_bloqueia` | Hash sobre resumo textual (formato fragil a mudanca de redacao) | Baixa | **Policy Gateway** (D6) | 1.15; 1.19 |
| Estado assinado (SHA-256 de insumos + HMAC local) com revalidacao por operacao | ADAPT | Integridade e deteccao de deriva da sessao; "trocar insumo = sessao nova" | `sessao/vinculo.py, estado.py`; `test_hardening` | Chave local por maquina (`.chave_sessao`) | Baixa | SessionEnvelope (D5) — campos `integridade` e `linhagem` | Epico 2 |
| `politica.json` — 7 rotas declarativas com ferramenta/modelo/effort/modo/autonomia | REWRITE | Politica de roteamento **declarativa e versionavel**, separada do codigo | `politica.json` v2 (hash em D3) | Schema informal; deriva interna conhecida (DV-6: aponta `executor.py`, registro mora em `adaptadores.py`) | Media: contrato ja derivou do codigo uma vez | RoutingDecision + Policy Gateway (D5/D6) | 1.15 |
| Catalogo de LLMs (`catalogo-llms.json`) + `kb/benchmark-inteligente-jul2026.md` | REFERENCE | Modelo de dados provedor/modelo/papel/cobranca; benchmark traduzido para roteamento | `config/catalogo-llms.json`; `kb/` | Dados de mercado pereciveis (precos, modelos) | Media: envelhece rapido; benchmark nao reverificado | Evidence Plane (referencia para RoutingDecision) | 1.15 |

## 2. Decomposicao e roteamento de tarefa

| Ativo | Classe | Comportamento util | Evidencia | Dependencias | Risco | Destino no SSC+ | Goal consumidor |
|---|---|---|---|---|---|---|---|
| Forjador (despacho cru → ato, 2 camadas, teto 4.000) | ADAPT | "Ato, nao tarefa": unidade minima roteavel com escopo recusado acima do teto | ADR-093; `sessao/forjador.py`; `test_forjador` | Meta-prompt de passe unico (1 chamada auxiliar faturavel) | Baixa | Task Router (intake → WorkUnit, D5/D6) | 1.17 |
| Decompositor (plano JSON validado deterministicamente; ondas topologicas; anti-competicao; ≤12 partes) | ADAPT | Decomposicao com validacao barata antes de pagar; contexto entre partes **por arquivo verbatim** (recusa >200 KB, nunca resumo) | ADR-093; `sessao/decompositor.py`; `test_decompositor` | Depende dos contratos externos de especialista (item 12) | Media: fluxo completo nunca exercitado e2e contra provedor real (DV-7) | Task Router (`parent_work_unit`, grafo de WorkUnits, D5) | 1.17; 1.19 |
| Classificador por regex | RETIRE (mecanismo) / REWRITE (principio) | Principio util: **ambiguidade = falha fechada** para julgamento; vocabulario travado por teste | `sessao/classificador.py`; handoff 2026-07-28 (sequestro por palavra de rodape) | Regex sobre texto livre — fragilidade medida em producao | **Alta**: falha conhecida e reproduzida | RoutingDecision com classificacao declarada + confianca + falha fechada (D5) | 1.15 |
| Regra "planejador caro × executor barato" (incl. inversao: planejador no economico) | REFERENCE | O legado **mede os dois lados**: economia por roteamento e o defeito de planejar no modelo barato | `sessao/adaptadores.py` (`modelo_para_rota`); handoff 2026-07-28-resolver; A4 `AC-01-VID-002` (alegacao "80%" **nao verificada**) | Nenhuma alem do catalogo de modelos | Media: regra repetida em fontes externas **sem medicao** (P-3 da A4); o SSC+ deve medir, nao assumir | RoutingDecision (`nivel_capacidade` L1/L2/L3 por etapa, D5); hipotese medida no Plano de Prova (D7) | 1.15; 1.19 |

## 3. Execucao e provedores

| Ativo | Classe | Comportamento util | Evidencia | Dependencias | Risco | Destino no SSC+ | Goal consumidor |
|---|---|---|---|---|---|---|---|
| Adaptadores de provedor (tipos `cli` e `openai_compat`; allowlist fechada de binarios) | ADAPT | Dois tipos cobrem todos os provedores; perfil nunca importa codigo; allowlist fecha vetor de execucao | ADR-098; `sessao/adaptadores.py`; handoff 2026-07-27 (defeito CRITICO de perfil-vetor, fechado) | CLIs externas instaladas; chave por env | Baixa | **Provider Adapters** (D6); ExecutionAttempt (D5) | 1.15 |
| Executor: retry so em transitorio (408/409/425/429/5xx, `Retry-After`, backoff 1,5→20s, 3x) + fallback sequencial com falha fechada | ADAPT | Distincao transitório × contrato; nao repetir 4xx | `sessao/executor.py`; `test_adaptadores` | Sem classificacao de erro no caminho CLI — **quota vira texto cru** (risco aberto medido) | Media: lacuna conhecida que o SSC+ deve fechar com RetryEvent/FallbackEvent tipados (D5) | **Execution Gateway** (D6); RetryEvent/FallbackEvent (D5) | 1.19 |
| Captura de saida de CLI | REWRITE | — (comportamento **ausente** no legado: `--print` descarta trabalho intermediario; perda de dado real medida; existe `stream-json` nao usado) | handoff 2026-07-28-diagnostico | Formato de stream varia por CLI | **Alta**: a ausencia ja causou perda real | ExecutionAttempt com captura estruturada obrigatoria (D5); provider falso no Plano de Prova (D7) | 1.19; Epico 2 |
| Sensor NIM / prova viva (`testar_nvidia.py`, prova viva de 5 modelos) | REFERENCE | Prova viva como criterio: modelo so entra em rota apos prova medida | `ferramentas/testar_nvidia.py`; handoff 2026-07-24; handoff 2026-07-27-a245 (Juiz 2 APROVADO sobre produto decomposto) | API NIM (paga/variavel) | Baixa | Plano de Prova — tarefas-ouro e piloto (D7) | 1.15; 1.20 |

## 4. Validacao e juizes

| Ativo | Classe | Comportamento util | Evidencia | Dependencias | Risco | Destino no SSC+ | Goal consumidor |
|---|---|---|---|---|---|---|---|
| Juiz 1 — validador de schema em subprocesso (`validar.py` + `saida.schema.json` + golden master) | ADAPT | Validacao deterministica do estado gravado **antes** do sucesso; golden master deliberado | `ferramentas/validar.py`; `specs/`; `test_validar` | Subconjunto proprio de JSON Schema (checagem cruzada) | Baixa (veredito ja dependeu de SO — ADR-091; matriz de CI mitiga) | ValidationVerdict deterministico (D5); Evaluation/Judge (D6) | 1.19 |
| Juiz 2 — juiz LLM independente (fila = todo conector ativo; independencia por provedor **e** modelo; `risco_do_plano` antes de pagar; rotas de risco nascem `AGUARDANDO_JUIZ2`) | ADAPT | Quem executa nao julga; previsao de risco do plano antes do gasto; veredito vira memoria | ADR-093/109; `sessao/juizes.py`; `test_juizes`; execucoes reais `6ec30f10…`/`db8df6f6…` | Precisa de ≥2 provedores ativos para independencia real | Media: **a fila ja colapsou** (2 nomes fixos — ADR-109); rejulgamento autorizado mostrou juiz barato acertando o fundo | **Evaluation/Judge** (D6) — independente por construcao, com fila minima declarada | 1.19; 1.20 |

## 5. Memoria, eventos e artefatos

| Ativo | Classe | Comportamento util | Evidencia | Dependencias | Risco | Destino no SSC+ | Goal consumidor |
|---|---|---|---|---|---|---|---|
| Fio JSONL append-only (um turno por linha; **referencia** de artefato, nunca conteudo; streaming por offset de bytes) | ADAPT | Log de eventos barato, greppable, base da conversa/SSE/retomada | ADR-109; `sessao/fio.py`; `test_fio_sse` | Disco local; rotacao manual (divida ADR-090) | Baixa | **EventLog** + Checkpoint (D5); Evidence Plane (D6) | Epico 2; 1.19 |
| Memoria com fonte verificavel, validade por tipo e lapide append-only | ADAPT | Lembranca exige procedencia; expiracao por tipo (7d/365d); esquecer nao apaga, lapida | ADR-098; `sessao/memoria.py`; `test_memoria_*` | `memoria.jsonl` sem poda (divida) | Baixa | Session Kernel — memoria da sessao logica (D5/D6) | Epico 2 |
| Worktree por parte + previa + aceite por arquivo (`git apply --include`) + rollback total | ADAPT | Execucao isolada, preview sem gasto, merge so aprovado, aceite parcial nao marca mesclado | ADR-093/109; `sessao/worktree.py, previa.py`; `test_worktree` (`TestFimDeLinha`) | Git no repo alvo; **defeito CRLF real** pos-correcao (`mesclar` nunca funcionou no repo real — teste e defeito compartilhavam premissa errada) | **Alta**: e2e nunca exercitado (DV-7); exige piloto com prova viva | Execution Gateway — modo worktree/preview/merge humano (D6/D7) | 1.19; 1.20 |
| Telemetria append-only + nomes OTel GenAI + SQLite como projecao descartavel | ADAPT | Telemetria serializada entre processos; `null` honesto quando a fonte nao mede; banco descartavel com equivalencia SQL×JSONL travada por teste | ADR-091; `sessao/telemetria.py, otel.py, banco.py`; `test_banco` | SQLite local | Baixa | **Evidence Plane** (D6) | 1.19 |
| Economia/relatorio (3 custos separados: teorico, API cobrada, premium; economia so com token em toda parte) | REFERENCE | Honestidade de medicao: nao somar o que nao foi medido; custo fantasma documentado (free tier como fatura) | `sessao/economia.py, relatorio.py`; handoff 2026-07-28 | Catalogo de precos perecivel | Media | Evidence Plane — metricas de custo do Plano de Prova (D7) | 1.15; 1.19 |
| Aprendizado (mediana, piso de 5 entregas, **propoe e nunca aplica**) | REFERENCE | Melhoria continua com gate humano por construcao | ADR-098; `sessao/aprendizado.py`; `test_aprendizado` | Telemetria acumulada | Baixa | Fora da fase 0.x; candidato a proposta futura | 1.19 |
| Retomada (briefing matinal custo zero, ordenado por consequencia) | REFERENCE | Sessao logica retoma contexto sem chamada paga | ADR-098; `sessao/retomada.py`; `test_memoria_retomada` | Fio + memoria | Baixa | SessionEnvelope/Checkpoint (D5) — principio de retomada na mesma linhagem | Epico 2 |

## 6. Superficies e perifericos

| Ativo | Classe | Comportamento util | Evidencia | Dependencias | Risco | Destino no SSC+ | Goal consumidor |
|---|---|---|---|---|---|---|---|
| TUI de fluxo stdlib (porta principal; confirmacao so onde ha gasto) | REFERENCE | Casca que nao decide; virada de formato com custo zero prova o desacoplamento | ADR-113; `sessao/tui.py`; `test_tui` (sensor anti-decisao via `tokenize`) | Terminal | Baixa | Nenhum (SSC+ 0.x nao constroi UI); principio "casca nao decide" vira regra do Control Plane (D6) | 1.16 |
| Extensao VSCode (casca JS, 16 casos de fumaca) | RETIRE | — (congelada desde ADR-113; superficie JS fora da suite Python; pendencia de duplicacao `.bak` nunca sanada) | ADR-094/113; `extensao-vscode/` | Editores especificos | Media (manutencao sem dono) | Nenhum | — |
| Painel HTTP (`painel.py`, `cockpit`) | REFERENCE | Observabilidade local | ADR-090 (token sem auth, DNS rebinding — corrigidos); `sessao/painel.py`; `test_producao` | Servidor local | Media: historico de seguranca exige redesenho se um dia existir | Nenhum na 0.x; Evidence Plane atende leitura | — |
| Mapa de especialidades + contratos externos (`agentes/**/especialista.md`, 53 arquivos, 5 usados) | REFERENCE | Contrato de especialista com tools/rota/schemas declarados; "quem mede nao conserta" | `config/mapa-especialidades.json`; CI vigiando `agentes/**` | **Acoplamento a enderecos fora do projeto** (ponto fragil 4 de D3) | Media: dependencia de estrutura de repo terceiro | ContextPackage (D5) carrega o contrato como conteudo, nao como caminho | 1.18 |
| Mega-brain / midia local (injecao de memoria por `ID=SHA256`; gate `AGUARDA_EXTRATOR_LOCAL`) | RETIRE | — (fora do escopo de orquestracao por tarefa; gate LGPD especifico do CEO) | ADR-121; `sessao/midia.py` | Extratores locais | Baixa | Nenhum | — |
| Docker/CI stdlib-only (matriz SO × Python; gate de diagnostico; cobertura piso 85) | REFERENCE | "Ambiente e fonte silenciosa de verde"; dependencia zero como politica | ADR-091; workflow CI; `Dockerfile`/`compose.yml` (hashes em D3) | Docker | Baixa | Pratica do repositorio SSC+ (ja adotada: zero dependencias) | Epico 2 |

## 7. Contagem e leitura da matriz

- **ADAPT: 14** — portao de custo/autonomia, estado assinado, forjador, decompositor,
  adaptadores de provedor, executor retry/fallback, Juiz 1, Juiz 2, fio/EventLog,
  memoria, worktree/previa/mesclar, telemetria/OTel/SQLite, catalogo de LLMs (dados
  como referencia adaptados ao modelo de dados), retomada (principio).
- **REWRITE: 4** — sessao como objeto, politica declarativa, captura de saida de CLI,
  classificador (principio de falha fechada preservado, mecanismo regex aposentado).
- **REFERENCE: 9** — regra planejador×executor, sensor/prova viva, economia/relatorio,
  aprendizado, TUI, painel, mapa de especialidades, Docker/CI, catalogo/benchmark.
- **RETIRE: 3** — classificador regex (mecanismo), extensao VSCode, mega-brain/midia.

**Leituras cruzadas obrigatorias:** (1) os dois riscos **Altos** (captura de CLI;
worktree e2e) entram no Plano de Prova (D7) como provas obrigatorias, nao como
suposicoes; (2) nenhum item ADAPT autoriza copia de codigo — o destino e sempre um
contrato/componente do D5/D6, implementado greenfield; (3) promocao de qualquer
linha ao canonico passa pelo protocolo D8 e pelo portao G1–G5 de ADR-0007 §5.3.
