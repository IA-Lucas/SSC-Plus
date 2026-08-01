#!/usr/bin/env python3
"""Revisao read-only da P1-A.2 por provider distinto — SSC+ (experimental).

UMA unica chamada por provider, via assinatura, custo variavel = 0, com
enforcement read-only do proprio CLI (codex: `--sandbox read-only
--ephemeral`; claude: `--permission-mode plan`). O pacote de revisao e
montado em memoria a partir dos artefatos da P1-A.2 e embutido no prompt
— o reviewer NAO recebe acesso de escrita e roda em diretorio
descartavel; a resposta (achados com severidade) e a unica saida
persistida. Nenhum segredo entra no pacote: somente arquivos do
laboratorio ja varridos, com o nome do usuario local redigido.

Executa DENTRO da capsula: o subprocesso do CLI recebe
`capsula.ambiente_capsula()` (nenhuma credencial de modelo no env-filho;
o ambiente global/HKCU permanece intocado). Escritor unico: verifica o
lease da sessao operacional antes de invocar e antes de gravar.

Uso: python 06_p1a/evidencias/revisao_p1a2.py codex|claude
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a2"

sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))

from capsula import ambiente_capsula  # noqa: E402

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a2-ops")

COMANDOS = {
    "codex": lambda tmp, prompt: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral", prompt],
    "claude": lambda tmp, prompt: [
        "claude", "-p", prompt, "--permission-mode", "plan"],
}


def _redigir(texto: str) -> str:
    """ACHADO 10: esta era a redacao mais fraca do acervo — inline, so a
    forma longa do usuario, sem a forma 8.3 e sem o caminho local.
    Delega a canonica."""
    from contencao import redigir
    return redigir(texto)


def _ler(rel: str) -> str:
    return _redigir((RAIZ / rel).read_text(encoding="utf-8"))


def _verificar_lock(fence_esperado: int | None = None) -> dict:
    """Escritor unico — verificacao CANONICA.

    Era a QUARTA copia local do mesmo guarda, e a unica do lado da P1-A
    que ainda nao delegava: sem `fence_esperado`, ela nao detectava
    troca de titular, e a varredura da P1-A.3.5 mediu que nenhuma das
    suas linhas de recusa era alcancada por teste. Delega a canonica,
    que ganha tambem o fence no retorno (acrescimo aditivo).
    """
    from contencao import verificar_lock
    return verificar_lock(RAIZ, SESSAO_LOCK, fence_esperado)


def _ultimo_preflight() -> str:
    cand = sorted((RAIZ / "06_p1a" / "evidencias").glob(
        "p1a2-preflight-*.json"))
    if not cand:
        return "(preflight P1-A.2 ainda nao persistido)"
    dados = json.loads(cand[-1].read_text(encoding="utf-8"))
    linhas = []
    for r in dados["frota"]:
        erros = ",".join(e["codigo"] for e in r["erros"]) or "-"
        linhas.append(f"  {r['provider_id']}: {r['resultado']} "
                      f"(plano={r['plano']}, quota={r['quota']}, "
                      f"modelos={len(r['modelos'])}, erros={erros})")
    return "\n".join(linhas)


def montar_prompt() -> str:
    return f"""Revise em modo SOMENTE LEITURA o changeset SSC+ P1-A.2 abaixo (laboratorio
experimental, sem autoridade). Voce NAO pode escrever nada: responda apenas
com a revisao em texto.

Contexto: o SSC+ opera em estacao do usuario que tem credenciais globais de
outros projetos (ex.: NVIDIA_API_KEY em HKCU). A P1-A.2 institui uma CAPSULA
subscription-only: o processo SSC+ nasce num ambiente-filho sem nenhuma
credencial de modelo (o global/HKCU NUNCA e modificado), e dentro da capsula
qualquer credencial visivel bloqueia (politica estrita). Alem disso, dois
defeitos do preflight foram corrigidos: F-1 (~ do executavel nao era
expandido; claude/kimi falsos CLI-INDISPONIVEL) e F-2 (`codex login status`
imprime em stderr; login valido era lido como ausente).

Preflight real mais recente dentro da capsula (sondas de diagnostico apenas,
zero chamada de modelo):
{_ultimo_preflight()}

Avalie com olhar adversarial, citando arquivo/trecho:
1. A capsula realmente impede credencial de modelo no processo-filho sem
   tocar o ambiente global? Ha caminho de vazamento ou enfraquecimento?
2. F-1: expanduser so no executavel — regressoes? espacos/metacaracteres?
3. F-2: combinacao stdout+stderr — algum caso vira login por inferencia?
   conflito entre canais esta fail-closed?
4. Cobertura dos testes contra a lista de provas da missao (injecao NVIDIA
   pre-sonda nos 5; variantes api_key nu/caixa/hifen/camelCase/listas;
   conflito OAuth×key; til/inexistente/metacaracteres; codex stdout/stderr/
   ambos/rc/negacao/conflito; zero segredo em erro/log).
5. Algum segredo, PII ou caminho local vazando para artefato/excecao/teste?

Formato de resposta: um achado por linha, prefixado por severidade
CRITICAL | MAJOR | MINOR | OBS, seguida de arquivo:tema e descricao curta.
Se nao houver achado num nivel, nao o invente. Termine com um veredito:
APROVADO | APROVADO-COM-RESSALVAS | REPROVADO.

=== 06_p1a/capsula.py ===
{_ler("06_p1a/capsula.py")}

=== 06_p1a/preflight/adaptadores.py (trechos F-1/F-2) ===
{_ler("06_p1a/preflight/adaptadores.py")[:5200]}

=== 06_p1a/tests/test_capsula_p1a2.py ===
{_ler("06_p1a/tests/test_capsula_p1a2.py")}

=== 06_p1a/06_adendo-capsula-p1a2.md ===
{_ler("06_p1a/06_adendo-capsula-p1a2.md")}
"""


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a2.py codex|claude", file=sys.stderr)
        return 2
    provider = sys.argv[1]
    lock = _verificar_lock()

    env = ambiente_capsula()
    removidas = sorted(set(os.environ) - set(env))
    tmp = tempfile.mkdtemp(prefix=f"p1a2-revisao-{provider}-")
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
        "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a2",
        "chamadas_de_modelo": 1, "custo_variavel": 0,
        "rotulo": "assinatura-oauth; UMA chamada; enforcement read-only",
        "lock_escritor_unico": lock,
        "argv_publico": ["<PROMPT>" if a == prompt else a for a in argv],
        "prompt_sha256": __import__("hashlib").sha256(
            prompt.encode()).hexdigest(),
        "dir_descartavel": tmp,
        "dir_descartavel_arquivos_restantes": restantes,
        "env_vars_removidas_nomes": removidas,
        "returncode": rc, "duracao_s": duracao,
        "resposta": _redigir(out.strip()),
        "stderr_resumo": _redigir(err.strip()[:2000]),
        "quota_observavel": "nao-exposta-pelo-cli",
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / f"{provider}-{ts}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({"provider": provider, "returncode": rc,
                      "duracao_s": duracao,
                      "resposta_inicio": meta["resposta"][:400]},
                     ensure_ascii=False, indent=2))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
