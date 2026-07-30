"""Especificacao estatica da frota real (SSC+ P1-A, experimental).

Dados declarados, editaveis pelo orquestrador: valores reais conhecidos
hoje dos 5 CLIs de assinatura. Nada aqui e executado — os comandos sao
somente descritores de diagnostico usados pelos adaptadores via sensores.

Regras da missao:
- google: permanece SUPERVISED (automacao condicional ate prova do canal);
  NAO reutilizar OAuth em cliente nao autorizado.
- grok: permanece SUPERVISED; somente cached token da assinatura, NUNCA
  XAI_API_KEY, nunca api.x.ai PAYG; unattended = TERMS_REVIEW_REQUIRED.

Nenhum caminho local e embutido no fonte: o executavel do Codex deriva do
home da estacao em tempo de importacao (os.path.expanduser).
"""

import os
from dataclasses import dataclass

_CODEX_EXE = os.path.join(
    os.path.expanduser("~"), "AppData", "Local", "Programs", "OpenAI",
    "Codex", "bin", "codex.exe")


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
    comandos: dict                  # versao/login/modelos: argv de diagnostico
    billing_mode: str = "subscription"
    variable_cost: float = 0.0
    teto_resultado: str = "ELIGIBLE"  # google/grok: "SUPERVISED"
    automacao: str = "allow-supervised"
    observacoes: str = ""


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
                  "modelos": ("models",)},
        observacoes="automacao: allow (supervised headless); billing "
                    "subscription; variable_cost 0"),
    "claude": EspecProvedor(
        provider_id="claude", cli="claude", versao_esperada="2.1.220",
        executavel="~/.local/bin/claude",
        canal_oficial="claude.ai OAuth (`claude auth status` devolve JSON "
                      "com subscriptionType)",
        headless=("-p",), acp=None,
        plano_esperado="Claude Max 5x",
        planos_aceitos=("claude max 5x", "claude max", "max"),
        modelos_esperados=("claude-opus", "claude-sonnet"),
        auth_esperada="subscription-oauth",
        chaves_payg_relacionadas=("ANTHROPIC_API_KEY",
                                  "ANTHROPIC_AUTH_TOKEN"),
        comandos={"versao": ("--version",),
                  "login": ("auth", "status"),
                  "modelos": ("models",)},
        observacoes="headless `claude -p`; billing subscription"),
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
        observacoes="4 modelos via provider list; ACP disponivel "
                    "(`kimi acp`); billing subscription"),
    "google": EspecProvedor(
        provider_id="google", cli="gemini", versao_esperada="0.52.0",
        executavel="gemini",  # npm
        canal_oficial="oauth-personal (security.auth.selectedType em "
                      "~/.gemini/settings.json)",
        headless=("-p",), acp=("--acp",),
        plano_esperado="Google AI Pro",
        planos_aceitos=("google ai pro", "ai pro"),
        modelos_esperados=("gemini",),
        auth_esperada="subscription-oauth",
        chaves_payg_relacionadas=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        comandos={"versao": ("--version",),
                  "login": ("auth", "status"),
                  "modelos": ("--list-models",)},
        teto_resultado="SUPERVISED",
        automacao="supervised-only",
        observacoes="regra da missao: permanece SUPERVISED (automacao "
                    "condicional ate prova do canal); NAO reutilizar OAuth "
                    "em cliente nao autorizado"),
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
                  "modelos": ("models",)},
        teto_resultado="SUPERVISED",
        automacao="supervised-only",
        observacoes="regra da missao: SUPERVISED; somente cached token da "
                    "assinatura, NUNCA XAI_API_KEY, nunca api.x.ai PAYG; "
                    "unattended = TERMS_REVIEW_REQUIRED"),
}


def frota_real() -> list:
    """As cinco especificacoes estaticas, na ordem declarada."""
    return list(ESPECIFICACOES.values())


def espec_de(provider_id: str) -> EspecProvedor:
    """Especificacao de um provedor pelo identificador."""
    return ESPECIFICACOES[provider_id]
