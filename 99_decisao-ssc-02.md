---
id: SSC-DEC-02
titulo: Relatorio e Decisao da Missao SSC+ 0.2
tipo: decisao-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Relatorio e Decisao da Missao SSC+ 0.2

> Registro reproduzivel da missao: revisao contratual (PORTAO 1) + primeiro
> corte vertical P0 (escolha de modelo/provedor/effort por WorkUnit, nova
> invocacao na mesma sessao logica e linhagem). Fase offline, isolada, sem
> autoridade canonica. Nao e FIT, nao e ADR, nao e ato soberano.

## DECISAO: **READY-FOR-SSC-0.3**

PORTAO 1 passou (**CONTRACTS-REVIEW-PASSED**, SSC-REV-02), a P0 esta
implementada com a bateria obrigatoria verde e a prova central demonstrada.
O SSC+ pode avancar para a 0.3 (definicao adiante, §10) — nunca decidindo a
frente da arquitetura canonica.

## 1. Checklist da missao

| # | Exigencia | Resultado | Evidencia |
|---|---|---|---|
| 1 | Revisao independente de D5/D6 por revisor distinto do autor, com evidencias e veredito | **PASS com limitacao declarada** | `02_alvo/revisao-independente-d5-d6.md` (SSC-REV-02): invocacao independente, zero contexto compartilhado; familia de modelo do autor nao atestavel (L1-02 declarada) |
| 2 | As 12 correcoes aplicadas por versao local, antes do codigo | **PASS** | D5/D6 v0.2.0; tabela item→secao em SSC-REV-02 §2; diffs em `02_alvo/diffs/`; nenhum arquivo `.py` criado antes do veredito |
| 3 | Sem CONTRACTS-REVIEW-PASSED → REVIEW-BLOCKED sem codigo | **PASS (nao disparou)** | Veredito positivo emitido antes da implementacao |
| 4 | Snapshot somente leitura do canonico; releitura de ADR-0021/RFC-0017/indices; recaptura se o legado mudou | **PASS** | `01_fontes/snapshots/canonico-2026-07-30-abertura-ssc02.sha256` (identico ao fechamento da 0.1, 98/98); releitura registrada no log; hashes do legado identicos a D3 §1 na abertura |
| 5 | Nao escrever fora do SSC-Plus; nao copiar codigo legado; nao usar rede/API/credencial/provider real | **PASS** | Todas as escritas em `SSC-Plus` (verificacao final §8); testes usam `tempfile` do sistema; providers falsos; implementador instruido a nem abrir o legado |
| 6 | P0 em Python stdlib: contratos tipados/serializaveis, validacao, maquina de estados, CAS, EventLog append-only, checkpoint reconstruido pelo log, interfaces de Kernel/Router/Policy/Execution/Judge determinístico/Evidence, providers falsos por seed | **PASS** | `05_p0/ssc_p0/` (14 modulos); `python -m unittest discover -s 05_p0/tests` → **73 testes, OK (1 skip justificado)** |
| 7 | Prova central: mesma sessao/linhagem, X→tentativa 1, nova decisao, Y→tentativa 2; memoria/orcamento/causalidade preservados; troca nunca reinicia sessao nem ignora politica/aprovacao | **PASS** | `05_p0/cenarios/prova_central.py`: **18/18 assercoes**, evidencia em `05_p0/saidas/prova_central.json` |
| 8 | Pre-registrar TO-1 a TO-5 antes das corridas | **PASS** | `03_prova/tarefas-ouro/` (README + 5 arquivos, criterios congelados) escritos antes de qualquer corrida |
| 9 | Bateria de testes obrigatorios (lista da missao) | **PASS** | §5 — mapeamento item→teste |
| 10 | Relatorio reproduzivel: testes, cobertura, falhas, limitacoes, diffs D5/D6, rastreabilidade D3→D4→contrato→teste | **PASS** | este documento |
| 11 | Nao medido = null; simulacao = simulada | **PASS** | §5 (cobertura de linha = null); todos os numeros das corridas rotulados `simulado` (MR-2) |
| 12 | Revalidar isolamento e hashes no fechamento | **PASS com achado externo** | §8: legado intacto; canonico alterado **por processo externo** em 7 indices (nao pela missao); snapshot de fechamento capturado |

## 2. PORTAO 1 — revisao contratual

- Revisor: invocacao independente (sem contexto do autor); metodo, identidade e
  a limitacao L1-02 (familia de modelo nao atestavel) em SSC-REV-02 §1.
- Os 12 itens mandados estavam **ausentes ou parciais** em v0.1.0 (tabela
  SSC-REV-02 §2); todos corrigidos em v0.2.0. Achados proprios adicionais:
  RA-1 (base de hash indefinida), RA-2 (relogio nao e ordem), RA-3 (attempt
  contra decisao supersedada).
- Diffs: `02_alvo/diffs/d5-v0.1.0-v0.2.0.diff` (378 linhas),
  `02_alvo/diffs/d6-v0.1.0-v0.2.0.diff` (348 linhas), gerados por `git diff`
  sobre a working tree do laboratorio (**sem commit nesta missao** — a decisao
  de commitar fica para o Soberano).

