"""A redacao de PII e de caminho local, exercida — SSC+ P1-A.3.5.

ACHADO 10. A varredura de guardas contou **nove** implementacoes desta
redacao espalhadas pelos runners, em **tres forcas diferentes**, e mediu
que **nenhuma** tinha teste: zero ocorrencia de `_redigir`,
`USUARIO_CURTO`, `<USUARIO>` ou `CAMINHO-LOCAL` em qualquer arquivo de
teste das duas suites.

As tres mais fracas — `preflight_capsula`, `preflight_atual` e
`revisao_p1a2` — redigiam SO a forma longa do usuario e deixavam passar
a forma 8.3, que e justamente a forma que `ZeroPiiNosArtefatos` procura.
Nenhum artefato versionado a carrega hoje, de modo que nao havia
violacao viva; o que havia era um guarda que so pegaria o caso DEPOIS
de gravado.

Seis das nove passaram a delegar a `contencao.redigir`. As duas de
`pacote_p1a31.py` e `pacote_p1a33.py` NAO foram repontadas de proposito:
o SHA-256 da saida delas e publicado e precisa reproduzir byte a byte
(medido nesta missao: `c17b730f…` e `87f41503…` reproduzem a partir do
HEAD atual). Elas ja implementam a forma mais forte; introduzir uma
dependencia de import num gerador cujos bytes sao publicados nao compra
nada e arrisca a ancoragem. Em lugar disso, `RedacaoDosGeradores` exige
que continuem EQUIVALENTES a canonica — divergir reprova.

Nenhum teste deste arquivo depende do usuario real da estacao: a
canonica aceita `usuario` injetavel, e os casos usam nomes ficticios.
"""

import importlib.util
import os
import sys
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P1A)
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

import contencao  # noqa: E402

# Usuario ficticio com espaco, como o real: exercita a forma 8.3, que e
# onde as copias fracas falhavam.
_FICTICIO = "Fulano DeTal"


