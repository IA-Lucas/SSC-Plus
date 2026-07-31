"""Correcoes dos seis MAJOR abertos — SSC+ P1-A.3.2 (experimental).

Um teste por propriedade corrigida, escrito para FALHAR se a correcao
for desfeita. Os seis alvos, na numeracao de 99_decisao-p1a31.md:

#1 §4 — atalho PAYG de google/grok fora do pipeline (preflight_capsula);
#2 §4 — regexes de quota esgotada cegas a zero decimal e percentual;
#3 §4 — isolamento do kimi: nada restringia nem detectava escrita fora
        do diretorio descartavel;
#4 §4 — lease verificado so na abertura, nunca antes da persistencia;
#5 §4.1 — pacote lido da arvore de trabalho, nao do commit;
#6 §4.2 — sentinela anti-P2 medindo lista de caminhos (o teste dele
        continua em test_emendas_p1a3.py, onde sempre viveu).

Nenhum teste invoca CLI real, rede ou modelo: sensores falsos, locks de
mentira em diretorio temporario e o proprio banco de objetos do git.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import apoio
from apoio import SENTINELA, codigos
from preflight import espec_de, executar_preflight
from preflight.adaptadores import _quota_de

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402
import preflight_capsula  # noqa: E402

_RAIZ_REPO = os.path.dirname(_DIR_P1A)
_ENV_LIMPO = {"PATH": os.environ.get("PATH", "")}
_PROVEDORES = ("codex", "claude", "kimi", "google", "grok")


class _SaidaMuda(io.StringIO):
    """stdout de teste: os runners chamam `reconfigure`, que StringIO nao tem."""

    def reconfigure(self, **kwargs):
        return None


def _sensores():
    """Sensores falsos verdes por provedor, com contador acessivel."""
    return {pid: apoio.sensores_dict(pid) for pid in _PROVEDORES}


def _escrever_lock(dir_locks, sessao, fence, expira_em):
    os.makedirs(dir_locks, exist_ok=True)
    with open(os.path.join(dir_locks, f"{sessao}.lease"), "w",
              encoding="utf-8") as f:
        json.dump({"sessao": sessao, "pid": os.getpid(), "token": fence,
                   "renovado_em": expira_em - 120,
                   "expira_em": expira_em}, f)
    with open(os.path.join(dir_locks, f"{sessao}.fence"), "w",
              encoding="ascii") as f:
        f.write(str(fence))


class AtalhoPaygGoogleGrok(unittest.TestCase):
    """MAJOR #1 — google/grok pulavam o pipeline e os bloqueios economicos.

    O atalho montava `{"resultado": "SUPERVISED"}` a mao, sem chamar
    `executar_preflight` nem `_config_persistida`. Restaurar o atalho faz
    todos os testes desta classe falharem: eles exigem BLOCKED onde o
    atalho devolvia SUPERVISED.
    """

    def _classificar(self, env, configs=None, sens=None):
        sens = sens or _sensores()
        mapa = configs or {}
        return {r.provider_id: r for r in preflight_capsula.classificar_frota(
            env, {}, config_de=lambda pid: mapa.get(pid, {}),
            sensor_de=lambda pid: sens[pid][0])}

    def test_google_com_chave_payg_do_proprio_provedor_e_blocked(self):
        rels = self._classificar({"GEMINI_API_KEY": SENTINELA})
        self.assertEqual(rels["google"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-ENV", codigos(rels["google"]))

    def test_grok_com_chave_payg_do_proprio_provedor_e_blocked(self):
        rels = self._classificar({"XAI_API_KEY": SENTINELA})
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-ENV", codigos(rels["grok"]))

    def test_google_com_endpoint_payg_persistido_e_blocked(self):
        rels = self._classificar(
            {}, {"google": {"base_url":
                            "https://generativelanguage.googleapis.com/v1"}})
        self.assertEqual(rels["google"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["google"]))

    def test_grok_com_auto_topup_persistido_e_blocked(self):
        rels = self._classificar({}, {"grok": {"auto_topup": True}})
        self.assertEqual(rels["grok"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["grok"]))

    def test_google_com_chave_de_api_persistida_e_blocked(self):
        rels = self._classificar({}, {"google": {"api_key": SENTINELA}})
        self.assertEqual(rels["google"].resultado, "BLOCKED")
        self.assertIn("P1A-PAYG-CONFIG", codigos(rels["google"]))

    def test_ambiente_limpo_mantem_supervised_e_zero_sondas(self):
        # A correcao nao pode reintroduzir sonda em google/grok: era o
        # motivo declarado do atalho (as sondas via Git Bash penduram).
        # A zero-sonda vem da especificacao, nao do atalho.
        sens = _sensores()
        rels = self._classificar({}, sens=sens)
        for pid in ("google", "grok"):
            with self.subTest(provider=pid):
                self.assertEqual(rels[pid].resultado, "SUPERVISED")
                self.assertEqual(rels[pid].origem_credencial, "nao-sondada")
                self.assertIsNone(rels[pid].versao)
                self.assertEqual(sens[pid][1].n, 0,
                                 "sonda de execucao invocada")
                self.assertEqual(sens[pid][2].n, 0,
                                 "sonda de modelos invocada")

    def test_nenhum_provedor_escapa_do_pipeline(self):
        # A frota inteira sai de `executar_preflight`: um relatorio
        # montado a mao nao seria RelatorioPreflight.
        from preflight.pipeline import RelatorioPreflight
        sens = _sensores()
        rels = preflight_capsula.classificar_frota(
            {}, {}, config_de=lambda pid: {},
            sensor_de=lambda pid: sens[pid][0])
        self.assertEqual(len(rels), len(_PROVEDORES))
        for rel in rels:
            self.assertIsInstance(rel, RelatorioPreflight)


class QuotaEsgotadaZeroDecimalEPercentual(unittest.TestCase):
    """MAJOR #2 — `0.0 tokens available` e `0% quota available` escapavam.

    O zero literal exigia `\\b0` seguido de espaco: zero decimal e zero
    percentual nao casavam regex alguma de esgotamento e caiam no sinal
    positivo `\\bavailable\\b` — quota zerada lida como disponivel
    (fail-open). Desfazer a correcao devolve "disponivel" aqui.
    """

    ESGOTADAS = (
        "0.0 tokens available",      # forma citada no achado
        "0% quota available",        # forma citada no achado
        "0,0 tokens available",      # decimal com virgula
        "quota available = 0%",
        "available: 0.0",
        "quota: 0",
        "credits = 0",
        "0 requests remaining",
        "0 of 100 requests remaining",
        "0/100 requests remaining",
        "no calls left",
    )
    # Franquia REAL disponivel: nenhuma pode virar "esgotada" — a
    # correcao nao pode trocar fail-open por fail-closed indevido.
    DISPONIVEIS = (
        "10.0 tokens available",     # o "0" depois do ponto nao e zero
        "0.5 calls left",            # meia franquia nao e zero
        "100 requests remaining",
        "1000 tokens available",
        "95% quota available",
        "50/100 requests remaining",
    )

    def test_zero_decimal_e_percentual_sao_esgotada(self):
        for texto in self.ESGOTADAS:
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, True), "esgotada")

    def test_zero_dentro_de_numero_maior_nao_esgota(self):
        for texto in self.DISPONIVEIS:
            with self.subTest(texto=texto):
                self.assertNotEqual(_quota_de(texto, True), "esgotada")

    def test_pipeline_bloqueia_com_zero_decimal_no_login(self):
        # Fim a fim: a saida do CLI chega pelo sensor e precisa produzir
        # BLOCKED tipado, nao ELIGIBLE.
        sensores, _, _ = apoio.sensores_dict(
            "codex",
            login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)\n"
                  "0.0 tokens available")
        rel = executar_preflight(espec_de("codex"), sensores, env={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA", codigos(rel))

    def test_pipeline_bloqueia_com_zero_percentual_no_login(self):
        sensores, _, _ = apoio.sensores_dict(
            "codex",
            login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)\n"
                  "0% quota available")
        rel = executar_preflight(espec_de("codex"), sensores, env={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA", codigos(rel))


class ContencaoDoReviewer(unittest.TestCase):
    """MAJOR #3 — nada restringia nem DETECTAVA escrita fora do descartavel.

    A lista de "arquivos restantes" so enxergava DENTRO do diretorio
    descartavel. O manifesto SHA-256 da arvore inteira e a metade que
    faltava: o que a instrucao textual nao impede, ele acusa.
    """

    def test_manifesto_acusa_arquivo_criado_fora_do_descartavel(self):
        with tempfile.TemporaryDirectory() as raiz:
            os.makedirs(os.path.join(raiz, "codigo"))
            with open(os.path.join(raiz, "codigo", "a.py"), "w") as f:
                f.write("original\n")
            antes = contencao.manifesto(raiz)
            # o "reviewer" escreve fora do seu diretorio descartavel
            with open(os.path.join(raiz, "codigo", "backdoor.py"), "w") as f:
                f.write("print('escrevi fora')\n")
            achados = contencao.mutacoes(antes, contencao.manifesto(raiz))
            self.assertEqual(achados, ["criado: codigo/backdoor.py"])

    def test_manifesto_acusa_alteracao_de_arquivo_existente(self):
        with tempfile.TemporaryDirectory() as raiz:
            alvo = os.path.join(raiz, "a.py")
            with open(alvo, "w") as f:
                f.write("original\n")
            antes = contencao.manifesto(raiz)
            with open(alvo, "w") as f:
                f.write("adulterado\n")
            self.assertEqual(contencao.mutacoes(antes,
                                                contencao.manifesto(raiz)),
                             ["alterado: a.py"])

    def test_manifesto_acusa_remocao(self):
        with tempfile.TemporaryDirectory() as raiz:
            alvo = os.path.join(raiz, "a.py")
            with open(alvo, "w") as f:
                f.write("original\n")
            antes = contencao.manifesto(raiz)
            os.remove(alvo)
            self.assertEqual(contencao.mutacoes(antes,
                                                contencao.manifesto(raiz)),
                             ["removido: a.py"])

    def test_arvore_intacta_nao_produz_alarme(self):
        with tempfile.TemporaryDirectory() as raiz:
            with open(os.path.join(raiz, "a.py"), "w") as f:
                f.write("original\n")
            antes = contencao.manifesto(raiz)
            self.assertEqual(contencao.mutacoes(antes,
                                                contencao.manifesto(raiz)), [])

    def test_locks_e_a_unica_exclusao_e_ela_e_declarada(self):
        # `locks/` sai porque o renovador dedicado reescreve o lease a
        # cada 30 s. Qualquer outra exclusao seria ponto cego.
        self.assertEqual(contencao.EXCLUIDOS_DO_MANIFESTO, ("locks",))
        with tempfile.TemporaryDirectory() as raiz:
            os.makedirs(os.path.join(raiz, "locks"))
            os.makedirs(os.path.join(raiz, ".git"))
            for rel in ("locks/x.lease", ".git/objeto", "a.py"):
                with open(os.path.join(raiz, rel), "w") as f:
                    f.write("x")
            manifesto = contencao.manifesto(raiz)
            self.assertNotIn("locks/x.lease", manifesto)
            self.assertIn(".git/objeto", manifesto)  # .git NAO e ponto cego
            self.assertIn("a.py", manifesto)

    def test_argv_do_kimi_usa_a_restricao_que_o_cli_oferece(self):
        argv = contencao.argv_kimi("/bin/kimi", "revise", "/tmp/skills-vazio")
        self.assertIn("--plan", argv)
        self.assertIn("--skills-dir", argv)
        self.assertEqual(argv[argv.index("--skills-dir") + 1],
                         "/tmp/skills-vazio")
        self.assertEqual(argv[-2:], ["-p", "revise"])

    def test_argv_do_kimi_nunca_auto_aprova_ferramenta(self):
        argv = contencao.argv_kimi("/bin/kimi", "revise", "/tmp/vazio")
        for flag in contencao.FLAGS_DE_AUTO_APROVACAO:
            with self.subTest(flag=flag):
                self.assertNotIn(flag, argv)

    # --- Fim a fim: detectar nao basta, tem de REPROVAR a corrida ----
    #
    # Os testes acima medem `manifesto`/`mutacoes` isolados. O que
    # importa em operacao e outra coisa: um reviewer que escreve fora do
    # descartavel precisa fazer a ferramenta devolver codigo de falha e
    # gravar a violacao na evidencia. Aqui roda `revisao_p1a31.main()`
    # de verdade, com um reviewer FALSO no lugar do CLI — zero chamada
    # de modelo, zero rede.

    def _revisao_com_reviewer_falso(self, raiz, corpo_do_reviewer):
        import importlib.util
        from pathlib import Path
        caminho = os.path.join(_DIR_P1A, "evidencias", "revisao_p1a31.py")
        spec = importlib.util.spec_from_file_location(
            "revisao_p1a31_sob_teste", caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        _escrever_lock(os.path.join(raiz, "locks"), modulo.SESSAO_LOCK, 4,
                       time.time() + 600)
        os.makedirs(os.path.join(raiz, "06_p1a"), exist_ok=True)
        agora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(os.path.join(raiz, "06_p1a", "tiers_declarados.json"),
                  "w", encoding="utf-8") as f:
            json.dump({"validade_maxima_horas": 24,
                       "declaracoes": [{"provider_id": "kimi",
                                        "tier": "allegretto",
                                        "declarado_por": "proprietario",
                                        "declarado_em_utc": agora,
                                        "validade_horas": 24}]}, f)
        pacote = os.path.join(raiz, "pacote.txt")
        with open(pacote, "wb") as f:
            f.write(b"pacote de mentira\n")

        saida = Path(raiz) / "06_p1a" / "evidencias" / "revisao-p1a31"
        env_minimo = {k: os.environ[k] for k in
                      ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
                       "PATHEXT") if k in os.environ}
        with mock.patch.dict(os.environ, env_minimo, clear=True), \
                mock.patch.object(modulo, "RAIZ", Path(raiz)), \
                mock.patch.object(modulo, "SAIDA", saida), \
                mock.patch.object(modulo, "COMANDOS", {
                    "kimi": lambda tmp, skills, prompt: [
                        sys.executable, "-c", corpo_do_reviewer]}), \
                mock.patch.object(sys, "argv",
                                  ["revisao_p1a31.py", "kimi", pacote]), \
                mock.patch("sys.stdout", _SaidaMuda()):
            rc = modulo.main()
        gravados = sorted(os.listdir(saida))
        with open(os.path.join(saida, gravados[0]), encoding="utf-8") as f:
            return rc, json.load(f)

    def test_reviewer_que_escreve_fora_reprova_a_corrida(self):
        with tempfile.TemporaryDirectory() as raiz:
            os.makedirs(os.path.join(raiz, "codigo"))
            with open(os.path.join(raiz, "codigo", "a.py"), "w") as f:
                f.write("original\n")
            fora = os.path.join(raiz, "codigo", "backdoor.py").replace(
                "\\", "\\\\")
            rc, evidencia = self._revisao_com_reviewer_falso(
                raiz, f"open(r'{fora}', 'w').write('escrevi fora')")
            self.assertEqual(rc, 3, "corrida com violacao nao pode dar 0")
            self.assertTrue(evidencia["contencao"]["violada"])
            self.assertIn("criado: codigo/backdoor.py",
                          evidencia["contencao"]["mutacoes_fora_do_descartavel"])

    def test_reviewer_bem_comportado_nao_reprova(self):
        # Contraprova: sem ela, um guarda que reprovasse sempre passaria
        # no teste acima. Escrever DENTRO do descartavel e permitido.
        with tempfile.TemporaryDirectory() as raiz:
            os.makedirs(os.path.join(raiz, "codigo"))
            with open(os.path.join(raiz, "codigo", "a.py"), "w") as f:
                f.write("original\n")
            rc, evidencia = self._revisao_com_reviewer_falso(
                raiz, "open('rascunho.txt', 'w').write('dentro do tmp')")
            self.assertEqual(rc, 0)
            self.assertFalse(evidencia["contencao"]["violada"])
            self.assertEqual(
                evidencia["contencao"]["mutacoes_fora_do_descartavel"], [])
            self.assertIn("rascunho.txt",
                          evidencia["dir_descartavel_arquivos_restantes"])

    def test_enforcement_nao_afirma_sandbox_que_nao_existe(self):
        # Honestidade do rotulo faz parte do conserto: o kimi nao tem
        # sandbox de filesystem, e a evidencia nao pode sugerir que tem.
        texto = contencao.enforcement_kimi().lower()
        self.assertIn("sem sandbox de filesystem", texto)
        self.assertIn("manifesto", texto)


class LeaseAntesDaPersistencia(unittest.TestCase):
    """MAJOR #4 — lease conferido so na abertura, nunca antes de gravar."""

    def test_lease_vivo_com_mesmo_fence_e_aceito(self):
        with tempfile.TemporaryDirectory() as raiz:
            _escrever_lock(os.path.join(raiz, "locks"), "s-ops", 7,
                           time.time() + 600)
            estado = contencao.verificar_lock(raiz, "s-ops",
                                              fence_esperado=7)
            self.assertEqual(estado["fence"], 7)

    def test_lease_expirado_para_antes_de_gravar(self):
        with tempfile.TemporaryDirectory() as raiz:
            _escrever_lock(os.path.join(raiz, "locks"), "s-ops", 7,
                           time.time() - 1)
            with self.assertRaises(SystemExit) as ctx:
                contencao.verificar_lock(raiz, "s-ops")
            self.assertIn("lease da sessao operacional morto",
                          str(ctx.exception))

    def test_titular_substituido_para_antes_de_gravar(self):
        # Fence superior = outra sessao adquiriu o escritor no intervalo.
        with tempfile.TemporaryDirectory() as raiz:
            _escrever_lock(os.path.join(raiz, "locks"), "s-ops", 8,
                           time.time() + 600)
            with self.assertRaises(SystemExit) as ctx:
                contencao.verificar_lock(raiz, "s-ops", fence_esperado=7)
            self.assertIn("titular do escritor substituido",
                          str(ctx.exception))

    def test_fence_ausente_para_antes_de_gravar(self):
        with tempfile.TemporaryDirectory() as raiz:
            _escrever_lock(os.path.join(raiz, "locks"), "s-ops", 7,
                           time.time() + 600)
            os.remove(os.path.join(raiz, "locks", "s-ops.fence"))
            with self.assertRaises(SystemExit) as ctx:
                contencao.verificar_lock(raiz, "s-ops")
            self.assertIn("fence ilegivel/ausente", str(ctx.exception))

    def _capsula_com_lock(self, raiz, fence, durante_as_sondas):
        """Roda preflight_capsula.main() sobre uma raiz de mentira.

        O stdout do runner e capturado: sem isso a suite imprime uma
        linha `evidencia: 06_p1a/evidencias/...` que parece — e nao e —
        escrita no repositorio (a gravacao vai para `raiz`, temporaria).
        """
        _escrever_lock(os.path.join(raiz, "locks"),
                       preflight_capsula._SESSAO_LOCK, fence,
                       time.time() + 600)
        with mock.patch.dict(os.environ, _ENV_LIMPO, clear=True), \
                mock.patch.object(preflight_capsula, "_RAIZ", raiz), \
                mock.patch.object(preflight_capsula, "classificar_frota",
                                  durante_as_sondas), \
                mock.patch("sys.stdout", _SaidaMuda()):
            return preflight_capsula.main()

    def test_capsula_para_se_o_titular_muda_entre_a_sonda_e_a_gravacao(self):
        # Este e o defeito exato do achado: a verificacao existia so na
        # abertura, e as sondas podiam exceder a janela do lease. Com a
        # conferencia apenas inicial, main() gravaria normalmente.
        with tempfile.TemporaryDirectory() as raiz:
            def sondas_que_perdem_o_escritor(*args, **kwargs):
                _escrever_lock(os.path.join(raiz, "locks"),
                               preflight_capsula._SESSAO_LOCK, 8,
                               time.time() + 600)
                return []

            with self.assertRaises(SystemExit) as ctx:
                self._capsula_com_lock(raiz, 7, sondas_que_perdem_o_escritor)
            self.assertIn("titular do escritor substituido",
                          str(ctx.exception))
            self.assertFalse(
                os.path.isdir(os.path.join(raiz, "06_p1a", "evidencias")),
                "nada pode ter sido gravado depois da PARADA")

    def test_capsula_para_se_o_lease_morre_entre_a_sonda_e_a_gravacao(self):
        with tempfile.TemporaryDirectory() as raiz:
            def sondas_que_estouram_o_lease(*args, **kwargs):
                _escrever_lock(os.path.join(raiz, "locks"),
                               preflight_capsula._SESSAO_LOCK, 7,
                               time.time() - 1)
                return []

            with self.assertRaises(SystemExit) as ctx:
                self._capsula_com_lock(raiz, 7, sondas_que_estouram_o_lease)
            self.assertIn("lease da sessao operacional morto",
                          str(ctx.exception))
            self.assertFalse(
                os.path.isdir(os.path.join(raiz, "06_p1a", "evidencias")))

    def test_capsula_grava_quando_o_titular_permanece(self):
        # Contraprova: sem ela, os dois testes acima passariam mesmo com
        # um guarda que reprovasse sempre.
        with tempfile.TemporaryDirectory() as raiz:
            rc = self._capsula_com_lock(raiz, 7, lambda *a, **k: [])
            self.assertEqual(rc, 0)
            evidencias = os.path.join(raiz, "06_p1a", "evidencias")
            gravados = os.listdir(evidencias)
            self.assertEqual(len(gravados), 1)
            with open(os.path.join(evidencias, gravados[0]),
                      encoding="utf-8") as f:
                doc = json.load(f)
            self.assertTrue(doc["lock_verificado_antes_da_persistencia"])
            self.assertEqual(doc["lock_escritor_unico"]["fence"], 7)


