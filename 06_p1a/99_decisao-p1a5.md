---
id: SSC-DEC-P1A5
titulo: Registro e Decisao da Missao SSC+ P1-A.5 — recalibrar o criterio e adotar o escritor unico
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-04
---

# Registro e Decisao — Missao SSC+ P1-A.5

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhuma decisao ou relatorio historico
> foi editado. Missao de **correcao** — e por isso ela **nao certifica
> nada**. Os tres achados que ela tocou so fecham quando um revisor
> independente disser que fecharam.

## DECISAO: **CONCLUIDO-COM-PULADOS**

As quatro ordens foram executadas. **Pulados**, por ordem expressa do
ato: os quatro MAJOR novos que a ordem 4 manda registrar sem corrigir, os
tres MAJOR de origem ainda abertos, os tres MINOR e as duas OBS. Cada um
esta na §5 com dono, gatilho e remedio.

Nao e CONCLUIDO puro porque *"registrei e nao corrigi"* precisa aparecer
na decisao, e nao so no corpo. Nao e ADJUST porque nenhuma ordem ficou
por fazer.

## SUMARIO — 10 linhas

1. **Criterio recalibrado** no `CLAUDE.md` da raiz, com as tres
   condicoes: (a) ganha o recorte *area ja revisada*, (b) intacta, (c)
   **nova** — saldo nao-positivo nos MAJOR de origem. O texto anterior
   **nao foi apagado**: fica ao lado, com a razao da superacao.
2. Sob o criterio vigente, a mesma medicao da P1-A.4 devolve **3, 2 e
   +9** — nenhuma das tres dispara, e a trilha segue aberta por medicao,
   nao por vontade.
3. **Escritor unico ADOTADO** (`P1A4-1`): renovador, prova minima e a
   verificacao canonica passam pelo `EscritorRepositorio`. O guarda que
   exigia isolamento foi **invertido**, nao apagado.
4. Prova (a): dois processos REAIS do renovador, nomes diferentes — a
   segunda sai com **codigo 3** e o manifesto SHA-256 dos locks fica
   **identico**; repetido contra o `locks/` **vivo**.
5. Prova (c): **cinco** pontos de chamada exercidos contra titular
   alheio, `revisao_p1a2.main()` real sem gravar um byte, e o preflight
   da P1-B corrido **na capsula** (rc 0, zero chamada paga).
6. Prova (b): **seis mutantes** medidos um a um — M1=**90** vermelhos,
   M2=**3**, M3=**2**, M4=**3**, M5=**5**, M6=**6**. Mutante registrado
   em disco **antes** de cada aplicacao.
7. A troca abriria um buraco na atribuicao, e ele foi fechado junto: com
   um lease so, atribuir por caminho bastaria ao intruso sobrescrever o
   arquivo. Agora exige **caminho E titular** medido no fechamento.
8. **`P1A4-3` corrigido**: o recibo declara `alcance_da_medicao` e nunca
   mais apresenta `nenhum` como ausencia. Exercido plantando escrita no
   lar do CLI — a cegueira e real, e o recibo a nomeia.
9. **`P1A4-6` corrigido exercendo**: `caminhos_lidos_de_fato` planta um
   campo-sentinela e pergunta ao leitor. O buraco era **inexistente**, e
   `VIGIADO_MAS_NAO_AUDITADO` fica **vazio por medicao**.
10. Suites: **344+256** e **894+1217** na abertura, **344+256** e
    **914+1241** no fechamento. Prova central **18 assercoes, 20
    eventos**. Custo variavel **0**; sem tag e sem remoto; lease
    `p1a5-ops` vivo do inicio ao fim.

> **Correcao desta linha, feita depois e declarada.** Ate 2026-08-04 ela
> dizia *"Prova central **18/20**"*. Era erro **desta** missao, e so
> desta linha: a §1 e a §1.2 deste mesmo documento sempre registraram o
> par correto. `18` e `20` sao **duas grandezas** — assercoes e eventos
> —, e escreve-las como fracao inventa um denominador e faz ler como
> *"duas assercoes falhando"*. Medido na apuracao: o fonte
> `05_p0/cenarios/prova_central.py` tem **um unico commit em toda a
> historia** (`33bc963`) e o blob no HEAD e byte a byte igual ao da
> baseline — **nenhuma assercao apareceu**. A regra que impede a
> repeticao esta no `CLAUDE.md` da raiz. Nenhum outro documento foi
> tocado: `18/20` nunca existiu fora daqui.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Medido |
|---|---|
| HEAD de abertura | `1af15c5` |
| Arvore | limpa (`git status --porcelain` vazio) |
| Branch / tag / remoto | `master` / nenhuma / nenhum |
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** — nenhum mutante esquecido |
| Lease desta missao | `p1a5-ops`, fence 1, pid 66364 — pelo mecanismo **antigo**, que era o vigente na abertura (ver §2.4) |
| Suite `05_p0/tests` | **344 passed, 256 subtests** |
| Suite `06_p1a/tests` | **894 passed, 1217 subtests** |
| Prova central | **18 assercoes, 20 eventos** |

