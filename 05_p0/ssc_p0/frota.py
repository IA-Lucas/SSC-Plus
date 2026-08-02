"""Frota subscription-only do SSC+ (ADENDO 0.3 — evolucao experimental).

Cinco assinaturas iniciais (Codex/ChatGPT Pro, Claude Code/Max, Kimi
Code/Allegretto, Google Antigravity/AI Pro, Grok Build/SuperGrok). Toda
escolha ocorre por WorkUnit/ExecutionAttempt DENTRO do mesmo
SessionEnvelope — nenhum provedor fica vinculado a sessao inteira.

POLITICA ECONOMICA IMUTAVEL (POLITICA_ECONOMICA):
external_variable_cost_cap = 0; subscription_oauth = ALLOW;
local_model = ALLOW; payg_api = DENY; extra_usage = DENY;
auto_topup = DENY; unknown_billing_mode = DENY.

Regras de canal:
- CLIs executam em ambiente SANITIZADO (ambiente_sanitizado): chaves PAYG
  nunca entram no processo SSC+; as credenciais globais NAO sao apagadas.
- API key presente NUNCA substitui o OAuth da assinatura.
- Grok: somente Grok Build da assinatura (cached token, headless ou ACP);
  NUNCA api.x.ai. GROK_SUPERVISED = ALLOW;
  GROK_UNATTENDED = TERMS_REVIEW_REQUIRED.
- Google: somente canal oficial da assinatura; automacao condicional ate
  prova do canal permitido.

QUOTA_EXHAUSTED: registra evento, preserva sessao/WorkUnit/memoria/
causalidade, emite NOVA RoutingDecision para outra assinatura capaz;
nenhuma disponivel = STOP_WAIT_RESET. Migrar para API paga, creditos
extras ou saldo pre-pago e PROIBIDO.
"""

import os
import re
from types import MappingProxyType

from . import contratos as ct
from .catalogo import Catalogo

STOP_WAIT_RESET = "STOP_WAIT_RESET"

POLITICA_ECONOMICA = MappingProxyType({
    "external_variable_cost_cap": 0,
    "subscription_oauth": "ALLOW",
    "local_model": "ALLOW",
    "payg_api": "DENY",
    "extra_usage": "DENY",
    "auto_topup": "DENY",
    "unknown_billing_mode": "DENY",
})

GROK_AUTOMATION = MappingProxyType({
    "supervised": "ALLOW",
    "unattended": "TERMS_REVIEW_REQUIRED",
})

# Chaves que NUNCA entram no processo SSC+ (adendo). O ambiente global do
# usuario NAO e modificado — apenas impedimos a heranca pelo subprocesso.
CHAVES_PROIBIDAS = frozenset({
    "OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN", "GEMINI_API_KEY", "GOOGLE_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS", "XAI_API_KEY",
})
_PADRAO_CHAVE_PAYG = re.compile(
    r"(_API_KEY|_AUTH_TOKEN|_ACCESS_TOKEN|_API_SECRET|_SECRET_KEY)$")


class PoliticaEconomicaViolada(Exception):
    """Billing/auth/custo fora da politica imutavel: bloqueio pre-invocacao."""


class CanalNaoOficial(Exception):
    """Grok/Google fora do canal oficial da assinatura."""


class IndependenciaInsuficiente(ct.FalhaContrato):
    """Autor, revisor e juiz precisam ser independentes em trabalho critico."""


def ambiente_sanitizado(env: dict | None = None) -> dict:
    """Copia do ambiente SEM chaves PAYG/de plataforma paga.

    Nunca muta `os.environ` nem o dict recebido: as credenciais globais do
    usuario permanecem intactas — elas apenas nao entram no processo SSC+.
    """
    fonte = dict(os.environ if env is None else env)
    return {k: v for k, v in fonte.items()
            if k not in CHAVES_PROIBIDAS and not _PADRAO_CHAVE_PAYG.search(k)}


def verificar_economia(entry: ct.FleetEntry) -> list:
    """Vetos da politica economica imutavel (bloqueio ANTES da invocacao)."""
    vetos = []
    if entry.variable_cost > POLITICA_ECONOMICA["external_variable_cost_cap"]:
        vetos.append("external_variable_cost_cap = 0: custo variavel "
                     f"{entry.variable_cost} proibido")
    if entry.auth_mode == "payg-api":
        vetos.append("payg_api = DENY")
    elif entry.auth_mode == "desconhecido":
        vetos.append("auth_mode desconhecido = DENY")
    if entry.billing_mode in ("payg", "prepaid", "extra-usage"):
        vetos.append(f"billing {entry.billing_mode} = DENY "
                     "(payg_api/extra_usage/auto_topup proibidos)")
    elif entry.billing_mode == "desconhecido":
        vetos.append("unknown_billing_mode = DENY")
    return vetos


