---
id: SSC-DOC-05
titulo: Contratos-alvo do SSC+
tipo: especificacao-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D5 — Contratos-alvo (especificacao, sem implementacao)

> Contratos do modelo de orquestracao por tarefa em sessao logica persistente.
> **Especificacao apenas** — nenhum codigo existe nesta fase. Nomes e campos sao
> vocabulario experimental do laboratorio: **nao** sao entidades do Meta Model
> canonico (FND-09 §5 nao preve Sessao/Tarefa/Execucao) e **nao** usam IDs
> canonicos. Se um dia forem propostos ao canonico, passam pelo protocolo D8.

## 0. Semantica central (vincula todos os contratos)

1. **A sessao logica e o objeto de vida longa.** Ela mantem memoria, contexto,
   orcamento e permissoes. Processos, processos-filho, CLIs e chamadas de API vêm e
   vão; a sessao logica persiste por EventLog + Checkpoint.
2. **Cada WorkUnit (ou etapa) escolhe** ferramenta, provedor, modelo, effort, modo
   e controle — decisao registrada em RoutingDecision **antes** da execucao.
3. **Trocar de modelo cria uma nova invocacao na mesma linhagem** — um novo
   ExecutionAttempt (e um novo evento de reroteamento) **dentro** da mesma sessao
   logica. A sessao nao reinicia; a linhagem (`linhagem_id`) nao muda.
4. **Quem executa nao verifica; quem propoe nao aprova.** Validacao e julgamento
   sao contratos separados da execucao (ValidationVerdict).
5. **Falha fechada:** ambiguidade de classificacao, provedor fora da politica ou
   contrato violado interrompem antes do gasto — nunca "seguir com o mais proximo".
6. **Referencia, nao conteudo:** eventos e vereditos guardam referencias
   (`sha256`) de artefatos, nao o conteudo (principio do fio legado, ADR-109).

Convencao de tipos: `id` = identificador local opaco (nao canonico) · `ts` =
timestamp ISO-8601 UTC · `sha256` = hash de conteudo · `enum` = lista fechada.

## 1. SessionEnvelope

O envelope da sessao logica. Um por sessao; imutavel nos campos de identidade.

| Campo | Tipo | Semantica |
|---|---|---|
| `sessao_id` | id | Identidade da sessao logica; nunca muda |
| `linhagem_id` | id | Linhagem da conversa/trabalho; igual a `sessao_id` na criacao; **imutavel** mesmo com troca de modelo, provedor ou ferramenta |
| `criado_em` / `encerrado_em` | ts | Vida da sessao logica |
| `estado` | enum(`ativa`,`suspensa`,`retomada`,`encerrada`) | Suspensa = checkpoint gravado, sem processo vivo; retomada = mesma sessao, novo processo |
| `escopo` | objeto | `repo_alvo` (caminho), `modo` (`read-only` \| `worktree` \| `escrita-aprovada`), `fronteiras` (lista de caminhos proibidos) |
| `permissoes` | objeto | Capacidades concedidas pelo humano: `pode_escrever`, `pode_executar`, `pode_rede`, `conectores_com_escrita` (lista nominal — herda o gate do ADR-121 legado) |
| `orcamento` | objeto | `teto_custo`, `teto_tokens`, `teto_tempo`, `consumido_*` (medidos); estouro = EscalationEvent, nunca estouro silencioso |
| `politica_ref` | sha256 | Hash da politica de roteamento vigente na abertura |
| `integridade` | objeto | `assinatura_insumos` (sha256 de repo/perfil/politica/catalogo) + `selo` (HMAC local); revalidado antes de cada operacao (principio do vinculo legado) |
| `contexto_ativo_ref` | sha256 | Checkpoint/contexto corrente |
| `memoria_ref` | sha256 | Cabeca da memoria da sessao (append-only, com fonte e validade por entrada) |
| `resumo_aprovacao` | objeto | Hashes dos resumos de custo e autonomia aprovados pelo humano na abertura (portao bloqueante) |

