"""Verificacao canonica do SSC+ em processos isolados e reproduziveis."""

from __future__ import annotations

import argparse
import getpass
import os
import platform
import subprocess
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def executar(rotulo: str, argv: list[str], cwd: Path = RAIZ) -> None:
    print(f"\n== {rotulo} ==", flush=True)
    resultado = subprocess.run(argv, cwd=cwd, env=os.environ.copy())
    if resultado.returncode:
        raise SystemExit(
            f"FALHA em {rotulo}: codigo {resultado.returncode}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Roda a verificacao unica e sem chamadas de modelo do SSC+.")
    parser.add_argument("--rapido", action="store_true",
                        help="omite cenarios/receitas; mantem as duas suites")
    args = parser.parse_args(argv)

    # Escopo somente para esta arvore e seus subprocessos; nao altera a
    # configuracao global da estacao e faz os testes historicos de blobs
    # funcionarem em runners cujo dono do checkout difere do usuario.
    os.environ["GIT_CONFIG_COUNT"] = "1"
    os.environ["GIT_CONFIG_KEY_0"] = "safe.directory"
    os.environ["GIT_CONFIG_VALUE_0"] = str(RAIZ)

    pytest_versao = subprocess.run(
        [sys.executable, "-m", "pytest", "--version"], cwd=RAIZ,
        capture_output=True, text=True).stdout.strip() or "nao instalado"
    autocrlf = subprocess.run(
        ["git", "-c", f"safe.directory={RAIZ.as_posix()}", "config",
         "--get", "core.autocrlf"], cwd=RAIZ, capture_output=True,
        text=True).stdout.strip() or "nao definido"
    print("plataforma: "
          f"interpretador={platform.python_implementation()} {platform.python_version()} | "
          f"pytest={pytest_versao} | core.autocrlf={autocrlf} | "
          f"usuario={getpass.getuser()}")

    executar("P0 unittest", [sys.executable, "-W", "error::ResourceWarning",
                              "-m", "unittest", "discover", "-s",
                              "05_p0/tests", "-v"])
    executar("P1-A/P2 unittest",
             [sys.executable, "-W", "error::ResourceWarning", "-m",
              "unittest", "discover", "-s", "06_p1a/tests", "-v"])
    if not args.rapido:
        executar("prova central",
                 [sys.executable, "05_p0/cenarios/prova_central.py",
                  "--sem-gravar"])
        executar("receitas P2",
                 [sys.executable, "08_p2/medidor.py", "--todas"])
    print("\nVERIFICACAO SSC+: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
