"""FASE 1.2 — o terceiro ramo do `AdaptadorAssinatura`, medido.

O ato manda: *corrigir, ou declarar com evidencia por que o comportamento
atual esta correto. Medir, nunca presumir.* Esta e a medicao, e a
correcao que ela justifica — que nao e a que o enunciado sugeria.

## 1. O ramo NAO dispara, e isso e por construcao

`frota.AdaptadorAssinatura.__init__` faz, em linhas consecutivas:

    self.env = ambiente_sanitizado(env)      # remove CHAVES_PROIBIDAS ∪ padrao
    ...
    if any(k in self.env for k in CHAVES_PROIBIDAS):   # <- o terceiro ramo

O predicado do guarda (`CHAVES_PROIBIDAS`) e SUBCONJUNTO PROPRIO do
predicado do sanitizador (`CHAVES_PROIBIDAS` ∪ sufixo de credencial).
Logo o ramo e falso para QUALQUER entrada. Medido por exaustao sobre as
oito chaves da lista: **0 de 8 sobrevivem** ao sanitizador.

## 2. E o comportamento atual esta CORRETO — com evidencia

Transformar o ramo em bloqueio de verdade exigiria conferir o ambiente
RECEBIDO em vez do sanitizado. Isso seria uma regressao, e o proprio
modulo diz por que: *"o ambiente global do usuario NAO e modificado —
apenas impedimos a heranca pelo subprocesso"*. Numa estacao que exporte
uma chave PAYG — o caso comum de quem tem conta de API —, toda
construcao legitima do adaptador passaria a levantar. O desenho da P0 e
FILTRAR, e o ramo e a REAUDITORIA do filtro, no mesmo padrao de
`capsula.ambiente_capsula`. O ramo fica como esta.

Medido tambem, e nao presumido: `AdaptadorAssinatura` **nao tem
chamador de producao** em `05_p0/ssc_p0` — so testes o constroem. Em
operacao, hoje, nenhum dos seus tres ramos e percorrido por codigo de
producao; a classe e o portao que a P1+ vai usar.

## 3. O defeito VIVO que a medicao encontrou

A reauditoria quantifica sobre a MESMA `CHAVES_PROIBIDAS` que o
sanitizador usa. Se um nome sair da lista, os dois lados encolhem juntos
e o ramo continua mudo. E nada no acervo prendia o conteudo dessa lista.

MEDIDO nesta missao: removida `GOOGLE_APPLICATION_CREDENTIALS` de
`CHAVES_PROIBIDAS`, as duas suites ficam **793/793 VERDES** — P0 238 e
P1-A 555, zero vermelhos. A chave passa a entrar no ambiente do
adaptador e ninguem ve.

`GOOGLE_APPLICATION_CREDENTIALS` nao e uma escolha arbitraria: das oito
chaves, **sete tambem casam** o padrao de sufixo (`_API_KEY`,
`_AUTH_TOKEN`) e sobreviveriam a perda da lista. Ela e a UNICA protegida
so pela lista — e por isso e a unica cuja remocao e invisivel.

## 4. A correcao, e por que o corpus vem de OUTRA camada

Um teste que iterasse `CHAVES_PROIBIDAS` para provar `CHAVES_PROIBIDAS`
repetiria a tautologia: encolher a lista encolheria o corpus e o teste
seguiria verde. O corpus tem de ser INDEPENDENTE.

Ele existe: `preflight.economia.CHAVES_PAYG_CONHECIDAS`, a lista que a
camada P1-A mantem por conta propria. O precedente e `EspelhoDaPoliticaP0`
(`test_economia.py:23`), que ja espelha a politica economica de uma
camada na outra pelo mesmo motivo.

O QUE ESTES TESTES NAO COBREM, declarado:
- **encolhimento SIMULTANEO das duas listas** nao e pego: o espelho
  compara uma com a outra, e duas remocoes casadas passam. O remedio
  para isso seria uma terceira fonte, e inventar uma seria politica
  nova, nao correcao;
- nao se afirma que as oito chaves sejam as chaves CERTAS: o corpus
  mede consistencia entre camadas, nunca suficiencia da politica.
  Medido e registrado: `OPENAI_KEY`, `ANTHROPIC_KEY`, `XAI_TOKEN`,
  `AWS_SESSION_TOKEN` e `GOOGLE_CLOUD_KEYFILE_JSON` atravessam os dois
  sanitizadores — nenhum casa lista nem sufixo;
- nao se cobre o valor da credencial em lugar nenhum: os testes usam a
  `SENTINELA` do acervo, que nunca foi credencial;
- nada aqui prova comportamento de subprocesso real — a P0 nao invoca
  provedor, e `invocar()` delega a um falso deterministico.
"""

import unittest

from apoio import SENTINELA
from preflight.economia import CHAVES_PAYG_CONHECIDAS
from ssc_p0 import contratos as ct
from ssc_p0.frota import (CHAVES_PROIBIDAS, AdaptadorAssinatura,
                          PoliticaEconomicaViolada, ambiente_sanitizado)
from ssc_p0.frota import _PADRAO_CHAVE_PAYG as PADRAO_P0

