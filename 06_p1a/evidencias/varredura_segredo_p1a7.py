#!/usr/bin/env python3
"""Varredura de segredo do repositorio SSC+ — P1-A.7, ordem 6.

Este repositorio NUNCA foi varrido por detector de credencial. O que
existia — `contencao.redigir` — redige PII (usuario, caminho local) e
NAO procura chave, token ou senha; e o gerador de pacote so olha
`.py/.md/.json/.txt`. Antes do primeiro push para um remoto publico, a
pergunta *"ha credencial no historico?"* nunca havia sido feita.

DUAS PASSAGENS, e a diferenca entre elas e a medida:

- **(a) do PORTAO** — reproduz as limitacoes do que o repositorio ja
  tinha: so as quatro extensoes versionaveis, bloco cercado de markdown
  pulado, `backups/` ignorado, palavra-chave so em ingles, nome de
  arquivo nao consultado, e SOMENTE a arvore de HEAD.
- **(b) CRUA** — todo objeto do banco de objetos do Git (alcancavel ou
  nao), mais toda a arvore de trabalho INCLUSIVE o que o `.gitignore`
  esconde (`saidas/`, `labs/`, `backups/`, `locks/`). Sem filtro de
  extensao, sem pular bloco cercado, binarios lidos byte a byte
  (`latin-1`, que e bijetora em byte), palavra-chave tambem em
  portugues, e nome de arquivo como regra propria.

A passagem (a) NAO existe para achar: existe para MEDIR O QUE O PORTAO
NAO VE. O veredito sai da (b).

O script nao classifica fixture nem absolve nada: ele mede e nomeia.
A separacao fixture/credencial-real e do relatorio, item a item.
"""

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXTENSOES_DO_PORTAO = (".py", ".md", ".json", ".txt")
DIRS_IGNORADOS_PELO_PORTAO = ("backups/", "_backups/")

# ---------------------------------------------------------------------
# REGRAS. Cada uma tem nome, alvo declarado e se o portao a possui.
# `so_crua=True` marca exatamente as cegueiras que o despacho nomeia.
# ---------------------------------------------------------------------

