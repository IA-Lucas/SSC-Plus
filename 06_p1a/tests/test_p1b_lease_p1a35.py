"""O escritor unico da P1-B, exercido — SSC+ P1-A.3.5 (achado 7).

MAJOR #4 dizia: o lease era verificado apenas ANTES do trabalho, e uma
chamada de provider excede a janela (256 s observados contra 120 s de
lease), de modo que a gravacao podia ocorrer com lease ja morto ou com
titular ja substituido. A P1-A.3.2 corrigiu isso em
`contencao.verificar_lock` e nos runners da P1-A.

A varredura de guardas da P1-A.3.5 mediu que a correcao **nunca alcancou
a copia da P1-B**: `07_p1b/preflight_atual.py` tem ZERO linha executada
pelas duas suites, `_verificar_lock_vivo` nao tinha `fence_esperado`, e
`main()` verificava uma unica vez na abertura e gravava depois das
sondas reais. Quatro implementacoes do mesmo guarda, e a unica sem o
conserto era justamente a que ninguem exercia.

POR QUE ESTE ARQUIVO VIVE NA SUITE P1-A. Criar `07_p1b/tests/` daria um
guarda que nenhuma suite roda — exatamente o defeito que este arquivo
corrige. O teste mora onde e efetivamente executado.

CUSTO ZERO POR CONSTRUCAO. `executar_preflight` e substituido, de modo
que nenhum CLI e invocado e nenhuma sonda real roda; `HOME` aponta para
um descartavel, de modo que nenhuma config real do usuario e lida. O que
se exerce aqui e o portao do escritor unico, nunca a frota.
"""

import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P1A)


class _SaidaMuda(io.StringIO):
    def reconfigure(self, **kwargs):
        return None


