#!/usr/bin/env python3
"""Contencao real do reviewer e escritor unico — SSC+ P1-A.3.2.

Duas correcoes da revisao P1-A.3.1, compartilhadas pelas ferramentas de
revisao (`revisao_p1a3.py` e `revisao_p1a31.py`), que ate aqui repetiam
o mesmo defeito em copias separadas.

MAJOR #3 — isolamento do kimi. `cwd` descartavel e instrucao textual no
prompt NAO restringem o filesystem: o processo filho herda as permissoes
do usuario e escreve onde quiser; e a lista de "arquivos restantes" so
olha DENTRO do descartavel, de modo que uma escrita fora dele nao
aparece em lugar nenhum. As duas metades do conserto vivem aqui:

- restricao REAL do alcance do CLI (`argv_kimi`), com as flags que o
  proprio CLI oferece — medidas em `kimi --help`, nao presumidas;
- DETECCAO DE ALCANCE DECLARADO (`Vigilancia`): SHA-256 de cada arquivo
  das raizes vigiadas antes e depois da chamada, seguido de ATRIBUICAO.
  O que a instrucao textual nao impede, o manifesto acusa — dentro do
  alcance que o rotulo declara, e so dentro dele.

CORRECAO P1-A.3.4 — a primeira metade acima estava INEXECUTAVEL. A
P1-A.3.3 (§4) mediu, invocando o CLI de verdade, que o kimi 0.30.0
recusa `--plan` junto com `-p/--prompt`:

    error: Cannot combine --prompt with --plan.

`--plan` era, portanto, restricao NENHUMA: ele nao restringia a corrida,
ele a IMPEDIA por inteiro — desde a P1-A.3.2 nenhuma chamada headless ao
kimi era possivel por esta ferramenta. `argv_kimi` deixa de emiti-lo.

Por que `kimi --help` nao bastou para pegar isso: `--help` lista as
flags ISOLADAMENTE e as duas existem de fato; a incompatibilidade so
aparece na COMBINACAO, que so a invocacao revela. Medir o cardapio nao e
exercer a interface — e a mesma classe do achado #6.

Plan mode nao tem substituto headless em 0.30.0: `--plan` e eixo de
sessao interativa. O que resta de restricao REAL pelo CLI e o modo de
permissao — o binario declara `Use one of: yolo / manual / auto` —, do
qual `-y/--yolo` e `--auto` sao justamente os dois nao-restritivos. Nao
passa-los e a restricao que sobra, e ela e verificada por teste.

A honestidade do rotulo faz parte do conserto: o kimi NAO tem sandbox de
filesystem como o `--sandbox read-only` do codex. O que se afirma aqui e
o que se mede — restricao parcial pelo CLI mais deteccao de alcance
DECLARADO por manifesto —, nunca isolamento equivalente.

MAJOR #4 — o lease era verificado apenas ANTES do trabalho. Uma chamada
de provider excede a janela do lease (256 s observados contra 120 s de
lease na P1-A.3.1), de modo que a gravacao podia ocorrer com lease ja
morto ou com titular ja substituido. `verificar_lock` aceita
`fence_esperado` e deve ser chamada IMEDIATAMENTE ANTES de cada
persistencia, nunca so na abertura.
"""

import hashlib
import os

_USUARIO_LOCAL = os.path.basename(os.path.expanduser("~"))

# Usuarios de INFRAESTRUTURA (runner de CI, conta generica): nao sao uma
# pessoa, e o objeto dos guardas de propriedade da estacao — nome do
# proprietario e configs instaladas por ele — nao existe numa estacao
# assim. Pior: nome generico curto ("runner") casa o acervo inteiro
# (`runner_p2`) e o guarda de PII vira ruido. Medido no primeiro CI
# verde-por-desenho (P1-A.10, 2026-08-13): o runner do GitHub roda como
# `runneradmin`.
#
# O salto exige DUAS provas, nao uma heuristica solta: a declaracao
# `GITHUB_ACTIONS=true` do ambiente E uma conta desta lista nominal. Um
# usuario local chamado `admin`, ou uma variavel de CI plantada sob o
# nome de uma pessoa, nao desliga guarda nenhum. Quem pula tambem grava
# a declaracao no motivo do `skip`; nunca conta ausencia como verde.
USUARIOS_DE_INFRAESTRUTURA = frozenset({
    "runner", "runneradmin", "root", "admin", "administrator",
    "user", "actions", "jenkins", "vagrant", "ci", "containeradministrator"})


