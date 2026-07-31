---
id: SSC-P1A3-ADENDO
titulo: Adendo experimental SSC+ P1-A.3 — emendas de especificacao decididas pelo Soberano
tipo: adendo-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-31
---

# Adendo P1-A.3 — emendas de especificacao (trilha SHADOW_ELIGIBLE)

> Documento ADITIVO. Nenhum relatorio historico foi reescrito: a decisao
> P1-A.2 (`99_decisao-p1a2.md`, ADJUST) permanece como foi escrita — este
> adendo registra a decisao do Soberano sobre as emendas la propostas (§6)
> e o seu efeito na especificacao operativa do preflight.

## 1. Decisao do Soberano (2026-07-31)

1. **APROVADA COM LIMITES** — tier declarado pelo proprietario + OAuth
   observado habilita **SOMENTE `SHADOW_ELIGIBLE`**, com validade maxima
   de **24 horas**. **Nao autoriza P2 nem execucao autonoma.**
2. **APROVADA** — `codex doctor` comprova o modelo efetivo atual e o modo
   de autenticacao, **sem equivaler a catalogo completo**.
3. **PARCIALMENTE APROVADA** — `kimi provider list` comprova OAuth e
   modelo efetivo, mas **nao o plano comercial**.
4. **NAO APROVADA POR DECLARACAO** — claude permanece **SUPERVISED**
   enquanto nao houver modelo exato observado por fonte oficial nao
   interativa. **O plano Max, isoladamente, nao basta.**
5. Google e Grok permanecem **SUPERVISED**, com **zero sondas
   automaticas**.
6. A capsula subscription-only, a politica NVIDIA e os bloqueios PAYG
   permanecem **inalterados**.
7. A revisao ocorre apos os testes offline e antes do preflight final,
   por **dois providers distintos**, usando somente assinaturas e
   nenhuma API paga.

## 2. Efeito na especificacao operativa

| Emenda | Implementacao |
|---|---|
| 1 | Novo resultado `SHADOW_ELIGIBLE` no enum do pipeline; `preflight/sombra.py` valida a declaracao do proprietario (`06_p1a/tiers_declarados.json`) com janela efetiva **nunca superior a 24 h** (fail-closed: ilegivel, futura ou expirada = `P1A-DECLARACAO-EXPIRADA`); sem declaracao, o bloqueio estatico original (`P1A-PLANO-DESCONHECIDO`) permanece |
| 2 | Descoberta codex: `comandos["modelos"] = ("doctor",)` com parser dedicado (`_modelos_codex_doctor`) — modelo efetivo + `auth mode chatgpt` exigidos; qualquer ausencia = fail-closed (`P1A-MODELO-REMOVIDO`) |
| 3 | Kimi sem plano observavel cai na trilha sombra do item 1 (OAuth + `Default model` via `provider list` + tier declarado) |
| 4 | Claude: `teto_resultado = "SUPERVISED"`, `automacao = "supervised-only"`, `comandos["modelos"] = None` (descoberta desativada — zero sondas de modelos) |
| 5 | Google/Grok: `sondas_automaticas = False` na especificacao — ZERO sondas (nem versao/login/modelos) e invariante do pipeline, nao convencao do runner |
| 6 | Nenhuma alteracao em `capsula.py` nem nas auditorias de `economia.py` (somente o novo erro tipado `DeclaracaoExpirada`, aditivo) |

## 3. Limites desta decisao

- `SHADOW_ELIGIBLE` **nao e** `ELIGIBLE`: nao habilita P2, nao habilita
  execucao autonoma, nao sobe o teto de nenhum provider SUPERVISED. E
  somente observacao-sombra de diagnostico, valida por no maximo 24 h
  por declaracao.
- A declaracao de tier e um **ato humano registrado** — nunca inferida
  pelo codigo. Expirada, exige renovacao humana.
- Claude so sai de SUPERVISED quando houver modelo exato observado por
  fonte oficial **nao interativa** — nova evidencia, nova decisao.
- Autorizacao **somente experimental**: nada aqui promove codigo ou
  politica ao canonico LucaX Enterprise OS.

## 4. Regressoes

