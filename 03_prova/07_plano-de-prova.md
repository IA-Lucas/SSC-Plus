---
id: SSC-DOC-07
titulo: Plano de Prova do SSC+
tipo: plano-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D7 — Plano de Prova

> Como o SSC+ provara que seu desenho funciona — **sem** inventar resultados. Este
> documento define tarefas, ambientes e metricas; **nenhum numero aqui e
> resultado**. Toda metrica declarada nasce `nao medido` e so ganha valor por
> medicao registrada no Evidence Plane, com base e metodo declarados.

## 1. Estrategia em quatro camadas

| Camada | Ambiente | Custo de API | O que prova |
|---|---|---|---|
| **P0 — Contratos** | Providers falsos (deterministicos) | R$ 0 | Maquina de estados, eventos tipados, recuperacao, checkpoint/retomada |
| **P1 — Shadow mode** | Provider real observado, **sem executar** | R$ 0 | RoutingDecision realista; comparacao do que o SSC+ decidiria × o que o executor real faria |
| **P2 — Piloto read-only** | Providers reais, escrita proibida | Baixo, com teto e portao | Qualidade/latencia/custo medidos em tarefas-ouro; juiz independente |
| **P3 — Worktree** | Providers reais, escrita **so em worktree**, merge humano | Baixo-medio, com teto e portao | Ciclo completo: decompor → executar → previa → merge humano → rollback |

Cada camada tem criterio de entrada e de saida; nao se avanca com vermelho aberto.

## 2. Tarefas-ouro (golden tasks)

Conjunto fechado e versionado (`03_prova/tarefas-ouro/`, a criar na 0.2) de
tarefas com resposta conhecida ou criterio objetivo de aceite **definido antes da
execucao**. Desenho:

- **TO-1 Deterministicas (L1):** saida verificavel por teste automatico (ex.:
  transformacao com diff exato). Mede: o barato basta?
- **TO-2 Contextuais (L2):** exigem ler um repo pequeno e responder com citacao de
  arquivo/linha. Mede: ContextPackage carrega o suficiente — e so o suficiente?
- **TO-3 Julgamento (L3):** revisao de um diff plantado com defeitos conhecidos
  (semente de erros). Mede: taxa de deteccao e de falso-positivo **lida**, nunca
  assumida — o contra-exemplo da A4: "um scanner sem taxa lida e instrumento nao
  calibrado".
- **TO-4 Decomposicao:** tarefa que exige `parent_work_unit` com 3–6 filhos e
  dependencias (onda topologica real). Mede: anti-competicao, ordem, custo total
  da decomposicao × execucao unica.
- **TO-5 Adversariais de roteamento:** despachos com rodape enganoso, ambiguidade
  real e pedido fora de politica. Mede: falha fechada acontece (e **barata**),
  em vez de rota errada silenciosa — replica controlada do defeito do
  classificador-regex legado.

Cada tarefa-ouro declara: entrada, criterio de aceite, metodo de verificacao,
evidencia esperada (espelha os seis campos de requisito de SF-15/ADR-0021, como
disciplina — nao como conformidade canonica).

## 3. Providers falsos (P0)

- Implementam a interface de Provider Adapter com respostas **deterministicas por
  seed**: sucesso, `falha-transitoria`, `falha-contrato`, `falha-quota`, latencia
  simulada, custo simulado **rotulado como simulado**.
- Bateria minima: todo enum de `resultado` exercitado; Retry-After respeitado;
  esgotamento de alternativas; orcamento estourando no meio; checkpoint invalido;
  selo divergente; EventLog com offset corrompido.
- **Proibido** provider falso "otimista" (so sucesso): toda corrida P0 inclui a
  bateria de falhas injetadas (§5).

## 4. Shadow mode (P1)

- O SSC+ roteia e registra RoutingDecision + custo previsto **sem executar**;
  o executor real (humano usando suas ferramentas usuais) executa normalmente.
- Comparacao registrada: rota escolhida × rota real; custo previsto × custo
  medido real (quando disponivel); casos em que a falha fechada teria evitado
  trabalho errado.
- Saida: relatorio de divergencias com classificacao (router errado / executor
  errado / empate informado). Nenhuma conclusao sem N declarado na abertura.

## 5. Falhas injetadas

Injecao deliberada em P0 e P2, uma por vez, com observacao do evento esperado:

| Falha injetada | Evento/contrato esperado |
|---|---|
| HTTP 429 com Retry-After | RetryEvent respeitando o header; esgotamento → FallbackEvent |
| 4xx de contrato | **zero** retry; FallbackEvent direto |
| Quota esgotada em CLI (texto cru) | `falha-quota` tipada (prova que a lacuna do legado foi fechada) |
| Provider fora da politica | Recusa do Policy Gateway antes de qualquer chamada |
| Custo acima do teto no meio da onda | EscalationEvent `orcamento`; nenhuma chamada posterior |
| Checkpoint adulterado | Sessao nao retoma; escalona |
| Juiz reprova artefato | WorkUnit `reprovada`; reparo = nova WorkUnit filha, nao retry |
| Dois filhos com intencao sobreposta | Recusa anti-competicao do Task Router |

## 6. Comparacao de executores

