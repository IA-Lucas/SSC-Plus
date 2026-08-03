"""A ponte preflight -> frota, medida contra a evidencia REAL.

O caso que a operacao percorre nao e um dicionario inventado no teste: e
o relatorio que o preflight de fato produziu nesta estacao. Por isso a
classe `RelatorioRealDaP1B` carrega
`07_p1b/evidencias/preflight-20260801T235521Z.json` do disco e mede a
frota que sai DELE — cinco provedores, dois habilitados, tres nao.

Foi essa fixture que pegou o primeiro defeito desta ordem: o codigo lia
`sombra["tier"]` porque esse e o nome do campo na dataclass
`DeclaracaoTier`, e o pipeline emite `sombra["tier_declarado"]`. Contra
um dicionario escrito a mao pelo proprio teste, os dois teriam
concordado — e a chave sairia `None` em operacao sem ninguem notar.

O vizinho recusado: montar o relatorio com `RelatorioPreflight(...)
.to_dict()`. Isso mede a dataclass contra ela mesma. A evidencia em disco
e a unica forma do teste discordar do codigo.

O QUE ESTES TESTES NAO COBREM, declarado:
- **nao provam que a frota resultante funcione**: provam que ela e
  construida com procedencia certa e vetada pelos portoes certos. Que uma
  invocacao chegue ao CLI e materia da ordem do runner;
- **nao cobrem provedor com dois modelos observados em operacao**. O caso
  esta exercido por relatorio sintetico; nenhuma corrida real produziu
  dois — os parsers dedicados de codex e kimi devolvem exatamente um;
- **nao medem `quota_reset`**: nenhuma corrida observou reset, e o campo
  sai `None` sempre;
- `billing_mode` e `variable_cost` vem da especificacao ESTATICA. Nada
  aqui os observa no CLI — e a evidencia em disco tambem nao os observa.
"""

import json
import os
import sys
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", "08_p2"):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import frota_medida as fm  # noqa: E402
from preflight.frota_real import ESPECIFICACOES  # noqa: E402
from ssc_p0 import contratos as ct  # noqa: E402
from ssc_p0.frota import Frota  # noqa: E402

EVIDENCIA_REAL = os.path.join(
    _RAIZ, "07_p1b", "evidencias", "preflight-20260801T235521Z.json")


def relatorio(**kw) -> dict:
    base = {"provider_id": "codex", "resultado": "SHADOW_ELIGIBLE",
            "erros": [], "caminho": None, "versao": "0.145.0",
            "plano": None, "origem_credencial": "subscription-oauth",
            "quota": "desconhecida", "modelos": ["gpt-5.6-sol"],
            "sombra": {"tier_declarado": "ChatGPT Pro 5x"}}
    base.update(kw)
    return base


class VeredictoQueHabilita(unittest.TestCase):

    def uma(self, **kw):
        entradas, descartes = fm.entradas_de(relatorio(**kw),
                                             ESPECIFICACOES["codex"])
        return entradas, descartes

    def test_shadow_eligible_habilita(self):
        entradas, descartes = self.uma()
        self.assertEqual(len(entradas), 1)
        self.assertEqual(descartes, [])

    def test_eligible_habilita(self):
        entradas, _ = self.uma(resultado="ELIGIBLE")
        self.assertEqual(len(entradas), 1)

    def test_supervised_e_blocked_viram_descarte_com_motivo(self):
        for veredito in ("SUPERVISED", "BLOCKED"):
            with self.subTest(veredito=veredito):
                entradas, descartes = self.uma(resultado=veredito)
                self.assertEqual(entradas, [])
                self.assertEqual(len(descartes), 1)
                self.assertIn(veredito, descartes[0]["motivo"])

    def test_veredito_bom_sem_modelo_observado_nao_vira_entrada(self):
        # D5: "model_id descoberto, nunca presumido". Preencher com
        # `modelos_esperados` da especificacao seria presumir exatamente o
        # que a regra proibe — e a especificacao do codex diz `gpt-5`,
        # enquanto o observado foi `gpt-5.6-sol`.
        entradas, descartes = self.uma(modelos=[])
        self.assertEqual(entradas, [])
        self.assertIn("sem modelo observado", descartes[0]["motivo"])

    def test_dois_modelos_observados_viram_duas_entradas(self):
        entradas, _ = self.uma(modelos=["m-1", "m-2"])
        self.assertEqual([e.model_id for e in entradas], ["m-1", "m-2"])


