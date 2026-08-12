# SSC+ P2 — usar a frota (experimental, sem autoridade)

> Laboratorio experimental. Nada aqui e norma. A P2 foi aberta pelo ato
> soberano de 2026-08-03 ([`00_ato-soberano-p2.md`](00_ato-soberano-p2.md)),
> que abriu a invocacao produtiva dentro da capsula, em modo
> supervisionado. A confirmacao operacional do proprietario em
> **2026-08-11** incluiu **Claude** e **Google Antigravity** na selecao e
> no fallback automaticos; Grok continua fora. **Chamada de API paga
> continua PROIBIDA** — a politica economica nao foi tocada.

## A FRONTEIRA — quando despachar poupa, e quando NAO poupa

Medido na P2.2 em **2026-08-03**, com quatro corridas novas mais a corrida
da P2.1 (`08_p2/evidencias/medicao-p22-*.json`). Esta secao vem antes dos
comandos porque quem chega aqui precisa saber **quando nao usar** — e o
numero bonito do item 1 abaixo veio de uma tarefa de um tipo so.

### O desenho: mesma tarefa, so o turno interno muda

Tres prompts de **forma identica**, mesmo pedido de saida (`no maximo 8
linhas`, duas perguntas), diferindo **somente** no turno interno exigido.
O prompt foi byte a byte igual nos dois canais.

| corrida | turno interno | razao | razao com a MESMA resposta nos dois lados |
|---|---|---|---|
| (a) P2.2 | `execution.py`, 13.778 B | **19,907** | 18,475 *(nao recarimbada — ver [MEDIDAS.md](MEDIDAS.md))* |
| (a) P2.1 | `eventlog.py`, 6.184 B | **8,776** | 8,092 |
| (c) P2.2 #1 | `estados.py`, 2.987 B | **6,737** | 5,512 |
| (c) P2.2 #2 | `estados.py`, 2.987 B (mesmo prompt) | **6,464** | 5,329 |
| (b) P2.2 | **nenhum** | **2,766** | **1,000** |

### A identidade que separa economia de ilusao

A poupanca decompoe, e a decomposicao fecha **em todas as cinco
corridas**:

    poupanca = turno_interno + (resposta_do_alternativo - resposta_da_assinatura)

O primeiro termo e economia: sao bytes que o despachante **nunca ingere**.
O segundo termo **nao vem de despachar** — vem de um canal responder mais
curto que o outro. Ele saiu **597, 783, 811, 837 e 890 B** nas cinco
corridas: praticamente constante e indiferente a classe da tarefa. Nas
tres corridas da P2.2 o codex usou 3 ou 4 das 8 linhas permitidas; o canal
alternativo usou 8. **Qual resposta presta, a proxy nao diz.**

### Onde a tese vale

**Poupa** quando o turno interno e grande diante desse termo de ~800 B —
ler arquivo, varrer diretorio, abrir muitas ferramentas. E o unico regime
em que a poupanca medida e majoritariamente economia: na corrida (a) o
turno interno foi 94% dela.

**A razao acompanha o tamanho do turno interno, e nao a classe.** Os
`8,78x` da P2.1 e os `19,91x` da P2.2 sao a MESMA classe de tarefa com
arquivos diferentes. Citar a razao sem citar o arquivo e citar a escolha
do arquivo.

### Onde a tese NAO vale

**Nao poupa** em pergunta autocontida, sem turno interno. Medindo com a
mesma resposta nos dois lados, a razao da classe (b) e **1,000 exatos** —
poupanca estrutural **zero**. Os `2,766` que o instrumento anuncia sao,
integralmente, os 890 B de diferenca de verbosidade: **890 de 890**. Ha
guarda que prende isso
(`test_sem_turno_interno_e_resposta_IGUAL_a_poupanca_e_ZERO`), para a
frase acima nao ser afirmacao que ninguem exerce.

**Custa MAIS** quando a assinatura responde mais longo que o canal
alternativo responderia — o instrumento diz `MAIS` nesse caso, e tem teste
para isso desde a P2.1. E **custa uma tentativa perdida** pedir capacidade
que puxa o kimi enquanto a franquia dele estiver esgotada (item 2 abaixo):
essa tentativa fica com a assinatura, nao com o despachante, entao a proxy
de fronteira **nao a mostra** ao despachante. A proxy mede a fronteira de
quem despacha, jamais a queima total da frota.

