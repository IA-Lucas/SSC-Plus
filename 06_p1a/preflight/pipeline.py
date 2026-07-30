"""Pipeline de preflight da frota real (SSC+ P1-A, experimental).

Encadeia: (a) auditoria de ambiente; (b) auditoria de config persistida;
(c) deteccao do CLI; (d) versao/status/modelos via sensores;
(e) classificacao ELIGIBLE | SUPERVISED | BLOCKED com erros tipados.

Qualquer violacao economica ou de auth BLOQUEIA ANTES de qualquer sensor
de modelo ser invocado. Google e Grok nunca saem de SUPERVISED, mesmo com
tudo verde (teto_resultado da especificacao).
"""

import os
from dataclasses import dataclass, field

from .adaptadores import AdaptadorPreflight, plano_reconhecido
from .economia import (CliIndisponivel, ConflitoAmbienteLogin, ErroPreflight,
                       ModeloRemovido, OAuthAusente, PlanoNaoReconhecido,
                       QuotaEsgotada, auditar_ambiente, auditar_config,
                       auditar_status)

RESULTADOS = ("ELIGIBLE", "SUPERVISED", "BLOCKED")


@dataclass(eq=False)
class RelatorioPreflight:
    """Relatorio de preflight de um provedor (round-trip via to_dict)."""

    provider_id: str
    resultado: str                       # ELIGIBLE | SUPERVISED | BLOCKED
    erros: list = field(default_factory=list)
    caminho: str | None = None
    versao: str | None = None
    plano: str | None = None
    origem_credencial: str = "ausente"
    quota: str = "desconhecida"
    modelos: list = field(default_factory=list)

    def __post_init__(self):
        if self.resultado not in RESULTADOS:
            raise ValueError(f"resultado fora do enum: {self.resultado!r}")

    def __eq__(self, outro):
        return isinstance(outro, RelatorioPreflight) \
            and self.to_dict() == outro.to_dict()

    def to_dict(self) -> dict:
        return {"provider_id": self.provider_id,
                "resultado": self.resultado,
                "caminho": self.caminho, "versao": self.versao,
                "plano": self.plano,
                "origem_credencial": self.origem_credencial,
                "quota": self.quota, "modelos": list(self.modelos),
                "erros": [e.to_dict() for e in self.erros]}

    @classmethod
    def from_dict(cls, dados: dict) -> "RelatorioPreflight":
        return cls(provider_id=dados["provider_id"],
                   resultado=dados["resultado"],
                   erros=[ErroPreflight.from_dict(e)
                          for e in dados.get("erros", [])],
                   caminho=dados.get("caminho"),
                   versao=dados.get("versao"), plano=dados.get("plano"),
                   origem_credencial=dados.get("origem_credencial",
                                               "ausente"),
                   quota=dados.get("quota", "desconhecida"),
                   modelos=list(dados.get("modelos", [])))


def _normalizar_sensores(sensores) -> dict:
    """Aceita um sensor unico (todas as sondas) ou dict com chaves
    "exec" (versao/login) e "modelos" (descoberta)."""
    if callable(sensores):
        return {"exec": sensores, "modelos": sensores}
    normalizado = dict(sensores)
    normalizado.setdefault("exec", None)
    normalizado.setdefault("modelos", normalizado.get("exec"))
    if normalizado["exec"] is None or normalizado["modelos"] is None:
        raise ValueError("sensores: ao menos 'exec' e obrigatorio")
    return normalizado


