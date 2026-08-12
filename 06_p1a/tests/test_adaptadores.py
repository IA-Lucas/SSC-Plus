"""Adaptadores de diagnostico (SSC+ P1-A, experimental).

O adaptador so faz tres perguntas ao CLI: qual sua versao, qual o status
do login e quais modelos existem. Nunca executa prompt produtivo, nunca
pede pagamento, nunca escreve arquivo. Aqui nenhum subprocesso real e
criado: o sensor real (`sensor_subprocess`) e testado com `Popen`
substituido, o que permite provar que o ambiente entregue ao processo
filho vai SEM credencial.
"""

import json
import subprocess
import sys
import unittest
from unittest import mock

import apoio
from apoio import SENTINELA, SensorFalso, sensores_verdes
from preflight import (AdaptadorPreflight, CliIndisponivel, ESPECIFICACOES,
                       espec_de, extrair_modelos, plano_reconhecido,
                       sensor_subprocess)
from preflight.adaptadores import TIMEOUT_PADRAO, _quota_de


def _adaptador(provider_id="codex", **sobre):
    sensor_exec, sensor_modelos = sensores_verdes(provider_id, **sobre)
    return AdaptadorPreflight(espec_de(provider_id), sensor_exec=sensor_exec,
                              sensor_modelos=sensor_modelos, env={})


class DeteccaoDeVersao(unittest.TestCase):

    def test_versao_extraida_do_texto(self):
        self.assertEqual(_adaptador("codex").detectar_versao(), "0.145.0")
        self.assertEqual(_adaptador("claude").detectar_versao(), "2.1.220")

    def test_versao_de_quatro_componentes(self):
        self.assertEqual(
            _adaptador("kimi", versao="kimi 1.2.3.4 (build)").detectar_versao(),
            "1.2.3.4")

    def test_texto_sem_numero_cai_na_primeira_linha(self):
        adaptador = _adaptador("codex", versao="codex-cli (dev)\nlinha 2")
        self.assertEqual(adaptador.detectar_versao(), "codex-cli (dev)")

    def test_saida_vazia_devolve_none(self):
        self.assertIsNone(_adaptador("codex", versao="   ").detectar_versao())

    def test_rc_diferente_de_zero_e_cli_indisponivel(self):
        espec = espec_de("codex")
        sensor = SensorFalso({espec.comandos["versao"]: (1, "", "boom")})
        adaptador = AdaptadorPreflight(espec, sensor_exec=sensor, env={})
        with self.assertRaises(CliIndisponivel) as ctx:
            adaptador.detectar_versao()
        self.assertEqual(ctx.exception.codigo, "P1A-CLI-INDISPONIVEL")

    def test_executavel_ausente_e_cli_indisponivel(self):
        adaptador = AdaptadorPreflight(
            espec_de("codex"), sensor_exec=SensorFalso(
                erro=FileNotFoundError("codex.exe")), env={})
        with self.assertRaises(CliIndisponivel):
            adaptador.detectar_versao()

    def test_argv_usa_o_executavel_declarado(self):
        adaptador = _adaptador("codex")
        adaptador.detectar_versao()
        self.assertEqual(adaptador.sensor_exec.chamadas, [("--version",)])
        # O caminho absoluto do executavel encabeca o argv.
        self.assertTrue(espec_de("codex").executavel.endswith("codex.exe"))

    def test_argv_cai_no_nome_do_cli_sem_caminho(self):
        espec = apoio.espec_com("codex", executavel="")
        sensor = SensorFalso({("--version",): (0, "1.0.0", "")})
        AdaptadorPreflight(espec, sensor_exec=sensor, env={}).detectar_versao()
        self.assertEqual(sensor.chamadas, [("--version",)])


