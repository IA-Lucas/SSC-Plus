---
id: SSC-P1B-DIAG-00
titulo: Diagnostico da parada da frota real — classificacao dos cinco provedores
tipo: diagnostico-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-01
---

# Diagnostico da PARADA da frota real — SSC+ P1-B.00

> Missao de **diagnostico**. Nada foi corrigido: nem provedor, nem
> credencial, nem codigo, nem politica. Nenhum provider foi invocado —
> **zero sonda de CLI, zero chamada de modelo, custo variavel zero**. A
> P1-B nao foi executada e a P2 nao foi iniciada. Este documento nao
> emenda nem edita nenhum registro historico: a
> `07_p1b/01_parada-preflight.md` permanece intacta, inclusive seu
> veredito **BLOCKED**.
>
> Escritor unico `p1b00-ops`, fence **1**, adquirido **antes** da
> primeira escrita. Nome proprio desta missao — nao reusa `.lease` nem
> `.fence` de missao anterior.

## 0. Estado medido na abertura

| Item | Medido |
|---|---|
| HEAD | `52f767d` (emenda do ACHADO 6, 31/07 22:33) |
| Arvore | limpa (`git status --porcelain` vazio) |
| Tag / remoto | nenhuma / nenhum |
| P0 | **100/100 OK** (`python -m unittest discover -s 05_p0/tests`) |
| P1-A | **346/346 OK** (`python -m unittest discover -s 06_p1a/tests`) |
| Prova central | **18 assercoes, 20 eventos, OK** (`python 05_p0/cenarios/prova_central.py`) |
| Sessao de escrita viva | **nenhuma** — zero processos `renovador_lock.py`; os **11** leases de `locks/` com PID titular **morto**, verificado um a um |
| Instante das medicoes de ambiente | **2026-08-01T10:43:21Z** |

Os numeros acima sao **medidos**, nunca esperados. Registro honesto: os
346 da P1-A divergem dos **342** citados na `99_decisao-p1a33.md` §5 —
a suite cresceu entre aquela missao e esta; o numero que vale e o
medido agora.

Nenhuma copia datada irma foi criada: pratica encerrada por ordem do
Fundador (31/07). Escritor unico confirmado **por ordem do Fundador**
antes da aquisicao, como manda a condicao operativa vigente do ACHADO 4
(`06_p1a/99_achados-governanca-20260731.md` §7) — o mecanismo nao exclui
entre missoes.

## 1. Os cinco provedores — classe unica, evidencia apontavel

**Instrumento.** O pipeline ratificado (`06_p1a/preflight/pipeline.py`)
foi executado contra o ambiente real de agora com um **sensor-sentinela**
que **levanta excecao se for chamado**. Assim mede-se, sem tocar em
nenhum CLI, se o pipeline chega a sondar. Resultado: **SONDAS = 0 nos
cinco**. O `BLOCKED` e decidido antes de qualquer contato.

| Provedor | Classe unica | Evidencia apontavel |
|---|---|---|
| **codex** | **Contencao do proprio laboratorio** | `evidencias/preflight-20260730T163152Z.json:29-36` (`P1A-PAYG-ENV`, alvo `NVIDIA_API_KEY`); caminho de decisao `pipeline.py:138-140` (`bloqueio_imediato` retorna BLOCKED **antes** de construir o adaptador); regra `economia.py:53` (`nvidia` em `_FAMILIAS_PROVEDOR`) + `economia.py:223-237` |
| **claude** | **Contencao do proprio laboratorio** | `…163152Z.json:47-54`; mesmo caminho `pipeline.py:138-140`; mesma regra `economia.py:53` |
| **kimi** | **Contencao do proprio laboratorio** | `…163152Z.json:65-72`; idem |
| **google** | **Contencao do proprio laboratorio** | `…163152Z.json:83-90`; idem — e note-se que google sequer teria sonda: `frota_real.py:140` (`sondas_automaticas=False`) |
| **grok** | **Contencao do proprio laboratorio** | `…163152Z.json:101-108`; idem — `frota_real.py:161` (`sondas_automaticas=False`) |

