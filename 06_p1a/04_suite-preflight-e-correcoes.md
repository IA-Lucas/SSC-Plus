---
id: SSC-P1A-04
titulo: Suite de testes do preflight e correcoes de defeito (P1-A)
tipo: evidencia-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Suite de preflight e correcoes — P1-A

> Laboratorio experimental, sem autoridade. Complementa
> `99_decisao-p1a.md` §3 (linha "Novos testes de preflight") e registra os
> tres defeitos que a suite revelou no proprio codigo do preflight.
> Nenhum CLI real foi invocado por nenhum destes testes: toda execucao
> externa passa por sensor injetavel.

## 1. Contagem por arquivo (contada por ferramenta, nao de memoria)

| Arquivo | Testes | O que prova |
|---|---|---|
| `tests/test_preflight.py` | 15 | as 9 falhas + caminho feliz, por **sensor explosivo** (qualquer sonda apos o bloqueio levanta AssertionError) |
| `tests/test_falhas_obrigatorias.py` | 35 | as 9 falhas, por **contagem de sondas** (uma classe por falha + meta-teste de cobertura das 9) |
| `tests/test_economia.py` | 34 | espelho fiel da `POLITICA_ECONOMICA` da P0, auditorias de ambiente/config/status, round-trip dos 9 erros tipados |
| `tests/test_adaptadores.py` | 38 | versao/login/modelos dos 5 parsers, quota nunca presumida, sensor real com `subprocess.run` substituido, sondas somente de diagnostico |
| `tests/test_pipeline.py` | 29 | classificacao dos 5, teto SUPERVISED de Google/Grok, ordem do bloqueio, invariantes da especificacao |
| `tests/test_isolamento.py` | 20 | o preflight nao escreve, nao abre rede, nao aprova automaticamente e nao registra segredo |
| **total** | **171** | 0 falhas, 0 skips |

Regressao preservada: `05_p0/tests` **100 testes, 0 falhas**; prova central
**18 assercoes, 20 eventos**.

As duas primeiras suites sao implementacoes **independentes** das mesmas 9
falhas, com tecnicas de prova diferentes (sensor explosivo x contagem de
sondas). A redundancia e deliberada: uma pega o que a outra deixa passar.

## 2. Defeitos encontrados pela suite e corrigidos

### 2.1 Chave persistida com nome nu escapava da auditoria (grave)

`_PADRAO_CHAVE_PAYG` exigia underscore antes do sufixo
(`_(api_key|auth_token|...)$`). Logo, o campo **`api_key` nu** — formato
comum de `auth.json`, por exemplo
`{"providers": {"openai": {"api_key": ...}}}` — **nao era detectado**.
Era exatamente a falha obrigatoria 2 (chave persistida substituindo
OAuth) passando em silencio.

Correcao: comparacao por **nome normalizado** (so letras/digitos,
minusculas) com sufixos conhecidos. Agora `api_key`, `API_KEY`, `apiKey`,
`api-key`, `accessToken` e `openai_api_key` caem todos na mesma regra.

### 2.2 Escopo de bloqueio confundido com escopo de sanitizacao (grave)

Ao corrigir 2.1, a regra mais ampla passou a acusar
`VSCODE_GIT_IPC_AUTH_TOKEN` — token local do VS Code — como chave PAYG.
Efeito pratico: no ambiente real desta estacao, **os cinco provedores
voltariam BLOCKED** por uma variavel que nao e canal tarifado de IA.

Correcao: dois escopos explicitos, com nomes distintos no codigo.

| Escopo | Funcao | Abrangencia | Efeito |
|---|---|---|---|
| Sanitizar | `_nome_payg` | amplo: qualquer nome com cara de credencial | nao entra no subprocesso |
| Bloquear | `_nome_payg_provedor` | estreito: credencial de **provedor de modelo** | `payg_api = DENY`, BLOCKED |

`auditar_ambiente` (bloqueio) usa o escopo estreito; `ambiente_sanitizado`
e `auditar_config` usam o amplo — numa config de CLI o campo nu ja e
chave substituindo OAuth, sem precisar de familia de provedor.

Consequencia auditada: `NVIDIA_API_KEY` (fora da frota, familia de
provedor de IA) **continua** violacao economica e continua sanitizada;
`VSCODE_GIT_IPC_AUTH_TOKEN` e sanitizado **sem** bloquear.

### 2.3 Sensor faltante levantava erro nao tipado (menor)

`_normalizar_sensores({"modelos": ...})` levantava `KeyError` cru em vez
do `ValueError` documentado. Corrigido com `setdefault("exec", None)`.

### 2.4 Fixture com forma de chave real (menor)

`tests/test_preflight.py` definia o valor ficticio como literal
`sk-...`, que casa com o padrao de chave real da varredura de segredos.
Passou a ser montado por concatenacao: o valor existe em memoria para o
teste, mas nenhuma linha do arquivo casa com o padrao. Nenhuma assercao
mudou.

## 3. O que a suite de isolamento prova (e como)

- **Nao escreve**: varredura do proprio fonte de `preflight/` (sem
  `open(`, `shutil`, `os.remove/makedirs/rename`, `write_text`, `mkdtemp`)
  e prova empirica — instantaneo sha256 de **todos** os arquivos de
  `06_p1a/` antes e depois de uma varredura completa dos 5 provedores:
  identico.
- **Nao abre rede**: ausencia de `urllib.request`, `http.client`,
  `requests.`, `socket.` (o `urlparse` importado e parser puro).
- **Um unico subprocesso**: `subprocess.run` existe somente em
  `adaptadores.py`, exatamente uma vez, e o trecho entre
  `def sensor_subprocess` e a chamada contem `ambiente_sanitizado(env)` —
  o filho nunca recebe credencial.
- **Sondas sao diagnostico**: todo comando das 5 especificacoes esta numa
  allowlist (`--version`, `login`, `status`, `auth`, `models`, `provider`,
  `list`, `--list-models`); nenhum contem `exec`, `-p`, `--yes`,
  `--always-approve`, `--api-key` ou `--batch-api`.
- **Zero segredo**: 7 padroes de VALOR de credencial (`sk-`, `xai-`,
  `AIza`, `ghp_`, JWT, `Bearer`, `api_key: <valor longo>`) varridos em
  todo `.py/.md/.json/.txt/.sh` de `06_p1a/` — zero achados; com
  contraprova de que os padroes detectam segredo plantado e de que a
  varredura tem alcance real (>10 arquivos).
- **Prova minima dentro do contrato**: o prompt do runner e exatamente o
  da missao, sem termo do LucaX; os comandos existem so para os 3
  ELIGIBLE (Google/Grok sem invocacao); execucao em `mkdtemp` com
  `cwd=tmp`; diretorio descartavel vazio nos registros que o verificam.
- **Sanitizacao sem deriva**: o runner duplica a regra de sanitizacao; o
  teste prova que a canonica e **pelo menos tao estrita** quanto a do
  runner para toda a bateria de nomes — se alguem afrouxar a canonica, o
  teste quebra.

## 4. Limitacao declarada desta suite

`evidencias/prova_minima.py` mantem sua propria copia da sanitizacao em
vez de importar `preflight.economia.ambiente_sanitizado`. A copia e mais
estreita (nao pega nome nu nem `apiKey`); hoje isso nao muda nenhum
resultado registrado, porque as variaveis do ambiente real tem prefixo.
Antes de qualquer nova invocacao real em P1-B, o runner deve **importar** a
sanitizacao canonica. O teste
`test_sanitizacao_do_script_e_coberta_pela_canonica` mantem a direcao da
divergencia sob vigilancia; ele nao substitui a unificacao.
