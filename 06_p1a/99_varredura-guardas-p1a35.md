---
id: SSC-VAR-P1A35
titulo: Varredura de guardas do SSC+ — enumeracao, classificacao e alcance medido
tipo: registro-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-01
---

# Varredura de guardas — SSC+ P1-A.3.5, Fase 1

> Laboratorio experimental. Nada aqui e norma. Registro **aditivo**:
> nenhum relatorio historico foi editado. Lease `p1a35-ops` fence **1**,
> adquirido antes da primeira escrita.

## 0. Estado medido na abertura

| Item | Medido |
|---|---|
| HEAD | `6a8c843be75f13507b969c9aa28e91beaf9997db` |
| Arvore | limpa |
| Tag / remoto | nenhuma / nenhum |
| Sessao viva | **nenhuma** — 12 leases, todos vencidos, nenhum PID titular vivo, nenhum `renovador_lock.py` em execucao |
| P0 | **100/100 OK** |
| P1-A | **346/346 OK** |
| Prova central | **18/18 OK** (20 eventos) |

O JSON da prova central carrega UUID por corrida; o arquivo versionado
foi restaurado apos a reexecucao e a arvore voltou limpa (precedente da
§5 da `99_decisao-p1a33.md`).

**Condicao operativa declarada, conforme a §7 da
`99_achados-governanca-20260731.md`:** enquanto o ACHADO 4 nao for
corrigido, a exclusao mutua entre missoes **nao existe**; o escritor
unico desta missao e garantido **por ordem do Fundador**, nunca pelo
mecanismo. O lease `p1a35-ops` nao impediria uma segunda sessao com
outro nome de escrever ao mesmo tempo.

## 1. Metodo de enumeracao — declarado, e por que e exaustivo

**O conjunto de arquivos nao e redigido a mao.** Ele vem de
`git ls-files '*.py'` — **66** arquivos, **66** parseados por `ast`,
**zero ilegiveis**. Lista a mao omite em silencio; o indice do Git nao
tem como omitir um arquivo rastreado.

**A unidade e o ponto de imposicao, nao o `raise`.** Varios `raise` que
impoem a mesma propriedade dentro da mesma funcao sao um guarda so.

**Guarda e ponto que afirma propriedade** de seguranca, politica,
economia, isolamento, escritor unico, proveniencia ou contencao. Neste
acervo, um ponto desses se manifesta de cinco formas — e sao cinco
colheitas mecanicas distintas, porque **uma so nao alcanca as outras
quatro**:

| Colheita | Regra mecanica | O que acharia sozinha |
|---|---|---|
| **G-A recusa** | todo `ast.Raise` em producao; toda construcao de subclasse de `ErroPreflight`; todo `return <int≠0>` em `main()` | so quem **recusa** |
| **G-B filtragem/redacao** | funcao de producao que **define ou chama** primitiva de sanitizacao (`_nome_payg`, `ambiente_sanitizado`, `ambiente_capsula`, `verificar_capsula`) ou que **redige** (`replace(... "<USUARIO>")`) | so quem **transforma** |
| **G-C construcao restrita** | tabela `COMANDOS` e `argv_*` de producao: a restricao **e** o comando montado | so quem **constroi** |
| **G-D residente em teste** | classe/metodo de teste que **e** a imposicao, sem ponto de producao correspondente | so quem vive **no teste** |
| **G-E deteccao** | funcao de producao que computa conjunto de violacao sem recusar nem filtrar (`manifesto`/`mutacoes`, `_quota_de`) | so quem **acusa** |

A G-B foi acrescentada porque a G-A sozinha **perdia** `ambiente_sanitizado`
e as nove redacoes: elas nao levantam nada. A G-C, porque `argv_kimi` nao
recusa nem filtra — restringe montando. A G-D, porque
`ZeroPiiNosArtefatos` nao tem contraparte em producao. A G-E, porque
`manifesto`/`mutacoes` nem recusa, nem filtra, nem constroi: devolve a
lista do que mudou, e e ela que reprova a corrida. Declarar so a primeira
teria produzido uma varredura que se diz completa e nao e.

**Uma sexta colheita foi tentada e DELIBERADAMENTE colapsada, com o
motivo.** Constantes de politica em modulo (`POLITICA_ECONOMICA`,
`_ENDPOINTS_PAYG`, `CHAVES_PAYG_CONHECIDAS`, `FLAGS_DE_AUTO_APROVACAO`,
`EXCLUIDOS_DO_MANIFESTO`…) sao guarda no sentido de **declarar a regra**.
Enumera-las como pontos proprios inflaria o inventario sem acrescentar
uma imposicao distinta: cada uma e o **dado** de um ponto ja contado —
`_ENDPOINTS_PAYG` e o dado de `auditar_config`, `POLITICA_ECONOMICA` e o
de `auditar_status`, `FLAGS_DE_AUTO_APROVACAO` e o de `argv_kimi`.
Colapsadas por decisao declarada, nunca por esquecimento.

**Dois erros de dupla contagem foram encontrados e corrigidos na propria
montagem da tabela**, e ficam registrados porque a tabela e a prova: o
portao de plano/sombra estava listado a parte de `executar_preflight`,
que o contem, e a auditoria de endpoint a parte de `auditar_config`, que
a contem. Os dois foram fundidos no ponto que os hospeda.

**Prestacao de contas do residuo — o que impede a omissao silenciosa.**
As **167** recusas colhidas na G-A foram particionadas por regra
declarada, e cada uma caiu em exatamente um balde:

| Balde | Qtd | Regra |
|---|---|---|
| GUARDA | **143** | tipo de politica, ou `SystemExit` dentro de funcao nomeada |
| CONVENCAO_DE_SAIDA | 11 | `raise SystemExit(main())` no rodape do modulo — devolve rc, nao afirma nada |
| ERRO_DE_ARGUMENTO | 7 | `ValueError`/`TypeError`/`AssertionError` que nao afirmam nenhuma das sete familias |
| REPROPAGACAO | 4 | `raise` nu dentro de `except` |
| METODO_ABSTRATO | 2 | `NotImplementedError` de classe base |
| **RESIDUO** | **0** | — |

O balde `RESIDUO` terminar **vazio** e a prova de que nada foi
descartado por conveniencia. Uma unica excecao ao criterio por tipo esta
**enumerada, nao inferida**: `06_p1a/capsula.py:95` levanta `TypeError`
e **e** guarda — proibir `argv` em `str` e o que sustenta `shell=False`.

**Contraprova do lado do teste.** A colheita achou **446** metodos
`test_*`; as duas suites executam **100 + 346 = 446**. Os dois numeros
fecham: nenhum metodo descoberto deixa de rodar, e nenhum teste roda sem
ter sido descoberto.

### 1.1 O alcance e medido, nao inferido

Toda classificacao abaixo que diga "o teste nao alcanca" e **medicao**:
as duas suites correram sob `sys.monitoring` (evento LINE), registrando
o conjunto de `(arquivo, linha)` efetivamente executado — **5.205**
linhas na P0 e **5.627** na P1-A, com 100 e 346 testes verdes sob
instrumentacao.

O instrumento foi corrigido durante a propria varredura: na primeira
versao o monitor entrava **depois** da descoberta, e os `def` de modulos
importados no topo apareciam como nao alcancados. Com o monitor entrando
antes, as contagens de linha subiram (4.247 → 5.205 e 4.051 → 5.627) e
**nenhuma conclusao mudou** — o que torna o resultado robusto ao vies que
o produzia.

Os instrumentos rodaram **de fora do repositorio** e nao foram
acrescentados ao acervo, por uma razao que e o proprio objeto desta
missao: um `.py` novo sem teste seria mais um caso do achado C.

## 2. Inventario — 86 guardas

A tabela integral, um guarda por linha com ponto, familia, classe e
evidencia, esta no **Anexo A**. As contagens abaixo sao **derivadas
dela**, nunca afirmadas antes: cada numero e o resultado de contar as
linhas do anexo.

| Colheita | Guardas |
|---|---|
| G-A recusa | **45** |
| G-B filtragem e redacao | **19** |
| G-C construcao restrita | **7** |
| G-D residente em teste | **13** |
| G-E deteccao | **2** |
| **Total** | **86** |

| Familia | Guardas |
|---|---|
| politica | 18 |
| contencao | 16 |
| economia | 16 |
| proveniencia | 14 |
| seguranca | 11 |
| escritor unico | 7 |
| isolamento | 4 |
| **Total** | **86** |

### 2.1 Classes — e por que sao cinco, nao quatro

As quatro classes do ato descrevem **a qualidade de um teste que
existe**. Onde nao existe teste nenhum nao ha o que classificar, e
chamar isso de INDETERMINADO **superestimaria** o estado: indeterminado e
o que falta evidencia para decidir, e aqui a evidencia e conclusiva e
negativa. Uso portanto um quinto rotulo, **SEM-TESTE**, que o proprio
acervo ja reconhece como classe distinta (§3.3 da `99_decisao-p1a34.md`:
*"nao e teste fraco, e ausencia de teste"*). Nenhuma conversao por
inferencia em nenhuma direcao.

| Classe | Qtd | Leitura |
|---|---|---|
| EXERCE | **49** | invoca a interface real ou varre o artefato real |
| SEM-TESTE | **26** | nenhum teste alcanca o ponto — **quase um terco do acervo** |
| AFIRMA | **9** | verifica um modelo, nao a coisa |
| INALCANCAVEL | **1** | o teste percorre caminho que a operacao nunca alcanca |
| INDETERMINADO | **1** | permanece; nao se converte |
| **Total** | **86** | |

O numero que dita esta missao nao e o de AFIRMA — e o de **SEM-TESTE**:
26 dos 86. A auditoria da P1-A.3.4 olhou os seis MAJOR e encontrou um
`AFIRMA`; olhando o acervo inteiro, a classe dominante de defeito nao e
guarda testado fraco, e **guarda nao testado**.

## 3. Os guardas, por classe, com evidencia apontavel

### 3.1 EXERCE (49)

**P0 — 20 pontos com todas as linhas de recusa alcancadas.** A interface
real da P0 e a API em processo, e as suites a dirigem: `eventlog` (5 de
10 ramos), `cas` (2 de 7), `router` (3 de 8), `writelock` (2 de 4),
`kernel::SessionKernel` (16 de 53), `estados::transitar`, `policy`,
`frota`, `judge::Juiz2`, `catalogo`, `contratos`. Os testes **mutam
bytes reais** de log e checkpoint (`test_eventlog.py:58`,
`test_crash.py:102`) e criam **junction real** no sistema de arquivos
(`test_seguranca.py:81`) — nao modelos.

`PolicyGateway.verificar_orcamento` (`policy.py:105`) merece nota: a
busca por nome do tipo `OrcamentoEstourado` nos testes devolve **zero**,
e ainda assim o guarda **e** exercido — `execution.py:81` o chama,
`:83` o captura, e `test_recuperacao.py:226` percorre o caminho inteiro
exigindo escalonamento e zero chamada posterior. Registrado porque e o
contraexemplo da propria heuristica: buscar o nome do tipo teria
produzido um falso achado de ausencia.

