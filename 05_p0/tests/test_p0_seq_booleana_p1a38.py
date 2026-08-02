"""FASE 1.1 — `bool` por `int` na seq, PROVADO NO CAMINHO DA OPERACAO.

O defeito foi achado e corrigido na P1-A.3.7 (`contratos._tipo`,
commit `684682c`). O que faltava e o que este arquivo entrega: a prova
no caminho que a operacao percorre.

POR QUE A PROVA ANTERIOR ERA VIZINHA. `test_p0_tipo_p1a37.py` exerce
`_tipo(...)` e `evento.validate()` — a PRIMITIVA e o metodo que a
chama. Medido nesta missao revertendo o guarda: **6 testes vermelhos,
todos em `test_p0_tipo_p1a37.py`, nenhum passando pelo `EventLog`**.
E a licao do achado N4 na letra: *primitiva corrigida nao cobre ponto
de chamada*. A afirmacao do registro da P1-A.3.7 e sobre o EventLog —
*"a seq do EventLog aceitava `True`"* —, e o EventLog nao era exercido.

O CASO QUE OCORRE, medido com o guarda revertido e nao suposto:

    linha crua: {"causado_por":null,...,"seq":true,...}
    EventLog.verificar  ACEITOU 1 registro; seq lido = True
    EventLog(caminho)   seq_atual = True   proxima_seq = 2
    EventLog.anexar     devolveu True; seq_atual = True

Um log com `"seq": true` na posicao 1 atravessa inteiro: `from_dict`
aceita, `validate()` aceitava, `evento.seq != i` e FALSO porque
`True == 1`, e a cadeia segue com a ponta em `True`. A seq e a
AUTORIDADE DE ORDEM da P0 — o relogio nao e —, e a partir dai dois
eventos ocupam a mesma posicao: a ordem deixa de ser total.

A PORTA E REAL. Nao e preciso encenar nada: o EventLog e relido do
disco a cada construcao (`__init__` chama `verificar`), e essa releitura
E a recuperacao apos queda. Um log editado, truncado e reescrito, ou
gerado por um produtor que serialize booleano onde o contrato pede
inteiro, entra por essa porta.

O DISCRIMINADOR. `test_a_recusa_nao_vem_da_canonicidade` mede que a
linha injetada E a serializacao canonica do proprio evento — ou seja,
o guarda de linha nao canonica (`EventoAdulterado`) NAO a pegaria. Sem
essa medicao, os testes abaixo poderiam passar pelo motivo errado e
ninguem saberia.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem a seq do CHECKPOINT: `Checkpoint.validate` nao chama
  `_tipo` sobre `estado_refs["seq"]` e `Juiz1.validar_checkpoint` usa
  `isinstance(..., int)`, que aceita `True`. Medido nesta missao:
  **nao e alcancavel em operacao** — a seq do checkpoint vem de
  `log.seq_atual()`, ja tipada aqui, e o checkpoint de disco e barrado
  pelo selo HMAC antes de qualquer uso. Fica registrado como defesa em
  profundidade ausente, nao como defeito vivo;
- nao cobrem `float` onde o contrato pede `int` (`seq=1.0`): o
  `_tipo` o recusa, e isso ja e coberto em `test_p0_tipo_p1a37.py`;
- nao provam que TODO campo inteiro do acervo esteja tipado — o que se
  mede aqui e a seq, que e a autoridade de ordem;
- nada aqui prova durabilidade nem concorrencia do log.
"""

import json
import os
import shutil
import unittest
import uuid

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import canonico, sha256_bytes
from ssc_p0.eventlog import EventLog, EventoTruncado, hash_evento

GENESE = "0" * 64


def _evento(seq, chave="k1", prev=GENESE) -> ct.Evento:
    """Evento com seq ARBITRARIA — inclusive booleana, de proposito."""
    return ct.Evento(
        evento_id=f"ev-{chave}", seq=seq, ts="2026-08-01T00:00:00Z",
        schema_version=ct.SCHEMA_VERSION, linhagem_id="lin-1",
        tipo="sessao", causado_por=None, idempotency_key=chave,
        prev_event_hash=prev, payload_ref="sha256:" + "a" * 64)


