"""P0-03 `cas.ler_arquivo_contido` — os ramos de recusa. FASE 3.

A varredura classificou este ponto SEM-TESTE com a medicao *"nenhuma
linha alcancada"*: o arquivo `cas.py` era exercido por `resolver_contido`
(P0-04) e pela classe `CAS` (P0-02), mas esta funcao — a que reduz TOCTOU
— nao tinha nenhuma linha executada por teste algum.

O CASO QUE OCORRE. `ler_arquivo_contido` e a leitura defendida: valida a
contencao, ABRE, e so entao confere se o alvo continua sendo o mesmo. O
ataque que ela existe para barrar e a troca do alvo ENTRE a validacao e a
leitura — o arquivo validado vira link para outro lugar no intervalo. Sao
tres recusas: fuga de contencao (herdada de `resolver_contido`), alvo
trocado por (dev, ino), e caminho real que muda depois da abertura.

COMO CADA UMA E EXERCIDA, e isto e o que separa medicao de encenacao:
- a fuga usa caminho REAL fora das raizes;
- a mudanca do caminho real usa a costura que a propria funcao oferece,
  o parametro `resolvedor` — um resolvedor que muda de resposta entre a
  validacao e a reconferencia e exatamente o que um symlink trocado
  produz, e nao um duplo do guarda;
- a troca por (dev, ino) e ENCENADA substituindo `os.stat` no modulo.
  Nao ha como provocar colisao real de inode de forma portavel. Isto e
  encenacao DECLARADA, e vale menos que as duas de cima.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao provam que a janela TOCTOU seja pequena o bastante: provam que a
  reconferencia acontece e recusa, nao que ela seja tempestiva;
- nao ha corrida real entre processos — nenhum teste aqui dispara duas
  threads disputando o alvo;
- nao cobrem descritor que morre entre `os.open` e `os.fstat`.
"""

import os
import shutil
import unittest
import uuid
from unittest import mock

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0 import cas as modulo_cas
from ssc_p0.cas import FugaDeCaminho, ler_arquivo_contido


class LeituraContidaRecusa(unittest.TestCase):

    def setUp(self):
        # Temporario na pasta IGNORADA do laboratorio, nunca no temp do
        # SO: e a regra que `apoio.py` declara e que
        # `test_seguranca.py:119` mede.
        self.raiz = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        self.dentro = os.path.join(self.raiz, "dentro")
        self.fora = os.path.join(self.raiz, "fora")
        os.makedirs(self.dentro)
        os.makedirs(self.fora)
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        self.alvo = os.path.join(self.dentro, "dado.txt")
        with open(self.alvo, "wb") as f:
            f.write(b"conteudo legitimo")
        self.intruso = os.path.join(self.fora, "segredo.txt")
        with open(self.intruso, "wb") as f:
            f.write(b"conteudo de fora")

    def test_arquivo_fora_das_raizes_e_recusado(self):
        with self.assertRaises(FugaDeCaminho) as ctx:
            ler_arquivo_contido(self.intruso, [self.dentro])
        self.assertIn("fora das raizes", str(ctx.exception))

    def test_fuga_por_pontos_e_recusada(self):
        caminho = os.path.join(self.dentro, "..", "fora", "segredo.txt")
        with self.assertRaises(FugaDeCaminho):
            ler_arquivo_contido(caminho, [self.dentro])

    def test_caminho_real_que_muda_apos_a_abertura_e_recusado(self):
        # A costura da propria funcao: um resolvedor que responde uma
        # coisa na validacao e outra na reconferencia e o que um
        # symlink trocado no intervalo produz.
        respostas = []

        def resolvedor_que_muda(caminho):
            real = os.path.realpath(caminho)
            respostas.append(real)
            if len(respostas) <= 2:      # validacao + raiz
                return real
            return os.path.join(self.fora, "outro-alvo.txt")

        with self.assertRaises(FugaDeCaminho) as ctx:
            ler_arquivo_contido(self.alvo, [self.dentro],
                                resolvedor=resolvedor_que_muda)
        self.assertIn("TOCTOU", str(ctx.exception))
        self.assertIn("caminho real mudou", str(ctx.exception))

    def test_alvo_trocado_por_dev_ino_e_recusado(self):
        # ENCENADO, e declarado como tal: nao ha modo portavel de
        # provocar colisao real de (dev, ino). O que se mede e que a
        # comparacao existe e que a divergencia recusa.
        real = os.stat

        class _OutroInode:
            st_dev = 999999
            st_ino = 999999

        with mock.patch.object(modulo_cas.os, "stat",
                               lambda *a, **k: _OutroInode()):
            with self.assertRaises(FugaDeCaminho) as ctx:
                ler_arquivo_contido(self.alvo, [self.dentro])
        self.assertIn("alvo trocado", str(ctx.exception))
        self.assertIs(os.stat, real, "o patch vazou do bloco")

    def test_o_descritor_nao_fica_aberto_apos_a_recusa(self):
        # Recusar vazando descritor transformaria o guarda em fuga de
        # recurso. No Windows, arquivo com descritor aberto nao pode ser
        # removido — e a remocao abaixo e a medicao.
        with mock.patch.object(modulo_cas.os, "stat",
                               lambda *a, **k: type("S", (), {
                                   "st_dev": 1, "st_ino": 2})()):
            with self.assertRaises(FugaDeCaminho):
                ler_arquivo_contido(self.alvo, [self.dentro])
        os.remove(self.alvo)      # levanta PermissionError se vazou
        self.assertFalse(os.path.exists(self.alvo))

    def test_leitura_legitima_devolve_os_bytes(self):
        # Contraprova: sem ela, uma funcao que recusasse sempre passaria
        # em todos os testes acima.
        self.assertEqual(ler_arquivo_contido(self.alvo, [self.dentro]),
                         b"conteudo legitimo")

    def test_leitura_legitima_por_caminho_nao_normalizado(self):
        # O caminho que a operacao entrega nem sempre vem normalizado; o
        # guarda nao pode recusar por isso.
        caminho = os.path.join(self.dentro, ".", "dado.txt")
        self.assertEqual(ler_arquivo_contido(caminho, [self.dentro]),
                         b"conteudo legitimo")


if __name__ == "__main__":
    unittest.main()
