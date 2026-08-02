#!/usr/bin/env python3
"""Revisao read-only da P1-A.3.6 por provider distinto — SSC+ (experimental).

Missao probatoria: submeter o ESTADO CORRIGIDO acumulado ate `6a3a3f8` a
revisao independente. Quem corrigiu nao certifica — o fechamento de cada
um dos seis MAJOR depende de pronunciamento explicito do revisor.

O pacote NAO e montado aqui. Ele e gerado por `pacote_p1a36.py`
(deterministico; duas geracoes em diretorios INDEPENDENTES com bytes e
SHA-256 identicos, mais prova de ancoragem em checkout limpo e sob
mutacao deliberada da arvore) e os MESMOS BYTES sao copiados para o
descartavel de cada revisor — nenhuma reconstrucao entre revisores.
UMA chamada valida por provider, por assinatura, custo variavel zero.

Herda integralmente as correcoes ja ratificadas:
- MAJOR #3 (isolamento): codex com `--sandbox read-only --ephemeral`;
  kimi sem sandbox de filesystem no CLI — restricao parcial
  (`--skills-dir` vazio, sem `-y/--yolo/--auto`; sem `--plan`, que o CLI
  recusa junto de `-p`) mais DETECCAO INTEGRAL por manifesto SHA-256 da
  arvore antes/depois. Mutacao fora do descartavel REPROVA a corrida
  (returncode 3), nao apenas aparece.
- MAJOR #4 (lease): `verificar_lock` com fence esperado IMEDIATAMENTE
  antes da persistencia, e nao so na abertura — a chamada de provider
  excede a janela do lease (256 s observados contra 120 s).

O tier declarado precisa estar VALIDO no instante da chamada; expirado =
PARADA (somente o proprietario renova). Executa DENTRO da capsula: o
subprocesso recebe `capsula.ambiente_capsula()`; o ambiente global/HKCU
permanece intacto.

Uso: python 06_p1a/evidencias/revisao_p1a36.py codex|kimi <pacote.txt>
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a36"

sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       manifesto, mutacoes, redigir, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a36-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")


def _redigir(texto: str) -> str:
    """Redige usuario local e caminho local — delega a UNICA implementacao.

    ACHADO 10 da P1-A.3.5: havia nove copias desta redacao em tres
    forcas, nenhuma com teste. Copia local aqui reintroduziria o achado.
    """
    return redigir(texto)


COMANDOS = {
    "codex": lambda tmp, skills, prompt: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral", prompt],
    "kimi": lambda tmp, skills, prompt: argv_kimi(_KIMI_EXE, prompt, skills),
}

ENFORCEMENT = {
    "codex": "--sandbox read-only --ephemeral (CLI)",
    "kimi": enforcement_kimi(),
}


def _modelo_efetivo(err: str) -> str:
    """Modelo efetivo quando o CLI o expoe no banner; senao, DESCONHECIDO.

    Registrar o que se observa, nunca o que se supoe: desconhecido
    permanece desconhecido.
    """
    m = re.search(r"^\s*model:\s*(\S+)", err or "", re.MULTILINE)
    return m.group(1) if m else "DESCONHECIDO (nao exposto pelo CLI)"


def _verificar_lock(fence_esperado: int | None = None) -> dict:
    return verificar_lock(RAIZ, SESSAO_LOCK, fence_esperado)


def _verificar_tier(provider: str) -> dict:
    """Tier declarado precisa estar valido NO INSTANTE da chamada."""
    dados = json.loads((RAIZ / "06_p1a" / "tiers_declarados.json")
                       .read_text(encoding="utf-8"))
    teto = float(dados["validade_maxima_horas"])
    agora = datetime.now(timezone.utc)
    for decl in dados["declaracoes"]:
        if decl["provider_id"] != provider:
            continue
        em = datetime.strptime(decl["declarado_em_utc"],
                               "%Y-%m-%dT%H:%M:%SZ").replace(
                                   tzinfo=timezone.utc)
        expira = em.timestamp() + min(float(decl["validade_horas"]),
                                      teto) * 3600
        if agora.timestamp() >= expira:
            expira_iso = datetime.fromtimestamp(
                expira, timezone.utc).isoformat()
            raise SystemExit(
                f"PARADA: tier declarado de {provider} EXPIRADO em "
                f"{expira_iso} — somente o proprietario renova")
        return {"provider_id": provider, "tier": decl["tier"],
                "declarado_por": decl["declarado_por"],
                "declarado_em_utc": decl["declarado_em_utc"],
                "expira_em_utc": datetime.fromtimestamp(
                    expira, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "valido_no_instante": True}
    raise SystemExit(f"PARADA: sem declaracao de tier para {provider}")


def montar_prompt() -> str:
    """Prompt curto (argv): o pacote e as perguntas vao no arquivo."""
    return (
        "Revise em modo SOMENTE LEITURA o pacote SSC+ P1-A.3.6. O pacote "
        "completo esta em ./pacote-revisao.txt no diretorio atual: "
        "leia-o POR INTEIRO antes de avaliar. Ele contem a identidade "
        "dos commits, o historico de revisao, as DECLARACOES "
        "OBRIGATORIAS, o diff, os arquivos completos, as suites, o "
        "threat review, os hashes de registros e evidencias e a secao "
        "'Perguntas de revisao' — siga aquela secao a risca, inclusive o "
        "formato de resposta. Voce NAO pode escrever nada: responda "
        "apenas com a revisao em texto.\n\n"
        "Contexto: a revisao da P1-A.3.1 REPROVOU este trabalho com SEIS "
        "MAJOR, e as duas tentativas de revisao seguintes nao produziram "
        "veredito nenhum. Este pacote e o estado DEPOIS das correcoes. "
        "Quem corrigiu nao certifica: e voce quem diz se cada MAJOR "
        "fechou. Uma correcao nao fecha por ter sido feita.\n\n"
        "Leia as 'Declaracoes obrigatorias' antes de julgar: sao quatro "
        "fatos que o autor do pacote e obrigado a lhe transmitir, dois "
        "deles contra o proprio interesse. Julgar 'escritor unico' sem a "
        "Declaracao 1 seria julgar contra premissa falsa.\n\n"
        "Sua resposta precisa conter, nesta ordem: as linhas PROVIDER, "
        "MODELO-OBSERVADO, CANAL, PACOTE-SHA256 (compute o SHA-256 de "
        "./pacote-revisao.txt) e ESCOPO; as SEIS linhas "
        "'MAJOR-<n>: FECHADO | NAO-FECHADO — <justificativa>'; a linha "
        "'DEFEITO-NOVO: SIM | NAO — <o que, onde>'; os achados, um por "
        "linha, prefixados por CRITICAL | MAJOR | MINOR | OBS com "
        "arquivo:tema e descricao curta (para cada MINOR, classifique "
        "bloqueante ou nao-bloqueante, com motivo; se nao houver achado "
        "num nivel, nao o invente); e a linha final "
        "'VEREDITO: APROVADO | APROVADO-COM-RESSALVAS | REPROVADO'.")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a36.py codex|kimi <pacote.txt>",
              file=sys.stderr)
        return 2
    provider = sys.argv[1]
    sys.stdout.reconfigure(errors="replace")
    lock = _verificar_lock()
    tier = _verificar_tier(provider)

    dados_pacote = Path(sys.argv[2]).read_bytes()
    pacote_sha256 = hashlib.sha256(dados_pacote).hexdigest()

    env = ambiente_capsula()
    removidas = sorted(set(os.environ) - set(env))
    tmp = tempfile.mkdtemp(prefix=f"p1a36-revisao-{provider}-")
    skills = tempfile.mkdtemp(prefix=f"p1a36-skills-vazio-{provider}-")
    # MESMOS BYTES para os dois revisores: copia verbatim, sem remontagem.
    with open(os.path.join(tmp, "pacote-revisao.txt"), "wb") as f:
        f.write(dados_pacote)
    prompt = montar_prompt()
    argv = COMANDOS[provider](tmp, skills, prompt)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    antes = manifesto(RAIZ)
    inicio = time.monotonic()
    try:
        proc = subprocess.run(
            argv, cwd=tmp, env=env, capture_output=True, text=True,
            timeout=1800, encoding="utf-8", errors="replace")
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, out = "TIMEOUT", (e.stdout or "")
        err = (e.stderr or "") + "\nTIMEOUT apos 1800s"
    duracao = round(time.monotonic() - inicio, 3)
    fora_do_descartavel = mutacoes(antes, manifesto(RAIZ))
    restantes = [str(p.relative_to(tmp)) for p in Path(tmp).rglob("*")
                 if p.is_file()]
    # MAJOR #4: lease reverificado AQUI, com o MESMO fence da abertura.
    lock = _verificar_lock(fence_esperado=lock["fence"])
    meta = {
        "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a36",
        "chamadas_de_modelo": 1, "custo_variavel": 0,
        "rotulo": "assinatura-oauth; UMA chamada; enforcement read-only",
        "enforcement_read_only": ENFORCEMENT[provider],
        "tier_declarado_no_instante": tier,
        "lock_escritor_unico": lock,
        "argv_publico": ["<PROMPT>" if a == prompt else a for a in argv],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "pacote_sha256": pacote_sha256,
        "pacote_bytes_entregues": len(dados_pacote),
        "dir_descartavel": _redigir(tmp),
        "dir_descartavel_arquivos_restantes": restantes,
        "contencao": {
            "medida": "manifesto SHA-256 da arvore inteira antes/depois",
            "arquivos_no_manifesto": len(antes),
            "excluido_e_declarado": ["locks"],
            "mutacoes_fora_do_descartavel": fora_do_descartavel,
            "violada": bool(fora_do_descartavel),
        },
        "lock_verificado_antes_da_persistencia": True,
        "env_vars_removidas_nomes": removidas,
        "returncode": rc, "duracao_s": duracao,
        "modelo_efetivo_no_banner": _modelo_efetivo(err),
        "resposta": _redigir((out or "").strip()),
        "stderr_resumo": _redigir((err or "").strip()[:2000]),
        "quota_observavel": "nao-exposta-pelo-cli",
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    texto = _redigir(json.dumps(meta, ensure_ascii=False, indent=2))
    (SAIDA / f"{provider}-{ts}.json").write_text(texto + "\n",
                                                 encoding="utf-8")
    print(json.dumps({"provider": provider, "returncode": rc,
                      "duracao_s": duracao,
                      "pacote_sha256": pacote_sha256,
                      "modelo_efetivo": meta["modelo_efetivo_no_banner"],
                      "contencao_violada": bool(fora_do_descartavel),
                      "resposta_inicio": meta["resposta"][:400]},
                     ensure_ascii=False, indent=2))
    if fora_do_descartavel:
        print("PARADA: contencao violada — mutacao fora do descartavel: "
              + "; ".join(fora_do_descartavel[:20]), file=sys.stderr)
        return 3
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
