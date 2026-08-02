"""P0-20 `kernel.ControlPlane.aprovar_work_unit` — a recusa. FASE 3.

A varredura classificou P0-20 SEM-TESTE com *"nenhuma alcancada"*, na
familia POLITICA. O `ControlPlane` e a superficie por onde o HUMANO age
sobre a sessao: escalar, aprovar, encerrar. A recusa que nunca era
alcancada e a que impede aprovar uma WorkUnit que nao esta pedindo
aprovacao.

O CASO QUE OCORRE, e ele e o eixo da governanca: *silencio nunca
aprova*. Uma WorkUnit classe C0/C1 nasce `proposta` e o router ja a
leva a `aprovada` sem ato humano; classe >= C2 ou tipo-1 para em
`aguardando-aprovacao` e espera (IW-4, `router.py:45`). Aprovar por engano uma WU que ja foi aprovada, ja
executou ou foi cancelada e o caminho pelo qual um ato humano vira
carimbo retroativo — e o registro do ato traz `ts` e `hash`, de modo que
ele PARECERIA legitimo depois de gravado.

O teste usa o `ControlPlane` do lab REAL, com WorkUnits forjadas pelo
router de verdade nas duas classes, e mede a recusa em cada estado que
uma WU de fato alcanca.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem `escalar` nem `encerrar`, que sao delegacoes diretas ao
  kernel e tem cobertura propria em `test_recuperacao.py`;
- nao afirmam nada sobre QUEM e o humano: o `ato_humano` e um dict
  opaco para a P0, e a identidade do aprovador nao e contrato;
- o `hash` do ato e conferido como presente e estavel, nao como prova
  de nao-repudio — nao ha assinatura no acervo.
"""

import unittest

import apoio
from ssc_p0.estados import TransicaoIlegal

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class RecusaDaAprovacaoHumana(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)

    def _forjar(self, classe="C1"):
        return self.lab.router.forjar(
            intencao=f"tarefa classe {classe}",
            criterios={"tipo": "saida-nao-vazia"}, tipo="ato", nivel="L2",
            perfil=PERFIL, classe=classe)

    def _ato(self):
        return {"quem": "fundador", "decisao": "aprovo", "motivo": "teste"}

    def test_aprovar_workunit_que_nao_pede_aprovacao_e_recusado(self):
        # C1 nao pede ato humano: o router ja a deixa `aprovada`
        # (IW-4). Aprova-la de novo seria inventar uma aprovacao que
        # ninguem pediu — e nenhum estado que nao seja
        # `aguardando-aprovacao` pode aceitar o ato.
        wu = self._forjar("C1")
        # O objeto devolvido por `forjar` e um instantaneo em
        # `proposta`; o estado VIVO, que e o que o guarda le, ja e
        # `aprovada`. Medir o instantaneo seria medir outra coisa.
        self.assertEqual(wu.estado, "proposta")
        self.assertEqual(
            self.lab.kernel.work_units[wu.work_unit_id].estado, "aprovada")
        with self.assertRaises(TransicaoIlegal) as ctx:
            self.lab.control.aprovar_work_unit(wu.work_unit_id, self._ato())
        self.assertIn("aprovacao humana com workunit em", str(ctx.exception))
        self.assertIn("aprovada", str(ctx.exception))

    def test_aprovar_duas_vezes_e_recusado(self):
        # O carimbo retroativo: a segunda aprovacao encontraria a WU ja
        # `aprovada` e, sem o guarda, gravaria um segundo ato humano com
        # ts e hash proprios — indistinguivel do legitimo.
        wu = self._forjar("C2")
        self.assertEqual(
            self.lab.kernel.work_units[wu.work_unit_id].estado,
            "aguardando-aprovacao")
        self.lab.control.aprovar_work_unit(wu.work_unit_id, self._ato())
        with self.assertRaises(TransicaoIlegal):
            self.lab.control.aprovar_work_unit(wu.work_unit_id, self._ato())

    def test_nenhum_evento_e_gravado_na_recusa(self):
        # O EventLog e append-only: aprovar e so depois recusar deixaria
        # o ato gravado para sempre.
        wu = self._forjar("C1")
        antes = self.lab.kernel.log.seq_atual()
        with self.assertRaises(TransicaoIlegal):
            self.lab.control.aprovar_work_unit(wu.work_unit_id, self._ato())
        self.assertEqual(self.lab.kernel.log.seq_atual(), antes)
        self.assertEqual(
            self.lab.kernel.work_units[wu.work_unit_id].estado, "aprovada")

    def test_aprovacao_legitima_atravessa_e_carimba_o_ato(self):
        # Contraprova: sem ela, um guarda que recusasse sempre tornaria
        # toda WorkUnit classe >= C2 ineexecutavel, e os testes acima
        # continuariam verdes.
        wu = self._forjar("C3")
        self.assertEqual(
            self.lab.kernel.work_units[wu.work_unit_id].estado,
            "aguardando-aprovacao")
        evento = self.lab.control.aprovar_work_unit(wu.work_unit_id,
                                                    self._ato())
        self.assertEqual(evento.tipo, "work-unit")
        self.assertEqual(
            self.lab.kernel.work_units[wu.work_unit_id].estado, "aprovada")

    def test_o_ato_humano_registrado_carrega_ts_e_hash(self):
        # O ato entra datado e hasheado — e o que permite a um terceiro
        # dizer QUANDO a aprovacao existiu.
        wu = self._forjar("C2")
        ato = self._ato()
        evento = self.lab.control.aprovar_work_unit(wu.work_unit_id, ato)
        self.assertNotIn("ts", ato, "o dict do chamador foi mutado")
        payload = self.lab.kernel.cas.ler(evento.payload_ref)
        self.assertIn(b"ato_humano", payload)
        self.assertIn(b'"hash"', payload)
        self.assertIn(b'"ts"', payload)


if __name__ == "__main__":
    unittest.main()