**Invariantes:** IS-1 trocar modelo/provedor/ferramenta **nao** altera
`sessao_id` nem `linhagem_id`. IS-2 qualquer mudanca em `escopo`, `permissoes`,
`orcamento` ou `politica_ref` exige nova aprovacao humana hasheada e gera evento —
ou encerra a sessao e abre outra (sem heranca silenciosa). IS-3 sessao `suspensa`
so retoma por Checkpoint valido (§8).

## 2. WorkUnit e `parent_work_unit`

A unidade de trabalho roteavel. Substitui o "ato" do legado com recursao
explicita.

| Campo | Tipo | Semantica |
|---|---|---|
| `work_unit_id` | id | Identidade local |
| `sessao_id` / `linhagem_id` | id | Dono (sempre a sessao logica) |
| `parent_work_unit` | id \| null | Pai na decomposicao; `null` = raiz. Grafo **aciclico** (validacao barata antes de pagar, herdada do decompositor legado) |
| `tipo` | enum(`ato`,`decomposicao`,`etapa`,`revisao`) | `ato` = folha executavel; `decomposicao` = no com filhos |
| `intencao` | texto (≤4.000 chars) | O que deve ser verdadeiro ao final; teto herdado do forjador legado — acima, recusa |
| `nivel_capacidade` | enum(`L1`,`L2`,`L3`) | **Capacidade exigida** (escala experimental, ver D6 §3): L1 = determinístico/mecanico; L2 = generico com contexto; L3 = especializado/julgamento. Independente de risco |
| `classe_governanca` | enum(`C0`,`C1`,`C2`,`C3`) | **Risco/efeito** da execucao sobre o mundo, na semantica canonica FND-04 §2 (preservada). Independente de capacidade |
| `contexto_ref` | sha256 | ContextPackage montado para esta unidade (§3) |
| `depende_de` | lista[id] | Arestas de ordem (ondas topologicas); executa quando todos concluem |
| `estado` | enum(`proposta`,`aprovada`,`em-execucao`,`aguardando-juiz`,`concluida`,`reprovada`,`cancelada`) | Rotas de risco nascem `aguardando-juiz` (principio Juiz 2 legado) |
| `resultado_ref` | sha256 \| null | Artefato produzido (referencia, nao conteudo) |
| `custo_medido` | objeto \| null | Tokens/custo/latencia medidos; `null` honesto quando a fonte nao mede |

**Invariantes:** IW-1 toda WorkUnit tem exatamente uma RoutingDecision vigente
antes de `em-execucao`. IW-2 `decomposicao` com mais de 12 filhos diretos e
recusada (teto legado). IW-3 duas WorkUnits irmas com `intencao` sobreposta
(competicao) = recusa (anti-competicao legado). IW-4 `classe_governanca` ≥ C2 ou
Tipo 1 exige `aprovada` por humano antes de `em-execucao`.

## 3. ContextPackage

O pacote de contexto montado por WorkUnit/etapa. Substitui o acoplamento do
legado a enderecos externos: o contrato de especialista (ou qualquer fonte) entra
como **conteudo**, nao como caminho.

| Campo | Tipo | Semantica |
|---|---|---|
| `contexto_id` | id | Identidade do pacote |
| `work_unit_id` | id | Consumidor |
| `entradas` | lista[objeto] | Cada entrada: `origem` (caminho/URL/id), `sha256`, `papel` (`contrato` \| `evidencia` \| `memoria` \| `artefato-anterior` \| `norma-citada`), `inclusao` (`verbatim` \| `recorte` \| `referencia`) |
| `politica_inclusao` | objeto | `verbatim_ate` (bytes; default 200 KB — recusa acima, **nunca resume**), `memoria_por_hash` (injecao so por `ID=SHA256` — principio ADR-121) |
| `custo_contexto_linhas` | int | Medido em linhas (disciplina CE-02); nunca estimado |
| `exclusoes` | lista[texto] | O que foi deliberadamente deixado fora, e por que |
| `hash_pacote` | sha256 | Identidade de conteudo; muda = novo pacote, novo RoutingDecision |

**Invariantes:** IC-1 toda entrada tem proveniencia completa (origem + hash).
IC-2 nenhuma entrada atravessa a fronteira de isolamento (D2): fontes read-only
entram como `evidencia`/`norma-citada`, nunca como instrucao executavel.
IC-3 conteudo externo nunca vira norma (rotulo preservado no pacote).

