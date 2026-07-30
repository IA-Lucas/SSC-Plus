---
id: SSC-P1A-03
titulo: Prova minima real por provedor elegivel (P1-A)
tipo: evidencia-experimental
versao: 0.2.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Prova minima real — P1-A

> Um prompt minimo e nao sensivel por provedor ELIGIBLE, apos confirmacao do
> login pelos canais oficiais (status de auth coletado no inventario).
> Execucao em diretorio descartavel (`tempfile`), sem aprovacao automatica,
> sem conteudo do LucaX, com ambiente sanitizado case-insensitive
> (`NVIDIA_API_KEY` removida apenas do subprocesso — verificado nos JSONs).
> Runner reproduzivel: `python 06_p1a/evidencias/prova_minima.py <provedor>`.
> Artefatos: `evidencias/prova-minima/<provedor>-<ts>.json` (+ `.stdout.txt`).
>
> **v0.2.0** — incorpora a revisao independente: re-prova do Kimi com
> modelo fixado, enforcement por provedor esclarecido, verificacao
> pos-corrida do diretorio descartavel agora registrada no JSON
> (`dir_descartavel_arquivos_restantes`) e modelo efetivo do Codex lido do
> stderr do CLI.

Prompt (identico nas execucoes): `Retorne apenas PROVIDER_OK e o
identificador público do modelo.`

## Resultados (2026-07-30)

| Provedor | Comando | rc | Duracao | Resposta | Quota observavel |
|---|---|---|---|---|---|
| Codex | `codex exec --sandbox read-only --cd <tmp> --skip-git-repo-check --ephemeral` | 0 | 5,69 s | `PROVIDER_OK gpt-5` (auto-relato); modelo efetivo no stderr do CLI: `gpt-5.6-sol` | nao exposta pelo CLI |
| Claude | `claude -p --permission-mode plan` | 0 | 15,58 s | `PROVIDER_OK claude-opus-5[1m]` (auto-relato) | nao exposta pelo CLI |
| Kimi (1a) | `kimi -p` | 0 | 12,22 s | `PROVIDER_OK Kimi (Moonshot AI)` — **fora do contrato** (nome do assistente, sem ID de modelo) | nao exposta pelo CLI |
| Kimi (re-prova) | `kimi -p -m kimi-code/k3` | 0 | 23,00 s | `PROVIDER_OK Kimi` + declaracao de que o ID interno nao e acessivel ao modelo; identificador publico registrado = `kimi-code/k3` (fonte: `kimi provider list` + flag `-m`) | nao exposta pelo CLI |

Transparencia sobre a re-prova: a 1a execucao do Kimi nao cumpriu o
contrato (apontado pela revisao independente). A re-prova com `-m
kimi-code/k3` confirmou o canal e o modelo selecionado; o modelo nao
consegue introspectar seu proprio ID, entao o identificador publico e
registrado a partir do CLI (fonte externa ao auto-relato). Total: 2
prompts Kimi, 1 Codex, 1 Claude — todos nao sensiveis, mesma natureza.

## Enforcement "sem ferramentas / sem aprovacao automatica" por provedor

- **Codex**: `--sandbox read-only` (escrita negada pelo sandbox) +
  `--ephemeral` (sem persistencia de sessao). O stderr registra
  `approval: never` — seguro porque a negacao de escrita vem do SANDBOX,
  nao de auto-aprovacao de ferramentas.
- **Claude**: `--permission-mode plan` — enforcement read-only pelo
  proprio CLI (ferramentas de escrita bloqueadas; leitura permitida, mas o
  prompt nao referencia arquivos e o cwd era vazio).
- **Kimi**: `kimi -p` NAO combina com `--plan` ("Cannot combine --prompt
  with --plan", verificado). A protecao e o modo de permissao padrao
  (aprovacao interativa; sem `-y`/`--auto` nenhuma ferramenta e
  auto-aprovada) + cwd descartavel vazio. Nenhuma ferramenta foi usada
  (resposta textual pura).

## Contencao verificada

- Dirs descartaveis: verificacao pos-corrida registrada em
  `dir_descartavel_arquivos_restantes` (vazio nas execucoes novas); os 3
  dirs da 1a rodada foram verificados vazios por inspecao direta.
- Google e Grok: **nenhuma chamada** — SUPERVISED por regra da missao
  (Google: OAuth pessoal nao reutilizavel em cliente nao autorizado;
  Grok: cached token, nunca `XAI_API_KEY`, UNATTENDED proibido).
- Nenhum conteudo de repositorio enviado; custo variavel incorrido: **0**.
- Prefixo de spinner (mojibake de console cp850) aparece no stdout do
  Kimi — artefato de terminal, nao conteudo do modelo.

## Conclusao

Codex, Claude e Kimi confirmam ELIGIBLE com prova real minima: canal
oficial + OAuth de assinatura + resposta `PROVIDER_OK`, sem custo variavel
e sem efeitos colaterais. Identificadores de modelo: Codex `gpt-5.6-sol`
(observado no CLI), Claude `claude-opus-5[1m]` (auto-relato), Kimi
`kimi-code/k3` (fonte CLI; auto-relato indisponivel).
