---
id: SSC-DOC-03
titulo: Baseline do SuperCondutor Legado
tipo: inventario-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D3 — Baseline do SuperCondutor (engenharia reversa)

> Inventario do SuperCondutor legado, sem copia de codigo. Toda referencia e por
> caminho + hash. Leitura feita em 2026-07-30, sobre o repositorio `lucaX` em
> `git HEAD = bf8a407c2d2fbd492f4ba4abeed522d345b5b786` (proveniencia).
>
> **Nota de proveniencia:** a working tree do `lucaX` tinha **334 modificacoes nao
> commitadas pre-existentes** (anteriores a esta missao), incluindo o proprio
> SuperCondutor (34 arquivos, +2.214/-220 vs HEAD). Os hashes abaixo referem-se
> a **working tree encontrada**, nao ao commit — o estado real do legado e
> "HEAD + mudancas locais do operador".

## 1. Objeto e proveniencia

| Item | Valor |
|---|---|
| Raiz | `E:/LucasIA/Projetos/lucaX/My_WorkSpace/Meus_projetos/SuperCondutor` (abaixo, `<SC>/`) |
| Repositorio | `E:/LucasIA/Projetos/lucaX` (git; HEAD `bf8a407c…b5b786`) |
| Ultima mutacao de codigo | 2026-07-29 (`supercondutor.py`) |
| Stack | Python **stdlib-only** (zero `pip`; CI proibe dependencia nova), Windows-first, matriz CI ubuntu+windows × Python 3.11/3.13 |
| Totais medidos | **75 arquivos .py de codigo, ~20.292 linhas** (79/21.446 incluindo 4 copias de runtime em `sessoes/execucoes/demo*/previa/`) + 1.508 linhas JS (`extensao-vscode/`) |
| Testes | **33 arquivos `test_*.py`, 569 casos, 8.081 linhas**, cobertura declarada 90,2% (medida por `ferramentas/cobertura.py`) |
| Documentacao externa | `lucaX/docs/adr/` (054, 090, 091, 093, 094, 098, 109, 113, 121) e `lucaX/docs/handoffs/` (12 handoffs `supercondutor-*`) |

### Hashes dos arquivos-chave (sha256)

| hash | arquivo (relativo a `<SC>/`) |
|---|---|
| `f17e5e111821dbdc549f383c527f0a9f4f12e967758aa16cdc060fbb306a8695` | `supercondutor.py` |
| `5cdfdd618ebc01df3c8fcc7e191336505a597b343e9b03f024f37e68d5b92959` | `politica.json` |
| `42c9fdabc5a953038d7987c68852e651183ef940f533e4b32ebae48bd68e4d20` | `README.md` |
| `2d635b4279494c085234e99c205d3b84b18d1ad74b621c6979f543bed6cfca87` | `ESTADO-SuperCondutor.md` |
| `e4faf55195825269c6a9e305cd8515b2f465e17dc19618515385ed4d8afbbe6d` | `CLAUDE.md` |
| `016134dd8f3ba348561c20084960244081d48926059a709e34abe0e44ad49e14` | `compose.yml` |
| `e14b2f04036e88765d79f8beedc07b82bc92b75093855e99845d8b9384652ec6` | `Dockerfile` |

Agregados por diretorio (`find <d> -name "*.py" | sort | xargs sha256sum | sha256sum`):
`sessao/` = `eff67678ab9096d91722daccc0f44e588db435557d4108017e4ee3561b5eb16c` ·
`ferramentas/` = `9ddba126d523366edbf8a8f0996920cb363d0596023d114d2d7ec53ce10d1a78` ·
`tests/` = `d6f881bb922158186f42b996d828185a0069b16d54239205e06eddba609c514f` ·
raiz = `cf8c9d38165b725b23f6e673a4ba643b02f36bdd8cab4e8c8ae1818e5018ee98`.

## 2. Inventario de modulos

