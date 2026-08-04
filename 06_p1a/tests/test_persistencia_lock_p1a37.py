"""O escritor e reverificado no CAMINHO DE PERSISTENCIA — MAJOR #4.

O DEFEITO, na voz do revisor independente que o manteve NAO-FECHADO:
*"`revisao_p1a2.main` verifica o lock so antes da chamada e grava em
`SAIDA` sem reverificacao com o fence original; o teste novo exercita
apenas a funcao canonica, nao esse caminho de persistencia"*.

E a frase que o atestado destacou (§3.3): a Declaracao 4 em acao — a
correcao anterior fortaleceu `contencao.verificar_lock` e testou A
FUNCAO. A funcao estava certa; o PONTO DE CHAMADA e que nao existia.
Cobertura de linha da primitiva nao diz nada sobre quem a chama.

O CAMINHO QUE A OPERACAO PERCORRE, e nao o vizinho dele:

    main() -> _verificar_lock()            (abertura)
           -> subprocess.run(reviewer)     (ate 900 s; o lease vive 120)
           -> _verificar_lock(fence_esperado=...)   <- o que faltava
           -> SAIDA.write_text(...)        (persistencia)

Estes testes rodam `revisao_p1a2.main()` DE VERDADE, com um "reviewer"
que e um `python -c` e que, no meio da janela, substitui o fence ou mata
o lease — exatamente o que uma segunda sessao faria. A assercao que
importa nao e "levantou SystemExit": e **nenhum arquivo foi gravado**.
Escritor obsoleto que aborta depois de gravar nao corrigiu nada.

O vizinho recusado: chamar `contencao.verificar_lock` com um fence
errado e conferir que ela levanta. Isso ja existia — e foi exatamente o
que o revisor recusou como prova.

O QUE ESTES TESTES NAO COBREM, declarado:
- nenhum CLI real e invocado; o reviewer e um processo Python local. O
  que se exerce e o protocolo de escritor unico, nunca o provedor;
- nao provam nada sobre corrida REAL entre dois processos: a
  substituicao de titular e encenada gravando o `.fence`, nao
  disputando o lock do SO. Exclusao mutua entre missoes segue sendo o
  ACHADO 4, tratado em separado;
- a varredura dos cinco runners e ESTRUTURAL (AST) para tres deles —
  `revisao_p1a3`, `revisao_p1a33` e `revisao_p1a36` —, e comportamental
  so para `revisao_p1a2` e `revisao_p1a31`. Estrutura nao e
  comportamento, e isto fica dito e nao presumido;
- nao cobrem `preflight_capsula` nem `07_p1b/preflight_atual`, que tem
  cobertura propria noutras suites.
"""

import ast
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import apoio  # (insere 06_p1a no sys.path e traz `escrever_lock`)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

# Os CINCO runners de revisao do acervo.
RUNNERS = ("revisao_p1a2", "revisao_p1a3", "revisao_p1a31",
           "revisao_p1a33", "revisao_p1a36")

# Arquivos que `revisao_p1a2.montar_prompt` le da arvore. Sao copiados
# para a raiz descartavel para que `main()` corra INTEIRA — trocar
# `montar_prompt` por um duplo faria o teste deixar de exercer o caminho.
FONTES_DO_PROMPT = (
    "06_p1a/capsula.py",
    "06_p1a/preflight/adaptadores.py",
    "06_p1a/tests/test_capsula_p1a2.py",
    "06_p1a/06_adendo-capsula-p1a2.md",
)


