"""P0-21 FASE 3 [1/6] — os dois ramos de CICLO do grafo de WorkUnits.

`SessionKernel._checar_ciclo` tem duas recusas, ambas medidas como NAO
ALCANCADAS: ciclo pela cadeia de `parent_work_unit` e ciclo por
`depende_de`. A tentacao e escrever um teste que mute uma WorkUnit ja
registrada para fabricar o ciclo, e chamar isso de cobertura. Este
arquivo faz o oposto: MEDE se o ramo e alcancavel pela interface real, e
registra o resultado.

MEDIDO, pela interface real e nao por leitura:

    registrar_work_unit(wu, parent_work_unit=<ela mesma>)
      -> FalhaContrato: parent_work_unit desconhecido
    registrar_work_unit(wu, depende_de=[<ela mesma>])
      -> FalhaContrato: depende_de desconhecido: 'wu-y'

Nenhuma das duas alcanca `_checar_ciclo`: as recusas de "desconhecido"
correm ANTES, na mesma funcao.

POR QUE OS DOIS RAMOS SAO INALCANCAVEIS, e nao apenas "nao testados".
E inducao sobre o grafo, e ela e curta:

- toda WorkUnit registrada teve `parent_work_unit` e `depende_de`
  conferidos contra `self.work_units` ANTES de entrar;
- logo todo pai e toda dependencia ja estavam registrados;
- logo o subgrafo dos registrados e aciclico, por construcao;
- a WorkUnit NOVA ainda nao esta em `self.work_units`, de modo que
  nenhuma aresta pode apontar para ela;
- acrescentar um no cujas arestas so saem, a um grafo aciclico, nao
  fecha ciclo.

O caso que a operacao percorre, portanto, e a recusa POR DESCONHECIDO —
e e ela que estes testes exercem. `_checar_ciclo` e DEFESA EM
PROFUNDIDADE: a segunda linha, que so tem trabalho se a primeira cair.

A REVERSAO PROVA A CAMADA. Removida a recusa de `depende_de
desconhecido`, quem passa a recusar e `_checar_ciclo` — com a mensagem
de ciclo. E a medicao de que as duas camadas nao sao a mesma, e de que
a segunda de fato funciona quando chamada.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem ciclo entre TRES ou mais WorkUnits: pela mesma inducao ele
  tambem e inalcancavel, e encena-lo exigiria mutar o dicionario interno
  do kernel — o vizinho que a regra proibe;
- nao cobrem replay: `_aplicar` reinsere as WorkUnits na ordem de seq do
  log, que e a ordem em que foram aceitas, de modo que a invariante e
  preservada. Nada aqui prova isso — e afirmacao de leitura, e esta
  declarada como tal;
- nao se afirma que `_checar_ciclo` esteja CORRETO para todo grafo: o
  que se mede e que a operacao nao chega ate ele.
"""

