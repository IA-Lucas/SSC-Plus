"""Especificacao estatica da frota real (SSC+ P1-A, experimental).

Dados declarados, editaveis pelo orquestrador: valores reais conhecidos
hoje dos 5 CLIs de assinatura. Nada aqui e executado — os comandos sao
somente descritores de diagnostico usados pelos adaptadores via sensores.

Regras da missao:
- google: usa o CLI oficial Antigravity (`agy`) e somente a franquia da
  assinatura; API/creditos extras continuam proibidos.
- grok: permanece SUPERVISED; somente cached token da assinatura, NUNCA
  XAI_API_KEY, nunca api.x.ai PAYG; unattended = TERMS_REVIEW_REQUIRED.
- claude: o modelo exato vem da configuracao persistida do proprio CLI e
  e fixado novamente em toda invocacao produtiva.

Nenhum caminho local e embutido no fonte: o executavel do Codex usa a
forma com `~`, expandida SOMENTE no momento da sonda
(`AdaptadorPreflight._argv`) — assim nem a especificacao, nem os
relatorios, nem as excecoes carregam o diretorio do usuario local
(revisao P1-A.3, rodada 3).
"""

from dataclasses import dataclass

_CODEX_EXE = "~/AppData/Local/Programs/OpenAI/Codex/bin/codex.exe"
_AGY_EXE = "~/AppData/Local/agy/bin/agy.exe"

# Marcador trocado pelo diretorio descartavel NO MOMENTO DA INVOCACAO
# (P2.3). A especificacao e estatica e o descartavel so existe quando a
# chamada acontece; sem marcador, ou a especificacao carregaria um
# caminho — e ela nao carrega caminho local por decisao da rodada 3 da
# revisao P1-A.3 —, ou o montador de argv precisaria saber a POSICAO da
# flag, que e conhecimento do CLI vivendo fora da especificacao dele.
MARCA_DESCARTAVEL = "<DESCARTAVEL>"


@dataclass(frozen=True)
class EspecProvedor:
    """Especificacao estatica de um provedor de assinatura."""

    provider_id: str
    cli: str                        # nome do comando
    versao_esperada: str            # versao conhecida hoje (informativo)
    executavel: str                 # caminho conhecido ou nome no PATH
    canal_oficial: str              # descricao do canal de assinatura
    headless: tuple                 # argv do modo headless (NUNCA usado aqui)
    acp: tuple | None               # argv ACP, quando disponivel
    plano_esperado: str             # nome legivel do plano
    planos_aceitos: tuple           # substrings lowercase aceitas
    modelos_esperados: tuple        # minimo que a descoberta deve conter
    auth_esperada: str              # subscription-oauth | cached-token
    chaves_payg_relacionadas: tuple # variaveis PAYG deste provedor
    comandos: dict                  # versao/login/modelos: argv de
                                    # diagnostico; modelos=None desativa
                                    # a descoberta (teto SUPERVISED)
    billing_mode: str = "subscription"
    variable_cost: float = 0.0
    teto_resultado: str = "ELIGIBLE"  # grok: "SUPERVISED"
    automacao: str = "allow-supervised"
    # Provedor sem canal diagnostico automatizavel fica classificado
    # estaticamente no teto, sem sensor de versao/login/modelos.
    sondas_automaticas: bool = True
    observacoes: str = ""
    # Flags de restricao REAL que o CLI oferece em modo headless, emitidas
    # ENTRE `headless` e o prompt (P2.3, achado A). Vazio significa
    # exatamente o que diz: o CLI nao oferece restricao de filesystem, e o
    # rotulo NAO pode afirmar sandbox que nao existe (achado N3 / MAJOR #3
    # — o kimi 0.30.0 devolve `unknown option '--sandbox'`, medido na
    # P1-A.3.4). Contem `MARCA_DESCARTAVEL` onde entra o diretorio
    # descartavel da invocacao.
    restricao_headless: tuple = ()
    flag_modelo: tuple = ()
    # Formato de saida exigido no caminho produtivo. Separado das flags de
    # restricao para que telemetria/parse nao seja rotulada como sandbox.
    formato_saida_headless: tuple = ()
    caminho_modelo_config: tuple = ()
    # Alguns CLIs (`agy`, `kimi`) exigem o texto logo apos `-p`; outros
    # (codex, claude) aceitam/esperam flags antes do argumento posicional.
    prompt_antes_das_flags: bool = False
    # No Windows, prompts grandes excedem o limite da linha de comando.
    # Codex e Claude documentam leitura por stdin em modo print/exec.
    prompt_via_stdin: bool = False