def _carregar(nome):
    caminho = os.path.join(_DIR_P1A, "evidencias", f"{nome}.py")
    spec = importlib.util.spec_from_file_location(f"{nome}_lock_sob_teste",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# P1-A.5, ordem 2: a copia local morreu; ver `apoio.escrever_lock`.
_escrever_lock = apoio.escrever_lock


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


class ReverificacaoAntesDeGravar(unittest.TestCase):
    """`revisao_p1a2.main()` de verdade, com titular trocado na janela."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-lock-")
        self.raiz = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        for rel in FONTES_DO_PROMPT:
            destino = self.raiz / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(os.path.join(_RAIZ_REAL, *rel.split("/")), destino)
        self.saida = self.raiz / "06_p1a" / "evidencias" / "revisao-p1a2"

    def _rodar(self, corpo_do_reviewer, fence=7):
        modulo = _carregar("revisao_p1a2")
        _escrever_lock(str(self.raiz / "locks"), modulo.SESSAO_LOCK, fence,
                       time.time() + 600)
        env_minimo = {k: os.environ[k] for k in
                      ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
                       "PATHEXT") if k in os.environ}
        with mock.patch.dict(os.environ, env_minimo, clear=True), \
                mock.patch.object(modulo, "RAIZ", self.raiz), \
                mock.patch.object(modulo, "SAIDA", self.saida), \
                mock.patch.object(modulo, "COMANDOS", {
                    "codex": lambda tmp, prompt: [
                        sys.executable, "-c", corpo_do_reviewer]}), \
                mock.patch.object(sys, "argv",
                                  ["revisao_p1a2.py", "codex"]), \
                mock.patch("sys.stdout", _SaidaMuda()):
            return modulo.main()

    def _gravados(self):
        if not self.saida.is_dir():
            return []
        return sorted(p.name for p in self.saida.iterdir())

    def _reviewer_que_troca_o_fence(self, novo):
        from escritor_repositorio import caminho_fence
        caminho = caminho_fence(str(self.raiz / "locks")).replace("\\", "\\\\")
        return ("import os\n"
                f"open(r'{caminho}', 'w').write('{novo}')\n")

    def test_titular_substituido_na_janela_nao_grava_um_byte(self):
        with self.assertRaises(SystemExit) as ctx:
            self._rodar(self._reviewer_que_troca_o_fence(99), fence=7)
        self.assertIn("titular do escritor substituido", str(ctx.exception))
        # A assercao que importa: nada foi persistido.
        self.assertEqual(self._gravados(), [])

    def test_lease_morto_na_janela_nao_grava_um_byte(self):
        from escritor_repositorio import caminho_lease
        caminho = caminho_lease(str(self.raiz / "locks")).replace("\\", "\\\\")
        corpo = ("import json, time\n"
                 f"caminho = r'{caminho}'\n"
                 "d = json.load(open(caminho))\n"
                 "d['expira_em'] = time.time() - 10\n"
                 "json.dump(d, open(caminho, 'w'))\n")
        with self.assertRaises(SystemExit) as ctx:
            self._rodar(corpo)
        self.assertIn("lease da sessao operacional morto",
                      str(ctx.exception))
        self.assertEqual(self._gravados(), [])

    def test_escritor_vivo_grava_e_declara_a_reverificacao(self):
        # Contraprova: sem ela, um `main()` que abortasse sempre passaria
        # nos dois testes acima.
        rc = self._rodar("print('revisao de mentira')")
        self.assertEqual(rc, 0)
        gravados = self._gravados()
        self.assertEqual(len(gravados), 1)
        with open(self.saida / gravados[0], encoding="utf-8") as f:
            evidencia = json.load(f)
        self.assertTrue(evidencia["lock_verificado_antes_da_persistencia"])
        self.assertEqual(evidencia["lock_escritor_unico"]["fence"], 7)


class ReverificacaoNoRunnerDaRevisaoIndependente(unittest.TestCase):
    """O segundo caso comportamental: `revisao_p1a31.main()`."""

    def test_fence_trocado_na_janela_impede_a_persistencia(self):
        import contencao
        modulo = _carregar("revisao_p1a31")
        with tempfile.TemporaryDirectory(prefix="p1a37-lock31-") as raiz:
            base = os.path.join(raiz, "locks")
            _escrever_lock(base, modulo.SESSAO_LOCK, 4, time.time() + 600)
            os.makedirs(os.path.join(raiz, "06_p1a"), exist_ok=True)
            agora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with open(os.path.join(raiz, "06_p1a",
                                   "tiers_declarados.json"), "w",
                      encoding="utf-8") as f:
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
            from escritor_repositorio import caminho_fence
            escapado = caminho_fence(base).replace("\\", "\\\\")
            corpo = f"open(r'{escapado}', 'w').write('42')\n"
            env_minimo = {k: os.environ[k] for k in
                          ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
                           "PATHEXT") if k in os.environ}
            with mock.patch.dict(os.environ, env_minimo, clear=True), \
                    mock.patch.object(
                        contencao, "ALVOS_VIGIADOS_FORA_DO_REPOSITORIO",
                        ()), \
                    mock.patch.object(modulo, "RAIZ", Path(raiz)), \
                    mock.patch.object(modulo, "SAIDA", saida), \
                    mock.patch.object(modulo, "COMANDOS", {
                        "kimi": lambda tmp, skills, prompt: [
                            sys.executable, "-c", corpo]}), \
                    mock.patch.object(sys, "argv",
                                      ["revisao_p1a31.py", "kimi", pacote]), \
                    mock.patch("sys.stdout", _SaidaMuda()):
                with self.assertRaises(SystemExit) as ctx:
                    modulo.main()
            self.assertIn("titular do escritor substituido",
                          str(ctx.exception))
            self.assertFalse(saida.is_dir(),
                             "nada pode ser gravado com escritor obsoleto")


class OsCincoRunnersReverificamAntesDeGravar(unittest.TestCase):
    """Varredura dos pontos de chamada — a licao do N4 aplicada aqui.

    A primitiva `contencao.verificar_lock` esta correta ha tres missoes.
    O que faltava era um PONTO DE CHAMADA, e um ponto de chamada so
    aparece varrendo todos eles.
    """

    def _main_de(self, nome):
        caminho = os.path.join(_DIR_P1A, "evidencias", f"{nome}.py")
        with open(caminho, encoding="utf-8") as f:
            arvore = ast.parse(f.read(), filename=caminho)
        for no in ast.walk(arvore):
            if isinstance(no, ast.FunctionDef) and no.name == "main":
                return no
        self.fail(f"{nome} nao tem main()")

    def test_todo_runner_chama_a_verificacao_com_fence_esperado(self):
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                chamadas = [
                    no for no in ast.walk(self._main_de(nome))
                    if isinstance(no, ast.Call)
                    and isinstance(no.func, ast.Name)
                    and no.func.id == "_verificar_lock"]
                com_fence = [c for c in chamadas
                             if any(k.arg == "fence_esperado"
                                    for k in c.keywords)]
                self.assertTrue(
                    chamadas, "main() nao verifica o escritor")
                self.assertTrue(
                    com_fence,
                    "main() nunca reverifica com o fence da abertura: "
                    "e o defeito exato do MAJOR #4")

    def test_a_reverificacao_vem_ANTES_da_gravacao(self):
        # Reverificar depois de gravar seria pior que nao reverificar:
        # daria a aparencia do guarda sem a sua funcao.
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                main = self._main_de(nome)
                linha_reverificacao = min(
                    no.lineno for no in ast.walk(main)
                    if isinstance(no, ast.Call)
                    and isinstance(no.func, ast.Name)
                    and no.func.id == "_verificar_lock"
                    and any(k.arg == "fence_esperado" for k in no.keywords))
                # So a gravacao da EVIDENCIA conta. Os cinco runners
                # tambem escrevem o pacote DENTRO do descartavel, com
                # `f.write`, e isso acontece antes da chamada por
                # construcao — incluir essa escrita mediria outra coisa.
                escritas = [no.lineno for no in ast.walk(main)
                            if isinstance(no, ast.Call)
                            and isinstance(no.func, ast.Attribute)
                            and no.func.attr == "write_text"]
                self.assertTrue(escritas,
                                f"{nome}: main() nao persiste evidencia?")
                self.assertLess(linha_reverificacao, min(escritas))


if __name__ == "__main__":
    unittest.main()
