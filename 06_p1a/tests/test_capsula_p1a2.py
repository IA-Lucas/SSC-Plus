"""Regressoes da P1-A.2 — capsula subscription-only + F-1/F-2 (experimental).

Cobre, uma classe por tema:

1. Capsula: ambiente-filho sem nenhuma credencial de modelo; o ambiente
   global NUNCA e mutado; reauditoria fail-closed; entry point com argv
   em lista e shell=False; processo fora da capsula aborta.
2. Injecao: NVIDIA_API_KEY dentro da capsula bloqueia o preflight ANTES
   de qualquer sonda, mesmo sem provider NVIDIA na frota.
3. F-1: _argv expande SOMENTE o ~ do executavel (sem expandvars, sem
   shell); argumentos preservados; metacaracteres literais; caminho
   inexistente -> CliIndisponivel.
4. F-2: _login_codex avalia stdout E stderr; rc!=0 e marcador negativo
   vencem; conflito entre canais -> desconhecido/BLOCKED; saida bruta
   nunca persistida.
5. Zero segredo: erros e excecoes carregam NOMES, nunca valores.

Nenhum teste invoca modelo, rede ou subprocesso real (subprocess.run e
substituido por dublê; as sondas usam SensorFalso).
"""

import os
import unittest
from unittest import mock

import apoio
from apoio import SENTINELA, SensorFalso, espec_com, sensores_dict
from preflight import executar_preflight
from preflight.adaptadores import AdaptadorPreflight, _login_codex
from preflight.economia import CliIndisponivel

import capsula
from capsula import (ViolacaoCapsula, ambiente_capsula,
                     exigir_capsula_limpa, verificar_capsula)

_ENV_SUJO = {
    "PATH": r"C:\Windows\System32",
    "HOME": r"C:\Users\alguem",
    "NVIDIA_API_KEY": SENTINELA,
    "OPENAI_API_KEY": SENTINELA,
    "XAI_API_KEY": SENTINELA,
    "outra_Auth_Token": SENTINELA,
    "MEU_ACCESS_TOKEN": SENTINELA,
    "segredo_api_secret": SENTINELA,
    "SECRET_KEY": SENTINELA,
    "svcBearerToken": SENTINELA,
    "api_key": SENTINELA,
    "EDITOR_LOCAL_TOKEN": "token-local-sem-cara-de-credencial",
}


class CapsulaAmbiente(unittest.TestCase):
    """A capsula remove TODA credencial de modelo e nao muta o global."""

    def test_remove_todos_os_padroes_proibidos(self):
        limpo = ambiente_capsula(_ENV_SUJO)
        self.assertEqual(verificar_capsula(limpo), [])
        self.assertNotIn("NVIDIA_API_KEY", limpo)

    def test_mantem_variaveis_inocuas(self):
        limpo = ambiente_capsula(_ENV_SUJO)
        self.assertEqual(limpo["PATH"], _ENV_SUJO["PATH"])
        self.assertEqual(limpo["EDITOR_LOCAL_TOKEN"],
                         "token-local-sem-cara-de-credencial")

    def test_nunca_muta_o_ambiente_de_origem(self):
        original = dict(_ENV_SUJO)
        ambiente_capsula(_ENV_SUJO)
        self.assertEqual(_ENV_SUJO, original)  # global/HKCU intocado

    def test_verificar_capsula_devolve_somente_nomes(self):
        nomes = verificar_capsula(_ENV_SUJO)
        self.assertIn("NVIDIA_API_KEY", nomes)
        self.assertNotIn(SENTINELA, " ".join(nomes))

    def test_guarda_de_entrada_aborta_fora_da_capsula(self):
        with self.assertRaises(ViolacaoCapsula) as ctx:
            exigir_capsula_limpa({"NVIDIA_API_KEY": SENTINELA})
        self.assertNotIn(SENTINELA, str(ctx.exception))  # so o nome

    def test_guarda_de_entrada_aceita_capsula_limpa(self):
        exigir_capsula_limpa(ambiente_capsula(_ENV_SUJO))  # nao levanta

    def test_reauditoria_fail_closed(self):
        # Se a filtragem falhar em silencio, a reauditoria levanta.
        with mock.patch.object(capsula, "verificar_capsula",
                               side_effect=[["X_API_KEY"]]):
            with self.assertRaises(ViolacaoCapsula):
                ambiente_capsula({"X_API_KEY": SENTINELA})


