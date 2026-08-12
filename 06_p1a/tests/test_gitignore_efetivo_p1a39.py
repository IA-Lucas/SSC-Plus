"""O EFEITO do .gitignore, nao o TEXTO dele — SSC+ P1-A.3.9.

MECANISMO (c) da FASE 2 da P1-A.3.8, guarda `P1A-51`. A linha da
remedicao e literal:

    le o `.gitignore` real e exige a substring `locks/`. Afirma o TEXTO
    da regra, nao o EFEITO: uma regra de desempate posterior no mesmo
    arquivo tornaria a linha inerte e o teste seguiria verde.
    Remedio: `git check-ignore -q locks/<arquivo>`.

`test_estabilizacao_p1a1.test_estado_de_lock_e_ignorado_pelo_git` NAO
foi editado — registro aditivo. Ele continua provando que a linha
EXISTE. Este arquivo prova que ela DECIDE.

E a mesma distincao do achado #6 da P1-A.3.4, que a `contencao` ja
registrou por escrito: *"medir o cardapio nao e exercer a interface"*.
`--help` lista as flags isoladamente; so a invocacao revela a
incompatibilidade. Aqui: o `.gitignore` lista as regras; so
`check-ignore` revela qual delas vence.

## Por que uma regra de desempate e o caso que ocorre

O formato do `.gitignore` e ultima-regra-vence. Basta uma linha
`!locks/*.lease` depois de `locks/` — plausivel, e o tipo de coisa que
se acrescenta querendo "versionar so o lease para depurar" — para que a
linha `locks/` continue no arquivo, o guarda antigo continue verde, e o
estado de lock passe a entrar no Git. MEDIDO nesta missao: com essa
linha acrescentada, o acervo inteiro fica VERDE e este arquivo fica
vermelho.

## O QUE ESTES TESTES NAO COBREM, declarado

- **`check-ignore` responde sobre CAMINHOS, nao sobre historico**: um
  arquivo que ja tenha sido commitado continua rastreado mesmo estando
  ignorado, e isso nao e medido aqui;
- **so os caminhos declarados** em `RUNTIME_QUE_NAO_ENTRA` sao
  perguntados; qualquer outro estado de runtime que apareca no futuro
  nao e coberto por este guarda ate ser acrescentado;
- **nada se afirma sobre `.gitignore` global do usuario nem sobre
  `.git/info/exclude`**: `check-ignore` os considera, de modo que um
  caminho poderia estar ignorado por fora do repositorio. O teste de
  ORIGEM abaixo mede exatamente isso e exige que a decisao venha do
  `.gitignore` versionado;
- sem git, ou fora de um repositorio, os testes sao PULADOS em vez de
  mentir.
"""

import os
import subprocess
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P1A)

# Estado de RUNTIME que nunca pode entrar no Git, com o motivo ao lado.
# Cada entrada e perguntada ao Git pelo EFEITO, nunca lida do texto.
RUNTIME_QUE_NAO_ENTRA = {
    "locks/p1a39-ops.lease": "lease do escritor unico",
    "locks/p1a39-ops.lock": "lock do SO",
    "locks/p1a39-ops.fence": "fencing token",
    "locks/qualquer-sessao-futura.lease": "sessao que ainda nao existe",
    "05_p0/saidas/labs/tests/x/lab/cas/objeto": "CAS de laboratorio",
    "05_p0/saidas/labs/corrida/logs/eventos.jsonl": "EventLog bruto",
    "05_p0/saidas/labs/corrida/chave_selo.bin": "chave de selo local",
    "06_p1a/__pycache__/economia.cpython-314.pyc": "cache de bytecode",
    ".coverage": "traco de medicao",
}

# A outra ponta: caminhos que PRECISAM ser versionados. Sem eles, um
# `.gitignore` com uma linha `*` passaria em tudo acima.
O_QUE_PRECISA_ENTRAR = (
    "06_p1a/preflight/economia.py",
    "05_p0/ssc_p0/kernel.py",
    "05_p0/saidas/prova_central.json",
    "06_p1a/tests/test_gitignore_efetivo_p1a39.py",
    ".gitignore",
)


def _tem_git() -> bool:
    try:
        return subprocess.run(["git", "rev-parse", "--git-dir"],
                              cwd=_RAIZ_REPO,
                              capture_output=True).returncode == 0
    except OSError:
        return False


