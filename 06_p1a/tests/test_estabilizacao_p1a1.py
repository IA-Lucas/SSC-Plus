"""Regressoes da estabilizacao P1-A.1 (SSC+, experimental).

Cobre as quatro correcoes do portao P1-A.1, uma classe por correcao:

1. Quota fail-closed: login valido SEM evidencia de quota retorna
   "desconhecida", nunca "disponivel"; "disponivel" exige sinal positivo
   observavel.
2. Auditoria de config: percorre dicionarios E listas; nomes de campo de
   endpoint normalizados (base_url, baseUrl, api-base-url equivalentes);
   auth_mode desconhecido = DENY (nunca ELIGIBLE por inferencia).
3. Sanitizacao unica: prova_minima.py usa exclusivamente
   preflight.economia.ambiente_sanitizado; variantes de nome sanitizadas;
   token local nao tarifado e sanitizado sem bloquear a frota.
4. Escritor unico: lease + fencing no ponto de entrada P1 — segunda
   sessao falha antes de escrever/invocar; token obsoleto e recusado;
   lock expirado e recuperado pelo sucessor.

Nenhum teste invoca modelo, rede ou subprocesso real.
"""

import importlib.util
import json
import os
import re
import tempfile
import time
import unittest

import apoio
from apoio import SENTINELA, espec_com, sensores_dict
from escritor import EscritorP1
from preflight import (OAuthAusente, QuotaEsgotada, ambiente_sanitizado,
                       auditar_ambiente, auditar_config, auditar_status,
                       espec_de, executar_preflight)
from preflight.adaptadores import _quota_de
from preflight.economia import _TIPOS_ERRO
from ssc_p0.writelock import EscritorObsoleto, LockIndisponivel

_DIR_TESTS = os.path.dirname(os.path.abspath(__file__))
DIR_P1A = os.path.dirname(_DIR_TESTS)

_PADRAO_EMAIL = re.compile(
    "[A-Za-z0-9._%+-]+" "@" "[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")


def _codigos(violacoes):
    return [v.codigo for v in violacoes]


class QuotaFailClosed(unittest.TestCase):
    """Correcao 1: "disponivel" so com sinal positivo observavel."""

    def test_login_sem_evidencia_de_quota_e_desconhecida(self):
        for texto in ("Logged in using ChatGPT (plan: ChatGPT Pro 5x)",
                      "managed:kimi-code type=kimi source=oauth",
                      "all good"):
            with self.subTest(texto=texto[:30]):
                self.assertEqual(_quota_de(texto, True), "desconhecida")

    def test_sinal_positivo_observavel_da_disponivel(self):
        for texto in ("5 requests remaining", "quota available",
                      "100 calls left", "within limit",
                      "resets at midnight"):
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, True), "disponivel")

    def test_esgotada_precede_qualquer_sinal_positivo(self):
        self.assertEqual(
            _quota_de("usage limit reached; resets in 3h", True),
            "esgotada")
        self.assertEqual(_quota_de("0 remaining", True), "esgotada")

    def test_zero_quota_em_grafias_alternativas_e_esgotada(self):
        # Revisao P1-A.1 (MAJOR): zero-quota sem o literal "0 remaining"
        # nao pode cair no sinal positivo "remaining"/"left".
        for texto in ("You have 0 requests remaining",
                      "requests remaining: 0",
                      "0 calls left", "no calls left",
                      "no requests left"):
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, True), "esgotada")

    def test_negacao_nao_e_sinal_positivo(self):
        # "unavailable" contem "available": casamento por palavra (\b).
        for texto in ("quota information unavailable",
                      "quota status unavailable, try again later"):
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, True), "desconhecida")

    def test_pipeline_bloqueia_quota_esgotada_em_grafia_alternativa(self):
        sens, _, sensor_modelos = sensores_dict(
            "codex", login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)"
                           "\nYou have 0 requests remaining")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(relatorio.resultado, "BLOCKED")
        self.assertTrue(any(isinstance(e, QuotaEsgotada)
                            for e in relatorio.erros))
        self.assertEqual(sensor_modelos.n, 0)

    def test_sem_login_mesmo_com_sinal_positivo_e_desconhecida(self):
        self.assertEqual(_quota_de("5 requests remaining", False),
                         "desconhecida")

    def test_pipeline_eligible_com_quota_desconhecida_nao_bloqueia(self):
        sens, _, _ = sensores_dict("codex")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(relatorio.resultado, "ELIGIBLE")
        self.assertEqual(relatorio.quota, "desconhecida")

    def test_pipeline_propaga_quota_disponivel_quando_observada(self):
        sens, _, _ = sensores_dict(
            "claude",
            login='{"loggedIn": true, "subscriptionType": "max", '
                  '"quota": "120 requests remaining"}')
        relatorio = executar_preflight(espec_de("claude"), sens, env={})
        # Emenda P1-A.3 item 4: claude tem teto SUPERVISED; a quota
        # observada continua propagada no diagnostico.
        self.assertEqual(relatorio.resultado, "SUPERVISED")
        self.assertEqual(relatorio.quota, "disponivel")

    def test_pipeline_quota_esgotada_segue_bloqueando(self):
        sens, _, sensor_modelos = sensores_dict(
            "codex", login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)"
                           "\nusage limit reached; resets in 3h")
        relatorio = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(relatorio.resultado, "BLOCKED")
        self.assertTrue(any(isinstance(e, QuotaEsgotada)
                            for e in relatorio.erros))
        self.assertEqual(relatorio.quota, "esgotada")
        self.assertEqual(sensor_modelos.n, 0)


