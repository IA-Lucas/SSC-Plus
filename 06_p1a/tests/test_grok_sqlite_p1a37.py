"""A config do grok em SQLite chega a auditoria — SSC+ P1-A.3.7, MAJOR #1.

O DEFEITO, na voz do revisor independente que o manteve NAO-FECHADO:
*"`leitores_config.config_persistida` le para grok somente JSONs de topo
e admite nao alcancar o SQLite observado; PAYG/auto-topup persistido
nessa fonte ainda nao chega a auditoria"*.

A P1-A.3.5 fechou a metade do JSON e DECLAROU a outra aberta. Uma
declaracao de limite nao e um guarda: `~/.grok/` desta estacao guarda
`grok.db` (+ `-wal`/`-shm`) e nenhum JSON de topo, de modo que o caso
que OCORRE em operacao era justamente o que a correcao anterior nao
alcancava.

O CASO QUE OCORRE, e nao o vizinho. Estes testes:
- criam um SQLite DE VERDADE com o modulo `sqlite3` (nao um arquivo com
  bytes de cabecalho falsos, que foi o que a suite anterior usava);
- gravam em modo WAL e deixam a escrita NO WAL, sem checkpoint — que e
  o estado medido da estacao (`grok.db` 4.096 bytes, `-wal` 263.712);
- chamam `preflight_capsula.classificar_frota` SEM injetar `config_de`,
  que e o binding que `main()` usa em operacao.

O vizinho recusado: afirmar sobre `ler_sqlite` isoladamente com um dict
montado a mao. Foi a classe do achado A — sete testes que provavam o
pipeline contra dicionarios que o leitor real nunca produzia.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao provam que o grok GRAVE auto top-up em SQLite, nem em que tabela:
  o esquema real de `grok.db` nao foi lido nesta missao (seria leitura
  de dado do usuario). O que se prova e que, se estiver la, a auditoria
  o alcanca — antes ela nao alcancaria em forma nenhuma;
- nao cobrem config do grok FORA de `~/.grok/`;
- nao cobrem formato embutido que nao seja JSON (YAML, base64, blob
  binario nao textual);
- nao cobrem banco cifrado ou com extensao de arquivo fora de
  `EXTENSOES_SQLITE`;
- nao exercem CLI algum: sensores sao falsos, zero subprocesso.
"""

import hashlib
import json
import os
import sqlite3
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