class AncoragemDoPacoteNoCommit(unittest.TestCase):
    """MAJOR #5 (§4.1) — o pacote era funcao da arvore, nao do commit.

    O bloco de hashes de evidencia usava `(RAIZ / rel).read_bytes()`.
    Com `core.autocrlf=true`, 4 de 11 hashes divergiam entre a copia de
    trabalho e um checkout novo, e a reproducao a partir do commit
    falhava. Estes testes exercem o gerador de verdade contra o banco de
    objetos do git.
    """

    @classmethod
    def setUpClass(cls):
        cls.gerador = os.path.join(_DIR_P1A, "evidencias",
                                   "pacote_p1a31.py")
        cls.spec = None
        if not os.path.isfile(cls.gerador):
            raise unittest.SkipTest("gerador ausente")
        import importlib.util
        spec = importlib.util.spec_from_file_location("pacote_p1a31_sob_teste",
                                                      cls.gerador)
        cls.spec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.spec)

    def test_hashes_de_evidencia_vem_do_blob_e_nao_do_disco(self):
        # A prova direta da ancoragem: para cada evidencia hasheada, o
        # valor precisa bater com `git cat-file blob ALVO:<path>`.
        modulo = self.spec
        for rel in modulo.EVIDENCIAS_HASHEADAS:
            with self.subTest(evidencia=rel):
                blob = subprocess.run(
                    ["git", "cat-file", "blob", f"{modulo.ALVO}:{rel}"],
                    cwd=_RAIZ_REPO, capture_output=True, check=True).stdout
                self.assertEqual(modulo._blob(rel), blob)

    def test_leitura_do_pacote_ignora_a_arvore_de_trabalho(self):
        # Mutar o disco NAO pode mudar o que o gerador le.
        modulo = self.spec
        rel = "06_p1a/tiers_declarados.json"
        caminho = os.path.join(_RAIZ_REPO, *rel.split("/"))
        antes = modulo._blob(rel)
        with open(caminho, "rb") as f:
            original = f.read()
        try:
            with open(caminho, "ab") as f:
                f.write(b"\nMUTACAO-DA-ARVORE-DE-TRABALHO\n")
            self.assertEqual(modulo._blob(rel), antes)
            self.assertEqual(modulo._conteudo_alvo(rel),
                             antes.decode("utf-8"))
        finally:
            with open(caminho, "wb") as f:
                f.write(original)

    def test_gerador_nao_depende_do_head_corrente(self):
        # O portao antigo exigia `rev-parse HEAD == ALVO` e por isso o
        # gerador parava de rodar apos qualquer commit — nenhum terceiro
        # reproduzia o pacote a partir do repositorio.
        modulo = self.spec
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_RAIZ_REPO,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
        pacote = modulo.montar_pacote()
        self.assertIn(modulo.ALVO, pacote)
        if head != modulo.ALVO:
            self.assertNotIn(head, pacote,
                             "o HEAD corrente nao pode entrar no pacote")

    def test_duas_geracoes_produzem_o_mesmo_texto(self):
        self.assertEqual(self.spec.montar_pacote(),
                         self.spec.montar_pacote())

    # --- O portao novo nao e mais fraco que o antigo ------------------
    # O portao antigo era `rev-parse HEAD == ALVO`. Ele so tinha valor
    # protetor porque o conteudo vinha da arvore de trabalho: dizia
    # "o checkout e o alvo, logo o que eu li e o alvo". Lendo do banco
    # de objetos, essa inferencia fica vazia — o checkout nao entra no
    # pacote. Os tres testes abaixo medem que o portao novo recusa
    # exatamente o que importa: alvo inexistente e paternidade errada.

    def test_portao_recusa_commit_alvo_inexistente(self):
        inexistente = "0" * 40
        with mock.patch.object(self.spec, "ALVO", inexistente):
            with self.assertRaises(SystemExit) as ctx:
                self.spec.montar_pacote()
        self.assertIn("commit alvo", str(ctx.exception))
        self.assertIn("ausente do repositorio", str(ctx.exception))

    def test_portao_recusa_paternidade_divergente(self):
        # PAI trocado por um commit real, porem que nao e o pai de ALVO.
        outro = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=_RAIZ_REPO,
            capture_output=True, text=True, check=True).stdout.strip()
        with mock.patch.object(self.spec, "PAI", outro):
            with self.assertRaises(SystemExit) as ctx:
                self.spec.montar_pacote()
        self.assertIn("pai inesperado", str(ctx.exception))

    def test_tree_publicado_e_o_do_alvo_e_nao_o_do_checkout(self):
        # O gerador antigo lia `HEAD^{tree}` — o tree do CHECKOUT. So
        # coincidia com o do alvo porque o portao forcava HEAD == ALVO.
        # Agora o tree publicado e o do proprio ALVO, e por isso vale
        # mesmo com o checkout em outro commit.
        modulo = self.spec
        tree_alvo = subprocess.run(
            ["git", "rev-parse", f"{modulo.ALVO}^{{tree}}"], cwd=_RAIZ_REPO,
            capture_output=True, text=True, check=True).stdout.strip()
        tree_checkout = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=_RAIZ_REPO,
            capture_output=True, text=True, check=True).stdout.strip()
        pacote = modulo.montar_pacote()
        self.assertIn(f"tree:   {tree_alvo}", pacote)
        if tree_checkout != tree_alvo:
            self.assertNotIn(tree_checkout, pacote)


if __name__ == "__main__":
    unittest.main()
