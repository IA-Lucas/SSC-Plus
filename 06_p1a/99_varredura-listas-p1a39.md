---
titulo: Varredura de listas de constante sob o criterio refinado — SSC+ P1-A.3.9
data: 2026-08-02
tipo: registro de medicao (NAO e atestado; quem corrige nao certifica)
evidencia: 06_p1a/evidencias/p1a39-varredura-listas.json
---

# Varredura de listas — cada membro, nao so o ultimo

## 0. A regua que mudou, e por que

A varredura anterior removia **um item por lista, o ultimo**, e chamava
de SOLTA a lista cuja remocao deixasse tudo verde. A correcao `[13/N]`
mediu que essa leitura e forte demais: `estados.TERMINAIS_WORK_UNIT`
saiu SOLTA porque seu ultimo membro (`cancelada`) nao prendia nada — mas
remover o outro membro (`concluida`) ja deixava vermelho um teste
anterior aquela missao.

O criterio refinado, gravado no `CLAUDE.md`:

> *"Remover o ultimo item e a suite fica verde"* prova que **AQUELE
> item** nao prende, jamais que a lista esta solta.

Classificacao, com cada membro mutado **isoladamente**:

| classe | definicao |
|---|---|
| **PRESA** | todo membro, ao sair, deixa >= 1 teste vermelho |
| **MEIO SOLTA** | alguns prendem, outros nao |
| **SOLTA** | nenhum membro prende |

## 1. O que foi medido

**50 listas · 245 mutantes · um mutante por vez · as duas suites
inteiras a cada mutante.** Corpus: toda atribuicao de modulo com nome
MAIUSCULO cujo valor e conjunto/lista/tupla/dicionario de strings
literais com >= 2 membros, em `05_p0/ssc_p0`, `06_p1a`,
`06_p1a/preflight` e `07_p1b`. E um **superconjunto** das 24 listas
"escolhidas por carregarem politica" da varredura anterior: aqui nao se
escolheu, varreu-se.

Baseline: **P0 315/315 · P1-A 686/686**, verde. Mutacoes em clones sob
o scratchpad; a arvore viva **nunca** foi mutada.

### Saldo

| | listas | membros | nao prendem |
|---|---|---|---|
| **Total** | **50** | **245** | **81 (33%)** |
| SOLTA | **4** | | |
| MEIO SOLTA | **30** | | |
| PRESA | **16** | | |

Por camada: P0 — 9 PRESAS, 22 MEIO SOLTAS, 2 SOLTAS (42 de 141 membros
nao prendem); P1-A — 7 PRESAS, 8 MEIO SOLTAS, 1 SOLTA (37 de 102);
P1-B — 1 lista, SOLTA.

**Um terco dos membros de constante deste repositorio nao e exercido por
teste nenhum.** A leitura antiga teria devolvido "duas listas soltas".

## 2. As quatro SOLTAS

| lista | membros |
|---|---|
| `contratos.ESTADOS_ATTEMPT` | `criado`, `despachado`, `concluido`, `orfao` |
| `estados._NOMES` | `attempt`, `sessao`, `workunit` |
| `preflight_capsula._VIA_GITBASH` | `google`, `grok` |
| `preflight_atual._VIA_GITBASH` (P1-B) | `google`, `grok` |

`ESTADOS_ATTEMPT` e a mais grave das quatro: e o enum fechado do ciclo
de vida do attempt, e **nenhum** dos quatro estados e exercido de modo
que sua remocao seja notada. Um attempt em estado fora do enum, ou um
estado do enum que deixasse de existir, atravessaria as duas suites.

Os dois `_VIA_GITBASH` sao a **mesma constante duplicada em duas
camadas**, e ambas as copias saem SOLTAS. A copia da P1-B saiu MEIO
SOLTA na primeira corrida e SOLTA na corrida limpa — foi contaminacao de
instrumento, nao propriedade (§4).

## 3. As MEIO SOLTAS que importam

Nem toda MEIO SOLTA merece a mesma atencao. Estas carregam politica de
recusa, e a metade solta e a metade que decide:

| lista | nao prendem |
|---|---|
| `economia._FAMILIAS_PROVEDOR` (23) | **16**, entre elas `anthropic`, `openai`, `google`, `claude`, `codex`, `kimi`, `grok` |
| `adaptadores._MARCADORES_NAO_LOGADO` (7) | **6** — so `not logged` prende |
| `adaptadores._MARCADORES_NEGACAO` (6) | **4** — so `no ` e `not ` prendem |
| `adaptadores._MARCADORES_QUOTA_ESGOTADA` (6) | **3**, entre elas `0 remaining` |
| `contratos.AUTH_MODES` (6) | `acp`, `local` |
| `contratos.QUOTA_STATES` (4) | `limitada`, `desconhecida` |
| `contratos.AUTOMATION_PERMISSIONS` (4) | **`deny`** |

`AUTH_MODES` merece nota: a correcao `[13/N]` prendeu `desconhecido`,
o membro que a varredura antiga havia medido — e **so ele**. `acp` e
`local` continuam sem exercicio. E a demonstracao pratica do refinamento:
prender o membro medido nao prende a lista.