### 1.1 O HEAD do ato nao e o HEAD da arvore, e isso e declarado

O ato diz *"HEAD 3f24085"*. A arvore estava em **`1af15c5`**, tres
commits adiante — e os tres sao o **registro da propria P1-A.4**
(`fc2ad14`, `d3fa762`, `1af15c5`), a missao que gerou este despacho.
`3f24085` e o ALVO do pacote que o revisor julgou, e continua sendo: o
que se corrige aqui e o que aquele pacote produziu de achado.

Nao houve `checkout`. Reescrever a arvore para tras apagaria o registro
que fundamenta o despacho.

### 1.2 A prova central regenera um arquivo rastreado

`05_p0/cenarios/prova_central.py` reescreve
`05_p0/saidas/prova_central.json` com identificadores nao-deterministas
(UUID-4 de sessao/linhagem/attempt). Medido: **18 assercoes, 20
eventos** — os mesmos numeros de sempre. O arquivo foi **restaurado ao
HEAD** (`git checkout --`), como na P1-A: a corrida e a medicao; o
diff seria ruido.

## 2. ORDEM 1 — a recalibracao

Commit **`ae5bed3`**. Gravada no `CLAUDE.md` da raiz, que e onde o ato
mandou e onde qualquer sessao futura a le.

### 2.1 O que mudou, e o que nao mudou

| # | Antes (P1-A.3.7) | Agora (P1-A.5) |
|---|---|---|
| (a) | 6+ defeitos NOVOS | 6+ novos **em area ja revisada**; estreia conta separado |
| (b) | 4+ na familia do MAJOR #3 | **identica** |
| (c) | — | **saldo nao-positivo** nos MAJOR de origem |

**O fundamento e a medicao, e ela e do proprio repositorio.** O criterio
original nasceu de *tres ciclos com saldo zero* — mas o texto media
**defeitos novos**, nunca **saldo**. A P1-A.4 fechou **nove de doze**,
viu a familia recuar de **4/6 para 2/6**, e ainda assim disparou a
parada no limiar exato. O `(c)` mede o que o fundamento sempre disse
medir.

### 2.2 A conta refeita sob o criterio vigente

| Condicao | Limiar | P1-A.4 | Dispara? |
|---|---|---|---|
| (a) novos em area ja revisada | 6+ | **3** (`P1A4-1`, `P1A4-2`, `P1A4-6`) | nao |
| (b) familia do MAJOR #3 | 4+ | **2** (`P1A4-3`, `P1A4-6`) | nao |
| (c) saldo nos MAJOR de origem | nao-positivo | **+9** | nao |

Os outros tres novos (`P1A4-3`, `P1A4-4`, `P1A4-5`) vivem na fase **P2**,
que o pacote `a36471a3…` submeteu a revisao **pela primeira vez**. A
declaracao de estreia esta feita, com o pacote nomeado, como o proprio
criterio vigente passou a exigir de quem a invoca.

### 2.3 O texto anterior nao foi apagado

Ele fica na secao seguinte do `CLAUDE.md`, com a razao da superacao
escrita. **A decisao STOP da P1-A.4 foi correta sob o criterio que vigia
entao**, e apagar o texto esconderia isso.

### 2.4 O lease desta missao

Adquirido na abertura pelo mecanismo **antigo** (`p1a5-ops`, fence 1,
pid 66364) — era o que existia. Depois da ordem 2 foi **encerrado e
readquirido** pelo mecanismo novo: `repositorio.lock`, titular
`p1a5-ops`, **fence 7**, pid 62096. A troca do proprio escritor da
missao no meio dela e deliberada: adotar um mecanismo e nao usa-lo seria
repetir, na missao que corrige o achado, o defeito que o achado descreve.

## 3. ORDEM 2 — o escritor unico entra em uso

Commit **`c5195cd`**.

### 3.1 O achado, e por que ele nao era do mecanismo

> `P1A4-1` — *"declara e testa que o lock unico novo NAO ESTA EM USO; o
> mecanismo vivo continua permitindo escritores de nomes distintos"*.
> FAMILIA: fora-de-ambas, falha de **integracao**.

O `escritor_repositorio` existia desde a P1-A.3.7, provado entre
processos reais, e **nenhum runner o importava** — havia um teste
exigindo que ninguem o importasse, porque a ordem daquela missao era
*nao trocar*. O defeito nunca foi o mecanismo: foi a **fiacao**.

