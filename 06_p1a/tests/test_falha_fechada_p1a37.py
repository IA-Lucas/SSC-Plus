"""Fonte de config NAO LIDA nunca e config limpa — SSC+ P1-A.3.7, N2.

O DEFEITO, como o revisor independente o descreveu: em
`06_p1a/leitores_config.py`, "fonte ausente, ilegivel ou JSON invalido
vira `{}`, indistinguivel de configuracao limpa". A docstring do modulo
AFIRMAVA a distincao — *"sempre por medicao do disco, jamais por
cegueira escrita no fonte"* — e o valor devolvido nao a carregava. E a
familia do MAJOR #3: a propriedade afirmada em prosa, nao exercida pela
interface.

O CAMINHO QUE A OPERACAO PERCORRE, e nao o vizinho dele. Em operacao,
`preflight_capsula.main()` chama `classificar_frota(env, tiers)` SEM
`config_de`; o binding padrao e `leitores_config.config_persistida`, que
le o disco a partir de `~`. Estes testes chamam exatamente
`classificar_frota` sem injetar `config_de`, com `~` redirecionado para
um descartavel — e o guarda de redirecionamento vem ANTES de qualquer
assercao, para que o teste nunca leia a config real da estacao.

O vizinho que estes testes NAO exercem, e que nao bastaria: chamar
`auditar_config({...})` com um dicionario montado a mao. Foi assim que o
achado A nasceu — sete testes provando o pipeline contra dicionarios que
o leitor real nunca produzia.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao exercem o CLI de nenhum provedor: sensores sao falsos, nenhum
  subprocesso e criado. O que se exerce e o leitor de disco;
- nao provam que as fontes declaradas em `FONTES` sejam as fontes reais
  de cada CLI — isso e evidencia da coleta da P1-A, e para grok segue
  parcialmente aberto (ver `test_grok_sqlite_p1a37.py`);
- nao cobrem permissao negada (`PermissionError`) por caminho real: o
  caso de arquivo que existe e nao abre e exercido por substituicao de
  `open`, nao por ACL de sistema de arquivos;
- nao dizem nada sobre config guardada em fonte que `FONTES` nao nomeia.
"""

import builtins
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import apoio
from apoio import codigos

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import leitores_config  # noqa: E402
import preflight_capsula  # noqa: E402
from preflight.economia import CHAVE_FONTE_NAO_LIDA, auditar_config  # noqa: E402

_PROVEDORES = ("codex", "claude", "kimi", "google", "grok")

# Fontes declaradas, na forma relativa ao lar. Uma fonte "lida e vazia"
# precisa EXISTIR — e a diferenca que este arquivo inteiro mede.
_FONTES_VAZIAS = {
    "codex": (".codex/auth.json", ".codex/config.toml"),
    "claude": (".claude/settings.json",),
    "kimi": (".kimi-code/config.toml",),
    "google": (".gemini/settings.json",),
    "grok": (".grok/",),
}


