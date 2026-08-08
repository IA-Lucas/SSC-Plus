"""O pacote nao descarta em silencio — SSC+ P1-A.7.

O DEFEITO, achado pelo `codex` na revisao dupla da P1-A.6 e confirmado
antes de ser registrado (`99_decisao-p1a6.md` §13.4):

    `pacote_p1a37.py:montar_pacote` omite silenciosamente alteracoes
    nao-Python fora de `.md`/`.json`/`.txt`; assim, o `pytest.ini` da
    correcao P1-A.5.1 nao foi incluido nem hasheado.

Familia **(F)**: o gerador **AFIRMAVA** completude na docstring —
*"EXCLUSOES, todas declaradas e nenhuma silenciosa"* — enquanto o codigo
descartava todo caminho fora de quatro extensoes. Afirmar a propriedade
em vez de exerce-la e a familia do MAJOR #3.

O remedio especificado na §16 da P1-A.6 e literal, e e o que estes
testes exercem:

    todo caminho do `git diff --name-status` entra como conteudo, como
    hash **ou** como exclusao **nomeada**, e **falhar** se sobrar
    caminho nao classificado.

## O CAMINHO QUE A OPERACAO PERCORRE, e nao o vizinho dele

O par `(3f24085, 0a40667)` **nao e exemplo**: e o par exato do pacote
que os DOIS revisores da P1-A.6 leram e julgaram — 141 903 bytes,
SHA-256 `673271a7…`. Era desse pacote que faltava o `pytest.ini`. Testar
qualquer outro par mediria um vizinho.

O vizinho recusado, e ele era tentador: afirmar que `disposicao()`
devolve `"lido"` para a string `"pytest.ini"`. Isso exerce a primitiva,
nao o ponto de chamada — e o achado **N4** deste acervo existe
exatamente porque primitiva corrigida nao cobre ponto de chamada. O que
se afirma aqui e sobre os BYTES DO PACOTE que iriam ao revisor.

## O CONTROLE POSITIVO, nas duas polaridades

Um guarda que so sabe dizer "esta tudo certo" nao distingue arvore sa de
varredura quebrada. Por isso as duas metades:

- **acha o que deve achar** — `pytest.ini` aparece no pacote do par
  real, com disposicao e motivo;
- **acusa quando o defeito volta** — `conferir_cobertura` recebe um
  caminho fora das tres disposicoes e **levanta**. E a funcao REAL com
  dado REAL, nao um dublê.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nao provam que o pacote foi ENVIADO nem lido.** O alcance dos dois
  vereditos da P1-A.6 continua limitado pela falta do `pytest.ini`, e
  nenhuma linha `FECHADO` daquela revisao e reexaminada aqui;
- **nao provam que a classificacao LIDO/ANCORADO esteja CERTA** para
  cada arquivo — provam que ela e TOTAL. Um `.md` classificado como
  ancorado quando o revisor precisaria le-lo continua sendo perda de
  detalhe; o que estes testes fecham e a perda **silenciosa**;
- **nao cobrem renomeacao.** `git diff --name-status` com `-z` devolve
  `R` como par de caminhos, e o parser vigente trata `R` como
  modificacao. Nada aqui afirma que renomeacao esteja bem tratada;
- **nao medem o tamanho do pacote nem se ele cabe em revisor algum.**
"""

import importlib.util
import os
import subprocess
import sys
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

_GERADOR = os.path.join(_DIR_P1A, "evidencias", "pacote_p1a37.py")

# O par EXATO que a P1-A.6 submeteu aos dois revisores (§12.2).
BASE = "3f24085"
ALVO = "0a40667"

# O arquivo que sumia. Nao e `.py`, e `.ini` nao estava em
# `EXTENSOES_HASHEADAS` — caia fora dos dois ramos.
O_QUE_SUMIA = "pytest.ini"


def _carregar_gerador():
    spec = importlib.util.spec_from_file_location("pacote_p1a7_sob_teste",
                                                  _GERADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _tem_git() -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", ALVO],
                          cwd=_RAIZ, capture_output=True).returncode == 0


