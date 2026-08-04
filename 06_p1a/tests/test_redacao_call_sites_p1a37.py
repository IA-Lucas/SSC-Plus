"""Redacao nos PONTOS DE CHAMADA, nao so na primitiva — N4.

O DEFEITO, medido linha a linha pelo revisor independente e confirmado
pelo atestado: `revisao_p1a2.py` gravava `"dir_descartavel": tmp` CRU e
escrevia `json.dumps(meta…)` SEM redacao integral, enquanto os outros
QUATRO runners faziam `_redigir(tmp)` e `_redigir(json.dumps(…))`.
Quatro corrigidos, um esquecido — o mecanismo do achado 10 e da correcao
7: a copia que ninguem exercita fica para tras.

E o achado tem uma segunda camada, que o atestado nomeia: *"a varredura
o viu, mas por outro eixo — linha P1A-33, `revisao_p1a2.py:51 redacao`,
SEM-TESTE. Ela mediu a PRIMITIVA de redacao. Nao mediu os PONTOS DE
CHAMADA."* Classe nao medida: cobertura de call-site, nao de funcao.

O CAMINHO QUE A OPERACAO PERCORRE. O temp desta estacao e
`C:\\Users\\<forma 8.3 do usuario>\\AppData\\Local\\Temp\\…`, e e
exatamente ali que `tempfile.mkdtemp` cria o descartavel. Logo, em
operacao, `dir_descartavel` carrega PII por construcao — nao por
acidente. O teste comportamental abaixo roda `revisao_p1a2.main()` DE
VERDADE, com o descartavel real, e varre o ARQUIVO GRAVADO.

O vizinho recusado: chamar `contencao.redigir("texto com usuario")` e
conferir a saida. Isso ja existia (`test_redacao_p1a35.py`) e nao teria
pego este defeito — a primitiva sempre esteve certa.

O QUE ESTES TESTES NAO COBREM, declarado:
- a varredura dos cinco e ESTRUTURAL (AST) para quatro deles e
  comportamental so para `revisao_p1a2`. Estrutura nao e comportamento;
- a redacao cobre nome de usuario (forma longa e 8.3) e prefixo de
  caminho local declarado em `PREFIXOS_DE_CAMINHO_LOCAL`. Outra PII —
  nome de maquina, IP, e-mail — NAO e redigida por este mecanismo e nao
  e verificada aqui;
- nao se afirma nada sobre a resposta do provedor conter PII de terceiro:
  ela passa pela mesma redacao, que so conhece os alvos declarados;
- nenhum CLI real e invocado.
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

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

RUNNERS = ("revisao_p1a2", "revisao_p1a3", "revisao_p1a31",
           "revisao_p1a33", "revisao_p1a36")

FONTES_DO_PROMPT = (
    "06_p1a/capsula.py",
    "06_p1a/preflight/adaptadores.py",
    "06_p1a/tests/test_capsula_p1a2.py",
    "06_p1a/06_adendo-capsula-p1a2.md",
)


def _fonte_de(nome):
    caminho = os.path.join(_DIR_P1A, "evidencias", f"{nome}.py")
    with open(caminho, encoding="utf-8") as f:
        return ast.parse(f.read(), filename=caminho)


def _main_de(nome):
    for no in ast.walk(_fonte_de(nome)):
        if isinstance(no, ast.FunctionDef) and no.name == "main":
            return no
    raise AssertionError(f"{nome} nao tem main()")


def _e_chamada_de_redacao(no) -> bool:
    return (isinstance(no, ast.Call) and isinstance(no.func, ast.Name)
            and no.func.id in ("_redigir", "redigir"))


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


class OArquivoGravadoNaoCarregaPii(unittest.TestCase):
    """`revisao_p1a2.main()` de verdade, com o descartavel REAL."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-pii-")
        self.raiz = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        for rel in FONTES_DO_PROMPT:
            destino = self.raiz / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(os.path.join(_RAIZ_REAL, *rel.split("/")), destino)
        self.saida = self.raiz / "06_p1a" / "evidencias" / "revisao-p1a2"

    def _rodar(self):
        caminho = os.path.join(_DIR_P1A, "evidencias", "revisao_p1a2.py")
        spec = importlib.util.spec_from_file_location("p1a2_pii", caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        # P1-A.5, ordem 2: a copia local morreu; ver `apoio.escrever_lock`.
        apoio.escrever_lock(str(self.raiz / "locks"), modulo.SESSAO_LOCK, 3,
                            time.time() + 600)
        env_minimo = {k: os.environ[k] for k in
                      ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
                       "PATHEXT") if k in os.environ}
        with mock.patch.dict(os.environ, env_minimo, clear=True), \
                mock.patch.object(modulo, "RAIZ", self.raiz), \
                mock.patch.object(modulo, "SAIDA", self.saida), \
                mock.patch.object(modulo, "COMANDOS", {
                    "codex": lambda tmp, prompt: [
                        sys.executable, "-c", "print('revisao falsa')"]}), \
                mock.patch.object(sys, "argv",
                                  ["revisao_p1a2.py", "codex"]), \
                mock.patch("sys.stdout", _SaidaMuda()):
            rc = modulo.main()
        gravados = sorted(self.saida.iterdir())
        self.assertEqual(len(gravados), 1)
        return rc, gravados[0].read_text(encoding="utf-8")

    def test_o_arquivo_gravado_nao_carrega_o_usuario_local(self):
        rc, texto = self._rodar()
        self.assertEqual(rc, 0)
        longo = os.path.basename(os.path.expanduser("~"))
        curto = contencao.forma_8_3(longo)
        self.assertNotIn(longo, texto)
        self.assertNotIn(curto, texto)

    def test_o_descartavel_real_carregava_a_forma_8_3(self):
        # Sem esta medicao o teste acima poderia estar verde por o temp
        # da estacao nao conter PII nenhuma — verde por acidente, nao por
        # redacao. Aqui se mede que o caminho REAL do descartavel carrega
        # o nome do usuario numa das duas formas.
        with tempfile.TemporaryDirectory(prefix="p1a37-medicao-") as t:
            longo = os.path.basename(os.path.expanduser("~"))
            curto = contencao.forma_8_3(longo)
            self.assertTrue(
                longo in t or curto in t,
                f"o temp desta estacao nao carrega o usuario: {t!r} — a "
                "prova comportamental de redacao perde o objeto e vira "
                "verde por acidente")

    def test_o_campo_dir_descartavel_sai_redigido(self):
        _, texto = self._rodar()
        evidencia = json.loads(texto)
        self.assertIn("<USUARIO>", evidencia["dir_descartavel"])

    def test_argv_publico_tambem_sai_redigido(self):
        # O revisor nomeou os DOIS campos. `argv_publico` recebe o mesmo
        # caminho cru quando o comando o passa (`--cd tmp`), e so a
        # redacao do documento INTEIRO o alcanca.
        _, texto = self._rodar()
        longo = os.path.basename(os.path.expanduser("~"))
        self.assertNotIn(longo, json.dumps(json.loads(texto)["argv_publico"]))


