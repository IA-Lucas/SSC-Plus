#!/usr/bin/env python3
"""Gerador deterministico do pacote de revisao da P1-A.3.6 — SSC+ (experimental).

A P1-A.3.6 submete a revisao independente o ESTADO CORRIGIDO acumulado
ate o HEAD `6a3a3f8`. Quem corrigiu nao certifica: nenhum dos seis MAJOR
fecha por esta missao, e o veredito e dos revisores.

POR QUE O BASE E `30107bd` E NAO `ac03f3a`. O pacote `87f41503…` da
P1-A.3.3 tinha `ac03f3a` como alvo, mas **nenhum revisor o leu**: o codex
foi recusado por limite de uso do ciclo (`revisao-p1a33/codex-20260731T160049Z.json`,
returncode 1) e o kimi morreu na validacao do CLI, antes de qualquer
chamada (`kimi-20260731T155932Z.json`, `Cannot combine --prompt with
--plan`). O ultimo estado que um revisor de fato leu e julgou e
`30107bd` — o estado REPROVADO com seis MAJOR pela P1-A.3.1. Ancorar o
diff em `ac03f3a` esconderia dos revisores justamente as correcoes dos
seis MAJOR, que e o que eles precisam julgar.

ANCORAGEM NO COMMIT (MAJOR #5, corrigido na P1-A.3.2 e herdado aqui).
TODA leitura vem do banco de objetos por `git cat-file blob <ALVO>:<path>`
— bytes exatos do blob, sem filtro de EOL e sem tocar o disco. Com
`core.autocrlf=true` os bytes em disco de um arquivo rastreado sao funcao
do historico de checkout, nao do commit; ler o disco foi o defeito que
reprovou a prova de ancoragem da P1-A.3.1. Consequencia verificavel:
mutar a arvore de trabalho nao muda um byte da saida, e um terceiro
reproduz o mesmo SHA-256 a partir de um checkout limpo de QUALQUER
commit que contenha os objetos.

O portao de identidade e ancorado nos commits, nunca no checkout: exige
que ALVO e BASE existam, que a paternidade ALVO->PAI confira e que BASE
seja ancestral de ALVO. O HEAD corrente e irrelevante.

ORDEM, NORMALIZACAO E EXCLUSOES (declaradas, exigidas pelo ato):

- ORDEM: secoes em sequencia fixa escrita no codigo; `ARQUIVOS_COMPLETOS`
  na ordem literal da lista; `CONTEXTO_COMPLETO` na ordem literal;
  `EVIDENCIAS_HASHEADAS` em `sorted()`; o diff na ordem que o proprio
  `git diff` produz para a lista literal de caminhos.
- NORMALIZACAO: fonte unica sao os blobs (LF por construcao); saida
  gravada em UTF-8 sem BOM; nenhuma reconstrucao entre revisores — os
  MESMOS bytes vao para os dois.
- EXCLUSOES, todas declaradas e nenhuma silenciosa:
  1. o diff publicado cobre os arquivos `.py` que **existem em BASE**
     (os modificados). Os arquivos `.py` **novos** nao entram no diff
     porque ali seriam a propria integra com prefixo `+`; eles entram
     por inteiro na secao de conteudo completo, uma vez;
  2. registros (`.md`) e evidencias (`.json`) alterados entre BASE e
     ALVO entram **somente como SHA-256** do blob em ALVO. O que neles
     e materia de julgamento esta transcrito na secao "Declaracoes
     obrigatorias", nao resumido para caber;
  3. nao entram timestamp, UUID, caminho absoluto, valor de variavel de
     ambiente, credencial, PII, lock, cache nem runtime;
  4. o usuario local (forma longa e 8.3) e o prefixo de caminho local
     sao redigidos.

Uso: python 06_p1a/evidencias/pacote_p1a36.py <saida.txt>
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Commit ALVO do pacote (HEAD da P1-B.02) e seu pai. Nome deliberado:
# nao e "HEAD" — o pacote e funcao DESTES commits, nao do checkout.
ALVO = "6a3a3f865483e488a2f230b02a32dcb224a9b076"
PAI = "e33400fa03550b300942a87f68052c07e8e40825"
# Estado REPROVADO com seis MAJOR pela P1-A.3.1: o ultimo estado que um
# revisor independente de fato leu e julgou.
BASE = "30107bd1ef30b07ab575ff5991e90d70345d702a"

# Pacotes das rodadas anteriores. Registrados para impedir equivalencia
# presumida: nenhum deles contem o estado deste pacote.
PACOTE_P1A31_SHA256 = (
    "c17b730ff8a060165332b08c35ba305f199021dc8b8cd90a55c53ad1a9141459")
PACOTE_P1A33_SHA256 = (
    "87f415031aa1c7ee6464ac6c74f73b8508912350816fc6402fde6a8e435b87c2")

USUARIO = os.path.basename(os.path.expanduser("~"))
USUARIO_CURTO = ("".join(c for c in USUARIO.upper() if c.isalnum())[:6]
                 + "~1")

# Os 9 arquivos `.py` que EXISTEM em BASE e foram modificados ate ALVO.
# O diff publicado cobre exatamente estes. Lista literal: sem glob, sem
# varredura de diretorio e sem `git status` — o conjunto do pacote nao
# pode depender do estado do disco.
PY_MODIFICADOS = [
    "06_p1a/evidencias/pacote_p1a31.py",
    "06_p1a/evidencias/revisao_p1a2.py",
    "06_p1a/evidencias/revisao_p1a3.py",
    "06_p1a/evidencias/revisao_p1a31.py",
    "06_p1a/preflight/adaptadores.py",
    "06_p1a/preflight/pipeline.py",
    "06_p1a/preflight_capsula.py",
    "06_p1a/tests/test_emendas_p1a3.py",
    "07_p1b/preflight_atual.py",
]

# Os 13 arquivos `.py` CRIADOS entre BASE e ALVO. Nao entram no diff
# (seriam a propria integra); entram por inteiro abaixo.
PY_NOVOS = [
    "06_p1a/evidencias/contencao.py",
    "06_p1a/evidencias/pacote_p1a33.py",
    "06_p1a/evidencias/revisao_p1a33.py",
    "06_p1a/leitor_tiers.py",
    "06_p1a/leitores_config.py",
    "06_p1a/tests/test_cli_real_p1a34.py",
    "06_p1a/tests/test_correcoes_p1a32.py",
    "06_p1a/tests/test_leitor_config_p1a35.py",
    "06_p1a/tests/test_p1b01_runner.py",
    "06_p1a/tests/test_p1b_lease_p1a35.py",
    "06_p1a/tests/test_pacote_p1a33.py",
    "06_p1a/tests/test_portao_tier_p1a35.py",
    "06_p1a/tests/test_redacao_p1a35.py",
]

# Conteudo completo em ALVO: os 22 alterados, modificados antes dos
# novos, cada bloco na ordem literal das duas listas acima.
ARQUIVOS_COMPLETOS = PY_MODIFICADOS + PY_NOVOS

# Contexto NAO alterado entre BASE e ALVO, necessario para julgar os
# bloqueios economicos, a trilha de tier declarado, a capsula e o
# escritor unico. Sem duplicar o que ja esta em ARQUIVOS_COMPLETOS.
CONTEXTO_COMPLETO = [
    "06_p1a/tiers_declarados.json",
    "06_p1a/capsula.py",
    "06_p1a/escritor.py",
    "05_p0/ssc_p0/writelock.py",
    "06_p1a/preflight/economia.py",
    "06_p1a/preflight/sombra.py",
    "06_p1a/preflight/frota_real.py",
]

# Registros e evidencias alterados entre BASE e ALVO: entram SOMENTE
# como hashes do blob em ALVO. A materia deles que pesa no julgamento
# esta transcrita em DECLARACOES.
EVIDENCIAS_HASHEADAS = [
    "06_p1a/99_achados-governanca-20260731.md",
    "06_p1a/99_decisao-p1a32.md",
    "06_p1a/99_decisao-p1a33.md",
    "06_p1a/99_decisao-p1a34.md",
    "06_p1a/99_decisao-p1a35.md",
    "06_p1a/99_varredura-guardas-p1a35.md",
    "06_p1a/evidencias/backups/tiers_declarados-2026-08-01-pre-redeclaracao.json",
    "06_p1a/evidencias/revisao-p1a33/codex-20260731T160049Z.json",
    "06_p1a/evidencias/revisao-p1a33/kimi-20260731T155932Z.json",
    "06_p1a/tiers_declarados.json",
    "07_p1b/02_diagnostico-parada-p1b00.md",
    "07_p1b/99_decisao-p1b01.md",
    "07_p1b/99_decisao-p1b02.md",
    "07_p1b/evidencias/preflight-20260801T221207Z.json",
    "07_p1b/evidencias/preflight-20260801T221451Z.json",
    "07_p1b/evidencias/preflight-20260801T235521Z.json",
]

HISTORICO = """\
O QUE UM REVISOR DE FATO LEU, ATE HOJE — e por isso o BASE deste pacote.

