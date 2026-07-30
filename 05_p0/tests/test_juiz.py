"""Juiz: IV-2 nao anulavel, veredito vinculado, independencia, alias."""

import tempfile
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.judge import IndependenciaImpossivel, Juiz1, Juiz2


class TestJuiz(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lab = apoio.novo_lab(self._tmp.name)
        self.k = self.lab.kernel

    def tearDown(self):
        self._tmp.cleanup()

    def _reprovar_deterministico(self):
        wu, d, r, _ = None, None, None, None
        wu = self.lab.router.forjar(
            intencao="artefato que sera reprovado", criterios={"tipo": "x"},
            tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        r = self.lab.execution.executar(wu, d, idempotency_key="op-j")
        v = Juiz1.julgar(
            self.k, wu, r.attempt_id,
            lambda saida, pacote, attempt: (
                [{"criterio": "criterio mecanico", "evidencia": "falhou",
                  "passou": False}], "reprovado"))
        return wu, d, r, v

    def test_iv2_veto_deterministico_nao_anulavel_por_juiz_llm(self):
        wu, d, r, v = self._reprovar_deterministico()
        self.assertEqual(v.resultado, "reprovado")
        juiz2 = self.lab.juiz2()
        with self.assertRaises(ct.FalhaContrato) as ctx:
            juiz2.julgar(
                self.k, wu, r.attempt_id,
                lambda saida, attempt: (
                    [{"criterio": "redacao", "evidencia": "override",
                      "passou": True}], "aprovado"))
        self.assertIn("IV-2", str(ctx.exception))
        # Tentativa de anulacao registrada como invalida (recusa no log).
        self.assertTrue(any("IV-2" in rec.get("motivo", "")
                            for rec in self.k.recusas))

    def test_iv2_humano_tambem_nao_anula(self):
        wu, d, r, v = self._reprovar_deterministico()
        veredito_humano = ct.ValidationVerdict(
            veredito_id="h" * 32,
            alvo={"work_unit_id": wu.work_unit_id,
                  "artefato_ref": None, "attempt_id": r.attempt_id},
            camada="humana", verificador={"nome": "soberano"},
            pacote_juiz={}, criterios_ref=wu.criterios_aceite_ref,
            contexto_ref=wu.contexto_ref, independencia={},
            resultado="aprovado", criterios=[], efeitos={})
        with self.assertRaises(ct.FalhaContrato):
            self.k.registrar_veredito(veredito_humano, None)

    def test_veredito_sem_attempt_id_invalido(self):
        wu, d, r, v = apoio.fluxo_sucesso(self.lab)
        veredito = ct.ValidationVerdict(
            veredito_id="s" * 32,
            alvo={"work_unit_id": wu.work_unit_id, "artefato_ref": None},
            camada="deterministica", verificador={"nome": "j"},
            pacote_juiz={}, criterios_ref=wu.criterios_aceite_ref,
            contexto_ref=wu.contexto_ref, independencia={},
            resultado="aprovado", criterios=[], efeitos={})
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.k.registrar_veredito(veredito, None)
        self.assertIn("attempt_id", str(ctx.exception))

    def test_veredito_criterios_ref_divergente_invalido_iv3(self):
        wu, d, r, v = apoio.fluxo_sucesso(self.lab)
        veredito = ct.ValidationVerdict(
            veredito_id="c" * 32,
            alvo={"work_unit_id": wu.work_unit_id, "artefato_ref": None,
                  "attempt_id": r.attempt_id},
            camada="deterministica", verificador={"nome": "j"},
            pacote_juiz={}, criterios_ref="0" * 64,  # divergente do congelado
            contexto_ref=wu.contexto_ref, independencia={},
            resultado="aprovado", criterios=[], efeitos={})
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.k.registrar_veredito(veredito, None)
        self.assertIn("IV-3", str(ctx.exception))

    def test_juiz_llm_so_julga_apos_camada_deterministica(self):
        wu = self.lab.router.forjar(
            intencao="artefato julgado fora de ordem",
            criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        r = self.lab.execution.executar(wu, d, idempotency_key="op-jl")
        juiz2 = self.lab.juiz2()
        with self.assertRaises(ct.FalhaContrato) as ctx:
            juiz2.julgar(self.k, wu, r.attempt_id, None)
        self.assertIn("deterministica", str(ctx.exception))

    def test_fila_sem_candidato_independente_falha_fechada(self):
        wu, d, r, v = apoio.fluxo_sucesso(self.lab)
        juiz2 = Juiz2([{"provedor": "prov-a", "modelo": "modelo-x",
                        "effort": "alto"}], seed=1)
        with self.assertRaises(IndependenciaImpossivel):
            juiz2.julgar(self.k, wu, r.attempt_id, None)

    def test_alias_nao_prova_identidade_divergencia_registrada(self):
        self._tmp2 = tempfile.TemporaryDirectory()
        try:
            lab = apoio.novo_lab(self._tmp2.name, observados={
                "prov-a/modelo-l1": {"provedor": "prov-a",
                                     "modelo": "modelo-l1-REAL-DIFERENTE",
                                     "effort": "alto"}})
            wu = lab.router.forjar(
                intencao="tarefa roteada por alias", criterios={"tipo": "x"},
                tipo="ato", nivel="L1", classe="C0",
                perfil={"modalidade": "texto", "ferramentas": [],
                        "formato_saida": "livre", "contexto_max_tokens": 100,
                        "dominio": "geral", "privacidade": "local-only",
                        "latencia_max_ms": None, "orcamento_max_custo": None})
            d = lab.router.propor_decisao(
                wu, rota="barata",
                selecao=lab.selecao("prov-a", "barato"),  # alias registrado
                aprovacao_custo=lab.aprovacao, motivo="alias")
            r = lab.execution.executar(wu, d, idempotency_key="op-alias")
            attempt = lab.kernel.attempts[r.attempt_id]["attempt"]
            self.assertTrue(attempt.executor_resolvido["alias_usado"])
            self.assertNotEqual(attempt.executor_observado["modelo"],
                                attempt.executor_resolvido["modelo"])
            # Evento tipado de divergencia gravado.
            from ssc_p0.evidence import EvidencePlane
            proj = EvidencePlane(lab.raiz, lab.envelope.sessao_id).projetar()
            self.assertEqual(len(proj["divergencias_observado_resolvido"]), 1)
            # O juiz calcula independencia sobre o OBSERVADO (nao o alias).
            Juiz1.julgar(lab.kernel, wu, r.attempt_id,
                         lambda saida, pacote, att: ([], "aprovado"),
                         conclui=False)
            juiz2 = lab.juiz2()
            v2 = juiz2.julgar(lab.kernel, wu, r.attempt_id, None)
            self.assertEqual(v2.independencia["base"], "observado")
            self.assertTrue(
                v2.independencia["provedor_distinto_do_executor"]
                and v2.independencia["modelo_distinto"])
        finally:
            self._tmp2.cleanup()


if __name__ == "__main__":
    unittest.main()
