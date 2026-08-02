"""Leitores de config persistida dos provedores — SSC+ P1-A.3.5.

POR QUE ESTE MODULO EXISTE. A varredura de guardas da P1-A.3.5 contou
DUAS implementacoes de `_config_persistida` — `06_p1a/preflight_capsula.py`
e `07_p1b/preflight_atual.py` — e as correcoes 1 e 3 desta missao
alcancaram apenas a primeira. A copia da P1-B ficou com os DOIS defeitos
que aquelas correcoes fecharam: cegueira incondicional para grok e a
allowlist de duas chaves no codex. E o mesmo mecanismo do ACHADO 7 (o
MAJOR #4 que nunca alcancou a P1-B) e do achado 10 (nove redacoes em tres
forcas): a copia que ninguem exercita e a que fica para tras.

POR QUE NAO DENTRO DE `preflight/`. O pacote `preflight/` e
deliberadamente livre de I/O — `CodigoNaoEscreveNemAbreRede`
(`tests/test_isolamento.py`) reprova qualquer `open(` nos seus modulos, e
essa e uma propriedade que se quer manter. Ler config de disco precisa
de um lar fora do pacote, e este e ele: um modulo de leitura, sem
politica, cujos resultados sao entregues a `economia.auditar_config`.

Os valores lidos NUNCA sao gravados: a auditoria devolve apenas nomes de
campo.

FALHA FECHADA (achado N2 da P1-A.3.7). Ate aqui, fonte ausente, ilegivel
ou com JSON invalido devolvia `{}` — o MESMO valor de uma fonte lida e
limpa. A distincao vivia na prosa desta docstring e o valor entregue a
`auditar_config` nao a carregava. Agora ela vive no VALOR: fonte que nao
pode ser lida devolve `{CHAVE_FONTE_NAO_LIDA: ["<fonte>: <motivo>"]}`, e
`auditar_config` transforma isso em `P1A-CONFIG-NAO-LIDA`. Somente
fonte lida DE FATO e vazia devolve `{}`.

Consequencia declarada, e nao efeito colateral: um provedor cuja fonte
declarada em `FONTES` nao exista na estacao passa a sair BLOCKED. E o
resultado pretendido — "nao localizada" descrevendo o que nao foi
procurado e o fundamento do MAJOR #1, e nao pode continuar valendo como
prova de estacao limpa.
"""

import json
import os
import tomllib

from preflight.economia import CHAVE_FONTE_NAO_LIDA

__all__ = ["CHAVE_FONTE_NAO_LIDA", "FONTES", "config_persistida",
           "ler_json", "ler_jsons_do_diretorio", "ler_toml"]

# Fontes reais por provedor, medidas na P1-A e na P1-A.3.5. Lista
# explicita: um provedor sem fonte declarada nao vira `{}` silencioso.
FONTES = {
    "codex": ("json", "~/.codex/auth.json"),
    "claude": ("json", "~/.claude/settings.json"),
    "kimi": ("toml", "~/.kimi-code/config.toml"),
    "google": ("json", "~/.gemini/settings.json"),
    "grok": ("dir-json", "~/.grok"),
}


def nao_lida(fonte: str, motivo: str) -> dict:
    """Valor que declara, no proprio conteudo, que a fonte nao foi lida.

    Nunca e `{}`: e essa desigualdade que `auditar_config` consome para
    falhar fechada. O motivo e o NOME da excecao ou uma frase curta —
    jamais bytes do arquivo.
    """
    return {CHAVE_FONTE_NAO_LIDA: [f"{fonte}: {motivo}"]}


def _juntar_nao_lidas(*dicts) -> list:
    """Motivos de fonte-nao-lida de topo dos dicts, na ordem recebida."""
    motivos = []
    for d in dicts:
        motivos.extend(d.get(CHAVE_FONTE_NAO_LIDA, ()))
    return motivos


def ler_json(caminho: str) -> dict:
    try:
        with open(os.path.expanduser(caminho), encoding="utf-8") as f:
            dado = json.load(f)
    except OSError as exc:
        return nao_lida(caminho, type(exc).__name__)
    except ValueError:
        return nao_lida(caminho, "JSON invalido")
    if not isinstance(dado, dict):
        return nao_lida(caminho, f"topo {type(dado).__name__}, nao objeto")
    return dado


