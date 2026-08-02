"""P0-19 `judge.Juiz2` — o ramo de recusa que faltava. FASE 3.

A varredura mediu **1 de 2 ramos alcancados**, familia ISOLAMENTO. Os
dois sao as duas formas de a independencia ser IMPOSSIVEL:
- fila de candidatos VAZIA — recusada na construcao;
- fila que existe mas nao tem nenhum candidato independente do executor
  que produziu o artefato.

O CASO QUE OCORRE, e ele e o coracao do eixo: um juiz do MESMO provedor
e do MESMO modelo que o executor nao esta julgando, esta se conferindo.
A independencia e calculada ANTES de julgar, e sobre o executor
OBSERVADO quando ele existe — nao sobre o resolvido, que e o que se
pretendia usar e nem sempre e o que respondeu. Essa distincao e o motivo
de o calculo estar antes: julgar primeiro e conferir depois deixaria o
veredito pronto para ser gravado.

O teste usa o fluxo REAL — lab, WorkUnit forjada, execucao pelo gateway
— e chama `Juiz2.julgar` sobre o attempt que existiu.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao ha juiz LLM real: o veredito sem avaliador e derivado por seed,
  deterministico, e nada aqui prova comportamento de modelo;
- a independencia e por provedor/modelo declarados no candidato; nao se
  afirma que dois provedores distintos sejam de fato independentes no
  mundo (mesma familia de pesos, por exemplo);
- `rubrica_ref` e `hash_catalogo` entram no pacote do juiz e nao sao o
  objeto aqui.
"""

import unittest

import apoio
from ssc_p0.judge import IndependenciaImpossivel, Juiz2

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class RecusasDoJuizComIndependencia(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)

    def _ate_a_validacao(self, provedor="prov-a", modelo="modelo-x"):
        wu = self.lab.router.forjar(
            intencao="tarefa para o juiz com independencia",
            criterios={"tipo": "saida-nao-vazia"}, tipo="ato", nivel="L2",
            perfil=PERFIL, classe="C1")
        decisao = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao(provedor, modelo),
            aprovacao_custo=self.lab.aprovacao, motivo="P0-19")
        resultado = self.lab.execution.executar(
            wu, decisao, idempotency_key=f"p0-19-{wu.work_unit_id}",
            entrada=b"dados")
        self.assertEqual(resultado.status, "sucesso")
        return wu, resultado.attempt_id

    def _ate_o_juiz_llm(self, provedor="prov-a", modelo="modelo-x"):
        """Fluxo real ate onde o Juiz2 de fato atua.

        O kernel recusa veredito de juiz-llm sobre WorkUnit que nao
        passou pela camada deterministica — `Juiz1` roda antes, com
        `conclui=False` para manter a WU aguardando a camada seguinte.
        Julgar fora dessa ordem mediria outro guarda.
        """
        from ssc_p0.judge import Juiz1
        wu, attempt_id = self._ate_a_validacao(provedor, modelo)
        Juiz1.julgar(
            self.lab.kernel, wu, attempt_id,
            lambda saida, pacote, attempt: (
                [{"criterio": "saida nao vazia", "evidencia": str(len(saida)),
                  "passou": True}], "aprovado"),
            conclui=False)
        return wu, attempt_id

    def test_fila_vazia_nao_deixa_o_juiz_nascer(self):
        # Recusar na construcao e mais forte: um juiz sem fila nunca
        # chega a julgar coisa nenhuma.
        for fila in ([], (), None):
            with self.subTest(fila=repr(fila)):
                with self.assertRaises(IndependenciaImpossivel) as ctx:
                    Juiz2(fila, seed=7)
                self.assertIn("fila de candidatos vazia", str(ctx.exception))

    def test_fila_sem_candidato_independente_e_recusada(self):
        # O caso que faltava: a fila existe, mas o unico candidato e o
        # PROPRIO executor. Julgar aqui seria a casa conferindo a si.
        wu, attempt_id = self._ate_a_validacao("prov-a", "modelo-x")
        juiz = Juiz2([{"provedor": "prov-a", "modelo": "modelo-x",
                       "effort": "alto"}], seed=7)
        with self.assertRaises(IndependenciaImpossivel) as ctx:
            juiz.julgar(self.lab.kernel, wu, attempt_id, avaliador=None)
        self.assertIn("falha fechada", str(ctx.exception))

    def test_candidato_com_so_o_modelo_distinto_nao_basta(self):
        # As duas condicoes sao CONJUNTIVAS no calculo de independencia.
        wu, attempt_id = self._ate_a_validacao("prov-a", "modelo-x")
        juiz = Juiz2([{"provedor": "prov-a", "modelo": "outro-modelo",
                       "effort": "alto"}], seed=7)
        with self.assertRaises(IndependenciaImpossivel):
            juiz.julgar(self.lab.kernel, wu, attempt_id, avaliador=None)

    def test_nenhum_veredito_e_gravado_na_recusa(self):
        # O EventLog e append-only: julgar e so depois recusar deixaria
        # o veredito nao independente gravado para sempre.
        wu, attempt_id = self._ate_a_validacao("prov-a", "modelo-x")
        juiz = Juiz2([{"provedor": "prov-a", "modelo": "modelo-x",
                       "effort": "alto"}], seed=7)
        antes = self.lab.kernel.log.seq_atual()
        with self.assertRaises(IndependenciaImpossivel):
            juiz.julgar(self.lab.kernel, wu, attempt_id, avaliador=None)
        self.assertEqual(self.lab.kernel.log.seq_atual(), antes)

    def test_fila_com_candidato_independente_julga_e_registra_a_evidencia(self):
        # Contraprova: sem ela, um guarda que recusasse sempre tornaria
        # o Juiz2 inutil e os testes acima seguiriam verdes.
        wu, attempt_id = self._ate_o_juiz_llm("prov-a", "modelo-x")
        veredito = self.lab.juiz2().julgar(
            self.lab.kernel, wu, attempt_id, avaliador=None)
        self.assertEqual(veredito.camada, "juiz-llm")
        self.assertTrue(
            veredito.independencia["provedor_distinto_do_executor"])
        self.assertTrue(veredito.independencia["modelo_distinto"])
        self.assertIn(veredito.independencia["base"],
                      ("observado", "resolvido"))

    def test_a_fila_inteira_entra_na_evidencia(self):
        # Quem le o veredito precisa saber QUAIS candidatos existiam —
        # senao "independente" e afirmacao sem lastro.
        wu, attempt_id = self._ate_o_juiz_llm("prov-a", "modelo-x")
        veredito = self.lab.juiz2().julgar(
            self.lab.kernel, wu, attempt_id, avaliador=None)
        self.assertEqual(len(veredito.independencia["fila"]), 2)


if __name__ == "__main__":
    unittest.main()