REGRAS = [
    # --- provedores, forma literal do token ---
    ("anthropic_sk_ant", rb"sk-ant-[A-Za-z0-9_\-]{20,}", False),
    ("openai_sk", rb"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9]{20,}\b", False),
    ("openrouter_sk_or", rb"\bsk-or-v1-[A-Za-z0-9]{32,}", False),
    ("deepseek_moonshot_sk", rb"\bsk-[a-zA-Z0-9]{32}\b", False),
    # `sk-` seguido de HIFEN no miolo. A forma acima, so-alfanumerica,
    # nao casa `sk-teste-payg-nao-usar-123456` nem `sk-proj-...-...`:
    # medido em `05_p0/tests/test_frota.py:59` e
    # `06_p1a/tests/test_preflight.py:36`, que a primeira rodada desta
    # varredura NAO viu. A regra do proprio acervo
    # (`test_isolamento.py:33`) ja era mais forte que a minha.
    ("sk_com_hifen", rb"\bsk-[A-Za-z0-9_\-]{16,}", False),
    ("xai_com_hifen", rb"\bxai-[A-Za-z0-9_\-]{16,}", False),
    ("ghp_generico", rb"\bghp_[A-Za-z0-9_\-]{16,}", False),
    ("aiza_generico", rb"\bAIza[A-Za-z0-9_\-]{16,}", False),
    ("aws_access_key_id", rb"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA|ABIA|ACCA)[A-Z0-9]{16}\b", False),
    ("aws_secret_access_key", rb"(?i)aws_secret_access_key\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{40}", False),
    ("github_token", rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b", False),
    ("github_pat_fino", rb"\bgithub_pat_[A-Za-z0-9_]{60,}", False),
    ("google_api_key", rb"\bAIza[0-9A-Za-z_\-]{35}\b", False),
    ("slack_token", rb"\bxox[baprse]-[A-Za-z0-9\-]{10,}", False),
    ("stripe_key", rb"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}", False),
    ("groq_gsk", rb"\bgsk_[A-Za-z0-9]{40,}", False),
    ("huggingface_hf", rb"\bhf_[A-Za-z0-9]{30,}", False),
    ("xai_key", rb"\bxai-[A-Za-z0-9]{40,}", False),
    ("npm_token", rb"\bnpm_[A-Za-z0-9]{36}\b", False),
    ("pypi_token", rb"\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{20,}", False),
    ("telegram_bot", rb"\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b", False),
    ("azure_storage", rb"(?i)AccountKey\s*=\s*[A-Za-z0-9+/=]{40,}", False),
    # --- material de chave ---
    ("bloco_chave_privada", rb"-----BEGIN [A-Z ]{0,32}PRIVATE KEY-----", False),
    ("ssh_rsa_publica_longa", rb"ssh-rsa AAAA[0-9A-Za-z+/]{100,}", False),
    ("jwt_tres_partes", rb"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{8,}", False),
    # --- transporte ---
    ("url_com_senha", rb"[a-zA-Z][a-zA-Z0-9+.\-]{1,20}://[^/\s:@\"']{1,64}:[^/\s:@\"']{1,64}@", False),
    ("bearer_literal", rb"(?i)bearer\s+[A-Za-z0-9_\-\.=]{20,}", False),
    ("header_authorization", rb"(?i)[\"']?authorization[\"']?\s*[:=]\s*[\"'][^\"']{16,}[\"']", False),
    # --- atribuicao por palavra-chave ---
    ("atribuicao_en", rb"(?i)\b(?:api[_-]?key|apikey|secret|token|password|passwd|pwd|credential|access[_-]?key|private[_-]?key|client[_-]?secret)\b\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']", False),
    ("env_maiusculo", rb"(?m)^[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)[A-Z0-9_]*=[^\s\"']{12,}$", False),
    # --- CEGUEIRAS DECLARADAS: so a passagem crua as tem ---
    ("atribuicao_pt", rb"(?i)\b(?:chave|senha|segredo|credencial|token|chave[_-]?api|chave[_-]?secreta)\b\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']", True),
]

# Nome de arquivo como regra propria — cegueira do portao.
RX_NOME_SUSPEITO = re.compile(
    r"(?i)(^|/)(\.env(\.|$)|.*\.(pem|key|p12|pfx|jks|keystore|ppk|asc|gpg)$"
    r"|id_rsa|id_ed25519|\.netrc|_netrc|\.npmrc|\.pypirc|\.pgpass"
    r"|chave_selo\.bin|credentials?(\.|$)|secrets?\.(json|ya?ml|txt)$"
    r"|.*\.secret\.json$|.*\.local\.json$)"
)

REGRAS_COMPILADAS = [(nome, re.compile(rx), so_crua) for nome, rx, so_crua in REGRAS]

# Hex puro de 32/40/64 e o formato dos hashes que este acervo produz aos
# milhares. Nao se descarta: separa-se, com o contexto de 60 bytes a
# esquerda, para que a leitura decida. Ver secao "hex_sem_contexto".
RX_HEX_LONGO = re.compile(rb"\b[0-9a-f]{32,128}\b")
RX_CONTEXTO_DE_HASH = re.compile(
    rb"(?i)(sha256|sha-256|sha1|sha|hash|blob|commit|tree|digest|fingerprint|"
    rb"sum|checksum|md5|oid|selo|ancora|ancoragem|id)"
)
RX_B64_LONGO = re.compile(rb"\b[A-Za-z0-9+/]{40,}={0,2}\b")

RX_CERCA = re.compile(rb"(?m)^\s*```")


def entropia(dados: bytes) -> float:
    if not dados:
        return 0.0
    c = Counter(dados)
    n = len(dados)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def sem_blocos_cercados(conteudo: bytes) -> bytes:
    """Remove o miolo de todo bloco cercado — a cegueira do portao."""
    partes = RX_CERCA.split(conteudo)
    saida, dentro = [], False
    for i, p in enumerate(partes):
        if i == 0:
            saida.append(p)
            continue
        dentro = not dentro
        if not dentro:
            saida.append(p)
    return b"".join(saida)


def _linha_de(conteudo: bytes, pos: int) -> int:
    return conteudo.count(b"\n", 0, pos) + 1


def _amostra(conteudo: bytes, ini: int, fim: int, folga: int = 40) -> str:
    a = max(0, ini - folga)
    b = min(len(conteudo), fim + folga)
    return conteudo[a:b].decode("latin-1").replace("\n", "\\n")


def varrer(conteudo: bytes, origem: str, crua: bool) -> list:
    """Aplica as regras a UM conteudo. `crua=False` = regras do portao."""
    achados = []
    for nome, rx, so_crua in REGRAS_COMPILADAS:
        if so_crua and not crua:
            continue
        for m in rx.finditer(conteudo):
            achados.append({
                "regra": nome,
                "origem": origem,
                "linha": _linha_de(conteudo, m.start()),
                "casado": m.group(0).decode("latin-1")[:200],
                "contexto": _amostra(conteudo, m.start(), m.end()),
            })
    if crua:
        for m in RX_HEX_LONGO.finditer(conteudo):
            esq = conteudo[max(0, m.start() - 60):m.start()]
            if RX_CONTEXTO_DE_HASH.search(esq):
                continue
            achados.append({
                "regra": "hex_sem_contexto",
                "origem": origem,
                "linha": _linha_de(conteudo, m.start()),
                "casado": m.group(0).decode("latin-1"),
                "contexto": _amostra(conteudo, m.start(), m.end(), 60),
            })
        for m in RX_B64_LONGO.finditer(conteudo):
            bruto = m.group(0)
            if re.fullmatch(rb"[0-9a-fA-F]+", bruto):
                continue
            e = entropia(bruto)
            if e < 4.5:
                continue
            achados.append({
                "regra": "entropia_alta_b64",
                "origem": origem,
                "linha": _linha_de(conteudo, m.start()),
                "casado": bruto.decode("latin-1")[:120],
                "entropia": round(e, 3),
                "contexto": _amostra(conteudo, m.start(), m.end(), 50),
            })
    return achados


def git(*args) -> bytes:
    return subprocess.run(("git",) + args, cwd=RAIZ, check=True,
                          stdout=subprocess.PIPE).stdout


def caminhos_por_blob() -> dict:
    """blob -> conjunto de caminhos onde ele ja apareceu, em TODA a historia."""
    saida = {}
    dados = git("rev-list", "--objects", "--all", "--reflog").decode("latin-1")
    for linha in dados.splitlines():
        if " " not in linha:
            continue
        oid, caminho = linha.split(" ", 1)
        saida.setdefault(oid, set()).add(caminho)
    return saida


def todos_os_blobs() -> list:
    dados = git("cat-file", "--batch-all-objects",
                "--batch-check=%(objecttype) %(objectname) %(objectsize)"
                ).decode("ascii")
    return [(p[1], int(p[2])) for p in (l.split() for l in dados.splitlines())
            if p and p[0] == "blob"]


def conteudo_do_blob(oid: str) -> bytes:
    return subprocess.run(("git", "cat-file", "blob", oid), cwd=RAIZ,
                          check=True, stdout=subprocess.PIPE).stdout


def arquivos_da_arvore_de_trabalho() -> list:
    """TUDO sob a raiz, inclusive ignorado — menos o proprio `.git/`."""
    saida = []
    for base, dirs, arquivos in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d != ".git"]
        for a in arquivos:
            p = os.path.join(base, a)
            rel = os.path.relpath(p, RAIZ).replace(os.sep, "/")
            saida.append((rel, p))
    return sorted(saida)