`06_p1a/tests/test_emendas_p1a3.py` — 69 testes, cobrindo toda a
superficie das emendas e dos achados das revisoes (trilha sombra
completa; doctor com auth conflitante e linhas espurias; kimi com
marcadores duplos NA MESMA LINHA e modelo conflitante; zero sondas
google/grok; declaracoes invalidas em todos os eixos, inclusive campos
nao-texto; 7 formatos de quota esgotada; plano incidental, negado e
observado incompativel; rotulo de plano como palavra inteira;
precedencia evidencia-observada > declarada; CliIndisponivel na sonda
de login; invariante anti-P2 reforcado — nenhum consumidor generico de
elegibilidade fora do pipeline; arquivo real de declaracoes).

## 5. Achados das revisoes ja tratados neste changeset

Primeira chamada (codex): pacote com dois arquivos TRUNCADOS pela
montagem — dois CRITICALs artefatos de empacotamento; o pacote final
embute os arquivos completos. Achados legitimos tratados:

- **google/grok com sondas no pipeline** (MAJOR): `comandos["modelos"]
  = None` primeiro; depois, na rodada seguinte (MAJOR recorrente),
  `sondas_automaticas = False` na especificacao — ZERO sondas (nem
  versao/login) virou invariante do pipeline, nao convencao do runner.
- **declaracao com campos vazios** (MINOR): descartada no carregamento.
- **OverflowError em timestamp extremo** (MINOR): `expira_em` e
  `_parse_utc` devolvem None sem excecao (calendario E offset).
- **usuario local na evidencia** (varredura ZeroPii): redacao da forma
  8.3 do perfil e do JSON inteiro da evidencia.
- **caminho local em `caminho`** (MAJOR): mitigacao existente
  ratificada — caminho expandido so em memoria; persistencia redige
  `<USUARIO>`; varredura ZeroPii cobre os artefatos.

Segunda chamada (codex, pacote completo) e primeira (kimi) — tratados:

- **plano por substring** (MAJOR, kimi): "pro" casava em
  "profile"/"prompt" — bypass para ELIGIBLE pleno. `_plano_de` e
  `plano_reconhecido` passaram a exigir token com fronteira de palavra.
- **quota "no requests remaining"** (MAJOR, codex): escapava das regras
  de esgotamento e casava o sinal positivo — incluida em
  `_RX_QUOTA_ESGOTADA` (fail-open eliminado).
- **descoberta kimi se provava pelo nome do provider** (MAJOR, codex):
  parser dedicado exige a linha "Default model:" e rc==0;
  "managed:kimi-code" sozinho nao e evidencia de modelo.
- **regexes do doctor nao ancoradas** (MAJOR, codex): ancoradas no
  inicio da linha — texto incidental nao comprova auth/modelo.
- **tier declarado sem confronto com planos_aceitos** (MAJOR, codex):
  portao exige compatibilidade; "free" declarado = P1A-PLANO-DESCONHECIDO.
- **marcador "chatgpt" solto como login** (MINOR, kimi): `_login_codex`
  exige "logged in" E "chatgpt".
- **relogio naive em `declaracao_valida`** (MINOR, kimi): fail-closed.
- **invariante modelos=None ⇒ teto SUPERVISED** (MINOR, kimi): virou
  assercao de teste.

Terceira chamada (codex) e segunda (kimi) — tratados:

- **plano incidental "Upgrade to Pro"** (MAJOR, codex): tokens curtos
  (< 4 chars) so valem com rotulo de plano ("plan:", "plano=").
- **contencao reciproca de tier** (MAJOR, ambos): "chatgpt"/"5x" casavam
  por fazer parte da frase aceita — `plano_reconhecido` passou a
  comparar SOMENTE reportado ⊇ aceito.
- **"0 of 100 requests remaining"** (MAJOR, codex) e "no remaining"/
  "none left" (OBS, kimi): regexes de esgotamento ampliadas.
- **auth conflitante no doctor** (MAJOR, codex): TODAS as linhas de auth
  precisam concordar em "chatgpt"; modelo exige identificador unico com
  digito (linhas "model reasoning..." ignoradas).
- **`declarado_por` nao validado** (MAJOR, codex): somente a string
  "proprietario" habilita; `null`/outros = declaracao descartada.
- **caminho local expandido** (MAJOR, codex): a especificacao passou a
  guardar o executavel do codex em forma `~/...` (expandido so na
  sonda) — relatorios e excecoes nao carregam mais o perfil local.