class ConsultaDeLogin(unittest.TestCase):

    def test_login_verde_dos_cinco_provedores(self):
        # grok: "SuperGrok" sem rotulo de plano na saida — com a regra
        # fail-closed da P1-A.3, plano NAO e reconhecido (None).
        esperado = {"codex": "chatgpt pro 5x", "claude": "max",
                    "kimi": "allegretto", "google": None,
                    "grok": None}
        for provider_id, plano in esperado.items():
            with self.subTest(provedor=provider_id):
                login = _adaptador(provider_id).consultar_login()
                self.assertTrue(login["logado"])
                self.assertEqual(login["plano"], plano)
                self.assertEqual(login["origem_credencial"],
                                 espec_de(provider_id).auth_esperada)
                esperado_quota = ("disponivel" if provider_id == "google"
                                   else "desconhecida")
                self.assertEqual(login["quota"], esperado_quota)

    def test_google_quota_estruturada_exige_zero_turnos_e_zero_tokens(self):
        v, login_verde, _ = apoio.VERDES["google"]
        dados = json.loads(login_verde)
        for campo, valor in (("num_turns", 1), ("status", "ERROR")):
            with self.subTest(campo=campo):
                ruim = dict(dados)
                ruim[campo] = valor
                login = _adaptador(
                    "google", login=json.dumps(ruim)).consultar_login()
                self.assertFalse(login["logado"])
        ruim = dict(dados)
        ruim["usage"] = dict(dados["usage"], total_tokens=1)
        self.assertFalse(_adaptador(
            "google", login=json.dumps(ruim)).consultar_login()["logado"])

    def test_google_zero_da_assinatura_e_esgotamento(self):
        _, login_verde, _ = apoio.VERDES["google"]
        dados = json.loads(login_verde)
        buckets = dados["command"]["data"]["groups"][0]["buckets"]
        for bucket in buckets:
            bucket["remaining_fraction"] = 0
        login = _adaptador(
            "google", login=json.dumps(dados)).consultar_login()
        self.assertTrue(login["logado"])
        self.assertEqual(login["quota"], "esgotada")

    def test_grok_reporta_cached_token_e_nunca_chave(self):
        login = _adaptador("grok").consultar_login()
        self.assertEqual(login["origem_credencial"], "cached-token")

    def test_nao_logado_zera_a_origem_e_a_quota(self):
        for provider_id in ESPECIFICACOES:
            with self.subTest(provedor=provider_id):
                login = _adaptador(provider_id,
                                   login="Not logged in").consultar_login()
                self.assertFalse(login["logado"])
                self.assertEqual(login["origem_credencial"], "ausente")
                self.assertEqual(login["quota"], "desconhecida")

    def test_rc_diferente_de_zero_no_status_nao_e_login(self):
        espec = espec_de("codex")
        sensor = SensorFalso({espec.comandos["versao"]: (0, "0.145.0", ""),
                              espec.comandos["login"]: (1, "Logged in", "")})
        adaptador = AdaptadorPreflight(espec, sensor_exec=sensor, env={})
        self.assertFalse(adaptador.consultar_login()["logado"])

    def test_claude_json_invalido_cai_no_parser_de_texto(self):
        login = _adaptador(
            "claude",
            login="Logged in via OAuth (plan: claude max)").consultar_login()
        self.assertTrue(login["logado"])
        self.assertEqual(login["plano"], "claude max")

    def test_claude_json_sem_login_explicito_usa_o_plano(self):
        login = _adaptador(
            "claude", login='{"subscriptionType": "max"}').consultar_login()
        self.assertTrue(login["logado"])
        self.assertEqual(login["plano"], "max")

    def test_claude_json_com_login_falso_nao_e_login(self):
        login = _adaptador(
            "claude",
            login='{"loggedIn": false, "subscriptionType": "max"}'
        ).consultar_login()
        self.assertFalse(login["logado"])

    def test_plano_mais_especifico_vence(self):
        # "chatgpt pro 5x" e "chatgpt pro" ambos casam: o maior ganha.
        login = _adaptador(
            "codex",
            login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)"
        ).consultar_login()
        self.assertEqual(login["plano"], "chatgpt pro 5x")


class ClassificacaoDeQuota(unittest.TestCase):

    def test_esgotada_vence_o_login_ativo(self):
        self.assertEqual(_quota_de("usage limit reached", True), "esgotada")

    def test_logado_sem_sinal_positivo_e_desconhecida(self):
        # Regressao P1-A.1: login valido SEM evidencia de quota nunca
        # retorna "disponivel" — ausencia de evidencia = unknown.
        self.assertEqual(_quota_de("all good", True), "desconhecida")

    def test_disponivel_exige_sinal_positivo_observavel(self):
        self.assertEqual(_quota_de("5 requests remaining", True),
                         "disponivel")

    def test_sem_login_a_quota_e_desconhecida_nunca_presumida(self):
        self.assertEqual(_quota_de("all good", False), "desconhecida")
        self.assertEqual(
            _quota_de("5 requests remaining", False), "desconhecida")

    def test_marcador_em_caixa_alta_tambem_conta(self):
        self.assertEqual(_quota_de("QUOTA EXHAUSTED", True), "esgotada")


