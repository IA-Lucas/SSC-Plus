#!/usr/bin/env python3
"""SSC+ P1-A — prova minima real por provedor ELIGIBLE.

Um unico prompt minimo e nao sensivel, em diretorio descartavel, sem
ferramentas, sem aprovacao automatica, sem conteudo do LucaX. Ambiente
sanitizado pela implementacao CANONICA e unica
(`preflight.economia.ambiente_sanitizado`, case-insensitive): nenhuma
chave PAYG entra no subprocesso; o ambiente global NAO e modificado.
Registra apenas metadados, resposta, duracao e quota observavel.

Escritor unico (P1-A.1; mecanismo trocado na P1-A.5, ordem 2): antes de
escrever qualquer evidencia ou invocar provedor, o runner adquire o
`EscritorRepositorio` (lease + fencing sobre o writelock da P0, num lock
UNICO para todo o repositorio). Uma segunda sessao falha na aquisicao —
QUALQUER que seja o nome dela, e antes de escrever um byte ou invocar
modelo. Ate a P1-A.4 o lock era `locks/<sessao>.lock`, e a exclusao
valia so dentro do mesmo nome: era o ACHADO 4. Estado de lock: `locks/`
(runtime, ignorado pelo Git).

Uso: python 06_p1a/evidencias/prova_minima.py codex|claude|kimi
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
SAIDA = RAIZ / "06_p1a" / "evidencias" / "prova-minima"

# A sanitizacao e EXCLUSIVAMENTE a canonica do preflight (P1-A.1): nenhuma
# implementacao local. Paths inseridos antes do import para o script rodar
# de qualquer diretorio.
sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))

from escritor_repositorio import (EscritorRepositorio,  # noqa: E402
                                  LockIndisponivel)
from preflight.economia import ambiente_sanitizado  # noqa: E402

PROMPT = "Retorne apenas PROVIDER_OK e o identificador público do modelo."

COMANDOS = {
    # codex: sandbox read-only + efemero = sem ferramentas de escrita, sem
    # persistencia de sessao. (approval observado: never — seguro porque a
    # negacao de escrita vem do sandbox, nao da aprovacao.)
    "codex": lambda tmp: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral", PROMPT],
    # claude: permission-mode plan = enforcement read-only (ferramentas de
    # escrita bloqueadas pelo proprio CLI).
    "claude": lambda tmp: [
        "claude", "-p", PROMPT, "--permission-mode", "plan"],
    # kimi: -p nao combina com --plan ("Cannot combine --prompt with
    # --plan", verificado em 2026-07-30). A protecao e: modo de permissao
    # padrao (pede aprovacao interativa; sem -y/--auto nenhuma ferramenta e
    # auto-aprovada) + cwd descartavel. -m fixa o modelo publico para que a
    # resposta traga o identificador real (contrato da prova).
    "kimi": lambda tmp: ["kimi", "-p", PROMPT, "-m", "kimi-code/k3"],
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMANDOS:
        print("uso: prova_minima.py codex|claude|kimi", file=sys.stderr)
        return 2
    provider = sys.argv[1]

    # Escritor unico ANTES de qualquer escrita ou invocacao de provedor:
    # uma segunda sessao aborta aqui (codigo 3), sem tocar em nada.
    escritor = EscritorRepositorio(RAIZ / "locks", sessao="p1-ops")
    try:
        token = escritor.adquirir()
    except LockIndisponivel as exc:
        print(f"escritor unico: {exc}; abortado ANTES de escrever ou "
              "invocar provedor", file=sys.stderr)
        return 3

    try:
        env = ambiente_sanitizado()
        removidas = sorted(set(os.environ) - set(env))
        tmp = tempfile.mkdtemp(prefix=f"p1a-prova-{provider}-")
        argv = COMANDOS[provider](tmp)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        inicio = time.monotonic()
        try:
            proc = subprocess.run(
                argv, cwd=tmp, env=env, capture_output=True, text=True,
                timeout=300, encoding="utf-8", errors="replace")
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            rc, out = "TIMEOUT", (e.stdout or "")
            err = (e.stderr or "") + "\nTIMEOUT apos 300s"
        duracao = round(time.monotonic() - inicio, 3)
        # Verificacao pos-corrida: o diretorio descartavel deve estar vazio
        # (zero escrita fora do laboratorio, inclusive no descartavel).
        restantes = [str(p.relative_to(tmp)) for p in Path(tmp).rglob("*")
                     if p.is_file()]
        meta = {
            "provider": provider,
            "ts_utc": ts,
            "argv_publico": ["<PROMPT>" if a == PROMPT else a for a in argv],
            "prompt": PROMPT,
            "dir_descartavel": tmp,
            "dir_descartavel_arquivos_restantes": restantes,
            "env_vars_removidas_nomes": removidas,
            "escritor_fencing_token": token,
            "returncode": rc,
            "duracao_s": duracao,
            "resposta": out.strip(),
            "stderr_resumo": err.strip()[:2000],
            "quota_observavel": "nao-exposta-pelo-cli",
            "custo_variavel": 0,
            "rotulo": "assinatura-oauth; prompt unico nao sensivel",
        }
        # Fencing + lease validos imediatamente antes de gravar evidencia:
        # um escritor substituido nunca escreve.
        escritor.verificar()
        SAIDA.mkdir(parents=True, exist_ok=True)
        (SAIDA / f"{provider}-{ts}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        (SAIDA / f"{provider}-{ts}.stdout.txt").write_text(
            out, encoding="utf-8")
        print(json.dumps({k: meta[k] for k in
                          ("provider", "returncode", "duracao_s",
                           "resposta")}, ensure_ascii=False, indent=2))
        return 0 if rc == 0 else 1
    finally:
        escritor.liberar()


if __name__ == "__main__":
    raise SystemExit(main())
