"""Auditoria economica pre-invocacao (SSC+ P1-A, experimental).

Prova tres coisas: (a) o espelho da POLITICA_ECONOMICA do preflight e fiel
a politica imutavel da camada P0; (b) as auditorias detectam PAYG em
ambiente, config persistida e status declarado; (c) NENHUMA auditoria
devolve valor de credencial — somente nomes de variaveis e caminhos de
campos.
"""

import json
import os
import unittest

import apoio
from apoio import SENTINELA
from preflight import (POLITICA_ECONOMICA, BillingDesconhecido,
                       ChavePaygDetectada, ConfigPaygPersistida, ErroPreflight,
                       ambiente_sanitizado, auditar_ambiente, auditar_config,
                       auditar_status)
from ssc_p0.frota import POLITICA_ECONOMICA as POLITICA_P0


class EspelhoDaPoliticaP0(unittest.TestCase):
    """O preflight nao importa a politica da P0 — logo, precisa espelha-la."""

    def test_espelho_identico_a_politica_imutavel_da_p0(self):
        self.assertEqual(dict(POLITICA_ECONOMICA), dict(POLITICA_P0))

    def test_regras_economicas_declaradas(self):
        self.assertEqual(POLITICA_ECONOMICA["external_variable_cost_cap"], 0)
        self.assertEqual(POLITICA_ECONOMICA["subscription_oauth"], "ALLOW")
        for regra in ("payg_api", "extra_usage", "auto_topup",
                      "unknown_billing_mode"):
            with self.subTest(regra=regra):
                self.assertEqual(POLITICA_ECONOMICA[regra], "DENY")

    def test_politica_e_imutavel(self):
        with self.assertRaises(TypeError):
            POLITICA_ECONOMICA["payg_api"] = "ALLOW"


class Sanitizacao(unittest.TestCase):
    """A chave global do usuario permanece intacta; so nao entra no filho."""

    def test_remove_chaves_payg_em_qualquer_caixa(self):
        env = {"OPENAI_API_KEY": SENTINELA, "Anthropic_Api_Key": SENTINELA,
               "xai_api_key": SENTINELA, "PATH": "C:\\Windows",
               "CLAUDE_CODE_THEME": "dark"}
        limpo = ambiente_sanitizado(env)
        self.assertEqual(limpo, {"PATH": "C:\\Windows",
                                 "CLAUDE_CODE_THEME": "dark"})
        self.assertNotIn(SENTINELA, json.dumps(limpo))

    def test_nao_muta_o_dict_recebido(self):
        env = {"OPENAI_API_KEY": SENTINELA, "PATH": "p"}
        copia = dict(env)
        ambiente_sanitizado(env)
        self.assertEqual(env, copia)

    def test_nao_muta_os_environ(self):
        antes = dict(os.environ)
        ambiente_sanitizado()
        self.assertEqual(dict(os.environ), antes)

    def test_padrao_le_o_ambiente_do_processo_sem_chaves_payg(self):
        limpo = ambiente_sanitizado()
        self.assertEqual([n for n in limpo if n.lower().endswith("_api_key")],
                         [])


