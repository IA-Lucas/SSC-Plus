"""Pipeline de preflight da frota real (SSC+ P1-A, experimental).

Encadeia: (a) auditoria de ambiente; (b) auditoria de config persistida;
(c) deteccao do CLI; (d) versao/status/modelos via sensores;
(e) classificacao ELIGIBLE | SHADOW_ELIGIBLE | SUPERVISED | BLOCKED com
erros tipados.

Qualquer violacao economica ou de auth BLOQUEIA ANTES de qualquer sensor
de modelo ser invocado. Google e Grok nunca saem de SUPERVISED, mesmo com
tudo verde (teto_resultado da especificacao).

Emendas P1-A.3 (decisao soberana sobre a P1-A.2):
- item 1: tier DECLARADO pelo proprietario + OAuth OBSERVADO habilita
  SOMENTE SHADOW_ELIGIBLE, com validade maxima de 24 h — nao autoriza P2
  nem execucao autonoma;
- item 4: sem modelo exato observado por fonte oficial nao interativa, o
  provedor fica com teto SUPERVISED (claude); a descoberta de modelos e
  OPCIONAL na especificacao (comandos["modelos"] = None a desativa).
"""

import os
from dataclasses import dataclass, field

from .adaptadores import AdaptadorPreflight, plano_reconhecido
from .economia import (CliIndisponivel, ConflitoAmbienteLogin,
                       DeclaracaoExpirada, ErroPreflight, ModeloRemovido,
                       OAuthAusente, PlanoNaoReconhecido, QuotaEsgotada,
                       auditar_ambiente, auditar_config, auditar_status)
from .sombra import declaracao_valida, expira_em

RESULTADOS = ("ELIGIBLE", "SHADOW_ELIGIBLE", "SUPERVISED", "BLOCKED")


