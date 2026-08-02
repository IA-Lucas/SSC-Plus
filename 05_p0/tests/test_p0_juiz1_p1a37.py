"""P0-18 `judge.Juiz1.julgar` — o ramo de recusa. FASE 3.

A varredura classificou P0-18 SEM-TESTE com *"nenhuma alcancada"*, na
familia POLITICA. `Juiz1` e a camada DETERMINISTICA de validacao: e ela
que decide se uma WorkUnit passou, sem modelo nenhum no meio. O guarda
recusa avaliador que devolva veredito fora do enum fechado.

O CASO QUE OCORRE. O avaliador e injetado por quem chama — `execution`,
um cenario, uma missao futura. Um avaliador que devolva `"ok"`,
`"passou"`, `True` ou `None` no lugar de `"aprovado"` esta afirmando um
veredito que o acervo nao reconhece. Sem a recusa, esse valor entraria
no `ValidationVerdict` e dali no EventLog — um veredito que nenhum
consumidor sabe ler, gravado como se fosse valido.

O teste roda o FLUXO REAL: lab de verdade, WorkUnit forjada pelo router,
execucao pelo gateway, e entao `Juiz1.julgar` sobre o attempt que
realmente existiu. O avaliador e o unico ponto injetado — que e como a
operacao o usa.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao afirmam que a lista `RESULTADOS_VEREDITO` seja a lista certa;
- nao cobrem o julgamento por camada de LLM (`Juiz2`), que e P0-19;
- nao cobrem avaliador que levante excecao propria: ela propaga, e o
  contrato nao promete converte-la;
- os criterios devolvidos pelo avaliador nao sao validados por este
  guarda — so o resultado.
"""

import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.judge import Juiz1


class RecusaDoJuizDeterministico(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)

    def _ate_a_validacao(self):
        """Fluxo real ate `aguardando-validacao` — sem julgar ainda.

        `apoio.fluxo_sucesso` julga no fim e deixa a WU concluida; um
        segundo julgamento sobre ela seria recusado pelo kernel por
        outro motivo, e o teste mediria o guarda errado. Cada caso ganha
        a sua propria WorkUnit, no estado em que o juiz de fato a
        encontra em operacao.
        """
        wu = self.lab.router.forjar(
            intencao="tarefa para o juiz deterministico",
            criterios={"tipo": "saida-nao-vazia"}, tipo="ato", nivel="L2",
            perfil={"modalidade": "texto", "ferramentas": [],
                    "formato_saida": "livre", "contexto_max_tokens": 8000,
                    "dominio": "geral", "privacidade": "remoto-permitido",
                    "latencia_max_ms": None, "orcamento_max_custo": None},
            classe="C1")
        decisao = self.lab.router.propor_decisao(
            wu, rota="padrao",
            selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="P0-18")
        resultado = self.lab.execution.executar(
            wu, decisao, idempotency_key=f"p0-18-{wu.work_unit_id}",
            entrada=b"dados")
        self.assertEqual(resultado.status, "sucesso")
        return wu, resultado.attempt_id

    def _julgar(self, resultado_do_avaliador, alvo=None):
        wu, attempt_id = alvo or self._ate_a_validacao()
        return Juiz1.julgar(
            self.lab.kernel, wu, attempt_id,
            lambda saida, pacote, attempt: (
                [{"criterio": "qualquer", "evidencia": "-", "passou": True}],
                resultado_do_avaliador))

    def test_veredito_fora_do_enum_e_recusado(self):
        for valor in ("ok", "passou", "APROVADO", "", None, True, 1):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self._julgar(valor)
                self.assertIn("avaliador devolveu", str(ctx.exception))

    def test_nenhum_veredito_e_gravado_quando_o_avaliador_erra(self):
        # O que importa nao e so levantar: e nao deixar rastro. Um
        # veredito invalido gravado no EventLog seria irreversivel — o
        # log e append-only.
        alvo = self._ate_a_validacao()
        antes = self.lab.kernel.log.seq_atual()
        with self.assertRaises(ct.FalhaContrato):
            self._julgar("ok", alvo=alvo)
        self.assertEqual(self.lab.kernel.log.seq_atual(), antes)

    def test_todo_valor_do_enum_e_aceito(self):
        # Contraprova: o guarda nao pode recusar um veredito que o
        # proprio enum declara. Cobre "reprovado" e "inconclusivo", que
        # o fluxo feliz nunca exercita.
        for valor in sorted(ct.RESULTADOS_VEREDITO):
            with self.subTest(valor=valor):
                veredito = self._julgar(valor)
                self.assertEqual(veredito.resultado, valor)
                self.assertEqual(veredito.camada, "deterministica")

    def test_o_veredito_produzido_valida_como_contrato(self):
        # Contraprova de forma: o objeto que sai daqui entra no acervo.
        alvo = self._ate_a_validacao()
        veredito = self._julgar("aprovado", alvo=alvo)
        veredito.validate()
        self.assertEqual(veredito.alvo["work_unit_id"], alvo[0].work_unit_id)


if __name__ == "__main__":
    unittest.main()
