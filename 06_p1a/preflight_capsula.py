"""Preflight DIAGNOSTICO real dentro da capsula — SSC+ P1-A.3 (experimental).

Executar SOMENTE via entry point da capsula:

    python 06_p1a/capsula.py python 06_p1a/preflight_capsula.py

O entry point (`capsula.iniciar_em_capsula`) cria o ambiente-filho sem
nenhuma credencial de modelo ANTES deste processo existir; a primeira
linha util deste script (`exigir_capsula_limpa`) ABORTA se qualquer
credencial estiver visivel — politica estrita da P1-A.2: chave visivel
dentro da capsula = bloqueio. O ambiente global/HKCU do usuario nunca e
lido, alterado ou persistido.

Emendas P1-A.3 aplicadas (decisao soberana sobre a P1-A.2):
- item 1: tiers declarados pelo proprietario (`tiers_declarados.json`,
  validade maxima 24 h) + OAuth observado => SOMENTE SHADOW_ELIGIBLE;
- item 2: descoberta codex via `codex doctor` (modelo efetivo + auth
  mode; NAO catalogo completo);
- item 3: `kimi provider list` comprova OAuth e modelo efetivo, nao o
  plano comercial (cai na trilha sombra do item 1);
- item 4: claude SUPERVISED, sem sonda de modelos (sem fonte oficial
  nao interativa);
- item 5: google/grok SUPERVISED estaticos, ZERO sondas automaticas.

Somente sondas oficiais de DIAGNOSTICO (versao/login/model-list/doctor):
ZERO prompt, ZERO geracao, custo variavel = 0 (billing subscription).
Cada sonda recebe nova copia sanitizada do ambiente (defesa em
profundidade sobre a capsula), via `sensor_subprocess` da P1-A. Nenhuma
saida bruta de CLI e persistida — apenas os campos parseados do
RelatorioPreflight.

Evidencia: `06_p1a/evidencias/p1a3-preflight-<UTC>.json`, com o nome do
usuario local redigido (`<USUARIO>`). Escritor unico: o lease da sessao
operacional e verificado antes da escrita.
"""

import json
import os
import shlex
import sys
from datetime import datetime, timezone

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, "05_p0"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a", "evidencias"))

import leitor_tiers  # noqa: E402
import leitores_config  # noqa: E402
from capsula import exigir_capsula_limpa, verificar_capsula  # noqa: E402
from preflight.adaptadores import sensor_subprocess  # noqa: E402
from preflight.economia import ambiente_sanitizado, auditar_ambiente  # noqa: E402
from preflight.frota_real import frota_real  # noqa: E402
from preflight.pipeline import executar_preflight  # noqa: E402

_GITBASH = r"E:\LucasIA\Git\bin\bash.exe"
_SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a3-ops")
_VIA_GITBASH = ("google", "grok")  # CLIs npm sem executavel Windows direto

# Leitor de tiers: implementacao UNICA em `leitor_tiers`, partilhada com
# o runner da P1-B. Estava aqui dentro, e a ordem 4 da P1-B.01 ia
# duplica-la do outro lado — o mecanismo dos achados 7, 10 e 14 (a copia
# que ninguem exercita fica para tras). Mesmo desenho que
# `leitores_config` recebeu na correcao 7 da P1-A.3.5.
_carregar_tiers = leitor_tiers.carregar_tiers


def _verificar_lock_vivo(fence_esperado: int | None = None,
                         raiz: str | None = None) -> dict:
    """Lease vivo + fence do titular do escritor unico.

    Revisao P1-A.3.1, MAJOR #4: chamar IMEDIATAMENTE ANTES DE CADA
    PERSISTENCIA, nao apenas na abertura do trabalho. Entre a abertura e
    a gravacao correm as sondas reais dos CLIs, que podem exceder a
    janela do lease (120 s na operacao) — verificar so no inicio permite
    gravar com lease ja expirado.

    Com `fence_esperado`, exige tambem que o titular NAO tenha sido
    substituido: fence diferente significa que outra sessao adquiriu o
    escritor no intervalo, e esta gravacao seria escrita de escritor
    obsoleto. Fail-closed nos dois casos: PARADA antes de escrever.
    """
    from escritor import EscritorP1
    base = os.path.join(raiz or _RAIZ, "locks")
    caminho = os.path.join(base, f"{_SESSAO_LOCK}.lease")
    try:
        with open(caminho, encoding="utf-8") as f:
            lease = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: lease ilegivel/ausente: {exc}")
    if lease.get("sessao") != _SESSAO_LOCK or \
            EscritorP1.lease_expirado(caminho):
        raise SystemExit("PARADA: lease da sessao operacional morto")
    try:
        with open(os.path.join(base, f"{_SESSAO_LOCK}.fence"),
                  encoding="ascii") as f:
            fence = int(f.read().strip())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: fence ilegivel/ausente: {exc}")
    if fence_esperado is not None and fence != fence_esperado:
        raise SystemExit(
            f"PARADA: titular do escritor substituido (fence {fence} != "
            f"{fence_esperado}); escritor obsoleto NAO grava")
    return {"sessao": lease["sessao"], "fence": fence}


def _sensor_de(provider_id: str):
    if provider_id not in _VIA_GITBASH:
        return sensor_subprocess

    def sensor_gitbash(argv, env=None, timeout=60):
        comando = shlex.join([str(a) for a in argv])
        return sensor_subprocess([_GITBASH, "-lc", comando], env=env,
                                 timeout=timeout)
    return sensor_gitbash


