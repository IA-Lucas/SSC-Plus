"""Regressoes das emendas P1-A.3 (SSC+, experimental — sem autoridade).

Decisao soberana sobre as emendas da P1-A.2:

1. APROVADA COM LIMITES: tier declarado pelo proprietario + OAuth
   observado habilita SOMENTE SHADOW_ELIGIBLE, validade maxima 24 h;
   NAO autoriza P2 nem execucao autonoma.
2. APROVADA: `codex doctor` comprova modelo efetivo atual e modo de
   autenticacao (NAO equivale a catalogo completo).
3. PARCIALMENTE APROVADA: `kimi provider list` comprova OAuth e modelo
   efetivo, NAO o plano comercial.
4. NAO APROVADA POR DECLARACAO: claude permanece SUPERVISED enquanto
   nao houver modelo exato observado por fonte oficial nao interativa;
   o plano Max, isoladamente, nao basta.
5. Google e Grok permanecem SUPERVISED, zero sondas automaticas.
6. Capsula subscription-only, politica NVIDIA e bloqueios PAYG
   inalterados (cobertos pelas suites anteriores, que seguem verdes).

Nenhum CLI real e invocado: todos os cenarios usam sensores falsos e
relogio injetado.
"""

import json
import os
import unittest
from datetime import datetime, timedelta, timezone

import apoio
from apoio import SENTINELA, SensorFalso, sensores_dict, sensores_verdes
from preflight import espec_de, executar_preflight
from preflight.pipeline import RelatorioPreflight
from preflight.sombra import (VALIDADE_MAXIMA_HORAS, DeclaracaoTier,
                              carregar_declaracoes, declaracao_valida,
                              expira_em)

AGORA = datetime(2026, 7, 31, 2, 0, 0, tzinfo=timezone.utc)

# Login OAuth observado SEM plano (o caso factual da P1-A.2: codex e
# kimi nao expoem o plano comercial no CLI).
_LOGIN_CODEX_SEM_PLANO = "Logged in using ChatGPT"
_LOGIN_KIMI_SEM_PLANO = "managed:kimi-code type=kimi source=oauth"


