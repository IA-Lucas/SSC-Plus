"""Os enums de AUTORIZACAO, presos pelo caminho que autoriza — P1-A.3.9.

ORDEM 1 do ato, por CONSEQUENCIA e nao por tamanho: `AUTOMATION_
PERMISSIONS` e `AUTH_MODES` sao controle de autorizacao. Membro que some
sem vermelho aqui muda o que o sistema **PERMITE**, nao o que ele relata.

## Os tres membros SEM EXERCICIO, medidos na varredura de listas

| lista | membro | vermelhos ANTES |
|---|---|---|
| `contratos.AUTOMATION_PERMISSIONS` | `deny` | **0** |
| `contratos.AUTH_MODES` | `acp` | **0** |
| `contratos.AUTH_MODES` | `local` | **0** |

E o que cada um custava, em comportamento:

- **`deny` fora do enum**: `FleetEntry.validate` passa a RECUSAR a
  entrada, e com isso o ramo `automation_permission == "deny"` de
  `verificar_automacao` fica INALCANCAVEL — a unica recusa categorica de
  automacao do adendo deixa de ter entrada possivel;
- **`acp` fora do enum**: e o modo que AUTORIZA o Grok Build
  (`verificar_canal` exige `cached-token` ou `acp`); sem ele, metade da
  autorizacao do grok fica inalcancavel;
- **`local` fora do enum**: `local` e o unico modo de assinatura ISENTO
  da exigencia de `oauth_profile` no portao pre-invocacao. Sem ele, a
  isencao nao tem entrada.

## O CASO QUE OCORRE, e o vizinho recusado

O vizinho — e o que a suite ja fazia — e chamar `verificar_automacao(e)`
e `verificar_canal(e)` **a seco** e conferir a lista de vetos. Aqui os
membros sao exercidos pelos DOIS caminhos por onde a autorizacao passa em
operacao:

1. **selecao** — `Frota.escolher` / `Frota.elegiveis`, que e quem decide
   se a assinatura entra na rodada;
2. **portao pre-invocacao** — `AdaptadorAssinatura.__init__`, que levanta
   `PoliticaEconomicaViolada` ANTES de qualquer invocacao.

Vetar na primitiva e nao vetar na selecao seria exatamente o achado N4
(*primitiva corrigida nao cobre ponto de chamada*).

## CORPUS NAO DERIVADO DA LISTA

Nenhuma assercao de vinculo itera `AUTOMATION_PERMISSIONS` ou
`AUTH_MODES`. Cada membro esta escrito a mao, com o efeito que lhe cabe.
Iterar a lista para provar a lista fica VERDE com o membro fora — foi
assim que `TERMINAIS_WORK_UNIT` passou por presa e e a familia do
MAJOR #3.

## O QUE ESTES TESTES NAO COBREM, declarado

- **remocao do membro JUNTO com o seu ramo consumidor** nao e pega: quem
  apagar `if entry.automation_permission == "deny"` junto com o valor
  passa nos dois. Limite estrutural, o mesmo da FASE 1.2 da P1-A.3.8;
- **nao se afirma que a POLITICA esteja certa** — mede-se que cada membro
  tem efeito exercido, jamais que `deny` deva negar ou que `acp` deva
  autorizar;
- **`supervised`, `allow`, `terms-review-required`, `subscription-oauth`,
  `cached-token`, `payg-api` e `desconhecido` ja prendiam** antes deste
  arquivo e nao sao re-provados aqui; o alvo sao os tres que nao prendiam;
- **`modo_execucao` so e exercido em `supervised` e `unattended`**; nao ha
  afirmacao sobre outros modos;
- **nada aqui exercita CLI, rede ou provedor real** — o executor e o
  `FakeProvider` deterministico, como no resto da P0.
"""

import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
from ssc_p0 import contratos as ct
from ssc_p0.frota import (AdaptadorAssinatura, Frota,
                          PoliticaEconomicaViolada)
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


def _falso(entry):
    return FakeProvider({"provedor": entry.provider_id,
                         "modelo": entry.model_id, "effort": "alto"}, seed=1)


class DenyNegaAutomacaoNosDoisCaminhos(unittest.TestCase):
    """`deny` preso pela SELECAO e pelo PORTAO, nao pela primitiva."""

    def test_assinatura_com_deny_nao_e_escolhida_pela_frota(self):
        # Caminho 1: a selecao. E aqui que a assinatura entra ou nao
        # entra na rodada, e `deny` precisa mante-la fora.
        frota = Frota([_entry(automation_permission="deny")])
        self.assertEqual(frota.elegiveis(), [])
        self.assertIsNone(frota.escolher())

    def test_a_mesma_assinatura_com_allow_E_escolhida(self):
        # CONTRAPROVA: sem ela, uma frota que nunca escolhesse ninguem
        # passaria no teste acima e a suite ficaria verde com a selecao
        # quebrada.
        frota = Frota([_entry(automation_permission="allow")])
        escolhida = frota.escolher()
        self.assertIsNotNone(escolhida)
        self.assertEqual(escolhida.automation_permission, "allow")

    def test_o_portao_pre_invocacao_recusa_deny(self):
        # Caminho 2: mesmo que alguem contorne a selecao e construa o
        # adaptador a mao, a recusa acontece ANTES de qualquer invocacao.
        entry = _entry(automation_permission="deny")
        with self.assertRaises(PoliticaEconomicaViolada) as ctx:
            AdaptadorAssinatura(entry, _falso(entry))
        self.assertIn("deny", str(ctx.exception))

    def test_o_portao_deixa_passar_a_mesma_assinatura_com_allow(self):
        # CONTRAPROVA do portao: um portao que recusasse tudo passaria
        # no teste acima.
        entry = _entry(automation_permission="allow")
        self.assertIsNotNone(AdaptadorAssinatura(entry, _falso(entry)))

    def test_deny_nega_mesmo_em_modo_supervisionado(self):
        # `deny` e categorico: nao depende de `modo_execucao`, ao
        # contrario de TERMS_REVIEW_REQUIRED do grok. Escrito a parte
        # porque e a propriedade que separa os dois.
        entry = _entry(automation_permission="deny")
        for modo in ("supervised", "unattended"):
            with self.subTest(modo=modo):
                frota = Frota([entry])
                self.assertEqual(frota.elegiveis(modo_execucao=modo), [])


