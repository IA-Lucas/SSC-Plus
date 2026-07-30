---
id: SSC-DOC-06
titulo: Arquitetura-alvo do SSC+
tipo: arquitetura-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D6 — Arquitetura-alvo

> Desenho dos componentes do SSC+ (especificacao, sem implementacao). Contratos
> em D5; origem de cada decisao na Matriz D4. **Capacidade e risco sao eixos
> independentes**: L1/L2/L3 (experimental) para capacidade; C0–C3 (canonico,
> FND-04 §2) preservado para governanca.

## 1. Visao geral

```
                         ┌────────────────────────────┐
                         │       CONTROL PLANE        │
                         │  escalonamento · aprovacao │
                         │  humana · ciclo de vida    │
                         └─────────────┬──────────────┘
                                       │
   humano ──► ┌───────────────┐   ┌────▼─────┐   ┌────────────────┐
   aprovacao  │ POLICY        ├──►│  TASK    ├──►│ EXECUTION      │
   ◄── portao │ GATEWAY       │   │  ROUTER  │   │ GATEWAY        │
              │ fronteira ·   │   │ WorkUnit │   │ attempts ·     │
              │ portao custo/ │   │ Routing  │   │ retry/fallback │
              │ autonomia     │   │ Decision │   │ worktree       │
              └───────┬───────┘   └────┬─────┘   └───────┬────────┘
                      │                │                 │
              ┌───────▼────────────────▼─────────────────▼────────┐
              │                SESSION KERNEL                     │
              │  SessionEnvelope · ContextPackage · memoria ·     │
              │  Checkpoint · EventLog                            │
              └───────────────────────┬───────────────────────────┘
                                      │
              ┌───────────────────────▼───────────┐   ┌────────────────────┐
              │        EVIDENCE PLANE             │   │ PROVIDER ADAPTERS  │
              │ telemetria · custo medido · placar│   │ cli · openai-compat│
              │ hashes · trilha de auditoria      │   │ allowlist binarios │
              └───────────────────────────────────┘   └────────────────────┘
                                      ▲
              ┌───────────────────────┴───────────┐
              │        EVALUATION / JUDGE         │
              │ deterministica · juiz-llm indep.  │
              └───────────────────────────────────┘
```

## 2. Componentes

### 2.1 Session Kernel
O coracao: mantem a sessao logica viva entre processos.
- Custodia `SessionEnvelope`, `ContextPackage`, memoria da sessao, `Checkpoint`,
  `EventLog` (D5 §1, §3, §8).
- Monta ContextPackage com proveniencia completa (origem + hash por entrada);
  injeta memoria **so por `ID=SHA256`** (principio ADR-121 legado).
- Grava checkpoint validado (Juiz 1 deterministico) antes de suspender; retoma por
  checkpoint + offset do EventLog, nunca por inferencia.
- **Nao roteia, nao executa, nao julga.** Origem: REWRITE "sessao como objeto" +
  ADAPT estado assinado/fio/memoria (D4 §1, §5).

### 2.2 Task Router
Transforma intencao em trabalho roteavel.
- Intake (forja): despacho cru → WorkUnit com `intencao` ≤ 4.000 chars; acima,
  recusa (principio do forjador legado).
- Decomposicao: WorkUnit `decomposicao` → filhos com `parent_work_unit`, grafo
  aciclico, ≤12 filhos, anti-competicao, ondas topologicas.
- Emite RoutingDecision por WorkUnit **antes** de qualquer execucao: classificacao
  declarada com `confianca`; `baixa` = falha fechada (o classificador-regex do
  legado e **aposentado** — fragilidade medida, D4 §2).
- **Nao executa e nao julga**; suas decisoes passam pelo veto do Policy Gateway.

### 2.3 Policy Gateway
O portao que bloqueia.
- Verifica toda RoutingDecision contra a politica vigente (`politica_ref` do
  envelope): rota permitida, executor na politica, `classe_governanca` × `modo`
  coerentes.
- Portao de custo e autonomia **bloqueante**: nenhum gasto sem
  `aprovacao_custo_ref` hasheada cobrindo **modelo** e `pode_escrever` (herda o
  fechamento do ADR-121 legado).
- Guarda a fronteira de isolamento: nenhum ContextPackage atravessa caminho
  proibido (D2); conteudo externo entra rotulado como evidencia.
