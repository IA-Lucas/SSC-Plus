"""Apoio comum dos testes P1-A: sys.path + sensores falsos.

Regra desta suite: NENHUM subprocesso real e criado e NENHUM CLI de
assinatura e invocado. Toda execucao externa dos adaptadores passa por um
sensor injetavel; aqui vivem os sensores falsos, que apenas devolvem
saidas fixas e contam chamadas. Assim os testes provam a ORDEM do
bloqueio (economia/auth antes da descoberta de modelos) sem gastar um
unico token de assinatura.
"""

import dataclasses
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_DIR))
# 05_p0 entra no path para provar que o espelho da politica economica do
# preflight e fiel a POLITICA_ECONOMICA imutavel da camada P0.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(_DIR)),
                                "05_p0"))

from preflight import espec_de  # noqa: E402

# Valor ficticio usado para provar que NENHUM valor de credencial vaza
# para relatorios, erros ou logs. Nao e e nunca foi uma credencial.
SENTINELA = "SENTINELA-VALOR-FICTICIO-NAO-E-CREDENCIAL"

# Saidas verdes por provedor: (versao, login, modelos). Refletem o formato
# real observado em 01_inventario-real.md, sem qualquer dado sensivel.
VERDES = {
    "codex": ("codex-cli 0.145.0",
              "Logged in using ChatGPT (plan: ChatGPT Pro 5x)",
              "gpt-5\ngpt-5-codex"),
    "claude": ("2.1.220",
               '{"loggedIn": true, "subscriptionType": "max"}',
               "claude-opus-5\nclaude-sonnet-5"),
    "kimi": ("0.30.0",
             "managed:kimi-code type=kimi source=oauth plan=Allegretto",
             "kimi-k2-thinking\nkimi-k2-turbo"),
    "google": ("0.52.0",
               "oauth-personal; plan: Google AI Pro",
               "gemini-3-pro\ngemini-3-flash"),
    "grok": ("1.1.7",
             "Using cached token (SuperGrok)",
             "grok-4-latest\ngrok-4-fast"),
}


class SensorFalso:
    """Sensor injetavel de teste: sensor(argv, env) -> (rc, out, err).

    `respostas` mapeia comando (tupla) -> (rc, out, err). `erro`, quando
    presente, e levantado no lugar da execucao (para provar a
    classificacao de CLI indisponivel). Cada chamada e registrada em
    `chamadas`, o que permite asserir que uma sonda NAO foi executada.
    """

    def __init__(self, respostas=None, erro=None, padrao=(0, "", "")):
        self.respostas = {tuple(k): v for k, v in (respostas or {}).items()}
        self.erro = erro
        self.padrao = padrao
        self.chamadas = []
        self.ambientes = []

    def __call__(self, argv, env=None, timeout=None):
        comando = tuple(argv[1:])
        self.chamadas.append(comando)
        self.ambientes.append(env)
        if self.erro is not None:
            raise self.erro
        for chave, resposta in self.respostas.items():
            if comando == chave or comando[:len(chave)] == chave:
                return resposta
        return self.padrao

    @property
    def n(self) -> int:
        return len(self.chamadas)


def sensores_verdes(provider_id, versao=None, login=None, modelos=None):
    """Par de sensores (exec, modelos) com as saidas verdes do provedor.

    Qualquer um dos tres textos pode ser sobrescrito para injetar uma
    falha especifica sem mexer nas outras sondas.
    """
    espec = espec_de(provider_id)
    v, lg, md = VERDES[provider_id]
    v = v if versao is None else versao
    lg = lg if login is None else login
    md = md if modelos is None else modelos
    sensor_exec = SensorFalso({
        espec.comandos["versao"]: (0, v, ""),
        espec.comandos["login"]: (0, lg, ""),
    })
    sensor_modelos = SensorFalso({espec.comandos["modelos"]: (0, md, "")})
    return sensor_exec, sensor_modelos


def sensores_dict(provider_id, **sobre):
    """`{"exec": ..., "modelos": ...}` no formato de executar_preflight."""
    sensor_exec, sensor_modelos = sensores_verdes(provider_id, **sobre)
    return {"exec": sensor_exec, "modelos": sensor_modelos}, \
        sensor_exec, sensor_modelos


def espec_com(provider_id, **sobre):
    """Copia da especificacao real com campos trocados (frozen dataclass)."""
    return dataclasses.replace(espec_de(provider_id), **sobre)


def codigos(relatorio) -> list:
    """Codigos de erro do relatorio, na ordem em que foram registrados."""
    return [e.codigo for e in relatorio.erros]
