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

## O ACHADO `P1A4-6`, e por que ele estava errado sobre o proprio buraco

Esta secao dizia, ate a P1-A.4:

    `contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO` vigia SEIS caminhos;
    `leitores_config.FONTES` audita CINCO. O sexto e
    `~/.codex/config.toml`, e ele NUNCA e lido por `auditar_config`.

O revisor independente da P1-A.4 mediu e devolveu o oposto, como MAJOR
novo da familia (F):

    o teste calcula "auditados" so por `FONTES`, embora
    `config_persistida("codex")` LEIA E MESCLE `~/.codex/config.toml`:
    afirma um buraco INEXISTENTE sem exercer a interface real.

Ele esta certo, e a leitura do fonte confirma: o ramo do codex em
`config_persistida` soma `ler_toml("~/.codex/config.toml")` ao
`auth.json`, e os campos das duas fontes chegam juntos a
`auditar_config`. O buraco nunca existiu — o que existia era uma conta
feita sobre a TABELA em vez de sobre o LEITOR.

**A correcao e exercer, e nao recontar.** `caminhos_lidos_de_fato`
planta um campo-sentinela em cada caminho candidato, dentro de um LAR
descartavel, e pergunta a `config_persistida` de CADA provedor se o
campo chegou. Quem le o que passa a ser MEDIDO plantando e observando;
nenhuma lista responde por outra. Com isso:

- `VIGIADO_MAS_NAO_AUDITADO` e **vazio**, e vazio por medicao;
- `test_contencao_atribuicao_p1a37.test_a_lista_vigiada_cobre_as_fontes_
  que_a_auditoria_le` deixa de acrescentar o caminho A MAO — o
  `# segunda fonte` era o sintoma exato que o revisor apontou;
- a segunda fonte do codex passa a ter prova de que a POLITICA a
  alcanca: planta-se um endpoint PAYG em `config.toml` e a auditoria
  acusa.

O que a correcao NAO faz: nao acrescenta fonte a `FONTES`, nao alarga a
superficie da auditoria e nao muda politica nenhuma. O comportamento do
codigo de producao e o mesmo de antes desta missao — o que muda e que a
medicao passou a dizer a verdade sobre ele.

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

import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

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

# MEDIDO EXERCENDO o leitor (P1-A.5, ordem 3 — achado `P1A4-6`), e nao
# contado na tabela `FONTES`. Ficou VAZIO: `~/.codex/config.toml`, o
# unico candidato a buraco, e lido e mesclado por
# `config_persistida("codex")`, e portanto auditado. O conjunto continua
# aqui, e nao foi apagado com o buraco: e ele que fica vermelho no dia em
# que a vigilancia cobrir um caminho que o leitor nao alcance.
VIGIADO_MAS_NAO_AUDITADO = frozenset()

# Campo plantado para descobrir QUEM LE O QUE. Nome improvavel de propo-
# sito: se ele aparecer numa config, veio deste teste.
SENTINELA_DE_LEITURA = "p1a5_marcador_de_leitura"

# Caminho que NENHUM leitor declara. E o controle negativo da sonda: sem
# ele, uma sonda que devolvesse "todos leem tudo" passaria despercebida.
CANDIDATO_QUE_NINGUEM_LE = "~/.codex/nao-e-fonte-de-ninguem.toml"


def _plantar(rel: str, chave: str) -> None:
    """Grava o campo-sentinela no formato que aquele caminho pede.

    O formato vem da EXTENSAO, e caminho sem extensao e tratado como
    diretorio de config (o caso do `~/.grok`). Errar o formato faria a
    sonda medir "nao lido" onde o leitor apenas nao parseou — e uma
    sonda que confunde as duas coisas nao mede nada.
    """
    destino = os.path.expanduser(rel)
    if rel.endswith(".json"):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            json.dump({chave: "plantado"}, f)
    elif rel.endswith(".toml"):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write(f'{chave} = "plantado"\n')
    else:
        os.makedirs(destino, exist_ok=True)
        with open(os.path.join(destino, "sonda.json"), "w",
                  encoding="utf-8") as f:
            json.dump({chave: "plantado"}, f)


def _tem_sentinela(cfg, chave: str) -> bool:
    return any(k == chave for _caminho, k, _valor in _achatar(cfg or {}))


def _com_lar(lar: str):
    """Aponta `~` para um lar descartavel, nas duas grafias do SO."""
    ambiente = dict(os.environ)
    ambiente.update({"USERPROFILE": lar, "HOME": lar,
                     "HOMEDRIVE": "", "HOMEPATH": lar})
    return mock.patch.dict(os.environ, ambiente, clear=True)


