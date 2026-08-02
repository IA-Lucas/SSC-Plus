"""P0-21 FASE 3 [3/6] — as cinco recusas do ExecutionAttempt.

  L475 `criar_attempt`     attempt de outra linhagem (IS-1)
  L491 `criar_attempt`     vinculos do attempt divergentes
  L500 `criar_attempt`     workunit em estado que nao aceita attempt
  L527 `concluir_attempt`  resultado fora do enum
  L529 `concluir_attempt`  efeito_externo=incerto sem resultado indeterminado

O attempt e o objeto que representa UMA chamada externa. As tres
recusas da criacao correm ANTES de qualquer invocacao — e duas delas
gravam evento de recusa, de modo que a tentativa fica na cadeia mesmo
sem ter acontecido. As duas da conclusao protegem a outra ponta: o que
foi registrado sobre uma chamada que ja ocorreu.

A L529 e a mais importante das cinco e a que menos parece guarda:
`efeito_externo == "incerto"` obriga `resultado == "indeterminado"`.
E a regra IR-2 escrita como codigo — **efeito incerto nunca e assumido
como sucesso**. Sem ela, uma chamada cujo efeito externo ninguem sabe
poderia ser gravada como "sucesso" e a WorkUnit concluiria sobre um
resultado que talvez nao exista.

O CASO QUE OCORRE, por ramo:
- L475/L491: o attempt chega com linhagem ou vinculos que nao sao os do
  estado corrente — o `ExecutionGateway` os calcula na hora, de modo que
  divergir e chegar de fora ou chegar velho;
- L500: attempt para uma WorkUnit **ja concluida**. O fluxo real inteiro
  e percorrido primeiro (forjar, decidir, executar, julgar) e so entao
  se tenta o attempt — que e exatamente o despacho duplicado ou o retry
  tardio;
- L527/L529: o attempt existe, foi despachado de verdade, e a CONCLUSAO
  e que carrega o valor invalido.

O QUE ESTES TESTES NAO COBREM, declarado:
- `RoutingDecision supersedada` (a outra recusa de `criar_attempt`) ja
  era alcancada e nao e destes cinco ramos;
- nada aqui prova que o provedor real produza `efeito_externo` correto:
  na P0 o provedor e falso e deterministico, e quem preenche o campo e
  o gateway;
- nao se cobre conclusao concorrente do mesmo attempt;
- os enums (`RESULTADOS_ATTEMPT`) sao tomados como dados: nao se afirma
  que a lista seja a lista certa.
"""

