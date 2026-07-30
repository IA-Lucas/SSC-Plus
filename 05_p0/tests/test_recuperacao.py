"""Recuperacao: retry/fallback/reroteamento/reparo/escalonamento distintos,
IR-1/IR-2, timeout, 429 Retry-After, quota, contrato, teto de custo."""

import tempfile
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.judge import Juiz1


class TestRecuperacao(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def _lab(self, programa=None, **kw):
        programa = programa or {}
        return apoio.novo_lab(self._tmp.name, programa_providers=programa, **kw)

    def _wu_decisao(self, lab, alternativas=None, modelo="modelo-x",
                    provedor="prov-a"):
        wu = lab.router.forjar(
            intencao="tarefa de recuperacao", criterios={"tipo": "x"},
            tipo="ato", nivel="L2", classe="C1")
        d = lab.router.propor_decisao(
            wu, rota="padrao", selecao=lab.selecao(provedor, modelo),
            alternativas=alternativas or [],
            aprovacao_custo=lab.aprovacao, motivo="t")
        return wu, d

    def _alt_y(self, lab):
        return [lab.selecao("prov-b", "modelo-y")]

    # -- indeterminado / timeout (IR-2) ------------------------------------

    def test_indeterminado_sem_retry_automatico_escalona_ir2(self):
        lab = self._lab({"prov-a/modelo-x": ["efeito-incerto"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-1")
        k = lab.kernel
        self.assertEqual(r.status, "indeterminado")
        self.assertEqual(len(k.retries), 0)  # IR-2: sem retry automatico
        self.assertTrue(any(e.motivo == "indeterminado" for e in k.escalacoes))
        self.assertEqual(k.attempts[r.attempt_id]["attempt"].resultado,
                         "indeterminado")

    def test_timeout_apos_envio_efeito_incerto_indeterminado(self):
        lab = self._lab({"prov-a/modelo-x": ["timeout"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-2")
        attempt = lab.kernel.attempts[r.attempt_id]["attempt"]
        self.assertEqual(attempt.resultado, "indeterminado")
        self.assertEqual(attempt.efeito_externo, "incerto")
        self.assertEqual(len(lab.kernel.retries), 0)

    # -- retry (IR-1) --------------------------------------------------------

    def test_retry_so_com_idempotency_key_ir1(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-transitoria", "sucesso"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-idem")
        self.assertEqual(r.status, "sucesso")
        self.assertEqual(len(lab.kernel.retries), 1)
        self.assertEqual(lab.kernel.retries[0].idempotency_key, "op-idem")

    def test_retry_com_efeito_nao_aplicado_sem_key_ir1(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-transitoria", "sucesso"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key=None)
        # efeito_externo=nao-aplicado (default do falso) permite retry.
        self.assertEqual(r.status, "sucesso")
        self.assertEqual(len(lab.kernel.retries), 1)

    def test_retry_negado_sem_key_e_efeito_aplicado_ir1(self):
        lab = self._lab({"prov-a/modelo-x": [
            {"comportamento": "falha-transitoria", "efeito": "aplicado"},
            "sucesso"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key=None)
        self.assertEqual(len(lab.kernel.retries), 0)  # IR-1 bloqueou
        self.assertEqual(r.status, "escalonado")

    def test_retry_maximo_3_e_esgotamento(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-transitoria"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-3")
        self.assertEqual(len(lab.kernel.retries), 3)  # max 3
        self.assertTrue(any(e.motivo == "sem-alternativa"
                            for e in lab.kernel.escalacoes))
        self.assertEqual(r.status, "escalonado")

    def test_429_com_retry_after_respeitado(self):
        lab = self._lab({"prov-a/modelo-x": [
            {"comportamento": "falha-transitoria", "retry_after_ms": 5000},
            "sucesso"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-429")
        self.assertEqual(r.status, "sucesso")
        retry = lab.kernel.retries[0]
        self.assertTrue(retry.respeitou_retry_after)
        self.assertGreaterEqual(retry.backoff_ms, 5000)

    # -- falhas tipadas ------------------------------------------------------

    def test_falha_quota_tipada(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-quota"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-q")
        attempt = lab.kernel.attempts[r.attempt_id]["attempt"]
        self.assertEqual(attempt.resultado, "falha-quota")

    def test_saida_invalida_falha_contrato_zero_retry(self):
        lab = self._lab({"prov-a/modelo-x": ["saida-invalida"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-inv")
        attempt = lab.kernel.attempts[r.attempt_id]["attempt"]
        self.assertEqual(attempt.resultado, "falha-contrato")
        self.assertEqual(len(lab.kernel.retries), 0)  # 4xx nunca repete

    def test_4xx_contrato_zero_retry_fallback_direto(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-contrato"]})
        wu, d = self._wu_decisao(lab, alternativas=self._alt_y(lab))
        r = lab.execution.executar(wu, d, idempotency_key="op-4xx")
        self.assertEqual(r.status, "sucesso")
        self.assertEqual(len(lab.kernel.retries), 0)
        self.assertEqual(len(lab.kernel.fallbacks), 1)
        fb = lab.kernel.fallbacks[0]
        self.assertEqual(fb.de_executor["modelo"], "modelo-x")
        self.assertEqual(fb.para_executor["modelo"], "modelo-y")

    # -- fallback / envelope ---------------------------------------------------

    def test_fallback_dentro_do_envelope(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-quota"]})
        wu, d = self._wu_decisao(lab, alternativas=self._alt_y(lab))
        r = lab.execution.executar(wu, d, idempotency_key="op-fb")
        self.assertEqual(r.status, "sucesso")
        self.assertEqual(len(lab.kernel.fallbacks), 1)

    def test_fallback_fora_do_envelope_e_escalonamento(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-quota"]})
        wu, d = self._wu_decisao(lab, alternativas=self._alt_y(lab))
        # Envelope estreito: so modelo-x permitido; fallback para y = fora.
        d.aprovacao_custo = dict(lab.aprovacao,
                                 modelos_permitidos=["prov-a/modelo-x"])
        r = lab.execution.executar(wu, d, idempotency_key="op-fbx")
        self.assertEqual(r.status, "escalonado")
        self.assertEqual(r.detalhe, "fallback-fora-do-envelope")
        self.assertEqual(len(lab.kernel.fallbacks), 0)  # nao tentou
        self.assertTrue(any(e.motivo == "sem-alternativa"
                            for e in lab.kernel.escalacoes))

    # -- reroteamento e reparo (caminhos distintos) ------------------------------

    def test_reroteamento_nova_decisao_supersede_mesma_linhagem(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-quota"]})
        wu, d1 = self._wu_decisao(lab)
        r1 = lab.execution.executar(wu, d1, idempotency_key="op-rr")
        self.assertEqual(r1.status, "escalonado")
        d2 = lab.router.rerotear(
            wu, rota="padrao", selecao=lab.selecao("prov-b", "modelo-y"),
            aprovacao_custo=lab.aprovacao, motivo="quota de x esgotada")
        self.assertEqual(d2.supersede, d1.decisao_id)
        r2 = lab.execution.executar(wu, d2, idempotency_key="op-rr")
        self.assertEqual(r2.status, "sucesso")
        a1 = lab.kernel.attempts[r1.attempt_id]["attempt"]
        a2 = lab.kernel.attempts[r2.attempt_id]["attempt"]
        self.assertEqual(a1.linhagem_id, a2.linhagem_id)
        self.assertEqual(a1.work_unit_id, a2.work_unit_id)

    def test_attempt_com_decisao_supersedada_recusado(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-quota"]})
        wu, d1 = self._wu_decisao(lab)
        lab.execution.executar(wu, d1, idempotency_key="op-s1")
        d2 = lab.router.rerotear(
            wu, rota="padrao", selecao=lab.selecao("prov-b", "modelo-y"),
            aprovacao_custo=lab.aprovacao, motivo="rerota")
        # Tenta criar attempt com a decisao ANTIGA (supersedada).
        from ssc_p0.kernel import VinculoDivergente
        attempt = ct.ExecutionAttempt(
            attempt_id="x" * 32, work_unit_id=wu.work_unit_id,
            decisao_id=d1.decisao_id,
            linhagem_id=lab.kernel.envelope.linhagem_id,
            selecao_solicitada=d1.selecao, executor_resolvido={},
            executor_observado=None,
            vinculos=lab.kernel.vinculos_correntes(d1.hash_pacote),
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo=None, custo_medido=None, artefato_ref=None)
        with self.assertRaises(VinculoDivergente):
            lab.kernel.criar_attempt(attempt, None)

    def test_reparo_e_nova_workunit_nao_retry(self):
        lab = self._lab({"prov-a/modelo-x": ["falha-contrato"]})
        wu, d = self._wu_decisao(lab)
        r = lab.execution.executar(wu, d, idempotency_key="op-rep")
        lab.execution.encerrar_com_falha(wu, None)
        Juiz1.julgar(
            lab.kernel, wu, r.attempt_id,
            lambda saida, pacote, attempt: (
                [{"criterio": "saida valida", "evidencia": "invalida",
                  "passou": False}], "reprovado"))
        self.assertEqual(lab.kernel.work_units[wu.work_unit_id].estado,
                         "reprovada")
        filha = lab.router.reparar(
            lab.kernel.work_units[wu.work_unit_id],
            {"erro": "saida invalida do provider"})
        self.assertEqual(filha.tipo, "etapa")
        self.assertEqual(filha.parent_work_unit, wu.work_unit_id)
        self.assertEqual(len(lab.kernel.retries), 0)  # reparo != retry

    # -- teto de custo -----------------------------------------------------------

    def test_teto_de_custo_escalation_orcamento_sem_chamada_posterior(self):
        lab = self._lab(**{"teto_custo": 0.011})
        wu, d = self._wu_decisao(lab)
        r1 = lab.execution.executar(wu, d, idempotency_key="op-t1")
        self.assertEqual(r1.status, "sucesso")
        # Segunda rodada: consumido + previsto > teto -> orcamento, zero chamadas.
        d2 = lab.router.rerotear(
            wu, rota="padrao", selecao=lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=lab.aprovacao, motivo="nova rodada")
        n_attempts_antes = len(lab.kernel.attempts)
        r2 = lab.execution.executar(wu, d2, idempotency_key="op-t2")
        self.assertEqual(r2.status, "escalonado")
        self.assertEqual(r2.detalhe, "orcamento")
        self.assertTrue(any(e.motivo == "orcamento"
                            for e in lab.kernel.escalacoes))
        self.assertEqual(len(lab.kernel.attempts), n_attempts_antes)


if __name__ == "__main__":
    unittest.main()
