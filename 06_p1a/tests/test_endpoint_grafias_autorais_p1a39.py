"""As onze grafias de endpoint, presas por corpus AUTORAL — P1-A.3.9.

ORDEM 3 do ato, e o achado mais desconfortavel da varredura [15/N]:
o defeito esta na correcao `[9/N]` **desta mesma missao**.

## O DEFEITO, medido

`test_config_real_p1a39.py:197` — `test_host_payg_plantado_em_cada_
grafia_e_acusado` — foi escrito como controle positivo de `P1A-13`. Ele
itera a lista que deveria provar:

    for grafia in sorted(_CHAVES_ENDPOINT):

Tirar uma grafia de `_CHAVES_ENDPOINT` **encolhe o laco junto**, e o
teste segue verde. E a familia do MAJOR #3 na forma pura — a mesma que o
docstring de `[13/N]` declara ter encontrado e desfeito na sua propria
primeira versao, e que a regra (b) do ato existe para impedir.

A consequencia foi medida, membro a membro, e nao suposta: das onze
grafias, **`base_url` e `baseurl` nao prendiam NADA**. As outras nove sao
presas por um teste ANTERIOR e autoral —
`test_estabilizacao_p1a1.test_grafias_de_endpoint_recebem_o_mesmo_
tratamento`, cujo corpus esta em MAIUSCULAS e escrito a mao —, e esse
corpus **nao inclui as duas**.

E `base_url` e justamente:

- a grafia que a missao `[9/N]` foi investigar;
- **a unica que existe de verdade nesta estacao** —
  `~/.kimi-code/config.toml` carrega tres.

O guarda que auditaria o unico endpoint real do laboratorio era o unico
sem exercicio.

## O REMEDIO: corpus AUTORAL, e o espelho que denuncia divergencia

`GRAFIAS` abaixo e escrita a mao neste arquivo. Ela **nao e importada**
de `preflight.economia`: e uma segunda fonte, no espirito de
`EspelhoDaPoliticaP0`. Encolher `_CHAVES_ENDPOINT` deixa a lista de
producao menor que o corpus autoral, e o teste que planta cada grafia
fica vermelho — porque a grafia removida deixa de ser acusada.

O espelho tambem falha para o outro lado: grafia ACRESCENTADA em
producao sem entrada aqui fica vermelha, o que a varredura de listas
declarou nao medir.

## O CASO QUE OCORRE, e o vizinho recusado

O vizinho e plantar num dicionario de brinquedo. O caso que ocorre e a
config REAL do provedor, com o valor trocado por host PAYG — e e o que
`ConfiguracaoRealComGrafiaPlantada` faz, com `_presentes()`.

Mas a config real e propriedade da ESTACAO, nao do repositorio: numa
maquina sem nenhum provedor instalado aquele teste pularia, e um guarda
que pula nao prende nada. Por isso a mesma propriedade e exercida
**duas** vezes — sobre a config real E sobre um dicionario sintetico —, e
e a segunda que garante a reversao vermelha em qualquer maquina. Declarar
isso e melhor que fingir que a estacao e o mundo.

## ACHADO AO MEDIR A REVERSAO: onze grafias, DEZ tokens

A reversao membro a membro devolveu **1 vermelho** para `base_url` e
**1** para `baseurl`, contra 8 a 12 das demais. Investigado, e a resposta
muda o que "presa" significa aqui: `auditar_config` compara **nomes
NORMALIZADOS** (`_normalizar_nome` remove tudo que nao e alfanumerico), e

    "base_url"  ->  "baseurl"
    "baseurl"   ->  "baseurl"

As duas grafias sao **o mesmo token**. `_CHAVES_ENDPOINT` tem onze
entradas e `_CHAVES_ENDPOINT_NORMALIZADAS` tem **dez**.

A consequencia e dura e esta declarada: **nenhum teste de comportamento
pode prender `base_url` ou `baseurl` isoladamente**, porque remover uma
delas nao muda comportamento nenhum — a outra cobre o mesmo token. O
unico vinculo possivel e o de DECLARACAO, e e o espelho autoral que o
faz. Chamar isso de "exercicio" seria a mentira que a regra (a) existe
para impedir.

`AsOnzeGrafiasSaoDezTokens` fixa o fato pelo nome, no padrao de
`OQueEVigiadoMasNaoEAuditado`: se a normalizacao mudar, ou se o par
deixar de colapsar, fica vermelho e alguem olha.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nao corrigem o teste tautologico** de `test_config_real_p1a39.py:197`
  — ele continua no acervo, verde e inutil como vinculo. Removê-lo e
  alteracao de outro arquivo de teste, e o ato desta ordem e prender as
  grafias; fica REGISTRADO como remedio pendente;
- **nao afirmam que as onze grafias sejam as CERTAS**: mede-se que cada
  uma tem efeito, jamais que a cobertura de grafias esteja completa. Uma
  decima segunda grafia usada por algum CLI real nao seria vista;
- **`base_url` e `baseurl` NAO sao exercidas isoladamente**, pelo motivo
  medido acima: sao o mesmo token normalizado. O vinculo delas e de
  declaracao, e so. Chamar de "presas" sem esta ressalva seria inflar a
  medicao;
- **profundidade**: o dicionario sintetico e raso; o aninhamento e
  exercido pelo teste do kimi em `test_config_real_p1a39.py`, que este
  arquivo nao substitui;
- **remocao SIMULTANEA da grafia em producao e aqui** passa;
- **nada aqui invoca CLI, rede ou provedor** — so leitura de config e
  dicionarios em memoria.
"""