# Protegida SO pela lista: o padrao de sufixo nao a alcanca, porque o
# nome nao termina em credencial — termina em CREDENTIALS, que e um
# CAMINHO DE ARQUIVO de credencial. Remove-la da lista era invisivel.
SO_PELA_LISTA = "GOOGLE_APPLICATION_CREDENTIALS"


class ProvedorFalso:
    def invocar(self, *a, **k):
        return {"saida": b"nada"}


def _entrada(**sobre) -> ct.FleetEntry:
    campos = {"provider_id": "prov-a", "model_id": "modelo-x",
              "capability_profile": {}, "auth_mode": "subscription-oauth",
              "billing_mode": "subscription", "quota_state": "disponivel",
              "quota_reset": None, "automation_permission": "allow",
              "terms_profile": {"oauth_profile": "oauth:prov-a"},
              "variable_cost": 0, "papeis_preferidos": [],
              "canal_oficial": True}
    campos.update(sobre)
    return ct.FleetEntry(**campos)


def _adaptador(env) -> AdaptadorAssinatura:
    """Constroi o adaptador REAL — o ponto de chamada, nao a primitiva."""
    return AdaptadorAssinatura(_entrada(), ProvedorFalso(), env=env)


class ListaProibidaPresaPorOutraCamada(unittest.TestCase):
    """O corpus vem da P1-A; o alvo e a P0. Encolher um lado fica vermelho."""

    def test_as_duas_listas_sao_a_mesma_lista(self):
        self.assertEqual({k.lower() for k in CHAVES_PROIBIDAS},
                         set(CHAVES_PAYG_CONHECIDAS))

    def test_nenhum_nome_do_corpus_sobrevive_no_ambiente_do_adaptador(self):
        # O ponto de chamada REAL: o objeto construido, e o dicionario
        # que ele levaria a um subprocesso — nao `ambiente_sanitizado`
        # chamada a seco, que e a primitiva.
        for nome in sorted(CHAVES_PAYG_CONHECIDAS):
            with self.subTest(chave=nome):
                adaptador = _adaptador({"PATH": "/bin",
                                        nome.upper(): SENTINELA})
                self.assertNotIn(nome.upper(), adaptador.env)
                self.assertEqual(adaptador.env.get("PATH"), "/bin")

    def test_ha_nome_no_corpus_que_SO_a_lista_protege(self):
        # DISCRIMINADOR. Sem ele, o teste acima poderia passar de graca
        # pelo padrao de sufixo, e a lista poderia esvaziar sem ruido.
        so_lista = sorted(n.upper() for n in CHAVES_PAYG_CONHECIDAS
                          if not PADRAO_P0.search(n.upper()))
        self.assertIn(SO_PELA_LISTA, so_lista)
        self.assertNotIn(SO_PELA_LISTA, ambiente_sanitizado(
            {SO_PELA_LISTA: SENTINELA}))
        self.assertNotIn(SO_PELA_LISTA,
                         _adaptador({SO_PELA_LISTA: SENTINELA}).env)

    def test_as_outras_sete_seguem_cobertas_pelo_padrao(self):
        # A outra metade da medicao: sete das oito sobrevivem a perda da
        # lista porque o padrao as pega. Registrar isso e o que torna o
        # discriminador acima uma medicao, e nao uma escolha de gosto.
        pelo_padrao = {n.upper() for n in CHAVES_PAYG_CONHECIDAS
                       if PADRAO_P0.search(n.upper())}
        self.assertEqual(len(pelo_padrao), len(CHAVES_PAYG_CONHECIDAS) - 1)


class OTerceiroRamoEReauditoria(unittest.TestCase):
    """Fixa o comportamento CORRETO: filtrar, nunca bloquear."""

    def test_chave_payg_no_ambiente_recebido_nao_bloqueia_a_construcao(self):
        # Se algum dia isto virar bloqueio, toda estacao que exporte uma
        # chave de API para de construir o adaptador. O desenho da P0 e
        # filtrar; o ambiente global do usuario nao e alterado.
        recebido = {"PATH": "/bin", "OPENAI_API_KEY": SENTINELA}
        adaptador = _adaptador(recebido)
        self.assertNotIn("OPENAI_API_KEY", adaptador.env)
        self.assertEqual(recebido["OPENAI_API_KEY"], SENTINELA)

    def test_o_ramo_e_inalcancavel_por_construcao(self):
        # Exaustao sobre a lista inteira: nenhuma chave sobrevive ao
        # sanitizador, logo `any(k in self.env ...)` e falso sempre.
        sobreviventes = [k for k in CHAVES_PROIBIDAS
                         if k in ambiente_sanitizado({k: SENTINELA})]
        self.assertEqual(sobreviventes, [])

    def test_nome_fora_da_lista_e_do_padrao_atravessa(self):
        # Contraprova: o sanitizador nao remove tudo. Sem ela, um
        # sanitizador que devolvesse `{}` passaria em todos os testes
        # acima e ninguem veria.
        adaptador = _adaptador({"PATH": "/bin", "LANG": "pt_BR"})
        self.assertEqual(adaptador.env.get("LANG"), "pt_BR")

    def test_entrada_ilegitima_continua_recusada(self):
        # Contraprova do outro lado: o adaptador nao virou permissivo.
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(_entrada(auth_mode="payg-api"),
                                ProvedorFalso(), env={})


if __name__ == "__main__":
    unittest.main()
