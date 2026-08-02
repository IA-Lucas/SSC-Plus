"""O rotulo de enforcement preso ao ARGV que sai — SSC+ P1-A.3.9.

MECANISMO (d) da FASE 2 da P1-A.3.8, guarda `P1A-43`. A linha da
remedicao e literal:

    so a entrada **kimi** e confrontada com o CLI; a entrada **codex
    nunca e invocada**.
    Remedio: o da frente P1 da P1-A.3.5 — sondar se o CLI do codex
    distingue erro pre e pos-parsing.

## O remedio prescrito NAO e executado, e o motivo esta escrito

Sondar o CLI do codex e invocar provedor. O ato desta missao proibe:
*"nao invocar provider ... Zero chamada paga"*. `P1A-43` fica aberto por
ORDEM. O que se faz aqui e a metade que nao depende de invocacao — e ela
fecha um buraco que a propria remedicao nao tinha visto.

## O ACHADO desta missao: o rotulo nao estava preso a nada

`ENFORCEMENT` e o dicionario cujo valor vai para o campo
`enforcement_read_only` da evidencia entregue ao revisor. Ele afirma, em
texto, a restricao que a corrida aplicou. MEDIDO: **zero ocorrencias de
`ENFORCEMENT` em qualquer arquivo de teste das duas suites**. Os quatro
runners de revisao publicam a afirmacao e nada a confronta com o argv
que de fato sai.

Consequencia concreta: remover `--ephemeral` do `COMANDOS["codex"]`
deixa a evidencia dizendo `--sandbox read-only --ephemeral (CLI)` e a
corrida rodando sem `--ephemeral`. E a familia do MAJOR #3 na forma
exata — o guarda AFIRMA a propriedade em vez de EXERCER a interface —,
agora no rotulo que o revisor le para decidir.

## Como o rotulo e preso, sem invocar CLI nenhum

- **codex**: o rotulo e uma lista de flags. Toda flag citada nele
  precisa estar no argv que `COMANDOS["codex"]` constroi;
- **kimi**: o rotulo e prosa, e prosa nao se confronta por texto sem
  virar adivinhacao. Ele e preso pelas CONSTANTES ESTRUTURADAS que a
  propria `contencao` mantem — `--skills-dir` presente,
  `FLAGS_DE_AUTO_APROVACAO` ausentes, `FLAGS_INCOMPATIVEIS_COM_PROMPT`
  ausentes. Sao os mesmos fatos que o rotulo afirma, em forma
  verificavel.

O corpus de runners e DESCOBERTO por AST: runner novo com `ENFORCEMENT`
entra sozinho, e provedor novo dentro de `ENFORCEMENT` sem regra aqui
reprova pelo nome.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nenhum CLI e invocado.** Que `--sandbox read-only` e `--ephemeral`
  facam o que o nome diz no codex real continua NAO exercido — e a
  metade que `P1A-43` mantem aberta, e ela e a metade que importa para
  um revisor;
- **o rotulo do kimi e prosa**: confere-se o que ele afirma em forma
  estruturada, jamais cada frase dele. `test_rotulo_contencao_p1a37`
  continua sendo quem guarda a HONESTIDADE das palavras (achado N3);
- **a construcao do argv usa marcadores**, nao caminhos reais: o que se
  mede sao os TOKENS de restricao, nunca o conteudo do prompt nem o
  descartavel;
- nada se afirma sobre o que o CLI faz com uma flag que ele nao
  reconhece — para isso so a invocacao serve, e ela nao acontece aqui.
"""

import ast
import importlib.util
import os
import sys
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

import contencao  # noqa: E402

# Provedores com regra de confronto declarada aqui. Provedor que apareca
# em ENFORCEMENT e nao esteja neste conjunto reprova — e assim que um
# terceiro nao entra sem que alguem diga como ele e verificado.
PROVEDORES_COM_REGRA = frozenset({"codex", "kimi"})

# P1A-43, o numero que a remedicao apontou, fixado pelo nome.
CONFRONTADO_COM_CLI_REAL = frozenset({"kimi"})
SEM_CONFRONTO_COM_CLI_REAL = frozenset({"codex"})