| Rodada | Pacote | codex | kimi |
|---|---|---|---|
| P1-A.3.1 | `c17b730f…` (alvo `677c585`) | leu e julgou: **REPROVADO, seis MAJOR** | falhou (returncode 1, 3,8 s) — nenhuma revisao |
| P1-A.3.3 | `87f41503…` (alvo `ac03f3a`) | **recusado por limite de uso do ciclo** — nenhuma revisao | **morreu na validacao do CLI** (`Cannot combine --prompt with --plan`) — nenhuma chamada |
| P1-A.3.6 | este | — | — |

Consequencia direta: as correcoes dos seis MAJOR (commits `029ff44` e
`ac03f3a`) **nunca foram vistas por revisor nenhum**. Por isso o diff
deste pacote parte de `30107bd`, o estado reprovado, e nao de `ac03f3a`.

Advertencia sobre o hash do pacote da P1-A.3.1: a evidencia daquela
rodada registra `c3b5c54a…` como o que os revisores receberam, e o
gerador ancorado reproduz `c17b730f…`. A divergencia NAO e ruido — e o
proprio MAJOR #5 (o gerador lia a arvore de trabalho, nao o commit).
Os dois numeros ficam publicados como estao.
"""

SUITES = """\
Suites medidas na ABERTURA desta missao, sobre o HEAD `6a3a3f8`, arvore
limpa, pelo numero MEDIDO e nunca pelo desejado:

