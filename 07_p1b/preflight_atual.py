"""Preflight ATUAL da frota real — SSC+ P1-B (experimental, sem autoridade).

Executa o pipeline de preflight da P1-A (`06_p1a/preflight`) contra os 5
CLIs de assinatura DESTA estacao, AGORA, e persiste o relatorio em JSON.
Somente sondas de DIAGNOSTICO (versao/login/modelos): NENHUMA chamada de
modelo e feita; custo variavel = 0 por construcao (billing subscription).

Portoes herdados da P1-A/P1-A.1 (nao reimplementados aqui):
- toda sonda passa por `sensor_subprocess` com `ambiente_sanitizado`
  (credenciais PAYG nunca entram no subprocesso);
- violacao economica/auth bloqueia ANTES de qualquer sonda de modelo;
- google e grok tem teto SUPERVISED; ausencia de evidencia = unknown.

Escritor unico: antes de escrever a evidencia, este script VERIFICA o
lease `locks/p1b-ops.lease` (sessao p1b-ops viva e nao expirada). O lock
e detido pelo processo titular da sessao P1-B; se o lease estiver morto,
o script aborta SEM escrever (parada: lock perdido).

Redacao: o nome do usuario local nunca persiste — caminhos do home sao
gravados como <USUARIO>. Nenhum valor de config persistida e gravado:
`auditar_config` recebe o dict parseado em memoria e reporta somente
NOMES de campos violadores.
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

from preflight.adaptadores import sensor_subprocess  # noqa: E402
from preflight.economia import ambiente_sanitizado, auditar_ambiente  # noqa: E402
from preflight.frota_real import frota_real  # noqa: E402
from preflight.pipeline import executar_preflight  # noqa: E402

_GITBASH = r"E:\LucasIA\Git\bin\bash.exe"
_USUARIO = os.path.basename(os.path.expanduser("~"))
_SESSAO_LOCK = "p1b-ops"
# CLIs npm sem executavel Windows direto: a sonda vai pelo Git Bash.
_VIA_GITBASH = ("google", "grok")


def _redigir(texto: str) -> str:
    return texto.replace(_USUARIO, "<USUARIO>")


def _verificar_lock_vivo() -> dict:
    """Le o lease da sessao P1-B; aborta se ausente/expirado/outra sessao."""
    from escritor import EscritorP1
    caminho = os.path.join(_RAIZ, "locks", f"{_SESSAO_LOCK}.lease")
    try:
        with open(caminho, encoding="utf-8") as f:
            lease = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(
            f"PARADA: lease do escritor unico ilegivel/ausente: {exc}")
    if lease.get("sessao") != _SESSAO_LOCK:
        raise SystemExit(
            f"PARADA: lease de outra sessao: {lease.get('sessao')!r}")
    if EscritorP1.lease_expirado(caminho):
        raise SystemExit("PARADA: lease do escritor unico EXPIRADO")
    with open(os.path.join(_RAIZ, "locks", f"{_SESSAO_LOCK}.fence"),
              encoding="ascii") as f:
        fence = int(f.read().strip())
    return {"sessao": lease["sessao"], "pid_titular": lease["pid"],
            "fence": fence, "expira_em": lease["expira_em"]}


def _sensor_de(provider_id: str):
    """Sensor real; google/grok (npm) rodam via Git Bash na estacao."""
    if provider_id not in _VIA_GITBASH:
        return sensor_subprocess

    def sensor_gitbash(argv, env=None, timeout=120):
        comando = shlex.join([os.path.expanduser(str(a)) for a in argv])
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
    """Config/auth persistida do provedor, parseada em MEMORIA (nunca
    gravada). Fontes: as mesmas auditadas na coleta P1-A (20_configs.txt).
    """
    if provider_id == "codex":
        # Escopo ratificado pela auditoria P1-A (02_auditoria-economica §2):
        # auth_mode + OPENAI_API_KEY (a chave que substituiria o OAuth).
        # tokens.access_token/refresh_token/id_token SAO a propria
        # credencial OAuth chatgpt — nao sao chave de API e ficam FORA da
        # auditoria de config (alimenta-los seria falso positivo).
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
    lock = _verificar_lock_vivo()
    agora = datetime.now(timezone.utc)
    viol_ambiente = auditar_ambiente(dict(os.environ))
    relatorios = []
    for espec in frota_real():
        rel = executar_preflight(
            espec, sensores=_sensor_de(espec.provider_id),
            env=dict(os.environ),
            config_persistida=_config_persistida(espec.provider_id))
        relatorios.append(rel.to_dict())

    documento = {
        "tipo": "preflight-atual-p1b",
        "gerado_em_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lock_escritor_unico": lock,
        "custo_variavel": 0,
        "chamadas_de_modelo": 0,
        "nota": "somente sondas de diagnostico (versao/login/modelos); "
                "nenhuma invocacao de modelo; env das sondas sanitizado "
                "pela canonica preflight.economia.ambiente_sanitizado",
        "violacoes_ambiente_nomes": sorted(
            {v.alvo for v in viol_ambiente if v.alvo}),
        "env_sanitizado_remove_nomes": sorted(
            set(os.environ) - set(ambiente_sanitizado())),
        "frota": relatorios,
    }
    texto = _redigir(json.dumps(documento, indent=2, ensure_ascii=False,
                                default=str))
    dir_saida = os.path.join(_RAIZ, "07_p1b", "evidencias")
    os.makedirs(dir_saida, exist_ok=True)
    nome = f"preflight-{agora.strftime('%Y%m%dT%H%M%SZ')}.json"
    caminho = os.path.join(dir_saida, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto + "\n")
        f.flush()
        os.fsync(f.fileno())

    print(f"evidencia: 07_p1b/evidencias/{nome}")
    for rel in relatorios:
        erros = ",".join(e["codigo"] for e in rel["erros"]) or "-"
        print(f"  {rel['provider_id']:7s} {rel['resultado']:10s} "
              f"plano={rel['plano'] or '-'} quota={rel['quota']} "
              f"modelos={len(rel['modelos'])} erros={erros}")
    elegiveis = [r["provider_id"] for r in relatorios
                 if r["resultado"] == "ELIGIBLE"]
    print(f"ELIGIBLE: {elegiveis}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
