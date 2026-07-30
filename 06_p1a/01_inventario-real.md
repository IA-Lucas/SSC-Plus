---
id: SSC-P1A-01
titulo: Inventario real da frota (preflight P1-A)
tipo: evidencia-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Inventario real da frota — P1-A

> Coleta de 2026-07-30 na maquina real (Windows 11, Git Bash). Nenhum
> token, cookie, chave ou segredo foi registrado — apenas metadados, flags
> booleanas e saidas de status. Registros contem PII operacional (e-mail da
> conta, caminhos com nome de usuario), que nao e segredo. Evidencias brutas
> reproduziveis em `evidencias/coleta-20260730-090127/` (1a rodada) e
> `evidencias/coleta-20260730-092436/` (2a rodada, pos-revisao); regenerar
> com `bash 06_p1a/evidencias/coletar.sh`. A coleta NAO escreve fora do
> repositorio-laboratorio; a unica escrita e a regeneracao de
> `05_p0/saidas/prova_central.json`, exigida pela propria missao
> ("reexecutar a prova central").

## Legenda de resultado

- **ELIGIBLE**: canal oficial + assinatura confirmada + headless disponivel +
  economia limpa; apto a prova minima real.
- **SUPERVISED**: tudo verde, mas a missao impoe supervisao humana
  permanente (Google e Grok, por regra explicita).
- **BLOCKED**: qualquer violacao economica/de auth; fora da frota.

## 1. Codex — ChatGPT Pro 5x (tier declarado; CLI nao expoe) → **ELIGIBLE**

| Campo | Valor observado |
|---|---|
| CLI e versao | `codex` 0.145.0 (standalone windows-x86_64) |
| Caminho | `C:\Users\<USUARIO>\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` |
| Canal oficial | ChatGPT (`codex login status` → "Logged in using ChatGPT") |
| Metodo de login | OAuth ChatGPT (device/browser), nao API key |
| Origem da credencial | `~/.codex/auth.json`, `auth_mode: chatgpt`; verificacao booleana: `OPENAI_API_KEY` ausente ou vazia ("presente e nao-vazia: False") |
| Plano reconhecido | CLI nao expoe o tier da assinatura (nenhum claim de plano nos JWTs); plano "ChatGPT Pro 5x" declarado pela conta — confirmacao humana no login |
| Modelos descobertos | CLI nao lista catalogo. Na prova minima: auto-relato do modelo `gpt-5`; modelo EFETIVO observado no stderr do CLI: `gpt-5.6-sol` (auto-relatos nao sao verificaveis; o observado prevalece) |
| Headless / ACP | `codex exec` (nao-interativo); sem ACP (ha `mcp-server` stdio) |
| Quota e reset | Nao exposta pelo CLI; consulta web fora de escopo → `desconhecida` |
| Automacao | headless supervisionado = permitido |
| Restricao contratual | uso via assinatura ChatGPT; termos OpenAI; sem PAYG |

## 2. Claude Code — Claude Max 5x ("max" confirmado pelo CLI; sufixo 5x declarado) → **ELIGIBLE**

| Campo | Valor observado |
|---|---|
| CLI e versao | `claude` 2.1.220 (Claude Code) |
| Caminho | `C:\Users\<USUARIO>\.local\bin\claude` |
| Canal oficial | claude.ai (firstParty) |
| Metodo de login | OAuth claude.ai |
| Origem da credencial | `claude auth status` → `loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty` |
| Plano reconhecido | `subscriptionType: "max"` (reportado pelo proprio CLI) |
| Modelos descobertos | identificador publico auto-relatado na prova minima: `claude-opus-5[1m]` (auto-relato, nao verificavel contra catalogo publico pelo CLI) |
| Headless / ACP | `claude -p` (print mode); sem ACP |
| Quota e reset | nao exposta em modo headless (`/usage` e interativo) → `desconhecida` |
| Automacao | headless supervisionado = permitido |
| Restricao contratual | assinatura Max; termos Anthropic; sem PAYG |

## 3. Kimi Code — Allegretto (tier declarado; CLI nao expoe) → **ELIGIBLE**

