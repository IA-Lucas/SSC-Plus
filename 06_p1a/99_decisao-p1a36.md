---
id: SSC-DEC-P1A36
titulo: Registro e Decisao da Missao SSC+ P1-A.3.6 — revisao independente do estado corrigido
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-02
---

# Registro e Decisao — Missao SSC+ P1-A.3.6

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhuma decisao ou relatorio historico
> foi editado. Missao **probatoria** — nao alterou uma linha de codigo,
> teste ou politica. Os unicos caminhos novos sao os dois instrumentos de
> revisao, as duas evidencias das chamadas e este registro.

## DECISAO: **ADJUST**

Um revisor independente pronunciou-se e **REPROVOU**. O portao exigia
zero CRITICAL e zero MAJOR nos **dois** vereditos; o veredito obtido tem
**seis MAJOR nao fechados, seis MAJOR novos e `DEFEITO-NOVO: SIM`**, e o
segundo veredito **nao existe** — o kimi foi recusado pelo provedor por
cota de ciclo esgotada.

Achado que exija alteracao encerra em ADJUST, e **nada foi corrigido
nesta missao**, como o ato manda.

**As duas metades do portao falharam por causas independentes, e fechar
uma nao abre a outra** — a §4.1 dispoe disso formalmente, para que
"ADJUST" nao seja lido como "feche os doze MAJOR e o portao passa".

## SUMARIO — 10 linhas

1. Pacote **NOVO** sobre o HEAD atual: `5ab35a6c…`, **445.056 bytes**,
   ALVO `6a3a3f8`, BASE `30107bd`. Nao reaproveita `c17b730f` nem
   `87f41503`.
2. **Cinco geracoes, um so hash** — duas em descartaveis independentes
   (byte a byte), duas em worktrees limpas (uma delas de **outro**
   commit) e uma com a arvore **deliberadamente mutada**.
3. **codex: veredito REPROVADO**, 238,975 s, modelo `gpt-5.6-sol`,
   pacote conferido pelo proprio revisor com o hash correto.
4. **kimi: sem veredito** — `403 You've reached your usage limit for this
   billing cycle`. Terceira falha consecutiva do kimi, por causa
   **diferente** das duas anteriores.
5. Os **seis MAJOR continuam abertos**, um a um, com justificativa
   apontavel. Nenhum fechou.
6. `DEFEITO-NOVO: SIM` — o revisor apontou a assimetria de `quota` que a
   **Declaracao 3, item 1** lhe havia transmitido.
7. **Seis MAJOR novos**, entre eles o ACHADO 4 que a Declaracao 1
   transmitiu: o revisor o classificou como MAJOR por conta propria.
8. As quatro declaracoes obrigatorias foram transmitidas e **surtiram
   efeito verificavel**: tres dos achados citam explicitamente o que
   elas informaram.
9. **Achado desta missao contra o proprio instrumento**: a contencao
   acusou mutacao fora do descartavel, e a causa foi **esta sessao**, nao
   o revisor.
10. Zero linha de codigo, teste ou politica alterada. Custo variavel
    **0**; arvore limpa, sem tag e sem remoto; lease `p1a36-ops` vivo do
    inicio ao fim.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Medido |
|---|---|
| HEAD de abertura | `6a3a3f865483e488a2f230b02a32dcb224a9b076` |
| Arvore | limpa (`git status --porcelain` vazio) |
| Branch | `master` |
| Tag / remoto | nenhuma / nenhum |
| Lease desta missao | `p1a36-ops`, fence **1**, pid 136168, renovado a 30 s, adquirido **antes da primeira escrita** |
| P0 / P1-A / prova central | **100/100 · 424/424 · 18/18** (20 eventos) |

**Declaracao de tier, verificada pelo leitor da missao no instante de
cada chamada** — o portao exigido pelo ato:

| provedor | tier | declarado_por | expira em UTC | valido no instante |
|---|---|---|---|---|
| codex | `ChatGPT Pro 5x` | proprietario | 2026-08-02T23:54:41Z | **sim** |
| kimi | `Allegretto` | proprietario | 2026-08-02T23:54:41Z | **sim** |

Expirada = BLOCKED, pelo ato. **Nao expirou**: a abertura mediu
2026-08-02T00:09:17Z, dentro da janela de 24 h aberta pela P1-B.02, e as
duas evidencias registram `valido_no_instante: true` medido no momento da
respectiva chamada.

**Condicao operativa declarada** (§7 da `99_achados-governanca-20260731.md`):
enquanto o ACHADO 4 nao for corrigido, a exclusao mutua entre missoes
**nao existe**; o escritor unico desta missao e garantido **por ordem do
Fundador**, nunca pelo mecanismo. O lease `p1a36-ops` nao impediria uma
segunda sessao de outro nome de escrever ao mesmo tempo.

**Artefato gerado durante a medicao, e restaurado.** Rodar
`prova_central.py` reescreve `05_p0/saidas/prova_central.json` com UUIDs
novos a cada corrida (108 linhas trocadas, todas `attempt_id` e
`decisao_id`). O arquivo foi restaurado por `git checkout --` e a arvore
reconferida limpa **antes** da geracao do pacote. Registrado porque e
ruido conhecido de toda medicao de pre-condicao, nao achado novo.

## 2. Pacote — NOVO sobre o HEAD atual

| Item | Valor |
|---|---|
| **SHA-256** | `5ab35a6c13c67ba9f0b03893263467d0cf7afdc7565a5d1fc8e3ee6d417f96c2` |
| Bytes | **445.056** |
| Gerador | `06_p1a/evidencias/pacote_p1a36.py` (novo; instrumento desta missao) |
| ALVO | `6a3a3f8` (HEAD da P1-B.02) |
| PAI | `e33400f` |
| BASE | `30107bd` |
| Commits entre BASE e ALVO | **20** |

**Nao reaproveita `c17b730f` nem `87f41503`**, como o ato exige. Os dois
hashes vao **dentro** do pacote, declarados nao-equivalentes, para
impedir que qualquer revisor presuma continuidade.