ESPECIFICACOES: dict[str, EspecProvedor] = {
    "codex": EspecProvedor(
        provider_id="codex", cli="codex", versao_esperada="0.145.0",
        executavel=_CODEX_EXE,
        canal_oficial="ChatGPT (login OAuth 'chatgpt', confirmado via "
                      "`codex login status`)",
        headless=("exec",), acp=None,
        plano_esperado="ChatGPT Pro 5x",
        planos_aceitos=("chatgpt pro 5x", "chatgpt pro", "pro"),
        modelos_esperados=("gpt-5",),
        auth_esperada="subscription-oauth",
        chaves_payg_relacionadas=("OPENAI_API_KEY", "CODEX_API_KEY"),
        comandos={"versao": ("--version",),
                  "login": ("login", "status"),
                  # Emenda P1-A.3, item 2 (APROVADA): `codex doctor`
                  # comprova o modelo efetivo atual e o auth mode — NAO
                  # equivale a catalogo completo (`codex models` e
                  # TTY-only, bloqueio factual da P1-A.2).
                  "modelos": ("doctor",)},
        # P2.3, achado A: as MESMAS flags que `prova_minima.py:46` ja
        # passava na P1-A e que a P2 nao herdou. Medidas contra o CLI
        # 0.145.0, nao lidas em `--help`: `--sandbox read-onlyX` e
        # recusado com `[possible values: read-only, workspace-write,
        # danger-full-access]`, e o argv completo abaixo faz o CLI
        # imprimir `sandbox: read-only` e `workdir: <descartavel>` no
        # proprio cabecalho antes de morrer sem credencial.
        # `--skip-git-repo-check` acompanha `--cd` por necessidade: o
        # descartavel nao e repositorio Git, e sem ele o CLI recusa
        # rodar ali.
        restricao_headless=("--sandbox", "read-only",
                            "--cd", MARCA_DESCARTAVEL,
                            "--skip-git-repo-check", "--ephemeral"),
        flag_modelo=("--model",),
        prompt_via_stdin=True,
        observacoes="automacao: allow (supervised headless); billing "
                    "subscription; variable_cost 0"),
    "claude": EspecProvedor(
        provider_id="claude", cli="claude", versao_esperada="2.1.220",
        executavel="~/.local/bin/claude.exe",
        canal_oficial="claude.ai OAuth (`claude auth status` devolve JSON "
                      "com subscriptionType)",
        headless=("-p",), acp=None,
        plano_esperado="Claude Max 5x",
        planos_aceitos=("claude max 5x", "claude max", "max"),
        modelos_esperados=("claude-",),
        auth_esperada="subscription-oauth",
        chaves_payg_relacionadas=("ANTHROPIC_API_KEY",
                                  "ANTHROPIC_AUTH_TOKEN"),
        comandos={"versao": ("--version",),
                  "login": ("auth", "status"),
                  # `claude models` continua interativo. O modelo exato
                  # vem da configuracao persistida oficial do proprio CLI.
                  "modelos": None},
        restricao_headless=("--permission-mode", "plan",
                            "--no-session-persistence",
                            "--disable-slash-commands"),
        flag_modelo=("--model",),
        caminho_modelo_config=("model",),
        prompt_via_stdin=True,
        observacoes="headless `claude -p`; modelo observado na config e "
                    "fixado por argv; permission-mode plan; billing "
                    "subscription"),
    "kimi": EspecProvedor(
        provider_id="kimi", cli="kimi", versao_esperada="0.30.0",
        executavel="~/.kimi-code/bin/kimi",
        canal_oficial="managed:kimi-code type=kimi source=oauth "
                      "(`kimi provider list`)",
        headless=("-p",), acp=("acp",),
        plano_esperado="Allegretto",
        planos_aceitos=("allegretto",),
        modelos_esperados=("kimi",),
        auth_esperada="subscription-oauth",
        chaves_payg_relacionadas=("KIMI_API_KEY", "MOONSHOT_API_KEY"),
        comandos={"versao": ("--version",),
                  "login": ("provider", "list"),
                  "modelos": ("provider", "list")},
        flag_modelo=("-m",),
        formato_saida_headless=("--output-format", "stream-json"),
        # O Commander do kimi exige o argumento de -p imediatamente depois
        # da flag. `kimi -p -m <modelo> <prompt>` interpreta o modelo como
        # comando e responde `unknown command`; a forma aceita e
        # `kimi -p <prompt> -m <modelo>`.
        prompt_antes_das_flags=True,
        # `restricao_headless` fica VAZIA de proposito, e a ausencia e o
        # achado: o kimi 0.30.0 devolve `unknown option '--sandbox'` e
        # recusa `--plan` junto com `-p` (medido na P1-A.3.4, nao lido em
        # `--help`). Nao ha flag de filesystem a emitir, e inventar uma
        # rotularia isolamento inexistente.
        observacoes="4 modelos via provider list; ACP disponivel "
                    "(`kimi acp`); billing subscription"),
    "google": EspecProvedor(
        provider_id="google", cli="agy", versao_esperada="1.1.12",
        executavel=_AGY_EXE,
        canal_oficial="Google Antigravity CLI oficial, quota da assinatura "
                      "observada por `/quota` sem turno de modelo",
        headless=("-p",), acp=None,
        plano_esperado="Google AI Pro",
        planos_aceitos=("google ai pro", "ai pro"),
        modelos_esperados=("gemini",),
        auth_esperada="subscription-oauth",
        chaves_payg_relacionadas=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        comandos={"versao": ("changelog",),
                  "login": ("-p", "/quota", "--output-format", "json",
                            "--mode", "plan"),
                  "modelos": ("models",)},
        # `--add-dir` poe o DESCARTAVEL no workspace do agy: sem ele a
        # leitura de contexto-ssc.txt cai na permissao `command`, que o
        # headless auto-nega, e o turno termina SUCCESS com resposta
        # vazia (medido em 2026-08-12; recibos fluxo-20260812T0111*/0119*).
        # Nao amplia alcance: e o mesmo diretorio que ja e cwd do filho.
        restricao_headless=("--output-format", "json", "--mode", "plan",
                            "--sandbox", "--disable-slash-commands",
                            "--add-dir", MARCA_DESCARTAVEL),
        flag_modelo=("--model",),
        prompt_antes_das_flags=True,
        observacoes="canal oficial Antigravity; quota de assinatura e "
                    "modelos Gemini observados sem turno produtivo; "
                    "plan+sandbox; API/creditos extras proibidos"),
    "grok": EspecProvedor(
        provider_id="grok", cli="grok", versao_esperada="1.1.7",
        executavel="grok",  # npm
        canal_oficial="Grok Build da assinatura (cached token)",
        headless=("-p",), acp=None,
        plano_esperado="SuperGrok",
        planos_aceitos=("supergrok",),
        modelos_esperados=("grok",),
        auth_esperada="cached-token",
        chaves_payg_relacionadas=("XAI_API_KEY",),
        comandos={"versao": ("--version",),
                  "login": ("auth", "status"),
                  # Emenda P1-A.3, item 5: ZERO sondas automaticas de
                  # modelos para grok (idem google).
                  "modelos": None},
        teto_resultado="SUPERVISED",
        automacao="supervised-only",
        sondas_automaticas=False,
        observacoes="regra da missao: SUPERVISED; somente cached token da "
                    "assinatura, NUNCA XAI_API_KEY, nunca api.x.ai PAYG; "
                    "unattended = TERMS_REVIEW_REQUIRED"),
}


