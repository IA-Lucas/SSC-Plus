"""A auditoria de config contra a config REAL desta estacao — P1-A.3.9.

MECANISMO (d) da FASE 2 da P1-A.3.8: *propriedade afirmada depende de
algo NAO exercido*. Guarda `P1A-13`, e a linha da remedicao e literal:

    todos os ramos alcancados, mas a indeterminacao declarada na §3.4 da
    varredura segue viva: NAO ESTA CONFIRMADO que `~/.gemini/settings.
    json` use `base_url`. O guarda pode estar auditando uma chave que a
    config real nao tem.
    Remedio: auditar a config do google e confirmar a chave.

## A resposta MEDIDA, e ela nao e a que a pergunta esperava

Lendo o disco desta estacao, campo a campo, sem invocar CLI e sem abrir
rede:

- **`~/.gemini/settings.json` NAO tem `base_url`** — nem nenhuma das
  onze grafias de `_CHAVES_ENDPOINT`. Os campos de topo sao `general`,
  `hooks`, `ide` e `security`. A suspeita da §3.4 estava certa para o
  google;
- **mas a chave EXISTE, e num provedor que ninguem tinha olhado:**
  `~/.kimi-code/config.toml` carrega **tres** `base_url` —
  `providers.managed:kimi-code.base_url`,
  `services.moonshot_search.base_url` e
  `services.moonshot_fetch.base_url` —, todas apontando para
  `api.kimi.com`.

Ou seja: o guarda **tem caso que ocorre**, ele so nao estava no provedor
que a pergunta citava. E o caso que ocorre e o LEGITIMO — `api.kimi.com`
e o canal da assinatura, nao um host PAYG —, de modo que a auditoria
corretamente NAO acusa. O que estava indeterminado deixa de estar: a
auditoria de endpoint le, hoje, tres campos reais e decide sobre eles.

O que NAO se afirma: QUAL chave o gemini usaria para um endpoint
alternativo continua nao confirmado, e responder isso exige fonte
externa. A diferenca e que a pergunta deixou de ser sobre a existencia
do objeto — o objeto existe, medido, em outro provedor.

## O ACHADO NOVO desta medicao, que nao e corrigido aqui

`contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO` vigia SEIS caminhos;
`leitores_config.FONTES` audita CINCO. O sexto e
`~/.codex/config.toml`, e ele nunca e lido por `auditar_config`. Ele
existe nesta estacao e carrega `service_tier`, `model` e
`mcp_servers.*.url` — inclusive uma chave de endpoint.

Pior: o teste que afirma o acoplamento entre as duas listas
(`test_contencao_atribuicao_p1a37.test_a_lista_vigiada_cobre_as_fontes_
que_a_auditoria_le`) **acrescenta o caminho ao corpus a mao**, com o
comentario `# segunda fonte`, para que a igualdade feche. E a familia do
MAJOR #3 na forma pura: o teste AFIRMA a cobertura em vez de EXERCER a
relacao real.

**Nao e corrigido nesta missao**: acrescentar uma fonte a
`leitores_config.FONTES` alarga a superficie da auditoria economica e
pode produzir BLOCKED novo em operacao — e alteracao de POLITICA, que o
ato desta missao proibe. O que se faz aqui e trocar a excecao ESCONDIDA
por uma declaracao MEDIDA: `OQueEVigiadoMasNaoEAuditado` fixa o buraco
pelo nome, e fica vermelho no dia em que ele mudar de tamanho, para
qualquer lado.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nenhum VALOR de config e comparado ou registrado** — so nomes de
  campo, caminhos e o HOST de uma URL, que e o que `auditar_config` ja
  publica pelo `_host_de`;
- **a config desta estacao nao e a de outra**: os testes que dependem de
  uma fonte presente sao PULADOS quando ela nao existe, nunca verdes por
  ausencia;
- **fonte NAO LIDA e resultado legitimo** (achado N2): `~/.grok` em
  SQLite ou permissao negada produzem o marcador, e isso e medido, nao
  reprovado;
- **nao se afirma que as onze grafias sejam suficientes** — mede-se
  quais aparecem, jamais que nao exista uma decima segunda;
- **nada aqui invoca CLI, abre rede ou consulta documentacao.**
"""

import os
import re
import sys
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
import leitores_config
from leitores_config import CHAVE_FONTE_NAO_LIDA, FONTES, config_persistida
from preflight.economia import (ConfigNaoLida, ConfigPaygPersistida,
                                _achatar, _CHAVES_ENDPOINT,
                                _CHAVES_ENDPOINT_NORMALIZADAS,
                                _ENDPOINTS_PAYG, _host_de, auditar_config)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

# Host PAYG usado como valor PLANTADO. Nao e credencial e nunca foi:
# e um endereco publico, e esta na propria `_ENDPOINTS_PAYG`.
HOST_PAYG_PLANTADO = "https://api.openai.com/v1"