- P0:            python -m unittest discover -s 05_p0/tests  -> 100/100 OK
- P1-A:          python -m unittest discover -s 06_p1a/tests -> 424/424 OK
- Prova central: python 05_p0/cenarios/prova_central.py      -> 18/18 OK (20 eventos)

Trajetoria da contagem da P1-A entre BASE e ALVO, para que o revisor
possa cobrar o vinculo entre correcao e teste:

- `30107bd` (BASE, estado reprovado): 306/307 — ja abria VERMELHA; o
  sentinela anti-P2 antigo acusava `evidencias/pacote_p1a31.py`, arquivo
  que apenas MENCIONA o literal no enunciado de uma pergunta;
- `ac03f3a` (correcao dos seis MAJOR): 342/342;
- P1-A.3.5 (oito correcoes de guardas): 401/401;
- P1-B.01 (cinco ordens, 23 testes novos): 424/424;
- `6a3a3f8` (ALVO): **424/424**.

A CONTAGEM E MEDIDA, NUNCA META. Conforme a §4.2.2 da
`99_decisao-p1a31.md`, `307/307` deixou de ser criterio de aceite valido:
o criterio e o sentinela medir comportamento, nao tamanho de lista.

NOTA DE ALCANCE, que o revisor deve considerar ao julgar: `EXERCE` mede
COBERTURA, nao forca de asercao — ver "Declaracoes obrigatorias", item 4.
"""

DECLARACOES = """\
Quatro declaracoes que o ato desta missao obriga a transmitir aos dois
revisores. Julgar sem elas seria julgar contra premissa falsa, e um
veredito assim nao vale — tenha ele aprovado ou reprovado.

--- DECLARACAO 1 — ACHADO 4: o "escritor unico" NAO exclui entre missoes

Isto atinge diretamente o eixo "escritor unico, lease e fencing", que o
revisor julga. O pacote da P1-A.3.1 afirmou esse controle sem saber
disto.

`LockSessao` (`05_p0/ssc_p0/writelock.py`) tranca o arquivo que recebe no
construtor — `msvcrt.locking` no Windows, `fcntl.flock` no POSIX —,
chaveado por `os.path.normcase(os.path.realpath(caminho_lock))`. E
`escritor.py:46-49` monta esse caminho como:

    locks/{sessao}.lock      e      locks/{sessao}.fence

Como CADA MISSAO USA UM NOME PROPRIO — `p1a2-ops`, `p1a3-ops`,
`p1a31-ops`, `p1a32-ops`, `p1a33-ops`, `p1a34-ops`, `achados-gov-ops`,
`p1a35-ops`, `p1b01-ops`, `p1b02-ops`, `p1a36-ops` —, duas missoes
concorrentes trancam ARQUIVOS DIFERENTES e nenhuma bloqueia a outra.
**A exclusao mutua entre missoes nao existe.**

A docstring de `escritor.py` afirma: "Uma segunda sessao falha na
aquisicao (LockIndisponivel) — antes de escrever um byte ou invocar
qualquer provedor." Isso vale SOMENTE para segunda sessao com o MESMO
nome. O teste que sustenta a afirmacao,
`test_runner_segunda_sessao_retorna_3_sem_invocar_nada`
(`test_estabilizacao_p1a1.py`), usa `"p1-ops"` nos DOIS lados: exercita o
unico caso que funciona e nunca o caso que ocorre em operacao.

Corolario ja observado: `liberar()` (`escritor.py:82-84`) solta apenas o
lock do SO; o arquivo `.lease` sobrevive com `expira_em` no futuro. Tres
sessoes consecutivas leram como "nao vencido, titular morto". E a suite
P1-A FABRICA esse artefato a cada corrida, porque
`test_estabilizacao_p1a1.py:358-360` adquire sobre o `locks/` REAL do
repositorio, nao um `tmpdir`.

CONDICAO OPERATIVA VIGENTE, sob a qual esta propria missao escreve:
enquanto o ACHADO 4 nao for corrigido, o escritor unico e garantido
**por ordem do Fundador — uma sessao de escrita por vez, decidida por
ele — e nunca pelo mecanismo.** O lease `p1a36-ops` desta missao nao
impediria uma segunda sessao com outro nome de escrever ao mesmo tempo.

