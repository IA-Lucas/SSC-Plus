"""P0-21 FASE 3 [4/6] — as sete recusas de `registrar_veredito`.

  L607 attempt nao concluido                    ALCANCAVEL
  L613 veredito para workunit desconhecida      ALCANCAVEL
  L621 decisao do attempt fora da cadeia da WU  INALCANCAVEL (medido)
  L625 veredito fora da linhagem da sessao      INALCANCAVEL (medido)
  L633 contexto_ref divergente do da WorkUnit   ALCANCAVEL
  L658 IV-1: juiz sem independencia             ALCANCAVEL
  L660 veredito com workunit em estado errado   ALCANCAVEL

O veredito e o que CONCLUI uma WorkUnit. Depois dele a WU sai do fluxo
e o resultado entra na linhagem como fato. As sete recusas existem para
que nenhum veredito conclua o que nao julgou.

## Os cinco alcancaveis, pelo caminho que a operacao percorre

Todos partem do FLUXO REAL — forjar, decidir, executar pelo gateway,
julgar por `Juiz1.julgar` — e nao de vereditos montados a mao:

- **L607**: um attempt CRIADO e DESPACHADO de verdade, mas ainda nao
  concluido. E o julgamento que chega antes da resposta;
- **L613**: veredito cujo `alvo.work_unit_id` nao existe;
- **L633**: veredito com `contexto_ref` que nao e o da WorkUnit — o juiz
  que julgou olhando outro contexto;
- **L658**: **IV-1**, e o mais importante dos sete. Um juiz da camada
  `juiz-llm` sem independencia declarada. O fluxo de duas camadas e
  percorrido de verdade (`Juiz1.julgar(conclui=False)` deixa a WU em
  `aguardando-validacao`, que e como a segunda camada a encontra) e so
  entao chega o veredito do juiz nao independente;
- **L660**: julgar duas vezes. A WorkUnit ja esta `concluida`, e um
  segundo veredito a reabriria.

## Os dois INALCANCAVEIS — medidos, nao presumidos

`L621` exige `attempt.decisao_id` apontando para uma decisao de OUTRA
WorkUnit. Mas `criar_attempt` recusa todo attempt cuja `decisao_id` nao
seja a **vigente da propria WorkUnit** (`self.vigente.get(...)`), e a
decisao vigente de uma WorkUnit tem, por construcao,
`decisao.work_unit_id` igual a ela. Nao ha attempt registrado que
viole isso.

`L625` exige `attempt.linhagem_id` ou `wu.linhagem_id` fora da linhagem
da sessao. Os dois campos sao conferidos na ENTRADA — `criar_attempt`
recusa o attempt (IS-1, testado em `test_p0_kernel_attempt_p1a38`) e
`registrar_work_unit` recusa a WorkUnit. Nada com linhagem errada chega
a existir.

Os dois sao DEFESA EM PROFUNDIDADE. O que este arquivo exerce e a
propriedade de onde sai a inalcancabilidade — que todo attempt
registrado aponta para a decisao vigente da propria WorkUnit, e que
tudo esta na linhagem da sessao — em vez de fabricar o estado que a
operacao nao produz.

O QUE ESTES TESTES NAO COBREM, declarado:
- IV-2 (veto deterministico nao anulavel), IV-3 (`criterios_ref`),
  `artefato_ref` fora da cadeia e "veredito cruzado" ja eram
  alcancados e nao sao destes sete ramos;
- o `Juiz2` real (juiz-llm falso deterministico) nao e usado: o
  veredito de camada `juiz-llm` e montado a partir do veredito
  deterministico REAL, alterando apenas camada e independencia. Nada
  aqui prova comportamento de juiz-llm;
- nao se afirma que os criterios de independencia sejam os certos —
  so que o guarda recusa quando eles sao negados;
- nao se cobre veredito concorrente sobre o mesmo attempt.
"""

import dataclasses
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import novo_id
from ssc_p0.judge import Juiz1
from ssc_p0.kernel import TransicaoIlegal

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}

APROVA = ([{"criterio": "saida nao vazia", "evidencia": "-", "passou": True}],
          "aprovado")


