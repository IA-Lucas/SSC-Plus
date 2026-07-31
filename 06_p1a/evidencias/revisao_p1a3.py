#!/usr/bin/env python3
"""Revisao read-only da P1-A.3 por provider distinto — SSC+ (experimental).

UMA unica chamada por provider, via assinatura, custo variavel = 0.
Enforcement read-only: codex roda com `--sandbox read-only --ephemeral`.
O kimi NAO tem sandbox de filesystem (medido em `kimi --help`): o
enforcement dele e (i) restricao parcial pelo proprio CLI — `--plan`,
`--skills-dir` vazio e ausencia deliberada de `-y/--yolo/--auto` — com
cwd num DIRETORIO DESCARTAVEL, e (ii) DETECCAO integral por manifesto
SHA-256 da arvore inteira antes e depois da chamada. Foi esta segunda
metade que faltava (revisao P1-A.3.1, MAJOR #3): cwd descartavel e
instrucao textual nao restringem o filesystem, e a lista de arquivos
restantes so olha DENTRO do descartavel — escrita fora dele passava sem
registro. Mutacao fora do descartavel agora reprova a corrida.
O pacote de revisao e montado em memoria a partir dos artefatos da
P1-A.3 e embutido no prompt — o reviewer NAO recebe acesso de escrita ao
repositorio. A resposta (achados com severidade) e a unica saida
persistida. Nenhum segredo entra no pacote: somente arquivos do
laboratorio ja varridos, com o nome do usuario local redigido.

Executa DENTRO da capsula: o subprocesso do CLI recebe
`capsula.ambiente_capsula()` (nenhuma credencial de modelo no env-filho;
o ambiente global/HKCU permanece intocado). Escritor unico: verifica o
lease da sessao operacional antes de invocar e antes de gravar.

Uso: python 06_p1a/evidencias/revisao_p1a3.py codex|kimi
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
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a3"

sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))

sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       manifesto, mutacoes, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a3-ops")
USUARIO = os.path.basename(os.path.expanduser("~"))
# Forma 8.3 do perfil do Windows (6 alfanumericos + "~1"): o codex ecoa
# o cwd em caminho curto; sem redigi-la, o usuario local vaza para a
# evidencia (revisao P1-A.3, varredura ZeroPii).
USUARIO_CURTO = ("".join(c for c in USUARIO.upper() if c.isalnum())[:6]
                 + "~1")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")


def _redigir(texto: str) -> str:
    """Redige usuario local (forma longa e 8.3) de qualquer saida."""
    return (texto or "").replace(USUARIO, "<USUARIO>").replace(
        USUARIO_CURTO, "<USUARIO>")

# Revisao P1-A.3.1 (MAJOR #3): o kimi deixa de rodar so com `-p` e
# instrucao textual — ver contencao.argv_kimi.
COMANDOS = {
    "codex": lambda tmp, skills, prompt: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral", prompt],
    "kimi": lambda tmp, skills, prompt: argv_kimi(_KIMI_EXE, prompt, skills),
}

# Enforcement read-only declarado por provider (evidencia).
ENFORCEMENT = {
    "codex": "--sandbox read-only --ephemeral (CLI)",
    "kimi": enforcement_kimi(),
}


def _ler(rel: str) -> str:
    return (RAIZ / rel).read_text(encoding="utf-8").replace(
        USUARIO, "<USUARIO>")


def _verificar_lock(fence_esperado: int | None = None) -> dict:
    return verificar_lock(RAIZ, SESSAO_LOCK, fence_esperado)


def montar_pacote() -> str:
    """Pacote de revisao: contexto + changeset completo da P1-A.3.

    Gravado em `pacote-revisao.txt` no diretorio descartavel do reviewer
    — o argv do Windows nao comporta o changeset inteiro (limite de
    ~32k chars do CreateProcess, WinError 206). Sem segredos: somente
    arquivos do laboratorio ja varridos, usuario local redigido.
    """
    return f"""PACOTE DE REVISAO — SSC+ P1-A.3 (laboratorio experimental, sem autoridade)

Contexto: a P1-A.2 entregou a capsula subscription-only, mas o preflight
real bateu em bloqueios FACTUAIS de especificacao: codex e kimi nao expoem
o plano comercial no CLI; `codex models` e TTY-only; `claude models` e
interativo. O Soberano decidiu as emendas que este changeset implementa:

1. APROVADA COM LIMITES: tier DECLARADO pelo proprietario
   (06_p1a/tiers_declarados.json) + OAuth OBSERVADO habilita SOMENTE
   SHADOW_ELIGIBLE, validade maxima de 24 horas. NAO autoriza P2 nem
   execucao autonoma.
2. APROVADA: `codex doctor` comprova o modelo efetivo atual e o modo de
   autenticacao, SEM equivaler a catalogo completo.
3. PARCIALMENTE APROVADA: `kimi provider list` comprova OAuth e modelo
   efetivo, mas NAO o plano comercial (cai na trilha sombra do item 1).
4. NAO APROVADA POR DECLARACAO: claude permanece SUPERVISED enquanto nao
   houver modelo exato observado por fonte oficial nao interativa; o
   plano Max, isoladamente, nao basta (descoberta desativada:
   comandos["modelos"] = None).
5. Google e Grok permanecem SUPERVISED, zero sondas automaticas.
6. Capsula subscription-only, politica NVIDIA e bloqueios PAYG
   INALTERADOS.

