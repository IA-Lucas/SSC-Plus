"""P0-08 `contratos.FleetEntry.validate` — os ramos de recusa. FASE 3.

A varredura classificou P0-08 SEM-TESTE com *"nenhuma alcancada"*, na
familia ECONOMIA. E o contrato que descreve uma assinatura da frota: o
modo de auth, o modo de cobranca, o estado da franquia, a permissao de
automacao e o CUSTO VARIAVEL. E a politica economica do acervo tem teto
`external_variable_cost_cap = 0`.

O CASO QUE OCORRE. Uma entrada de frota chega de uma descoberta — de
`frota.py`, do preflight, de um arquivo. Se `billing_mode` vier com um
valor que ninguem previu, ou `variable_cost` vier negativo (que e como
um credito se disfarca de economia), ou `automation_permission` vier
fora do enum, o que entra no acervo e uma assinatura que a politica nao
sabe avaliar. Enum FECHADO existe para isso: valor fora da lista e falha
de contrato, NUNCA coercao.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao afirmam que os enums tenham os valores CERTOS: medem que valor
  fora deles e recusado, nao que a lista esteja completa;
- nao cobrem coerencia CRUZADA entre campos (`billing_mode=subscription`
  com `variable_cost>0`, por exemplo) — o contrato nao a impoe, e quem
  a impoe e a politica economica, noutro ponto;
- `capability_profile` e `terms_profile` sao verificados como dict, e o
  CONTEUDO deles nao e contrato.
"""

import unittest

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0 import contratos as ct


def frota(**sobre) -> ct.FleetEntry:
    campos = {"provider_id": "prov-a", "model_id": "modelo-x",
              "capability_profile": {}, "auth_mode": "subscription-oauth",
              "billing_mode": "subscription", "quota_state": "disponivel",
              "quota_reset": None, "automation_permission": "supervised",
              "terms_profile": {}, "variable_cost": 0,
              "papeis_preferidos": ["autor"], "canal_oficial": True}
    campos.update(sobre)
    return ct.FleetEntry(**campos)


class RecusaDoContratoDeFrota(unittest.TestCase):

    def test_identificadores_obrigatorios(self):
        for campo in ("provider_id", "model_id"):
            with self.subTest(campo=campo):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    frota(**{campo: None}).validate()
                self.assertIn(campo, str(ctx.exception))

    def test_enum_fechado_recusa_valor_novo(self):
        casos = {"auth_mode": "oauth2", "billing_mode": "gratis",
                 "quota_state": "cheia",
                 "automation_permission": "permitido"}
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    frota(**{campo: valor}).validate()
                self.assertIn("fora do enum fechado", str(ctx.exception))

    def test_enum_nao_faz_coercao_de_caixa(self):
        # "SUBSCRIPTION" nao e "subscription": enum fechado nao
        # normaliza, porque normalizar e adivinhar.
        with self.assertRaises(ct.FalhaContrato):
            frota(billing_mode="SUBSCRIPTION").validate()

    def test_custo_variavel_negativo_e_recusado(self):
        # Credito disfarcado de economia: com custo negativo, uma soma
        # de custos poderia ficar abaixo do teto por compensacao.
        for valor in (-0.01, -1, -1000):
            with self.subTest(valor=valor):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    frota(variable_cost=valor).validate()
                self.assertIn("negativo", str(ctx.exception))

    def test_custo_variavel_nao_numerico_e_recusado(self):
        for valor in ("0", None, [], True):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ct.FalhaContrato):
                    frota(variable_cost=valor).validate()

    def test_perfis_precisam_ser_dicionarios(self):
        for campo in ("capability_profile", "terms_profile"):
            with self.subTest(campo=campo):
                with self.assertRaises(ct.FalhaContrato):
                    frota(**{campo: "texto"}).validate()

    def test_papel_fora_do_enum_e_recusado(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            frota(papeis_preferidos=["autor", "arquiteto"]).validate()
        self.assertIn("papeis_preferidos", str(ctx.exception))

    def test_papeis_preferidos_precisa_ser_lista(self):
        with self.assertRaises(ct.FalhaContrato):
            frota(papeis_preferidos="autor").validate()

    def test_canal_oficial_precisa_ser_booleano(self):
        for valor in ("sim", 1, None):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ct.FalhaContrato):
                    frota(canal_oficial=valor).validate()

    def test_entrada_legitima_atravessa_e_faz_round_trip(self):
        # Contraprova: sem ela, um validate() que levantasse sempre
        # passaria em todos os testes acima. Cobre tambem os limites
        # LEGITIMOS: custo zero, lista de papeis vazia, reset ausente.
        entrada = frota(variable_cost=0, papeis_preferidos=[],
                        quota_reset=None)
        entrada.validate()
        self.assertEqual(ct.FleetEntry.from_dict(entrada.to_dict()), entrada)

    def test_todo_valor_do_enum_e_aceito(self):
        # A outra metade da contraprova: o guarda nao pode recusar um
        # valor que a propria lista declara.
        for modo in sorted(ct.BILLING_MODES):
            with self.subTest(billing_mode=modo):
                frota(billing_mode=modo).validate()


if __name__ == "__main__":
    unittest.main()
