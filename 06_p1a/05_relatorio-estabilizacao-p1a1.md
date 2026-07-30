---
id: SSC-P1A1-RELATORIO
titulo: Relatorio de Estabilizacao SSC+ P1-A.1 — portao para P1-B
tipo: relatorio-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Relatorio de Estabilizacao — Missao SSC+ P1-A.1

> Portao de estabilizacao da P1-A antes do shadow mode (P1-B). Nenhum
> modelo foi invocado nesta missao; nenhuma escrita ocorreu fora do
> laboratorio e da copia datada autorizada. Documento aditivo: nada da
> P1-A foi reescrito — somente corrigido, redigido e coberto por teste.

## 1. Pre-condicoes (verificadas)

| Item | Resultado |
|---|---|
| HEAD `0da9d41` descendente de `a96eda5` | OK (`git merge-base --is-ancestor`) |
| Unica mudanca inicial: `06_p1a/` nao versionada | OK (`git status --porcelain`) |
| Lock exclusivo com lease + fencing ANTES da primeira escrita | OK — `locks/repo-p1a1.{lock,fence,lease}` via `LockSessao` da P0, fencing token 1, lease renovado a 5 s; segunda aquisicao recusada (`LockIndisponivel`) |
| Copia datada fora do repositorio | OK — `E:/LucasIA/Projetos/SSC-Plus_copia-20260730-100839`, 2203 arquivos, `diff -r` vazio; os dois `12_claude.txt` originais existem SOMENTE la |

## 2. Correcoes — rastreabilidade achado → codigo → teste

### E-1. PII operacional e caminhos locais em evidencias (curadoria)

- **Achado**: os dois `evidencias/coleta-*/12_claude.txt` continham PII
  operacional (e-mail da conta, 2 ocorrencias cada) e 18 arquivos de
  evidencia/doc traziam caminhos locais de usuario (`C:\Users\<USUARIO>`
  e a forma curta `<USUARIO>~1`). O repositorio versionado nao tinha
  nenhum caso — a P1-A nao podia introduzir o primeiro.
- **Codigo/acao**: redacao dos 20 arquivos para derivados
  (`<EMAIL-REDACTED>`, `<USUARIO>`, `<USUARIO>~1`); originais preservados
  SOMENTE na copia externa datada; `evidencias/MANIFESTO-REDACTADOS.json`
  registra sha256 do original e do redigido + contagens, sem nenhum
  valor. Varredura ampliada (e-mail, sk-, xai-, AIza, ghp_, JWT, Bearer,
  campos de credencial preenchidos, AWS): zero achados restantes.
  `.gitignore` passa a ignorar `locks/`; `__pycache__/` ja era ignorado.
- **Teste**: `tests/test_estabilizacao_p1a1.py::ZeroPiiNosArtefatos`
  (nenhum e-mail sob `06_p1a/`); `test_isolamento.py::ZeroSegredo`
  (padroes de segredo) — ambos verdes.

### E-2. Sanitizacao duplicada no runner da prova minima

- **Achado**: `evidencias/prova_minima.py` mantinha copia propria e mais
  estreita (`CHAVES_PROIBIDAS` + `PADRAO_PAYG`): o nome nu `api_key` e
  variantes sem prefixo escapavam do runner que mais tarde invocaria
  provedores reais.
- **Codigo**: `evidencias/prova_minima.py` importa EXCLUSIVAMENTE
  `preflight.economia.ambiente_sanitizado`; a implementacao local foi
  removida; `env_vars_removidas_nomes` deriva da mesma funcao
  (`set(os.environ) - set(ambiente_sanitizado())`).
- **Teste**: `SanitizacaoUnica` (identidade da funcao importada, ausencia
  dos simbolos duplicados, nomes nus/camelCase/hifen/caixa sanitizados,
  `removidas` derivadas da canonica, token local nao tarifado sanitizado
  sem bloquear a frota, credencial de provedor sanitizada E bloqueada) +
  `test_isolamento.py::test_sanitizacao_do_script_e_a_canonica` e
  `::test_sanitizacao_canonica_cobre_todas_as_variantes`.

### E-3. Quota fail-open (`_quota_de`)

- **Achado**: login valido sem nenhuma evidencia de franquia retornava
  `disponivel` — "disponivel" por inferencia, violando "ausencia de
  evidencia = unknown".
