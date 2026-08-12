"""Fluxo multi-provider e gate de aplicacao explicita."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import apoio  # noqa: F401

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ / "08_p2") not in sys.path:
    sys.path.insert(0, str(_RAIZ / "08_p2"))

import fluxo_controlado as fc  # noqa: E402
import executar_fluxo as ef  # noqa: E402
import contencao  # noqa: E402


PATCH = """diff --git a/alvo.txt b/alvo.txt
index 5626abf..f719efd 100644
--- a/alvo.txt
+++ b/alvo.txt
@@ -1 +1 @@
-old
+new
"""


class DespachanteFalso:
    def __init__(self, alterar=True, revisao="APROVADA", juiz="APROVADO",
                 nu_em=None):
        self.alterar = alterar
        self.revisao = revisao
        self.juiz = juiz
        self.nu_em = nu_em
        self.chamadas = []

    def __call__(self, **pedido):
        self.chamadas.append(pedido)
        etapa = pedido["etapa"]
        saidas = {
            "contextualizar": "mapa\nSSC_CONTEXTO: PRONTO",
            "planejar": "plano\nSSC_PLANO: PRONTO",
            "implementar": (
                "proposta\nSSC_IMPLEMENTACAO: PROPOSTA\nSSC_PATCH:\n"
                "```diff\n" + PATCH.rstrip() + "\n```"
                if self.alterar else
                "analise\nSSC_IMPLEMENTACAO: SEM_ALTERACAO"),
            "revisar": f"parecer\nSSC_REVISAO: {self.revisao}",
            "julgar": f"veredito\nSSC_JULGAMENTO: {self.juiz}",
        }
        if etapa == self.nu_em:
            saidas[etapa] = "SSC_STATUS: SUCESSO"
        return {"status": "sucesso", "saida": saidas[etapa],
                "attempts": [{"executor_resolvido": {
                    "provedor": pedido["provedor"]}}]}


class FluxoEstruturado(unittest.TestCase):
    def test_recibo_publico_e_redigido_como_documento_inteiro(self):
        usuario = "USUARIO-FICTICIO-FLUXO"
        anterior = contencao._USUARIO_LOCAL
        try:
            contencao._USUARIO_LOCAL = usuario
            seguro = ef._documento_redigido({
                "novo_campo": f"C:\\Users\\{usuario}\\segredo",
                "aninhado": [{"valor": usuario}],
            })
        finally:
            contencao._USUARIO_LOCAL = anterior
        serializado = str(seguro)
        self.assertNotIn(usuario, serializado)
        self.assertIn("<USUARIO>", serializado)

    def test_ordem_e_papeis_sao_vinculantes(self):
        d = DespachanteFalso(alterar=True)
        r = fc.executar_fluxo(
            "corrigir", "troque old por new", d,
            lambda patch: {"returncode": 0, "patch": bool(patch)})
        self.assertEqual(
            [(c["etapa"], c["provedor"], c["papel"]) for c in d.chamadas],
            [("contextualizar", "kimi", "autor"),
             ("planejar", "codex", "autor"),
             ("implementar", "codex", "autor"),
             ("revisar", "claude", "revisor"),
             ("julgar", "google", "juiz")])
        self.assertEqual(r["sequencia"],
                         ["contextualizar", "planejar", "implementar",
                          "revisar", "julgar", "testar"])
        self.assertTrue(r["qualidade_aprovada"])
        self.assertFalse(r["aplicado"])
        self.assertTrue(r["pronto_para_aprovacao_explicita"])

    def test_status_sucesso_sozinho_nao_e_prova_de_qualidade(self):
        with self.assertRaises(fc.FluxoRecusado) as ctx:
            fc.executar_fluxo(
                "corrigir", "x", DespachanteFalso(nu_em="revisar"),
                lambda patch: {"returncode": 0})
        self.assertIn("SSC_REVISAO", str(ctx.exception))

    def test_revisor_ou_juiz_reprovando_bloqueia_antes_dos_testes(self):
        for nome, d in (("revisor", DespachanteFalso(revisao="REPROVADA")),
                        ("juiz", DespachanteFalso(juiz="REPROVADO"))):
            chamado = []
            with self.subTest(nome=nome), self.assertRaises(fc.FluxoRecusado):
                fc.executar_fluxo(
                    "corrigir", "x", d,
                    lambda patch: chamado.append(patch) or {"returncode": 0})
            self.assertEqual(chamado, [])

    def test_testes_vermelhos_impedem_pronto_para_aprovacao(self):
        with self.assertRaises(fc.FluxoRecusado) as ctx:
            fc.executar_fluxo(
                "corrigir", "x", DespachanteFalso(),
                lambda patch: {"returncode": 7})
        self.assertIn("testes reprovaram", str(ctx.exception))

    def test_operacao_sem_mudanca_tambem_percorre_todos_os_gates(self):
        r = fc.executar_fluxo(
            "analisar", "riscos", DespachanteFalso(alterar=False),
            lambda patch: {"returncode": 0, "recebeu": patch})
        self.assertIsNone(r["patch"])
        self.assertFalse(r["pronto_para_aprovacao_explicita"])
        self.assertEqual(len(r["etapas"]), 5)


class CopiaFielParaOPortaoDeTestes(unittest.TestCase):
    def test_a_copia_leva_o_git_e_deixa_o_runtime(self):
        """`.git` viaja; `locks/` e caches nao — e o git da copia FUNCIONA.

        Copia sem `.git` nao e o estado em que a operacao roda: a suite
        completa ancora testes de blob em commits e, sem historico, um
        gerador de pacote da SystemExit que mata o unittest sem sumario
        (medido em 2026-08-12, `fluxo-20260812T135319*-recusado.json`).
        Aqui a interface exercida e a mesma do portao: `copytree` com
        `_ignorar_copia`, e um comando git REAL dentro da copia.
        """
        import shutil
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            origem = Path(tmp) / "origem"
            (origem / "locks").mkdir(parents=True)
            (origem / "__pycache__").mkdir()
            (origem / "locks" / "x.lease").write_text("runtime")
            (origem / "modulo.pyc").write_text("cache")
            (origem / "codigo.py").write_text("print('ok')\n")
            ambiente = {**os.environ,
                        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
            for argv in (["git", "init", "-q"],
                         ["git", "add", "codigo.py"],
                         ["git", "commit", "-q", "-m", "base"]):
                subprocess.run(argv, cwd=origem, env=ambiente,
                               capture_output=True, check=True)
            destino = Path(tmp) / "copia"
            shutil.copytree(origem, destino, ignore=fc._ignorar_copia)

            self.assertFalse((destino / "locks").exists())
            self.assertFalse((destino / "__pycache__").exists())
            self.assertFalse((destino / "modulo.pyc").exists())
            cabeca = lambda raiz: subprocess.run(  # noqa: E731
                ["git", "-c", f"safe.directory={raiz.as_posix()}",
                 "rev-parse", "HEAD"], cwd=raiz, capture_output=True,
                text=True)
            na_copia = cabeca(destino)
            self.assertEqual(na_copia.returncode, 0,
                             "o git da copia nao funciona: "
                             + na_copia.stderr[:200])
            self.assertEqual(na_copia.stdout, cabeca(origem).stdout,
                             "a copia nao carrega o MESMO historico")


class AplicacaoExplicita(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fluxo-gate-")
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name) / "repo"
        self.estado = Path(self.tmp.name) / "estado"
        self.raiz.mkdir()
        (self.raiz / "alvo.txt").write_text("old\n", encoding="utf-8")

    def resultado(self):
        return {
            "fluxo_id": "fluxo-teste", "patch": PATCH,
            "patch_sha256": fc._sha256_texto(PATCH),
            "qualidade_aprovada": True,
        }

    def test_patch_e_testado_na_copia_sem_mudar_a_arvore_real(self):
        teste = fc.testar_patch_isolado(
            PATCH, self.raiz,
            [sys.executable, "-c",
             "from pathlib import Path; assert Path('alvo.txt').read_text() == 'new\\n'"])
        self.assertEqual(teste["returncode"], 0, teste)
        self.assertEqual((self.raiz / "alvo.txt").read_text(), "old\n")

    def test_sem_token_correto_nada_e_aplicado(self):
        pasta, token = fc.preparar_aprovacao(
            self.resultado(), self.raiz, self.estado)
        with self.assertRaises(fc.FluxoRecusado):
            fc.aplicar_patch_aprovado(pasta, token + "errado", self.raiz)
        self.assertEqual((self.raiz / "alvo.txt").read_text(), "old\n")

        fc.aplicar_patch_aprovado(pasta, token, self.raiz)
        self.assertEqual((self.raiz / "alvo.txt").read_text(), "new\n")

    def test_deriva_depois_dos_testes_invalida_aprovacao(self):
        pasta, token = fc.preparar_aprovacao(
            self.resultado(), self.raiz, self.estado)
        (self.raiz / "alvo.txt").write_text("drift\n", encoding="utf-8")
        with self.assertRaises(fc.FluxoRecusado) as ctx:
            fc.aplicar_patch_aprovado(pasta, token, self.raiz)
        self.assertIn("mudou depois dos testes", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
