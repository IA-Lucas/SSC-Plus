"""P0-16 `frota.AdaptadorAssinatura` — o ramo que faltava. FASE 3.

A varredura mediu **2 de 3 ramos alcancados**, familia ECONOMIA. O
adaptador e o portao PRE-INVOCACAO: ele existe para que nenhuma chamada
saia sem que a politica economica imutavel tenha dito sim.

O CASO QUE OCORRE. Sao tres recusas, todas na construcao — antes de o
objeto existir, e portanto antes de qualquer invocacao:
1. vetos de economia/canal/automacao (custo variavel acima do teto ZERO,
   auth payg, billing payg/prepaid/extra-usage, canal fora do oficial);
2. perfil OAuth AUSENTE numa entrada que declara canal de assinatura —
   e a regra que diz, com todas as letras, que chave de API NUNCA
   substitui o OAuth. Este era o ramo faltante;
3. chave PAYG visivel no ambiente que o adaptador recebeu.

A recusa na CONSTRUCAO e o que importa: um adaptador que so recusasse
em `invocar()` ja teria sido guardado em alguma estrutura, e bastaria um
caminho que o chamasse por outra porta.

O QUE ESTES TESTES NAO COBREM, declarado:
- `invocar()` delega ao provedor falso deterministico; nada aqui prova
  comportamento de provedor real, e a P0 nao invoca nenhum;
- a lista `CHAVES_PROIBIDAS` e enumerada, mais o padrao de sufixo: uma
  chave com outro nome e fora do padrao passa pela sanitizacao;
- nao se afirma que `ambiente_sanitizado` cubra toda forma de vazamento
  — o guarda equivalente da P1-A tem cobertura propria.
"""

import unittest

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0 import contratos as ct
from ssc_p0.frota import (AdaptadorAssinatura, CHAVES_PROIBIDAS,
                          PoliticaEconomicaViolada)


class ProvedorFalso:
    def invocar(self, *a, **k):
        return {"saida": b"nada"}


def entrada(**sobre) -> ct.FleetEntry:
    campos = {"provider_id": "prov-a", "model_id": "modelo-x",
              "capability_profile": {}, "auth_mode": "subscription-oauth",
              "billing_mode": "subscription", "quota_state": "disponivel",
              "quota_reset": None, "automation_permission": "allow",
              "terms_profile": {"oauth_profile": "oauth:prov-a"},
              "variable_cost": 0, "papeis_preferidos": [],
              "canal_oficial": True}
    campos.update(sobre)
    return ct.FleetEntry(**campos)