- **Codigo**: `preflight/adaptadores.py` — `_quota_de` fail-closed:
  `esgotada` vence sempre; `disponivel` EXIGE sinal positivo observavel
  (`_MARCADORES_QUOTA_DISPONIVEL`); todo o resto e `desconhecida`,
  inclusive com login ativo.
- **Teste**: `QuotaFailClosed` (7 testes: sem evidencia → desconhecida;
  sinal positivo → disponivel; esgotada precede sinal positivo; sem
  login → desconhecida mesmo com sinal; pipeline ELIGIBLE com quota
  desconhecida nao bloqueia; pipeline propaga `disponivel` observada;
  esgotada segue bloqueando antes da descoberta). Contratos antigos
  atualizados em `test_adaptadores.py`, `test_pipeline.py`,
  `test_preflight.py` (saidas verdes sem sinal → `desconhecida`,
  coerente com `99_decisao-p1a.md` §4: quota nao exposta por nenhum CLI).

### E-4. Auditoria de config nao percorria listas nem normalizava endpoint

- **Achado**: `_achatar` so descia em dicts — uma chave PAYG ou endpoint
  dentro de lista (ex.: `providers: [{api_key: ...}]`) escapava; e a
  comparacao de campo de endpoint era literal (`low in _CHAVES_ENDPOINT`),
  deixando `api-base-url`, `apiBaseUrl`, `BASE-URL` de fora.
- **Codigo**: `preflight/economia.py` — `_achatar` percorre dicts E
  listas (`pai[indice]`; escalar de lista herda o nome do campo pai);
  endpoint comparado por nome normalizado
  (`_CHAVES_ENDPOINT_NORMALIZADAS`): `base_url`, `baseUrl`,
  `api-base-url` e equivalentes recebem o MESMO tratamento.
- **Teste**: `ConfigRecursivaENormalizada` (chave em lista com caminho
  `providers[0].api_key`; lista aninhada em dict; endpoint PAYG em lista
  herdando o campo pai; 8 grafias de endpoint detectadas; top-up em
  lista; endpoint de assinatura segue sem violacao).

### E-5. Auth desconhecida virava ELIGIBLE por inferencia

- **Achado**: `auditar_status` so negava auth PAYG; um `auth_mode`
  presente mas nao reconhecido passava em silencio — billing, endpoint
  ou auth desconhecido nao pode virar ELIGIBLE por inferencia.
- **Codigo**: `preflight/economia.py` — `auth_mode` presente e fora de
  `_AUTH_CONHECIDAS` (`subscription-oauth`, `cached-token`, `local`) gera
  `OAuthAusente` com codigo `P1A-AUTH-DESCONHECIDA`. Nenhum 10o tipo de
  erro criado (round-trip dos 9 preservado). Campo ausente/vazio segue
  coberto por `P1A-BILLING-DESCONHECIDO`, sem duplicar violacao.
- **Teste**: `test_auth_desconhecida_e_deny_nunca_inferida`,
  `test_auth_ausente_nao_duplica_billing_desconhecido`,
  `test_auth_desconhecida_no_spec_nunca_vira_eligible` (BLOCKED antes de
  qualquer sonda), `test_nove_tipos_de_erro_preservados`.

### E-6. Escritor unico ausente no ponto de entrada das operacoes P1

- **Achado**: a P1-A registrou dois orquestradores simultaneos no mesmo
  diretorio (`99_decisao-p1a.md` §5.2) e o writelock da P0 nao estava
  integrado a nenhum entry point P1 — em P1-B isso seria falha de
  governanca.
- **Codigo**: novo `06_p1a/escritor.py` (`EscritorP1`): lease JSON
  (`sessao/pid/token/renovado_em/expira_em`) + fencing token sobre o
  `LockSessao` da P0, com `renovar()`, `verificar()` (fencing + lease
  antes de cada escrita), recuperacao de lock expirado (sucessor
  incrementa o fence e o escritor antigo e recusado para sempre) e
  recusa de token obsoleto. Integrado em `prova_minima.main()`: aquisicao
  ANTES de qualquer escrita ou invocacao (segunda sessao sai com codigo
  3 sem tocar em nada), `verificar()` imediatamente antes de gravar
  evidencia, `liberar()` em `finally`. Estado de lock em `locks/` —
  runtime, ignorado pelo Git.