**Por que a classe e a mesma nos cinco, e nao uma coincidencia.**
`NVIDIA_API_KEY` nao pertence a nenhum dos cinco: nao consta de
`chaves_payg_relacionadas` de provedor nenhum (`frota_real.py:69`,
`:89-90`, `:115`, `:131`, `:153`). Por isso ela cai em `env_outras`
(`pipeline.py:126-127`) para **todos**, e `env_outras` alimenta
`bloqueio_imediato` (`pipeline.py:138`). Medido, por provedor, no
ambiente real de agora:

```
codex   sondas_automaticas=True  teto=ELIGIBLE   relacionadas=[] outras=['NVIDIA_API_KEY']
claude  sondas_automaticas=True  teto=SUPERVISED relacionadas=[] outras=['NVIDIA_API_KEY']
kimi    sondas_automaticas=True  teto=ELIGIBLE   relacionadas=[] outras=['NVIDIA_API_KEY']
google  sondas_automaticas=False teto=SUPERVISED relacionadas=[] outras=['NVIDIA_API_KEY']
grok    sondas_automaticas=False teto=SUPERVISED relacionadas=[] outras=['NVIDIA_API_KEY']
```

**A variavel continua presente e persistente.** Medido em
`HKCU\Environment`: `NVIDIA_API_KEY` consta entre os nomes. **Somente o
nome foi lido; o valor nunca foi acessado, exibido nem gravado.**

### 1.1 As outras quatro classes estao VAZIAS — e nao por descuido

| Classe | Provedores | Por que |
|---|---|---|
| Credencial ausente ou invalida | **nenhum** | ver §5.1 — o campo `origem_credencial: "ausente"` da evidencia e **valor-padrao de dataclass**, nao observacao |
| Tier nao declarado ou declaracao expirada | **nenhum** | o portao de plano (`pipeline.py:195-241`) fica **atras** do bloqueio; nunca foi alcancado. O estado das declaracoes esta medido em §5.2, mas **nao e a causa da parada** |
| Quota esgotada no ciclo | **nenhum** | `quota` no relatorio e `"desconhecida"` — tambem valor-padrao (`pipeline.py:46`); nenhuma franquia foi consultada em provedor nenhum |
| Defeito de codigo no preflight | **nenhum** | a regra que bloqueia foi **deliberada e ratificada** (decisao D-2 da P1-A.1, `06_p1a/04_suite-preflight-e-correcoes.md` §2.2) — codigo fazendo exatamente o que foi mandado fazer nao e defeito. Os defeitos reais medidos estao na §5 e **nenhum deles produz o BLOCKED** |

## 2. O que destrava — proprietario x codigo

Ha **uma** classe instanciada, logo **um** destrave necessario. Ele e
integralmente do proprietario.

### 2.1 Classe "contencao do proprio laboratorio" (os cinco)

| Natureza | Acao |
|---|---|
| **Decisao/acao do proprietario** | (a) remover `NVIDIA_API_KEY` de `HKCU\Environment` — ou ao menos da sessao que roda o preflight; **ou** (b) emendar por rito a regra economica ratificada, tirando `nvidia` do escopo de **bloqueio** e mantendo-o no de **sanitizacao**; **ou** (c) declarar STOP da linha P1-B. As tres sao atos do Soberano. |
| **Trabalho de codigo** | **NENHUM para esta classe.** O caminho (b) exigiria alterar `economia.py:53` + regressao + revisao, mas isso e consequencia da decisao, nao pre-requisito dela. |

**A ambiguidade de governanca segue de pe** e nao foi resolvida aqui:
a auditoria humana da P1-A (`06_p1a/02_auditoria-economica.md` §1) julga
`NVIDIA_API_KEY` "fora da frota — ela apenas nao entra no processo"; o
pipeline codificado da P1-A.1 a trata como familia de provedor no escopo
de bloqueio. Os dois artefatos sao ratificados e divergem no efeito.
Resolver isso e ato do Soberano, nao do orquestrador — exatamente como a
`01_parada-preflight.md` §3 ja registrava.

### 2.2 Trabalho de codigo que existe, mas destrava OUTRA coisa

Os defeitos da §5 **nao** destravam a parada. Destravam o que vem
**depois** dela: sem eles corrigidos, um preflight com o ambiente limpo
produziria relatorio enganoso (§5.1), trilha sombra inalcancavel (§5.3)
e sumario incompleto (§4). Registrar isso como "o que destrava a parada"
seria falso.

## 3. Falha do provedor x recusa do laboratorio — declarado por provedor

