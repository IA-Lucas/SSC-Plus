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
campo. Fonte ausente, ilegivel ou vazia devolve `{}` — sempre por
medicao do disco, jamais por cegueira escrita no fonte.
"""

import json
import os
import tomllib

# Fontes reais por provedor, medidas na P1-A e na P1-A.3.5. Lista
# explicita: um provedor sem fonte declarada nao vira `{}` silencioso.
FONTES = {
    "codex": ("json", "~/.codex/auth.json"),
    "claude": ("json", "~/.claude/settings.json"),
    "kimi": ("toml", "~/.kimi-code/config.toml"),
    "google": ("json", "~/.gemini/settings.json"),
    "grok": ("dir-json", "~/.grok"),
}


def ler_json(caminho: str) -> dict:
    try:
        with open(os.path.expanduser(caminho), encoding="utf-8") as f:
            dado = json.load(f)
        return dado if isinstance(dado, dict) else {}
    except (OSError, ValueError):
        return {}


def ler_toml(caminho: str) -> dict:
    try:
        with open(os.path.expanduser(caminho), "rb") as f:
            return tomllib.load(f)
    except (OSError, ValueError):
        return {}


def ler_jsons_do_diretorio(caminho: str) -> dict:
    """Todo JSON de TOPO de um diretorio de config, sob a chave do arquivo.

    Diretorio ausente, ilegivel ou sem JSON devolve `{}` — porem por
    MEDICAO do disco, nunca por cegueira escrita no fonte. Cada arquivo
    entra sob o proprio nome, de modo que o `alvo` da violacao nomeie o
    arquivo que a carrega (`user-settings.json.auto_topup`).

    Le o DIRETORIO em vez de um nome de arquivo fixo de proposito: um
    nome fixo seria invencao — nenhuma evidencia do acervo diz como o
    arquivo do grok se chama —, enquanto o diretorio foi observado.
    """
    base = os.path.expanduser(caminho)
    try:
        nomes = sorted(n for n in os.listdir(base) if n.endswith(".json"))
    except OSError:
        return {}
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
        cfg = {k: v for k, v in auth.items() if k != "tokens"}
        cfg.update(ler_toml("~/.codex/config.toml"))
        return cfg
    return ler_json(caminho)
