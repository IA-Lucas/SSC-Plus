"""O LEITOR REAL de config persistida, exercido — SSC+ P1-A.3.5.

MAJOR #1, a metade que a P1-A.3.2 nao fechou. A correcao daquela missao
fez a frota inteira passar por `executar_preflight`, e sete testes
(`AtalhoPaygGoogleGrok`) provam que o **pipeline** bloqueia diante de um
dicionario com `auto_topup`/`base_url`/`api_key`. Nenhum deles prova que
o **leitor real** produza tal dicionario: todos injetam `config_de=`.

A varredura de guardas da P1-A.3.5 mediu a consequencia disso sob
`sys.monitoring`: `_config_persistida` tinha **zero linha executada**
pelas duas suites. E, para grok, `preflight_capsula.py` devolvia `{}`
INCONDICIONALMENTE — de modo que o caminho percorrido por
`test_grok_com_auto_topup_persistido_e_blocked` era **inalcancavel em
operacao**: o leitor real nunca poderia produzir o dicionario contra o
qual aquele teste afirmava BLOCKED.

O que muda aqui: estes testes chamam `classificar_frota` **sem injetar
`config_de`**, exercendo o binding padrao de `preflight_capsula.py`
contra um HOME descartavel e controlado. O sensor continua injetado —
nenhum subprocesso e criado e nenhum CLI e invocado, de modo que a regra
de `apoio.py` permanece intacta: o que se exerce aqui e o LEITOR DE
DISCO, nunca um provedor.

Prova por reversao: devolver `{}` incondicional para grok em
`_config_persistida` torna
`test_grok_com_config_json_persistida_e_blocked_pelo_leitor_real`
vermelho.
"""

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

import preflight_capsula  # noqa: E402

_PROVEDORES = ("codex", "claude", "kimi", "google", "grok")