class DescobertaDeModelos(unittest.TestCase):

    def test_modelos_dos_cinco_provedores_contem_o_esperado(self):
        for provider_id, espec in ESPECIFICACOES.items():
            with self.subTest(provedor=provider_id):
                if espec.comandos["modelos"] is None:
                    # Emenda P1-A.3, item 4 (claude): sem fonte oficial
                    # nao interativa, a descoberta esta desativada.
                    continue
                modelos = _adaptador(provider_id).descobrir_modelos()
                self.assertTrue(
                    any(esperado in m for m in modelos
                        for esperado in espec.modelos_esperados), modelos)

    def test_extracao_ordena_e_deduplica_em_minusculas(self):
        self.assertEqual(extrair_modelos("GPT-5\ngpt-5\ngpt-5-codex"),
                         ["gpt-5", "gpt-5-codex"])

    def test_palavras_sem_separador_nao_sao_modelo(self):
        self.assertEqual(extrair_modelos("Models available: none yet"), [])

    def test_texto_vazio_devolve_lista_vazia(self):
        self.assertEqual(extrair_modelos(""), [])

    def test_sensor_de_modelos_e_independente_do_de_execucao(self):
        sensor_exec, sensor_modelos = sensores_verdes("codex")
        adaptador = AdaptadorPreflight(espec_de("codex"),
                                       sensor_exec=sensor_exec,
                                       sensor_modelos=sensor_modelos, env={})
        adaptador.descobrir_modelos()
        self.assertEqual(sensor_exec.n, 0)
        # Emenda P1-A.3, item 2: a descoberta do codex e `doctor`.
        self.assertEqual(sensor_modelos.chamadas, [("doctor",)])

    def test_sensor_de_modelos_default_e_o_de_execucao(self):
        sensor = SensorFalso({("doctor",): (
            0, "model gpt-5\nstored auth mode chatgpt", "")})
        adaptador = AdaptadorPreflight(espec_de("codex"), sensor_exec=sensor,
                                       env={})
        self.assertEqual(adaptador.descobrir_modelos(), ["gpt-5"])


class ReconhecimentoDePlano(unittest.TestCase):

    def test_substring_nos_dois_sentidos(self):
        self.assertTrue(plano_reconhecido("ChatGPT Pro 5x", ("chatgpt pro",)))
        self.assertTrue(plano_reconhecido("Max", ("claude max 5x", "max")))

    def test_plano_vazio_ou_none_nunca_e_reconhecido(self):
        for valor in (None, "", "   "):
            with self.subTest(valor=valor):
                self.assertFalse(plano_reconhecido(valor, ("max",)))

    def test_plano_de_outro_tier_nao_e_reconhecido(self):
        self.assertFalse(plano_reconhecido("team", ("claude max 5x", "max")))
        self.assertFalse(plano_reconhecido("free", ("chatgpt pro",)))