A distincao nao pode ficar implicita, e a medicao a fecha:

| Provedor | Provedor esta bloqueado? | O que ocorreu |
|---|---|---|
| codex | **Nao se sabe — e nao foi por ele** | o SSC+ nao o alcancou: 0 sondas |
| claude | **Nao se sabe — e nao foi por ele** | idem |
| kimi | **Nao se sabe — e nao foi por ele** | idem |
| google | **Nao se sabe — e nao foi por ele** | idem |
| grok | **Nao se sabe — e nao foi por ele** | idem |

**Nos cinco casos a recusa e do laboratorio.** A prova nao e leitura de
codigo: e o sensor-sentinela, que levantaria excecao ao primeiro contato
e **nao levantou em nenhum dos cinco**. Nenhum byte saiu em direcao a
provedor nenhum. Dizer "os cinco provedores estao bloqueados" inverte o
sujeito da frase — **o SSC+ e que nao os alcanca**.

Contraprova medida, para que a afirmacao nao dependa de uma corrida so.
Com o mesmo pipeline e o mesmo sentinela, sobre um ambiente hipotetico
identico exceto pela ausencia de `NVIDIA_API_KEY` (**nao-oficial**,
nao classifica nada):

```
codex   -> o pipeline TENTOU sondar <USUARIO>/AppData/Local/Programs/OpenAI/Codex/bin/codex.exe --version
claude  -> o pipeline TENTOU sondar <USUARIO>/.local/bin/claude --version
kimi    -> o pipeline TENTOU sondar <USUARIO>/.kimi-code/bin/kimi --version
google  SUPERVISED  SONDAS=0  erros=-
grok    SUPERVISED  SONDAS=0  erros=-
```

Tres consequencias, todas medidas:

1. **A variavel e a unica coisa entre o pipeline e os CLIs** para codex,
   claude e kimi. Removida ela, o proximo passo e contato real — e so
   entao havera evidencia sobre credencial, tier ou quota.
2. **google e grok nunca dependeram de provedor algum.** Com o ambiente
   limpo eles saem **SUPERVISED com zero sondas** (`pipeline.py:147-154`,
   `frota_real.py:140` e `:161`). O `BLOCKED` deles e **100% recusa do
   laboratorio**, sem sequer a possibilidade de ser outra coisa.
3. **Os defeitos latentes F-1 e F-2 da `01_parada-preflight.md` §5 nao
   estao mais de pe.** Medido no codigo de hoje: `adaptadores.py:353-360`
   expande o `~` do executavel (F-1 corrigido em `c4fa5a0`, 30/07 18:27,
   **depois** da corrida de 16:31) e `adaptadores.py:192-208` avalia o
   login do codex sobre stdout **e** stderr combinados (F-2, mesmo
   commit, reforcado em `677c585`). A saida acima confirma F-1 na
   pratica: o caminho sondado sai **expandido**. A §5 daquele registro
   descrevia o codigo de 30/07 e continua verdadeira **para aquela data**
   — nao e emendada aqui, e situada.

## 4. O achado de `07_p1b/preflight_atual.py:172` — INDEPENDENTE

**Medido, nao presumido.** O achado (aberto na P1-A.3.2,
`99_decisao-p1a32.md` §5.3) e:

```
07_p1b/preflight_atual.py:171-172
    elegiveis = [r["provider_id"] for r in relatorios
                 if r["resultado"] == "ELIGIBLE"]
```

| Pergunta | Resposta medida |
|---|---|
| E **causa** da parada? | **Nao.** Ele roda em `main()` **depois** de `relatorios` estar pronto (`preflight_atual.py:132-137` monta; `:171` le). A classificacao BLOCKED e produzida em `pipeline.py:138-140`, noutro modulo, antes de `main()` sequer imprimir. |
| E **consequencia** da parada? | **Nao.** A linha existe desde a criacao do runner (30/07 13:31), anterior a corrida oficial de 16:31; nao foi introduzida por ela nem alterada por ela. |
| Entao? | **INDEPENDENTE.** Nao contribuiu para o BLOCKED e nao foi produzido por ele. |

