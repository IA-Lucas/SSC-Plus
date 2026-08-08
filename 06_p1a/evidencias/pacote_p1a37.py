#!/usr/bin/env python3
"""Gerador deterministico de pacote de revisao — SSC+ P1-A.3.7.

CORRIGE O MAJOR #5 / N6, que o pacote da P1-A.3.6 deixou aberto: ele
mandava o revisor julgar a construcao do gerador e nao incluia o codigo
do gerador. Aqui o fonte deste arquivo entra no pacote com o seu SHA-256
ao lado (`autoinclusao.secao_do_gerador`), e a montagem PARA se o pacote
pedir o julgamento sem carregar o objeto (`autoinclusao.conferir`).

HERDA A ANCORAGEM (MAJOR #5, a metade que a P1-A.3.6 ja tinha certa):
todo conteudo julgado vem de `git cat-file blob <ALVO>:<caminho>` — o
banco de objetos, nunca a arvore de trabalho. Um checkout sujo, ou um
checkout de OUTRO commit, produz o mesmo pacote.

DUAS DIFERENCAS DELIBERADAS em relacao ao gerador da P1-A.3.6:

1. ALVO e BASE sao ARGUMENTOS, nao constantes no fonte. Constante no
   fonte obriga a editar o gerador a cada missao, e foi editando o
   gerador que a lista de arquivos e o alvo divergiram antes;
2. as listas de arquivos sao DERIVADAS de `git diff --name-status`, nao
   escritas a mao. A lista literal precisava de conferencia contra o
   banco de objetos para nao virar omissao silenciosa; derivada, ela nao
   pode divergir do diff que descreve.

O CRITERIO DE INCLUSAO — corrigido na P1-A.7, e ele NAO e mais uma
lista de extensao. Ate aqui o gerador perguntava *"a extensao esta em
`.py`/`.md`/`.json`/`.txt`?"* e, se a resposta fosse nao, o caminho
**sumia sem uma linha de aviso**. Foi assim que o `pytest.ini` — metade
da correcao da P1-A.5.1 — foi submetido a dois revisores sem estar no
pacote, e assim que o `06_p1a/.gitattributes`, que e o REMEDIO do
MAJOR #5, ficou fora do pacote da P1-A.4 que dizia prova-lo.

A pergunta passa a ser **o que o pacote precisa provar**, e ela se
responde em tres disposicoes que cobrem TODO caminho do diff:

  1. **LIDO** — o revisor precisa LER o arquivo para julgar se a
     correcao fecha o que diz fechar. E o caso do que EXECUTA ou do que
     alguma ferramenta CONSULTA para decidir comportamento: fonte
     (`.py`, `.sh`) e configuracao de mecanismo (`pytest.ini`,
     `conftest.py`, `.gitattributes`, `.gitignore`, `setup.cfg`,
     `pyproject.toml`, `tox.ini`, `.editorconfig`). Modificado entra
     como diff; novo entra inteiro, uma vez.
  2. **ANCORADO** — o revisor precisa ANCORAR o arquivo, nao le-lo
     inteiro: registro, evidencia, corpus, binario, e **toda extensao
     que este gerador nao conhece**. Entra como SHA-256 do blob (em
     ALVO; em BASE quando removido).
  3. **EXCLUIDO** — so existe se **NOMEADO** em `EXCLUSOES_NOMEADAS`,
     com motivo. Lista vazia hoje: nada e excluido.

**O DEFAULT E ANCORAR, NUNCA DESCARTAR.** Esta e a diferenca que
importa. A extensao deixou de ser o portao e passou a decidir apenas
*quanto* do arquivo o revisor ve; errar a classificacao custa detalhe,
e nunca mais silencio. Uma extensao que ninguem previu entra com o seu
hash em vez de evaporar.

**E a completude e EXERCIDA, nao afirmada** (`conferir_cobertura`): o
gerador PARA se sobrar um so caminho do `git diff --name-status` que
nao esteja numa das tres disposicoes. A docstring anterior AFIRMAVA
*"todas declaradas e nenhuma silenciosa"* enquanto o codigo descartava
em silencio — a familia do MAJOR #3, dentro do arquivo que o pacote
manda julgar.

O `=== MANIFESTO DE COBERTURA ===` imprime caminho a caminho a
disposicao e o motivo, para que o revisor confira a conta em vez de
acreditar nela.

O QUE CONTINUA VALENDO:
  - arquivo REMOVIDO entre BASE e ALVO entra como linha de remocao, com
    o SHA-256 que ele tinha em BASE — sumir seria omissao;
  - nao entram timestamp, UUID, caminho absoluto, credencial nem lock;
  - usuario local (forma longa e 8.3) e prefixo de caminho local sao
    redigidos.

O QUE ESTE GERADOR NAO FAZ: nao envia, nao invoca provedor e nao decide
quem revisa. Ele monta bytes num arquivo de saida, e nada mais.

Uso: python 06_p1a/evidencias/pacote_p1a37.py <BASE> <ALVO> <saida>
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from autoinclusao import conferir, secao_do_gerador  # noqa: E402
from contencao import redigir  # noqa: E402

# --------------------------------------------------------------------
# O CRITERIO, em codigo. Ver a secao "O CRITERIO DE INCLUSAO" no topo.
# --------------------------------------------------------------------

# Extensoes de coisa que EXECUTA.
_EXTENSOES_QUE_EXECUTAM = (".py", ".sh")

# Nomes de arquivo que alguma FERRAMENTA consulta para decidir
# comportamento. E nome, nao extensao, porque e assim que a ferramenta
# os procura: o pytest procura `pytest.ini`, o git procura
# `.gitattributes`. `pytest.ini` esta aqui por medicao, nao por
# simetria — a P1-A.6 julgou a correcao da P1-A.5.1 sem ele.
_CONFIGURACAO_DE_MECANISMO = frozenset((
    "pytest.ini", "conftest.py", ".gitattributes", ".gitignore",
    "setup.cfg", "pyproject.toml", "tox.ini", ".editorconfig",
))

# Exclusao so existe se NOMEADA, e com motivo. Vazia hoje: o gerador
# nao exclui nada. Quem acrescentar um item aqui esta declarando a
# exclusao no manifesto, que e exatamente o oposto de descartar em
# silencio.
EXCLUSOES_NOMEADAS: dict = {}


class CoberturaIncompleta(Exception):
    """Sobrou caminho do diff sem disposicao — o defeito da P1-A.7.

    Existe para ser LEVANTADA, nao para ser documentada: e ela que
    transforma a completude de afirmacao em exercicio.
    """


def disposicao(rel: str) -> tuple:
    """(disposicao, motivo) para UM caminho. Nunca devolve 'descartado'.

    O default e ANCORADO. Uma extensao desconhecida entra com o seu
    SHA-256; nenhuma entrada deste dicionario pode faze-la sumir.
    """
    if rel in EXCLUSOES_NOMEADAS:
        return "excluido", EXCLUSOES_NOMEADAS[rel]
    nome = rel.rsplit("/", 1)[-1]
    if nome in _CONFIGURACAO_DE_MECANISMO:
        return "lido", f"configuracao de mecanismo ({nome})"
    if rel.endswith(_EXTENSOES_QUE_EXECUTAM):
        return "lido", "fonte executavel"
    return "ancorado", "registro, evidencia ou extensao nao-executavel"


def conferir_cobertura(todos, lidos, ancorados, excluidos) -> None:
    """PARA se sobrar caminho sem disposicao.

    O portao que faltava. Ate a P1-A.7 o gerador AFIRMAVA na docstring
    que nenhuma exclusao era silenciosa, e descartava em silencio todo
    caminho fora de quatro extensoes.
    """
    cobertos = set(lidos) | set(ancorados) | set(excluidos)
    sobra = sorted(set(todos) - cobertos)
    if sobra:
        raise CoberturaIncompleta(
            "caminhos do diff sem disposicao — o pacote omitiria "
            f"{len(sobra)} arquivo(s) em silencio: {sobra}")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True).stdout


def _blob(commit: str, rel: str) -> bytes:
    """Bytes EXATOS do blob versionado — nunca o disco.

    Esta funcao e a ancoragem. `git cat-file blob` devolve o objeto cru,
    sem filtro de EOL e sem depender de `core.autocrlf`. Trocar por
    leitura de arquivo reintroduz o MAJOR #5.
    """
    return subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{rel}"], cwd=RAIZ,
        capture_output=True, check=True).stdout


def _classificar(base: str, alvo: str) -> dict:
    """`git diff --name-status` -> listas por classe, sem lista literal."""
    saida = _git("diff", "--name-status", "-z", base, alvo)
    campos = [c for c in saida.split("\0") if c]
    classes = {"modificados": [], "novos": [], "removidos": []}
    i = 0
    while i < len(campos) - 1:
        estado, rel = campos[i][:1], campos[i + 1]
        i += 2
        destino = {"A": "novos", "D": "removidos"}.get(estado, "modificados")
        classes[destino].append(rel)
    for chave in classes:
        classes[chave].sort()
    return classes


def montar_pacote(base: str, alvo: str) -> str:
    # Portao de identidade ANCORADO NOS COMMITS, nao no checkout.
    try:
        alvo = _git("rev-parse", f"{alvo}^{{commit}}").strip()
        base = _git("rev-parse", f"{base}^{{commit}}").strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"PARADA: commit alvo ou base ausente: {exc}") from exc
    if subprocess.run(["git", "merge-base", "--is-ancestor", base, alvo],
                      cwd=RAIZ).returncode != 0:
        raise SystemExit(f"PARADA: {base} nao e ancestral de {alvo}")

    classes = _classificar(base, alvo)

    # Toda decisao passa por `disposicao`; nenhum caminho cai fora dela.
    motivos = {}
    lidos_modificados, lidos_novos, ancorados_vivos, excluidos = [], [], [], []
    for rel in classes["modificados"] + classes["novos"]:
        disp, motivo = disposicao(rel)
        motivos[rel] = motivo
        novo = rel in classes["novos"]
        if disp == "excluido":
            excluidos.append(rel)
        elif disp == "lido":
            (lidos_novos if novo else lidos_modificados).append(rel)
        else:
            ancorados_vivos.append(rel)
    for rel in classes["removidos"]:
        motivos[rel] = "removido entre BASE e ALVO — hash do blob em BASE"

    # O portao: sobrou caminho sem disposicao? O pacote nao nasce.
    todos = (classes["modificados"] + classes["novos"]
             + classes["removidos"])
    conferir_cobertura(
        todos,
        lidos_modificados + lidos_novos,
        ancorados_vivos + classes["removidos"],
        excluidos)

    for lista in (lidos_modificados, lidos_novos, ancorados_vivos, excluidos):
        lista.sort()
    hasheados = [(r, alvo) for r in ancorados_vivos]
    hasheados += [(r, base) for r in classes["removidos"]]

    partes = [
        "PACOTE DE REVISAO — SSC+ (laboratorio experimental, sem "
        "autoridade)\n",
        "Quem corrigiu nao certifica: correcao nao fecha por ter sido "
        "feita, fecha por revisor independente dizer que fechou.\n",
        "=== IDENTIDADE (ancorada em commit, nao no checkout) ===",
        f"BASE:  {base}  {_git('log', '-1', '--format=%s', base).strip()}",
        f"ALVO:  {alvo}  {_git('log', '-1', '--format=%s', alvo).strip()}",
        f"tree de ALVO: {_git('rev-parse', f'{alvo}^{{tree}}').strip()}",
        f"commits entre BASE e ALVO: "
        f"{_git('rev-list', '--count', f'{base}..{alvo}').strip()}",
        "Todo conteudo abaixo vem de `git cat-file blob <commit>:<caminho>`."
        " A arvore de trabalho NAO e lida — exceto pelo fonte do gerador,"
        " que e o objeto sob julgamento e nao pode vir do commit.\n",
        secao_do_gerador(__file__, redigir),
        "=== CRITERIO DE INCLUSAO (nao e lista de extensao) ===",
        "LIDO     — o revisor precisa LER: fonte executavel e "
        "configuracao de mecanismo. Modificado entra como diff; novo, "
        "inteiro.",
        "ANCORADO — o revisor precisa ANCORAR: registro, evidencia e "
        "TODA extensao que o gerador nao conhece. Entra como SHA-256.",
        "EXCLUIDO — so se NOMEADO, com motivo. Nenhuma exclusao "
        "silenciosa: o gerador PARA se sobrar caminho sem disposicao.",
        "Removido entra como linha de remocao com o SHA-256 que tinha "
        "em BASE. Usuario local e prefixo de caminho local sao "
        "redigidos.\n",
        "=== MANIFESTO DE COBERTURA — todo caminho do diff, com motivo ===",
        f"caminhos no diff: {len(todos)}  =  lidos {len(lidos_modificados)}"
        f"+{len(lidos_novos)}  ancorados {len(ancorados_vivos)}  "
        f"removidos {len(classes['removidos'])}  "
        f"excluidos {len(excluidos)}",
    ]
    for rel in sorted(todos):
        if rel in classes["removidos"]:
            rotulo = "REMOVIDO"
        elif rel in excluidos:
            rotulo = "EXCLUIDO"
        elif rel in lidos_novos or rel in lidos_modificados:
            rotulo = "LIDO"
        else:
            rotulo = "ANCORADO"
        partes.append(f"  {rotulo:9s} {rel}  — {motivos[rel]}")
    partes.append("")

    partes.append(f"=== DIFF DOS LIDOS MODIFICADOS ({len(lidos_modificados)}) ===")
    if lidos_modificados:
        partes.append(_git("diff", base, alvo, "--", *lidos_modificados))
    else:
        partes.append("(nenhum arquivo lido foi modificado entre BASE e ALVO)\n")

    partes.append(
        f"=== CONTEUDO COMPLETO DOS LIDOS NOVOS ({len(lidos_novos)}) ===")
    for rel in lidos_novos:
        partes.append(f"--- {rel} ---")
        partes.append(_blob(alvo, rel).decode("utf-8", errors="replace"))

    partes.append(f"=== SHA-256 DE REGISTROS E EVIDENCIAS ({len(hasheados)}) ===")
    for rel, commit in sorted(hasheados):
        marca = "removido em ALVO, hash de BASE" if commit == base else ""
        digest = hashlib.sha256(_blob(commit, rel)).hexdigest()
        partes.append(f"{digest}  {rel}  {marca}".rstrip())

    partes.append(
        "\n=== O QUE SE PEDE AO REVISOR ===\n"
        "1. Cada correcao fecha o achado que diz fechar, ou so muda de "
        "forma?\n"
        "2. O teste de cada correcao exerce o caso que OCORRE em "
        "operacao, ou um vizinho dele?\n"
        "3. Ha defeito NOVO introduzido pelas correcoes?\n"
        "4. O gerador DESTE pacote esta incluido acima, com o seu "
        "SHA-256 — julgue-o tambem, e nao apenas o que ele produziu.\n"
        "Responda um achado por linha, prefixado por CRITICAL | MAJOR | "
        "MINOR | OBS, e termine com APROVADO | APROVADO-COM-RESSALVAS | "
        "REPROVADO.\n")
    return redigir("\n".join(partes))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print("uso: pacote_p1a37.py <BASE> <ALVO> <saida>", file=sys.stderr)
        return 2
    base, alvo, saida = argv
    texto = montar_pacote(base, alvo)
    # N6: pedir julgamento sobre o gerador e omiti-lo e o defeito. O
    # portao roda ANTES de a saida existir — pacote defeituoso nao chega
    # a virar arquivo.
    conferir(texto, __file__)
    dados = texto.encode("utf-8")
    with open(saida, "wb") as f:
        f.write(dados)
        f.flush()
        os.fsync(f.fileno())
    print(f"pacote: {saida}")
    print(f"sha256: {hashlib.sha256(dados).hexdigest()}")
    print(f"bytes:  {len(dados)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