def usuario_e_infraestrutura(
        usuario: str | None = None,
        ambiente: dict | None = None) -> bool:
    """CI declarado + conta nominal de infraestrutura, nunca so um deles."""
    alvo = _USUARIO_LOCAL if usuario is None else str(usuario)
    env = os.environ if ambiente is None else ambiente
    github_actions = str(env.get("GITHUB_ACTIONS", "")).strip().lower()
    return (github_actions == "true" and
            alvo.strip().lower() in USUARIOS_DE_INFRAESTRUTURA)

# NENHUMA exclusao. Ate a P1-A.3.6, `locks/` saia do manifesto porque o
# renovador dedicado reescreve o lease a cada 30 s, e a alternativa
# conhecida era alarme falso em toda corrida. O revisor independente
# mediu o preco disso: *"cobre apenas RAIZ e exclui todo `locks/`; o
# kimi segue capaz de alterar arquivos fora do repositorio, ou locks nao
# verificados, sem aparecer em `mutacoes`"*.
#
# A saida nao e excluir: e SEPARAR AS DUAS PERGUNTAS que o manifesto
# respondia juntas (§6 do registro da P1-A.3.6) — *a arvore mudou?*, que
# e deteccao, e *quem escreveu?*, que e atribuicao. O lease do renovador
# volta a ser fotografado e passa a ser ATRIBUIDO (`atribuir`), nao
# apagado. Ponto cego por exclusao vira ponto declarado por atribuicao.
EXCLUIDOS_DO_MANIFESTO = ()

# Alvos vigiados FORA do repositorio — a metade "cobrir alem de RAIZ".
#
# Sao exatamente as fontes de config que `auditar_config` le. A escolha
# nao e arbitraria e nao e "tudo o que der": vigiar o disco inteiro e
# inviavel, e vigiar diretorios de CLI produziria alarme por escrita
# LEGITIMA do proprio revisor (o codex grava sessao e log em `~/.codex/`
# durante a chamada). O que se vigia e a SUPERFICIE QUE A AUDITORIA
# ECONOMICA CONSOME: adulterar uma destas fontes e o caminho pelo qual
# uma escrita de fora derrubaria a politica de custo zero.
#
# A lista e acoplada por teste a `leitores_config.FONTES` — se a
# auditoria passar a ler uma fonte nova e esta lista nao acompanhar, o
# teste fica vermelho, e nao ha divergencia silenciosa.
ALVOS_VIGIADOS_FORA_DO_REPOSITORIO = (
    "~/.codex/auth.json",
    "~/.codex/config.toml",
    "~/.claude/settings.json",
    "~/.kimi-code/config.toml",
    "~/.gemini/settings.json",
    "~/.grok",
)

# O que NAO e vigiado, dito por extenso para que o rotulo possa cita-lo:
# todo o resto do disco. Escrita do revisor em qualquer caminho fora do
# repositorio e fora das fontes acima NAO e detectada por este
# mecanismo — e limite conhecido, nao propriedade.
NAO_VIGIADO = ("todo caminho fora do repositorio e fora das fontes de "
               "config declaradas")

