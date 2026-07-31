---
id: SSC-DEC-P1A31
titulo: Registro e Decisao da Missao SSC+ P1-A.3.1 — revisao do estado final exato (ADJUST)
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-31
---

# Registro e Decisao — Missao SSC+ P1-A.3.1

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo** sobre o HEAD `677c585` (P1-A.3). A
> `99_decisao-p1a3.md` NAO foi reescrita nem alterada. `NVIDIA_API_KEY`
> global/HKCU jamais removida, alterada ou persistida.

## DECISAO: **ADJUST** — nenhum atestado emitido; P1-B-02 permanece FECHADA

Esta missao **nao** emite `READY-FOR-P1-B-RETRY` e **nao** cria o atestado
aditivo previsto, porque a condicao do atestado ("somente com ambos os
vereditos verdes") nao foi satisfeita. Dois fundamentos independentes,
cada um suficiente por si:

1. **Codex: `VEREDITO: REPROVADO`, com 4 MAJOR remanescentes.** A regra da
   missao e "nenhum CRITICAL ou MAJOR pode permanecer" e "se qualquer
   correcao de codigo, teste, politica ou pacote for necessaria, NAO
   corrigir nesta missao: retornar ADJUST, pois a correcao criaria novo
   estado nao revisado". Nada foi corrigido.
2. **Kimi: revisao nao obtida.** A chamada unica retornou
   `403 usage limit for this billing cycle` — quota do ciclo esgotada,
   sem resposta de revisao. A declaracao de tier estava valida no
   instante da chamada (expira `2026-08-01T01:31:00Z`), mas a quota do
   ciclo nao e renovavel por esta sessao: **somente o proprietario** pode
   renovar/adquirir. Custo variavel permaneceu zero.
3. **Achado novo MAJOR desta missao: o pacote nao e ancorado no commit**
   (§4.1). Descoberto ao executar a prova de ancoragem exigida para o
   micro-commit: 4 dos 11 hashes de evidencia sao funcao dos bytes da
   copia de trabalho local, nao do conteudo versionado. Corrigi-lo e
   trabalho da proxima missao — corrigir aqui criaria novo estado nao
   revisado, exatamente o que esta missao existe para impedir.
4. **Achado novo MAJOR desta missao: o sentinela anti-P2 mede lista de
   caminhos, nao comportamento** (§4.2). Revelado pelo micro-commit
   `dc19e8c`: falha por falso positivo diante de qualquer arquivo
   aditivo que mencione o literal, e por falso negativo diante de um
   consumidor real escrito dentro da allowlist. Consertar o sentinela e
   **pre-condicao** da P1-A.3.2.

**Total: 6 MAJOR** — 4 do codex, 2 desta missao — e 1 MINOR, cuja
classificacao de nao bloqueante foi superada pelos fatos (§4.2).

O conteudo funcional em revisao e, e continua sendo, o commit `677c585`.
Esta missao nao alterou codigo, teste, configuracao nem documento
historico.

## 1. Identidade e pre-condicoes (verificadas)

| Item | Resultado |
|---|---|
| HEAD exigido | OK — `677c5853cf3d504696e7d2e326287cc1a8a37f38` |
| Pai exigido | OK — `c4fa5a0615d834ee33561a5ec9c93b2b8d95430f` |
| Tree | `3d9b59e2537ffb39ebbf14cea61e89ffffafd606` |
| Sem tag e sem remoto | OK (verificado na abertura) |
| Arvore limpa na abertura | OK |
| Copia datada | OK — `SSC-Plus_copia-p1a31-20260731-074426` |
| Lock operacional com fencing superior | OK — `locks/p1a31-ops.*`, fence 1, lease 120 s renovado a 30 s por processo dedicado (`evidencias/renovador_lock.py`) durante toda a missao |
| `99_decisao-p1a3.md` intocada | OK |
| P1-B-01, capsula, politica NVIDIA, evidencias anteriores preservadas | OK |

## 2. Suites reexecutadas sobre o HEAD `677c585`

| Suite | Comando | Resultado |
|---|---|---|
| P0 | `python -m unittest discover -s 05_p0/tests` | **100/100 OK** |
| P1-A | `python -m unittest discover -s 06_p1a/tests` | **307/307 OK** |
| Prova central | `python 05_p0/cenarios/prova_central.py` | **18/18 assercoes OK** |

O JSON da prova contem UUIDs por corrida; o arquivo versionado foi
restaurado apos a reexecucao — a arvore permaneceu limpa.

## 3. Pacote exato de revisao

| Item | Valor |
|---|---|
| **SHA-256 do pacote revisado** | `c3b5c54a2520f21196f182dc8cb3d1c94efba3b9740e2c84614096281e4bfc7e` |
| Bytes | 447.693 |
| Geracao | deterministica, a partir do HEAD, por `06_p1a/evidencias/pacote_p1a31.py` |
| Determinismo | **provado apenas na copia de trabalho**: geracoes repetidas produzem SHA-256 identico (duas geracoes frescas apos a revisao reproduziram o hash do arquivo entregue). **NAO reproduzivel a partir do commit** — ver achado §4.1 |
| Conteudo | identidade commit/tree, diff integral contra o pai, arquivos funcionais/politicos/testes completos no HEAD, resultados das suites, threat review, hashes das evidencias, perguntas 1–6 |
| Redacao | fonte exclusivamente de conteudo git; usuario local redigido (forma longa e 8.3); evidencias entram somente como hashes; **zero credencial e zero valor de ambiente** |
| Bytes identicos aos dois revisores | sim — os mesmos bytes copiados para os dois diretorios descartaveis; **nenhuma reconstrucao entre revisores** |

**Pacote anterior (nao equivalente).** A ultima rodada da P1-A.3 revisou o
pacote SHA-256
`2c8061c0a5aaa52e23a6710e42b1384433135e9a30579cafee7033a188316016`.
Esse pacote **nao equivale automaticamente** ao pacote final: o commit
`677c585` contem correcoes posteriores a ele. Foi exatamente essa lacuna
que motivou a P1-A.3.1.

## 4. Revisao — codex (executada)

| Campo | Valor |
|---|---|
| Provider declarado | OpenAI |
| Modelo observado | GPT-5 (Codex; identificador exato nao exposto). Cabecalho do CLI: `gpt-5.6-sol`, `provider: openai`, `reasoning effort: high` |
| Canal | assinatura OAuth (ChatGPT Pro 5x), tier valido no instante |
| Hash do pacote recebido | `c3b5c54a…3187…` — **coincide** com o pacote entregue (sem divergencia) |
| Enforcement read-only | `codex exec --sandbox read-only --ephemeral`, cwd descartavel |
| Chamadas de modelo | 1 |
| Custo variavel | 0 |
| Duracao | 256,3 s |
| Escopo | pacote integral: identidade, diff, arquivos completos, suites, threat review, hashes e perguntas 1–6 |
| **Veredito** | **REPROVADO** |

### Achados (verbatim resumido, severidade preservada)

| # | Sev. | Alvo | Achado |
|---|---|---|---|
| 1 | MAJOR | `06_p1a/preflight_capsula.py` — google/grok PAYG | O atalho manual para Google/Grok nao chama `executar_preflight` nem `_config_persistida`; chave, endpoint PAYG ou auto-topup persistidos podem resultar em SUPERVISED, contrariando os bloqueios economicos. |
| 2 | MAJOR | `06_p1a/preflight/adaptadores.py` — quota esgotada | Formatos como `0.0 tokens available` ou `0% quota available` escapam das regexes de esgotamento e casam `available`, classificando quota zero como disponivel. |
| 3 | MAJOR | `06_p1a/evidencias/revisao_p1a3.py` — isolamento kimi | cwd descartavel e instrucao textual nao restringem o filesystem; o Kimi pode escrever fora do diretorio, e a verificacao de arquivos restantes nao detecta essas mutacoes. |
| 4 | MAJOR | `preflight_capsula.py` + `revisao_p1a3.py` — lease/fencing | Ambos verificam o lease somente antes do trabalho, nao imediatamente antes da persistencia; apos chamadas superiores aos 120 s do lease, podem gravar com lease expirado ou titular substituido. |
| 5 | MINOR | `06_p1a/tests/test_emendas_p1a3.py` — anti-P2 | **Nao bloqueante** (classificacao e motivo do proprio revisor): o teste limita-se a `06_p1a` e a duas grafias literais, nao detectando consumidores externos ou variantes com aspas simples/enum; **o changeset apresentado nao contem consumidor efetivo**. |

**CRITICAL: nenhum.** **MAJOR: 4 (remanescentes).** **MINOR: 1, nao
bloqueante.** **OBS: nenhum.**

**Observacao autorreferente (registrada, nao corrigida).** O MAJOR #4
descreve uma classe de defeito que se aplica tambem a ferramenta desta
missao (`06_p1a/evidencias/revisao_p1a31.py`, derivada de
`revisao_p1a3.py`): a chamada ao codex durou 256 s, acima do lease de
120 s. Nao houve titular concorrente e o renovador dedicado manteve o
lease vivo o tempo todo, mas a verificacao imediatamente anterior a
persistencia nao existe. Corrigir isso e trabalho da proxima missao.

## 4.1 Achado novo desta missao (nao originado dos revisores)

**MAJOR — `06_p1a/evidencias/pacote_p1a31.py`: o pacote nao e ancorado no
commit.** Revelado ao tentar executar a prova de ancoragem exigida (§10.2).

O gerador declara, no proprio docstring (linhas 18–20), que *"toda a
leitura e via `git show`/`git diff` (conteudo versionado, LF)"*. A
afirmacao e **falsa para o bloco de hashes de evidencia**: a linha 193 usa
`(RAIZ / rel).read_bytes()`, isto e, le os **bytes da arvore de trabalho
local**, nao o blob versionado. Com `core.autocrlf=true` (confirmado neste
repositorio, sem `.gitattributes`), os bytes em disco de um arquivo
rastreado sao funcao do **historico de checkout**, nao do commit:

**Os 4 de 11 arquivos divergentes** (medidos; os 7 restantes coincidem):

| Arquivo | blob git | disco (arvore principal) | checkout novo |
|---|---|---|---|
| `06_p1a/evidencias/revisao-p1a3/codex-20260731T020226Z.json` | 4530 B | 4530 B (LF) | 4566 B (CRLF) |
| `06_p1a/evidencias/revisao-p1a3/codex-20260731T021442Z.json` | 5116 B | 5116 B (LF) | 5152 B (CRLF) |
| `06_p1a/evidencias/revisao-p1a3/kimi-20260731T021718Z.json` | 7659 B | 7659 B (LF) | 7689 B (CRLF) |
| `06_p1a/tiers_declarados.json` | 716 B | 716 B (LF) | 738 B (CRLF) |

Contraste com um arquivo **coincidente**, que ja estava em CRLF no disco:
`revisao-p1a3/codex-20260731T023445Z.json` — blob 5205 B, disco 5241 B
(CRLF), checkout 5241 B (CRLF): identico nos dois lados.

Os arquivos gravados pelas ferramentas Python da missao permaneceram em LF
no disco (o git os considera limpos porque normaliza na entrada); um
checkout novo os materializa em CRLF. Dai 4 dos 11 hashes divergirem.

Consequencias:

1. **Os hashes de evidencia mostrados ao codex nao correspondem ao
   conteudo versionado.** Um revisor que tentasse recomputa-los a partir
   do repositorio em `677c585` obteria valores diferentes em 4 de 11
   linhas — o bloco perde justamente a funcao probatoria que motiva
   inclui-lo.
2. **O determinismo verificado foi o mais fraco.** "Duas geracoes
   produzem o mesmo SHA-256" foi confirmado (inclusive duas geracoes
   frescas apos a revisao), mas isso so prova estabilidade **dentro desta
   copia de trabalho**, nao reprodutibilidade a partir do commit.
