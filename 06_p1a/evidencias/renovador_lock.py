#!/usr/bin/env python3
"""Renovador dedicado do lease operacional — SSC+ (experimental).

Processo dedicado que adquire o escritor unico do REPOSITORIO em nome da
sessao operacional (ex.: p1a5-ops) e renova o lease a cada 30 s enquanto
a missao durar. Os runners da missao (preflight da capsula, revisao
independente) VERIFICAM esse lease antes de escrever ou invocar provedor:
lease morto, ou titular que nao e a sessao, = parada — nunca escrita sem
escritor vivo.

P1-A.5, ordem 2: o escritor passa a ser o `EscritorRepositorio`. Ate a
P1-A.4 este processo adquiria `locks/<sessao>.lock`, de modo que uma
missao de OUTRO nome adquiria outro arquivo e as duas se consideravam
escritor unico — o ACHADO 4. Agora o arquivo e sempre
`locks/repositorio.lock` e o nome e apenas o titular registrado: a
segunda missao FALHA na aquisicao, com codigo 3, antes de escrever um
byte.

Uso: python 06_p1a/evidencias/renovador_lock.py [sessao] [dir_locks]
     # padroes: p1a3-ops e <raiz>/locks
O segundo argumento existe para que a prova entre PROCESSOS REAIS possa
correr sobre um diretorio descartavel em vez do `locks/` vivo. Ele nao
muda o comportamento de quem nao o passa, e nao ha caminho operacional
que o use.
Encerramento: Ctrl+C (libera o lock do SO e EXPIRA o lease concedido) ou
morte do processo (o lock do SO morre junto; o sucessor readquire com
fence superior).
"""

import os
import sys
import time

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_RAIZ, "05_p0"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))

from escritor_repositorio import (EscritorRepositorio,  # noqa: E402
                                  LockIndisponivel, titular_atual)

RENOVACAO_S = 30
LEASE_S = 120


def main() -> int:
    sessao = sys.argv[1] if len(sys.argv) > 1 else "p1a3-ops"
    dir_locks = sys.argv[2] if len(sys.argv) > 2 \
        else os.path.join(_RAIZ, "locks")
    escritor = EscritorRepositorio(dir_locks, sessao=sessao, lease_s=LEASE_S)
    try:
        token = escritor.adquirir()
    except LockIndisponivel as exc:
        # A segunda missao para AQUI: antes de escrever um byte e antes
        # de qualquer runner poder invocar provedor.
        titular = titular_atual(dir_locks)
        nome = titular["sessao"] if titular else "desconhecido (lease vencido)"
        print(f"PARADA: o escritor unico do repositorio ja e de {nome!r}; "
              f"{sessao!r} nao adquiriu e nao escreveu ({exc})",
              file=sys.stderr, flush=True)
        return 3
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