O pacote **nao foi versionado**: ele e funcao exclusiva de commits, e as
cinco geracoes da §2.3 mostram que qualquer terceiro o reproduz byte a
byte com `python 06_p1a/evidencias/pacote_p1a36.py <saida>`. Versionar
445 KB de conteudo que ja esta no proprio repositorio nao acrescenta
verificabilidade; o hash publicado e o gerador versionado, sim.

### 2.1 Por que o BASE e `30107bd` e nao `ac03f3a`

Medido nas evidencias, nao presumido: **nenhum revisor jamais leu o
pacote `87f41503`**. O codex foi recusado por limite de uso do ciclo
(`revisao-p1a33/codex-20260731T160049Z.json`, returncode 1) e o kimi
morreu na validacao do CLI antes de qualquer chamada
(`kimi-20260731T155932Z.json`, `Cannot combine --prompt with --plan`).

O ultimo estado que um revisor de fato leu e julgou e `30107bd` — o
estado **reprovado com seis MAJOR** pela P1-A.3.1. Ancorar o diff em
`ac03f3a` esconderia dos revisores justamente as correcoes dos seis
MAJOR, que e o que eles precisam julgar. O ato manda nao reaproveitar os
pacotes anteriores; nao manda herdar o alvo de um pacote que ninguem leu.

### 2.2 Ordem, normalizacao e exclusoes — declaradas no gerador e no pacote

- **ORDEM**: secoes em sequencia fixa escrita no codigo;
  `ARQUIVOS_COMPLETOS` na ordem literal (9 modificados, depois 13 novos);
  `CONTEXTO_COMPLETO` na ordem literal; `EVIDENCIAS_HASHEADAS` em
  `sorted()`; o diff na ordem que o `git diff` produz para a lista
  literal.
- **NORMALIZACAO**: fonte unica sao os blobs em ALVO (LF por construcao);
  saida UTF-8 sem BOM; nenhuma remontagem entre revisores.
- **EXCLUSOES**, todas declaradas e **nenhuma silenciosa**:
  1. o diff cobre os **9** arquivos `.py` que **existem em BASE**. Os
     **13** `.py` **novos** nao entram no diff porque ali seriam a
     propria integra com prefixo `+`; entram por inteiro, uma vez, na
     secao de conteudo completo;
  2. registros (`.md`) e evidencias (`.json`) alterados entre BASE e
     ALVO entram **somente como SHA-256** do blob em ALVO — **16**
     entradas. O que neles e materia de julgamento esta **transcrito**
     nas Declaracoes obrigatorias, nao resumido para caber;
  3. nao entram timestamp, UUID, caminho absoluto, valor de variavel de
     ambiente, credencial, PII, lock, cache nem runtime;
  4. usuario local (forma longa e 8.3) e prefixo de caminho local sao
     redigidos.

**A exclusao 1 e conferida contra o banco de objetos, nao afirmada.** O
gerador para com PARADA se um caminho declarado modificado nao existir em
BASE, ou se um declarado novo existir — sem isso, a exclusao declarada
viraria omissao silenciosa.

**Verificacao de vazamento no pacote pronto**, medida e nao presumida:
usuario local (forma longa) **0**, forma 8.3 **0**, `E:\LucasIA` e
`E:/LucasIA` **0**, e-mail do proprietario **0**, e zero casamento para
os cinco padroes de chave de API testados (`sk-`, `gsk_`, `xai-`,
`AIza`, `ghp_`). Redacoes efetivamente aplicadas: **29** `<USUARIO>` e
**16** `<CAMINHO-LOCAL>`.

### 2.3 Prova de ancoragem — executada ANTES do envio, e PASSOU