class SensorRealSemProcesso(unittest.TestCase):
    """`Popen` substituido: nenhum CLI real e executado aqui."""

    def _chamar(self, env, **retorno):
        base = {"returncode": 0, "stdout": "ok", "stderr": ""}
        base.update(retorno)
        proc = mock.Mock(returncode=base["returncode"])
        proc.communicate.return_value = (base["stdout"], base["stderr"])
        with mock.patch("preflight.adaptadores.subprocess.Popen",
                        return_value=proc) as popen:
            resultado = sensor_subprocess(["cli", "--version"], env=env)
            return resultado, popen.call_args, proc

    def test_credencial_nunca_entra_no_processo_filho(self):
        env = {"OPENAI_API_KEY": SENTINELA, "XAI_API_KEY": SENTINELA,
               "VSCODE_GIT_IPC_AUTH_TOKEN": SENTINELA,
               "ORCA_AGENT_HOOK_TOKEN": SENTINELA,
               "ORCA_AGENT_HOOK_PORT": "9999", "PATH": "C:\\Windows"}
        _, chamada, _ = self._chamar(env)
        entregue = chamada.kwargs["env"]
        self.assertEqual(entregue, {"PATH": "C:\\Windows"})
        self.assertNotIn(SENTINELA, repr(entregue))
        self.assertFalse(any(k.startswith("ORCA_") for k in entregue))

    def test_saida_e_capturada_e_nunca_ecoada(self):
        _, chamada, proc = self._chamar({"PATH": "p"})
        self.assertEqual(chamada.kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(chamada.kwargs["stderr"], subprocess.PIPE)
        self.assertNotIn("text", chamada.kwargs)
        proc.communicate.assert_called_once_with(timeout=TIMEOUT_PADRAO)

    def test_retorno_do_processo_e_repassado(self):
        (rc, out, err), _, _ = self._chamar(
            {}, returncode=3, stdout="s", stderr="e")
        self.assertEqual((rc, out, err), (3, "s", "e"))

    def test_saida_none_vira_texto_vazio(self):
        (rc, out, err), _, _ = self._chamar({}, stdout=None, stderr=None)
        self.assertEqual((out, err), ("", ""))

    def test_timeout_devolve_codigo_124_sem_excecao(self):
        proc = mock.Mock(returncode=None)
        proc.communicate.side_effect = [
            subprocess.TimeoutExpired(cmd="cli", timeout=1), ("", "")]
        with mock.patch("preflight.adaptadores.subprocess.Popen",
                        return_value=proc), \
                mock.patch("preflight.adaptadores.encerrar_arvore") as matar:
            rc, out, err = sensor_subprocess(["cli", "--version"], env={})
        matar.assert_called_once_with(proc)
        self.assertEqual(rc, 124)
        self.assertEqual(out, "")
        self.assertIn("timeout", err)

    def test_sensor_real_decodifica_utf8_sem_depender_da_locale(self):
        codigo = ("import sys;sys.stdout.buffer.write("
                  "'função'.encode('utf-8'))")
        rc, out, err = sensor_subprocess(
            [sys.executable, "-c", codigo], env={}, timeout=10)
        self.assertEqual((rc, out, err), (0, "função", ""))


class ComandosSaoSomenteDiagnostico(unittest.TestCase):
    """Nenhum comando de diagnostico pode ser uma invocacao produtiva."""

    PERMITIDOS = frozenset({
        "--version", "--list-models", "login", "status", "auth", "models",
        "provider", "list", "doctor", "changelog", "/quota",
        "--output-format", "json", "--mode", "plan", "-p",
    })

    def test_apenas_verbos_de_diagnostico_declarados(self):
        for provider_id, espec in ESPECIFICACOES.items():
            for sonda, comando in espec.comandos.items():
                with self.subTest(provedor=provider_id, sonda=sonda):
                    if comando is None:
                        # Descoberta desativada (emenda P1-A.3, item 4):
                        # somente a sonda "modelos" pode ser None.
                        self.assertEqual(sonda, "modelos")
                        continue
                    self.assertTrue(set(comando) <= self.PERMITIDOS,
                                    f"{provider_id}/{sonda}: {comando}")

    def test_tres_sondas_por_provedor(self):
        for provider_id, espec in ESPECIFICACOES.items():
            with self.subTest(provedor=provider_id):
                self.assertEqual(set(espec.comandos), {"versao", "login",
                                                       "modelos"})

    def test_headless_nunca_usa_prompt_produtivo_como_sonda(self):
        for provider_id, espec in ESPECIFICACOES.items():
            with self.subTest(provedor=provider_id):
                self.assertTrue(espec.headless)
                for comando in espec.comandos.values():
                    if comando is None:  # descoberta desativada (P1-A.3)
                        continue
                    if provider_id == "google" and comando == \
                            espec.comandos["login"]:
                        # `/quota` e resposta local read-only do proprio
                        # CLI; o parser exige num_turns=0 e uso=0.
                        self.assertIn("/quota", comando)
                        continue
                    self.assertNotIn(espec.headless[0], comando)

    def test_nenhuma_sonda_aprova_automaticamente(self):
        proibidos = ("--always-approve", "--yes", "--dangerously-skip-"
                     "permissions", "--auto-approve", "-y", "exec", "run",
                     "--print", "--api-key", "--batch-api")
        for provider_id, espec in ESPECIFICACOES.items():
            for comando in espec.comandos.values():
                if comando is None:  # descoberta desativada (P1-A.3)
                    continue
                with self.subTest(provedor=provider_id, comando=comando):
                    for proibido in proibidos:
                        self.assertNotIn(proibido, comando)


if __name__ == "__main__":
    unittest.main()
