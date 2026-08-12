"""Pipeline de preflight e classificacao da frota (SSC+ P1-A, experimental).

Prova a ORDEM (economia -> auth -> descoberta), a classificacao
ELIGIBLE | SUPERVISED | BLOCKED, o teto SUPERVISED de Google e Grok e as
invariantes da especificacao estatica da frota. Nenhum CLI real invocado.
"""

import json
import os
import unittest
from datetime import datetime, timedelta, timezone

import apoio
from apoio import SENTINELA, SensorFalso, sensores_dict, sensores_verdes
from preflight import (ESPECIFICACOES, RESULTADOS, RelatorioPreflight,
                       espec_de, executar_preflight, frota_real)
from preflight.pipeline import _normalizar_sensores
from preflight.sombra import DeclaracaoTier

AGORA = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)


def _kwargs_verdes(provider_id):
    kwargs = {"env": {}, "agora": AGORA}
    if provider_id == "claude":
        kwargs["config_persistida"] = {"model": "claude-fable-5[1m]"}
    if provider_id == "google":
        kwargs["tiers_declarados"] = {"google": DeclaracaoTier(
            provider_id="google", tier="Google AI Pro",
            declarado_por="proprietario",
            declarado_em_utc=(AGORA - timedelta(hours=1)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"))}
    return kwargs


class FrotaVerde(unittest.TestCase):
    """Com tudo verde, cada provedor chega ao seu teto — nunca acima."""

    def test_classificacao_dos_cinco_provedores(self):
        esperado = {"codex": "ELIGIBLE", "claude": "ELIGIBLE",
                    "kimi": "ELIGIBLE", "google": "SHADOW_ELIGIBLE",
                    "grok": "SUPERVISED"}
        for provider_id, resultado in esperado.items():
            with self.subTest(provedor=provider_id):
                sens, _, _ = sensores_dict(provider_id)
                relatorio = executar_preflight(espec_de(provider_id), sens,
                                               **_kwargs_verdes(provider_id))
                self.assertEqual(relatorio.resultado, resultado)
                self.assertEqual(relatorio.erros, [])
                self.assertEqual(
                    relatorio.quota,
                    "disponivel" if provider_id == "google"
                    else "desconhecida")
                if not espec_de(provider_id).sondas_automaticas:
                    # ZERO sondas (google/grok): campos de evidencia NAO
                    # observados — plano/origem declarados nao podem
                    # parecer prova de login.
                    self.assertIsNone(relatorio.versao)
                    self.assertIsNone(relatorio.plano)
                    self.assertEqual(relatorio.origem_credencial,
                                     "nao-sondada")
                    self.assertEqual(relatorio.modelos, [])
                    continue
                self.assertEqual(relatorio.origem_credencial,
                                 espec_de(provider_id).auth_esperada)
                self.assertTrue(relatorio.modelos)
                self.assertTrue(relatorio.versao)

    def test_google_automatico_e_grok_permanece_supervisionado(self):
        sens, _, _ = sensores_dict("google")
        google = executar_preflight(espec_de("google"), sens,
                                    **_kwargs_verdes("google"))
        self.assertEqual(google.resultado, "SHADOW_ELIGIBLE")
        self.assertEqual(espec_de("google").automacao, "allow-supervised")
        sens, _, _ = sensores_dict("grok")
        grok = executar_preflight(espec_de("grok"), sens, env={})
        self.assertEqual(grok.resultado, "SUPERVISED")
        self.assertEqual(espec_de("grok").automacao, "supervised-only")

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
                                       env={"PATH": "p"},
                                       config_persistida={
                                           "model": "claude-fable-5[1m]"})
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
        # Emenda P1-A.3, item 1: SHADOW_ELIGIBLE entra no enum.
        self.assertEqual(RESULTADOS, ("ELIGIBLE", "SHADOW_ELIGIBLE",
                                      "SUPERVISED", "BLOCKED"))

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
                                     "(plan: ChatGPT Pro 5x)", ""),
            ("doctor",): (0, "model gpt-5\nstored auth mode chatgpt", "")})
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

    def test_google_declara_canal_antigravity_e_teto_eligible(self):
        espec = espec_de("google")
        self.assertEqual(espec.teto_resultado, "ELIGIBLE")
        self.assertIn("Antigravity", espec.canal_oficial)

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
            relatorios.append(executar_preflight(
                espec, sens, **_kwargs_verdes(espec.provider_id)))
        self.assertEqual(len(relatorios), 5)
        self.assertEqual(sum(1 for r in relatorios
                             if r.resultado == "ELIGIBLE"), 3)
        self.assertEqual(sum(1 for r in relatorios
                             if r.resultado == "SHADOW_ELIGIBLE"), 1)
        self.assertEqual(sum(1 for r in relatorios
                             if r.resultado == "SUPERVISED"), 1)
        self.assertEqual([r for r in relatorios if r.erros], [])


if __name__ == "__main__":
    unittest.main()