def caminhos_lidos_de_fato(candidatos) -> dict:
    """`{caminho: {providers que o leem}}` — medido, nunca tabelado.

    A CORRECAO DO `P1A4-6`. Ate a P1-A.4 esta relacao era calculada a
    partir de `leitores_config.FONTES`, que e a DECLARACAO do leitor e
    nao o leitor: `config_persistida("codex")` le uma segunda fonte que
    a tabela nao lista, e a conta afirmava um buraco inexistente.

    Aqui a pergunta e feita a interface real. Para cada candidato: um lar
    descartavel, o campo-sentinela plantado SO naquele caminho, e uma
    chamada a `config_persistida` de cada provedor da frota. Quem
    devolver o sentinela leu o arquivo — nao ha o que interpretar.

    LIMITE DECLARADO: a sonda mede o que CHEGA ao dicionario devolvido.
    Um leitor que abrisse o arquivo e descartasse todo o conteudo sairia
    daqui como "nao le", e para o efeito que importa — a auditoria
    economica enxerga o campo? — essa e a resposta certa.
    """
    saida = {}
    for rel in sorted(candidatos):
        with tempfile.TemporaryDirectory(prefix="p1a5-lar-") as lar:
            with _com_lar(lar):
                _plantar(rel, SENTINELA_DE_LEITURA)
                saida[rel] = {
                    pid for pid in FONTES
                    if _tem_sentinela(config_persistida(pid),
                                      SENTINELA_DE_LEITURA)}
    return saida