### 3.2 O que passou a usar o escritor unico

| Ponto | Antes | Agora |
|---|---|---|
| `evidencias/renovador_lock.py` | `EscritorP1(<sessao>.lock)` | `EscritorRepositorio`, e **aborta com codigo 3** se ja ha titular |
| `evidencias/prova_minima.py` | `EscritorP1` | `EscritorRepositorio` |
| `evidencias/contencao.py:verificar_lock` | montava `f"{sessao}.lease"` | le o lease UNICO; `sessao` virou o **titular exigido** |
| `preflight_capsula.py` | **quarta copia** do guarda | delega a canonica |
| `07_p1b/preflight_atual.py` | montava o caminho para `expira_em` | pede o caminho a quem o define |

**O guarda foi invertido, nao apagado.** `OMecanismoVivoNaoFoiTrocado`
virou `OMecanismoVivoFOITrocado`, e fica vermelho se a adocao for
desfeita — nas duas pontas: nenhum caminho operacional pode deixar de
importar o escritor novo, e **nenhum modulo de producao pode instanciar
o antigo**.

### 3.3 O buraco que a troca abriria, fechado junto

Com um lease so, atribuir apenas por CAMINHO seria mais fraco do que
antes: bastaria ao intruso **sobrescrever `repositorio.lease`** para ser
atribuido ao renovador e nao reprovar a corrida. Antes, um lease de
outro nome caia em `nao_atribuidas` por nao casar o caminho.

`atribuir` passa a exigir **duas** condicoes: o caminho e o do escritor
unico **e** o titular medido no fechamento da janela e a sessao
operacional. Titular ausente, vencido ou de outro nome atribui **nada** —
fail-closed, inclusive no default (quem nao mede o titular nao atribui).

### 3.4 As tres provas

**(a) duas sessoes de NOMES DIFERENTES, a segunda sem escrever um byte.**
Dois processos **reais** do `renovador_lock.py` — o ponto de entrada que
a operacao executa, nao um construtor chamado de dentro do teste. A
segunda sai com **returncode 3**, imprime `PARADA` nomeando o titular, e
o **manifesto SHA-256 do diretorio de locks fica identico** antes e
depois. Repetido contra o `locks/` **vivo** deste repositorio:

    PARADA: o escritor unico do repositorio ja e de 'p1a5-ops';
    'missao-intrusa-ops' nao adquiriu e nao escreveu

Contraprova no mesmo arquivo: morto o titular, a outra missao adquire
com **fence maior**. Sem ela, um escritor que recusasse sempre passaria
no teste acima e travaria o repositorio.

**(c) o caminho operacional real, e nao so o teste.** Tres camadas:

1. **cada ponto de chamada**, exercido contra titular alheio —
   `contencao.verificar_lock`, `preflight_capsula`,
   `07_p1b/preflight_atual`, `revisao_p1a2`, `revisao_p1a4`. Com
   contraprova: sob o **proprio** titular, todos passam;
2. **`revisao_p1a2.main()` de verdade**, com o escritor detido por outro
   nome: `SystemExit` e **zero arquivo gravado**. E a contraprova — sob o
   proprio escritor, grava e o recibo registra o titular;
3. **o preflight da P1-B corrido na capsula**, no repositorio real:
   `python 06_p1a/capsula.py python 07_p1b/preflight_atual.py`, rc **0**,
   cinco provedores classificados, **zero chamada paga**. O recibo
   (`07_p1b/evidencias/preflight-20260804T125015Z.json`) carrega
   `{"sessao": "p1a5-ops", "pid_titular": 62096, "fence": 7}` — do lease
   unico.

**(b) reversao vermelha, quatro mutantes na ordem 2.**

| Mutante | O que desfaz | Vermelhos em `06_p1a/tests` |
|---|---|---|
| **M1** | `verificar_lock` volta a ler `f"{sessao}.lease"` | **90** |
| **M2** | renovador volta ao `EscritorP1` | **3** |
| **M3** | `prova_minima` volta ao `EscritorP1` | **2** |
| **M4** | condicao do titular desligada em `atribuir` | **3** |

Cada mutante foi registrado em `scratchpad/MUTANTE-ATIVO.txt` **antes**
de ser aplicado, revertido a mao e conferido com a suite verde antes do
registro ser apagado.

**M2 mediu tambem os proprios testes desta ordem.** Com ele, a corrida
da prova (a) passou de **0,11 s** para **60 s** — o tempo do segundo
renovador rodando ate o teto em vez de morrer na aquisicao. O verde
rapido nao era vacuidade: era o mecanismo funcionando.

### 3.5 O que a ordem 2 mudou alem do pedido — declarado

