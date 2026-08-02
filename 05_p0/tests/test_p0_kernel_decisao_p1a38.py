"""P0-21 FASE 3 [2/6] — as quatro recusas de RoutingDecision.

Quatro ramos medidos como NAO ALCANCADOS:

  L431 `registrar_decisao`  decisao para workunit desconhecida
  L434 `registrar_decisao`  vinculos divergentes do estado corrente
  L438 `registrar_decisao`  reroteamento sem supersede = vigente
  L461 `decisao_canonica`   decisao desconhecida

A RoutingDecision e o objeto que autoriza gasto. Tudo o que a P0
promete sobre custo — teto zero, nenhuma chamada sem rota aprovada —
depende de a decisao registrada ser a MESMA que a execucao usa. Estes
quatro ramos sao o que impede uma decisao solta, de outra WorkUnit, de
outro estado ou simplesmente inexistente de virar autorizacao.

O CASO QUE OCORRE, por ramo — medido antes de escrito:

- **L431** e exercido pelo **router real**: `propor_decisao` sobre uma
  WorkUnit que nunca foi registrada. Nao e o kernel chamado a seco: e o
  caminho por onde toda decisao nasce;
- **L434** e a decisao cujos vinculos nao descrevem mais o estado. Ela
  so pode CHEGAR ao kernel ja divergente — o router os calcula na hora
  —, e chegar divergente e exatamente o que o guarda nomeia: pacote
  trocado sob uma decisao com o resto intacto;
- **L438** e o reroteamento que nao aponta para a decisao vigente. O
  `TaskRouter.rerotear` preenche `supersede` sozinho, de modo que este
  ramo e a rede que pega quem NAO passa pelo router;
- **L461** e exercido pelo seu **ponto de chamada**, `criar_attempt`, e
  nao pela funcao a seco. E ali que a decisao desconhecida seria
  transformada em gasto.

O QUE ESTES TESTES NAO COBREM, declarado:
- `DecisaoMutada` (mutacao apos o registro) nao e destes quatro ramos e
  nao e coberta aqui;
- os tres ramos de `registrar_decisao` sao exercidos com objetos
  PRODUZIDOS PELO ROUTER e alterados em um campo. Nao ha, no acervo,
  um segundo produtor de RoutingDecision, de modo que "decisao que
  chega divergente" e uma hipotese sobre um chamador futuro — declarada
  como tal, nao mascarada;
- nada aqui prova que a Policy vete o que deve vetar: o veto corre
  ANTES e e outro guarda (`P0-24`);
- nao se cobre reroteamento concorrente.
"""

import dataclasses
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import novo_id
from ssc_p0.kernel import VinculoDivergente

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class RecusasDeRoutingDecision(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel
        self.wu = self.lab.router.forjar(
            intencao="tarefa base para as recusas de decisao",
            criterios={"tipo": "saida-nao-vazia"}, tipo="ato", nivel="L2",
            perfil=dict(PERFIL), classe="C1")

    def _decisao(self, **sobre) -> ct.RoutingDecision:
        d = self.lab.router.propor_decisao(
            self.wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="decisao legitima")
        return dataclasses.replace(d, **sobre) if sobre else d

    # --- L431: decisao para WorkUnit desconhecida ----------------------

    def test_router_recusa_decisao_para_workunit_nunca_registrada(self):
        # Pelo ROUTER, que e por onde toda decisao nasce.
        solta = dataclasses.replace(self.wu, work_unit_id="wu-nao-registrada")
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.lab.router.propor_decisao(
                solta, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=self.lab.aprovacao, motivo="solta")
        self.assertIn("workunit desconhecida", str(ctx.exception))

    def test_decisao_para_workunit_desconhecida_nao_fica_vigente(self):
        # O dano nao e a excecao: e a decisao solta virar autorizacao.
        solta = dataclasses.replace(self.wu, work_unit_id="wu-fantasma")
        with self.assertRaises(ct.FalhaContrato):
            self.lab.router.propor_decisao(
                solta, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=self.lab.aprovacao, motivo="solta")
        self.assertNotIn("wu-fantasma", self.kernel.vigente)

    # --- L434: vinculos divergentes ------------------------------------

    def test_decisao_com_pacote_trocado_e_recusada(self):
        trocada = self._decisao(decisao_id=novo_id(), hash_pacote="0" * 64)
        with self.assertRaises(VinculoDivergente) as ctx:
            self.kernel.registrar_decisao(trocada, None)
        self.assertIn("vinculos da decisao divergem", str(ctx.exception))

    def test_decisao_divergente_nao_entra_no_indice_de_decisoes(self):
        trocada = self._decisao(decisao_id=novo_id(), hash_pacote="0" * 64)
        with self.assertRaises(VinculoDivergente):
            self.kernel.registrar_decisao(trocada, None)
        self.assertNotIn(trocada.decisao_id, self.kernel.decisoes)

    # --- L438: supersede fora da vigente -------------------------------

    def test_reroteamento_sem_supersede_da_vigente_e_recusado(self):
        self._decisao()  # ha uma decisao vigente
        errada = self._decisao(decisao_id=novo_id(),
                               supersede="decisao-que-nunca-existiu")
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_decisao(errada, None)
        self.assertIn("supersede = decisao vigente", str(ctx.exception))

    def test_o_router_preenche_supersede_sozinho_e_o_reroteamento_passa(self):
        # Contraprova e medicao ao mesmo tempo: o caminho legitimo do
        # reroteamento nao depende de quem chama acertar o campo.
        primeira = self._decisao()
        segunda = self.lab.router.rerotear(
            self.wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="nova rodada")
        self.assertEqual(segunda.supersede, primeira.decisao_id)
        self.assertEqual(self.kernel.vigente[self.wu.work_unit_id],
                         segunda.decisao_id)

    # --- L461: decisao desconhecida, no PONTO DE CHAMADA ---------------

    def test_attempt_que_aponta_para_decisao_inexistente_e_recusado(self):
        # O ponto de chamada de `decisao_canonica` e `criar_attempt` — e
        # e ali que a decisao desconhecida viraria gasto.
        decisao = self._decisao()
        attempt = ct.ExecutionAttempt(
            attempt_id=novo_id(), work_unit_id=self.wu.work_unit_id,
            linhagem_id=self.kernel.envelope.linhagem_id,
            decisao_id="decisao-que-nao-existe",
            selecao_solicitada=dict(decisao.selecao),
            executor_resolvido=dict(decisao.selecao),
            executor_observado=None,
            vinculos=self.kernel.vinculos_correntes(decisao.hash_pacote),
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo="nenhum", custo_medido=None, artefato_ref=None)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.criar_attempt(attempt, None)
        self.assertIn("decisao desconhecida", str(ctx.exception))
        self.assertNotIn(attempt.attempt_id, self.kernel.attempts)

    # --- contraprova geral ---------------------------------------------

    def test_o_fluxo_legitimo_continua_registrando_e_executando(self):
        # Sem ela, um `registrar_decisao` que recusasse sempre passaria
        # em todos os testes acima e ninguem veria.
        decisao = self._decisao()
        self.assertEqual(self.kernel.vigente[self.wu.work_unit_id],
                         decisao.decisao_id)
        self.assertIs(self.kernel.decisao_canonica(decisao.decisao_id),
                      self.kernel.decisoes[decisao.decisao_id])
        resultado = self.lab.execution.executar(
            self.wu, decisao, idempotency_key="idem-ok", entrada=b"dados")
        self.assertEqual(resultado.status, "sucesso")


if __name__ == "__main__":
    unittest.main()
