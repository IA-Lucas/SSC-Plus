"""Maquinas de estado fechadas (D5 §1.2, §2.1, §5.1).

Toda transicao fora da tabela e ilegal e levanta TransicaoIlegal.
`None` como origem representa a criacao do objeto.
"""

from .contratos import ESTADOS_WORK_UNIT


class TransicaoIlegal(Exception):
    """Transicao fora da tabela da maquina de estados."""


# D5 §1.2 — Sessao
SESSAO = frozenset({
    (None, "ativa"),               # abertura aprovada (portao de custo/autonomia)
    ("ativa", "suspensa"),         # checkpoint validado gravado (IP-1)
    ("suspensa", "retomada"),      # checkpoint valido + selo + log integro
    ("retomada", "ativa"),         # primeira operacao pos-retomada
    ("ativa", "encerrada"),        # ato humano / orcamento / condicao
    ("retomada", "encerrada"),     # idem
    ("suspensa", "encerrada"),     # ato humano
})

# D5 §2.1 — WorkUnit (transicoes nomeadas)
_WORKUNIT_NOMEADAS = {
    (None, "proposta"),
    ("proposta", "aguardando-aprovacao"),
    ("proposta", "aprovada"),
    ("aguardando-aprovacao", "aprovada"),
    ("aguardando-aprovacao", "cancelada"),
    ("aprovada", "em-execucao"),
    ("em-execucao", "aguardando-validacao"),
    ("em-execucao", "em-execucao"),      # retry/fallback: novo attempt, mesma WU
    ("aguardando-validacao", "concluida"),
    ("aguardando-validacao", "reprovada"),
    ("aguardando-validacao", "proposta"),  # inconclusivo -> reformulacao humana
    ("reprovada", "proposta"),             # reparo
}

TERMINAIS_WORK_UNIT = frozenset({"concluida", "cancelada"})

# D5 §2.1 — "qualquer nao-terminal -> cancelada" (ato humano / encerramento)
WORKUNIT = frozenset(
    _WORKUNIT_NOMEADAS
    | {(estado, "cancelada")
       for estado in ESTADOS_WORK_UNIT - TERMINAIS_WORK_UNIT}
)

# D5 §5.1 — Attempt: criado -> despachado -> concluido (sem retry interno)
ATTEMPT = frozenset({
    (None, "criado"),
    ("criado", "despachado"),
    ("despachado", "concluido"),
})

# Marcacao de orfao: EXCLUSIVA da retomada (D6 §4); nunca caminho normal.
ATTEMPT_RETOMADA = frozenset({
    ("criado", "orfao"),
    ("despachado", "orfao"),
})

_NOMES = {"sessao": SESSAO, "workunit": WORKUNIT, "attempt": ATTEMPT}


def transitar(tabela, de: str | None, para: str, nome: str = "maquina") -> str:
    """Devolve `para` se (de, para) esta na tabela; senao TransicaoIlegal."""
    if (de, para) not in tabela:
        raise TransicaoIlegal(
            f"{nome}: transicao ilegal {de!r} -> {para!r}"
        )
    return para


def transitar_sessao(de, para):
    return transitar(SESSAO, de, para, "sessao")


def transitar_workunit(de, para):
    return transitar(WORKUNIT, de, para, "workunit")


def transitar_attempt(de, para):
    return transitar(ATTEMPT, de, para, "attempt")


def marcar_orfao(de):
    """Transicao exclusiva da retomada: attempt sem conclusao -> orfao."""
    return transitar(ATTEMPT_RETOMADA, de, "orfao", "attempt(retomada)")
