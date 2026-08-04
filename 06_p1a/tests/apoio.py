"""Apoio comum dos testes P1-A: sys.path + sensores falsos.

Regra desta suite: NENHUM subprocesso real e criado e NENHUM CLI de
assinatura e invocado. Toda execucao externa dos adaptadores passa por um
sensor injetavel; aqui vivem os sensores falsos, que apenas devolvem
saidas fixas e contam chamadas. Assim os testes provam a ORDEM do
bloqueio (economia/auth antes da descoberta de modelos) sem gastar um
unico token de assinatura.
"""

import dataclasses
import json
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
# codex: saida no formato `codex doctor` (emenda P1-A.3, item 2) — modelo
# efetivo + auth mode, NAO catalogo. claude: sem sonda de modelos desde a
# emenda P1-A.3 item 4 (comandos["modelos"] = None); o texto e mantido
# somente para testes que injetam uma espec com descoberta reativada.
VERDES = {
    "codex": ("codex-cli 0.145.0",
              "Logged in using ChatGPT (plan: ChatGPT Pro 5x)",
              "model gpt-5.6-sol\nstored auth mode chatgpt"),
    "claude": ("2.1.220",
               '{"loggedIn": true, "subscriptionType": "max"}',
               "claude-opus-5\nclaude-sonnet-5"),
    "kimi": ("0.30.0",
             "managed:kimi-code type=kimi source=oauth plan=Allegretto",
             "Default model: kimi-code/k3\n"
             "managed:kimi-code type=kimi source=oauth"),
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
    falha especifica sem mexer nas outras sondas. Provedor sem comando de
    descoberta (comandos["modelos"] = None — claude desde a P1-A.3)
    recebe um sensor de modelos vazio: qualquer sonda de modelos nele e
    regressao (a descoberta foi desativada pela especificacao).
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
    comando_modelos = espec.comandos.get("modelos")
    sensor_modelos = SensorFalso(
        {} if comando_modelos is None else {comando_modelos: (0, md, "")})
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


def escrever_lock(dir_locks, sessao, fence, expira_em):
    """Lease + fence do escritor UNICO do repositorio, para os testes.

    IMPLEMENTACAO UNICA, e a razao e medida. Ate a P1-A.4 esta funcao
    existia copiada em QUATRO suites (`test_correcoes_p1a32`,
    `test_p1b_lease_p1a35`, `test_persistencia_lock_p1a37`,
    `test_contencao_atribuicao_p1a37`), cada uma montando
    `f"{sessao}.lease"` a mao. Quando a P1-A.5 trocou o escritor para
    exclusao por repositorio, as quatro ficaram vermelhas no mesmo
    instante — que e o mecanismo dos achados 7, 10 e 14 visto do outro
    lado. Aqui ela existe uma vez e PERGUNTA o caminho ao modulo que o
    define, de modo que a proxima troca de mecanismo nao precise achar
    copia nenhuma.

    `sessao` e o TITULAR gravado dentro do lease — nao escolhe mais o
    nome do arquivo, e e exatamente isso que a troca fez.
    """
    from escritor_repositorio import caminho_fence, caminho_lease
    os.makedirs(dir_locks, exist_ok=True)
    with open(caminho_lease(dir_locks), "w", encoding="utf-8") as f:
        json.dump({"sessao": sessao, "pid": os.getpid(), "token": fence,
                   "renovado_em": expira_em - 120, "expira_em": expira_em}, f)
    with open(caminho_fence(dir_locks), "w", encoding="ascii") as f:
        f.write(str(fence))
