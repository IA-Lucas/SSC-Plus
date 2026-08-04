"""Exclusao mutua ENTRE MISSOES — SSC+ P1-A.3.7, FASE 4 (ACHADO 4 / N1).

O ACHADO, aberto desde 2026-07-31 e elevado a MAJOR por revisor
independente: `LockSessao` tranca `locks/<sessao>.lock`, de modo que
duas missoes de NOMES DIFERENTES trancam arquivos diferentes e nenhuma
exclui a outra. O escritor unico ENTRE MISSOES nunca existiu — o que
existia e escritor unico por nome de sessao, que e outra propriedade. A
frase do revisor: *"a ordem manual do Fundador nao substitui exclusao
mutua"*.

A PROVA EXIGIDA PELO ATO, literal: *"duas sessoes de NOMES DIFERENTES
tentando adquirir, e a segunda falha ANTES DE ESCREVER UM BYTE"*. Ela
esta em `test_segunda_missao_de_outro_nome_falha_antes_de_escrever`, e
tem duas metades que nao se substituem:
(a) a segunda aquisicao levanta `LockIndisponivel`;
(b) o manifesto SHA-256 do diretorio de locks e IDENTICO antes e depois
    da tentativa falha. "Falhou" sem (b) admitiria um mecanismo que
    escreve e depois desiste.

E ha a prova CRUZADA, que e o que separa medicao de afirmacao: o mesmo
cenario, com o mecanismo VIVO (`EscritorP1`), deixa as duas missoes
adquirirem. O ACHADO 4 e medido no proprio arquivo que o corrige — nao
citado de um registro.

O MECANISMO VIVO FOI TROCADO NA P1-A.5, ordem 2. Ate a P1-A.4 este
modulo vivia em ISOLADO por ordem expressa, e havia aqui um teste
exigindo que NENHUM runner o importasse. O revisor da P1-A.4 leu essa
mesma medicao e a classificou como falha de INTEGRACAO (`P1A4-1`).
Autorizada a troca, o teste nao foi apagado: ele foi INVERTIDO
(`OMecanismoVivoFOITrocado`), e agora fica vermelho se a adocao for
desfeita.

O QUE ESTES TESTES NAO COBREM, declarado:
- o mecanismo e COOPERATIVO. Um processo que escreva no repositorio sem
  passar por aqui nao e barrado por nada, e nenhum teste afirma o
  contrario;
- a prova entre processos usa dois processos REAIS sincronizados por
  arquivo-sinal, nao disputa simultanea com temporizacao;
- nada se afirma sobre lock em sistema de arquivos de rede;
- a exclusao vale para o diretorio de locks recebido: dois repositorios
  distintos tem escritores distintos, e isso e por construcao.
"""

import hashlib
import json
import os
import subprocess
import sys
import textwrap
import time
import unittest

import apoio  # noqa: F401  (insere 06_p1a e 05_p0 no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

from escritor import EscritorP1  # noqa: E402
from escritor_repositorio import (EscritorObsoleto,  # noqa: E402
                                  EscritorRepositorio, LockIndisponivel,
                                  NOME_DO_LOCK, titular_atual)

import tempfile  # noqa: E402