**Mas nao e inofensivo, e o diagnostico o mede.** O filtro aceita
**somente** `"ELIGIBLE"`. Os outros tres resultados do enum
(`pipeline.py:31`) — `SHADOW_ELIGIBLE`, `SUPERVISED`, `BLOCKED` — caem
fora. Consequencia concreta e verificavel: no cenario da §3 com ambiente
limpo, google e grok saem **SUPERVISED**, e ainda assim a ultima linha
impressa pelo runner seria `ELIGIBLE: []` — indistinguivel de "nenhum
provedor passou". **O achado nao causou esta parada; ele deturparia o
relato da proxima corrida verde.**

Continua **NAO corrigido**, por ordem da missao. Fica registrado com dono
e gatilho, sem gerar missao propria:

| Campo | Valor |
|---|---|
| **Dono** | a missao que reabrir a P1-B |
| **Gatilho** | primeira corrida do `preflight_atual.py` com o ambiente destravado |
| **Gera missao propria?** | **Nao** |

## 5. Defeitos medidos nesta sessao — nenhum e causa da parada

Registrados porque foram **medidos**, e porque cada um deturparia a
leitura da proxima corrida. Nenhum foi corrigido.

### 5.1 O relatorio afirma "credencial ausente" sem ter olhado

`pipeline.py:138-140` retorna `relatorio("BLOCKED", …)` **sem** informar
`origem_credencial`. O campo cai no valor-padrao da dataclass,
`origem_credencial: str = "ausente"` (`pipeline.py:45`). Resultado: a
evidencia oficial diz `"origem_credencial": "ausente"` para os **cinco**
(`…163152Z.json:26`, `:44`, `:62`, `:80`, `:98`) — e nenhuma credencial
foi consultada. O mesmo vale para `"quota": "desconhecida"`
(`pipeline.py:46`) e `"versao": null`.

**A classe do defeito ja e conhecida do acervo e ja foi corrigida no
caminho vizinho.** O caminho de zero-sondas de google/grok grava
explicitamente `origem_credencial="nao-sondada"` (`pipeline.py:150-154`),
com o comentario *"com zero sondas, plano e origem declarados NAO podem
parecer prova de login no relatorio"* — revisao P1-A.3. O caminho de
bloqueio imediato **nao recebeu a mesma correcao**.

**Consequencia direta para esta missao:** um leitor que classificasse os
cinco provedores a partir do arquivo de evidencia poria todos em
"credencial ausente ou invalida". Estaria errado, e o arquivo teria
induzido o erro. E precisamente a "inferencia plausivel" que esta missao
proibe — e a razao de a §1.1 declarar aquela classe **vazia**.

### 5.2 As declaracoes de tier estao expiradas — e isso e ortogonal

Medido em 2026-08-01T10:43:21Z contra `06_p1a/tiers_declarados.json`:

| Provedor | Tier declarado | Declarado em | Expira | Valida agora |
|---|---|---|---|---|
| codex | `ChatGPT Pro 5x` | 2026-07-31T01:31:00Z | 2026-08-01T01:31:00Z | **Nao** |
| kimi | `Allegretto` | 2026-07-31T01:31:00Z | 2026-08-01T01:31:00Z | **Nao** |
| claude / google / grok | — | — | — | nunca declarado |

As duas venceram pela janela maxima de 24 h (`sombra.py:23`). **Isto nao
e a causa da parada** e por isso a classe "tier expirado" fica vazia na
§1: as declaracoes so seriam consultadas em `pipeline.py:215`, muito
depois do ponto onde o BLOCKED e decidido — e, alem disso, elas foram
criadas em 31/07 01:31, **depois** da corrida oficial de 30/07 16:31.
Para claude, google e grok a trilha sombra e inaplicavel por desenho: ela
so promove `ELIGIBLE -> SHADOW_ELIGIBLE` (`pipeline.py:296`), e os tres
tem teto `SUPERVISED`.

Renovar a declaracao e **acao do proprietario**, nao trabalho de codigo —
e so faz diferenca depois de a contencao da §2.1 cair.

### 5.3 O runner da P1-B nunca carrega as declaracoes

Medido por contagem no fonte de `07_p1b/preflight_atual.py`:
**0 ocorrencias** de `tiers_declarados` e **0** de `carregar_declaracoes`.
A chamada em `preflight_atual.py:133-136` passa `sensores`, `env` e
`config_persistida`, e **omite** `tiers_declarados` — que entao vale
`None` (`pipeline.py:97`).