| Modulo | Tamanho | Responsabilidade |
|---|---|---|
| `supercondutor.py` | 1.213 linhas | Entrypoint CLI unico; argparse com **25 subcomandos** (`abrir, classificar, forjar, executar, decompor, conversa, eventos, previa, julgar, placar, painel, tui, banco, mesclar, relatorio, fio, cockpit, catalogo, aprendizado, auditar, projeto, memoria, retomar, ferramenta, diagnostico`); so despacha para `sessao/*` |
| `politica.json` | 153 linhas, v2 | Contrato declarativo: flags da primeira tela/portao, fronteira permitido/proibido, **7 rotas** (`sensor_local, decisao_arquitetural, codigo_complexo, codigo_simples, contexto_grande, fallback_quota, juiz_final`) com ferramenta/modelo/effort/modo/autonomia, metricas de aprendizado, bloco `execucao` |
| `sessao/` (35 .py) | 10.298 linhas | O motor inteiro. Maiores: `decompositor.py` (845), `tui.py` (779), `executor.py` (557), `conversa.py` (534), `catalogo.py` (487), `memoria.py` (448), `adaptadores.py` (445), `painel.py` (432), `ferramentas.py` (409). Demais: `portao, contexto, economia, estado, vinculo, arquivo, classificador, juizes, telemetria, otel, banco, fio, worktree, previa, anexo, aprendizado, retomada, auditoria, projeto, diagnostico, cockpit, painel_ui, relatorio, forjador, midia` |
| `tests/` (35 .py) | 8.081 linhas | 33 arquivos `test_*.py` + suporte; unittest stdlib |
| `ferramentas/` (4 .py) | 700 linhas | Scripts operacionais: `validar.py` (402; o **Juiz 1**, validador do schema do `estado_sessao.json`, em subprocesso), `cobertura.py` (piso 85), `testar_nvidia.py` (sensor de prova viva NIM), `painel_demo.py` |
| `specs/` | 0 .py | `saida.schema.json` (JSON Schema 2020-12 do `estado_sessao.json`, subconjunto com checagem cruzada em `validar.py`) + `estado_sessao.example.json` (golden master, 218 linhas) |
| `config/` | 5 JSON | `catalogo-llms.json` (provedores/modelos/papeis/cobranca), `fontes-benchmark.json`, `mapa-especialidades.json` (192 linhas; camadas → enderecos externos de agentes), `perfil.example.json`, `perfil.local.json` (real, gitignored) |
| `sessoes/` | ~403 KB | **Runtime com dados reais de producao**: `estado_sessao.json`, `.chave_sessao` (HMAC, gitignored), `telemetria.jsonl`, `fio.jsonl`, `memoria.jsonl`, `contextos/`, `execucoes/` (8 reais, incl. `6ec30f10…` APROVADA e `db8df6f6…` REPROVADA por Juiz 2), `planos_recusados/` (4 planos pagos recusados). Nao e codigo — lido apenas como evidencia |
| `docs/` | 7 .md (~1.233 linhas) | Runbook (`operacao.md`, 463), despacho, plano de orquestracao de modelos, onboarding, adaptadores, guia NIM |
| `kb/` | 265 linhas | `benchmark-inteligente-jul2026.md` — benchmark traduzido para roteamento |
| `extensao-vscode/` | 1.508 linhas JS | Casca CommonJS puro (sem build): `extension.js` (663), `conversa.js` (532), `teste-fumaca.js` (313; 16 casos). Congelada desde ADR-113 (TUI virou porta principal), funcional |
| `Dockerfile` / `compose.yml` | 57 / 85 linhas | `python:3.13-slim` + git, zero pip; CMD roda a suite; 4 servicos; porta so em `127.0.0.1:8765`; volume `..:/repo:ro`; `NVIDIA_API_KEY` por ambiente, sem valor escrito |
| `.github/workflows/supercondutor-ci.yml` | (repo-pai) | Matriz ubuntu+windows; `-W error::ResourceWarning`; `compileall`; gate de `diagnostico`; cobertura piso 85; dispara tambem em `agentes/**/especialista.md` |

## 3. Contratos

- **Contratos de especialista (externos ao projeto):** 53 `especialista.md` sob
  `lucaX/agentes/**`; o SuperCondutor usa efetivamente os **5** referenciados por
  `config/mapa-especialidades.json` (governanca/agentops, producao/tecnologia,
  producao/design, producao/dados, governanca/qualidade). Frontmatter YAML simples
  (`especialista, camada, tools, rota_preferida, effort, schema_entrada,
  schema_saida`); so `producao/tecnologia` tem escrita (`Write, Edit` + `Bash`);
  qualidade e agentops nao escrevem ("quem mede nao conserta").