# Leitores de config: implementacao UNICA em `leitores_config`, partilhada
# com o runner da P1-B. Ate a P1-A.3.5 havia duas copias, e as correcoes
# 1 e 3 desta missao alcancaram so esta — a copia da P1-B ficou com os
# dois defeitos que elas fecharam. O alias abaixo preserva o nome
# historico usado pelos testes e pelo binding padrao.
_config_persistida = leitores_config.config_persistida

def classificar_frota(env: dict, tiers: dict, config_de=None,
                      sensor_de=None) -> list:
    """Classifica a frota INTEIRA pelo pipeline — sem atalho por provedor.

    Revisao P1-A.3.1, MAJOR #1: o atalho manual de google/grok montava o
    relatorio SUPERVISED a mao, sem passar por `executar_preflight` nem
    por `_config_persistida`. Chave PAYG do provedor no ambiente,
    endpoint pago ou auto top-up persistido resultavam em SUPERVISED —
    os bloqueios economicos nao eram sequer consultados.

    A ZERO-sonda que motivava o atalho nao depende dele: e propriedade
    declarada na especificacao (`sondas_automaticas=False`) e o pipeline
    a respeita — classifica no teto sem invocar sensor algum, e por isso
    nao ha risco de as sondas via Git Bash pendurarem. O que o pipeline
    acrescenta e justamente o que faltava: auditoria de ambiente e de
    config ANTES do teto, com BLOCKED quando a economia e violada.

    `config_de`/`sensor_de` sao injetaveis SOMENTE para teste; em
    operacao valem os leitores reais.
    """
    ler_config = config_de or _config_persistida
    escolher_sensor = sensor_de or _sensor_de
    return [executar_preflight(
                espec, sensores=escolher_sensor(espec.provider_id),
                env=env,
                config_persistida=ler_config(espec.provider_id),
                tiers_declarados=tiers)
            for espec in frota_real()]


def main() -> int:
    exigir_capsula_limpa()  # politica estrita: chave visivel = aborta
    lock = _verificar_lock_vivo()
    tiers = _carregar_tiers()
    agora = datetime.now(timezone.utc)
    relatorios = [rel.to_dict()
                  for rel in classificar_frota(dict(os.environ), tiers)]

    # Revisao P1-A.3.1 (MAJOR #4): as sondas acima podem exceder a janela
    # do lease. O escritor e reverificado AQUI, imediatamente antes da
    # persistencia, e o fence precisa ser o MESMO da abertura — lease
    # morto ou titular substituido = PARADA sem gravar.
    lock_persistencia = _verificar_lock_vivo(fence_esperado=lock["fence"])

    documento = {
        "tipo": "preflight-diagnostico-p1a3-capsula",
        "gerado_em_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "emendas_p1a3": {
            "tiers_declarados": {pid: d.tier
                                 for pid, d in sorted(tiers.items())},
            "limite": "SHADOW_ELIGIBLE somente; validade maxima 24 h; "
                      "NAO autoriza P2 nem execucao autonoma",
        },
        "capsula": {
            "violacoes_no_env_do_processo": verificar_capsula(
                dict(os.environ)),
            "politica": "subscription-only; qualquer credencial de modelo "
                        "visivel dentro da capsula = bloqueio",
        },
        "lock_escritor_unico": lock_persistencia,
        "lock_verificado_antes_da_persistencia": True,
        "custo_variavel": 0,
        "chamadas_de_modelo": 0,
        "nota": "somente sondas oficiais de diagnostico "
                "(version/login/model-list/doctor); zero prompt/geracao; "
                "sondas receberam nova copia sanitizada do env da capsula",
        "violacoes_ambiente_nomes": sorted(
            {v.alvo for v in auditar_ambiente(dict(os.environ)) if v.alvo}),
        "env_sanitizado_remove_nomes": sorted(
            set(os.environ) - set(ambiente_sanitizado())),
        "frota": relatorios,
    }
    # ACHADO 10: esta redacao era uma das TRES mais fracas do acervo —
    # redigia so a forma longa do usuario e deixava passar a forma 8.3,
    # que e justamente a que `ZeroPiiNosArtefatos` procura. Passa a usar
    # a redacao CANONICA, que cobre tambem o prefixo de caminho local
    # (este proprio arquivo carrega um em `_GITBASH`).
    from contencao import redigir
    texto = redigir(json.dumps(documento, indent=2, ensure_ascii=False,
                               default=str))
    dir_saida = os.path.join(_RAIZ, "06_p1a", "evidencias")
    os.makedirs(dir_saida, exist_ok=True)
    nome = f"p1a3-preflight-{agora.strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(os.path.join(dir_saida, nome), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
        f.flush()
        os.fsync(f.fileno())

    print(f"evidencia: 06_p1a/evidencias/{nome}")
    for rel in relatorios:
        erros = ",".join(e["codigo"] for e in rel["erros"]) or "-"
        sombra = f" sombra={rel['sombra']['tier_declarado']}" \
            if rel.get("sombra") else ""
        print(f"  {rel['provider_id']:7s} {rel['resultado']:15s} "
              f"plano={rel['plano'] or '-'} quota={rel['quota']} "
              f"modelos={len(rel['modelos'])} erros={erros}{sombra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
