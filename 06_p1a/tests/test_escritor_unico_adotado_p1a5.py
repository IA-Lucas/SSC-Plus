"""A ADOCAO do escritor unico, exercida — SSC+ P1-A.5, ordem 2.

O ACHADO, na voz do revisor independente da P1-A.4 (`P1A4-1`, familia
`fora de ambas`, falha de INTEGRACAO):

    "declara e testa que o lock unico novo NAO ESTA EM USO; o mecanismo
    vivo continua permitindo escritores de nomes distintos"

O modulo correto existia desde a P1-A.3.7 e era provado entre processos
reais — em ISOLADO. Nenhum runner o importava, e havia guarda exigindo
que ninguem o importasse. O defeito nunca foi o mecanismo: foi a
FIACAO. Por isso este arquivo nao mede o `EscritorRepositorio` outra vez
(`test_escritor_repositorio_p1a37.py` ja o faz, e continua fazendo):
mede que **a operacao passa por ele**.

## As tres provas que o ato exigiu, e onde cada uma esta

(a) *"duas sessoes de NOMES DIFERENTES tentando adquirir — a segunda
    falha antes de escrever um byte"* — `AAquisicaoEntreProcessosReais`.
    Dois processos REAIS do `renovador_lock.py`, que e o ponto de
    entrada que a operacao de fato executa, e nao um construtor chamado
    de dentro do teste. A segunda metade e o manifesto SHA-256 do
    diretorio de locks, IDENTICO antes e depois da tentativa falha:
    "falhou" sem isso admitiria um mecanismo que escreve e desiste.

(c) *"o caminho operacional real usa o mecanismo novo, nao so o teste"* —
    `CadaPontoDeChamadaRecusaOutroTitular` e `ORunnerRealNaoGravaUmByte`.
    O primeiro exerce a funcao que CADA runner do acervo chama, uma por
    uma, contra um lease detido por outro nome; o segundo roda o `main()`
    de um runner de verdade e mede que nada foi gravado. A licao do
    achado N4 aplicada: primitiva corrigida nao cobre ponto de chamada.

(b) a reversao vermelha nao mora aqui: ela e MEDICAO, feita revertendo o
    codigo e contando os vermelhos, e esta registrada em
    `06_p1a/99_decisao-p1a5.md` §3.

## O CASO QUE OCORRE EM OPERACAO, e nao o vizinho dele

O que ocorre e: uma missao segura o escritor sob um nome, outra missao —
de nome proprio, como este repositorio manda — tenta trabalhar. Ate a
P1-A.4 as duas trabalhavam, cada uma se vendo como escritor unico. O
vizinho que estes testes NAO exercem, de proposito, e o par de nomes
IGUAIS: essa metade sempre funcionou e ja tem guarda
(`test_fronteira_escritor_p1a39`).

## O QUE ESTES TESTES NAO COBREM, declarado

- **nao provam exclusao contra quem nao passa pelo escritor.** O
  mecanismo e cooperativo; `git commit` segue sem consultar lease, e a
  medicao disso continua em `test_fronteira_escritor_p1a39`, intacta.
  Fechar o ACHADO 4 nao move essa fronteira;
- **nao ha disputa simultanea com temporizacao.** Os dois processos sao
  sincronizados por arquivo-sinal: o primeiro adquire, avisa, e so entao
  o segundo tenta. Corrida real nao e o objeto;
- **nenhum CLI de assinatura e invocado** e nenhum modelo responde: o
  "reviewer" e um `python -c`. O que se exerce e o portao do escritor;
- **nada aqui afirma que os `locks/` de dois repositorios se excluam** —
  a exclusao vale para o diretorio recebido, por construcao;
- **a varredura de pontos de chamada e a lista `PONTOS_OPERACIONAIS`**,
  escrita a mao. Ela cobre os modulos que hoje verificam o escritor; um
  runner novo que nao entre nela nao e medido aqui, e sim pelo guarda
  estrutural de `test_escritor_repositorio_p1a37`.
"""

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import apoio  # (insere 06_p1a/05_p0 no sys.path e traz `escrever_lock`)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402
from escritor_repositorio import (EscritorRepositorio,  # noqa: E402
                                  caminho_lease, titular_atual)