import os
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
from leitores_config import FONTES, config_persistida
from preflight.economia import (ConfigPaygPersistida, _CHAVES_ENDPOINT,
                                _CHAVES_ENDPOINT_NORMALIZADAS,
                                _normalizar_nome, auditar_config)

# Host PAYG plantado. Nao e credencial e nunca foi: endereco publico, e
# esta na propria `_ENDPOINTS_PAYG`.
HOST_PAYG_PLANTADO = "https://api.openai.com/v1"

# CORPUS AUTORAL — escrito a mao, NAO importado de `_CHAVES_ENDPOINT`.
# E a segunda fonte: se a lista de producao encolher, esta nao encolhe
# junto, e o vinculo aparece como vermelho.
GRAFIAS = (
    "api_base",
    "api_base_url",
    "api_endpoint",
    "api_url",
    "base_url",
    "base_url_override",
    "baseurl",
    "endpoint",
    "host",
    "server",
    "url",
)


def _fonte_existe(provider_id: str) -> bool:
    _tipo, caminho = FONTES[provider_id]
    return os.path.exists(os.path.expanduser(caminho))


def _presentes() -> list:
    return sorted(p for p in FONTES if _fonte_existe(p))


def _acusa_payg(config: dict) -> bool:
    return ConfigPaygPersistida in [type(v) for v in auditar_config(config)]


class GrafiaSinteticaEAcusada(unittest.TestCase):
    """A metade que roda em QUALQUER maquina, sem depender da estacao."""

    def test_cada_grafia_autoral_com_host_payg_e_acusada(self):
        # O vinculo. Uma grafia que saia de `_CHAVES_ENDPOINT` deixa de
        # ser acusada aqui, e o corpus autoral nao encolhe junto.
        for grafia in GRAFIAS:
            with self.subTest(grafia=grafia):
                self.assertTrue(_acusa_payg({grafia: HOST_PAYG_PLANTADO}),
                                f"grafia {grafia!r} com host PAYG nao acusada")

    def test_a_mesma_grafia_com_host_da_assinatura_NAO_e_acusada(self):
        # CONTRAPROVA: uma auditoria que acusasse qualquer valor passaria
        # no teste acima, e o guarda bloquearia canal legitimo.
        for grafia in GRAFIAS:
            with self.subTest(grafia=grafia):
                self.assertFalse(
                    _acusa_payg({grafia: "https://api.kimi.com/v1"}),
                    f"grafia {grafia!r} com host de assinatura foi acusada")

    def test_chave_que_nao_e_endpoint_nao_dispara(self):
        # CONTRAPROVA do outro lado: se qualquer chave com um host PAYG
        # disparasse, a lista de grafias seria decoracao.
        self.assertFalse(_acusa_payg({"comentario": HOST_PAYG_PLANTADO}))