class ConfigRecursivaENormalizada(unittest.TestCase):
    """Correcao 2: listas percorridas + grafias de endpoint equivalentes."""

    def test_chave_payg_dentro_de_lista_e_detectada(self):
        violacoes = auditar_config(
            {"providers": [{"name": "x", "api_key": SENTINELA}]})
        self.assertEqual(_codigos(violacoes), ["P1A-PAYG-CONFIG"])
        self.assertEqual(violacoes[0].alvo, "providers[0].api_key")
        self.assertNotIn(SENTINELA, json.dumps(violacoes[0].to_dict()))

    def test_lista_aninhada_em_dict_aninhado(self):
        violacoes = auditar_config(
            {"a": {"b": [[{"secret_key": SENTINELA}]]}})
        self.assertEqual(_codigos(violacoes), ["P1A-PAYG-CONFIG"])

    def test_endpoint_payg_dentro_de_lista_herda_o_campo_pai(self):
        violacoes = auditar_config(
            {"endpoint": ["https://api.openai.com/v1"]})
        self.assertEqual(len(violacoes), 1)
        self.assertIn("api.openai.com", violacoes[0].detalhe)
        self.assertEqual(violacoes[0].alvo, "endpoint[0]")

    def test_grafias_de_endpoint_recebem_o_mesmo_tratamento(self):
        for chave in ("base_url", "baseUrl", "api-base-url", "apiBaseUrl",
                      "BASE-URL", "base_url_override", "apiEndpoint",
                      "API_BASE"):
            with self.subTest(chave=chave):
                violacoes = auditar_config(
                    {chave: "https://api.anthropic.com/v1"})
                self.assertEqual(_codigos(violacoes), ["P1A-PAYG-CONFIG"],
                                 chave)

    def test_chaves_genericas_de_endpoint_tambem_sao_auditadas(self):
        # Revisao P1-A.1 (MINOR): url/api_url/server/host com host PAYG
        # nao escapam mais da auditoria.
        for chave in ("url", "api_url", "apiUrl", "server", "host"):
            with self.subTest(chave=chave):
                violacoes = auditar_config(
                    {chave: "https://api.openai.com/v1"})
                self.assertEqual(_codigos(violacoes), ["P1A-PAYG-CONFIG"],
                                 chave)
        # Host que nao e PAYG segue sem violacao (mesmo em chave ampla).
        self.assertEqual(auditar_config(
            {"url": "https://chatgpt.com/backend-api/codex"}), [])

    def test_topup_dentro_de_lista_e_detectado(self):
        violacoes = auditar_config({"flags": [{"autoTopUp": True}]})
        self.assertEqual(_codigos(violacoes), ["P1A-PAYG-CONFIG"])
        self.assertEqual(violacoes[0].alvo, "flags[0].autoTopUp")

    def test_endpoint_de_assinatura_segue_sem_violacao(self):
        self.assertEqual(auditar_config(
            {"baseUrl": "https://chatgpt.com/backend-api/codex"}), [])
        self.assertEqual(auditar_config(
            {"endpoint": ["https://chatgpt.com/backend-api/codex"]}), [])

    def test_auth_desconhecida_e_deny_nunca_inferida(self):
        violacoes = auditar_status(
            {"billing_mode": "subscription", "variable_cost": 0,
             "auth_mode": "mtls-corporativo"})
        self.assertEqual(_codigos(violacoes), ["P1A-AUTH-DESCONHECIDA"])
        self.assertIsInstance(violacoes[0], OAuthAusente)

    def test_auth_ausente_nao_duplica_billing_desconhecido(self):
        self.assertEqual(_codigos(auditar_status({})),
                         ["P1A-BILLING-DESCONHECIDO"])

    def test_auth_desconhecida_no_spec_nunca_vira_eligible(self):
        espec = espec_com("codex", auth_esperada="mtls-corporativo")
        sens, sensor_exec, sensor_modelos = sensores_dict("codex")
        relatorio = executar_preflight(espec, sens, env={})
        self.assertEqual(relatorio.resultado, "BLOCKED")
        self.assertIn("P1A-AUTH-DESCONHECIDA", _codigos(relatorio.erros))
        # Bloqueio pre-sensor: nenhuma sonda chegou a executar.
        self.assertEqual(sensor_exec.n, 0)
        self.assertEqual(sensor_modelos.n, 0)

    def test_onze_tipos_de_erro_preservados(self):
        # 9 tipos originais + DeclaracaoExpirada (emenda P1-A.3, item 1:
        # declaracao de tier fora da validade de 24 h e erro tipado)
        # + ConfigNaoLida (P1-A.3.7, N2: fonte nao lida falha fechada).
        self.assertEqual(len(_TIPOS_ERRO), 11)