Efeito: mesmo com declaracao **valida**, codex e kimi receberiam
`P1A-PLANO-DESCONHECIDO` com o detalhe *"plano nao observavel no CLI e
sem declaracao de tier do proprietario"* (`pipeline.py:225-228`) — a
trilha `SHADOW_ELIGIBLE` inteira, ratificada na emenda P1-A.3 item 1, e
**inalcancavel a partir deste runner**. Confirmado na corrida (C) do
sentinela: carregar as declaracoes e passa-las nao muda nada enquanto o
bloqueio de ambiente estiver de pe, e o runner nem as carrega.

**Trabalho de codigo**, nao acao do proprietario. **Nao corrigido** —
esta missao nao corrige codigo. Dono: a missao que reabrir a P1-B.
Gatilho: mesma corrida da §4.

### 5.4 O ACHADO 4.1 se reproduziu nesta sessao, ao vivo

Nao e achado novo — e a confirmacao medida do corolario ja registrado
(`99_achados-governanca-20260731.md` §4.1): a suite P1-A adquire o
escritor sobre o `locks/` **real** do repositorio
(`test_estabilizacao_p1a1.py:358-360`), nao um `tmpdir`.

| Hora local | Fato medido |
|---|---|
| 23:45:17 | a corrida da suite P1-A desta sessao gravou `locks/p1-ops.lease` e levou `p1-ops.fence` a **66** |
| 23:46:25 | `p1-ops` lido como **nao vencido** (faltavam 845 s) com PID titular **morto** |

O artefato falso-positivo foi **fabricado pela propria pre-condicao**
desta missao. Nenhum lock foi removido a mao; o sinal foi derrotado pelo
protocolo, como manda o registro. **Nao corrigido** — e materia 4 da
missao de politica.

## 6. O que permanece INDETERMINADO — declarado

Nao convertido por inferencia, para nenhum provedor:

- **codex, claude, kimi** — credencial valida? plano observavel? franquia
  disponivel? **INDETERMINADO.** Zero sondas; nenhuma evidencia existe.
  O que a evidencia oficial mostra nesses campos e valor-padrao (§5.1).
- **google, grok** — idem, e por desenho permanente: `sondas_automaticas
  = False` significa que o laboratorio **nunca** produzira essa
  evidencia por conta propria, com ou sem a parada.
- **A ambiguidade de governanca da §2.1** — nao resolvida, so situada.
- **`~/.local/bin/claude` e `~/.kimi-code/bin/kimi`**: os caminhos
  declarados em `frota_real.py:82` e `:107` **nao existem como arquivo**
  na estacao; os executaveis reais carregam sufixo `.exe`. Se a resolucao
  de extensao do Windows salva a sonda mesmo assim, **nao foi medido
  aqui** — mediria invocando o CLI, e esta missao nao invoca. A
  `01_parada-preflight.md` §5 registra medicao de 30/07 em que o caminho
  expandido respondeu `rc=0`; e evidencia daquela data, nao desta.
  **INDETERMINADO.**

## 7. Alcance — o que este registro estabelece e o que NAO estabelece

**Estabelece.** Que os cinco `BLOCKED` de 30/07 tem **uma unica causa
comum**, interna ao laboratorio, e que ela continua vigente em
2026-08-01T10:43:21Z. Cada linha da §1 tem contraexemplo verificavel por
terceiro: o arquivo de evidencia, a linha da regra, a linha do pipeline e
o sensor-sentinela que nao disparou.

**Nao estabelece.** Nao afirma que provedor algum esteja funcional,
degradado ou bloqueado — nao foram consultados. Nao converte nenhum
INDETERMINADO. Nao reabre o veredito **BLOCKED** da
`01_parada-preflight.md`, que segue de pe pelas mesmas razoes que a
originaram. Nao classifica MAJOR: quem classifica e revisor. Nao afirma
que o achado da §4 seja inofensivo — afirma que e independente **desta**
parada.

**Nao alterado.** Zero linha de codigo, teste, politica, evidencia ou
relatorio historico. O unico caminho novo e este documento.

## 8. Decisao

**BLOCKED** — mantido, agora com a causa isolada e nomeada. A parada
**nao** e falha de provedor: e recusa do proprio laboratorio, medida com
zero contato externo. O destrave e **integralmente decisao do
proprietario** (§2.1); nenhum trabalho de codigo e pre-requisito dele.