class CapsulaEntryPoint(unittest.TestCase):
    """iniciar_em_capsula: argv lista, shell=False, env-filho limpo."""

    def test_argv_str_proibida(self):
        with self.assertRaises(TypeError):
            capsula.iniciar_em_capsula("python --version")

    def test_filho_recebe_env_limpo_e_shell_false(self):
        capturado = {}
        antes = os.environ.get("NVIDIA_API_KEY")

        def run_falso(argv, **kwargs):
            capturado["argv"] = argv
            capturado.update(kwargs)

            class R:
                returncode = 0
                stdout = ""
                stderr = ""
            return R()

        with mock.patch.object(capsula.subprocess, "run", run_falso):
            with mock.patch.dict(os.environ, {"NVIDIA_API_KEY": SENTINELA}):
                capsula.iniciar_em_capsula(["python", "--version"])
        self.assertIsInstance(capturado["argv"], list)
        self.assertFalse(capturado["shell"])
        self.assertEqual(verificar_capsula(capturado["env"]), [])
        self.assertNotIn(SENTINELA, str(capturado["env"].values()))
        # o ambiente do pai segue intacto (comparacao booleana: nenhum
        # valor real aparece em mensagem de falha)
        self.assertTrue(os.environ.get("NVIDIA_API_KEY") == antes)


class InjecaoNvidiaNaCapsula(unittest.TestCase):
    """NVIDIA_API_KEY visivel dentro da capsula = BLOCKED pre-sonda."""

    def test_bloqueia_os_cinco_antes_de_qualquer_sonda(self):
        for pid in ("codex", "claude", "kimi", "google", "grok"):
            sens, sensor_exec, sensor_modelos = sensores_dict(pid)
            rel = executar_preflight(
                espec_com(pid), sensores=sens,
                env={"NVIDIA_API_KEY": SENTINELA, "PATH": "x"})
            self.assertEqual(rel.resultado, "BLOCKED", pid)
            self.assertIn("P1A-PAYG-ENV", apoio.codigos(rel), pid)
            self.assertEqual(sensor_exec.n, 0, f"sonda exec em {pid}")
            self.assertEqual(sensor_modelos.n, 0, f"sonda modelos em {pid}")

    def test_erro_carrega_nome_nunca_valor(self):
        rel = executar_preflight(
            espec_com("codex"), sensores=sensores_dict("codex")[0],
            env={"NVIDIA_API_KEY": SENTINELA})
        texto = " ".join(e.detalhe + str(e.alvo) for e in rel.erros)
        self.assertIn("NVIDIA_API_KEY", texto)
        self.assertNotIn(SENTINELA, texto)


class F1ExpansaoDoExecutavel(unittest.TestCase):
    """_argv expande SOMENTE o ~ do executavel, sem expandvars nem shell."""

    def _argv(self, executavel, comando=("--version",)):
        espec = espec_com("claude", executavel=executavel)
        return AdaptadorPreflight(espec, sensor_exec=SensorFalso())._argv(
            comando)

    def test_til_expandido_no_executavel(self):
        argv = self._argv("~/.local/bin/claude")
        self.assertEqual(argv[0], os.path.expanduser("~/.local/bin/claude"))
        self.assertFalse(argv[0].startswith("~"))

    def test_expandvars_nao_aplicado(self):
        argv = self._argv("$HOME/bin/claude")
        self.assertEqual(argv[0], "$HOME/bin/claude")  # literal

    def test_argumentos_preservados_com_espacos(self):
        argv = self._argv("~/bin/claude", ("auth", "status detalhado"))
        self.assertEqual(list(argv[1:]), ["auth", "status detalhado"])

    def test_metacaracteres_sao_literais_no_argv(self):
        alvo = "~/bin/claude; echo $HOME $(id) `id` & | > <"
        argv = self._argv(alvo)
        self.assertEqual(argv[0], os.path.expanduser(alvo))

    def test_caminho_inexistente_vira_cli_indisponivel(self):
        espec = espec_com("claude", executavel="~/nao-existe-xyz/claude")
        sensor = SensorFalso(erro=FileNotFoundError("nao existe"))
        adp = AdaptadorPreflight(espec, sensor_exec=sensor)
        with self.assertRaises(CliIndisponivel):
            adp.detectar_versao()
        # o sensor recebeu o caminho EXPANDIDO (prova de que o erro vem
        # do SO, nao de um til cru)
        self.assertEqual(sensor.chamadas, [("--version",)])

    def test_pipeline_claude_kimi_ate_o_teto_com_til(self):
        # Emenda P1-A.3: claude tem teto SUPERVISED; kimi segue ELIGIBLE.
        esperado = {"claude": "SUPERVISED", "kimi": "ELIGIBLE"}
        for pid, resultado in esperado.items():
            sens, sensor_exec, _ = sensores_dict(pid)
            rel = executar_preflight(espec_com(pid), sensores=sens,
                                     env={"PATH": "x"})
            self.assertEqual(rel.resultado, resultado, pid)
            # a 1a sonda (versao) recebeu o executavel sem til cru
            self.assertTrue(sensor_exec.n >= 1)