`AUTOMATION_PERMISSIONS` sem `deny` e o caso mais desconfortavel: o
valor que NEGA automacao pode sair do enum fechado sem um vermelho.

## 4. ACHADO NO INSTRUMENTO, medido e corrigido antes de reportar

A primeira corrida completa **foi descartada**. Sobras de
`05_p0/saidas/labs` acumuladas dentro de cada clone ao longo das
corridas faziam `ZeroPiiNasTresRaizes` acusar o nome do usuario local
nos caminhos dos labs — vermelho que **nao vinha do mutante**.

O erro soma na direcao perigosa: transforma *nao prende* em *prende*, ou
seja, faz lista solta passar por presa. Medido, comparando as duas
corridas: **10 membros mudaram de veredito** e **2 listas mudaram de
classe** (`_AUTH_CONHECIDAS` PRESA -> MEIO SOLTA; `_VIA_GITBASH` da P1-B
MEIO SOLTA -> SOLTA).

O instrumento passou a limpar `labs` antes de cada corrida e a rodar um
**baseline de saida por clone**: ao fim, os seis clones voltaram
315/315 e 686/686. A primeira corrida nao tinha essa prova, e e por isso
que a contaminacao passou despercebida.

## 5. ACHADO NO ACERVO — o controle positivo de P1A-13 e corpus derivado

`test_config_real_p1a39.py:197` — `test_host_payg_plantado_em_cada_
grafia_e_acusado` — itera `_CHAVES_ENDPOINT` para provar
`_CHAVES_ENDPOINT`:

    for grafia in sorted(_CHAVES_ENDPOINT):

Remover uma grafia encolhe o laco junto, e o teste segue verde. E a
familia do MAJOR #3, na correcao `[9/N]` **desta mesma missao** — a
mesma forma que o docstring de `[13/N]` declara ter encontrado e
desfeito na sua propria primeira versao.

A consequencia foi medida, e nao suposta: das onze grafias, **`base_url`
e `baseurl` nao prendem nada**. As outras nove sao presas por um teste
ANTERIOR e autoral (`test_estabilizacao_p1a1.test_grafias_de_endpoint_
recebem_o_mesmo_tratamento`, corpus em maiusculas), que nao as inclui.

`base_url` e justamente a grafia que a missao `[9/N]` foi investigar e a
unica que **existe de verdade nesta estacao** —
`~/.kimi-code/config.toml` carrega tres. O guarda que a auditaria e o
unico sem exercicio.

**Nao corrigido aqui**, por dois motivos: quem corrige nao certifica, e
o remedio (corpus autoral independente para as onze grafias) e correcao
nova, com regra de prova propria — nao apendice de um registro.

## 6. Classificacao por familia

Obrigatoria neste repositorio. Registrada, e ela **NAO afere o criterio
de parada**: isto e registro de medicao da propria sessao que corrige,
nao revisao independente.

| # | achado | familia |
|---|---|---|
| 1 | controle positivo de P1A-13 itera a lista que protege (§5) | **(F)** |
| 2 | 4 listas SOLTAS; 81 de 245 membros sem exercicio (§2, §1) | **(N)** — o eixo da varredura de 86 guardas era alcance de linha; nao podia ver isto |
| 3 | `_VIA_GITBASH` duplicada em duas camadas, ambas soltas (§2) | **(N)** |
| 4 | contaminacao do instrumento por sobra de `labs` (§4) | **fora de ambas** — defeito do instrumento de medicao, nao guarda do acervo |

## 7. O QUE ESTA MEDICAO NAO ESTABELECE

- **Nao afirma que os membros sejam os CERTOS.** Mede-se exercicio,
  jamais completude da politica. Lista PRESA pode estar errada.
- **Membro que prende nao e membro bem exercido.** O criterio e "sair
  produz vermelho"; a forca da assercao ao redor nao foi olhada.
- **A mutacao e sempre REMOCAO de um membro.** ACRESCIMO nao foi medido,
  e acrescimo e a direcao em que uma allowlist se afrouxa.
- **Um membro por vez.** Remocoes simultaneas, e remocao de membro junto
  com seu consumidor, nao sao pegas.
- **O sinal "corpus encolhe com a lista" deu ZERO e isso nao e prova.**
  Ele compara o NUMERO de testes, e laco de `subTest` nao muda esse
  numero — que e exatamente a forma usada em §5. O achado de §5 saiu de
  leitura de codigo, nao do sinal. Um detector de corpus derivado que
  preste teria de ser estrutural (AST), e nao foi feito.
- **So constantes de nivel de modulo com nome MAIUSCULO e valor literal
  de strings.** Listas montadas em tempo de execucao, membros nao-string
  e constantes locais ficaram fora.
- **Nenhuma correcao foi feita.** Nem uma linha de producao mudou.
- **O instrumento nao entra no acervo**, pelo precedente da P1-A.3.8:
  `.py` novo sem teste seria mais um caso do achado C. Ele fica no
  scratchpad; a evidencia bruta das 245 medicoes esta em
  `evidencias/p1a39-varredura-listas.json`.
