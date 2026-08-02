"""`_VIA_GITBASH` presa nas DUAS copias — e a duplicata registrada — P1-A.3.9.

ORDEM 4 do ato, segunda metade. A varredura [15/N] mediu a MESMA
constante, duplicada em duas camadas, e as duas copias SOLTAS:

| copia | membros | vermelhos ANTES |
|---|---|---|
| `06_p1a/preflight_capsula.py::_VIA_GITBASH` | `google`, `grok` | **0** |
| `07_p1b/preflight_atual.py::_VIA_GITBASH` | `google`, `grok` | **0** |

## ACHADO DE ARQUITETURA, alem de guarda — por ordem do ato

*"Duplicata que ninguem exercita diverge em silencio"* — o mecanismo dos
achados 7, 10 e 14 desta trilha. E aqui a divergencia **ja comecou**, o
que este arquivo mede em vez de supor. As duas copias da CONSTANTE sao
iguais; os dois SENSORES construidos a partir dela **nao sao**:

| | `preflight_capsula` | `preflight_atual` (P1-B) |
|---|---|---|
| `timeout` do wrapper | **60** | **120** |
| argv | `str(a)` | `os.path.expanduser(str(a))` |

Ou seja: a lista que decide QUEM vai pelo Git Bash e a mesma, e o COMO
ja se separou. Nenhum teste via isso, porque nenhum dos dois lados era
exercido.

**Nao se unifica nesta missao**, por ordem explicita do ato. O remedio
fica registrado: implementacao UNICA de `_sensor_de` numa camada
partilhada, no mesmo desenho que `leitor_tiers` e `leitores_config`
receberam nas correcoes 7 da P1-A.3.5 e ordem 1 da P1-B.01 — os dois
casos em que esta mesma duplicacao ja foi desfeita neste repositorio. Ate
la, `AsDuasCopiasNaoPodemDivergirEmSilENCIO` faz o minimo: qualquer
mudanca de um lado sem o outro fica vermelha.

## O CASO QUE OCORRE, e o vizinho recusado

O vizinho e conferir que a tupla contem `"google"`. O que a operacao
percorre e `_sensor_de(provider_id)`, que decide se a sonda daquele
provedor vai por subprocesso direto ou pelo Git Bash — e e ele que esta
exercido aqui, nas duas copias, com o argv REALMENTE construido.

**Custo zero por construcao:** `sensor_subprocess` e substituido por um
capturador em cada modulo durante o teste, de modo que **nenhum
subprocesso e criado e nenhum CLI e invocado**. O que se observa e o argv
que teria sido executado.

## O QUE ESTE ARQUIVO NAO COBRE, declarado

- **nao unifica as copias** — por ordem do ato. O guarda impede
  divergencia silenciosa; nao remove a duplicacao, que segue sendo o
  defeito de fundo;
- **nao afirma que `google` e `grok` sejam os provedores CERTOS** para o
  Git Bash: mede-se que a lista tem efeito, jamais que a escolha esteja
  certa para esta ou outra estacao;
- **nao exercita o Git Bash de verdade.** `_GITBASH` e um caminho
  absoluto desta estacao (`E:/LucasIA/Git/bin/bash.exe`, com barras
  invertidas no codigo) e nada aqui verifica que ele exista ou funcione —
  o que se prova e o ROTEAMENTO, nunca a execucao;
- **a divergencia de `timeout` e de `expanduser` e FIXADA, nao
  corrigida**: se alguem alinhar os dois lados, este arquivo fica
  vermelho de proposito, para que a mudanca seja vista e nao presumida;
- **remocao SIMULTANEA do membro nas duas copias E no `_sensor_de`**
  passa.
"""

