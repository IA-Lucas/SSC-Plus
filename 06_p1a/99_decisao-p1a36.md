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
