"""Pipeline de preflight e classificacao da frota (SSC+ P1-A, experimental).

Prova a ORDEM (economia -> auth -> descoberta), a classificacao
ELIGIBLE | SUPERVISED | BLOCKED, o teto SUPERVISED de Google e Grok e as
invariantes da especificacao estatica da frota. Nenhum CLI real invocado.
"""

import json
import os
import unittest

import apoio
from apoio import SENTINELA, SensorFalso, sensores_dict, sensores_verdes
from preflight import (ESPECIFICACOES, RESULTADOS, RelatorioPreflight,
                       espec_de, executar_preflight, frota_real)
from preflight.pipeline import _normalizar_sensores


class FrotaVerde(unittest.TestCase):
    """Com tudo verde, cada provedor chega ao seu teto — nunca acima."""

    def test_classificacao_dos_cinco_provedores(self):
        esperado = {"codex": "ELIGIBLE", "claude": "ELIGIBLE",
                    "kimi": "ELIGIBLE", "google": "SUPERVISED",
                    "grok": "SUPERVISED"}
        for provider_id, resultado in esperado.items():
            with self.subTest(provedor=provider_id):
                sens, _, _ = sensores_dict(provider_id)
                relatorio = executar_preflight(espec_de(provider_id), sens,
                                               env={})
                self.assertEqual(relatorio.resultado, resultado)
                self.assertEqual(relatorio.erros, [])
                # Sem sinal positivo de quota nas saidas verdes: unknown.
                self.assertEqual(relatorio.quota, "desconhecida")
                self.assertEqual(relatorio.origem_credencial,
                                 espec_de(provider_id).auth_esperada)
                self.assertTrue(relatorio.modelos)
                self.assertTrue(relatorio.versao)

    def test_google_e_grok_nunca_sobem_para_eligible(self):
        for provider_id in ("google", "grok"):
            with self.subTest(provedor=provider_id):
                sens, _, _ = sensores_dict(provider_id)
                relatorio = executar_preflight(espec_de(provider_id), sens,
                                               env={})
                self.assertNotEqual(relatorio.resultado, "ELIGIBLE")
                self.assertEqual(espec_de(provider_id).automacao,
                                 "supervised-only")

    def test_tres_sondas_exatas_no_caminho_verde(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        executar_preflight(espec_de("codex"), sens, env={})
        # versao + login no sensor de execucao; 1 descoberta de modelos.
        self.assertEqual(sensor_exec.chamadas,
                         [("--version",), ("login", "status")])
        self.assertEqual(sensor_modelos.n, 1)

    def test_caminho_verde_nao_registra_erro_nem_segredo(self):
        sens, _, _ = sensores_dict("claude")
        relatorio = executar_preflight(espec_de("claude"), sens,
                                       env={"PATH": "p"})
        self.assertNotIn(SENTINELA, json.dumps(relatorio.to_dict()))
        self.assertEqual(relatorio.to_dict()["erros"], [])


class OrdemDoBloqueio(unittest.TestCase):
    """Economia primeiro: violacao economica nem chega a detectar o CLI."""

    def test_violacao_economica_bloqueia_antes_da_deteccao_do_cli(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_de("codex"), sens, env={"NVIDIA_API_KEY": SENTINELA})
        self.assertEqual(relatorio.resultado, "BLOCKED")
        self.assertEqual(sensor_exec.n, 0)
        self.assertEqual(sensor_modelos.n, 0)
        self.assertIsNone(relatorio.versao)

    def test_violacao_de_auth_bloqueia_antes_da_descoberta(self):
        sens, sensor_exec, sensor_modelos = sensores_dict(
            "codex", login="Not logged in")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(relatorio.resultado, "BLOCKED")
        self.assertEqual(sensor_exec.n, 2)      # versao + login
        self.assertEqual(sensor_modelos.n, 0)   # descoberta nunca ocorre
        self.assertIsNotNone(relatorio.versao)  # diagnostico preservado

    def test_erros_acumulados_saem_todos_no_relatorio(self):
        sens, _, _ = sensores_dict(
            "codex", login="Logged in using ChatGPT (plan: Free)\n"
                           "usage limit reached")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(apoio.codigos(relatorio),
                         ["P1A-PLANO-DESCONHECIDO", "P1A-QUOTA-ESGOTADA"])


class RoundTripDoRelatorio(unittest.TestCase):

    def test_relatorio_verde_sobrevive_ao_round_trip(self):
        sens, _, _ = sensores_dict("kimi")
        relatorio = executar_preflight(espec_de("kimi"), sens, env={})
        volta = RelatorioPreflight.from_dict(relatorio.to_dict())
        self.assertEqual(volta, relatorio)

    def test_relatorio_bloqueado_preserva_os_erros_tipados(self):
        sens, _, _ = sensores_dict("codex", login="Not logged in")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        volta = RelatorioPreflight.from_dict(relatorio.to_dict())
        self.assertEqual(volta, relatorio)
        self.assertEqual([type(e) for e in volta.erros],
                         [type(e) for e in relatorio.erros])

    def test_json_do_relatorio_e_serializavel(self):
        sens, _, _ = sensores_dict("grok")
        relatorio = executar_preflight(espec_de("grok"), sens, env={})
        texto = json.dumps(relatorio.to_dict(), sort_keys=True)
        self.assertEqual(json.loads(texto), relatorio.to_dict())

    def test_resultado_fora_do_enum_e_recusado(self):
        with self.assertRaises(ValueError):
            RelatorioPreflight(provider_id="x", resultado="OK")

    def test_enum_de_resultados_e_exatamente_o_da_missao(self):
        self.assertEqual(RESULTADOS, ("ELIGIBLE", "SUPERVISED", "BLOCKED"))

    def test_relatorios_diferentes_nao_sao_iguais(self):
        sens_a, _, _ = sensores_dict("codex")
        sens_b, _, _ = sensores_dict("claude")
        a = executar_preflight(espec_de("codex"), sens_a, env={})
        b = executar_preflight(espec_de("claude"), sens_b, env={})
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, "nao e relatorio")


