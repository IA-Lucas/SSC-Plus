"""P0-13 `contratos._tipo` — o ramo de recusa, e um defeito vivo. FASE 3.

A varredura classificou P0-13 SEM-TESTE com *"nenhuma alcancada"*.
`_tipo` e o guarda de tipo de TODO contrato da P0 — `from_dict` o chama
antes de qualquer coisa, e cada `validate()` o chama campo a campo — e
nenhuma das suas linhas de recusa era alcancada.

ACHADO DESTA MISSAO, encontrado ao EXERCER o guarda e nao ao le-lo:
`isinstance(True, int)` e verdadeiro em Python. `Evento(seq=True)`
atravessava `_tipo(self.seq, int, ...)` e virava **seq 1** no EventLog.
A seq e a AUTORIDADE DE ORDEM da P0 (o relogio nao e), de modo que dois
eventos podiam ocupar a mesma posicao e a cadeia deixava de ser total. O
mesmo valia para `variable_cost=True`, que passaria por custo 1 sob uma
politica cujo teto e ZERO.

Nao e defeito de estilo: e o caso em que o guarda AFIRMAVA verificar
tipo e nao verificava. A correcao esta em `_tipo`, o ponto unico — e nao
em cada `validate()`, que seria o mecanismo de copia que produziu os
achados 7, 10 e 14.

O CASO QUE OCORRE. Os dois pontos de chamada reais: `from_dict`, por
onde entra todo contrato LIDO DE DISCO, e `validate()`, por onde passa
todo contrato construido em memoria. Ambos exercidos com objetos reais.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem tipos numericos exoticos (`Decimal`, `Fraction`,
  `numpy.int64`): o acervo nao os usa e o teste nao inventa uso;
- `_tipo` nao verifica o CONTEUDO de dict e list, so o tipo do
  invólucro — um dict com valores absurdos passa, e quem o recusa e o
  `validate()` do contrato, se recusar;
- nao se afirma que TODO campo de TODO contrato esteja tipado: o que se
  mede e o comportamento do guarda, nao a completude do seu uso.
"""

import unittest

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0 import contratos as ct


class RecusaDeTipo(unittest.TestCase):

    def test_tipo_errado_e_recusado_com_o_caminho_no_erro(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            ct._tipo("texto", int, "alvo.campo")
        self.assertIn("alvo.campo", str(ctx.exception))
        self.assertIn("str", str(ctx.exception))

    def test_tupla_de_tipos_aceita_qualquer_um_deles(self):
        ct._tipo(1, (int, float), "alvo.campo")
        ct._tipo(1.5, (int, float), "alvo.campo")
        with self.assertRaises(ct.FalhaContrato):
            ct._tipo("1", (int, float), "alvo.campo")

    def test_booleano_NAO_satisfaz_int(self):
        # O achado. Antes desta correcao isto passava.
        with self.assertRaises(ct.FalhaContrato) as ctx:
            ct._tipo(True, int, "alvo.campo")
        self.assertIn("bool", str(ctx.exception))

    def test_booleano_NAO_satisfaz_numero(self):
        with self.assertRaises(ct.FalhaContrato):
            ct._tipo(False, (int, float), "alvo.campo")

    def test_booleano_satisfaz_campo_que_pede_booleano(self):
        # Contraprova indispensavel: `frota.canal_oficial` E booleano.
        # Sem ela, a correcao teria trocado um fail-open por um
        # fail-closed que reprova contrato legitimo.
        ct._tipo(True, bool, "frota.canal_oficial")
        ct._tipo(False, (bool, str), "alvo.campo")

    # --- os dois pontos de chamada REAIS -------------------------------

    def test_evento_com_seq_booleana_e_recusado(self):
        # O caso operacional do achado: a seq e a autoridade de ordem.
        evento = ct.Evento(
            evento_id="ev-1", seq=True, ts="2026-08-01T00:00:00Z",
            schema_version=ct.SCHEMA_VERSION, linhagem_id="lin-1",
            tipo=sorted(ct.TIPOS_EVENTO)[0], causado_por=None,
            idempotency_key="idem-1", prev_event_hash="0" * 64,
            payload_ref="sha256:" + "a" * 64)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            evento.validate()
        self.assertIn("evento.seq", str(ctx.exception))

    def test_custo_variavel_booleano_e_recusado(self):
        # `variable_cost=True` passaria por custo 1 sob uma politica cujo
        # teto e ZERO — e o guarda economico nao veria diferenca.
        entrada = _frota_valida(variable_cost=True)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            entrada.validate()
        self.assertIn("variable_cost", str(ctx.exception))

    def test_from_dict_recusa_o_que_nao_e_dict(self):
        # `from_dict` chama `_tipo` na primeira linha: e a porta de
        # entrada de todo contrato lido de disco.
        for valor in ("nao e dict", ["lista"], 42, None):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ct.FalhaContrato):
                    ct.Evento.from_dict(valor)

    def test_contrato_legitimo_continua_atravessando(self):
        # Contraprova geral: um `_tipo` que recusasse sempre reprovaria
        # o acervo inteiro, e os testes acima nao veriam diferenca.
        _frota_valida().validate()


def _frota_valida(**sobre) -> ct.FleetEntry:
    campos = {"provider_id": "prov-a", "model_id": "modelo-x",
              "capability_profile": {}, "auth_mode": sorted(ct.AUTH_MODES)[0],
              "billing_mode": sorted(ct.BILLING_MODES)[0],
              "quota_state": "disponivel", "quota_reset": None,
              "automation_permission": sorted(ct.AUTOMATION_PERMISSIONS)[0],
              "terms_profile": {}, "variable_cost": 0,
              "papeis_preferidos": [], "canal_oficial": True}
    campos.update(sobre)
    return ct.FleetEntry(**campos)


if __name__ == "__main__":
    unittest.main()
