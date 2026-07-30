"""Preflight da frota real (SSC+ P1-A): as 9 falhas obrigatorias + caminho feliz.

1. Variavel PAYG em caixa mista no Windows e detectada e bloqueia.
2. Chave persistida em configuracao (auth.json) bloqueia.
3. OAuth ausente -> OAuthAusente, BLOCKED.
4. Plano nao reconhecido -> PlanoNaoReconhecido.
5. Quota esgotada -> QuotaEsgotada e nenhuma invocacao.
6. Billing desconhecido -> BillingDesconhecido.
7. CLI indisponivel -> CliIndisponivel.
8. Modelo removido -> ModeloRemovido.
9. Conflito ambiente x login -> ConflitoAmbienteLogin.

NENHUM subprocesso real roda: toda execucao externa usa sensores falsos.
Em toda falha, um sensor de modelos que levanta AssertionError prova que
nada foi invocado apos o bloqueio.
"""

import dataclasses
import json
import os
import unittest

import apoio  # noqa: F401  (sys.path)

from preflight import (BillingDesconhecido, ChavePaygDetectada,
                       CliIndisponivel, ConfigPaygPersistida,
                       ConflitoAmbienteLogin, ModeloRemovido, OAuthAusente,
                       PlanoNaoReconhecido, QuotaEsgotada,
                       RelatorioPreflight, ambiente_sanitizado,
                       auditar_ambiente, auditar_config, espec_de,
                       executar_preflight)

# Montado por concatenacao de proposito: assim o valor existe em memoria
# para os testes, mas NENHUMA linha do arquivo casa com o padrao de chave
# real (`sk-...`) da varredura de segredos em test_isolamento.py.
SEGREDO = "sk-" + "segredo-que-jamais-deve-vazar-123456"

_LOGIN_VERDE = {
    "codex": (0, "Logged in using ChatGPT\nPlano: ChatGPT Pro 5x", ""),
    "claude": (0, json.dumps({"loggedIn": True, "authMethod": "oauth",
                              "subscriptionType": "max"}), ""),
    "kimi": (0, "managed:kimi-code  type=kimi  source=oauth  "
                "plano=Allegretto", ""),
    "google": (0, "logged in: oauth-personal\nPlano: Google AI Pro", ""),
    "grok": (0, "logged in (cached token)\nPlano: SuperGrok", ""),
}
_MODELOS_VERDE = {
    "codex": (0, "gpt-5-codex\ngpt-5", ""),
    "claude": (0, "claude-opus-4-5\nclaude-sonnet-4-5", ""),
    "kimi": (0, "kimi-k2\nkimi-k2-thinking", ""),
    "google": (0, "gemini-2.5-pro\ngemini-2.5-flash", ""),
    "grok": (0, "grok-4\ngrok-code-fast-1", ""),
}
_VERSAO_VERDE = {
    "codex": (0, "codex-cli 0.145.0", ""),
    "claude": (0, "2.1.220 (Claude Code)", ""),
    "kimi": (0, "kimi-code 0.30.0", ""),
    "google": (0, "gemini 0.52.0", ""),
    "grok": (0, "grok 1.1.7", ""),
}


def sensor_explosivo(argv, env):
    """Prova de bloqueio: se qualquer sensor for chamado, o teste falha."""
    raise AssertionError(f"sensor chamado apos bloqueio: {argv}")


class SensorFalso:
    """Sensor de execucao deterministico (versao + login)."""

    def __init__(self, versao, login):
        self.resposta_versao = versao
        self.resposta_login = login
        self.chamadas = []

    def __call__(self, argv, env):
        self.chamadas.append(list(argv))
        resposta = self.resposta_versao if "--version" in argv \
            else self.resposta_login
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