import importlib.util
import os
import sys
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _p in (os.path.join(_RAIZ, "06_p1a"), os.path.join(_RAIZ, "07_p1b"),
           os.path.join(_RAIZ, "06_p1a", "evidencias")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Provedores que NAO vao pelo Git Bash — escrito a mao, nao derivado de
# `FONTES` nem de `_VIA_GITBASH`. Se saisse de uma das duas, encolher a
# estrutura encolheria o corpus junto.
DIRETOS = ("claude", "codex", "kimi")
ARGV_DE_SONDA = ("gemini", "--version")


def _carregar(caminho: str, apelido: str):
    spec = importlib.util.spec_from_file_location(apelido, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_CAPSULA = _carregar(os.path.join(_RAIZ, "06_p1a", "preflight_capsula.py"),
                     "preflight_capsula_sob_teste_p1a39")
_ATUAL = _carregar(os.path.join(_RAIZ, "07_p1b", "preflight_atual.py"),
                   "preflight_atual_sob_teste_p1a39")

RUNNERS = (("preflight_capsula", _CAPSULA), ("preflight_atual", _ATUAL))


class _Capturador:
    """Substitui `sensor_subprocess`: registra o argv e NAO executa nada."""

    def __init__(self):
        self.chamadas = []

    def __call__(self, argv, env=None, timeout=None):
        self.chamadas.append({"argv": list(argv), "timeout": timeout})
        return {"rc": 0, "stdout": "", "stderr": ""}


class OSensorRoteiaPeloGitBashQuemAListaDiz(unittest.TestCase):
    """O ponto de chamada real, nas DUAS copias, sem criar subprocesso."""

    def _com_capturador(self, modulo):
        cap = _Capturador()
        original = modulo.sensor_subprocess
        modulo.sensor_subprocess = cap
        self.addCleanup(setattr, modulo, "sensor_subprocess", original)
        return cap

    def test_google_vai_pelo_git_bash_nos_dois_runners(self):
        # `google` escrito a mao: se sair da tupla de qualquer um dos
        # dois modulos, `_sensor_de` devolve o sensor direto e este
        # teste fica vermelho naquele runner.
        for nome, modulo in RUNNERS:
            with self.subTest(runner=nome):
                cap = self._com_capturador(modulo)
                modulo._sensor_de("google")(list(ARGV_DE_SONDA))
                self.assertEqual(len(cap.chamadas), 1)
                argv = cap.chamadas[0]["argv"]
                self.assertEqual(argv[0], modulo._GITBASH)
                self.assertEqual(argv[1], "-lc")
                self.assertIn("gemini", argv[2])

    def test_grok_vai_pelo_git_bash_nos_dois_runners(self):
        for nome, modulo in RUNNERS:
            with self.subTest(runner=nome):
                cap = self._com_capturador(modulo)
                modulo._sensor_de("grok")(["grok", "--version"])
                self.assertEqual(cap.chamadas[0]["argv"][0], modulo._GITBASH)

    def test_os_demais_provedores_NAO_passam_pelo_git_bash(self):
        # CONTRAPROVA: um `_sensor_de` que mandasse todo mundo pelo Git
        # Bash passaria nos dois testes acima.
        for nome, modulo in RUNNERS:
            for provider_id in DIRETOS:
                with self.subTest(runner=nome, provedor=provider_id):
                    self.assertIs(modulo._sensor_de(provider_id),
                                  modulo.sensor_subprocess)

    def test_o_sensor_direto_nao_reescreve_o_argv(self):
        # A outra metade da contraprova: o caminho direto precisa
        # entregar o argv INTACTO.
        for nome, modulo in RUNNERS:
            with self.subTest(runner=nome):
                cap = self._com_capturador(modulo)
                modulo._sensor_de("codex")(list(ARGV_DE_SONDA))
                self.assertEqual(cap.chamadas[0]["argv"],
                                 list(ARGV_DE_SONDA))


class AsDuasCopiasNaoPodemDivergirEmSilencio(unittest.TestCase):
    """A duplicata fixada pelo nome, no padrao de OQueEVigiadoMasNaoEAuditado."""

    def test_as_duas_copias_da_constante_sao_iguais(self):
        self.assertEqual(tuple(_CAPSULA._VIA_GITBASH),
                         tuple(_ATUAL._VIA_GITBASH))

    def test_a_constante_nao_esta_vazia(self):
        # Guarda anti-igualdade-trivial: duas tuplas vazias sao iguais.
        self.assertEqual(len(_CAPSULA._VIA_GITBASH), 2)

    def test_a_divergencia_JA_EXISTENTE_dos_wrappers_esta_declarada(self):
        # MEDIDO, nao suposto: as constantes sao iguais e os wrappers ja
        # se separaram. Fixado aqui para que alinhar os dois lados seja
        # um ato VISTO, e nao um efeito colateral.
        cap_c = _Capturador()
        cap_a = _Capturador()
        for modulo, cap in ((_CAPSULA, cap_c), (_ATUAL, cap_a)):
            original = modulo.sensor_subprocess
            modulo.sensor_subprocess = cap
            self.addCleanup(setattr, modulo, "sensor_subprocess", original)
            modulo._sensor_de("google")(["gemini", "~/x"])
        self.assertEqual(cap_c.chamadas[0]["timeout"], 60)
        self.assertEqual(cap_a.chamadas[0]["timeout"], 120)
        # `preflight_atual` expande `~`; `preflight_capsula` nao.
        self.assertIn("~/x", cap_c.chamadas[0]["argv"][2])
        self.assertNotIn("~/x", cap_a.chamadas[0]["argv"][2])


if __name__ == "__main__":
    unittest.main()
