"""Ancoragem no commit do gerador que FOI a revisao — SSC+ P1-A.3.5.

Achado C (§3.3 da `99_decisao-p1a34.md`): `evidencias/pacote_p1a33.py`
**nao tinha teste algum**, e e ele que produziu o pacote `87f41503`
enviado a Codex e Kimi. A varredura de guardas da P1-A.3.5 mediu a
extensao disso sob `sys.monitoring`: o arquivo tem **zero linha
executada** pelas duas suites — nao e cobertura fraca, e ausencia.

A propriedade do MAJOR #5 vale para ele **por construcao** (tambem le
por `git cat-file blob`) e foi observada uma vez, a mao, na §10.1 da
`99_decisao-p1a33.md`. Construcao e observacao **nao sao teste de
regressao**: nada impedia que uma edicao futura reintroduzisse leitura
de disco sem que a suite percebesse. E disso que trata este arquivo.

Alem dos portoes que `pacote_p1a31.py` ja tem, este gerador tem **um a
mais** — `BASE` precisa ser ancestral de `ALVO` —, e esse portao nunca
foi exercido por teste nenhum.

Nenhum CLI, nenhuma rede, nenhum modelo: so o banco de objetos do Git
do proprio repositorio.
"""

import importlib.util
import os
import subprocess
import sys
import unittest
from unittest import mock

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P1A)


def _carregar(nome_arquivo: str, apelido: str):
    caminho = os.path.join(_DIR_P1A, "evidencias", nome_arquivo)
    if not os.path.isfile(caminho):
        raise unittest.SkipTest(f"gerador ausente: {nome_arquivo}")
    spec = importlib.util.spec_from_file_location(apelido, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=_RAIZ_REPO,
                          capture_output=True, text=True,
                          check=True).stdout.strip()


