"""Contencao do kimi exercida contra o CLI REAL — SSC+ P1-A.3.4.

EXCECAO DECLARADA, e a unica, a regra escrita em `apoio.py`: *"NENHUM
subprocesso real e criado e NENHUM CLI de assinatura e invocado"*. O ato
da P1-A.3.4 a suspende para este arquivo, com uma justificativa que e o
proprio achado da P1-A.3.3 (§4): a correcao do MAJOR #3 passou por SETE
testes verdes e mesmo assim montava um comando que o CLI recusa. Testes
que afirmam a forma de uma lista nao podem falsear uma afirmacao sobre
uma interface externa — so exerce-la pode.

O PROPOSITO da regra de `apoio.py` e preservado integralmente: *"sem
gastar um unico token de assinatura"*. Aqui o custo e zero por
CONSTRUCAO, nao por promessa, e isso e verificado dentro do proprio
teste:

1. `HOME`/`USERPROFILE` apontam para um diretorio temporario VAZIO, de
   modo que nenhuma credencial OAuth do usuario e alcancavel;
2. o ambiente do filho e montado por ALLOWLIST (nem `KIMI_API_KEY` nem
   `KIMI_CODE_BASE_URL` sobrevivem), de modo que nenhum modelo pode ser
   configurado por variavel;
3. cada invocacao morre em `No model configured` — asseverado — ou antes
   ainda, na validacao de argumentos. As duas mortes sao anteriores a
   qualquer rede.

O que separa "argv aceito" de "argv recusado" e observavel na saida do
proprio CLI, e e nisso que estes testes se apoiam. O kimi 0.30.0 tem
DUAS classes de erro:

    error: Cannot combine --prompt with --plan.     <- validacao de argv
    error: unknown option '--sandbox'               <- validacao de argv
    error: failed to run prompt: No model configured ...   <- DEPOIS dela

A segunda so e alcancavel se o parser aprovou o comando inteiro. Ela e,
portanto, prova positiva de aceitacao — obtida sem gastar chamada.

Prova por reversao contra a REALIDADE, nao contra o codigo: reintroduzir
`--plan` em `argv_kimi` faz `test_o_cli_real_aceita_o_argv_de_producao`
falhar, porque o CLI de verdade passa a recusar o comando. Nenhum mock
media essa falha.
"""

import os
import subprocess
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

# Sem `-p` nao ha modo headless, e todo o argv sob teste e headless.
_PROMPT = "ping"

# Allowlist do ambiente do filho: o que NAO esta aqui nao chega ao CLI.
# `KIMI_*` fica de fora deliberadamente — e o caminho pelo qual um modelo
# poderia ser configurado sem passar pelo `HOME` isolado.
_ENV_HERDAVEL = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC", "PATHEXT")

_TIMEOUT_S = 90


def _kimi_exe() -> str:
    """O MESMO executavel que o runner de producao invoca."""
    return os.path.expanduser("~/.kimi-code/bin/kimi")


def _kimi_disponivel() -> bool:
    exe = _kimi_exe()
    return any(os.path.isfile(exe + suf) for suf in ("", ".exe", ".cmd"))