**P1-A:**

| Guarda | Ponto | Lastro | Evidencia |
|---|---|---|---|
| PII zero nos artefatos | G-D `test_estabilizacao_p1a1.py:378` | proprio | varre a arvore real de `06_p1a`; ja reprovou o artefato de quem o escrevia |
| Zero segredo nos artefatos | G-D `test_isolamento.py:150` | proprio | varre arquivos reais **e tem controle positivo** (`:170` planta 7 amostras) |
| Varredura nao toca o FS | G-D `test_isolamento.py:129` | proprio | instantaneo SHA-256 real de `06_p1a` antes/depois da frota inteira |
| Sentinela anti-P2 | G-D `test_emendas_p1a3.py:787` | proprio | varre os `.py` **reais** (`:810`) e os parseia com `ast` (`:813`) |
| Ancoragem do pacote no commit | `pacote_p1a31.py:211,214` | `test_correcoes_p1a32.py:518-606` | roda `git cat-file blob` de verdade e **muta o disco** exigindo que o gerador ignore |
| Contencao por manifesto | `contencao.py:90,115` | `:221-262` + `:351-379` | roda `revisao_p1a31.main()` com subprocesso que **escreve mesmo** fora do descartavel e exige `rc == 3` |
| Restricao real do kimi | G-C `contencao.py:131` via `revisao_p1a33.COMANDOS` | `test_cli_real_p1a34.py:128` | **invoca o CLI 0.30.0**; a reversao reprova pela voz do proprio CLI |
| Quota esgotada | `adaptadores.py` `_ZERO`/`_RX_*` | `test_correcoes_p1a32.py:182-210` | importa a regex de producao e a executa; limite em §3.4 |
| Capsula limpa | `capsula.py:65,81,95` | `test_capsula_p1a2.py` | `iniciar_em_capsula` real, com `argv` em `str` recusado |
| Sanitizacao canonica | G-B `economia.py:213`, `:183`, `:197` | `test_economia.py`, `test_estabilizacao_p1a1.py:240-262` | dupla assercao: token local **sanitiza sem bloquear**, credencial de provedor **sanitiza E bloqueia** |
| Lease antes da persistencia | `contencao.py:176,182,184` | `test_correcoes_p1a32.py:400-492` | lease/fence reais em disco + `preflight_capsula.main()` de verdade |
| `locks/` fora do Git | G-D `test_estabilizacao_p1a1.py:371` | proprio | le o `.gitignore` real |
| Espelho da politica P0 | G-D `test_economia.py:23` | proprio | compara com a `POLITICA_ECONOMICA` importada da P0 |
| Sondas so de diagnostico | G-D `test_adaptadores.py:268` | proprio | verbos declarados em `frota_real.ESPECIFICACOES` |
| Cobertura das nove falhas | G-D `test_falhas_obrigatorias.py:422` | proprio | meta-guarda: uma classe por falha, codigo estavel e unico |
| Zero escrita fora da raiz | G-D `05_p0/tests/test_seguranca.py:119` | proprio | `os.walk` real |

### 3.2 AFIRMA (9) — o teste verifica um modelo, nao a coisa