3. **Nao contamina o conteudo funcional revisado — verificado, nao
   presumido.** O diff entre o pacote entregue e o pacote regenerado a
   partir do commit tem exatamente 4 linhas alteradas, **todas** no bloco
   de hashes de evidencia: o diff integral e o conteudo completo dos 17
   arquivos funcionais/politicos/testes sao **identicos byte a byte**.
   Logo, o que o codex avaliou como codigo, teste e politica esta
   corretamente ancorado em `677c585`.

**Alcance dos vereditos — em aberto, sem presuncao de sobrevivencia.** O
paragrafo acima sustenta o eixo *funcional* dos vereditos. Ele **nao**
sustenta o eixo *evidencia*: os hashes que o codex viu nao correspondem
ao conteudo versionado, e nao se afirma aqui que a avaliacao do revisor
sobre esse eixo permaneceria a mesma se ele tivesse visto os hashes
corretos. **Nao se presume sobrevivencia.** Julgar o alcance dos
vereditos sobre o eixo evidencia e trabalho da **P1-A.3.2**, nao desta
missao.

Correcao devida (proxima missao, nao aqui): ler as evidencias por
`git show HEAD:<path>` — ou declarar explicitamente que sao hashes da
copia de trabalho — e alinhar o docstring a implementacao.