def _argv_de_producao(skills: str) -> list:
    """argv como o runner REAL o monta — nao como o teste gostaria.

    Vai por `revisao_p1a33.COMANDOS["kimi"]`, e nao direto por
    `argv_kimi`, para que a fiacao do chamador entre no escopo do teste:
    `argv_kimi` correto com chamador errado continuaria quebrado.
    """
    import importlib.util
    caminho = os.path.join(_DIR_P1A, "evidencias", "revisao_p1a33.py")
    spec = importlib.util.spec_from_file_location("runner_sob_teste_p1a34",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.COMANDOS["kimi"]("/tmp-inexistente", skills, _PROMPT)


def _rodar_kimi(argv, lar_vazio, cwd):
    """Invoca o CLI real com HOME vazio, stdin fechado e timeout."""
    env = {k: os.environ[k] for k in _ENV_HERDAVEL if k in os.environ}
    env.update({"HOME": lar_vazio, "USERPROFILE": lar_vazio,
                "HOMEDRIVE": lar_vazio[:2], "HOMEPATH": lar_vazio[2:],
                "XDG_CONFIG_HOME": os.path.join(lar_vazio, "cfg")})
    proc = subprocess.run(argv, env=env, cwd=cwd, capture_output=True,
                          text=True, timeout=_TIMEOUT_S,
                          stdin=subprocess.DEVNULL, encoding="utf-8",
                          errors="replace")
    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


@unittest.skipUnless(_kimi_disponivel(),
                     f"CLI do kimi ausente em {_kimi_exe()} — sem CLI real "
                     "esta propriedade NAO e verificavel, e o skip existe "
                     "para dizer isso alto, nunca para dar a suite por verde")
class ContencaoDoKimiContraOCliReal(unittest.TestCase):
    """MAJOR #3, metade 'restricao pelo CLI' — exercida, nao afirmada."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a34-cli-real-")
        self.raiz = self._tmp.name
        self.lar = os.path.join(self.raiz, "lar-vazio")
        self.skills = os.path.join(self.raiz, "skills-vazio")
        self.cwd = os.path.join(self.raiz, "cwd")
        for d in (self.lar, self.skills, self.cwd):
            os.makedirs(d)
        self.addCleanup(self._tmp.cleanup)

    def _sem_credencial_alcancavel(self):
        """Guarda de custo: o HOME do filho precisa estar mesmo vazio."""
        self.assertEqual(os.listdir(self.lar), [],
                         "HOME do teste nao esta vazio: haveria risco de "
                         "credencial alcancavel e de chamada de modelo")

    def test_o_cli_real_aceita_o_argv_de_producao(self):
        # A propriedade que os sete testes da P1-A.3.2 nao mediram: o CLI
        # ACEITA o comando. Prova positiva — o erro pos-parsing so e
        # alcancavel depois de o parser aprovar o argv inteiro.
        self._sem_credencial_alcancavel()
        argv = _argv_de_producao(self.skills)
        rc, out, err = _rodar_kimi(argv, self.lar, self.cwd)
        saida = err + out

        self.assertIn(
            contencao.MARCADOR_ARGV_ACEITO, saida,
            "o CLI real NAO passou da validacao de argumentos com o argv "
            f"de producao {argv[1:]!r}: {saida.strip()[:400]!r}")
        # Custo zero comprovado pela propria saida, nao prometido: o CLI
        # parou por falta de modelo configurado, antes de qualquer rede.
        self.assertIn("no model configured", saida.lower(),
                      "o CLI passou do ponto de 'sem modelo configurado' — "
                      "o isolamento de HOME falhou e pode ter havido "
                      "chamada de modelo")
        self.assertNotEqual(rc, 0, "corrida sem credencial nao pode dar 0")

    def test_o_cli_real_recusa_plan_junto_com_prompt(self):
        # O defeito, medido na propria interface. Este teste e o que torna
        # vermelha qualquer reintroducao de `--plan`: nao existe estado do
        # repositorio em que os dois testes fiquem verdes ao mesmo tempo.
        self._sem_credencial_alcancavel()
        argv = _argv_de_producao(self.skills)
        argv_com_plan = [argv[0], "--plan"] + list(argv[1:])
        rc, out, err = _rodar_kimi(argv_com_plan, self.lar, self.cwd)
        saida = (err + out).lower()

        self.assertIn("cannot combine --prompt with --plan", saida,
                      f"o CLI 0.30.0 deveria recusar {argv_com_plan[1:]!r}")
        self.assertNotIn(contencao.MARCADOR_ARGV_ACEITO.lower(), saida,
                         "recusa de argumento nao pode chegar ao pos-parsing")
        self.assertNotEqual(rc, 0)

    def test_toda_flag_declarada_incompativel_e_recusada_pelo_cli(self):
        # Mantem a constante honesta: cada flag listada precisa ser
        # recusada DE VERDADE. Uma entrada obsoleta ou inventada aqui
        # deixaria de descrever o CLI, e o teste reprova.
        self._sem_credencial_alcancavel()
        argv = _argv_de_producao(self.skills)
        self.assertTrue(contencao.FLAGS_INCOMPATIVEIS_COM_PROMPT)
        for flag in contencao.FLAGS_INCOMPATIVEIS_COM_PROMPT:
            with self.subTest(flag=flag):
                rc, out, err = _rodar_kimi([argv[0], flag] + list(argv[1:]),
                                           self.lar, self.cwd)
                saida = (err + out).lower()
                self.assertNotIn(
                    contencao.MARCADOR_ARGV_ACEITO.lower(), saida,
                    f"{flag} esta declarada incompativel com -p, mas o CLI "
                    "aceitou o comando")
                self.assertIn("error:", saida)
                self.assertNotEqual(rc, 0)

    def test_o_argv_de_producao_nao_carrega_flag_de_auto_aprovacao(self):
        # Contraparte da aceitacao: um argv aceito porem permissivo seria
        # pior que um recusado. Medido no argv que o runner monta.
        argv = _argv_de_producao(self.skills)
        for flag in contencao.FLAGS_DE_AUTO_APROVACAO:
            with self.subTest(flag=flag):
                self.assertNotIn(flag, argv)


if __name__ == "__main__":
    unittest.main()