def verificar_canal(entry: ct.FleetEntry) -> list:
    """Regras de canal do adendo: Grok (Build/ACP, nunca api.x.ai) e Google
    (canal oficial da assinatura)."""
    vetos = []
    if entry.provider_id == "grok":
        if entry.auth_mode not in ("cached-token", "acp"):
            vetos.append("grok: somente Grok Build da assinatura "
                         "(cached token, headless ou ACP)")
        endpoint = entry.terms_profile.get("endpoint", "")
        if "api.x.ai" in endpoint:
            vetos.append("grok: api.x.ai PROIBIDO (nunca API paga)")
        if not entry.canal_oficial:
            vetos.append("grok: canal fora do Grok Build autenticado")
    if entry.provider_id == "google" and not entry.canal_oficial:
        vetos.append("google: OAuth reutilizado em cliente incompativel; "
                     "somente canal oficial da assinatura")
    return vetos


def verificar_automacao(entry: ct.FleetEntry,
                        modo_execucao: str = "supervised") -> list:
    """Nivel de autonomia: Grok unattended = TERMS_REVIEW_REQUIRED; Google
    condicional ate prova do canal permitido."""
    vetos = []
    if entry.automation_permission == "deny":
        vetos.append("automation_permission = deny")
    if entry.provider_id == "grok" and modo_execucao == "unattended":
        vetos.append(f"GROK_UNATTENDED = {GROK_AUTOMATION['unattended']}")
    if entry.provider_id == "google" \
            and entry.automation_permission == "terms-review-required":
        vetos.append("google: automacao condicional ate prova do canal "
                     "permitido (TERMS_REVIEW_REQUIRED)")
    return vetos


class Frota:
    """Catalogo de assinaturas com descoberta de modelos.

    O catalogo DESCOBRE os modelos disponiveis por assinatura (sensor
    injetavel); aliases sao resolvidos na hora da selecao, nunca
    presumidos permanentes.
    """

    def __init__(self, entradas: list):
        self.entradas = [e.validado() for e in entradas]
        self._por_provider: dict[str, list] = {}
        for e in self.entradas:
            self._por_provider.setdefault(e.provider_id, []).append(e)

    def descobrir(self, sensor=None) -> dict:
        """provider_id -> [model_id disponivel]. sensor(provider_id) ->
        list[str] substitui a leitura declarada (descoberta real futura)."""
        modelo_por_provider = {}
        for provider_id, entradas in self._por_provider.items():
            if sensor is not None:
                modelo_por_provider[provider_id] = list(sensor(provider_id))
            else:
                modelo_por_provider[provider_id] = [
                    e.model_id for e in entradas]
        return modelo_por_provider

    def elegiveis(self, papel: str | None = None,
                  excluir_providers=frozenset(),
                  modo_execucao: str = "supervised") -> list:
        """Assinaturas que passam economia + canal + automacao + quota."""
        saida = []
        for e in self.entradas:
            if e.provider_id in excluir_providers:
                continue
            if e.quota_state == "esgotada":
                continue
            if papel is not None and e.papeis_preferidos \
                    and papel not in e.papeis_preferidos:
                continue  # preferencia registrada; nao e papel fixo
            if verificar_economia(e) or verificar_canal(e) \
                    or verificar_automacao(e, modo_execucao):
                continue
            saida.append(e)
        return saida

    def escolher(self, capacidade: str | None = None,
                 papel: str | None = None,
                 excluir_providers=frozenset(),
                 modo_execucao: str = "supervised") -> ct.FleetEntry | None:
        """Primeira assinatura elegivel que atende a capacidade pedida."""
        for e in self.elegiveis(papel, excluir_providers, modo_execucao):
            if capacidade is None \
                    or capacidade in e.capability_profile.get(
                        "capacidades", []):
                return e
        return None

    def registrar_quota_exhausted(self, provider_id: str,
                                  model_id: str) -> ct.FleetEntry:
        """Marca a franquia como esgotada (estado conhecido, com reset)."""
        for e in self._por_provider.get(provider_id, []):
            if e.model_id == model_id:
                e.quota_state = "esgotada"
                return e
        raise ct.FalhaContrato(
            f"quota de entrada desconhecida: {provider_id}/{model_id}")

    @staticmethod
    def verificar_independencia(autor: ct.FleetEntry,
                                outro: ct.FleetEntry,
                                papel_outro: str) -> dict:
        """Evidencia de independencia autor x revisor/juiz (trabalho critico)."""
        provider_distinto = autor.provider_id != outro.provider_id
        modelo_distinto = autor.model_id != outro.model_id
        evidencia = {
            "papel": papel_outro,
            "autor": f"{autor.provider_id}/{autor.model_id}",
            "outro": f"{outro.provider_id}/{outro.model_id}",
            "provider_distinto": provider_distinto,
            "modelo_distinto": modelo_distinto,
        }
        if not (provider_distinto and modelo_distinto):
            raise IndependenciaInsuficiente(
                f"{papel_outro} nao independente do autor: {evidencia}")
        return evidencia


