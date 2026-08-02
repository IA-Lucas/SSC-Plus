"""P0-17 `frota.Frota` — o ramo de recusa que faltava. FASE 3.

A varredura mediu **1 de 2 ramos alcancados** neste ponto, familia
ISOLAMENTO. Os dois sao:
- `registrar_quota_exhausted` para uma entrada que a frota nao conhece;
- `verificar_independencia`, que recusa autor e revisor/juiz do MESMO
  provedor ou do MESMO modelo.

O CASO QUE OCORRE. `registrar_quota_exhausted` e chamada quando um
provedor devolve esgotamento: se o par provider/model nao existir na
frota, marcar "esgotada" em silencio esconderia que o acervo perdeu de
vista qual assinatura falhou — e o proximo roteamento escolheria no
escuro.

`verificar_independencia` e o eixo do trabalho critico: um revisor do
mesmo provedor E do mesmo modelo que o autor nao e revisao independente,
e a recusa e o que impede o acervo de registrar uma "revisao" que so
confirma a si mesma. As duas condicoes sao CONJUNTIVAS, e cada metade
sozinha ja e insuficiente — os testes medem as tres combinacoes.

O QUE ESTES TESTES NAO COBREM, declarado:
- `elegiveis()` filtra por economia/canal/automacao/quota e tem
  cobertura em `test_frota.py`: aqui o objeto sao as DUAS recusas;
- independencia e medida por provider_id e model_id declarados, nao por
  observacao do que respondeu — o executor OBSERVADO e materia do
  `Juiz2` (P0-19);
- nada se afirma sobre a frota REAL do adendo.
"""

import unittest

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0 import contratos as ct
from ssc_p0.frota import Frota, IndependenciaInsuficiente


def entrada(provider_id="prov-a", model_id="modelo-x") -> ct.FleetEntry:
    return ct.FleetEntry(
        provider_id=provider_id, model_id=model_id, capability_profile={},
        auth_mode="subscription-oauth", billing_mode="subscription",
        quota_state="disponivel", quota_reset=None,
        automation_permission="allow",
        terms_profile={"oauth_profile": f"oauth:{provider_id}"},
        variable_cost=0, papeis_preferidos=[], canal_oficial=True)


class RecusasDaFrota(unittest.TestCase):

    def test_quota_esgotada_de_entrada_desconhecida_e_recusada(self):
        frota = Frota([entrada()])
        for provider_id, model_id in (("prov-z", "modelo-x"),
                                      ("prov-a", "modelo-inexistente"),
                                      ("", "")):
            with self.subTest(alvo=f"{provider_id}/{model_id}"):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    frota.registrar_quota_exhausted(provider_id, model_id)
                self.assertIn("quota de entrada desconhecida",
                              str(ctx.exception))

    def test_a_recusa_nao_altera_nenhuma_entrada(self):
        # Marcar a entrada errada seria pior que nao marcar nada.
        frota = Frota([entrada(), entrada(model_id="modelo-y")])
        with self.assertRaises(ct.FalhaContrato):
            frota.registrar_quota_exhausted("prov-a", "modelo-z")
        self.assertEqual([e.quota_state for e in frota.entradas],
                         ["disponivel", "disponivel"])

    def test_revisor_do_mesmo_provedor_e_modelo_e_recusado(self):
        autor = entrada()
        with self.assertRaises(IndependenciaInsuficiente) as ctx:
            Frota.verificar_independencia(autor, entrada(), "revisor")
        self.assertIn("nao independente do autor", str(ctx.exception))

    def test_so_o_modelo_distinto_nao_basta(self):
        # As duas condicoes sao CONJUNTIVAS: mesmo provedor com outro
        # modelo continua sendo a mesma casa julgando a si propria.
        autor = entrada()
        with self.assertRaises(IndependenciaInsuficiente):
            Frota.verificar_independencia(
                autor, entrada(model_id="modelo-y"), "juiz")

    def test_so_o_provedor_distinto_nao_basta(self):
        autor = entrada()
        with self.assertRaises(IndependenciaInsuficiente):
            Frota.verificar_independencia(
                autor, entrada(provider_id="prov-b"), "revisor")

    def test_a_evidencia_da_recusa_nomeia_os_dois_lados(self):
        # Sem os dois nomes no erro, quem le nao sabe qual par foi
        # recusado — e a evidencia deixa de ser acionavel.
        autor = entrada()
        with self.assertRaises(IndependenciaInsuficiente) as ctx:
            Frota.verificar_independencia(autor, entrada(), "juiz")
        texto = str(ctx.exception)
        self.assertIn("prov-a/modelo-x", texto)
        self.assertIn("juiz", texto)

    def test_par_independente_atravessa_com_evidencia(self):
        # Contraprova: sem ela, um guarda que recusasse sempre tornaria
        # toda revisao impossivel e os testes acima seguiriam verdes.
        evidencia = Frota.verificar_independencia(
            entrada(), entrada(provider_id="prov-b", model_id="modelo-y"),
            "revisor")
        self.assertTrue(evidencia["provider_distinto"])
        self.assertTrue(evidencia["modelo_distinto"])
        self.assertEqual(evidencia["papel"], "revisor")

    def test_quota_esgotada_conhecida_e_registrada(self):
        # A outra metade da contraprova.
        frota = Frota([entrada()])
        marcada = frota.registrar_quota_exhausted("prov-a", "modelo-x")
        self.assertEqual(marcada.quota_state, "esgotada")
        self.assertEqual([e for e in frota.elegiveis()], [])


if __name__ == "__main__":
    unittest.main()
