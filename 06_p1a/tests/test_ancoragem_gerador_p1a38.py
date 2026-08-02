"""FASE 4 — a ancoragem do gerador auto-incluido, medida e presa.

O DEFEITO, achado ao EXECUTAR a prova de ancoragem que o ato exige e
nao ao ler o codigo.

`pacote_p1a37.py` embute o proprio fonte com o SHA-256 ao lado — e o
remedio do MAJOR #5 / N6, entregue na P1-A.3.7. O fonte e lido do
DISCO, por decisao declarada: *"o objeto sob julgamento e o gerador que
ESTA RODANDO"*. A consequencia tambem estava declarada: o hash do
pacote e funcao dos commits **e** do fonte do gerador.

O que NAO estava previsto e que "o fonte do gerador" deixasse de ser
funcao do commit. Medido nesta missao:

    geracao no repositorio de trabalho   sha256 c2505a41…  82110 bytes
    geracao em CHECKOUT LIMPO do commit  sha256 8f5efac7…  82110 bytes

Mesmo tamanho, uma unica linha diferente — a linha do SHA-256 do proprio
gerador. A causa, medida e nao suposta:

    blob no Git                 8277 bytes, 191 LF, 0 CRLF
    arquivo no checkout limpo   8468 bytes, 191 CRLF

O BLOB E IDENTICO nos dois repositorios (`892479a7…`). O que difere e o
que o `git checkout` escreve no disco: com `core.autocrlf=true` e sem
atributo, o arquivo e convertido para CRLF. O gerador entao hasheia
bytes que nao sao os do commit — e o pacote deixa de reproduzir.

O PRECEDENTE JA EXISTIA E NAO FOI ESTENDIDO. `06_p1a/.gitattributes`
marca `/evidencias/pacote_p1a31.py -text` e
`/evidencias/revisao_p1a31.py -text` exatamente por isto. O gerador novo
nasceu sem o atributo. E o mecanismo do achado 10 mais uma vez: a copia
que ninguem exercita fica para tras.

A CORRECAO e a linha que faltava — `/evidencias/pacote_p1a37.py -text`
—, e este arquivo e o guarda que impede o proximo gerador de nascer sem
ela.

O CASO QUE OCORRE, e por que o teste NAO compara disco com blob e para
por ai: nesta estacao os dois JA sao iguais (o arquivo nunca foi
reescrito por um checkout). Um teste que so comparasse bytes passaria
verde com o defeito vivo — foi assim que ele sobreviveu. O que este
teste exige e o ATRIBUTO, que e a propriedade que vale em toda estacao,
e a igualdade de bytes vem junto como segunda metade.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao provam que um `git checkout` real preserve os bytes: isso exigiria
  clonar dentro do teste, e a suite nao cria repositorio. A medicao do
  clone esta acima, feita a mao e registrada;
- nao cobrem outros geradores do acervo que nao se auto-incluem
  (`pacote_p1a31`, `pacote_p1a33`): eles ja tem o atributo por outro
  motivo, e os seus hashes estao publicados;
- nao se afirma que `-text` seja suficiente para toda forma de
  normalizacao (por exemplo, filtros `clean`/`smudge` configurados na
  estacao);
- nada aqui prova o conteudo do pacote — so a sua reprodutibilidade.
"""

import os
import subprocess
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ = os.path.dirname(_DIR_P1A)

# Geradores que embutem o PROPRIO fonte com o SHA-256 ao lado. Todo
# arquivo desta lista tem os seus bytes de disco hasheados dentro do
# pacote — e portanto precisa sair do checkout byte a byte igual ao blob.
AUTO_INCLUIDOS = ("06_p1a/evidencias/pacote_p1a37.py",)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_RAIZ, capture_output=True,
                          text=True, check=True).stdout


class GeradorAutoIncluidoEAncorado(unittest.TestCase):

    def test_todo_gerador_auto_incluido_esta_marcado_como_binario(self):
        # A propriedade que vale em TODA estacao: sem `-text` o checkout
        # converte EOL e o hash do gerador deixa de ser funcao do commit.
        for rel in AUTO_INCLUIDOS:
            with self.subTest(gerador=rel):
                saida = _git("check-attr", "text", "--", rel).strip()
                self.assertTrue(
                    saida.endswith("text: unset"),
                    f"{rel} precisa de `-text` em .gitattributes; "
                    f"check-attr devolveu {saida!r}")

    def test_os_bytes_de_disco_sao_os_bytes_do_blob(self):
        # A segunda metade: aqui e agora, disco e commit coincidem.
        for rel in AUTO_INCLUIDOS:
            with self.subTest(gerador=rel):
                blob = subprocess.run(
                    ["git", "cat-file", "blob", f"HEAD:{rel}"], cwd=_RAIZ,
                    capture_output=True, check=True).stdout
                with open(os.path.join(_RAIZ, rel), "rb") as f:
                    disco = f.read()
                self.assertEqual(len(disco), len(blob))
                self.assertEqual(disco, blob)

    def test_o_gerador_realmente_se_auto_inclui(self):
        # Guarda contra lista vazia de significado: se o gerador deixar
        # de se auto-incluir, esta lista nao descreve mais nada e os dois
        # testes acima viram cerimonia.
        import sys
        sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))
        from autoinclusao import ROTULO_SECAO
        for rel in AUTO_INCLUIDOS:
            with self.subTest(gerador=rel):
                with open(os.path.join(_RAIZ, rel), encoding="utf-8") as f:
                    fonte = f.read()
                self.assertIn("secao_do_gerador", fonte)
                self.assertTrue(ROTULO_SECAO)

    def test_o_precedente_do_acervo_continua_valendo(self):
        # Contraprova de que o teste mede o atributo certo: os dois
        # arquivos que JA tinham `-text` continuam tendo. Se
        # `check-attr` mudasse de formato, isto reprovaria junto.
        for rel in ("06_p1a/evidencias/pacote_p1a31.py",
                    "06_p1a/evidencias/revisao_p1a31.py"):
            with self.subTest(arquivo=rel):
                self.assertTrue(
                    _git("check-attr", "text", "--", rel).strip().endswith(
                        "text: unset"))

    def test_um_arquivo_sem_o_atributo_e_visivelmente_diferente(self):
        # Contraprova do outro lado: o teste nao passa para tudo. Um
        # `.py` qualquer do acervo NAO e `-text`, e o guarda enxerga a
        # diferenca — sem isto, um `check-attr` quebrado passaria.
        saida = _git("check-attr", "text", "--",
                     "06_p1a/evidencias/autoinclusao.py").strip()
        self.assertTrue(saida.endswith("text: unspecified"), saida)


if __name__ == "__main__":
    unittest.main()
