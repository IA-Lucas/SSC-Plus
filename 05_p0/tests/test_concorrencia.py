"""Escritor unico: concorrencia serializa; segundo escritor e detectado."""

import os
import tempfile
import threading
import unittest

import apoio
from ssc_p0.canonico import canonico, novo_id
from ssc_p0.eventlog import EventLog


class TestConcorrencia(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lab = apoio.novo_lab(self._tmp.name)
        self.k = self.lab.kernel

    def tearDown(self):
        self._tmp.cleanup()

    def _log_path(self):
        return os.path.join(self.k.raiz, "logs",
                            f"{self.k.envelope.sessao_id}.jsonl")

    def test_escritor_unico_appends_concorrentes_serializam_seq(self):
        n_threads, n_por_thread = 8, 5
        erros = []

        def trabalhador(t):
            try:
                for i in range(n_por_thread):
                    self.k.registrar_memoria(
                        {"fonte": f"thread-{t}", "validade": "sessao",
                         "rotulo": f"m-{t}-{i}"}, None)
            except Exception as exc:  # pragma: no cover
                erros.append(exc)

        threads = [threading.Thread(target=trabalhador, args=(t,))
                   for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(erros, [])
        registros = self.k.verificar_integridade()
        seqs = [r["evento"].seq for r in registros]
        esperado = 1 + n_threads * n_por_thread
        self.assertEqual(seqs, list(range(1, esperado + 1)))
        self.assertEqual(len(self.k.memoria), n_threads * n_por_thread)

    def test_segundo_escritor_direto_no_arquivo_detectado(self):
        apoio.fluxo_sucesso(self.lab)
        # Escritor estranho ao kernel escreve direto no arquivo (proibido).
        registros = EventLog.verificar(self._log_path(),
                                       self.k.log.hash_genese)
        ultimo = registros[-1]
        forjado = ultimo["evento"].to_dict()
        forjado["evento_id"] = novo_id()
        forjado["seq"] = ultimo["evento"].seq + 1
        forjado["prev_event_hash"] = "f" * 64  # cadeia quebrada
        with open(self._log_path(), "ab") as f:
            f.write(canonico(forjado) + b"\n")
        from ssc_p0.eventlog import EventoAdulterado
        with self.assertRaises(EventoAdulterado):
            self.k.verificar_integridade()


if __name__ == "__main__":
    unittest.main()
