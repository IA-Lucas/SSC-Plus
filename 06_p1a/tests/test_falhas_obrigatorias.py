"""As 9 falhas obrigatorias da missao SSC+ P1-A (experimental).

1. variavel PAYG em caixa mista no Windows;
2. chave persistida em configuracao;
3. OAuth ausente;
4. plano nao reconhecido;
5. quota esgotada;
6. billing desconhecido;
7. CLI indisponivel;
8. modelo removido;
9. conflito entre ambiente e login.

Exigencia: TODAS bloqueiam antes da invocacao ou devolvem erro tipado, e
NENHUMA cai em API paga. Cada teste afirma tres coisas: (a) resultado
BLOCKED; (b) codigo de erro tipado esperado; (c) nenhuma sonda de modelo
executada (o contador do sensor prova a ordem do bloqueio) — exceto na
falha 8, em que a propria descoberta e o ponto de falha. Nenhum teste cria
subprocesso: os CLIs reais nunca sao invocados.
"""

import json
import re
import unittest

import apoio
from apoio import SENTINELA, SensorFalso, codigos, espec_com, sensores_dict
from preflight import (BillingDesconhecido, ChavePaygDetectada,
                       CliIndisponivel, ConfigPaygPersistida,
                       ConflitoAmbienteLogin, ModeloRemovido, OAuthAusente,
                       PlanoNaoReconhecido, QuotaEsgotada,
                       ambiente_sanitizado, auditar_ambiente, espec_de,
                       executar_preflight)

# Nenhuma origem de credencial aceita pode ser um canal tarifado.
_ORIGENS_PAGAS = ("payg", "payg-api", "api-key", "api_key", "api key")


class FalhaObrigatoriaBase(unittest.TestCase):
    """Asserções comuns: bloqueio, tipagem e ausencia de queda em PAYG."""

    def afirmar_bloqueio(self, relatorio, codigo, sensor_modelos=None,
                         chamadas_modelos=0):
        self.assertEqual(relatorio.resultado, "BLOCKED")
        self.assertIn(codigo, codigos(relatorio))
        for erro in relatorio.erros:
            self.assertTrue(erro.codigo.startswith("P1A-"), erro.codigo)
            self.assertIsInstance(erro.detalhe, str)
            self.assertTrue(erro.detalhe.strip(), "erro tipado sem detalhe")
        if sensor_modelos is not None:
            self.assertEqual(sensor_modelos.n, chamadas_modelos,
                             "sonda de modelos executada fora de ordem")
        self.afirmar_sem_payg(relatorio)

    def afirmar_sem_payg(self, relatorio):
        """Nenhuma queda em API paga e nenhum valor de credencial no laudo."""
        despejo = json.dumps(relatorio.to_dict(), ensure_ascii=False)
        self.assertNotIn(SENTINELA, despejo,
                         "valor de credencial vazou para o relatorio")
        self.assertNotIn(relatorio.origem_credencial.lower(), _ORIGENS_PAGAS)
        self.assertNotIn("api.openai.com", despejo)
        self.assertNotIn("api.x.ai", despejo)