### O que NENHUMA destas corridas estabelece

**Nao ha tendencia estabelecida, em nenhuma das tres classes.** O `n` por
classe, sendo honesto sobre o que conta como repeticao:

| classe | corridas | repeticoes de MESMO prompt |
|---|---|---|
| (a) turno interno pesado | 2 | **0** — arquivos diferentes, tarefas diferentes |
| (b) turno interno nulo | 1 | **0** |
| (c) intermediaria | 2 | **1** |

A unica repeticao real do acervo moveu a razao de **6,737 para 6,464
(-4,1 %)**, com o lado alternativo mantido identico de proposito: a
variacao veio toda do tamanho da resposta da assinatura (438 -> 466 B).
Uma repeticao da **um delta**, nunca uma dispersao — e a P2.1 escreveu
`8,776`, com tres casas, sobre `n = 1`.

**Quantas corridas seriam necessarias, e por que nao ha resposta medida.**
Um `n` justificado sai de uma estimativa de dispersao, e a dispersao so
existe depois das corridas: nenhum numero aqui pode ser deduzido do que
foi medido. O que se pode afirmar sem extrapolar:

1. **2 corridas de mesmo prompt por classe** e o minimo para existir
   qualquer delta — hoje so a classe (c) tem;
2. **5 por classe** e o menor `n` em que existe mediana que um unico
   outlier nao move. E propriedade aritmetica da mediana, **nao** medicao
   deste acervo, e esta escrito como convencao declarada;
3. **um intervalo de confianca continua fora de alcance** ate haver
   variancia estimada, e estima-la exige as corridas — a ordem nao pode
   ser invertida.

E a proxima medicao provavelmente **nao** deve ser repeticao: como a razao
acompanha o tamanho do turno interno, varrer tamanhos de turno interno
mede a fronteira, e repetir o mesmo arquivo mede o ruido da resposta.

## LEIA ANTES DE RODAR — cinco limites que valem hoje

Estao aqui, e nao no rodape, porque quem vem usar a P2 segue os tres
passos abaixo e pode nunca rolar ate o fim. Os cinco sao **medidos**, com
data e evidencia; nenhum e precaucao generica.

### 1. A economia de TOKEN nao esta comparada entre os provedores

Codex, Claude e Kimi nao reportam aqui uma contagem estruturada comparavel.
O Google Antigravity reporta `usage.total_tokens`, agora preservado no
recibo, mas essa metrica isolada nao torna comparaveis os quatro canais.

O que existe e uma **proxy**, que nao e a medicao: `08_p2/medidor.py`
conta a **carga de fronteira** em bytes e caracteres. **Uma** corrida
comparada, em 2026-08-03 (`08_p2/evidencias/medicao-p21-*.json`) — ler o
arquivo `05_p0/ssc_p0/eventlog.py` e resumi-lo em ate 8 linhas:

| | bytes utf-8 |
|---|---|
| o que o despachante pagou ao despachar | **872** |
| o que o outro canal gastaria fazendo a MESMA tarefa sozinho | **7.653** |
| poupanca na fronteira | **6.781** — razao **8,78x** |

A poupanca e, quase inteira, o turno interno: os 6.184 B do arquivo que a
assinatura leu por conta propria e o despachante nao precisou ingerir.

**Nao cite esse 8,78x sozinho.** Byte nao e token; `n = 1`; e a proxy
declara **oito** coisas que nao captura — entre elas raciocinio, contexto
reenviado e cache, que e onde a economia de verdade mora. Os oito viajam
DENTRO da saida de `comparar`, de proposito: o numero nao circula sem os
proprios limites.

A tese central do projeto — despachar para a assinatura poupa token de
outro canal — segue **NAO MEDIDA em token**. O que ha e uma corrida, numa
proxy declarada, apontando na direcao dela.

