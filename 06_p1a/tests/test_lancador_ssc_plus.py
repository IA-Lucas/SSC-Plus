"""Entrada unica: lease e argv nascem sem PowerShell montado pelo usuario."""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

import apoio  # noqa: F401

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import ssc_plus  # noqa: E402
from escritor_repositorio import titular_atual  # noqa: E402


class LeaseEmUmProcesso(unittest.TestCase):
    def test_context_manager_adquire_renova_e_expira_ao_sair(self):
        with tempfile.TemporaryDirectory(prefix="ssc-launcher-lock-") as tmp:
            with ssc_plus.LeaseAutomatico(
                    "ssc-teste", tmp, renovacao_s=0.03, lease_s=0.2) as fence:
                self.assertGreater(fence, 0)
                primeiro = titular_atual(tmp)
                self.assertEqual(primeiro["sessao"], "ssc-teste")
                renovado_em = primeiro["renovado_em"]
                time.sleep(0.08)
                segundo = titular_atual(tmp)
                self.assertGreater(segundo["renovado_em"], renovado_em)
            self.assertIsNone(titular_atual(tmp),
                              "launcher saiu mas deixou lease vivo")


class ComandoCurto(unittest.TestCase):
    def test_launcher_monta_todos_os_argumentos_do_runner(self):
        argv = ssc_plus.construir_argv_runner(
            Path("preflight.json"), "analise os riscos", "cite arquivos",
            "arquitetura", "revisor")
        self.assertEqual(argv[argv.index("--preflight") + 1],
                         "preflight.json")
        self.assertEqual(argv[argv.index("--tarefa") + 1],
                         "analise os riscos")
        self.assertIn("--capacidade", argv)
        self.assertIn("--papel", argv)

    def test_cmd_chama_launcher_local_sem_comando_longo(self):
        texto = (_RAIZ / "SSC-Plus.cmd").read_text(encoding="utf-8")
        self.assertIn('python "%~dp0ssc_plus.py" %*', texto)
        self.assertNotIn("runner_p2.py", texto)
        self.assertNotIn("preflight-2026", texto)

    def test_opcoes_simples_mapeiam_para_o_fluxo_completo(self):
        self.assertEqual(ssc_plus.OPERACOES,
                         {"1": "analisar", "2": "corrigir",
                          "3": "implementar", "4": "revisar"})
        argv = ssc_plus.construir_argv_fluxo(
            Path("preflight.json"), "corrigir", "conserte o portao")
        self.assertEqual(argv[argv.index("--operacao") + 1], "corrigir")
        self.assertEqual(argv[argv.index("--tarefa") + 1],
                         "conserte o portao")

    def test_parser_expoe_as_quatro_operacoes_e_aprovacao_separada(self):
        args = ssc_plus._parser().parse_args([
            "--operacao", "implementar", "--tarefa", "nova funcao"])
        self.assertEqual(args.operacao, "implementar")
        aplicar = ssc_plus._parser().parse_args([
            "--aplicar-fluxo", "fluxo-1", "--token", "confirmacao"])
        self.assertEqual(aplicar.aplicar_fluxo, "fluxo-1")
        self.assertEqual(aplicar.token, "confirmacao")


if __name__ == "__main__":
    unittest.main()
