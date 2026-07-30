"""Crash, checkpoint e retomada: orfao->indeterminado, IP-1/IP-2, IP-4."""

import json
import os
import tempfile
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import canonico, novo_id
from ssc_p0.kernel import CheckpointInvalido, SessionKernel


class TestCrashCheckpoint(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lab = apoio.novo_lab(self._tmp.name)
        self.k = self.lab.kernel

    def tearDown(self):
        self._tmp.cleanup()

    def _attempt_despachado(self):
        wu = self.lab.router.forjar(
            intencao="tarefa que vai travar no meio",
            criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        attempt = ct.ExecutionAttempt(
            attempt_id=novo_id(), work_unit_id=wu.work_unit_id,
            decisao_id=d.decisao_id,
            linhagem_id=self.k.envelope.linhagem_id,
            selecao_solicitada=d.selecao,
            executor_resolvido={"provedor": "prov-a", "modelo": "modelo-x",
                                "effort": "alto",
                                "hash_catalogo": self.k.envelope.catalogo_ref,
                                "alias_usado": False},
            executor_observado=None,
            vinculos=self.k.vinculos_correntes(d.hash_pacote),
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo=None, custo_medido=None, artefato_ref=None)
        ev_criar = self.k.criar_attempt(attempt, None)
        self.k.despachar_attempt(attempt.attempt_id, ev_criar.evento_id)
        return wu, attempt

    def test_crash_antes_de_persistir_conclusao_orfao_indeterminado(self):
        wu, attempt = self._attempt_despachado()
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        del self.k  # "crash": nenhuma conclusao persistida
        k2 = SessionKernel.retomar(self.lab.raiz, sessao,
                                   relogio=self.lab.relogio)
        reg = k2.attempts[attempt.attempt_id]
        self.assertEqual(reg["estado"], "orfao")
        self.assertEqual(reg["attempt"].resultado, "indeterminado")
        self.assertEqual(reg["attempt"].efeito_externo, "incerto")
        self.assertNotEqual(reg["attempt"].resultado, "sucesso")
        # Marcacao do orfao e a primeira operacao pos-retomada (D5 §1.2).
        self.assertEqual(k2.envelope.estado, "ativa")

    def test_crash_depois_de_persistir_retomada_limpa(self):
        apoio.fluxo_sucesso(self.lab)
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        k2 = SessionKernel.retomar(self.lab.raiz, sessao,
                                   relogio=self.lab.relogio)
        # Nenhum orfao: tudo concluido antes do crash.
        self.assertFalse(any(r["estado"] == "orfao"
                             for r in k2.attempts.values()))
        k2.verificar_integridade()

    def test_checkpoint_retomada_feliz_estado_identico(self):
        apoio.fluxo_sucesso(self.lab)
        self.k.registrar_memoria(
            {"fonte": "t", "validade": "sessao", "rotulo": "nota"}, None)
        self.k.gravar_checkpoint()
        snap_antes = apoio.snapshot_normalizado(self.k)
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        k2 = SessionKernel.retomar(self.lab.raiz, sessao,
                                   relogio=self.lab.relogio)
        snap_depois = apoio.snapshot_normalizado(k2)
        self.assertEqual(snap_antes, snap_depois)

    def _checkpoint_path(self):
        diretorio = os.path.join(self.k.raiz, "checkpoints",
                                 self.k.envelope.sessao_id)
        return os.path.join(diretorio, sorted(os.listdir(diretorio))[-1])

    def test_checkpoint_invalido_nao_retoma_escalona(self):
        apoio.fluxo_sucesso(self.lab)
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        caminho = self._checkpoint_path()
        with open(caminho, "rb") as f:
            dados = json.loads(f.read())
        dados["estado_refs"]["seq"] += 1  # adultera conteudo (selo diverge)
        with open(caminho, "wb") as f:
            f.write(canonico(dados))
        seq_antes = self.k.log.seq_atual()
        with self.assertRaises(CheckpointInvalido):
            SessionKernel.retomar(self.lab.raiz, sessao,
                                  relogio=self.lab.relogio)
        # Nao retomou: nenhum evento novo no log.
        self.assertEqual(self.k.log.seq_atual(), seq_antes)

    def test_checkpoint_selo_divergente_nao_retoma(self):
        apoio.fluxo_sucesso(self.lab)
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        caminho = self._checkpoint_path()
        with open(caminho, "rb") as f:
            dados = json.loads(f.read())
        dados["selo"] = ("0" if dados["selo"][0] != "0" else "1") \
            + dados["selo"][1:]
        with open(caminho, "wb") as f:
            f.write(canonico(dados))
        with self.assertRaises(CheckpointInvalido):
            SessionKernel.retomar(self.lab.raiz, sessao,
                                  relogio=self.lab.relogio)

    def test_log_adulterado_nao_retoma(self):
        apoio.fluxo_sucesso(self.lab)
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        log_path = os.path.join(self.k.raiz, "logs", f"{sessao}.jsonl")
        with open(log_path, "rb") as f:
            linhas = f.read().split(b"\n")[:-1]
        meio = json.loads(linhas[1].decode("utf-8"))
        meio["payload_ref"] = "0" * 64
        linhas[1] = canonico(meio)
        with open(log_path, "wb") as f:
            for linha in linhas:
                f.write(linha + b"\n")
        from ssc_p0.eventlog import EventoAdulterado
        with self.assertRaises(EventoAdulterado):
            SessionKernel.retomar(self.lab.raiz, sessao,
                                  relogio=self.lab.relogio)


if __name__ == "__main__":
    unittest.main()
