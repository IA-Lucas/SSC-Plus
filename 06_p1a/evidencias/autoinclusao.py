"""Auto-inclusao do gerador no pacote de revisao — SSC+ P1-A.3.7.

MAJOR #5 e achado N6, que sao o mesmo objeto visto de dois lados. O
pacote da P1-A.3.6 mandava o revisor julgar a construcao do gerador —
*"O gerador DESTE pacote herda a mesma construcao — julgue-a tambem"* —
e **nao incluia o codigo do gerador**. O proprio revisor levantou o
ponto, e o registro da missao o aceitou por inteiro: pedir julgamento
sobre um artefato ausente e defeito de composicao.

O remedio especificado no §9.4 tem a forma de um OU exclusivo:

    o gerador embute o PROPRIO codigo-fonte (lido do disco, com o
    SHA-256 do arquivo declarado ao lado), OU o pacote deixa de pedir
    julgamento sobre ele. As duas coisas juntas — pedir o julgamento e
    omitir o objeto — e o defeito.

Este modulo implementa as duas metades e a conferencia entre elas:
`secao_do_gerador` produz o bloco; `conferir` PARA a montagem quando o
pacote pede o julgamento e nao carrega o objeto.

POR QUE LIDO DO DISCO, e nao do commit. O objeto sob julgamento e o
gerador que ESTA RODANDO, nao a sua versao versionada — se as duas
divergirem, e a de disco que produziu o pacote. Consequencia declarada:
o hash do pacote passa a ser funcao dos commits **e** do fonte do
gerador. Isto NAO afrouxa a ancoragem do MAJOR #5: o conteudo julgado
continua vindo de `git cat-file blob <ALVO>:<path>`; o que vem do disco
e apenas o gerador, que e o unico artefato que o commit nao pode conter
enquanto ele ainda esta sendo escrito.
"""

import hashlib
import os
import re

__all__ = ["ROTULO_SECAO", "conferir", "contem_o_gerador",
           "pede_julgamento_do_gerador", "secao_do_gerador",
           "sha256_do_arquivo"]

ROTULO_SECAO = "=== GERADOR DESTE PACOTE (auto-incluido) ==="

# Uma linha PEDE julgamento sobre o gerador quando nomeia o gerador e
# manda julga-lo. A deteccao e por linha para nao casar um "julgue" de
# um paragrafo com um "gerador" de outro, tres paragrafos adiante.
_VERBOS_DE_JULGAMENTO = ("julgue", "julgar", "julga-", "avalie", "avaliar",
                         "revise", "revisar")
_RX_GERADOR = re.compile(r"\bgerador(?:es)?\b", re.IGNORECASE)


def sha256_do_arquivo(caminho) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def secao_do_gerador(caminho, redigir=None) -> str:
    """Bloco com o fonte INTEGRAL do gerador e o SHA-256 do arquivo.

    `redigir` e a redacao canonica; sem ela o bloco sai cru, o que so e
    aceitavel em teste. O SHA-256 e do arquivo em BYTES, antes da
    redacao — e assim que um terceiro o confere: `sha256sum` no arquivo
    que ele tem em maos, nao no texto redigido.
    """
    caminho = str(caminho)
    digest = sha256_do_arquivo(caminho)
    with open(caminho, encoding="utf-8") as f:
        fonte = f.read()
    if redigir is not None:
        fonte = redigir(fonte)
    return (f"{ROTULO_SECAO}\n"
            f"arquivo: {os.path.basename(caminho)}\n"
            f"sha256 (bytes do arquivo, ANTES da redacao): {digest}\n"
            "lido do DISCO, nao do commit: o objeto sob julgamento e o "
            "gerador que produziu este pacote.\n"
            "Confira com `sha256sum` sobre o arquivo do repositorio; se "
            "divergir, este pacote foi montado por outro codigo.\n\n"
            f"{fonte}\n")


def pede_julgamento_do_gerador(texto: str) -> bool:
    """O pacote manda o revisor julgar o gerador?"""
    for linha in (texto or "").splitlines():
        if not _RX_GERADOR.search(linha):
            continue
        if any(v in linha.lower() for v in _VERBOS_DE_JULGAMENTO):
            return True
    return False


def contem_o_gerador(texto: str, caminho) -> bool:
    """O pacote carrega o fonte do gerador E o SHA-256 do arquivo?

    As duas coisas: so o fonte deixaria o revisor sem como conferir que
    o arquivo do repositorio e o mesmo; so o hash seria pedir confianca.
    """
    texto = texto or ""
    if ROTULO_SECAO not in texto or sha256_do_arquivo(caminho) not in texto:
        return False
    with open(str(caminho), encoding="utf-8") as f:
        linhas = [ln for ln in f.read().splitlines() if ln.strip()]
    # Amostra do fonte, e nao o fonte inteiro: a secao passa por redacao,
    # de modo que uma comparacao integral falharia por construcao. A
    # amostra e de linhas nao vazias distribuidas pelo arquivo.
    amostra = [linhas[0], linhas[len(linhas) // 2], linhas[-1]]
    return all(linha in texto for linha in amostra)


def conferir(texto: str, caminho) -> None:
    """PARADA quando o pacote pede o julgamento e omite o objeto.

    Este e o defeito N6 na sua forma exata, e o portao existe para que
    ele nao possa ser reintroduzido por esquecimento: quem escrever um
    pedido de julgamento sobre o gerador e nao incluir o gerador nao
    consegue montar o pacote.
    """
    if pede_julgamento_do_gerador(texto) and not contem_o_gerador(
            texto, caminho):
        raise SystemExit(
            "PARADA: o pacote pede julgamento sobre o gerador e NAO "
            f"carrega o fonte de {os.path.basename(str(caminho))} com o "
            "seu SHA-256. Pedir julgamento sobre artefato ausente e o "
            "defeito N6 / MAJOR #5 — inclua a secao ou retire o pedido")
