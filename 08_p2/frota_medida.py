"""Ponte preflight -> frota: a FleetEntry sai do que foi OBSERVADO.

CONSUMIDOR DECLARADO do veredito (`06_p1a/tests/sentinela_antip2.py`,
`CONSUMIDORES_DECLARADOS`), autorizado pelo ato soberano de 2026-08-03.
Este e o unico lugar da P2 onde duas provas independentes se encontram:
a classificacao tecnica do preflight e um ato operacional de P2. Nenhuma
das duas, isoladamente, vira rota. O modulo nao executa nada: devolve
entradas e descartes, e quem invoca e outro modulo.

A diferenca entre este modulo e `frota.frota_inicial()`, que a P0 usava:
la os cinco provedores nasciam com `model_id` ESCRITO NO FONTE
(`gpt-5-codex`, `kimi-k2`), plano presumido e canal presumido. Aqui cada
campo tem procedencia declarada, e a regra de D5 — *"model_id descoberto,
nunca presumido"* — passa a ser exercida em vez de citada: relatorio sem
modelo observado NAO vira entrada, ele vira descarte com motivo.

NADA SOME. Provedor que nao habilita, que nao tem modelo, ou que o portao
economico veta sai em `descartes`/`vetos`, com o motivo por escrito. Um
relatorio que so listasse os aprovados esconderia exatamente a informacao
que o operador precisa para entender por que a frota esta vazia.

O QUE E OBSERVADO E O QUE E DECLARADO, sem confundir os dois:

| campo | procedencia |
|---|---|
| `model_id` | **observado** (`codex doctor`, config Claude, `kimi provider list`, `agy models`) |
| `auth_mode`, `canal_oficial` | **observado** (`origem_credencial`) |
| `quota_state` | **observado** (texto do CLI; `desconhecida` e o normal) |
| `billing_mode`, `variable_cost` | **declarado** na especificacao estatica |
| `capability_profile`, `papeis_preferidos` | **preferencia** declarada no adendo 09 |
"""

import caminhos  # noqa: F401  (insere 05_p0/06_p1a/08_p2 no sys.path)

from ssc_p0 import contratos as ct
from ssc_p0.frota import (verificar_automacao, verificar_canal,
                          verificar_economia)

# Estes resultados sao tecnicamente admissiveis, mas NAO sao autorizacao de
# P2. Em particular, o payload de SHADOW_ELIGIBLE diz literalmente que ele
# nao autoriza P2. A autorizacao operacional independente e conferida logo
# abaixo. Manter os conceitos separados fecha a divergencia entre o contrato
# da trilha sombra e o antigo nome `RESULTADOS_QUE_HABILITAM`.
RESULTADOS_TECNICAMENTE_ADMISSIVEIS = ("ELIGIBLE", "SHADOW_ELIGIBLE")

# Atos operacionais que autorizam o consumidor supervisionado. A declaracao
# de tier nunca aparece como fonte: ela so produz evidencia tecnica sombra.
# Codex/Kimi foram abertos pelo ato de 03/08; Claude/Google, pela confirmacao
# operacional registrada em 11/08. Grok continua deliberadamente ausente.
AUTORIZACAO_OPERACIONAL_P2 = {
    "id": "SSC-P2-SUPERVISIONADA-20260811",
    "modo": "supervised",
    "provedores": {
        "codex": "08_p2/00_ato-soberano-p2.md",
        "kimi": "08_p2/00_ato-soberano-p2.md",
        "claude": "08_p2/100_ativacao-claude-google-20260811.md",
        "google": "08_p2/100_ativacao-claude-google-20260811.md",
    },
}

# Origens de credencial que comprovam canal de assinatura. Qualquer outra
# — inclusive `nao-sondada` e `ausente` — vira `desconhecido`, que o
# portao economico ratificado NEGA (`auth_mode desconhecido = DENY`).
_AUTH_POR_ORIGEM = {
    "subscription-oauth": "subscription-oauth",
    "cached-token": "cached-token",
    "acp": "acp",
}

# Automacao: a P2 opera SUPERVISED por ato soberano. Especificacao que
# nao declare um dos dois modos conhecidos vira `deny` — fail-closed.
_AUTOMACAO_POR_ESPEC = {
    "allow-supervised": "supervised",
    "supervised-only": "supervised",
}

# PREFERENCIAS do adendo 09 §1 — nunca papel fixo, nunca capacidade
# observada. Servem ao `Frota.escolher(capacidade=...)`; a frase do adendo
# e "perfil inicial (PREFERENCIA, nao papel fixo)".
CAPACIDADES_PREFERIDAS = {
    "codex": ["implementacao", "operacao-repo"],
    "claude": ["arquitetura", "specs", "revisao-profunda"],
    "kimi": ["engenharia-reversa", "contexto-extenso", "volume"],
    "google": ["multimodal", "julgamento-transversal"],
    "grok": ["pesquisa-atual", "x-web", "red-team", "coding-alternativo"],
}


def _quota_do_relatorio(quota) -> str:
    """Franquia observada -> enum de contrato, sem inventar disponibilidade.

    `desconhecida` e o valor NORMAL nesta frota: nenhuma corrida de
    preflight ate hoje observou franquia em nenhum dos cinco. Converte-la
    em `disponivel` por ausencia de sinal negativo seria o fail-open que a
    P1-A.3.2 fechou no detector.
    """
    return quota if quota in ct.QUOTA_STATES else "desconhecida"