class Falha01VariavelPaygCaixaMista(FalhaObrigatoriaBase):
    """1. Variavel PAYG em caixa mista no Windows (env case-insensitive)."""

    def test_bloqueia_antes_de_qualquer_sonda(self):
        # Chave PAYG de OUTRO provedor, em caixa mista: o bloqueio ocorre
        # na auditoria de ambiente, antes de detectar o CLI.
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_de("codex"), sens,
            env={"Gemini_Api_Key": SENTINELA, "PATH": "C:\\Windows"})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-ENV", sensor_modelos)
        self.assertEqual(sensor_exec.n, 0,
                         "CLI sondado apesar da violacao economica")
        self.assertIsInstance(relatorio.erros[0], ChavePaygDetectada)
        # O nome e registrado com a caixa original; o valor, nunca.
        self.assertEqual(relatorio.erros[0].alvo, "Gemini_Api_Key")

    def test_deteccao_independe_da_caixa(self):
        for nome in ("OPENAI_API_KEY", "openai_api_key", "OpenAI_Api_Key",
                     "oPeNaI_aPi_KeY", "XAI_API_KEY", "Xai_Api_Key",
                     "Anthropic_Auth_Token", "GOOGLE_APPLICATION_CREDENTIALS",
                     "Google_Application_Credentials"):
            with self.subTest(nome=nome):
                violacoes = auditar_ambiente({nome: SENTINELA})
                self.assertEqual(len(violacoes), 1, nome)
                self.assertEqual(violacoes[0].codigo, "P1A-PAYG-ENV")
                self.assertEqual(violacoes[0].alvo, nome)
                self.assertNotIn(SENTINELA, str(violacoes[0]))

    def test_provedor_fora_da_frota_em_caixa_mista_tambem_bloqueia(self):
        # Provedor de modelo que nem esta na frota: a chave e PAYG ativa no
        # ambiente e bloqueia igual, em qualquer caixa.
        for nome in ("OpenRouter_Api_Key", "NVIDIA_API_KEY",
                     "DeepSeek_Api_Key", "Groq_Api_Key"):
            with self.subTest(nome=nome):
                violacoes = auditar_ambiente({nome: SENTINELA})
                self.assertEqual([v.codigo for v in violacoes],
                                 ["P1A-PAYG-ENV"], nome)

    def test_variavel_inocente_nao_bloqueia(self):
        self.assertEqual(auditar_ambiente(
            {"PATH": "C:\\Windows", "CLAUDE_CODE_THEME": "dark",
             "APIKEYS_DOC": "leia-me.md"}), [])

    def test_token_local_de_outra_ferramenta_e_filtrado_sem_bloquear(self):
        # Distincao de escopo: o token IPC do VS Code nao e canal tarifado
        # de IA (nao bloqueia), mas tambem nunca entra no subprocesso.
        env = {"VSCODE_GIT_IPC_AUTH_TOKEN": SENTINELA, "PATH": "C:\\Windows"}
        self.assertEqual(auditar_ambiente(env), [])
        self.assertNotIn("VSCODE_GIT_IPC_AUTH_TOKEN",
                         ambiente_sanitizado(env))
        sens, _, _ = sensores_dict("codex")
        relatorio = executar_preflight(espec_de("codex"), sens, env=env)
        self.assertEqual(relatorio.resultado, "ELIGIBLE")
        self.afirmar_sem_payg(relatorio)


class Falha02ChavePersistidaEmConfig(FalhaObrigatoriaBase):
    """2. Chave persistida em configuracao (substituindo OAuth)."""

    def test_chave_persistida_bloqueia_antes_da_sonda(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_de("codex"), sens, env={"PATH": "C:\\Windows"},
            config_persistida={"auth": {"OPENAI_API_KEY": SENTINELA}})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-CONFIG", sensor_modelos)
        self.assertEqual(sensor_exec.n, 0)
        self.assertIsInstance(relatorio.erros[0], ConfigPaygPersistida)
        self.assertEqual(relatorio.erros[0].alvo, "auth.OPENAI_API_KEY")

    def test_endpoint_payg_persistido_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict("claude")
        relatorio = executar_preflight(
            espec_de("claude"), sens, env={},
            config_persistida={"base_url": "https://api.anthropic.com/v1"})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-CONFIG", sensor_modelos)
        self.assertIn("api.anthropic.com", relatorio.erros[0].detalhe)

    def test_auto_topup_e_extra_usage_bloqueiam(self):
        for config in ({"billing": {"auto_topup": True}},
                       {"auto_top_up_enabled": "true"},
                       {"extra_usage": 1},
                       {"limits": {"allowExtraCharges": "on"}},
                       {"pay_as_you_go": "yes"}):
            with self.subTest(config=config):
                sens, _, sensor_modelos = sensores_dict("kimi")
                relatorio = executar_preflight(espec_de("kimi"), sens, env={},
                                               config_persistida=config)
                self.afirmar_bloqueio(relatorio, "P1A-PAYG-CONFIG",
                                      sensor_modelos)

    def test_config_de_assinatura_limpa_nao_bloqueia(self):
        sens, _, _ = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_de("codex"), sens, env={},
            config_persistida={"preferred_auth_method": "chatgpt",
                               "auto_topup": False, "extra_usage": "off",
                               "base_url": ""})
        self.assertEqual(relatorio.resultado, "ELIGIBLE")