def executar_preflight(provider_spec, sensores, env=None,
                       config_persistida=None) -> RelatorioPreflight:
    """Preflight completo de um provedor. Nunca invoca modelo produtivo.

    provider_spec: EspecProvedor (frota_real). sensores: sensor unico ou
    dict {"exec": fn, "modelos": fn}, fn(argv, env) -> (rc, out, err).
    env: ambiente a auditar (padrao: os.environ — nunca mutado).
    config_persistida: dict ja parseado de auth/config do CLI.
    """
    sens = _normalizar_sensores(sensores)
    ambiente = dict(os.environ if env is None else env)
    persistido = dict(config_persistida or {})

    def relatorio(resultado, erros, **diagnostico):
        base = {"provider_id": provider_spec.provider_id,
                "caminho": provider_spec.executavel}
        base.update(diagnostico)
        return RelatorioPreflight(resultado=resultado, erros=list(erros),
                                  **base)

    # (a) auditoria de ambiente — chaves PAYG, case-insensitive.
    viol_env = auditar_ambiente(ambiente)
    relacionadas = frozenset(k.lower()
                             for k in provider_spec.chaves_payg_relacionadas)
    env_relacionadas = [v for v in viol_env
                        if (v.alvo or "").lower() in relacionadas]
    env_outras = [v for v in viol_env
                  if (v.alvo or "").lower() not in relacionadas]

    # (b) auditoria da config persistida + status economico estatico.
    viol_cfg = auditar_config(persistido)
    viol_status = auditar_status({
        "billing_mode": provider_spec.billing_mode,
        "variable_cost": provider_spec.variable_cost,
        "auth_mode": provider_spec.auth_esperada})

    # Bloqueio pre-sensor: violacoes que NAO dependem do status de login
    # (chaves PAYG de outros provedores, config PAYG, billing/custo/auth).
    bloqueio_imediato = env_outras + viol_cfg + viol_status
    if bloqueio_imediato:
        return relatorio("BLOCKED", bloqueio_imediato + env_relacionadas)

    # (c)+(d) deteccao, versao e login via sensor de execucao.
    adaptador = AdaptadorPreflight(provider_spec,
                                   sensor_exec=sens["exec"],
                                   sensor_modelos=sens["modelos"],
                                   env=ambiente)
    try:
        versao = adaptador.detectar_versao()
    except CliIndisponivel as exc:
        return relatorio("BLOCKED", env_relacionadas + [exc])

    login = adaptador.consultar_login()
    erros = []
    # Chave PAYG do proprio provedor + login OAuth ativo = CONFLITO:
    # a chave nunca pode vencer o OAuth da assinatura. Sem login ativo, a
    # chave permanece uma violacao economica simples (P1A-PAYG-ENV).
    if env_relacionadas:
        if login["logado"]:
            erros.append(ConflitoAmbienteLogin(
                detalhe="chave(s) PAYG do provedor no ambiente com login "
                        "OAuth da assinatura ativo; a chave nunca vence o "
                        "OAuth: " + ", ".join(v.alvo
                                              for v in env_relacionadas),
                alvo=", ".join(v.alvo for v in env_relacionadas)))
        else:
            erros.extend(env_relacionadas)
    if not login["logado"]:
        erros.append(OAuthAusente(
            detalhe="login OAuth da assinatura ausente "
                    f"({provider_spec.canal_oficial})"))
    elif login["origem_credencial"] != provider_spec.auth_esperada:
        erros.append(OAuthAusente(
            detalhe=f"origem {login['origem_credencial']} diverge da "
                    f"esperada {provider_spec.auth_esperada}"))
    if login["logado"] and not plano_reconhecido(
            login["plano"], provider_spec.planos_aceitos):
        erros.append(PlanoNaoReconhecido(
            detalhe=f"plano reportado {login['plano']!r} fora de "
                    f"{list(provider_spec.planos_aceitos)}"))
    if login["quota"] == "esgotada":
        erros.append(QuotaEsgotada(
            detalhe=f"franquia da assinatura {provider_spec.provider_id} "
                    "esgotada; nenhuma invocacao (STOP_WAIT_RESET, "
                    "nunca PAYG)"))
    if erros:
        # Bloqueio ANTES de qualquer sensor de modelo.
        return relatorio("BLOCKED", erros, versao=versao,
                         plano=login["plano"],
                         origem_credencial=login["origem_credencial"],
                         quota=login["quota"])

    # (d) descoberta de modelos — somente com economia/auth verdes.
    try:
        modelos = adaptador.descobrir_modelos()
    except CliIndisponivel as exc:
        return relatorio("BLOCKED", [exc], versao=versao,
                         plano=login["plano"],
                         origem_credencial=login["origem_credencial"],
                         quota=login["quota"])
    esperados = [m for m in modelos if any(
        esperado in m for esperado in provider_spec.modelos_esperados)]
    if not esperados:
        return relatorio("BLOCKED",
                         [ModeloRemovido(
                             detalhe="descoberta sem nenhum modelo esperado "
                                     f"{list(provider_spec.modelos_esperados)}"
                                     f"; encontrados: {modelos}")],
                         versao=versao, plano=login["plano"],
                         origem_credencial=login["origem_credencial"],
                         quota=login["quota"], modelos=modelos)

    # (e) classificacao: google/grok tem teto SUPERVISED pela especificacao.
    return relatorio(provider_spec.teto_resultado, [],
                     versao=versao, plano=login["plano"],
                     origem_credencial=login["origem_credencial"],
                     quota=login["quota"], modelos=modelos)
