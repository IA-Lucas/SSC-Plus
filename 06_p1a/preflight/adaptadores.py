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
import os
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
# Zero como NUMERO, nao como digito solto (revisao P1-A.3.1, MAJOR #2).
# Cobre "0", "0.0" e "0,0"; recusa o zero que e parte de outro numero.
# As duas ancoras sao necessarias e nao simetricas:
#   - sem a de tras, "10.0 tokens available" casaria pelo "0" depois do
#     ponto e bloquearia franquia DISPONIVEL (fail-closed indevido);
#   - sem a da frente, "0.5 calls left" casaria pelo "0" e bloquearia
#     meia franquia.
_ZERO = r"(?<![\d.,])0(?:[.,]0+)?(?![\d.,])"

# Esgotamento em grafias alternativas (regex): zero-quota e negacao.
# Sem isto, "0 requests remaining" ou "no calls left" escapavam dos
# marcadores literais e caiam no sinal positivo "remaining"/"left" —
# quota REALMENTE esgotada classificada como disponivel (fail-open).
#
# Revisao P1-A.3.1, MAJOR #2: o zero literal `\b0\s+` exigia digito nu
# seguido de espaco, de modo que "0.0 tokens available" (zero decimal) e
# "0% quota available" (zero percentual) escapavam de TODAS as regexes e
# caiam no sinal positivo `\bavailable\b` — quota zerada classificada
# como disponivel, o fail-open exato do achado. `_ZERO` e o sinal de
# porcentagem opcional fecham as duas grafias.
_RX_QUOTA_ESGOTADA = tuple(re.compile(p) for p in (
    # "0 requests remaining"; "0 of 100 requests remaining";
    # "0.0 tokens available"; "0% quota available"; "0 remaining".
    _ZERO + r"\s*%?\s*(?:of\s+[\d.,]+\s+)?(?:\w+\s+)?"
            r"(?:remaining|left|available)\b",
    # "requests remaining: 0"; "available: 0.0"; "quota available = 0%".
    r"\b(?:remaining|left|available)\s*[:=]?\s*" + _ZERO + r"\s*%?",
    # "quota: 0"; "credits = 0"; "tokens: 0.0"; "balance: 0%".
    r"\b(?:quota|credits?|tokens?|requests?|calls?|balance)\s*[:=]\s*"
    + _ZERO + r"\s*%?",
    _ZERO + r"\s*/\s*[\d.,]+",                # "0/100 requests remaining"
    # Negacao com ou sem palavra intermediaria (revisoes P1-A.3):
    # "no calls left", "no requests remaining", "no remaining quota",
    # "none left", "no quota available" — qualquer uma vence o sinal
    # positivo "remaining"/"available".
    r"\bno(?:ne)?\s+(?:[a-z]+\s+)?(?:remaining|left|available)\b",
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


def _contem_token(texto: str, token: str) -> bool:
    """Token presente como PALAVRA(S) inteiras no texto.

    Fronteiras nao alfanumericas nos dois lados (revisao P1-A.3, MAJOR):
    sem isto, "pro" casava em "profile"/"prompt" e "max" em "maximum" —
    plano reconhecido por acidente em texto incidental (fail-open).
    """
    return re.search(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])",
                     texto) is not None


# Negacoes que invalidam um plano/tier reportado (revisao P1-A.3,
# rodada 5): "not pro" NUNCA e o plano "pro".
_MARCADORES_NEGACAO = ("not ", "no ", "non ", "não ", "nao ", "never ")


def plano_reconhecido(plano, planos_aceitos) -> bool:
    """Plano reportado cobre algum plano aceito (tokens inteiros).

    SOMENTE o sentido reportado ⊇ aceito (revisao P1-A.3, rodada 3): a
    comparacao reciproca aceitava tiers genericos como "chatgpt" ou "5x"
    por fazerem parte da frase aceita. Valor com marcador de negacao e
    rejeitado sempre (rodada 5).
    """
    low = str(plano or "").strip().lower()
    if not low or any(n in low for n in _MARCADORES_NEGACAO):
        return False
    return any(_contem_token(low, p) for p in planos_aceitos)


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


