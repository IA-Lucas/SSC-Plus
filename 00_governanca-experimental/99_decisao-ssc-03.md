---
id: SSC-DEC-03
titulo: Relatorio e Decisao da Missao SSC+ 0.2.1 (hardening, baseline e portao para P1)
tipo: decisao-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Relatorio e Decisao da Missao SSC+ 0.2.1

> Hardening da P0: preservacao da 0.2 como evidencia, correcao das falhas da
> revisao independente e portao para P1. Fase offline, isolada, sem rede, sem
> API, sem credencial, sem provider real, sem escrita fora do SSC-Plus.

## DECISAO: **READY-FOR-P1**

As 13 correcoes estao aplicadas e com regressao propria, a bateria esta em
**91 testes / 0 falhas / 0 skips** (teste critico de junction real no
Windows), a cobertura esta medida (100% via `trace` stdlib) e a revisao
independente (Claude Opus 4.8, familia distinta do autor) vereditou
**APROVADO-COM-RESSALVAS** com 13/13 itens OK e zero achados CRITICO/MAIOR —
as 4 ressalvas MENOR foram **endereçadas e revalidadas** nesta missao
(§4). O shadow mode (P1) esta liberado para definicao de escopo; esta
missao NAO o iniciou.

## 1. PORTAO A — commit curado

- `.gitignore` atualizado: exclui `05_p0/saidas/labs/` (CAS, sessoes,
  EventLogs, checkpoints, locks, temporarios de teste e cobertura),
  `chave_selo.bin`, `*.jsonl`, `*.tmp`, `*.trace`, `.coverage`, `htmlcov/`.
  Mantidos: codigo, testes, contratos, diffs, tarefas-ouro, fixtures,
  snapshots, relatorios e JSONs agregados (`05_p0/saidas/*.json`).
- Prova de nao-versionamento: staging explicito por caminho (sem
  `git add -A`); `git ls-files --cached | grep -Ei
  'saidas/labs|chave_selo|\.jsonl$|__pycache__|\.pyc$|\.env|\.key|\.pem|
  secret|\.tmp$|coverage|trace'` → **vazio**; scan de padroes de segredo no
  indice → apenas fixtures sinteticas de `test_seguranca.py`.
- Commit `33bc963` **"experimental baseline — ADJUST"** — sem tag, sem
  remoto (`git tag` = 0, `git remote -v` = 0).

## 2. Correcoes obrigatorias (13/13 aplicadas)

| # | Correcao | Onde | Regressao |
|---|---|---|---|
| 1 | RoutingDecision persistida + hasheada; Execution usa so a copia canonica; mutacao recusada | `kernel.py` (`decisao_canonica`, `_hashes_decisao`, `DecisaoMutada`), `execution.py` | `test_decisao_mutada_recusada` |
| 2 | ValidationVerdict prova a cadeia (attempt/WU/decisao/contexto/criterios/artefato/linhagem) | `kernel.py` `registrar_veredito` | `test_veredito_cruzado_attempt_de_A_nao_conclui_B` |
| 3 | Reducer validado antes do append; rejeitado nao duravel, estado restaurado | `kernel.py` `_emitir` + `_snapshot_estado`/`_restaurar_estado` | `test_reducer_rejeitado_nada_duravel` |
| 4 | Escritor unico entre processos: lock/lease (msvcrt/fcntl) + fencing token | `writelock.py`, `kernel.py` `_adquirir_lock` | `test_lock_segundo_processo_recusado`, `test_crash_de_processo_retomada_por_outro_processo`, `test_lock_obsoleto_fencing_token` |
| 5 | Idempotency key com fingerprint; conflito tipado; chave propagada ao provider | `eventlog.py` (`EventoConflitoIdempotencia`), `providers.py`, `execution.py` | `test_idempotencia_reentrega_aceita_payload_diferente_conflito`, `test_idempotency_key_propagada_ao_provider` |
| 6 | Fallback = NOVA RoutingDecision (todos os portoes), selecao real, mesmo envelope | `execution.py` (fallback via `router.rerotear`) | `test_fallback_gera_nova_decisao_selecao_real_no_envelope` |
| 7 | ContextPackage ligado ao work_unit_id real; bytes no CAS (`bytes_ref`); falha fechada; catches de pacote vazio removidos | `kernel.py` (`montar_contexto`, `ler_pacote`), `router.py`, `judge.py`, `execution.py` | `test_contexto_corrompido_ou_ausente_falha_fechada`, `test_contexto_ligado_a_outra_workunit_recusado` |
| 8 | Checkpoint pelo ultimo evento valido/seq, nunca por UUID | `kernel.py` `retomar` | `test_checkpoint_escolhido_por_seq_nao_por_uuid` |
| 9 | Divergencia modelo/effort observado × resolvido = falha fechada (escala) | `execution.py`, enum `divergencia-executor` | `test_divergencia_modelo_effort_falha_fechada` |
| 10 | IDs validados em caminhos; Evidence Plane com CAS read-only sem criar diretorios | `kernel.py` `_validar_id`, `cas.py` (`somente_leitura`), `evidence.py` | `test_ids_invalidos_em_caminhos_recusados`, `test_evidence_plane_readonly_sem_criar_diretorios` |
| 11 | `causado_por` na mesma linhagem; payload CAS existente/integro no replay | `kernel.py` `_emitir`, `_replay_de_zero` | `test_causado_por_fora_da_cadeia_recusado` |
| 12 | RetryEvent 1..3 e teto de backoff (60s); indeterminado nunca repete | `contratos.py`, `execution.py` | `test_retry_fora_dos_limites_recusado`, `test_backoff_teto_aplicado_e_indeterminado_nao_repete` |
| 13 | Threat model declarado (HMAC local != defesa contra atacante com a chave; credencial futura so por referencia/cofre) | `05_p0/THREAT-MODEL.md` | documento |