| Mudanca | Por que ela e parte da troca |
|---|---|
| `preflight_capsula` deixa de ter copia propria do guarda | manter a quarta copia enquanto o mecanismo muda e o achado **N4** na letra: primitiva corrigida que nao alcanca o ponto de chamada |
| **sete** copias de `_escrever_lock` nos testes viram uma (`apoio.escrever_lock`) | as sete ficaram vermelhas **no mesmo instante** — o mecanismo dos achados 7, 10 e 14 visto do outro lado |
| `renovador_lock.py` ganha 2º argumento (diretorio de locks) | a prova entre processos reais precisa correr sobre descartavel; nao ha caminho operacional que o use, e isso e teste, nao configuracao |
| `test_estabilizacao_p1a1` deixa de adquirir no `locks/` **vivo** | inofensivo enquanto cada nome tinha o seu arquivo; com um lock so, a suite disputaria o escritor com o renovador da missao |
| `preflight_capsula` passa a devolver `pid_titular` | campo **novo** na evidencia da capsula, nunca campo trocado |

### 3.6 O que a ordem 2 NAO move, e esta escrito

**A fronteira entre o lease e o Git.** `git commit` continua sem
consultar lease nenhum, e `test_fronteira_escritor_p1a39` continua
medindo isso **sem uma linha alterada** na classe que o mede. O
mecanismo e cooperativo: quem escreve sem passar pelo escritor nao e
barrado por nada. Fechar o ACHADO 4 deu exclusao entre missoes — nao deu,
e nao podia dar, alcance sobre quem nao passa por ali. Confundir as duas
coisas seria fechar um achado com a prova de outro.

**`EscritorP1` nao foi apagado.** Ele continua correto no que sempre
garantiu — exclusao dentro de um nome — e a prova cruzada dos testes
depende dele para **medir** o ACHADO 4 em vez de cita-lo.

**O lock de sessao da P0 (`ssc_p0/kernel.py`) nao foi tocado.** Ele
tranca por sessao de trabalho do kernel, que e outra propriedade; o
ACHADO 4 e sobre missoes que escrevem no acervo.

## 4. ORDEM 3 — os dois da familia (F)

Commit **`92b1a41`**.

### 4.1 `P1A4-3` — o recibo afirmava ausencia sobre o que nao vigia

> *"o recibo afirma `nenhum` apesar do alcance parcial e da escrita
> conhecida em `CODEX_HOME`"*. FAMILIA: **(F)**.

O recibo publicava `efeito_externo: "nenhum"` e, ao lado, *"fotografia
sem nenhuma mutacao — `nenhum` aqui e medicao, nao eco do envelope"*. A
segunda frase era verdadeira **sobre a P2.3** e falsa **sobre o
alcance**: a fotografia cobre o descartavel e as raizes vigiadas, e o
lar do proprio CLI fica de fora **por decisao** — `contencao` diz, desde
a P1-A.3.6, que vigia-lo produziria alarme por escrita legitima. Nao
vigiar e defensavel; **publicar ausencia sobre o que nao se vigia, nao**.

**A correcao nao alarga a vigilancia — alarga a DECLARACAO.** O recibo
ganha `alcance_da_medicao`, com `medido` (o descartavel desta invocacao
e as raizes que a `Vigilancia` de fato fotografou) e `nao_medido` (o que
ela declara nao alcancar, **o lar do CLI nomeado** e o lado remoto). Os
dois saem do relatorio real, nao de prosa fixa. `contencao.LAR_DO_CLI`
existe para dar nome ao caminho, e **nao liga vigilancia nenhuma**.

`EFEITOS_EXTERNO` da P0 **nao foi tocado**: `nenhum` continua sendo o
valor de contrato para *sem efeito medido*.

**Exercido, e nao afirmado.** O teste **planta escrita no lar do CLI** e
mede as duas metades, que nao se substituem: (i) a cegueira e **real** —
nada aparece em `mutacoes_fora_do_descartavel` e o efeito segue
`nenhum`; (ii) o recibo a **declara**, nomeando `~/.codex`. Mais o
fail-loud: provedor sem lar declarado sai
`<lar do CLI NAO DECLARADO para '...'>` no recibo, em vez de um `nenhum`
sem ressalva.

**O teste exerce o caminho que a operacao percorre, ou um vizinho?** O
caminho: `ProvedorAssinaturaReal.invocar` inteiro, com sensor que escreve
onde o CLI real escreve. O vizinho recusado seria chamar `classificar`
com lista vazia e conferir o retorno — isso ja existia e nao vê recibo.

**O que o teste NAO cobre:**
- **o lar do CLI continua sem ser vigiado.** O que se prova e que o
  recibo diz a verdade sobre a propria cegueira, jamais que a cegueira
  acabou. Ligar a vigilancia ali e **decisao de politica**, com preco
  conhecido (alarme em toda corrida), e nao cabe a uma missao de
  correcao;