# LAR de cada CLI de assinatura: o diretorio em que o proprio CLI grava
# sessao, log e cache DURANTE a chamada.
#
# Ele NAO e vigiado, e a razao esta escrita quatro paragrafos acima —
# vigia-lo produziria alarme por escrita LEGITIMA do CLI em toda corrida.
# Essa decisao continua de pe. O que muda na P1-A.5, ordem 3, e que ela
# deixa de ser silencio: o revisor da P1-A.4 manteve o achado A da P2
# NAO-FECHADO porque *"ha escrita em CODEX_HOME fora das fontes vigiadas,
# e o recibo ainda publica `efeito_externo: nenhum`"* — e ele esta certo.
# Nao vigiar e uma escolha defensavel; publicar ausencia sobre o que nao
# se vigia, nao.
#
# Por isso esta lista existe: para que o recibo NOMEIE, caminho por
# caminho, onde a escrita e CONHECIDA e nao medida. Ela nao liga
# vigilancia nenhuma — ela e o vocabulario da declaracao de alcance.
LAR_DO_CLI = {
    "codex": "~/.codex",
    "claude": "~/.claude",
    "kimi": "~/.kimi-code",
    "google": "~/.gemini",
    "grok": "~/.grok",
}

# Restricoes REAIS que o CLI do kimi oferece em modo headless (`-p`),
# medidas EXERCENDO o CLI 0.30.0, nao lendo `--help`: NAO existe
# `--sandbox read-only` como no codex.
#   --skills-dir DIR  carrega skills SOMENTE de DIR; apontado para um
#                     diretorio vazio, impede que skills do usuario ou do
#                     projeto sejam carregadas e ajam.
# O que NAO se passa importa tanto quanto: `-y/--yolo` e `--auto`
# auto-aprovariam chamadas de ferramenta sem perguntar. A ausencia deles
# e deliberada e verificada por teste.
FLAGS_DE_AUTO_APROVACAO = ("-y", "--yolo", "--auto")

# Flags que o CLI RECUSA em combinacao com `-p/--prompt` — medido, nao
# presumido (P1-A.3.3 §4; reexercido pelo teste de CLI real da P1-A.3.4).
# Emitir qualquer uma delas aborta a corrida na validacao de argumentos,
# antes da rede: o efeito e impedir a chamada, nunca restringi-la.
FLAGS_INCOMPATIVEIS_COM_PROMPT = ("--plan",)

# Marcador do erro de validacao de argumentos do kimi 0.30.0. O CLI
# distingue duas classes de falha, e so a segunda prova que o argv foi
# ACEITO: `error: <problema de argumento>` acontece ANTES de qualquer
# trabalho; `error: failed to run prompt: ...` so acontece DEPOIS de o
# parser aprovar o comando. O teste de CLI real usa exatamente essa
# fronteira para provar aceitacao sem gastar chamada de modelo.
PREFIXO_ERRO_DE_ARGUMENTO = "error: "
MARCADOR_ARGV_ACEITO = "failed to run prompt"


# Prefixos de caminho local que nunca podem vazar para um revisor ou
# para uma evidencia publicada. Redigidos junto com o usuario porque
# `preflight_capsula` carrega um caminho local no proprio fonte.
PREFIXOS_DE_CAMINHO_LOCAL = ("E:\\LucasIA", "E:/LucasIA")


def forma_8_3(usuario: str) -> str:
    """Forma curta (8.3) do nome de usuario, como o Windows a produz."""
    return "".join(c for c in usuario.upper() if c.isalnum())[:6] + "~1"


