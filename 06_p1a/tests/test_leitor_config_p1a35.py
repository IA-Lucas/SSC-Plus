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

import leitores_config  # noqa: E402
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

    def test_diretorio_lido_e_limpo_mantem_grok_supervised(self):
        # Sem esta contraprova, um leitor que devolvesse violacao sempre
        # passaria em todos os testes acima. Desde a P1-A.3.7 a
        # contraprova exige um diretorio que EXISTA: lar sem `.grok/` e
        # fonte NAO LIDA, e nao fonte lida e limpa (achado N2).
        self._no_lar_descartavel()
        os.makedirs(os.path.join(self.lar, ".grok"))
        rels = self._classificar_sem_injetar_config()
        self.assertEqual(rels["grok"].resultado, "SUPERVISED")
        self.assertNotIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_diretorio_de_grok_ausente_e_diretorio_vazio_nao_colidem(self):
        # Estado desta estacao, medido na P1-A.3.5: `~/.grok/` existe mas
        # guarda SQLite, sem JSON de topo. Ate a P1-A.3.7 ausencia e
        # vazio eram o MESMO `{}`; agora sao valores distintos — ausencia
        # e fonte NAO LIDA (achado N2), diretorio lido e sem JSON e `{}`.
        from preflight.economia import CHAVE_FONTE_NAO_LIDA
        self._no_lar_descartavel()
        self.assertIn(CHAVE_FONTE_NAO_LIDA,
                      preflight_capsula._config_persistida("grok"))
        os.makedirs(os.path.join(self.lar, ".grok"))
        self.assertEqual(preflight_capsula._config_persistida("grok"), {})

    # --- achado A: o leitor real dos CINCO, nao so do grok -------------

    FONTES_REAIS = {
        "codex": ".codex/auth.json",
        "claude": ".claude/settings.json",
        "kimi": ".kimi-code/config.toml",
        "google": ".gemini/settings.json",
        "grok": ".grok/user-settings.json",
    }

    def _escrever_config(self, pid: str, dados: dict) -> None:
        """Escreve a config no formato REAL da fonte de cada provedor."""
        rel = self.FONTES_REAIS[pid]
        if rel.endswith(".toml"):
            caminho = os.path.join(self.lar, *rel.split("/"))
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            linhas = []
            for chave, valor in dados.items():
                literal = (str(valor).lower() if isinstance(valor, bool)
                           else f'"{valor}"')
                linhas.append(f"{chave} = {literal}")
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
        else:
            self._escrever(rel, dados)

    def test_todo_provedor_e_lido_do_disco_pelo_binding_padrao(self):
        # Achado A na sua forma geral: ate aqui NENHUM teste executava
        # `_config_persistida` — a varredura mediu zero linha. Cada
        # provedor recebe auto top-up na sua fonte REAL e precisa
        # BLOQUEAR sem que `config_de` seja injetado.
        for pid in _PROVEDORES:
            with self.subTest(provedor=pid):
                with tempfile.TemporaryDirectory(prefix="p1a35-cinco-") as lar:
                    self.lar = lar
                    self._no_lar_descartavel()
                    self._escrever_config(pid, {"auto_topup": True})
                    rels = self._classificar_sem_injetar_config()
                    self.assertEqual(rels[pid].resultado, "BLOCKED")
                    self.assertIn("P1A-PAYG-CONFIG", codigos(rels[pid]))

    def test_chave_de_api_persistida_bloqueia_em_todo_provedor(self):
        for pid in _PROVEDORES:
            with self.subTest(provedor=pid):
                with tempfile.TemporaryDirectory(prefix="p1a35-chave-") as lar:
                    self.lar = lar
                    self._no_lar_descartavel()
                    self._escrever_config(pid, {"api_key": apoio.SENTINELA})
                    rels = self._classificar_sem_injetar_config()
                    self.assertEqual(rels[pid].resultado, "BLOCKED")
                    self.assertIn("P1A-PAYG-CONFIG", codigos(rels[pid]))

    def test_lar_limpo_nao_produz_violacao_de_config_em_ninguem(self):
        # Contraprova dos dois testes acima: sem ela, um leitor que
        # devolvesse violacao sempre passaria em ambos.
        self._no_lar_descartavel()
        rels = self._classificar_sem_injetar_config()
        for pid in _PROVEDORES:
            with self.subTest(provedor=pid):
                self.assertNotIn("P1A-PAYG-CONFIG", codigos(rels[pid]))

    def test_credencial_oauth_do_codex_nao_e_falso_positivo(self):
        # Escopo ratificado na auditoria P1-A (02_auditoria-economica §2):
        # `tokens.*` de `auth.json` SAO a credencial OAuth do ChatGPT, nao
        # chave de API. Alimenta-las a auditoria acusaria PAYG em toda
        # estacao logada — o guarda bloquearia justamente quem esta no
        # canal certo. Este teste fixa a exclusao.
        self._no_lar_descartavel()
        self._escrever(".codex/auth.json", {
            "auth_mode": "subscription-oauth",
            "tokens": {"access_token": apoio.SENTINELA,
                       "refresh_token": apoio.SENTINELA,
                       "id_token": apoio.SENTINELA}})
        # A SEGUNDA fonte do codex precisa existir e estar vazia: desde a
        # P1-A.3.7 uma fonte ausente e declarada NAO LIDA, e o marcador
        # entraria no dicionario junto com `auth_mode`.
        with open(os.path.join(self.lar, ".codex", "config.toml"), "w",
                  encoding="utf-8") as f:
            f.write("")
        cfg = preflight_capsula._config_persistida("codex")
        self.assertEqual(cfg, {"auth_mode": "subscription-oauth"})
        self.assertNotIn("tokens", cfg)
        rels = self._classificar_sem_injetar_config()
        self.assertNotIn("P1A-PAYG-CONFIG", codigos(rels["codex"]))

    def test_codex_soma_auth_json_e_config_toml(self):
        # O leitor do codex tem DUAS fontes; ler so uma deixaria a outra
        # fora da auditoria sem que nada acusasse.
        self._no_lar_descartavel()
        self._escrever(".codex/auth.json", {"auth_mode": "subscription-oauth"})
        caminho = os.path.join(self.lar, ".codex", "config.toml")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write('base_url = "https://api.openai.com/v1"\n')
        cfg = preflight_capsula._config_persistida("codex")
        self.assertEqual(cfg["auth_mode"], "subscription-oauth")
        self.assertEqual(cfg["base_url"], "https://api.openai.com/v1")
        rels = self._classificar_sem_injetar_config()
        self.assertEqual(rels["codex"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["codex"]))

    def test_config_ausente_nao_vira_excecao_e_se_declara_nao_lida(self):
        # Fail-safe: fonte ausente nao pode virar excecao. O que ela
        # devolve mudou na P1-A.3.7 (achado N2): era `{}`, indistinguivel
        # de fonte lida e limpa; passa a ser o marcador de fonte NAO
        # LIDA, que `auditar_config` transforma em P1A-CONFIG-NAO-LIDA.
        from preflight.economia import CHAVE_FONTE_NAO_LIDA
        self._no_lar_descartavel()
        for pid in _PROVEDORES:
            with self.subTest(provedor=pid):
                cfg = preflight_capsula._config_persistida(pid)
                self.assertIn(CHAVE_FONTE_NAO_LIDA, cfg)
                self.assertNotEqual(cfg, {})

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
        # O arquivo quebrado carrega o marcador de fonte NAO LIDA sob a
        # PROPRIA chave (P1-A.3.7, N2): antes ele virava `{}` e sumia da
        # auditoria com cara de arquivo lido e limpo.
        from preflight.economia import CHAVE_FONTE_NAO_LIDA
        self.assertEqual(cfg["bom.json"], {"auto_topup": True})
        self.assertEqual(list(cfg["quebrado.json"]), [CHAVE_FONTE_NAO_LIDA])
        motivo = cfg["quebrado.json"][CHAVE_FONTE_NAO_LIDA][0]
        self.assertTrue(motivo.endswith("quebrado.json: JSON invalido"),
                        motivo)


