"""Providers falsos deterministicos por seed (D7 §3, D6 §2.7).

Bateria de comportamentos programaveis por cenario:
sucesso, falha-transitoria (com Retry-After), falha-contrato, falha-quota,
timeout (enviou, sem resposta -> efeito incerto), saida-invalida,
efeito-externo-incerto.

Latencia e custo sao SIMULADOS e rotulados 'simulado' (MR-2).
PROIBIDO provider falso otimista: a bateria de falhas e obrigatoria.
"""

from dataclasses import dataclass
from typing import Optional

from .canonico import sha256_bytes

COMPORTAMENTOS = frozenset({
    "sucesso", "falha-transitoria", "falha-contrato", "falha-quota",
    "timeout", "saida-invalida", "efeito-incerto",
})


@dataclass
class RespostaProvedor:
    """O que o adaptador falso devolve ao Execution Gateway."""

    ok: bool
    saida: bytes
    falha: Optional[str]                 # enum resultado do attempt, se falha
    executor_observado: Optional[dict]   # None honesto quando nao reporta
    efeito_externo: str                  # nenhum/aplicado/nao-aplicado/incerto
    custo: dict                          # {'valor', 'tokens', 'rotulo': 'simulado'}
    latencia_ms: int
    latencia_rotulo: str                 # sempre 'simulado'
    retry_after_ms: Optional[int]


class FakeProvider:
    """Adaptador falso: mesma seed + mesmo programa = mesmas respostas.

    programa: lista de comportamentos consumidos por chamada; o ultimo
    comportamento repete-se quando a lista acaba. Cada item pode ser str
    (nome do comportamento) ou dict com chaves extras:
      {'comportamento': 'falha-transitoria', 'retry_after_ms': 5000,
       'efeito': 'nao-aplicado'}
    funcao_sucesso: callable(bytes_da_entrada, pacote_dict) -> bytes, usada
    no comportamento 'sucesso' (deterministica por construcao do cenario).
    observado: dict {provedor, modelo, effort} reportado na resposta; default
    = o executor resolvido; pode ser programado para divergir (teste de
    "alias nao prova identidade").
    """

    def __init__(self, executor_resolvido: dict, seed: int,
                 programa=None, funcao_sucesso=None, observado=None):
        self.executor = dict(executor_resolvido)
        self.seed = int(seed)
        self.programa = list(programa or ["sucesso"])
        for item in self.programa:
            nome = item if isinstance(item, str) else item.get("comportamento")
            if nome not in COMPORTAMENTOS:
                raise ValueError(f"comportamento desconhecido: {nome!r}")
        self.funcao_sucesso = funcao_sucesso
        self.observado_programado = observado
        self.chamadas = 0

    def _derivado(self, rotulo: str, modulo: int) -> int:
        h = sha256_bytes(f"{self.seed}|{self.executor.get('modelo')}|"
                         f"{self.chamadas}|{rotulo}".encode("utf-8"))
        return int(h[:8], 16) % modulo

    def _observado(self) -> dict:
        if self.observado_programado is not None:
            return dict(self.observado_programado)
        return {
            "provedor": self.executor["provedor"],
            "modelo": self.executor["modelo"],
            "effort": self.executor["effort"],
        }

    def _custos(self) -> tuple[dict, int]:
        valor = round((self._derivado("custo", 90) + 10) / 1000.0, 4)
        tokens = self._derivado("tokens", 900) + 100
        latencia = 50 + self._derivado("latencia", 950)
        return ({"valor": valor, "tokens": tokens, "rotulo": "simulado"}, latencia)

    def invocar(self, entrada: bytes, pacote: Optional[dict] = None) -> RespostaProvedor:
        item = self.programa[min(self.chamadas, len(self.programa) - 1)]
        self.chamadas += 1
        if isinstance(item, str):
            comportamento, extras = item, {}
        else:
            extras = dict(item)
            comportamento = extras.pop("comportamento")
        custo, latencia = self._custos()
        observado = self._observado()

        if comportamento == "sucesso":
            if self.funcao_sucesso is not None:
                saida = self.funcao_sucesso(entrada, pacote or {})
            else:
                saida = b"saida-simulada:" + bytes(str(self.seed), "ascii")
            return RespostaProvedor(
                ok=True, saida=saida, falha=None,
                executor_observado=observado,
                efeito_externo=extras.get("efeito", "aplicado"),
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=None,
            )
        if comportamento == "falha-transitoria":
            return RespostaProvedor(
                ok=False, saida=b"erro transitorio simulado (429/5xx)",
                falha="falha-transitoria", executor_observado=observado,
                efeito_externo=extras.get("efeito", "nao-aplicado"),
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=extras.get("retry_after_ms"),
            )
        if comportamento == "falha-contrato":
            return RespostaProvedor(
                ok=False, saida=b"4xx de contrato simulado",
                falha="falha-contrato", executor_observado=observado,
                efeito_externo=extras.get("efeito", "nao-aplicado"),
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=None,
            )
        if comportamento == "falha-quota":
            return RespostaProvedor(
                ok=False, saida=b"quota esgotada (texto cru de CLI) simulado",
                falha="falha-quota", executor_observado=observado,
                efeito_externo=extras.get("efeito", "nao-aplicado"),
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=None,
            )
        if comportamento == "timeout":
            # Enviou e nao houve resposta: efeito externo INCERTO.
            return RespostaProvedor(
                ok=False, saida=b"", falha="indeterminado",
                executor_observado=observado,
                efeito_externo="incerto",
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=None,
            )
        if comportamento == "efeito-incerto":
            return RespostaProvedor(
                ok=False, saida=b"conexao cortada sem resposta",
                falha="indeterminado", executor_observado=observado,
                efeito_externo="incerto",
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=None,
            )
        if comportamento == "saida-invalida":
            return RespostaProvedor(
                ok=False, saida=b"<<<nao-json>>> {{{",
                falha="falha-contrato", executor_observado=observado,
                efeito_externo=extras.get("efeito", "nao-aplicado"),
                custo=custo, latencia_ms=latencia, latencia_rotulo="simulado",
                retry_after_ms=None,
            )
        raise AssertionError(f"comportamento nao tratado: {comportamento!r}")