Estado: candidato a SETIMO MAJOR, **nao corrigido**. Quem classifica
MAJOR e revisor, nao a sessao que registrou o achado. A correcao exige
mudanca de politica (lock unico do repositorio, e `liberar()` que expire
o lease que concedeu) e e materia 4 da missao de politica.

--- DECLARACAO 2 — o achado de `07_p1b/preflight_atual.py:172`

Aberto na P1-A.3.2 (§5.3 da `99_decisao-p1a32.md`) e caracterizado no §4
de `07_p1b/02_diagnostico-parada-p1b00.md`. O texto original:

    07_p1b/preflight_atual.py:171-172
        elegiveis = [r["provider_id"] for r in relatorios
                     if r["resultado"] == "ELIGIBLE"]

O filtro aceitava SOMENTE `"ELIGIBLE"`. Os outros tres resultados do enum
(`pipeline.py:31`) caiam fora, de modo que uma corrida com google e grok
em SUPERVISED ainda imprimiria `ELIGIBLE: []` — indistinguivel de
"nenhum provedor passou". O achado foi medido como INDEPENDENTE da
parada de 30/07: nao a causou e nao foi produzido por ela.

ESTADO NO ALVO, medido e nao presumido — e o revisor precisa julgar isto,
nao aceitar: a ordem 2 da P1-B.01 (commit `64837da`) substituiu aquele
filtro por uma particao sobre `pipeline.RESULTADOS`, com os quatro
resultados impressos SEMPRE, inclusive vazios, mais ramo `FORA-DO-ENUM` e
linha `total classificado: N+M de T`. O codigo esta em
`07_p1b/preflight_atual.py:287-305`, no conteudo completo deste pacote.
A linha 172 do ALVO ja nao e aquele filtro.

O que **permanece aberto** e a metade de escopo do mesmo achado, o
achado 13 da `99_varredura-guardas-p1a35.md`: a metade (A) do sentinela
anti-P2 (`06_p1a/tests/test_emendas_p1a3.py`) cobre so `06_p1a`, e
portanto uma decisao sobre elegibilidade escrita em `07_p1b` **nao e
vista pelo sentinela**. Nada impede a construcao de reaparecer ali.

--- DECLARACAO 3 — as tres divergencias registradas pela P1-B.01

A P1-B.01 fechou como CONCLUIDA registrando tres itens com remedio
especificado, EM VEZ de corrigi-los por conta propria (§6 e §9 de
`07_p1b/99_decisao-p1b01.md`). Eles seguem ABERTOS no ALVO:

1. ASSIMETRIA DE `quota` NO CAMINHO DE ZERO SONDAS. Depois da ordem 3, o
   bloqueio imediato reporta `quota: "nao-sondada"`, mas o caminho de
   zero sondas (`pipeline.py:163-164`) continua com `"desconhecida"` —
   embora ali tambem nada tenha sido sondado.
   POR QUE NAO FOI CORRIGIDA: mudar contradiria teste ratificado
   (`test_pipeline.py:36`, que exige `"desconhecida"` para os cinco no
   caminho verde).
   REMEDIO ESPECIFICADO: decisao do proprietario sobre qual dos dois
   valores e o correto, e entao a correcao com o teste reapontado.

2. O LACO DE CLASSIFICACAO DO RUNNER DA P1-B ESTA DUPLICADO. `main()` de
   `07_p1b/preflight_atual.py` mantem o proprio laco sobre `frota_real()`,
   com a mesma forma de `preflight_capsula.classificar_frota`.
   POR QUE NAO FOI CORRIGIDA: unifica-los quebraria a garantia de custo
   zero de `test_p1b_lease_p1a35.py`, que substitui `executar_preflight`
   NO MODULO da P1-B — sem atualizar o teste, a suite passaria a invocar
   os CLIs reais.
   REMEDIO ESPECIFICADO: extrair a classificacao para modulo partilhado
   E reapontar o mock, no mesmo commit.
   NOTA DE CLASSE: e o mesmo mecanismo dos achados 7, 10 e da correcao 7
   da P1-A.3.5 — a copia que ninguem exercita fica para tras.

3. O RUNNER DA P1-A AUDITA `dict(os.environ)` CRU
   (`preflight_capsula.py:161`). E verdadeiro apenas PELO GUARDA
   `exigir_capsula_limpa` (`:156`), nao por construcao — exatamente a
   assimetria que a ordem 1(a) fechou do lado da P1-B, onde
   `ambiente_capsula(os.environ)` faz a propriedade valer por construcao.
   POR QUE NAO FOI CORRIGIDA: codigo ratificado, fora do escopo ordenado.
   REMEDIO ESPECIFICADO: aplicar do lado da P1-A a mesma derivacao da
   ordem 1(a).

--- DECLARACAO 4 — `EXERCE` mede COBERTURA, nao forca de asercao

A P1-A.3.5 classificou os 86 guardas do acervo em EXERCE / SEM-TESTE /
AFIRMA / INALCANCAVEL / INDETERMINADO, e fechou com EXERCE 64,
SEM-TESTE 13, AFIRMA 8, INALCANCAVEL 0, INDETERMINADO 1.