class NormalizacaoDeSensores(unittest.TestCase):

    def test_sensor_unico_atende_todas_as_sondas(self):
        sensor = SensorFalso({
            ("--version",): (0, "0.145.0", ""),
            ("login", "status"): (0, "Logged in using ChatGPT "
                                     "(ChatGPT Pro 5x)", ""),
            ("models",): (0, "gpt-5", "")})
        relatorio = executar_preflight(espec_de("codex"), sensor, env={})
        self.assertEqual(relatorio.resultado, "ELIGIBLE")
        self.assertEqual(sensor.n, 3)

    def test_dict_sem_modelos_reaproveita_o_de_execucao(self):
        sensor = SensorFalso()
        normalizado = _normalizar_sensores({"exec": sensor})
        self.assertIs(normalizado["modelos"], sensor)

    def test_dict_sem_exec_e_recusado(self):
        with self.assertRaises(ValueError):
            _normalizar_sensores({"modelos": SensorFalso()})

    def test_exec_nulo_e_recusado(self):
        with self.assertRaises(ValueError):
            _normalizar_sensores({"exec": None, "modelos": SensorFalso()})


class AmbientePadrao(unittest.TestCase):

    def test_ambiente_do_processo_nunca_e_mutado(self):
        antes = dict(os.environ)
        sens, _, _ = sensores_dict("codex")
        relatorio = executar_preflight(espec_de("codex"), sens)
        self.assertEqual(dict(os.environ), antes)
        self.assertIn(relatorio.resultado, RESULTADOS)

    def test_env_explicito_nao_e_mutado(self):
        env = {"PATH": "p", "NVIDIA_API_KEY": SENTINELA}
        copia = dict(env)
        sens, _, _ = sensores_dict("codex")
        executar_preflight(espec_de("codex"), sens, env=env)
        self.assertEqual(env, copia)

    def test_config_persistida_nao_e_mutada(self):
        config = {"auth": {"api_key": SENTINELA}}
        copia = json.loads(json.dumps(config))
        sens, _, _ = sensores_dict("codex")
        executar_preflight(espec_de("codex"), sens, env={},
                           config_persistida=config)
        self.assertEqual(config, copia)


class EspecificacaoDaFrota(unittest.TestCase):

    def test_cinco_provedores_na_ordem_da_missao(self):
        self.assertEqual([e.provider_id for e in frota_real()],
                         ["codex", "claude", "kimi", "google", "grok"])

    def test_espec_de_devolve_a_mesma_instancia_do_registro(self):
        for provider_id in ESPECIFICACOES:
            with self.subTest(provedor=provider_id):
                self.assertIs(espec_de(provider_id),
                              ESPECIFICACOES[provider_id])

    def test_provedor_desconhecido_levanta_keyerror(self):
        with self.assertRaises(KeyError):
            espec_de("provedor-inexistente")

    def test_toda_espec_e_subscription_com_custo_variavel_zero(self):
        for provider_id, espec in ESPECIFICACOES.items():
            with self.subTest(provedor=provider_id):
                self.assertEqual(espec.billing_mode, "subscription")
                self.assertEqual(espec.variable_cost, 0.0)
                self.assertIn(espec.teto_resultado,
                              ("ELIGIBLE", "SUPERVISED"))
                self.assertIn(espec.auth_esperada,
                              ("subscription-oauth", "cached-token"))

    def test_espec_e_imutavel(self):
        with self.assertRaises(Exception):
            espec_de("codex").teto_resultado = "ELIGIBLE"

    def test_grok_declara_cached_token_e_a_chave_proibida(self):
        espec = espec_de("grok")
        self.assertEqual(espec.auth_esperada, "cached-token")
        self.assertIn("XAI_API_KEY", espec.chaves_payg_relacionadas)
        self.assertEqual(espec.teto_resultado, "SUPERVISED")

    def test_google_declara_oauth_personal_e_teto_supervised(self):
        espec = espec_de("google")
        self.assertEqual(espec.teto_resultado, "SUPERVISED")
        self.assertIn("oauth-personal", espec.canal_oficial)

    def test_toda_espec_declara_chaves_payg_do_proprio_provedor(self):
        for provider_id, espec in ESPECIFICACOES.items():
            with self.subTest(provedor=provider_id):
                self.assertTrue(espec.chaves_payg_relacionadas)
                self.assertTrue(espec.modelos_esperados)
                self.assertTrue(espec.planos_aceitos)
                self.assertTrue(espec.canal_oficial)

    def test_frota_completa_varrida_de_uma_vez(self):
        relatorios = []
        for espec in frota_real():
            sens, _, _ = sensores_dict(espec.provider_id)
            relatorios.append(executar_preflight(espec, sens, env={}))
        self.assertEqual(len(relatorios), 5)
        self.assertEqual(sum(1 for r in relatorios
                             if r.resultado == "ELIGIBLE"), 3)
        self.assertEqual(sum(1 for r in relatorios
                             if r.resultado == "SUPERVISED"), 2)
        self.assertEqual([r for r in relatorios if r.erros], [])


if __name__ == "__main__":
    unittest.main()