def frota_inicial() -> list:
    """As cinco assinaturas do adendo, com perfis INICIAIS (preferencias,
    nunca papeis fixos). variable_cost = 0 (assinatura), OAuth por perfil.
    """
    def entrada(provider_id, model_id, capacidades, preferencias,
                auth="subscription-oauth", automation="allow",
                canal=True, terms_extra=None, papeis=None):
        terms = {"oauth_profile": f"oauth:{provider_id}",
                 "preferencias_iniciais": preferencias}
        terms.update(terms_extra or {})
        return ct.FleetEntry(
            provider_id=provider_id, model_id=model_id,
            capability_profile={"capacidades": capacidades},
            auth_mode=auth, billing_mode="subscription",
            quota_state="disponivel", quota_reset=None,
            automation_permission=automation,
            terms_profile=terms, variable_cost=0.0,
            papeis_preferidos=papeis or ["autor", "revisor", "juiz"],
            canal_oficial=canal)

    return [
        entrada("codex", "gpt-5-codex", ["implementacao", "operacao-repo"],
                "implementacao principal e operacao de repositorio"),
        entrada("claude", "claude-opus", ["arquitetura", "specs",
                                          "revisao-profunda"],
                "arquitetura, Specs e revisao profunda"),
        entrada("kimi", "kimi-k2", ["engenharia-reversa", "contexto-extenso",
                                    "volume"],
                "engenharia reversa, contexto extenso e volume"),
        entrada("google", "gemini-pro", ["multimodal",
                                         "julgamento-transversal"],
                "multimodalidade e julgamento transversal",
                automation="terms-review-required"),  # condicional (adendo)
        entrada("grok", "grok-build", ["pesquisa-atual", "x-web", "red-team",
                                       "coding-alternativo"],
                "pesquisa atual, X/web, red team e coding alternativo",
                auth="cached-token",
                terms_extra={"endpoint": "grok-build://assinatura"}),
    ]


class AdaptadorAssinatura:
    """Falso CLI de assinatura: ambiente sanitizado + auth/canal/economia
    ANTES de qualquer invocacao.

    Em P1+, envolvera o subprocesso real do CLI; na P0/P0.3 envolve um
    FakeProvider deterministico. Registra o ambiente efetivo para prova.
    """

    def __init__(self, entry: ct.FleetEntry, provedor_fake, env=None,
                 modo_execucao: str = "supervised"):
        self.entry = entry
        self.env = ambiente_sanitizado(env)
        vetos = (verificar_economia(entry) + verificar_canal(entry)
                 + verificar_automacao(entry, modo_execucao))
        if vetos:
            raise PoliticaEconomicaViolada("; ".join(vetos))
        # API key presente NUNCA substitui o OAuth da assinatura: sem perfil
        # OAuth/cached token valido, a invocacao e bloqueada — mesmo que uma
        # chave PAYG exista no ambiente original.
        if entry.auth_mode in ("subscription-oauth", "cached-token", "acp") \
                and not entry.terms_profile.get("oauth_profile"):
            raise PoliticaEconomicaViolada(
                "perfil OAuth da assinatura ausente; chave de API nao "
                "substitui OAuth (payg_api = DENY)")
        if any(k in self.env for k in CHAVES_PROIBIDAS):
            raise PoliticaEconomicaViolada(
                "ambiente nao sanitizado: chave PAYG presente")
        self.provedor_fake = provedor_fake

    def invocar(self, entrada: bytes, pacote: dict | None = None,
                idempotency_key: str | None = None):
        """Delega ao falso deterministico (P1+: subprocesso sanitizado)."""
        return self.provedor_fake.invocar(
            entrada, pacote, idempotency_key=idempotency_key)


# --- Integracao com o lab (catalogo/politica/envelope derivados da frota) -----

def catalogo_de_frota(frota: Frota) -> Catalogo:
    """Catalogo de executores falsos derivado dos modelos DESCOBERTOS."""
    executores = []
    for provider_id, modelos in frota.descobrir().items():
        entry = next(e for e in frota.entradas
                     if e.provider_id == provider_id and e.model_id in modelos)
        capacidades = entry.capability_profile.get("capacidades", [])
        executores.append({
            "executor_id": f"{provider_id}/{entry.model_id}",
            "ferramenta": "cli-assinatura",
            "provedor": provider_id,
            "modelo": entry.model_id,
            "efforts": ["baixo", "alto"],
            "nivel": entry.capability_profile.get("nivel", "L2"),
            "perfil": {
                "modalidades": ["texto", "codigo", "mista"],
                "ferramentas": [],
                "formatos": ["livre", "json-schema", "patch"],
                "contexto_max_tokens": 128000,
                "dominios": ["*"] + capacidades,
                "privacidade": "remoto-permitido",
                "latencia_base_ms": 500,
                "custo_base": 0.0,  # assinatura: custo variavel zero
            },
        })
    return Catalogo(executores)


