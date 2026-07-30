"""Adaptadores de DIAGNOSTICO (preflight) para os CLIs de assinatura.

NUNCA executam chamada produtiva a modelo, nunca solicitam pagamento,
nunca alteram arquivos do projeto: apenas --version, status de login/auth
e listagem de modelos. Toda execucao externa passa por um "sensor"
injetavel: sensor(argv, env) -> (returncode, stdout, stderr). Nos testes
sensores falsos substituem qualquer subprocesso; o sensor padrao
(sensor_subprocess) so roda em operacao real, com ambiente sanitizado,
timeout e captura de saida — e nunca imprime segredos.
"""

import json
import re
import subprocess

from .economia import CliIndisponivel, ambiente_sanitizado

TIMEOUT_PADRAO = 20

_MARCADORES_NAO_LOGADO = (
    "not logged", "logged out", "unauthenticated", "nao autenticado",
    "não autenticado", "login required", "no credentials",
)
_MARCADORES_QUOTA_ESGOTADA = (
    "quota exhausted", "quota esgotada", "esgotada", "0 remaining",
    "rate_limit_exceeded", "usage limit reached",
)
# Esgotamento em grafias alternativas (regex): zero-quota e negacao.
# Sem isto, "0 requests remaining" ou "no calls left" escapavam dos
# marcadores literais e caiam no sinal positivo "remaining"/"left" —
# quota REALMENTE esgotada classificada como disponivel (fail-open).
_RX_QUOTA_ESGOTADA = tuple(re.compile(p) for p in (
    r"\b0\s+\w+\s+(?:remaining|left)\b",      # "0 requests remaining"
    r"\b(?:remaining|left)\s*[:=]?\s*0\b",    # "requests remaining: 0"
    r"\bno\s+\w+\s+left\b",                   # "no calls left"
))
# Sinais POSITIVOS observaveis de franquia disponivel, casados por
# PALAVRA (\b) — "unavailable" nao pode casar "available". "Disponivel"
# NUNCA e presumida do login: sem um destes sinais no texto do CLI, a
# quota e "desconhecida" (ausencia de evidencia = unknown, fail-closed).
_RX_QUOTA_DISPONIVEL = tuple(re.compile(p) for p in (
    r"\bremaining\b", r"\bavailable\b", r"\bdispon[ií]vel\b",
    r"\bleft\b", r"\bresets\b", r"\breset at\b", r"\bwithin limit\b",
    r"\bquota ok\b",
))
_PADRAO_MODELO = re.compile(r"\b[a-z][a-z0-9]*(?:[-._][a-z0-9]+)+\b")
_PADRAO_VERSAO = re.compile(r"\d+(?:\.\d+){1,3}")