class AuditoriaDeAmbiente(unittest.TestCase):

    def test_nomes_conhecidos_sao_detectados(self):
        from preflight.economia import CHAVES_PAYG_CONHECIDAS
        for nome in CHAVES_PAYG_CONHECIDAS:
            with self.subTest(nome=nome):
                violacoes = auditar_ambiente({nome.upper(): SENTINELA})
                self.assertEqual(len(violacoes), 1)
                self.assertIsInstance(violacoes[0], ChavePaygDetectada)

    def test_violacoes_saem_em_ordem_estavel(self):
        env = {"XAI_API_KEY": SENTINELA, "GEMINI_API_KEY": SENTINELA,
               "OPENAI_API_KEY": SENTINELA}
        alvos = [v.alvo for v in auditar_ambiente(env)]
        self.assertEqual(alvos, sorted(alvos))

    def test_ambiente_vazio_nao_gera_violacao(self):
        self.assertEqual(auditar_ambiente({}), [])

    def test_escopo_de_bloqueio_e_mais_estreito_que_o_de_sanitizacao(self):
        # Token local de ferramenta: sanitizado (nao entra no subprocesso)
        # mas NAO acusado como PAYG — nao e canal tarifado de IA.
        env = {"VSCODE_GIT_IPC_AUTH_TOKEN": SENTINELA,
               "GIT_ASKPASS_ACCESS_TOKEN": SENTINELA, "PATH": "p"}
        self.assertEqual(auditar_ambiente(env), [])
        self.assertEqual(ambiente_sanitizado(env), {"PATH": "p"})

    def test_chave_de_provedor_fora_da_frota_bloqueia_e_e_sanitizada(self):
        for nome in ("NVIDIA_API_KEY", "OPENROUTER_API_KEY",
                     "DEEPSEEK_API_KEY", "Mistral_Api_Key",
                     "TOGETHER_API_KEY", "HuggingFace_Api_Token"):
            with self.subTest(nome=nome):
                env = {nome: SENTINELA, "PATH": "p"}
                self.assertEqual([v.codigo for v in auditar_ambiente(env)],
                                 ["P1A-PAYG-ENV"], nome)
                self.assertEqual(ambiente_sanitizado(env), {"PATH": "p"})

    def test_campo_api_key_nu_em_config_e_chave_persistida(self):
        # Escopo amplo na config: o campo nu, sem prefixo de provedor, ja e
        # chave substituindo OAuth (formato comum de auth.json).
        for campo in ("api_key", "apiKey", "api-key", "auth_token",
                      "accessToken", "secret_key"):
            with self.subTest(campo=campo):
                violacoes = auditar_config({campo: SENTINELA})
                self.assertEqual([v.codigo for v in violacoes],
                                 ["P1A-PAYG-CONFIG"], campo)

    def test_nenhum_valor_no_detalhe_nem_no_dict(self):
        violacao = auditar_ambiente({"OPENAI_API_KEY": SENTINELA})[0]
        self.assertNotIn(SENTINELA, violacao.detalhe)
        self.assertNotIn(SENTINELA, json.dumps(violacao.to_dict()))
        self.assertNotIn(SENTINELA, str(violacao))


class AuditoriaDeConfig(unittest.TestCase):

    def test_chave_persistida_aninhada_reporta_caminho(self):
        violacoes = auditar_config(
            {"providers": {"openai": {"api_key": SENTINELA}}})
        self.assertEqual(len(violacoes), 1)
        self.assertEqual(violacoes[0].alvo, "providers.openai.api_key")
        self.assertNotIn(SENTINELA, json.dumps(violacoes[0].to_dict()))

    def test_endpoint_payg_reporta_somente_o_host(self):
        # Caminho/query podem carregar segredo: so o host entra no laudo.
        violacoes = auditar_config(
            {"base_url": f"https://api.openai.com/v1?token={SENTINELA}"})
        self.assertEqual(len(violacoes), 1)
        self.assertIn("api.openai.com", violacoes[0].detalhe)
        self.assertNotIn(SENTINELA, violacoes[0].detalhe)

    def test_todos_os_hosts_payg_conhecidos_sao_detectados(self):
        from preflight.economia import _ENDPOINTS_PAYG
        for host in _ENDPOINTS_PAYG:
            with self.subTest(host=host):
                violacoes = auditar_config({"endpoint": f"https://{host}/v1"})
                self.assertEqual(len(violacoes), 1, host)

    def test_endpoint_de_assinatura_nao_e_violacao(self):
        self.assertEqual(auditar_config(
            {"base_url": "https://chatgpt.com/backend-api/codex"}), [])

    def test_chave_vazia_nao_e_violacao(self):
        self.assertEqual(auditar_config({"api_key": "", "auth_token": "   "}),
                         [])

    def test_config_vazia_ou_none(self):
        self.assertEqual(auditar_config({}), [])
        self.assertEqual(auditar_config(None), [])

    def test_flags_de_topup_em_variantes_de_escrita(self):
        for chave in ("auto_topup", "autoTopUp", "auto-top-up",
                      "AUTO_TOPUP_ENABLED", "extra_usage", "extraUsage",
                      "allowExtraCharges", "pay_as_you_go"):
            with self.subTest(chave=chave):
                violacoes = auditar_config({chave: True})
                self.assertEqual(len(violacoes), 1, chave)
                self.assertIsInstance(violacoes[0], ConfigPaygPersistida)

    def test_flag_desligada_em_qualquer_representacao(self):
        for valor in (False, 0, "false", "off", "no", "", "disabled", None):
            with self.subTest(valor=valor):
                self.assertEqual(auditar_config({"auto_topup": valor}), [])

    def test_flag_ligada_em_qualquer_representacao(self):
        for valor in (True, 1, "true", "on", "yes", "enabled", "TRUE"):
            with self.subTest(valor=valor):
                self.assertEqual(len(auditar_config({"auto_topup": valor})), 1)


