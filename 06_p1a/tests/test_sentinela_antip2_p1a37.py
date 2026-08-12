"""O sentinela anti-P2 exercido contra violadores — MAJOR #6.

O DEFEITO, na voz do revisor independente que o manteve NAO-FECHADO:
*"a metade (A) segue sem cobrir `07_p1b`"*. A varredura de guardas ja o
tinha registrado como achado 13: *"a metade (A) do sentinela anti-P2
cobre so `06_p1a`; `07_p1b` decide sobre o veredito fora do
classificador e NAO e visto"*.

E ha um segundo defeito, que nao esta no texto do achado e sim na forma
do guarda: ele so podia ser exercido varrendo o repositorio real e
achando-o limpo. Um guarda que nunca viu um violador nao esta provado —
esta apenas verde. Toda a evidencia que existia dele era negativa.

O CAMINHO QUE A OPERACAO PERCORRE. O sentinela roda sobre a arvore real
do repositorio; e o que `test_shadow_eligible_nao_tem_consumidor_de_
execucao` continua fazendo. Estes testes acrescentam o CONTROLE
POSITIVO: arvores sinteticas em disco, com a mesma estrutura de
diretorios do acervo (`06_p1a/preflight/pipeline.py` como classificador,
`07_p1b/` ao lado), contendo o consumidor que se quer pegar. A mesma
funcao, `sentinela_antip2.varrer`, e chamada nos dois casos — nao ha uma
versao para a operacao e outra para o teste.

O vizinho recusado: montar um `ast.parse` de um trecho e chamar
`_portoes_de_execucao` nele. Isso mede a primitiva. O que se mede aqui e
a VARREDURA, com raiz, caminhada de diretorios e escolha de
classificador — que e onde o defeito do escopo vivia.

O QUE ESTES TESTES NAO COBREM, declarado:
- alias por import, concatenacao e propagacao por booleano NAO sao
  resolvidos por esta metade da correcao: sao o achado N5, e ficam para
  o commit seguinte. Ate la, o sentinela e contornavel de proposito, e
  isto e limite conhecido e nao propriedade;
- a analise e estatica e por arquivo: nao segue dataflow entre modulos;
- a lista `PRIMITIVAS_EXECUCAO` e enumerada. Uma primitiva de execucao
  fora dela nao e reconhecida como execucao;
- nada aqui prova que a P1-B nao consuma o veredito por outro meio que
  nao o codigo-fonte versionado (configuracao, dado, prompt).
"""

import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sentinela_antip2 as sentinela  # noqa: E402

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)

CLASSIFICADOR_REL = os.path.join("06_p1a", "preflight", "pipeline.py")

# Um classificador de mentira: PRODUZ o veredito, que e trabalho
# legitimo. Nenhuma varredura pode acusa-lo.
FONTE_CLASSIFICADOR = '''
RESULTADOS = ("ELIGIBLE", "SHADOW_ELIGIBLE", "SUPERVISED", "BLOCKED")


def classificar(teto, sombra):
    resultado = teto
    if sombra is not None and resultado == "ELIGIBLE":
        resultado = "SHADOW_ELIGIBLE"
    return resultado
'''


class _ArvoreSintetica(unittest.TestCase):
    """Uma arvore com a MESMA forma do acervo, montada em disco."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-sent-")
        self.raiz = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.classificador = os.path.join(self.raiz, CLASSIFICADOR_REL)
        self.escrever(CLASSIFICADOR_REL, FONTE_CLASSIFICADOR)

    def escrever(self, rel: str, fonte: str) -> str:
        caminho = os.path.join(self.raiz, *rel.split(os.sep)
                               if os.sep in rel else rel.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(fonte)
        return caminho

    def varrer(self) -> dict:
        return sentinela.varrer(self.raiz, self.classificador)


class MetadeAAlcanca07P1B(_ArvoreSintetica):
    """MAJOR #6: a raiz de (A) e o REPOSITORIO, nao `06_p1a`."""

    def test_decisao_em_07_p1b_e_vista(self):
        # O caso EXATO do achado 13 e do MAJOR #6. Sob o escopo antigo
        # este arquivo era invisivel.
        self.escrever("07_p1b/consumidor.py",
                      'def usar(r):\n'
                      '    if r == "SHADOW_ELIGIBLE":\n'
                      '        return "segue"\n'
                      '    return "para"\n')
        achados = self.varrer()
        self.assertEqual(
            [a.split(":")[0].replace("\\", "/") for a in
             achados["decisoes_fora"]],
            ["07_p1b/consumidor.py"])

    def test_decisao_em_06_p1a_continua_vista(self):
        # A cobertura antiga nao pode ter sido trocada pela nova.
        self.escrever("06_p1a/consumidor.py",
                      'def usar(r):\n'
                      '    return r != "BLOCKED"\n')
        achados = self.varrer()
        self.assertTrue(any("consumidor.py" in a
                            for a in achados["decisoes_fora"]))

    def test_decisao_na_raiz_do_repositorio_e_vista(self):
        self.escrever("consumidor_de_topo.py",
                      'def usar(r):\n'
                      '    return r in ("ELIGIBLE", "SUPERVISED")\n')
        self.assertTrue(any("consumidor_de_topo.py" in a
                            for a in self.varrer()["decisoes_fora"]))

    def test_o_classificador_produz_e_nao_e_acusado(self):
        # Contraprova indispensavel: sem ela, um sentinela que acusasse
        # todo arquivo com o literal passaria em tudo acima — e o
        # classificador legitimo ficaria vermelho para sempre.
        achados = self.varrer()
        self.assertEqual(achados["decisoes_fora"], [])
        self.assertEqual(achados["portoes"], [])

    def test_arvore_limpa_nao_produz_achado(self):
        self.escrever("06_p1a/util.py",
                      'def somar(a, b):\n    return a + b\n')
        self.escrever("07_p1b/relatorio.py",
                      'def imprimir(rels):\n'
                      '    for r in rels:\n'
                      '        print(r)\n')
        achados = self.varrer()
        # Emenda da P2: o relatorio ganhou `portoes_autorizados` e
        # `decisoes_autorizadas`. A comparacao segue sendo do dicionario
        # INTEIRO — de proposito: e ela que garante que arvore limpa nao
        # produz achado em campo NENHUM, inclusive nos campos novos. Um
        # `assertEqual` por chave deixaria de reprovar quando um campo
        # futuro nascesse sujo.
        self.assertEqual(achados, {"ilegiveis": [], "portoes": [],
                                   "decisoes_fora": [],
                                   "nao_resolvidos": [],
                                   "nao_resolvidos_reconhecidos": [],
                                   "portoes_autorizados": [],
                                   "decisoes_autorizadas": []})