def passagem_do_portao() -> dict:
    """(a) — arvore de HEAD, filtros e cegueiras do portao preservados."""
    achados, lidos, pulados_ext, pulados_dir = [], 0, 0, 0
    rastreados = git("ls-files").decode("latin-1").splitlines()
    for rel in rastreados:
        if any(d in rel for d in DIRS_IGNORADOS_PELO_PORTAO):
            pulados_dir += 1
            continue
        if not rel.endswith(EXTENSOES_DO_PORTAO):
            pulados_ext += 1
            continue
        p = os.path.join(RAIZ, rel)
        if not os.path.isfile(p):
            continue
        with open(p, "rb") as f:
            conteudo = f.read()
        if rel.endswith(".md"):
            conteudo = sem_blocos_cercados(conteudo)
        lidos += 1
        achados.extend(varrer(conteudo, f"arvore:{rel}", crua=False))
    return {
        "arquivos_rastreados": len(rastreados),
        "arquivos_lidos": lidos,
        "pulados_por_extensao": pulados_ext,
        "pulados_por_diretorio": pulados_dir,
        "achados": achados,
    }


def passagem_crua() -> dict:
    """(b) — todo o banco de objetos + toda a arvore, sem filtro nenhum."""
    mapa = caminhos_por_blob()
    blobs = todos_os_blobs()
    achados, bytes_lidos = [], 0
    for oid, tam in blobs:
        conteudo = conteudo_do_blob(oid)
        bytes_lidos += len(conteudo)
        caminhos = sorted(mapa.get(oid, ()))
        rotulo = caminhos[0] if caminhos else "<inalcancavel>"
        achados.extend(varrer(conteudo, f"blob:{oid[:12]}:{rotulo}", crua=True))

    arquivos = arquivos_da_arvore_de_trabalho()
    nomes = [rel for rel, _ in arquivos if RX_NOME_SUSPEITO.search("/" + rel)]
    for rel, p in arquivos:
        try:
            with open(p, "rb") as f:
                conteudo = f.read()
        except OSError:
            continue
        bytes_lidos += len(conteudo)
        achados.extend(varrer(conteudo, f"disco:{rel}", crua=True))

    inalcancaveis = [oid for oid, _ in blobs if oid not in mapa]
    return {
        "blobs_no_banco": len(blobs),
        "blobs_inalcancaveis": len(inalcancaveis),
        "arquivos_em_disco": len(arquivos),
        "bytes_lidos": bytes_lidos,
        "nomes_de_arquivo_suspeitos": nomes,
        "achados": achados,
    }


