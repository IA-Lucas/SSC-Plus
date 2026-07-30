"""Auditoria economica pre-invocacao do SSC+ P1-A (experimental, sem autoridade).

Espelha a POLITICA_ECONOMICA imutavel da camada P0 (05_p0/ssc_p0/frota.py)
sem importa-la: external_variable_cost_cap = 0; subscription_oauth = ALLOW;
payg_api = DENY; extra_usage = DENY; auto_topup = DENY;
unknown_billing_mode = DENY.

Toda violacao e um erro tipado derivado de ErroPreflight, com `codigo`
estavel (ex.: "P1A-PAYG-ENV") e `detalhe`. As auditorias NUNCA retornam
valores de credenciais — somente nomes de variaveis/campos.
"""

import os
import re
from types import MappingProxyType
from urllib.parse import urlparse

POLITICA_ECONOMICA = MappingProxyType({
    "external_variable_cost_cap": 0,
    "subscription_oauth": "ALLOW",
    "local_model": "ALLOW",
    "payg_api": "DENY",
    "extra_usage": "DENY",
    "auto_topup": "DENY",
    "unknown_billing_mode": "DENY",
})

# Nomes PAYG conhecidos, SEMPRE comparados em lowercase (Windows tem
# variaveis de ambiente case-insensitive: OpenAI_Api_Key == OPENAI_API_KEY).
CHAVES_PAYG_CONHECIDAS = frozenset({
    "openai_api_key", "codex_api_key", "anthropic_api_key",
    "anthropic_auth_token", "gemini_api_key", "google_api_key",
    "google_application_credentials", "xai_api_key",
})
# Sufixos de nome de credencial, comparados sobre o nome NORMALIZADO (so
# letras/digitos, lowercase). Assim `api_key`, `API_KEY`, `apiKey`,
# `openai_api_key` e `providers.openai.api-key` caem todos na mesma regra:
# o nome nu, sem prefixo de provedor, tambem e chave persistida.
_SUFIXOS_PAYG = frozenset({
    "apikey", "apitoken", "authtoken", "accesstoken", "bearertoken",
    "apisecret", "secretkey",
})

# Familias de PROVEDOR DE MODELO. Separam dois escopos que nao sao o
# mesmo: SANITIZAR (amplo — qualquer nome com cara de credencial sai do
# subprocesso, inclusive tokens locais de ferramentas como o IPC do VS
# Code) e BLOQUEAR (estreito — somente credencial de provedor de modelo
# caracteriza `payg_api = DENY`). Um token local de editor nao e canal
# tarifado de IA: filtra-se, mas nao se acusa PAYG.
_FAMILIAS_PROVEDOR = frozenset({
    "openai", "codex", "anthropic", "claude", "gemini", "google", "vertex",
    "xai", "grok", "kimi", "moonshot", "openrouter", "azureopenai",
    "deepseek", "mistral", "cohere", "groq", "nvidia", "together",
    "fireworks", "perplexity", "replicate", "huggingface",
})

# Hosts de API paga (PAYG) que nunca podem ser o endpoint de uma assinatura.
_ENDPOINTS_PAYG = (
    "api.openai.com", "api.anthropic.com", "api.x.ai",
    "generativelanguage.googleapis.com",
)
_CHAVES_ENDPOINT = frozenset({
    "base_url", "baseurl", "api_base", "api_base_url", "endpoint",
    "base_url_override", "api_endpoint", "url", "api_url", "server",
    "host",
})
# Mesmas chaves NORMALIZADAS (so letras/digitos, lowercase): base_url,
# baseUrl, api-base-url, API-BASE-URL e variantes recebem exatamente o
# mesmo tratamento — nenhuma grafia escapa da auditoria de endpoint.
_CHAVES_ENDPOINT_NORMALIZADAS = frozenset(
    re.sub(r"[^a-z0-9]", "", c) for c in _CHAVES_ENDPOINT)
# Flags de auto top-up / extra usage (normalizadas: so letras, lowercase).
_FLAGS_TOPUP = frozenset({
    "autotopup", "autotopupenabled", "extrausage", "extrausageenabled",
    "allowextracharges", "payasyougo",
})
# Modos de auth reconhecidos como canal de assinatura/local. Qualquer
# outro valor PRESENTE em auth_mode e desconhecido = DENY (fail-closed);
# campo ausente/vazio e coberto pela regra de billing desconhecido.
_AUTH_CONHECIDAS = frozenset({
    "subscription-oauth", "cached-token", "local",
})


# --- Erros tipados ------------------------------------------------------------

class ErroPreflight(Exception):
    """Base dos erros de preflight: codigo estavel + detalhe (sem segredos)."""

    codigo = "P1A-GENERICO"

    def __init__(self, detalhe: str = "", codigo: str | None = None,
                 alvo: str | None = None):
        if codigo is not None:
            self.codigo = codigo
        self.detalhe = detalhe
        self.alvo = alvo  # nome de variavel/campo — NUNCA o valor
        super().__init__(f"{self.codigo}: {detalhe}")

    def to_dict(self) -> dict:
        return {"tipo": type(self).__name__, "codigo": self.codigo,
                "detalhe": self.detalhe, "alvo": self.alvo}

    @staticmethod
    def from_dict(dados: dict) -> "ErroPreflight":
        cls = _TIPOS_ERRO[dados["tipo"]]
        return cls(detalhe=dados.get("detalhe", ""),
                   codigo=dados.get("codigo"), alvo=dados.get("alvo"))


