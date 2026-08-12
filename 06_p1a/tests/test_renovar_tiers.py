"""Renovacao de tiers: ato explicito, backup e fence no caminho real."""

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone

import apoio  # noqa: F401

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if os.path.join(_RAIZ, "06_p1a") not in sys.path:
    sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))

import renovar_tiers as rt  # noqa: E402


class RenovacaoDoProprietario(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tiers-renovar-")
        self.addCleanup(self.tmp.cleanup)
        self.original = (rt.CAMINHO_TIERS, rt.DIR_BACKUPS,
                         rt._verificar_lock_vivo)
        rt.CAMINHO_TIERS = os.path.join(self.tmp.name, "tiers.json")
        rt.DIR_BACKUPS = os.path.join(self.tmp.name, "backups")
        with open(os.path.join(_RAIZ, "06_p1a", "tiers_declarados.json"),
                  encoding="utf-8") as fonte:
            self.dados = json.load(fonte)
        with open(rt.CAMINHO_TIERS, "w", encoding="utf-8") as destino:
            json.dump(self.dados, destino)
        self.chamadas_lock = []

        def lock(fence=None):
            self.chamadas_lock.append(fence)
            return {"fence": 17}

        rt._verificar_lock_vivo = lock
        self.addCleanup(self._restaurar)

    def _restaurar(self):
        rt.CAMINHO_TIERS, rt.DIR_BACKUPS, rt._verificar_lock_vivo = self.original

    def args(self, confirmar=True):
        argumentos = ["--codex-tier", "ChatGPT Pro 5x",
                      "--kimi-tier", "Allegretto",
                      "--google-tier", "Google AI Pro"]
        return (["--confirmo-proprietario"] + argumentos
                if confirmar else argumentos)

    def bytes_atuais(self):
        with open(rt.CAMINHO_TIERS, "rb") as arquivo:
            return arquivo.read()

    def test_sem_confirmacao_explicita_nao_muda_nem_cria_backup(self):
        antes = self.bytes_atuais()
        with self.assertRaises(SystemExit):
            rt.main(self.args(confirmar=False))
        self.assertEqual(self.bytes_atuais(), antes)
        self.assertFalse(os.path.exists(rt.DIR_BACKUPS))

    def test_main_faz_backup_antes_e_publica_tiers_com_mesmo_fence(self):
        instante = datetime(2026, 8, 11, 18, 30, tzinfo=timezone.utc)
        original_agora = rt.agora_utc
        rt.agora_utc = lambda: instante
        self.addCleanup(setattr, rt, "agora_utc", original_agora)
        self.assertEqual(rt.main(self.args()), 0)
        self.assertEqual(self.chamadas_lock, [None, 17])
        backups = os.listdir(rt.DIR_BACKUPS)
        self.assertEqual(len(backups), 1)
        with open(os.path.join(rt.DIR_BACKUPS, backups[0]), encoding="utf-8") as f:
            self.assertEqual(json.load(f), self.dados)
        with open(rt.CAMINHO_TIERS, encoding="utf-8") as f:
            novo = json.load(f)
        self.assertEqual({d["declarado_em_utc"] for d in novo["declaracoes"]},
                         {"2026-08-11T18:30:00Z"})
        self.assertEqual({d["declarado_por"] for d in novo["declaracoes"]},
                         {"proprietario"})

    def test_tier_divergente_para_antes_do_lock_e_do_backup(self):
        with self.assertRaises(SystemExit) as ctx:
            rt.renovar({"codex": "API paga", "kimi": "Allegretto",
                        "google": "Google AI Pro"})
        self.assertIn("diverge", str(ctx.exception))
        self.assertEqual(self.chamadas_lock, [])
        self.assertFalse(os.path.exists(rt.DIR_BACKUPS))

    def test_perda_do_fence_depois_do_backup_nao_altera_declaracao(self):
        antes = self.bytes_atuais()

        def lock(fence=None):
            if fence is not None:
                raise SystemExit("lock perdido")
            return {"fence": 23}

        rt._verificar_lock_vivo = lock
        with self.assertRaises(SystemExit):
            rt.renovar({"codex": "ChatGPT Pro 5x", "kimi": "Allegretto",
                        "google": "Google AI Pro"},
                       datetime(2026, 8, 11, tzinfo=timezone.utc))
        self.assertEqual(self.bytes_atuais(), antes)
        self.assertEqual(len(os.listdir(rt.DIR_BACKUPS)), 1)

    def test_comando_isolado_alcanca_o_guarda_canonico_real(self):
        """Exerce o import/lock que a operacao percorre, sem apoio.py."""
        caminho_modulo = os.path.join(_RAIZ, "06_p1a", "renovar_tiers.py")
        codigo = textwrap.dedent(f"""
            import importlib.util
            import os
            import tempfile

            spec = importlib.util.spec_from_file_location(
                "renovar_tiers_isolado", {caminho_modulo!r})
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            from escritor_repositorio import EscritorRepositorio

            with tempfile.TemporaryDirectory(prefix="tiers-lock-real-") as raiz:
                escritor = EscritorRepositorio(
                    os.path.join(raiz, "locks"), sessao="teste-renovacao",
                    lease_s=120)
                token = escritor.adquirir()
                try:
                    modulo._RAIZ = raiz
                    modulo.SESSAO_LOCK = "teste-renovacao"
                    estado = modulo._verificar_lock_vivo()
                    assert estado["fence"] == token, estado
                finally:
                    escritor.liberar()
        """)
        ambiente = dict(os.environ)
        ambiente.pop("PYTHONPATH", None)
        proc = subprocess.run(
            [sys.executable, "-I", "-c", codigo], cwd=self.tmp.name,
            env=ambiente, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
