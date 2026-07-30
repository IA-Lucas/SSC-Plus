"""Seguranca: IC-4 (segredos), IC-5 (contencao de caminho), zero escrita externa."""

import os
import tempfile
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.cas import FugaDeCaminho, resolver_contido
from ssc_p0.kernel import SegredoDetectado, SessionKernel


class TestSeguranca(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.lab = apoio.novo_lab(self._tmp.name)
        self.k = self.lab.kernel

    def tearDown(self):
        self._tmp.cleanup()

    # -- IC-4 ----------------------------------------------------------------

    def test_ic4_segredo_em_evento_recusado(self):
        with self.assertRaises(SegredoDetectado):
            self.k.registrar_memoria(
                {"fonte": "teste", "validade": "sessao",
                 "rotulo": 'api_key: "AKIA1234567890ABCDEF"'}, None)

    def test_ic4_segredo_padrao_token_em_payload_recusado(self):
        with self.assertRaises(SegredoDetectado):
            self.k._emitir("memoria",
                           {"acao": "registrar",
                            "entrada": {"fonte": "t", "validade": "s",
                                        "rotulo": "password: sup3rsegreda123"}},
                           causado_por=None)

    def test_ic4_segredo_em_contexto_recusado(self):
        with self.assertRaises(SegredoDetectado):
            self.k.montar_contexto(
                "wu",
                [{"origem": "inline:segredo", "papel": "evidencia",
                  "inclusao": "verbatim",
                  "conteudo": "-----BEGIN PRIVATE KEY-----\nabc"}])

    def test_ic4_contexto_limpo_aceito(self):
        pacote = self.k.montar_contexto(
            "wu",
            [{"origem": "inline:ok", "papel": "evidencia",
              "inclusao": "verbatim", "conteudo": "texto absolutamente limpo"}])
        pacote.validate()

    # -- IC-5 ------------------------------------------------------------------

    def test_ic5_fuga_caminho_dotdot_recusada(self):
        fora = os.path.join(self.k.raiz, "..", "fora_da_raiz.txt")
        with self.assertRaises(FugaDeCaminho):
            resolver_contido(fora, [self.k.raiz])
        with self.assertRaises(FugaDeCaminho):
            self.k.montar_contexto(
                "wu", [{"origem": fora, "papel": "evidencia",
                        "inclusao": "verbatim"}])

    def test_ic5_fuga_por_symlink_mock_do_resolvedor(self):
        # Resolvedor mock: simula junction apontando para fora da raiz.
        alvo_fora = os.path.join(tempfile.gettempdir(), "alvo_secreto_fora")
        dentro = os.path.join(self.k.raiz, "link_falso.txt")
        resolvedor_mock = lambda p: (
            alvo_fora if os.path.normpath(p) == os.path.normpath(dentro)
            else os.path.realpath(p))
        with self.assertRaises(FugaDeCaminho):
            resolver_contido(dentro, [self.k.raiz], resolvedor=resolvedor_mock)

    def test_ic5_fuga_por_symlink_real(self):
        alvo = os.path.join(self._tmp.name, "alvo_real.txt")
        with open(alvo, "w", encoding="utf-8") as f:
            f.write("conteudo do alvo fora do lab")
        link = os.path.join(self.k.raiz, "link_real.txt")
        try:
            os.symlink(alvo, link)
        except OSError as exc:
            self.skipTest(
                f"Windows sem privilegio para criar symlink ({exc}); "
                "cobertura garantida pelo teste com mock do resolvedor")
        with self.assertRaises(FugaDeCaminho):
            self.k.montar_contexto(
                "wu", [{"origem": link, "papel": "evidencia",
                        "inclusao": "verbatim"}])

    # -- zero escrita externa -----------------------------------------------------

    def test_zero_escrita_externa_tudo_sob_a_raiz(self):
        tmp2 = tempfile.TemporaryDirectory()
        try:
            raiz_lab = os.path.join(tmp2.name, "lab")
            lab = apoio.novo_lab(tmp2.name)
            apoio.fluxo_sucesso(lab)
            lab.kernel.gravar_checkpoint()
            lab.kernel.suspender()
            SessionKernel.retomar(lab.raiz, lab.envelope.sessao_id,
                                  relogio=lab.relogio)
            # Todo arquivo criado no tmp esta sob a raiz declarada do lab.
            criados = []
            for base, _dirs, arquivos in os.walk(tmp2.name):
                for nome in arquivos:
                    criados.append(os.path.join(base, nome))
            self.assertTrue(criados)
            for caminho in criados:
                self.assertTrue(
                    os.path.normcase(os.path.realpath(caminho)).startswith(
                        os.path.normcase(os.path.realpath(raiz_lab))),
                    f"arquivo fora da raiz declarada: {caminho}")
        finally:
            tmp2.cleanup()


if __name__ == "__main__":
    unittest.main()