def entradas_de(relatorio: dict, espec, autorizacao_p2: dict | None) -> tuple:
    """(entradas, descartes) de UM relatorio de preflight.

    Uma entrada por modelo OBSERVADO: `Frota` e indexada por
    provedor+modelo, e um provedor que exponha dois modelos e duas rotas
    possiveis, nao uma escolha a ser feita aqui.
    """
    pid = relatorio.get("provider_id")
    resultado = relatorio.get("resultado")
    if resultado not in RESULTADOS_TECNICAMENTE_ADMISSIVEIS:
        return ([], [{"provider_id": pid, "motivo":
                      f"preflight tecnicamente inadmissivel: {resultado}"}])

    fontes = ((autorizacao_p2 or {}).get("provedores") or {})
    fonte_ato = fontes.get(pid)
    modo_autorizado = (autorizacao_p2 or {}).get("modo")
    if not isinstance(fonte_ato, str) or not fonte_ato \
            or modo_autorizado != "supervised":
        return ([], [{"provider_id": pid,
                      "motivo": "sem autorizacao operacional P2 "
                                "independente do preflight"}])

    modelos = list(relatorio.get("modelos") or [])
    if not modelos:
        # D5: "model_id descoberto, nunca presumido". Sem modelo observado
        # nao ha o que rotear — e preencher com o esperado da
        # especificacao seria presumir exatamente o que a regra proibe.
        return ([], [{"provider_id": pid,
                      "motivo": f"veredito {resultado} sem modelo observado; "
                                "model_id nunca e presumido"}])

    origem = relatorio.get("origem_credencial")
    auth = _AUTH_POR_ORIGEM.get(origem, "desconhecido")
    canal_provado = auth != "desconhecido"
    # `terms_profile` sem `oauth_profile` faz `AdaptadorAssinatura` recusar
    # a invocacao mesmo que tudo o mais passe — a regra do adendo §4:
    # chave de API nunca substitui OAuth.
    terms = {"origem_credencial_observada": origem,
             "plano_observado": relatorio.get("plano"),
             # `tier_declarado` e a chave que o pipeline emite (medida na
             # evidencia real `preflight-20260801T235521Z.json`, nao
             # suposta pelo nome do campo da dataclass).
             "tier_declarado": (relatorio.get("sombra") or {}).get(
                 "tier_declarado"),
             "veredito_preflight": resultado,
             "autorizacao_p2_id": autorizacao_p2.get("id"),
             "autorizacao_p2_fonte": fonte_ato,
             "autorizacao_p2_modo": modo_autorizado}
    if canal_provado:
        terms["oauth_profile"] = f"oauth:{pid}"

    entradas = []
    for model_id in modelos:
        entradas.append(ct.FleetEntry(
            provider_id=pid,
            model_id=model_id,
            capability_profile={"capacidades":
                                list(CAPACIDADES_PREFERIDAS.get(pid, []))},
            auth_mode=auth,
            billing_mode=espec.billing_mode,
            quota_state=_quota_do_relatorio(relatorio.get("quota")),
            quota_reset=None,          # nenhuma corrida observou reset
            automation_permission=_AUTOMACAO_POR_ESPEC.get(
                espec.automacao, "deny"),
            terms_profile=dict(terms),
            variable_cost=espec.variable_cost,
            papeis_preferidos=["autor", "revisor", "juiz"],
            canal_oficial=canal_provado,
        ).validado())
    return (entradas, [])


def frota_do_preflight(relatorios, especs: dict,
                       modo_execucao: str = "supervised",
                       autorizacao_p2: dict | None = None) -> dict:
    """A frota admitida por preflight E ato, com tudo que ficou de fora.

    Devolve `{"entradas": [...], "descartes": [...], "vetos": [...]}`.

    `vetos` NAO e decisao deste modulo: e a resposta dos portoes
    ratificados da P0 (`verificar_economia`, `verificar_canal`,
    `verificar_automacao`) sobre cada entrada construida, registrada para
    que o operador leia o motivo. A entrada vetada CONTINUA na lista — quem
    a exclui da escolha e `Frota.elegiveis`, no lugar de sempre. Filtra-la
    aqui criaria um segundo portao economico, e dois portoes que precisam
    concordar sao dois portoes que um dia divergem.
    """
    entradas, descartes, vetos = [], [], []
    for relatorio in relatorios:
        pid = relatorio.get("provider_id")
        espec = especs.get(pid)
        if espec is None:
            descartes.append({"provider_id": pid,
                              "motivo": "sem especificacao estatica"})
            continue
        novas, recusadas = entradas_de(relatorio, espec, autorizacao_p2)
        entradas.extend(novas)
        descartes.extend(recusadas)

    for entrada in entradas:
        motivos = (verificar_economia(entrada) + verificar_canal(entrada)
                   + verificar_automacao(entrada, modo_execucao))
        if motivos:
            vetos.append({"provider_id": entrada.provider_id,
                          "model_id": entrada.model_id,
                          "motivos": motivos})
    return {"entradas": entradas, "descartes": descartes, "vetos": vetos}