def _carregar_p1b():
    caminho = os.path.join(_RAIZ_REPO, "07_p1b", "preflight_atual.py")
    if not os.path.isfile(caminho):
        raise unittest.SkipTest("runner da P1-B ausente")
    spec = importlib.util.spec_from_file_location("preflight_atual_sob_teste",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _escrever_lock(dir_locks, sessao, fence, expira_em):
    os.makedirs(dir_locks, exist_ok=True)
    with open(os.path.join(dir_locks, f"{sessao}.lease"), "w",
              encoding="utf-8") as f:
        json.dump({"sessao": sessao, "pid": os.getpid(), "token": fence,
                   "renovado_em": expira_em - 120, "expira_em": expira_em}, f)
    with open(os.path.join(dir_locks, f"{sessao}.fence"), "w",
              encoding="ascii") as f:
        f.write(str(fence))


class EscritorUnicoDaP1B(unittest.TestCase):
    """O portao que o MAJOR #4 exige, agora tambem na P1-B."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _carregar_p1b()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a35-p1b-")
        self.raiz = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.lar = os.path.join(self.raiz, "lar-vazio")
        os.makedirs(self.lar)

    def _rodar_main(self, fence, durante_as_sondas=None):
        """`main()` da P1-B sobre uma raiz de mentira, sem sonda real."""
        from preflight.pipeline import RelatorioPreflight

        def preflight_falso(espec, **kwargs):
            if durante_as_sondas is not None:
                durante_as_sondas()
            return RelatorioPreflight(provider_id=espec.provider_id,
                                      resultado="SUPERVISED")

        _escrever_lock(os.path.join(self.raiz, "locks"),
                       self.mod._SESSAO_LOCK, fence, time.time() + 600)
        env = {"USERPROFILE": self.lar, "HOME": self.lar,
               "PATH": os.environ.get("PATH", "")}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(self.mod, "_RAIZ", self.raiz), \
                mock.patch.object(self.mod, "executar_preflight",
                                  preflight_falso), \
                mock.patch("sys.stdout", _SaidaMuda()):
            return self.mod.main()

    def _gravados(self):
        saida = os.path.join(self.raiz, "07_p1b", "evidencias")
        return sorted(os.listdir(saida)) if os.path.isdir(saida) else []

    # --- o defeito do achado 7 ------------------------------------------

    def test_para_se_o_titular_muda_entre_a_sonda_e_a_gravacao(self):
        # O defeito exato: com a conferencia apenas inicial, main()
        # gravaria normalmente com o escritor ja substituido.
        def outra_sessao_assume():
            _escrever_lock(os.path.join(self.raiz, "locks"),
                           self.mod._SESSAO_LOCK, 8, time.time() + 600)

        with self.assertRaises(SystemExit) as ctx:
            self._rodar_main(7, outra_sessao_assume)
        self.assertIn("titular do escritor substituido", str(ctx.exception))
        self.assertEqual(self._gravados(), [],
                         "nada pode ter sido gravado depois da PARADA")

    def test_para_se_o_lease_morre_entre_a_sonda_e_a_gravacao(self):
        def lease_estoura():
            _escrever_lock(os.path.join(self.raiz, "locks"),
                           self.mod._SESSAO_LOCK, 7, time.time() - 1)

        with self.assertRaises(SystemExit) as ctx:
            self._rodar_main(7, lease_estoura)
        self.assertIn("lease da sessao operacional morto", str(ctx.exception))
        self.assertEqual(self._gravados(), [])

    def test_grava_quando_o_titular_permanece(self):
        # Contraprova: sem ela, os dois testes acima passariam mesmo com
        # um guarda que reprovasse sempre.
        rc = self._rodar_main(7)
        self.assertEqual(rc, 0)
        gravados = self._gravados()
        self.assertEqual(len(gravados), 1)
        with open(os.path.join(self.raiz, "07_p1b", "evidencias",
                               gravados[0]), encoding="utf-8") as f:
            doc = json.load(f)
        self.assertTrue(doc["lock_verificado_antes_da_persistencia"])
        self.assertEqual(doc["lock_escritor_unico"]["fence"], 7)
        self.assertIn("expira_em", doc["lock_escritor_unico"])

    # --- os ramos fail-closed que a copia da P1-B nao tinha -------------

    def test_lease_ausente_para_antes_de_qualquer_leitura(self):
        with self.assertRaises(SystemExit) as ctx:
            with mock.patch.object(self.mod, "_RAIZ", self.raiz):
                self.mod._verificar_lock_vivo()
        self.assertIn("lease ilegivel/ausente", str(ctx.exception))

    def test_fence_ilegivel_e_parada_tipada_e_nao_excecao_crua(self):
        # Antes desta correcao a leitura do fence nao estava protegida:
        # um fence ilegivel virava excecao crua, e nao PARADA.
        _escrever_lock(os.path.join(self.raiz, "locks"),
                       self.mod._SESSAO_LOCK, 7, time.time() + 600)
        with open(os.path.join(self.raiz, "locks",
                               f"{self.mod._SESSAO_LOCK}.fence"), "w",
                  encoding="ascii") as f:
            f.write("nao-e-inteiro")
        with self.assertRaises(SystemExit) as ctx:
            with mock.patch.object(self.mod, "_RAIZ", self.raiz):
                self.mod._verificar_lock_vivo()
        self.assertIn("fence ilegivel/ausente", str(ctx.exception))

    def test_a_verificacao_da_p1b_e_a_canonica_e_nao_uma_quarta_copia(self):
        # A varredura contou QUATRO implementacoes do mesmo guarda, e a
        # da P1-B era a unica sem o conserto do MAJOR #4. Este teste
        # impede que ela volte a divergir: se alguem reescrever uma copia
        # local aqui, o vinculo com a canonica se rompe e isto reprova.
        import contencao
        with open(os.path.join(_RAIZ_REPO, "07_p1b", "preflight_atual.py"),
                  encoding="utf-8") as f:
            fonte = f.read()
        self.assertIn("from contencao import verificar_lock", fonte)
        self.assertTrue(callable(contencao.verificar_lock))


if __name__ == "__main__":
    unittest.main()