class MetadeBGovernoDeExecucao(_ArvoreSintetica):
    """A metade (B) tambem passa a ser exercida contra violador."""

    def test_portao_de_execucao_em_07_p1b_e_acusado(self):
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(r):\n'
                      '    if r == "SHADOW_ELIGIBLE":\n'
                      '        subprocess.run(["kimi", "-p", "oi"])\n')
        achados = self.varrer()
        self.assertTrue(achados["portoes"], "portao nao foi acusado")
        self.assertIn("run()", achados["portoes"][0])

    def test_portao_dentro_do_classificador_tambem_e_acusado(self):
        # A metade (B) nao poupa o classificador: produzir e legitimo,
        # governar execucao nao e — nem la dentro.
        self.escrever(CLASSIFICADOR_REL,
                      FONTE_CLASSIFICADOR +
                      '\n\ndef autorizar(r):\n'
                      '    if r == "ELIGIBLE":\n'
                      '        return eval("1 + 1")\n')
        self.assertTrue(self.varrer()["portoes"])

    def test_execucao_no_ELSE_da_mesma_decisao_e_acusada(self):
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(r):\n'
                      '    if r == "BLOCKED":\n'
                      '        return None\n'
                      '    else:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertTrue(self.varrer()["portoes"])


class FailClosedDoSentinela(_ArvoreSintetica):

    def test_fonte_ilegivel_nao_e_declarado_limpo(self):
        self.escrever("07_p1b/quebrado.py", "def (:\n")
        achados = self.varrer()
        self.assertTrue(achados["ilegiveis"])
        self.assertIn("SyntaxError", achados["ilegiveis"][0])

    def test_testes_e_pycache_ficam_fora_da_varredura(self):
        # Exclusao DECLARADA: os proprios testes citam o vocabulario o
        # tempo todo. Sem ela o sentinela acusaria a si mesmo.
        self.escrever("06_p1a/tests/test_x.py",
                      'def t(r):\n    assert r == "BLOCKED"\n')
        self.assertEqual(self.varrer()["decisoes_fora"], [])


class AVarreduraDaOperacaoUsaAMesmaFuncao(unittest.TestCase):

    def test_a_arvore_real_do_repositorio_esta_limpa(self):
        # O caso que a operacao percorre — a mesma assercao que
        # `test_emendas_p1a3` faz, repetida aqui para que este arquivo
        # nao seja so controle sintetico.
        achados = sentinela.varrer(
            _RAIZ_REAL, os.path.join(_RAIZ_REAL, CLASSIFICADOR_REL))
        self.assertEqual(achados["ilegiveis"], [])
        self.assertEqual(achados["portoes"], [])
        self.assertEqual(achados["decisoes_fora"], [])

    def test_07_p1b_esta_dentro_da_varredura_real(self):
        # Sem esta medicao, "a arvore real esta limpa" poderia significar
        # "o sentinela nem olhou para 07_p1b" — que era o defeito.
        fontes = [os.path.relpath(c, _RAIZ_REAL).replace("\\", "/")
                  for c in sentinela.fontes_py(_RAIZ_REAL)]
        self.assertIn("07_p1b/preflight_atual.py", fontes)


if __name__ == "__main__":
    unittest.main()