- Matriz: cada tarefa-ouro × cada executor candidato (minimo 2 provedores, senao a
  independencia do Juiz e impossivel — licao da fila colapsada, ADR-109 legado).
- **Kimi K3** entra nesta matriz **como candidato**, no fim da fila (politica de
  provider novo), sem nenhuma vantagem presumida. Proveniencia: evidencia externa
  `AC-01-VID-004` (nao verificada); handoff legado 2026-07-24 registra K2.6 fora
  da rota por 404/410. A candidatura so vira fato medido neste plano.
- Comparacao cega quando possivel: o Juiz avalia artefatos sem saber o executor
  (campo `executor` omitido do pacote de julgamento).
- Hipotese explicita a medir (nao a assumir): "planejador L3 × executor L1/L2"
  supera "L3 para tudo" em custo com qualidade estatisticamente igual — a alegacao
  de "80% de economia" da evidencia externa (`AC-03-VID-005`, V7) **permanece nao
  verificada** ate medicao propria; o legado mediu os dois lados (economia real e
  o defeito de planejar no barato), e esse e o unico precedente aceito.

## 7. Worktree, previa e merge humano (P3)

- Toda escrita em worktree isolada; `previa` nao gasta; aceite **por arquivo**;
  aceite parcial nao marca mesclado; falha = rollback total.
- **Merge e ato humano**, sempre: o SSC+ propoe o patch, o humano aplica.
- Prova obrigatoria antes de declarar P3 apto: o fluxo
  `decompor → executar → previa → merge` de ponta a ponta **contra provedor real**
  — exatamente o fluxo que o legado **nunca** exerceu e2e (DV-7 do baseline) e
  onde o defeito CRLF viveu. A prova inclui repo com CRLF e com fins de linha
  mistos (o teste `TestFimDeLinha` do legado e a semente).

## 8. Juiz independente

- Toda tarefa-ouro em P2/P3 e julgada por Juiz de camada `juiz-llm` com
  `independencia.provedor_distinto_do_executor = true` calculada **antes** do
  julgamento; veredito declara `verificador.provedor` e `verificador.modelo`.
- Fila minima: ≥2 candidatos independentes declarados por classe de tarefa;
  fila menor = a tarefa nao abre (falha fechada, nao improviso).
- Amostra de vereditos de Juiz-llm e revisada pelo humano (calibracao); taxa de
  concordancia registrada como metrica, com N.
- Camada deterministica (Juiz 1) valida todo checkpoint e todo EventLog fechado —
  sem excecao, inclusive em teste.

## 9. Rollback

- **De artefato:** worktree descartavel; rollback total em falha (principio
  legado); merge humano = ponto sem retorno automatico — revert e commit novo,
  nunca reescrita.
- **De sessao:** checkpoint anterior valido; retomada testada como cenario de P0.
- **Do laboratorio:** o repositorio inteiro e descartavel sem efeito colateral —
  nada fora dele depende dele (Manifesto D2); a promocao ao canonico e um ato
  separado (D8), nunca uma consequencia.

## 10. Metricas (definicao, nao resultado)

| Metrica | Definicao | Metodo | Base |
|---|---|---|---|
| Qualidade | % de tarefas-ouro com veredito `aprovado` | Juiz independente, criterios pre-definidos | N declarado por camada |
| Deteccao (TO-3) | taxa de deteccao e de falso-positivo | Semente de defeitos conhecida | N declarado |
| Custo | tokens e custo cobrado por tarefa, por executor, por rota | Telemetria medida; `null` quando a fonte nao mede | Evidence Plane |
| Latencia | `fim - inicio` por ExecutionAttempt; p50/p95 por rota | Timestamps medidos | Evidence Plane |
| Economia de roteamento | custo da rota escolhida × custo da rota-L3-para-tudo, mesma qualidade | Comparacao emparelhada nas tarefas-ouro | N declarado |
| Precisao de previsao | custo previsto × medido (shadow mode) | Razao por tarefa | N declarado |
| Falha fechada | % de situacoes adversariais (TO-5/falhas injetadas) com evento correto e custo ≤ limiar | Bateria de falhas | Cobertura da bateria |

Regras: MR-1 nenhuma metrica sem base e metodo declarados antes da coleta.
MR-2 estimativas sao rotuladas `estimado` e nunca se misturam com medicoes.
MR-3 resultado que depender de segredo de provedor nao publicavel e reportado
agregado. MR-4 **nao medido** e resposta valida — inventar numero e violacao da
missao.

## 11. Criterios de saida por camada

- **P0 → P1:** bateria de falhas 100% com evento correto; checkpoint/retomada
  provados; zero escrita fora do repo.
- **P1 → P2:** relatorio de shadow mode com N declarado; divergencias classificadas;
  precisao de previsao medida.
- **P2 → P3:** tarefas-ouro medidas em ≥2 provedores; juiz independente operando
  com fila minima; custo dentro do teto aprovado.
- **P3 → proposta (D8):** fluxo e2e contra provedor real com merge humano provado
  (incl. CRLF); metricas §10 publicadas com base; lacunas nomeadas. Entao, e so
  entao, o SSC+ escreve a evidencia que alimenta o Goal competente.
