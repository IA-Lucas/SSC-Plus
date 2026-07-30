"""Preflight DIAGNOSTICO real dentro da capsula — SSC+ P1-A.2 (experimental).

Executar SOMENTE via entry point da capsula:

    python 06_p1a/capsula.py python 06_p1a/preflight_capsula.py

O entry point (`capsula.iniciar_em_capsula`) cria o ambiente-filho sem
nenhuma credencial de modelo ANTES deste processo existir; a primeira
linha util deste script (`exigir_capsula_limpa`) ABORTA se qualquer
credencial estiver visivel — politica estrita da P1-A.2: chave visivel
dentro da capsula = bloqueio. O ambiente global/HKCU do usuario nunca e
lido, alterado ou persistido.

Somente sondas oficiais de DIAGNOSTICO (versao/login/model-list): ZERO
prompt, ZERO geracao, custo variavel = 0 (billing subscription). Cada
sonda recebe nova copia sanitizada do ambiente (defesa em profundidade
sobre a capsula), via `sensor_subprocess` da P1-A. Nenhuma saida bruta de
CLI e persistida — apenas os campos parseados do RelatorioPreflight.

Evidencia: `06_p1a/evidencias/p1a2-preflight-<UTC>.json`, com o nome do
usuario local redigido (`<USUARIO>`). Escritor unico: o lease da sessao
operacional e verificado antes da escrita.
"""

import json
import os
import shlex
import sys
import tomllib
from datetime import datetime, timezone

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, "05_p0"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))

from capsula import exigir_capsula_limpa, verificar_capsula  # noqa: E402
from preflight.adaptadores import sensor_subprocess  # noqa: E402
from preflight.economia import ambiente_sanitizado, auditar_ambiente  # noqa: E402
from preflight.frota_real import frota_real  # noqa: E402
from preflight.pipeline import executar_preflight  # noqa: E402

_GITBASH = r"E:\LucasIA\Git\bin\bash.exe"
_USUARIO = os.path.basename(os.path.expanduser("~"))
_SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a2-ops")
_VIA_GITBASH = ("google", "grok")  # CLIs npm sem executavel Windows direto


def _verificar_lock_vivo() -> dict:
    from escritor import EscritorP1
    caminho = os.path.join(_RAIZ, "locks", f"{_SESSAO_LOCK}.lease")
    try:
        with open(caminho, encoding="utf-8") as f:
            lease = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: lease ilegivel/ausente: {exc}")
    if lease.get("sessao") != _SESSAO_LOCK or \
            EscritorP1.lease_expirado(caminho):
        raise SystemExit("PARADA: lease da sessao operacional morto")
    with open(os.path.join(_RAIZ, "locks", f"{_SESSAO_LOCK}.fence"),
              encoding="ascii") as f:
        fence = int(f.read().strip())
    return {"sessao": lease["sessao"], "fence": fence}


def _sensor_de(provider_id: str):
    if provider_id not in _VIA_GITBASH:
        return sensor_subprocess

    def sensor_gitbash(argv, env=None, timeout=60):
        comando = shlex.join([str(a) for a in argv])
        return sensor_subprocess([_GITBASH, "-lc", comando], env=env,
                                 timeout=timeout)
    return sensor_gitbash


def _ler_json(caminho: str) -> dict:
    try:
        with open(os.path.expanduser(caminho), encoding="utf-8") as f:
            dado = json.load(f)
        return dado if isinstance(dado, dict) else {}
    except (OSError, ValueError):
        return {}


def _ler_toml(caminho: str) -> dict:
    try:
        with open(os.path.expanduser(caminho), "rb") as f:
            return tomllib.load(f)
    except (OSError, ValueError):
        return {}


def _config_persistida(provider_id: str) -> dict:
    """Config/auth persistida, parseada em MEMORIA (valores nunca gravados).
    Codex: somente auth_mode + OPENAI_API_KEY + config.toml — os campos
    tokens.* SAO a propria credencial OAuth, nao chave de API (escopo
    ratificado na auditoria P1-A, 02_auditoria-economica §2).
    """
    if provider_id == "codex":
        auth = _ler_json("~/.codex/auth.json")
        cfg = {k: auth[k] for k in ("auth_mode", "OPENAI_API_KEY")
               if k in auth}
        cfg.update(_ler_toml("~/.codex/config.toml"))
        return cfg
    if provider_id == "claude":
        return _ler_json("~/.claude/settings.json")
    if provider_id == "kimi":
        return _ler_toml("~/.kimi-code/config.toml")
    if provider_id == "google":
        return _ler_json("~/.gemini/settings.json")
    return {}  # grok: nenhuma config parseavel localizada na P1-A


def main() -> int:
    exigir_capsula_limpa()  # politica estrita: chave visivel = aborta
    lock = _verificar_lock_vivo()
    agora = datetime.now(timezone.utc)
    relatorios = []
    for espec in frota_real():
        if espec.provider_id in _VIA_GITBASH:
            # google/grok: SUPERVISED por regra da missao e NAO necessarios.
            # Sondas reais via Git Bash penduram (netos node/npm seguram o
            # pipe e o timeout do subprocess nao mata a arvore) — observado
            # em duas corridas abortadas. Classificacao estatica, sem sonda.
            relatorios.append({
                "provider_id": espec.provider_id,
                "resultado": "SUPERVISED",
                "caminho": espec.executavel, "versao": None,
                "plano": espec.plano_esperado,
                "origem_credencial": espec.auth_esperada,
                "quota": "desconhecida", "modelos": [],
                "erros": [],
                "nota": "SUPERVISED por regra da missao; sonda real nao "
                        "necessaria (provedor nao usado na frota)"})
            continue
        rel = executar_preflight(
            espec, sensores=_sensor_de(espec.provider_id),
            env=dict(os.environ),
            config_persistida=_config_persistida(espec.provider_id))
        relatorios.append(rel.to_dict())

    documento = {
        "tipo": "preflight-diagnostico-p1a2-capsula",
        "gerado_em_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "capsula": {
            "violacoes_no_env_do_processo": verificar_capsula(
                dict(os.environ)),
            "politica": "subscription-only; qualquer credencial de modelo "
                        "visivel dentro da capsula = bloqueio",
        },
        "lock_escritor_unico": lock,
        "custo_variavel": 0,
        "chamadas_de_modelo": 0,
        "nota": "somente sondas oficiais de diagnostico "
                "(version/login/model-list); zero prompt/geracao; sondas "
                "receberam nova copia sanitizada do env da capsula",
        "violacoes_ambiente_nomes": sorted(
            {v.alvo for v in auditar_ambiente(dict(os.environ)) if v.alvo}),
        "env_sanitizado_remove_nomes": sorted(
            set(os.environ) - set(ambiente_sanitizado())),
        "frota": relatorios,
    }
    texto = json.dumps(documento, indent=2, ensure_ascii=False,
                       default=str).replace(_USUARIO, "<USUARIO>")
    dir_saida = os.path.join(_RAIZ, "06_p1a", "evidencias")
    os.makedirs(dir_saida, exist_ok=True)
    nome = f"p1a2-preflight-{agora.strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(os.path.join(dir_saida, nome), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
        f.flush()
        os.fsync(f.fileno())

    print(f"evidencia: 06_p1a/evidencias/{nome}")
    for rel in relatorios:
        erros = ",".join(e["codigo"] for e in rel["erros"]) or "-"
        print(f"  {rel['provider_id']:7s} {rel['resultado']:10s} "
              f"plano={rel['plano'] or '-'} quota={rel['quota']} "
              f"modelos={len(rel['modelos'])} erros={erros}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
