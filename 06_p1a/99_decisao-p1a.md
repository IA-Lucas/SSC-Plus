---
id: SSC-DEC-P1A
titulo: Relatorio e Decisao da Missao SSC+ P1-A — Preflight da Frota Real
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Relatorio e Decisao — Missao SSC+ P1-A (preflight da frota real)

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao LucaX
> Enterprise OS canonico. SSC+ 0.1–0.3 preservados: nenhum arquivo
> pre-existente foi editado; todo o trabalho e aditivo em `06_p1a/`.

## DECISAO: **READY-FOR-P1-B**

Criterio atendido: Codex, Claude e Kimi **ELIGIBLE** com prova real;
Google e Grok **SUPERVISED**; nenhum provedor PAYG na frota; todas as
validacoes do §3 verdes apos a incorporacao da revisao independente (§5).

## 1. Pre-condicoes (verificadas em 2026-07-30)

| Item | Resultado |
|---|---|
| `0da9d41` descende de `a96eda5` | OK (`git merge-base --is-ancestor`) |
| Working tree limpa NO INICIO da missao | OK (`git status --porcelain` vazio antes de qualquer trabalho) |
| 100 testes reexecutados | OK — 100 testes, 0 falhas, 0 skips |
| Prova central 18/18 | OK — 18 assercoes, 20 eventos |
| SSC+ 0.1–0.3 preservados | OK — nenhum arquivo pre-existente editado. Nota de precisao: a reexecucao da prova central (exigida pela missao) regenera `05_p0/saidas/prova_central.json`; o diff era **somente** identificador nao-determinista (UUID-4 de sessao/linhagem/attempt/evento e hashes derivados) — 18/18 assercoes e 20 eventos em ambas as corridas. Copia datada em `evidencias/backups/prova_central-2026-07-30-pre-p1a-fechamento.json` e o arquivo rastreado restaurado ao HEAD: o git agora mostra **apenas `?? 06_p1a/`**, ou seja, o trabalho e 100% aditivo. Nenhum commit foi feito. |
| Nada instalado/autenticado silenciosamente | OK — nenhuma instalacao, nenhum fluxo de login iniciado |

Evidencia: `evidencias/coleta-20260730-090127/` e
`evidencias/coleta-20260730-092436/` (nomes de diretorio em hora LOCAL;
timestamps de conteudo em UTC).

## 2. Entregaveis

1. **Inventario real** — `01_inventario-real.md` (5 provedores, 12 campos
   cada, resultado por provedor; nenhum segredo registrado).
2. **Auditoria economica** — `02_auditoria-economica.md`, executada antes
   de qualquer chamada, com NIVEIS DE EVIDENCIA por item (CLI / CONFIG /
   inferencia forte / indeterminado) — sem "CONFIRMADO" generico.
3. **Adaptadores de diagnostico** — `preflight/` (5 modulos, 804 linhas):
   deteccao de CLI, versao/status, descoberta de modelos, auth source,
   quota, 9 erros tipados com `codigo` estavel, bloqueio pre-invocação,
   sensores injetaveis (zero subprocesso real nos testes), nunca solicita
   pagamento, nunca altera arquivos.
4. **Prova minima real** — `03_prova-minima.md` v0.2.0 +
   `evidencias/prova-minima/`: Codex `PROVIDER_OK` (modelo efetivo
   `gpt-5.6-sol` observado no stderr), Claude `PROVIDER_OK
   claude-opus-5[1m]`, Kimi `PROVIDER_OK` com identificador registrado
   `kimi-code/k3` (re-prova com `-m`; a 1a execucao ficou fora do
   contrato e foi documentada). Google e Grok: nenhuma chamada.
5. **Falhas obrigatorias** — duas suites independentes:
   `tests/test_preflight.py` (sensor explosivo: qualquer sonda apos o
   bloqueio levanta AssertionError) e `tests/test_falhas_obrigatorias.py`
   (contagem de sondas, uma classe por falha + meta-teste de cobertura das
   9). As 9 falhas bloqueiam antes da invocacao ou retornam erro tipado;
   nenhuma cai em API paga.
6. **Isolamento verificavel** — `tests/test_isolamento.py`: o preflight
   nao escreve arquivo, nao abre rede, tem um unico `subprocess.run`
   (sempre com ambiente sanitizado), so usa sondas de diagnostico e nao
   deixa segredo em artefato. Ver `04_suite-preflight-e-correcoes.md`.

## 3. Validacao (reexecutada pelo orquestrador apos a revisao)

