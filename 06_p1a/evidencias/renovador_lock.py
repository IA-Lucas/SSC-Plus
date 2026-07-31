#!/usr/bin/env python3
"""Renovador dedicado do lease operacional — SSC+ (experimental).

Processo dedicado que adquire o escritor unico da sessao operacional
(ex.: p1a3-ops) e renova o lease a cada 30 s enquanto a missao durar.
Os runners da missao (preflight da capsula, revisao independente)
VERIFICAM esse lease antes de escrever ou invocar provedor: lease morto
= parada, nunca escrita sem escritor vivo.

Uso: python 06_p1a/evidencias/renovador_lock.py [sessao]   # padrao: p1a3-ops
Encerramento: Ctrl+C (libera o lock do SO) ou morte do processo (o lock
do SO morre junto; o sucessor readquire com fence superior).
"""

import os
import sys
import time

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "05_p0"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))

from escritor import EscritorP1  # noqa: E402

RENOVACAO_S = 30
LEASE_S = 120


def main() -> int:
    sessao = sys.argv[1] if len(sys.argv) > 1 else "p1a3-ops"
    escritor = EscritorP1(os.path.join(_RAIZ, "locks"), sessao=sessao,
                          lease_s=LEASE_S)
    token = escritor.adquirir()
    print(f"lock adquirido: sessao={sessao} fence={token} pid={os.getpid()}",
          flush=True)
    try:
        while True:
            time.sleep(RENOVACAO_S)
            escritor.renovar()
    except KeyboardInterrupt:
        pass
    finally:
        escritor.liberar()
        print(f"lock liberado: sessao={sessao}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