class ProcedenciaDosCampos(unittest.TestCase):
    """Observado nao pode virar declarado, nem o contrario."""

    def uma(self, **kw):
        entradas, _ = fm.entradas_de(relatorio(**kw), ESPECIFICACOES["codex"])
        return entradas[0]

    def test_model_id_e_o_observado_nunca_o_esperado_da_espec(self):
        e = self.uma()
        self.assertEqual(e.model_id, "gpt-5.6-sol")
        self.assertNotIn(e.model_id, ESPECIFICACOES["codex"].modelos_esperados)

    def test_auth_e_canal_saem_da_origem_observada(self):
        e = self.uma(origem_credencial="subscription-oauth")
        self.assertEqual(e.auth_mode, "subscription-oauth")
        self.assertTrue(e.canal_oficial)
        self.assertEqual(e.terms_profile["oauth_profile"], "oauth:codex")

    def test_origem_nao_sondada_vira_desconhecido_e_perde_o_oauth_profile(self):
        # Fail-closed: sem canal provado nao ha `oauth_profile`, e
        # `AdaptadorAssinatura` recusa a invocacao mesmo que o resto passe
        # (adendo §4: chave de API nunca substitui OAuth).
        for origem in ("nao-sondada", "ausente", "payg-api", None):
            with self.subTest(origem=origem):
                e = self.uma(origem_credencial=origem)
                self.assertEqual(e.auth_mode, "desconhecido")
                self.assertFalse(e.canal_oficial)
                self.assertNotIn("oauth_profile", e.terms_profile)

    def test_quota_desconhecida_nao_vira_disponivel(self):
        # `desconhecida` e o valor NORMAL nesta frota: nenhuma corrida ate
        # hoje observou franquia. Converte-la por ausencia de sinal
        # negativo seria o fail-open que a P1-A.3.2 fechou.
        self.assertEqual(self.uma(quota="desconhecida").quota_state,
                         "desconhecida")
        self.assertEqual(self.uma(quota="esgotada").quota_state, "esgotada")
        self.assertEqual(self.uma(quota="disponivel").quota_state,
                         "disponivel")

    def test_quota_fora_do_enum_vira_desconhecida(self):
        self.assertEqual(self.uma(quota="qualquer-coisa").quota_state,
                         "desconhecida")

    def test_billing_e_custo_vem_da_especificacao_estatica(self):
        e = self.uma()
        self.assertEqual(e.billing_mode, ESPECIFICACOES["codex"].billing_mode)
        self.assertEqual(e.variable_cost, 0.0)

    def test_o_veredito_e_o_tier_ficam_registrados_na_entrada(self):
        # Rastreabilidade: a entrada carrega de qual classificacao ela
        # nasceu, para que a evidencia da corrida nao dependa de memoria.
        e = self.uma()
        self.assertEqual(e.terms_profile["veredito_preflight"],
                         "SHADOW_ELIGIBLE")
        self.assertEqual(e.terms_profile["tier_declarado"], "ChatGPT Pro 5x")

    def test_a_entrada_e_um_FleetEntry_validado(self):
        # Enums fechados do D5: valor fora do enum e FalhaContrato, nunca
        # coercao. `validado()` ja rodou dentro de `entradas_de`.
        self.assertIsInstance(self.uma(), ct.FleetEntry)


class NadaSomeDaFrota(unittest.TestCase):
    """Vetado continua na lista; quem exclui e `Frota.elegiveis`."""

    def frota(self, *relatorios):
        return fm.frota_do_preflight(relatorios, ESPECIFICACOES)

    def test_entrada_vetada_permanece_na_lista_e_o_motivo_aparece(self):
        # Filtrar aqui criaria um SEGUNDO portao economico. Dois portoes
        # que precisam concordar sao dois portoes que um dia divergem.
        r = self.frota(relatorio(origem_credencial="nao-sondada"))
        self.assertEqual(len(r["entradas"]), 1)
        self.assertEqual(len(r["vetos"]), 1)
        self.assertTrue(any("desconhecido" in m
                            for m in r["vetos"][0]["motivos"]))

    def test_o_veto_vem_dos_portoes_ratificados_da_P0(self):
        # O texto do motivo e o de `verificar_economia`, nao um texto
        # proprio deste modulo — se ele fosse proprio, seria uma segunda
        # politica economica escrita em outro lugar.
        r = self.frota(relatorio(origem_credencial="nao-sondada"))
        self.assertIn("auth_mode desconhecido = DENY", r["vetos"][0]["motivos"])

    def test_provedor_sem_especificacao_vira_descarte(self):
        r = self.frota(relatorio(provider_id="inventado"))
        self.assertEqual(r["entradas"], [])
        self.assertIn("sem especificacao", r["descartes"][0]["motivo"])

    def test_entrada_aprovada_nao_produz_veto(self):
        # Contraprova: se tudo virasse veto, os testes acima passariam sem
        # medir nada.
        r = self.frota(relatorio())
        self.assertEqual(r["vetos"], [])