def peso() -> dict:
    """O que viaja no push, e o que ja pesa na arvore."""
    rastreados = git("ls-files").decode("latin-1").splitlines()
    total = 0
    maiores = []
    for linha in git("ls-tree", "-r", "-l", "HEAD").decode("latin-1").splitlines():
        partes = linha.split(None, 4)
        if len(partes) < 5 or partes[3] == "-":
            continue
        tam = int(partes[3])
        total += tam
        maiores.append((tam, partes[4].strip()))
    maiores.sort(reverse=True)

    blobs = todos_os_blobs()
    historia = sum(t for _, t in blobs)

    return {
        "arquivos_rastreados_em_head": len(rastreados),
        "bytes_da_arvore_head": total,
        "mb_da_arvore_head": round(total / 1048576, 3),
        "blobs_em_toda_a_historia": len(blobs),
        "bytes_somados_dos_blobs_descompactados": historia,
        "mb_somados_dos_blobs_descompactados": round(historia / 1048576, 3),
        "vinte_maiores_em_head": [
            {"bytes": t, "caminho": c} for t, c in maiores[:20]
        ],
    }


def carga_do_push() -> dict:
    """A medida DECISIVA: varre exatamente o que o push envia.

    `git bundle create --all` empacota os objetos alcancaveis a partir
    das refs — o mesmo conjunto que `git push` transmite. Clonar o bundle
    produz um repositorio cujo banco de objetos E a carga do push, sem
    inalcancavel nenhum. Varrer ESSE clone responde a pergunta que
    importa, que nao e *"ha segredo no disco?"* e sim *"ha segredo no que
    viaja?"*.
    """
    global RAIZ
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="ssc-carga-push-")
    try:
        bundle = os.path.join(tmp, "carga.bundle")
        subprocess.run(("git", "bundle", "create", bundle, "--all"),
                       cwd=RAIZ, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clone = os.path.join(tmp, "clone")
        subprocess.run(("git", "clone", "-q", bundle, clone), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raiz_real = RAIZ
        try:
            RAIZ = clone
            varrido = passagem_crua()
        finally:
            RAIZ = raiz_real
        varrido["bytes_do_bundle"] = os.path.getsize(bundle)
        varrido["mb_do_bundle"] = round(os.path.getsize(bundle) / 1048576, 3)
        varrido["achados"] = [a for a in varrido["achados"]]
        return varrido
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    resultado = {
        "missao": "P1-A.7 ordem 6 — varredura de segredo antes do push",
        "raiz": "<RAIZ-DO-REPOSITORIO>",
        "head": git("rev-parse", "HEAD").decode().strip(),
        "commits": int(git("rev-list", "--count", "--all").decode().strip()),
        "regras": [
            {"nome": n, "so_na_crua": s} for n, _, s in REGRAS
        ] + [
            {"nome": "nome_de_arquivo", "so_na_crua": True},
            {"nome": "hex_sem_contexto", "so_na_crua": True},
            {"nome": "entropia_alta_b64", "so_na_crua": True},
        ],
        "passagem_a_portao": passagem_do_portao(),
        "passagem_b_crua": passagem_crua(),
        "carga_do_push": carga_do_push(),
        "peso": peso(),
    }
    for chave in ("passagem_a_portao", "passagem_b_crua", "carga_do_push"):
        c = Counter(a["regra"] for a in resultado[chave]["achados"])
        resultado[chave]["por_regra"] = dict(sorted(c.items()))
        resultado[chave]["total_de_achados"] = len(resultado[chave]["achados"])

    # PESO DA PROPRIA EVIDENCIA. O dump integral deu 1.510.735 bytes —
    # sozinho, quase o dobro do que o push inteiro transmite (1.600.613).
    # Versiona-lo seria repetir o log de tunel do nxtrack: peso rastreado
    # viaja para sempre. `--reduzido` COLAPSA `hex_sem_contexto` em
    # contagem por origem e por tamanho, e preserva INTEGRALMENTE todo o
    # resto. O que se larga esta nomeado aqui e regenera-se rodando este
    # mesmo script sem a flag, sobre o mesmo estado da arvore.
    if "--reduzido" in sys.argv:
        for chave in ("passagem_a_portao", "passagem_b_crua", "carga_do_push"):
            bloco = resultado[chave]
            hexes = [a for a in bloco["achados"] if a["regra"] == "hex_sem_contexto"]
            bloco["achados"] = [a for a in bloco["achados"]
                                if a["regra"] != "hex_sem_contexto"]
            por_origem = Counter(a["origem"].split(":", 2)[-1] for a in hexes)
            bloco["hex_sem_contexto_colapsado"] = {
                "total": len(hexes),
                "valores_distintos": len({a["casado"] for a in hexes}),
                "por_tamanho": dict(sorted(
                    Counter(len(a["casado"]) for a in hexes).items())),
                "por_origem": dict(por_origem.most_common()),
                "o_que_se_largou": "linha, valor e contexto de cada casamento "
                                   "de `hex_sem_contexto`; preservados o total, "
                                   "o numero de valores distintos, a "
                                   "distribuicao por tamanho e a contagem por "
                                   "arquivo de origem",
            }

    saida = json.dumps(resultado, ensure_ascii=False, indent=2)
    destino = sys.argv[1] if len(sys.argv) > 1 else None
    if destino == "--reduzido":
        destino = sys.argv[2] if len(sys.argv) > 2 else None
    if destino:
        with open(destino, "w", encoding="utf-8") as f:
            f.write(saida)
        print(f"gravado: {destino}")
        print(f"sha256 do json: {hashlib.sha256(saida.encode('utf-8')).hexdigest()}")
    else:
        print(saida)
    for chave in ("passagem_a_portao", "passagem_b_crua", "carga_do_push"):
        print(f"{chave}: {resultado[chave]['total_de_achados']} achados "
              f"{resultado[chave]['por_regra']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
