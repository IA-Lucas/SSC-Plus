"""Apoio comum dos testes P0: sys.path + helpers de lab em diretorio tmp.

0.2.1: os temporarios de teste ficam na pasta IGNORADA do laboratorio
(05_p0/saidas/labs/tests/) — nada de temp do SO sem autorizacao. Cada
teste limpa o proprio diretorio no tearDown (limpar_lab).
"""

import json
import os
import shutil
import sys
import uuid

_DIR = os.path.dirname(os.path.abspath(__file__))
_DIR_P0 = os.path.dirname(_DIR)
sys.path.insert(0, _DIR_P0)
sys.path.insert(0, os.path.join(_DIR_P0, "cenarios"))

from comum import Lab  # noqa: E402
from ssc_p0 import contratos as ct  # noqa: E402
from ssc_p0.canonico import canonico, sha256_de  # noqa: E402
from ssc_p0.judge import Juiz1  # noqa: E402

DIR_TESTS = os.path.join(_DIR_P0, "saidas", "labs", "tests")


def novo_lab(tmp=None, **kwargs):
    """Lab completo numa raiz isolada por teste (pasta ignorada do lab)."""
    raiz = tmp or os.path.join(DIR_TESTS, uuid.uuid4().hex)
    os.makedirs(raiz, exist_ok=True)
    return Lab(os.path.join(raiz, "lab"), **kwargs)


def limpar_lab(lab) -> None:
    """Remove a raiz do lab de teste (inventario limpo por teste)."""
    try:
        lab.kernel.fechar()
    except Exception:
        pass
    shutil.rmtree(os.path.dirname(lab.raiz), ignore_errors=True)


def fluxo_sucesso(lab, modelo="modelo-x", provedor="prov-a", nivel="L2",
                  intencao="tarefa de fluxo feliz"):
    """Wu aprovada + decisao + execucao com sucesso + juiz aprovado.

    Devolve (wu, decisao, resultado_execucao, veredito).
    """
    wu = lab.router.forjar(
        intencao=intencao,
        criterios={"tipo": "saida-nao-vazia"},
        tipo="ato", nivel=nivel,
        perfil={"modalidade": "texto", "ferramentas": [],
                "formato_saida": "livre", "contexto_max_tokens": 8000,
                "dominio": "geral", "privacidade": "remoto-permitido",
                "latencia_max_ms": None, "orcamento_max_custo": None},
        classe="C1")
    decisao = lab.router.propor_decisao(
        wu, rota="padrao", selecao=lab.selecao(provedor, modelo),
        aprovacao_custo=lab.aprovacao, motivo="fluxo de teste")
    resultado = lab.execution.executar(
        wu, decisao, idempotency_key="fluxo-teste", entrada=b"dados")
    assert resultado.status == "sucesso", resultado.status
    veredito = Juiz1.julgar(
        lab.kernel, wu, resultado.attempt_id,
        lambda saida, pacote, attempt: (
            [{"criterio": "saida nao vazia", "evidencia": str(len(saida)),
              "passou": bool(saida)}],
            "aprovado" if saida else "reprovado"))
    return wu, decisao, resultado, veredito


def snapshot_normalizado(kernel):
    """estado_snapshot com campos de ciclo de vida normalizados p/ comparar."""
    snap = kernel.estado_snapshot()
    if snap["envelope"]:
        snap["envelope"]["estado"] = "*"
        snap["envelope"]["encerrado_em"] = None
    return snap