class SeqBooleanaNoCaminhoDaOperacao(unittest.TestCase):

    def setUp(self):
        self.raiz = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        os.makedirs(self.raiz)
        self.addCleanup(shutil.rmtree, self.raiz, ignore_errors=True)
        self.caminho = os.path.join(self.raiz, "log.jsonl")

    def _gravar_linha_com_seq_booleana(self) -> bytes:
        """Escreve no disco a linha CANONICA de um evento com seq=True."""
        linha = canonico(_evento(True).to_dict()) + b"\n"
        with open(self.caminho, "wb") as f:
            f.write(linha)
        return linha

    # --- a releitura do disco: o caminho da recuperacao -----------------

    def test_verificar_recusa_log_com_seq_booleana(self):
        self._gravar_linha_com_seq_booleana()
        with self.assertRaises(EventoTruncado) as ctx:
            EventLog.verificar(self.caminho, GENESE)
        self.assertIn("fora de schema", str(ctx.exception))
        self.assertIn("evento.seq", str(ctx.exception))

    def test_construir_o_eventlog_sobre_esse_log_recusa(self):
        # `EventLog.__init__` relê o arquivo existente: e por aqui que a
        # sessao volta apos uma queda. Se a construcao aceitasse, a
        # ponta da cadeia passaria a ser `True` sem ninguem ver.
        self._gravar_linha_com_seq_booleana()
        with self.assertRaises(EventoTruncado):
            EventLog(self.caminho, GENESE)

    def test_a_recusa_nao_vem_da_canonicidade(self):
        # DISCRIMINADOR. A linha injetada E a serializacao canonica do
        # evento que ela descreve: o guarda de "linha nao canonica"
        # calcula o mesmo hash e nao a recusaria. Logo, quem recusa e o
        # guarda de TIPO — e nao um vizinho dele.
        linha = self._gravar_linha_com_seq_booleana()
        self.assertIn(b'"seq":true', linha)
        dados = json.loads(linha.decode("utf-8"))
        self.assertIs(dados["seq"], True)
        evento_lido = ct.Evento(**dados)
        self.assertEqual(sha256_bytes(linha[:-1]), hash_evento(evento_lido))

    # --- a escrita em memoria: o caminho do kernel ----------------------

    def test_anexar_com_seq_booleana_nao_escreve_byte_algum(self):
        # O log e append-only: aceitar e depois desfazer nao existe.
        open(self.caminho, "wb").close()
        log = EventLog(self.caminho, GENESE)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            log.anexar(_evento(True))
        self.assertIn("evento.seq", str(ctx.exception))
        self.assertEqual(os.path.getsize(self.caminho), 0)
        self.assertEqual(log.seq_atual(), 0)

    def test_a_ponta_da_cadeia_continua_inteira_apos_a_recusa(self):
        # O dano que o defeito causava nao era a linha ruim: era a ponta
        # virar `True` e a proxima seq nascer de um booleano.
        open(self.caminho, "wb").close()
        log = EventLog(self.caminho, GENESE)
        self.assertTrue(log.anexar(_evento(1)))
        with self.assertRaises(ct.FalhaContrato):
            log.anexar(_evento(True, chave="k2",
                               prev=hash_evento(_evento(1))))
        self.assertIsInstance(log.seq_atual(), int)
        self.assertNotIsInstance(log.seq_atual(), bool)
        self.assertEqual(log.proxima_seq(), 2)

    # --- contraprova ----------------------------------------------------

    def test_log_com_seq_inteira_continua_atravessando(self):
        # Sem esta, um guarda que recusasse toda seq passaria em tudo
        # acima e o acervo inteiro pararia sem que os testes vissem.
        open(self.caminho, "wb").close()
        log = EventLog(self.caminho, GENESE)
        primeiro = _evento(1)
        self.assertTrue(log.anexar(primeiro))
        self.assertTrue(log.anexar(_evento(2, chave="k2",
                                           prev=hash_evento(primeiro))))
        registros = EventLog.verificar(self.caminho, GENESE)
        self.assertEqual([r["evento"].seq for r in registros], [1, 2])
        self.assertEqual(EventLog(self.caminho, GENESE).seq_atual(), 2)


if __name__ == "__main__":
    unittest.main()