class OEspelhoDenunciaDivergencia(unittest.TestCase):
    """Corpus autoral e lista de producao, presos um ao outro."""

    def test_o_corpus_autoral_e_a_lista_de_producao_coincidem(self):
        # Falha nos DOIS sentidos: grafia removida de producao, ou
        # grafia acrescentada sem entrada no corpus autoral.
        self.assertEqual(set(GRAFIAS), set(_CHAVES_ENDPOINT))

    def test_o_corpus_autoral_nao_esta_vazio(self):
        # Guarda anti-corpus-vazio: um `GRAFIAS = ()` satisfaria todo
        # laco acima em silencio.
        self.assertGreaterEqual(len(GRAFIAS), 11)
        self.assertEqual(len(set(GRAFIAS)), len(GRAFIAS))


class AsOnzeGrafiasSaoDezTokens(unittest.TestCase):
    """O buraco declarado pelo nome, em vez de escondido no corpus.

    Medido na reversao desta correcao: a auditoria compara nomes
    NORMALIZADOS, e o par `base_url`/`baseurl` colapsa num token so. Se
    isso mudar — para qualquer lado — fica vermelho aqui.
    """

    def test_o_par_base_url_e_baseurl_colapsa_no_mesmo_token(self):
        self.assertEqual(_normalizar_nome("base_url"),
                         _normalizar_nome("baseurl"))

    def test_onze_grafias_produzem_exatamente_dez_tokens(self):
        self.assertEqual(len(_CHAVES_ENDPOINT), 11)
        self.assertEqual(len(_CHAVES_ENDPOINT_NORMALIZADAS), 10)

    def test_as_demais_grafias_NAO_colapsam_entre_si(self):
        # CONTRAPROVA: se a normalizacao fosse agressiva demais, varias
        # grafias virariam um token so e a lista seria decoracao.
        restantes = [g for g in GRAFIAS if g not in ("base_url", "baseurl")]
        tokens = [_normalizar_nome(g) for g in restantes]
        self.assertEqual(len(set(tokens)), len(tokens))


class ConfiguracaoRealComGrafiaPlantada(unittest.TestCase):
    """A metade forte: a config REAL do provedor, nao um brinquedo."""

    def _com_campo(self, provider_id: str, chave: str, valor):
        real = dict(config_persistida(provider_id) or {})
        real[chave] = valor
        return real

    def test_cada_grafia_plantada_na_config_real_e_acusada(self):
        presentes = _presentes()
        if not presentes:
            self.skipTest("nenhuma config de provedor nesta estacao — a "
                          "propriedade NAO e verificavel aqui, e o skip "
                          "existe para dizer isso alto")
        for provider_id in presentes:
            for grafia in GRAFIAS:
                with self.subTest(provider=provider_id, grafia=grafia):
                    self.assertTrue(
                        _acusa_payg(self._com_campo(provider_id, grafia,
                                                    HOST_PAYG_PLANTADO)),
                        f"{provider_id}/{grafia} nao acusado")

    def test_a_config_real_intocada_nao_e_acusada(self):
        # CONTRAPROVA na forma real: as configs desta estacao sao de
        # assinatura. Se a auditoria acusasse alguma delas SEM plantio,
        # o teste acima nao provaria nada.
        presentes = _presentes()
        if not presentes:
            self.skipTest("nenhuma config de provedor nesta estacao")
        for provider_id in presentes:
            with self.subTest(provider=provider_id):
                self.assertFalse(
                    _acusa_payg(dict(config_persistida(provider_id) or {})),
                    f"config real de {provider_id} acusada sem plantio")


if __name__ == "__main__":
    unittest.main()
