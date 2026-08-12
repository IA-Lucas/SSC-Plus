"""Os QUATRO campos de plataforma no instrumento que publica numeros — P1A9-b.

O achado (`06_p1a/99_decisao-p1a9.md` §7): a regra dos quatro campos —
interpretador, pytest, `core.autocrlf`, usuario da estacao — era regra de
processo e NENHUM teste a impunha. Afirmar a propriedade sem exercer a
interface e a familia do MAJOR #3, e a regra denunciava a si mesma.

O que se exerce aqui, e como:

- o guarda roda `scripts/verificar.py` DO REPOSITORIO (bytes lidos do
  arquivo real no momento do teste, nunca uma copia congelada no teste)
  num esqueleto descartavel com suites triviais, pela MESMA porta da
  operacao: `python scripts/verificar.py --rapido` em subprocesso;
- exige a linha `plataforma:` com os quatro campos NOMEADOS e com valor,
  ANTES de qualquer suite — numero sem plataforma na frente e exatamente
  o que a P1-A.8 mediu como irreproduzivel;
- exige que dois dos valores sejam MEDIDOS e nao afirmados: o
  interpretador tem de ser a versao do Python que executou, e o usuario
  tem de ser o desta estacao (comparado, nunca escrito literal — os
  guardas ZeroPii derivam o alvo dele).

## O que estes testes NAO cobrem, declarado

- numeros publicados fora do instrumento (prosa de missao, tabela de
  atestado) continuam sem guarda — cobertura disso exigiria varrer
  prosa por heuristica, e afirmariamos mais do que se mede;
- o esqueleto tem suites triviais: a CONTAGEM real de testes nao e
  objeto daqui, so a moldura de plataforma em volta dela;
- o esqueleto nao e repositorio git: `core.autocrlf` sai "nao definido",
  o que prova a PRESENCA do campo, nao o valor desta arvore.
"""

import getpass
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_RAIZ_REPO = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
_VERIFICAR_REAL = os.path.join(_RAIZ_REPO, "scripts", "verificar.py")

_TESTE_TRIVIAL = (
    "import unittest\n"
    "class Ok(unittest.TestCase):\n"
    "    def test_ok(self):\n"
    "        self.assertTrue(True)\n"
)


def _esqueleto() -> str:
    raiz = tempfile.mkdtemp(prefix="p1a9b-esqueleto-")
    for suite in ("05_p0/tests", "06_p1a/tests"):
        os.makedirs(os.path.join(raiz, suite))
        with open(os.path.join(raiz, suite, "test_trivial.py"), "w",
                  encoding="ascii") as arquivo:
            arquivo.write(_TESTE_TRIVIAL)
    os.makedirs(os.path.join(raiz, "scripts"))
    shutil.copyfile(_VERIFICAR_REAL,
                    os.path.join(raiz, "scripts", "verificar.py"))
    return raiz


class OInstrumentoDeclaraOsQuatroCampos(unittest.TestCase):
    """`verificar.py` real, porta real, esqueleto descartavel."""

    @classmethod
    def setUpClass(cls):
        cls.raiz = _esqueleto()
        cls.processo = subprocess.run(
            [sys.executable, "scripts/verificar.py", "--rapido"],
            cwd=cls.raiz, capture_output=True, text=True, timeout=300)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.raiz, ignore_errors=True)

    def _linha_plataforma(self) -> str:
        linhas = [linha for linha in self.processo.stdout.splitlines()
                  if linha.startswith("plataforma:")]
        self.assertEqual(
            len(linhas), 1,
            "a linha `plataforma:` deve existir e ser unica; "
            f"stdout={self.processo.stdout[:400]!r} "
            f"stderr={self.processo.stderr[:400]!r}")
        return linhas[0]

    def test_verificacao_conclui_no_esqueleto(self):
        self.assertEqual(
            self.processo.returncode, 0,
            f"verificar.py falhou no esqueleto: "
            f"{self.processo.stderr[:400]!r}")

    def test_os_quatro_campos_estao_na_mesma_linha_e_com_valor(self):
        linha = self._linha_plataforma()
        for campo in ("interpretador=", "pytest=", "core.autocrlf=",
                      "usuario="):
            with self.subTest(campo=campo):
                self.assertIn(campo, linha)
                valor = linha.split(campo, 1)[1].split("|", 1)[0].strip()
                self.assertTrue(valor, f"{campo} sem valor na linha "
                                       f"de plataforma: {linha!r}")

    def test_a_plataforma_vem_antes_de_qualquer_numero_de_suite(self):
        stdout = self.processo.stdout
        posicao_plataforma = stdout.index("plataforma:")
        primeira_suite = stdout.index("==")
        self.assertLess(posicao_plataforma, primeira_suite,
                        "a plataforma tem de emoldurar o numero, nao "
                        "vir depois dele")

    def test_interpretador_e_usuario_sao_medidos_e_nao_afirmados(self):
        # O esqueleto rodou com ESTE interpretador e ESTE usuario; se a
        # linha trouxesse texto fixo, qualquer um dos dois divergiria.
        linha = self._linha_plataforma()
        self.assertIn(platform.python_version(), linha)
        usuario = linha.split("usuario=", 1)[1].strip()
        self.assertEqual(usuario, getpass.getuser())


if __name__ == "__main__":
    unittest.main()
