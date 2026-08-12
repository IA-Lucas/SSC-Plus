"""`_VIA_GITBASH` presa nas DUAS copias — e a duplicata registrada — P1-A.3.9.

ORDEM 4 do ato, segunda metade. A varredura [15/N] mediu a MESMA
constante, duplicada em duas camadas, e as duas copias SOLTAS:

| copia | membros | vermelhos ANTES |
|---|---|---|
| `06_p1a/preflight_capsula.py::_VIA_GITBASH` | `google`, `grok` | **0** |
| `07_p1b/preflight_atual.py::_VIA_GITBASH` | `google`, `grok` | **0** |

## ACHADO DE ARQUITETURA, alem de guarda — por ordem do ato

*"Duplicata que ninguem exercita diverge em silencio"* — o mecanismo dos
achados 7, 10 e 14 desta trilha. E aqui a divergencia **ja tinha
comecado**, o que este arquivo mediu em vez de supor. As duas copias da
CONSTANTE eram iguais; os dois SENSORES construidos a partir dela **nao
eram**:

| | `preflight_capsula` | `preflight_atual` (P1-B) |
|---|---|---|
| `timeout` do wrapper | 60 | **120** |
| argv | `str(a)` | **`os.path.expanduser(str(a))`** |

A lista que decide QUEM vai pelo Git Bash era a mesma, e o COMO ja se
separara. Nenhum teste via isso, porque nenhum dos dois lados era
exercido.

## O ALINHAMENTO, e por que cada lado venceu onde venceu

Feito na ordem 2 do despacho final da P1-A.3.9. **Nenhum dos dois
arquivos venceu inteiro** — cada atributo foi decidido pelo seu proprio
fundamento, e nao por qual copia veio primeiro.

**`timeout`: venceu 60, o MENOR.** Medido, nao arbitrado: o teto canonico
da camada partilhada e `adaptadores.TIMEOUT_PADRAO = 20`, e a partida do
Git Bash nesta estacao custa **0,35 s** (5 corridas de `bash -lc true`;
min 0,31, max 0,41). A camada extra justifica cerca de **21 s** — nem 60,
nem 120. Os dois numeros carregam margem sem fundamento escrito; fica o
menor, porque o timeout e **fail-closed** (`rc 124` -> `CliIndisponivel`)
e encurtar nunca transforma falha em passagem: so faz o portao decidir
mais cedo, que e o que se quer de um preflight.

**`expanduser`: venceu a versao da P1-B, por necessidade.** O catalogo
guarda caminhos com `~` (`07_p1b/evidencias/*.json`, campo `caminho`:
`~/AppData/Local/Programs/...`), e `shlex.join` **cita** o til. Medido:
`bash -lc "echo '~/x'"` imprime `~/x` literal, contra `/c/Users/.../x`
sem as aspas. Sem `expanduser`, o caminho chegava literal ao CLI e nao
resolvia — a omissao em `preflight_capsula` era **defeito latente**, nao
diferenca de estilo.

**A constante segue duplicada**, por ordem do ato: o achado de
arquitetura permanece ABERTO, com o remedio registrado abaixo.

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
- **o alinhamento nao foi VALIDADO contra os CLIs reais.** Que 60 s
  bastem para a sonda de `google` e `grok` nesta estacao **nao foi
  medido** — as sondas nao foram invocadas, por restricao do ato (zero
  chamada, cota fechada ate 5 de agosto). O que se mediu foi a partida do
  Git Bash e o teto canonico da camada; se alguma sonda estourar 60 s em
  operacao, o efeito e `CliIndisponivel`, visivel e fail-closed, nunca
  passagem silenciosa. **Confirmar na primeira corrida real do preflight
  fica REGISTRADO como pendencia;**
- **`expanduser` nao e exercido contra caminho que exista**: prova-se que
  o til deixa de sair literal, jamais que o caminho expandido aponte para
  um executavel presente;
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
DIRETOS = ("claude", "codex", "kimi", "google")
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

    def test_google_agy_vai_direto_nos_dois_runners(self):
        for nome, modulo in RUNNERS:
            with self.subTest(runner=nome):
                cap = self._com_capturador(modulo)
                modulo._sensor_de("google")(list(ARGV_DE_SONDA))
                self.assertEqual(len(cap.chamadas), 1)
                argv = cap.chamadas[0]["argv"]
                self.assertEqual(argv, list(ARGV_DE_SONDA))

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
        self.assertEqual(tuple(_CAPSULA._VIA_GITBASH), ("grok",))

    def test_os_wrappers_estao_ALINHADOS_nos_dois_runners(self):
        # ERA o teste que fixava a DIVERGENCIA (timeout 60 contra 120 e
        # `expanduser` so na P1-B). A divergencia foi alinhada na ordem 2
        # do despacho final da P1-A.3.9, e este teste ficou vermelho DE
        # PROPOSITO — que era a intencao declarada: alinhar tinha de ser
        # ato visto. Agora fixa o estado ALINHADO, e voltar a divergir
        # fica vermelho pelo mesmo motivo.
        cap_c = _Capturador()
        cap_a = _Capturador()
        for modulo, cap in ((_CAPSULA, cap_c), (_ATUAL, cap_a)):
            original = modulo.sensor_subprocess
            modulo.sensor_subprocess = cap
            self.addCleanup(setattr, modulo, "sensor_subprocess", original)
            modulo._sensor_de("grok")(["grok", "~/x"])
        # TIMEOUT: venceu 60, o menor dos dois. Fundamento medido —
        # `adaptadores.TIMEOUT_PADRAO` e 20 e a partida do Git Bash custa
        # 0,35 s nesta estacao, entao a camada extra justifica ~21 s.
        self.assertEqual(cap_c.chamadas[0]["timeout"], 60)
        self.assertEqual(cap_a.chamadas[0]["timeout"], 60)
        self.assertEqual(cap_c.chamadas[0]["timeout"],
                         cap_a.chamadas[0]["timeout"])
        # EXPANDUSER: venceu a versao da P1-B, por necessidade medida —
        # `shlex.join` CITA o til e o bash nao o expande entre aspas
        # simples, entao sem expandir o caminho chega literal ao CLI.
        for cap in (cap_c, cap_a):
            self.assertNotIn("~/x", cap.chamadas[0]["argv"][2])

    def test_os_dois_wrappers_produzem_o_MESMO_comando(self):
        # A propriedade que o alinhamento quer dizer, exercida inteira:
        # mesma entrada, mesmo argv e mesmo teto nos dois runners.
        caps = []
        for modulo in (_CAPSULA, _ATUAL):
            cap = _Capturador()
            original = modulo.sensor_subprocess
            modulo.sensor_subprocess = cap
            self.addCleanup(setattr, modulo, "sensor_subprocess", original)
            modulo._sensor_de("grok")(["grok", "~/bin/grok", "--version"])
            caps.append(cap)
        self.assertEqual(caps[0].chamadas[0]["argv"][1:],
                         caps[1].chamadas[0]["argv"][1:])
        self.assertEqual(caps[0].chamadas[0]["timeout"],
                         caps[1].chamadas[0]["timeout"])


if __name__ == "__main__":
    unittest.main()