- **Resolucao:** `sessao/catalogo.py` (`carregar_especialista`, linha ~259) resolve o
  endereco **contra o repo alvo (`--repo`)**, nao contra o projeto; valida
  `contrato["especialista"] == entrada["id"]` (nome divergente = erro). O
  decompositor injeta os contratos no prompt do plano; especialista fora do mapa =
  plano recusado, custo zero. A CI vigia `agentes/**/especialista.md` porque mexer
  num contrato quebra a suite fora do diretorio do projeto.
- **Contrato de estado:** `specs/saida.schema.json` + golden master — o contrato do
  `estado_sessao.json`, validado pelo Juiz 1 em subprocesso antes do sucesso.

## 4. Testes (569 casos)

- **Infra/contrato/CLI:** `test_cli_ponta_a_ponta` (e2e in-process, rede monkeypatched para explodir + sensor anti-rede), `test_validar`, `test_portao_bloqueia`, `test_conectores_cobranca`, `test_fases_3_4`, `test_sem_segredo`.
- **Motor de orquestracao:** `test_classificador`, `test_adaptadores`, `test_forjador`, `test_decompositor`, `test_juizes`, `test_nvidia_selecao`, `test_conversa`, `test_previa`, `test_worktree` (incl. `TestFimDeLinha`, LF explicito — nasceu de bug CRLF real), `test_fio_sse`.
- **Ambiente operacional:** `test_ferramentas_locais`, `test_memoria_contexto`, `test_memoria_retomada`, `test_aprendizado`, `test_projeto`, `test_auditoria`, `test_banco` (equivalencia SQL×JSONL), `test_economia_estimada`, `test_relatorio`, `test_cockpit_catalogo`, `test_contexto_git_acervo`, `test_anexo`, `test_midia_local`.
- **Producao/UI:** `test_producao` (652 linhas; `ThreadingHTTPServer` real, subprocessos, 40 threads), `test_hardening` (vinculo/HMAC, `.chave_sessao` via `git check-ignore`), `test_painel_ui`, `test_tui` (incl. sensor `test_tui_nao_decide_quem_atende` via `tokenize`).
- **Integracao real:** `test_cli_ponta_a_ponta`, `test_producao`, `test_fio_sse`, `test_previa`/`test_worktree` (repos git de verdade em tmp). Maioria unitaria com executor injetado — divida admitida no ADR-098.
- **Sem arquivo dedicado** (cobertura indireta, sem orfaos reais): `sessao/otel.py`, `sessao/arquivo.py`, `sessao/vinculo.py`. Suite JS separada (16 casos), fora do unittest.

## 5. Integracoes e acoplamentos