- **nada se afirma sobre o lado remoto.** Escrita no servico do provedor
  nao aparece em fotografia local, e `alcance_da_medicao` a declara;
- **`LAR_DO_CLI` e uma lista escrita a mao.** Um provedor novo sem
  entrada nela cai no ramo fail-loud — que e o desenho —, mas a lista em
  si nao e derivada de medicao do disco.

### 4.2 `P1A4-6` — o teste afirmava um buraco inexistente

> *"o teste calcula 'auditados' apenas por `FONTES`, embora
> `config_persistida("codex")` leia e mescle `~/.codex/config.toml`; ele
> afirma um buraco inexistente sem exercer a interface real"*.
> FAMILIA: **(F)**.

O revisor esta certo, e o fonte confirma: o ramo do codex soma
`ler_toml("~/.codex/config.toml")` ao `auth.json`, e os campos das duas
fontes chegam juntos a `auditar_config`. **O buraco nunca existiu.** O
que existia era uma conta feita sobre a **tabela** em vez de sobre o
**leitor** — e um `# segunda fonte` acrescentado **a mao** ao corpus de
`test_contencao_atribuicao_p1a37` para a igualdade fechar. O sintoma e o
achado eram a mesma linha.

**A correcao e exercer, e nao recontar.** `caminhos_lidos_de_fato` planta
um campo-sentinela em cada caminho candidato, dentro de um **lar
descartavel**, e pergunta a `config_persistida` de **cada** provedor se
o campo chegou. Medido:

| caminho | quem le |
|---|---|
| `~/.codex/auth.json` | codex |
| `~/.codex/config.toml` | **codex** |
| `~/.claude/settings.json` | claude |
| `~/.kimi-code/config.toml` | kimi |
| `~/.gemini/settings.json` | google |
| `~/.grok` | grok |
| `~/.codex/nao-e-fonte-de-ninguem.toml` | **ninguem** |

A ultima linha e o **controle negativo**, e ela vem primeiro no arquivo:
uma sonda que dissesse *"todos leem tudo"* faria os outros testes
passarem sem medir nada. O controle positivo e a linha de cada provedor.

Com isso: `VIGIADO_MAS_NAO_AUDITADO` fica **vazio, por medicao**; o
corpus do teste de acoplamento vem da sonda; e a segunda fonte do codex
ganha prova de que a **politica** a alcanca — planta-se um endpoint PAYG
so em `config.toml` e `auditar_config` acusa, com contraprova de config
limpa.

**Nenhuma politica foi alterada:** `FONTES` intacta, superficie da
auditoria economica intacta, comportamento de producao do leitor
identico ao de antes desta missao. O que mudou e que a medicao passou a
dizer a verdade sobre ele.

**O que o teste NAO cobre:**
- **a sonda mede o que CHEGA ao dicionario devolvido.** Um leitor que
  abrisse o arquivo e descartasse todo o conteudo sairia daqui como
  *"nao le"* — e, para o efeito que importa (a auditoria enxerga o
  campo?), essa e a resposta certa, mas nao e a mesma pergunta que *"o
  arquivo foi aberto?"*;
- **o formato do plantio vem da extensao do caminho.** Um leitor futuro
  que espere outro formato no mesmo caminho seria medido como *"nao le"*
  por erro da sonda, nao do leitor;
- **nada aqui audita a config REAL desta estacao** — o plantio corre em
  lar descartavel. Os testes que dependem da config real continuam
  sendo os outros do mesmo arquivo, e continuam sendo **pulados** quando
  a fonte nao existe.

### 4.3 Reversao vermelha da ordem 3

| Mutante | O que desfaz | Vermelhos |
|---|---|---|
| **M5** | recibo volta a afirmar ausencia (some `alcance_da_medicao`) | **5** |
| **M6** | segunda fonte do codex removida da **producao** | **6** |

**M6 merece a medicao honesta, e ela nao favorece esta missao.** Dos seis
vermelhos, **tres ja existiam** — `test_codex_soma_auth_json_e_config_
toml` e `test_as_duas_fontes_do_codex_sobrevivem_no_marcador` ja
prendiam a LEITURA da segunda fonte. O que **nao** tinha guarda era o
**acoplamento vigiar/auditar**, e era exatamente ali que a afirmacao
falsa vivia. O achado `P1A4-6` nunca foi *"a segunda fonte nao e lida"*:
foi *"a conta sobre ela e feita no lugar errado"*.

Para o `P1A4-6`, o mutante util e de **producao**, nao de teste: reverter
o teste corrigido nao mede nada, porque o teste antigo passava **verde**
sobre o defeito. Essa e a propria definicao da familia (F).

