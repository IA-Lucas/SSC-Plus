"""Ato explicito do proprietario para renovar declaracoes de tier.

Este comando nao infere plano, nao consulta CLI e nao abre a P2. Ele apenas
registra uma afirmacao atual do proprietario, com backup e lease verificado.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, "05_p0"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a", "evidencias"))

import leitor_tiers  # noqa: E402
from contencao import verificar_lock  # noqa: E402
from preflight.frota_real import espec_de  # noqa: E402
from preflight.sombra import VALIDADE_MAXIMA_HORAS  # noqa: E402
from seguranca_artefatos import gravar_json_atomico  # noqa: E402


CAMINHO_TIERS = leitor_tiers.CAMINHO_PADRAO
DIR_BACKUPS = os.path.join(_RAIZ, "06_p1a", "evidencias", "backups")
SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p2-ops")
PROVEDORES = ("codex", "kimi", "google")
CHAVES_RAIZ = {"tipo", "ato", "limites", "validade_maxima_horas",
               "declaracoes"}
CHAVES_DECLARACAO = {"provider_id", "tier", "declarado_por",
                     "declarado_em_utc", "validade_horas"}


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _verificar_lock_vivo(fence_esperado=None):
    return verificar_lock(_RAIZ, SESSAO_LOCK, fence_esperado)


def _carregar_fechado(caminho: str) -> dict:
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: declaracao atual ilegivel ({exc})")
    if not isinstance(dados, dict) or set(dados) != CHAVES_RAIZ:
        raise SystemExit("PARADA: schema fechado da declaracao foi violado")
    entradas = dados.get("declaracoes")
    if not isinstance(entradas, list) or len(entradas) not in (2, 3):
        raise SystemExit("PARADA: conjunto de declaracoes inesperado")
    if any(not isinstance(e, dict) or set(e) != CHAVES_DECLARACAO
           for e in entradas):
        raise SystemExit("PARADA: schema fechado de uma declaracao foi violado")
    ids = {e["provider_id"] for e in entradas}
    if ids not in ({"codex", "kimi"}, set(PROVEDORES)):
        raise SystemExit(
            "PARADA: declaracoes precisam cobrir codex, kimi e google")
    return dados


def renovar(tiers: dict[str, str], instante: datetime | None = None) -> str:
    """Renova somente depois de validar tier, backup e o mesmo fence."""
    if set(tiers) != set(PROVEDORES):
        raise SystemExit(
            "PARADA: declare exatamente os tiers de codex, kimi e google")
    for provider_id in PROVEDORES:
        esperado = espec_de(provider_id).plano_esperado
        if tiers[provider_id] != esperado:
            raise SystemExit(
                f"PARADA: tier de {provider_id} diverge da especificacao; "
                f"esperado={esperado!r}, declarado={tiers[provider_id]!r}")

    agora = instante or agora_utc()
    if agora.tzinfo is None:
        raise SystemExit("PARADA: relogio sem fuso nao renova declaracao")
    agora = agora.astimezone(timezone.utc)
    carimbo = agora.strftime("%Y%m%dT%H%M%S%fZ")
    timestamp = agora.strftime("%Y-%m-%dT%H:%M:%SZ")

    lock = _verificar_lock_vivo()
    fence = lock["fence"]
    atual = _carregar_fechado(CAMINHO_TIERS)

    # Backup completo nasce antes da alteracao e tambem sob lease vivo.
    os.makedirs(DIR_BACKUPS, exist_ok=True)
    backup = os.path.join(
        DIR_BACKUPS, f"tiers_declarados-{carimbo}-pre-renovacao.json")
    gravar_json_atomico(backup, atual)

    novo = dict(atual)
    novo["validade_maxima_horas"] = VALIDADE_MAXIMA_HORAS
    novo["declaracoes"] = [
        {
            "provider_id": provider_id,
            "tier": tiers[provider_id],
            "declarado_por": "proprietario",
            "declarado_em_utc": timestamp,
            "validade_horas": VALIDADE_MAXIMA_HORAS,
        }
        for provider_id in PROVEDORES
    ]

    # A janela entre backup e publicacao tambem pode exceder/perder lease.
    _verificar_lock_vivo(fence)
    gravar_json_atomico(CAMINHO_TIERS, novo)

    # A leitura canonica precisa reconhecer exatamente o que foi publicado.
    carregado = leitor_tiers.carregar_tiers(CAMINHO_TIERS)
    if set(carregado) != set(PROVEDORES) or any(
            carregado[p].tier != tiers[p] for p in PROVEDORES):
        raise SystemExit("PARADA: declaracao publicada nao passou pelo leitor")
    return backup


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Registra a confirmacao atual de tiers pelo proprietario.")
    parser.add_argument("--confirmo-proprietario", action="store_true",
                        help="confirma que os tiers informados estao ativos agora")
    parser.add_argument("--codex-tier", required=True)
    parser.add_argument("--kimi-tier", required=True)
    parser.add_argument("--google-tier", required=True)
    args = parser.parse_args(argv)
    if not args.confirmo_proprietario:
        raise SystemExit(
            "PARADA: falta --confirmo-proprietario; tier nunca e inferido")
    backup = renovar({"codex": args.codex_tier, "kimi": args.kimi_tier,
                      "google": args.google_tier})
    print("declaracoes renovadas por no maximo 24 h")
    print(f"backup: {backup}")
    print("P2 ainda fechada: gere e valide um preflight novo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
