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
import shutil
import sqlite3
import tempfile
import tomllib

from preflight.economia import CHAVE_FONTE_NAO_LIDA

__all__ = ["CHAVE_FONTE_NAO_LIDA", "FONTES", "LIMITE_LINHAS_POR_TABELA",
           "config_persistida", "ler_config_do_diretorio", "ler_json",
           "ler_jsons_do_diretorio", "ler_sqlite", "ler_toml", "nao_lida"]

# Extensoes de banco SQLite observadas em `~/.grok/` nesta estacao
# (`grok.db`, mais `-shm`/`-wal`). As duas outras grafias correntes
# entram porque o acervo NAO tem evidencia de que o nome seja fixo — a
# mesma razao que fez o leitor do grok ler o DIRETORIO e nao um nome.
EXTENSOES_SQLITE = (".db", ".sqlite", ".sqlite3")

# Teto de linhas lidas por tabela. Excedente NAO e ignorado em silencio:
# marca a fonte como NAO LIDA (achado N2), porque tabela truncada e
# tabela parcialmente lida, e o que nao foi lido nao e limpo.
LIMITE_LINHAS_POR_TABELA = 20000

# Uma celula textual so e promovida a NOME de chave se couber na forma
# de um nome de configuracao: curta e sem espaco. Sem este limite, uma
# frase de conversa terminada em "api key" seria normalizada para
# `...apikey`, casaria `_nome_payg` e produziria violacao PERMANENTE —
# um guarda que reprova sempre, que e o oposto do que se quer.
LIMITE_NOME_DE_CHAVE = 64