def redigir(texto, usuario: str | None = None) -> str:
    """Redacao CANONICA de PII e de caminho local — SSC+ P1-A.3.5.

    ACHADO 10. A varredura de guardas contou **nove** copias desta
    redacao espalhadas pelos runners, em **tres forcas diferentes**, e
    mediu que **nenhuma** tinha teste: zero ocorrencia de `_redigir`,
    `USUARIO_CURTO`, `<USUARIO>` ou `CAMINHO-LOCAL` em qualquer arquivo
    de teste das duas suites.

    As tres mais fracas — `preflight_capsula`, `preflight_atual` e
    `revisao_p1a2` — redigiam **somente a forma longa** do usuario, e
    deixavam passar a forma 8.3: exatamente a forma que
    `ZeroPiiNosArtefatos` procura. Nenhum artefato versionado a carrega
    hoje (medido: zero arquivos), de modo que nao havia violacao viva; o
    que havia era um guarda que so pegaria o caso **depois** de gravado.

    Esta e a implementacao unica, e a mais forte das tres: forma longa,
    forma 8.3 e prefixo de caminho local. `usuario` e injetavel SOMENTE
    para teste — em operacao vale o usuario real da estacao.
    """
    longo = _USUARIO_LOCAL if usuario is None else usuario
    saida = (texto or "").replace(longo, "<USUARIO>")
    saida = saida.replace(forma_8_3(longo), "<USUARIO>")
    for prefixo in PREFIXOS_DE_CAMINHO_LOCAL:
        saida = saida.replace(prefixo, "<CAMINHO-LOCAL>")
    return saida


def manifesto(raiz, excluir=EXCLUIDOS_DO_MANIFESTO) -> dict:
    """Caminho relativo (com `/`) -> SHA-256, de tudo sob `raiz`.

    Arquivo ilegivel entra como `<ilegivel>`: some do manifesto seria
    declara-lo intacto por omissao.
    """
    raiz = os.path.abspath(str(raiz))
    excluidos = {e.replace(os.sep, "/") for e in excluir}
    saida = {}
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = sorted(
            d for d in dirs
            if os.path.relpath(os.path.join(base, d),
                               raiz).replace(os.sep, "/") not in excluidos)
        for nome in sorted(arquivos):
            caminho = os.path.join(base, nome)
            rel = os.path.relpath(caminho, raiz).replace(os.sep, "/")
            try:
                with open(caminho, "rb") as f:
                    saida[rel] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                saida[rel] = "<ilegivel>"
    return saida