import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import novo_id
from ssc_p0.kernel import TransicaoIlegal, VinculoDivergente

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class RecusasDoAttempt(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel
        self.wu = self.lab.router.forjar(
            intencao="tarefa base para as recusas de attempt",
            criterios={"tipo": "saida-nao-vazia"}, tipo="ato", nivel="L2",
            perfil=dict(PERFIL), classe="C1")
        self.decisao = self.lab.router.propor_decisao(
            self.wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="decisao legitima")

    def _attempt(self, **sobre) -> ct.ExecutionAttempt:
        campos = {
            "attempt_id": novo_id(), "work_unit_id": self.wu.work_unit_id,
            "decisao_id": self.decisao.decisao_id,
            "linhagem_id": self.kernel.envelope.linhagem_id,
            "selecao_solicitada": dict(self.decisao.selecao),
            "executor_resolvido": dict(self.decisao.selecao),
            "executor_observado": None,
            "vinculos": self.kernel.vinculos_correntes(
                self.decisao.hash_pacote),
            "inicio": None, "fim": None, "captura": {}, "resultado": None,
            "efeito_externo": None, "custo_medido": None,
            "artefato_ref": None}
        campos.update(sobre)
        return ct.ExecutionAttempt(**campos)

    # --- criacao: antes de qualquer invocacao --------------------------

    def test_attempt_de_outra_linhagem_e_recusado(self):
        with self.assertRaises(VinculoDivergente) as ctx:
            self.kernel.criar_attempt(
                self._attempt(linhagem_id="linhagem-alheia"), None)
        self.assertIn("outra linhagem", str(ctx.exception))

    def test_attempt_com_vinculos_divergentes_e_recusado(self):
        alvo = self._attempt(vinculos={"hash_envelope": "0" * 64})
        with self.assertRaises(VinculoDivergente) as ctx:
            self.kernel.criar_attempt(alvo, None)
        self.assertIn("vinculos do attempt divergentes", str(ctx.exception))
        self.assertNotIn(alvo.attempt_id, self.kernel.attempts)

    def test_a_recusa_por_vinculos_deixa_evento_de_recusa_na_cadeia(self):
        # RA-3: a tentativa recusada nao some. Um attempt barrado sem
        # rastro seria indistinguivel de um attempt que nunca existiu.
        antes = self.kernel.log.seq_atual()
        with self.assertRaises(VinculoDivergente):
            self.kernel.criar_attempt(
                self._attempt(vinculos={"hash_envelope": "0" * 64}), None)
        self.assertGreater(self.kernel.log.seq_atual(), antes)

    def test_attempt_para_workunit_ja_concluida_e_recusado(self):
        # O fluxo real inteiro primeiro; so entao o despacho tardio.
        apoio.fluxo_sucesso(self.lab, intencao="tarefa que conclui")
        concluidas = [w for w in self.kernel.work_units.values()
                      if w.estado == "concluida"]
        self.assertTrue(concluidas, "o fluxo nao concluiu nenhuma WorkUnit")
        alvo = concluidas[0]
        decisao_id = self.kernel.vigente[alvo.work_unit_id]
        decisao = self.kernel.decisao_canonica(decisao_id)
        attempt = self._attempt(
            work_unit_id=alvo.work_unit_id, decisao_id=decisao_id,
            selecao_solicitada=dict(decisao.selecao),
            executor_resolvido=dict(decisao.selecao),
            vinculos=self.kernel.vinculos_correntes(decisao.hash_pacote))
        with self.assertRaises(TransicaoIlegal) as ctx:
            self.kernel.criar_attempt(attempt, None)
        self.assertIn("nao aceita attempt", str(ctx.exception))

    # --- conclusao: o que se registra sobre a chamada ------------------

    def _captura(self) -> dict:
        """Captura estruturada REAL: bytes no CAS, como o gateway grava."""
        ref = self.kernel.cas.gravar(b"saida de prova")
        return {"saida_estruturada_ref": ref, "saida_final_ref": ref,
                "stderr_ref": None, "codigo_saida": 0, "assinatura": None}

    def _despachado(self) -> str:
        attempt = self._attempt()
        ev = self.kernel.criar_attempt(attempt, None)
        self.kernel.despachar_attempt(attempt.attempt_id, ev.evento_id)
        return attempt.attempt_id

    def test_resultado_fora_do_enum_e_recusado(self):
        attempt_id = self._despachado()
        for ruim in ("ok", "passou", "SUCESSO", "indefinido"):
            with self.subTest(resultado=ruim):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.concluir_attempt(
                        attempt_id, ruim, "nenhum", self._captura(), None,
                        None, None, None)
                self.assertIn("resultado fora do enum", str(ctx.exception))

    def test_efeito_incerto_com_resultado_de_sucesso_e_recusado(self):
        # IR-2: efeito externo incerto NUNCA vira sucesso.
        attempt_id = self._despachado()
        for resultado in ("sucesso", "falha-transitoria"):
            with self.subTest(resultado=resultado):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.concluir_attempt(
                        attempt_id, resultado, "incerto", self._captura(),
                        None, None, None, None)
                self.assertIn("efeito_externo=incerto", str(ctx.exception))

    def test_efeito_incerto_com_indeterminado_atravessa(self):
        # A outra metade da regra: incerto + indeterminado e legitimo, e
        # e assim que um attempt orfao termina. Sem esta contraprova, um
        # guarda que recusasse todo "incerto" passaria acima.
        attempt_id = self._despachado()
        evento = self.kernel.concluir_attempt(
            attempt_id, "indeterminado", "incerto", self._captura(), None,
            None, None, None)
        self.assertIsNotNone(evento.evento_id)
        reg = self.kernel.attempts[attempt_id]
        self.assertEqual(reg["attempt"].resultado, "indeterminado")

    def test_conclusao_legitima_continua_atravessando(self):
        attempt_id = self._despachado()
        evento = self.kernel.concluir_attempt(
            attempt_id, "sucesso", "nenhum", self._captura(), None, None,
            None, None)
        self.assertIsNotNone(evento.evento_id)
        self.assertEqual(
            self.kernel.attempts[attempt_id]["attempt"].resultado, "sucesso")


if __name__ == "__main__":
    unittest.main()