# Fontes reais por provedor, medidas na P1-A e na P1-A.3.5. Lista
# explicita: um provedor sem fonte declarada nao vira `{}` silencioso.
FONTES = {
    "codex": ("json", "~/.codex/auth.json"),
    "claude": ("json", "~/.claude/settings.json"),
    "kimi": ("toml", "~/.kimi-code/config.toml"),
    "google": ("json", "~/.gemini/settings.json"),
    "grok": ("dir-config", "~/.grok"),
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


def _e_nome_de_chave(valor) -> bool:
    """Texto com forma de NOME de campo de configuracao."""
    return (isinstance(valor, str) and valor.strip()
            and len(valor) <= LIMITE_NOME_DE_CHAVE
            and not any(c.isspace() for c in valor))


def _linha_auditavel(colunas, valores) -> dict:
    """Uma linha de tabela na forma que `auditar_config` sabe auditar.

    Tres transformacoes, todas declaradas:

    1. BLOB vira texto UTF-8 com substituicao — sem isto, um endpoint ou
       uma chave gravados como blob ficariam fora da auditoria;
    2. celula textual que parseia como JSON entra TAMBEM parseada, sob
       `<coluna>#json`: config aninhada num campo de texto e a forma
       corrente de um CLI guardar settings dentro de um banco;
    3. celula textual com FORMA de nome de campo e promovida a NOME dos
       demais valores da linha. Numa tabela chave/valor — a forma
       corrente de persistir configuracao em SQLite — o nome do campo
       vive no DADO, nao no esquema; sem esta promocao, `auto_topup` na
       coluna `key` seria apenas mais um valor de string e nada o
       acusaria. A promocao nunca sobrescreve o nome de uma coluna real.
    """
    linha = {}
    for coluna, valor in zip(colunas, valores):
        if isinstance(valor, (bytes, bytearray, memoryview)):
            valor = bytes(valor).decode("utf-8", "replace")
        linha[str(coluna)] = valor
    embutidos = {}
    for coluna, valor in linha.items():
        if not isinstance(valor, str) or not valor.strip():
            continue
        try:
            dado = json.loads(valor)
        except ValueError:
            continue
        if isinstance(dado, (dict, list)):
            embutidos[f"{coluna}#json"] = dado
    promovidas = {}
    for valor in list(linha.values()):
        if not _e_nome_de_chave(valor) or valor in linha:
            continue
        promovidas[valor] = [outro for outro in linha.values()
                             if outro is not valor]
    linha.update(embutidos)
    linha.update(promovidas)
    return linha


def ler_sqlite(caminho: str) -> dict:
    """Todo o conteudo auditavel de um banco SQLite, tabela a tabela.

    MAJOR #1, a metade que faltava. O leitor do grok alcancava somente
    JSON de topo em `~/.grok/`, e o revisor mediu a consequencia: *"admite
    nao alcancar o SQLite observado; PAYG/auto-topup persistido nessa
    fonte ainda nao chega a auditoria"*. O estado do grok nesta estacao
    vive em `grok.db` (+ `-wal`/`-shm`), e era ali que a auditoria nao
    entrava.

    O arquivo VIVO nunca e aberto pelo sqlite3: `grok.db`, `-wal` e
    `-shm` sao copiados para um descartavel e o banco aberto e a COPIA.
    Abrir o vivo, mesmo em modo somente-leitura, faria o SQLite recuperar
    o WAL e escrever no `-shm` do usuario. Ler pela copia tambem evita o
    inverso — ignorar o WAL com `immutable=1` leria um estado velho e
    perderia justamente a config recem-gravada.

    LIMITES DECLARADOS: ate `LIMITE_LINHAS_POR_TABELA` linhas por tabela,
    e o excedente marca a fonte como NAO LIDA; blob nao textual sai como
    texto de substituicao e nao e auditavel; texto que embuta JSON e
    reparseado, mas outros formatos embutidos (YAML, base64) nao.
    """
    origem = os.path.expanduser(caminho)
    if not os.path.isfile(origem):
        return nao_lida(caminho, "FileNotFoundError")
    descartavel = tempfile.mkdtemp(prefix="ssc-leitor-sqlite-")
    saida, truncadas = {}, []
    try:
        destino = os.path.join(descartavel, os.path.basename(origem))
        for sufixo in ("", "-wal", "-shm"):
            if os.path.exists(origem + sufixo):
                shutil.copy2(origem + sufixo, destino + sufixo)
        conexao = sqlite3.connect(destino)
        try:
            conexao.text_factory = lambda b: b.decode("utf-8", "replace")
            tabelas = sorted(
                linha[0] for linha in conexao.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"))
            for tabela in tabelas:
                cursor = conexao.execute(f'SELECT * FROM "{tabela}"')
                colunas = [d[0] for d in cursor.description]
                linhas = cursor.fetchmany(LIMITE_LINHAS_POR_TABELA + 1)
                if len(linhas) > LIMITE_LINHAS_POR_TABELA:
                    truncadas.append(tabela)
                    linhas = linhas[:LIMITE_LINHAS_POR_TABELA]
                saida[tabela] = [_linha_auditavel(colunas, linha)
                                 for linha in linhas]
        finally:
            conexao.close()
    except (sqlite3.Error, OSError, ValueError) as exc:
        return nao_lida(caminho, type(exc).__name__)
    finally:
        shutil.rmtree(descartavel, ignore_errors=True)
    if truncadas:
        saida[CHAVE_FONTE_NAO_LIDA] = [
            f"{caminho}: tabela {t} acima de "
            f"{LIMITE_LINHAS_POR_TABELA} linhas" for t in truncadas]
    return saida


def ler_config_do_diretorio(caminho: str) -> dict:
    """JSON de topo E banco SQLite de um diretorio de config.

    Diretorio ausente ou ilegivel devolve o marcador de fonte NAO LIDA.
    Cada arquivo entra sob o proprio nome — `user-settings.json` e
    `grok.db` lado a lado —, de modo que o `alvo` da violacao diga qual
    arquivo a carrega.
    """
    base = os.path.expanduser(caminho)
    try:
        nomes = sorted(os.listdir(base))
    except OSError as exc:
        return nao_lida(caminho, type(exc).__name__)
    saida = {}
    for nome in nomes:
        completo = os.path.join(base, nome)
        if nome.endswith(".json"):
            saida[nome] = ler_json(completo)
        elif nome.endswith(EXTENSOES_SQLITE):
            saida[nome] = ler_sqlite(completo)
    return saida


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
    A P1-A.3.5 fechou a metade do JSON de topo e DECLAROU a outra aberta
    — *"config em SQLite nao e alcancada por esta leitura"* —, e foi
    exatamente por ela que o revisor independente manteve o MAJOR #1
    NAO-FECHADO. O SQLite passa a ser lido (`ler_sqlite`), pela COPIA do
    banco e dos seus `-wal`/`-shm`.
    LIMITE QUE PERMANECE DECLARADO: config do grok fora de `~/.grok/`
    nao e alcancada; dentro dele, so JSON de topo e bancos SQLite —
    outro formato de arquivo nao e lido nem marcado.
    """
    fonte = FONTES.get(provider_id)
    if fonte is None:
        return {}  # provider fora da frota declarada
    tipo, caminho = fonte
    if tipo == "toml":
        return ler_toml(caminho)
    if tipo == "dir-config":
        return ler_config_do_diretorio(caminho)
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
