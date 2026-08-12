"""Policy Gateway: envelope de aprovacao de custo, veto, perfil, fronteira."""

import unittest

import apoio
from ssc_p0.router import FalhaFechadaClassificacao, RotaVetada


class TestPolicy(unittest.TestCase):
    def setUp(self):
        self.lab = apoio.novo_lab()
        self.k = self.lab.kernel

    def tearDown(self):
        apoio.limpar_lab(self.lab)

    def _wu(self, privacidade="remoto-permitido", nivel="L2"):
        return self.lab.router.forjar(
            intencao="tarefa de policy", criterios={"tipo": "x"},
            tipo="ato", nivel=nivel, classe="C1",
            perfil={"modalidade": "texto", "ferramentas": [],
                    "formato_saida": "livre", "contexto_max_tokens": 8000,
                    "dominio": "geral", "privacidade": privacidade,
                    "latencia_max_ms": None, "orcamento_max_custo": None})

    def test_envelope_modelo_fora_da_lista_veto_mesmo_na_politica(self):
        wu = self._wu()
        # modelo-x ESTA na politica, mas o envelope so permite modelo-l1.
        envelope = dict(self.lab.aprovacao,
                        modelos_permitidos=["prov-a/modelo-l1"])
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=envelope, motivo="fora do envelope")
        self.assertTrue(any("envelope" in v for v in ctx.exception.vetos))
        # veto gravado como evento; nenhum attempt
        self.assertTrue(any(r.get("acao") == "veto" for r in self.k.recusas))
        self.assertEqual(len(self.k.attempts), 0)

    def test_reroteamento_dentro_do_envelope_sem_nova_aprovacao(self):
        wu = self._wu()
        d1 = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="d1")
        n_eventos = self.k.log.seq_atual()
        d2 = self.lab.router.rerotear(
            wu, rota="padrao", selecao=self.lab.selecao("prov-b", "modelo-y"),
            aprovacao_custo=self.lab.aprovacao,
            motivo="dentro do envelope: sem nova aprovacao")
        self.assertEqual(d2.supersede, d1.decisao_id)
        self.assertEqual(d1.aprovacao_custo, d2.aprovacao_custo)
        # Nenhum evento de aprovacao humana (work-unit aguardando-aprovacao).
        self.assertGreater(self.k.log.seq_atual(), n_eventos)
        self.assertEqual(self.k.work_units[wu.work_unit_id].estado, "aprovada")

    def test_envelope_expirado_veto(self):
        wu = self._wu()
        envelope = dict(self.lab.aprovacao,
                        validade="2020-01-01T00:00:00Z")
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=envelope, motivo="expirado")
        self.assertTrue(any("expirado" in v for v in ctx.exception.vetos))

    def test_provedor_fora_da_politica_veto_antes_de_chamada(self):
        wu = self._wu()
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-ladino", "modelo-x"),
                aprovacao_custo=self.lab.aprovacao, motivo="fora")
        self.assertTrue(any("fora da politica" in v
                            for v in ctx.exception.vetos))
        self.assertEqual(len(self.k.attempts), 0)

    def test_perfil_privacidade_local_only_nunca_remoto(self):
        wu = self._wu(privacidade="local-only", nivel="L2")
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),  # remoto
                aprovacao_custo=self.lab.aprovacao, motivo="remoto")
        self.assertTrue(any("local-only" in v or "perfil" in v
                            for v in ctx.exception.vetos))

    def test_classificacao_confianca_baixa_falha_fechada(self):
        wu = self._wu()
        with self.assertRaises(FalhaFechadaClassificacao):
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                confianca="baixa", aprovacao_custo=self.lab.aprovacao,
                motivo="ambiguo")
        self.assertTrue(any(e.motivo == "ambiguidade"
                            for e in self.k.escalacoes))
        self.assertEqual(len(self.k.attempts), 0)

    def test_sem_aprovacao_custo_quando_exigida_veto(self):
        wu = self._wu()
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=None, motivo="sem envelope")
        self.assertTrue(any("aprovacao_custo" in v
                            for v in ctx.exception.vetos))

    def test_custo_zero_nao_contorna_envelope_ausente(self):
        """Exerce o caminho operacional da assinatura: custo previsto zero."""
        wu = self._wu()
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                custo_previsto={"valor": 0.0, "rotulo": "assinatura"},
                aprovacao_custo=None, motivo="zero sem envelope")
        self.assertTrue(any("aprovacao_custo" in v
                            for v in ctx.exception.vetos))

    def test_autonomo_nao_contorna_envelope_expirado(self):
        wu = self._wu()
        envelope = dict(self.lab.aprovacao,
                        validade="2020-01-01T00:00:00Z")
        with self.assertRaises(RotaVetada) as ctx:
            self.lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x",
                                         controle="autonomo"),
                custo_previsto={"valor": 0.0},
                aprovacao_custo=envelope, motivo="autonomo expirado")
        self.assertTrue(any("expirado" in v for v in ctx.exception.vetos))

    def test_fallback_recusa_envelope_que_expirou_depois_da_decisao(self):
        wu = self._wu()
        decisao = self.lab.router.propor_decisao(
            wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            alternativas=[self.lab.selecao("prov-b", "modelo-y")],
            aprovacao_custo=self.lab.aprovacao, motivo="antes de expirar")
        decisao.aprovacao_custo["validade"] = "2020-01-01T00:00:00Z"
        self.assertFalse(self.lab.policy.verificar_fallback_envelope(
            decisao, self.lab.selecao("prov-b", "modelo-y")))


if __name__ == "__main__":
    unittest.main()
