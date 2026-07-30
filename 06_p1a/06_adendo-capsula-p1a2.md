---
id: SSC-P1A2-ADENDO
titulo: Adendo experimental SSC+ P1-A.2 — capsula subscription-only e politica estrita
tipo: adendo-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Adendo P1-A.2 — capsula subscription-only e politica estrita

> Documento ADITIVO. Nenhum relatorio historico foi reescrito: a auditoria
> economica da P1-A (`02_auditoria-economica.md`) e a decisao P1-A
> (`99_decisao-p1a.md`) permanecem como foram escritas. Este adendo
> registra a decisao do Soberano que SUPERA, para o trabalho futuro, uma
> leitura anterior — sem apagar o registro dela.

## 1. Decisao do Soberano (2026-07-30)

1. `NVIDIA_API_KEY` global/HKCU **nao e removida, alterada ou persistida**
   pelo SSC+ — ela pertence a outros projetos do usuario na estacao.
2. O SSC+ inicia dentro de uma **capsula subscription-only**: ambiente-
   filho derivado, sem nenhuma credencial de modelo, gerado ANTES de
   carregar o SSC+ (`06_p1a/capsula.py`, argv em lista, `shell=False`).
3. **Politica estrita dentro da capsula**: qualquer `*_API_KEY`,
   `*_AUTH_TOKEN`, `*_ACCESS_TOKEN`, `*_API_SECRET`, `*_SECRET_KEY` (e
   variantes de caixa/separador, e as chaves conhecidas de
   `economia.CHAVES_PAYG_CONHECIDAS`) visivel dentro da capsula =
   **bloqueio**. Isso inclui `NVIDIA_API_KEY` injetada na capsula, mesmo
   sem provider NVIDIA na frota.
4. A auditoria economica segue fail-closed: chave, endpoint PAYG,
   top-up, extra-usage, billing ou canal desconhecido = BLOCKED.

## 2. O que este adendo supera (sem reescrever)

A leitura manual da P1-A — "`NVIDIA_API_KEY` fora da frota; nenhuma acao
sobre a variavel global — ela apenas nao entra no processo"
(`02_auditoria-economica.md` §1) — classificou a frota ELIGIBLE com a
variavel presente no ambiente. O pipeline codificado da P1-A.1 ja a
tratava como violacao de bloqueio (`04_suite-preflight-e-correcoes.md`
§2.2: "`NVIDIA_API_KEY` (...) continua violacao economica e continua
sanitizada"), divergencia que so apareceu quando o pipeline foi executado
contra o ambiente real (parada P1-B-01, `07_p1b/01_parada-preflight.md`).

A partir deste adendo, a leitura operativa e a **politica estrita**: a
presenca de credencial de provedor de modelo no ambiente DE EXECUCAO do
SSC+ bloqueia; a capsula e o mecanismo que torna as duas exigencias
compativeis — o usuario mantem suas credenciais globais, e o SSC+ opera
num ambiente-filho onde nenhuma existe.

## 3. Defesa em profundidade

| Camada | Mecanismo | Efeito |
|---|---|---|
| 1. Borda | `capsula.ambiente_capsula` / `iniciar_em_capsula` | o processo SSC+ nasce sem nenhuma credencial de modelo; global intocado |
| 2. Guarda de entrada | `capsula.exigir_capsula_limpa` | qualquer credencial visivel no processo aborta ANTES de sonda/escrita |
| 3. Auditoria | `economia.auditar_ambiente` | credencial de provedor (incl. NVIDIA injetada) = P1A-PAYG-ENV, BLOCKED pre-sonda |
| 4. Subprocessos | `sensor_subprocess` + `ambiente_sanitizado` | toda sonda recebe NOVA copia sanitizada do env da capsula |

## 4. Correcoes F-1/F-2 (defeitos revelados pela parada P1-B-01)

- **F-1** — `AdaptadorPreflight._argv` expande SOMENTE o `~` do
  executavel (`os.path.expanduser`): sem expandvars, sem shell, sem
  hardcode de usuario; argumentos preservados em lista (espacos e
  metacaracteres literais); caminho inexistente -> `CliIndisponivel`.
  Causa raiz do falso `P1A-CLI-INDISPONIVEL` de claude/kimi na P1-B-01.
- **F-2** — `_login_codex` avalia stdout E stderr combinados em memoria
  (`codex login status` imprime "Logged in using ChatGPT" em stderr).
  rc != 0 ou marcador negativo vence sempre; conflito entre canais
  resulta desconhecido/BLOCKED, nunca login por inferencia. Saida bruta
  nunca persistida (somente logado/plano/origem/quota parseados).

Regressoes: `06_p1a/tests/test_capsula_p1a2.py` (27 testes: capsula,
injecao NVIDIA pre-sonda nos 5, F-1 com til/expandvars/metacaracteres/
inexistente, F-2 com stdout/stderr/ambos/rc/negacao/conflito/quota,
zero segredo em erro/excecao).

## 5. Limites desta decisao

- Autorizacao **somente experimental**: nada aqui promove codigo ou
  politica ao canonico LucaX Enterprise OS.
- A capsula protege o processo SSC+ e seus filhos; ela NAO audita nem
  altera o restante da estacao do usuario.
- `NVIDIA_API_KEY` permanece presente e intacta no ambiente global —
  verificado por existencia (nome/tipo/tamanho), nunca por valor.