def decl(provider_id, tier="ChatGPT Pro 5x", horas_atras=1, validade=24,
         declarado_em=None):
    """Declaracao de tier valida por padrao (1 h atras, 24 h de janela)."""
    em = declarado_em or (AGORA - timedelta(hours=horas_atras)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    return DeclaracaoTier(provider_id=provider_id, tier=tier,
                          declarado_por="proprietario",
                          declarado_em_utc=em, validade_horas=validade)


def preflight_sombra(provider_id, declaracoes, agora=AGORA, **sobre):
    sens, sensor_exec, sensor_modelos = sensores_dict(provider_id, **sobre)
    relatorio = executar_preflight(
        espec_de(provider_id), sens, env={},
        tiers_declarados=declaracoes, agora=agora)
    return relatorio, sensor_exec, sensor_modelos


class TrilhaShadowEligible(unittest.TestCase):
    """Emenda 1: tier declarado + OAuth observado => SOMENTE SHADOW."""

    def test_codex_sem_plano_com_declaracao_valida_e_shadow(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "SHADOW_ELIGIBLE")
        self.assertEqual(rel.erros, [])
        self.assertEqual(rel.sombra["tier_declarado"], "ChatGPT Pro 5x")
        self.assertEqual(rel.sombra["declarado_por"], "proprietario")
        self.assertIn("NAO autoriza P2", rel.sombra["autorizacao"])
        self.assertIn("execucao autonoma", rel.sombra["autorizacao"])

    def test_kimi_sem_plano_com_declaracao_valida_e_shadow(self):
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        rel, _, _ = preflight_sombra(
            "kimi", declaracoes, login=_LOGIN_KIMI_SEM_PLANO)
        self.assertEqual(rel.resultado, "SHADOW_ELIGIBLE")
        self.assertEqual(rel.sombra["tier_declarado"], "Allegretto")

    def test_shadow_nunca_e_eligible(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertNotEqual(rel.resultado, "ELIGIBLE")

    def test_shadow_nunca_sobe_o_teto_supervised(self):
        # Provider com teto SUPERVISED, OAuth observado, plano NAO
        # exposto e declaracao valida: a trilha sombra e avaliada, mas o
        # teto vence — e o payload sombra NAO sai no relatorio.
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        sens, _, _ = sensores_dict("kimi", login=_LOGIN_KIMI_SEM_PLANO)
        rel = executar_preflight(
            apoio.espec_com("kimi", teto_resultado="SUPERVISED"), sens,
            env={}, tiers_declarados=declaracoes, agora=AGORA)
        self.assertEqual(rel.resultado, "SUPERVISED")
        self.assertIsNone(rel.sombra)

    def test_sem_declaracao_volta_ao_bloqueio_estatico(self):
        rel, _, _ = preflight_sombra(
            "codex", {}, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_declaracao_expirada_bloqueia_com_erro_tipado(self):
        declaracoes = {"codex": decl("codex", horas_atras=25)}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-DECLARACAO-EXPIRADA", apoio.codigos(rel))

    def test_declaracao_no_futuro_e_invalida(self):
        declaracoes = {"codex": decl("codex", horas_atras=-1)}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-DECLARACAO-EXPIRADA", apoio.codigos(rel))

    def test_declaracao_com_timestamp_ilegivel_e_invalida(self):
        declaracoes = {"codex": decl("codex",
                                     declarado_em="nao-e-uma-data")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-DECLARACAO-EXPIRADA", apoio.codigos(rel))

    def test_validade_declarada_acima_de_24h_e_limitada_a_24h(self):
        d23 = decl("codex", horas_atras=23, validade=720)
        self.assertTrue(declaracao_valida(d23, AGORA))
        d25 = decl("codex", horas_atras=25, validade=720)
        self.assertFalse(declaracao_valida(d25, AGORA))
        # A validade efetiva e SEMPRE limitada a 24 h, mesmo com 720
        # declaradas: as duas expiracoes diferem exatamente das 2 h que
        # separam as declaracoes.
        self.assertEqual(expira_em(d23) - expira_em(d25),
                         timedelta(hours=2))

    def test_fronteira_exata_das_24h(self):
        d = decl("codex", horas_atras=24)
        # No instante exato da expiracao a janela ja fechou.
        self.assertFalse(declaracao_valida(d, AGORA))
        # Um segundo antes da expiracao a janela ainda esta aberta (o
        # timestamp ISO tem resolucao de 1 s).
        d_quase = decl("codex", declarado_em=(
            AGORA - timedelta(hours=23, minutes=59, seconds=59)
        ).strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertTrue(declaracao_valida(d_quase, AGORA))

    def test_shadow_nao_vence_quota_esgotada(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, sensor_modelos = preflight_sombra(
            "codex", declaracoes,
            login=_LOGIN_CODEX_SEM_PLANO + "\nusage limit reached")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA", apoio.codigos(rel))
        self.assertEqual(sensor_modelos.n, 0)  # bloqueio pre-descoberta

    def test_shadow_nao_vence_conflito_env_login(self):
        declaracoes = {"codex": decl("codex")}
        sens, _, _ = sensores_dict("codex", login=_LOGIN_CODEX_SEM_PLANO)
        rel = executar_preflight(
            espec_de("codex"), sens, env={"OPENAI_API_KEY": SENTINELA},
            tiers_declarados=declaracoes, agora=AGORA)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-CONFLITO-ENV-LOGIN", apoio.codigos(rel))

    def test_shadow_nao_substitui_oauth_ausente(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login="Not logged in")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-OAUTH-AUSENTE", apoio.codigos(rel))

    def test_relatorio_shadow_sobrevive_ao_round_trip(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        clone = RelatorioPreflight.from_dict(
            json.loads(json.dumps(rel.to_dict())))
        self.assertEqual(clone, rel)
        self.assertEqual(clone.sombra["tier_declarado"],
                         "ChatGPT Pro 5x")


class DescobertaCodexDoctor(unittest.TestCase):
    """Emenda 2: `codex doctor` — modelo efetivo + auth mode, nao catalogo."""

    def _descoberta(self, rc, out, err=""):
        from preflight.adaptadores import AdaptadorPreflight
        sensor = SensorFalso({("doctor",): (rc, out, err)})
        adp = AdaptadorPreflight(espec_de("codex"), sensor_exec=sensor,
                                 env={})
        return adp.descobrir_modelos()

    def test_modelo_efetivo_e_auth_chatgpt(self):
        self.assertEqual(
            self._descoberta(0, "model gpt-5.6-sol\n"
                                "stored auth mode chatgpt"),
            ["gpt-5.6-sol"])

    def test_saida_em_stderr_tambem_vale(self):
        self.assertEqual(
            self._descoberta(0, "", "model gpt-5.6-sol\n"
                                    "stored auth mode chatgpt"),
            ["gpt-5.6-sol"])

    def test_sem_auth_mode_e_fail_closed(self):
        self.assertEqual(self._descoberta(0, "model gpt-5.6-sol"), [])

    def test_auth_mode_diferente_de_chatgpt_e_fail_closed(self):
        self.assertEqual(
            self._descoberta(0, "model gpt-5.6-sol\n"
                                "stored auth mode apikey"), [])

    def test_rc_nao_zero_e_fail_closed(self):
        self.assertEqual(
            self._descoberta(1, "model gpt-5.6-sol\n"
                                "stored auth mode chatgpt"), [])

    def test_sem_modelo_efetivo_e_fail_closed(self):
        self.assertEqual(
            self._descoberta(0, "stored auth mode chatgpt"), [])

    def test_pipeline_shadow_com_modelo_do_doctor(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "SHADOW_ELIGIBLE")
        self.assertEqual(rel.modelos, ["gpt-5.6-sol"])

    def test_doctor_incompreensivel_bloqueia_com_modelo_removido(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO,
            modelos="saida irreconhecivel")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-MODELO-REMOVIDO", apoio.codigos(rel))


class KimiProviderList(unittest.TestCase):
    """Emenda 3: `provider list` comprova OAuth e modelo efetivo, nao plano."""

    def test_oauth_e_modelo_efetivo_sem_plano_e_shadow(self):
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        rel, _, _ = preflight_sombra(
            "kimi", declaracoes, login=_LOGIN_KIMI_SEM_PLANO,
            modelos="Default model: kimi-code/k3")
        self.assertEqual(rel.resultado, "SHADOW_ELIGIBLE")
        self.assertTrue(any("kimi" in m for m in rel.modelos))

    def test_sem_declaracao_bloqueia(self):
        rel, _, _ = preflight_sombra(
            "kimi", {}, login=_LOGIN_KIMI_SEM_PLANO)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))


class ClaudeSupervised(unittest.TestCase):
    """Emenda 4: claude SUPERVISED; plano Max sozinho nao basta."""

    def test_plano_max_observado_nao_passa_de_supervised(self):
        sens, _, sensor_modelos = sensores_dict("claude")
        rel = executar_preflight(espec_de("claude"), sens, env={})
        self.assertEqual(rel.resultado, "SUPERVISED")
        self.assertEqual(rel.plano, "max")
        self.assertEqual(rel.modelos, [])
        # ZERO sondas de modelos: `claude models` e interativo e a
        # descoberta foi desativada na especificacao.
        self.assertEqual(sensor_modelos.n, 0)

    def test_declaracao_de_tier_nao_muda_o_teto_do_claude(self):
        declaracoes = {"claude": decl("claude", tier="Claude Max 5x")}
        sens, _, _ = sensores_dict("claude")
        rel = executar_preflight(espec_de("claude"), sens, env={},
                                 tiers_declarados=declaracoes, agora=AGORA)
        self.assertEqual(rel.resultado, "SUPERVISED")

    def test_plano_desconhecido_segue_bloqueando(self):
        sens, _, _ = sensores_dict(
            "claude", login='{"loggedIn": true, "subscriptionType": "team"}')
        rel = executar_preflight(espec_de("claude"), sens, env={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))


class DeclaracoesDoProprietario(unittest.TestCase):
    """O arquivo real de tiers: estrutura e coerencia com a especificacao."""

    def _arquivo(self):
        caminho = os.path.join(os.path.dirname(apoio.__file__), "..",
                               "tiers_declarados.json")
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)

    def test_arquivo_real_parseia_e_cobre_codex_e_kimi(self):
        declaracoes = carregar_declaracoes(self._arquivo())
        self.assertEqual(set(declaracoes), {"codex", "kimi"})
        for pid, d in declaracoes.items():
            with self.subTest(provedor=pid):
                self.assertEqual(d.tier, espec_de(pid).plano_esperado)
                self.assertEqual(d.declarado_por, "proprietario")
                self.assertLessEqual(d.validade_horas,
                                     VALIDADE_MAXIMA_HORAS)

    def test_estrutura_malformada_devolve_vazio(self):
        self.assertEqual(carregar_declaracoes({}), {})
        self.assertEqual(carregar_declaracoes({"declaracoes": [{}]}), {})
        self.assertEqual(carregar_declaracoes("nao-e-dict"), {})

    def test_campos_vazios_nao_habilitam_nada(self):
        # Revisao P1-A.3 (MINOR): tier ou declarante vazio = descartado.
        base = {"provider_id": "codex", "tier": "ChatGPT Pro 5x",
                "declarado_por": "proprietario",
                "declarado_em_utc": "2026-07-31T01:00:00Z"}
        for campo in ("provider_id", "tier", "declarado_por"):
            with self.subTest(campo=campo):
                entrada = dict(base, **{campo: "  "})
                self.assertEqual(
                    carregar_declaracoes({"declaracoes": [entrada]}), {})

    def test_timestamp_extremo_nao_transborda(self):
        # Revisao P1-A.3 (MINOR): declarado_em perto de datetime.max
        # causava OverflowError; agora e declaracao invalida, sem excecao.
        d = decl("codex", declarado_em="9999-12-31T23:59:59Z")
        self.assertIsNone(expira_em(d))
        self.assertFalse(declaracao_valida(d, AGORA))


class GoogleGrokZeroSondas(unittest.TestCase):
    """Emenda 5: google/grok SUPERVISED com ZERO sondas automaticas."""

    def test_supervised_sem_nenhuma_sonda(self):
        for pid in ("google", "grok"):
            with self.subTest(provedor=pid):
                sens, sensor_exec, sensor_modelos = sensores_dict(pid)
                rel = executar_preflight(espec_de(pid), sens, env={})
                self.assertEqual(rel.resultado, "SUPERVISED")
                self.assertEqual(rel.modelos, [])
                self.assertEqual(sensor_exec.n, 0)     # nem versao/login
                self.assertEqual(sensor_modelos.n, 0)  # nem modelos

    def test_sem_sonda_de_modelos_implica_teto_supervised(self):
        # Revisao P1-A.3 (MINOR): o invariante deixa de ser convencao —
        # descoberta desativada so pode coexistir com teto SUPERVISED.
        from preflight import ESPECIFICACOES
        for espec in ESPECIFICACOES.values():
            with self.subTest(provedor=espec.provider_id):
                if espec.comandos["modelos"] is None:
                    self.assertEqual(espec.teto_resultado, "SUPERVISED")


class RevisaoCodexRodada2(unittest.TestCase):
    """Achados da 2a revisao codex: fail-closed adicional."""

    def test_kimi_rc_nao_zero_bloqueia(self):
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        sens, _, _ = sensores_dict("kimi", login=_LOGIN_KIMI_SEM_PLANO)
        sens["modelos"] = SensorFalso(padrao=(1, "", "erro"))
        rel = executar_preflight(espec_de("kimi"), sens, env={},
                                 tiers_declarados=declaracoes, agora=AGORA)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-MODELO-REMOVIDO", apoio.codigos(rel))

    def test_kimi_sem_default_model_nao_se_prova_pelo_nome_do_provider(self):
        # "managed:kimi-code" na saida NAO e evidencia de modelo efetivo.
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        rel, _, _ = preflight_sombra(
            "kimi", declaracoes, login=_LOGIN_KIMI_SEM_PLANO,
            modelos="managed:kimi-code type=kimi source=oauth")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-MODELO-REMOVIDO", apoio.codigos(rel))

    def test_tier_declarado_incompativel_bloqueia(self):
        declaracoes = {"codex": decl("codex", tier="free")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_no_requests_remaining_e_quota_esgotada(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes,
            login=_LOGIN_CODEX_SEM_PLANO + "\nno requests remaining")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA", apoio.codigos(rel))

    def test_offset_extremo_nao_transborda(self):
        d = decl("codex", declarado_em="0001-01-01T00:00:00+14:00")
        self.assertFalse(declaracao_valida(d, AGORA))  # sem OverflowError

    def test_relogio_naive_e_fail_closed(self):
        d = decl("codex")
        self.assertFalse(declaracao_valida(
            d, AGORA.replace(tzinfo=None)))


class RevisaoKimiRodada1(unittest.TestCase):
    """Achados da revisao kimi: bypass de plano e marcador solto."""

    def test_substring_incidental_nao_e_plano(self):
        # "profile" contem "pro": sem fronteira de palavra isto virava
        # ELIGIBLE pleno, pulando POR CIMA da trilha sombra.
        for texto in ("profile updated", "prompt ready", "maximum"):
            with self.subTest(texto=texto):
                rel, _, _ = preflight_sombra(
                    "codex", {},
                    login=f"Logged in using ChatGPT\n{texto}")
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn("P1A-PLANO-DESCONHECIDO",
                              apoio.codigos(rel))

    def test_plano_real_continua_reconhecido(self):
        sens, _, _ = sensores_dict("codex")
        rel = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(rel.resultado, "ELIGIBLE")
        self.assertEqual(rel.plano, "chatgpt pro 5x")

    def test_chatgpt_solto_nao_e_login(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login="visit chatgpt.com for details")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-OAUTH-AUSENTE", apoio.codigos(rel))

    def test_caminho_eligible_pleno_do_codex_via_doctor(self):
        # Plano observado + doctor comprovando modelo/auth: ELIGIBLE
        # pleno (a trilha sombra so existe para plano NAO observavel).
        sens, _, _ = sensores_dict("codex")
        rel = executar_preflight(espec_de("codex"), sens, env={})
        self.assertEqual(rel.resultado, "ELIGIBLE")
        self.assertEqual(rel.modelos, ["gpt-5.6-sol"])


class RevisaoRodada3(unittest.TestCase):
    """Achados da 3a rodada codex + 2a kimi (confirmacao)."""

    def test_upgrade_to_pro_nao_e_plano(self):
        # Token curto sem rotulo de plano: texto comercial incidental.
        rel, _, _ = preflight_sombra(
            "codex", {},
            login="Logged in using ChatGPT\nUpgrade to Pro today!")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_plano_rotulado_curto_e_aceito(self):
        rel, _, _ = preflight_sombra(
            "codex", {}, login="Logged in using ChatGPT\nplan: pro")
        self.assertEqual(rel.resultado, "ELIGIBLE")
        self.assertEqual(rel.plano, "pro")

    def test_tier_parcial_nao_satisfaz_o_portao(self):
        # "pro" consta literalmente em planos_aceitos do codex — aceito.
        # O bypass da revisao era a contencao RECIPROCA: tiers que so
        # aparecem DENTRO da frase aceita ("chatgpt", "5x") ou de outro
        # provedor ("claude") nao podem satisfazer o portao.
        for tier in ("5x", "chatgpt", "claude"):
            with self.subTest(tier=tier):
                declaracoes = {"codex": decl("codex", tier=tier)}
                rel, _, _ = preflight_sombra(
                    "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO)
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_zero_of_cem_remaining_e_esgotada(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes,
            login=_LOGIN_CODEX_SEM_PLANO + "\n0 of 100 requests remaining")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA", apoio.codigos(rel))

    def test_no_remaining_e_none_left_sao_esgotadas(self):
        from preflight.adaptadores import _quota_de
        self.assertEqual(_quota_de("no remaining quota", True), "esgotada")
        self.assertEqual(_quota_de("none left", True), "esgotada")

    def test_doctor_com_auth_conflitante_e_fail_closed(self):
        from preflight.adaptadores import AdaptadorPreflight
        sensor = SensorFalso({("doctor",): (
            0, "model gpt-5.6-sol\nstored auth mode chatgpt\n"
               "auth mode apikey", "")})
        adp = AdaptadorPreflight(espec_de("codex"), sensor_exec=sensor,
                                 env={})
        self.assertEqual(adp.descobrir_modelos(), [])

    def test_doctor_com_linhas_modelo_espurias(self):
        # "model reasoning effort" nao e identificador de modelo.
        from preflight.adaptadores import AdaptadorPreflight
        sensor = SensorFalso({("doctor",): (
            0, "model gpt-5.6-sol\nmodel reasoning effort high\n"
               "stored auth mode chatgpt", "")})
        adp = AdaptadorPreflight(espec_de("codex"), sensor_exec=sensor,
                                 env={})
        self.assertEqual(adp.descobrir_modelos(), ["gpt-5.6-sol"])

    def test_declarante_que_nao_e_o_proprietario_e_descartado(self):
        base = {"provider_id": "codex", "tier": "ChatGPT Pro 5x",
                "declarado_em_utc": "2026-07-31T01:00:00Z"}
        for declarante in (None, "operador", "", 42):
            with self.subTest(declarante=declarante):
                entrada = dict(base, declarado_por=declarante)
                self.assertEqual(
                    carregar_declaracoes({"declaracoes": [entrada]}), {})

    def test_caminho_do_relatorio_nao_carrega_perfil_local(self):
        import os as _os
        sens, _, _ = sensores_dict("codex")
        rel = executar_preflight(espec_de("codex"), sens, env={})
        texto = json.dumps(rel.to_dict())
        self.assertNotIn(_os.path.expanduser("~"), texto)
        self.assertEqual(rel.caminho,
                         "~/AppData/Local/Programs/OpenAI/Codex/bin/"
                         "codex.exe")

    def test_google_grok_estatico_nao_simula_evidencia(self):
        for pid in ("google", "grok"):
            with self.subTest(provedor=pid):
                sens, _, _ = sensores_dict(pid)
                rel = executar_preflight(espec_de(pid), sens, env={})
                self.assertEqual(rel.resultado, "SUPERVISED")
                self.assertIsNone(rel.plano)
                self.assertEqual(rel.origem_credencial, "nao-sondada")

    def test_oauth_solto_nao_e_login_claude(self):
        sens, _, _ = sensores_dict("claude", login="oauth token expired")
        rel = executar_preflight(espec_de("claude"), sens, env={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-OAUTH-AUSENTE", apoio.codigos(rel))

    def test_sombra_ausente_em_blocked_e_supervised(self):
        # ModeloRemovido apos o portao sombra: o payload nao acompanha.
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes, login=_LOGIN_CODEX_SEM_PLANO,
            modelos="saida irreconhecivel")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIsNone(rel.sombra)


class RevisaoRodada4(unittest.TestCase):
    """Achados da 4a rodada codex (confirmacao final)."""

    def test_upgrade_to_chatgpt_pro_nao_e_plano(self):
        # Nome longo do plano em texto corrido: sem rotulo, nao e prova.
        rel, _, _ = preflight_sombra(
            "codex", {},
            login="Logged in using ChatGPT\nUpgrade to ChatGPT Pro!")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_kimi_login_exige_os_dois_marcadores(self):
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        for login in ("managed:kimi-code type=kimi",
                      "source=oauth ativo"):
            with self.subTest(login=login):
                rel, _, _ = preflight_sombra(
                    "kimi", declaracoes, login=login)
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn("P1A-OAUTH-AUSENTE", apoio.codigos(rel))

    def test_kimi_default_model_conflitante_e_fail_closed(self):
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        rel, _, _ = preflight_sombra(
            "kimi", declaracoes, login=_LOGIN_KIMI_SEM_PLANO,
            modelos="Default model: kimi-code/k3\n"
                    "Default model: kimi-code/k2")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-MODELO-REMOVIDO", apoio.codigos(rel))

    def test_portao_revalida_a_declaracao(self):
        # DeclaracaoTier construida DIRETAMENTE (sem carregar_declaracoes)
        # com campos ilegitimos nao habilita sombra.
        from preflight.sombra import DeclaracaoTier
        em = "2026-07-31T01:00:00Z"
        casos = {
            "declarante-errado": DeclaracaoTier(
                "codex", "ChatGPT Pro 5x", "operador", em),
            "provider-errado": DeclaracaoTier(
                "kimi", "ChatGPT Pro 5x", "proprietario", em),
            "tier-vazio": DeclaracaoTier(
                "codex", " ", "proprietario", em),
        }
        for nome, d in casos.items():
            with self.subTest(caso=nome):
                rel, _, _ = preflight_sombra(
                    "codex", {"codex": d}, login=_LOGIN_CODEX_SEM_PLANO)
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_quota_available_esgotada(self):
        declaracoes = {"codex": decl("codex")}
        for texto in ("0 tokens available", "no quota available"):
            with self.subTest(texto=texto):
                rel, _, _ = preflight_sombra(
                    "codex", declaracoes,
                    login=_LOGIN_CODEX_SEM_PLANO + "\n" + texto)
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn("P1A-QUOTA-ESGOTADA", apoio.codigos(rel))

    def test_cli_indisponivel_na_sonda_de_login_e_blocked(self):
        def exec_misto(argv, env=None, timeout=None):
            if tuple(argv[1:]) == ("--version",):
                return (0, "0.145.0", "")
            raise FileNotFoundError("codex.exe")
        rel = executar_preflight(
            espec_de("codex"),
            {"exec": exec_misto, "modelos": SensorFalso()}, env={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-CLI-INDISPONIVEL", apoio.codigos(rel))

    def test_plano_observado_incompativel_bloqueia_mesmo_com_declaracao(self):
        # Revisao final kimi: "plan: team" e evidencia OBSERVADA contra o
        # tier — precede a declaracao; a trilha sombra nao se aplica.
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes,
            login="Logged in using ChatGPT\nplan: team")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))
        self.assertIsNone(rel.sombra)

    def test_shadow_eligible_nao_tem_consumidor_de_execucao(self):
        # Invariante de integracao (revisao P1-A.3): o literal
        # SHADOW_ELIGIBLE so existe no pipeline (classificacao) — nenhum
        # runner/consumidor o usa para executar ou autorizar algo.
        dir_p1a = os.path.dirname(os.path.dirname(apoio.__file__))
        ocorrencias = []
        for base, dirs, arquivos in os.walk(dir_p1a):
            dirs[:] = [d for d in dirs
                       if d not in ("__pycache__", "tests")]
            for nome in arquivos:
                if not nome.endswith(".py"):
                    continue
                caminho = os.path.join(base, nome)
                with open(caminho, encoding="utf-8") as f:
                    if "SHADOW_ELIGIBLE" in f.read():
                        ocorrencias.append(
                            os.path.relpath(caminho, dir_p1a))
        self.assertEqual(
            sorted(ocorrencias),
            sorted([
                os.path.join("preflight", "pipeline.py"),   # logica
                # mencoes documentais (docstrings/comentarios/prompt),
                # nenhuma com logica sobre o valor:
                os.path.join("preflight", "__init__.py"),
                os.path.join("preflight", "economia.py"),
                os.path.join("preflight", "sombra.py"),
                "preflight_capsula.py",
                os.path.join("evidencias", "revisao_p1a3.py")]))
        # Reforco (revisao P1-A.3, rodada 5): fora do pacote preflight e
        # dos testes, NENHUM arquivo consome elegibilidade de forma
        # generica (`!= "BLOCKED"`, `== "ELIGIBLE"`) — nao ha consumidor
        # que transforme classificacao em execucao.
        for base, dirs, arquivos in os.walk(dir_p1a):
            dirs[:] = [d for d in dirs
                       if d not in ("__pycache__", "tests", "preflight")]
            for nome in arquivos:
                if not nome.endswith(".py"):
                    continue
                caminho = os.path.join(base, nome)
                with open(caminho, encoding="utf-8") as f:
                    fonte = f.read()
                self.assertNotIn('!= "BLOCKED"', fonte, caminho)
                self.assertNotIn('== "ELIGIBLE"', fonte, caminho)


class RevisaoRodada5(unittest.TestCase):
    """Achados da 5a rodada codex (convergencia)."""

    def test_rotulo_precisa_ser_palavra_inteira(self):
        # "explanation: pro" contem "plan" dentro de "explanation" —
        # nao e rotulo de plano.
        rel, _, _ = preflight_sombra(
            "codex", {},
            login="Logged in using ChatGPT\nexplanation: pro")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_plano_negado_nunca_e_reconhecido(self):
        from preflight.adaptadores import plano_reconhecido
        self.assertFalse(plano_reconhecido("not pro", ("pro",)))
        self.assertFalse(plano_reconhecido("no max", ("max",)))
        rel, _, _ = preflight_sombra(
            "codex", {}, login="Logged in using ChatGPT\nplan: not pro")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))

    def test_kimi_oauth_de_outra_linha_nao_valida(self):
        # Marcadores em registros DISTINTOS: o OAuth de outro provider
        # nao valida o managed:kimi-code.
        declaracoes = {"kimi": decl("kimi", tier="Allegretto")}
        rel, _, _ = preflight_sombra(
            "kimi", declaracoes,
            login="managed:other source=oauth\nmanaged:kimi-code type=kimi")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-OAUTH-AUSENTE", apoio.codigos(rel))

    def test_quota_barra_zero_e_esgotada(self):
        declaracoes = {"codex": decl("codex")}
        rel, _, _ = preflight_sombra(
            "codex", declaracoes,
            login=_LOGIN_CODEX_SEM_PLANO + "\n0/100 requests remaining")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA", apoio.codigos(rel))

    def test_declaracao_com_campos_nao_texto_e_fail_closed(self):
        from preflight.sombra import DeclaracaoTier
        em = "2026-07-31T01:00:00Z"
        for campos in (("codex", None, "proprietario", em),
                       ("codex", "ChatGPT Pro 5x", None, em),
                       ("codex", "ChatGPT Pro 5x", 42, em)):
            with self.subTest(campos=campos[1:3]):
                d = DeclaracaoTier(*campos)
                rel, _, _ = preflight_sombra(
                    "codex", {"codex": d}, login=_LOGIN_CODEX_SEM_PLANO)
                self.assertEqual(rel.resultado, "BLOCKED")
                self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(rel))


    def test_validade_infinita_no_loader_e_descartada(self):
        # Revisao final kimi: int(inf) lancava OverflowError no loader.
        entrada = {"provider_id": "codex", "tier": "ChatGPT Pro 5x",
                   "declarado_por": "proprietario",
                   "declarado_em_utc": "2026-07-31T01:00:00Z",
                   "validade_horas": float("inf")}
        self.assertEqual(carregar_declaracoes({"declaracoes": [entrada]}),
                         {})


if __name__ == "__main__":
    unittest.main()