# MEDIDO nesta missao, e nao escolhido: o unico caminho que a vigilancia
# cobre e a auditoria NAO le.
VIGIADO_MAS_NAO_AUDITADO = frozenset({"~/.codex/config.toml"})


def _fonte_existe(provider_id: str) -> bool:
    _tipo, caminho = FONTES[provider_id]
    return os.path.exists(os.path.expanduser(caminho))


def _presentes() -> list:
    return sorted(p for p in FONTES if _fonte_existe(p))


def _normalizar(nome: str) -> str:
    return re.sub(r"[^a-z0-9]", "", nome.lower())


def campos_de_endpoint(provider_id: str) -> list:
    """(caminho, host) de todo campo de endpoint da config REAL.

    Nunca devolve o valor: so o host, que e o que `auditar_config`
    publica no proprio detalhe da violacao.
    """
    achados = []
    for caminho, chave, valor in _achatar(config_persistida(provider_id) or {}):
        if _normalizar(chave) not in _CHAVES_ENDPOINT_NORMALIZADAS:
            continue
        achados.append((caminho,
                        _host_de(valor) if isinstance(valor, str) else None))
    return sorted(achados)


class ASuperficieRealDeEndpointEMedida(unittest.TestCase):
    """A resposta a §3.4, medida no disco em vez de suposta."""

    def test_o_google_NAO_tem_grafia_de_endpoint_na_config_real(self):
        # A metade da pergunta que era sobre o google: respondida NAO.
        if not _fonte_existe("google"):
            self.skipTest("~/.gemini/settings.json ausente")
        self.assertEqual(campos_de_endpoint("google"), [])

    def test_algum_provedor_TEM_grafia_de_endpoint_na_config_real(self):
        # DISCRIMINADOR, e a metade que a pergunta nao previa: se
        # NENHUM provedor tivesse a chave, a auditoria de endpoint seria
        # defesa em profundidade sem objeto. MEDIDO: o kimi tem tres.
        com_endpoint = {p: campos_de_endpoint(p) for p in _presentes()}
        com_endpoint = {p: v for p, v in com_endpoint.items() if v}
        self.assertTrue(
            com_endpoint,
            "nenhuma config real desta estacao carrega grafia de "
            "endpoint — a auditoria de endpoint perdeu o objeto e volta "
            "a ser indeterminada")

    def test_nenhum_endpoint_real_aponta_para_host_PAYG(self):
        # A propriedade que o guarda existe para sustentar, medida sobre
        # os campos que existem de verdade.
        for provider_id in _presentes():
            for caminho, host in campos_de_endpoint(provider_id):
                with self.subTest(provider=provider_id, campo=caminho):
                    self.assertNotIn(host, _ENDPOINTS_PAYG)

    def test_a_config_real_intacta_nao_gera_violacao_de_payg(self):
        # CONTRAPROVA: uma auditoria que acusasse sempre bloquearia a
        # frota inteira desta estacao. Fonte NAO LIDA e resultado
        # legitimo e nao entra na conta.
        for provider_id in _presentes():
            with self.subTest(provider=provider_id):
                pagas = [v for v in auditar_config(config_persistida(
                    provider_id)) if isinstance(v, ConfigPaygPersistida)]
                self.assertEqual([v.alvo for v in pagas], [])

    def test_a_leitura_nao_devolve_config_vazia(self):
        # Sem isto, um leitor que devolvesse `{}` — caminho errado,
        # parser trocado — deixaria todos os testes acima verdes por
        # vacuidade.
        for provider_id in _presentes():
            with self.subTest(provider=provider_id):
                lido = config_persistida(provider_id)
                self.assertTrue(
                    lido, f"{provider_id}: config real lida como VAZIA")

    def test_a_config_do_google_tem_a_forma_medida_nesta_missao(self):
        if not _fonte_existe("google"):
            self.skipTest("~/.gemini/settings.json ausente")
        campos = [c for c, _k, _v in _achatar(config_persistida("google"))]
        self.assertIn("security.auth.selectedType", campos)


