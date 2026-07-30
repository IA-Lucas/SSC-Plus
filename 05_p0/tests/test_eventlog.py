"""EventLog: idempotencia, replay deterministico (IP-4) e as 4 corrupcoes."""

import json
import os
import tempfile
import unittest

import apoio
from ssc_p0.canonico import canonico, novo_id
from ssc_p0.eventlog import (EventLog, EventoAdulterado, EventoDuplicado,
                             EventoForaDeOrdem, EventoTruncado)
from ssc_p0.kernel import SessionKernel


class TestEventLog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lab = apoio.novo_lab(self._tmp.name)
        self.k = self.lab.kernel

    def tearDown(self):
        self._tmp.cleanup()

    def _log_path(self):
        return os.path.join(self.k.raiz, "logs",
                            f"{self.k.envelope.sessao_id}.jsonl")

    def test_idempotency_key_reentrega_ignorada(self):
        entrada = {"fonte": "teste", "validade": "sessao", "rotulo": "m1"}
        ev1, criado1 = self.k._emitir(
            "memoria", {"acao": "registrar", "entrada": entrada},
            causado_por=None, idempotency_key="chave-unica-1")
        self.assertTrue(criado1)
        ev2, criado2 = self.k._emitir(
            "memoria", {"acao": "registrar", "entrada": entrada},
            causado_por=None, idempotency_key="chave-unica-1")
        self.assertFalse(criado2)  # reentrega ignorada
        seqs = [r["evento"].seq for r in self.k.verificar_integridade()]
        self.assertEqual(seqs, list(range(1, len(seqs) + 1)))
        self.assertEqual(len(self.k.memoria), 1)

    def test_ip4_replay_deterministico_igual_estado_corrente(self):
        apoio.fluxo_sucesso(self.lab)
        self.k.registrar_memoria(
            {"fonte": "teste", "validade": "sessao", "rotulo": "nota"}, None)
        snap_vivo = apoio.snapshot_normalizado(self.k)
        # Replay do zero em kernel novo sobre o mesmo log (IP-4).
        k2 = SessionKernel.anexar_existente(
            self.k.raiz, self.k.envelope.sessao_id,
            relogio=self.lab.relogio)
        snap_replay = apoio.snapshot_normalizado(k2)
        self.assertEqual(snap_vivo, snap_replay)

    def _linhas(self):
        with open(self._log_path(), "rb") as f:
            return f.read().split(b"\n")[:-1]

    def _reescrever(self, linhas):
        with open(self._log_path(), "wb") as f:
            for linha in linhas:
                f.write(linha + b"\n")

    def test_evento_duplicado_detectado_falha_fechada(self):
        apoio.fluxo_sucesso(self.lab)
        registros = EventLog.verificar(self._log_path(), self.k.log.hash_genese)
        ultimo = registros[-1]
        # Forja evento com seq/prev corretos mas idempotency_key REPETIDA.
        forjado = ultimo["evento"].to_dict()
        forjado["evento_id"] = novo_id()
        forjado["seq"] = ultimo["evento"].seq + 1
        forjado["prev_event_hash"] = ultimo["hash"]
        linhas = self._linhas() + [canonico(forjado)]
        self._reescrever(linhas)
        with self.assertRaises(EventoDuplicado):
            EventLog.verificar(self._log_path(), self.k.log.hash_genese)

    def test_evento_fora_de_ordem_detectado_falha_fechada(self):
        apoio.fluxo_sucesso(self.lab)
        linhas = self._linhas()
        # Copia a primeira linha no fim: seq 1 na ultima posicao.
        linhas.append(linhas[0])
        self._reescrever(linhas)
        with self.assertRaises(EventoForaDeOrdem):
            EventLog.verificar(self._log_path(), self.k.log.hash_genese)

    def test_evento_truncado_detectado_falha_fechada(self):
        apoio.fluxo_sucesso(self.lab)
        with open(self._log_path(), "ab") as f:
            f.write(b'{"evento_id": "abc", "seq": 99')  # sem fechar/sem \n
        with self.assertRaises(EventoTruncado):
            EventLog.verificar(self._log_path(), self.k.log.hash_genese)

    def test_evento_adulterado_detectado_falha_fechada(self):
        apoio.fluxo_sucesso(self.lab)
        linhas = self._linhas()
        meio = json.loads(linhas[2].decode("utf-8"))
        meio["payload_ref"] = "0" * 64  # adultera sem quebrar o JSON
        linhas[2] = canonico(meio)
        self._reescrever(linhas)
        with self.assertRaises(EventoAdulterado):
            EventLog.verificar(self._log_path(), self.k.log.hash_genese)


if __name__ == "__main__":
    unittest.main()