class _LarComGrok(unittest.TestCase):
    """`~` descartavel, com as outras quatro fontes presentes e vazias."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-grok-")
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
                         "o `~/.grok/` real do usuario")
        for rel, texto in ((".codex/auth.json", "{}"),
                           (".codex/config.toml", ""),
                           (".claude/settings.json", "{}"),
                           (".kimi-code/config.toml", ""),
                           (".gemini/settings.json", "{}")):
            caminho = os.path.join(self.lar, *rel.split("/"))
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto)
        self.dir_grok = os.path.join(self.lar, ".grok")
        os.makedirs(self.dir_grok)
        self.banco = os.path.join(self.dir_grok, "grok.db")

    def gravar_no_wal(self, comandos, nome="grok.db") -> str:
        """Banco SQLite real em modo WAL, com a escrita DEIXADA no WAL.

        `wal_autocheckpoint = 0` mais uma conexao que permanece ABERTA
        reproduzem o estado medido da estacao: o dado recente vive no
        `-wal`, nao no `.db`, e os tres arquivos coexistem. Fechar a
        ultima conexao faria o SQLite fazer checkpoint e apagar o WAL —
        o teste deixaria de exercer o caso que ocorre. Um leitor que
        abrisse o banco com `immutable=1` nao veria nada do que esta
        aqui.
        """
        caminho = os.path.join(self.dir_grok, nome)
        conexao = sqlite3.connect(caminho, isolation_level=None)
        self.addCleanup(conexao.close)
        conexao.execute("PRAGMA journal_mode = WAL")
        conexao.execute("PRAGMA wal_autocheckpoint = 0")
        for comando in comandos:
            conexao.execute(comando)
        return caminho

    def classificar(self) -> dict:
        sens = {pid: apoio.sensores_dict(pid) for pid in _PROVEDORES}
        relatorios = preflight_capsula.classificar_frota(
            {}, {}, sensor_de=lambda pid: sens[pid][0])
        return {r.provider_id: r for r in relatorios}


class ConfigEmSqliteChegaAAuditoria(_LarComGrok):

    def test_auto_topup_em_tabela_chave_valor_bloqueia(self):
        # A forma corrente de um CLI guardar config em SQLite: o NOME do
        # campo vive no DADO, nao no esquema. Sem a promocao de celula
        # textual a nome, `auto_topup` seria so mais uma string.
        self.gravar_no_wal([
            "CREATE TABLE settings (key TEXT, value TEXT)",
            "INSERT INTO settings VALUES ('theme', 'dark')",
            "INSERT INTO settings VALUES ('auto_topup', 'true')",
        ])
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_a_violacao_nomeia_o_banco_e_a_tabela(self):
        self.gravar_no_wal([
            "CREATE TABLE settings (key TEXT, value TEXT)",
            "INSERT INTO settings VALUES ('auto_topup', 1)",
        ])
        rels = self.classificar()
        alvos = [e.alvo for e in rels["grok"].erros
                 if e.codigo == "P1A-PAYG-CONFIG"]
        self.assertTrue(alvos, "violacao sem alvo apontavel")
        for alvo in alvos:
            self.assertTrue(alvo.startswith("grok.db.settings"), alvo)

    def test_chave_de_api_em_coluna_propria_bloqueia(self):
        # Esquema com o nome do campo NA COLUNA — o outro formato
        # corrente. Os dois precisam ser alcancados.
        self.gravar_no_wal([
            "CREATE TABLE conta (usuario TEXT, api_key TEXT)",
            f"INSERT INTO conta VALUES ('x', '{apoio.SENTINELA}')",
        ])
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_endpoint_payg_embutido_em_json_de_texto_bloqueia(self):
        # Config aninhada dentro de um campo TEXT: sem o reparse do JSON
        # a subarvore inteira ficaria fora da auditoria.
        self.gravar_no_wal([
            "CREATE TABLE estado (nome TEXT, payload TEXT)",
            "INSERT INTO estado VALUES ('perfil', '"
            + json.dumps({"base_url": "https://api.x.ai/v1"}) + "')",
        ])
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_valor_gravado_como_blob_tambem_e_auditado(self):
        self.gravar_no_wal([
            "CREATE TABLE conta (api_key BLOB)",
            "INSERT INTO conta VALUES (CAST('"
            + apoio.SENTINELA + "' AS BLOB))",
        ])
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_o_dado_lido_esta_no_wal_e_nao_no_db(self):
        # Prova de que a leitura NAO ignora o WAL: o `.db` sozinho nao
        # contem a tabela. Este e o estado medido da estacao.
        self.gravar_no_wal([
            "CREATE TABLE settings (key TEXT, value TEXT)",
            "INSERT INTO settings VALUES ('auto_topup', 1)",
        ])
        self.assertTrue(os.path.getsize(self.banco + "-wal") > 0,
                        "o teste nao deixou escrita no WAL")
        so_o_db = os.path.join(self.lar, "copia-sem-wal.db")
        with open(self.banco, "rb") as origem, \
                open(so_o_db, "wb") as destino:
            destino.write(origem.read())
        conexao = sqlite3.connect(so_o_db)
        try:
            tabelas = [linha[0] for linha in conexao.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")]
        finally:
            conexao.close()
        self.assertNotIn("settings", tabelas,
                         "o dado ja estava no .db: o teste nao prova "
                         "leitura do WAL")
        cfg = leitores_config.config_persistida("grok")
        self.assertIn("settings", cfg["grok.db"])

    def test_ler_o_banco_nao_altera_um_byte_da_fonte_viva(self):
        # `grok.db` e estado do USUARIO. Abrir o banco vivo, mesmo em
        # modo somente-leitura, faria o SQLite recuperar o WAL e escrever
        # no `-shm`. A leitura e por COPIA — e isto o prova.
        self.gravar_no_wal([
            "CREATE TABLE settings (key TEXT, value TEXT)",
            "INSERT INTO settings VALUES ('theme', 'dark')",
        ])

        def impressao():
            estado = {}
            for nome in sorted(os.listdir(self.dir_grok)):
                caminho = os.path.join(self.dir_grok, nome)
                with open(caminho, "rb") as f:
                    estado[nome] = hashlib.sha256(f.read()).hexdigest()
            return estado

        antes = impressao()
        leitores_config.config_persistida("grok")
        self.assertEqual(impressao(), antes)

    def test_banco_corrompido_e_fonte_nao_lida_e_nao_fonte_limpa(self):
        # Encadeamento com o achado N2: banco ilegivel nao pode sair
        # como estacao limpa.
        with open(self.banco, "wb") as f:
            f.write(b"isto nao e um banco sqlite")
        cfg = leitores_config.config_persistida("grok")
        self.assertIn(leitores_config.CHAVE_FONTE_NAO_LIDA, cfg["grok.db"])
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-CONFIG-NAO-LIDA", codigos(rels["grok"]))

    def test_tabela_acima_do_teto_marca_a_fonte_como_nao_lida(self):
        # Truncar em silencio seria declarar limpo o que nao foi lido.
        limite = leitores_config.LIMITE_LINHAS_POR_TABELA
        with mock.patch.object(leitores_config,
                               "LIMITE_LINHAS_POR_TABELA", 2):
            self.gravar_no_wal([
                "CREATE TABLE t (a TEXT)",
                "INSERT INTO t VALUES ('1'), ('2'), ('3')",
            ])
            cfg = leitores_config.config_persistida("grok")
        self.assertEqual(leitores_config.LIMITE_LINHAS_POR_TABELA, limite)
        self.assertIn(leitores_config.CHAVE_FONTE_NAO_LIDA, cfg["grok.db"])


class ContraprovaBancoLimpo(_LarComGrok):
    """O leitor nao reprova sempre — e nao inventa violacao."""

    def test_banco_real_e_inocuo_mantem_grok_supervised(self):
        self.gravar_no_wal([
            "CREATE TABLE settings (key TEXT, value TEXT)",
            "INSERT INTO settings VALUES ('theme', 'dark')",
            "INSERT INTO settings VALUES ('auto_topup', 0)",
            "CREATE TABLE conversas (id INTEGER, texto TEXT)",
            "INSERT INTO conversas VALUES (1, "
            "'como eu configuro minha openai api key aqui?')",
        ])
        rels = self.classificar()
        self.assertEqual(rels["grok"].resultado, "SUPERVISED")
        self.assertEqual(codigos(rels["grok"]), [])

    def test_frase_de_conversa_nao_vira_nome_de_chave(self):
        # O risco oposto do fail-open: sem o limite de forma, a frase
        # "... minha openai api key" normalizaria para `...apikey` e
        # bloquearia a estacao para sempre.
        self.assertFalse(leitores_config._e_nome_de_chave(
            "como eu configuro minha openai api key"))
        self.assertTrue(leitores_config._e_nome_de_chave("openai_api_key"))
        self.assertFalse(leitores_config._e_nome_de_chave("x" * 200))

    def test_diretorio_com_json_e_banco_le_os_dois(self):
        caminho = os.path.join(self.dir_grok, "user-settings.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"theme": "claro"}, f)
        self.gravar_no_wal([
            "CREATE TABLE settings (key TEXT, value TEXT)",
            "INSERT INTO settings VALUES ('theme', 'dark')",
        ])
        cfg = leitores_config.config_persistida("grok")
        self.assertEqual(cfg["user-settings.json"], {"theme": "claro"})
        self.assertIn("settings", cfg["grok.db"])


if __name__ == "__main__":
    unittest.main()