| Exigencia | Estado |
|---|---|
| Testes anteriores verdes | OK — 100/100 (`05_p0/tests`) |
| Novos testes de preflight | OK — **171 testes, 0 falhas, 0 skips** (`06_p1a/tests`: test_preflight 15, test_falhas_obrigatorias 35, test_economia 34, test_adaptadores 38, test_pipeline 29, test_isolamento 20), incluindo as 9 falhas obrigatorias em **duas** implementacoes independentes. Detalhe e correcoes: `04_suite-preflight-e-correcoes.md` |
| Prova central | OK — 18/18 |
| Zero segredo em logs/Git | OK — varredura registrada em `evidencias/coleta-20260730-092436/22_scan_segredos.txt` ("zero padroes"); revisor confirmou independentemente. Registros contem PII operacional (e-mail da conta), declarada |
| Zero custo variavel | OK — contado nos registros: **5 execucoes do runner, 4 chamadas que alcancaram modelo** (codex 1, claude 1, kimi 2); a 5a (`kimi-20260730T122206Z`) abortou na analise de argumentos em 0,744 s (`Cannot combine --prompt with --plan`), sem chamada de modelo e sem consumo de franquia. Nenhuma API tarifada; `custo_variavel = 0` em todos os registros |
| Zero escrita fora do laboratorio/descartavel | OK — dirs descartaveis verificados vazios (registrado em `dir_descartavel_arquivos_restantes` nos JSONs a partir da 2a rodada); git so com `06_p1a/` novo (prova_central.json restaurado ao HEAD). Prova adicional: `test_isolamento` compara instantaneo sha256 de todo `06_p1a/` antes/depois da varredura dos 5 — identico |
| Evidencia reproduzivel por provedor | OK — `evidencias/coletar.sh` (2 rodadas) + `evidencias/prova_minima.py` |
| Revisao independente | OK — 18 achados recebidos e incorporados (§5) |

## 4. Resultado por provedor

| Provedor | Plano | Resultado | Base |
|---|---|---|---|
| Codex | ChatGPT Pro 5x (declarado) | **ELIGIBLE** | OAuth chatgpt + prova real (`gpt-5.6-sol`) |
| Claude | Max (CLI confirma; 5x declarado) | **ELIGIBLE** | `subscriptionType: max` + prova real |
| Kimi | Allegretto (declarado) | **ELIGIBLE** | OAuth managed:kimi-code + prova real (`kimi-code/k3`) |
| Google | AI Pro (declarado) | **SUPERVISED** | regra da missao; oauth-personal confirmado; hooks externos no settings.json |
| Grok | SuperGrok (declarado) | **SUPERVISED** | regra da missao; cached token (origem nao localizada — confirmacao humana pendente); nunca XAI_API_KEY |

Observacao honesta de escopo: apenas Claude expoe o tier do plano pelo
CLI; Codex/Kimi/Google/Grok tem plano declarado pela conta (confirmacao
humana na janela de login). Quota/reset: nao exposta por nenhum dos 5
CLIs em modo headless — classificada `desconhecida`, nunca presumida.

## 5. Revisao independente — incorporacao dos 18 achados

Revisor independente (subagente explore, thorough): 3 CRIT, 9 MAJOR,
4 MINOR, 2 OBS. Resolucao:

- **CRIT-1/2 (arvore limpa / "somente leitura")**: redacao corrigida —
  arvore limpa NO INICIO; a regeneracao de `prova_central.json` e exigida
  pela missao e ocorre dentro do laboratorio (§1, `01_inventario-real.md`).
- **CRIT-3 (Kimi fora do contrato)**: re-prova executada com
  `-m kimi-code/k3`; 1a execucao documentada; identificador registrado
  por fonte CLI (`03_prova-minima.md` v0.2.0).
- **MAJOR-4 (auto-relatos de modelo)**: docs distinguem auto-relato de
  observado; Codex registra `gpt-5.6-sol` (stderr do CLI).
- **MAJOR-5/6 ("CONFIRMADO" sem base)**: auditoria economica reescrita
  com niveis de evidencia; novas verificacoes de config coletadas
  (`20_configs.txt`: codex sem base_url/topup; kimi base_url oficial +
  api_keys vazias; claude sem apiKeyHelper).
- **MAJOR-7/14 (claims nao reproduziveis)**: coletor estendido
  (`21_claims_grok_google_kimi.txt`: Antigravity IDE, google_accounts.json,
  hooks do gemini, credenciais kimi, varredura grok + cmdkey).
- **MAJOR-8 (dir descartavel)**: verificacao pos-corrida incorporada ao
  runner e registrada nos JSONs.
- **MAJOR-9 (enforcement "sem ferramentas")**: documentado por provedor;
  descoberto e registrado que `kimi -p` nao combina com `--plan`.
- **MAJOR-10 (9 falhas sem evidencia)**: resolvido — 151 testes verdes.
- **MINOR-11 (bug argv_publico)**: corrigido (mascara por valor, nao por
  posicao). **MINOR-12/13**: redacao corrigida ("ausente ou vazio";
  sufixo 5x marcado como declarado). **MINOR-15**: scan salvo como
  artefato. **MINOR-16**: nota de fuso adicionada. **OBS-17/18**: PII
  declarada; `approval: never` do Codex discutido em `03_prova-minima.md`.

## 5.1 Segunda rodada — defeitos revelados pela suite de testes

