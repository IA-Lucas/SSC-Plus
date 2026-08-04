"""A FRONTEIRA do escritor unico, medida — SSC+ P1-A.3.9.

MECANISMO (d) da FASE 2 da P1-A.3.8, guardas `P1A-04` e `P1A-19`. As
duas linhas dizem a mesma coisa:

    P1A-04: lease vencido recusa escrita, com arquivos reais. Mas a
    propriedade AFIRMADA e escritor unico ENTRE MISSOES, e essa e o
    ACHADO 4 — duas missoes de nomes diferentes trancam arquivos
    diferentes. Remedio: trocar para `escritor_repositorio`; entregue na
    P1-A.3.7 e NAO LIGADO, por decisao do Fundador.

    P1A-19: mesma limitacao do P1A-04 — o lease e nomeado pelo proprio
    verificador.

## Os dois fecharam na P1-A.5, ordem 2 — e a fronteira NAO se moveu

Quando este arquivo nasceu, o ato da missao dizia *"nao trocar o
mecanismo de lock"*, e os dois guardas ficavam abertos por ordem, nao
por dificuldade. A troca foi autorizada na P1-A.5, e o `P1A-04`/`P1A-19`
deixaram de medir "escritor unico DENTRO DO NOME": a classe abaixo passa
a exercer o `EscritorRepositorio`, e a verificacao canonica recusa quem
nao e o titular.

**O QUE A TROCA NAO MOVEU, e e o objeto deste arquivo:** a fronteira
entre o lease e o Git. `git commit` continua sem consultar lease nenhum,
e a classe `OLeaseNaoAlcancaOGit` continua medindo exatamente isso, sem
uma linha alterada. Trocar o escritor deu exclusao mutua entre missoes;
nao deu, e nao podia dar, alcance sobre quem escreve sem passar pelo
escritor. Confundir as duas coisas seria fechar um achado com a prova de
outro.

## O CASO QUE OCORREU NESTA MISSAO, e nao um exemplo inventado

Durante esta missao, com o lease `p1a39-ops` VIVO e renovado a cada 30 s,
um processo que nao era o desta missao criou o commit
`cdde5ac654129010387e3579241295b39fafee5d` sobre o HEAD, reescreveu as
terminacoes de linha de 62 arquivos e levou junto um arquivo que estava
no INDEX desta missao. O fuso do commit (`Z`) difere do desta sessao
(`-03:00`), o que mede que o autor foi outro ambiente Git.

O lease nao impediu, e nao poderia: **nada no acervo faz `git commit`
consultar o lease**. Os pontos de chamada de `verificar_lock` sao todos
de ESCRITA DE EVIDENCIA e de INVOCACAO DE PROVEDOR. Este arquivo mede
exatamente isso, com um repositorio Git descartavel.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nada aqui conserta a fronteira** — ela e medida, nao movida. Mover
  exige o `escritor_repositorio`, que existe e nao esta ligado por
  decisao do Fundador;
- **nao se afirma que `git commit` DEVA consultar o lease**: isso e
  politica, e politica nao se decide numa missao de correcao. O que se
  afirma e que hoje ele nao consulta;
- **a varredura de pontos de chamada e ESTRUTURAL** (por texto do
  fonte): ela mede onde o guarda e chamado, nunca se a chamada esta
  correta — para isso valem os testes de lease do acervo;
- **concorrencia real entre processos nao e simulada**: os dois
  escritores deste teste vivem no mesmo processo. O que se mede e o
  MECANISMO DE NOME, nao a corrida.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import apoio  # noqa: F401  (ajusta sys.path da suite)
from escritor import EscritorP1, LockIndisponivel
from escritor_repositorio import EscritorRepositorio, caminho_lease

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

# Arquivos que CHAMAM a verificacao do escritor unico. Descobertos por
# varredura, nunca listados a mao — ver `_chamadores_do_lease`.
_MARCADORES = ("verificar_lock(", "_verificar_lock(", "_verificar_lock_vivo(")

# Diretorios varridos: o codigo de producao das tres camadas.
_RAIZES = (os.path.join(_DIR_P1A, "evidencias"), _DIR_P1A,
           os.path.join(_RAIZ_REPO, "07_p1b"))


def _chamadores_do_lease() -> set:
    achados = set()
    for raiz in _RAIZES:
        if not os.path.isdir(raiz):
            continue
        for nome in sorted(os.listdir(raiz)):
            caminho = os.path.join(raiz, nome)
            if not os.path.isfile(caminho) or not nome.endswith(".py"):
                continue
            with open(caminho, encoding="utf-8") as f:
                fonte = f.read()
            if any(m in fonte for m in _MARCADORES):
                achados.add(nome[:-3])
    return achados


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True)


def _tem_git() -> bool:
    try:
        return subprocess.run(["git", "--version"],
                              capture_output=True).returncode == 0
    except OSError:
        return False


class OEscritorUnicoTrancaDentroDoNOME(unittest.TestCase):
    """O que o mecanismo DE FATO garante — e o limite exato disso."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a39-lease-")
        self.addCleanup(self._tmp.cleanup)
        self.locks = os.path.join(self._tmp.name, "locks")

    def test_duas_sessoes_do_MESMO_nome_se_excluem(self):
        # A metade que funciona, e que os testes de lease do acervo ja
        # provam. Reafirmada aqui porque a metade seguinte so tem
        # sentido ao lado dela.
        primeiro = EscritorP1(self.locks, sessao="missao-x")
        primeiro.adquirir()
        try:
            with self.assertRaises(LockIndisponivel):
                EscritorP1(self.locks, sessao="missao-x").adquirir()
        finally:
            primeiro.liberar()

    def test_duas_sessoes_de_NOMES_DIFERENTES_NAO_se_excluem(self):
        # O ACHADO 4, exercido em vez de descrito. As duas adquirem, as
        # duas se consideram escritor unico, e nenhuma ve a outra.
        primeiro = EscritorP1(self.locks, sessao="missao-x")
        segundo = EscritorP1(self.locks, sessao="missao-y")
        token_a = primeiro.adquirir()
        try:
            token_b = segundo.adquirir()
            try:
                self.assertIsNotNone(token_a)
                self.assertIsNotNone(token_b)
                primeiro.verificar()
                segundo.verificar()
                self.assertEqual(
                    sorted(os.listdir(self.locks)),
                    sorted(["missao-x.fence", "missao-x.lease",
                            "missao-x.lock", "missao-y.fence",
                            "missao-y.lease", "missao-y.lock"]))
            finally:
                segundo.liberar()
        finally:
            primeiro.liberar()

    def test_o_verificador_recusa_quem_nao_e_o_titular_do_repositorio(self):
        # `P1A-19` media que quem verifica escolhe o NOME do lease, de modo
        # que "o lease esta vivo" era sempre sobre o proprio lease — e por
        # isso a propriedade nao dizia nada sobre outra missao. Desde a
        # P1-A.5, ordem 2, ha um lease so: `sessao` deixou de escolher o
        # arquivo e virou o titular EXIGIDO. Quem nao e o titular PARA.
        escritor = EscritorRepositorio(self.locks, "missao-x")
        escritor.adquirir()
        self.addCleanup(escritor.liberar)
        raiz = Path(self.locks).parent
        estado = contencao.verificar_lock(raiz, "missao-x")
        self.assertEqual(estado["sessao"], "missao-x")
        with self.assertRaises(SystemExit) as ctx:
            contencao.verificar_lock(raiz, "missao-y")
        self.assertIn("repositorio e de 'missao-x', nao de 'missao-y'",
                      str(ctx.exception))

    def test_lease_vencido_recusa_e_fence_divergente_recusa(self):
        # A metade forte de `P1A-04`, com arquivos reais — mantida.
        raiz = Path(self.locks).parent
        escritor = EscritorRepositorio(self.locks, "missao-x")
        fence = escritor.adquirir()
        self.addCleanup(escritor.liberar)
        contencao.verificar_lock(raiz, "missao-x", fence_esperado=fence)
        with self.assertRaises(SystemExit):
            contencao.verificar_lock(raiz, "missao-x",
                                     fence_esperado=fence + 1)
        caminho = caminho_lease(self.locks)
        with open(caminho, encoding="utf-8") as f:
            lease = json.load(f)
        lease["expira_em"] = time.time() - 1
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(lease, f)
        with self.assertRaises(SystemExit):
            contencao.verificar_lock(raiz, "missao-x")