def ler_toml(caminho: str) -> dict:
    try:
        with open(os.path.expanduser(caminho), "rb") as f:
            return tomllib.load(f)
    except OSError as exc:
        return nao_lida(caminho, type(exc).__name__)
    except ValueError:
        return nao_lida(caminho, "TOML invalido")


def ler_jsons_do_diretorio(caminho: str) -> dict:
    """Todo JSON de TOPO de um diretorio de config, sob a chave do arquivo.

    Diretorio ausente ou ilegivel devolve o marcador de fonte NAO LIDA
    (achado N2). Diretorio lido e SEM nenhum JSON devolve `{}` — este
    sim por MEDICAO do disco. Cada arquivo entra sob o proprio nome, de
    modo que o `alvo` da violacao nomeie o arquivo que a carrega
    (`user-settings.json.auto_topup`), e o arquivo que nao pode ser lido
    carregue o marcador sob a propria chave.

    Le o DIRETORIO em vez de um nome de arquivo fixo de proposito: um
    nome fixo seria invencao — nenhuma evidencia do acervo diz como o
    arquivo do grok se chama —, enquanto o diretorio foi observado.
    """
    base = os.path.expanduser(caminho)
    try:
        nomes = sorted(n for n in os.listdir(base) if n.endswith(".json"))
    except OSError as exc:
        return nao_lida(caminho, type(exc).__name__)
    return {n: ler_json(os.path.join(base, n)) for n in nomes}


def config_persistida(provider_id: str) -> dict:
    """Config/auth persistida, parseada em MEMORIA (valores nunca gravados).

    CODEX (achado 14 da P1-A.3.5, encontrado ao EXERCER o leitor). O
    ramo do codex era uma ALLOWLIST de duas chaves — `auth_mode` e
    `OPENAI_API_KEY` —, enquanto a justificativa escrita ao lado dela
    fala de UMA exclusao: os campos `tokens.*`, que SAO a credencial
    OAuth do ChatGPT e nao chave de API (escopo ratificado na auditoria
    P1-A, 02_auditoria-economica §2); audita-los acusaria PAYG em toda
    estacao logada. A allowlist excluia muito mais do que a sua propria
    razao pedia: `auto_topup`, `api_key` ou um endpoint escritos em
    `auth.json` ficavam INVISIVEIS a `auditar_config`. Denylist da
    subarvore `tokens` implementa a razao declarada com exatidao.

    GROK (MAJOR #1). `preflight_capsula` devolvia `{}` INCONDICIONAL,
    com o fundamento "nenhuma config parseavel localizada na P1-A". Duas
    medicoes o desfazem: a coleta da P1-A auditou config de TRES
    provedores apenas, de modo que "nao localizada" descrevia o que NAO
    foi procurado; e `~/.grok/` existe, com o estado do grok em SQLite.
    LIMITE DECLARADO: config em SQLite, ou fora de `~/.grok/`, nao e
    alcancada por esta leitura.
    """
    fonte = FONTES.get(provider_id)
    if fonte is None:
        return {}  # provider fora da frota declarada
    tipo, caminho = fonte
    if tipo == "toml":
        return ler_toml(caminho)
    if tipo == "dir-json":
        return ler_jsons_do_diretorio(caminho)
    if provider_id == "codex":
        auth = ler_json(caminho)
        toml = ler_toml("~/.codex/config.toml")
        cfg = {k: v for k, v in auth.items()
               if k not in ("tokens", CHAVE_FONTE_NAO_LIDA)}
        cfg.update({k: v for k, v in toml.items()
                    if k != CHAVE_FONTE_NAO_LIDA})
        # As DUAS fontes do codex sao somadas, e os marcadores das duas
        # tambem: sem esta juncao, um `update` faria a segunda fonte
        # apagar o marcador da primeira e uma delas sumiria da auditoria.
        motivos = _juntar_nao_lidas(auth, toml)
        if motivos:
            cfg[CHAVE_FONTE_NAO_LIDA] = motivos
        return cfg
    return ler_json(caminho)
