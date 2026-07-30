"""Transicoes ilegais recusadas nas 3 maquinas (item: maquinas de estado)."""

import unittest

import apoio  # noqa: F401
from ssc_p0 import estados


class TestEstados(unittest.TestCase):
    def test_transicao_ilegal_sessao_recusada(self):
        ilegais = [("ativa", "retomada"), ("suspensa", "ativa"),
                   ("encerrada", "ativa"), ("retomada", "suspensa"),
                   ("ativa", "ativa"), ("suspensa", "suspensa")]
        for de, para in ilegais:
            with self.subTest(de=de, para=para):
                with self.assertRaises(estados.TransicaoIlegal):
                    estados.transitar_sessao(de, para)

    def test_transicao_ilegal_workunit_recusada(self):
        ilegais = [("proposta", "em-execucao"),
                   ("proposta", "concluida"),
                   ("aprovada", "concluida"),
                   ("aguardando-validacao", "em-execucao"),
                   ("concluida", "proposta"),
                   ("cancelada", "proposta"),
                   ("reprovada", "em-execucao"),
                   ("reprovada", "concluida")]
        for de, para in ilegais:
            with self.subTest(de=de, para=para):
                with self.assertRaises(estados.TransicaoIlegal):
                    estados.transitar_workunit(de, para)

    def test_transicao_ilegal_attempt_recusada(self):
        ilegais = [("criado", "concluido"), ("concluido", "despachado"),
                   ("despachado", "criado"), (None, "despachado"),
                   ("criado", "orfao")]
        for de, para in ilegais:
            with self.subTest(de=de, para=para):
                with self.assertRaises(estados.TransicaoIlegal):
                    estados.transitar_attempt(de, para)

    def test_orfao_apenas_via_retomada(self):
        # despachado -> orfao existe so na tabela exclusiva da retomada.
        estados.marcar_orfao("despachado")
        with self.assertRaises(estados.TransicaoIlegal):
            estados.transitar_attempt("despachado", "orfao")
        with self.assertRaises(estados.TransicaoIlegal):
            estados.marcar_orfao("concluido")

    def test_transicoes_legais_tres_maquinas(self):
        estados.transitar_sessao(None, "ativa")
        estados.transitar_sessao("ativa", "suspensa")
        estados.transitar_sessao("suspensa", "retomada")
        estados.transitar_sessao("retomada", "ativa")
        estados.transitar_workunit(None, "proposta")
        estados.transitar_workunit("proposta", "aprovada")
        estados.transitar_workunit("aprovada", "em-execucao")
        estados.transitar_workunit("em-execucao", "aguardando-validacao")
        estados.transitar_workunit("aguardando-validacao", "concluida")
        estados.transitar_attempt(None, "criado")
        estados.transitar_attempt("criado", "despachado")
        estados.transitar_attempt("despachado", "concluido")

    def test_cancelamento_de_qualquer_estado_nao_terminal(self):
        for de in ("proposta", "aguardando-aprovacao", "aprovada",
                   "em-execucao", "aguardando-validacao", "reprovada"):
            with self.subTest(de=de):
                estados.transitar_workunit(de, "cancelada")
        with self.assertRaises(estados.TransicaoIlegal):
            estados.transitar_workunit("concluida", "cancelada")


if __name__ == "__main__":
    unittest.main()