class AcpAutorizaOGrokBuild(unittest.TestCase):
    """`acp` preso pela selecao real, nao por `verificar_canal` a seco."""

    @staticmethod
    def _grok(**sobre):
        base = dict(provider_id="grok", model_id="grok-build",
                    terms_profile={"oauth_profile": "acp:grok",
                                   "endpoint": "grok-build://assinatura"})
        base.update(sobre)
        return _entry(**base)

    def test_grok_por_acp_e_escolhido_pela_frota(self):
        # O caso que ocorre: e por `acp` que o Grok Build entra. Se o
        # valor sair do enum, esta assinatura deixa de existir.
        escolhida = Frota([self._grok(auth_mode="acp")]).escolher()
        self.assertIsNotNone(escolhida)
        self.assertEqual(escolhida.auth_mode, "acp")

    def test_grok_por_oauth_de_assinatura_NAO_e_escolhido(self):
        # CONTRAPROVA que separa os modos: o adendo admite `cached-token`
        # e `acp` para o grok, e recusa os demais. Sem este par, uma
        # `verificar_canal` que aprovasse tudo passaria no teste acima.
        self.assertIsNone(
            Frota([self._grok(auth_mode="subscription-oauth")]).escolher())

    def test_grok_por_acp_atravessa_o_portao_pre_invocacao(self):
        # O segundo caminho, para `acp`: `acp` esta entre os modos que
        # EXIGEM perfil OAuth, e com o perfil presente o portao deixa
        # passar.
        entry = self._grok(auth_mode="acp")
        self.assertIsNotNone(AdaptadorAssinatura(entry, _falso(entry)))

    def test_grok_por_acp_SEM_perfil_e_recusado_no_portao(self):
        # E a outra metade da mesma regra: `acp` sem perfil OAuth e
        # bloqueado. E o ramo que distingue `acp` de `local`.
        entry = self._grok(auth_mode="acp", terms_profile={})
        with self.assertRaises(PoliticaEconomicaViolada) as ctx:
            AdaptadorAssinatura(entry, _falso(entry))
        self.assertIn("OAuth", str(ctx.exception))


class LocalEOModoIsentoDePerfilOAuth(unittest.TestCase):
    """`local` preso pela ISENCAO que so ele tem no portao."""

    def test_modelo_local_sem_perfil_oauth_atravessa_o_portao(self):
        # O caso que ocorre, e a razao de `local` existir no enum: um
        # modelo local nao tem OAuth de assinatura para apresentar. Se o
        # valor sair da lista, a isencao fica sem entrada possivel.
        entry = _entry(provider_id="local-llama", model_id="llama-local",
                       auth_mode="local", billing_mode="local-free",
                       terms_profile={})
        self.assertIsNotNone(AdaptadorAssinatura(entry, _falso(entry)))

    def test_assinatura_oauth_sem_perfil_e_recusada_no_mesmo_portao(self):
        # CONTRAPROVA: sem ela, um portao que nao exigisse perfil de
        # ninguem passaria no teste acima e a isencao de `local` nao
        # significaria nada.
        entry = _entry(auth_mode="subscription-oauth", terms_profile={})
        with self.assertRaises(PoliticaEconomicaViolada) as ctx:
            AdaptadorAssinatura(entry, _falso(entry))
        self.assertIn("OAuth", str(ctx.exception))

    def test_modelo_local_e_escolhido_pela_frota(self):
        # O caminho da selecao para `local`: custo variavel zero e
        # billing local-free nao produzem veto economico.
        escolhida = Frota([_entry(provider_id="local-llama",
                                  model_id="llama-local", auth_mode="local",
                                  billing_mode="local-free",
                                  terms_profile={})]).escolher()
        self.assertIsNotNone(escolhida)
        self.assertEqual(escolhida.auth_mode, "local")


class OsValoresForaDoEnumContinuamRecusados(unittest.TestCase):
    """Guarda anti-enum-decorativo, para os dois campos desta correcao."""

    def test_permissao_de_automacao_fora_da_lista_e_recusada(self):
        with self.assertRaises(ct.FalhaContrato):
            _entry(automation_permission="pode-tudo")

    def test_modo_de_autenticacao_fora_da_lista_e_recusado(self):
        with self.assertRaises(ct.FalhaContrato):
            _entry(auth_mode="oauth-magico")


if __name__ == "__main__":
    unittest.main()