Avalie com olhar adversarial, citando arquivo/trecho:
1. A trilha SHADOW_ELIGIBLE pode virar ELIGIBLE em algum caminho? Ela
   sobe o teto de algum provider SUPERVISED? Autoriza algo alem de
   diagnostico?
2. A validade de 24 h e fail-closed? Timestamp ilegivel/futuro/expirado,
   validade declarada > 24 h, fronteira exata — algum caso vaza?
3. O parser do `codex doctor` e fail-closed (rc!=0, auth ausente ou
   diferente de chatgpt, modelo ausente)? Ha saida que produza modelo
   sem auth comprovado?
4. Claude: com comandos["modelos"] = None, existe caminho que ainda
   sondaria modelos ou classificaria acima de SUPERVISED?
5. As emendas enfraqueceram algum bloqueio economico (PAYG, capsula,
   conflito env x login, quota esgotada)? A trilha sombra vence algum
   deles?
6. Cobertura dos testes novos contra os itens 1-5 acima; algum segredo,
   PII ou caminho local vazando para artefato/excecao/teste?

=== 06_p1a/preflight/pipeline.py ===
{_ler("06_p1a/preflight/pipeline.py")}

=== 06_p1a/preflight/sombra.py ===
{_ler("06_p1a/preflight/sombra.py")}

=== 06_p1a/preflight/adaptadores.py (arquivo completo) ===
{_ler("06_p1a/preflight/adaptadores.py")}

=== 06_p1a/preflight/frota_real.py (especificacao emendada) ===
{_ler("06_p1a/preflight/frota_real.py")}

=== 06_p1a/preflight/economia.py (arquivo completo) ===
{_ler("06_p1a/preflight/economia.py")}

=== 06_p1a/tiers_declarados.json ===
{_ler("06_p1a/tiers_declarados.json")}

=== 06_p1a/tests/test_emendas_p1a3.py ===
{_ler("06_p1a/tests/test_emendas_p1a3.py")}

=== 06_p1a/07_adendo-emendas-p1a3.md ===
{_ler("06_p1a/07_adendo-emendas-p1a3.md")}
"""


def montar_prompt() -> str:
    """Prompt curto (argv): o changeset vai no arquivo do diretorio."""
    return (
        "Revise em modo SOMENTE LEITURA o changeset SSC+ P1-A.3. O pacote "
        "completo (contexto, perguntas 1-6 e todos os arquivos do "
        "changeset) esta em ./pacote-revisao.txt no diretorio atual: "
        "leia-o POR INTEIRO antes de avaliar. Voce NAO pode escrever "
        "nada: responda apenas com a revisao em texto.\n\n"
        "Formato de resposta: um achado por linha, prefixado por "
        "severidade CRITICAL | MAJOR | MINOR | OBS, seguida de "
        "arquivo:tema e descricao curta. Se nao houver achado num nivel, "
        "nao o invente. Termine com um veredito: APROVADO | "
        "APROVADO-COM-RESSALVAS | REPROVADO.")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a3.py codex|kimi", file=sys.stderr)
        return 2
    provider = sys.argv[1]
    # O console Windows (cp1252) nao cobre todos os glifos da resposta;
    # a evidencia completa vai para o JSON — o stdout e so um resumo.
    sys.stdout.reconfigure(errors="replace")
    lock = _verificar_lock()

    env = ambiente_capsula()
    removidas = sorted(set(os.environ) - set(env))
    tmp = tempfile.mkdtemp(prefix=f"p1a3-revisao-{provider}-")
    skills = tempfile.mkdtemp(prefix=f"p1a3-skills-vazio-{provider}-")
    pacote = montar_pacote()
    with open(os.path.join(tmp, "pacote-revisao.txt"), "w",
              encoding="utf-8") as f:
        f.write(pacote)
    prompt = montar_prompt()
    argv = COMANDOS[provider](tmp, skills, prompt)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Revisao P1-A.3.1 (MAJOR #3): manifesto SHA-256 da arvore INTEIRA
    # antes e depois — a lista de restantes so ve dentro do descartavel.
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
    # Revisao P1-A.3.1 (MAJOR #4): lease reverificado imediatamente antes
    # de persistir, com o MESMO fence da abertura.
    lock = _verificar_lock(fence_esperado=lock["fence"])
    meta = {
        "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a3",
        "chamadas_de_modelo": 1, "custo_variavel": 0,
        "rotulo": "assinatura-oauth; UMA chamada; enforcement read-only",
        "enforcement_read_only": ENFORCEMENT[provider],
        "lock_escritor_unico": lock,
        "argv_publico": ["<PROMPT>" if a == prompt else a for a in argv],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "pacote_sha256": hashlib.sha256(pacote.encode()).hexdigest(),
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
    # argv_publico e restantes) — defesa em profundidade sobre a redacao
    # campo a campo.
    texto = _redigir(json.dumps(meta, ensure_ascii=False, indent=2))
    (SAIDA / f"{provider}-{ts}.json").write_text(texto + "\n",
                                                 encoding="utf-8")
    print(json.dumps({"provider": provider, "returncode": rc,
                      "duracao_s": duracao,
                      "contencao_violada": bool(fora_do_descartavel),
                      "resposta_inicio": meta["resposta"][:400]},
                     ensure_ascii=False, indent=2))
    if fora_do_descartavel:
        # A evidencia da violacao ja foi persistida; a corrida, nao.
        print("PARADA: contencao violada — mutacao fora do descartavel: "
              + "; ".join(fora_do_descartavel[:20]), file=sys.stderr)
        return 3
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