## 4.2 Achado #6 — o sentinela anti-P2 mede lista de caminhos, nao comportamento

**MAJOR — `06_p1a/tests/test_emendas_p1a3.py:642`,
`test_shadow_eligible_nao_tem_consumidor_de_execucao`.** Revelado pelo
micro-commit probatorio `dc19e8c`.

O teste faz `os.walk` sobre `06_p1a` — varre o **filesystem**, nao o git —
coleta os arquivos `.py` que contem o literal `SHADOW_ELIGIBLE` e exige
**igualdade exata** com uma allowlist fixa de 6 caminhos.

**O nome do teste afirma ausencia de consumidor de execucao; o corpo
verifica uma lista de arquivos. Sao propriedades diferentes**, e a
segunda nao implica a primeira.

Por medir conjunto de caminhos em vez de comportamento, o guarda falha
**nos dois sentidos**:

- **Falso positivo.** Qualquer arquivo aditivo sob `06_p1a` que apenas
  *mencione* o literal — documentacao, ferramenta de missao, texto de
  pergunta de revisao — reprova a suite inteira, sem introduzir consumo
  algum. Foi o que ocorreu: `evidencias/pacote_p1a31.py` contem o literal
  no enunciado da pergunta 2.
- **Falso negativo, mais grave.** Um consumidor de execucao real escrito
  **dentro de um dos 6 arquivos ja na allowlist** passa sem deteccao: a
  lista continua identica e o teste segue verde. **O guarda anti-P2 e
  contornavel escrevendo no lugar certo.**