- **Nao julga merito** (espelha FND-04 §12): verifica conformidade, nao qualidade.

### 2.4 Execution Gateway
O braco.
- Materializa ExecutionAttempt a partir de RoutingDecision aprovada; captura
  estruturada da saida **obrigatoria** (a ausencia causou perda real no legado).
- Aplica a maquina de recuperacao (§4): retry tipado, fallback na ordem declarada,
  esgotamento → EscalationEvent.
- Modos de escrita: `read-only` (padrao do piloto), `worktree` (isolada, previa
  sem gasto, **merge so humano**, aceite por arquivo, rollback total — herda
  worktree/previa/mesclar do legado, com o defeito CRLF tratado como prova
  obrigatoria D7), `escrita-aprovada` (futuro, gate nominal de conectores).
- **Nao decide rota** (isso e do Router) **nem se julga** (isso e do Judge).

### 2.5 Control Plane
O ciclo de vida e a voz humana.
- Abertura/suspensao/retomada/encerramento de sessao; recebe EscalationEvent e o
  apresenta ao humano com o contexto minimo suficiente.
- Registra aprovacoes humanas (ato explicito e datado; **silencio nunca aprova** —
  GV-05 como disciplina local).
- Superficie = casca que **nao decide** (principio ADR-113: a TUI provou que a
  casca pode mudar com custo zero quando quem decide e o nucleo).

### 2.6 Evidence Plane
A memoria dos fatos.
- Telemetria append-only por evento; custo/tokens/latencia **medidos ou `null`
  honesto** (nunca estimado apresentado como medicao; custo fantasma do legado e
  contra-exemplo registrado).
- Placar por provedor/modelo/rota; projecoes descartaveis (SQLite) com
  equivalencia a fonte JSONL travada por teste (principio ADR-091).
- Emite as metricas do Plano de Prova (D7): qualidade, custo, latencia — com base
  de medicao declarada.

### 2.7 Provider Adapters
A fala com os provedores.
- Dois tipos bastam: `cli` (binario local, **allowlist fechada auditada** — o
  perfil-vetor de execucao do legado e o contra-exemplo) e `openai-compat`
  (endpoint + chave por ambiente).
- Provedor novo entra **no fim da fila**; promocao so por preferencia declarada
  com evidencia de prova viva.
- Nenhum adaptador contem logica de roteamento; erro bruto do provedor entra no
  classificador de falha do Execution Gateway (`falha-quota` tipada — lacuna do
  legado fechada por contrato).
- **Kimi K3:** candidato a piloto (evidencia externa `AC-01-VID-004`,
  **nao verificado**, zero endosso canonico). Entra — se entrar — como adaptador
  `openai-compat` no fim da fila, avaliado pelas tarefas-ouro do D7. Nota de
  proveniencia: handoff legado 2026-07-24 registra "Kimi K2.6 fora da rota
  (404/410)" — a candidatura e do K3, nao do K2.6, e permanece **a verificar**.

### 2.8 Evaluation / Judge
O veredito independente.
- Camada **deterministica** (Juiz 1): valida schemas, invariantes e checkpoints —
  antes de qualquer sucesso ser declarado.
- Camada **juiz-llm** (Juiz 2): julga WorkUnits de risco (`aguardando-juiz`),
  com independencia calculada por provedor **e** modelo **antes** de julgar;
  `verificador.modelo` declarado no veredito (o defeito ADR-109 nasceu da omissao).
  Fila minima de candidatos declarada — a fila de 2 nomes fixos **colapsou** no
  legado.
- Camada **humana**: o Soberano, para C2+ e Tipo 1.
- Quem executa nao verifica; quem propoe nao aprova (GV-04; ADR-0005 canonico como
  disciplina do laboratorio).

## 3. Eixos: capacidade × risco (independentes)

| Eixo | Escala | Natureza | Uso |
|---|---|---|---|
| **Capacidade** | `L1` mecanico/deterministico · `L2` generico com contexto · `L3` especializado/julgamento | **Vocabulario experimental do laboratorio** — o canonico **nao** define L1/L2/L3 (sua maturidade e o eixo de 7 valores de FND-08 §3.3) | Escolher o executor mais barato que atende a WorkUnit (`nivel_capacidade_atendido ≥ nivel_capacidade`) |
| **Risco/governanca** | `C0` editorial · `C1` operacional · `C2` estrutural · `C3` constitucional (+ Tipo 1/2) | **Semantica canonica preservada** (FND-04 §2), citada, nao redefinida | Decidir portoes: C2+ ou Tipo 1 = aprovacao humana previa; C3 = indelegavel ao humano |