- **Teste**: `EscritorUnicoP1` (9 testes: concessao de lease+token;
  segunda sessao recusada; handoff com token incrementado; crash →
  recuperacao → token antigo recusado em `verificar()` e `renovar()`;
  renovacao estende o lease; lease expirado recusa escrita; lease
  ausente/ilegivel = morto; ordem estrutural no runner — `adquirir()`
  antes de `subprocess.run` e de `write_text`, `verificar()` antes de
  `write_text`; `locks/` no `.gitignore`).

### E-7. Caminho local embutido no fonte (`frota_real.py`)

- **Achado**: o executavel do Codex estava hardcoded com o nome de
  usuario da estacao — configuracao local dentro de codigo a versionar.
- **Codigo**: `preflight/frota_real.py` — `_CODEX_EXE` deriva de
  `os.path.expanduser("~")` em tempo de importacao; nenhum caminho local
  permanece no fonte.
- **Teste**: coberto por `test_adaptadores.py::test_argv_usa_o_executavel_declarado`
  (`endswith("codex.exe")`) e pela suite verde dos 5 provedores.

## 3. Provas reexecutadas (saida integral persistida)

| Prova | Resultado | Evidencia |
|---|---|---|
| P0 (`05_p0/tests`) | **100/100**, 0 falhas, 0 skips | `evidencias/p1a1-estabilizacao/02_testes_p0.txt` |
| P1-A (`06_p1a/tests`) | **211/211**, 0 falhas, 0 skips | `evidencias/p1a1-estabilizacao/03_testes_p1a.txt` |
| Prova central | **18/18** assercoes, 20 eventos | `evidencias/p1a1-estabilizacao/04_prova_central.txt` + `05_prova_central.json` |

Nota de contagem honesta: a exigencia nominal era "P1-A: 171/171". As
regressoes obrigatorias elevaram a suite para **211** (baseline 171 +
38 testes de estabilizacao + 2 splits em suites existentes), com 0
falhas e 0 skips — superconjunto estrito do exigido. Distribuicao:
test_adaptadores 39, test_economia 34, test_estabilizacao_p1a1 38,
test_falhas_obrigatorias 35, test_isolamento 21, test_pipeline 29,
test_preflight 15.

Exigencias cruzadas:

- **Zero chamada de modelo**: esta missao nao executou `prova_minima.py`
  nem nenhum CLI de provedor; toda a suite usa sensores falsos.
- **Zero escrita externa**: escritas apenas no laboratorio, na copia
  datada autorizada e em tempdirs de teste; `prova_central.json`
  rastreado foi restaurado ao HEAD apos a reexecucao (a copia da corrida
  fica em `05_prova_central.json`).
- **Zero segredo/PII versionado**: varredura dupla (E-1 +
  `ZeroPiiNosArtefatos`/`ZeroSegredo` em teste).

## 4. Curadoria do commit (staging explicito)

Versionados (staging arquivo a arquivo, nunca `git add -A`): documentos
`01–04`, `99_decisao-p1a.md`, `README.md`, este relatorio; `preflight/`
(5 modulos), `escritor.py`, `tests/` (8 arquivos); evidencias redigidas
das duas coletas, `prova-minima/`, `backups/`, `coletar.sh`,
`prova_minima.py`, `MANIFESTO-REDACTADOS.json`, `p1a1-estabilizacao/`;
`.gitignore` (acrescenta `locks/`).

Excluidos do Git: `__pycache__/` (todos), `locks/` (runtime do escritor
unico), credenciais/configuracoes locais (nenhuma presente — verificado
pela varredura) e os originais com PII (somente na copia externa).

## 5. Revisao independente

Revisor: subagente independente (explore, thorough), mesma linhagem de
agente desta sessao — **limitacao declarada**: a fronteira da missao
proibe invocar qualquer modelo, logo uma revisao por provider distinto
exigiria ferir a fronteira; a palavra final de READY-FOR-P1-B permanece
do humano (ver §7). Veredito do revisor: **APROVADO-COM-RESSALVAS**
(1 MAJOR, 4 MINOR, 7 OBS), com reexecucao independente da suite
(211 testes verdes) e reconferencia dos 20 sha256 do manifesto.