O que `EXERCE` significa, exatamente: o alcance daquela linha de guarda
foi MEDIDO sob `sys.monitoring` durante a suite — isto e, a linha foi
executada por algum teste. Isso e condicao NECESSARIA e nunca suficiente:
**a linha ter sido executada nao diz que a assercao ao redor dela seja
forte.** Um guarda pode estar em EXERCE e ainda assim ser verificado por
um teste que nao reprovaria se o guarda fosse removido.

O exemplo vivo disso esta no proprio acervo e NAO foi corrigido: a lacuna
de sensibilidade do sentinela, §3.4 da `99_decisao-p1a34.md`.

Consequencia para esta revisao: NAO tratar "EXERCE 64" como prova de
corretude de 64 guardas. Onde o revisor quiser cobrar forca de asercao,
cobre-a do teste concreto — os arquivos de teste vao completos neste
pacote.
"""

THREAT_REVIEW = """\
Threat review da P1-A.3.6 (revisao independente do estado corrigido):

| Ameaca | Mitigacao | Estado |
|---|---|---|
| Quem corrigiu certifica a propria correcao | Missao probatoria: nao altera codigo, teste nem politica. O fechamento de cada MAJOR depende de pronunciamento explicito de revisor independente | coberto por construcao |
| Revisor julga "escritor unico" sem saber do ACHADO 4 | Declaracao 1, obrigatoria, transmitida aos DOIS revisores com o mecanismo, a demonstracao e a condicao operativa vigente | coberto por construcao |
| Pacote reaproveitado de rodada anterior | Pacote NOVO sobre o HEAD atual; `c17b730f…` e `87f41503…` publicados apenas para impedir equivalencia presumida | coberto por construcao |
| Pacote reconstruido entre revisores (bytes divergentes) | Geracao unica e deterministica, executada 2x em diretorios descartaveis INDEPENDENTES, com bytes e SHA-256 identicos exigidos; os MESMOS bytes sao copiados para os dois descartaveis; cada revisor declara o SHA-256 recebido | coberto por construcao |
| Pacote nao reproduzivel a partir do commit (defeito que reprovou a P1-A.3.1) | Toda leitura via `git cat-file blob <ALVO>:<path>`; prova de ancoragem executada ANTES do envio: regeneracao em checkout limpo do commit deve bater com a geracao da arvore, e mutacao deliberada da arvore de trabalho NAO pode mudar o hash | verificado antes do envio |
| Pacote vaza PII, caminho local ou segredo | Fonte exclusivamente de conteudo git; registros e evidencias somente como hashes; redacao do usuario local (forma longa e 8.3) e do prefixo de caminho local; zero valor de ambiente | coberto por construcao |
| Exclusao usada para encolher o pacote ate caber | As exclusoes sao declaradas no gerador e no proprio pacote, e sao de CLASSE (registro/evidencia como hash; diff so dos modificados), nunca de conveniencia. Pacote que nao couber em qualquer revisor encerra a missao em BLOCKED — sem resumir e sem enviar pacotes diferentes | coberto por construcao |
| Revisor escreve fora do diretorio descartavel | codex: `--sandbox read-only --ephemeral`; kimi: sem sandbox de filesystem no CLI (medido) — restricao parcial (`--skills-dir` vazio, sem `-y/--yolo/--auto`) mais DETECCAO INTEGRAL por manifesto SHA-256 da arvore antes/depois, que REPROVA a corrida | mitigado; limite declarado |
| Chamada extra de modelo ou custo variavel | UMA chamada valida por provider, por assinatura; a capsula remove toda credencial de modelo do env-filho; nenhum PAYG, top-up, extra usage ou fallback pago | coberto por construcao |
| Tier declarado expirado no instante da chamada | Validade reverificada imediatamente antes de cada chamada; expirado = PARADA. Somente o proprietario renova. As duas declaracoes vigentes expiram em 2026-08-02T23:54:41Z | verificado nesta missao |
| Quota esgotada tratada como renovavel pela sessao | O codex encerrou em limite de uso do ciclo na P1-A.3.3, com data de reabertura fora de qualquer janela desta missao; a missao nao tenta via paga nem renovacao automatica, e registra o resultado como esta | limite declarado |
| Lease morre durante a chamada longa | Renovador dedicado (30 s, lease 120 s); `verificar_lock` com fence esperado IMEDIATAMENTE antes de cada persistencia — a chamada de provider excede a janela do lease (256 s observados contra 120 s) | coberto por construcao |
| Micro-commit tocar codigo, teste, politica ou historico | Missao probatoria: escritas restritas a instrumentos de revisao, evidencias, atestado e registro; staging explicito caminho a caminho; suites rodadas com os arquivos staged | coberto por verificacao |
"""

PERGUNTAS = """\
Avalie com olhar adversarial, citando arquivo e trecho.

