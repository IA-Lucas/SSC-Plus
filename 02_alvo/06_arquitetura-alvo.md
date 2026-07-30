---
id: SSC-DOC-06
titulo: Arquitetura-alvo do SSC+
tipo: arquitetura-experimental
versao: 0.2.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
atualizado_em: 2026-07-30
---

# D6 — Arquitetura-alvo

> Desenho dos componentes do SSC+ (especificacao). Contratos em D5 (v0.2.0);
> origem de cada decisao na Matriz D4. **Capacidade e risco sao eixos
> independentes**: L1/L2/L3 (experimental) + perfil de capacidade; C0–C3 e
> Tipo 1/2 (canonico, FND-04 §2) preservados para governanca.
>
> **v0.2.0** — corrigida pela revisao independente SSC-REV-02 (PORTAO 1 da
> Missao 0.2). Diff contra v0.1.0 em `02_alvo/diffs/d6-v0.1.0-v0.2.0.diff`.

## 1. Visao geral

Fluxo de decisao: **Router propoe → Policy veta → Execution executa.** O Session
Kernel e o **unico escritor** do EventLog; todos os demais componentes emitem
fatos ao Kernel. O Evidence Plane **apenas le o log e projeta**.

```
                         ┌────────────────────────────┐
                         │       CONTROL PLANE        │
                         │  escalonamento · aprovacao │
                         │  humana · ciclo de vida    │
                         └─────────────┬──────────────┘
                                       │
              ┌───────────────┐   ┌────▼─────┐   ┌────────────────┐
   intencao ─►│  TASK         ├──►│ POLICY   ├──►│ EXECUTION      │
              │  ROUTER       │   │ GATEWAY  │   │ GATEWAY        │
              │ WorkUnit ·    │   │ fronteira│   │ attempts ·     │
              │ Routing       │   │ portao   │   │ retry/fallback │
              │ Decision      │   │ custo/   │   │ worktree       │
              └───────┬───────┘   │ autonomia│   └───────┬────────┘
                      │           └────┬─────┘           │
                      │     fatos (nao escrevem o log)   │
              ┌───────▼────────────────▼─────────────────▼────────┐
              │                SESSION KERNEL                     │
              │  SessionEnvelope · ContextPackage · memoria ·     │
              │  Checkpoint · EventLog (ESCRITOR UNICO) · CAS     │
              └───────────────────────┬───────────────────────────┘
                                      │ leitura (somente)
              ┌───────────────────────▼───────────┐   ┌────────────────────┐
              │        EVIDENCE PLANE             │   │ PROVIDER ADAPTERS  │
              │ telemetria · custo medido · placar│   │ cli · openai-compat│
              │ projecoes · trilha de auditoria   │   │ allowlist binarios │
              └───────────────────────────────────┘   └────────────────────┘
                                      ▲
              ┌───────────────────────┴───────────┐
              │        EVALUATION / JUDGE         │
              │ deterministica (veta) · juiz-llm  │
              └───────────────────────────────────┘
```

## 2. Componentes

### 2.1 Session Kernel
O coracao: mantem a sessao logica viva entre processos.
- Custodia `SessionEnvelope`, `ContextPackage`, memoria da sessao, `Checkpoint`,
  `EventLog` e o CAS (D5 §1, §3, §8).
- **Escritor unico do EventLog:** recebe fatos tipados de Router, Policy,
  Execution, Judge e Control Plane; atribui `seq`, `causado_por`,
  `idempotency_key` e `prev_event_hash`; grava. Deduplicacao por
  `idempotency_key`; recusa de evento fora de schema ou com segredo (IC-4).
- Aplica as maquinas de estado (D5 §1.2, §2.1, §5.1): transicao fora da tabela =
  recusa com evento.
- Valida vinculos: attempt cuja RoutingDecision nao e vigente ou cujos
  `vinculos` divergem do estado corrente = falha de contrato antes do gasto.
- Monta ContextPackage com proveniencia completa; injeta memoria **so por
  `ID=SHA256`**; scanner de segredos (IC-4) e contencao de caminho (IC-5) na
  montagem.
- Grava checkpoint validado (Juiz 1 deterministico) antes de suspender; retoma
  por checkpoint + cadeia de hash do EventLog, nunca por inferencia; estado
  corrente **reconstruivel por replay deterministico do log** (IP-4).
