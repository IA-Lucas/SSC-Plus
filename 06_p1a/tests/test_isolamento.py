"""Isolamento e restricoes da missao (SSC+ P1-A, experimental).

Transforma em teste executavel as restricoes que a missao impoe ao proprio
preflight: nao escreve arquivo, nao abre rede, nao invoca modelo
produtivo, nao aprova automaticamente e nao registra segredo. Duas provas
sao estruturais (varredura do proprio codigo-fonte) e duas sao empiricas
(o sistema de arquivos antes/depois de uma varredura completa da frota e a
ausencia de padrao de segredo nos artefatos gravados).
"""

import hashlib
import importlib.util
import json
import os
import re
import unittest

import apoio
import citacoes_declaradas
from apoio import sensores_dict
from preflight import ambiente_sanitizado, executar_preflight, frota_real

_DIR_TESTS = os.path.dirname(os.path.abspath(__file__))
DIR_P1A = os.path.dirname(_DIR_TESTS)
DIR_PREFLIGHT = os.path.join(DIR_P1A, "preflight")
DIR_PROVA = os.path.join(DIR_P1A, "evidencias", "prova-minima")

# Prompt exigido pela missao para a prova minima (unico, nao sensivel).
PROMPT_DA_MISSAO = ("Retorne apenas PROVIDER_OK e o identificador "
                    "público do modelo.")

# Padroes que casam VALORES de credencial (nao nomes de campo).
PADROES_DE_SEGREDO = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),            # OpenAI/Anthropic
    re.compile(r"\bxai-[A-Za-z0-9_-]{16,}"),           # xAI
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),           # Google
    re.compile(r"\bghp_[A-Za-z0-9]{20,}"),             # GitHub
    re.compile(r"\bey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."),  # JWT
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|auth[_-]?token|access[_-]?token)"
               r"\"?\s*[:=]\s*\"?[A-Za-z0-9_\-]{20,}"),
)

_EXTENSOES_TEXTO = (".py", ".md", ".json", ".txt", ".sh", ".cfg", ".toml")


def _fontes_do_preflight():
    return sorted(f for f in os.listdir(DIR_PREFLIGHT) if f.endswith(".py"))