## 3. P0 implementada (corte vertical)

`05_p0/`: pacote `ssc_p0` (14 modulos, stdlib apenas, Python 3.14), cenarios
executaveis, fixtures, 11 arquivos de teste, saidas de evidencia. Decisoes de
implementacao dignas de registro (do relatorio do implementador, verificadas):

- `hash_envelope` dos vinculos **exclui campos volateis** (estado, consumido,
  cabecas) — senao todo consumo invalidaria as decisoes vigentes e o
  reroteamento dentro do envelope seria impossivel.
- Payloads de eventos no CAS; o EventLog guarda apenas `payload_ref`.
- Control Plane minimo vive em `kernel.py` (organizacional; autoridade
  preservada — so emite fatos ao Kernel).
- Anti-competicao (IW-3) por similaridade de tokens (Jaccard 0,6),
  deterministico; ciclo recusado no Router e, em defesa profunda, no Kernel.

## 4. Prova central (verificada pelo orquestrador, nao so pelo implementador)

Cenario executado: WorkUnit A (C1, tipo-2) → RoutingDecision 1 (modelo/effort X,
provedor fake-a) → tentativa 1 `falha-quota` tipada → escalonamento registrado →
**nova RoutingDecision 2** (`supersede` a 1; modelo/effort Y, provedor fake-b,
**dentro do mesmo envelope de aprovacao**) → tentativa 2 `sucesso` → Juiz 1
`aprovado` → WorkUnit `concluida`. Assercoes (18/18): `sessao_id` e
`linhagem_id` inalterados em todos os 20 eventos; memoria preservada; orcamento
acumulou as duas tentativas; cadeia `causado_por` integra (decisao 2 apos a
falha; attempt 2 causado pela decisao 2); troca passou pela Policy sem veto e
sem exigir aprovacao humana extra (dentro do envelope, D5 §4). Evidencia:
`05_p0/saidas/prova_central.json`.

## 5. Testes

- **Resultado:** `python -m unittest discover -s 05_p0/tests -v` → **73 testes,
  72 ok, 1 skip, 0 falhas** (4,5 s). Reexecutado pelo orquestrador no
  fechamento com o mesmo resultado (reproduzivel).
- **Skip justificado:** `test_ic5_fuga_por_symlink_real` — Windows sem
  privilegio de symlink (WinError 1314); cobertura equivalente verde em
  `test_ic5_fuga_por_symlink_mock_do_resolvedor`.
- **Cobertura de linha:** **null** (nao medido — stdlib nao inclui medidor e a
  missao proibe dependencias; MR-4). Cobertura por item obrigatorio: 100% da
  lista da missao mapeada abaixo.

| Item obrigatorio da missao | Arquivo de teste |
|---|---|
| round-trip/schema | `test_contratos.py` |
| transicoes ilegais (3 maquinas) | `test_estados.py` |
| DAG/ciclos + anti-competicao | `test_workunits.py` |
| idempotencia e replay (IP-4) | `test_eventlog.py` |
| evento duplicado/fora de ordem/truncado/adulterado | `test_eventlog.py` |
| concorrencia (escritor unico) | `test_concorrencia.py` |
| crash antes/depois de persistir; orfao → indeterminado | `test_crash.py` |
| resultado indeterminado (IR-2) | `test_recuperacao.py`, `test_crash.py` |
| retry/reparo/fallback/reroteamento/escalonamento distintos (IR-1; fallback fora do envelope) | `test_recuperacao.py` |
| timeout, 429/Retry-After, quota, contrato/saida invalida | `test_recuperacao.py` |
| teto de custo | `test_policy.py` |
| checkpoint/retomada; checkpoint invalido/selo divergente | `test_crash.py`, `test_seguranca.py` |
| segredo em evento/contexto (IC-4) | `test_seguranca.py` |
| fuga por symlink/junction/`..` (IC-5) | `test_seguranca.py` |
| zero escrita externa | `test_seguranca.py` |
| alias nao prova identidade; IV-2; veredito invalido (sem attempt, IV-3); envelope de custo | `test_juiz.py`, `test_policy.py` |

**Falhas encontradas:** nenhuma falha de teste em aberto no fechamento; o
historico red-green intermediario do implementador nao foi registrado em log
estruturado (lacuna de processo, registrada — nao ha o que reportar alem do
estado final verde reexecutado). O unico desvio de comportamento detectado na
revisao final: nenhum conhecido (§7).

## 6. Corridas TO-1 a TO-5 (numeros simulados, rotulados)