import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import canonico

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class CicloNoGrafoDeWorkUnits(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel

    def _wu(self, wid, **sobre) -> ct.WorkUnit:
        ref = self.kernel.cas.gravar(
            canonico({"work_unit_id": wid, "entradas": []}))
        campos = {
            "work_unit_id": wid,
            "sessao_id": self.kernel.envelope.sessao_id,
            "linhagem_id": self.kernel.envelope.linhagem_id,
            "parent_work_unit": None, "tipo": "ato", "tipo_decisao": "tipo-2",
            "intencao": f"intencao de {wid}", "criterios_aceite_ref": ref,
            "nivel_capacidade": "L2", "perfil_capacidade": dict(PERFIL),
            "classe_governanca": "C1", "contexto_ref": ref, "depende_de": [],
            "estado": "proposta", "resultado_ref": None, "custo_medido": None}
        campos.update(sobre)
        return ct.WorkUnit(**campos)

    # --- o caso que a operacao percorre --------------------------------

    def test_workunit_que_se_declara_propria_mae_e_recusada(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_work_unit(
                self._wu("wu-x", parent_work_unit="wu-x"), None)
        self.assertIn("parent_work_unit desconhecido", str(ctx.exception))

    def test_workunit_que_depende_de_si_mesma_e_recusada(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_work_unit(
                self._wu("wu-y", depende_de=["wu-y"]), None)
        self.assertIn("depende_de desconhecido", str(ctx.exception))

    def test_dependencia_futura_e_recusada_antes_de_existir(self):
        # A unica forma de fechar um ciclo seria uma aresta apontando
        # para quem ainda nao nasceu. E exatamente isso que a recusa por
        # "desconhecido" torna impossivel.
        self.kernel.registrar_work_unit(self._wu("wu-a"), None)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_work_unit(
                self._wu("wu-b", depende_de=["wu-a", "wu-c"]), None)
        self.assertIn("wu-c", str(ctx.exception))

    def test_nada_e_gravado_quando_a_aresta_e_recusada(self):
        # A recusa por "desconhecido" acontece ANTES de qualquer evento:
        # `_registrar_recusa` so e chamado no ramo de ciclo, que nao e
        # alcancado. Uma WorkUnit malformada nao deixa rastro no log.
        antes = self.kernel.log.seq_atual()
        with self.assertRaises(ct.FalhaContrato):
            self.kernel.registrar_work_unit(
                self._wu("wu-z", depende_de=["inexistente"]), None)
        self.assertEqual(self.kernel.log.seq_atual(), antes)
        self.assertNotIn("wu-z", self.kernel.work_units)

    # --- a inducao, exercida em vez de afirmada -------------------------

    def test_toda_cadeia_de_pais_registrada_termina_em_None(self):
        # A propriedade de onde sai a inalcancabilidade: nenhum ciclo
        # pode existir entre os registrados. Aqui ela e MEDIDA sobre uma
        # cadeia real de tres niveis, percorrendo ate o fim.
        self.kernel.registrar_work_unit(self._wu("wu-1"), None)
        self.kernel.registrar_work_unit(
            self._wu("wu-2", parent_work_unit="wu-1"), None)
        self.kernel.registrar_work_unit(
            self._wu("wu-3", parent_work_unit="wu-2"), None)
        for inicio in ("wu-1", "wu-2", "wu-3"):
            with self.subTest(de=inicio):
                atual, passos = inicio, 0
                while atual is not None:
                    passos += 1
                    self.assertLessEqual(passos, len(self.kernel.work_units))
                    atual = self.kernel.work_units[atual].parent_work_unit
                self.assertLessEqual(passos, 3)

    def test_grafo_de_dependencias_registrado_e_aciclico(self):
        self.kernel.registrar_work_unit(self._wu("wu-1"), None)
        self.kernel.registrar_work_unit(
            self._wu("wu-2", depende_de=["wu-1"]), None)
        self.kernel.registrar_work_unit(
            self._wu("wu-3", depende_de=["wu-1", "wu-2"]), None)
        # Toda aresta aponta para um no que JA existia: a ordem de
        # registro e, ela propria, uma ordenacao topologica.
        ordem = list(self.kernel.work_units)
        for i, wid in enumerate(ordem):
            for dep in self.kernel.work_units[wid].depende_de:
                with self.subTest(de=wid, para=dep):
                    self.assertLess(ordem.index(dep), i)

    # --- contraprova ----------------------------------------------------

    def test_grafo_legitimo_continua_sendo_aceito(self):
        # Sem ela, um `registrar_work_unit` que recusasse toda aresta
        # passaria em todos os testes acima.
        self.kernel.registrar_work_unit(self._wu("wu-raiz"), None)
        evento = self.kernel.registrar_work_unit(
            self._wu("wu-filha", parent_work_unit="wu-raiz",
                     depende_de=["wu-raiz"]), None)
        self.assertEqual(self.kernel.work_units["wu-filha"].parent_work_unit,
                         "wu-raiz")
        self.assertIsNotNone(evento.evento_id)


if __name__ == "__main__":
    unittest.main()
