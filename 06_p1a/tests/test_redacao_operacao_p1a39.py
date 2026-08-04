"""Redacao no PONTO DE CHAMADA, exercida em OPERACAO — SSC+ P1-A.3.9.

MECANISMO (a) da FASE 2 da P1-A.3.8: *primitiva exercida, ponto de
chamada nao*. Sete dos nove guardas daquele mecanismo sao redacao
(`P1A-30`, `P1A-31`, `P1A-32`, `P1A-34`, `P1A-35`, `P1A-36`, `P1A-37`).
A remedicao mediu, um por um, que o acervo tinha:

- a PRIMITIVA coberta por comportamento (`RedacaoDosRunners`,
  `RedacaoDosGeradores` em `test_redacao_p1a35.py`);
- o PONTO DE CHAMADA coberto por ESTRUTURA (AST) em
  `test_redacao_call_sites_p1a37.py`, que declara ele mesmo: *"estrutura
  nao e comportamento"*;
- e `preflight_capsula` fora dos DOIS corpora — sem cobertura
  comportamental nem estrutural.

Este arquivo fecha o mecanismo, nao os guardas um a um: roda o `main()`
REAL de cada escritor de evidencia JSON do acervo e varre o ARQUIVO
GRAVADO.

## O corpus e DESCOBERTO, nunca listado

`RedacaoDosRunners.RUNNERS` e `test_redacao_call_sites_p1a37.RUNNERS`
sao tuplas escritas a mao, e nada as prende ao acervo: um escritor novo
— ou um que ninguem lembrou de acrescentar — fica de fora e a suite
segue verde. Foi assim que `preflight_capsula` ficou sem cobertura
nenhuma, e MEDIDO nesta missao que `revisao_p1a36` nunca entrou em
`RedacaoDosRunners.RUNNERS`.

E o mesmo padrao do defeito vivo 2 da P1-A.3.8 (lista que nada prende),
aplicado a um corpus de teste em vez de a uma constante de producao.

O corpus daqui e derivado por AST da propria arvore: todo modulo do
acervo que passa um `json.dumps` por redacao e grava o resultado. Um
escritor novo entra sozinho; se nao tiver prova comportamental
registrada, `OCorpusEDescobertoNaoListado` reprova com o nome dele.

## O CASO QUE OCORRE, e por que este e ele

Dois fatos MEDIDOS nesta estacao sustentam que o caminho exercido e o da
operacao, e nao um vizinho:

1. `tempfile.mkdtemp` cria o descartavel sob um caminho que carrega o
   nome do usuario local na forma 8.3 — o teste o remede a cada corrida
   (`test_o_descartavel_real_carrega_o_usuario`), de modo que a prova
   nao pode ficar verde por o temp da estacao ter deixado de carregar
   PII;
2. a resposta do revisor volta pelo `stdout` do CLI e vai INTEIRA para o
   campo `resposta`. O revisor le o pacote DENTRO do descartavel, cujo
   caminho carrega o usuario: uma resposta que cite o caminho traz PII
   por construcao. O comando falso deste teste devolve exatamente esse
   texto — as tres formas que a canonica conhece.

Para os dois runners de preflight o campo que carrega PII em operacao e
`frota[].caminho`. Nao e suposicao: os artefatos REAIS
`07_p1b/evidencias/preflight-20260730T162725Z.json` e
`preflight-20260730T163152Z.json` gravam
`"caminho": "C:\\\\Users\\\\<USUARIO>\\\\AppData\\\\..."` — o marcador so
existe porque a redacao agiu ali.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nenhum CLI real e invocado.** O comando de cada corrida e um
  `python -c` que imprime texto fixo; o que se prova e o tratamento da
  SAIDA, nunca o comportamento do revisor;
- a redacao cobre nome de usuario (forma longa e 8.3) e os prefixos de
  `PREFIXOS_DE_CAMINHO_LOCAL`. Nome de maquina, IP, e-mail e qualquer
  outra PII **nao** sao redigidos por este mecanismo e nao sao
  verificados aqui;
- os GERADORES de pacote (`pacote_p1a31`, `pacote_p1a33`,
  `pacote_p1a36`, `pacote_p1a37`) montam texto por concatenacao, nao por
  `json.dumps`: estao FORA do corpus deste arquivo e sao objeto de
  correcao propria;
- `pipeline.py:115` grava hoje a forma `~` em `frota[].caminho`, de modo
  que o documento produzido pela frota DESTA estacao nao carrega o nome
  do usuario por esse campo. O que se exerce e o portao de saida —
  documento com PII entra, arquivo sem PII sai —, que e o que os dois
  artefatos historicos citados acima mostram tendo agido;
- nada aqui afirma que a redacao seja SUFICIENTE: ela e a ultima porta,
  e uma porta exercida nao e uma politica completa.
"""