## 5. ORDEM 4 — registrado, e NAO corrigido

Nada nesta secao foi tocado por esta missao. Cada item tem **dono**,
**gatilho** e **remedio**.

### 5.1 Os MAJOR novos da P1-A.4 que ficam abertos

| # | Objeto | Familia | Dono | Gatilho | Remedio especificado |
|---|---|---|---|---|---|
| `P1A4-2` | `tests/sentinela_antip2.py:resolucao` — `%`, `.format`, `join` e imports dinamicos atravessam a varredura **sem gerar negacao** | **(N)** | missao que tratar a sentinela (mesmo objeto do MAJOR-6 e do N5) | proxima revisao independente | a varredura precisa **negar** o que nao consegue resolver, em vez de passar em silencio: construcao nao resolvida = reprova, nao = ignora |
| `P1A4-4` | `08_p2/medidor.py:reprodutibilidade` — a receita recompoe numeros com insumos **testemunhais**; nao permite recontar respostas alternativas nem a corrida sem recibo | fora de ambas | missao de reproducao da P2 | tentativa de reconto por terceiro | gravar a **evidencia bruta** que falta (respostas alternativas e o recibo da corrida sem ele) ou declarar a classe como nao-reproduzivel no proprio README |
| `P1A4-5` | `08_p2/runner_p2.py:persistencia` — `relatar(registro)` vem **antes** da reverificacao e da gravacao; nova falha de saida consome franquia e perde o recibo | fora de ambas | missao de correcao da P2 | proxima corrida real que falhe na saida | mover `relatar` para **depois** da reverificacao e da gravacao — e o mesmo desenho que o MAJOR #4 impos aos runners de revisao |

`P1A4-1` foi **tratado na ordem 2** desta missao — e nao esta fechado:
quem corrige nao certifica.

### 5.2 Os tres MAJOR de origem que seguem abertos

| # | Objeto | Situacao apos esta missao |
|---|---|---|
| **6** | sentinela contornavel por `%`/`.format`/`join`/import dinamico **sem negacao** | aberto, intocado — mesmo objeto do `P1A4-2` |
| **N1** | escritor unico existia e nao estava em uso | **tratado na ordem 2**; nao fechado, porque nao se certifica o proprio conserto |
| **N5** | ha formas deliberadas de contorno ainda invisiveis e **nao negadas** | aberto, intocado — mesmo objeto do MAJOR-6 |

O MAJOR-6, o N5 e o `P1A4-2` sao **um objeto so** visto de tres angulos:
a sentinela que deixa passar sem negar. Contam separado pela regra da
P1-A.3.6 §9.4, e o remedio e comum.

### 5.3 Os tres MINOR

| # | Objeto | Bloqueante? | Dono | Gatilho | Remedio |
|---|---|---|---|---|---|
| `08_p2/provedor_assinatura.py:ciclo-de-vida` | **SIM** para aprovacao sem ressalvas | missao de correcao da P2 | toda invocacao, hoje | `invocar` cria um `mkdtemp` por tentativa e **nunca o remove**; limpar no fim (ou registrar retencao deliberada, com o caminho no recibo) |
| `README.md:provedores-produtivos` | nao isoladamente | missao de documentacao | proxima leitura do README por terceiro | restringir a promessa ao **medido**: o kimi nunca completou uma corrida, em quatro tentativas |
| `README.md:indice-P2` | nao isoladamente | missao de documentacao | rastreabilidade dos numeros publicados | o indice da raiz omite os registros **P2.1 e P2.2**, que os numeros publicados usam |

**Nota sobre o MINOR do ciclo-de-vida**: ele vive no arquivo que a ordem
3 corrigiu. Nao foi tratado de carona — o ato manda registrar, e corrigir
por proximidade seria decidir escopo por conveniencia.

### 5.4 As duas OBS

| # | Objeto | Por que e OBS e nao achado |
|---|---|---|
| `08_p2/evidencias:historico-sem-manifesto` | nas **nove corridas anteriores a P2.3** nao se sabe se houve escrita | lacuna historica **irrecuperavel**; nao e propriedade de guarda, e nenhum conserto futuro a alcanca |
| `08_p2/medidor.py:tese-central` | o acervo mede **proxy de bytes**, nao tokens, e `executor_observado` permanece `None` | limite **declarado**; nao pertence as duas familias |

A segunda e a mesma frase que os atestados repetem desde a P1-A: **a
tese central segue nao medida em token**.

### 5.5 A contencao acusou a propria sessao — PELA SEGUNDA VEZ

Na P1-A.4, a corrida do codex devolveu:

    "violada": true,
    "mutacoes_fora_do_descartavel": [
      "alterado: repositorio/.pytest_cache/v/cache/lastfailed",
      "alterado: repositorio/06_p1a/__pycache__/leitores_config…pyc",
      "alterado: repositorio/06_p1a/tests/__pycache__/test_redacao…pyc",
      "alterado: repositorio/06_p1a/tests/test_redacao_operacao_p1a39.py"
    ]