- **`_host_de` devolvia URL integral malformada** (MINOR, codex):
  marcador generico `<host-ilegivel>`.
- **campos estaticos parecendo observados** (MINOR, ambos): google/grok
  saem com `plano=None` e `origem_credencial="nao-sondada"`.
- **payload `sombra` em relatorios BLOCKED/SUPERVISED** (MINOR, kimi):
  o payload so existe no resultado SHADOW_ELIGIBLE.
- **"oauth" solto no fallback do claude** (MINOR, kimi): fallback exige
  "logged in" E "oauth".

Quarta chamada (codex) e terceira (kimi) — tratados:

- **"Upgrade to ChatGPT Pro"** (MAJOR, codex): TODA evidencia de plano
  exige rotulo — tokens longos em texto corrido tambem nao comprovam.
- **`_login_kimi` com marcador unico e stderr ignorado** (MAJOR, codex):
  stdout+stderr combinados; "source=oauth" E "managed:kimi-code"
  exigidos.
- **`Default model:` sem vinculo/conflito** (MAJOR, codex): exatamente
  um valor distinto; conflito = fail-closed.
- **portao nao revalidava a declaracao** (MAJOR, codex): provider, tier
  nao vazio e declarante "proprietario" revalidados no pipeline, mesmo
  sem passar pelo loader.
- **"0 tokens available"/"no quota available"** (MAJOR, codex): regexes
  de esgotamento cobrem "available".
- **sem teste de integracao anti-P2** (MAJOR, codex): invariante
  estatico — o literal SHADOW_ELIGIBLE so tem LOGICA no pipeline;
  nenhum runner/consumidor o usa para executar.
- **plano observado incompativel caia na sombra** (MINOR, kimi):
  precedencia corrigida — "plan: team" bloqueia DIRETO, mesmo com
  declaracao valida; a sombra so existe para plano NAO observado.
- **CliIndisponivel na sonda de login propagava excecao** (MINOR,
  codex): capturada — BLOCKED tipado.
- **`descobrir_modelos` sem guarda propria** (OBS, kimi): devolve []
  sem sondar quando a especificacao desativa a descoberta.
- **REJEITADO com evidencia**: "_normalizar_sensores exige sensor de
  modelos" (MINOR, codex) — incorreto: `modelos` cai para o sensor de
  execucao via `setdefault` (teste
  `test_dict_sem_modelos_reaproveita_o_de_execucao`); nunca aborta.
- **registrado sem mudanca**: `detectar_versao` ecoa a primeira linha
  crua do CLI quando o padrao de versao nao casa (OBS, kimi) — mitigado
  pela redacao na persistencia + varredura ZeroPii; candidato a
  endurecimento futuro.

Quinta chamada (codex) e quarta (kimi) — tratados:

- **rotulo de plano sem fronteira inicial** (MAJOR): "explanation: pro"
  casava via `\w*` — rotulo agora exige palavra inteira (`\b...\b`).
- **plano negado ("not pro") reconhecido** (MAJOR): marcadores de
  negacao rejeitam o valor em `plano_reconhecido`.
- **marcadores kimi em registros distintos** (MAJOR): "source=oauth" e
  "managed:kimi-code" exigidos NA MESMA LINHA.
- **"0/100 requests remaining"** (MAJOR): formato com barra incluido
  nas regexes de esgotamento.
- **anti-P2 so procurava o literal** (MAJOR): invariante reforcado —
  nenhum consumidor generico de elegibilidade (`!= "BLOCKED"`,
  `== "ELIGIBLE"`) fora do pipeline.
- **revalidacao sem checagem de tipo** (MINOR, ambos): tier/declarante
  nao-texto = declaracao ilegitima, sem excecao (pipeline e loader).
- **`int(inf)` no loader** (MINOR, kimi): OverflowError capturado —
  estrutura inesperada = {}.
- **OBS registrados (sem mudanca)**: "resets/reset at" como sinal fraco
  de quota; token trailing no auth do doctor; tokens genericos curtos
  em `planos_aceitos` (risco aceito, fiel a especificacao);
  `detectar_versao` ecoa linha crua (mitigado por redacao + varredura).