@dataclass(eq=False)
class RelatorioPreflight:
    """Relatorio de preflight de um provedor (round-trip via to_dict)."""

    provider_id: str
    resultado: str                       # ELIGIBLE | SHADOW_ELIGIBLE |
                                         # SUPERVISED | BLOCKED
    erros: list = field(default_factory=list)
    caminho: str | None = None
    versao: str | None = None
    plano: str | None = None
    origem_credencial: str = "ausente"
    quota: str = "desconhecida"
    modelos: list = field(default_factory=list)
    sombra: dict | None = None           # diagnostico da trilha SHADOW

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
                "sombra": self.sombra,
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
                   modelos=list(dados.get("modelos", [])),
                   sombra=dados.get("sombra"))


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
                       config_persistida=None, tiers_declarados=None,
                       agora=None) -> RelatorioPreflight:
    """Preflight completo de um provedor. Nunca invoca modelo produtivo.

    provider_spec: EspecProvedor (frota_real). sensores: sensor unico ou
    dict {"exec": fn, "modelos": fn}, fn(argv, env) -> (rc, out, err).
    env: ambiente a auditar (padrao: os.environ — nunca mutado).
    config_persistida: dict ja parseado de auth/config do CLI.
    tiers_declarados: provider_id -> DeclaracaoTier (sombra.py), o ato
    humano registrado da emenda P1-A.3 item 1; agora: relogio injetavel
    para a validade de 24 h (padrao: UTC real).
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

    # Emenda P1-A.3, item 5 (google/grok): ZERO sondas automaticas. A
    # classificacao e estatica no teto SUPERVISED — somente as auditorias
    # locais (ambiente/config/status) contam; nenhum sensor e invocado,
    # nem versao, nem login, nem modelos. Chave PAYG do proprio provedor
    # no ambiente bloqueia sem precisar de evidencia de login.
    if not provider_spec.sondas_automaticas:
        if env_relacionadas:
            return relatorio("BLOCKED", env_relacionadas)
        # Campos de evidencia ficam NAO observados (revisao P1-A.3):
        # com zero sondas, plano e origem declarados NAO podem parecer
        # prova de login no relatorio.
        return relatorio(provider_spec.teto_resultado, [],
                         origem_credencial="nao-sondada")

    # (c)+(d) deteccao, versao e login via sensor de execucao.
    adaptador = AdaptadorPreflight(provider_spec,
                                   sensor_exec=sens["exec"],
                                   sensor_modelos=sens["modelos"],
                                   env=ambiente)
    try:
        versao = adaptador.detectar_versao()
    except CliIndisponivel as exc:
        return relatorio("BLOCKED", env_relacionadas + [exc])

    try:
        login = adaptador.consultar_login()
    except CliIndisponivel as exc:
        # Revisao P1-A.3 (MINOR): falha de execucao NA SONDA DE LOGIN
        # tambem e BLOCKED tipado — nunca excecao propagada.
        return relatorio("BLOCKED", env_relacionadas + [exc],
                         versao=versao)
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
    # Portao de plano (emenda P1-A.3, item 1): plano nao observavel no CLI
    # deixa de ser bloqueio automatico SOMENTE quando ha (i) OAuth
    # observado (login ativo, origem conforme — verificado acima) e
    # (ii) tier declarado pelo proprietario, valido por no maximo 24 h.
    # O resultado e SHADOW_ELIGIBLE — nunca ELIGIBLE, nunca P2, nunca
    # execucao autonoma. Sem declaracao valida, o bloqueio estatico
    # original permanece.
    sombra = None
    if login["logado"] and login["plano"] is not None \
            and not plano_reconhecido(
                login["plano"], provider_spec.planos_aceitos):
        # Plano OBSERVADO e incompativel: bloqueio DIRETO (revisao
        # P1-A.3) — evidencia observada divergente tem precedencia sobre
        # a declarada; a trilha sombra NAO existe contra ela.
        erros.append(PlanoNaoReconhecido(
            detalhe=f"plano observado {login['plano']!r} fora de "
                    f"{list(provider_spec.planos_aceitos)}"))
    elif login["logado"] and login["plano"] is None:
        # Plano NAO observavel no CLI (o bloqueio factual da P1-A.2):
        # a trilha sombra da emenda 1 se aplica.
        decl = (tiers_declarados or {}).get(provider_spec.provider_id)
        # Revalidacao no portao (revisao P1-A.3, MAJOR): mesmo uma
        # DeclaracaoTier construida SEM passar por carregar_declaracoes
        # precisa ser do proprio provider, ter tier nao vazio e ser
        # declarada pelo PROPRIETARIO.
        decl_legitima = decl is not None \
            and decl.provider_id == provider_spec.provider_id \
            and isinstance(decl.tier, str) and bool(decl.tier.strip()) \
            and isinstance(decl.declarado_por, str) \
            and decl.declarado_por.strip().lower() == "proprietario"
        if not decl_legitima:
            erros.append(PlanoNaoReconhecido(
                detalhe="plano nao observavel no CLI e sem declaracao "
                        "de tier do proprietario"))
        elif not declaracao_valida(decl, agora):
            erros.append(DeclaracaoExpirada(
                detalhe=f"declaracao de tier {decl.tier!r} "
                        f"({decl.declarado_em_utc}) ilegivel, futura ou "
                        "fora da validade maxima de 24 h"))
        elif not plano_reconhecido(decl.tier, provider_spec.planos_aceitos):
            # Revisao P1-A.3 (MAJOR): o tier declarado precisa ser um dos
            # planos aceitos do provedor — uma declaracao "free" ou
            # arbitraria NAO satisfaz o portao comercial.
            erros.append(PlanoNaoReconhecido(
                detalhe=f"tier declarado {decl.tier!r} incompativel com "
                        f"os planos aceitos "
                        f"{list(provider_spec.planos_aceitos)}"))
        else:
            sombra = {"tier_declarado": decl.tier,
                      "declarado_por": decl.declarado_por,
                      "declarado_em_utc": decl.declarado_em_utc,
                      "expira_em_utc": expira_em(decl).strftime(
                          "%Y-%m-%dT%H:%M:%SZ"),
                      "autorizacao": "somente observacao-sombra de "
                                     "diagnostico; NAO autoriza P2 nem "
                                     "execucao autonoma"}
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

    # (d) descoberta de modelos — somente com economia/auth verdes, e
    # somente quando a especificacao declara um comando de descoberta
    # (emenda P1-A.3, item 4: claude nao tem fonte oficial nao interativa
    # — sem sonda de modelos, teto SUPERVISED).
    # O payload `sombra` NAO acompanha relatorios BLOCKED (revisao
    # P1-A.3): autorizacao-sombra so existe no resultado SHADOW_ELIGIBLE.
    modelos = []
    if provider_spec.comandos.get("modelos") is not None:
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
                                 detalhe="descoberta sem nenhum modelo "
                                         "esperado "
                                         f"{list(provider_spec.modelos_esperados)}"
                                         f"; encontrados: {modelos}")],
                             versao=versao, plano=login["plano"],
                             origem_credencial=login["origem_credencial"],
                             quota=login["quota"], modelos=modelos)

    # (e) classificacao: google/grok/claude tem teto SUPERVISED pela
    # especificacao. A trilha sombra NUNCA sobe o teto: SHADOW_ELIGIBLE
    # somente onde o teto e ELIGIBLE — e o payload `sombra` so existe
    # nesse resultado (nunca em SUPERVISED nem BLOCKED).
    resultado = provider_spec.teto_resultado
    if sombra is not None and resultado == "ELIGIBLE":
        resultado = "SHADOW_ELIGIBLE"
    return relatorio(resultado, [],
                     versao=versao, plano=login["plano"],
                     origem_credencial=login["origem_credencial"],
                     quota=login["quota"], modelos=modelos,
                     sombra=sombra if resultado == "SHADOW_ELIGIBLE"
                     else None)