_RENOVADOR = os.path.join(_DIR_P1A, "evidencias", "renovador_lock.py")

# Arquivos que `revisao_p1a2.montar_prompt` le da arvore, copiados para a
# raiz descartavel para que `main()` corra INTEIRA.
_FONTES_DO_PROMPT = (
    "06_p1a/capsula.py",
    "06_p1a/preflight/adaptadores.py",
    "06_p1a/tests/test_capsula_p1a2.py",
    "06_p1a/06_adendo-capsula-p1a2.md",
)


def _manifesto(diretorio) -> dict:
    """SHA-256 de cada arquivo — o que prova "nem um byte".

    LIMITE DECLARADO: o proprio `.lock` fica travado pelo SO enquanto ha
    detentor, e no Windows nem se le. Para ele guarda-se o TAMANHO, que
    ainda detecta crescimento — a forma que uma escrita nele teria —,
    mas nao troca de bytes de mesmo tamanho dentro do arquivo travado.
    """
    saida = {}
    for base, _, arquivos in os.walk(diretorio):
        for nome in sorted(arquivos):
            caminho = os.path.join(base, nome)
            rel = os.path.relpath(caminho, diretorio)
            try:
                with open(caminho, "rb") as f:
                    saida[rel] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                saida[rel] = f"<travado:{os.path.getsize(caminho)}>"
    return saida