Foi este exato defeito que reprovou a P1-A.3.1 (MAJOR #5). **Cinco
geracoes, todas identicas:**

| Geracao | Condicao | SHA-256 |
|---|---|---|
| A | arvore de trabalho intacta, descartavel proprio | `5ab35a6c…` |
| B | **segundo descartavel, independente** | `5ab35a6c…` |
| C | **worktree destacada e limpa em `6a3a3f8`** (o ALVO) | `5ab35a6c…` |
| D | **worktree destacada e limpa em `30107bd`** (checkout de OUTRO commit) | `5ab35a6c…` |
| E | arvore de trabalho **deliberadamente mutada** | `5ab35a6c…` — **inalterado** |

A e B tem **445.056 bytes** e foram comparados **byte a byte** sem
diferenca (`filecmp.cmp(..., shallow=False)`).

A geracao E mutou **dois** arquivos presentes nas listas do gerador —
`06_p1a/tiers_declarados.json` (contexto **e** hasheado) e
`07_p1b/preflight_atual.py` (diff **e** conteudo completo) — e o
`git status --porcelain` no instante da geracao confirmou a arvore suja.
O hash nao se moveu. Copia de seguranca dos dois arquivos feita **antes**
da mutacao; apos a restauracao, os SHA-256 dos dois conferem com os da
copia e a arvore voltou a limpa.

A geracao D e a mais forte: o pacote reproduz identico a partir de um
checkout de commit **diferente** do alvo — so possivel porque toda
leitura vem de `git cat-file blob <ALVO>:<path>` e nunca do disco. As
duas worktrees foram removidas e `git worktree prune` executado.

## 3. As duas chamadas — mesmos bytes, mesmo hash

Os **mesmos bytes** foram copiados para os dois descartaveis, sem
remontagem. As duas evidencias registram `pacote_sha256` identico —
`5ab35a6c…`, 445.056 bytes — e o codex **computou o hash por conta
propria** e declarou o mesmo valor.

| Campo | codex | kimi |
|---|---|---|
| Evidencia | `revisao-p1a36/codex-20260802T001922Z.json` | `revisao-p1a36/kimi-20260802T002414Z.json` |
| Canal | assinatura OAuth (ChatGPT Pro 5x) | assinatura OAuth (Allegretto) |
| Tier valido no instante | sim | sim |
| Enforcement | `--sandbox read-only --ephemeral` | restricao parcial + deteccao integral |
| Modelo efetivo observado | **`gpt-5.6-sol`** (banner do CLI) | **DESCONHECIDO** — nao exposto pelo CLI |
| returncode | **0** | 1 |
| Duracao | **238,975 s** | 6,751 s |
| Resposta produzida | **sim** | **nao** (vazia) |
| Custo variavel | 0 | 0 |
| Lease reverificado antes de persistir | sim, fence 1 | sim, fence 1 |
| Arquivos restantes no descartavel | `pacote-revisao.txt` | `pacote-revisao.txt` |
| **Veredito** | **REPROVADO** | **inexistente** |

### 3.1 kimi — cota do ciclo esgotada no provedor

```
error: failed to run prompt: provider.api_error: 403 You've reached your
usage limit for this billing cycle. Your quota will be refreshed in the
next cycle.
```

O comando montado por `argv_kimi` **rodou** — a correcao da P1-A.3.4
(remocao de `--plan`) esta comprovada por este resultado: onde a
P1-A.3.3 morria na validacao do CLI em 0,667 s, agora a chamada atravessa
o CLI, alcanca o provedor e volta com erro **de servico**, em 6,751 s.
**A causa da falha mudou; a falha permaneceu.**

As duas saidas oferecidas — **comprar uso extra** ou **subir de plano** —
estao ambas fora do alcance desta missao: a primeira e via paga,
proibida; a segunda e ato do proprietario. **Nao houve nova tentativa.**
Repetir nao mudaria o resultado: o limite e do ciclo de faturamento, nao
de uma janela de taxa, e a regra de uma chamada valida por provedor nao
autoriza tentativas em serie contra um portao comercial.

**Terceira falha consecutiva do kimi, por tres causas distintas:**
P1-A.3.1 (returncode 1, 3,844 s, causa nao caracterizada na evidencia);
P1-A.3.3 (validacao do CLI, `--plan` incompativel com `-p`); P1-A.3.6
(403 do provedor). **A revisao dupla nunca ocorreu**, e o criterio de
aceite "mesmo pacote/hash nos dois revisores" da §9 da
`99_decisao-p1a31.md` continua aberto — agora com a metade do pacote
**cumprida** (mesmos bytes e hash preparados e entregues aos dois) e a
metade do revisor **nao cumprida**.

### 3.2 codex — o veredito, integral

O texto completo esta em
`06_p1a/evidencias/revisao-p1a36/codex-20260802T001922Z.json`, campo
`resposta`. O revisor declarou escopo `pacote-revisao.txt integral
(9.519 linhas)`.

**PARTE 1 — os seis MAJOR. Nenhum fechou.**

| MAJOR | Pronunciamento | Justificativa do revisor (resumo fiel) |
|---|---|---|
| 1 | **NAO-FECHADO** | `classificar_frota` eliminou o atalho, mas `leitores_config.config_persistida` le para grok somente JSONs de topo e admite nao alcancar o SQLite observado; PAYG/auto-topup persistido nessa fonte ainda nao chega a auditoria |
| 2 | **NAO-FECHADO** | `adaptadores._ZERO` aceita somente um zero inicial; `.0 tokens available` e `00 tokens available` escapam e ainda casam `available` — fail-open mantido |
| 3 | **NAO-FECHADO** | `contencao.manifesto` cobre apenas `RAIZ` e exclui todo `locks/`; o kimi segue capaz de alterar arquivos fora do repositorio, ou locks nao verificados, sem aparecer em `mutacoes` |
| 4 | **NAO-FECHADO** | `revisao_p1a2.main` verifica o lock so antes da chamada e grava em `SAIDA` sem reverificacao com o fence original; o teste novo exercita apenas a funcao canonica, nao esse caminho de persistencia |
| 5 | **NAO-FECHADO** | a ancoragem por `git cat-file blob` esta correta e a troca do portao de HEAD e substituicao **valida**; mas o gerador **deste** pacote, que o proprio pacote manda julgar, **nao esta entre os conteudos completos** — construcao e portao ficaram inauditaveis |
| 6 | **NAO-FECHADO** | `test_emendas_p1a3` so reconhece literais exatos e aliases atribuidos no mesmo arquivo; concatenacao, constante importada (`RESULTADOS`) ou propagacao por booleano contornam `_portoes_de_execucao`, e a metade (A) segue sem cobrir `07_p1b` |

**PARTE 2 — `DEFEITO-NOVO: SIM`.** `preflight/pipeline.py`: o bloqueio
imediato passou a emitir `quota="nao-sondada"` enquanto o caminho vizinho
de zero sondas preservou `"desconhecida"`. **E exatamente a assimetria
que a Declaracao 3, item 1, lhe transmitiu** — o revisor a confirmou como
defeito introduzido, e nao como divergencia aceitavel.

**PARTE 3 — achados.** Seis MAJOR novos, tres MINOR (os tres classificados
**nao-bloqueantes**, com motivo) e um OBS. Zero CRITICAL.

| Sev. | Alvo | Achado |
|---|---|---|
| MAJOR | `05_p0/ssc_p0/writelock.py:escritor-unico` | nomes distintos permitem escritores concorrentes entre missoes; **"a ordem manual do Fundador nao substitui exclusao mutua"** |
| MAJOR | `06_p1a/leitores_config.py:falha-fechada` | fonte ausente, ilegivel ou JSON invalido vira `{}`, indistinguivel de configuracao limpa |
| MAJOR | `06_p1a/evidencias/contencao.py:isolamento` | o rotulo "deteccao integral" **excede o mecanismo**, que fotografa so a arvore do repositorio e exclui `locks/` |
| MAJOR | `06_p1a/evidencias/revisao_p1a2.py:credenciais-e-PII` | `dir_descartavel` e `argv_publico` recebem o caminho temporario cru e o JSON nao passa por redacao integral |
| MAJOR | `06_p1a/tests/test_emendas_p1a3.py:anti-P2` | o sentinela AST e explorável e nao protege consumidores introduzidos em P1-B |
| MAJOR | `pacote-revisao.txt:ancoragem` | falta o codigo completo do gerador da P1-A.3.6 |
| MINOR | `pipeline.py:quota` | nao-bloqueante: prejudica a fidelidade da evidencia, mas nao promove provedor |
| MINOR | `07_p1b/preflight_atual.py:duplicacao` | nao-bloqueante: o laco duplicado classifica corretamente, mas mantem o mecanismo de deriva |
| MINOR | `preflight_capsula.py:capsula` | nao-bloqueante: a propriedade vale pelo guarda, nao pela derivacao por construcao |
| OBS | `07_p1b:autorizacao-sombra` | **este estado nao autoriza reabrir a P1-B em observacao-sombra** enquanto isolamento, escritor unico, fencing e anti-P2 seguirem abertos |

### 3.3 As declaracoes obrigatorias surtiram efeito verificavel

Nao foram formalidade. **Tres achados do revisor citam o que so as
declaracoes lhe deram:**

- a **Declaracao 1** (ACHADO 4) produziu um MAJOR proprio sobre
  `writelock.py`, com a frase que fecha o ponto: *"a ordem manual do
  Fundador nao substitui exclusao mutua"*. Sem a declaracao, este eixo
  teria sido julgado contra premissa falsa — que e precisamente o que a
  §8 da `99_achados-governanca-20260731.md` mandava evitar;
- a **Declaracao 3, item 1** virou o `DEFEITO-NOVO: SIM`;
- a **Declaracao 4** (`EXERCE` mede cobertura) aparece no MAJOR-4, onde o
  revisor recusa aceitar a correcao porque *"o teste novo exercita apenas
  a funcao canonica, nao esse caminho de persistencia"* — exatamente a
  distincao entre cobertura e forca de asercao;
- a **Declaracao 2** teve efeito parcial: o revisor aceitou que o filtro
  `ELIGIBLE`-unico foi substituido e **nao** o levantou como achado, mas
  manteve o escopo aberto no MAJOR-6 (a metade (A) nao cobre `07_p1b`).

Declarar contra o proprio interesse **piorou** o veredito, e e assim que
tinha de ser.

### 3.4 O achado do revisor contra este proprio pacote

O MAJOR-5 e o MAJOR `pacote-revisao.txt:ancoragem` sao o mesmo ponto, e
**procede integralmente**: o pacote manda o revisor julgar a construcao do
gerador (*"O gerador DESTE pacote herda a mesma construcao — julgue-a
tambem"*) e **nao inclui o codigo do gerador**. `pacote_p1a36.py` nao
esta em `ARQUIVOS_COMPLETOS` porque nao existia em ALVO — e a lista se
ancora em ALVO por construcao, que e a correcao do MAJOR #5. Pedir
julgamento sobre um artefato ausente e defeito de composicao **desta
missao**, nao do acervo.

Nao foi corrigido, e **nao podia ser**: corrigir exigiria gerar outro
pacote e reenviar, e o ato admite **uma chamada valida por provedor**.
Fica com dono e gatilho:

| Campo | Valor |
|---|---|
| **Dono** | a missao que refizer a revisao independente |
| **Gatilho** | montagem do proximo pacote |
| **Remedio especificado** | o gerador deve embutir **o proprio codigo-fonte** (lido do disco, com o SHA-256 do arquivo declarado ao lado), OU o pacote deve deixar de pedir julgamento sobre ele. As duas coisas juntas — pedir o julgamento e omitir o objeto — e o defeito |

## 4. Portao

O ato define: **zero CRITICAL e zero MAJOR nos dois vereditos**.

| Condicao | Medido |
|---|---|
| CRITICAL no veredito do codex | **0** |
| MAJOR no veredito do codex | **12** (6 nao-fechados + 6 novos) |
| Veredito do kimi | **inexistente** |
| **Portao** | **NAO ATRAVESSADO** |

`READY-FOR-P1-B-RETRY` esta **fora de alcance** por dois caminhos
independentes, e bastaria um. Os achados exigem alteracao de codigo e de
teste; a missao e probatoria e **nao corrige**. Logo: **ADJUST**.

**Nao e BLOCKED.** O ato reserva BLOCKED para declaracao de tier expirada
— que nao expirou — e para pacote que nao coubesse em algum revisor — e o
pacote coube: o codex leu as 9.519 linhas e computou o hash. A falha do
kimi e **comercial**, no provedor, e nao de tamanho.

### 4.1 Disposicao formal da metade "nos dois vereditos"

Emenda de registro proprio, acrescentada apos o commit `8b227aa`: a §4
concluia que o portao nao foi atravessado **sem dispor** da segunda metade
da clausula. Dispor dela e necessario — sem isso, uma missao futura pode
ler "ADJUST" como "feche os doze MAJOR e o portao passa", que e **falso**.

**O portao tem duas metades, e as duas falharam por causas independentes.**

| Metade | Exigencia | Medido | Reparavel nesta missao? |
|---|---|---|---|
| (a) | zero CRITICAL e zero MAJOR | 0 CRITICAL, **12 MAJOR** | Nao — corrigir e alterar codigo e teste, vedado a missao probatoria |
| (b) | **nos dois** vereditos | **um** veredito existe, nao dois | Nao — depende de ato do proprietario ou de terceiro provedor |

**Fechar (a) NAO faz o portao passar.** Ainda que os doze MAJOR fossem
fechados amanha, o portao continuaria fechado sobre esta evidencia, porque
(b) exige um segundo veredito que **nao existe**. As duas metades sao
conjuntivas, e este registro nao as funde.

**(b) e hoje insatisfazivel, e isso e medido, nao suposto.** A ultima
corrida de frota (`07_p1b/evidencias/preflight-20260801T235521Z.json`,
2026-08-01T23:55:21Z) da:

| provedor | resultado |
|---|---|
| codex | **SHADOW_ELIGIBLE** |
| kimi | **SHADOW_ELIGIBLE** |
| claude | SUPERVISED |
| google | SUPERVISED |
| grok | SUPERVISED |

O ato nomeia revisor entre os **SHADOW_ELIGIBLE**, e ha exatamente dois —
um deles com a cota do ciclo esgotada. **Nao existe substituto**:
SUPERVISED e teto de especificacao, nao autorizacao, e trocar por um
SUPERVISED seria promover provedor por conveniencia de portao — exatamente
o que o eixo anti-P2 proibe.

**Por que ADJUST e nao BLOCKED, pelo texto do ato e nao por preferencia.**
O ato nomeia **dois** gatilhos de BLOCKED, e os dois foram **medidos
ausentes**: declaracao de tier expirada (nao expirou —
`valido_no_instante: true` nas duas evidencias) e pacote que nao coubesse
em algum revisor (coube — 9.519 linhas lidas, hash recomputado pelo
revisor). O ato nomeia **um** gatilho de ADJUST — "achado que exija
alteracao" — e ele **ocorreu**, com doze ocorrencias apontaveis. Entre um
terminal cujas condicoes nao ocorreram e um cuja condicao ocorreu, o
registro segue o que foi medido.

BLOCKED tambem seria **menos informativo**: apagaria do rotulo o unico
resultado substantivo desta missao — um veredito independente, integral e
desfavoravel.

**Nenhuma segunda tentativa contra o kimi.** O 403 e do **ciclo de
faturamento**, nao de janela de taxa: repetir devolve a mesma recusa. E
"uma chamada valida por provedor" limita chamadas **validas** — nao
autoriza recusas em serie contra um portao comercial, cujas duas saidas
(comprar uso extra, subir de plano) sao respectivamente proibida e ato do
proprietario.

| Campo | Valor |
|---|---|
| **Dono** | o proprietario, para a cota do kimi; a missao de frota, para um terceiro SHADOW_ELIGIBLE |
| **Gatilho** | renovacao do ciclo do kimi, ou provedor novo saindo SHADOW_ELIGIBLE numa corrida de preflight |
| **Estado da metade (b)** | **ABERTA e insatisfazivel no ciclo corrente** |
| **Corrigido nesta missao?** | **Nao** — nao e materia de missao probatoria |

Isto **nao reabre** o veredito do codex nem o converte. Registra-se que o
criterio de aceite "mesmo pacote/hash nos dois revisores" (§9 da
`99_decisao-p1a31.md`) tem hoje a metade do **pacote cumprida** — mesmos
bytes preparados e entregues aos dois, hash identico nas duas evidencias —
e a metade do **revisor descumprida**, pela terceira rodada consecutiva.

**Escritor desta emenda.** Lease `p1a36-emenda-ops`, fence **1**, pid
108332, adquirido antes desta escrita. Nome distinto de `p1a36-ops`
deliberadamente: reusar o lease da missao sobrescreveria `.lease` e
`.fence`, que sao a evidencia do escritor unico citada na §1 e nas duas
evidencias de revisao — precedente de `achados-gov-emenda6-ops`.

## 5. Fronteira, custo e ambiente

| Item | Estado **verificado** |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | 5 caminhos: 2 instrumentos, 2 evidencias, 1 `.gitattributes`, mais este registro — **nenhum de codigo, teste ou politica** |
| Escritas fora do repositorio | descartaveis das chamadas, pacote gerado e copia de seguranca da prova E — todos no temp da sessao |
| Copia datada irma | **nenhuma criada** — pratica encerrada por decisao do Fundador |
| Escrita em `lucaX` ou `LucaX Enterprise OS` | **nenhuma** |
| Store do harness | **nao gravado** |
| **Chamadas de provedor** | **2** — uma por provedor, ambas por assinatura |
| **Chamadas de modelo efetivamente servidas** | **1** (codex). O kimi foi recusado por 403 antes de qualquer inferencia |
| Custo variavel | **0** — nenhuma via paga, top-up, extra usage ou fallback |
| Tag, remoto ou push | nenhum |
| Lock tomado a forca | nenhum |
| HKCU / variavel persistente do usuario | **nao tocada** — a capsula filtra a COPIA |

As duas chamadas correram **dentro da capsula**: o subprocesso recebeu
`ambiente_capsula()`, e o `env_vars_removidas_nomes` de cada evidencia
registra, **por nome e nunca por valor**, o que foi retirado.

## 6. Achado desta missao — contra o proprio instrumento de contencao

**A contencao acusou mutacao fora do descartavel na corrida do codex, e a
causa foi esta sessao.** A evidencia registra, como medida:

```
"mutacoes_fora_do_descartavel": ["criado: 06_p1a/99_decisao-p1a36.md"],
"violada": true
```

Enquanto o codex lia o pacote, a sessao escreveu o rascunho **deste
arquivo** no repositorio. O manifesto SHA-256 fotografa a arvore inteira
antes e depois da chamada; ele viu a criacao e reprovou a corrida
(returncode 3), como foi construido para fazer.

**O que isto e, e o que nao e.** Nao e escrita do revisor: o codex correu
com `--sandbox read-only --ephemeral`, em `cwd` descartavel, e o unico
arquivo restante no descartavel e o proprio pacote. E escrita do
**operador**, atribuivel por construcao — o arquivo e produto do editor
desta sessao, num caminho que o revisor nao conhece e nao poderia nomear.

**Controle positivo, e vale registrar.** A corrida seguinte, do kimi,
correu sob disciplina de nao-escrita e devolveu
`mutacoes_fora_do_descartavel: []`, `violada: false`. O mesmo instrumento,
duas corridas, dois resultados opostos conforme a sessao escrevia ou nao:
o guarda **mede o que diz medir**.

**O defeito e do instrumento, e o revisor o encontrou por outro caminho.**
`manifesto` nao distingue escritor: qualquer mutacao na arvore durante a
janela da chamada e imputada ao revisor. Some-se o MAJOR do revisor —
*o rotulo "deteccao integral" excede o mecanismo, que fotografa so a
arvore do repositorio e exclui `locks/`* — e o quadro fica completo: o
instrumento e **cego para fora** e **indiscriminado para dentro**.

| Campo | Valor |
|---|---|
| **Dono** | a missao que tratar o MAJOR-3 / MAJOR `contencao.py:isolamento` |
| **Gatilho** | proxima revisao independente |
| **Remedio especificado** | separar as duas perguntas que hoje o manifesto responde junto: (a) *o revisor escreveu?* — que exige atribuicao, nao so deteccao; (b) *a arvore mudou?* — que exige cobertura alem de `RAIZ`. Enquanto (a) nao existir, a sessao **nao escreve no repositorio durante a janela da chamada**, e isso e disciplina de operacao, nao propriedade do codigo |
| **Corrigido nesta missao?** | **Nao** — missao probatoria |

## 7. Alcance — o que esta missao estabelece e o que NAO estabelece

### 7.1 Estabelecido — medido, e independente de quem escreve

| Fato | Como |
|---|---|
| O pacote e funcao dos commits, e de mais nada | 5 geracoes, 1 hash; inclusive de checkout de OUTRO commit e sob arvore mutada |
| Os dois revisores receberam os MESMOS bytes | copia verbatim; `pacote_sha256` identico nas duas evidencias; o codex recomputou e confirmou |
| O pacote coube num revisor real | 9.519 linhas lidas, 238,975 s, veredito produzido |
| As quatro declaracoes obrigatorias chegaram e pesaram | tres achados do revisor citam o que so elas informaram |
| A correcao de `argv_kimi` (P1-A.3.4) vale | a chamada atravessou o CLI e alcancou o provedor; a falha mudou de classe |
| O escritor unico foi reverificado antes de cada persistencia | fence 1 nas duas evidencias, o mesmo da abertura |
| O pacote nao vaza usuario, caminho local nem chave | medido: 0 ocorrencias em 6 alvos e 5 padroes de chave |

### 7.2 NAO estabelecido — e nao se presume

- **Nenhum dos seis MAJOR fechou.** O unico revisor que falou disse
  NAO-FECHADO para os seis, com justificativa apontavel em cada um.
- **A revisao dupla continua nao tendo ocorrido.** Um veredito nao e
  dois. Nada nesta missao autoriza tratar o pronunciamento do codex como
  se fosse consenso de dois revisores independentes.
- **Nada se afirma sobre o merito dos achados novos.** Esta sessao os
  **transcreve**; verificar cada um e trabalho da missao de correcao, e
  ela nao pode certificar o proprio conserto.
- **A P1-B nao esta autorizada em modo sombra.** O revisor disse o
  contrario de forma explicita, e esta missao nao tem o que opor.
- **A quota do kimi permanece NAO MEDIDA ex ante.** O que se mediu foi o
  **403 depois** da tentativa; o CLI 0.30.0 continua sem expor franquia
  antes da chamada.
- **`EXERCE 64` continua nao significando 64 guardas corretos** — e o
  revisor usou exatamente essa distincao para nao fechar o MAJOR-4.
- **Nada foi corrigido.** Zero linha de codigo, teste ou politica.

## 8. O que a proxima missao precisa

1. **Corrigir, uma correcao por commit, com as duas provas** — teste que
   exerce a coisa real e reversao vermelha medida —, na ordem dos seis
   MAJOR nao fechados, e depois nos seis MAJOR novos.
2. **O gerador do proximo pacote deve embutir o proprio codigo-fonte**
   (§3.4), ou parar de pedir julgamento sobre si.
3. **Nao escrever no repositorio durante a janela da chamada de revisao**
   (§6), ate que a contencao saiba atribuir escritor.
4. **A revisao independente segue devendo o segundo revisor.** Enquanto a
   cota do kimi nao for renovada — ato do proprietario —, ou outro
   provedor SHADOW_ELIGIBLE nao existir, o criterio de aceite
   "mesmo pacote/hash nos dois revisores" nao fecha.
5. **A missao de politica segue com as quatro materias intactas**: esta
   missao nao tocou politica em ponto algum. O ACHADO 4 acaba de receber
   classificacao **MAJOR por revisor independente** — deixou de ser
   candidato.

> Quem corrigiu nao certificou, e quem revisou reprovou. O resultado
> desta missao e o veredito, nao o conserto.

## 9. ATESTADO

Emenda de registro proprio, por ordem do Fundador. Lease
`p1a36-atestado-ops`, fence **1**, pid 97572, adquirido antes desta
escrita — nome distinto, para nao sobrescrever `p1a36-ops` nem
`p1a36-emenda-ops`, que sao evidencia citada nas §1 e §4.1.

### 9.1 Eram SEIS. Agora sao SEIS + SEIS = DOZE

Os dois numeros ficam **separados**, e o total nunca aparece sozinho:

| Conjunto | Quantos | Origem |
|---|---|---|
| MAJOR **nao fechados** | **6** | abertos pela revisao da P1-A.3.1; o codex pronunciou-se sobre cada um e disse NAO-FECHADO nos seis |
| MAJOR **novos** | **6** | abertos pelo proprio veredito do codex desta missao |
| | **6 + 6** | escrever "12" sem os dois numeros esconde que **nenhum** dos originais fechou |

Escrever so o total permitiria a leitura falsa de que houve progresso
parcial. **Nao houve.** O saldo dos seis originais e zero fechados.

### 9.2 Classificacao dos seis novos — medida, nao presumida

Duas classes, conforme a ordem: **(F) mesma familia** — guarda que
**afirma** a propriedade em vez de exercer a interface real, a classe do
MAJOR #3 — ou **(N) classe que a varredura dos 86 guardas nao media**.
Cada linha traz a medicao que sustenta a classificacao.

**N1 · `05_p0/ssc_p0/writelock.py` — escritor unico entre missoes**
→ **(F) mesma familia, E (N) invisivel ao eixo da varredura.**
Medido: a docstring de `escritor.py` **afirma** *"uma segunda sessao
falha na aquisicao"*, e o teste que a sustenta
(`test_estabilizacao_p1a1.py:347`) usa `"p1-ops"` nos **dois** lados —
exercita o unico caso que funciona, nunca o que ocorre em operacao. E
familia do MAJOR #3 sem ambiguidade.
Mas a varredura **o viu e o classificou EXERCE**: linha P0-26,
`writelock.py:78-108 LockSessao`, *"2 de 4 ramos; lock de SO real em
tmpdir"*. O eixo media **alcance de linha**, e a linha era alcancada. O
que o eixo nao podia ver e que **o caso exercido nao e o caso que
ocorre**. Esta e a Declaracao 4 demonstrada num achado real, e nao em
tese.
A varredura ja o registrara por outro caminho — linha A1, "Escritor
unico entre missoes" —, e a P1-A.3.5 §5 **P4** o pulou como materia de
politica. O que muda hoje: deixou de ser candidato e **e MAJOR por
revisor independente**.

**N2 · `06_p1a/leitores_config.py` — falha fechada**
→ **(F) mesma familia.**
Medido no fonte: `ler_json` e `ler_toml` fazem
`except (OSError, ValueError): return {}`. A docstring do modulo
**afirma** *"Fonte ausente, ilegivel ou vazia devolve `{}` — sempre por
medicao do disco, jamais por cegueira escrita no fonte"*. A distincao
existe **na prosa**; o valor devolvido nao a carrega, e nenhum consumidor
a jusante consegue separar "fonte lida e limpa" de "fonte que nao pude
ler". A propriedade e afirmada, nao exercida — familia do MAJOR #3.
**A varredura nao media isto**: o modulo nasceu da correcao 7 da propria
P1-A.3.5 e tem teste (`test_leitor_config_p1a35.py`); o eixo perguntava
se a linha do guarda era alcancada, nunca se o **valor degradado** era
distinguivel do valor limpo.

**N3 · `06_p1a/evidencias/contencao.py` — rotulo "deteccao integral"**
→ **(F) mesma familia — e e a familia do MAJOR #3 no sentido literal.**
Medido: `EXCLUIDOS_DO_MANIFESTO = ("locks",)` e `manifesto(raiz)`
fotografa **so** a arvore sob `RAIZ`; o rotulo `enforcement_kimi()`
afirma *"DETECCAO INTEGRAL por manifesto SHA-256 da arvore inteira"*.
Escrita fora do repositorio nao aparece. O rotulo afirma alcance que o
mecanismo nao tem.
**Parcialmente medida pela varredura**: existe teste que **proibe** o
rotulo de afirmar sandbox inexistente (heranca da P1-A.3.2) — logo o eixo
"rotulo honesto" foi exercido para a palavra *sandbox*. A palavra
*integral* nao foi. Classe medida no principio, nao no caso.

**N4 · `06_p1a/evidencias/revisao_p1a2.py` — credenciais e PII**
→ **(F) mesma familia, pelo mecanismo ja nomeado do achado 10 e da
correcao 7: a copia que ninguem exercita fica para tras.**
Medido linha a linha, e o revisor esta **exato**:
`revisao_p1a2.py:170` grava `"dir_descartavel": tmp` **cru**, e
`:179-180` escreve `json.dumps(meta…)` **sem redacao integral**. Os
outros quatro runners fazem `_redigir(tmp)` e
`_redigir(json.dumps(…))` — `revisao_p1a3.py:228,248`,
`revisao_p1a31.py:202,221`, `revisao_p1a33.py:202,220` e
`revisao_p1a36.py:207,225`. **Quatro corrigidos, um esquecido.**
**A varredura o viu, mas por outro eixo**: linha P1A-33,
`revisao_p1a2.py:51 redacao`, **SEM-TESTE**, *"forca FRACA; arquivo com
ZERO linha executada"*. Ela mediu a **primitiva** de redacao. Nao mediu
os **pontos de chamada** — se cada campo que sai para disco passa por
ela. Classe nao medida: cobertura de call-site, nao de funcao.

**N5 · `06_p1a/tests/test_emendas_p1a3.py` — anti-P2**
→ **(F) mesma familia** quanto ao escopo, **(N) classe nao medida**
quanto a explorabilidade.
Medido: a varredura ja registrara a metade de escopo como **achado 13** —
*"a metade (A) do sentinela anti-P2 cobre so `06_p1a`"*, marcado
`escopo (ja aberto)`. Isso o revisor confirmou.
O que ele acrescentou e **novo e nao medido**: o sentinela so reconhece
literais exatos e aliases atribuidos no mesmo arquivo, de modo que
concatenacao, constante importada (`RESULTADOS`) ou propagacao por
booleano **contornam** `_portoes_de_execucao`. A varredura classificava
guardas; **nao media se um guarda podia ser contornado de proposito**.

**N6 · `pacote-revisao.txt` — ancoragem**
→ **nem (F) nem (N): nao e guarda do acervo.**
E defeito de composicao **desta missao** — o pacote manda julgar o
gerador e omite seu codigo-fonte (§3.4). O objeto **nao existia** quando
os 86 foram varridos, e nao poderia ter sido classificado por ela.
Registrado como classe propria para nao inflar nenhuma das outras duas.

**Saldo da classificacao:** **4 de 6** na mesma familia por inteiro
(N1–N4), **1** partilhado entre as duas classes (N5), **1** fora de ambas
(N6). A familia do MAJOR #3 — afirmar em vez de exercer — **continua
sendo a classe dominante**, agora dita por revisor independente e nao
pela sessao que a nomeou.

### 9.3 O portao exige zero MAJOR nos DOIS vereditos, e so existe UM

**A revisao dupla nunca ocorreu desde a P1-A.3.1.** Medido, rodada a
rodada:

| Rodada | codex | kimi | Causa da falta |
|---|---|---|---|
| P1-A.3.1 | veredito (REPROVADO, seis MAJOR) | **sem veredito** | returncode 1, 3,844 s; causa nao caracterizada na evidencia |
| P1-A.3.3 | **sem veredito** | **sem veredito** | codex: limite de uso do ciclo. kimi: `Cannot combine --prompt with --plan` |
| P1-A.3.6 | veredito (REPROVADO) | **sem veredito** | kimi: 403, cota do ciclo de faturamento |

Em **tres** rodadas houve **dois** vereditos ao todo, ambos do codex,
ambos REPROVADO. **Nunca houve dois vereditos na mesma rodada.**

**Ausencia de veredito nao e ressalva.** Nao conta como aprovacao
parcial, nao conta como silencio favoravel e nao se soma ao veredito
existente para formar consenso. Onde falta um veredito, falta **um
revisor** — e a §9 da `99_decisao-p1a31.md` exige os dois. A metade (b)
do portao esta **aberta**, nao mitigada (§4.1).

Correcao ao que o despacho supunha: a falta do kimi na **P1-A.3.3** nao
foi por tier vencido — foi incompatibilidade de flags do CLI, medida em
`kimi-20260731T155932Z.json`. Tier vencido foi a causa do **BLOCKED de
codex e kimi no preflight** da P1-B.01, coisa distinta. Registrado pelo
que foi medido.

### 9.4 Dono, gatilho e remedio dos doze

**Os seis nao fechados** (numeracao original da P1-A.3.1):

| # | Dono | Gatilho | Remedio especificado |
|---|---|---|---|
| 1 | missao de correcao | abertura | alcancar a config do grok em SQLite, ou devolver **INDETERMINADO** em vez de `{}` — nunca classificar como limpo o que nao foi lido |
| 2 | missao de correcao | abertura | ancorar `_ZERO` no **valor numerico parseado**, nao em prefixo textual; casos `.0`, `00`, `0.00`, `0,0` no teste, e contraprova com franquia real |
| 3 | missao de correcao | abertura | separar **atribuicao** de **deteccao** (§6); cobrir alem de `RAIZ` ou retirar a palavra "integral" do rotulo — teste que reprove o rotulo excedente, como ja existe para "sandbox" |
| 4 | missao de correcao | abertura | `_verificar_lock(fence_esperado=…)` imediatamente antes da persistencia em `revisao_p1a2.main`, como os outros quatro runners ja fazem; teste **no caminho de persistencia**, nao so na funcao canonica |
| 5 | missao que refizer a revisao | montagem do proximo pacote | o gerador embute o **proprio** codigo-fonte com o SHA-256 do arquivo ao lado, OU o pacote para de pedir julgamento sobre ele |
| 6 | missao que reabrir a P1-B | ja disparado | metade (A) passa a cobrir `07_p1b`; o sentinela resolve alias, import e concatenacao — ou **nega** quando nao consegue resolver |

**Os seis novos:**

| # | Dono | Gatilho | Remedio especificado |
|---|---|---|---|
| N1 | **missao de politica, materia 4** | abertura dessa missao | lock **unico do repositorio**, e `liberar()` que expire o lease que concedeu; teste com **nomes distintos** nos dois lados |
| N2 | missao de correcao | primeira correcao do MAJOR-1 | distinguir no **valor** "fonte ausente/ilegivel" de "fonte lida e vazia" (sentinela ou excecao), e `auditar_config` falhar **fechada** no primeiro caso |
| N3 | missao de correcao | junto com o MAJOR-3 | o mesmo remedio do MAJOR-3 — as duas linhas sao o mesmo objeto visto de dois lados, e **nao se fundem na contagem** |
| N4 | missao de correcao | primeira correcao | `_redigir` em `dir_descartavel` e no `json.dumps` integral de `revisao_p1a2.py`; teste que reprove o caminho cru, e que varra **os cinco** runners de uma vez |
| N5 | missao que reabrir a P1-B | junto com o MAJOR-6 | idem MAJOR-6, acrescida da resolucao de alias/import/concatenacao; **nao se funde na contagem** |
| N6 | missao que refizer a revisao | montagem do proximo pacote | idem MAJOR-5; **nao se funde na contagem** |

Tres pares (3/N3, 6/N5, 5/N6) tratam do mesmo objeto por lados
diferentes. Ficam com o **mesmo remedio** e **contagem separada**: fundi-los
transformaria doze em nove e produziria a aparencia de progresso que a
§9.1 existe para impedir.

### 9.5 Quem corrigiu nao certificou, e ADJUST e desfecho previsto

**Nenhuma das correcoes sob julgamento foi certificada por quem as fez.**
As correcoes dos seis MAJOR vieram da P1-A.3.2, da P1-A.3.4 e da
P1-A.3.5; nenhuma dessas missoes emitiu atestado de fechamento — todas
registraram, com essas palavras, que fechar depende de revisor
independente. Esta missao **nao corrigiu nada** e por isso podia
submeter. O revisor falou, e disse NAO-FECHADO nos seis.

**ADJUST e desfecho previsto pelo ato, nao falha da missao.** O ato
escreve *"Achado que exija alteracao encerra em ADJUST; nao corrigir
nesta missao"* e *"Commitar o registro qualquer que seja o veredito,
inclusive ADJUST e BLOCKED"*. A missao entregou o que lhe cabia: pacote
novo e ancorado, mesmos bytes aos dois provedores, as quatro declaracoes
obrigatorias transmitidas — com efeito verificavel em tres achados do
veredito —, pronunciamento explicito por MAJOR e sobre defeito novo, e o
registro commitado com o resultado desfavoravel intacto.

**O que seria falha:** corrigir aqui para o portao passar, resumir o
pacote para caber, tratar a ausencia do kimi como ressalva, ou escrever
"12 MAJOR" sem dizer que seis sao os mesmos de antes. Nada disso foi
feito.

**Contagem como medida, nunca como meta.** Os numeros deste atestado —
6 + 6, 4 de 6 na mesma familia, 2 vereditos em 3 rodadas — sao o que foi
medido. Nenhum e alvo a perseguir.
