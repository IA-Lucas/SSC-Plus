"""P0-02 `cas.CAS` — os cinco ramos de recusa que faltavam. FASE 3.

A varredura mediu **2 de 7 ramos alcancados** (o teste existente cria
junction real, o que e forte, mas cobre um ramo so). Os cinco que
faltavam sao os que separam um armazenamento enderecado por conteudo de
um diretorio comum.

O CASO QUE OCORRE. O CAS guarda TODO payload de evento e TODO artefato
do acervo. Os ramos:
- hash malformado (curto, longo, com caractere fora do hex, nao-texto):
  e o que chega quando uma referencia vem corrompida de um log ou de um
  checkpoint, e o CAS nao pode transformar isso em leitura de caminho
  arbitrario;
- CAS somente-leitura (Evidence Plane) que recebe gravacao: e a
  fronteira entre o plano de execucao e o plano de evidencia;
- `gravar` com algo que nao e bytes;
- objeto CORROMPIDO em disco: o sha256 relido nao bate. E o unico ramo
  que prova a propriedade que da nome ao CAS.

O QUE ESTES TESTES NAO COBREM, declarado:
- symlink no destino de `gravar`/`ler` NAO e coberto aqui: criar link
  simbolico no Windows exige privilegio que a sessao pode nao ter, e o
  teste nao pode depender disso. `test_seguranca.py:81` cobre a
  travessia por junction, que e o caso vizinho e o que esta ao alcance;
- nao se afirma nada sobre concorrencia de gravacao entre processos;
- `_fsync_diretorio` nao e verificado: durabilidade nao e medivel por
  teste em processo.
"""

import os
import shutil
import unittest
import uuid

import apoio
from ssc_p0.cas import CAS, CorrupcaoDetectada, FugaDeCaminho


class RecusasDoCas(unittest.TestCase):

    def setUp(self):
        self.raiz = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        os.makedirs(self.raiz)
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        self.cas = CAS(os.path.join(self.raiz, "cas"))

    def test_hash_malformado_e_recusado(self):
        # Referencia corrompida vinda de um log nao pode virar leitura
        # de caminho arbitrario.
        for ruim in ("", "abc", "z" * 64, "A" * 64, "0" * 63, "0" * 65,
                     "../" + "0" * 61, None, 123, b"0" * 64):
            with self.subTest(hash=repr(ruim)[:24]):
                with self.assertRaises(FugaDeCaminho) as ctx:
                    self.cas.ler(ruim)
                self.assertIn("hash invalido", str(ctx.exception))

    def test_hash_malformado_e_recusado_tambem_em_existe(self):
        # `existe` tambem passa por `_caminho`: um consumidor que so
        # perguntasse "existe?" nao pode escapar da validacao.
        with self.assertRaises(FugaDeCaminho):
            self.cas.existe("nao-e-hash")

    def test_cas_somente_leitura_recusa_gravacao(self):
        # A fronteira do Evidence Plane.
        evidencia = CAS(os.path.join(self.raiz, "cas"), somente_leitura=True)
        with self.assertRaises(PermissionError) as ctx:
            evidencia.gravar(b"tentativa")
        self.assertIn("somente leitura", str(ctx.exception))

    def test_cas_somente_leitura_nao_cria_diretorio(self):
        # Nao basta recusar a gravacao: abrir um CAS somente-leitura nao
        # pode CRIAR a arvore que ele diz so ler.
        caminho = os.path.join(self.raiz, "inexistente")
        CAS(caminho, somente_leitura=True)
        self.assertFalse(os.path.exists(caminho))

    def test_gravar_o_que_nao_e_bytes_e_recusado(self):
        for valor in ("texto", 42, None, ["b"], {"a": 1}):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(TypeError):
                    self.cas.gravar(valor)

    def test_objeto_corrompido_no_disco_e_recusado(self):
        # A propriedade que da nome ao CAS: enderecado por CONTEUDO. Se
        # o conteudo mudou, a referencia deixou de valer — e ler o que
        # esta la seria servir dado adulterado sob o hash antigo.
        ref = self.cas.gravar(b"conteudo original")
        caminho = self.cas._caminho(ref)
        with open(caminho, "wb") as f:
            f.write(b"conteudo adulterado")
        with self.assertRaises(CorrupcaoDetectada) as ctx:
            self.cas.ler(ref)
        self.assertIn(ref, str(ctx.exception))

    def test_gravacao_idempotente_reverifica_antes_de_aceitar(self):
        # Regravar o MESMO conteudo e idempotente — mas so depois de
        # conferir o que esta em disco. Com o objeto corrompido, a
        # regravacao tem de falhar em vez de devolver o hash em silencio.
        ref = self.cas.gravar(b"conteudo original")
        with open(self.cas._caminho(ref), "wb") as f:
            f.write(b"adulterado")
        with self.assertRaises(CorrupcaoDetectada):
            self.cas.gravar(b"conteudo original")

    def test_gravacao_e_leitura_legitimas_atravessam(self):
        # Contraprova: sem ela, um CAS que recusasse sempre passaria em
        # todos os testes acima.
        ref = self.cas.gravar(b"dados legitimos")
        self.assertEqual(len(ref), 64)
        self.assertEqual(self.cas.ler(ref), b"dados legitimos")
        self.assertTrue(self.cas.existe(ref))
        self.assertEqual(self.cas.gravar(b"dados legitimos"), ref)

    def test_cas_somente_leitura_le_o_que_o_outro_gravou(self):
        # A outra metade da contraprova: somente-leitura nao e inutil.
        ref = self.cas.gravar(b"evidencia")
        evidencia = CAS(os.path.join(self.raiz, "cas"), somente_leitura=True)
        self.assertEqual(evidencia.ler(ref), b"evidencia")


if __name__ == "__main__":
    unittest.main()
