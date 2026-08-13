"""Caso operacional: tarefa de repositorio recebe snapshot, nao cwd vazio."""

import os
import sys
import subprocess
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

    def test_junction_para_fora_da_raiz_nao_vaza_no_snapshot(self):
        """MAJOR da P1-A.10 (TOCTOU/contencao do snapshot), o caso Windows.

        `os.path.islink` NAO ve junction; sem a leitura contida, o walk
        desceria pela juncao e um arquivo de FORA da raiz entraria no
        snapshot enviado ao provedor. A janela de troca pos-checagem
        (o TOCTOU literal) nao se simula num teste sem corrida; o que se
        exerce aqui e o MESMO guarda que a fecha — `ler_arquivo_contido`
        confere descritor e realpath —, contra o vizinho de mecanismo
        que ele tambem fecha e que E reproduzivel: alvo resolvendo fora
        da raiz. Limite declarado: a corrida em si nao foi exercida.
        """
        fora = tempfile.TemporaryDirectory(prefix="ssc-fora-")
        self.addCleanup(fora.cleanup)
        with open(os.path.join(fora.name, "vazado.py"), "w",
                  encoding="utf-8") as f:
            f.write("SEGREDO_DE_FORA_DA_RAIZ = 1\n")
        self.escrever("raiz/normal.py", "print('dentro')\n")
        juncao = os.path.join(self.tmp.name, "raiz", "atalho")
        criada = subprocess.run(
            ["cmd", "/c", "mklink", "/J", juncao, fora.name],
            capture_output=True).returncode == 0
        if not criada:
            self.skipTest("mklink /J indisponivel nesta estacao")
        snapshot = cw.montar_snapshot(
            os.path.join(self.tmp.name, "raiz"), "tarefa", "criterio")
        self.assertNotIn("SEGREDO_DE_FORA_DA_RAIZ", snapshot.prompt,
                         "conteudo de FORA da raiz vazou no snapshot")
        self.assertIn("dentro", snapshot.prompt)
        vazados = [i for i in snapshot.resumo["arquivos_incluidos"]
                   if "vazado" in i["caminho"]]
        self.assertEqual(vazados, [])

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