class ChavePaygDetectada(ErroPreflight):
    """Variavel PAYG presente no ambiente (payg_api = DENY)."""
    codigo = "P1A-PAYG-ENV"


class ConfigPaygPersistida(ErroPreflight):
    """Config persistida com chave PAYG, endpoint pago ou top-up ligado."""
    codigo = "P1A-PAYG-CONFIG"


class OAuthAusente(ErroPreflight):
    """Login OAuth da assinatura ausente ou origem divergente da esperada."""
    codigo = "P1A-OAUTH-AUSENTE"


class PlanoNaoReconhecido(ErroPreflight):
    """Plano reportado pelo CLI fora da lista de planos aceitos."""
    codigo = "P1A-PLANO-DESCONHECIDO"


class QuotaEsgotada(ErroPreflight):
    """Franquia da assinatura esgotada: nenhuma invocacao permitida."""
    codigo = "P1A-QUOTA-ESGOTADA"


class BillingDesconhecido(ErroPreflight):
    """Billing desconhecido = DENY (unknown_billing_mode)."""
    codigo = "P1A-BILLING-DESCONHECIDO"


class CliIndisponivel(ErroPreflight):
    """Executavel do CLI ausente ou sem resposta."""
    codigo = "P1A-CLI-INDISPONIVEL"


class ModeloRemovido(ErroPreflight):
    """Descoberta real sem nenhum dos modelos esperados da assinatura."""
    codigo = "P1A-MODELO-REMOVIDO"


class ConflitoAmbienteLogin(ErroPreflight):
    """Chave PAYG do provedor no ambiente com login OAuth ativo.

    A chave NUNCA pode vencer o OAuth da assinatura: a coexistencia e
    bloqueio, nao fallback.
    """
    codigo = "P1A-CONFLITO-ENV-LOGIN"


_TIPOS_ERRO = {c.__name__: c for c in (
    ChavePaygDetectada, ConfigPaygPersistida, OAuthAusente,
    PlanoNaoReconhecido, QuotaEsgotada, BillingDesconhecido,
    CliIndisponivel, ModeloRemovido, ConflitoAmbienteLogin)}


# --- Auditorias ---------------------------------------------------------------

def _normalizar_nome(nome: str) -> str:
    """Nome reduzido a letras/digitos minusculos (caixa e separadores fora)."""
    return re.sub(r"[^a-z0-9]", "", str(nome).lower())


def _nome_payg(nome: str) -> bool:
    """Nome tem cara de credencial? (escopo AMPLO — sanitizacao/config.)

    Comparacao SEMPRE case-insensitive (no Windows `OpenAI_Api_Key` e a
    mesma variavel que `OPENAI_API_KEY`) e insensivel a separadores, para
    que `api_key`, `apiKey` e `api-key` sejam o mesmo campo. Numa config
    persistida de CLI, o campo `api_key` NU ja e chave substituindo OAuth.
    """
    if nome.lower() in CHAVES_PAYG_CONHECIDAS:
        return True
    normalizado = _normalizar_nome(nome)
    return any(normalizado.endswith(s) for s in _SUFIXOS_PAYG)


def _nome_payg_provedor(nome: str) -> bool:
    """Credencial de PROVEDOR DE MODELO? (escopo ESTREITO — bloqueio.)

    Somente estes nomes caracterizam `payg_api = DENY` no ambiente: uma
    chave de provedor de IA. Credencial local de outra ferramenta (por
    exemplo `VSCODE_GIT_IPC_AUTH_TOKEN`) e sanitizada pelo escopo amplo,
    mas nao e canal tarifado de IA e nao pode bloquear a frota.
    """
    if nome.lower() in CHAVES_PAYG_CONHECIDAS:
        return True
    normalizado = _normalizar_nome(nome)
    if not any(normalizado.endswith(s) for s in _SUFIXOS_PAYG):
        return False
    return any(f in normalizado for f in _FAMILIAS_PROVEDOR)


def ambiente_sanitizado(env: dict | None = None) -> dict:
    """Copia do ambiente SEM chaves PAYG (case-insensitive).

    Nunca muta `os.environ` nem o dict recebido: as credenciais globais do
    usuario permanecem intactas — elas apenas nao entram no subprocesso.
    """
    fonte = dict(os.environ if env is None else env)
    return {k: v for k, v in fonte.items() if not _nome_payg(k)}