## 3. Portao Windows e testes

- **Prova real de junction/reparse point**: `test_ic5_fuga_por_junction_real`
  cria junction de verdade via `mklink /J` (sem privilegio) apontando para
  fora da raiz; `resolver_contido` e `ler_arquivo_contido` recusam. O antigo
  skip (WinError 1314) foi eliminado — **0 skips**. TOCTOU reduzido em
  `ler_arquivo_contido` (fstat×stat + re-resolucao apos abertura).
- **Temporarios de teste**: redirecionados para `05_p0/saidas/labs/tests/`
  (pasta ignorada), criados por `apoio.novo_lab()` e limpos por
  `apoio.limpar_lab()` a cada teste. Temp do SO nao e mais usado.
- **Resultado**: `python -m unittest discover -s 05_p0/tests` → **91 testes,
  0 falhas, 0 skips** (73 anteriores + 18 regressoes novas). Prova central
  reexecutada: **18/18 assercoes**. Corridas TO-1..TO-5 reexecutadas: OK.
- **Cobertura**: medida com `trace` (stdlib) via `05_p0/cenarios/cobertura.py`
  → **2296/2296 linhas (100%)** dos modulos `ssc_p0`; detalhes em
  `05_p0/saidas/labs/cobertura/` (ignorado). Metodo declarado; nenhum
  percentual inventado.

## 4. Revisao independente

- **Revisor**: Claude Opus 4.8 (`claude-opus-4-8`), Anthropic — **familia
  verificavel e distinta do autor** (Kimi/Moonshot). Kimi nao revisou o
  proprio codigo. Prompt em `logs/prompt-revisao-0.2.1.md`; relatorio
  integral em `logs/revisao-independente-0.2.1-claude.md`; diff revisado em
  `logs/diff-0.2.1-hardening.patch` (3079 linhas, 29 arquivos).
- **Metodo do revisor**: rodou a suite (91 passed, 50 subtests), leu os 13
  pontos no codigo e nos testes e sondou caminhos adversariais.
- **Veredito**: **APROVADO-COM-RESSALVAS** — 13/13 itens OK; zero achados
  CRITICO/MAIOR; 4 MENOR + 1 nota.
- **Ressalvas endereçadas nesta missao** (e revalidadas: 91 testes OK,
  prova central 18/18, corridas OK, cobertura 2297/2297):
  1. `except Exception` generico no fallback → estreitado para
     `(RotaVetada, ct.FalhaContrato)`; bug de programacao nao e mais
     rotulado de veto (`execution.py`).
  2. Invariante do item 1 re-verificada pos-fallback: a decisao de fallback
     tambem passa por `decisao_canonica` antes de executar (`execution.py`).
  3. `_ler_fence` → 0 em erro: comentario no codigo declara a dependencia
     do lock do SO (fencing = defesa secundaria; THREAT-MODEL §2).
  4. Comentario impreciso "reducer validado em copia" corrigido
     (`kernel.py` — a fold executa antes do append com rollback por
     snapshot).
  - Nota 5 (idempotencia de efeito vive no EventLog, nao no provider falso)
    registrada como limitacao, nao exige codigo.

## 5. Fechamento

- Commit final **"SSC+ 0.2.1 hardening — READY-FOR-P1"** com staging
  explicito (sem `git add -A`), working tree limpa, sem tag e sem remoto.
- Inventario e prova de zero runtime/chave versionados: verificacao
  `git ls-files` contra padroes proibidos → vazio (mesma rotina do PORTAO A).
- Hashes: `git log` registra baseline `33bc963` (ADJUST) + commit final;
  relatorio reproduzivel: `python -m unittest discover -s 05_p0/tests`,
  `python 05_p0/cenarios/prova_central.py`,
  `python 05_p0/cenarios/corridas_to.py`,
  `python 05_p0/cenarios/cobertura.py`.

## 6. Limitacoes conhecidas (remanescentes)

- O lock entre processos cobre um escritor por sessao na mesma maquina;
  nao ha coordinador distribuido (fora de escopo da P0).
- `fsync` de diretorio ignorado no Windows (durabilidade de rename reduzida)
  — herdado da 0.2, declarado.
- Threat model: HMAC local nao defende contra atacante com acesso a
  `chave_selo.bin` (declarado em `THREAT-MODEL.md` §2).
- Testes de concorrencia multiprocesso usam `spawn`; o crash e via
  `terminate()` (SIGKILL equivalente), nao falha de hardware.
