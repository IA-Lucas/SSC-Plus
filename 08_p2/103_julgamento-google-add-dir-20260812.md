# O julgamento vazio do Google, medido e fechado no mecanismo — 2026-08-12

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica. Este registro e insumo de revisao independente.

## O sintoma, como os recibos o deixaram

Dois fluxos reais de 12/08 (`fluxo-20260812T011132038677Z-recusado.json`
e `fluxo-20260812T011927316485Z-recusado.json`) morreram no julgamento:
o CLI Google devolveu JSON `status: SUCCESS` com `response` vazia, o
parser fail-closed recusou (`falha-contrato`) e o gate — corretamente —
nao fez fallback de juiz. A saida bruta nao foi persistida (redacao dos
recibos), entao a causa exigia reproducao.

## A causa raiz, encontrada por sonda real

Todos os provedores rodam com `contrato_semantico=True`: o prompt
integral vai em `contexto-ssc.txt` no diretorio descartavel, e o argv
leva so o ponteiro *"leia o arquivo"*. Ler o arquivo exige uma
ferramenta do CLI — e ai estava o defeito, dito pelo proprio `agy` no
stderr da sonda B:

> `jetski: no output produced — a tool required the "command" permission
> that headless mode cannot prompt for, so it was auto-denied.`

O modelo tentava ler o arquivo, a permissao era auto-negada em headless,
e o turno terminava `SUCCESS` sem texto. Por isso a sonda curta da
sessao anterior respondia (prompt direto, sem leitura) e o julgamento
nao (ponteiro + arquivo).

### As cinco sondas, todas com o argv de producao

| Sonda | Arranjo | Resultado |
|---|---|---|
| A | prompt direto, flags de producao | `SUCCESS`, resposta correta |
| B | ponteiro + arquivo, flags de producao | `SUCCESS`, **resposta vazia**, permissao `command` auto-negada no stderr — **o sintoma, reproduzido** |
| C | conteudo por stdin | o `agy` **nao le stdin**; rota descartada |
| D | ponteiro + arquivo + `--add-dir <descartavel>` | `SUCCESS`, **arquivo lido**, marcador devolvido |
| E | argv de producao COMPLETO (com `--mode plan`) + `--add-dir` | `SUCCESS`, arquivo lido, marcador devolvido |

## A correcao

`06_p1a/preflight/frota_real.py`, spec do google: `restricao_headless`
ganha `"--add-dir", MARCA_DESCARTAVEL` — o mecanismo de marcador ja
existia e troca pelo descartavel da invocacao. **Nao amplia alcance**: e
o mesmo diretorio que ja e `cwd` do processo filho; `--sandbox`
permanece; `--dangerously-skip-permissions` nao foi usado nem sera.

Guarda novo em `test_p2_provedor_real_p2.py`
(`test_google_workspace_cobre_o_descartavel_com_add_dir`): exerce
`invocar()` com sensor que confere, no instante da chamada, que o
`--add-dir` aponta exatamente para o descartavel onde `contexto-ssc.txt`
esta.

**Reversao vermelha, medida em clone descartavel** (arvore viva nunca
mutada): removido o `--add-dir` do spec → **1 failed**; restaurado →
52 passed, 29 subtests.

## Achado lateral, declarado para revisao — `--mode plan` e INERTE

O stderr das sondas A/B/E avisa, literal:

> `warning: --mode plan has no effect while slash command expansion is
> disabled.`

A restricao declarada do google e `plan+sandbox`, mas o proprio
`--disable-slash-commands` da mesma lista **desliga o efeito do plan**.
A contencao efetiva hoje e sandbox + permissao (que este proprio caso
mediu ativa). Classificacao proposta: **(F)** — a lista de flags afirma
uma contencao que o CLI nao exerce. Nao removi a flag nem mudei a
politica: qual contencao o julgamento deve ter e decisao de quem
ratificou a restricao, nao de missao de correcao.

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, declarado por descricao —
os guardas `ZeroPii` reprovam o literal).

## O que fica aberto

- a prova operacional de ponta a ponta (fluxo real `analisar` com
  julgamento nao-vazio) e registrada em recibo proprio quando concluir;
  este registro nao a antecipa;
- modelo fixado nas sondas: `gemini-3.1-pro-high`, o mesmo dos recibos
  recusados; outros modelos nao foram sondados;
- o custo das sondas saiu da quota da assinatura Google (5 turnos
  curtos, ~90k tokens de entrada somados, ~21k no maior), medido nos
  JSONs de `usage` — as sondas vivem no scratchpad da sessao e nao foram
  versionadas; os numeros acima sao a transcricao do que elas mediram.