Regras de independencia: EI-1 uma WorkUnit L3/C0 (julgamento sobre texto, sem
efeito no mundo) nao precisa de humano; uma L1/C2 (script mecanico que altera
estrutura) **precisa**. EI-2 nenhum dos dois eixos se substitui: capacidade alta
nao reduz portao de risco; risco baixo nao reduz exigencia de capacidade.
EI-3 se a escala L1/L2/L3 for um dia proposta ao canonico, entra como materia
propria (rito de FND-09 §11.2 — graduacao de instrumento), nunca como "o que o
canonico ja diz".

## 4. Recuperacao: sete conceitos distintos

| Conceito | Definicao operacional | Instrumento (D5) | Quem decide |
|---|---|---|---|
| **Retry** | Mesmo executor, mesma decisao, so falha transitoria, backoff com teto | RetryEvent | Execution Gateway (automatico, limitado a 3) |
| **Reparo** | Nova WorkUnit filha (`etapa`) com o erro no contexto; nao repete a mesma chamada | WorkUnit + RoutingDecision novos | Task Router |
| **Fallback** | Proximo executor da ordem declarada na mesma RoutingDecision | FallbackEvent | Execution Gateway (ordem da politica) |
| **Reroteamento** | Nova RoutingDecision que `supersede` a anterior (ex.: classe errada, modelo indisponivel) — **nova invocacao na mesma linhagem, sessao intacta** | RoutingDecision (`supersede`) | Task Router (+ veto Policy) |
| **Escalonamento** | Esgotamento, orcamento, ambiguidade ou juiz reprovou → humano | EscalationEvent | Control Plane → humano |
| **Validacao** | Verificacao por camada independente (deterministica/juiz-llm) | ValidationVerdict | Evaluation/Judge |
| **Aprovacao humana** | Ato explicito, datado, hasheado; indelegavel em C3/Tipo 1 | `resumo_aprovacao` / `aprovacao_custo_ref` | Humano (Soberano) |

## 5. Decisoes de desenho e origem (rastreabilidade)

| Decisao | Origem (fonte → decisao) |
|---|---|
| Sessao logica persistente via EventLog + Checkpoint | Legado ADR-054/109 (sessao e o produto; fio append-only) → REWRITE/ADAPT (D4) |
| Portao de custo/autonomia no Gateway, nao na casca | Legado ADR-094/121 (portao na casca funciona, mas a casca congela; o portao cobre modelo e escrita) → ADAPT |
| Classificacao declarada com falha fechada (sem regex) | Handoff 2026-07-28 (sequestro por rodape) → RETIRE mecanismo, REWRITE principio (D4 §2) |
| Captura estruturada obrigatoria | Handoff 2026-07-28 (perda real com `--print`) → REWRITE (D4 §3) |
| Juiz independente por provedor **e** modelo, fila minima | ADR-109 (fila colapsada; juiz no economico) → ADAPT (D4 §4) |
| Dois tipos de adaptador + allowlist | ADR-098 + handoff 2026-07-27 (perfil-vetor CRITICO) → ADAPT (D4 §3) |
| Capacidade × risco em eixos separados | FND-04 §2 (C0–C3 preservado) + ausencia de L1–L3 no canonico (verificado) → vocabulario experimental §3 |
| Worktree/previa/merge humano | ADR-093/109 + defeito CRLF real → ADAPT com prova obrigatoria (D7) |
| Nenhuma UI nesta fase | ADR-113 (casca nao decide) → REFERENCE; Control Plane minimal |

## 6. O que esta deliberadamente fora

- UI/TUI/painel (REFERENCE; fase posterior, se houver sinal).
- Aprendizado automatico de rotas (REFERENCE; propoe-e-nunca-aplica, futuro).
- Midia/mega-brain (RETIRE, fora do escopo de orquestracao).
- Multi-tenancy, rede distribuida, fila externa — sem gatilho observado (AF-41 do
  Contexto do Soberano: recusa de abstracao sem gatilho, respeitada aqui).