def auditar_ambiente(env: dict) -> list:
    """Detecta credenciais de PROVEDOR no ambiente (case-insensitive).

    Escopo de bloqueio: chave de provedor de modelo. Credenciais locais de
    outras ferramentas nao entram aqui — elas sao apenas sanitizadas por
    `ambiente_sanitizado`. Retorna lista de ChavePaygDetectada. NUNCA
    inclui valores — somente os nomes, na caixa original.
    """
    violacoes = []
    for nome in sorted(env):
        if _nome_payg_provedor(nome):
            violacoes.append(ChavePaygDetectada(
                detalhe=f"variavel PAYG no ambiente: {nome} "
                        "(payg_api = DENY)", alvo=nome))
    return violacoes


def _achatar(persistido, prefixo: str = "", chave_pai: str | None = None):
    """Achatamento recursivo de dicts E listas: (caminho, chave, valor).

    Dicts rendem `pai.filho`; listas rendem `pai[indice]` e tambem sao
    percorridas — uma chave PAYG dentro de uma lista de providers nao
    escapa da auditoria. Itens escalares de lista herdam o nome do
    campo pai, para que `base_url: ["https://host"]` receba o mesmo
    tratamento que `base_url: "https://host"`.
    """
    itens = persistido.items() if isinstance(persistido, dict) \
        else enumerate(persistido)
    for chave, valor in itens:
        if isinstance(persistido, dict):
            caminho = f"{prefixo}.{chave}" if prefixo else str(chave)
            nome = str(chave)
        else:
            caminho = f"{prefixo}[{chave}]"
            nome = chave_pai if chave_pai is not None else str(chave)
        if isinstance(valor, (dict, list)):
            yield from _achatar(valor, caminho, nome)
        else:
            yield caminho, nome, valor


def _host_de(url: str) -> str:
    """Somente o host da URL — caminho/query podem carregar segredos."""
    texto = url if "://" in url else f"https://{url}"
    return urlparse(texto).hostname or url


def _verdadeiro(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return valor != 0
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "1", "on", "yes", "enabled")
    return False


def auditar_config(persistido: dict) -> list:
    """Detecta PAYG na configuracao persistida do CLI (auth.json, settings).

    Tres violacoes: chave de API persistida substituindo OAuth; endpoint
    PAYG configurado quando o canal deveria ser assinatura; flags de auto
    top-up / extra usage ligados. Nunca retorna valores, somente caminhos.
    """
    violacoes = []
    for caminho, chave, valor in _achatar(persistido or {}):
        low = chave.lower()
        normalizado = _normalizar_nome(chave)
        if isinstance(valor, str) and valor.strip():
            if _nome_payg(low):
                violacoes.append(ConfigPaygPersistida(
                    detalhe="chave de API persistida substituindo OAuth: "
                            f"{caminho} (payg_api = DENY)", alvo=caminho))
                continue
            if normalizado in _CHAVES_ENDPOINT_NORMALIZADAS \
                    and any(h in valor.lower() for h in _ENDPOINTS_PAYG):
                violacoes.append(ConfigPaygPersistida(
                    detalhe="endpoint PAYG configurado: "
                            f"{_host_de(valor)} (canal deveria ser "
                            "assinatura)", alvo=caminho))
        if normalizado in _FLAGS_TOPUP and _verdadeiro(valor):
            violacoes.append(ConfigPaygPersistida(
                detalhe=f"auto top-up/extra usage ligado: {caminho} "
                        "(extra_usage/auto_topup = DENY)", alvo=caminho))
    return violacoes


def auditar_status(entry: dict) -> list:
    """Vetos economicos sobre o status declarado da assinatura.

    billing_mode deve ser "subscription" (desconhecido = DENY),
    variable_cost == 0 e auth_mode diferente de payg. Fail-closed: um
    auth_mode PRESENTE mas nao reconhecido tambem e DENY — billing ou
    auth desconhecidos nunca viram ELIGIBLE por inferencia.
    """
    violacoes = []
    billing = (entry.get("billing_mode") or "").strip().lower()
    if billing in ("", "desconhecido", "unknown"):
        violacoes.append(BillingDesconhecido(
            detalhe="billing_mode desconhecido = DENY "
                    "(unknown_billing_mode)"))
    elif billing != "subscription":
        violacoes.append(ConfigPaygPersistida(
            codigo="P1A-PAYG-BILLING",
            detalhe=f"billing_mode={billing} fora da assinatura "
                    "(payg/extra_usage/auto_topup = DENY)"))
    if entry.get("variable_cost", 0) != 0:
        violacoes.append(ConfigPaygPersistida(
            codigo="P1A-PAYG-CUSTO",
            detalhe=f"variable_cost={entry.get('variable_cost')} > "
                    "external_variable_cost_cap = 0"))
    auth = (entry.get("auth_mode") or "").strip().lower()
    if auth in ("payg", "payg-api", "api-key", "api_key"):
        violacoes.append(ConfigPaygPersistida(
            codigo="P1A-PAYG-AUTH",
            detalhe=f"auth_mode={auth}: payg_api = DENY"))
    elif auth and auth not in _AUTH_CONHECIDAS:
        violacoes.append(OAuthAusente(
            codigo="P1A-AUTH-DESCONHECIDA",
            detalhe=f"auth_mode={auth} nao reconhecido = DENY "
                    "(ausencia de evidencia = unknown, nunca inferido)"))
    return violacoes
