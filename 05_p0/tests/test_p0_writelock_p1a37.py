"""P0-26 `writelock.LockSessao` — os ramos que faltavam. FASE 3.

A varredura mediu **2 de 4 ramos alcancados** — "lock de SO real em
tmpdir" — e foi exatamente sobre esta linha que o atestado da P1-A.3.6
fez a demonstracao da Declaracao 4: *"o eixo media ALCANCE DE LINHA, e a
linha era alcancada; o que ele nao podia ver e que o caso exercido nao e
o caso que ocorre"*.

Este arquivo NAO fecha o ACHADO 4 — a exclusao mutua ENTRE MISSOES de
nomes distintos e materia da Fase 4 desta missao, e continua aberta aqui
por construcao: `LockSessao` tranca `locks/<sessao>.lock`, e dois nomes
distintos trancam arquivos distintos. O que este arquivo faz e alcancar
os quatro ramos de recusa da primitiva COMO ELA E.

O CASO QUE OCORRE, ramo a ramo:
- guarda intra-processo: dois `LockSessao` vivos sobre o MESMO caminho
  no mesmo processo. O lock do SO nao distingue handles do mesmo
  processo, e sem este guarda dois kernels da mesma sessao coexistiriam
  no mesmo interpretador — que e o caso de uma missao que instancia o
  kernel duas vezes por engano;
- lock detido por OUTRO PROCESSO: exercido com subprocesso REAL, nao
  encenado. E o unico jeito de medir a primitiva do SO;
- `verificar()` sem lock ativo: o escritor que ja liberou, ou que nunca
  adquiriu, e mesmo assim tenta escrever;
- `verificar()` com fence DEFASADO: o escritor que "acorda" depois de
  outro ter assumido. E a defesa que sobrevive a morte de processo.

O QUE ESTES TESTES NAO COBREM, e e o essencial:
- **a exclusao entre missoes de NOMES DIFERENTES nao existe e nao e
  testada aqui** — ACHADO 4, Fase 4;
- nao ha corrida real com temporizacao: o subprocesso e sincronizado por
  arquivo-sinal, nao por disputa simultanea;
- nada se afirma sobre lock em sistema de arquivos de rede;
- `simular_crash` e simulacao de morte de processo, nao morte real.
"""

import os
import shutil
import subprocess
import sys
import textwrap
import time
import unittest
import uuid

import apoio
from ssc_p0.writelock import EscritorObsoleto, LockIndisponivel, LockSessao