def _carregar(rel, apelido):
    caminho = os.path.join(_RAIZ, *rel.split("/"))
    spec = importlib.util.spec_from_file_location(apelido, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


class AAquisicaoEntreProcessosReais(unittest.TestCase):
    """(a) — dois processos, dois nomes, um escritor so."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a5-adocao-")
        self.addCleanup(self._tmp.cleanup)
        self.locks = os.path.join(self._tmp.name, "locks")
        os.makedirs(self.locks)

    def _primeiro_titular(self, nome):
        """Sobe o renovador REAL e espera ele anunciar a aquisicao.

        As saidas vao para DEVNULL de proposito: com `PIPE`, qualquer
        leitura do canal de um processo VIVO bloqueia ate o EOF, e o
        renovador so termina quando o teste o mata. Nao ha nada a ler
        aqui — o que se observa e o LEASE em disco, que e o que a
        operacao observa.
        """
        filho = subprocess.Popen(
            [sys.executable, _RENOVADOR, nome, self.locks],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self._encerrar, filho)
        limite = time.monotonic() + 30
        while titular_atual(self.locks) is None:
            self.assertLess(time.monotonic(), limite,
                            "o renovador nao adquiriu o escritor")
            self.assertIsNone(filho.poll(), "o renovador morreu antes de "
                                            "adquirir o escritor")
            time.sleep(0.02)
        return filho

    @staticmethod
    def _encerrar(filho):
        """Mata E ESPERA: o `.lock` fica aberto ate o processo sair, e no
        Windows a limpeza do descartavel falha enquanto ele existir."""
        filho.kill()
        filho.wait(timeout=10)

    def test_a_segunda_missao_de_OUTRO_nome_para_sem_escrever_um_byte(self):
        filho = self._primeiro_titular("missao-alfa-ops")
        try:
            antes = _manifesto(self.locks)
            segunda = subprocess.run(
                [sys.executable, _RENOVADOR, "missao-beta-ops", self.locks],
                capture_output=True, text=True, timeout=60)
            # (i) o ponto de entrada PARA, com codigo proprio.
            self.assertEqual(segunda.returncode, 3, segunda.stderr)
            self.assertIn("PARADA", segunda.stderr)
            self.assertIn("missao-alfa-ops", segunda.stderr)
            # (ii) NEM UM BYTE: o diretorio de locks esta identico.
            self.assertEqual(_manifesto(self.locks), antes,
                             "a tentativa falha escreveu no diretorio")
            # (iii) e o titular continua sendo o primeiro, nomeado.
            self.assertEqual(titular_atual(self.locks)["sessao"],
                             "missao-alfa-ops")
        finally:
            self._encerrar(filho)

    def test_depois_que_o_titular_morre_a_outra_missao_adquire(self):
        # Contraprova indispensavel: sem ela, um escritor que recusasse
        # SEMPRE passaria no teste acima e travaria o repositorio para
        # sempre. O sucessor entra com fence maior.
        filho = self._primeiro_titular("missao-alfa-ops")
        fence_antes = int(Path(self.locks, "repositorio.fence").read_text())
        self._encerrar(filho)
        sucessora = EscritorRepositorio(self.locks, "missao-beta-ops")
        self.addCleanup(sucessora.liberar)
        self.assertEqual(sucessora.adquirir(), fence_antes + 1)
        self.assertEqual(titular_atual(self.locks)["sessao"],
                         "missao-beta-ops")


# Cada ponto do acervo que verifica o escritor antes de gravar ou de
# invocar provedor, com o modo de aplica-lo. `sessao` e o nome que aquele
# ponto usa; o teste segura o escritor sob OUTRO nome e exige PARADA.
def _pt_contencao(raiz, sessao):
    contencao.verificar_lock(raiz, sessao)


def _pt_capsula(raiz, sessao):
    import preflight_capsula
    with mock.patch.object(preflight_capsula, "_SESSAO_LOCK", sessao):
        preflight_capsula._verificar_lock_vivo(raiz=raiz)


def _pt_p1b(raiz, sessao):
    mod = _carregar("07_p1b/preflight_atual.py", "p1b_adocao")
    with mock.patch.object(mod, "_RAIZ", raiz), \
            mock.patch.object(mod, "_SESSAO_LOCK", sessao):
        mod._verificar_lock_vivo()


def _pt_revisao(rel, apelido):
    def aplicar(raiz, sessao):
        mod = _carregar(rel, apelido)
        with mock.patch.object(mod, "RAIZ", Path(raiz)), \
                mock.patch.object(mod, "SESSAO_LOCK", sessao):
            mod._verificar_lock()
    return aplicar


PONTOS_OPERACIONAIS = {
    "contencao.verificar_lock": _pt_contencao,
    "preflight_capsula": _pt_capsula,
    "07_p1b/preflight_atual": _pt_p1b,
    "revisao_p1a2": _pt_revisao("06_p1a/evidencias/revisao_p1a2.py",
                                "p1a2_adocao"),
    "revisao_p1a4": _pt_revisao("06_p1a/evidencias/revisao_p1a4.py",
                                "p1a4_adocao"),
}


class CadaPontoDeChamadaRecusaOutroTitular(unittest.TestCase):
    """(c) — o caminho operacional, ponto de chamada por ponto de chamada.

    O achado N4 na letra: *primitiva corrigida nao cobre ponto de
    chamada*. Corrigir `contencao.verificar_lock` e exercer so ela
    deixaria de fora as copias e os invocadores — foi exatamente o
    defeito que a P1-A.3.5 mediu na P1-B.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a5-pontos-")
        self.addCleanup(self._tmp.cleanup)
        self.raiz = self._tmp.name
        self.locks = os.path.join(self.raiz, "locks")

    def test_com_o_escritor_de_OUTRA_missao_todo_ponto_PARA(self):
        # O lease e real em disco e nomeia `missao-alfa-ops`; cada ponto
        # trabalha em nome de `missao-beta-ops`, como faria uma segunda
        # missao. Nenhum pode passar.
        apoio.escrever_lock(self.locks, "missao-alfa-ops", 1,
                            time.time() + 600)
        for nome, aplicar in PONTOS_OPERACIONAIS.items():
            with self.subTest(ponto=nome):
                with self.assertRaises(SystemExit) as ctx:
                    aplicar(self.raiz, "missao-beta-ops")
                self.assertIn("missao-alfa-ops", str(ctx.exception),
                              f"{nome} parou, mas nao por causa do titular")

    def test_com_o_escritor_da_PROPRIA_missao_todo_ponto_passa(self):
        # Contraprova, e ela e o que separa medicao de teatro: sem esta,
        # um ponto que levantasse SystemExit sempre passaria no teste
        # acima e o guarda nao mediria nada.
        apoio.escrever_lock(self.locks, "missao-alfa-ops", 1,
                            time.time() + 600)
        for nome, aplicar in PONTOS_OPERACIONAIS.items():
            with self.subTest(ponto=nome):
                aplicar(self.raiz, "missao-alfa-ops")

    def test_o_titular_vem_do_lease_UNICO_e_nao_de_um_arquivo_por_nome(self):
        # A propriedade estrutural que a troca criou, exercida: existe UM
        # lease, e o nome vive DENTRO dele. Antes da P1-A.5 haveria dois
        # arquivos e os dois pontos passariam — que e o ACHADO 4.
        apoio.escrever_lock(self.locks, "missao-alfa-ops", 1,
                            time.time() + 600)
        self.assertEqual(sorted(os.listdir(self.locks)),
                         ["repositorio.fence", "repositorio.lease"])
        self.assertEqual(json.loads(Path(caminho_lease(self.locks))
                                    .read_text(encoding="utf-8"))["sessao"],
                         "missao-alfa-ops")


class ORunnerRealNaoGravaUmByte(unittest.TestCase):
    """(c), a metade que so o `main()` de verdade responde.

    Exercer as funcoes de verificacao uma a uma ainda deixaria em pe a
    pergunta que interessa em operacao: *e o runner, grava?*. Aqui
    `revisao_p1a2.main()` corre inteiro, com o escritor detido por um
    processo REAL de outro nome.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a5-runner-")
        self.raiz = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        for rel in _FONTES_DO_PROMPT:
            destino = self.raiz / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(os.path.join(_RAIZ, *rel.split("/")), destino)
        self.saida = self.raiz / "06_p1a" / "evidencias" / "revisao-p1a2"
        self.locks = str(self.raiz / "locks")
        os.makedirs(self.locks)

    def _rodar(self):
        modulo = _carregar("06_p1a/evidencias/revisao_p1a2.py",
                           "p1a2_runner_adocao")
        env_minimo = {k: os.environ[k] for k in
                      ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
                       "PATHEXT") if k in os.environ}
        with mock.patch.dict(os.environ, env_minimo, clear=True), \
                mock.patch.object(modulo, "RAIZ", self.raiz), \
                mock.patch.object(modulo, "SAIDA", self.saida), \
                mock.patch.object(modulo, "COMANDOS", {
                    "codex": lambda tmp, prompt: [
                        sys.executable, "-c", "print('revisao de mentira')"]}), \
                mock.patch.object(sys, "argv", ["revisao_p1a2.py", "codex"]), \
                mock.patch("sys.stdout", _SaidaMuda()):
            return modulo.main()

    def _gravados(self):
        if not self.saida.is_dir():
            return []
        return sorted(p.name for p in self.saida.iterdir())

    def test_com_o_escritor_de_outro_processo_o_runner_nao_grava(self):
        # `revisao_p1a2` opera sob `SESSAO_LOCK` proprio; o escritor esta
        # com `missao-alfa-ops`, num processo REAL. Ate a P1-A.4 os dois
        # nomes trancavam arquivos diferentes e este runner gravaria.
        titular = EscritorRepositorio(self.locks, "missao-alfa-ops")
        titular.adquirir()
        try:
            with self.assertRaises(SystemExit) as ctx:
                self._rodar()
            self.assertIn("missao-alfa-ops", str(ctx.exception))
            self.assertEqual(self._gravados(), [],
                             "o runner gravou com escritor de outra missao")
        finally:
            titular.liberar()

    def test_sob_o_proprio_escritor_o_runner_grava(self):
        # Contraprova: o runner precisa continuar funcionando. Sem ela, a
        # adocao poderia ter simplesmente quebrado a operacao e o teste
        # acima ficaria verde do mesmo jeito.
        modulo = _carregar("06_p1a/evidencias/revisao_p1a2.py",
                           "p1a2_contraprova_adocao")
        titular = EscritorRepositorio(self.locks, modulo.SESSAO_LOCK)
        titular.adquirir()
        try:
            self.assertEqual(self._rodar(), 0)
            gravados = self._gravados()
            self.assertEqual(len(gravados), 1)
            with open(self.saida / gravados[0], encoding="utf-8") as f:
                evidencia = json.load(f)
            self.assertTrue(
                evidencia["lock_verificado_antes_da_persistencia"])
            self.assertEqual(evidencia["lock_escritor_unico"]["sessao"],
                             modulo.SESSAO_LOCK)
        finally:
            titular.liberar()


if __name__ == "__main__":
    unittest.main()
