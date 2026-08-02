"""P0-15 `eventlog.EventLog` — os cinco ramos que faltavam. FASE 3.

A varredura mediu **5 de 10 ramos alcancados**: o teste existente MUTA
BYTES REAIS do log (`test_eventlog.py:58`), o que e forte, mas cobre um
subconjunto das anomalias.

O CASO QUE OCORRE. O EventLog e a AUTORIDADE DE ORDEM da P0 e a unica
coisa que permite a um terceiro reconstruir o estado sem confiar em
ninguem. As anomalias que faltavam:
- `anexar` com seq fora de ordem — buraco ou regressao na cadeia;
- `anexar` com `prev_event_hash` que nao e a ponta — cadeia bifurcada;
- reentrega IDENTICA da mesma idempotency_key: aceita e ignorada (nao e
  anomalia, e o contrato de entrega ao menos uma vez);
- mesma idempotency_key com payload DIFERENTE: conflito, recusado;
- `verificar` sobre arquivo com CAUDA TRUNCADA — a ultima linha sem
  terminador, que e o que uma queda de energia deixa;
- `verificar` sobre linha nao canonica: a linha crua tem de SER a
  serializacao canonica do evento. Um espaco a mais, editado a mao, ja
  quebra — e essa e a propriedade que impede edicao local silenciosa.

Todos os ramos sao exercidos sobre um log REAL em disco, com bytes
escritos e relidos — nunca sobre um duplo do log.

O QUE ESTES TESTES NAO COBREM, declarado:
- durabilidade: `os.fsync` e chamado, e nenhum teste em processo pode
  provar que o dado sobreviveu a queda de energia;
- concorrencia: o docstring diz que o CHAMADOR serializa, e nada aqui
  prova que ele serialize;
- nao se cobre arquivo de log ausente em `verificar` (erro de OS, nao
  anomalia de cadeia).
"""

import os
import shutil
import unittest
import uuid

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import canonico
from ssc_p0.eventlog import (EventLog, EventoAdulterado,
                             EventoConflitoIdempotencia, EventoForaDeOrdem,
                             EventoTruncado, hash_evento)

GENESE = "0" * 64


def evento(seq, chave, prev, payload="sha256:" + "a" * 64) -> ct.Evento:
    return ct.Evento(
        evento_id=f"ev-{seq}-{chave}", seq=seq, ts="2026-08-01T00:00:00Z",
        schema_version=ct.SCHEMA_VERSION, linhagem_id="lin-1",
        tipo="sessao", causado_por=None, idempotency_key=chave,
        prev_event_hash=prev, payload_ref=payload)


class RecusasDoEventLog(unittest.TestCase):

    def setUp(self):
        self.raiz = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        os.makedirs(self.raiz)
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        self.caminho = os.path.join(self.raiz, "log.jsonl")
        open(self.caminho, "wb").close()
        self.log = EventLog(self.caminho, GENESE)

    def _primeiro(self) -> ct.Evento:
        ev = evento(1, "k1", GENESE)
        self.assertTrue(self.log.anexar(ev))
        return ev

    def test_seq_fora_de_ordem_e_recusada(self):
        self._primeiro()
        for seq in (1, 3, 99):
            with self.subTest(seq=seq):
                ev = evento(seq, f"k-{seq}", self.log.ultimo_hash())
                with self.assertRaises(EventoForaDeOrdem) as ctx:
                    self.log.anexar(ev)
                self.assertIn("fora de ordem", str(ctx.exception))

    def test_prev_hash_que_nao_e_a_ponta_e_recusado(self):
        self._primeiro()
        ev = evento(2, "k2", "f" * 64)
        with self.assertRaises(EventoAdulterado) as ctx:
            self.log.anexar(ev)
        self.assertIn("prev_event_hash", str(ctx.exception))

    def test_reentrega_identica_e_aceita_e_ignorada(self):
        # NAO e anomalia: e o contrato de entrega ao menos uma vez. O
        # log nao pode crescer, e a resposta e False.
        primeiro = self._primeiro()
        self.assertFalse(self.log.anexar(primeiro))
        self.assertEqual(self.log.seq_atual(), 1)

    def test_mesma_chave_com_payload_diferente_e_conflito(self):
        self._primeiro()
        ev = evento(2, "k1", self.log.ultimo_hash(),
                    payload="sha256:" + "b" * 64)
        with self.assertRaises(EventoConflitoIdempotencia) as ctx:
            self.log.anexar(ev)
        self.assertIn("reutilizada", str(ctx.exception))

    def test_nada_e_escrito_quando_a_anexacao_e_recusada(self):
        # O log e append-only: escrever e so depois recusar seria
        # irreversivel.
        self._primeiro()
        tamanho = os.path.getsize(self.caminho)
        with self.assertRaises(EventoAdulterado):
            self.log.anexar(evento(2, "k2", "f" * 64))
        self.assertEqual(os.path.getsize(self.caminho), tamanho)

    # --- verificar(): a releitura por um terceiro ----------------------

    def test_cauda_truncada_e_recusada(self):
        # O que uma queda de energia deixa: ultima linha sem terminador.
        self._primeiro()
        with open(self.caminho, "ab") as f:
            f.write(b'{"parcial": ')
        with self.assertRaises(EventoTruncado) as ctx:
            EventLog.verificar(self.caminho, GENESE)
        self.assertIn("cauda truncada", str(ctx.exception))

    def test_linha_nao_canonica_e_recusada(self):
        # A propriedade que impede edicao local silenciosa: a linha crua
        # tem de SER a serializacao canonica. Um espaco a mais basta.
        ev = self._primeiro()
        linha = canonico(ev.to_dict()).decode("utf-8")
        with open(self.caminho, "wb") as f:
            f.write((linha.replace(",", ", ", 1) + "\n").encode("utf-8"))
        with self.assertRaises(EventoAdulterado) as ctx:
            EventLog.verificar(self.caminho, GENESE)
        self.assertIn("nao canonica", str(ctx.exception))

    def test_linha_ilegivel_e_recusada(self):
        self._primeiro()
        with open(self.caminho, "wb") as f:
            f.write(b"isto nao e json\n")
        with self.assertRaises(EventoTruncado) as ctx:
            EventLog.verificar(self.caminho, GENESE)
        self.assertIn("invalida", str(ctx.exception))

    def test_evento_fora_de_schema_no_disco_e_recusado(self):
        self._primeiro()
        with open(self.caminho, "wb") as f:
            f.write(b'{"evento_id": "x"}\n')
        with self.assertRaises(EventoTruncado) as ctx:
            EventLog.verificar(self.caminho, GENESE)
        self.assertIn("fora de schema", str(ctx.exception))

    def test_log_intacto_verifica_e_devolve_a_cadeia(self):
        # Contraprova: sem ela, um verificador que recusasse sempre
        # passaria em todos os testes acima.
        primeiro = self._primeiro()
        segundo = evento(2, "k2", hash_evento(primeiro))
        self.assertTrue(self.log.anexar(segundo))
        registros = EventLog.verificar(self.caminho, GENESE)
        self.assertEqual([r["evento"].seq for r in registros], [1, 2])
        self.assertEqual(registros[-1]["hash"], self.log.ultimo_hash())

    def test_log_vazio_verifica_sem_erro(self):
        # A outra metade: log recem-criado nao e cadeia quebrada.
        self.assertEqual(EventLog.verificar(self.caminho, GENESE), [])


if __name__ == "__main__":
    unittest.main()