class _LarDescartavel(unittest.TestCase):
    """Base: `~` redirecionado para um descartavel, com prova."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-n2-")
        self.lar = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        env = {"USERPROFILE": self.lar, "HOME": self.lar,
               "HOMEDRIVE": self.lar[:2], "HOMEPATH": self.lar[2:]}
        contexto = mock.patch.dict(os.environ, env, clear=True)
        contexto.start()
        self.addCleanup(contexto.stop)
        self.assertEqual(os.path.realpath(os.path.expanduser("~")),
                         os.path.realpath(self.lar),
                         "`~` NAO aponta para o descartavel: o teste leria "
                         "a config real do usuario")

    def escrever(self, rel: str, texto: str) -> str:
        caminho = os.path.join(self.lar, *rel.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        return caminho

    def criar_fontes_vazias(self) -> None:
        """Todas as fontes declaradas EXISTEM e estao vazias."""
        for rels in _FONTES_VAZIAS.values():
            for rel in rels:
                if rel.endswith("/"):
                    os.makedirs(os.path.join(self.lar, *rel.split("/")),
                                exist_ok=True)
                elif rel.endswith(".json"):
                    self.escrever(rel, "{}")
                else:
                    self.escrever(rel, "")

    def classificar(self) -> dict:
        """A chamada de operacao: `config_de` NAO e passado.

        O sensor segue falso — nenhum CLI e invocado; o alvo aqui e o
        leitor de disco no binding padrao de `preflight_capsula`.
        """
        sens = {pid: apoio.sensores_dict(pid) for pid in _PROVEDORES}
        relatorios = preflight_capsula.classificar_frota(
            {}, {}, sensor_de=lambda pid: sens[pid][0])
        return {r.provider_id: r for r in relatorios}


class FonteNaoLidaFalhaFechada(_LarDescartavel):
    """O que nao foi lido NAO e limpo — pelo caminho de operacao."""

    def test_fonte_ausente_bloqueia_a_frota_inteira(self):
        # Lar vazio: NENHUMA fonte declarada existe. Antes desta
        # correcao os cinco saiam classificados como se o disco tivesse
        # sido lido e estivesse limpo.
        rels = self.classificar()
        for pid in _PROVEDORES:
            with self.subTest(provedor=pid):
                self.assertEqual(rels[pid].resultado, "BLOCKED")
                self.assertIn("P1A-CONFIG-NAO-LIDA", codigos(rels[pid]))

    def test_json_invalido_bloqueia_no_caminho_de_operacao(self):
        self.criar_fontes_vazias()
        self.escrever(".claude/settings.json", "{isto nao e json")
        rels = self.classificar()
        self.assertEqual(rels["claude"].resultado, "BLOCKED")
        self.assertIn("P1A-CONFIG-NAO-LIDA", codigos(rels["claude"]))

    def test_toml_invalido_bloqueia_no_caminho_de_operacao(self):
        self.criar_fontes_vazias()
        self.escrever(".kimi-code/config.toml", "isto = nao ) e toml")
        rels = self.classificar()
        self.assertEqual(rels["kimi"].resultado, "BLOCKED")
        self.assertIn("P1A-CONFIG-NAO-LIDA", codigos(rels["kimi"]))

    def test_json_de_topo_que_nao_e_objeto_bloqueia(self):
        # `[1, 2]` parseia, mas nao e config: antes virava `{}` e passava
        # por limpo pelo mesmo caminho do arquivo ausente.
        self.criar_fontes_vazias()
        self.escrever(".gemini/settings.json", "[1, 2]")
        rels = self.classificar()
        self.assertEqual(rels["google"].resultado, "BLOCKED")
        self.assertIn("P1A-CONFIG-NAO-LIDA", codigos(rels["google"]))

    def test_arquivo_ilegivel_dentro_do_diretorio_nomeia_o_arquivo(self):
        # O marcador aninhado vale tanto quanto o de topo, e o `alvo`
        # precisa dizer QUAL arquivo nao foi lido — evidencia acionavel.
        self.criar_fontes_vazias()
        self.escrever(".grok/bom.json", json.dumps({"tema": "escuro"}))
        self.escrever(".grok/quebrado.json", "{isto nao e json")
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        alvos = [e.alvo for e in rels["grok"].erros
                 if e.codigo == "P1A-CONFIG-NAO-LIDA"]
        self.assertEqual(
            alvos, [f"quebrado.json.{CHAVE_FONTE_NAO_LIDA}[0]"])

    def test_arquivo_que_existe_e_nao_abre_bloqueia(self):
        # O caso que separa "ausente" de "ilegivel": o arquivo esta la e
        # o processo nao consegue le-lo. Sem PermissionError encenado
        # nao ha como exercer este ramo de forma portavel.
        self.criar_fontes_vazias()
        alvo = os.path.join(self.lar, ".claude", "settings.json")
        real = builtins.open

        def recusar(caminho, *a, **k):
            if os.path.realpath(str(caminho)) == os.path.realpath(alvo):
                raise PermissionError(13, "acesso negado")
            return real(caminho, *a, **k)

        with mock.patch("builtins.open", recusar):
            cfg = leitores_config.config_persistida("claude")
        self.assertIn(CHAVE_FONTE_NAO_LIDA, cfg)
        self.assertIn("PermissionError", cfg[CHAVE_FONTE_NAO_LIDA][0])
        self.assertEqual([e.codigo for e in auditar_config(cfg)],
                         ["P1A-CONFIG-NAO-LIDA"])

    def test_as_duas_fontes_do_codex_sobrevivem_no_marcador(self):
        # `auth.json` e `config.toml` sao somados; um `update` cru faria
        # o marcador da segunda apagar o da primeira e uma das duas
        # fontes sumiria da auditoria sem que nada acusasse.
        rels_motivos = leitores_config.config_persistida("codex")
        self.assertEqual(len(rels_motivos[CHAVE_FONTE_NAO_LIDA]), 2)
        self.assertEqual(
            [e.codigo for e in auditar_config(rels_motivos)],
            ["P1A-CONFIG-NAO-LIDA", "P1A-CONFIG-NAO-LIDA"])


class ContraprovaFonteLidaEVazia(_LarDescartavel):
    """O guarda nao reprova sempre: fonte lida e vazia continua limpa."""

    def test_fontes_presentes_e_vazias_nao_bloqueiam(self):
        self.criar_fontes_vazias()
        rels = self.classificar()
        for pid in _PROVEDORES:
            with self.subTest(provedor=pid):
                self.assertNotIn("P1A-CONFIG-NAO-LIDA", codigos(rels[pid]))
        self.assertEqual(rels["grok"].resultado, "SUPERVISED")
        self.assertEqual(rels["google"].resultado, "SUPERVISED")

    def test_o_valor_separa_lida_e_vazia_de_nao_lida(self):
        # A distincao no VALOR — que e o objeto do achado. Antes os dois
        # lados desta desigualdade eram `{}`.
        self.assertEqual(leitores_config.config_persistida("google"),
                         leitores_config.nao_lida(
                             "~/.gemini/settings.json", "FileNotFoundError"))
        self.escrever(".gemini/settings.json", "{}")
        self.assertEqual(leitores_config.config_persistida("google"), {})

    def test_diretorio_do_grok_lido_e_sem_json_e_vazio(self):
        # Estado medido desta estacao: `~/.grok/` existe e nao tem JSON
        # de topo. Diretorio LIDO e sem JSON e `{}`; diretorio ausente e
        # marcador. Os dois casos nao podem colidir.
        self.assertIn(CHAVE_FONTE_NAO_LIDA,
                      leitores_config.config_persistida("grok"))
        os.makedirs(os.path.join(self.lar, ".grok"))
        self.assertEqual(leitores_config.config_persistida("grok"), {})

    def test_provider_fora_da_frota_nao_vira_fonte_nao_lida(self):
        # Provedor que a frota nao declara nao tem fonte para nao ler:
        # `{}` aqui e ausencia de objeto, nao falha de leitura.
        self.assertEqual(leitores_config.config_persistida("inexistente"), {})
        self.assertEqual(auditar_config(
            leitores_config.config_persistida("inexistente")), [])


class MarcadorNaoVazaConteudo(_LarDescartavel):
    """O motivo e nome de excecao ou frase curta — nunca o arquivo."""

    def test_conteudo_do_arquivo_ilegivel_nao_entra_no_erro(self):
        self.criar_fontes_vazias()
        self.escrever(".claude/settings.json",
                      '{"api_key": "' + apoio.SENTINELA + '" nao fecha')
        cfg = leitores_config.config_persistida("claude")
        erros = auditar_config(cfg)
        texto = json.dumps([e.to_dict() for e in erros])
        self.assertNotIn(apoio.SENTINELA, texto)
        self.assertNotIn(apoio.SENTINELA, json.dumps(cfg))
        self.assertEqual([e.codigo for e in erros], ["P1A-CONFIG-NAO-LIDA"])


if __name__ == "__main__":
    unittest.main()
