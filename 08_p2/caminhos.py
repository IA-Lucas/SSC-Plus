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

# `06_p1a/evidencias` entra na lista desde a P2.3: e onde vive
# `contencao`, o protocolo UNICO de contencao do acervo, agora usado
# tambem pelo executor real — e nao so pelo runner, que ate aqui inseria
# esse caminho por conta propria.
for _dir in ("05_p0", "06_p1a", "08_p2",
             os.path.join("06_p1a", "evidencias")):
    _caminho = os.path.join(RAIZ, _dir)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

# Nome do lease do escritor unico desta sessao. Leitor UNICO: o runner e o
# executor real precisam do MESMO nome — o runner para reverificar o lease
# antes de persistir, o executor para atribuir a mutacao do renovador na
# `Vigilancia`. Duas leituras de `SSC_LOCK_SESSAO` com o mesmo default
# seriam a duplicacao de leitor que este acervo ja tem em aberto noutro
# lugar (`_VIA_GITBASH`).
SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p2-ops")