class Falha03OAuthAusente(FalhaObrigatoriaBase):
    """3. OAuth ausente (login da assinatura nao encontrado)."""

    def test_nao_logado_bloqueia_antes_dos_modelos(self):
        sens, _, sensor_modelos = sensores_dict(
            "codex", login="Not logged in. Run `codex login`.")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-OAUTH-AUSENTE", sensor_modelos)
        self.assertIsInstance(relatorio.erros[0], OAuthAusente)
        self.assertEqual(relatorio.origem_credencial, "ausente")

    def test_origem_divergente_da_esperada_bloqueia(self):
        # Grok espera cached-token; um login que se anuncia OAuth de outro
        # canal nao serve — origem diferente da esperada e bloqueio.
        espec = espec_com("grok", auth_esperada="subscription-oauth")
        sens, _, sensor_modelos = sensores_dict(
            "grok", login="Using cached token (SuperGrok)")
        relatorio = executar_preflight(espec, sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-OAUTH-AUSENTE", sensor_modelos)
        self.assertIn("cached-token", relatorio.erros[0].detalhe)

    def test_marcadores_de_ausencia_reconhecidos(self):
        for texto in ("not logged in", "logged out", "unauthenticated",
                      "nao autenticado", "login required", "no credentials"):
            with self.subTest(texto=texto):
                sens, _, sensor_modelos = sensores_dict("codex", login=texto)
                relatorio = executar_preflight(espec_de("codex"), sens, env={})
                self.afirmar_bloqueio(relatorio, "P1A-OAUTH-AUSENTE",
                                      sensor_modelos)


class Falha04PlanoNaoReconhecido(FalhaObrigatoriaBase):
    """4. Plano nao reconhecido (fora da lista de planos aceitos)."""

    def test_plano_fora_da_lista_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict(
            "codex", login="Logged in using ChatGPT (plan: ChatGPT Free)")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-PLANO-DESCONHECIDO",
                              sensor_modelos)
        self.assertIsInstance(relatorio.erros[0], PlanoNaoReconhecido)

    def test_plano_ausente_no_status_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict(
            "kimi", login="managed:kimi-code type=kimi source=oauth")
        relatorio = executar_preflight(espec_de("kimi"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-PLANO-DESCONHECIDO",
                              sensor_modelos)
        self.assertIsNone(relatorio.plano)

    def test_plano_de_outra_assinatura_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict(
            "claude", login='{"loggedIn": true, "subscriptionType": "team"}')
        relatorio = executar_preflight(espec_de("claude"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-PLANO-DESCONHECIDO",
                              sensor_modelos)
        self.assertEqual(relatorio.plano, "team")


class Falha05QuotaEsgotada(FalhaObrigatoriaBase):
    """5. Quota esgotada: STOP_WAIT_RESET, nunca PAYG."""

    def test_quota_esgotada_bloqueia_e_nao_cai_em_payg(self):
        sens, _, sensor_modelos = sensores_dict(
            "codex", login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)\n"
                           "usage limit reached; resets in 3h")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-QUOTA-ESGOTADA", sensor_modelos)
        self.assertIsInstance(relatorio.erros[0], QuotaEsgotada)
        self.assertEqual(relatorio.quota, "esgotada")
        self.assertIn("STOP_WAIT_RESET", relatorio.erros[0].detalhe)
        self.assertIn("nunca PAYG", relatorio.erros[0].detalhe)

    def test_marcadores_de_esgotamento_reconhecidos(self):
        for marcador in ("quota exhausted", "quota esgotada", "0 remaining",
                         "rate_limit_exceeded", "usage limit reached"):
            with self.subTest(marcador=marcador):
                sens, _, sensor_modelos = sensores_dict(
                    "claude",
                    login='{"loggedIn": true, "subscriptionType": "max", '
                          f'"aviso": "{marcador}"}}')
                relatorio = executar_preflight(espec_de("claude"), sens,
                                               env={})
                self.afirmar_bloqueio(relatorio, "P1A-QUOTA-ESGOTADA",
                                      sensor_modelos)


class Falha06BillingDesconhecido(FalhaObrigatoriaBase):
    """6. Billing desconhecido = DENY (unknown_billing_mode)."""

    def test_billing_vazio_bloqueia_antes_de_tudo(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(espec_com("codex", billing_mode=""),
                                       sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-BILLING-DESCONHECIDO",
                              sensor_modelos)
        self.assertEqual(sensor_exec.n, 0)
        self.assertIsInstance(relatorio.erros[0], BillingDesconhecido)

    def test_billing_declaradamente_desconhecido_bloqueia(self):
        for valor in ("desconhecido", "unknown", "   "):
            with self.subTest(valor=valor):
                sens, _, sensor_modelos = sensores_dict("codex")
                relatorio = executar_preflight(
                    espec_com("codex", billing_mode=valor), sens, env={})
                self.afirmar_bloqueio(relatorio, "P1A-BILLING-DESCONHECIDO",
                                      sensor_modelos)

    def test_billing_payg_bloqueia(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_com("codex", billing_mode="payg"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-BILLING", sensor_modelos)
        self.assertEqual(sensor_exec.n, 0)

    def test_custo_variavel_positivo_bloqueia(self):
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_com("codex", variable_cost=0.01), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-CUSTO", sensor_modelos)
        self.assertEqual(sensor_exec.n, 0)

    def test_auth_esperada_payg_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_com("codex", auth_esperada="api-key"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-AUTH", sensor_modelos)


class Falha07CliIndisponivel(FalhaObrigatoriaBase):
    """7. CLI indisponivel (executavel ausente ou sem resposta)."""

    def test_executavel_ausente_e_erro_tipado(self):
        sensor_exec = SensorFalso(erro=FileNotFoundError("codex.exe"))
        sensor_modelos = SensorFalso()
        relatorio = executar_preflight(
            espec_de("codex"),
            {"exec": sensor_exec, "modelos": sensor_modelos}, env={})
        self.afirmar_bloqueio(relatorio, "P1A-CLI-INDISPONIVEL",
                              sensor_modelos)
        self.assertIsInstance(relatorio.erros[0], CliIndisponivel)
        self.assertIsNone(relatorio.versao)

    def test_erro_de_os_tambem_e_cli_indisponivel(self):
        sensor_exec = SensorFalso(erro=OSError("acesso negado"))
        relatorio = executar_preflight(
            espec_de("grok"), {"exec": sensor_exec, "modelos": SensorFalso()},
            env={})
        self.afirmar_bloqueio(relatorio, "P1A-CLI-INDISPONIVEL")

    def test_versao_com_rc_diferente_de_zero_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict("google")
        sens["exec"].respostas[espec_de("google").comandos["versao"]] = \
            (127, "", "command not found")
        relatorio = executar_preflight(espec_de("google"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-CLI-INDISPONIVEL",
                              sensor_modelos)

    def test_timeout_da_sonda_bloqueia(self):
        # O sensor real devolve rc=124 em timeout; o adaptador classifica
        # como CLI indisponivel, nunca como "pode invocar".
        sens, _, sensor_modelos = sensores_dict("kimi")
        sens["exec"].respostas[espec_de("kimi").comandos["versao"]] = \
            (124, "", "timeout do sensor de preflight")
        relatorio = executar_preflight(espec_de("kimi"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-CLI-INDISPONIVEL",
                              sensor_modelos)


class Falha08ModeloRemovido(FalhaObrigatoriaBase):
    """8. Modelo removido: descoberta sem nenhum modelo esperado."""

    def test_descoberta_sem_modelo_esperado_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict(
            "codex", modelos="text-embedding-3-small\nwhisper-1")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        # A descoberta E o ponto de falha: uma unica sonda de modelos.
        self.afirmar_bloqueio(relatorio, "P1A-MODELO-REMOVIDO",
                              sensor_modelos, chamadas_modelos=1)
        self.assertIsInstance(relatorio.erros[0], ModeloRemovido)
        self.assertIn("text-embedding-3-small", relatorio.modelos)
        self.assertNotIn("gpt-5", relatorio.modelos)

    def test_descoberta_vazia_bloqueia(self):
        sens, _, sensor_modelos = sensores_dict("claude", modelos="")
        relatorio = executar_preflight(espec_de("claude"), sens, env={})
        self.afirmar_bloqueio(relatorio, "P1A-MODELO-REMOVIDO",
                              sensor_modelos, chamadas_modelos=1)
        self.assertEqual(relatorio.modelos, [])

    def test_cli_de_modelos_indisponivel_bloqueia(self):
        sensor_exec, _ = apoio.sensores_verdes("codex")
        relatorio = executar_preflight(
            espec_de("codex"),
            {"exec": sensor_exec,
             "modelos": SensorFalso(erro=FileNotFoundError("codex.exe"))},
            env={})
        self.afirmar_bloqueio(relatorio, "P1A-CLI-INDISPONIVEL")
        # Diagnostico do login preservado apesar da falha na descoberta.
        self.assertEqual(relatorio.origem_credencial, "subscription-oauth")


class Falha09ConflitoAmbienteLogin(FalhaObrigatoriaBase):
    """9. Conflito entre ambiente e login: a chave nunca vence o OAuth."""

    def test_chave_do_provedor_com_oauth_ativo_e_conflito(self):
        sens, _, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(
            espec_de("codex"), sens, env={"OpenAI_Api_Key": SENTINELA})
        self.afirmar_bloqueio(relatorio, "P1A-CONFLITO-ENV-LOGIN",
                              sensor_modelos)
        self.assertIsInstance(relatorio.erros[0], ConflitoAmbienteLogin)
        self.assertEqual(relatorio.erros[0].alvo, "OpenAI_Api_Key")
        self.assertIn("nunca vence o OAuth", relatorio.erros[0].detalhe)

    def test_chave_do_provedor_sem_oauth_e_violacao_economica(self):
        # Sem login ativo nao ha conflito, mas a chave segue proibida: em
        # nenhum dos dois caminhos o preflight aceita a chave PAYG.
        sens, _, sensor_modelos = sensores_dict(
            "codex", login="Not logged in.")
        relatorio = executar_preflight(
            espec_de("codex"), sens, env={"OPENAI_API_KEY": SENTINELA})
        self.afirmar_bloqueio(relatorio, "P1A-PAYG-ENV", sensor_modelos)
        self.assertIn("P1A-OAUTH-AUSENTE", codigos(relatorio))

    def test_xai_api_key_nunca_vence_cached_token_do_grok(self):
        sens, _, sensor_modelos = sensores_dict("grok")
        relatorio = executar_preflight(
            espec_de("grok"), sens, env={"XAI_API_KEY": SENTINELA})
        self.afirmar_bloqueio(relatorio, "P1A-CONFLITO-ENV-LOGIN",
                              sensor_modelos)
        self.assertEqual(relatorio.erros[0].alvo, "XAI_API_KEY")

    def test_conflito_com_multiplas_chaves_lista_todos_os_nomes(self):
        sens, _, sensor_modelos = sensores_dict("claude")
        relatorio = executar_preflight(
            espec_de("claude"), sens,
            env={"ANTHROPIC_API_KEY": SENTINELA,
                 "Anthropic_Auth_Token": SENTINELA})
        self.afirmar_bloqueio(relatorio, "P1A-CONFLITO-ENV-LOGIN",
                              sensor_modelos)
        alvo = relatorio.erros[0].alvo
        self.assertIn("ANTHROPIC_API_KEY", alvo)
        self.assertIn("Anthropic_Auth_Token", alvo)


class CoberturaDasNoveFalhas(unittest.TestCase):
    """Meta-teste: as 9 falhas obrigatorias estao todas cobertas."""

    def test_uma_classe_por_falha_obrigatoria(self):
        classes = [nome for nome in globals()
                   if re.fullmatch(r"Falha\d{2}\w+", nome)
                   and isinstance(globals()[nome], type)]
        self.assertEqual(len(classes), 9, sorted(classes))
        for n in range(1, 10):
            with self.subTest(falha=n):
                self.assertTrue(
                    any(nome.startswith(f"Falha{n:02d}") for nome in classes),
                    f"falha obrigatoria {n} sem classe de teste")

    def test_todo_erro_tipado_tem_codigo_estavel_e_unico(self):
        tipos = (ChavePaygDetectada, ConfigPaygPersistida, OAuthAusente,
                 PlanoNaoReconhecido, QuotaEsgotada, BillingDesconhecido,
                 CliIndisponivel, ModeloRemovido, ConflitoAmbienteLogin)
        self.assertEqual(len(tipos), 9)
        codigos_ = [t.codigo for t in tipos]
        self.assertEqual(len(set(codigos_)), 9, codigos_)
        for tipo in tipos:
            with self.subTest(tipo=tipo.__name__):
                self.assertTrue(tipo.codigo.startswith("P1A-"))
                self.assertTrue(issubclass(tipo, Exception))


if __name__ == "__main__":
    unittest.main()