class SensorModelos:
    """Sensor de descoberta de modelos deterministico."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.chamadas = []

    def __call__(self, argv, env):
        self.chamadas.append(list(argv))
        return self.resposta


def _sensores_verdes(provider_id, modelos=None):
    return {"exec": SensorFalso(_VERSAO_VERDE[provider_id],
                                _LOGIN_VERDE[provider_id]),
            "modelos": SensorModelos(modelos or _MODELOS_VERDE[provider_id])}


def _tipos(rel):
    return {type(e) for e in rel.erros}


class TestFalhasObrigatorias(unittest.TestCase):

    # -- 1. Variavel PAYG em caixa mista no Windows -----------------------------

    def test_falha_1_variavel_payg_caixa_mista_bloqueia(self):
        # Chave do proprio provedor, login INATIVO: violacao economica pura.
        for provider_id, nome in (("codex", "OpenAI_Api_Key"),
                                  ("grok", "xAi_ApI_KeY")):
            with self.subTest(provider=provider_id, variavel=nome):
                exec_falso = SensorFalso(_VERSAO_VERDE[provider_id],
                                         (1, "Not logged in", ""))
                rel = executar_preflight(
                    espec_de(provider_id),
                    {"exec": exec_falso, "modelos": sensor_explosivo},
                    env={nome: SEGREDO}, config_persistida={})
                self.assertEqual(rel.resultado, "BLOCKED")
                chave = next(e for e in rel.erros
                             if isinstance(e, ChavePaygDetectada))
                self.assertEqual(chave.codigo, "P1A-PAYG-ENV")
                self.assertEqual(chave.alvo, nome)
                self.assertNotIn(SEGREDO, chave.detalhe)
        # Chave de OUTRO provedor: bloqueio imediato, zero sensores.
        rel = executar_preflight(
            espec_de("codex"),
            {"exec": sensor_explosivo, "modelos": sensor_explosivo},
            env={"xAi_ApI_KeY": SEGREDO}, config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn(ChavePaygDetectada, _tipos(rel))

    # -- 2. Chave persistida em configuracao bloqueia -----------------------------

    def test_falha_2_chave_persistida_em_config_bloqueia(self):
        config = {"auth_mode": "chatgpt", "OPENAI_API_KEY": SEGREDO}
        rel = executar_preflight(
            espec_de("codex"),
            {"exec": sensor_explosivo, "modelos": sensor_explosivo},
            env={}, config_persistida=config)
        self.assertEqual(rel.resultado, "BLOCKED")
        cfg = next(e for e in rel.erros
                   if isinstance(e, ConfigPaygPersistida))
        self.assertEqual(cfg.codigo, "P1A-PAYG-CONFIG")
        self.assertNotIn(SEGREDO, cfg.detalhe)
        # Endpoint PAYG e auto top-up tambem bloqueiam.
        for config_ruim in ({"base_url": "https://api.openai.com/v1"},
                            {"base_url": "https://api.x.ai/v1"},
                            {"auto_topup": True},
                            {"extraUsageEnabled": "true"}):
            with self.subTest(config=config_ruim):
                rel = executar_preflight(
                    espec_de("grok"),
                    {"exec": sensor_explosivo,
                     "modelos": sensor_explosivo},
                    env={}, config_persistida=config_ruim)
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn(ConfigPaygPersistida, _tipos(rel))

    # -- 3. OAuth ausente -----------------------------------------------------------

    def test_falha_3_oauth_ausente_bloqueia(self):
        rel = executar_preflight(
            espec_de("codex"),
            {"exec": SensorFalso(_VERSAO_VERDE["codex"],
                                 (1, "Not logged in", "")),
             "modelos": sensor_explosivo},
            env={}, config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        oauth = next(e for e in rel.erros if isinstance(e, OAuthAusente))
        self.assertEqual(oauth.codigo, "P1A-OAUTH-AUSENTE")
        self.assertNotIn(QuotaEsgotada, _tipos(rel))
        self.assertNotIn(ChavePaygDetectada, _tipos(rel))

    # -- 4. Plano nao reconhecido ------------------------------------------------------

    def test_falha_4_plano_nao_reconhecido_bloqueia(self):
        login_free = (0, json.dumps({"loggedIn": True,
                                     "subscriptionType": "free"}), "")
        rel = executar_preflight(
            espec_de("claude"),
            {"exec": SensorFalso(_VERSAO_VERDE["claude"], login_free),
             "modelos": sensor_explosivo},
            env={}, config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        plano = next(e for e in rel.erros
                     if isinstance(e, PlanoNaoReconhecido))
        self.assertEqual(plano.codigo, "P1A-PLANO-DESCONHECIDO")

    # -- 5. Quota esgotada --------------------------------------------------------------

    def test_falha_5_quota_esgotada_bloqueia_sem_invocacao(self):
        login = (0, "Logged in using ChatGPT Pro 5x\n"
                    "quota exhausted: 0 remaining", "")
        exec_falso = SensorFalso(_VERSAO_VERDE["codex"], login)
        rel = executar_preflight(
            espec_de("codex"),
            {"exec": exec_falso, "modelos": sensor_explosivo},
            env={}, config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        quota = next(e for e in rel.erros if isinstance(e, QuotaEsgotada))
        self.assertEqual(quota.codigo, "P1A-QUOTA-ESGOTADA")
        self.assertEqual(rel.quota, "esgotada")
        # Nenhuma invocacao de modelo: so versao + login passaram.
        self.assertEqual(len(exec_falso.chamadas), 2)

    # -- 6. Billing desconhecido -----------------------------------------------------------

    def test_falha_6_billing_desconhecido_bloqueia(self):
        espec_ruim = dataclasses.replace(espec_de("codex"),
                                         billing_mode="desconhecido")
        rel = executar_preflight(
            espec_ruim,
            {"exec": sensor_explosivo, "modelos": sensor_explosivo},
            env={}, config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        billing = next(e for e in rel.erros
                       if isinstance(e, BillingDesconhecido))
        self.assertEqual(billing.codigo, "P1A-BILLING-DESCONHECIDO")

    # -- 7. CLI indisponivel ------------------------------------------------------------------

    def test_falha_7_cli_indisponivel_bloqueia(self):
        casos = {
            "FileNotFoundError": SensorFalso(
                FileNotFoundError("codex.exe"), (0, "", "")),
            "returncode-127": SensorFalso((127, "", "not found"),
                                          (0, "", "")),
        }
        for nome, exec_falso in casos.items():
            with self.subTest(causa=nome):
                rel = executar_preflight(
                    espec_de("codex"),
                    {"exec": exec_falso, "modelos": sensor_explosivo},
                    env={}, config_persistida={})
                self.assertEqual(rel.resultado, "BLOCKED")
                cli = next(e for e in rel.erros
                           if isinstance(e, CliIndisponivel))
                self.assertEqual(cli.codigo, "P1A-CLI-INDISPONIVEL")

    # -- 8. Modelo removido -----------------------------------------------------------------------

    def test_falha_8_modelo_removido_bloqueia(self):
        for nome, resposta in (("sem-esperado",
                                (0, "modelo-desconhecido-9\noutro-1", "")),
                               ("vazia", (0, "", ""))):
            with self.subTest(descoberta=nome):
                rel = executar_preflight(
                    espec_de("claude"),
                    {"exec": SensorFalso(_VERSAO_VERDE["claude"],
                                         _LOGIN_VERDE["claude"]),
                     "modelos": SensorModelos(resposta)},
                    env={}, config_persistida={})
                self.assertEqual(rel.resultado, "BLOCKED")
                modelo = next(e for e in rel.erros
                              if isinstance(e, ModeloRemovido))
                self.assertEqual(modelo.codigo, "P1A-MODELO-REMOVIDO")

    # -- 9. Conflito ambiente x login ---------------------------------------------------------------

    def test_falha_9_conflito_ambiente_login_bloqueia(self):
        rel = executar_preflight(
            espec_de("claude"),
            {"exec": SensorFalso(_VERSAO_VERDE["claude"],
                                 _LOGIN_VERDE["claude"]),
             "modelos": sensor_explosivo},
            env={"ANTHROPIC_API_KEY": SEGREDO}, config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        conflito = next(e for e in rel.erros
                        if isinstance(e, ConflitoAmbienteLogin))
        self.assertEqual(conflito.codigo, "P1A-CONFLITO-ENV-LOGIN")
        self.assertEqual(conflito.alvo, "ANTHROPIC_API_KEY")
        # A chave nunca vence o OAuth: conflito SUBSTITUI a violacao simples.
        self.assertNotIn(ChavePaygDetectada, _tipos(rel))
        self.assertNotIn(SEGREDO, conflito.detalhe)


class TestCaminhoFeliz(unittest.TestCase):

    def test_codex_claude_kimi_eligible_com_sensores_verdes(self):
        for provider_id in ("codex", "claude", "kimi"):
            with self.subTest(provider=provider_id):
                sensores = _sensores_verdes(provider_id)
                rel = executar_preflight(espec_de(provider_id), sensores,
                                         env={}, config_persistida={})
                self.assertEqual(rel.resultado, "ELIGIBLE")
                self.assertEqual(rel.erros, [])
                # Fail-closed (P1-A.1): sem sinal positivo, quota e unknown.
                self.assertEqual(rel.quota, "desconhecida")
                self.assertEqual(rel.origem_credencial,
                                 "subscription-oauth")
                self.assertTrue(rel.versao)
                self.assertTrue(rel.modelos)
                # Sensor de modelos foi chamado (ordem: economia -> modelos).
                self.assertEqual(len(sensores["modelos"].chamadas), 1)

    def test_google_grok_supervised_mesmo_com_tudo_verde(self):
        for provider_id in ("google", "grok"):
            with self.subTest(provider=provider_id):
                rel = executar_preflight(espec_de(provider_id),
                                         _sensores_verdes(provider_id),
                                         env={}, config_persistida={})
                self.assertEqual(rel.resultado, "SUPERVISED")
                self.assertEqual(rel.erros, [])
                self.assertTrue(rel.modelos)

    def test_grok_origem_cached_token(self):
        rel = executar_preflight(espec_de("grok"),
                                 _sensores_verdes("grok"),
                                 env={}, config_persistida={})
        self.assertEqual(rel.origem_credencial, "cached-token")

    def test_relatorio_roundtrip(self):
        for rel in (executar_preflight(espec_de("codex"),
                                       _sensores_verdes("codex"),
                                       env={}, config_persistida={}),
                    executar_preflight(
                        espec_de("claude"),
                        {"exec": SensorFalso(_VERSAO_VERDE["claude"],
                                             (1, "Not logged in", "")),
                         "modelos": sensor_explosivo},
                        env={"ANTHROPIC_API_KEY": SEGREDO},
                        config_persistida={})):
            with self.subTest(resultado=rel.resultado):
                clone = RelatorioPreflight.from_dict(rel.to_dict())
                self.assertEqual(rel, clone)
                via_json = RelatorioPreflight.from_dict(
                    json.loads(json.dumps(rel.to_dict())))
                self.assertEqual(rel, via_json)

    def test_auditoria_ambiente_nao_retorna_valores(self):
        env = {"OPENAI_API_KEY": SEGREDO, "ANTHROPIC_AUTH_TOKEN": SEGREDO,
               "PATH": "inofensivo"}
        violacoes = auditar_ambiente(env)
        self.assertEqual(len(violacoes), 2)
        for v in violacoes:
            self.assertNotIn(SEGREDO, v.detalhe)
            self.assertNotIn(SEGREDO, repr(v.to_dict()))
        # Config persistida tambem nao vaza valores.
        viol_cfg = auditar_config({"OPENAI_API_KEY": SEGREDO})
        self.assertEqual(len(viol_cfg), 1)
        self.assertNotIn(SEGREDO, repr(viol_cfg[0].to_dict()))
        # Ambiente sanitizado remove PAYG (case-insensitive) sem mutar.
        limpo = ambiente_sanitizado({"OpenAI_Api_Key": SEGREDO,
                                     "PATH": "inofensivo"})
        self.assertEqual(limpo, {"PATH": "inofensivo"})

    def test_ambiente_global_nao_e_mutado(self):
        antes = dict(os.environ)
        env = {"GEMINI_API_KEY": SEGREDO, "OUTRA": "valor"}
        copia = dict(env)
        executar_preflight(espec_de("google"),
                           _sensores_verdes("google"),
                           env=env, config_persistida={})
        ambiente_sanitizado(env)
        self.assertEqual(dict(os.environ), antes)
        self.assertEqual(env, copia)


if __name__ == "__main__":
    unittest.main()