class RecusasDoAdaptador(unittest.TestCase):

    def _adaptador(self, entry=None, env=None):
        return AdaptadorAssinatura(entry or entrada(), ProvedorFalso(),
                                   env=env if env is not None else {})

    def test_perfil_oauth_ausente_e_recusado(self):
        # O ramo que faltava: a entrada declara canal de assinatura e nao
        # tem perfil OAuth. Chave de API NUNCA substitui o OAuth.
        for modo in ("subscription-oauth", "cached-token", "acp"):
            with self.subTest(auth_mode=modo):
                entry = entrada(auth_mode=modo, terms_profile={})
                if modo != "subscription-oauth":
                    entry = entrada(auth_mode=modo, terms_profile={},
                                    provider_id="grok",
                                    automation_permission="supervised")
                with self.assertRaises(PoliticaEconomicaViolada) as ctx:
                    self._adaptador(entry)
                self.assertIn("perfil OAuth", str(ctx.exception))

    def test_custo_variavel_acima_do_teto_e_recusado(self):
        with self.assertRaises(PoliticaEconomicaViolada) as ctx:
            self._adaptador(entrada(variable_cost=0.01))
        self.assertIn("external_variable_cost_cap = 0", str(ctx.exception))

    def test_auth_payg_e_billing_pago_sao_recusados(self):
        casos = {"auth_mode": "payg-api", "billing_mode": "payg"}
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                with self.assertRaises(PoliticaEconomicaViolada):
                    self._adaptador(entrada(**{campo: valor}))

    def test_auth_desconhecida_e_recusada(self):
        # Ausencia de evidencia = unknown = DENY, nunca "provavelmente ok".
        with self.assertRaises(PoliticaEconomicaViolada) as ctx:
            self._adaptador(entrada(auth_mode="desconhecido"))
        self.assertIn("desconhecido", str(ctx.exception))

    def test_a_chave_payg_do_ambiente_e_filtrada_e_nao_bloqueia(self):
        # MEDIDO, e nao suposto: em operacao a chave nao chega a
        # disparar o terceiro ramo — `ambiente_sanitizado` roda ANTES e
        # ja a remove. O comportamento da P0 e FILTRAR, e este teste
        # fixa isso para que ninguem o confunda com bloqueio.
        adaptador = self._adaptador(
            env={"PATH": "/bin", "OPENAI_API_KEY": "valor-ficticio"})
        self.assertNotIn("OPENAI_API_KEY", adaptador.env)
        self.assertEqual(adaptador.env.get("PATH"), "/bin")

    def test_a_reauditoria_do_ambiente_dispara_se_o_sanitizador_regredir(self):
        # O terceiro ramo e uma REAUDITORIA do proprio sanitizador — o
        # mesmo desenho de `capsula.ambiente_capsula`, que reaudita o
        # que produziu. Enquanto o sanitizador funciona, ele nao dispara;
        # o caso que ele existe para pegar e a REGRESSAO do sanitizador,
        # e e essa que se encena aqui, de forma declarada.
        import ssc_p0.frota as modulo
        original = modulo.ambiente_sanitizado
        modulo.ambiente_sanitizado = lambda env: dict(env or {})
        try:
            for chave in sorted(CHAVES_PROIBIDAS)[:3]:
                with self.subTest(chave=chave):
                    with self.assertRaises(PoliticaEconomicaViolada) as ctx:
                        self._adaptador(env={chave: "valor-ficticio"})
                    self.assertIn("ambiente nao sanitizado",
                                  str(ctx.exception))
        finally:
            modulo.ambiente_sanitizado = original
        # O patch nao pode vazar: a construcao legitima volta a passar.
        self._adaptador(env={"OPENAI_API_KEY": "valor-ficticio"})

    def test_o_valor_da_chave_nunca_aparece_no_erro(self):
        # A recusa nao pode virar canal de vazamento.
        import ssc_p0.frota as modulo
        original = modulo.ambiente_sanitizado
        modulo.ambiente_sanitizado = lambda env: dict(env or {})
        try:
            with self.assertRaises(PoliticaEconomicaViolada) as ctx:
                self._adaptador(env={"OPENAI_API_KEY": "SENTINELA-FICTICIA"})
        finally:
            modulo.ambiente_sanitizado = original
        self.assertNotIn("SENTINELA-FICTICIA", str(ctx.exception))

    def test_a_recusa_acontece_na_CONSTRUCAO(self):
        # Se so recusasse em `invocar()`, o adaptador ja estaria guardado
        # em alguma estrutura e bastaria uma porta que o chamasse de
        # outro jeito. Aqui o objeto nem chega a existir.
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(entrada(variable_cost=1), ProvedorFalso(),
                                env={})

    def test_entrada_legitima_constroi_e_sanitiza_o_ambiente(self):
        # Contraprova: sem ela, um adaptador que recusasse sempre passaria
        # em todos os testes acima. E o ambiente do adaptador nao pode
        # carregar a chave que ele recebeu.
        adaptador = AdaptadorAssinatura(entrada(), ProvedorFalso(),
                                        env={"PATH": "/bin"})
        self.assertEqual(adaptador.env.get("PATH"), "/bin")
        self.assertEqual(adaptador.entry.provider_id, "prov-a")
        self.assertNotIn("OPENAI_API_KEY", adaptador.env)


if __name__ == "__main__":
    unittest.main()