def _hash_de_arquivo(caminho: str) -> str:
    try:
        with open(caminho, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return "<ilegivel>"


def manifesto_de_alvos(alvos=None) -> dict:
    """SHA-256 dos alvos vigiados fora do repositorio.

    `alvos=None` resolve a lista DENTRO da funcao, e nao no `def`: assim
    a lista declarada e um ponto unico, e um teste que a substitua
    alcanca tambem os chamadores que nao a passam.

    Alvo que e ARQUIVO entra sozinho; alvo que e DIRETORIO entra com os
    arquivos do seu topo, um a um (o `~/.grok/` desta estacao guarda
    `grok.db` + `-wal` + `-shm`). Alvo AUSENTE entra como `<ausente>` —
    some-lo seria nao detectar a sua CRIACAO durante a janela, que e
    justamente uma das formas de plantar config PAYG.
    """
    saida = {}
    for alvo in (ALVOS_VIGIADOS_FORA_DO_REPOSITORIO if alvos is None
                 else alvos):
        caminho = os.path.expanduser(alvo)
        if os.path.isdir(caminho):
            try:
                nomes = sorted(os.listdir(caminho))
            except OSError:
                saida[alvo] = "<ilegivel>"
                continue
            achou = False
            for nome in nomes:
                completo = os.path.join(caminho, nome)
                if os.path.isfile(completo):
                    saida[f"{alvo}/{nome}"] = _hash_de_arquivo(completo)
                    achou = True
            if not achou:
                saida[f"{alvo}/"] = "<diretorio-vazio>"
        elif os.path.isfile(caminho):
            saida[alvo] = _hash_de_arquivo(caminho)
        else:
            saida[alvo] = "<ausente>"
    return saida


def manifesto_vigiado(raiz, alvos=None) -> dict:
    """As DUAS raizes vigiadas num so manifesto, com rotulo de origem.

    `repositorio/...` para a arvore do laboratorio (inteira, inclusive
    `locks/` e `.git`) e `fora/...` para as fontes de config declaradas.
    O rotulo existe para que a evidencia diga ONDE a mutacao ocorreu sem
    carregar caminho absoluto.
    """
    saida = {f"repositorio/{rel}": h
             for rel, h in manifesto(raiz).items()}
    saida.update({f"fora/{rel}": h
                  for rel, h in manifesto_de_alvos(alvos).items()})
    return saida


def titular_medido(raiz) -> str | None:
    """Nome que o lease do repositorio traz AGORA, ou None.

    Le do disco, sem adquirir nada e sem levantar: lease ausente,
    ilegivel ou VENCIDO devolve None. Serve a `atribuir`, que precisa
    saber de quem e o escritor no instante em que a fotografia fecha —
    nao de quem se supunha que fosse quando ela abriu.
    """
    from escritor_repositorio import titular_atual
    titular = titular_atual(os.path.join(str(raiz), "locks"))
    return None if titular is None else titular.get("sessao")


def atribuir(mudancas, sessao_lock: str, titular=None) -> dict:
    """Separa DETECCAO de ATRIBUICAO — a segunda pergunta do §6.

    `mutacoes` responde *a arvore mudou?*. Esta funcao responde *ha
    escritor esperado para esta mudanca?*. So um caminho tem escritor
    esperado durante a janela da chamada: o lease e o fence do ESCRITOR
    UNICO DO REPOSITORIO, reescritos a cada 30 s pelo renovador dedicado,
    por construcao e nao por acidente.

    P1-A.5, ordem 2 — o que mudou, e o buraco que a mudanca abriria se
    parasse na metade. Os caminhos esperados deixam de variar com o nome
    da missao: ha um lease so, `locks/repositorio.lease`. Sozinha, essa
    troca ENFRAQUECERIA a atribuicao — antes, um intruso que plantasse
    `locks/intrusa-ops.lease` caia em `nao_atribuidas` porque o nome nao
    era o esperado; com um caminho unico, ele bastaria sobrescrever o
    lease do repositorio para ser atribuido ao renovador e nao reprovar
    a corrida.

    Por isso a atribuicao passa a exigir DUAS condicoes, e nao uma:

    1. o caminho e o do escritor unico; **e**
    2. `titular` — o nome que o lease traz no fim da janela, medido em
       disco por `titular_medido` — e a sessao operacional.

    Titular ausente, vencido ou de OUTRO nome atribui **nada**: tudo cai
    em `nao_atribuidas` e a corrida reprova. Fail-closed de proposito, e
    o default `None` e parte disso — quem nao mede o titular nao atribui.

    LIMITE DECLARADO, e e o que separa esta funcao de uma prova de
    autoria: a atribuicao continua sendo por CONVENCAO, agora de caminho
    E de titular. Um revisor que sobrescrevesse o lease mantendo o nome
    da sessao operacional dentro dele ainda seria atribuido ao renovador.
    O que se afirma e que aquele par caminho/titular e o unico com
    escritor esperado — nunca que o byte veio dele. A pergunta *quem
    escreveu?* segue sem resposta, e e o remedio ainda nao entregue do
    MAJOR #3.
    """
    from escritor_repositorio import NOME_DO_LOCK

    esperados = {f"repositorio/locks/{NOME_DO_LOCK}{sufixo}"
                 for sufixo in (".lease", ".lease.tmp", ".fence",
                                ".fence.tmp")}
    if titular != sessao_lock:
        esperados = set()
    do_renovador, nao_atribuidas = [], []
    for mudanca in mudancas:
        caminho = mudanca.split(": ", 1)[-1]
        destino = do_renovador if caminho in esperados else nao_atribuidas
        destino.append(mudanca)
    return {"do_renovador": do_renovador,
            "nao_atribuidas": nao_atribuidas}


class Vigilancia:
    """Protocolo UNICO de contencao das corridas de revisao.

    Os quatro runners (`revisao_p1a3`, `_p1a31`, `_p1a33`, `_p1a36`)
    repetiam a mesma sequencia `manifesto(RAIZ)` / `mutacoes(...)` em
    copias separadas — o mecanismo dos achados 7, 10 e 14: a copia que
    ninguem exercita fica para tras. Aqui ela existe uma vez, e o teste
    de varredura exige que os quatro apontem para ESTA classe.
    """

    def __init__(self, raiz, sessao_lock: str, alvos=None):
        self.raiz = str(raiz)
        self.sessao_lock = str(sessao_lock)
        self.alvos = tuple(ALVOS_VIGIADOS_FORA_DO_REPOSITORIO
                           if alvos is None else alvos)
        self.antes = None

    def abrir(self) -> dict:
        self.antes = manifesto_vigiado(self.raiz, self.alvos)
        return self.antes

    def fechar(self) -> dict:
        """Fotografia final, deteccao e atribuicao — nesta ordem."""
        if self.antes is None:
            raise RuntimeError("Vigilancia.fechar() sem abrir()")
        depois = manifesto_vigiado(self.raiz, self.alvos)
        mudancas = mutacoes(self.antes, depois)
        # O titular e medido NO FECHAMENTO, e nao presumido pela abertura:
        # e justamente no fim da janela que se sabe quem detem o escritor.
        titular = titular_medido(self.raiz)
        atribuicao = atribuir(mudancas, self.sessao_lock, titular)
        return {
            "titular_do_escritor_no_fechamento": titular,
            "medida": "manifesto SHA-256 antes/depois das raizes "
                      "vigiadas, com atribuicao separada da deteccao",
            "raizes_vigiadas": ["repositorio (toda a arvore sob RAIZ, "
                                "inclusive locks/ e .git)"]
                               + [f"fora: {a}" for a in self.alvos],
            "nao_vigiado": NAO_VIGIADO,
            "arquivos_no_manifesto": len(self.antes),
            "mutacoes_detectadas": mudancas,
            "mutacoes_atribuidas_ao_renovador": atribuicao["do_renovador"],
            "mutacoes_fora_do_descartavel": atribuicao["nao_atribuidas"],
            "violada": bool(atribuicao["nao_atribuidas"]),
        }


def mutacoes(antes: dict, depois: dict) -> list:
    """Caminhos criados, removidos ou alterados entre dois manifestos."""
    mudou = []
    for rel in sorted(set(antes) | set(depois)):
        hash_antes, hash_depois = antes.get(rel), depois.get(rel)
        if hash_antes == hash_depois:
            continue
        if hash_antes is None:
            mudou.append(f"criado: {rel}")
        elif hash_depois is None:
            mudou.append(f"removido: {rel}")
        else:
            mudou.append(f"alterado: {rel}")
    return mudou


def argv_kimi(executavel: str, prompt: str, dir_skills: str) -> list:
    """Comando do kimi com a restricao maxima que o CLI oferece — e que ELE ACEITA.

    Sem `-y`, sem `--yolo` e sem `--auto` — ver FLAGS_DE_AUTO_APROVACAO.
    Sem `--plan` — ver FLAGS_INCOMPATIVEIS_COM_PROMPT: o CLI o recusa em
    combinacao com `-p`, e o comando inteiro morre na validacao.
    """
    return [executavel, "--skills-dir", dir_skills, "-p", prompt]


# Palavras de ALCANCE TOTAL. Nenhuma pode aparecer no rotulo: o
# mecanismo nao tem alcance total e o rotulo nao pode afirma-lo (achado
# N3). O teste que as procura e o irmao do que ja proibia "sandbox".
PALAVRAS_DE_ALCANCE_TOTAL = ("integral", "arvore inteira", "disco inteiro",
                             "qualquer mutacao", "toda mutacao",
                             "deteccao completa", "todo o sistema")


def enforcement_kimi() -> str:
    """Rotulo do enforcement do kimi — o que se mede, nao o que se quer.

    ACHADO N3. O rotulo afirmava deteccao de alcance TOTAL sobre a
    arvore, e o revisor independente mediu que ele **excedia o
    mecanismo**: a arvore fotografada era so `RAIZ`, com
    `locks/` de fora, e escrita fora do repositorio nao aparecia. Era a
    familia do MAJOR #3 no sentido literal — afirmar a propriedade em
    vez de exerce-la.

    O rotulo passa a ser CONSTRUIDO a partir dos mesmos objetos que o
    mecanismo usa (`ALVOS_VIGIADOS_FORA_DO_REPOSITORIO`, `NAO_VIGIADO`).
    Ampliar ou reduzir a cobertura muda o rotulo por construcao — nao
    por alguem lembrar de reescrever a frase. Foi por a frase e o
    mecanismo serem objetos independentes que um pode ter passado o
    outro.
    """
    alvos = ", ".join(ALVOS_VIGIADOS_FORA_DO_REPOSITORIO)
    return ("sem sandbox de filesystem no CLI (nao ha equivalente ao "
            "`--sandbox read-only` do codex) e sem plan mode em headless "
            "(o CLI recusa `--plan` com `-p`): restricao PARCIAL por "
            "`--skills-dir` vazio, sem `-y/--yolo/--auto`; "
            "cwd descartavel; e DETECCAO DE ALCANCE DECLARADO por "
            "manifesto SHA-256 antes/depois da chamada, sobre duas "
            "raizes — a arvore do repositorio (inclusive `locks/` e "
            f"`.git`) e as fontes de config declaradas ({alvos}). "
            f"NAO detecta escrita em {NAO_VIGIADO}. A mutacao detectada "
            "passa por ATRIBUICAO: o lease da sessao operacional tem "
            "escritor esperado (o renovador); o que nao tem escritor "
            "esperado reprova a corrida")


def verificar_lock(raiz, sessao: str, fence_esperado: int | None = None,
                   agora: float | None = None) -> dict:
    """Lease vivo + fence do titular do escritor unico.

    MAJOR #4: chamar IMEDIATAMENTE ANTES DE CADA PERSISTENCIA, nao
    apenas na abertura do trabalho. Com `fence_esperado`, exige tambem
    que o titular NAO tenha sido substituido — fence diferente significa
    que outra sessao adquiriu o escritor no intervalo, e esta gravacao
    seria escrita de escritor obsoleto. Fail-closed nos tres casos
    (lease ilegivel, lease morto, fence divergente): PARADA sem gravar.

    P1-A.5, ordem 2 (ACHADO 4 / N1 / `P1A4-1`): o lease lido e o UNICO do
    repositorio (`escritor_repositorio.caminho_lease`), nunca mais
    `locks/<sessao>.lease`. `sessao` deixa de escolher o ARQUIVO e passa
    a ser o TITULAR exigido: se o lease do repositorio nomeia outra
    missao, esta chamada PARA. Antes, duas missoes de nomes diferentes
    liam arquivos diferentes e cada uma se via como escritor unico — o
    proprio ACHADO 4, na porta de entrada da persistencia.
    """
    import json

    from escritor_repositorio import (caminho_fence, caminho_lease,
                                      lease_expirado)

    base = os.path.join(str(raiz), "locks")
    caminho = caminho_lease(base)
    try:
        with open(caminho, encoding="utf-8") as f:
            lease = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: lease ilegivel/ausente: {exc}")
    if lease.get("sessao") != sessao:
        raise SystemExit(
            f"PARADA: o escritor unico do repositorio e de "
            f"{lease.get('sessao')!r}, nao de {sessao!r}")
    if lease_expirado(caminho, agora):
        raise SystemExit("PARADA: lease da sessao operacional morto")
    try:
        with open(caminho_fence(base), encoding="ascii") as f:
            fence = int(f.read().strip())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: fence ilegivel/ausente: {exc}")
    if fence_esperado is not None and fence != fence_esperado:
        raise SystemExit(
            f"PARADA: titular do escritor substituido (fence {fence} != "
            f"{fence_esperado}); escritor obsoleto NAO grava")
    return {"sessao": lease["sessao"], "pid_titular": lease["pid"],
            "fence": fence}
