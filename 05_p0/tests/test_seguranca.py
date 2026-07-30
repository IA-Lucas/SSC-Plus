"""Seguranca: IC-4 (segredos), IC-5 (contencao de caminho), zero escrita externa.

0.2.1: teste REAL de junction/reparse point no Windows (mklink /J nao exige
privilegio) — mock nao substitui prova real. Temporarios na pasta ignorada
do laboratorio (apoio.DIR_TESTS), limpos por teste.
"""

import os
import subprocess
import unittest
import uuid

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import novo_id
from ssc_p0.cas import FugaDeCaminho, ler_arquivo_contido, resolver_contido
from ssc_p0.kernel import SegredoDetectado, SessionKernel


class TestSeguranca(unittest.TestCase):
    def setUp(self):
        self.lab = apoio.novo_lab()
        self.k = self.lab.kernel

    def tearDown(self):
        apoio.limpar_lab(self.lab)

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
                novo_id(),
                [{"origem": "inline:segredo", "papel": "evidencia",
                  "inclusao": "verbatim",
                  "conteudo": "-----BEGIN PRIVATE KEY-----\nabc"}])

    def test_ic4_contexto_limpo_aceito(self):
        pacote = self.k.montar_contexto(
            novo_id(),
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
                novo_id(), [{"origem": fora, "papel": "evidencia",
                             "inclusao": "verbatim"}])

    def test_ic5_fuga_por_symlink_mock_do_resolvedor(self):
        # Resolvedor mock: simula junction apontando para fora da raiz.
        alvo_fora = os.path.join(os.path.dirname(self.k.raiz),
                                 "alvo_secreto_fora")
        dentro = os.path.join(self.k.raiz, "link_falso.txt")
        resolvedor_mock = lambda p: (
            alvo_fora if os.path.normpath(p) == os.path.normpath(dentro)
            else os.path.realpath(p))
        with self.assertRaises(FugaDeCaminho):
            resolver_contido(dentro, [self.k.raiz], resolvedor=resolvedor_mock)

    def test_ic5_fuga_por_junction_real(self):
        """PROVA REAL (Windows): junction/reparse point criado de verdade.

        mklink /J nao exige privilegio. Se a criacao falhar, o teste FALHA
        (teste critico nao pode ficar skipped para liberar P1). Fora do
        Windows, usa symlink de diretorio.
        """
        base = os.path.dirname(self.k.raiz)
        alvo = os.path.join(base, "alvo_junction_real")
        os.makedirs(alvo, exist_ok=True)
        with open(os.path.join(alvo, "segredo.txt"), "w",
                  encoding="utf-8") as f:
            f.write("conteudo fora do lab, alcancado via reparse point")
        link = os.path.join(self.k.raiz, "junction_dir")
        if os.name == "nt":
            resultado = subprocess.run(
                ["cmd", "/c", "mklink", "/J", link, alvo],
                capture_output=True, text=True)
            self.assertEqual(
                resultado.returncode, 0,
                f"mklink /J falhou (ambiente Windows nao preparado): "
                f"{resultado.stdout}{resultado.stderr}")
            self.assertTrue(os.path.isdir(link))
        else:
            os.symlink(alvo, link, target_is_directory=True)
        caminho_via_link = os.path.join(link, "segredo.txt")
        # O resolvedor real atravessa o reparse point: fuga detectada.
        with self.assertRaises(FugaDeCaminho):
            resolver_contido(caminho_via_link, [self.k.raiz])
        with self.assertRaises(FugaDeCaminho):
            ler_arquivo_contido(caminho_via_link, [self.k.raiz])
        with self.assertRaises(FugaDeCaminho):
            self.k.montar_contexto(
                novo_id(), [{"origem": caminho_via_link, "papel": "evidencia",
                             "inclusao": "verbatim"}])

    # -- zero escrita externa -----------------------------------------------------

    def test_zero_escrita_externa_tudo_sob_a_raiz(self):
        base = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        lab = apoio.novo_lab(base)
        try:
            raiz_lab = lab.raiz
            apoio.fluxo_sucesso(lab)
            lab.kernel.gravar_checkpoint()
            lab.kernel.suspender()
            lab.kernel._simular_crash()
            k2 = SessionKernel.retomar(lab.raiz, lab.envelope.sessao_id,
                                       relogio=lab.relogio)
            k2.fechar()
            # Todo arquivo criado esta sob a raiz declarada do lab.
            criados = []
            for base_dir, _dirs, arquivos in os.walk(base):
                for nome in arquivos:
                    criados.append(os.path.join(base_dir, nome))
            self.assertTrue(criados)
            for caminho in criados:
                self.assertTrue(
                    os.path.normcase(os.path.realpath(caminho)).startswith(
                        os.path.normcase(os.path.realpath(raiz_lab))),
                    f"arquivo fora da raiz declarada: {caminho}")
        finally:
            apoio.limpar_lab(lab)


if __name__ == "__main__":
    unittest.main()
