"""Frota subscription-only (ADENDO 0.3): os 8 testes minimos exigidos.

1. API key presente nao substitui OAuth da assinatura.
2. Billing desconhecido bloqueia ANTES da invocacao.
3. Quota esgotada troca de provedor sem perder linhagem.
4. Ausencia de provedor = STOP_WAIT_RESET, nunca PAYG.
5. Autor nao aprova a propria entrega critica.
6. Grok usa cached_token/ACP, nunca XAI_API_KEY/api.x.ai.
7. Google e Grok respeitam o nivel de autonomia permitido.
8. Catalogo descobre modelos; aliases nunca permanentes.
"""

import os
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.frota import (AdaptadorAssinatura, Frota, IndependenciaInsuficiente,
                          PoliticaEconomicaViolada, STOP_WAIT_RESET,
                          ambiente_sanitizado, catalogo_de_frota,
                          envelope_de_frota, executar_com_frota, frota_inicial,
                          politica_de_frota, verificar_automacao,
                          verificar_canal, verificar_economia)
from ssc_p0.providers import FakeProvider


def _entry(provider_id="codex", model_id="gpt-5-codex", **sobre):
    base = dict(
        provider_id=provider_id, model_id=model_id,
        capability_profile={"capacidades": ["implementacao"]},
        auth_mode="subscription-oauth", billing_mode="subscription",
        quota_state="disponivel", quota_reset=None,
        automation_permission="allow",
        terms_profile={"oauth_profile": f"oauth:{provider_id}"},
        variable_cost=0.0, papeis_preferidos=["autor", "revisor", "juiz"],
        canal_oficial=True)
    base.update(sobre)
    return ct.FleetEntry(**base).validado()


def _lab_frota(apoio_mod, frota, programa=None):
    return apoio_mod.novo_lab(
        catalogo=catalogo_de_frota(frota),
        politica=politica_de_frota(frota),
        aprovacao=envelope_de_frota(frota),
        programa_providers=programa or {},
        teto_custo=1.0)