# Rotulos que introduzem a evidencia de plano numa saida de CLI. TODA
# evidencia de plano exige rotulo COMO PALAVRA INTEIRA (revisao P1-A.3,
# rodadas 3-5): "explanation: pro" nao e rotulo (sem \b inicial), e
# texto corrido — "Upgrade to Pro" — NAO comprova plano.
_ROTULO_PLANO = r"\b(?:plan|plano|subscription)s?\b\s*[:\-=]?\s*"
_RX_PLANO_ROTULADO_BRUTO = re.compile(
    _ROTULO_PLANO + r"([a-z0-9][a-z0-9 ._-]{0,40})")


def _plano_de(texto: str, planos_aceitos):
    """Plano ROTULADO no texto: o maior aceito, ou o valor bruto.

    Somente `plan:`/`plano=`/`subscription` introduzem evidencia de
    plano. Retorna o maior plano ACEITO rotulado; se o rotulo introduz
    um plano fora dos aceitos, retorna o valor BRUTO observado (revisao
    P1-A.3: "plan: team" NAO pode virar None e cair na trilha sombra —
    evidencia observada divergente tem precedencia sobre a declarada).
    Sem rotulo, retorna None (plano nao observado).
    """
    low = texto.lower()
    for plano in sorted(planos_aceitos, key=len, reverse=True):
        if re.search(_ROTULO_PLANO + re.escape(plano) + r"(?![a-z0-9])",
                     low):
            return plano
    bruto = _RX_PLANO_ROTULADO_BRUTO.search(low)
    if bruto:
        return bruto.group(1).strip(" .-_") or None
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
    # F-2 (P1-A.2): `codex login status` imprime o status em STDERR
    # (stdout vazio). Login, plano e quota sao avaliados sobre stdout e
    # stderr COMBINADOS em memoria — a saida bruta nunca e persistida.
    # rc != 0 ou marcador negativo vence sempre: um conflito entre os
    # canais (positivo num, negativo noutro) resulta desconhecido/BLOCKED,
    # nunca login por inferencia.
    # Revisao P1-A.3 (MINOR): o OAuth do codex exige os DOIS marcadores
    # ("logged in" E "chatgpt") — um "chatgpt" solto em texto qualquer
    # (ex.: "visit chatgpt.com", rc=0) nao e prova de login.
    texto = (out or "") + "\n" + (err or "")
    low = texto.lower()
    logado = rc == 0 \
        and not any(m in low for m in _MARCADORES_NAO_LOGADO) \
        and "logged in" in low and "chatgpt" in low
    return _resultado(logado, _plano_de(texto, espec.planos_aceitos),
                      "subscription-oauth", texto)


def _login_claude(rc, out, err, espec):
    try:
        dados = json.loads(out)
        plano = dados.get("subscriptionType") or dados.get("plan")
        logado = rc == 0 and bool(dados.get("loggedIn", plano is not None))
    except (json.JSONDecodeError, AttributeError):
        # Fallback de texto (revisao P1-A.3): exige os DOIS marcadores —
        # "oauth" solto em texto incidental (ex.: "oauth token expired")
        # nao e prova de login.
        low = (out or "").lower()
        logado = rc == 0 \
            and not any(m in low for m in _MARCADORES_NAO_LOGADO) \
            and "logged in" in low and "oauth" in low
        plano = _plano_de(out, espec.planos_aceitos)
    return _resultado(logado, str(plano) if plano else None,
                      "subscription-oauth", out)


def _login_kimi(rc, out, err, espec):
    # Revisao P1-A.3 (MAJOR): stdout e stderr COMBINADOS, e os dois
    # marcadores exigidos NA MESMA LINHA — um "source=oauth" de outro
    # provider na saida nao valida o registro managed:kimi-code.
    texto = (out or "") + "\n" + (err or "")
    low = texto.lower()
    linha_oauth = any("managed:kimi-code" in linha
                      and "source=oauth" in linha
                      for linha in low.splitlines())
    logado = rc == 0 \
        and not any(m in low for m in _MARCADORES_NAO_LOGADO) \
        and linha_oauth
    return _resultado(logado, _plano_de(texto, espec.planos_aceitos),
                      "subscription-oauth", texto)


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


# Emenda P1-A.3, item 2 (APROVADA): `codex doctor` comprova o modelo
# efetivo atual e o modo de autenticacao — NAO equivale a catalogo
# completo (a descoberta `codex models` e TTY-only, bloqueio factual da
# P1-A.2). Regexes ANCORADAS no inicio da linha (revisao P1-A.3): texto
# incidental como "expected auth mode chatgpt" no meio de uma frase nao
# comprova auth nem modelo.
_RX_DOCTOR_AUTH = re.compile(
    r"^\s*(?:stored\s+)?auth\s+mode\s*:?\s*([a-z0-9._-]+)\b", re.MULTILINE)