import ast
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

import contencao  # noqa: E402

# Resolvido no IMPORT, antes de qualquer `mock.patch.dict(os.environ)`:
# dentro do ambiente minimo das corridas nao ha `USERPROFILE`, e
# `os.path.expanduser("~")` devolveria `~` — o campo perderia a PII que
# esta prova existe para medir.
_HOME_REAL = os.path.expanduser("~")

# Raizes do acervo varridas pela descoberta. `tests/` fica de fora: o
# objeto sao os ESCRITORES de evidencia, nao quem os exercita.
_RAIZES_DO_ACERVO = ((_DIR_P1A, ("tests", "__pycache__", "evidencias")),
                     (_DIR_EVID, ("__pycache__",)),
                     (os.path.join(_RAIZ_REAL, "07_p1b"),
                      ("__pycache__", "evidencias")))


def _e_chamada_de_redacao(no) -> bool:
    return (isinstance(no, ast.Call) and isinstance(no.func, ast.Name)
            and no.func.id in ("_redigir", "redigir"))


def _redige_um_documento_json(fonte: str) -> bool:
    """O modulo passa um `json.dumps(...)` INTEIRO por redacao?

    E a assinatura do escritor de evidencia: redigir campo a campo deixa
    de fora todo campo novo; o que a correcao do achado N4 exige e a
    redacao do DOCUMENTO.
    """
    try:
        arvore = ast.parse(fonte)
    except SyntaxError:
        return False
    for no in ast.walk(arvore):
        if not _e_chamada_de_redacao(no):
            continue
        for dentro in ast.walk(no):
            if (isinstance(dentro, ast.Call)
                    and isinstance(dentro.func, ast.Attribute)
                    and dentro.func.attr == "dumps"):
                return True
    return False


def _escritores_descobertos() -> tuple:
    """Rotulo -> caminho de todo escritor de evidencia JSON do acervo."""
    achados = {}
    for raiz, ignorados in _RAIZES_DO_ACERVO:
        if not os.path.isdir(raiz):
            continue
        for nome in sorted(os.listdir(raiz)):
            caminho = os.path.join(raiz, nome)
            if not os.path.isfile(caminho) or not nome.endswith(".py"):
                continue
            if nome in ignorados:
                continue
            with open(caminho, encoding="utf-8") as f:
                fonte = f.read()
            if _redige_um_documento_json(fonte):
                achados[nome[:-3]] = caminho
    return tuple(sorted(achados.items()))


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


