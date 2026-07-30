"""WorkUnits: DAG/ciclo, anti-competicao (IW-3), IW-1, IW-2, IW-4."""

import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.router import TaskRouter


class TestWorkUnits(unittest.TestCase):
    def setUp(self):
        self.lab = apoio.novo_lab()
        self.k = self.lab.kernel

    def tearDown(self):
        apoio.limpar_lab(self.lab)

    def _pai(self):
        return self.lab.router.forjar(
            intencao="decompor trabalho em filhos de teste",
            criterios={"tipo": "dag"}, tipo="decomposicao", nivel="L2",
            classe="C0")

    def _filho(self, pai, intencao, **kw):
        return self.lab.router.forjar(
            intencao=intencao, criterios={"tipo": "x"}, tipo="etapa",
            nivel="L1", classe="C0", parent=pai.work_unit_id, **kw)

    def test_iw3_anti_competicao_recusada(self):
        pai = self._pai()
        self._filho(pai, "gerar o sumario executivo do relatorio final")
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self._filho(pai, "gerar o sumario executivo do relatorio "
                             "final agora")
        self.assertIn("IW-3", str(ctx.exception))
        # recusa registrada como evento
        self.assertTrue(any("IW-3" in r.get("motivo", "")
                            for r in self.k.recusas))

    def test_iw3_intencoes_distintas_aceitas(self):
        pai = self._pai()
        self._filho(pai, "coletar amostras do sensor norte")
        self._filho(pai, "redigir parecer juridico tributario")

    def test_dag_ciclo_recusado_antes_de_execucao(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            TaskRouter.validar_plano([
                {"id": "a", "depende_de": ["b"]},
                {"id": "b", "depende_de": ["a"]},
            ])
        self.assertIn("ciclo", str(ctx.exception))
        # DAG valido passa
        TaskRouter.validar_plano([
            {"id": "a", "depende_de": []},
            {"id": "b", "depende_de": ["a"]},
        ])

    def test_iw2_mais_de_12_filhos_recusado(self):
        pai = self._pai()
        for i in range(12):
            self._filho(pai, f"acao-{i:02d} palavra{i}a palavra{i}b palavra{i}c")
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self._filho(pai, "decimo terceiro filho completamente distinto")
        self.assertIn("IW-2", str(ctx.exception))

    def test_iw4_classe_c2_nasce_aguardando_aprovacao(self):
        wu = self.lab.router.forjar(
            intencao="mudanca estrutural de teste", criterios={"tipo": "x"},
            tipo="ato", nivel="L1", classe="C2")
        # O objeto retornado e uma copia; o estado vivo fica no kernel.
        self.assertEqual(self.k.work_units[wu.work_unit_id].estado,
                         "aguardando-aprovacao")
        self.lab.control.aprovar_work_unit(
            wu.work_unit_id, {"aprovador": "soberano", "parecer": "aprovo"})
        self.assertEqual(self.k.work_units[wu.work_unit_id].estado, "aprovada")

    def test_iw4_tipo1_nasce_aguardando_aprovacao(self):
        wu = self.lab.router.forjar(
            intencao="acao irreversivel de teste", criterios={"tipo": "x"},
            tipo="ato", tipo_decisao="tipo-1", nivel="L1", classe="C0")
        self.assertEqual(self.k.work_units[wu.work_unit_id].estado,
                         "aguardando-aprovacao")

    def test_iw1_sem_decisao_vigente_nao_executa(self):
        wu = self.lab.router.forjar(
            intencao="tarefa sem decisao de rota", criterios={"tipo": "x"},
            tipo="ato", nivel="L1", classe="C0")
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.k.transicionar_work_unit(wu.work_unit_id, "em-execucao", None)
        self.assertIn("IW-1", str(ctx.exception))

    def test_dependencia_nao_concluida_bloqueia_execucao(self):
        pai = self._pai()
        a = self._filho(pai, "produzir insumo alfa")
        b = self._filho(pai, "consumir insumo beta",
                        depende_de=[a.work_unit_id])
        d = self.lab.router.propor_decisao(
            b, rota="barata", selecao=self.lab.selecao("prov-a", "modelo-l1"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        from ssc_p0.canonico import novo_id
        attempt = ct.ExecutionAttempt(
            attempt_id=novo_id(), work_unit_id=b.work_unit_id,
            decisao_id=d.decisao_id, linhagem_id=self.k.envelope.linhagem_id,
            selecao_solicitada=d.selecao, executor_resolvido={},
            executor_observado=None,
            vinculos=self.k.vinculos_correntes(d.hash_pacote),
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo=None, custo_medido=None, artefato_ref=None)
        with self.assertRaises(ct.FalhaContrato):
            self.k.criar_attempt(attempt, None)


if __name__ == "__main__":
    unittest.main()