class SanitizacaoUnica(unittest.TestCase):
    """Correcao 3: uma unica implementacao — a canonica do preflight."""

    @classmethod
    def setUpClass(cls):
        caminho = os.path.join(DIR_P1A, "evidencias", "prova_minima.py")
        spec = importlib.util.spec_from_file_location(
            "_prova_minima_est", caminho)
        cls.modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.modulo)
        with open(caminho, encoding="utf-8") as f:
            cls.fonte = f.read()

    def test_script_importa_exclusivamente_a_canonica(self):
        from preflight import economia
        self.assertIs(self.modulo.ambiente_sanitizado,
                      economia.ambiente_sanitizado)

    def test_nenhuma_implementacao_duplicada_no_script(self):
        for removido in ("PADRAO_PAYG", "CHAVES_PROIBIDAS"):
            with self.subTest(simbolo=removido):
                self.assertNotIn(removido, self.fonte)

    def test_variantes_de_nome_sao_sanitizadas(self):
        env = {"api_key": "v", "apiKey": "v", "api-key": "v",
               "OpenAI_Api_Key": "v", "ANTHROPIC_AUTH_TOKEN": "v",
               "X_Custom_Secret_Key": "v", "PATH": "p"}
        self.assertEqual(ambiente_sanitizado(env), {"PATH": "p"})

    def test_removidas_do_runner_derivam_da_canonica(self):
        # Mesmo calculo de main(): nomes removidos = env - sanitizado.
        env = {"api_key": "v", "OpenAI_Api_Key": "v",
               "VSCODE_GIT_IPC_AUTH_TOKEN": "v", "PATH": "p"}
        removidas = sorted(set(env) - set(ambiente_sanitizado(env)))
        self.assertEqual(removidas, ["OpenAI_Api_Key",
                                     "VSCODE_GIT_IPC_AUTH_TOKEN",
                                     "api_key"])

    def test_token_local_nao_tarifado_sanitiza_sem_bloquear_a_frota(self):
        env = {"VSCODE_GIT_IPC_AUTH_TOKEN": "v", "PATH": "p"}
        self.assertEqual(auditar_ambiente(env), [])
        self.assertEqual(ambiente_sanitizado(env), {"PATH": "p"})

    def test_credencial_de_provedor_sanitiza_E_bloqueia(self):
        env = {"OpenAI_Api_Key": "v", "PATH": "p"}
        self.assertEqual(_codigos(auditar_ambiente(env)), ["P1A-PAYG-ENV"])
        self.assertEqual(ambiente_sanitizado(env), {"PATH": "p"})