### 4.2.1 A regressao e real e o alarme e falso — as duas metades

Medicao em checkouts limpos (worktrees destacadas), que separa
contaminacao de copia de trabalho de regressao commitada:

| Commit | P1-A em checkout limpo |
|---|---|
| `677c585` | **307/307 OK** |
| `dc19e8c` | **306/307 FAILED** |

Ambas as metades valem, e nenhuma cancela a outra:

- **Mecanicamente real.** O commit `dc19e8c` reprova a suite em checkout
  limpo. Nao e artefato da copia de trabalho, nao e flake, e nao depende
  de estado local. Um portao verde/vermelho esta vermelho por causa deste
  commit.
- **Semanticamente falso positivo.** Nenhum codigo, teste ou politica foi
  alterado; nenhum consumidor de execucao foi introduzido; a mencao esta
  num texto de pergunta. A propriedade que o teste diz proteger —
  ausencia de consumidor — nao foi violada.

Registrar so a primeira metade transformaria uma ferramenta de missao em
regressao funcional inexistente; registrar so a segunda dispensaria um
vermelho legitimo. Ficam as duas.

### 4.2.2 Consequencias normativas

1. **`P1-A 307/307` deixa de ser criterio de aceite valido** em Goal
   futuro enquanto o sentinela medir lista de arquivos em vez de
   comportamento. O numero passou a depender de quantos artefatos
   probatorios existem sob `06_p1a`, nao da integridade do invariante.
   Um Goal que exija 307/307 exige, na pratica, que a missao nao escreva
   evidencia — o oposto do que este laboratorio pede.
