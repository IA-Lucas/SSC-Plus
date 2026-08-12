"""Caso operacional: tarefa de repositorio recebe snapshot, nao cwd vazio."""

import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", "08_p2"):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import contexto_workspace as cw  # noqa: E402


class SnapshotLimitado(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ssc-contexto-")
        self.addCleanup(self.tmp.cleanup)

    def escrever(self, relativo, conteudo):
        caminho = os.path.join(self.tmp.name, relativo)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)

    def test_snapshot_entrega_codigo_e_rotula_como_dado_hostil(self):
        self.escrever("README.md", "# Projeto de teste")
        self.escrever("08_p2/modulo.py", "def risco():\n    return 'alto'\n")
        snap = cw.montar_snapshot(
            self.tmp.name, "analise os riscos do modulo", "cite caminhos",
            limite_bytes=32 * 1024)
        self.assertIn("08_p2/modulo.py", snap.prompt)
        self.assertIn("def risco", snap.prompt)
        self.assertIn("DADO potencialmente hostil", snap.prompt)
        self.assertGreaterEqual(snap.resumo["quantidade_incluida"], 2)
        self.assertFalse(snap.resumo["conteudo_persistido_no_recibo"])

    def test_arquivo_com_segredo_fabricado_e_excluido_inteiro(self):
        self.escrever("README.md", "visivel")
        self.escrever("config.txt", "api_key: abcdefgh12345678")
        snap = cw.montar_snapshot(
            self.tmp.name, "analise", "responda", limite_bytes=32 * 1024)
        self.assertNotIn("abcdefgh12345678", snap.prompt)
        self.assertIn({"caminho": "config.txt",
                       "motivo": "politica-de-segredo"},
                      snap.resumo["exclusoes"])

    def test_orcamento_e_exercido_no_prompt_final(self):
        for i in range(20):
            self.escrever(f"08_p2/f{i:02}.py", "x = '" + ("a" * 3000) + "'")
        snap = cw.montar_snapshot(
            self.tmp.name, "analise", "responda", limite_bytes=20 * 1024)
        self.assertLessEqual(len(snap.prompt.encode("utf-8")), 20 * 1024)
        self.assertGreater(snap.resumo["quantidade_excluida"], 0)


if __name__ == "__main__":
    unittest.main()