def _ler(caminho):
    with open(caminho, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _arquivos_de_texto(raiz):
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in sorted(arquivos):
            if nome.lower().endswith(_EXTENSOES_TEXTO):
                yield os.path.join(base, nome)


def _instantaneo(raiz):
    """Caminho relativo -> sha256 de todo arquivo sob a raiz."""
    estado = {}
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for nome in sorted(arquivos):
            caminho = os.path.join(base, nome)
            with open(caminho, "rb") as fh:
                estado[os.path.relpath(caminho, raiz)] = \
                    hashlib.sha256(fh.read()).hexdigest()
    return estado


def _prova_minima_modulo():
    """Carrega evidencias/prova_minima.py sem executar o `main`."""
    caminho = os.path.join(DIR_P1A, "evidencias", "prova_minima.py")
    spec = importlib.util.spec_from_file_location("_prova_minima", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class CodigoNaoEscreveNemAbreRede(unittest.TestCase):
    """Varredura estrutural: o preflight e read-only e offline por dentro."""

    PROIBIDOS_GERAIS = (
        "shutil", "os.remove", "os.unlink", "os.rmdir", "os.makedirs",
        "os.mkdir", "os.rename", "write_text", "write_bytes", "mkdtemp",
        "urllib.request", "http.client", "requests.", "socket.",
        "os.environ[", "os.putenv", "os.system",
    )

    def test_nenhum_modulo_escreve_arquivo_ou_abre_rede(self):
        for nome in _fontes_do_preflight():
            fonte = _ler(os.path.join(DIR_PREFLIGHT, nome))
            for proibido in self.PROIBIDOS_GERAIS:
                with self.subTest(modulo=nome, proibido=proibido):
                    self.assertNotIn(proibido, fonte)

    def test_nenhum_modulo_abre_arquivo(self):
        for nome in _fontes_do_preflight():
            with self.subTest(modulo=nome):
                fonte = _ler(os.path.join(DIR_PREFLIGHT, nome))
                self.assertIsNone(re.search(r"(?<![A-Za-z])open\(", fonte))

    def test_subprocesso_existe_somente_no_sensor_real(self):
        for nome in _fontes_do_preflight():
            fonte = _ler(os.path.join(DIR_PREFLIGHT, nome))
            with self.subTest(modulo=nome):
                if nome == "adaptadores.py":
                    self.assertIn("subprocess.Popen", fonte)
                else:
                    self.assertNotIn("subprocess.Popen", fonte)

    def test_o_unico_subprocesso_roda_com_ambiente_sanitizado(self):
        fonte = _ler(os.path.join(DIR_PREFLIGHT, "adaptadores.py"))
        self.assertEqual(fonte.count("subprocess.Popen("), 1)
        trecho = fonte[fonte.index("def sensor_subprocess"):]
        trecho = trecho[:trecho.index("subprocess.Popen(")]
        self.assertIn("ambiente_sanitizado(env)", trecho)

    def test_ha_pelo_menos_os_quatro_modulos_do_preflight(self):
        self.assertTrue({"economia.py", "adaptadores.py", "frota_real.py",
                         "pipeline.py"} <= set(_fontes_do_preflight()))


class VarreduraNaoTocaOSistemaDeArquivos(unittest.TestCase):
    """Prova empirica: preflight completo dos 5 sem uma unica escrita."""

    def test_frota_inteira_nao_altera_nenhum_arquivo(self):
        antes = _instantaneo(DIR_P1A)
        for espec in frota_real():
            sens, _, _ = sensores_dict(espec.provider_id)
            executar_preflight(espec, sens, env={})
        self.assertEqual(_instantaneo(DIR_P1A), antes)

    def test_ambiente_global_do_usuario_permanece_intacto(self):
        antes = dict(os.environ)
        for espec in frota_real():
            sens, _, _ = sensores_dict(espec.provider_id)
            executar_preflight(espec, sens)
        self.assertEqual(dict(os.environ), antes)
        # A sanitizacao produz copia; nunca remove do processo real.
        ambiente_sanitizado()
        self.assertEqual(dict(os.environ), antes)


class ZeroSegredoNosArtefatos(unittest.TestCase):
    """Nenhum valor de credencial em codigo, doc, log ou evidencia."""

    def _varrer(self) -> dict:
        """rel -> n casamentos. Varre e nao julga."""
        por_arquivo = {}
        for caminho in _arquivos_de_texto(DIR_P1A):
            texto = _ler(caminho)
            n = sum(len(p.findall(texto)) for p in PADROES_DE_SEGREDO)
            if n:
                rel = os.path.relpath(caminho, DIR_P1A).replace(os.sep, "/")
                por_arquivo[rel] = n
        return por_arquivo

    def test_nenhum_padrao_de_segredo_em_06_p1a(self):
        # P1-A.9 ordem 3: os padroes continuam os mesmos. O que mudou e
        # que ARTEFATO DE VARREDURA declarado — que ecoa o valor casado
        # de proposito, para que um terceiro confira que e fixture —
        # deixa de contar como segredo. Ver `citacoes_declaradas`.
        self.assertEqual(
            citacoes_declaradas.nao_declarados(
                self._varrer(),
                citacoes_declaradas.ARTEFATOS_QUE_CITAM_FIXTURE),
            [], "possivel segredo em artefato NAO declarado")

    def test_declaracao_de_fixture_nao_pode_ser_decorativa(self):
        self.assertEqual(
            citacoes_declaradas.declaracoes_mortas(
                self._varrer(),
                citacoes_declaradas.ARTEFATOS_QUE_CITAM_FIXTURE, DIR_P1A),
            [], "declaracao que nao casa mais e decoracao")

    def test_arquivo_NAO_declarado_com_segredo_e_pego(self):
        # CONTROLE POSITIVO do lado da declaracao.
        self.assertEqual(
            citacoes_declaradas.nao_declarados(
                {"evidencias/inventado.json": 3},
                citacoes_declaradas.ARTEFATOS_QUE_CITAM_FIXTURE),
            ["evidencias/inventado.json"])

    def test_a_varredura_realmente_le_arquivos(self):
        # Guarda contra teste vazio: a varredura precisa ter alcance real.
        arquivos = list(_arquivos_de_texto(DIR_P1A))
        self.assertGreater(len(arquivos), 10)
        self.assertTrue(any(c.endswith("economia.py") for c in arquivos))

    def test_padroes_detectam_segredo_plantado(self):
        # Todas as amostras sao montadas por concatenacao: nenhuma linha
        # deste arquivo casa com os proprios padroes que ele varre.
        amostras = ("sk-" + "a" * 24, "xai-" + "b" * 24, "AIza" + "c" * 24,
                    "ghp_" + "d" * 24,
                    "ey" + "JhbGciOiJIUzI1" + "." + "eyJzdWIiOiIxMj" + ".x",
                    "Bearer " + "e" * 24, 'api_key: "' + "f" * 24 + '"')
        for amostra in amostras:
            with self.subTest(amostra=amostra[:12]):
                self.assertTrue(
                    any(p.search(amostra) for p in PADROES_DE_SEGREDO),
                    amostra[:12])


class ProvaMinimaRespeitaAsRestricoes(unittest.TestCase):
    """O script da prova minima e as evidencias que ele gravou."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _prova_minima_modulo()
        cls.registros = []
        if os.path.isdir(DIR_PROVA):
            for nome in sorted(os.listdir(DIR_PROVA)):
                if nome.endswith(".json"):
                    cls.registros.append(
                        (nome, json.loads(_ler(os.path.join(DIR_PROVA,
                                                            nome)))))

    def test_prompt_e_exatamente_o_da_missao(self):
        self.assertEqual(self.modulo.PROMPT, PROMPT_DA_MISSAO)

    def test_prompt_nao_carrega_conteudo_do_lucax(self):
        for termo in ("LucaX", "lucax", "constituicao", "ADR", "RD-",
                      "governanca", "canonico"):
            with self.subTest(termo=termo):
                self.assertNotIn(termo, self.modulo.PROMPT)

    def test_nenhum_comando_aprova_automaticamente(self):
        proibidos = ("--always-approve", "--auto-approve", "--yes", "-y",
                     "--dangerously-skip-permissions", "--api-key",
                     "--batch-api", "--full-auto")
        for provider, construir in self.modulo.COMANDOS.items():
            argv = construir("DIR")
            for proibido in proibidos:
                with self.subTest(provedor=provider, proibido=proibido):
                    self.assertNotIn(proibido, argv)

    def test_apenas_provedores_eligible_tem_comando(self):
        # Google e Grok sao SUPERVISED: nenhuma invocacao definida.
        self.assertEqual(set(self.modulo.COMANDOS),
                         {"codex", "claude", "kimi"})

    def test_execucao_ocorre_no_diretorio_descartavel(self):
        fonte = _ler(os.path.join(DIR_P1A, "evidencias", "prova_minima.py"))
        self.assertIn("cwd=tmp", fonte)
        self.assertIn("tempfile.mkdtemp", fonte)
        # Codex tambem recebe o diretorio explicitamente (--cd).
        argv = self.modulo.COMANDOS["codex"]("DIR")
        self.assertEqual(argv[argv.index("--cd") + 1], "DIR")

    def test_sanitizacao_do_script_e_a_canonica(self):
        # Unica implementacao (P1-A.1): o script importa
        # preflight.economia.ambiente_sanitizado — nenhuma copia local.
        from preflight import economia
        self.assertIs(self.modulo.ambiente_sanitizado,
                      economia.ambiente_sanitizado)
        fonte = _ler(os.path.join(DIR_P1A, "evidencias",
                                  "prova_minima.py"))
        self.assertNotIn("PADRAO_PAYG", fonte)
        self.assertNotIn("CHAVES_PROIBIDAS", fonte)

    def test_sanitizacao_canonica_cobre_todas_as_variantes(self):
        # Nomes nus, camelCase, hifen, caixa mista e credenciais de
        # provedor sao sanitizados; token local nao tarifado tambem sai
        # do subprocesso (sem bloquear a frota — escopo de BLOQUEIO e
        # coberto em test_economia).
        nomes = ["api_key", "apiKey", "api-key", "API-KEY",
                 "OPENAI_API_KEY", "OpenAI_Api_Key", "xai_api_key",
                 "X_ACCESS_TOKEN", "ALGO_API_SECRET", "NVIDIA_API_KEY",
                 "VSCODE_GIT_IPC_AUTH_TOKEN"]
        env = {n: "v" for n in nomes}
        env["PATH"] = "p"
        self.assertEqual(ambiente_sanitizado(env), {"PATH": "p"})

    def test_registros_gravados_declaram_custo_variavel_zero(self):
        self.assertTrue(self.registros, "nenhuma evidencia de prova minima")
        for nome, registro in self.registros:
            with self.subTest(evidencia=nome):
                self.assertEqual(registro["custo_variavel"], 0)
                self.assertEqual(registro["prompt"], PROMPT_DA_MISSAO)
                self.assertIn("assinatura-oauth", registro["rotulo"])
                # O argv publicado mascara o prompt e nao traz credencial.
                self.assertIn("<PROMPT>", registro["argv_publico"])

    def test_registros_nao_guardam_valor_de_variavel_removida(self):
        for nome, registro in self.registros:
            with self.subTest(evidencia=nome):
                # Somente NOMES das variaveis removidas, nunca valores.
                for var in registro["env_vars_removidas_nomes"]:
                    self.assertRegex(var, r"^[A-Za-z0-9_]+$")

    def test_diretorio_descartavel_vazio_quando_verificado(self):
        verificados = [(nome, r) for nome, r in self.registros
                       if "dir_descartavel_arquivos_restantes" in r]
        for nome, registro in verificados:
            with self.subTest(evidencia=nome):
                self.assertEqual(
                    registro["dir_descartavel_arquivos_restantes"], [])

    def test_diretorio_descartavel_fora_do_laboratorio(self):
        for nome, registro in self.registros:
            with self.subTest(evidencia=nome):
                self.assertNotIn("SSC-Plus", registro["dir_descartavel"])
                self.assertNotIn("LucaX", registro["dir_descartavel"])


if __name__ == "__main__":
    unittest.main()