class EscritorUnicoP1(unittest.TestCase):
    """Correcao 4: lease + fencing no ponto de entrada das operacoes P1."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="p1a1-escritor-")

    def test_aquisicao_concede_lease_e_fencing_token(self):
        escritor = EscritorP1(self.dir, sessao="t", lease_s=60)
        token = escritor.adquirir()
        self.assertEqual(token, 1)
        with open(escritor.caminho_lease, encoding="utf-8") as f:
            lease = json.load(f)
        self.assertEqual(lease["token"], 1)
        self.assertGreater(lease["expira_em"], time.time())
        self.assertFalse(EscritorP1.lease_expirado(escritor.caminho_lease))
        escritor.liberar()

    def test_segunda_sessao_falha_na_aquisicao(self):
        primeiro = EscritorP1(self.dir, sessao="t")
        primeiro.adquirir()
        with self.assertRaises(LockIndisponivel):
            EscritorP1(self.dir, sessao="t").adquirir()
        primeiro.liberar()

    def test_liberar_permite_o_sucessor_com_token_incrementado(self):
        primeiro = EscritorP1(self.dir, sessao="t")
        self.assertEqual(primeiro.adquirir(), 1)
        primeiro.liberar()
        segundo = EscritorP1(self.dir, sessao="t")
        self.assertEqual(segundo.adquirir(), 2)
        segundo.liberar()

    def test_crash_e_recuperacao_invalidam_o_token_antigo(self):
        antigo = EscritorP1(self.dir, sessao="t")
        antigo.adquirir()
        antigo._lock.simular_crash()  # morte: solta o lock do SO
        sucessor = EscritorP1(self.dir, sessao="t")
        self.assertEqual(sucessor.adquirir(), 2)  # recuperacao do lock
        with self.assertRaises(EscritorObsoleto):
            antigo.verificar()  # token obsoleto recusado
        with self.assertRaises(EscritorObsoleto):
            antigo.renovar()
        sucessor.verificar()  # o escritor vivo segue escrevendo
        sucessor.liberar()

    def test_renovar_estende_o_lease(self):
        escritor = EscritorP1(self.dir, sessao="t", lease_s=30)
        escritor.adquirir()
        with open(escritor.caminho_lease, encoding="utf-8") as f:
            expira_antes = json.load(f)["expira_em"]
        time.sleep(0.02)
        escritor.renovar()
        with open(escritor.caminho_lease, encoding="utf-8") as f:
            expira_depois = json.load(f)["expira_em"]
        self.assertGreater(expira_depois, expira_antes)
        escritor.liberar()

    def test_lease_expirado_sem_renovacao_recusa_a_escrita(self):
        escritor = EscritorP1(self.dir, sessao="t", lease_s=-1)
        escritor.adquirir()
        with self.assertRaises(EscritorObsoleto):
            escritor.verificar()
        escritor._lock.simular_crash()  # limpeza do lock do SO

    def test_lease_ausente_ou_ilegivel_e_tratado_como_morto(self):
        self.assertTrue(EscritorP1.lease_expirado(
            os.path.join(self.dir, "nao-existe.lease")))

    def test_runner_adquire_escritor_antes_de_invocar_provedor(self):
        # Prova estrutural: em prova_minima.main, a aquisicao do escritor
        # precede a invocacao (subprocess) e a gravacao de evidencia.
        with open(os.path.join(DIR_P1A, "evidencias", "prova_minima.py"),
                  encoding="utf-8") as f:
            fonte = f.read()
        corpo = fonte[fonte.index("def main()"):]
        self.assertLess(corpo.index("adquirir()"),
                        corpo.index("subprocess.run("))
        self.assertLess(corpo.index("adquirir()"),
                        corpo.index("write_text("))
        self.assertLess(corpo.index("verificar()"),
                        corpo.index("write_text("))

    def test_runner_segunda_sessao_retorna_3_sem_invocar_nada(self):
        # Prova comportamental (revisao P1-A.1): com o lock detido por
        # outra sessao, main() retorna 3 sem subprocesso e sem escrita.
        import importlib.util
        import sys
        from unittest import mock
        caminho = os.path.join(DIR_P1A, "evidencias", "prova_minima.py")
        spec = importlib.util.spec_from_file_location("_prova_minima_lock",
                                                      caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        locks = os.path.join(os.path.dirname(DIR_P1A), "locks")
        titular = EscritorP1(locks, sessao="p1-ops")
        titular.adquirir()
        try:
            with mock.patch.object(sys, "argv",
                                   ["prova_minima.py", "codex"]), \
                    mock.patch("subprocess.run") as espiar:
                rc = modulo.main()
            self.assertEqual(rc, 3)
            espiar.assert_not_called()
        finally:
            titular.liberar()

    def test_estado_de_lock_e_ignorado_pelo_git(self):
        with open(os.path.join(os.path.dirname(DIR_P1A), ".gitignore"),
                  encoding="utf-8") as f:
            gitignore = f.read()
        self.assertIn("locks/", gitignore)


class ZeroPiiNosArtefatos(unittest.TestCase):
    """Curadoria P1-A.1: nenhum e-mail nem usuario local versionado."""

    def test_nenhum_email_nem_usuario_local_em_06_p1a(self):
        # Tokens montados por concatenacao para este arquivo nao casar
        # consigo mesmo na varredura.
        usuario = "IA " + "Lucas"
        usuario_curto = "IA" + "LUCA"
        achados = []
        for base, dirs, arquivos in os.walk(DIR_P1A):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for nome in sorted(arquivos):
                if not nome.lower().endswith(
                        (".py", ".md", ".json", ".txt", ".sh")):
                    continue
                caminho = os.path.join(base, nome)
                with open(caminho, encoding="utf-8",
                          errors="replace") as f:
                    texto = f.read()
                rel = os.path.relpath(caminho, DIR_P1A)
                if _PADRAO_EMAIL.search(texto):
                    achados.append(f"{rel}: email")
                if usuario in texto or usuario_curto in texto:
                    achados.append(f"{rel}: usuario-local")
        self.assertEqual(achados, [], f"PII em: {achados}")


if __name__ == "__main__":
    unittest.main()