class AuditoriaDeStatus(unittest.TestCase):

    def _base(self, **sobre):
        entry = {"billing_mode": "subscription", "variable_cost": 0,
                 "auth_mode": "subscription-oauth"}
        entry.update(sobre)
        return entry

    def test_assinatura_limpa_passa(self):
        self.assertEqual(auditar_status(self._base()), [])

    def test_billing_desconhecido_e_deny(self):
        for valor in ("", "   ", "desconhecido", "unknown", None):
            with self.subTest(valor=valor):
                violacoes = auditar_status(self._base(billing_mode=valor))
                self.assertEqual(len(violacoes), 1)
                self.assertIsInstance(violacoes[0], BillingDesconhecido)

    def test_billing_fora_da_assinatura_e_payg(self):
        for valor in ("payg", "pay-as-you-go", "credits", "prepaid"):
            with self.subTest(valor=valor):
                violacoes = auditar_status(self._base(billing_mode=valor))
                self.assertEqual([v.codigo for v in violacoes],
                                 ["P1A-PAYG-BILLING"])

    def test_custo_variavel_acima_do_teto(self):
        violacoes = auditar_status(self._base(variable_cost=0.0001))
        self.assertEqual([v.codigo for v in violacoes], ["P1A-PAYG-CUSTO"])

    def test_auth_payg_em_qualquer_grafia(self):
        for valor in ("payg", "payg-api", "api-key", "api_key", "API-KEY"):
            with self.subTest(valor=valor):
                violacoes = auditar_status(self._base(auth_mode=valor))
                self.assertEqual([v.codigo for v in violacoes],
                                 ["P1A-PAYG-AUTH"])

    def test_violacoes_acumulam(self):
        violacoes = auditar_status({"billing_mode": "payg",
                                    "variable_cost": 5,
                                    "auth_mode": "api-key"})
        self.assertEqual(len(violacoes), 3)

    def test_status_sem_campos_e_billing_desconhecido(self):
        self.assertEqual([v.codigo for v in auditar_status({})],
                         ["P1A-BILLING-DESCONHECIDO"])


class ErrosTipados(unittest.TestCase):

    def test_round_trip_preserva_tipo_codigo_detalhe_e_alvo(self):
        original = ChavePaygDetectada(detalhe="variavel PAYG: X", alvo="X")
        volta = ErroPreflight.from_dict(original.to_dict())
        self.assertIsInstance(volta, ChavePaygDetectada)
        self.assertEqual(volta.to_dict(), original.to_dict())

    def test_round_trip_de_todos_os_tipos(self):
        from preflight.economia import _TIPOS_ERRO
        # 9 tipos originais + DeclaracaoExpirada (emenda P1-A.3, item 1).
        self.assertEqual(len(_TIPOS_ERRO), 10)
        for nome, cls in _TIPOS_ERRO.items():
            with self.subTest(tipo=nome):
                erro = cls(detalhe="d", alvo="a")
                volta = ErroPreflight.from_dict(erro.to_dict())
                self.assertIsInstance(volta, cls)
                self.assertEqual(volta.codigo, cls.codigo)

    def test_codigo_pode_ser_especializado_sem_perder_o_tipo(self):
        erro = ConfigPaygPersistida(detalhe="d", codigo="P1A-PAYG-BILLING")
        volta = ErroPreflight.from_dict(erro.to_dict())
        self.assertEqual(volta.codigo, "P1A-PAYG-BILLING")
        self.assertIsInstance(volta, ConfigPaygPersistida)

    def test_erro_e_excecao_levantavel(self):
        with self.assertRaises(ErroPreflight) as ctx:
            raise BillingDesconhecido(detalhe="billing ausente")
        self.assertIn("P1A-BILLING-DESCONHECIDO", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
