"""Ciclo de vida de uma arvore de subprocessos, inclusive no Windows.

`Popen.kill()` encerra apenas o processo imediato. CLIs npm iniciados por
Git Bash deixam `node.exe` neto segurando os pipes e continuando a executar.
Esta primitiva cria um grupo proprio e encerra a arvore inteira no timeout.
"""

from __future__ import annotations

import os
import locale
import signal
import subprocess


def opcoes_nova_arvore() -> dict:
    """Opcoes de `Popen` que isolam a arvore sem abrir um shell."""
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def decodificar_saida(bruto: bytes | str | None) -> str:
    """Decodifica a saida medida sem confiar na page de codigo do pai."""
    if bruto is None:
        return ""
    if isinstance(bruto, str):
        return bruto
    if not bruto:
        return ""
    tentativas = ["utf-8"]
    local = locale.getpreferredencoding(False)
    if local and local.lower() not in [t.lower() for t in tentativas]:
        tentativas.append(local)
    if "cp1252" not in [t.lower() for t in tentativas]:
        tentativas.append("cp1252")
    for codificacao in tentativas:
        try:
            return bruto.decode(codificacao)
        except (UnicodeDecodeError, LookupError):
            continue
    return bruto.decode("utf-8", errors="replace")


def encerrar_arvore(proc: subprocess.Popen, espera_s: int = 10) -> None:
    """Encerra `proc` e descendentes; retorna apenas depois do pai morrer."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=espera_s, check=False)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
    if proc.poll() is None:
        try:
            proc.kill()
        except OSError:
            pass
    try:
        proc.wait(timeout=espera_s)
    except (subprocess.TimeoutExpired, OSError):
        pass