2. **Consertar o sentinela e PRE-CONDICAO da P1-A.3.2, nao item dela.**
   A P1-A.3.2 escreve evidencia sob `06_p1a` e **colide na primeira
   escrita**: qualquer arquivo `.py` seu que mencione o literal reprova a
   suite antes de a missao comecar. O conserto precisa preceder a
   abertura, sob pena de a missao nascer vermelha.
3. **Ordem de verificacao.** O despacho que autorizou `dc19e8c` ordenou a
   conferencia das suites em **pos-commit**, quando a falha ja era
   observavel em **pre-commit** (os arquivos estavam staged e em disco, e
   o sentinela varre o filesystem). Rodar as suites com os arquivos
   staged, antes de persistir, teria exibido 306/307 e evitado commitar
   um vermelho. Fica a regra prospectiva: **suites com os arquivos
   staged, antes do commit** — nao apenas depois.

## 5. Revisao — kimi (nao obtida)

| Campo | Valor |
|---|---|
| Provider | kimi (familia/provider distinto do codex) |
| Canal | assinatura OAuth, tier Allegretto, valido no instante (`expira 2026-08-01T01:31:00Z`) |
| Hash do pacote entregue | `c3b5c54a…` — os **mesmos bytes** do codex, 447.693 bytes |
| Chamadas de modelo | 1 (consumida sem resposta) |
| Custo variavel | 0 |
| Retorno | `returncode 1` em 3,8 s |
| Erro | `provider.api_error: 403 You've reached your usage limit for this billing cycle.` |
| Modelo observado | **nao observado** (nenhuma resposta produzida) |
| Veredito | **inexistente** |

A quota do ciclo de faturamento esta esgotada (limite semanal 100%
utilizado). **Somente o proprietario** pode renovar, adquirir uso extra
ou aguardar a virada do ciclo. A missao nao tentou nenhuma via paga,
nenhuma segunda chamada e nenhum provider substituto.

## 6. Ressalva sobre o commit `677c585`

O commit `677c585` ocorreu **apos a liberacao do lease** da missao
P1-A.3. A identidade HEAD/pai/arvore foi verificada na abertura desta
missao e corresponde exatamente ao exigido; **nenhuma corrida foi
observada**. A ressalva fica registrada por completude probatoria, nao
por evidencia de dano.

## 7. Regra prospectiva (vinculante para as proximas missoes)

**Staging, commit e pos-verificacao sempre sob lease vivo.** O lease nao
pode ser liberado antes da comprovacao de arvore limpa pos-commit. Alem
disso, e por forca do MAJOR #4: a verificacao do lease deve ocorrer
**imediatamente antes de cada persistencia**, nao apenas na abertura do
trabalho — especialmente quando a operacao intermediaria (chamada de
provider) pode exceder a janela do lease.