class RelatorioRealDaP1B(unittest.TestCase):
    """A evidencia que o preflight produziu nesta estacao, do disco."""

    @classmethod
    def setUpClass(cls):
        with open(EVIDENCIA_REAL, encoding="utf-8") as f:
            cls.evidencia = json.load(f)
        cls.resultado = fm.frota_do_preflight(cls.evidencia["frota"],
                                              ESPECIFICACOES)

    def test_a_evidencia_usada_e_a_de_custo_zero(self):
        # Se um dia esta fixture for trocada por uma corrida que gastou,
        # o teste avisa em vez de aceitar em silencio.
        self.assertEqual(self.evidencia["chamadas_de_modelo"], 0)
        self.assertEqual(self.evidencia["custo_variavel"], 0)

    def test_a_frota_real_habilita_exatamente_codex_e_kimi(self):
        self.assertEqual(sorted(e.provider_id
                                for e in self.resultado["entradas"]),
                         ["codex", "kimi"])

    def test_os_tres_supervised_saem_com_motivo_escrito(self):
        motivos = {d["provider_id"]: d["motivo"]
                   for d in self.resultado["descartes"]}
        self.assertEqual(sorted(motivos), ["claude", "google", "grok"])
        for pid, motivo in motivos.items():
            with self.subTest(provider=pid):
                self.assertIn("SUPERVISED", motivo)

    def test_os_modelos_sao_os_OBSERVADOS_na_corrida(self):
        observados = {e.provider_id: e.model_id
                      for e in self.resultado["entradas"]}
        self.assertEqual(observados,
                         {"codex": "gpt-5.6-sol", "kimi": "kimi-code/k3"})

    def test_o_tier_declarado_chega_a_entrada_pela_chave_certa(self):
        # O defeito que esta fixture pegou: o codigo lia `sombra["tier"]`
        # (nome do campo na dataclass) e o pipeline emite
        # `sombra["tier_declarado"]`. Contra um dicionario escrito a mao no
        # proprio teste, os dois teriam concordado.
        tiers = {e.provider_id: e.terms_profile["tier_declarado"]
                 for e in self.resultado["entradas"]}
        self.assertEqual(tiers, {"codex": "ChatGPT Pro 5x",
                                 "kimi": "Allegretto"})

    def test_nenhuma_entrada_real_e_vetada_pelos_portoes(self):
        self.assertEqual(self.resultado["vetos"], [])

    def test_model_id_e_exatamente_o_que_a_evidencia_registrou(self):
        # Pino contra o relatorio em disco, campo a campo: se o codigo
        # passar a completar `modelos` com a especificacao, o valor deixa
        # de casar com o que a corrida observou.
        do_disco = {r["provider_id"]: list(r["modelos"])
                    for r in self.evidencia["frota"] if r["modelos"]}
        das_entradas = {}
        for e in self.resultado["entradas"]:
            das_entradas.setdefault(e.provider_id, []).append(e.model_id)
        self.assertEqual(das_entradas, do_disco)

    def test_supervised_com_modelo_observado_continua_sem_habilitar(self):
        # A folga que o mutante desta ordem revelou: na evidencia real os
        # tres SUPERVISED tambem estao sem modelo, entao um bug que fizesse
        # SUPERVISED habilitar rota NAO apareceria nesta fixture — os tres
        # cairiam no descarte seguinte, por outro motivo, e o teste ficaria
        # verde pela razao errada.
        #
        # Aqui o relatorio REAL do claude recebe um modelo observado, e so
        # isso. O veredito continua sendo o dele. E hipotese declarada
        # sobre relatorio real, nao dicionario inventado.
        claude = next(r for r in self.evidencia["frota"]
                      if r["provider_id"] == "claude")
        self.assertEqual(claude["resultado"], "SUPERVISED")
        self.assertEqual(claude["modelos"], [])
        com_modelo = dict(claude, modelos=["claude-opus-hipotetico"])

        entradas, descartes = fm.entradas_de(com_modelo,
                                             ESPECIFICACOES["claude"])
        self.assertEqual(entradas, [],
                         "SUPERVISED habilitou rota: teto de especificacao "
                         "nao e autorizacao")
        self.assertIn("SUPERVISED", descartes[0]["motivo"])

    def test_a_frota_da_P0_aceita_as_entradas_e_as_elege(self):
        # Exercicio da interface REAL, nao afirmacao sobre ela: as entradas
        # entram em `Frota`, passam por economia + canal + automacao, e
        # `escolher` devolve uma delas para o papel de autor.
        frota = Frota(self.resultado["entradas"])
        elegiveis = frota.elegiveis(papel="autor")
        self.assertEqual(len(elegiveis), 2)
        escolhida = frota.escolher(capacidade="implementacao", papel="autor")
        self.assertIsNotNone(escolhida)
        self.assertEqual(escolhida.provider_id, "codex")

    def test_independencia_entre_os_dois_e_verificavel(self):
        # Trabalho critico exige autor e revisor com provider E modelo
        # distintos (adendo §7). Com dois provedores na frota, existe par.
        frota = Frota(self.resultado["entradas"])
        codex = frota.escolher(capacidade="implementacao")
        kimi = frota.escolher(capacidade="volume")
        evidencia = Frota.verificar_independencia(codex, kimi, "revisor")
        self.assertTrue(evidencia["provider_distinto"])
        self.assertTrue(evidencia["modelo_distinto"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
