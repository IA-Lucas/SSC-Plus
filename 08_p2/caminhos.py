"""Raiz do repositorio e sys.path da P2 — importado ANTES dos demais.

Mesmo mecanismo de `06_p1a/tests/apoio.py`: a insercao no `sys.path` e
efeito de import, feita num lugar so. Os diretorios `05_p0`, `06_p1a` e
`08_p2` nao sao pacotes importaveis pelo nome (comecam com digito), e
repetir o preambulo em cada modulo da P2 seria a duplicacao de leitor que
este acervo ja tem em aberto noutro lugar.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for _dir in ("05_p0", "06_p1a", "08_p2"):
    _caminho = os.path.join(RAIZ, _dir)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)
