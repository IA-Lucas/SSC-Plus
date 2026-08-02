"""P0-07 `contratos.Evento.validate` — os ramos de recusa. FASE 3.

A varredura classificou este ponto SEM-TESTE com *"nenhuma alcancada"*.
E o contrato do EventLog: todo evento gravado no log append-only passa
por `validate()`, e nenhuma das suas recusas era exercida.

O CASO QUE OCORRE. O EventLog e a autoridade de ordem da P0 (o relogio
nao e). Um evento com `seq` fora de ordem, com `schema_version` de outra
versao do acervo, com `tipo` fora do enum fechado ou sem
`prev_event_hash` quebra a cadeia — e a cadeia e o que permite a um
terceiro reconstruir o estado. As recusas sao exercidas pelo objeto
REAL, construido com os campos reais e validado pela funcao de producao;
e tambem pelo `from_dict`, que e por onde um evento LIDO DE DISCO entra.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao provam nada sobre o encadeamento de hash entre eventos: isso e o
  EventLog (P0-15), nao o contrato de um evento isolado;
- nao cobrem a gravacao: `validate()` recusa antes, e o que se mede aqui
  e a recusa;
- `ts` e verificado apenas como obrigatorio — o contrato nao impoe
  formato de data, e o teste nao inventa um.
"""

import unittest

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0 import contratos as ct


def evento_valido(**sobre) -> ct.Evento:
    campos = {"evento_id": "ev-1", "seq": 1, "ts": "2026-08-01T00:00:00Z",
              "schema_version": ct.SCHEMA_VERSION, "linhagem_id": "lin-1",
              "tipo": sorted(ct.TIPOS_EVENTO)[0], "causado_por": None,
              "idempotency_key": "idem-1", "prev_event_hash": "0" * 64,
              "payload_ref": "sha256:" + "a" * 64}
    campos.update(sobre)
    return ct.Evento(**campos)


class RecusaDoContratoDeEvento(unittest.TestCase):

    def test_seq_abaixo_de_um_e_recusada(self):
        # A seq e a autoridade de ordem: 0 e negativo nao existem no log.
        for seq in (0, -1, -999):
            with self.subTest(seq=seq):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    evento_valido(seq=seq).validate()
                self.assertIn("evento.seq", str(ctx.exception))

    def test_seq_que_nao_e_inteiro_e_recusada(self):
        for seq in ("1", 1.0, None):
            with self.subTest(seq=repr(seq)):
                with self.assertRaises(ct.FalhaContrato):
                    evento_valido(seq=seq).validate()

    def test_seq_booleana_e_recusada(self):
        # `True` e `isinstance(x, int)` em Python. Um evento com
        # `seq=True` passaria pelo teste de tipo e viraria seq 1 — dois
        # eventos com a mesma ordem, e a cadeia deixa de ser total.
        with self.assertRaises(ct.FalhaContrato):
            evento_valido(seq=True).validate()

    def test_schema_version_de_outra_versao_e_recusado(self):
        for versao in ("ssc-p0/1.1", "ssc-p0/2.0", "", None):
            with self.subTest(versao=repr(versao)):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    evento_valido(schema_version=versao).validate()
                self.assertIn("schema_version", str(ctx.exception))

    def test_tipo_fora_do_enum_fechado_e_recusado(self):
        for tipo in ("inventado", "", None, "EXECUCAO"):
            with self.subTest(tipo=repr(tipo)):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    evento_valido(tipo=tipo).validate()
                self.assertIn("evento.tipo", str(ctx.exception))

    def test_campo_obrigatorio_ausente_e_recusado(self):
        for campo in ("evento_id", "ts", "linhagem_id", "idempotency_key",
                      "prev_event_hash", "payload_ref"):
            with self.subTest(campo=campo):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    evento_valido(**{campo: None}).validate()
                self.assertIn(campo, str(ctx.exception))

    def test_causado_por_ausente_e_legitimo(self):
        # Contraprova interna: `causado_por` e opcional por contrato — o
        # primeiro evento de uma linhagem nao tem causa anterior. Um
        # guarda que exigisse tudo reprovaria a abertura de sessao.
        evento_valido(causado_por=None).validate()

    def test_evento_lido_de_disco_com_campo_a_mais_e_recusado(self):
        # O caminho por onde um evento ADULTERADO entra: `from_dict`.
        dados = evento_valido().to_dict()
        dados["campo_intruso"] = "x"
        with self.assertRaises(ct.FalhaContrato) as ctx:
            ct.Evento.from_dict(dados)
        self.assertIn("fora do schema", str(ctx.exception))

    def test_evento_lido_de_disco_com_campo_a_menos_e_recusado(self):
        dados = evento_valido().to_dict()
        del dados["payload_ref"]
        with self.assertRaises(ct.FalhaContrato) as ctx:
            ct.Evento.from_dict(dados)
        self.assertIn("ausentes", str(ctx.exception))

    def test_evento_valido_atravessa_e_faz_round_trip(self):
        # Contraprova: sem ela, um validate() que levantasse sempre
        # passaria em todos os testes acima.
        evento = evento_valido()
        evento.validate()
        self.assertEqual(ct.Evento.from_dict(evento.to_dict()), evento)


if __name__ == "__main__":
    unittest.main()