_MARCADORES = {"tmp": "<DESCARTAVEL>", "skills": "<SKILLS>",
               "prompt": "<PROMPT>"}


def runners_com_enforcement() -> set:
    """Runner de evidencias que define `ENFORCEMENT` — por AST."""
    achados = set()
    for nome in sorted(os.listdir(_DIR_EVID)):
        if not nome.startswith("revisao_") or not nome.endswith(".py"):
            continue
        with open(os.path.join(_DIR_EVID, nome), encoding="utf-8") as f:
            try:
                arvore = ast.parse(f.read())
            except SyntaxError:
                continue
        for no in arvore.body:
            if isinstance(no, ast.Assign) and any(
                    isinstance(a, ast.Name) and a.id == "ENFORCEMENT"
                    for a in no.targets):
                achados.add(nome[:-3])
    return achados


def _carregar(nome: str):
    caminho = os.path.join(_DIR_EVID, f"{nome}.py")
    spec = importlib.util.spec_from_file_location(f"p1a39_enf_{nome}",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def argv_de(modulo, provider_id: str) -> list:
    """Argv que o runner constroi, com marcadores no lugar dos dados."""
    construir = modulo.COMANDOS[provider_id]
    aridade = construir.__code__.co_argcount
    if aridade == 2:
        return construir(_MARCADORES["tmp"], _MARCADORES["prompt"])
    return construir(_MARCADORES["tmp"], _MARCADORES["skills"],
                     _MARCADORES["prompt"])


def flags_do_rotulo(rotulo: str) -> set:
    """Tokens `--flag` citados no rotulo — so a forma longa, sem prosa."""
    return {palavra.strip("`,.;:()")
            for palavra in rotulo.split()
            if palavra.strip("`,.;:()").startswith("--")}


class ORotuloDoCodexEstaNoArgv(unittest.TestCase):
    """O buraco que a medicao desta missao achou, fechado."""

    def test_todo_runner_com_enforcement_e_confrontado(self):
        descobertos = runners_com_enforcement()
        self.assertGreaterEqual(len(descobertos), 4)
        for nome in sorted(descobertos):
            with self.subTest(runner=nome):
                modulo = _carregar(nome)
                self.assertTrue(set(modulo.ENFORCEMENT) <= PROVEDORES_COM_REGRA,
                                f"{nome}: provedor em ENFORCEMENT sem regra "
                                f"de confronto: "
                                f"{sorted(set(modulo.ENFORCEMENT) - PROVEDORES_COM_REGRA)}")

    def test_toda_flag_do_rotulo_do_codex_sai_no_argv(self):
        for nome in sorted(runners_com_enforcement()):
            with self.subTest(runner=nome):
                modulo = _carregar(nome)
                if "codex" not in modulo.ENFORCEMENT:
                    continue
                flags = flags_do_rotulo(modulo.ENFORCEMENT["codex"])
                argv = argv_de(modulo, "codex")
                self.assertTrue(flags, f"{nome}: rotulo do codex sem flag")
                for flag in sorted(flags):
                    self.assertIn(
                        flag, argv,
                        f"{nome}: o rotulo entregue ao revisor afirma "
                        f"{flag}, e o argv que sai NAO o carrega")

    def test_o_extrator_de_flags_recusa_um_rotulo_que_mente(self):
        # CONTROLE POSITIVO: sem ele, um extrator que devolvesse `set()`
        # deixaria o teste acima verde com qualquer rotulo.
        self.assertEqual(flags_do_rotulo("--sandbox read-only --ephemeral "
                                         "(CLI)"),
                         {"--sandbox", "--ephemeral"})
        self.assertEqual(flags_do_rotulo("sem flag nenhuma aqui"), set())
        mentiroso = "--sandbox read-only --ephemeral --inventada (CLI)"
        argv = argv_de(_carregar("revisao_p1a33"), "codex")
        self.assertFalse(flags_do_rotulo(mentiroso) <= set(argv))

    def test_os_quatro_runners_publicam_o_MESMO_rotulo_de_codex(self):
        # A copia que fica para tras (achados 7, 10 e 14): se um runner
        # divergir, o revisor recebe duas afirmacoes diferentes sobre a
        # mesma restricao e nao tem como saber qual vale.
        rotulos = {nome: _carregar(nome).ENFORCEMENT.get("codex")
                   for nome in sorted(runners_com_enforcement())}
        distintos = set(rotulos.values())
        self.assertEqual(len(distintos), 1, rotulos)


class ORotuloDoKimiEPresoPelasConstantes(unittest.TestCase):
    """Prosa nao se confronta por texto: confronta-se pelo que ela afirma."""

    def _argv_kimi(self, nome):
        return argv_de(_carregar(nome), "kimi")

    def test_a_restricao_que_o_rotulo_afirma_APLICAR_esta_no_argv(self):
        for nome in sorted(runners_com_enforcement()):
            with self.subTest(runner=nome):
                if "kimi" not in _carregar(nome).ENFORCEMENT:
                    continue
                argv = self._argv_kimi(nome)
                self.assertIn("--skills-dir", argv)
                self.assertIn(_MARCADORES["skills"], argv)

    def test_as_flags_que_o_rotulo_afirma_NAO_passar_estao_fora(self):
        for nome in sorted(runners_com_enforcement()):
            with self.subTest(runner=nome):
                if "kimi" not in _carregar(nome).ENFORCEMENT:
                    continue
                argv = set(self._argv_kimi(nome))
                for flag in (contencao.FLAGS_DE_AUTO_APROVACAO
                             + contencao.FLAGS_INCOMPATIVEIS_COM_PROMPT):
                    self.assertNotIn(flag, argv, f"{nome}: {flag} no argv")

    def test_o_rotulo_do_kimi_e_o_canonico_em_todo_runner(self):
        canonico = contencao.enforcement_kimi()
        for nome in sorted(runners_com_enforcement()):
            with self.subTest(runner=nome):
                modulo = _carregar(nome)
                if "kimi" not in modulo.ENFORCEMENT:
                    continue
                self.assertEqual(modulo.ENFORCEMENT["kimi"], canonico)

    def test_o_argv_do_kimi_e_o_canonico_em_todo_runner(self):
        # Sem isto, um runner poderia montar o argv a mao e divergir do
        # `argv_kimi` que o rotulo descreve — rotulo canonico sobre argv
        # que nao e o canonico e pior que rotulo divergente.
        canonico = contencao.argv_kimi("<EXE>", _MARCADORES["prompt"],
                                       _MARCADORES["skills"])
        for nome in sorted(runners_com_enforcement()):
            with self.subTest(runner=nome):
                modulo = _carregar(nome)
                if "kimi" not in modulo.ENFORCEMENT:
                    continue
                self.assertEqual(self._argv_kimi(nome)[1:], canonico[1:])


class ALacunaDoCodexEDeclarada(unittest.TestCase):
    """`P1A-43` pelo nome: quem e confrontado com CLI real, e quem nao e."""

    def test_a_particao_cobre_os_provedores_com_regra(self):
        self.assertEqual(
            CONFRONTADO_COM_CLI_REAL | SEM_CONFRONTO_COM_CLI_REAL,
            set(PROVEDORES_COM_REGRA))
        self.assertEqual(
            CONFRONTADO_COM_CLI_REAL & SEM_CONFRONTO_COM_CLI_REAL, set())

    def test_o_confronto_do_kimi_existe_no_acervo(self):
        arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "test_cli_real_p1a34.py")
        self.assertTrue(os.path.isfile(arquivo),
                        "o unico confronto com CLI real sumiu do acervo")

    def test_o_codex_segue_sem_confronto_com_cli_real(self):
        # O achado, escrito: nao e meta e nao e alarme, e o estado. Se um
        # ato futuro autorizar a sonda do codex, este teste fica vermelho
        # e a declaracao muda com registro.
        arquivos = [n for n in os.listdir(
            os.path.dirname(os.path.abspath(__file__)))
            if n.startswith("test_cli_real")]
        self.assertEqual(arquivos, ["test_cli_real_p1a34.py"])
        self.assertEqual(sorted(SEM_CONFRONTO_COM_CLI_REAL), ["codex"])


if __name__ == "__main__":
    unittest.main()