| Campo | Valor observado |
|---|---|
| CLI e versao | `kimi` 0.30.0 (Kimi Code CLI) |
| Caminho | `C:\Users\<USUARIO>\.kimi-code\bin\kimi` |
| Canal oficial | Moonshot/Kimi Code (`kimi login`, device-code flow); `config.toml` com `base_url` oficial `api.kimi.com/coding/v1` |
| Metodo de login | OAuth (`kimi provider list` → `managed:kimi-code type=kimi source=oauth`); os 3 campos `api_key` do config.toml estao VAZIOS |
| Origem da credencial | `~/.kimi-code/credentials/kimi-code.json` (existencia confirmada na coleta 2; conteudo nao lido) |
| Plano reconhecido | CLI nao expoe o tier "Allegretto" em modo nao-interativo; confirmacao humana no login |
| Modelos descobertos | 4 modelos no provider gerenciado; default `kimi-code/k3`. Na prova minima o modelo auto-relatou apenas "Kimi (Moonshot AI)" (sem ID interno acessivel ao modelo); identificador publico registrado = `kimi-code/k3` (fonte: `kimi provider list` + flag `-m` da invocacao) |
| Headless / ACP | `kimi -p`; ACP via `kimi acp` |
| Quota e reset | nao exposta pelo CLI → `desconhecida` |
| Automacao | headless supervisionado = permitido |
| Restricao contratual | assinatura Kimi Code; sem PAYG |

## 4. Google Antigravity — Google AI Pro → **SUPERVISED** (regra da missao)

| Campo | Valor observado |
|---|---|
| CLI e versao | `gemini` 0.52.0 (npm); Antigravity IDE instalada em `~/AppData/Local/Programs/Antigravity IDE`, SEM CLI `antigravity` no PATH |
| Caminho | `C:\Users\<USUARIO>\AppData\Roaming\npm\gemini` |
| Canal oficial | `oauth-personal` (confirmado em `~/.gemini/settings.json` → `security.auth.selectedType`) |
| Metodo de login | OAuth conta Google pessoal |
| Origem da credencial | `~/.gemini/` (google_accounts.json presente; conteudo nao lido); nenhuma chave de API persistida em settings |
| Plano reconhecido | CLI nao expoe tier "Google AI Pro"; confirmacao humana no login |
| Modelos descobertos | nao consultados (SUPERVISED: nenhuma chamada nesta fase) |
| Headless / ACP | `gemini -p`; ACP via `gemini --acp` |
| Quota e reset | nao consultada → `desconhecida` |
| Automacao | condicional ate prova do canal permitido — SUPERVISED permanente na P1 |
| Restricao contratual | OAuth pessoal NAO pode ser reutilizado em cliente nao autorizado; somente canal oficial |
| Observacao | `settings.json` tem hooks externos (BeforeAgent/AfterAgent/BeforeTool/AfterTool) chamando script local — fator adicional para manter SUPERVISED |

## 5. Grok Build — SuperGrok → **SUPERVISED** (regra da missao)

| Campo | Valor observado |
|---|---|
| CLI e versao | `grok` 1.1.7 (npm, pacote `grok-dev`) |
| Caminho | `C:\Users\<USUARIO>\AppData\Roaming\npm\grok` |
| Canal oficial | Grok Build CLI (xAI) |
| Metodo de login | cached token da assinatura (esperado); **origem nao localizada**: sem arquivo de credencial visivel em `~/.grok/`, `~/.config/grok` vazio, nada no Windows Credential Manager; `grok models` responde (5 modelos), o que indica sessao funcional OU listagem publica — confirmacao humana de login pendente |
| Origem da credencial | indeterminada nesta coleta (ver linha acima); NENHUM `XAI_API_KEY` no ambiente |
| Plano reconhecido | CLI nao expoe tier "SuperGrok"; confirmacao humana no login |
| Modelos descobertos | grok-4.3, grok-4.20-multi-agent-0309, grok-4.20-0309-reasoning, grok-4.20-non-reasoning, grok-3-mini (os precos exibidos sao o tarifario PUBLICO da API xAI impresso pelo CLI — informativo, nao custo incorrido) |
| Headless / ACP | `grok -p` (headless), `--format json`; sem ACP |
| Quota e reset | nao exposta → `desconhecida` |
| Automacao | SUPERVISED = permitido; UNATTENDED = TERMS_REVIEW_REQUIRED |
| Restricao contratual | somente cached token da assinatura; NUNCA `XAI_API_KEY`; NUNCA endpoint `api.x.ai` PAYG; `--api-key` e `--batch-api` do CLI sao PROIBIDOS na frota |

## Resumo

| Provedor | Plano | Auth efetiva | Headless | Resultado |
|---|---|---|---|---|
| Codex | ChatGPT Pro 5x (declarado; CLI nao expoe) | OAuth chatgpt | `codex exec` | **ELIGIBLE** |
| Claude | Max (CLI confirma `max`) | OAuth claude.ai | `claude -p` | **ELIGIBLE** |
| Kimi | Allegretto (declarado; CLI nao expoe) | OAuth managed:kimi-code | `kimi -p` / ACP | **ELIGIBLE** |
| Google | AI Pro (declarado) | oauth-personal | `gemini -p` / ACP | **SUPERVISED** |
| Grok | SuperGrok (declarado) | cached token (origem a confirmar) | `grok -p` | **SUPERVISED** |