**Suites com os arquivos staged, ANTES do commit.** Verificacao apenas
em pos-commit persiste um vermelho que era observavel antes — foi o que
ocorreu com `dc19e8c` (§4.2.2, item 3). Portao de suite roda sobre o
conjunto que sera commitado, nao sobre o que ja foi.

## 8. Evidencias desta missao (hashes SHA-256)

```
63bf77e7b196d989a61b9b3afef592f21ff2019e673ec446bbfe21b602339b44  06_p1a/evidencias/revisao-p1a31/codex-20260731T105702Z.json
d400a2162d7bb4287b93557fc793cb6ac97d2e9e735191c84da9dfee122ada5e  06_p1a/evidencias/revisao-p1a31/kimi-20260731T110318Z.json
c3b5c54a2520f21196f182dc8cb3d1c94efba3b9740e2c84614096281e4bfc7e  06_p1a/evidencias/revisao-p1a31/pacote-p1a31.txt
895ded416cf3e978f341ad5c67d7692950f00f7ca7e3c3a7469ca61306596afa  06_p1a/evidencias/pacote_p1a31.py
916ab23a622f75664f3e8685494866e6b2d75d43e7e4fc3da6b909b60f399a1f  06_p1a/evidencias/revisao_p1a31.py
```

## 9. Aceite — conferencia item a item

| Criterio de aceite | Estado |
|---|---|
| Mesmo pacote/hash nos dois revisores | **parcial** — mesmos bytes preparados e entregues; o kimi nao produziu revisao (403) |
| Zero CRITICAL/MAJOR | **NAO** — 4 MAJOR remanescentes (codex) |
| Suites verdes | **parcial** — na abertura (HEAD `677c585`): 100/100, 307/307, 18/18. Apos o micro-commit `dc19e8c`: P0 100/100 e prova 18/18 verdes, **P1-A 306/307** pelo sentinela do §4.2 (falso positivo mecanicamente real) |
| Micro-commit exclusivamente probatorio | OK — §10: staging explicito, apenas caminhos novos, zero arquivo rastreado tocado, escopo `-text` declarado em §10.0 |
| Zero escrita canonica | OK |
| Zero PAYG / zero custo variavel | OK — 2 chamadas por assinatura, custo 0 |
| Zero PII/segredo no pacote | OK |
| Lock cobre toda mutacao Git | OK — nenhuma mutacao Git ocorreu; lock vivo durante toda a missao |

## 10. Micro-commit probatorio

O **atestado aditivo nao foi criado** — a condicao "somente com ambos os
vereditos verdes" nao foi satisfeita, e o conteudo do atestado depende do
veredito. O **registro** da decisao, por outro lado, existe
independentemente do veredito: as escritas autorizadas (evidencias,
atestado e micro-commit probatorio) sao um **limite de escopo**, nao um
gatilho condicionado a aprovacao; a verificacao final exige "arvore limpa
apos o commit" sem condicionar a verde; e o precedente do repositorio
commita decisoes negativas (`c4fa5a0` ADJUST, `cf61e0d` BLOCKED). Manter
um ADJUST fora do historico introduziria vies no rastro probatorio.

Por essa leitura, o micro-commit probatorio foi **autorizado** pelo
Soberano, sob lease vivo, restrito a quatro caminhos **novos**:

```
06_p1a/99_decisao-p1a31.md                (este registro)
06_p1a/evidencias/revisao-p1a31/          (evidencias + pacote revisado)
06_p1a/evidencias/pacote_p1a31.py         (ferramenta da missao)
06_p1a/evidencias/revisao_p1a31.py        (ferramenta da missao)
```

Staging explicito caminho a caminho (**sem `git add -A`**); zero arquivo
rastreado modificado ou removido; zero alteracao de codigo, teste,
configuracao ou documento historico; sem runtime, sem segredo, sem tag,
sem remoto, sem push. O identificador do commit e as provas pos-commit
estao em `locks/registro-commit-p1a31.txt` (este documento e conteudo do
proprio commit e nao pode conter o hash que o inclui).