class LeitorUnicoParaOsDoisRunners(unittest.TestCase):
    """Um leitor so, e nao dois que derivam em silencio.

    As correcoes 1 e 3 desta missao fecharam dois defeitos em
    `preflight_capsula`: a cegueira incondicional para grok e a allowlist
    de duas chaves no codex. A copia de `07_p1b/preflight_atual.py`
    carregava os DOIS, porque a correcao alcancou so a copia que a suite
    exercita — mesmo mecanismo do ACHADO 7 e do achado 10. Agora os dois
    runners apontam para a MESMA funcao, e este teste e o que impede que
    voltem a divergir.
    """

    def _runner_p1b(self):
        caminho = os.path.join(os.path.dirname(_DIR_P1A), "07_p1b",
                               "preflight_atual.py")
        if not os.path.isfile(caminho):
            self.skipTest("runner da P1-B ausente")
        import importlib.util
        spec = importlib.util.spec_from_file_location("p1b_leitor", caminho)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_os_dois_runners_usam_a_mesma_funcao(self):
        import leitores_config
        p1b = self._runner_p1b()
        self.assertIs(preflight_capsula._config_persistida,
                      leitores_config.config_persistida)
        self.assertIs(p1b._config_persistida,
                      leitores_config.config_persistida)

    def test_toda_a_frota_tem_fonte_declarada(self):
        # Um provedor sem fonte declarada devolveria `{}` silencioso —
        # que e exatamente o defeito do MAJOR #1. A lista e explicita.
        import leitores_config
        self.assertEqual(sorted(leitores_config.FONTES), sorted(_PROVEDORES))

    def test_provider_fora_da_frota_devolve_vazio_sem_inventar(self):
        import leitores_config
        self.assertEqual(leitores_config.config_persistida("inexistente"), {})


if __name__ == "__main__":
    unittest.main()