class F2LoginCodexDoisCanais(unittest.TestCase):
    """_login_codex avalia stdout E stderr; negativo/rc vence; conflito
    resulta desconhecido/BLOCKED; saida bruta nao persistida."""

    POS = "Logged in using ChatGPT (plan: ChatGPT Pro 5x)"

    def test_login_so_em_stdout(self):
        r = _login_codex(0, self.POS, "", espec_com("codex"))
        self.assertTrue(r["logado"])
        self.assertEqual(r["plano"], "chatgpt pro 5x")

    def test_login_so_em_stderr(self):
        r = _login_codex(0, "", self.POS, espec_com("codex"))
        self.assertTrue(r["logado"])
        self.assertEqual(r["plano"], "chatgpt pro 5x")

    def test_login_em_ambos(self):
        r = _login_codex(0, "Logged in using ChatGPT", self.POS,
                         espec_com("codex"))
        self.assertTrue(r["logado"])

    def test_rc_nao_zero_vence_marcador_positivo(self):
        r = _login_codex(1, "", self.POS, espec_com("codex"))
        self.assertFalse(r["logado"])

    def test_negacao_em_stderr_vence_positivo_em_stdout(self):
        r = _login_codex(0, "Logged in using ChatGPT",
                         "Error: not logged in", espec_com("codex"))
        self.assertFalse(r["logado"])  # conflito -> desconhecido/BLOCKED

    def test_negacao_em_stdout_vence_positivo_em_stderr(self):
        r = _login_codex(0, "not logged in", self.POS, espec_com("codex"))
        self.assertFalse(r["logado"])

    def test_quota_esgotada_lida_do_stderr(self):
        r = _login_codex(0, "", self.POS + "; requests remaining: 0",
                         espec_com("codex"))
        self.assertEqual(r["quota"], "esgotada")

    def test_saida_bruta_nao_e_persistida(self):
        r = _login_codex(0, "", self.POS, espec_com("codex"))
        self.assertEqual(set(r), {"logado", "plano", "origem_credencial",
                                  "quota"})

    def test_pipeline_codex_eligible_com_login_em_stderr(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        sensor_exec.respostas[("login", "status")] = (0, "", self.POS)
        rel = executar_preflight(espec_com("codex"), sensores=sens,
                                 env={"PATH": "x"})
        self.assertEqual(rel.resultado, "ELIGIBLE")
        self.assertEqual(rel.plano, "chatgpt pro 5x")

    def test_pipeline_codex_conflito_de_canais_bloqueia(self):
        sens, sensor_exec, _ = sensores_dict("codex")
        sensor_exec.respostas[("login", "status")] = (
            0, "Logged in using ChatGPT", "not logged in")
        rel = executar_preflight(espec_com("codex"), sensores=sens,
                                 env={"PATH": "x"})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-OAUTH-AUSENTE", apoio.codigos(rel))


if __name__ == "__main__":
    unittest.main()