**A primeira tentativa de autorizacao foi condicionada a uma prova de
ancoragem — regenerar o pacote a partir do commit e obter `c3b5c5…` — que
foi executada e FALHOU (§10.2).** O commit foi entao abortado e so
retomado sob nova decisao soberana, ja com a falha registrada e **sem
qualquer afirmacao de ancoragem**. A falha nao decorre deste commit:
decorre do defeito pre-existente do §4.1.

### 10.0 Extensao de escopo declarada: dois `.gitattributes`

Antes do staging, cada caminho foi submetido ao portao
`git hash-object` vs `git hash-object --no-filters`. **Dois arquivos
divergiram** — `revisao-p1a31/codex-20260731T105702Z.json` e
`revisao-p1a31/kimi-20260731T110318Z.json` —, sinal de que o filtro de
EOL alteraria seus bytes. Conforme autorizado, foi criado um
`.gitattributes` **escopado ao diretorio de evidencias desta missao**
(`06_p1a/evidencias/revisao-p1a31/.gitattributes`, conteudo `* -text`).
**Nao** foi criado `.gitattributes` na raiz e **`core.autocrlf`
permanece `true`, inalterado.**

Um teste mais forte que o portao — recheckout do indice via
`git checkout-index` e comparacao `cmp` byte a byte — revelou que outros
**tres** caminhos, fora daquele diretorio, tambem nao preservavam bytes
(o proprio git avisou `LF will be replaced by CRLF`):

| Caminho | disco | apos recheckout | escopo `-text` |
|---|---|---|---|
| `06_p1a/99_decisao-p1a31.md` | 18.090 B | 18.414 B | estendido |
| `06_p1a/evidencias/pacote_p1a31.py` | 10.780 B | 10.997 B | estendido |
| `06_p1a/evidencias/revisao_p1a31.py` | 9.224 B | 9.432 B | estendido |
| `06_p1a/evidencias/revisao-p1a31/*` (4 arquivos) | — | identico | ja coberto |

Por decisao soberana, o escopo foi **estendido** com um segundo arquivo,
`06_p1a/.gitattributes`, contendo **quatro entradas ancoradas por
arquivo** (nao um curinga):

```
/.gitattributes -text
/99_decisao-p1a31.md -text
/evidencias/pacote_p1a31.py -text
/evidencias/revisao_p1a31.py -text
```

A primeira entrada e auto-referente e necessaria: sem ela o proprio
`.gitattributes` nao preserva bytes no recheckout — defeito detectado
pelo portao e corrigido antes do commit.

Ambos os `.gitattributes` integram este commit e sao aqui **declarados
como extensao de escopo** em relacao aos quatro caminhos originais.
Verificado: nenhum arquivo rastreado foi modificado pela introducao deles
(o staging exibe apenas entradas `A`, nenhuma `M`), e nenhum arquivo alem
dos tres nomeados e afetado.

### 10.1 Ancoragem: as evidencias estao FORA do conjunto revisavel

Questao decidida antes do commit: *os quatro caminhos de evidencia estao
dentro ou fora das exclusoes declaradas do pacote `c3b5c5…`?* Se
estivessem **dentro**, a evidencia da revisao residiria no conjunto
revisado — circularidade e defeito de definicao do pacote, nao
trade-off.

**Estao FORA**, por construcao verificavel em `pacote_p1a31.py`. O pacote
tem exatamente tres fontes de conteudo, todas enumeradas explicitamente,
sem glob, sem varredura de diretorio e sem `git status`:

| Fonte | Definicao | Contem algum dos 4 caminhos? |
|---|---|---|
| `ARQUIVOS_COMPLETOS` | 17 caminhos literais (`06_p1a/preflight*`, `06_p1a/tests/*`, `tiers_declarados.json`), lidos via `git show 677c585:<path>` | **nao** |
| `EVIDENCIAS_HASHEADAS` | 11 caminhos literais, todos em `revisao-p1a3/` (nao `revisao-p1a31/`), `p1a3-preflight-*.json` e `tiers_declarados.json` | **nao** |
| Diff integral | `git diff PAI HEAD` com `PAI`/`HEAD` **constantes fixadas** no script (`c4fa5a0` / `677c585`) | **nao** — commits posteriores nao entram num diff de par historico fixo |

Consequencia: o commit probatorio **nao altera nenhum byte** do pacote.

Consequencia: os quatro caminhos novos **nao alteram nenhum byte** do
pacote, e essa conclusao permanece valida.

### 10.2 A prova de ancoragem foi executada e FALHOU

O gerador valida `git rev-parse HEAD == 677c585` e aborta em qualquer
outro HEAD (`PARADA: HEAD/pai inesperados`), de modo que apos um commit
ele nao roda na arvore principal — salvaguarda funcionando. A prova foi
entao montada da unica forma que a torna significativa: uma **worktree
temporaria destacada em `677c585`**, alimentada pelo mesmo gerador, para
verificar se o pacote e reproduzivel **a partir do commit**. Resultado:

```
pacote entregue ao codex (arvore principal) = c3b5c54a2520f21196f182dc8cb3d1c94efba3b9740e2c84614096281e4bfc7e
pacote regenerado a partir do commit 677c585 = e1f856e78ac2b6298bfe0b5a6a2c064039c30be3f14a957f5ecb46c5e37103b9
```

**Divergencia.** O diff entre os dois pacotes tem exatamente 4 linhas
alteradas, todas dentro do bloco de hashes de evidencia; o diff integral
e o conteudo completo dos 17 arquivos funcionais sao **identicos byte a
byte**. Por forca da regra da missao ("divergencia de hash... interrompe
a missao") e por a autorizacao do commit ter sido condicionada a esta
prova, o commit foi abortado e a worktree temporaria removida.

## 11. O que a proxima missao (P1-A.3.2) precisa fazer

A correcao do gerador e a **P1-A.3.2**, nao esta missao. Cabe a ela
tambem julgar o alcance dos vereditos sobre o eixo evidencia (§4.1), sem
presuncao de sobrevivencia.

0. **PRE-CONDICAO — corrigir o sentinela anti-P2 (§4.2) antes de abrir a
   P1-A.3.2.** Sem isso a missao colide na primeira escrita de evidencia
   sob `06_p1a` e nasce vermelha. O teste deve verificar **comportamento**
   (ausencia de consumidor de execucao), nao igualdade de lista de
   caminhos.
1. **Corrigir os 6 MAJOR** (missao propria, com lock e copia datada):
   atalho google/grok fora do preflight; regexes de quota esgotada
   (`0.0 tokens available`, `0% quota available`); isolamento real do
   kimi no filesystem; verificacao de lease imediatamente antes de cada
   persistencia (incluindo as ferramentas `revisao_p1a3*.py`); e a
   ancoragem do pacote no commit (§4.1) — sem ela, nenhum pacote futuro
   e verificavel por terceiros a partir do repositorio; e o sentinela
   anti-P2 (§4.2), que hoje e contornavel por dentro da allowlist.
2. **Novo commit** com as correcoes → **novo HEAD, novo tree, novo
   pacote** (o pacote `c3b5c5…` deixa de representar o estado).
3. **Nova revisao dupla** sobre o novo pacote: o codex precisa rever o
   novo estado, e o kimi precisa de **quota renovada pelo proprietario**
   e tier declarado valido no instante da chamada.
4. **P1-B-02 permanece FECHADA** ate `READY-FOR-P1-B-RETRY` emitido sobre
   um HEAD efetivamente revisado por dois providers com zero
   CRITICAL/MAJOR.
