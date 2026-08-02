---
id: SSC-DEC-P1A37
titulo: Registro e Decisao da Missao SSC+ P1-A.3.7 — correcao dos doze e trabalho de volume
tipo: decisao-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-02
---

# Registro e Decisao — Missao SSC+ P1-A.3.7

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhuma decisao ou relatorio historico
> foi editado. **Quem corrige nao certifica — nenhum defeito fecha
> aqui.** Este registro descreve o que foi feito e o que ficou aberto;
> ele nao e atestado de aprovacao.

## DECISAO: **CONCLUIDA-COM-PULADOS**

Todo item das quatro fases tem resultado ou bloqueio registrado. Dois
itens ficam com **remedio entregue e gatilho fora desta missao** (MAJOR
#5 e N6), um com **fatia alcancada e resto declarado** (P0-21), e a
**troca do mecanismo do ACHADO 4 fica para decisao atendida do
Fundador**, como o ato mandou.

## SUMARIO — 10 linhas

1. **Doze itens corrigidos, doze commits** — os seis MAJOR nao fechados
   e os seis novos N1 a N6, um por commit, na ordem de dependencia.
2. **Nenhum fecha.** Quem corrige nao certifica; fechar depende de
   revisor independente, e esta missao nao o convocou.
3. **Reversao vermelha medida em TODAS as vinte e nove correcoes**, com
   o numero de testes vermelhos registrado em cada commit.
4. **Contraprova em todas**: nenhuma correcao reprova sempre, e cada
   contraprova segue VERDE sob a propria reversao.
5. **Fase 3 consumida por inteiro**: os 16 pontos da P0 com ramo de
   recusa nao alcancado, um commit cada.
6. **Dois defeitos VIVOS encontrados ao exercer** — `bool` passando por
   `int` em `_tipo` (a seq do EventLog aceitava `True`), e o terceiro
   ramo do `AdaptadorAssinatura` sendo reauditoria e nao bloqueio.
7. **Fase 4 entregue em isolado**: exclusao por repositorio implementada
   e provada entre processos; o mecanismo vivo **nao foi trocado**.
8. **Fase 2**: **13 guardas** tocados sobrevivem a regra dura; os **64
   EXERCE** da varredura ficam **NAO REMEDIDOS**, sem conversao por
   inferencia.
9. Suites no HEAD final: **P0 238/238**, **P1-A 555/555**, prova central
   **18/18**. Custo variavel **0**; zero chamada de provedor.
10. Arvore limpa, sem tag e sem remoto; lease `p1a37-ops`, fence 1, vivo
    do inicio ao fim.

## 1. Identidade e pre-condicoes (medidas na abertura)

| Item | Medido |
|---|---|
| HEAD de abertura | `7d25bc7` |
| Arvore | limpa (`git status --porcelain` vazio) |
| Branch | `master` |
| Tag / remoto | nenhuma / nenhum |
| Lease desta missao | `p1a37-ops`, fence **1**, pid 143836, adquirido **antes da primeira escrita** |
| P0 / P1-A / prova central na abertura | **100/100 · 424/424 · 18/18** (20 eventos) |

`05_p0/saidas/prova_central.json` foi reescrito pela corrida da prova
central (UUIDs novos a cada execucao) e **restaurado** por
`git checkout --` antes da primeira escrita. Ruido conhecido de toda
medicao de pre-condicao, registrado como nas missoes anteriores.

**Condicao operativa declarada.** Enquanto o ACHADO 4 nao for corrigido
NO MECANISMO VIVO, a exclusao mutua entre missoes nao existe; o escritor
unico desta missao foi garantido **por ordem do Fundador**, nunca pelo
mecanismo. A Fase 4 entrega o mecanismo; a troca nao foi feita.

## 2. FASE 1 — os doze

| # | Correcao | Teste que prova (caso que OCORRE) | Reversao vermelha | O que o teste NAO cobre | Commit |
|---|---|---|---|---|---|
| **N2** | fonte de config nao lida deixa de valer por limpa; marcador no VALOR + `auditar_config` fail-closed | `test_falha_fechada_p1a37.py` — `classificar_frota` SEM `config_de`, com `~` redirecionado e guarda de redirecionamento antes de qualquer assercao | `nao_lida` devolvendo `{}` => **12 falhas + 1 erro** em 12 | nao exerce CLI algum; nao prova que `FONTES` nomeie as fontes reais; `PermissionError` encenado por substituicao de `open` | `801868e` |
| **MAJOR #1** | config do grok em SQLite alcancada, por copia do banco + `-wal`/`-shm` | `test_grok_sqlite_p1a37.py` — SQLite REAL em modo WAL, escrita deixada no WAL, `classificar_frota` sem injecao | leitor ignorando `.db` no diretorio => **5 falhas + 4 erros** em 12 | nao prova que o grok GRAVE top-up em SQLite nem em que tabela; nao cobre config fora de `~/.grok/`, formato embutido que nao seja JSON, banco cifrado | `f761f61` |
| **MAJOR #2** | zero de franquia decidido pelo VALOR parseado, nao por prefixo textual | `test_quota_numerica_p1a37.py` — `_quota_de` da producao e `executar_preflight` fim a fim, com a grafia entrando pelo sensor | `_NUMERO` de volta ao texto antigo => **11 falhas** em 9 | as grafias seguem AUTORAIS (achado B / `P1A-58` NAO fecha); `%`-format e separador de milhar nao cobertos | `bf20598` |
| **MAJOR #3** | atribuicao separada da deteccao; `locks/` deixa de ser cego; cobertura alem de `RAIZ`; protocolo unico `Vigilancia` nos quatro runners | `test_contencao_atribuicao_p1a37.py` — `revisao_p1a31.main()` real com reviewer falso plantando lease em `locks/` | (A) `locks` excluido => **5 falhas**; (B) sem vigilancia fora do repo => **1 falha + 1 erro**, em 13 | a atribuicao e por CONVENCAO DE CAMINHO, nao prova de autoria; a cobertura fora do repo alcanca so as fontes de config declaradas | `2f8b451` |
| **N3** | rotulo deixa de afirmar alcance total; construido a partir dos objetos do mecanismo | `test_rotulo_contencao_p1a37.py` — VALOR de `enforcement_kimi()` (campo gravado em toda evidencia), e mudanca da cobertura muda o rotulo | rotulo antigo restaurado => **13 falhas** em 8 | nao prova que o alcance declarado seja SUFICIENTE; a lista de palavras de alcance total e enumerada | `f2c612b` |
| **MAJOR #4** | reverificacao do escritor com o fence da abertura, ANTES de persistir, em `revisao_p1a2.main` | `test_persistencia_lock_p1a37.py` — `main()` real, reviewer troca o fence na janela; a assercao e **nenhum arquivo gravado** | linha removida => **3 falhas + 1 erro** em 6 | varredura ESTRUTURAL (AST) para tres dos cinco runners; substituicao de titular encenada gravando o `.fence`, nao disputando o lock | `da582b0` |
| **N4** | `_redigir` em `dir_descartavel` e no `json.dumps` integral; varredura dos cinco call-sites | `test_redacao_call_sites_p1a37.py` — `main()` real, descartavel REAL, varredura do ARQUIVO gravado; e medicao de que o temp carrega o usuario | dois pontos revertidos => **4 falhas** em 7 | varredura estrutural para quatro runners; redacao cobre usuario e caminho local declarado, nao nome de maquina/IP/e-mail | `f0d5eb7` |
| **MAJOR #5** | gerador embute o proprio fonte com o SHA-256 ao lado (`autoinclusao` + `pacote_p1a37.py`) | `test_pacote_autoinclusao_p1a37.py` — `montar_pacote` contra commits REAIS; ancoragem reprovada com arvore mutada | secao do gerador removida => **2 falhas + 1 erro** em 10 | nenhum pacote e ENVIADO; `pacote_p1a33/36` NAO sao corrigidos (hashes publicados); determinismo medido na mesma estacao | `8c58264` |
| **N6** | pedir julgamento sem carregar o objeto vira PARADA, antes de a saida existir | `test_pedido_de_julgamento_p1a37.py` — `main()` NAO CRIA o arquivo com pacote defeituoso; estado dos geradores do acervo medido | (A) portao fora de `main` => **1 falha**; (B) detector cego => **5 falhas**, em 11 | deteccao por linha e vocabulario enumerado de verbos; `pacote_p1a36` segue com o defeito, DE PROPOSITO | `87854f5` |
| **MAJOR #6** | metade (A) do sentinela passa a ter a raiz do REPOSITORIO; maquinaria extraida para poder ser exercida contra violador | `test_sentinela_antip2_p1a37.py` — a MESMA `varrer` na arvore real e em arvores sinteticas com o consumidor plantado | metade (A) de volta a `06_p1a` => **2 falhas** em 12 | alias/import/concatenacao ficam para N5; analise estatica por arquivo, sem dataflow; `PRIMITIVAS_EXECUCAO` enumerada | `7093852` |
| **N5** | sentinela resolve concatenacao, constante importada e propagacao booleana — **ou NEGA** quando nao resolve | `test_sentinela_n5_p1a37.py` — 19 casos por `varrer`; e medicao de que `RESULTADOS` importado em `07_p1b` e de fato resolvido | (A) sem dobra => **4**; (B) sem import => **8**; (C) sem ponto fixo => **3**, em 19 | `%`/`.format`/`join` nao sao dobrados; import dinamico nao e seguido nem negado; resolucao por sufixo, nao por `sys.path` | `1fc8cbd` |
| **N1** | exclusao por REPOSITORIO + `liberar()` que expira o lease concedido — **em isolado** | `test_escritor_repositorio_p1a37.py` — dois NOMES diferentes, entre PROCESSOS reais; manifesto identico antes/depois da tentativa falha | (A) lock por nome => **4**; (B) `liberar` sem expirar => **2**, em 12 | mecanismo COOPERATIVO; sem disputa simultanea; manifesto usa TAMANHO para o `.lock` travado | `7fd77c4` |

### 2.1 A ordem seguida, e por que ela nao e a ordem da tabela do §9.4

O ato manda corrigir "na ordem de dependencia do §9.4". Em dois pares a
dependencia REAL inverte a ordem de listagem, e a inversao esta
declarada aqui em vez de silenciosa:

- **N2 antes do MAJOR #1**: o remedio do MAJOR #1 e *"alcancar o SQLite,
  **ou** devolver INDETERMINADO em vez de `{}`"*, e a segunda metade E a
  maquinaria do N2. Construir o marcador primeiro evitou que o MAJOR #1
  nascesse com um marcador que nao fazia nada;
- **MAJOR #3 antes do N3**: o rotulo do N3 e construido a partir dos
  objetos do mecanismo, e o mecanismo e o MAJOR #3. Fixar o rotulo antes
  teria exigido reescreve-lo em seguida.

Os pares 5/N6 e 6/N5 seguiram a ordem da tabela.

## 3. FASE 2 — reclassificacao sob a regra dura

**A regra dura**: `EXERCE` exige exercer **o caso que ocorre em
operacao**, nao alcance de linha.

### 3.1 Os guardas tocados nesta missao, reclassificados

| Guarda (ponto da varredura, quando ha) | Classe antes | Classe agora | Por que |
|---|---|---|---|
| `leitores_config` — fonte nao lida (novo eixo) | inexistente | **EXERCE** | `classificar_frota` sem `config_de`, binding de operacao |
| `P1A-18` `_config_persistida` (grok) | **INALCANCAVEL** | **EXERCE** | SQLite real com WAL; o caminho deixou de ser inalcancavel |
| `P1A-17` `classificar_frota` | **AFIRMA** | **EXERCE** | os testes deixaram de injetar `config_de` |
| `P1A-58` `_ZERO`/`_RX_QUOTA` | **INDETERMINADO** | **INDETERMINADO** | o eixo mudou (valor, nao texto), mas 9 das 11 formas seguem autorais — **nao se converte** |
| `contencao.manifesto`/`mutacoes` (G-E) | **EXERCE** | **EXERCE** | agora tambem com atribuicao, e com fim a fim que reprova a corrida |
| `contencao.enforcement_kimi` (rotulo) | **AFIRMA** (parcial) | **EXERCE** | o VALOR do rotulo e conferido contra os objetos do mecanismo |
| `P1A-08` `revisao_p1a2._verificar_lock` | **SEM-TESTE** | **EXERCE** | `main()` real, com a assercao de que nada foi gravado |
| `P1A-33` `revisao_p1a2` redacao | **SEM-TESTE** | **EXERCE** | arquivo gravado varrido, com descartavel real |
| Sentinela anti-P2 (G-D) | **EXERCE** | **EXERCE** | e agora com controle positivo, que nao existia |
| `P0-01` `canonico` | **SEM-TESTE** | **EXERCE** | |
| `P0-03` `ler_arquivo_contido` | **SEM-TESTE** | **EXERCE** (parcial) | um dos tres ramos e ENCENADO (`os.stat`) |
| `P0-07` `Evento.validate` | **SEM-TESTE** | **EXERCE** | |
| `P0-08` `FleetEntry.validate` | **SEM-TESTE** | **EXERCE** | |
| `P0-13` `_tipo` | **SEM-TESTE** | **EXERCE** | e com defeito vivo corrigido |
| `P0-18` `Juiz1` | **SEM-TESTE** | **EXERCE** | fluxo real ate `aguardando-validacao` |
| `P0-20` `ControlPlane` | **SEM-TESTE** | **EXERCE** | |
| `P0-02` `CAS` | **EXERCE** (2 de 7) | **EXERCE** | symlink segue fora, e declarado |
| `P0-05` `Catalogo` | **EXERCE** (1 de 4) | **EXERCE** | |
| `P0-15` `EventLog` | **EXERCE** (5 de 10) | **EXERCE** | |
| `P0-16` `AdaptadorAssinatura` | **EXERCE** (2 de 3) | **EXERCE** (parcial) | o terceiro ramo e reauditoria, exercido por regressao ENCENADA |
| `P0-17` `Frota` | **EXERCE** (1 de 2) | **EXERCE** | |
| `P0-19` `Juiz2` | **EXERCE** (1 de 2) | **EXERCE** | |
| `P0-21` `SessionKernel` | **EXERCE** (16 de 53) | **PARCIAL** | quatro familias alcancadas; o resto declarado aberto |
| `P0-25` `TaskRouter` | **EXERCE** (3 de 8) | **EXERCE** | |
| `P0-26` `LockSessao` | **EXERCE** (2 de 4) | **EXERCE** | e a medicao do ACHADO 4 vive no proprio arquivo |
| `escritor_repositorio` (novo) | inexistente | **EXERCE, FORA DE USO** | provado entre processos, e nao ligado ao acervo |

**Saldo:** **26 guardas tocados**. Sobrevivem a regra dura como
`EXERCE` pleno **21**; como `EXERCE` **parcial e declarado** **3**
(`P0-03`, `P0-16`, `P0-21`); permanece `INDETERMINADO` **1**
(`P1A-58`); e **1** e `EXERCE` mas **fora de uso** por ordem
(`escritor_repositorio`).

### 3.2 O que NAO foi remedido, e nao se converte

Os **64 `EXERCE`** da varredura da P1-A.3.5 **NAO foram remedidos sob a
regra nova**. Deles, os que esta missao tocou estao na tabela acima; **o
restante permanece NAO REMEDIDO SOB A REGRA NOVA**, e nenhum foi
convertido por inferencia.

Isto e afirmacao deliberadamente fraca. O achado N1 mostrou o preco de
converter por inferencia: um guarda classificado `EXERCE` por alcance de
linha era, na verdade, um guarda que exercitava o unico caso que
funciona. Reclassificar 64 pontos sem remedir repetiria exatamente esse
erro — com o agravante de que desta vez ele estaria por escrito.

## 4. FASE 3 — os 16 pontos da P0

Todos os dezesseis, um commit cada, na ordem em que foram feitos:
`P0-01` `5cbec59`, `P0-03` `e8b1227`, `P0-13` `684682c`, `P0-07`
`d5712d6`, `P0-08` `7d6b47a`, `P0-18` `c07b9be`, `P0-20` `aac4045`,
`P0-02` `bbcdc39`, `P0-05` `ce5e2a2`, `P0-17` `a4eb4cb`, `P0-16`
`57b4415`, `P0-19` `f0580a8`, `P0-26` `3bd16eb`, `P0-15` `c8a2119`,
`P0-25` `bdfca5d`, `P0-21` `2c64c1c`.

### 4.1 Dois defeitos VIVOS, encontrados ao exercer e nao ao ler

**1. `bool` passava por `int` em `contratos._tipo`** (`684682c`).
`isinstance(True, int)` e verdadeiro em Python, de modo que
`Evento(seq=True)` atravessava a validacao e virava **seq 1** no
EventLog. A seq e a **autoridade de ordem** da P0 — o relogio nao e —,
e dois eventos podiam ocupar a mesma posicao: a cadeia deixava de ser
total. O mesmo valia para `variable_cost=True`, que passaria por custo 1
sob uma politica cujo teto e ZERO. Corrigido no ponto UNICO, `_tipo`, e
nao em cada `validate()` — que seria o mecanismo de copia dos achados 7,
10 e 14. E a familia do MAJOR #3 encontrada na P0: o guarda **afirmava**
verificar tipo e nao verificava.

**2. O terceiro ramo do `AdaptadorAssinatura` e reauditoria, nao
bloqueio** (`57b4415`). `ambiente_sanitizado` roda na linha ANTERIOR e
ja removeu a chave, de modo que `if any(k in self.env ...)` nunca
dispara em operacao. Nao e defeito — e reauditoria do proprio
sanitizador, o desenho de `capsula.ambiente_capsula`. O que seria
defeito e escrever um teste "provando" bloqueio por chave no ambiente:
afirmaria o que nao ocorre. Os testes fixam o comportamento REAL (a
chave e FILTRADA) e exercem a reauditoria pelo caso que ela existe para
pegar — a regressao do sanitizador, encenada de forma declarada.

### 4.2 Uma medicao contra o proprio guarda

Em `P0-20`, a reversao produziu **UMA** falha em cinco, nao cinco: os
demais casos continuam recusados pela maquina de estados, a jusante.
O guarda do `ControlPlane` e **defesa em profundidade**, e a sua
contribuicao unica e recusar ANTES de o ato humano ser carimbado.
Registrar isso e mais util que exibir cinco vermelhos.

## 5. FASE 4 — ACHADO 4 / N1, e a troca que NAO foi feita

`06_p1a/escritor_repositorio.py` implementa o remedio do §9.4: lock
UNICO do repositorio (`locks/repositorio.lock`, nome nao
parametrizavel) e `liberar()` que EXPIRA o lease concedido.

A prova exigida pelo ato foi entregue com as duas metades: a segunda
sessao, de nome diferente, levanta `LockIndisponivel`, **e** o manifesto
SHA-256 do diretorio de locks e identico antes e depois — *"falhou"* sem
a segunda metade admitiria um mecanismo que escreve e depois desiste. A
prova corre tambem **entre processos reais**.

**A prova cruzada e o que separa medicao de afirmacao**: o mesmo cenario
com o mecanismo vivo (`EscritorP1`) deixa as duas missoes adquirirem, e
o lease do vivo **sobrevive** ao `liberar()`. O ACHADO 4 esta medido no
proprio arquivo que o corrige.

**O mecanismo vivo NAO foi trocado**, e ha um teste varrendo o
repositorio para garantir que ninguem o troque por acidente. A troca e
decisao atendida do Fundador.

## 6. Fronteira, custo e ambiente

| Item | Estado **verificado** |
|---|---|
| Escritas em `E:/LucasIA/Projetos/SSC-Plus` | codigo, teste e registro desta missao; nada fora |
| Escritas fora do repositorio | descartaveis dos testes, no temp da sessao e na pasta ignorada do laboratorio |
| Copia datada irma | **nenhuma criada** — pratica encerrada por decisao do Fundador |
| Store do harness | **nao gravado** |
| **Chamadas de provedor / de modelo** | **0** |
| Custo variavel | **0** |
| Tag, remoto ou push | nenhum |
| Lock tomado a forca | nenhum |
| HKCU / variavel persistente do usuario | **nao tocada** |
| `~/.grok`, `~/.codex`, `~/.claude` | **lidos so por existencia**, nenhum valor impresso ou gravado |

**Incidente registrado.** Uma corrida da suite P1-A foi morta por
timeout do orquestrador enquanto um teste pre-existente
(`test_pacote_p1a33.py`) mantinha `06_p1a/tiers_declarados.json` mutado
para provar a ancoragem. O arquivo ficou sujo e foi restaurado por
`git checkout --`; o guarda que o detectou foi
`test_arquivo_real_parseia_e_cobre_codex_e_kimi`, que ficou vermelho.
Nenhum commit foi feito com a arvore nesse estado. Registrado porque
matar suite no meio de teste que muta a arvore e risco de operacao, nao
defeito do acervo.

## 7. Alcance — o que esta missao estabelece e o que NAO estabelece

### 7.1 Estabelecido — medido

| Fato | Como |
|---|---|
| Cada correcao esta acoplada ao seu guarda | reversao vermelha medida, uma por correcao, com o numero em cada commit |
| Nenhuma correcao reprova sempre | contraprova em cada uma, verde sob a propria reversao |
| Os doze itens foram tocados | doze commits, um por item |
| Os 16 pontos da P0 foram consumidos | dezesseis commits, um por ponto |
| A exclusao por repositorio funciona entre processos | subprocesso real, manifesto identico na falha |
| O mecanismo vivo nao foi trocado | teste que varre o repositorio atras de consumidores |
| Suites no HEAD final | P0 238/238, P1-A 555/555, prova central 18/18 |

### 7.2 NAO estabelecido — e nao se presume

- **Nenhum dos doze fecha.** Quem corrige nao certifica. Fechar depende
  de revisor independente, e esta missao nao o convocou nem podia.
- **MAJOR #5 e N6 tem remedio entregue e gatilho fora daqui.** O gatilho
  e a montagem do proximo pacote, e o dono e a missao que refizer a
  revisao. `pacote_p1a36.py` **continua com o defeito**, de proposito:
  o hash que ele produz esta publicado.
- **`P0-21` nao esta fechado.** Quatro familias alcancadas de um ponto
  com 37 ramos fora; o resto esta nomeado no proprio commit.
- **A troca do mecanismo do ACHADO 4 nao foi feita.**
- **Os 64 `EXERCE` da varredura seguem NAO REMEDIDOS** sob a regra dura.
- **O achado B (`P1A-58`) segue INDETERMINADO**: as grafias de quota
  esgotada continuam autorais.
- **A metade (b) do portao da P1-A.3.6 — dois vereditos — nao foi
  tocada.** Ela nao e materia de missao de correcao.
- **Nada foi certificado, nenhum pacote foi enviado, nenhuma revisao foi
  reaberta, nenhum provedor foi invocado.**

## 8. O que a proxima missao precisa

1. **Revisao independente do estado corrigido**, com **classificacao por
   familia obrigatoria** — sem ela o criterio de parada gravado no
   `CLAUDE.md` da raiz nao pode ser aferido.
2. **Aplicar o criterio de parada**: seis ou mais defeitos novos, ou
   quatro ou mais na familia do MAJOR #3, e a trilha para e volta ao
   Fundador.
3. **Montar o proximo pacote com `pacote_p1a37.py`**, que embute o
   proprio fonte — e assim MAJOR #5 e N6 ganham o objeto que lhes falta.
4. **Decidir a troca do escritor unico** para `escritor_repositorio`.
5. **Missao propria de cobertura da P0** para os 37 ramos restantes do
   `SessionKernel`, com o metodo da P1-A.3.5.

> Vinte e nove correcoes, vinte e nove reversoes vermelhas medidas, e
> zero defeitos fechados. Fechar nao e trabalho de quem corrige.