Incorporacao dos achados (todos, antes do commit):

- **MAJOR-1 (quota fail-open por substring)**: "quota information
  unavailable" casava `available`; "0 requests remaining", "requests
  remaining: 0" e "no calls left" classificavam quota esgotada como
  `disponivel`. Corrigido em `adaptadores.py`: sinais positivos casados
  por palavra (`\b`) e tres regex de esgotamento/zero-quota adicionadas.
  Regressoes: `test_zero_quota_em_grafias_alternativas_e_esgotada`,
  `test_negacao_nao_e_sinal_positivo`,
  `test_pipeline_bloqueia_quota_esgotada_em_grafia_alternativa`.
- **MINOR-2 (usuario local citado no proprio relatorio)**:
  autorreferencias redigidas; `ZeroPiiNosArtefatos` reforcado para
  varrer tambem o usuario local (tokens montados por concatenacao no
  teste).
- **MINOR-3 (curadoria nao auto-sustentavel)**: `evidencias/coletar.sh`
  ganhou redacao em linha (`redigir`: e-mail + usuario local) aplicada
  ao bloco do Claude e em passagem final sobre toda a coleta, mais
  `24_scan_pii.txt` — nova coleta nao reintroduz PII.
- **MINOR-4 (escritor unico so na prova minima)**: `coletar.sh` agora
  SEGURA o lock `p1-ops` (lease renovado a 5 s) do inicio ao fim; sob
  contencao aborta com codigo 3 antes de escrever ou invocar CLI
  (validado funcionalmente no bash: rc=3 com titular ativo).
- **MINOR-5 (chaves genericas de endpoint)**: `url`, `api_url`,
  `server` e `host` entram em `_CHAVES_ENDPOINT` (mesma normalizacao);
  regressao `test_chaves_genericas_de_endpoint_tambem_sao_auditadas`.
- **OBS**: teste comportamental do runner sob contencao
  (`test_runner_segunda_sessao_retorna_3_sem_invocar_nada`: rc=3, zero
  subprocesso). OBS benignos registrados sem acao: casamento de host
  por substring (fail-safe), `~` literal em claude/kimi (BLOCKED
  fail-safe), segundo `write_text` sem `verificar()` proprio (inocuo —
  o lock do SO segue detido).

## 6. Regras preservadas

Codex, Claude e Kimi permanecem candidatos ELIGIBLE somente sob os
portoes economicos; Google e Grok permanecem SUPERVISED; ausencia de
evidencia = unknown; nenhuma conclusao da P1-A/P1-A.1 autoriza execucao
autonoma. Nenhum inicio de P1-B nesta missao.

## 7. Decisao

**READY-FOR-P1-B** — sob reserva declarada e ratificacao humana.

Condicoes do portao, uma a uma:

| Condicao | Estado |
|---|---|
| Commit curado, sem tag nem remoto | OK — staging explicito, arquivo a arquivo |
| Working tree limpa ao final | OK (verificado pos-commit) |
| Lock efetivo (lease + fencing) | OK — sessao detem `locks/repo-p1a1.*` desde antes da 1a escrita; segunda sessao recusada |
| Sanitizacao unica | OK — `prova_minima.py` importa exclusivamente `preflight.economia.ambiente_sanitizado` |
| Quota/config corrigidas (fail-closed) | OK — incl. MAJOR-1 da revisao (negacao/zero-quota) |
| Regressoes persistidas | OK — P0 100/100, P1-A 211/211, central 18/18 em `evidencias/p1a1-estabilizacao/` |
| Revisao independente | OK com reserva — subagente independente (APROVADO-COM-RESSALVAS, tudo incorporado); MESMA linhagem de agente do autor. A fronteira "sem invocar modelo" impede provider distinto; a ratificacao humana final e o fechamento desta reserva |

Reserva: se o Soberano exigir revisao por provider distinto do autor,
esta missao nao a pode produzir sem violar a propria fronteira — nesse
caso a decisao fica ADJUST ate a revisao humana/distinta ocorrer.

Hash do commit, contagem de arquivos e impressao digital: registrados no
fechamento da missao (o hash nao pode constar no proprio commit) em
`locks/registro-commit-p1a1.txt` (runtime) e na resposta final ao
orquestrador.