def _caminhos_do_diff() -> list:
    """A verdade contra a qual o pacote se mede: o proprio git."""
    saida = subprocess.run(
        ["git", "diff", "--name-status", "-z", BASE, ALVO], cwd=_RAIZ,
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", check=True).stdout
    campos = [c for c in saida.split("\0") if c]
    return sorted(campos[i + 1] for i in range(0, len(campos) - 1, 2))


@unittest.skipUnless(_tem_git(), "repositorio git indisponivel")
class OPacoteNaoDescartaEmSilencio(unittest.TestCase):
    """Sobre os BYTES do pacote do par realmente julgado."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar_gerador()
        cls.texto = cls.modulo.montar_pacote(BASE, ALVO)

    def test_o_pytest_ini_esta_no_pacote_do_par_que_foi_julgado(self):
        # A assercao central. Antes da P1-A.7 a unica ocorrencia da
        # string no pacote era uma MENCAO dentro da docstring do
        # `conftest.py` — o arquivo em si nao estava.
        self.assertIn(f"LIDO      {O_QUE_SUMIA}", self.texto,
                      "o pytest.ini nao entrou no pacote como arquivo — "
                      "e o defeito da P1-A.6 §13.4 intacto")

    def test_o_conteudo_do_pytest_ini_viaja_e_nao_so_o_nome(self):
        # Constar do manifesto e nao carregar os bytes seria trocar um
        # descarte silencioso por um descarte declarado.
        self.assertIn("addopts = -p no:cacheprovider", self.texto,
                      "o nome entrou no manifesto, os bytes nao")

    def test_todo_caminho_do_diff_aparece_no_manifesto_com_motivo(self):
        faltando = [rel for rel in _caminhos_do_diff()
                    if f" {rel}  — " not in self.texto]
        self.assertEqual(faltando, [],
                         f"caminhos ausentes do manifesto: {faltando}")

    def test_a_conta_do_manifesto_fecha_com_o_git(self):
        # O manifesto declara um total; se ele nao bater com o diff, o
        # numero e decoracao.
        esperado = len(_caminhos_do_diff())
        self.assertIn(f"caminhos no diff: {esperado}  =", self.texto)


@unittest.skipUnless(_tem_git(), "repositorio git indisponivel")
class OGuardaAcusaQuandoSobraCaminho(unittest.TestCase):
    """CONTROLE POSITIVO — a metade que acusa, com a funcao REAL."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar_gerador()

    def test_caminho_fora_das_tres_disposicoes_levanta(self):
        with self.assertRaises(self.modulo.CoberturaIncompleta) as ctx:
            self.modulo.conferir_cobertura(
                todos=["a.py", "pytest.ini"],
                lidos=["a.py"], ancorados=[], excluidos=[])
        self.assertIn("pytest.ini", str(ctx.exception))

    def test_nao_levanta_quando_a_cobertura_e_total(self):
        # Sem esta metade, um `raise` incondicional passaria no teste
        # acima e o guarda nao mediria nada.
        self.modulo.conferir_cobertura(
            todos=["a.py", "pytest.ini"],
            lidos=["a.py", "pytest.ini"], ancorados=[], excluidos=[])


class ODefaultEAncorarNuncaDescartar(unittest.TestCase):
    """A propriedade que impede o defeito de renascer numa extensao nova."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar_gerador()

    def test_extensao_que_o_gerador_nunca_viu_entra_ancorada(self):
        for rel in ("x/y.parquet", "z.bin", "sem_extensao",
                    "logs/d.patch", "s/c.sha256"):
            with self.subTest(rel=rel):
                disp, motivo = self.modulo.disposicao(rel)
                self.assertEqual(disp, "ancorado")
                self.assertTrue(motivo)

    def test_nenhuma_disposicao_significa_descartado(self):
        alvos = ("pytest.ini", ".gitignore", "06_p1a/.gitattributes",
                 "a.py", "b.sh", "r.md", "e.json", "q.parquet")
        for rel in alvos:
            with self.subTest(rel=rel):
                disp, _ = self.modulo.disposicao(rel)
                self.assertIn(disp, ("lido", "ancorado", "excluido"))


if __name__ == "__main__":
    unittest.main()
