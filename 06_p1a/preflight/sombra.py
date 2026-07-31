"""Declaracao de tier pelo proprietario — trilha SHADOW_ELIGIBLE (P1-A.3).

Decisao soberana sobre as emendas da P1-A.2, item 1 (APROVADA COM
LIMITES): o tier DECLARADO pelo proprietario, somado ao OAuth OBSERVADO
no CLI, pode habilitar SOMENTE `SHADOW_ELIGIBLE`, com validade maxima de
24 horas. Nao autoriza P2 nem execucao autonoma.

A declaracao e um ato humano registrado em `06_p1a/tiers_declarados.json`
— nunca inferida pelo codigo. Declaracao ausente, timestamp ilegivel,
declaracao no futuro ou validade expirada = trilha sombra INDISPONIVEL
(fail-closed: o pipeline cai no bloqueio estatico original, como antes da
emenda). A validade efetiva nunca excede 24 h, mesmo que o arquivo
declare mais.

Como todo modulo do pacote `preflight/`, este NAO abre arquivos nem rede
(invariante de isolamento): quem le o JSON do disco e o runner da
missao, que entrega o dict ja parseado a `carregar_declaracoes`.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

VALIDADE_MAXIMA_HORAS = 24

__all__ = ["VALIDADE_MAXIMA_HORAS", "DeclaracaoTier",
           "carregar_declaracoes", "declaracao_valida", "expira_em"]


@dataclass(frozen=True)
class DeclaracaoTier:
    """Declaracao de tier do proprietario para um provedor."""

    provider_id: str
    tier: str
    declarado_por: str
    declarado_em_utc: str            # ISO 8601 UTC, ex.: 2026-07-31T01:31:00Z
    validade_horas: int = VALIDADE_MAXIMA_HORAS


def _parse_utc(texto) -> datetime | None:
    """Timestamp ISO UTC estrito; ilegivel = None (fail-closed).

    A conversao de fuso tambem fica dentro do try (revisao P1-A.3):
    offsets extremos (ex.: ano 1 com +14:00) transbordam o calendario
    ao normalizar para UTC — OverflowError = None, nunca excecao.
    """
    try:
        instante = datetime.fromisoformat(
            str(texto).strip().replace("Z", "+00:00"))
        if instante.tzinfo is None:
            return None
        return instante.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def expira_em(decl: DeclaracaoTier) -> datetime | None:
    """Expiracao efetiva: declarado_em + min(validade declarada, 24 h).

    A validade NUNCA excede 24 horas, mesmo que a declaracao peca mais;
    validade declarada <= 0 ou timestamp ilegivel = None (fail-closed).
    Timestamp extremo que transborda o calendario (OverflowError) tambem
    e None — nunca excecao para o chamador.
    """
    declarado = _parse_utc(decl.declarado_em_utc)
    if declarado is None:
        return None
    try:
        horas = min(int(decl.validade_horas), VALIDADE_MAXIMA_HORAS)
        if horas <= 0:
            return None
        return declarado + timedelta(hours=horas)
    except (TypeError, ValueError, OverflowError):
        return None


def declaracao_valida(decl: DeclaracaoTier,
                      agora: datetime | None = None) -> bool:
    """Declaracao dentro da janela [declarado_em, expira_em).

    Declaracao datada no FUTURO tambem e invalida: um timestamp que o
    relogio local ainda nao alcancou nao pode ser verificado (fail-closed
    contra adulteracao de janela). Relogio `agora` NAIVE e invalido
    (revisao P1-A.3): o Python o interpretaria como horario LOCAL,
    deslocando a janela pelo offset do fuso.
    """
    instante = agora if agora is not None else datetime.now(timezone.utc)
    if instante.tzinfo is None:
        return False
    instante = instante.astimezone(timezone.utc)
    declarado = _parse_utc(decl.declarado_em_utc)
    limite = expira_em(decl)
    if declarado is None or limite is None:
        return False
    return declarado <= instante < limite


def carregar_declaracoes(dados: dict) -> dict:
    """Declaracoes a partir do JSON JA PARSEADO pelo runner da missao.

    Estrutura inesperada ou entradas malformadas = trilha sombra
    indisponivel ({}), nunca excecao propagada — o pipeline decide o
    bloqueio com os erros tipados da especificacao.
    """
    try:
        declaracoes = {}
        for e in dados["declaracoes"]:
            # Fail-closed (revisao P1-A.3): os tres campos precisam ser
            # TEXTO nao vazio — `null` nao vira a string "None"; e o
            # declarante precisa ser o PROPRIETARIO (a emenda e "tier
            # declarado PELO PROPRIETARIO" — qualquer outro valor nao
            # habilita nada).
            provider_id = e["provider_id"]
            tier = e["tier"]
            declarado_por = e["declarado_por"]
            if not all(isinstance(v, str) and v.strip()
                       for v in (provider_id, tier, declarado_por)):
                continue
            if declarado_por.strip().lower() != "proprietario":
                continue
            decl = DeclaracaoTier(
                provider_id=provider_id.strip(),
                tier=tier.strip(),
                declarado_por=declarado_por.strip(),
                declarado_em_utc=str(e["declarado_em_utc"]),
                validade_horas=int(e.get("validade_horas",
                                         VALIDADE_MAXIMA_HORAS)))
            declaracoes[decl.provider_id] = decl
        return declaracoes
    except (KeyError, TypeError, ValueError, OverflowError):
        # OverflowError (revisao P1-A.3): validade_horas=Infinity vinda
        # do JSON — int(inf) transborda; estrutura inesperada = {}.
        return {}