| # | Guarda | Ponto | Por que AFIRMA |
|---|---|---|---|
| A1 | **Escritor unico entre missoes** | `contencao.py:152`, `preflight_capsula.py:73`, `revisao_p1a2.py:57`, `preflight_atual.py:52` | confere um lease que **ele mesmo nomeia**; duas missoes com nomes diferentes trancam arquivos diferentes (ACHADO 4). `test_estabilizacao_p1a1.py:347` usa `"p1-ops"` nos **dois** lados: exercita o unico caso que funciona, nunca o que ocorre em operacao |
| A2 | **Atalho PAYG google/grok** (MAJOR #1) | `preflight_capsula.py:161` | os 7 testes de `AtalhoPaygGoogleGrok` injetam `config_de=` (`:90`); `_config_persistida` tem **zero linha executada** pela suite — medido, nao inferido |
| A3 | **argv da prova minima** | G-C `prova_minima.py:42` (codex, claude, kimi) | `test_isolamento.py:207` mede a **forma da lista**; nenhum CLI e invocado. E a classe exata do MAJOR #3, que so foi corrigida na **outra** tabela `COMANDOS` |
| A4 | **Execucao no descartavel** | `prova_minima.py:81` | `test_isolamento.py:222` casa **substring no fonte** (`"cwd=tmp" in fonte`) — modelo do texto, nao do comportamento |
| A5 | **Preflight e read-only/offline** | G-D `test_isolamento.py:85` | varre o fonte real, porem por **substring proibida**: mede o texto, nao o efeito; e o alcance e so `preflight/*.py` |
| A6 | **Sanitizacao do runner e a canonica** | `prova_minima.py:79` | `test_isolamento.py:230` compara identidade de funcao e ausencia de nomes no fonte |
| A7 | **Sondas do adaptador** | `adaptadores.py:79` | `SensorRealSemProcesso` substitui `subprocess.run`: verifica o modelo do sensor, nunca um processo |
| A8 | **`frota_real.ESPECIFICACOES`** | G-C `frota_real.py:58` | os `comandos` sao descritores; nenhum teste confronta um so deles com o CLI que os executaria |

### 3.3 INALCANCAVEL (1) — o teste percorre caminho que a operacao nunca alcanca

**`test_grok_com_auto_topup_persistido_e_blocked`**
(`test_correcoes_p1a32.py:110-113`; era `:102` antes de a P1-A.3.4
inserir 8 linhas de ressalva no docstring — **o deslocamento e de 8
linhas, e o alvo e o mesmo**).

O teste exige BLOCKED a partir de `{"auto_topup": True}` como config do
grok. `preflight_capsula.py:158` devolve `{}` **incondicionalmente** para
grok. O dicionario contra o qual o teste afirma **nao pode ser produzido
pelo leitor real** — logo o caminho e inalcancavel em operacao.

**Medido nesta missao, e o acervo nunca tinha medido:** o grok **tem**
estado local em `~/.grok/`, mas ele vive em **SQLite** (`grok.db`,
mais `-shm`/`-wal`) e nao ha config JSON/TOML de topo. A coleta de
evidencias da P1-A auditou config de **tres** provedores apenas — codex,
kimi e claude (`coleta-20260730-092436/20_configs.txt`, 21 linhas) —, de
modo que a frase *"nenhuma config parseavel localizada na P1-A"* descreve
**o que nao foi procurado**, e nao o que foi procurado e nao existe.
A diferenca importa: a primeira nao autoriza `return {}` incondicional.

### 3.4 INDETERMINADO (1) — permanece, e nao se converte

| # | Guarda | Por que permanece |
|---|---|---|
| I1 | **Corpus de `ESGOTADAS`** (achado B, `P1A-58`) | 9 das 11 formas sao autorais; resolver exige saida real de CLI com quota esgotada, indisponivel nesta missao. **Nao e defeito — e limite conhecido** |

**Uma segunda indeterminacao existe e NAO vira linha do inventario.**
`test_google_com_endpoint_payg_persistido_e_blocked` injeta `base_url`
como config do google; que `~/.gemini/settings.json` use mesmo essa
chave **nao foi confirmado** (a coleta da P1-A nunca auditou a config do
google — §3.3). Ela nao ganha linha propria porque o ponto de imposicao
que a hospeda, `auditar_config`, ja e uma linha (`P1A-13`), e duplicar
seria a mesma dupla contagem que a §1 corrigiu. Fica registrada aqui, no
corpo, como **indeterminacao declarada de `P1A-17`** — nao se afirma
alcancavel nem inalcancavel. Se a config do google for auditada e a
chave confirmada, ela vira EXERCE; se for outra chave, vira um segundo
INALCANCAVEL ao lado do grok.

### 3.5 SEM-TESTE (26) — nenhuma linha de recusa alcancada por teste algum

**Quatro arquivos de producao com guarda dentro tem ZERO linha
executada pelas duas suites** — nunca sao sequer carregados:

| Arquivo | Guardas dentro |
|---|---|
| `06_p1a/evidencias/pacote_p1a33.py` | 3 portoes de identidade (`:265,268,272`) + redacao (`:223`) + `COMANDOS`-equivalente |
| `06_p1a/evidencias/revisao_p1a2.py` | lease (`:61,64`) + redacao (`:51`) + `COMANDOS` (`:40`) |
| `06_p1a/evidencias/revisao_p1a3.py` | redacao (`:60`) + `COMANDOS` (`:67`) |
| `07_p1b/preflight_atual.py` | lease (`:60,63,66`) + redacao (`:48`) |

`pacote_p1a33.py` e o achado C nomeado pelo ato — **e ele gerou o pacote
`87f41503` que foi a revisao**. Os outros tres sao da mesma classe e
**nao estavam registrados**.

**O portao de tier expirado nunca e exercido.** `revisao_p1a31.py:98,106`
e `revisao_p1a33.py:111,120` param a corrida quando a declaracao de tier
esta invalida ou vencida. Nenhuma das quatro linhas e alcancada. Isto
contradiz uma linha do proprio pacote enviado a revisao: a tabela de
threat review de `pacote_p1a33.py:136` declara *"Tier declarado expirado
… Validade reverificada imediatamente antes de cada chamada; expirado =
PARADA | **verificado nesta missao**"*. Verificado por ato manual, nao
por teste — e ato manual nao protege contra regressao.

**A redacao de PII/caminho nao tem teste — e sao nove copias com tres
forcas diferentes.** Medido: **zero** ocorrencia de `_redigir`,
`USUARIO_CURTO`, `<USUARIO>` ou `CAMINHO-LOCAL` em qualquer arquivo de
teste das duas suites.

| Forca | Redige | Copias |
|---|---|---|
| forte | usuario longo + **forma 8.3** + `E:\LucasIA` + `E:/LucasIA` | `pacote_p1a31.py:161`, `pacote_p1a33.py:223` |
| media | usuario longo + forma 8.3 | `revisao_p1a3.py:60`, `revisao_p1a31.py:52`, `revisao_p1a33.py:61` |
| **fraca** | **somente o usuario longo** | `preflight_capsula.py:234`, `preflight_atual.py:48`, `revisao_p1a2.py:51` |

As tres fracas nao redigem a **forma 8.3** — que e exatamente a forma
que `ZeroPiiNosArtefatos` procura. Hoje nenhum artefato versionado a
carrega (medido: zero arquivos), de modo que **nao ha violacao viva**; o
que ha e um guarda que so pega o caso depois de gravado, em vez de
impedi-lo.

**MAJOR #4 nunca alcancou a P1-B.** `07_p1b/preflight_atual.py:52`
`_verificar_lock_vivo` **nao tem o parametro `fence_esperado`**, e
`main()` o chama **uma unica vez** (`:128`), antes das sondas reais,
gravando em `:160` sem reverificar. E o defeito exato que o MAJOR #4
descreve, intacto na copia da P1-B. A leitura do fence (`:67-69`)
tampouco esta protegida por `try`, de modo que fence ilegivel vira
excecao crua em vez de PARADA tipada.

**P0 — ramos de recusa nunca alcancados.** Medido: `kernel::SessionKernel`
**37 de 53**, `cas::CAS` 5 de 7, `eventlog::EventLog` 5 de 10,
`router::TaskRouter` 5 de 8, `catalogo::Catalogo` 3 de 4,
`writelock::LockSessao` 2 de 4, mais 7 pontos com **nenhuma** linha
alcancada (`canonico::canonico`, `cas::ler_arquivo_contido`,
`contratos::Evento`, `contratos::FleetEntry`, `contratos::_tipo`,
`judge::Juiz1`, `kernel::ControlPlane`).

**Dois ramos fail-closed do lease tambem nao sao alcancados:**
`contencao.py:173` e `preflight_capsula.py:95,104` — os casos de lease
ou fence **ilegivel/ausente**. Os demais ramos dos dois estao cobertos.

## 4. Achados novos desta varredura

Numerados a partir do 7, sem recontar ACHADO 4/4.1 nem MAJOR #1 e os
achados A, B e C, que ja existiam.

| # | Achado | Classe |
|---|---|---|
| **7** | `07_p1b/preflight_atual.py` — MAJOR #4 nunca foi aplicado a esta copia: sem `fence_esperado`, sem reverificacao antes de gravar, fence lido sem `try` | SEM-TESTE + defeito |
| **8** | Achado C alcanca **quatro** arquivos, nao um: `pacote_p1a33.py`, `revisao_p1a2.py`, `revisao_p1a3.py`, `preflight_atual.py` — zero linha executada | SEM-TESTE |
| **9** | O portao de tier expirado (`revisao_p1a31/33`) nunca e exercido, e o pacote enviado a revisao o declara "verificado" | SEM-TESTE |
| **10** | A redacao de PII/caminho tem **9 copias em 3 forcas**, e **nenhuma** tem teste; as 3 fracas omitem a forma 8.3 | SEM-TESTE |
| **11** | `prova_minima.COMANDOS` repete o MAJOR #3: argv afirmado **so pela forma** para codex, claude e kimi | AFIRMA |
| **12** | A coleta da P1-A auditou config de 3 dos 5 provedores; "nenhuma config parseavel" para grok descreve o que **nao foi procurado** | fundamento do MAJOR #1 |
| **13** | A metade (A) do sentinela anti-P2 cobre so `06_p1a`; `07_p1b/preflight_atual.py:172` decide sobre o veredito fora do classificador e **nao e visto** | escopo (ja aberto) |

## 5. Ordem de dependencia declarada para a Fase 2

Os itens 1 a 3 vem do ato. A ordem do item 4 e derivada desta varredura,
por dependencia real e nao por severidade:

1. **MAJOR #1** — leitor real cego para grok + assercao inalcancavel.
2. **Achado C** — teste de `pacote_p1a33.py`.
3. **Achado A** — cobertura real de `_config_persistida`. *Depende do 1:*
   corrigir o leitor antes de cobri-lo evita escrever um teste que fixa
   a cegueira como esperada.
4. **Achado 7** — MAJOR #4 na copia da P1-B. *Independente.*
5. **Achado 10** — redacao. *Depende do 3 apenas por ordem de commit.*
6. **Achado 9** — portao de tier. *Independente.*
7. **Achado 11** — argv da prova minima. **Exige invocar os CLIs reais de
   codex e claude**, o que as RESTRICOES desta missao vedam: registrado
   com a correcao especificada e **PULADO**.
8. **P0, ramos nao alcancados** — 30+ ramos. *Volume incompativel com
   esta missao;* registrado com dono e gatilho.

## 6. Alcance — o que esta varredura estabelece e o que NAO estabelece

**Estabelece.** O conjunto de arquivos e fechado pelo indice do Git; a
particao das 167 recusas tem residuo **zero**; 446 metodos colhidos = 446
testes executados; e o alcance de cada linha de guarda e **medido** sob
`sys.monitoring`, nao inferido. Cada afirmacao de ausencia acima tem
contraexemplo verificavel por terceiro reexecutando as suites sob o mesmo
instrumento.

**Nao estabelece.** Nenhum dos seis MAJOR fecha aqui — fechar e
pronunciamento de revisor independente (§9.3 da `99_decisao-p1a33.md`), e
esta sessao classifica e corrige. Nao se afirma que os guardas
classificados EXERCE estejam corretos: exercer a coisa real e condicao
necessaria, nunca suficiente. O alcance medido diz que uma linha **foi
executada**, nao que a assercao ao redor dela seja forte — a lacuna de
sensibilidade do sentinela (§3.4 da `99_decisao-p1a34.md`) continua sendo
o exemplo vivo disso. Nada se afirma sobre versoes de CLI diferentes das
instaladas.

## Anexo A — os 86 guardas, um por linha

Colheitas: **G-A** recusa · **G-B** filtragem/redacao · **G-C**
construcao restrita · **G-D** residente em teste · **G-E** deteccao.
As contagens da secao 2 sao derivadas desta tabela.
| id | colheita | ponto | familia | classe | evidencia |
|---|---|---|---|---|---|
| P0-01 | G-A | `05_p0/ssc_p0/canonico.py:29 canonico` | proveniencia | **SEM-TESTE** | nenhuma linha de recusa alcancada; nenhum teste nomeia ErroCanonico |
| P0-02 | G-A | `05_p0/ssc_p0/cas.py:112-158 CAS` | contencao | **EXERCE** | 2 de 7 ramos alcancados; test_seguranca.py:81 cria junction real |
| P0-03 | G-A | `05_p0/ssc_p0/cas.py:81,85 ler_arquivo_contido` | contencao | **SEM-TESTE** | nenhuma linha alcancada |
| P0-04 | G-A | `05_p0/ssc_p0/cas.py:52,63 resolver_contido` | contencao | **EXERCE** | todas as linhas alcancadas |
| P0-05 | G-A | `05_p0/ssc_p0/catalogo.py:30-58 Catalogo` | politica | **EXERCE** | 1 de 4 ramos alcancado; resolver() dirigido por router/execution |
| P0-06 | G-A | `05_p0/ssc_p0/contratos.py:104,109 ContratoBase` | politica | **EXERCE** | todas alcancadas |
| P0-07 | G-A | `05_p0/ssc_p0/contratos.py:497,500 Evento` | proveniencia | **SEM-TESTE** | nenhuma alcancada |
| P0-08 | G-A | `05_p0/ssc_p0/contratos.py:314 FleetEntry` | economia | **SEM-TESTE** | nenhuma alcancada |
| P0-09 | G-A | `05_p0/ssc_p0/contratos.py:381,386 RetryEvent` | politica | **EXERCE** | todas alcancadas |
| P0-10 | G-A | `05_p0/ssc_p0/contratos.py:185 WorkUnit` | politica | **EXERCE** | todas alcancadas |
| P0-11 | G-A | `05_p0/ssc_p0/contratos.py:79 _enum` | politica | **EXERCE** | todas alcancadas |
| P0-12 | G-A | `05_p0/ssc_p0/contratos.py:84 _obrigatorio` | politica | **EXERCE** | todas alcancadas |
| P0-13 | G-A | `05_p0/ssc_p0/contratos.py:89 _tipo` | politica | **SEM-TESTE** | nenhuma alcancada |
| P0-14 | G-A | `05_p0/ssc_p0/estados.py:69 transitar` | politica | **EXERCE** | todas alcancadas |
| P0-15 | G-A | `05_p0/ssc_p0/eventlog.py:87-151 EventLog` | proveniencia | **EXERCE** | 5 de 10 ramos; test_eventlog.py:58 muta bytes reais do log |
| P0-16 | G-A | `05_p0/ssc_p0/frota.py:283-293 AdaptadorAssinatura` | economia | **EXERCE** | 2 de 3 ramos alcancados |
| P0-17 | G-A | `05_p0/ssc_p0/frota.py:204,222 Frota` | isolamento | **EXERCE** | 1 de 2 ramos alcancado |
| P0-18 | G-A | `05_p0/ssc_p0/judge.py:61 Juiz1` | politica | **SEM-TESTE** | nenhuma alcancada |
| P0-19 | G-A | `05_p0/ssc_p0/judge.py:98,140 Juiz2` | isolamento | **EXERCE** | 1 de 2 ramos alcancado |
| P0-20 | G-A | `05_p0/ssc_p0/kernel.py:1133 ControlPlane` | politica | **SEM-TESTE** | nenhuma alcancada |
| P0-21 | G-A | `05_p0/ssc_p0/kernel.py:214-963 SessionKernel` | proveniencia | **EXERCE** | 16 de 53 ramos; test_crash.py:102 muta checkpoint real |
| P0-22 | G-A | `05_p0/ssc_p0/kernel.py:56 _validar_id` | politica | **EXERCE** | todas alcancadas |
| P0-23 | G-A | `05_p0/ssc_p0/kernel.py:77 escanear_segredos` | seguranca | **EXERCE** | test_seguranca.py:30-52 |
| P0-24 | G-A | `05_p0/ssc_p0/policy.py:105 PolicyGateway` | economia | **EXERCE** | test_recuperacao.py:226 percorre o teto de custo fim a fim |
| P0-25 | G-A | `05_p0/ssc_p0/router.py:51-197 TaskRouter` | politica | **EXERCE** | 3 de 8 ramos; test_policy.py |
| P0-26 | G-A | `05_p0/ssc_p0/writelock.py:78-108 LockSessao` | escritor-unico | **EXERCE** | 2 de 4 ramos; lock de SO real em tmpdir |
| P0-27 | G-B | `05_p0/ssc_p0/frota.py:76 ambiente_sanitizado` | economia | **EXERCE** | test_frota.py:62,77 assertNotIn sobre o env real do adaptador |
| P0-28 | G-D | `05_p0/tests/test_seguranca.py:119 zero escrita fora da raiz` | contencao | **EXERCE** | os.walk real |
| P1A-01 | G-A | `06_p1a/capsula.py:65 ambiente_capsula` | contencao | **EXERCE** | reauditoria pos-filtragem; todas alcancadas |
| P1A-02 | G-A | `06_p1a/capsula.py:81 exigir_capsula_limpa` | contencao | **EXERCE** | todas alcancadas |
| P1A-03 | G-A | `06_p1a/capsula.py:95 iniciar_em_capsula` | contencao | **EXERCE** | argv em str recusado; shell=False |
| P1A-04 | G-A | `06_p1a/escritor.py:79 EscritorP1.verificar` | escritor-unico | **EXERCE** | test_estabilizacao_p1a1.py:322 lease vencido recusa escrita |
| P1A-05 | G-A | `06_p1a/evidencias/contencao.py:173,176,182,184 verificar_lock` | escritor-unico | **AFIRMA** | 3 de 4 ramos alcancados, mas confere lease que ele mesmo nomeia (ACHADO 4); :173 nunca alcancado |
| P1A-06 | G-A | `06_p1a/evidencias/pacote_p1a31.py:211,214 montar_pacote` | proveniencia | **EXERCE** | git cat-file blob real; disco mutado e ignorado |
| P1A-07 | G-A | `06_p1a/evidencias/pacote_p1a33.py:265,268,272 montar_pacote` | proveniencia | **SEM-TESTE** | arquivo com ZERO linha executada pelas suites (achado C) |
| P1A-08 | G-A | `06_p1a/evidencias/revisao_p1a2.py:61,64 _verificar_lock` | escritor-unico | **SEM-TESTE** | arquivo com ZERO linha executada |
| P1A-09 | G-A | `06_p1a/evidencias/revisao_p1a31.py:98,106 _verificar_tier` | economia | **SEM-TESTE** | nenhuma linha de recusa alcancada |
| P1A-10 | G-A | `06_p1a/evidencias/revisao_p1a33.py:111,120 _verificar_tier` | economia | **SEM-TESTE** | nenhuma linha de recusa alcancada |
| P1A-11 | G-A | `06_p1a/preflight/adaptadores.py:368,376 AdaptadorPreflight` | politica | **EXERCE** | CliIndisponivel tipado; todas alcancadas |
| P1A-12 | G-A | `06_p1a/preflight/economia.py:234 auditar_ambiente` | economia | **EXERCE** | test_economia.py + test_falhas_obrigatorias.py |
| P1A-13 | G-A | `06_p1a/preflight/economia.py:297,303,308 auditar_config` | economia | **EXERCE** | todas alcancadas |
| P1A-14 | G-A | `06_p1a/preflight/economia.py:325-344 auditar_status` | economia | **EXERCE** | todas alcancadas |
| P1A-15 | G-A | `06_p1a/preflight/pipeline.py:179-282 executar_preflight` | economia | **EXERCE** | nove construcoes tipadas, todas alcancadas |
| P1A-16 | G-A | `06_p1a/preflight_capsula.py:95,98,104,106 _verificar_lock_vivo` | escritor-unico | **AFIRMA** | 2 de 4 ramos; mesma propriedade de P1A-05 |
| P1A-17 | G-A | `06_p1a/preflight_capsula.py:161 classificar_frota` | economia | **AFIRMA** | 7 testes injetam config_de; _config_persistida com zero linha executada |
| P1A-18 | G-A | `06_p1a/preflight_capsula.py:140-158 _config_persistida (grok)` | economia | **INALCANCAVEL** | :158 devolve {} incondicional; test_correcoes_p1a32.py:110 afirma BLOCKED contra dict que o leitor nao produz |
| P1A-19 | G-A | `07_p1b/preflight_atual.py:60,63,66 _verificar_lock_vivo` | escritor-unico | **SEM-TESTE** | arquivo com ZERO linha executada; sem fence_esperado (MAJOR #4 nao aplicado) |
| P1A-20 | G-B | `06_p1a/preflight/economia.py:183 _nome_payg` | seguranca | **EXERCE** | test_estabilizacao_p1a1.py:240 variantes de caixa/separador |
| P1A-21 | G-B | `06_p1a/preflight/economia.py:197 _nome_payg_provedor` | economia | **EXERCE** | test_estabilizacao_p1a1.py:254,259 par sanitiza-sem-bloquear / sanitiza-E-bloqueia |
| P1A-22 | G-B | `06_p1a/preflight/economia.py:213 ambiente_sanitizado` | seguranca | **EXERCE** | test_isolamento.py:241 cobre 11 variantes |
| P1A-23 | G-B | `06_p1a/capsula.py:43 verificar_capsula` | contencao | **EXERCE** | test_capsula_p1a2.py |
| P1A-24 | G-B | `06_p1a/preflight/adaptadores.py:86 sensor_subprocess` | seguranca | **AFIRMA** | SensorRealSemProcesso substitui subprocess.run: verifica o modelo do sensor |
| P1A-25 | G-B | `06_p1a/evidencias/prova_minima.py:79 env sanitizado` | seguranca | **AFIRMA** | test_isolamento.py:230 compara identidade de funcao e ausencia de nome no fonte |
| P1A-26 | G-B | `06_p1a/evidencias/revisao_p1a2.py:139 ambiente_capsula` | seguranca | **SEM-TESTE** | arquivo com ZERO linha executada |
| P1A-27 | G-B | `06_p1a/evidencias/revisao_p1a3.py:189 ambiente_capsula` | seguranca | **SEM-TESTE** | arquivo com ZERO linha executada |
| P1A-28 | G-B | `06_p1a/evidencias/revisao_p1a31.py:150 ambiente_capsula` | seguranca | **EXERCE** | test_correcoes_p1a32.py:308 roda main() com env minimo real |
| P1A-29 | G-B | `06_p1a/evidencias/revisao_p1a33.py:163 ambiente_capsula` | seguranca | **SEM-TESTE** | linha nao alcancada |
| P1A-30 | G-B | `06_p1a/preflight_capsula.py:234 redacao` | proveniencia | **SEM-TESTE** | forca FRACA (so usuario longo); zero teste cita redacao |
| P1A-31 | G-B | `06_p1a/evidencias/pacote_p1a31.py:161 _redigir` | proveniencia | **SEM-TESTE** | forca forte; zero teste cita redacao |
| P1A-32 | G-B | `06_p1a/evidencias/pacote_p1a33.py:223 _redigir` | proveniencia | **SEM-TESTE** | forca forte; arquivo com ZERO linha executada |
| P1A-33 | G-B | `06_p1a/evidencias/revisao_p1a2.py:51 redacao` | proveniencia | **SEM-TESTE** | forca FRACA; arquivo com ZERO linha executada |
| P1A-34 | G-B | `06_p1a/evidencias/revisao_p1a3.py:60 _redigir` | proveniencia | **SEM-TESTE** | forca media; arquivo com ZERO linha executada |
| P1A-35 | G-B | `06_p1a/evidencias/revisao_p1a31.py:52 _redigir` | proveniencia | **SEM-TESTE** | forca media; zero teste cita redacao |
| P1A-36 | G-B | `06_p1a/evidencias/revisao_p1a33.py:61 _redigir` | proveniencia | **SEM-TESTE** | forca media; zero teste cita redacao |
| P1A-37 | G-B | `07_p1b/preflight_atual.py:48 _redigir` | proveniencia | **SEM-TESTE** | forca FRACA; arquivo com ZERO linha executada |
| P1A-38 | G-C | `06_p1a/evidencias/contencao.py:131 argv_kimi` | contencao | **EXERCE** | test_cli_real_p1a34.py:128 invoca o CLI 0.30.0 real |
| P1A-39 | G-C | `06_p1a/evidencias/prova_minima.py:42 COMANDOS` | contencao | **AFIRMA** | test_isolamento.py:207 mede a forma da lista; nenhum CLI invocado (achado 11) |
| P1A-40 | G-C | `06_p1a/evidencias/revisao_p1a2.py:40 COMANDOS` | contencao | **SEM-TESTE** | arquivo com ZERO linha executada |
| P1A-41 | G-C | `06_p1a/evidencias/revisao_p1a3.py:67 COMANDOS` | contencao | **SEM-TESTE** | arquivo com ZERO linha executada |
| P1A-42 | G-C | `06_p1a/evidencias/revisao_p1a31.py:61 COMANDOS` | contencao | **SEM-TESTE** | carregado, porem SUBSTITUIDO por mock.patch em todo teste que roda main() |
| P1A-43 | G-C | `06_p1a/evidencias/revisao_p1a33.py:67 COMANDOS` | contencao | **EXERCE** | somente a entrada kimi, via test_cli_real_p1a34.py; codex nao exercido |
| P1A-44 | G-C | `06_p1a/preflight/frota_real.py:58 ESPECIFICACOES.comandos` | politica | **AFIRMA** | ComandosSaoSomenteDiagnostico verifica verbos declarados, nunca o CLI |
| P1A-45 | G-D | `06_p1a/tests/test_estabilizacao_p1a1.py:378 ZeroPiiNosArtefatos` | seguranca | **EXERCE** | varre a arvore real; ja reprovou o artefato de quem o escrevia |
| P1A-46 | G-D | `06_p1a/tests/test_isolamento.py:150 ZeroSegredoNosArtefatos` | seguranca | **EXERCE** | varre arquivos reais e tem controle positivo (:170) |
| P1A-47 | G-D | `06_p1a/tests/test_isolamento.py:85 CodigoNaoEscreveNemAbreRede` | isolamento | **AFIRMA** | casa substring proibida no fonte; alcance so preflight/*.py |
| P1A-48 | G-D | `06_p1a/tests/test_isolamento.py:129 VarreduraNaoTocaOSistemaDeArquivos` | isolamento | **EXERCE** | instantaneo SHA-256 real antes/depois |
| P1A-49 | G-D | `06_p1a/tests/test_isolamento.py:222 execucao no descartavel` | contencao | **AFIRMA** | casa "cwd=tmp" como substring do fonte |
| P1A-50 | G-D | `06_p1a/tests/test_emendas_p1a3.py:787 sentinela anti-P2` | politica | **EXERCE** | varre .py reais e parseia com ast; escopo da metade A exclui 07_p1b |
| P1A-51 | G-D | `06_p1a/tests/test_estabilizacao_p1a1.py:371 locks fora do Git` | escritor-unico | **EXERCE** | le o .gitignore real |
| P1A-52 | G-D | `06_p1a/tests/test_economia.py:23 EspelhoDaPoliticaP0` | economia | **EXERCE** | compara com POLITICA_ECONOMICA importada da P0 |
| P1A-53 | G-D | `06_p1a/tests/test_adaptadores.py:268 ComandosSaoSomenteDiagnostico` | politica | **EXERCE** | verbos de diagnostico declarados |
| P1A-54 | G-D | `06_p1a/tests/test_falhas_obrigatorias.py:422 CoberturaDasNoveFalhas` | politica | **EXERCE** | meta-guarda: uma classe por falha, codigo estavel e unico |
| P1A-55 | G-D | `06_p1a/tests/test_isolamento.py:164 varredura le mesmo arquivos` | politica | **EXERCE** | meta-guarda contra teste vazio |
| P1A-56 | G-D | `06_p1a/tests/test_isolamento.py:254 evidencias declaram custo zero` | economia | **EXERCE** | le os JSON reais gravados; assertTrue impede conjunto vazio |
| P1A-57 | G-E | `06_p1a/evidencias/contencao.py:90,115 manifesto/mutacoes` | contencao | **EXERCE** | test_correcoes_p1a32.py:351 reviewer falso escreve fora e rc==3 |
| P1A-58 | G-E | `06_p1a/preflight/adaptadores.py:36-74 _ZERO/_RX_QUOTA` | economia | **INDETERMINADO** | regex de producao executada, porem 9 das 11 formas de ESGOTADAS sao autorais (achado B) |