def _carregar(caminho: str, apelido: str):
    spec = importlib.util.spec_from_file_location(apelido, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _texto_com_pii() -> str:
    """As tres formas que a canonica conhece, montadas em tempo de execucao.

    Montado a partir de `contencao`, nunca literal: um literal aqui faria
    `ZeroPiiNosArtefatos` (`test_estabilizacao_p1a1.py`) reprovar este
    proprio arquivo, e com razao.
    """
    usuario = contencao._USUARIO_LOCAL
    return (f"lar={usuario} curto={contencao.forma_8_3(usuario)} "
            f"raiz={contencao.PREFIXOS_DE_CAMINHO_LOCAL[1]}/SSC-Plus/x")


def _sem_pii(caso, texto: str, onde: str) -> None:
    """Nenhuma das tres formas sobrevive no arquivo gravado."""
    usuario = contencao._USUARIO_LOCAL
    caso.assertNotIn(usuario, texto, f"{onde}: forma longa do usuario")
    caso.assertNotIn(contencao.forma_8_3(usuario), texto,
                     f"{onde}: forma 8.3 do usuario")
    for prefixo in contencao.PREFIXOS_DE_CAMINHO_LOCAL:
        caso.assertNotIn(prefixo, texto, f"{onde}: prefixo de caminho local")


def _preparar_lock(raiz: Path, sessao: str, fence: int = 7) -> None:
    # P1-A.5, ordem 2: a copia local morreu; ver `apoio.escrever_lock`.
    apoio.escrever_lock(str(raiz / "locks"), sessao, fence, time.time() + 600)


def _env_minimo() -> dict:
    return {k: os.environ[k] for k in
            ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC", "PATHEXT")
            if k in os.environ}


def _preparar_tiers(raiz: Path) -> None:
    """Declaracao VALIDA no instante — o portao de tier nao e o objeto aqui.

    Os runners da P1-A.3.1 em diante param antes de tudo se o tier
    declarado estiver vencido; sem esta fixture a corrida nunca chega ao
    ponto de chamada da redacao. O portao em si e exercido por
    `test_portao_tier_operacao_p1a39.py`.
    """
    destino = raiz / "06_p1a"
    destino.mkdir(parents=True, exist_ok=True)
    agora = (datetime.now(timezone.utc) - timedelta(hours=1)
             ).strftime("%Y-%m-%dT%H:%M:%SZ")
    (destino / "tiers_declarados.json").write_text(
        json.dumps({"validade_maxima_horas": 24, "declaracoes": [
            {"provider_id": "codex", "tier": "ChatGPT Pro 5x",
             "declarado_por": "proprietario", "declarado_em_utc": agora,
             "validade_horas": 24}]}), encoding="utf-8")


# Runners de revisao: `main()` recebe o provider em argv e, a partir da
# P1-A.3.1, tambem o caminho do pacote. `fontes` sao os arquivos que
# `montar_pacote()` le da arvore — sem eles o runner nao chega ao ponto
# de chamada da redacao.
_RUNNERS = {
    "revisao_p1a2": {"sessao": "p1a2-ops", "argv": 1, "saida": "revisao-p1a2",
                     "fontes": ("06_p1a/capsula.py",
                                "06_p1a/preflight/adaptadores.py",
                                "06_p1a/tests/test_capsula_p1a2.py",
                                "06_p1a/06_adendo-capsula-p1a2.md")},
    "revisao_p1a3": {"sessao": "p1a3-ops", "argv": 1, "saida": "revisao-p1a3",
                     "fontes": ("06_p1a/preflight/pipeline.py",
                                "06_p1a/preflight/sombra.py",
                                "06_p1a/preflight/adaptadores.py",
                                "06_p1a/preflight/frota_real.py",
                                "06_p1a/preflight/economia.py",
                                "06_p1a/tiers_declarados.json",
                                "06_p1a/tests/test_emendas_p1a3.py",
                                "06_p1a/07_adendo-emendas-p1a3.md")},
    "revisao_p1a31": {"sessao": "p1a31-ops", "argv": 2,
                      "saida": "revisao-p1a31", "fontes": ()},
    "revisao_p1a33": {"sessao": "p1a33-ops", "argv": 2,
                      "saida": "revisao-p1a33", "fontes": ()},
    "revisao_p1a36": {"sessao": "p1a36-ops", "argv": 2,
                      "saida": "revisao-p1a36", "fontes": ()},
    "revisao_p1a4": {"sessao": "p1a4-ops", "argv": 2,
                     "saida": "revisao-p1a4", "fontes": ()},
}

_PREFLIGHTS = {
    "preflight_capsula": {"sessao": "p1a3-ops",
                          "saida": ("06_p1a", "evidencias")},
    "preflight_atual": {"sessao": "p1b-ops", "saida": ("07_p1b",
                                                       "evidencias")},
}

# O registro que o corpus descoberto confronta. Chave = modulo; valor =
# a classe que o exerce COMPORTAMENTALMENTE neste arquivo.
EXERCIDOS = {nome: "OsRunnersGravamRedigido" for nome in _RUNNERS}
EXERCIDOS.update({nome: "OsPreflightsGravamRedigido" for nome in _PREFLIGHTS})


class OCorpusEDescobertoNaoListado(unittest.TestCase):
    """Prende o corpus a arvore: escritor novo sem prova reprova aqui."""

    def test_todo_escritor_de_evidencia_json_tem_prova_comportamental(self):
        descobertos = {nome for nome, _ in _escritores_descobertos()}
        faltando = sorted(descobertos - set(EXERCIDOS))
        self.assertEqual(
            faltando, [],
            "escritor de evidencia JSON sem prova comportamental de "
            f"redacao no ponto de chamada: {faltando}. Ou o modulo entra "
            "em EXERCIDOS com uma classe que rode o main() dele, ou ele "
            "grava PII sem ninguem ver — foi assim que preflight_capsula "
            "ficou fora dos dois corpora ate a P1-A.3.8")

    def test_o_registro_nao_tem_modulo_que_sumiu_da_arvore(self):
        # A outra ponta: registro que aponta para modulo inexistente
        # deixa de exercer e ninguem nota.
        descobertos = {nome for nome, _ in _escritores_descobertos()}
        self.assertEqual(sorted(set(EXERCIDOS) - descobertos), [])

    def test_a_descoberta_tem_alcance_real(self):
        # Guarda anti-varredura-vazia, no padrao de
        # `ZeroSegredoNosArtefatos.test_a_varredura_realmente_le_arquivos`.
        descobertos = {nome for nome, _ in _escritores_descobertos()}
        self.assertGreaterEqual(len(descobertos), 7)
        self.assertIn("preflight_capsula", descobertos)
        self.assertIn("preflight_atual", descobertos)

    def test_o_detector_reprova_um_escritor_sem_redacao(self):
        # CONTROLE POSITIVO. Sem ele, um detector que devolvesse False
        # sempre deixaria o corpus vazio e os dois testes acima verdes.
        com = "import json\ndef m():\n    return _redigir(json.dumps(d))\n"
        sem = "import json\ndef m():\n    return json.dumps(d)\n"
        campo = "import json\ndef m():\n    return _redigir(d['x'])\n"
        self.assertTrue(_redige_um_documento_json(com))
        self.assertFalse(_redige_um_documento_json(sem))
        self.assertFalse(_redige_um_documento_json(campo))


class OsRunnersGravamRedigido(unittest.TestCase):
    """`main()` REAL dos cinco runners; a varredura e do arquivo gravado."""

    def _rodar(self, nome: str) -> str:
        espec = _RUNNERS[nome]
        with tempfile.TemporaryDirectory(prefix="p1a39-red-") as bruto:
            raiz = Path(bruto)
            for rel in espec["fontes"]:
                destino = raiz / rel
                destino.parent.mkdir(parents=True, exist_ok=True)
                origem = os.path.join(_RAIZ_REAL, *rel.split("/"))
                with open(origem, encoding="utf-8") as f:
                    dados = f.read()
                destino.write_text(dados, encoding="utf-8")
            saida = raiz / "06_p1a" / "evidencias" / espec["saida"]
            _preparar_lock(raiz, espec["sessao"])
            _preparar_tiers(raiz)
            pacote = raiz / "pacote.txt"
            pacote.write_bytes(b"pacote de prova")
            modulo = _carregar(os.path.join(_DIR_EVID, f"{nome}.py"),
                               f"p1a39_{nome}")
            argv = ["runner.py", "codex"]
            if espec["argv"] == 2:
                argv.append(str(pacote))
            # A resposta do revisor volta pelo stdout e vai INTEIRA para
            # o campo `resposta`: e por ali que a PII entra em operacao.
            script = ("import sys;sys.stdout.write(sys.argv[1])",)
            with mock.patch.object(modulo, "RAIZ", raiz), \
                    mock.patch.object(modulo, "SAIDA", saida), \
                    mock.patch.object(modulo, "COMANDOS", {
                        "codex": lambda *a: [sys.executable, "-c", script[0],
                                             _texto_com_pii()]}), \
                    mock.patch.object(
                        contencao, "ALVOS_VIGIADOS_FORA_DO_REPOSITORIO",
                        ()), \
                    mock.patch.dict(os.environ, _env_minimo(), clear=True), \
                    mock.patch.object(sys, "argv", argv), \
                    mock.patch("sys.stdout", _SaidaMuda()):
                modulo.main()
            gravados = sorted(p for p in saida.iterdir() if p.is_file())
            self.assertEqual(len(gravados), 1, f"{nome}: gravados {gravados}")
            return gravados[0].read_text(encoding="utf-8")

    def test_o_arquivo_gravado_de_cada_runner_nao_carrega_pii(self):
        for nome in sorted(_RUNNERS):
            with self.subTest(runner=nome):
                _sem_pii(self, self._rodar(nome), nome)

    def test_a_redacao_agiu_e_o_documento_nao_estava_limpo(self):
        # DISCRIMINADOR do proprio teste acima: sem esta metade, um
        # runner que gravasse `{}` passaria. Exige o MARCADOR — prova de
        # que havia PII e ela foi substituida, nao de que nunca houve.
        for nome in sorted(_RUNNERS):
            with self.subTest(runner=nome):
                evidencia = json.loads(self._rodar(nome))
                self.assertIn("<USUARIO>", evidencia["dir_descartavel"])
                self.assertIn("<USUARIO>", evidencia["resposta"])
                self.assertIn("<CAMINHO-LOCAL>", evidencia["resposta"])

    def test_o_descartavel_real_carrega_o_usuario(self):
        # Sem esta medicao a prova acima poderia ficar verde por o temp
        # da estacao ter deixado de carregar PII — verde por acidente.
        with tempfile.TemporaryDirectory(prefix="p1a39-medicao-") as t:
            usuario = contencao._USUARIO_LOCAL
            self.assertTrue(
                usuario in t or contencao.forma_8_3(usuario) in t,
                f"o temp desta estacao nao carrega o usuario: {t!r}")


class OsPreflightsGravamRedigido(unittest.TestCase):
    """`main()` REAL dos dois runners de preflight, sem sonda nenhuma."""

    class _RelatorioFalso:
        """Relatorio com o campo que carrega PII em operacao.

        `caminho` e o campo medido nos artefatos reais
        `07_p1b/evidencias/preflight-20260730T16*.json`, onde ele saiu
        como `C:\\Users\\<USUARIO>\\AppData\\...` — o marcador so existe
        porque a redacao agiu sobre ele.
        """

        provider_id = "codex"

        def to_dict(self) -> dict:
            return {"provider_id": "codex", "resultado": "SUPERVISED",
                    "caminho": os.path.join(_HOME_REAL, "AppData",
                                            "cli.exe"),
                    "versao": None, "plano": None,
                    "origem_credencial": "ausente",
                    "quota": "desconhecida", "modelos": [], "sombra": None,
                    "erros": [{"codigo": "P1A-CLI-INDISPONIVEL",
                               "detalhe": _texto_com_pii(), "alvo": None}]}

    def _rodar(self, nome: str) -> str:
        espec = _PREFLIGHTS[nome]
        subdir = ("06_p1a" if nome == "preflight_capsula" else "07_p1b")
        caminho = os.path.join(_RAIZ_REAL, subdir, f"{nome}.py")
        with tempfile.TemporaryDirectory(prefix="p1a39-pre-") as bruto:
            raiz = Path(bruto)
            _preparar_lock(raiz, espec["sessao"])
            modulo = _carregar(caminho, f"p1a39_{nome}")
            falso = self._RelatorioFalso()
            remendos = [mock.patch.object(modulo, "_RAIZ", str(raiz)),
                        mock.patch.dict(os.environ, _env_minimo(),
                                        clear=True),
                        mock.patch("sys.stdout", _SaidaMuda())]
            if nome == "preflight_capsula":
                remendos.append(mock.patch.object(
                    modulo, "classificar_frota", lambda *a, **k: [falso]))
            else:
                remendos.append(mock.patch.object(
                    modulo, "frota_real", lambda: [falso]))
                remendos.append(mock.patch.object(
                    modulo, "executar_preflight", lambda *a, **k: falso))
                remendos.append(mock.patch.object(
                    modulo, "_config_persistida", lambda pid: {}))
            for remendo in remendos:
                remendo.start()
                self.addCleanup(remendo.stop)
            modulo.main()
            for remendo in remendos:
                remendo.stop()
            self.addCleanup(lambda: None)
            destino = raiz.joinpath(*espec["saida"])
            gravados = sorted(p for p in destino.iterdir() if p.is_file())
            self.assertEqual(len(gravados), 1, f"{nome}: {gravados}")
            return gravados[0].read_text(encoding="utf-8")

    def test_o_arquivo_gravado_de_cada_preflight_nao_carrega_pii(self):
        for nome in sorted(_PREFLIGHTS):
            with self.subTest(runner=nome):
                _sem_pii(self, self._rodar(nome), nome)

    def test_a_redacao_agiu_sobre_o_campo_que_carrega_pii_em_operacao(self):
        # DISCRIMINADOR: exige o marcador NO CAMPO `caminho` da frota —
        # exatamente onde os dois artefatos historicos o mostram.
        for nome in sorted(_PREFLIGHTS):
            with self.subTest(runner=nome):
                documento = json.loads(self._rodar(nome))
                self.assertIn("<USUARIO>", documento["frota"][0]["caminho"])
                self.assertIn("<CAMINHO-LOCAL>",
                              documento["frota"][0]["erros"][0]["detalhe"])

    def test_o_home_desta_estacao_carrega_o_usuario(self):
        # Contraparte da medicao dos runners: se o home deixasse de
        # conter o nome do usuario, o campo `caminho` nao carregaria PII
        # e a prova acima ficaria verde por acidente.
        self.assertIn(contencao._USUARIO_LOCAL, _HOME_REAL)


if __name__ == "__main__":
    unittest.main()