class LeitorRealDeConfig(unittest.TestCase):
    """`_config_persistida` exercido contra disco, pelo binding padrao."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a35-lar-")
        self.lar = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    # --- infraestrutura ------------------------------------------------

    def _no_lar_descartavel(self):
        """Redireciona `~` para o descartavel — e PROVA que redirecionou.

        Sem esta prova o teste leria a config REAL do usuario: daria
        verde por acidente num caso e leria dado que nao lhe pertence no
        outro. O guarda vem antes de qualquer assercao, como em
        `test_cli_real_p1a34.py`.
        """
        env = {"USERPROFILE": self.lar, "HOME": self.lar,
               "HOMEDRIVE": self.lar[:2], "HOMEPATH": self.lar[2:]}
        contexto = mock.patch.dict(os.environ, env, clear=True)
        contexto.start()
        self.addCleanup(contexto.stop)
        self.assertEqual(os.path.realpath(os.path.expanduser("~")),
                         os.path.realpath(self.lar),
                         "`~` NAO aponta para o descartavel: o teste leria "
                         "a config real do usuario")

    def _escrever(self, rel: str, dados: dict) -> None:
        caminho = os.path.join(self.lar, *rel.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f)

    def _classificar_sem_injetar_config(self) -> dict:
        """A chamada que importa: `config_de` NAO e passado.

        O sensor continua falso — o alvo deste arquivo e o leitor de
        disco, e invocar CLI aqui nao provaria nada sobre ele.
        """
        sens = {pid: apoio.sensores_dict(pid) for pid in _PROVEDORES}
        relatorios = preflight_capsula.classificar_frota(
            {}, {}, sensor_de=lambda pid: sens[pid][0])
        return {r.provider_id: r for r in relatorios}

    # --- grok: o defeito nomeado pelo ato -------------------------------

    def test_grok_com_config_json_persistida_e_blocked_pelo_leitor_real(self):
        # O caso que era INALCANCAVEL: antes desta correcao o leitor
        # devolvia {} incondicional e nenhuma config de grok podia
        # chegar a `auditar_config`.
        self._no_lar_descartavel()
        self._escrever(".grok/user-settings.json", {"auto_topup": True})
        rels = self._classificar_sem_injetar_config()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_o_leitor_de_grok_nao_depende_do_nome_do_arquivo(self):
        # O acervo nao tem evidencia de COMO o arquivo de config do grok
        # se chama. Fixar um nome seria invencao; o leitor le o
        # diretorio, e esta e a propriedade que sustenta a escolha.
        for nome in ("user-settings.json", "settings.json", "config.json"):
            with self.subTest(arquivo=nome):
                with tempfile.TemporaryDirectory(prefix="p1a35-nome-") as lar:
                    caminho = os.path.join(lar, ".grok")
                    os.makedirs(caminho)
                    with open(os.path.join(caminho, nome), "w",
                              encoding="utf-8") as f:
                        json.dump({"auto_topup": True}, f)
                    with mock.patch.dict(
                            os.environ,
                            {"USERPROFILE": lar, "HOME": lar,
                             "HOMEDRIVE": lar[:2], "HOMEPATH": lar[2:]},
                            clear=True):
                        self.assertEqual(
                            os.path.realpath(os.path.expanduser("~")),
                            os.path.realpath(lar))
                        cfg = preflight_capsula._config_persistida("grok")
                    self.assertEqual(cfg, {nome: {"auto_topup": True}})

    def test_a_violacao_de_grok_nomeia_o_arquivo_que_a_carrega(self):
        # Cada JSON entra sob a propria chave: o `alvo` do erro precisa
        # dizer de onde veio, senao a evidencia nao e acionavel.
        self._no_lar_descartavel()
        self._escrever(".grok/user-settings.json", {"auto_topup": True})
        rels = self._classificar_sem_injetar_config()
        alvos = [e.alvo for e in rels["grok"].erros
                 if e.codigo == "P1A-PAYG-CONFIG"]
        self.assertEqual(alvos, ["user-settings.json.auto_topup"])

    def test_endpoint_payg_de_grok_tambem_bloqueia_pelo_leitor_real(self):
        # A outra metade da auditoria de config: endpoint pago escrito
        # numa config real de grok.
        self._no_lar_descartavel()
        self._escrever(".grok/user-settings.json",
                       {"base_url": "https://api.x.ai/v1"})
        rels = self._classificar_sem_injetar_config()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    # --- contraprovas: o guarda nao pode reprovar sempre ----------------

    def test_lar_limpo_mantem_grok_supervised(self):
        # Sem esta contraprova, um leitor que devolvesse violacao sempre
        # passaria em todos os testes acima.
        self._no_lar_descartavel()
        rels = self._classificar_sem_injetar_config()
        self.assertEqual(rels["grok"].resultado, "SUPERVISED")
        self.assertNotIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_diretorio_de_grok_ausente_devolve_vazio_sem_excecao(self):
        # Estado desta estacao, medido na P1-A.3.5: `~/.grok/` existe mas
        # guarda SQLite, sem JSON de topo. Ausencia e vazio precisam ser
        # o mesmo caminho tranquilo — e `{}` aqui e MEDICAO do disco, nao
        # a cegueira incondicional que havia antes.
        self._no_lar_descartavel()
        self.assertEqual(preflight_capsula._config_persistida("grok"), {})
        os.makedirs(os.path.join(self.lar, ".grok"))
        with open(os.path.join(self.lar, ".grok", "grok.db"), "wb") as f:
            f.write(b"SQLite format 3\x00")
        self.assertEqual(preflight_capsula._config_persistida("grok"), {})

    def test_json_ilegivel_nao_derruba_o_leitor(self):
        # Fail-safe do leitor: um JSON corrompido nao pode transformar a
        # auditoria inteira numa excecao — os demais arquivos continuam
        # sendo auditados.
        self._no_lar_descartavel()
        caminho = os.path.join(self.lar, ".grok")
        os.makedirs(caminho)
        with open(os.path.join(caminho, "quebrado.json"), "w",
                  encoding="utf-8") as f:
            f.write("{isto nao e json")
        self._escrever(".grok/bom.json", {"auto_topup": True})
        cfg = preflight_capsula._config_persistida("grok")
        self.assertEqual(cfg, {"bom.json": {"auto_topup": True},
                               "quebrado.json": {}})


if __name__ == "__main__":
    unittest.main()