def sensor_subprocess(argv, env=None, timeout: int = TIMEOUT_PADRAO):
    """Sensor real (somente operacao): subprocesso sanitizado + timeout.

    Captura stdout/stderr sem ecoa-los (nunca imprime segredos) e devolve
    (returncode, stdout, stderr). FileNotFoundError/OSError propagam para
    o adaptador classificar como CliIndisponivel.
    """
    ambiente = ambiente_sanitizado(env)
    try:
        proc = subprocess.run(list(argv), env=ambiente, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return (124, "", "timeout do sensor de preflight")
    return (proc.returncode, proc.stdout or "", proc.stderr or "")


def extrair_modelos(texto: str) -> list:
    """Identificadores de modelo (tokens com hifen/ponto) no texto."""
    return sorted(set(_PADRAO_MODELO.findall(texto.lower())))


def plano_reconhecido(plano, planos_aceitos) -> bool:
    """Plano reportado consta na lista de planos aceitos (substring)."""
    low = str(plano or "").strip().lower()
    if not low:
        return False
    return any(p in low or low in p for p in planos_aceitos)


def _quota_de(texto: str, logado: bool) -> str:
    """Classifica a franquia: disponivel | esgotada | desconhecida.

    Fail-closed: "esgotada" vence sempre; "disponivel" EXIGE sinal
    positivo observavel no texto (login valido sozinho nunca basta);
    qualquer outra situacao e "desconhecida" — ausencia de evidencia
    e unknown, nunca presumida disponivel.
    """
    low = texto.lower()
    if any(m in low for m in _MARCADORES_QUOTA_ESGOTADA) \
            or any(rx.search(low) for rx in _RX_QUOTA_ESGOTADA):
        return "esgotada"
    if not logado:
        return "desconhecida"
    if any(rx.search(low) for rx in _RX_QUOTA_DISPONIVEL):
        return "disponivel"
    return "desconhecida"


def _plano_de(texto: str, planos_aceitos):
    """Maior substring aceita presente no texto; None se nenhuma."""
    low = texto.lower()
    for plano in sorted(planos_aceitos, key=len, reverse=True):
        if plano in low:
            return plano
    return None


def _logado_texto(rc: int, out: str, marcadores_positivos) -> bool:
    low = out.lower()
    if rc != 0 or any(m in low for m in _MARCADORES_NAO_LOGADO):
        return False
    return any(m in low for m in marcadores_positivos)


def _resultado(logado, plano, origem, texto):
    return {"logado": logado, "plano": plano,
            "origem_credencial": origem if logado else "ausente",
            "quota": _quota_de(texto, logado)}


def _login_codex(rc, out, err, espec):
    logado = _logado_texto(rc, out, ("logged in", "chatgpt"))
    return _resultado(logado, _plano_de(out, espec.planos_aceitos),
                      "subscription-oauth", out)


def _login_claude(rc, out, err, espec):
    try:
        dados = json.loads(out)
        plano = dados.get("subscriptionType") or dados.get("plan")
        logado = rc == 0 and bool(dados.get("loggedIn", plano is not None))
    except (json.JSONDecodeError, AttributeError):
        logado = _logado_texto(rc, out, ("logged in", "oauth"))
        plano = _plano_de(out, espec.planos_aceitos)
    return _resultado(logado, str(plano) if plano else None,
                      "subscription-oauth", out)


def _login_kimi(rc, out, err, espec):
    logado = _logado_texto(rc, out, ("source=oauth", "managed:kimi-code"))
    return _resultado(logado, _plano_de(out, espec.planos_aceitos),
                      "subscription-oauth", out)


def _login_google(rc, out, err, espec):
    logado = _logado_texto(rc, out, ("oauth-personal", "logged in"))
    return _resultado(logado, _plano_de(out, espec.planos_aceitos),
                      "subscription-oauth", out)


def _login_grok(rc, out, err, espec):
    logado = _logado_texto(rc, out, ("cached", "logged in", "supergrok"))
    return _resultado(logado, _plano_de(out, espec.planos_aceitos),
                      "cached-token", out)


_PARSERS_LOGIN = {
    "codex": _login_codex,
    "claude": _login_claude,
    "kimi": _login_kimi,
    "google": _login_google,
    "grok": _login_grok,
}


class AdaptadorPreflight:
    """Diagnostico read-only de um CLI de assinatura.

    Recebe a especificacao estatica (EspecProvedor) e sensores injetaveis.
    Toda execucao externa passa pelo sensor: sensor(argv, env) ->
    (returncode, stdout, stderr).
    """

    def __init__(self, espec, sensor_exec=None, sensor_modelos=None,
                 env=None):
        self.espec = espec
        self.sensor_exec = sensor_exec or sensor_subprocess
        self.sensor_modelos = sensor_modelos or self.sensor_exec
        self.env = dict(env) if env is not None else None

    def _argv(self, comando) -> list:
        return [self.espec.executavel or self.espec.cli] + list(comando)

    def sonda(self, comando, sensor=None):
        """Executa um comando de diagnostico via sensor injetavel."""
        sonda_sensor = sensor or self.sensor_exec
        try:
            return sonda_sensor(self._argv(comando), self.env)
        except (FileNotFoundError, OSError) as exc:
            raise CliIndisponivel(
                detalhe=f"executavel indisponivel: {self.espec.executavel} "
                        f"({type(exc).__name__})") from exc

    def detectar_versao(self):
        """Deteccao do CLI + versao: a sonda de --version e a deteccao."""
        rc, out, _ = self.sonda(self.espec.comandos["versao"])
        if rc != 0:
            raise CliIndisponivel(
                detalhe=f"{self.espec.cli} nao respondeu a "
                        f"{self.espec.comandos['versao']} (rc={rc})")
        match = _PADRAO_VERSAO.search(out)
        if match:
            return match.group(0)
        return out.strip().splitlines()[0] if out.strip() else None

    def consultar_login(self) -> dict:
        """Status de login/auth: logado, plano, origem da credencial, quota."""
        rc, out, err = self.sonda(self.espec.comandos["login"])
        return _PARSERS_LOGIN[self.espec.provider_id](rc, out, err,
                                                      self.espec)

    def descobrir_modelos(self) -> list:
        """Descoberta de modelos via CLI (sensor de modelos dedicado)."""
        rc, out, _ = self.sonda(self.espec.comandos["modelos"],
                                sensor=self.sensor_modelos)
        return extrair_modelos(out)
