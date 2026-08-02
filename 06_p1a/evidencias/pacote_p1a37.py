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

EXCLUSOES, todas declaradas e nenhuma silenciosa:
  1. o diff cobre os `.py` que EXISTEM em BASE; os `.py` novos entrariam
     ali como a propria integra com prefixo `+`, e por isso entram
     inteiros, uma vez, na secao de conteudo completo;
  2. registro (`.md`) e evidencia (`.json`) alterados entram SOMENTE
     como SHA-256 do blob em ALVO;
  3. arquivo REMOVIDO entre BASE e ALVO entra como linha de remocao, com
     o SHA-256 que ele tinha em BASE — sumir seria omissao;
  4. nao entram timestamp, UUID, caminho absoluto, credencial nem lock;
  5. usuario local (forma longa e 8.3) e prefixo de caminho local sao
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

EXTENSOES_HASHEADAS = (".md", ".json", ".txt")


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
    py_modificados = [r for r in classes["modificados"] if r.endswith(".py")]
    py_novos = [r for r in classes["novos"] if r.endswith(".py")]
    hasheados = [(r, alvo) for r in classes["modificados"] + classes["novos"]
                 if r.endswith(EXTENSOES_HASHEADAS)]
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
        "=== EXCLUSOES DECLARADAS ===",
        "1. diff so dos .py que existem em BASE; .py novos entram "
        "inteiros na secao de conteudo completo, uma unica vez;",
        "2. .md/.json/.txt alterados ou novos entram SOMENTE como "
        "SHA-256 do blob em ALVO;",
        "3. arquivo removido entra como linha de remocao com o SHA-256 "
        "que tinha em BASE;",
        "4. usuario local (forma longa e 8.3) e prefixo de caminho local "
        "sao redigidos.\n",
        f"=== DIFF DOS .PY MODIFICADOS ({len(py_modificados)}) ===",
    ]
    if py_modificados:
        partes.append(_git("diff", base, alvo, "--", *py_modificados))
    else:
        partes.append("(nenhum .py modificado entre BASE e ALVO)\n")

    partes.append(f"=== CONTEUDO COMPLETO DOS .PY NOVOS ({len(py_novos)}) ===")
    for rel in py_novos:
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
