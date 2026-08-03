"""Infra comum das corridas P0: monta um lab completo em uma raiz declarada.

Tudo fica sob a raiz: CAS, logs, checkpoints, envelope, chave de selo local.
Providers falsos deterministicos por seed; numeros simulados e rotulados.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ssc_p0.canonico import RelogioDeterministico, canonico, sha256_de
from ssc_p0.catalogo import Catalogo, catalogo_padrao
from ssc_p0.execution import ExecutionGateway
from ssc_p0.judge import Juiz2, fila_juizes_padrao
from ssc_p0.kernel import ControlPlane, SessionKernel
from ssc_p0.policy import (PolicyGateway, envelope_aprovacao_padrao,
                           politica_padrao)
from ssc_p0.providers import FakeProvider
from ssc_p0.router import TaskRouter

DIR_P0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SAIDAS = os.path.join(DIR_P0, "saidas")
DIR_LABS = os.path.join(DIR_SAIDAS, "labs")
DIR_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "fixtures")


class Lab:
    """Feixe de componentes de uma corrida."""

    def __init__(self, raiz, relogio=None, teto_custo=0.5,
                 programa_providers=None, seeds=None,
                 funcoes_sucesso=None, observados=None,
                 catalogo=None, politica=None, aprovacao=None,
                 fabrica_provider=None, teto_tokens=100000):
        """`fabrica_provider(executor_id, executor, resolvido) -> provider`.

        Ponto de troca acrescentado pela P2: sem ele, `Lab` so sabia montar
        `FakeProvider`, e executar de verdade exigiria um segundo montador
        de laboratorio — dois montadores que precisam concordar sao dois
        montadores que um dia divergem. O default continua sendo o falso
        deterministico, e nenhuma corrida da P0 muda de comportamento.
        """
        self.raiz = os.path.realpath(str(raiz))
        self.relogio = relogio or RelogioDeterministico()
        self.catalogo = catalogo or catalogo_padrao()
        self.politica = politica or politica_padrao()
        self.aprovacao = aprovacao or envelope_aprovacao_padrao()
        self.kernel = SessionKernel(self.raiz, self.relogio,
                                    raizes_fontes=[DIR_FIXTURES])
        self.control = ControlPlane(self.kernel)
        self.policy = PolicyGateway(self.politica, self.catalogo, self.relogio)
        self.router = TaskRouter(self.kernel, self.policy, self.catalogo,
                                 self.control)
        programa_providers = programa_providers or {}
        seeds = seeds or {}
        funcoes_sucesso = funcoes_sucesso or {}
        observados = observados or {}
        self.providers = {}
        for eid, executor in self.catalogo.executores.items():
            chave = (executor["provedor"], executor["modelo"])
            resolvido = {"provedor": executor["provedor"],
                         "modelo": executor["modelo"], "effort": "alto"}
            if fabrica_provider is not None:
                self.providers[chave] = fabrica_provider(eid, executor,
                                                         resolvido)
                continue
            self.providers[chave] = FakeProvider(
                resolvido,
                seed=seeds.get(eid, 7),
                programa=programa_providers.get(eid, ["sucesso"]),
                funcao_sucesso=funcoes_sucesso.get(eid),
                observado=observados.get(eid))
        self.execution = ExecutionGateway(
            self.kernel, self.policy, self.catalogo, self.providers,
            self.control, router=self.router)
        self.envelope = self.control.abrir_sessao(
            escopo={"repo_alvo": self.raiz, "modo": "read-only",
                    "fronteiras": []},
            permissoes={"pode_escrever": False, "pode_executar": True,
                        "pode_rede": False, "conectores_com_escrita": []},
            orcamento={"teto_custo": teto_custo, "teto_tokens": teto_tokens,
                       "teto_tempo": 3600, "consumido_custo": 0.0,
                       "consumido_tokens": 0, "consumido_tempo": 0},
            politica_ref=sha256_de(self.politica),
            catalogo_ref=self.catalogo.hash_catalogo(),
            resumo_aprovacao={
                "custo": sha256_de(self.aprovacao),
                "autonomia": sha256_de({"controle": "confirma-no-gasto"}),
            })

    def juiz2(self, seed=99, fila=None):
        return Juiz2(fila or fila_juizes_padrao(), seed)

    def selecao(self, provedor, modelo, effort="alto", modo="read-only",
                controle="confirma-no-gasto"):
        return {"ferramenta": "fake-cli", "provedor": provedor,
                "modelo": modelo, "effort": effort, "modo": modo,
                "controle": controle}

    def gravar_evidencia(self, nome: str, evidencia: dict) -> str:
        """Grava o JSON de evidencia da corrida sob 05_p0/saidas."""
        return gravar_evidencia(nome, evidencia)


def gravar_evidencia(nome: str, evidencia: dict) -> str:
    """Grava o JSON de evidencia da corrida sob 05_p0/saidas."""
    import json
    os.makedirs(DIR_SAIDAS, exist_ok=True)
    caminho = os.path.join(DIR_SAIDAS, nome)
    with open(caminho, "wb") as f:
        f.write(json.dumps(evidencia, ensure_ascii=False,
                           indent=2, sort_keys=True).encode("utf-8"))
    return caminho