## 4. RoutingDecision

A decisao de roteamento, registrada **antes** da execucao e imutavel (superseded
por nova decisao, nunca editada — principio ADR canonico aplicado localmente).

| Campo | Tipo | Semantica |
|---|---|---|
| `decisao_id` | id | Identidade |
| `work_unit_id` / `hash_pacote` | id + sha256 | Objeto e contexto da decisao |
| `classificacao` | objeto | `rota` (enum da politica), `confianca` (`alta` \| `baixa`), `metodo` (`declarado` \| `sensor` \| `llm`); **`baixa` = falha fechada** para julgamento humano ou decomposicao — substitui o classificador-regex aposentado |
| `selecao` | objeto | `ferramenta`, `provedor`, `modelo`, `effort`, `modo` (`read-only` \| `worktree` \| `escrita-aprovada`), `controle` (`autonomo` \| `confirma-no-gasto` \| `humano-no-loop`) |
| `nivel_capacidade_atendido` | enum(`L1`,`L2`,`L3`) | Capacidade do executor escolhido; deve ser ≥ `nivel_capacidade` da WorkUnit |
| `alternativas` | lista[objeto] | Ordem de fallback declarada (provedor novo entra no fim da fila — principio legado) |
| `custo_previsto` | objeto \| null | Previsao rotulada `estimado`; nunca apresentada como medicao |
| `aprovacao_custo_ref` | sha256 \| null | Obrigatorio quando `custo_previsto` > 0 e `controle` ≠ `autonomo` (portao bloqueante) |
| `motivo` | texto | Por que esta selecao (rastreabilidade fonte→decisao→destino) |
| `supersede` | id \| null | Decisao anterior substituida (ex.: reroteamento) |

## 5. ExecutionAttempt

Uma invocacao concreta de executor. Trocar modelo = **novo ExecutionAttempt** na
mesma WorkUnit e mesma `linhagem_id`.

| Campo | Tipo | Semantica |
|---|---|---|
| `attempt_id` | id | Identidade da invocacao |
| `work_unit_id` / `decisao_id` | id | WorkUnit e RoutingDecision que autorizam |
| `linhagem_id` | id | Sempre o da sessao logica — **a troca de modelo nao cria sessao nova** |
| `executor` | objeto | `ferramenta`, `provedor`, `modelo`, `effort` efetivos (resolvidos) |
| `inicio` / `fim` | ts | Latencia medida |
| `captura` | objeto | `saida_estruturada_ref` (sha256 do stream capturado — **obrigatoria**: a ausencia desta captura causou perda de dado real no legado), `saida_final_ref` |
| `resultado` | enum(`sucesso`,`falha-transitoria`,`falha-contrato`,`falha-quota`,`falha-desconhecida`,`recusa`) | Classificacao tipada — fecha a lacuna "quota vira texto cru" do legado |
| `custo_medido` | objeto \| null | Tokens/custo; `null` honesto |
| `artefato_ref` | sha256 \| null | Produzido (worktree/patch), se houver |

## 6. RetryEvent, FallbackEvent, EscalationEvent

Eventos de recuperacao. **Retry, reparo, fallback, reroteamento e escalonamento
sao conceitos distintos** (definicoes operacionais em D6 §4):

| Contrato | Gatilho | Campos-chave | Limite |
|---|---|---|---|
| **RetryEvent** | `falha-transitoria` no ExecutionAttempt (mesma decisao, mesmo executor) | `attempt_id`, `tentativa_n`, `backoff_ms`, `respeitou_retry_after` (bool) | Max. 3; so transitorio (408/409/425/429/5xx); 4xx de contrato **nunca** repete |
| **FallbackEvent** | Falha nao-transitoria ou retry esgotado; **proximo executor da `alternativas`** da mesma RoutingDecision | `attempt_id`, `de_executor`, `para_executor`, `motivo` | Segue a ordem declarada; nunca pula para executor fora da politica |
| **EscalationEvent** | Alternativas esgotadas, orcamento estourado, confianca `baixa`, ou `classe_governanca` exigindo humano | `work_unit_id`, `motivo` (enum: `sem-alternativa` \| `orcamento` \| `ambiguidade` \| `aprovacao-humana` \| `juiz-reprovou`), `destino` (`humano` \| `decompor` \| `abandonar`) | Sempre termina em decisao humana registrada; silencio nao resolve |