def _carregar(nome: str, apelido: str):
    caminho = os.path.join(_DIR_EVID, nome)
    if not os.path.isfile(caminho):
        raise unittest.SkipTest(f"runner ausente: {nome}")
    spec = importlib.util.spec_from_file_location(apelido, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class RedacaoCanonica(unittest.TestCase):
    """`contencao.redigir` — a implementacao unica."""

    def test_redige_a_forma_longa_do_usuario(self):
        texto = f"C:\\Users\\{_FICTICIO}\\.codex\\auth.json"
        self.assertEqual(contencao.redigir(texto, _FICTICIO),
                         "C:\\Users\\<USUARIO>\\.codex\\auth.json")

    def test_redige_a_forma_8_3_que_as_copias_fracas_deixavam_passar(self):
        # O defeito exato do achado 10. `ZeroPiiNosArtefatos` procura
        # esta forma; uma redacao que so cobre a longa deixa o artefato
        # sair sujo e so e pega depois de gravado.
        curto = contencao.forma_8_3(_FICTICIO)
        self.assertEqual(curto, "FULANO~1")
        self.assertEqual(contencao.redigir(f"C:\\Users\\{curto}\\x",
                                           _FICTICIO),
                         "C:\\Users\\<USUARIO>\\x")

    def test_redige_o_prefixo_de_caminho_local_nas_duas_barras(self):
        for prefixo in contencao.PREFIXOS_DE_CAMINHO_LOCAL:
            with self.subTest(prefixo=prefixo):
                self.assertEqual(
                    contencao.redigir(prefixo + "\\Projetos", _FICTICIO),
                    "<CAMINHO-LOCAL>\\Projetos")

    def test_redige_as_tres_formas_no_mesmo_texto(self):
        curto = contencao.forma_8_3(_FICTICIO)
        texto = (f"lar={_FICTICIO} curto={curto} "
                 f"raiz={contencao.PREFIXOS_DE_CAMINHO_LOCAL[1]}/SSC-Plus")
        saida = contencao.redigir(texto, _FICTICIO)
        self.assertEqual(saida, "lar=<USUARIO> curto=<USUARIO> "
                                "raiz=<CAMINHO-LOCAL>/SSC-Plus")

    def test_texto_vazio_ou_nulo_nao_quebra(self):
        self.assertEqual(contencao.redigir(None, _FICTICIO), "")
        self.assertEqual(contencao.redigir("", _FICTICIO), "")

    def test_texto_sem_pii_atravessa_intacto(self):
        # Contraprova: uma redacao que substituisse demais passaria em
        # todos os testes acima e destruiria a evidencia.
        limpo = "provider=codex resultado=SUPERVISED erros=[]"
        self.assertEqual(contencao.redigir(limpo, _FICTICIO), limpo)

    def test_em_operacao_usa_o_usuario_real_da_estacao(self):
        # `usuario` e injetavel SOMENTE para teste; sem ele, vale o da
        # estacao. Sem esta assercao, a canonica poderia redigir o nome
        # ficticio e nunca o verdadeiro.
        self.assertEqual(contencao._USUARIO_LOCAL,
                         os.path.basename(os.path.expanduser("~")))
        self.assertNotEqual(contencao._USUARIO_LOCAL, _FICTICIO)


class RedacaoDosRunners(unittest.TestCase):
    """As seis copias repontadas redigem tudo o que a canonica redige."""

    RUNNERS = (("revisao_p1a2.py", "red_p1a2"),
               ("revisao_p1a3.py", "red_p1a3"),
               ("revisao_p1a31.py", "red_p1a31"),
               ("revisao_p1a33.py", "red_p1a33"))

    def _texto_de_prova(self):
        real = contencao._USUARIO_LOCAL
        return (f"{real}|{contencao.forma_8_3(real)}|"
                f"{contencao.PREFIXOS_DE_CAMINHO_LOCAL[1]}/x")

    def test_todo_runner_redige_as_tres_formas(self):
        texto = self._texto_de_prova()
        esperado = "<USUARIO>|<USUARIO>|<CAMINHO-LOCAL>/x"
        for nome, apelido in self.RUNNERS:
            with self.subTest(runner=nome):
                mod = _carregar(nome, apelido)
                self.assertEqual(mod._redigir(texto), esperado)

    def test_o_runner_da_p1b_redige_as_tres_formas(self):
        caminho = os.path.join(_RAIZ_REPO, "07_p1b", "preflight_atual.py")
        if not os.path.isfile(caminho):
            self.skipTest("runner da P1-B ausente")
        spec = importlib.util.spec_from_file_location("red_p1b", caminho)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod._redigir(self._texto_de_prova()),
                         "<USUARIO>|<USUARIO>|<CAMINHO-LOCAL>/x")


class RedacaoDosGeradores(unittest.TestCase):
    """As duas nao repontadas precisam continuar EQUIVALENTES a canonica.

    Elas nao delegam porque o SHA-256 da saida delas e publicado. O que
    as prende a canonica e este teste: se qualquer uma divergir, aqui
    reprova — e e assim que as nove copias deixam de derivar em silencio.
    """

    GERADORES = (("pacote_p1a31.py", "red_pac31"),
                 ("pacote_p1a33.py", "red_pac33"))

    def test_geradores_redigem_o_mesmo_que_a_canonica(self):
        real = contencao._USUARIO_LOCAL
        texto = (f"{real}|{contencao.forma_8_3(real)}|"
                 f"{contencao.PREFIXOS_DE_CAMINHO_LOCAL[0]}|"
                 f"{contencao.PREFIXOS_DE_CAMINHO_LOCAL[1]}|limpo")
        canonica = contencao.redigir(texto)
        for nome, apelido in self.GERADORES:
            with self.subTest(gerador=nome):
                mod = _carregar(nome, apelido)
                self.assertTrue(
                    mod._redigir(texto) == canonica,
                    f"{nome}: a redacao divergiu da canonica "
                    "(contencao.redigir)")

    def test_a_forma_8_3_dos_geradores_e_a_mesma_da_canonica(self):
        real = contencao._USUARIO_LOCAL
        for nome, apelido in self.GERADORES:
            with self.subTest(gerador=nome):
                mod = _carregar(nome, apelido)
                self.assertTrue(
                    mod.USUARIO_CURTO == contencao.forma_8_3(real),
                    f"{nome}: forma 8.3 divergente da canonica")


if __name__ == "__main__":
    unittest.main()