def politica_de_frota(frota: Frota) -> dict:
    """Politica derivada da frota: so modelos descobertos, rota 'frota'."""
    descobertos = frota.descobrir()
    return {
        "nome": "politica-frota-subscription-only",
        "rotas_permitidas": ["frota"],
        "executores": [f"{p}/{m}" for p, modelos in descobertos.items()
                       for m in modelos],
        "classe_modos": {
            "C0": ["read-only", "worktree", "escrita-aprovada"],
            "C1": ["read-only", "worktree", "escrita-aprovada"],
            "C2": ["worktree", "escrita-aprovada"],
            "C3": ["escrita-aprovada"],
        },
    }


def envelope_de_frota(frota: Frota) -> dict:
    """Envelope de custo da frota: teto zero de custo variavel, fallback
    autorizado entre assinaturas (QUOTA_EXHAUSTED -> outra assinatura)."""
    descobertos = frota.descobrir()
    return {
        "modelos_permitidos": [f"{p}/{m}" for p, modelos in descobertos.items()
                               for m in modelos],
        "efforts_permitidos": ["baixo", "alto"],
        "teto_custo": 0.0,  # external_variable_cost_cap = 0
        "modo": "read-only",
        "validade": "2027-01-01T00:00:00Z",
        "fallback_autorizado": True,
    }


class ResultadoFrota:
    """Resultado de uma rodada orquestrada pela frota."""

    def __init__(self, status: str, resultado_execucao=None, detalhe=""):
        self.status = status  # sucesso | STOP_WAIT_RESET | escalonado
        self.resultado = resultado_execucao
        self.detalhe = detalhe

    def __repr__(self):
        return f"ResultadoFrota({self.status!r}, {self.detalhe!r})"


def executar_com_frota(lab, frota: Frota, wu, papel: str = "autor",
                       idempotency_key: str | None = None,
                       entrada: bytes = b"") -> ResultadoFrota:
    """Escolha por WorkUnit dentro do MESMO SessionEnvelope (adendo).

    QUOTA_EXHAUSTED -> estado registrado na frota + nova RoutingDecision
    para outra assinatura capaz (sessao, WorkUnit, memoria e causalidade
    preservados pelo proprio mecanismo de fallback 0.2.1-6). Nenhuma
    assinatura disponivel = STOP_WAIT_RESET — NUNCA PAYG.
    """
    elegiveis = frota.elegiveis(papel=papel)
    if not elegiveis:
        return ResultadoFrota(
            STOP_WAIT_RESET,
            detalhe="nenhuma assinatura capaz disponivel; migracao para "
                    "API paga/creditos/saldo pre-pago e PROIBIDA")
    primeira, *restantes = elegiveis

    def selecao(entry):
        return {"ferramenta": "cli-assinatura",
                "provedor": entry.provider_id, "modelo": entry.model_id,
                "effort": "alto", "modo": "read-only",
                "controle": "autonomo"}

    decisao = lab.router.propor_decisao(
        wu, rota="frota", selecao=selecao(primeira),
        alternativas=[selecao(e) for e in restantes],
        aprovacao_custo=lab.aprovacao,
        motivo=f"frota: {primeira.provider_id}/{primeira.model_id} por "
               f"capacidade/preferencia (fallback autorizado)",
        papel=papel)
    resultado = lab.execution.executar(
        wu, decisao, idempotency_key=idempotency_key, entrada=entrada)
    # Marca quota esgotada na frota para cada assinatura que falhou quota.
    for attempt in lab.kernel.attempts.values():
        att = attempt["attempt"]
        if att.work_unit_id == wu.work_unit_id \
                and att.resultado == "falha-quota":
            resolvido = att.executor_resolvido
            frota.registrar_quota_exhausted(resolvido["provedor"],
                                            resolvido["modelo"])
    if resultado.status == "sucesso":
        return ResultadoFrota("sucesso", resultado)
    if resultado.detalhe in ("sem-alternativa", "fallback-fora-do-envelope"):
        return ResultadoFrota(
            STOP_WAIT_RESET, resultado,
            detalhe="assinaturas esgotadas/indisponiveis; STOP_WAIT_RESET, "
                    "nunca PAYG")
    return ResultadoFrota(resultado.status, resultado)