CONTEXTO. A revisao da P1-A.3.1 REPROVOU este trabalho com SEIS MAJOR.
Duas rodadas de revisao foram tentadas desde entao e NENHUMA produziu
veredito (ver "Historico de revisao"). Este pacote e o estado depois de
todas as correcoes. Quem corrigiu nao certifica: cabe a voce dizer se
cada MAJOR fechou. Uma correcao nao fecha por ter sido feita.

Leia antes as "Declaracoes obrigatorias": quatro fatos que o autor do
pacote e obrigado a lhe transmitir, dois deles contra o proprio interesse.

PARTE 1 — OS SEIS MAJOR, UM PRONUNCIAMENTO EXPLICITO PARA CADA UM.
Responda exatamente uma linha por item, no formato
`MAJOR-<n>: FECHADO | NAO-FECHADO — <justificativa curta citando trecho>`.
Nenhum item pode ficar sem linha.

MAJOR-1 `06_p1a/preflight_capsula.py` — o atalho manual de google/grok
  montava relatorio SUPERVISED sem chamar `executar_preflight` nem
  `_config_persistida`, pulando as auditorias economicas. Corrigido por
  `classificar_frota`. A frota inteira passa mesmo pelas auditorias?
  Chave, endpoint PAYG ou auto-topup persistidos agora bloqueiam? A
  propriedade de zero sondas para google/grok foi preservada?
MAJOR-2 `06_p1a/preflight/adaptadores.py` — formatos como
  `0.0 tokens available` e `0% quota available` escapavam das regexes de
  esgotamento e casavam o sinal positivo, classificando quota zero como
  disponivel (fail-open). Corrigido por `_ZERO`. As duas ancoras estao
  corretas? Ha forma de quota zerada que ainda escape, ou franquia
  disponivel que agora bloqueie indevidamente?
MAJOR-3 `06_p1a/evidencias/contencao.py` + os runners — o cwd
  descartavel e a instrucao textual nao restringem o filesystem, e a
  lista de arquivos restantes so olhava DENTRO do descartavel. Corrigido
  por restricao parcial do CLI mais manifesto SHA-256 da arvore inteira.
  Atencao: a primeira correcao era INEXECUTAVEL — `--plan` com `-p`
  mata o comando do kimi na validacao, o que so a invocacao revelou, e
  foi consertado depois (`argv_kimi`). A deteccao tem ponto cego? A unica
  exclusao (`locks`) e legitima, sendo ela justamente o diretorio do
  escritor unico? O rotulo de enforcement afirma algo que o CLI nao
  sustenta?
MAJOR-4 `contencao.verificar_lock` e os chamadores — o lease era
  verificado so na abertura, e a chamada de provider excede a janela
  (256 s observados contra 120 s de lease), de modo que a gravacao podia
  ocorrer com lease morto ou titular substituido. Corrigido com
  verificacao imediatamente antes de cada persistencia, com fence
  esperado. Ha caminho de gravacao que escape da verificacao? Considere
  que a correcao chegou a `07_p1b/preflight_atual.py` so depois, pela
  P1-A.3.5, e leia a Declaracao 1 antes de julgar este item.
MAJOR-5 `06_p1a/evidencias/pacote_p1a31.py` — o bloco de hashes de
  evidencia lia os bytes da ARVORE DE TRABALHO; com `core.autocrlf=true`
  4 de 11 hashes divergiam do conteudo versionado, e a prova de
  ancoragem falhou. Corrigido para `git cat-file blob`. O portao de
  identidade foi TROCADO (deixou de exigir `rev-parse HEAD == ALVO` e
  passou a exigir existencia do par e paternidade): isso e afrouxamento
  de guarda ou substituicao de um guarda que ficou vacuo? Justifique.
  O gerador DESTE pacote herda a mesma construcao — julgue-a tambem.
MAJOR-6 `06_p1a/tests/test_emendas_p1a3.py` — o sentinela anti-P2
  comparava CONJUNTO DE CAMINHOS com allowlist fixa; falhava nos dois
  sentidos (falso positivo por mencao documental, falso negativo para
  consumidor escrito dentro da allowlist). Reescrito para medir
  comportamento por AST em duas metades. A analise por AST tem furo
  explorável? A metade (A) deveria cobrir `07_p1b` tambem — ver a
  Declaracao 2, que registra este escopo como aberto?

PARTE 2 — DEFEITO NOVO INTRODUZIDO PELAS CORRECOES.
As correcoes acumuladas entre `30107bd` e `6a3a3f8` introduziram defeito
novo, regressao, ou enfraqueceram alguma garantia que existia antes?
Responda uma linha:
`DEFEITO-NOVO: SIM | NAO — <o que, onde>`.
Olhe em especial para o que foi TROCADO e nao apenas acrescentado, e
para os pontos onde uma correcao alcancou uma copia e nao a outra.