# Palavras que AFIRMAM restricao do CLI. Nenhuma pode aparecer no rotulo
# de um provedor cuja `restricao_headless` esteja vazia — a licao do
# achado N3, aqui aplicada ao outro rotulo do acervo: o kimi nao tem
# sandbox de filesystem, e dizer que tem seria afirmar a propriedade em
# vez de exerce-la (MAJOR #3).
PALAVRAS_DE_RESTRICAO_DO_CLI = ("sandbox", "read-only", "somente leitura",
                                "isolad", "efemer")


def rotulo_restricao(espec) -> str:
    """O que a restricao E — CONSTRUIDO a partir das flags que serao emitidas.

    Nao ha frase fixa: o rotulo se monta a partir de
    `espec.restricao_headless`, o MESMO objeto que o executor emite. Uma
    flag removida some do rotulo por construcao, e uma flag acrescentada
    aparece — nunca por alguem lembrar de reescrever a frase. Foi por a
    frase e o mecanismo serem objetos independentes que um pode ter
    passado o outro (achado N3, `contencao.enforcement_kimi`).

    Vazio nao vira silencio: o rotulo diz, por extenso, que o CLI nao
    oferece restricao de filesystem e nomeia o que sobra.
    """
    if not espec.restricao_headless:
        return (f"o CLI `{espec.cli}` NAO oferece restricao de filesystem "
                "em modo headless: nenhuma flag de restricao e emitida. O "
                "que resta e o diretorio de trabalho descartavel do "
                "processo filho e a deteccao por manifesto SHA-256 antes e "
                "depois da invocacao (`contencao.Vigilancia`) — deteccao "
                "declarada, jamais impedimento")
    flags = " ".join(espec.restricao_headless)
    return (f"restricao emitida ao CLI `{espec.cli}` em modo headless: "
            f"`{flags}` (o marcador {MARCA_DESCARTAVEL} e trocado pelo "
            "diretorio descartavel da invocacao), mais o diretorio de "
            "trabalho descartavel do processo filho e a deteccao por "
            "manifesto SHA-256 antes e depois (`contencao.Vigilancia`). O "
            "que a flag FAZ dentro do turno do modelo e propriedade do CLI "
            "externo e NAO foi medido aqui")


def frota_real() -> list:
    """As cinco especificacoes estaticas, na ordem declarada."""
    return list(ESPECIFICACOES.values())


def espec_de(provider_id: str) -> EspecProvedor:
    """Especificacao de um provedor pelo identificador."""
    return ESPECIFICACOES[provider_id]