**Emenda da P2.2 (2026-08-03).** Os `8,78x` acima continuam verdadeiros
sobre a corrida que os produziu, e a P2.2 mediu duas coisas que mudam como
eles se leem: a razao **acompanha o tamanho do arquivo lido** (a mesma
classe de tarefa, com um arquivo de 13.778 B, deu 19,907) e parte da
poupanca **nao vem de despachar**, e sim de um canal responder mais curto
que o outro. Antes de citar qualquer razao daqui, ler
[A FRONTEIRA](#a-fronteira--quando-despachar-poupa-e-quando-nao-poupa),
acima: e la que esta escrito em que tipo de tarefa despachar **nao poupa
nada**. `NAO_CAPTURA` tem hoje **nove** limites, nao oito.

### 2. A indisponibilidade historica do Kimi nao define a frota atual

Medido em **2026-08-03T11:56Z**
(`08_p2/evidencias/execucao-20260803T115622Z.json`): com `--capacidade
volume`, que puxa o kimi primeiro, o kimi devolveu `falha-quota` e a
maquina rerroteou sozinha para o codex, que concluiu. Mesma medicao de
2026-08-03T02:38Z, agora repetida.

Essa continua sendo a evidencia historica: **`kimi -p` nao foi validado
ali num caminho de sucesso**. Ela nao autoriza concluir que a quota atual
esta esgotada: o preflight de 2026-08-11 reavaliou a frota e deve ser a
fonte da decisao corrente.

### 3. Ninguem certificou a P2

Quem construiu nao certifica — regra do `CLAUDE.md` da raiz. A P2.0
escreveu o codigo, os testes e a propria evidencia; a P2.1 escreveu o
medidor e mediu as corridas acima; a P2.2 mediu a fronteira, achou dois
defeitos e fechou os dois; a P2.3 corrigiu o mecanismo do achado A e a
P2.4 pos a receita das medicoes no repositorio — as duas **declararam o
proprio conserto sem fecha-lo**. **Nenhuma revisao independente passou
por nada disso** — nem sobre a P2.0, nem sobre a P2.1, nem sobre a P2.2,
nem sobre a P2.3, nem sobre a P2.4. Nao existe atestado de aprovacao da
P2, e este README nao e um.

### 4. O `read-only` so vale a partir de `abc75e8` — e o passado nao esta atestado

O achado **A** de 2026-08-03
([`99_achados-divergencias-20260803.md`](99_achados-divergencias-20260803.md))
mediu que nada impedia escrita: nenhuma restricao de filesystem chegava
ao CLI, o diretorio de trabalho era herdado do terminal — a **raiz deste
repositorio** — e `efeito_externo: "nenhum"` era gravado **por
declaracao**, sem que nada olhasse o disco.

**CORRIGIDO NO MECANISMO A PARTIR DE `abc75e8`** (missao P2.3, registro em
[`99_registro-p23.md`](99_registro-p23.md)): o codex passa a receber
`--sandbox read-only --cd <descartavel> --skip-git-repo-check
--ephemeral`, o processo filho corre no descartavel, a `Vigilancia` abre
e fecha em volta da invocacao, e o efeito externo do recibo passa a ser
**medido** por manifesto SHA-256 antes e depois.

**O achado A NAO esta fechado.** Quem corrige nao certifica: ele segue
aberto ate uma revisao independente dizer que fechou.

**Sobre as corridas ANTERIORES a `abc75e8`, a resposta honesta e "nao se
sabe".** As nove corridas da P2.0, P2.1 e P2.2 rodaram **sem fotografia
de antes e depois**. Nao ha como afirmar nem negar que alguma tenha
escrito em algum lugar. Esta secao existe para dizer isso, e nao para
sugerir que a correcao alcanca o passado — ela nao alcanca.

**O que continua NAO MEDIDO, mesmo depois da correcao:**

- **o que `codex exec` faz por conta propria.** Mede-se que o CLI aceita
  a flag, valida o valor (`--sandbox read-onlyX` e recusado com a lista
  de valores possiveis) e ecoa `sandbox: read-only` no cabecalho. Que ele
  **recuse** uma escrita pedida pelo modelo exigiria invocacao real com
  credencial — e nenhuma foi feita;
- **a config do codex fora deste repositorio** (`~/.codex/config.toml`).
  Os testes usam `CODEX_HOME` isolado justamente para nao depender dela,
  o que tambem significa que nao medem o efeito dela numa corrida de
  operacao. E, seja qual for, ela vive num arquivo que qualquer processo
  altera: nao e mecanismo que o SSC+ controle;
- **o lado remoto.** A medicao ve DISCO, dentro das raizes vigiadas.
  Escrita que um provedor faca no proprio servico nao aparece em
  fotografia local nenhuma;
- **o kimi nao tem sandbox de filesystem** — o CLI nao oferece a flag
  (`unknown option '--sandbox'`, medido na P1-A.3.4). Ali a protecao e o
  descartavel como diretorio de trabalho mais a `Vigilancia`, e o rotulo
  do proprio codigo diz isso por extenso em vez de afirmar isolamento
  inexistente.

### 5. Os numeros da fronteira REPRODUZEM — e 21 % deles e testemunho

Desde a P2.4 ha comando, e ele roda sem provedor nenhum:

```powershell
python 08_p2/medidor.py --todas
```

Ele refaz as cinco medicoes publicadas a partir de insumos versionados
([`08_p2/receitas/`](receitas/)) e confere contra
`08_p2/evidencias/medicao-*.json`. **30 de 30 campos conferem** —
`8,776`, `19,907`, `2,766`, `6,737`, `6,464` e os residuais `872`, `773`,
`504`, `662`, `690`. Codigo de saida **1** em qualquer divergencia.

**O que voce reproduz, e o que tera de aceitar como testemunho.** Esta e
a parte que importa antes de citar qualquer razao:

| insumo | reproduzivel? | onde |
|---|---|---|
| turno interno (o termo dominante) | **SIM**, nas 4 corridas que tem | arquivo versionado, recontado do disco |
| resposta da assinatura | **SIM em 4 de 5** | campo `saida` de `08_p2/evidencias/execucao-*.json` |
| prompt | **SIM em 1 de 5** | `08_p2/receitas/prompt-p22-c.txt`, recuperado do unico lab sobrevivente |
| resposta do canal alternativo | **NAO**, em nenhuma | nunca foi gravada em lugar nenhum |
| resposta da assinatura da corrida (c) | **NAO** | essa corrida nao tem recibo (ver abaixo) |

No conjunto, **28.057 B sao recontados do repositorio e 7.409 B sao
testemunho** — 79 % recontado. Por classe a diferenca e grande, e o
comando imprime a fracao em toda corrida: a classe (a) tem **89,7 %**
recontado; a classe **(b) tem 17,3 %**, porque sem turno interno os dois
maiores termos dela sao justamente o prompt e a resposta do outro canal,
que ninguem pode recontar. **Citar o `2,766` da classe (b) e citar,
sobretudo, testemunho.**

**Uma das cinco corridas nao tem recibo.** A sessao
`dd4567c703d3497fae7269ebfd5d1ca7` (classe (c), 1a corrida) nao aparece
em `08_p2/evidencias/`: foi ela que caiu no `UnicodeEncodeError` do
console — o attempt deu sucesso, a franquia foi gasta, e o artefato de
registro nunca existiu. A resposta dela e testemunho declarado, e a
receita diz isso em vez de inventar um texto que pesasse 438 B.

**E as corridas continuam sem fotografia de antes e depois** (limite 4):
a receita reproduz os NUMEROS, nunca o que a corrida fez no disco.

Detalhes, incluindo o controle positivo que prova que o comando le mesmo
os insumos: [`99_registro-p24.md`](99_registro-p24.md).

## Abrir e usar sem montar comandos

No Explorer, de duplo clique em `SSC-Plus.cmd`. No PowerShell, o comando
equivalente e uma linha curta:

```powershell
.\SSC-Plus.cmd
```

O menu principal oferece `Analisar projeto`, `Corrigir problema`, `Implementar
funcionalidade` e `Revisar alteracao`. Essas opcoes usam o fluxo controlado
completo: Kimi contextualiza, Codex planeja e propoe, Claude revisa, Google
julga e a suite local testa. Para mudancas, o patch e testado numa copia e
fica pendente; aplicar na arvore real exige um segundo ato com `fluxo_id` e o
token de aprovacao exibido uma unica vez. Detalhes e limites em
[`102_fluxo-controlado-20260811.md`](102_fluxo-controlado-20260811.md).

O lancador segura e renova o lease no proprio processo, reutiliza um preflight
autenticado ainda valido ou produz outro, pede confirmacao explicita se os
tiers venceram e pergunta tarefa/capacidade. Ao sair, expira o lease. O snapshot
read-only do workspace e montado automaticamente; arquivos com padrao de
segredo sao omitidos, e o recibo guarda apenas caminhos, hashes e contagens.

Uso nao interativo continua curto:

```powershell
python .\ssc_plus.py --tarefa "Analise os riscos do SSC Plus"
```

### Fluxo manual avancado

### 1. Segurar o lease e declarar o tier (ato do proprietario, vale 24 h)

O codigo **nunca** infere o tier. Primeiro, num terminal proprio, segure o
lease e deixe o processo aberto:

```powershell
cd H:\SSC-Plus
python 06_p1a\evidencias\renovador_lock.py p2-ops
```

Noutro terminal, e somente se os dois valores forem verdadeiros agora:

```powershell
cd H:\SSC-Plus
$env:SSC_LOCK_SESSAO = "p2-ops"
python 06_p1a\renovar_tiers.py --confirmo-proprietario `
  --codex-tier "ChatGPT Pro 5x" --kimi-tier "Allegretto" `
  --google-tier "Google AI Pro"
```

O comando valida os tiers contra a especificacao, cria backup atomico,
reverifica o mesmo fence e so entao publica a declaracao. Sem a flag de
confirmacao, tier divergente ou lease perdido, nada e renovado. Declaracao
vencida = `P1A-DECLARACAO-EXPIRADA`; isso e o mecanismo funcionando.

### 2. Rodar o preflight sob o mesmo lease

```powershell
$env:SSC_LOCK_SESSAO = "p2-ops"
python 06_p1a\capsula.py python 07_p1b\preflight_atual.py
```

Ele imprime o caminho da evidencia. Guarde-o.

### 3. Despachar a tarefa

```powershell
python 06_p1a\capsula.py python 08_p2\runner_p2.py `
  --preflight 07_p1b\evidencias\preflight-<data>.json `
  --tarefa "o que voce quer feito" `
  --criterio "como saber se ficou bom"
```

| flag | efeito |
|---|---|
| `--tarefa` / `--tarefa-arquivo` | o prompt (um dos dois, nunca os dois); arquivo deve estar contido neste repositorio e ter no maximo 1 MiB |
| `--criterio` | criterio de aceite, **CONGELADO** na WorkUnit |
| `--capacidade` | preferencia de rota: implementacao/operacao → Codex; arquitetura/specs/revisao profunda → Claude; volume/contexto extenso/engenharia reversa → Kimi; multimodal/julgamento transversal → Google |
| `--papel` | `autor` (padrao), `revisor`, `juiz` |
| `--timeout` | teto de parede por invocacao (padrao 900 s) |
| `--validade-h` | pode estreitar a janela para 1..24 h; valores acima de 24 h sao recusados |

### Divisao de trabalho da frota ativa

Os papeis nao sao cargos fixos por LLM. `--papel autor|revisor|juiz` e um
eixo separado da capacidade: os quatro provedores ativos podem exercer os tres
papeis. Em trabalho critico, revisor ou juiz precisa usar provedor **e** modelo
distintos dos usados pelo autor.

| provedor ativo | modelo descoberto no preflight | preferencia de capacidade | uso recomendado |
|---|---|---|---|
| Codex (`ChatGPT Pro 5x`) | `gpt-5.6-sol` | `implementacao`, `operacao-repo` | mudancas de codigo, testes e operacao do repositorio |
| Claude (`Claude Max 5x`) | `claude-fable-5[1m]` | `arquitetura`, `specs`, `revisao-profunda` | arquitetura, especificacoes e revisao independente profunda |
| Kimi (`Allegretto`) | `kimi-code/k3` | `volume`, `contexto-extenso`, `engenharia-reversa` | leitura ampla, inventario, rastreamento entre muitos arquivos e segunda leitura independente |
| Google (`Google AI Pro`) | `gemini-3.1-pro-high` | `multimodal`, `julgamento-transversal` | inspecao multimodal e julgamento cruzado entre artefatos |

Sem `--capacidade`, a ordem medida do preflight prevalece e Codex e tentado
primeiro. Pedir uma capacidade reordena a fila; nao reserva o provedor. Se a
primeira assinatura falhar por quota, o SSC+ cria nova decisao para a proxima.
Para mudanca critica, uma divisao inicial util e Codex como autor, Claude como
revisor e Google como juiz; Kimi assume a leitura extensa. A independencia
continua obrigatoria: revisor/juiz nao reutilizam provedor e modelo do autor.

## O que acontece sozinho

- **quota esgotada** num provedor → nova `RoutingDecision` para o outro,
  dentro do envelope, com a linhagem preservada. Sem assinatura capaz =
  `STOP_WAIT_RESET`. **Nunca** migra para API paga;
- **falha transitoria** → retry com backoff, no maximo 3, e so sob IR-1
  (idempotency key ou efeito comprovadamente nao aplicado);
- **timeout** → `indeterminado`, escalonamento, **sem** retry automatico:
  uma tarefa que talvez tenha rodado nao roda de novo por conta propria;
- **preflight velho** → PARADA. Veredito de ontem nao autoriza gasto de
  hoje.

Cada corrida grava primeiro, de forma atomica, um recibo redigido em
`08_p2/evidencias/`. O recibo contem apenas tamanho e SHA-256 da resposta,
nunca o texto. O laboratorio proprio em `08_p2/saidas/labs/` fica fora do
Git e carrega o CAS bruto; diretorios descartaveis de subprocesso sao
removidos depois da medicao. Preflight antigo ou editado e recusado: o
produtor o assina com chave HMAC local em `locks/`, e o consumidor valida
assinatura e schema fechado antes de confiar nos campos.

## Limites que voce precisa saber antes de confiar

1. **Claude e Google entram; Grok nao.** Os dois primeiros exigem login de
   assinatura, quota/canal aceitos e modelo exato observado. Grok permanece
   `SUPERVISED`, sem rota automatica;
2. **`executor_observado` e sempre `None`.** O CLI nao ecoa qual modelo
   serviu a chamada, entao o guarda de divergencia da P0 (0.2.1-9) **nao
   dispara** para a P2. Voce sabe qual modelo foi *resolvido*, nao qual
   respondeu;
3. **token nao e comparavel entre canais.** Google informa
   `usage.total_tokens`; os demais continuam sem telemetria equivalente. A
   proxy de bytes em `08_p2/medidor.py` mantem seus limites declarados;
4. **o contexto e seletivo, nao integral.** O snapshot tem teto de 384 KiB,
   prioriza codigo central e omite binarios, evidencias, labs, arquivos grandes
   e qualquer arquivo recusado pela politica de segredos. O recibo declara
   inclusoes e exclusoes, mas nao persiste o conteudo;
5. **read-only.** O envelope nasce `pode_escrever: False`. A P2 responde;
   nao aplica patch;
6. **a franquia do Kimi estava esgotada nas medicoes de 2026-08-03**;
   isso e historico, nao substitui o preflight atual;
7. **quem construiu nao certificou.** Nenhuma revisao independente foi
   feita sobre a P2 — nem sobre a P2.0, nem sobre a P2.1. Ver o item 3
   do bloco no topo;
8. **dois guardas da P2.0 estavam pela metade**, medido pela reversao
   vermelha da P2.1: o teto de custo zero podia ser AFROUXADO sem
   vermelho nenhum, e a correcao de codificacao prendia a primitiva
   `decodificar` mas nao o ponto de chamada `sensor_subprocess`. Os dois
   foram fechados com teste, sem tocar producao. O que isso ensina sobre
   o resto do acervo — quantos outros guardas estao na mesma condicao —
   **nao foi medido**;
9. **o relato do runner ja perdeu uma evidencia, e a ORDEM entre relatar e
   persistir continua sem guarda.** Medido na P2.2: a resposta do codex
   trouxe `→`, o console da estacao codifica cp1252, e `print` derrubou o
   processo ANTES do bloco que persiste a evidencia — com o attempt em
   **sucesso** e a franquia gasta. O relato foi corrigido e nao pode mais
   derrubar a corrida por codificacao; mas nada prova que a evidencia seja
   gravada se outra coisa levantar antes da persistencia, porque exercitar
   isso exige `main` com lease vivo e invocacao real. Enquanto isso valer,
   **corrida cujo artefato nao apareceu em `08_p2/evidencias/` ainda pode
   ter ocorrido** — a cadeia em `08_p2/saidas/labs/` e quem sabe.