**Quatro mutacoes fora do descartavel, e a causa foi a propria sessao**:
ela rodava a suite e editava aquele arquivo de teste enquanto o codex
lia o pacote. A corrida seguinte, do kimi, com a arvore em silencio,
devolveu `violada: false` — controle positivo no mesmo instrumento.

**O agravante, dito com o nome certo:** e a **segunda** ocorrencia, e a
primeira ja tinha remedio escrito. A P1-A.3.6 §6 especificou: *"enquanto
a atribuicao nao existir, a sessao nao escreve no repositorio durante a
janela da chamada, e isso e disciplina de operacao, nao propriedade do
codigo"*. A disciplina foi quebrada.

> **Disciplina que depende de quem opera nao e guarda.**

| Campo | Valor |
|---|---|
| **Dono** | a missao que tratar `contencao.py:atribuicao` (mesmo objeto do MAJOR #3) |
| **Gatilho** | **toda** corrida de revisao independente — nao e hipotese, ocorreu duas vezes em duas oportunidades de ocorrer |
| **Remedio especificado** | ou a atribuicao real do escritor (a pergunta *"quem escreveu?"*, hoje sem resposta), ou uma **porta que IMPECA** a sessao de escrever durante a janela. Nao mais um aviso a ser lembrado |
| **Corrigido nesta missao?** | **Nao** — a ordem 4 manda registrar |

**O que esta missao fez com isso, e o limite:** a ordem 2 fortaleceu a
atribuicao — ela passou a exigir **titular**, e nao so caminho. Isso
**nao** resolve o achado. A pergunta *"quem escreveu este byte?"* segue
sem resposta, e uma escrita da propria sessao continua caindo em
`nao_atribuidas` (que e o certo) sem que nada a **impeca** (que e o
achado). Fortalecer a atribuicao nao e criar a porta.

**Esta missao nao repetiu a quebra**, e a razao e pobre: ela nao fez
nenhuma chamada a provedor. Nao ha janela sem chamada. Isso e ausencia de
oportunidade, **nao** prova de disciplina, e registrar como prova seria
o mesmo tipo de erro que o resto deste documento mede.

### 5.6 A prova de ancoragem 3 passou VAZIA — defeito do PROCEDIMENTO

Na P1-A.4, a terceira prova de ancoragem do pacote (*"mutar arquivos
julgados e conferir que o hash nao muda"*) foi executada assim: dois
arquivos escolhidos (`08_p2/medidor.py` e `08_p2/README.md`), mutados
com `>>`, e `cmp` conferindo o hash.

**Os dois arquivos nao existiam no commit em que o clone estava.** O `>>`
devolveu *No such file or directory*, nenhuma mutacao ocorreu, e o `cmp`
passou **verde sobre nada**. A prova foi refeita com arquivos que existem
no checkout **e** que o pacote julga, e so entao valeu.

Isto e registrado como **defeito do procedimento de prova**, e nao como
incidente:

| Campo | Valor |
|---|---|
| **Dono** | a missao que gerar o proximo pacote de revisao |
| **Gatilho** | toda prova de ancoragem por mutacao |
| **Remedio especificado** | a prova precisa **falhar** quando a mutacao nao acontece. Concretamente: conferir que o arquivo **existe** e que o conteudo **mudou** (hash antes ≠ hash depois do alvo) **antes** de comparar o hash do pacote. Sem esse degrau, "o hash nao mudou" e verdade trivial |
| **Classe** | a mesma de *alcance nao prova exercicio*: o comando correu, e nao exerceu nada |

**A licao geral, que vale alem do pacote:** um passo de prova que so
verifica o **resultado esperado** passa quando o **estimulo** nao
aconteceu. Toda prova por mutacao precisa medir a mutacao.

## 6. O que esta missao alterou, integralmente

| Ordem | Commit | Producao | Teste | Registro |
|---|---|---|---|---|
| 1 | `ae5bed3` | — | — | `CLAUDE.md` |
| 2 | `c5195cd` | `escritor_repositorio.py`, `contencao.py`, `prova_minima.py`, `renovador_lock.py`, `preflight_capsula.py`, `preflight_atual.py` | 13 arquivos + `test_escritor_unico_adotado_p1a5.py` (novo) | evidencia de preflight |
| 3 | `92b1a41` | `contencao.py` (`LAR_DO_CLI`), `provedor_assinatura.py` | `test_config_real_p1a39.py`, `test_contencao_atribuicao_p1a37.py`, `test_p2_protecao_no_mecanismo_p23.py` | — |
| 4 | este | — | — | este documento |

Um commit por ordem, com as duas suites rodadas **com os arquivos
staged** antes de cada um.

### 6.1 Custo

**Zero chamada paga.** A unica execucao externa foi o preflight
diagnostico dentro da capsula (versao/login/doctor), que e o mesmo custo
variavel **0** de sempre. Nenhum modelo respondeu a esta missao.

Cota e tier **nao foram renovados**, por ordem expressa. O kimi segue com
**quatro** falhas consecutivas e **zero** vereditos; a revisao dupla
segue sem nunca ter acontecido, e nada nesta missao a aproxima.

## 7. Alcance — o que esta missao estabelece e o que NAO estabelece

### 7.1 Estabelecido — medido

| Fato | Como |
|---|---|
| O criterio de parada vigente e o de tres condicoes | gravado no `CLAUDE.md`, com a conta da P1-A.4 refeita sob ele |
| O escritor unico do repositorio esta EM USO no caminho operacional | dois processos reais, cinco pontos de chamada, um `main()` real, e o preflight na capsula |
| Uma segunda missao de outro nome nao adquire e nao escreve | returncode 3 e manifesto identico, em descartavel e no `locks/` vivo |
| A atribuicao exige titular, e nao so caminho | mutante M4: 3 vermelhos |
| O recibo da P2 declara o alcance do que mediu | escrita plantada no lar do CLI: invisivel, e nomeada no recibo |
| `~/.codex/config.toml` E lido e auditado | sonda por plantio, com controle negativo e positivo |
| Os seis guardas desta missao prendem | seis mutantes, 90/3/2/3/5/6 vermelhos |

### 7.2 NAO estabelecido — e nao se presume

- **Nada foi certificado.** Esta e missao de correcao; os tres achados
  que ela tocou (`P1A4-1`, `P1A4-3`, `P1A4-6`) so fecham quando um
  **revisor independente** disser que fecharam. O veredito vigente
  continua sendo **REPROVADO**;
- **o criterio recalibrado nao muda nada do que ja foi medido.** A
  P1-A.4 continua com nove fechados, tres abertos e seis novos; o que
  muda e quando a trilha para;
- **o mecanismo de lock continua cooperativo.** `git commit` nao consulta
  lease, e nada aqui alcanca quem escreve sem passar pelo escritor;
- **o lar do CLI continua nao vigiado.** Ele passou a ser **declarado**,
  nao medido;
- **a contencao continua sem responder "quem escreveu?"**, e a porta que
  impeca a sessao de escrever durante a janela **nao existe**;
- **o kimi nao disse nada**, pela quarta vez. Nao se sabe o que um
  segundo revisor acharia de coisa alguma neste repositorio;
- **os quatro achados da P2 seguem abertos**, o A inclusive — a ordem 3
  tocou o objeto do A sem fecha-lo;
- **as nove corridas anteriores a `abc75e8` seguem sem fotografia**;
- **a tese central segue nao medida em token.**

## 8. ATESTADO

**Esta missao corrigiu, e por isso NAO certifica.** A regra do
`CLAUDE.md` e literal: *"nenhuma missao fecha o proprio conserto"*. O que
esta escrito aqui e o que foi feito e o que foi medido; o que fechou,
quem diz e outro.

**O que seria falha, e nao foi feito:** apagar o criterio anterior em vez
de supera-lo; adotar o escritor unico e nao usa-lo na propria missao;
declarar a troca provada pelo teste sem exercer o caminho operacional;
corrigir o `P1A4-6` recontando a tabela em vez de exercer o leitor;
alargar a vigilancia para fazer o `nenhum` do recibo virar verdade, em
vez de declarar o alcance; corrigir o MINOR do ciclo-de-vida de carona
por estar no mesmo arquivo; medir a reversao vermelha do `P1A4-6` no
teste, onde ela nao mede nada; e chamar de disciplina o que foi ausencia
de oportunidade (§5.5).

**O que ficou aquem, e esta escrito:** os seis testes novos da ordem 2
passaram em 0,44 s e isso levantou suspeita legitima de vacuidade — ela
so foi desfeita pelo mutante M2, e nao pela leitura do codigo. Se a
reversao vermelha nao fosse obrigatoria neste repositorio, o verde
rapido teria entrado neste registro como prova.

**Contagem como medida, nunca como meta.** Os numeros deste atestado —
3/2/+9 na conta recalibrada, 90/3/2/3/5/6 nos mutantes, 914+1241 na
suite — sao o que foi medido. Nenhum e alvo a perseguir.

**DECISAO: CONCLUIDO-COM-PULADOS.** As quatro ordens executadas; os
pulados sao os da ordem 4, e estao na §5 com dono, gatilho e remedio.