class TestFrotaEconomiaEAmbiente(unittest.TestCase):
    def tearDown(self):
        if getattr(self, "lab", None) is not None:
            apoio.limpar_lab(self.lab)

    # -- 1. API key nao substitui OAuth ---------------------------------------

    def test_api_key_presente_nao_substitui_oauth(self):
        env_host = dict(os.environ)
        env_host["OPENAI_API_KEY"] = "sk-teste-payg-nao-usar-123456"
        # Ambiente sanitizado: a chave NAO entra no processo SSC+...
        limpo = ambiente_sanitizado(env_host)
        self.assertNotIn("OPENAI_API_KEY", limpo)
        # ...e o ambiente global NAO foi apagado/alterado.
        self.assertEqual(env_host["OPENAI_API_KEY"],
                         "sk-teste-payg-nao-usar-123456")
        # Mesmo com a chave PAYG presente no host, sem perfil OAuth da
        # assinatura a invocacao e BLOQUEADA (payg_api = DENY).
        sem_oauth = _entry(terms_profile={})
        fake = FakeProvider({"provedor": "codex", "modelo": "gpt-5-codex",
                             "effort": "alto"}, seed=1)
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(sem_oauth, fake, env=env_host)
        self.assertEqual(fake.chamadas, 0)  # nada foi invocado
        # Com o perfil OAuth da assinatura, passa — e a chave PAYG continua
        # fora do ambiente efetivo do adaptador.
        adaptador = AdaptadorAssinatura(_entry(), fake, env=env_host)
        self.assertNotIn("OPENAI_API_KEY", adaptador.env)

    # -- 2. Billing desconhecido bloqueia antes da invocacao ---------------------

    def test_billing_desconhecido_bloqueia_antes_da_invocacao(self):
        for billing in ("desconhecido", "payg", "prepaid", "extra-usage"):
            with self.subTest(billing=billing):
                entry = _entry(billing_mode=billing)
                self.assertTrue(verificar_economia(entry))
                fake = FakeProvider(
                    {"provedor": "codex", "modelo": "gpt-5-codex",
                     "effort": "alto"}, seed=1)
                with self.assertRaises(PoliticaEconomicaViolada):
                    AdaptadorAssinatura(entry, fake, env={})
                self.assertEqual(fake.chamadas, 0)  # pre-invocacao

    # -- 3. Quota esgotada troca de provedor sem perder linhagem -------------------

    def test_quota_esgotada_troca_provedor_preserva_linhagem(self):
        frota = Frota(frota_inicial())
        self.lab = _lab_frota(
            apoio, frota, programa={"codex/gpt-5-codex": ["falha-quota"]})
        k = self.lab.kernel
        wu = self.lab.router.forjar(
            intencao="implementar peca via frota", criterios={"tipo": "x"},
            tipo="ato", nivel="L2", classe="C1")
        r = executar_com_frota(self.lab, frota, wu,
                               idempotency_key="frota-quota-1")
        self.assertEqual(r.status, "sucesso")
        # Codex marcou quota esgotada; Claude assumiu com NOVA decisao.
        codex = next(e for e in frota.entradas if e.provider_id == "codex")
        self.assertEqual(codex.quota_state, "esgotada")
        self.assertEqual(len(k.decisoes), 2)  # nova RoutingDecision emitida
        attempt = k.attempts[r.resultado.attempt_id]["attempt"]
        self.assertEqual(attempt.executor_resolvido["provedor"], "claude")
        # Sessao, WorkUnit, memoria e causalidade preservados.
        self.assertEqual(attempt.linhagem_id, k.envelope.linhagem_id)
        self.assertEqual(attempt.work_unit_id, wu.work_unit_id)
        k.verificar_integridade()  # cadeia causal integra

    # -- 4. Ausencia de provedor = STOP, nunca PAYG --------------------------------

    def test_sem_provedor_stop_wait_reset_nunca_payg(self):
        esgotada = _entry(provider_id="codex", model_id="gpt-5-codex",
                          quota_state="esgotada",
                          quota_reset="2026-08-01T00:00:00Z")
        payg = _entry(provider_id="openai-payg", model_id="gpt-5",
                      auth_mode="payg-api", billing_mode="payg",
                      variable_cost=0.03)
        frota = Frota([esgotada, payg])
        self.assertEqual(frota.elegiveis(), [])  # PAYG nunca elegivel
        self.lab = _lab_frota(apoio, Frota([esgotada]))
        wu = self.lab.router.forjar(
            intencao="tarefa sem assinatura disponivel",
            criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
        r = executar_com_frota(self.lab, frota, wu,
                               idempotency_key="frota-stop-1")
        self.assertEqual(r.status, STOP_WAIT_RESET)
        self.assertEqual(len(self.lab.kernel.attempts), 0)  # zero invocacao
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(payg, FakeProvider(
                {"provedor": "openai-payg", "modelo": "gpt-5",
                 "effort": "alto"}, seed=1), env={})

    # -- 5. Autor nao aprova a propria entrega critica ------------------------------

    def test_autor_nao_aprova_propria_entrega_critica(self):
        autor = _entry(provider_id="codex", model_id="gpt-5-codex")
        mesmo = _entry(provider_id="codex", model_id="gpt-5-codex")
        revisor = _entry(provider_id="claude", model_id="claude-opus")
        with self.assertRaises(IndependenciaInsuficiente):
            Frota.verificar_independencia(autor, mesmo, "revisor")
        evidencia = Frota.verificar_independencia(autor, revisor, "revisor")
        self.assertTrue(evidencia["provider_distinto"]
                        and evidencia["modelo_distinto"])

    # -- 6. Grok: cached token/ACP, nunca XAI_API_KEY/api.x.ai ------------------------

    def test_grok_cached_token_acp_sem_xai_key(self):
        grok = _entry(provider_id="grok", model_id="grok-build",
                      auth_mode="cached-token",
                      terms_profile={"oauth_profile": "cached:grok",
                                     "endpoint": "grok-build://assinatura"})
        env = {"XAI_API_KEY": "xai-nao-usar-123456"}
        adaptador = AdaptadorAssinatura(grok, FakeProvider(
            {"provedor": "grok", "modelo": "grok-build", "effort": "alto"},
            seed=1), env=env)
        self.assertNotIn("XAI_API_KEY", adaptador.env)  # chave fora
        # api.x.ai e fora do Grok Build: bloqueados.
        for ruim in (
                _entry(provider_id="grok", model_id="grok-4",
                       auth_mode="payg-api", billing_mode="payg",
                       terms_profile={"endpoint": "https://api.x.ai/v1"}),
                _entry(provider_id="grok", model_id="grok-build",
                       auth_mode="subscription-oauth",
                       terms_profile={"oauth_profile": "oauth:grok"}),
                _entry(provider_id="grok", model_id="grok-build",
                       auth_mode="cached-token", canal_oficial=False,
                       terms_profile={"oauth_profile": "cached:grok"})):
            with self.subTest(auth=ruim.auth_mode, canal=ruim.canal_oficial):
                self.assertTrue(verificar_canal(ruim)
                                or verificar_economia(ruim))

    # -- 7. Google e Grok respeitam o nivel de autonomia ----------------------------

    def test_google_grok_respeitam_nivel_de_autonomia(self):
        grok = _entry(provider_id="grok", model_id="grok-build",
                      auth_mode="cached-token",
                      terms_profile={"oauth_profile": "cached:grok"})
        # GROK_SUPERVISED = ALLOW; GROK_UNATTENDED = TERMS_REVIEW_REQUIRED.
        self.assertEqual(verificar_automacao(grok, "supervised"), [])
        self.assertTrue(any("TERMS_REVIEW_REQUIRED" in v for v in
                            verificar_automacao(grok, "unattended")))
        # Google: canal nao-oficial bloqueia; automacao condicional.
        google_pendente = _entry(
            provider_id="google", model_id="gemini-pro",
            automation_permission="terms-review-required",
            terms_profile={"oauth_profile": "oauth:google"})
        self.assertTrue(verificar_automacao(google_pendente))
        google_fora = _entry(provider_id="google", model_id="gemini-pro",
                             canal_oficial=False,
                             terms_profile={"oauth_profile": "oauth:google"})
        self.assertTrue(verificar_canal(google_fora))
        google_ok = _entry(provider_id="google", model_id="gemini-pro",
                           terms_profile={"oauth_profile": "oauth:google"})
        self.assertEqual(verificar_canal(google_ok), [])
        self.assertEqual(verificar_automacao(google_ok), [])

    # -- 8. Catalogo descobre modelos; aliases nao permanentes -----------------------

    def test_catalogo_descobre_modelos_sem_aliases_permanentes(self):
        frota = Frota(frota_inicial())
        declarado = frota.descobrir()
        self.assertIn("gpt-5-codex", declarado["codex"])
        # Sensor de descoberta substitui a leitura declarada: modelo novo
        # aparece sem nenhum alias pre-registrado.
        descoberto = frota.descobrir(
            sensor=lambda p: ["claude-opus-4-8"] if p == "claude"
            else [e.model_id for e in frota._por_provider[p]])
        self.assertEqual(descoberto["claude"], ["claude-opus-4-8"])
        catalogo = catalogo_de_frota(frota)
        self.assertEqual(catalogo.aliases, {})  # zero alias permanente
        # A selecao resolve por capacidade no momento; nao ha apelido fixo.
        escolha = frota.escolher(capacidade="revisao-profunda")
        self.assertEqual(escolha.provider_id, "claude")

    # -- contrato: round-trip e enums fechados da FleetEntry ---------------------------

    def test_fleetentry_roundtrip_e_enums_fechados(self):
        entry = _entry()
        clone = ct.FleetEntry.from_dict(entry.to_dict())
        self.assertEqual(entry, clone)
        with self.assertRaises(ct.FalhaContrato):
            _entry(auth_mode="oauth-magic")  # fora do enum
        with self.assertRaises(ct.FalhaContrato):
            _entry(automation_permission="yolo")  # fora do enum


if __name__ == "__main__":
    unittest.main()
