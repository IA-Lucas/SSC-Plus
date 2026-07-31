#!/usr/bin/env python3
"""Revisao read-only da P1-A.3.1 por provider distinto — SSC+ (experimental).

Diferenca para a P1-A.3: o pacote NAO e montado aqui. Ele e gerado UMA
vez por `pacote_p1a31.py` (deterministico, 2 geracoes com SHA-256
identico) e os MESMOS BYTES sao copiados para o diretorio descartavel
de cada reviewer — nenhuma reconstrucao entre revisores. UMA unica
chamada por provider, via assinatura, custo variavel = 0. Enforcement
read-only: codex `--sandbox read-only --ephemeral`; kimi sem modo
read-only headless: cwd descartavel vazio + instrucao explicita +
politica `auto` com regras estaticas de deny; restantes registrados.

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

from capsula import ambiente_capsula  # noqa: E402

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a31-ops")
USUARIO = os.path.basename(os.path.expanduser("~"))
USUARIO_CURTO = ("".join(c for c in USUARIO.upper() if c.isalnum())[:6]
                 + "~1")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")


def _redigir(texto: str) -> str:
    """Redige usuario local (forma longa e 8.3) de qualquer saida."""
    return (texto or "").replace(USUARIO, "<USUARIO>").replace(
        USUARIO_CURTO, "<USUARIO>")


COMANDOS = {
    "codex": lambda tmp, prompt: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral", prompt],
    "kimi": lambda tmp, prompt: [_KIMI_EXE, "-p", prompt],
}

ENFORCEMENT = {
    "codex": "--sandbox read-only --ephemeral (CLI)",
    "kimi": "sem modo read-only headless no CLI; cwd descartavel vazio + "
            "instrucao de somente leitura; `-p` aplica a politica auto "
            "com regras estaticas de deny (docs oficiais)",
}


def _verificar_lock() -> dict:
    from escritor import EscritorP1
    caminho = RAIZ / "locks" / f"{SESSAO_LOCK}.lease"
    try:
        lease = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: lease ilegivel/ausente: {exc}")
    if lease.get("sessao") != SESSAO_LOCK or \
            EscritorP1.lease_expirado(str(caminho)):
        raise SystemExit("PARADA: lease da sessao operacional morto")
    return {"sessao": lease["sessao"], "pid_titular": lease["pid"]}


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
    # MESMOS BYTES para os dois revisores: copia verbatim, sem remontagem.
    with open(os.path.join(tmp, "pacote-revisao.txt"), "wb") as f:
        f.write(dados_pacote)
    prompt = montar_prompt()
    argv = COMANDOS[provider](tmp, prompt)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
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
    restantes = [str(p.relative_to(tmp)) for p in Path(tmp).rglob("*")
                 if p.is_file()]
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
                      "resposta_inicio": meta["resposta"][:400]},
                     ensure_ascii=False, indent=2))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