Reparo e reroteamento **nao sao eventos proprios**: reparo = nova WorkUnit filha
de tipo `etapa` com contexto do erro; reroteamento = nova RoutingDecision que
`supersede` a anterior + FallbackEvent ou novo ExecutionAttempt.

## 7. ValidationVerdict

O veredito de validacao/julgamento. Emitido por verificador **distinto** do
executor (quem executa nao verifica — GV-04; proibicao de autoverificacao do
canonico, ADR-0005, adotada como disciplina do laboratorio).

| Campo | Tipo | Semantica |
|---|---|---|
| `veredito_id` | id | Identidade |
| `alvo` | objeto | `work_unit_id` ou `sessao_id`; `artefato_ref` |
| `camada` | enum(`deterministica`,`juiz-llm`,`humana`) | Deterministica = schema/invariantes (Juiz 1); juiz-llm = modelo independente (Juiz 2); humana = soberano |
| `verificador` | objeto | Identidade do verificador; para `juiz-llm`: `provedor` e `modelo` **declarados** (o legado julgou no economico por omissao deste campo — defeito ADR-109) |
| `independencia` | objeto | `provedor_distinto_do_executor` (bool), `modelo_distinto` (bool), `motivos` — calculado **antes** de julgar; fila minima de candidatos declarada (a fila do legado colapsou com 2 nomes fixos) |
| `resultado` | enum(`aprovado`,`reprovado`,`inconclusivo`) | Inconclusivo = EscalationEvent, nao nova tentativa automatica |
| `criterios` | lista[objeto] | Criterio × evidencia × passou/falhou (criterios definidos **antes** da execucao, na WorkUnit) |
| `efeitos` | objeto | Carimba `artefato_ref`, placar da sessao e memoria (veredito = memoria com validade longa) |

## 8. Checkpoint e EventLog

A persistencia que faz a sessao logica sobreviver a processos.

**EventLog** — append-only, um evento por linha (JSONL), tipos: `sessao`,
`work-unit`, `routing`, `attempt`, `retry`, `fallback`, `escalation`, `veredito`,
`checkpoint`, `memoria`, `orcamento`. Campos comuns: `evento_id`, `ts`,
`linhagem_id`, `tipo`, `payload_ref` (sha256). Streaming por offset de bytes
(principio do fio legado). Nunca guarda conteudo de artefato — so referencia.

**Checkpoint**

| Campo | Tipo | Semantica |
|---|---|---|
| `checkpoint_id` | id | Identidade |
| `sessao_id` / `linhagem_id` | id | Dono |
| `estado_refs` | objeto | Hashes: envelope, work-units abertas, memoria-cabeca, orcamento-consumido, eventlog-offset |
| `ponto_de_retomada` | objeto | Proxima acao pendente, ordenada por consequencia (briefing de retomada **custo zero** — principio legado) |
| `validacao` | objeto | Veredito deterministico (Juiz 1) sobre o checkpoint gravado — gravacao so e sucesso apos validacao |
| `selo` | HMAC | Integridade local (vinculo legado) |

**Invariantes:** IP-1 retomar = ler Checkpoint valido + EventLog a partir do
offset; **nunca** reconstruir por inferencia. IP-2 checkpoint invalido ou selo
divergente = sessao nao retoma; escalona. IP-3 EventLog nunca e reescrito
(historico nao se reescreve — AF-16); correcao = novo evento.

## 9. Mapa contrato → componente (ponte para D6)

| Contrato | Componente dono (D6) |
|---|---|
| SessionEnvelope, Checkpoint, EventLog, memoria da sessao | Session Kernel |
| WorkUnit, RoutingDecision | Task Router (com veto do Policy Gateway) |
| ContextPackage | Session Kernel (montagem) + Policy Gateway (fronteira) |
| ExecutionAttempt, RetryEvent, FallbackEvent | Execution Gateway |
| EscalationEvent | Control Plane |
| ValidationVerdict | Evaluation/Judge |
| Telemetria, custo medido, placar | Evidence Plane |