class AncoragemDoPacoteP1a33(unittest.TestCase):
    """O gerador que produziu o pacote enviado a revisao, exercido."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _carregar("pacote_p1a33.py", "pacote_p1a33_sob_teste")
        # Uma geracao de referencia, reaproveitada pelos testes que
        # apenas INSPECIONAM o texto. Os que medem determinismo ou
        # independencia da arvore geram de novo, porque e a geracao
        # repetida que eles estao medindo. Sem este cache o arquivo
        # gerava o pacote sete vezes e sozinho dobrava a suite P1-A.
        cls.pacote = cls.mod.montar_pacote()

    # --- a ancoragem: o pacote e funcao do commit, nao do checkout -----

    def test_hashes_de_evidencia_vem_do_blob_e_nao_do_disco(self):
        # Prova direta: para cada evidencia hasheada, os bytes que o
        # gerador le precisam ser os do blob em ALVO.
        self.assertTrue(self.mod.EVIDENCIAS_HASHEADAS)
        for rel in self.mod.EVIDENCIAS_HASHEADAS:
            with self.subTest(evidencia=rel):
                blob = subprocess.run(
                    ["git", "cat-file", "blob", f"{self.mod.ALVO}:{rel}"],
                    cwd=_RAIZ_REPO, capture_output=True, check=True).stdout
                self.assertEqual(self.mod._blob(rel), blob)

    def test_leitura_ignora_a_arvore_de_trabalho(self):
        # Mutar o disco NAO pode mudar um byte do que o gerador le. Com
        # `core.autocrlf=true` foi exatamente isso que reprovou a prova
        # de ancoragem da P1-A.3.1.
        rel = "06_p1a/tiers_declarados.json"
        caminho = os.path.join(_RAIZ_REPO, *rel.split("/"))
        antes = self.mod._blob(rel)
        with open(caminho, "rb") as f:
            original = f.read()
        try:
            with open(caminho, "ab") as f:
                f.write(b"\nMUTACAO-DA-ARVORE-DE-TRABALHO\n")
            self.assertEqual(self.mod._blob(rel), antes)
            self.assertEqual(self.mod._conteudo_alvo(rel),
                             antes.decode("utf-8"))
        finally:
            with open(caminho, "wb") as f:
                f.write(original)

    def test_o_pacote_inteiro_nao_muda_com_a_arvore_mutada(self):
        # A propriedade acima medida onde ela importa: no artefato
        # inteiro, nao so numa funcao auxiliar.
        rel = "06_p1a/tiers_declarados.json"
        caminho = os.path.join(_RAIZ_REPO, *rel.split("/"))
        antes = self.pacote
        with open(caminho, "rb") as f:
            original = f.read()
        try:
            with open(caminho, "ab") as f:
                f.write(b"\nMUTACAO-DA-ARVORE-DE-TRABALHO\n")
            self.assertEqual(self.mod.montar_pacote(), antes)
        finally:
            with open(caminho, "wb") as f:
                f.write(original)

    def test_gerador_nao_depende_do_head_corrente(self):
        # E o que permite a um terceiro reproduzir o pacote depois de
        # commits posteriores — inclusive os desta missao.
        head = _git("rev-parse", "HEAD")
        self.assertIn(self.mod.ALVO, self.pacote)
        if head != self.mod.ALVO:
            self.assertNotIn(head, self.pacote,
                             "o HEAD corrente nao pode entrar no pacote")

    def test_duas_geracoes_produzem_o_mesmo_texto(self):
        self.assertEqual(self.mod.montar_pacote(), self.pacote)

    def test_tree_publicado_e_o_do_alvo_e_nao_o_do_checkout(self):
        tree_alvo = _git("rev-parse", f"{self.mod.ALVO}^{{tree}}")
        tree_checkout = _git("rev-parse", "HEAD^{tree}")
        self.assertIn(f"tree do ALVO:         {tree_alvo}", self.pacote)
        if tree_checkout != tree_alvo:
            self.assertNotIn(tree_checkout, self.pacote)

    # --- os portoes de identidade ---------------------------------------

    def test_portao_recusa_commit_alvo_inexistente(self):
        with mock.patch.object(self.mod, "ALVO", "0" * 40):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.montar_pacote()
        self.assertIn("ausente", str(ctx.exception))

    def test_portao_recusa_paternidade_divergente(self):
        outro = _git("rev-parse", "HEAD")
        with mock.patch.object(self.mod, "PAI", outro):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.montar_pacote()
        self.assertIn("pai inesperado", str(ctx.exception))

    def test_portao_recusa_base_que_nao_e_ancestral_do_alvo(self):
        # O portao que `pacote_p1a31.py` NAO tem, e que nenhum teste do
        # acervo exercia. Sem ele o pacote publicaria um diff entre
        # commits sem relacao de ancestralidade, e o revisor julgaria um
        # "estado anterior" que nunca foi anterior a coisa nenhuma.
        descendente = _git("rev-parse", "HEAD")
        self.assertNotEqual(descendente, self.mod.ALVO)
        with mock.patch.object(self.mod, "BASE", descendente):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.montar_pacote()
        self.assertIn("nao e ancestral", str(ctx.exception))

    def test_base_declarada_e_mesmo_ancestral_do_alvo(self):
        # Contraprova dos tres portoes: sem ela, um gerador que parasse
        # SEMPRE passaria nos testes acima.
        rc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", self.mod.BASE,
             self.mod.ALVO], cwd=_RAIZ_REPO).returncode
        self.assertEqual(rc, 0)
        self.assertEqual(_git("rev-parse", f"{self.mod.ALVO}^"),
                         self.mod.PAI)
        self.assertIn("=== Diff integral BASE..ALVO ===", self.pacote)


class AncoragemValeParaOsDoisGeradores(unittest.TestCase):
    """A ancoragem e invariante do par, nao acidente de um arquivo.

    `AncoragemDoPacoteNoCommit` (test_correcoes_p1a32.py) cobre o
    gerador da P1-A.3.1; a classe acima cobre o da P1-A.3.3. Esta aqui
    exige a MESMA propriedade dos dois de uma vez, para que corrigir um
    e esquecer o outro fique visivel — que e como o achado C nasceu.
    """

    GERADORES = (("pacote_p1a31.py", "gerador_p1a31_par"),
                 ("pacote_p1a33.py", "gerador_p1a33_par"))

    def test_todo_gerador_le_por_cat_file_blob_e_nao_do_disco(self):
        rel = "06_p1a/tiers_declarados.json"
        caminho = os.path.join(_RAIZ_REPO, *rel.split("/"))
        with open(caminho, "rb") as f:
            original = f.read()
        try:
            for arquivo, apelido in self.GERADORES:
                with self.subTest(gerador=arquivo):
                    mod = _carregar(arquivo, apelido)
                    esperado = subprocess.run(
                        ["git", "cat-file", "blob", f"{mod.ALVO}:{rel}"],
                        cwd=_RAIZ_REPO, capture_output=True,
                        check=True).stdout
                    with open(caminho, "wb") as f:
                        f.write(original + b"\nMUTACAO\n")
                    self.assertEqual(mod._blob(rel), esperado)
        finally:
            with open(caminho, "wb") as f:
                f.write(original)


if __name__ == "__main__":
    unittest.main()