class OsCincoRunnersRedigemNosDoisPontos(unittest.TestCase):
    """Varredura de CALL-SITE — a classe que a varredura nao media."""

    def test_dir_descartavel_passa_por_redacao_em_todo_runner(self):
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                valores = [
                    valor for no in ast.walk(_main_de(nome))
                    if isinstance(no, ast.Dict)
                    for chave, valor in zip(no.keys, no.values)
                    if isinstance(chave, ast.Constant)
                    and chave.value == "dir_descartavel"]
                self.assertTrue(valores,
                                f"{nome}: campo dir_descartavel ausente")
                for valor in valores:
                    self.assertTrue(
                        _e_chamada_de_redacao(valor),
                        f"{nome}: dir_descartavel gravado CRU — e o "
                        "defeito literal do achado N4")

    def test_o_json_integral_passa_por_redacao_em_todo_runner(self):
        # Redigir campo a campo deixa de fora todo campo novo. O que a
        # correcao exige e a redacao do DOCUMENTO.
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                redigidos_com_json = [
                    no for no in ast.walk(_main_de(nome))
                    if _e_chamada_de_redacao(no)
                    and any(isinstance(f, ast.Call)
                            and isinstance(f.func, ast.Attribute)
                            and f.func.attr == "dumps"
                            for f in ast.walk(no))]
                self.assertTrue(
                    redigidos_com_json,
                    f"{nome}: o JSON vai para o disco sem redacao integral")

    def test_a_redacao_de_todo_runner_e_a_canonica(self):
        # Contraprova estrutural: um `_redigir` local que nao fizesse
        # nada passaria nos dois testes acima. Aqui se exige que a funcao
        # chamada seja, em valor, a canonica de `contencao`.
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                caminho = os.path.join(_DIR_P1A, "evidencias", f"{nome}.py")
                spec = importlib.util.spec_from_file_location(
                    f"{nome}_red", caminho)
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)
                usuario = "USUARIO-FICTICIO-DE-TESTE"
                with mock.patch.object(contencao, "_USUARIO_LOCAL",
                                       usuario):
                    saida = modulo._redigir(f"lar de {usuario} aqui")
                self.assertEqual(saida, "lar de <USUARIO> aqui")


if __name__ == "__main__":
    unittest.main()
