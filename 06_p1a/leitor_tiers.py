"""Leitor UNICO das declaracoes de tier do proprietario — SSC+ P1-B.01.

POR QUE ESTE MODULO EXISTE. A ordem 4 da P1-B.01 mediu que
`07_p1b/preflight_atual.py` tinha ZERO ocorrencia de
`carregar_declaracoes` e que a chamada a `executar_preflight` omitia
`tiers_declarados`, que vale `None` (`pipeline.py:97`) — a trilha
SHADOW_ELIGIBLE inteira, ratificada na emenda P1-A.3 item 1, era
inalcancavel a partir daquele runner mesmo com declaracao valida em
disco. O runner da P1-A ja tinha o leitor, dentro do proprio arquivo.

Copiar aquelas seis linhas para o segundo runner reproduziria o
mecanismo que os achados 7, 10 e 14 da P1-A.3.5 descrevem — a copia que
ninguem exercita fica para tras. O remedio ja tem precedente ratificado
nesta base: `leitores_config.py`, criado pela correcao 7 da P1-A.3.5
justamente para desfazer as DUAS copias do leitor de config. Este modulo
segue o mesmo desenho.

POR QUE NAO DENTRO DE `preflight/`. Mesma razao do leitor de config: o
pacote `preflight/` e deliberadamente livre de I/O —
`CodigoNaoEscreveNemAbreRede` (`tests/test_isolamento.py`) reprova
qualquer `open(` nos seus modulos. A POLITICA (validade de 24 h,
declarante = proprietario, tier dentro dos planos aceitos) continua
inteira em `preflight/sombra.py` e em `preflight/pipeline.py`; aqui ha
somente a leitura do disco.

FAIL-CLOSED. Arquivo ausente, ilegivel ou com estrutura inesperada
devolve `{}` — trilha sombra indisponivel, nunca excecao propagada e
nunca declaracao inventada. Declaracao VENCIDA nao e filtrada aqui: ela
chega ao pipeline e sai como `DeclaracaoExpirada` no relatorio, que e o
que a evidencia deve mostrar. Renovar declaracao e ato do proprietario,
nunca do runner.
"""

import json
import os

from preflight.sombra import carregar_declaracoes

CAMINHO_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "tiers_declarados.json")


def carregar_tiers(caminho: str | None = None) -> dict:
    """`provider_id` -> DeclaracaoTier, lidos do JSON do proprietario.

    O parse e a validacao de forma sao de `preflight.sombra`; aqui ha
    apenas o `open`. Devolve `{}` (fail-closed) quando a fonte nao existe
    ou nao e legivel — por MEDICAO do disco, jamais por cegueira escrita
    no fonte.
    """
    try:
        with open(caminho or CAMINHO_PADRAO, encoding="utf-8") as f:
            return carregar_declaracoes(json.load(f))
    except (OSError, ValueError):
        return {}