- **Nao roteia, nao executa, nao julga.**

### 2.2 Task Router
Transforma intencao em trabalho roteavel. **Propoe; nao executa, nao julga, nao
grava no log.**
- Intake (forja): despacho cru → WorkUnit com `intencao` ≤ 4.000 chars e
  `criterios_aceite_ref` **congelados** na proposta; acima do teto, recusa.
- Decomposicao: WorkUnit `decomposicao` → filhos com `parent_work_unit`, grafo
  aciclico, ≤12 filhos, anti-competicao, ondas topologicas.
- Emite RoutingDecision por WorkUnit **antes** de qualquer execucao, com
  `vinculos` completos (6 hashes, D5 §4); classificacao declarada com
  `confianca`; `baixa` = falha fechada.
- Reroteamento = nova RoutingDecision que `supersede` a anterior (nova invocacao
  na mesma linhagem, sessao intacta); submete toda decisao ao veto da Policy.

### 2.3 Policy Gateway
O portao que bloqueia. **Veta; nao julga merito, nao executa.**
- Verifica toda RoutingDecision contra a politica vigente (`politica_ref` do
  envelope): rota permitida, executor na politica e no catalogo,
  `classe_governanca` × `modo` coerentes, `perfil_capacidade` atendido.
- Portao de custo e autonomia **bloqueante**: nenhum gasto sem
  `aprovacao_custo` **envelope** (D5 §4): modelos permitidos (lista), efforts
  permitidos, teto, modo, validade nao expirada e regra de fallback. Selecao
  fora do envelope = veto, mesmo que o modelo esteja na politica.
- Verifica o orcamento da sessao antes de autorizar cada attempt; estouro =
  EscalationEvent (`orcamento`), nunca estouro silencioso.
- Guarda a fronteira de isolamento: nenhum ContextPackage atravessa caminho
  proibido (D2/IC-5); conteudo externo entra rotulado como evidencia.

### 2.4 Execution Gateway
O braco. **Executa; nao decide rota, nao se julga, nao grava no log.**
- Materializa ExecutionAttempt a partir de RoutingDecision aprovada; registra
  `selecao_solicitada`, `executor_resolvido` (com `hash_catalogo` e
  `alias_usado`) e `executor_observado` (ou `null` honesto); divergencia
  observado ≠ resolvido = evento tipado (D5 §5).
- Captura estruturada da saida **obrigatoria**; classificacao de falha tipada,
  incluindo `falha-quota` e **`indeterminado`** (efeito externo incerto).
- Aplica a maquina de recuperacao (§4): retry tipado **sob IR-1** (idempotente
  ou comprovadamente nao aplicado), fallback na ordem declarada **dentro** do
  envelope de custo, esgotamento → EscalationEvent.
- Modos de escrita: `read-only` (padrao do piloto), `worktree` (isolada, previa
  sem gasto, **merge so humano**, aceite por arquivo, rollback total — defeito
  CRLF como prova obrigatoria D7), `escrita-aprovada` (futuro).

### 2.5 Control Plane
O ciclo de vida e a voz humana. **Apresenta e registra; nao decide rota.**
- Abertura/suspensao/retomada/encerramento de sessao (tabela D5 §1.2); recebe
  EscalationEvent e o apresenta ao humano com o contexto minimo suficiente.
- Registra aprovacoes humanas (ato explicito, datado, hasheado; **silencio nunca
  aprova** — GV-05 como disciplina local), incluindo o envelope `aprovacao_custo`.
- Superficie = casca que **nao decide** (principio ADR-113).