def manifesto(diretorio) -> dict:
    """SHA-256 de cada arquivo do diretorio — o que prova "nem um byte".

    LIMITE DECLARADO: o proprio `.lock` fica travado pelo SO enquanto ha
    detentor, e no Windows nem se le. Para ele o manifesto guarda o
    TAMANHO, nao o hash — o que ainda detecta crescimento, que e a forma
    que uma escrita nele teria, mas nao detectaria troca de bytes de
    mesmo tamanho dentro do arquivo travado.
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


class ExclusaoEntreMissoesDeNomesDiferentes(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-repo-lock-")
        self.locks = os.path.join(self._tmp.name, "locks")
        os.makedirs(self.locks)
        self.addCleanup(self._tmp.cleanup)

    # --- a prova exigida pelo ato --------------------------------------

    def test_segunda_missao_de_outro_nome_falha_antes_de_escrever(self):
        primeira = EscritorRepositorio(self.locks, "missao-alfa-ops")
        self.addCleanup(primeira.liberar)
        primeira.adquirir()

        antes = manifesto(self.locks)
        segunda = EscritorRepositorio(self.locks, "missao-beta-ops")
        with self.assertRaises(LockIndisponivel) as ctx:
            segunda.adquirir()
        self.assertIn("lock da sessao", str(ctx.exception))

        # (b) NEM UM BYTE: o diretorio de locks esta identico.
        self.assertEqual(manifesto(self.locks), antes,
                         "a tentativa falha escreveu no diretorio de locks")
        # E o titular continua sendo a primeira, nomeada.
        self.assertEqual(titular_atual(self.locks)["sessao"],
                         "missao-alfa-ops")

    def test_a_prova_cruzada_o_mecanismo_VIVO_deixa_as_duas_entrarem(self):
        # O ACHADO 4 medido aqui, e nao citado. Com `EscritorP1`, os
        # nomes distintos trancam ARQUIVOS distintos e ambas adquirem.
        alfa = EscritorP1(self.locks, sessao="missao-alfa-ops")
        beta = EscritorP1(self.locks, sessao="missao-beta-ops")
        self.addCleanup(alfa.liberar)
        self.addCleanup(beta.liberar)
        alfa.adquirir()
        beta.adquirir()          # NAO levanta — e o ACHADO 4
        alfa.verificar()
        beta.verificar()         # duas escritoras vivas ao mesmo tempo

    def test_entre_PROCESSOS_a_segunda_missao_tambem_falha(self):
        # Lock de arquivo so vale se valer entre processos. Subprocesso
        # REAL segura o escritor sob um nome; esta sessao tenta com
        # OUTRO nome.
        sinal = os.path.join(self._tmp.name, "adquirido.txt")
        programa = textwrap.dedent(f"""
            import sys, time
            sys.path.insert(0, {os.path.join(_RAIZ, "05_p0")!r})
            sys.path.insert(0, {_DIR_P1A!r})
            from escritor_repositorio import EscritorRepositorio
            e = EscritorRepositorio({self.locks!r}, "missao-do-subprocesso")
            e.adquirir()
            open({sinal!r}, "w").write("ok")
            time.sleep(20)
            """)
        filho = subprocess.Popen([sys.executable, "-c", programa])
        self.addCleanup(filho.kill)
        try:
            limite = time.monotonic() + 20
            while not os.path.exists(sinal):
                self.assertLess(time.monotonic(), limite,
                                "o subprocesso nao adquiriu o escritor")
                self.assertIsNone(filho.poll(), "o subprocesso morreu")
                time.sleep(0.02)
            antes = manifesto(self.locks)
            outra = EscritorRepositorio(self.locks, "missao-desta-sessao")
            with self.assertRaises(LockIndisponivel):
                outra.adquirir()
            self.assertEqual(manifesto(self.locks), antes)
            self.assertEqual(titular_atual(self.locks)["sessao"],
                             "missao-do-subprocesso")
        finally:
            filho.kill()
            filho.wait(timeout=10)

    # --- liberar() expira o lease que concedeu --------------------------

    def test_liberar_expira_o_lease_e_o_titular_some(self):
        # O remedio do §9.4, N1. Um lease que sobrevive ao detentor
        # afirma o que nao ha.
        escritor = EscritorRepositorio(self.locks, "missao-alfa-ops")
        escritor.adquirir()
        self.assertEqual(titular_atual(self.locks)["sessao"],
                         "missao-alfa-ops")
        escritor.liberar()
        self.assertIsNone(titular_atual(self.locks),
                          "o lease sobreviveu ao detentor")

    def test_o_lease_liberado_guarda_a_evidencia_de_que_houve_titular(self):
        # Apagar o arquivo apagaria a evidencia. Ele fica, VENCIDO, com
        # `liberado_em` — e quem auditar sabe quem esteve la.
        escritor = EscritorRepositorio(self.locks, "missao-alfa-ops")
        escritor.adquirir()
        escritor.liberar()
        with open(os.path.join(self.locks, f"{NOME_DO_LOCK}.lease"),
                  encoding="utf-8") as f:
            lease = json.load(f)
        self.assertEqual(lease["sessao"], "missao-alfa-ops")
        self.assertIn("liberado_em", lease)
        self.assertLessEqual(lease["expira_em"], time.time())

    def test_o_mecanismo_VIVO_deixa_o_lease_sobreviver_ao_detentor(self):
        # A prova cruzada da segunda metade: com `EscritorP1`, depois de
        # `liberar()` o lease continua valendo, e um leitor ve escritor
        # vivo onde nao ha.
        vivo = EscritorP1(self.locks, sessao="missao-alfa-ops")
        vivo.adquirir()
        vivo.liberar()
        self.assertFalse(
            EscritorP1.lease_expirado(vivo.caminho_lease),
            "o mecanismo vivo mudou: o lease agora expira ao liberar")

    # --- sucessao e verificacao ----------------------------------------

    def test_apos_liberar_outra_missao_adquire_com_fence_maior(self):
        # Contraprova: sem ela, um escritor que recusasse sempre passaria
        # em todos os testes acima e o repositorio ficaria travado.
        alfa = EscritorRepositorio(self.locks, "missao-alfa-ops")
        primeiro = alfa.adquirir()
        alfa.liberar()
        beta = EscritorRepositorio(self.locks, "missao-beta-ops")
        self.addCleanup(beta.liberar)
        self.assertEqual(beta.adquirir(), primeiro + 1)
        beta.verificar()
        self.assertEqual(titular_atual(self.locks)["sessao"],
                         "missao-beta-ops")

    def test_verificar_recusa_quem_nao_e_o_titular_registrado(self):
        # Sem esta condicao, uma sessao poderia gravar sob o lease de
        # outra se o fence coincidisse, e o nome no lease nao
        # significaria nada.
        alfa = EscritorRepositorio(self.locks, "missao-alfa-ops")
        self.addCleanup(alfa.liberar)
        alfa.adquirir()
        impostora = EscritorRepositorio(self.locks, "missao-impostora")
        impostora._lock.token = alfa.token
        impostora._lock._ativo = True
        with self.assertRaises(EscritorObsoleto) as ctx:
            impostora.verificar()
        self.assertIn("titular do repositorio e", str(ctx.exception))

    def test_sessao_sem_nome_e_recusada(self):
        for nome in ("", "   ", "\t"):
            with self.subTest(nome=repr(nome)):
                with self.assertRaises(ValueError):
                    EscritorRepositorio(self.locks, nome)

    def test_lease_vencido_nao_tem_titular(self):
        escritor = EscritorRepositorio(self.locks, "missao-alfa-ops",
                                       lease_s=-1)
        self.addCleanup(escritor.liberar)
        escritor.adquirir()
        self.assertIsNone(titular_atual(self.locks))
        with self.assertRaises(EscritorObsoleto):
            escritor.verificar()


class OMecanismoVivoFOITrocado(unittest.TestCase):
    """P1-A.5, ordem 2: o inverso exato do que esta classe media antes.

    Ate a P1-A.4 ela exigia que NENHUM runner importasse este modulo — o
    isolamento era a ordem em vigor. Foi essa medicao que o revisor da
    P1-A.4 leu e classificou como falha de INTEGRACAO (`P1A4-1`): *"o
    lock unico novo nao esta em uso"*. Autorizada a troca, o guarda nao
    e apagado: ele passa a exigir o oposto, e continua vermelho se
    alguem desfizer a adocao.
    """

    # Os pontos operacionais que TEM de passar pelo escritor unico. Nao e
    # a lista do que existe: e a lista do que, se sair daqui, reabre o
    # ACHADO 4 sem ninguem perceber.
    CAMINHOS_OPERACIONAIS = (
        os.path.join("06_p1a", "evidencias", "renovador_lock.py"),
        os.path.join("06_p1a", "evidencias", "prova_minima.py"),
        os.path.join("06_p1a", "evidencias", "contencao.py"),
        os.path.join("07_p1b", "preflight_atual.py"),
    )

    def test_o_caminho_operacional_real_importa_o_escritor_novo(self):
        for rel in self.CAMINHOS_OPERACIONAIS:
            with self.subTest(modulo=rel):
                with open(os.path.join(_RAIZ, rel), encoding="utf-8") as f:
                    self.assertIn(
                        "escritor_repositorio", f.read(),
                        f"{rel} deixou de usar o escritor unico: o ACHADO 4 "
                        "volta por este caminho")

    def test_nenhum_modulo_de_producao_adquire_mais_o_escritor_por_sessao(self):
        # A outra metade, e a que importa: nao basta importar o novo — nao
        # pode sobrar quem ADQUIRA o antigo. `EscritorP1` continua no
        # acervo (a prova cruzada depende dele), mas quem o instancia fora
        # dos testes esta abrindo um segundo escritor por nome.
        instanciam = []
        for base, dirs, arquivos in os.walk(_RAIZ):
            dirs[:] = [d for d in dirs
                       if d not in ("__pycache__", ".git", "tests")]
            for nome in arquivos:
                if not nome.endswith(".py"):
                    continue
                caminho = os.path.join(base, nome)
                with open(caminho, encoding="utf-8") as f:
                    fonte = f.read()
                if "EscritorP1(" in fonte and nome != "escritor.py":
                    instanciam.append(os.path.relpath(caminho, _RAIZ))
        self.assertEqual(
            instanciam, [],
            "modulo de producao ainda constroi o escritor POR SESSAO")

    def test_o_escritor_por_sessao_continua_existindo_e_intacto(self):
        # Trocar nao e apagar. `EscritorP1` segue correto no que sempre
        # garantiu, e a prova cruzada deste arquivo mede o ACHADO 4 com
        # ele — sem ele, o achado voltaria a ser citado em vez de medido.
        self.assertTrue(hasattr(EscritorP1, "lease_expirado"))
        escritor = EscritorP1(self.locks_tmp(), sessao="qualquer-ops")
        self.assertTrue(escritor.caminho_lease.endswith("qualquer-ops.lease"))

    def locks_tmp(self):
        tmp = tempfile.TemporaryDirectory(prefix="p1a37-vivo-")
        self.addCleanup(tmp.cleanup)
        return tmp.name


if __name__ == "__main__":
    unittest.main()