class AAuditoriaPegaOQueEPlantadoNaFormaREAL(unittest.TestCase):
    """CONTROLE POSITIVO na forma real, nao num dicionario de brinquedo."""

    def _com_campo(self, provider_id: str, chave: str, valor):
        real = dict(config_persistida(provider_id) or {})
        real[chave] = valor
        return real

    def test_host_payg_plantado_em_cada_grafia_e_acusado(self):
        # A pergunta que importa nao e "a chave existe?", e sim "se o
        # valor virasse um host PAYG, a auditoria o pegaria na config
        # REAL?". Sem esta metade a medicao acima seria constatacao.
        for provider_id in _presentes():
            for grafia in sorted(_CHAVES_ENDPOINT):
                with self.subTest(provider=provider_id, chave=grafia):
                    violacoes = auditar_config(
                        self._com_campo(provider_id, grafia,
                                        HOST_PAYG_PLANTADO))
                    self.assertIn(ConfigPaygPersistida,
                                  [type(v) for v in violacoes],
                                  f"{provider_id}/{grafia} nao acusado")

    def test_o_endpoint_real_do_kimi_seria_acusado_se_virasse_PAYG(self):
        # O caso mais forte: nao um campo novo no topo, e sim o campo
        # que EXISTE, no caminho em que ele existe, com o valor trocado.
        if not _fonte_existe("kimi"):
            self.skipTest("~/.kimi-code/config.toml ausente")
        campos = campos_de_endpoint("kimi")
        if not campos:
            self.skipTest("a config do kimi deixou de ter endpoint")
        real = config_persistida("kimi")
        caminho = campos[0][0].split(".")
        no = real
        for parte in caminho[:-1]:
            no = no[parte]
        original = no[caminho[-1]]
        try:
            no[caminho[-1]] = HOST_PAYG_PLANTADO
            violacoes = auditar_config(real)
            self.assertIn(ConfigPaygPersistida,
                          [type(v) for v in violacoes],
                          "o endpoint REAL do kimi, virado PAYG, nao e "
                          "acusado — a auditoria nao alcanca a "
                          "profundidade em que ele vive")
        finally:
            no[caminho[-1]] = original

    def test_flag_de_topup_plantada_na_config_real_e_acusada(self):
        for provider_id in _presentes():
            with self.subTest(provider=provider_id):
                violacoes = auditar_config(
                    self._com_campo(provider_id, "auto_topup", True))
                self.assertIn(ConfigPaygPersistida,
                              [type(v) for v in violacoes])

    def test_fonte_nao_lida_continua_falhando_fechada(self):
        # O achado N2, exercido junto: o marcador reservado precisa
        # continuar produzindo violacao TIPADA, e nao silencio.
        violacoes = auditar_config(
            {CHAVE_FONTE_NAO_LIDA: ["fonte-x: FileNotFoundError"]})
        self.assertEqual([type(v) for v in violacoes], [ConfigNaoLida])

    def test_nenhuma_violacao_publica_o_valor(self):
        # A regra que `auditar_config` declara — "nunca retorna valores,
        # somente caminhos" — exercida com valor plantado conhecido.
        for provider_id in _presentes():
            with self.subTest(provider=provider_id):
                for violacao in auditar_config(
                        self._com_campo(provider_id, "base_url",
                                        HOST_PAYG_PLANTADO)):
                    self.assertNotIn(HOST_PAYG_PLANTADO, violacao.detalhe)


class OQueEVigiadoMasNaoEAuditado(unittest.TestCase):
    """O ACHADO NOVO, fixado pelo nome em vez de escondido no corpus.

    `test_contencao_atribuicao_p1a37.test_a_lista_vigiada_cobre_as_
    fontes_que_a_auditoria_le` acrescenta `~/.codex/config.toml` ao
    corpus A MAO para que a igualdade feche. Aqui o buraco e declarado,
    medido e preso: mudou de tamanho, para qualquer lado, fica vermelho.
    """

    def test_a_diferenca_entre_vigiar_e_auditar_e_exatamente_a_declarada(self):
        vigiados = set(contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO)
        auditados = {caminho for _tipo, caminho in FONTES.values()}
        self.assertEqual(
            vigiados - auditados, set(VIGIADO_MAS_NAO_AUDITADO),
            "a lista de caminhos VIGIADOS mas NAO AUDITADOS mudou. Isto "
            "nao e um teste a consertar: e um buraco a decidir. Vigiar "
            "detecta mutacao; auditar aplica a politica economica. Um "
            "caminho so vigiado nunca produz BLOCKED.")

    def test_nada_e_auditado_sem_ser_vigiado(self):
        # A outra ponta: fonte que a auditoria le e a vigilancia nao ve
        # seria pior — mutacao economica invisivel na corrida de revisao.
        vigiados = set(contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO)
        auditados = {caminho for _tipo, caminho in FONTES.values()}
        self.assertEqual(auditados - vigiados, set())

    def test_o_caminho_nao_auditado_existe_e_tem_conteudo_economico(self):
        # Sem esta medicao o buraco seria teorico. Ele nao e: o arquivo
        # existe e carrega campos que a politica economica trataria.
        for rel in sorted(VIGIADO_MAS_NAO_AUDITADO):
            with self.subTest(caminho=rel):
                caminho = os.path.expanduser(rel)
                if not os.path.isfile(caminho):
                    self.skipTest(f"{rel} ausente nesta estacao")
                self.assertGreater(os.path.getsize(caminho), 0)

    def test_a_lista_de_fontes_e_a_do_leitor_unico(self):
        # A copia que fica para tras (achados 7, 10 e 14): se algum dia
        # existir um segundo leitor, esta medicao vale para um so.
        self.assertIs(config_persistida, leitores_config.config_persistida)

    def test_ao_menos_tres_fontes_declaradas_existem_nesta_estacao(self):
        presentes = _presentes()
        self.assertGreaterEqual(
            len(presentes), 3,
            f"so {presentes} existem — a auditoria de config perde o "
            "objeto e os testes acima ficam verdes por ausencia")


if __name__ == "__main__":
    unittest.main()
