"""P0-25 `router.TaskRouter` — os cinco ramos que faltavam. FASE 3.

A varredura mediu **3 de 8 ramos alcancados**. O router e o ponto onde
uma intencao vira uma decisao de rota — e onde uma decisao mal formada
tem de morrer ANTES de qualquer gasto.

O CASO QUE OCORRE, ramo a ramo:
- intencao acima do teto de 4000 chars: entrada nao limitada e o que
  transforma um prompt colado num contexto que ninguem previu;
- plano de decomposicao com `depende_de` DESCONHECIDO e com CICLO: os
  dois sao recusados ANTES de qualquer registro, e a ordem importa —
  validar depois de registrar deixaria WorkUnits orfas no log;
- `decompor` sobre WorkUnit que nao e do tipo `decomposicao`;
- `rerotear` sem decisao vigente previa: reroteamento e SUPERSEDE, e
  superseder o nada e criar uma decisao que finge ter historia;
- `reparar` sobre WorkUnit que nao esta `reprovada`.

Todos exercidos com o router REAL do lab, contra o kernel real.

O QUE ESTES TESTES NAO COBREM, declarado:
- `RotaVetada` e `FalhaFechadaClassificacao` tem cobertura em
  `test_policy.py` e nao sao reexercidos aqui;
- o teto de 4000 chars e um numero do acervo; nada aqui afirma que ele
  seja o numero certo;
- `validar_plano` valida o GRAFO proposto, nao o merito dos filhos.
"""

import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.router import TaskRouter

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class RecusasDoRouter(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)

    def _forjar(self, **sobre):
        campos = {"intencao": "tarefa qualquer",
                  "criterios": {"tipo": "saida-nao-vazia"}, "tipo": "ato",
                  "nivel": "L2", "perfil": PERFIL, "classe": "C1"}
        campos.update(sobre)
        return self.lab.router.forjar(**campos)

    def test_intencao_acima_do_teto_e_recusada(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self._forjar(intencao="x" * 4001)
        self.assertIn("teto de 4000", str(ctx.exception))

    def test_nada_e_registrado_quando_a_intencao_estoura(self):
        antes = self.lab.kernel.log.seq_atual()
        with self.assertRaises(ct.FalhaContrato):
            self._forjar(intencao="x" * 5000)
        self.assertEqual(self.lab.kernel.log.seq_atual(), antes)

    def test_plano_com_dependencia_desconhecida_e_recusado(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            TaskRouter.validar_plano([
                {"id": "a", "depende_de": []},
                {"id": "b", "depende_de": ["inexistente"]}])
        self.assertIn("depende_de desconhecido", str(ctx.exception))

    def test_plano_com_ciclo_e_recusado(self):
        for plano in (
            [{"id": "a", "depende_de": ["a"]}],
            [{"id": "a", "depende_de": ["b"]},
             {"id": "b", "depende_de": ["a"]}],
            [{"id": "a", "depende_de": ["b"]},
             {"id": "b", "depende_de": ["c"]},
             {"id": "c", "depende_de": ["a"]}],
        ):
            with self.subTest(tamanho=len(plano)):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    TaskRouter.validar_plano(plano)
                self.assertIn("ciclo detectado", str(ctx.exception))

    def test_decompor_workunit_que_nao_e_decomposicao_e_recusado(self):
        wu = self._forjar(tipo="ato")
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.lab.router.decompor(wu, [{"id": "a", "depende_de": []}])
        self.assertIn("so WorkUnit 'decomposicao'", str(ctx.exception))

    def test_rerotear_sem_decisao_vigente_e_recusado(self):
        # Reroteamento e SUPERSEDE: superseder o nada seria criar uma
        # decisao que finge ter historia.
        wu = self._forjar()
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.lab.router.rerotear(
                wu, rota="padrao",
                selecao=self.lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=self.lab.aprovacao, motivo="sem historia")
        self.assertIn("decisao vigente previa", str(ctx.exception))

    def test_reparar_workunit_que_nao_foi_reprovada_e_recusado(self):
        wu = self._forjar()
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.lab.router.reparar(wu, {"erro": "qualquer"})
        self.assertIn("reparo exige workunit 'reprovada'", str(ctx.exception))

    # --- contraprovas ---------------------------------------------------

    def test_intencao_no_limite_exato_atravessa(self):
        # A fronteira: 4000 e aceito, 4001 nao. Sem isto, o teto poderia
        # ter virado 3999 sem ninguem notar.
        wu = self._forjar(intencao="x" * 4000)
        self.assertEqual(len(wu.intencao), 4000)

    def test_plano_acilico_atravessa(self):
        TaskRouter.validar_plano([
            {"id": "a", "depende_de": []},
            {"id": "b", "depende_de": ["a"]},
            {"id": "c", "depende_de": ["a", "b"]}])

    def test_rerotear_com_decisao_vigente_atravessa(self):
        # Contraprova do ramo do reroteamento, e a mais importante: sem
        # ela, um guarda que recusasse sempre tornaria o reroteamento
        # impossivel e os testes acima seguiriam verdes.
        wu = self._forjar()
        self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="primeira")
        nova = self.lab.router.rerotear(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="segunda")
        self.assertIsNotNone(nova.supersede)


if __name__ == "__main__":
    unittest.main()