- **Provedores LLM** (`sessao/adaptadores.py`, `ESPECIFICACOES_EMBUTIDAS`): `anthropic_claude` (CLI `claude -p`), `openai_chatgpt_codex` (CLI `codex exec`), `google_gemini_antigravity` (CLI `agy`), `nvidia_nim` (`openai_compat`, endpoint fixo, chave so por env). Tipo `openai_compat` generico cobre Grok/DeepSeek/Ollama/LM Studio por perfil; tipo `cli` tem **allowlist fechada de binarios** (`BINARIOS_AUDITADOS`). Modelos NIM ativos: GLM-5.2, DeepSeek V4 Pro/Flash, Nemotron 3 Ultra, MiniMax M3.
- **Dependencias externas: nenhuma** (sem `requirements.txt`/`pyproject.toml`/`setup.py`). Ambiente: git + CLIs dos provedores.
- **Acoplamentos fora do projeto:** (a) mapa de especialidades → `agentes/**/especialista.md` no repo lucaX; (b) `sessao/contexto.py` le estrutura do repo alvo (git, acervo, fila Juiz 2 — infra lucaX; repo generico degrada honestamente); (c) compose monta `..:/repo:ro`. **Nenhum caminho absoluto hardcoded em codigo de produto** (os `E:\` encontrados sao docstrings/testes).
- **Docker:** existe primariamente para rodar a suite em Linux (achou 8 vermelhas no 1º run, incl. veredito do Juiz 1 dependente de SO).

## 6. Divergencias documentacao × codigo × testes

| # | Divergencia | Evidencia |
|---|---|---|
| DV-1 | `CLAUDE.md` declara "Fase atual: **Fase 0**" — o codigo entrega Fases 1–5 + ambiente operacional + IDE + TUI | `CLAUDE.md` × ADR-121; conteudo normativo (regras de casca) segue valido |
| DV-2 | `ESTADO-SuperCondutor.md` mantem "DECISAO DO CEO PENDENTE" (modelo fora do hash de custo; `pode_editar_arquivos` fora do hash de autonomia) — **ADR-121 ja decidiu incluir ambos** | `sessao/portao.py:109-111,157-187` confirma; secao do ESTADO vencida |
| DV-3 | README omite `tui` (porta principal desde ADR-113) e trata a extensao como superficie corrente sem avisar que esta congelada; nao cobre `midia` | README × ADR-113/121 |
| DV-4 | "24 subcomandos" (ESTADO/ADR-113) × **25 reais** no argparse | `supercondutor.py` |
| DV-5 | `config/projetos.json` nao existe no checkout — `sessao/projeto.py:36` o espera como `REGISTRO_PADRAO`; criado em runtime | documentado como se existisse |
| DV-6 | `politica.json.execucao.adaptadores` aponta `sessao/executor.py`, mas o registro mora em `sessao/adaptadores.py` desde ADR-098 | deriva interna do proprio contrato |
| DV-7 | Estado declarado × prova viva: coerente nos numeros (569 testes, 90,2%, execucoes reais), mas `decompor --isolar` + `previa` + `mesclar --arquivo` contra provedor real **nunca foi exercitado de ponta a ponta**; `pode_editar_arquivos: false` nos 4 conectores faz patches pagos virem vazios por construcao (gate humano declarado) | `perfil.local.json`, handoffs |

## 7. Decisoes e riscos registrados (sintese por fonte)

- **ADR-054** — SuperCondutor **e** a sessao; escolha de ferramenta/modelo/effort/modo/autonomia **por ato**; portao de custo e autonomia bloqueantes. Risco: rotear despacho inteiro = produto errado.
- **ADR-090** — 6 defeitos de producao corrigidos (telemetria × lock no Windows; painel com token sem auth/DNS rebinding; veredito de Juiz 2 nao voltava ao disco; escrita nao-atomica; `.chave_sessao` fora do gitignore; `os.kill` no Windows). Divida: rotacao manual.
- **ADR-091** — Docker+SQLite; Docker se pagou (veredito do Juiz 1 dependia de SO). Banco = **projecao descartavel** do JSONL; escrita dupla recusada.
- **ADR-093** — **Agregar, nao competir**; forjador 2 camadas (teto 4.000); decompositor em ondas topologicas; contexto por arquivo verbatim; Juiz 2 exclui provedores usados; fio/SSE; worktree com merge so aprovado e rollback.
- **ADR-094** — Extensao como casca que nao decide; portao de custo na casca; `--repo` explicito. Risco: JS fora da suite Python.
- **ADR-098** — Registro de adaptadores; `sensor_local` executa com recusa em vez de promocao paga; memoria com fonte/validade por tipo; aprendizado propoe e nunca aplica; auditoria nao corrige. Divida: vocabulario classificador×catalogo acoplado (travado por teste); `memoria.jsonl` sem poda.
- **ADR-109** — Conversa = projecao do fio; preview nao gasta; anexo recusa (nunca corta); diff nativo com `git apply --include`; **a fila de juizes colapsou** (2 nomes fixos + multi-provedor = nenhum juiz independente; corrigido com fila = todo conector ativo + `risco_do_plano`); Juiz 2 julgava no modelo economico. Posfacio: `mesclar` nunca funcionou no repo real (CRLF via stdin; teste e defeito compartilhavam a premissa errada).
- **ADR-113** — Porta principal vira **TUI de fluxo** stdlib; confirmacao so onde ha gasto; virada de formato com custo zero porque a casca nao decide.
- **ADR-121** — Portao passa a cobrir **modelo** (hash de custo) e **`pode_editar_arquivos`** (hash de autonomia); mega-brain injeta memoria so por `ID=SHA256`; midia local com gate `AGUARDA_EXTRATOR_LOCAL`; upload externo bloqueado (LGPD). Proximo gate humano: escolher quais conectores podem escrever.
- **Handoffs (riscos abertos relevantes):** chave NVIDIA apareceu em conversa (rotacao recomendada, A-224); **perda de dado real** — revisao de 9 achados sobreviveu so como mensagem final porque a CLI foi chamada com `--print` (existe `--output-format stream-json` nao usado); classificador "sequestrado" por palavra de rodape; sem deteccao de quota esgotada em CLI; custo fantasma (free tier exibido como fatura); modelo aposentado trocado com prova (239s→18s); **planejador do decompositor rodava no modelo economico** — "a chamada que decide como o trabalho se divide era a mais barata do fluxo".

## 8. Conceitos de orquestracao presentes (insumo da Matriz D4)

| Conceito | Onde vive | Como funciona |
|---|---|---|
| Sessao | `sessao/portao.py, contexto.py, economia.py, estado.py, vinculo.py` | Abertura nao-interativa com duas aprovacoes hasheadas (custo + autonomia; pos-ADR-121 cobrindo modelos e `pode_editar_arquivos`); estado assinado (SHA-256 de repo/perfil/politica/catalogo + HMAC local) e revalidado antes de cada operacao; estado gravado passa pelo Juiz 1 antes do sucesso. Trocar insumo = sessao nova, sem heranca silenciosa |
| Tarefa/subtarefa | `sessao/forjador.py, decompositor.py` | Forja: despacho cru → ato em 2 camadas (sensor deterministico de 5 dimensoes + meta-prompt de passe unico; teto 4.000 chars). Decomposicao: plano JSON por 1 chamada auxiliar → validacao deterministica (especialista existe, grafo aciclico, anti-competicao, ≤12 partes) → ondas topologicas com threads (max. 4); contexto entre partes por arquivo verbatim (recusa >200 KB, nunca resumo); log por parte |
| Roteamento de modelo | `sessao/classificador.py, adaptadores.py` | Regex deterministica (ambiguidade = falha fechada); `ORDEM_PADRAO` por rota; `modelo_para_rota` qualidade×economico; provedor novo entra no fim da fila; promocao so via `preferencia_por_rota`. Falha conhecida: sensivel a palavra de rodape |
| Retry/fallback | `sessao/executor.py` | Fallback sequencial entre provedores ativos com falha fechada; retry com backoff exponencial (1,5s→20s, 3 tentativas) **so em erro transitorio** (408/409/425/429/5xx, respeita `Retry-After`); 4xx de contrato nao repete. CLI sem classificacao de erro — quota vira texto cru (risco aberto) |
| Juizes/validacao | `ferramentas/validar.py`, `sessao/juizes.py` | Juiz 1: schema + checagens cruzadas, em subprocesso. Juiz 2: fila = preferencia + todo conector ativo; independencia por provedor **e** modelo; `risco_do_plano` preve antes de pagar; rotas de risco nascem `AGUARDANDO_JUIZ2`; veredito carimba registro/artefato/placar e vira memoria |
| Checkpoint/memoria | `sessao/fio.py, memoria.py, retomada.py, worktree.py, previa.py, arquivo.py` | Fio JSONL append-only (um turno por linha; guarda **referencia** de artefato, nunca conteudo; streaming por offset); memoria exige fonte verificavel e validade por tipo (7d falha de provedor, 365d veredito); esquecer = lapide append-only; retomada = briefing custo zero; worktree por parte, patch como unico sobrevivente, aceite por arquivo, rollback total em falha; escrita atomica |
| Orcamento/custo | `sessao/telemetria.py, otel.py, banco.py, economia.py, relatorio.py, aprendizado.py` | Telemetria append-only serializada entre processos; `null` honesto quando CLI nao mede; nomes OTel GenAI; SQLite = projecao descartavel (equivalencia SQL×JSONL travada por teste); 3 custos separados (teorico, API cobrada, premium); economia medida so com token em toda parte; aprendizado com mediana e piso de 5 entregas, propoe e nunca aplica; portao de custo com aprovacao hasheada; chamadas auxiliares faturaveis mas fora da contagem de trabalho |

## 9. Pontos frageis conhecidos (insumo de risco da D4)

1. Classificador por regex fragil a texto acessorio (handoff 2026-07-28).
2. Ausencia de captura estruturada da saida das CLIs — perda de dado real medida.
3. Ausencia de classificacao de erro/quota no caminho CLI.
4. Acoplamento do mapa de especialistas a enderecos fora do projeto.
5. Fluxo decomposto completo contra provedor real nunca exercitado de ponta a ponta (DV-7).
6. `memoria.jsonl` sem poda; rotacao manual de telemetria/execucoes.