class OLeaseNaoAlcancaOGit(unittest.TestCase):
    """A fronteira que esta missao mediu no proprio corpo."""

    @unittest.skipUnless(_tem_git(), "git indisponivel")
    def test_um_commit_acontece_com_o_lease_de_outra_sessao_vivo(self):
        # O caso que OCORREU: com um lease vivo, um processo que nao e o
        # titular commita, e nada o impede. Aqui num repositorio
        # descartavel, para medir sem tocar no repositorio real.
        with tempfile.TemporaryDirectory(prefix="p1a39-git-") as raiz:
            _git("init", "-q", cwd=raiz)
            _git("config", "user.email", "lab@local", cwd=raiz)
            _git("config", "user.name", "lab", cwd=raiz)
            escritor = EscritorP1(os.path.join(raiz, "locks"),
                                  sessao="titular-vivo")
            escritor.adquirir()
            try:
                escritor.verificar()  # o titular esta vivo, medido
                alvo = os.path.join(raiz, "arquivo.txt")
                with open(alvo, "w", encoding="utf-8") as f:
                    f.write("escrita de quem nao detem o lease\n")
                _git("add", "arquivo.txt", cwd=raiz)
                feito = _git("commit", "-q", "-m", "commit sem lease",
                             cwd=raiz)
                self.assertEqual(
                    feito.returncode, 0,
                    "o commit falhou por outro motivo; a medicao perdeu "
                    f"o objeto: {feito.stderr}")
                registro = _git("log", "--oneline", "-1", cwd=raiz)
                self.assertIn("commit sem lease", registro.stdout)
            finally:
                escritor.liberar()

    def test_nenhum_chamador_do_lease_esta_num_caminho_de_commit(self):
        # A razao estrutural: o lease e consultado antes de ESCREVER
        # EVIDENCIA e antes de INVOCAR PROVEDOR — nunca antes de
        # commitar, porque nenhum modulo do acervo commita.
        chamadores = _chamadores_do_lease()
        self.assertTrue(chamadores, "nenhum chamador do lease encontrado — "
                                    "a varredura perdeu o objeto")
        for nome in sorted(chamadores):
            for raiz in _RAIZES:
                caminho = os.path.join(raiz, f"{nome}.py")
                if not os.path.isfile(caminho):
                    continue
                with open(caminho, encoding="utf-8") as f:
                    fonte = f.read()
                with self.subTest(modulo=nome):
                    self.assertNotIn(
                        '"commit"', fonte,
                        f"{nome} commita E consulta o lease — a fronteira "
                        "medida aqui mudou e esta declaracao precisa ser "
                        "reescrita")

    def test_a_varredura_de_chamadores_alcanca_os_modulos_conhecidos(self):
        # Guarda anti-varredura-vazia: sem ele, `_chamadores_do_lease`
        # devolvendo `set()` deixaria o teste acima verde por vacuidade.
        chamadores = _chamadores_do_lease()
        for esperado in ("revisao_p1a33", "preflight_capsula",
                         "preflight_atual", "contencao"):
            with self.subTest(modulo=esperado):
                self.assertIn(esperado, chamadores)

    def test_o_repositorio_real_nao_tem_gancho_que_consulte_o_lease(self):
        # A outra maneira de fechar a fronteira seria um hook de Git. Nao
        # ha nenhum, e isso e medido: a ausencia e o estado, nao uma
        # suposicao.
        hooks = os.path.join(_RAIZ_REPO, ".git", "hooks")
        if not os.path.isdir(hooks):
            self.skipTest("sem diretorio de hooks")
        vivos = [h for h in sorted(os.listdir(hooks))
                 if not h.endswith(".sample")]
        self.assertEqual(vivos, [],
                         f"ha hook de Git vivo ({vivos}) — a medicao "
                         "desta fronteira precisa considera-lo")


if __name__ == "__main__":
    unittest.main()