class RecusasDoWritelock(unittest.TestCase):

    def setUp(self):
        self.raiz = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        os.makedirs(self.raiz)
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        self.lock = os.path.join(self.raiz, "s.lock")
        self.fence = os.path.join(self.raiz, "s.fence")

    def _novo(self):
        return LockSessao(self.lock, self.fence)

    def test_dois_kernels_vivos_no_mesmo_processo_sao_recusados(self):
        primeiro = self._novo()
        primeiro.adquirir()
        self.addCleanup(primeiro.liberar)
        with self.assertRaises(LockIndisponivel) as ctx:
            self._novo().adquirir()
        self.assertIn("kernel vivo", str(ctx.exception))

    def test_o_guarda_intra_processo_normaliza_o_caminho(self):
        # Dois caminhos textualmente diferentes para o MESMO arquivo nao
        # podem virar dois detentores. E o caso de quem passa o caminho
        # relativo num lugar e o absoluto noutro.
        primeiro = self._novo()
        primeiro.adquirir()
        self.addCleanup(primeiro.liberar)
        outro = LockSessao(os.path.join(self.raiz, ".", "s.lock"), self.fence)
        with self.assertRaises(LockIndisponivel):
            outro.adquirir()

    def test_lock_detido_por_outro_PROCESSO_e_recusado(self):
        # Subprocesso REAL: e o unico jeito de medir a primitiva do SO.
        sinal = os.path.join(self.raiz, "adquirido.txt")
        programa = textwrap.dedent(f"""
            import sys, time
            sys.path.insert(0, {os.path.dirname(apoio._DIR_P0)!r})
            sys.path.insert(0, {apoio._DIR_P0!r})
            from ssc_p0.writelock import LockSessao
            lock = LockSessao({self.lock!r}, {self.fence!r})
            lock.adquirir()
            open({sinal!r}, "w").write("ok")
            time.sleep(10)
            """)
        filho = subprocess.Popen([sys.executable, "-c", programa])
        self.addCleanup(filho.kill)
        try:
            limite = time.monotonic() + 15
            while not os.path.exists(sinal):
                self.assertLess(time.monotonic(), limite,
                                "o subprocesso nao adquiriu o lock")
                self.assertIsNone(filho.poll(), "o subprocesso morreu")
                time.sleep(0.02)
            with self.assertRaises(LockIndisponivel) as ctx:
                self._novo().adquirir()
            self.assertIn("outro processo", str(ctx.exception))
        finally:
            filho.kill()
            filho.wait(timeout=10)

    def test_verificar_sem_lock_ativo_e_recusado(self):
        escritor = self._novo()
        with self.assertRaises(EscritorObsoleto) as ctx:
            escritor.verificar()
        self.assertIn("sem lock ativo", str(ctx.exception))

    def test_verificar_depois_de_liberar_e_recusado(self):
        escritor = self._novo()
        escritor.adquirir()
        escritor.verificar()          # vivo: nao levanta
        escritor.liberar()
        with self.assertRaises(EscritorObsoleto):
            escritor.verificar()

    def test_escritor_com_fence_defasado_e_recusado(self):
        # O escritor que "acorda" depois de outro assumir. E a defesa
        # que sobrevive a morte de processo: o token velho nunca mais
        # escreve, mesmo que o objeto ainda exista em memoria.
        antigo = self._novo()
        antigo.adquirir()
        antigo.simular_crash()        # morte: solta o lock do SO
        sucessor = self._novo()
        self.addCleanup(sucessor.liberar)
        self.assertEqual(sucessor.adquirir(), antigo.token + 1)
        antigo._ativo = True          # o objeto velho "acorda"
        with self.assertRaises(EscritorObsoleto) as ctx:
            antigo.verificar()
        self.assertIn("fencing token defasado", str(ctx.exception))

    def test_fence_ilegivel_conta_como_zero_e_nao_explode(self):
        # Arquivo de fence corrompido nao pode virar excecao crua: a
        # unicidade nao depende dele (quem a garante e o lock do SO), e
        # o fencing e defesa secundaria.
        with open(self.fence, "wb") as f:
            f.write(b"isto nao e um inteiro")
        escritor = self._novo()
        self.addCleanup(escritor.liberar)
        self.assertEqual(escritor.adquirir(), 1)

    def test_aquisicao_legitima_e_sucessao_atravessam(self):
        # Contraprova: sem ela, um lock que recusasse sempre passaria em
        # todos os testes acima — e a sucessao apos liberacao e o caso
        # normal de handoff entre missoes.
        primeiro = self._novo()
        self.assertEqual(primeiro.adquirir(), 1)
        primeiro.verificar()
        primeiro.liberar()
        segundo = self._novo()
        self.addCleanup(segundo.liberar)
        self.assertEqual(segundo.adquirir(), 2)
        segundo.verificar()

    def test_o_ACHADO_4_continua_aberto_e_isto_e_medido(self):
        # Nomes de sessao distintos trancam ARQUIVOS distintos: as duas
        # aquisicoes passam. Nao e teste de que esta certo — e a medicao
        # de que a exclusao entre missoes NAO existe nesta primitiva, e
        # o registro de que a Fase 4 e quem trata disso.
        uma = LockSessao(os.path.join(self.raiz, "missao-a.lock"),
                         os.path.join(self.raiz, "missao-a.fence"))
        outra = LockSessao(os.path.join(self.raiz, "missao-b.lock"),
                           os.path.join(self.raiz, "missao-b.fence"))
        self.addCleanup(uma.liberar)
        self.addCleanup(outra.liberar)
        uma.adquirir()
        outra.adquirir()              # NAO levanta — e o ACHADO 4
        uma.verificar()
        outra.verificar()


if __name__ == "__main__":
    unittest.main()