PARTE 3 — EIXOS DE AVALIACAO DO ESTADO EXATO.
Avalie e reporte achados nestes eixos: (1) cobranca e custo variavel;
(2) credenciais e vazamento; (3) falha fechada; (4) tier declarado e sua
janela; (5) descoberta de modelo; (6) quotas — inclusive a assimetria da
Declaracao 3, item 1; (7) anti-P2 — a trilha de observacao-sombra nao
pode virar autorizacao plena, subir o teto de provider supervisionado nem
habilitar execucao autonoma; (8) isolamento do revisor; (9) escritor
unico, lease e fencing — leia a Declaracao 1 antes; (10) evidencia e sua
ancoragem; (11) testes — a cobertura acompanha o codigo, e alguma
expectativa foi enfraquecida? Lembre a Declaracao 4: `EXERCE` mede
cobertura, nao forca de asercao; (12) autorizacao de P1-B em modo sombra:
este estado autoriza reabrir a P1-B em observacao-sombra, ou nao?

FORMATO DA RESPOSTA (obrigatorio, nesta ordem).
Primeiro, uma linha cada:
PROVIDER: <seu provider>
MODELO-OBSERVADO: <o modelo que voce observa ser; se nao observavel, escreva DESCONHECIDO>
CANAL: <canal de acesso>
PACOTE-SHA256: <SHA-256 de ./pacote-revisao.txt — compute-o>
ESCOPO: <o que voce revisou>
Depois as seis linhas `MAJOR-<n>:` da PARTE 1, a linha `DEFEITO-NOVO:`
da PARTE 2, e entao um achado por linha, prefixado por severidade
CRITICAL | MAJOR | MINOR | OBS, com arquivo:tema e descricao curta.
Para cada MINOR, classifique bloqueante ou nao-bloqueante, com motivo.
Se nao houver achado num nivel, nao o invente.
Termine com: VEREDITO: APROVADO | APROVADO-COM-RESSALVAS | REPROVADO
"""


def _redigir(texto: str) -> str:
    """Redige usuario local (longa e 8.3) e o prefixo de caminho local.

    A redacao atinge SOMENTE o pacote; o repositorio permanece intacto.
    O codigo versionado contem um caminho local em `preflight_capsula`,
    que nao pode vazar para o revisor.
    """
    return ((texto or "").replace(USUARIO, "<USUARIO>")
            .replace(USUARIO_CURTO, "<USUARIO>")
            .replace("E:\\LucasIA", "<CAMINHO-LOCAL>")
            .replace("E:/LucasIA", "<CAMINHO-LOCAL>"))


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True).stdout


def _blob(rel: str) -> bytes:
    """Bytes EXATOS do blob versionado em ALVO — nunca o disco.

    Esta funcao e a ancoragem do pacote: `git cat-file blob` devolve o
    objeto cru, sem passar pelo filtro de EOL e sem depender de
    `core.autocrlf`. Trocar por leitura de arquivo reintroduz o MAJOR #5.
    """
    return subprocess.run(
        ["git", "cat-file", "blob", f"{ALVO}:{rel}"], cwd=RAIZ,
        capture_output=True, check=True).stdout


def _conteudo_alvo(rel: str) -> str:
    return _blob(rel).decode("utf-8", errors="replace")


def montar_pacote() -> str:
    # Portao de identidade ANCORADO NOS COMMITS, nao no checkout.
    try:
        pai_de_alvo = _git("rev-parse", f"{ALVO}^").strip()
        tree = _git("rev-parse", f"{ALVO}^{{tree}}").strip()
        _git("rev-parse", "--verify", f"{BASE}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"PARADA: commit alvo {ALVO} ou base {BASE} ausente") from exc
    if pai_de_alvo != PAI:
        raise SystemExit(
            f"PARADA: pai inesperado de {ALVO}: {pai_de_alvo} != {PAI}")
    if subprocess.run(["git", "merge-base", "--is-ancestor", BASE, ALVO],
                      cwd=RAIZ).returncode != 0:
        raise SystemExit(
            f"PARADA: {BASE} nao e ancestral de {ALVO}")
    # O conjunto do diff e a lista literal, e a conferencia e feita
    # contra o banco de objetos: arquivo que nao exista em BASE nao pode
    # estar em PY_MODIFICADOS, e arquivo que exista nao pode estar em
    # PY_NOVOS. Sem isso a exclusao declarada viraria omissao silenciosa.
    for rel in PY_MODIFICADOS:
        if subprocess.run(["git", "cat-file", "-e", f"{BASE}:{rel}"],
                          cwd=RAIZ, capture_output=True).returncode != 0:
            raise SystemExit(
                f"PARADA: {rel} declarado modificado mas ausente em BASE")
    for rel in PY_NOVOS:
        if subprocess.run(["git", "cat-file", "-e", f"{BASE}:{rel}"],
                          cwd=RAIZ, capture_output=True).returncode == 0:
            raise SystemExit(
                f"PARADA: {rel} declarado novo mas presente em BASE")

    sujeito_alvo = _git("log", "-1", "--format=%s", ALVO).strip()
    sujeito_pai = _git("log", "-1", "--format=%s", PAI).strip()
    sujeito_base = _git("log", "-1", "--format=%s", BASE).strip()
    n_commits = _git("rev-list", "--count", f"{BASE}..{ALVO}").strip()
    diff = _git("diff", BASE, ALVO, "--", *PY_MODIFICADOS)
    partes = [
        "PACOTE DE REVISAO — SSC+ P1-A.3.6 (laboratorio experimental, "
        "sem autoridade)\n",
        "Missao: revisao INDEPENDENTE do estado corrigido. Missao "
        "probatoria — nao altera codigo, teste nem politica. Quem "
        "corrigiu nao certifica: correcao nao fecha por ter sido feita, "
        "fecha por revisor dizer que fechou.\n",
        "\n=== Identidade dos commits ===\n",
        f"ALVO (HEAD revisado): {ALVO}\n",
        f"  sujeito: {sujeito_alvo}\n",
        f"PAI do alvo:          {PAI}\n",
        f"  sujeito: {sujeito_pai}\n",
        f"BASE (estado REPROVADO com seis MAJOR pela P1-A.3.1): {BASE}\n",
        f"  sujeito: {sujeito_base}\n",
        f"tree do ALVO:         {tree}\n",
        f"commits entre BASE e ALVO: {n_commits}\n",
        "branch master; sem tag e sem remoto (verificado na abertura da "
        "missao)\n",
        "\n=== Historico de revisao — o que um revisor de fato leu ===\n",
        HISTORICO,
        "\n=== Pacotes das rodadas anteriores (NAO equivalem a este) ===\n",
        f"SHA-256 do pacote da P1-A.3.1: {PACOTE_P1A31_SHA256}\n",
        f"SHA-256 do pacote da P1-A.3.3: {PACOTE_P1A33_SHA256}\n",
        "Nenhum dos dois contem o estado deste pacote. Nenhuma "
        "equivalencia pode ser presumida.\n",
        "\n=== Declaracoes obrigatorias ===\n", DECLARACOES,
        "\n=== Suites ===\n", SUITES,
        "\n=== Threat review ===\n", THREAT_REVIEW,
        "\n=== Perguntas de revisao ===\n", PERGUNTAS,
        "\n=== Composicao deste pacote (ordem, normalizacao, exclusoes) "
        "===\n",
        f"- diff publicado: `git diff {BASE} {ALVO} -- <lista literal>`, "
        f"cobrindo os {len(PY_MODIFICADOS)} arquivos .py que EXISTEM em "
        "BASE;\n",
        f"- os {len(PY_NOVOS)} arquivos .py CRIADOS entre BASE e ALVO nao "
        "entram no diff (seriam a propria integra com prefixo `+`) e "
        "entram por inteiro na secao de conteudo completo;\n",
        f"- conteudo completo em ALVO: {len(ARQUIVOS_COMPLETOS)} arquivos "
        f"alterados + {len(CONTEXTO_COMPLETO)} de contexto nao alterado;\n",
        f"- registros (.md) e evidencias (.json) alterados: "
        f"{len(EVIDENCIAS_HASHEADAS)} entradas, SOMENTE como SHA-256 do "
        "blob em ALVO. A materia deles que pesa no julgamento esta "
        "transcrita nas Declaracoes obrigatorias;\n",
        "- toda leitura vem de `git cat-file blob <ALVO>:<path>`, nunca "
        "do disco; saida UTF-8 sem BOM;\n",
        "- nao entram timestamp, UUID, caminho absoluto, valor de "
        "variavel de ambiente, credencial, PII, lock, cache nem runtime; "
        "usuario local (forma longa e 8.3) e prefixo de caminho local "
        "sao redigidos.\n",
        "\n=== Hashes SHA-256 dos registros e evidencias (blob em ALVO) "
        "===\n",
    ]
    for rel in sorted(EVIDENCIAS_HASHEADAS):
        partes.append(f"{hashlib.sha256(_blob(rel)).hexdigest()}  {rel}\n")
    partes.append(f"\n=== Diff {BASE[:7]}..{ALVO[:7]} — arquivos .py "
                  "modificados ===\n")
    partes.append(diff)
    partes.append("\n=== Arquivos alterados — conteudo completo em ALVO "
                  "===\n")
    for rel in ARQUIVOS_COMPLETOS:
        partes.append(f"\n--- {rel} ---\n")
        partes.append(_conteudo_alvo(rel))
    partes.append("\n=== Contexto nao alterado — conteudo completo em "
                  "ALVO ===\n")
    for rel in CONTEXTO_COMPLETO:
        partes.append(f"\n--- {rel} ---\n")
        partes.append(_conteudo_alvo(rel))
    return _redigir("".join(partes))


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: pacote_p1a36.py <saida.txt>", file=sys.stderr)
        return 2
    dados = montar_pacote().encode("utf-8")
    Path(sys.argv[1]).write_bytes(dados)
    print(hashlib.sha256(dados).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