def _ignorado(caminho: str) -> bool:
    """`git check-ignore -q` — a DECISAO do Git, nao o texto da regra."""
    return subprocess.run(["git", "check-ignore", "-q", "--", caminho],
                          cwd=_RAIZ_REPO,
                          capture_output=True).returncode == 0


def _origem_da_decisao(caminho: str) -> str:
    """Arquivo e linha da regra que DECIDIU — `check-ignore -v`."""
    saida = subprocess.run(["git", "check-ignore", "-v", "--", caminho],
                           cwd=_RAIZ_REPO, capture_output=True, text=True)
    return saida.stdout.strip()


@unittest.skipUnless(_tem_git(), "repositorio git indisponivel")
class OGitDecideIgnorarOEstadoDeRuntime(unittest.TestCase):
    """O EFEITO da regra, perguntado ao proprio Git."""

    def test_todo_caminho_de_runtime_e_efetivamente_ignorado(self):
        for caminho, motivo in sorted(RUNTIME_QUE_NAO_ENTRA.items()):
            with self.subTest(caminho=caminho):
                self.assertTrue(
                    _ignorado(caminho),
                    f"{caminho} ({motivo}) NAO e ignorado pelo Git — a "
                    "linha pode existir no .gitignore e estar inerte por "
                    "uma regra de desempate posterior")

    def test_o_que_precisa_ser_versionado_NAO_e_ignorado(self):
        # CONTRAPROVA. Sem ela, um `.gitignore` com uma unica linha `*`
        # passaria em todo o teste acima e o repositorio inteiro sumiria.
        for caminho in O_QUE_PRECISA_ENTRAR:
            with self.subTest(caminho=caminho):
                self.assertFalse(
                    _ignorado(caminho),
                    f"{caminho} esta sendo IGNORADO pelo Git")

    def test_a_decisao_vem_do_gitignore_VERSIONADO(self):
        # `check-ignore` considera tambem o `.gitignore` global do
        # usuario e `.git/info/exclude`. Se a decisao viesse de la, ela
        # valeria nesta estacao e em nenhuma outra — verde local, defeito
        # em qualquer clone.
        origem = _origem_da_decisao("locks/p1a39-ops.lease")
        self.assertTrue(origem, "check-ignore -v nao explicou a decisao")
        self.assertTrue(origem.startswith(".gitignore:"),
                        f"a decisao NAO vem do .gitignore versionado: "
                        f"{origem}")

    def test_nenhum_arquivo_de_lock_esta_rastreado(self):
        # `check-ignore` fala de CAMINHOS; um arquivo ja commitado segue
        # rastreado mesmo ignorado. Esta e a outra pergunta, e ela e
        # respondida por `ls-files`.
        saida = subprocess.run(["git", "ls-files", "--", "locks/"],
                               cwd=_RAIZ_REPO, capture_output=True, text=True)
        self.assertEqual(saida.stdout.strip(), "",
                         "ha arquivo de lock RASTREADO no Git")

    def test_o_instrumento_distingue_de_fato_os_dois_casos(self):
        # CONTROLE POSITIVO do proprio instrumento: um `_ignorado` que
        # devolvesse True sempre passaria no primeiro teste, e um que
        # devolvesse False sempre passaria no segundo. Aqui os dois lados
        # sao exigidos na mesma assercao.
        self.assertEqual(
            [_ignorado("locks/p1a39-ops.lease"),
             _ignorado("06_p1a/preflight/economia.py")],
            [True, False])

    def test_estado_de_lock_real_criado_agora_fica_ignorado(self):
        # Exerce o caso numa estacao limpa: a propria prova cria um objeto
        # de runtime, pergunta ao Git e o remove. Depender de sobra de uma
        # corrida anterior tornava o resultado propriedade da estacao.
        diretorio = os.path.join(_RAIZ_REPO, "locks")
        os.makedirs(diretorio, exist_ok=True)
        caminho = os.path.join(diretorio, "prova-p1a39-runtime.lease")
        try:
            with open(caminho, "w", encoding="ascii") as arquivo:
                arquivo.write("runtime")
            self.assertTrue(_ignorado("locks/prova-p1a39-runtime.lease"))
        finally:
            try:
                os.remove(caminho)
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    unittest.main()