| TO | Resultado | Evidencia |
|---|---|---|
| TO-1 | 3/3 aprovados (sementes 11/22/33) — o barato (L1) bastou, **neste cenario simulado** | `05_p0/saidas/to1.json` |
| TO-2 | 3/3 com citacao correta; pacote sem o arquivo certo → reprovado (comportamento programado do falso) | `to2.json` |
| TO-3 | taxas de deteccao **lidas** 1.0/0.8/0.6, FP {0,1,0}; tentativa de anular falha deterministica via LLM registrada como invalida (IV-2) | `to3.json` |
| TO-4 | DAG de 5 filhos com ordem topologica por `seq`; competicao e ciclo recusados; custo decomposicao × unica registrado (simulado) | `to4.json` |
| TO-5 | 3/3 cenarios com evento esperado, **zero attempts**, custo 0, cadeia integra | `to5.json` |

Nenhuma conclusao sobre custo/qualidade real pode ser derivada destes numeros —
sao provas de mecanismo contra providers falsos (D7 §3).

## 7. Limitacoes conhecidas

- Single-processo: escritor unico garantido por lock em memoria; sem file-lock
  entre processos (suficiente para P0; registrado para 0.3+).
- `fsync` de diretorio ignorado no Windows (durabilidade de rename reduzida).
- Scanner IC-4 e lista fechada de padroes — nao e prova de ausencia de segredo.
- `encerrada`, heranca `linhagem_origem` e modo `worktree` estao nos contratos
  mas sem cenario de teste proprio.
- Cobertura de linha null; historico red-green nao registrado (§5).
- L1-02 (familia de modelo do revisor) permanece: o Soberano pode pedir revisao
  humana complementar de D5/D6 v0.2.0.

## 8. Incidente 2: escrita concorrente no canonico (nao causada pela missao)

- **Fato:** entre a abertura e o fechamento desta missao, processo externo
  alterou 7 arquivos do canonico, todos indices/registros: `README.md` (raiz),
  `decisions/README.md`, `departments/README.md`, `foundation/README.md`,
  `rfcs/README.md`, `governance/README.md`, `governance/artifact-registry.md`.
- **Evidencia de nao-autoria:** nenhuma ferramenta desta missao escreveu fora de
  `SSC-Plus`; o padrao (indices de governanca) repete o incidente da 0.1.
- **Impacto:** **nulo para os entregaveis.** Os documentos citados pela missao
  (`decisions/ADR-0021`, `rfcs/RFC-0017`) verificaram **OK** na revalidacao de
  fechamento; os indices alterados foram relidos na abertura (A2) e nenhuma
  posicao usada depende das linhas que mudaram.
- **Fechamento:** `canonico-2026-07-30-fechamento-ssc02.sha256` capturado (98
  arquivos, estado corrente). Legado SuperCondutor revalidado no fechamento:
  7/7 arquivos e 4/4 agregados identicos a D3 §1.

## 9. Rastreabilidade D3 → D4 → contrato → teste

| Fonte (D3/D4) | Decisao | Contrato (D5 v0.2.0) | Teste |
|---|---|---|---|
| Sessao/fio/estado assinado legado (D4 §1,§5) | sessao logica, EventLog+CAS | §1, §8 | `test_eventlog.py`, `test_crash.py` |
| Classificador-regex aposentado (D4 §2) | falha fechada, confianca baixa | §4 | TO-5, `test_policy.py` |
| Perda real com `--print` (D4 §3) | captura obrigatoria | §5 | `test_contratos.py`, TO-1 |
| Fila de juiz colapsada, juiz no economico (D4 §4) | independencia + pacote_juiz + IV-2 | §7 | `test_juiz.py`, TO-3 |
| Perfil-vetor (D4 §3) | IC-5, allowlist, CAS contido | §3, §8.1 | `test_seguranca.py` |
| Portao na casca congela (ADR-094/121) | envelope de aprovacao de custo | §4 | `test_policy.py` |
| Quota vira texto cru (lacuna legado) | `falha-quota` tipada | §5 | `test_recuperacao.py` |
| Revisao SSC-REV-02 (12 itens + RA-1/2/3) | v0.2.0 integral | todos | bateria §5 |

## 10. Proximo passo e acoes deixadas para a 0.3

- **A1-02** Definir o escopo da 0.3 com o Soberano: candidatos naturais sao
  P1 (shadow mode, D7 §4) ou endurecimento da P0 (file-lock entre processos,
  cenarios para `encerrada`/`linhagem_origem`/worktree, cobertura de linha
  medida com ferramenta permitida).
- **A2-02** Revisao humana complementar de D5/D6 v0.2.0 (mitiga L1-02), se o
  Soberano julgar necessaria.
- **A3-02** Decisao do Soberano sobre commit da working tree do laboratorio
  (esta missao nao commitou).

## 11. Alternativas consideradas (e por que nao)

- **ADJUST** — seria a decisao se houvesse teste vermelho, item obrigatorio sem
  cobertura ou correcao de contrato nao verificada. Tudo verde e mapeado.
- **REVIEW-BLOCKED** — o portao passou; nao ha o que bloquear.
- **STOP** — nenhuma condicao de encerramento da Carta D1 §8; o incidente
  externo e risco gerenciado (mesmo perfil da 0.1), nao violacao do laboratorio.