_RX_DOCTOR_MODELO = re.compile(
    r"^\s*model\s*:?\s*([a-z0-9][a-z0-9._-]*)\b", re.MULTILINE)


def _modelos_codex_doctor(rc, out, err):
    """Descoberta codex via `doctor`: modelo efetivo + auth mode chatgpt.

    Fail-closed: rc != 0, auth mode ausente, diferente de `chatgpt` ou
    CONFLITANTE (revisao P1-A.3, rodada 3: uma saida com "auth mode
    chatgpt" E "auth mode apikey" nao comprova nada — todas as linhas de
    auth precisam concordar), ou modelo efetivo ausente/conflitante =>
    lista vazia (ModeloRemovido/BLOCKED no pipeline). stdout e stderr
    combinados em memoria; a saida bruta nunca e persistida.
    """
    if rc != 0:
        return []
    texto = ((out or "") + "\n" + (err or "")).lower()
    auths = set(_RX_DOCTOR_AUTH.findall(texto))
    if auths != {"chatgpt"}:
        return []
    # Somente tokens com DIGITO contam como identificador de modelo —
    # linhas espurias tipo "model reasoning effort" nao geram conflito
    # falso ("reasoning" nao e id de modelo).
    modelos = {m for m in _RX_DOCTOR_MODELO.findall(texto)
               if any(c.isdigit() for c in m)}
    if len(modelos) != 1:
        return []
    return [modelos.pop()]


# Emenda P1-A.3, item 3 (PARCIALMENTE APROVADA): `kimi provider list`
# comprova OAuth e o MODELO EFETIVO ("Default model:"), nao o plano
# comercial. Sem a linha do modelo efetivo, o nome do provider
# ("managed:kimi-code") NAO pode satisfazer a descoberta (revisao
# P1-A.3: a extracao generica aceitava "kimi-code" como modelo).
_RX_KIMI_MODELO_EFETIVO = re.compile(
    r"^\s*default\s+model\s*:?\s*([a-z0-9][a-z0-9._/-]*)\b",
    re.IGNORECASE | re.MULTILINE)


def _modelos_kimi_provider_list(rc, out, err):
    """Descoberta kimi via `provider list`: SOMENTE o modelo efetivo.

    Fail-closed: rc != 0, linha "Default model:" ausente ou CONFLITANTE
    (revisao P1-A.3: valores distintos em linhas diferentes nao comprovam
    um modelo efetivo) => lista vazia (ModeloRemovido/BLOCKED).
    """
    if rc != 0:
        return []
    modelos = set(_RX_KIMI_MODELO_EFETIVO.findall(
        (out or "") + "\n" + (err or "")))
    if len(modelos) != 1:
        return []
    return [modelos.pop()]


# Parsers dedicados de descoberta por provedor; os demais usam a
# extracao generica de identificadores (extrair_modelos).
_PARSERS_MODELOS = {
    "codex": _modelos_codex_doctor,
    "kimi": _modelos_kimi_provider_list,
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
        # F-1 (P1-A.2): expande SOMENTE o ~ do executavel (os.path.expanduser).
        # Sem expandvars, sem shell, sem hardcode de usuario: os argumentos
        # seguem em lista, intactos (espacos e metacaracteres sao literais,
        # pois a execucao e sempre argv-lista com shell=False). Caminho
        # inexistente vira CliIndisponivel na sonda (FileNotFoundError).
        exe = os.path.expanduser(self.espec.executavel or self.espec.cli)
        return [exe] + list(comando)

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
        """Descoberta de modelos via CLI (sensor de modelos dedicado).

        Sem comando de descoberta na especificacao (comandos["modelos"]
        = None — claude/google/grok desde a P1-A.3), devolve lista vazia
        sem sondar (guarda propria; o pipeline nem chama neste caso).
        Provedores com parser dedicado (`_PARSERS_MODELOS`, ex.: codex
        `doctor` — emenda P1-A.3) comprovam modelo efetivo + auth mode;
        os demais usam a extracao generica de identificadores.
        """
        comando = self.espec.comandos.get("modelos")
        if comando is None:
            return []
        rc, out, err = self.sonda(comando, sensor=self.sensor_modelos)
        parser = _PARSERS_MODELOS.get(self.espec.provider_id)
        if parser is not None:
            return parser(rc, out, err)
        return extrair_modelos(out)