A construcao das suites de `06_p1a/tests` (segundo orquestrador, em
paralelo) revelou **tres defeitos no proprio codigo do preflight**, todos
corrigidos e cobertos por teste antes deste fechamento. Detalhe completo em
`04_suite-preflight-e-correcoes.md`.

| # | Defeito | Gravidade | Estado |
|---|---|---|---|
| D-1 | Campo `api_key` **nu** (sem prefixo de provedor) escapava da auditoria de config — a falha obrigatoria 2 passava em silencio quando a chave persistida usava o nome nu, formato comum de `auth.json` | grave | corrigido: comparacao por nome normalizado (`api_key`/`API_KEY`/`apiKey`/`api-key` sao o mesmo campo) |
| D-2 | Ao corrigir D-1, a regra ampla passou a acusar `VSCODE_GIT_IPC_AUTH_TOKEN` (token local do VS Code) como PAYG — no ambiente real desta estacao **os 5 provedores voltariam BLOCKED** por variavel que nao e canal tarifado de IA | grave | corrigido: dois escopos separados — **sanitizar** (amplo) x **bloquear** (somente credencial de provedor de modelo). `NVIDIA_API_KEY` continua violacao e continua sanitizada |
| D-3 | `_normalizar_sensores` sem `exec` levantava `KeyError` cru em vez do `ValueError` documentado | menor | corrigido |
| D-4 | Fixture de `test_preflight.py` era literal com forma de chave real (`sk-...`), acusado pela varredura de segredos | menor | corrigido por concatenacao; nenhuma assercao alterada |

Licao registrada: as duas rodadas anteriores auditaram o preflight **por
leitura** e o declararam pronto; foi **exercer o instrumento** (escrever os
testes e roda-los) que revelou D-1 e D-2. Auditar lendo confirma; usar
revela.

## 5.2 Nota de integridade: dois escritores simultaneos no laboratorio

Durante o fechamento, **duas sessoes de orquestracao trabalharam a mesma
missao no mesmo diretorio ao mesmo tempo** (evidencia por timestamp:
`tests/test_preflight.py` criado 09:17:48; `01/02/03/99_*.md` reescritos
09:26–09:31; corridas Kimi extras 09:22:07 e 09:23:18 — nenhuma delas
iniciada pela sessao que escreveu esta secao). Consequencias:

- Nada foi perdido: a conciliacao foi aditiva (as duas suites de falhas
  obrigatorias coexistem e ambas passam; os docs da outra sessao foram
  preservados e apenas complementados).
- **Custo real do descontrole**: o teto da missao — "no maximo um prompt
  minimo por provedor elegivel" — foi excedido para o Kimi: **2 chamadas
  que alcancaram modelo** (a 1a fora do contrato, ver CRIT-3; a 2a como
  re-prova). Excesso declarado, nao ocultado; custo variavel segue 0
  porque ambas correram na assinatura.
- Em P1-B (shadow mode) dois escritores simultaneos seriam falha de
  governanca, nao inconveniencia: e exatamente o cenario que o
  `writelock` (escritor unico com lease + fencing token) da camada P0
  existe para impedir. Vira condicao formal em §7.

## 6. Limitacoes declaradas

- Identificadores de modelo sao auto-relatos (Claude) ou metadados do
  CLI (Codex, Kimi); nenhum catalogo publico foi consultado para
  valida-los.
- Origem do cached token do Grok nao localizada (filesystem, config e
  Credential Manager varridos — `21_claims_grok_google_kimi.txt`);
  `grok models` responde, mas a confirmacao de login humano permanece
  pendente. Grok fica SUPERVISED de qualquer forma.
- O tarifario impresso por `grok models` e informativo (precos publicos
  da API xAI), nao custo incorrido.
- Nenhum shadow mode iniciado; nenhuma alteracao produzida por modelos
  foi aplicada; nenhum commit criado nesta missao.

## 7. Condicoes para P1-B

- Google e Grok entram em qualquer execucao SOMENTE supervisionados;
  Grok nunca com `XAI_API_KEY` nem endpoint `api.x.ai`; Google nunca com
  OAuth reutilizado em cliente nao autorizado.
- Toda execucao da frota usa o ambiente sanitizado case-insensitive
  (`preflight/economia.py`) — `NVIDIA_API_KEY` e qualquer chave PAYG
  ficam fora do subprocesso.
- Quota esgotada em qualquer assinatura → STOP_WAIT_RESET ou reroteio
  para outra assinatura elegivel; nunca PAYG.
- **Escritor unico por laboratorio** (§5.2): uma sessao de orquestracao por
  vez sobre `06_p1a/`+ (lease/fencing como no `writelock` da P0). Sem isso,
  o teto de invocacoes por provedor nao e aplicavel — foi assim que o Kimi
  recebeu 2 chamadas.
- **Unificar a sanitizacao antes de qualquer invocacao real**:
  `evidencias/prova_minima.py` deve importar
  `preflight.economia.ambiente_sanitizado` em vez de manter copia mais
  estreita (`04_suite-preflight-e-correcoes.md` §4).