def candidatos_de_config() -> set:
    """Todo caminho que QUALQUER das duas listas menciona.

    Nao e uma terceira lista: e a uniao das duas que se quer comparar,
    para que a sonda nunca deixe de fora justamente o caminho em disputa.
    """
    return set(contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO) | {
        caminho for _tipo, caminho in FONTES.values()}


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
        if contencao.usuario_e_infraestrutura():
            self.skipTest(
                "GITHUB_ACTIONS=true + conta nominal de INFRAESTRUTURA: "
                "configs reais do proprietario nao existem neste runner; "
                "SKIP declarado, nunca medido como verde")
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
    """A relacao vigiar/auditar, EXERCIDA — correcao do `P1A4-6`.

    Esta classe media a relacao contando a tabela `FONTES`, e por isso
    afirmava um buraco que nao existe. Agora ela pergunta ao LEITOR:
    planta um campo em cada caminho e observa quem o devolve. A conta
    passou a ser sobre o comportamento, e nao sobre a declaracao.
    """

    @classmethod
    def setUpClass(cls):
        # Uma sonda por classe: ela cria um lar descartavel por caminho e
        # chama `config_persistida` cinco vezes em cada um.
        cls.lidos = caminhos_lidos_de_fato(
            candidatos_de_config() | {CANDIDATO_QUE_NINGUEM_LE})

    def _lidos_de_fato(self) -> set:
        return {rel for rel, quem in self.lidos.items() if quem}

    def test_a_sonda_mede_leitura_e_nao_devolve_tudo(self):
        # CONTROLE NEGATIVO, e ele vem primeiro: uma sonda que dissesse
        # "todos leem tudo" faria os dois testes seguintes passarem sem
        # medir nada. Um caminho que ninguem declara tem de sair vazio.
        self.assertEqual(self.lidos[CANDIDATO_QUE_NINGUEM_LE], set(),
                         "a sonda acusou leitura de um caminho que nenhum "
                         "leitor declara — ela nao esta medindo leitura")

    def test_a_sonda_alcanca_a_fonte_declarada_de_cada_provedor(self):
        # CONTROLE POSITIVO: a fonte que `FONTES` declara para cada
        # provedor tem de ser lida POR ELE. Sem isto, uma sonda quebrada
        # que devolvesse sempre vazio passaria no teste acima.
        for pid, (_tipo, rel) in sorted(FONTES.items()):
            with self.subTest(provider=pid, fonte=rel):
                self.assertIn(pid, self.lidos[rel])

    def test_a_diferenca_entre_vigiar_e_auditar_e_exatamente_a_declarada(self):
        vigiados = set(contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO)
        self.assertEqual(
            vigiados - self._lidos_de_fato(), set(VIGIADO_MAS_NAO_AUDITADO),
            "a lista de caminhos VIGIADOS mas NAO LIDOS mudou. Isto nao e "
            "um teste a consertar: e um buraco a decidir. Vigiar detecta "
            "mutacao; auditar aplica a politica economica. Um caminho so "
            "vigiado nunca produz BLOCKED.")

    def test_nada_e_lido_sem_ser_vigiado(self):
        # A outra ponta: fonte que a auditoria le e a vigilancia nao ve
        # seria pior — mutacao economica invisivel na corrida de revisao.
        vigiados = set(contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO)
        self.assertEqual(self._lidos_de_fato() - vigiados, set())

    def test_a_SEGUNDA_fonte_do_codex_e_lida_e_nao_so_listada(self):
        # O objeto exato do `P1A4-6`. `~/.codex/config.toml` nao esta em
        # `FONTES` e e lido: quem responde e a sonda, nao a tabela.
        self.assertIn("codex", self.lidos["~/.codex/config.toml"],
                      "a segunda fonte do codex deixou de ser lida — ou a "
                      "sonda deixou de alcanca-la")

    def test_a_POLITICA_alcanca_a_segunda_fonte_do_codex(self):
        # Ler nao basta: o que fecha o achado e a auditoria ACUSAR um
        # campo que so existe na segunda fonte. Aqui o endpoint PAYG e
        # plantado SOMENTE em `config.toml`, com `auth.json` limpo.
        with tempfile.TemporaryDirectory(prefix="p1a5-codex-") as lar:
            with _com_lar(lar):
                os.makedirs(os.path.expanduser("~/.codex"), exist_ok=True)
                with open(os.path.expanduser("~/.codex/auth.json"), "w",
                          encoding="utf-8") as f:
                    json.dump({"auth_mode": "chatgpt"}, f)
                with open(os.path.expanduser("~/.codex/config.toml"), "w",
                          encoding="utf-8") as f:
                    f.write(f'base_url = "{HOST_PAYG_PLANTADO}"\n')
                violacoes = list(auditar_config(config_persistida("codex")))
        self.assertTrue(
            any(isinstance(v, ConfigPaygPersistida) for v in violacoes),
            f"endpoint PAYG na segunda fonte nao foi acusado: {violacoes}")

    def test_sem_o_plantio_a_segunda_fonte_do_codex_nao_acusa(self):
        # Contraprova do teste acima: sem ela, uma auditoria que acusasse
        # SEMPRE passaria — e o guarda mediria a si mesmo.
        with tempfile.TemporaryDirectory(prefix="p1a5-codex-") as lar:
            with _com_lar(lar):
                os.makedirs(os.path.expanduser("~/.codex"), exist_ok=True)
                with open(os.path.expanduser("~/.codex/auth.json"), "w",
                          encoding="utf-8") as f:
                    json.dump({"auth_mode": "chatgpt"}, f)
                with open(os.path.expanduser("~/.codex/config.toml"), "w",
                          encoding="utf-8") as f:
                    f.write('model = "gpt-5.6-sol"\n')
                violacoes = list(auditar_config(config_persistida("codex")))
        self.assertEqual(
            [v for v in violacoes if isinstance(v, ConfigPaygPersistida)], [],
            "config limpa foi acusada de PAYG")

    def test_a_lista_de_fontes_e_a_do_leitor_unico(self):
        # A copia que fica para tras (achados 7, 10 e 14): se algum dia
        # existir um segundo leitor, esta medicao vale para um so.
        self.assertIs(config_persistida, leitores_config.config_persistida)

    def test_ao_menos_tres_fontes_declaradas_existem_nesta_estacao(self):
        if contencao.usuario_e_infraestrutura():
            self.skipTest(
                "GITHUB_ACTIONS=true + conta nominal de INFRAESTRUTURA: "
                "configs reais do proprietario nao existem neste runner; "
                "SKIP declarado, nunca medido como verde")
        presentes = _presentes()
        self.assertGreaterEqual(
            len(presentes), 3,
            f"so {presentes} existem — a auditoria de config perde o "
            "objeto e os testes acima ficam verdes por ausencia")


class AEstacaoDeCINaoAfirmaConfigsDoProprietario(unittest.TestCase):
    """Os dois discriminadores sem objeto pulam; as sondas ficam ativas."""

    def test_os_dois_guardas_pulam_com_declaracao_apontavel(self):
        casos = (
            ASuperficieRealDeEndpointEMedida(
                "test_algum_provedor_TEM_grafia_de_endpoint_na_config_real"),
            OQueEVigiadoMasNaoEAuditado(
                "test_ao_menos_tres_fontes_declaradas_existem_nesta_estacao"),
        )
        metodos = (
            casos[0].test_algum_provedor_TEM_grafia_de_endpoint_na_config_real,
            casos[1].test_ao_menos_tres_fontes_declaradas_existem_nesta_estacao,
        )
        with mock.patch.object(contencao, "_USUARIO_LOCAL", "runneradmin"), \
                mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            for metodo in metodos:
                with self.subTest(guarda=metodo.__name__):
                    with self.assertRaisesRegex(
                            unittest.SkipTest,
                            r"GITHUB_ACTIONS=true.*SKIP declarado"):
                        metodo()


if __name__ == "__main__":
    unittest.main()