class RecusasDoVeredito(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel

    def _wu(self, marca: str) -> ct.WorkUnit:
        return self.lab.router.forjar(
            intencao=f"tarefa {marca} para as recusas de veredito",
            criterios={"tipo": "saida-nao-vazia"}, tipo="ato", nivel="L2",
            perfil=dict(PERFIL), classe="C1")

    def _ate_o_attempt(self, marca: str):
        """Fluxo real ate ter um attempt CONCLUIDO com sucesso."""
        wu = self._wu(marca)
        decisao = self.lab.router.propor_decisao(
            wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo=f"decisao {marca}")
        resultado = self.lab.execution.executar(
            wu, decisao, idempotency_key=f"idem-{marca}", entrada=b"dados")
        self.assertEqual(resultado.status, "sucesso")
        return wu, decisao, resultado.attempt_id

    def _julgar(self, wu, attempt_id, conclui=True):
        return Juiz1.julgar(self.kernel, wu, attempt_id,
                            lambda saida, pacote, attempt: APROVA,
                            conclui=conclui)

    # --- L607: julgamento antes da resposta ----------------------------

    def test_veredito_sobre_attempt_ainda_nao_concluido_e_recusado(self):
        wu = self._wu("nao-concluida")
        decisao = self.lab.router.propor_decisao(
            wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="decisao")
        attempt = ct.ExecutionAttempt(
            attempt_id=novo_id(), work_unit_id=wu.work_unit_id,
            decisao_id=decisao.decisao_id,
            linhagem_id=self.kernel.envelope.linhagem_id,
            selecao_solicitada=dict(decisao.selecao),
            executor_resolvido=dict(decisao.selecao), executor_observado=None,
            vinculos=self.kernel.vinculos_correntes(decisao.hash_pacote),
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo=None, custo_medido=None, artefato_ref=None)
        ev = self.kernel.criar_attempt(attempt, None)
        self.kernel.despachar_attempt(attempt.attempt_id, ev.evento_id)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self._julgar(wu, attempt.attempt_id)
        self.assertIn("exige attempt concluido", str(ctx.exception))

    # --- L613 / L633 / L660: sobre um veredito REAL alterado -----------

    def test_veredito_para_workunit_desconhecida_e_recusado(self):
        wu, _, attempt_id = self._ate_o_attempt("desconhecida")
        real = self._julgar(wu, attempt_id, conclui=False)
        alheio = dataclasses.replace(
            real, veredito_id=novo_id(),
            alvo={**real.alvo, "work_unit_id": "wu-que-nao-existe"})
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_veredito(alheio, None)
        self.assertIn("workunit desconhecida", str(ctx.exception))

    def test_veredito_com_contexto_de_outra_workunit_e_recusado(self):
        wu, _, attempt_id = self._ate_o_attempt("contexto")
        real = self._julgar(wu, attempt_id, conclui=False)
        torto = dataclasses.replace(real, veredito_id=novo_id(),
                                    contexto_ref="0" * 64)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_veredito(torto, None)
        self.assertIn("contexto_ref do veredito diverge", str(ctx.exception))

    def test_segundo_veredito_sobre_workunit_ja_concluida_e_recusado(self):
        wu, _, attempt_id = self._ate_o_attempt("dois-vereditos")
        primeiro = self._julgar(wu, attempt_id)
        self.assertEqual(self.kernel.work_units[wu.work_unit_id].estado,
                         "concluida")
        segundo = dataclasses.replace(primeiro, veredito_id=novo_id())
        with self.assertRaises(TransicaoIlegal) as ctx:
            self.kernel.registrar_veredito(segundo, None)
        self.assertIn("veredito com workunit em", str(ctx.exception))

    # --- L658: IV-1, o juiz sem independencia --------------------------

    def test_juiz_llm_sem_independencia_e_recusado(self):
        # O fluxo de DUAS CAMADAS, percorrido: a deterministica aprova
        # sem concluir, e a WorkUnit fica `aguardando-validacao` — que e
        # o estado em que a segunda camada a encontra em operacao.
        wu, _, attempt_id = self._ate_o_attempt("iv1")
        self._julgar(wu, attempt_id, conclui=False)
        self.assertEqual(self.kernel.work_units[wu.work_unit_id].estado,
                         "aguardando-validacao")
        base = self.kernel.vereditos[-1]
        for negado in ("provedor_distinto_do_executor", "modelo_distinto"):
            with self.subTest(negado=negado):
                sem_indep = dataclasses.replace(
                    base, veredito_id=novo_id(), camada="juiz-llm",
                    independencia={**base.independencia, negado: False})
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.registrar_veredito(sem_indep, None)
                self.assertIn("IV-1: juiz sem independencia",
                              str(ctx.exception))

    def test_juiz_llm_com_independencia_atravessa(self):
        # Contraprova indispensavel de IV-1: sem ela, um guarda que
        # recusasse toda camada juiz-llm passaria no teste acima.
        wu, _, attempt_id = self._ate_o_attempt("iv1-ok")
        self._julgar(wu, attempt_id, conclui=False)
        base = self.kernel.vereditos[-1]
        segunda_camada = dataclasses.replace(
            base, veredito_id=novo_id(), camada="juiz-llm")
        evento = self.kernel.registrar_veredito(segunda_camada, None)
        self.assertIsNotNone(evento.evento_id)
        self.assertEqual(self.kernel.work_units[wu.work_unit_id].estado,
                         "concluida")

    # --- os dois INALCANCAVEIS: a invariante, exercida -----------------

    def test_todo_attempt_aponta_para_a_decisao_vigente_da_propria_wu(self):
        # A invariante de onde sai a inalcancabilidade de L621. Medida
        # sobre attempts REAIS de duas WorkUnits distintas.
        for marca in ("inv-a", "inv-b"):
            self._ate_o_attempt(marca)
        self.assertGreaterEqual(len(self.kernel.attempts), 2)
        for attempt_id, reg in self.kernel.attempts.items():
            attempt = reg["attempt"]
            with self.subTest(attempt=attempt_id[:8]):
                decisao = self.kernel.decisoes[attempt.decisao_id]
                self.assertEqual(decisao.work_unit_id, attempt.work_unit_id)

    def test_tudo_que_existe_esta_na_linhagem_da_sessao(self):
        # A invariante de onde sai a inalcancabilidade de L625.
        self._ate_o_attempt("inv-linhagem")
        linhagem = self.kernel.envelope.linhagem_id
        for wid, wu in self.kernel.work_units.items():
            with self.subTest(work_unit=wid[:8]):
                self.assertEqual(wu.linhagem_id, linhagem)
        for attempt_id, reg in self.kernel.attempts.items():
            with self.subTest(attempt=attempt_id[:8]):
                self.assertEqual(reg["attempt"].linhagem_id, linhagem)

    # --- contraprova geral ---------------------------------------------

    def test_veredito_legitimo_conclui_a_workunit(self):
        wu, _, attempt_id = self._ate_o_attempt("legitimo")
        veredito = self._julgar(wu, attempt_id)
        self.assertEqual(veredito.resultado, "aprovado")
        self.assertEqual(self.kernel.work_units[wu.work_unit_id].estado,
                         "concluida")


if __name__ == "__main__":
    unittest.main()