### 2.6 Evidence Plane
A memoria dos fatos. **Somente leitura e projecao sobre o EventLog** — nao
escreve no log nem no CAS (correcao do item 11: em v0.1.0 havia "telemetria
append-only por evento", um escritor paralelo; aposentado).
- Consome o EventLog por leitura (cadeia verificada) e projeta: telemetria,
  custo/tokens/latencia **medidos ou `null` honesto** (nunca estimado
  apresentado como medicao).
- Placar por provedor/modelo/rota, incluindo divergencias observado ≠ resolvido;
  projecoes descartaveis (SQLite) com equivalencia a fonte JSONL travada por
  teste (principio ADR-091).
- Emite as metricas do Plano de Prova (D7): qualidade, custo, latencia — com
  base de medicao declarada.

### 2.7 Provider Adapters
A fala com os provedores. Na P0: **apenas adaptadores falsos deterministicos
por seed** (D7); nenhum adaptador real, nenhuma rede.
- Dois tipos bastam: `cli` (binario local, **allowlist fechada auditada**) e
  `openai-compat` (endpoint + chave por ambiente) — ambos **fora** da P0.
- Todo adaptador declara o que observa: preenche `executor_observado` ou admite
  `null`; declara `efeito_externo` (`nenhum`/`aplicado`/`nao-aplicado`/`incerto`).
- Provedor novo entra **no fim da fila**; promocao so por preferencia declarada
  com evidencia de prova viva.
- Nenhum adaptador contem logica de roteamento; erro bruto entra no
  classificador de falha do Execution Gateway.
- **Kimi K3:** candidato a piloto (evidencia externa `AC-01-VID-004`,
  **nao verificado**, zero endosso canonico). Entra — se entrar — como adaptador
  `openai-compat` no fim da fila, avaliado pelas tarefas-ouro do D7.

### 2.8 Evaluation / Judge
O veredito independente. **Julga; nao executa, nao grava no log.**
- Camada **deterministica** (Juiz 1): valida schemas, invariantes, checkpoints e
  criterios mecanicos — **antes** de qualquer sucesso ser declarado. Seu
  `reprovado` **veta e nao e anulavel** por juiz-llm nem por humano sobre o
  mesmo artefato (IV-2); so novo artefato reabre julgamento.
- Camada **juiz-llm** (Juiz 2): julga WorkUnits de risco
  (`aguardando-validacao`), com independencia calculada por provedor **e**
  modelo — sobre `executor_observado` quando disponivel — **antes** de julgar;
  `pacote_juiz` completo no veredito (provedor/modelo/effort/rubrica_ref/seed).
  Fila minima de candidatos declarada. Na P0, o juiz-llm e **falso e
  deterministico por seed** (mesmo regime dos providers).
- Camada **humana**: o Soberano, para C2+ e Tipo 1.
- Todo veredito vincula `attempt_id`, `criterios_ref` (= congelado da WorkUnit)
  e `contexto_ref` (D5 §7).

## 3. Eixos: capacidade × risco (independentes)

| Eixo | Escala | Natureza | Uso |
|---|---|---|---|
| **Capacidade** | `L1` mecanico/deterministico · `L2` generico com contexto · `L3` especializado/julgamento — **+ perfil** (abaixo) | **Vocabulario experimental do laboratorio** — o canonico **nao** define L1/L2/L3 | Escolher o executor mais barato que atende a WorkUnit |
| **Risco/governanca** | `C0` editorial · `C1` operacional · `C2` estrutural · `C3` constitucional (+ Tipo 1/2) | **Semantica canonica preservada** (FND-04 §2), citada, nao redefinida | Decidir portoes: C2+ ou Tipo 1 = aprovacao humana previa; C3 = indelegavel ao humano |

**Perfil de capacidade (complemento obrigatorio do nivel):** alem de L1–L3,
WorkUnit e executor carregam um perfil com 8 dimensoes (D5 §2): `modalidade`,
`ferramentas`, `formato_saida`, `contexto_max_tokens`, `dominio`, `privacidade`,
`latencia_max_ms`, `orcamento_max_custo`. Regra de casamento: o executor
escolhido atende **todas** as dimensoes exigidas (ex.: WorkUnit
`privacidade=local-only` nunca roteia para executor remoto; WorkUnit
`formato_saida=json-schema` exige executor com saida estruturada). Falta de
casamento = falha fechada, nao degradacao silenciosa.

Regras de independencia: EI-1 uma WorkUnit L3/C0 nao precisa de humano; uma
L1/C2 **precisa**. EI-2 nenhum dos dois eixos se substitui. EI-3 se a escala
L1/L2/L3 for um dia proposta ao canonico, entra como materia propria (rito de
FND-09 §11.2), nunca como "o que o canonico ja diz".

## 4. Recuperacao: sete conceitos distintos

| Conceito | Definicao operacional | Instrumento (D5) | Quem decide |
|---|---|---|---|
| **Retry** | Mesmo executor, mesma decisao, so falha transitoria, backoff com teto — **e so se idempotente (`idempotency_key`) ou comprovadamente nao aplicada**; efeito incerto = `indeterminado`, sem retry (IR-1/IR-2) | RetryEvent | Execution Gateway (automatico, limitado a 3) |
| **Reparo** | Nova WorkUnit filha (`etapa`) com o erro no contexto, ou reprovada de volta a `proposta`; nao repete a mesma chamada | WorkUnit + RoutingDecision novos | Task Router |
| **Fallback** | Proximo executor da ordem declarada na mesma RoutingDecision, **dentro do envelope `aprovacao_custo`** | FallbackEvent | Execution Gateway (ordem da politica) |
| **Reroteamento** | Nova RoutingDecision que `supersede` a anterior — **nova invocacao na mesma linhagem, sessao intacta** | RoutingDecision (`supersede`) | Task Router (+ veto Policy) |
| **Escalonamento** | Esgotamento, orcamento, ambiguidade, `indeterminado` ou juiz reprovou → humano | EscalationEvent | Control Plane → humano |
| **Validacao** | Verificacao por camada independente; **deterministica veta e nao e anulavel por LLM** | ValidationVerdict | Evaluation/Judge |
| **Aprovacao humana** | Ato explicito, datado, hasheado; indelegavel em C3/Tipo 1; custo aprovado como **envelope**, nao modelo fixo | `resumo_aprovacao` / `aprovacao_custo` | Humano (Soberano) |

Crash entre despacho e conclusao: na retomada, o attempt sem evento de conclusao
e marcado `orfao` e tratado como `indeterminado` (IR-2) — nunca como sucesso.

## 5. Decisoes de desenho e origem (rastreabilidade)

| Decisao | Origem (fonte → decisao) |
|---|---|
| Sessao logica persistente via EventLog + Checkpoint | Legado ADR-054/109 → REWRITE/ADAPT (D4) |
| EventLog com escritor unico, cadeia de hash e idempotencia | Revisao SSC-REV-02 (itens 7/11) + principio do fio legado → REWRITE |
| CAS local, leitura verificada, contencao de caminho | Revisao SSC-REV-02 (itens 6/10) + IC-5 → REWRITE |
| Portao de custo/autonomia como **envelope** no Gateway | Legado ADR-094/121 + revisao SSC-REV-02 (item 12) → ADAPT |
| Classificacao declarada com falha fechada (sem regex) | Handoff 2026-07-28 → RETIRE mecanismo, REWRITE principio (D4 §2) |
| Captura estruturada obrigatoria | Handoff 2026-07-28 (perda real com `--print`) → REWRITE (D4 §3) |
| Identidade de executor em 3 camadas (solicitado/resolvido/observado) | Revisao SSC-REV-02 (item 4): alias nao prova identidade → REWRITE |
| Retry condicionado a idempotencia; `indeterminado` | Revisao SSC-REV-02 (item 8) → REWRITE |
| Juiz independente, precedencia deterministica, veredito vinculado | ADR-109 (fila colapsada; juiz no economico) + revisao SSC-REV-02 (item 9) → ADAPT |
| Dois tipos de adaptador + allowlist | ADR-098 + handoff 2026-07-27 → ADAPT (D4 §3); **P0: somente falsos** |
| Capacidade × risco em eixos separados + perfil de 8 dimensoes | FND-04 §2 + ausencia de L1–L3 no canonico + revisao SSC-REV-02 (item 5) → vocabulario experimental §3 |
| Worktree/previa/merge humano | ADR-093/109 + defeito CRLF real → ADAPT com prova obrigatoria (D7) |
| Nenhuma UI nesta fase | ADR-113 (casca nao decide) → REFERENCE; Control Plane minimal |

## 6. O que esta deliberadamente fora

- UI/TUI/painel (REFERENCE; fase posterior, se houver sinal).
- Aprendizado automatico de rotas (REFERENCE; propoe-e-nunca-aplica, futuro).
- Midia/mega-brain (RETIRE, fora do escopo de orquestracao).
- Adaptadores reais, rede, multiusuario, integracao canonica — fora da P0 por
  definicao da Missao 0.2.
- Multi-tenancy, rede distribuida, fila externa — sem gatilho observado (AF-41).
