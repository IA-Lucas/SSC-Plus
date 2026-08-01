#!/usr/bin/env python3
"""Revisao read-only da P1-A.3.1 por provider distinto — SSC+ (experimental).

Diferenca para a P1-A.3: o pacote NAO e montado aqui. Ele e gerado UMA
vez por `pacote_p1a31.py` (deterministico, 2 geracoes com SHA-256
identico) e os MESMOS BYTES sao copiados para o diretorio descartavel
de cada reviewer — nenhuma reconstrucao entre revisores. UMA unica
chamada por provider, via assinatura, custo variavel = 0. Enforcement
read-only: codex `--sandbox read-only --ephemeral`; kimi sem sandbox de
filesystem no CLI — restricao parcial (`--plan`, `--skills-dir` vazio,
sem `-y/--yolo/--auto`) mais DETECCAO integral por manifesto SHA-256 da
arvore antes/depois (revisao P1-A.3.1, MAJOR #3).

O tier declarado do provider (`tiers_declarados.json`) precisa estar
VALIDO no instante da chamada; expirado = PARADA (somente o proprietario
renova). Executa DENTRO da capsula: o subprocesso recebe
`capsula.ambiente_capsula()`; o ambiente global/HKCU permanece intacto.
Escritor unico: lease da sessao operacional verificado antes de invocar
e antes de gravar.

Uso: python 06_p1a/evidencias/revisao_p1a31.py codex|kimi <pacote.txt>
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a31"

sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))

sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       manifesto, mutacoes, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a31-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")


def _redigir(texto: str) -> str:
    """Redige usuario local e caminho local — implementacao CANONICA.

    ACHADO 10 da P1-A.3.5: havia nove copias desta redacao em tres
    forcas, nenhuma com teste. Esta delega a unica, que acrescenta o
    prefixo de caminho local ao que ja era feito aqui.
    """
    from contencao import redigir
    return redigir(texto)


# Revisao P1-A.3.1 (MAJOR #3): o kimi deixa de rodar so com `-p` e
# instrucao textual. `dir_skills` e um diretorio VAZIO criado ao lado do
# descartavel — ver contencao.argv_kimi.
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


def _verificar_lock(fence_esperado: int | None = None) -> dict:
    return verificar_lock(RAIZ, SESSAO_LOCK, fence_esperado)


def _verificar_tier(provider: str) -> dict:
    """Tier declarado precisa estar valido NO INSTANTE da chamada.

    Expirado = PARADA: somente o proprietario pode renovar a declaracao.
    """
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
                "declarado_em_utc": decl["declarado_em_utc"],
                "expira_em_utc": datetime.fromtimestamp(
                    expira, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "valido_no_instante": True}
    raise SystemExit(f"PARADA: sem declaracao de tier para {provider}")


def montar_prompt() -> str:
    """Prompt curto (argv): o pacote vai no arquivo do diretorio."""
    return (
        "Revise em modo SOMENTE LEITURA o pacote SSC+ P1-A.3.1. O pacote "
        "completo (identidade do commit/tree, diff integral, arquivos "
        "completos, suites, threat review, hashes de evidencias e as "
        "perguntas 1-6) esta em ./pacote-revisao.txt no diretorio "
        "atual: leia-o POR INTEIRO antes de avaliar. Voce NAO pode "
        "escrever nada: responda apenas com a revisao em texto.\n\n"
        "Declare obrigatoriamente, uma linha cada, ANTES dos achados:\n"
        "PROVIDER: <seu provider>\n"
        "MODELO-OBSERVADO: <o modelo que voce observa ser>\n"
        "CANAL: <canal de acesso, ex.: assinatura OAuth>\n"
        "PACOTE-SHA256: <SHA-256 de ./pacote-revisao.txt — compute, ex.: "
        "`sha256sum pacote-revisao.txt` ou `python -c \"import hashlib;"
        "print(hashlib.sha256(open('pacote-revisao.txt','rb').read())"
        ".hexdigest())\"`>\n"
        "ESCOPO: <o que voce revisou>\n\n"
        "Depois: um achado por linha, prefixado por severidade "
        "CRITICAL | MAJOR | MINOR | OBS, seguida de arquivo:tema e "
        "descricao curta. Para cada MINOR, classifique como bloqueante "
        "ou nao-bloqueante, com motivo. Se nao houver achado num nivel, "
        "nao o invente. Termine com VEREDITO: APROVADO | "
        "APROVADO-COM-RESSALVAS | REPROVADO.")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a31.py codex|kimi <pacote.txt>",
              file=sys.stderr)
        return 2
    provider = sys.argv[1]
    # O console Windows (cp1252) nao cobre todos os glifos da resposta;
    # a evidencia completa vai para o JSON — o stdout e so um resumo.
    sys.stdout.reconfigure(errors="replace")
    lock = _verificar_lock()
    tier = _verificar_tier(provider)

    dados_pacote = Path(sys.argv[2]).read_bytes()
    pacote_sha256 = hashlib.sha256(dados_pacote).hexdigest()

    env = ambiente_capsula()
    removidas = sorted(set(os.environ) - set(env))
    tmp = tempfile.mkdtemp(prefix=f"p1a31-revisao-{provider}-")
    skills = tempfile.mkdtemp(prefix=f"p1a31-skills-vazio-{provider}-")
    # MESMOS BYTES para os dois revisores: copia verbatim, sem remontagem.
    with open(os.path.join(tmp, "pacote-revisao.txt"), "wb") as f:
        f.write(dados_pacote)
    prompt = montar_prompt()
    argv = COMANDOS[provider](tmp, skills, prompt)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Revisao P1-A.3.1 (MAJOR #3): manifesto SHA-256 da arvore INTEIRA
    # antes e depois da chamada. A lista de restantes so olha dentro do
    # descartavel; e a escrita FORA dele que precisava de deteccao.
    antes = manifesto(RAIZ)
    inicio = time.monotonic()
    try:
        proc = subprocess.run(
            argv, cwd=tmp, env=env, capture_output=True, text=True,
            timeout=900, encoding="utf-8", errors="replace")
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, out = "TIMEOUT", (e.stdout or "")
        err = (e.stderr or "") + "\nTIMEOUT apos 900s"
    duracao = round(time.monotonic() - inicio, 3)
    fora_do_descartavel = mutacoes(antes, manifesto(RAIZ))
    restantes = [str(p.relative_to(tmp)) for p in Path(tmp).rglob("*")
                 if p.is_file()]
    # Revisao P1-A.3.1 (MAJOR #4): o lease e reverificado AQUI, depois da
    # chamada e imediatamente antes de persistir, com o MESMO fence da
    # abertura — a chamada pode ter excedido a janela do lease.
    lock = _verificar_lock(fence_esperado=lock["fence"])
    meta = {
        "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a31",
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
        "resposta": _redigir((out or "").strip()),
        "stderr_resumo": _redigir((err or "").strip()[:2000]),
        "quota_observavel": "nao-exposta-pelo-cli",
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    # Redacao aplicada ao JSON INTEIRO (todos os campos, inclusive
    # argv_publico e restantes) — defesa em profundidade.
    texto = _redigir(json.dumps(meta, ensure_ascii=False, indent=2))
    (SAIDA / f"{provider}-{ts}.json").write_text(texto + "\n",
                                                 encoding="utf-8")
    print(json.dumps({"provider": provider, "returncode": rc,
                      "duracao_s": duracao,
                      "pacote_sha256": pacote_sha256,
                      "contencao_violada": bool(fora_do_descartavel),
                      "resposta_inicio": meta["resposta"][:400]},
                     ensure_ascii=False, indent=2))
    if fora_do_descartavel:
        # A evidencia da violacao ja foi persistida acima; a corrida,
        # porem, nao pode ser dada por valida.
        print("PARADA: contencao violada — mutacao fora do descartavel: "
              + "; ".join(fora_do_descartavel[:20]), file=sys.stderr)
        return 3
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
