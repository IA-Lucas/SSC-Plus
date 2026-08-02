"""P0-21 `kernel.SessionKernel` — fatia dos ramos que faltavam. FASE 3.

A varredura mediu **16 de 53 ramos alcancados** — 37 fora. Este e o
ponto de maior volume dos dezesseis, e a P1-A.3.5 o pulou por isso.

O QUE ESTE COMMIT FECHA, e o que NAO fecha, dito antes de qualquer
outra coisa. Ele alcanca **quatro familias** de recusa do kernel, com
os ramos exercidos pelo fluxo real:

  A. IDENTIDADE E PROVENIENCIA de WorkUnit — nasce em `proposta`, e da
     sessao, e da linhagem, id nao duplicado, `depende_de` conhecido,
     `parent_work_unit` conhecido;
  B. INTEGRIDADE DO PACOTE DE CONTEXTO — ausente no CAS, sem
     work_unit_id, ligado a OUTRA work_unit, com bytes de entrada
     ausentes. E o guarda que impede o kernel de aceitar contexto vazio
     ou trocado, e a rubrica 0.2.1-7 o chama de falha fechada;
  C. VALIDACAO DE ID contra uso em caminho (`_validar_id`) e deteccao de
     SEGREDO (IC-4);
  D. MEMORIA da sessao sem fonte/validade.

**NAO fecha as demais familias**, e elas ficam REGISTRADAS, nao
abandonadas: anti-competicao IW-3 e teto IW-2 de 12 filhos, ciclo via
parent/depende_de, vinculos divergentes de attempt e decisao, decisao
mutada, resultado de attempt fora do enum, as onze recusas de
`registrar_veredito`, checkpoint invalido/selo divergente, retomada sem
checkpoint, e a verificacao de cadeia na retomada. Sao materia de uma
missao de cobertura da P0 com o metodo da P1-A.3.5 — alcance medido sob
`sys.monitoring`, um teste por ramo, contraprova por ponto —, e nesta
missao nao cabem. Declarar isso e o oposto de escrever "P0-21 fechado".

O QUE ESTES TESTES NAO COBREM, alem do acima:
- nada e afirmado sobre desempenho ou sobre volume de eventos;
- o detector de segredo e por PADRAO, e padrao nao e exaustivo;
- o limiar de similaridade da anti-competicao nao e exercido aqui.
"""

import json
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import canonico
from ssc_p0.kernel import SegredoDetectado

PERFIL = {"modalidade": "texto", "ferramentas": [], "formato_saida": "livre",
          "contexto_max_tokens": 8000, "dominio": "geral",
          "privacidade": "remoto-permitido", "latencia_max_ms": None,
          "orcamento_max_custo": None}


class RecusasDoKernel(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel

    def _wu_valida(self, **sobre) -> ct.WorkUnit:
        """WorkUnit bem formada, com pacote de contexto REAL no CAS."""
        wu_id = sobre.pop("work_unit_id", None) or ct.__name__ + "-wu"
        wu_id = sobre.pop("_id", None) or f"wu-{len(self.kernel.work_units)}"
        pacote = {"work_unit_id": wu_id, "entradas": []}
        ref = self.kernel.cas.gravar(canonico(pacote))
        campos = {
            "work_unit_id": wu_id,
            "sessao_id": self.kernel.envelope.sessao_id,
            "linhagem_id": self.kernel.envelope.linhagem_id,
            "parent_work_unit": None, "tipo": "ato", "tipo_decisao": "tipo-2",
            "intencao": "intencao qualquer", "criterios_aceite_ref": ref,
            "nivel_capacidade": "L2", "perfil_capacidade": dict(PERFIL),
            "classe_governanca": "C1", "contexto_ref": ref, "depende_de": [],
            "estado": "proposta", "resultado_ref": None, "custo_medido": None}
        campos.update(sobre)
        return ct.WorkUnit(**campos)

    # --- A. identidade e proveniencia ----------------------------------

    def test_workunit_que_nao_nasce_em_proposta_e_recusada(self):
        for estado in ("aprovada", "em-execucao", "concluida"):
            with self.subTest(estado=estado):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.registrar_work_unit(
                        self._wu_valida(estado=estado), None)
                self.assertIn("nasce em 'proposta'", str(ctx.exception))

    def test_workunit_de_outra_sessao_ou_linhagem_e_recusada(self):
        casos = {"sessao_id": "outra-sessao", "linhagem_id": "outra-linhagem"}
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.registrar_work_unit(
                        self._wu_valida(**{campo: valor}), None)
                self.assertIn("outra", str(ctx.exception))

    def test_work_unit_id_duplicado_e_recusado(self):
        wu = self._wu_valida(_id="wu-dup")
        self.kernel.registrar_work_unit(wu, None)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_work_unit(self._wu_valida(_id="wu-dup"),
                                            None)
        self.assertIn("duplicado", str(ctx.exception))

    def test_depende_de_desconhecido_e_recusado(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_work_unit(
                self._wu_valida(depende_de=["nao-existe"]), None)
        self.assertIn("depende_de desconhecido", str(ctx.exception))

    def test_parent_desconhecido_e_recusado(self):
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.registrar_work_unit(
                self._wu_valida(parent_work_unit="nao-existe"), None)
        self.assertIn("parent_work_unit desconhecido", str(ctx.exception))

    # --- B. integridade do pacote de contexto --------------------------

    def test_pacote_ausente_no_cas_e_recusado(self):
        # 0.2.1-7: falha fechada, NUNCA pacote vazio ou substituto.
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.ler_pacote("0" * 64, "wu-x")
        self.assertIn("ContextPackage ausente no CAS", str(ctx.exception))

    def test_pacote_sem_work_unit_id_e_recusado(self):
        ref = self.kernel.cas.gravar(canonico({"entradas": []}))
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.ler_pacote(ref, None)
        self.assertIn("sem work_unit_id", str(ctx.exception))

    def test_pacote_ligado_a_outra_workunit_e_recusado(self):
        # O pacote TROCADO: existe, e integro, e e de outra WorkUnit.
        ref = self.kernel.cas.gravar(
            canonico({"work_unit_id": "wu-a", "entradas": []}))
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.ler_pacote(ref, "wu-b")
        self.assertIn("ligado a outro work_unit_id", str(ctx.exception))

    def test_pacote_com_bytes_de_entrada_ausentes_e_recusado(self):
        ref = self.kernel.cas.gravar(canonico({
            "work_unit_id": "wu-a",
            "entradas": [{"origem": "contrato", "bytes_ref": "a" * 64}]}))
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.ler_pacote(ref, "wu-a")
        self.assertIn("bytes de entrada de contexto ausentes",
                      str(ctx.exception))

    def test_workunit_com_pacote_trocado_nao_e_registrada(self):
        # O ponto de chamada: `registrar_work_unit` le o pacote e a
        # recusa acontece antes de qualquer evento.
        alheio = self.kernel.cas.gravar(
            canonico({"work_unit_id": "wu-de-outra", "entradas": []}))
        antes = self.kernel.log.seq_atual()
        with self.assertRaises(ct.FalhaContrato):
            self.kernel.registrar_work_unit(
                self._wu_valida(contexto_ref=alheio), None)
        self.assertEqual(self.kernel.log.seq_atual(), antes)

    # --- C. id de caminho e segredo ------------------------------------

    def test_id_invalido_para_caminho_e_recusado(self):
        from ssc_p0.kernel import _validar_id
        for ruim in ("../fuga", "a/b", "a\\b", "", ".", "..", "a:b", "a*b"):
            with self.subTest(id=repr(ruim)):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    _validar_id(ruim, "rotulo")
                self.assertIn("id invalido para uso em caminho",
                              str(ctx.exception))

    def test_segredo_detectado_e_recusado(self):
        from ssc_p0.kernel import escanear_segredos
        for texto in (b"sk-" + b"a" * 32, b"AKIA" + b"B" * 16,
                      b"-----BEGIN PRIVATE KEY-----",
                      b'api_key: "abcdefgh12345678"'):
            with self.subTest(amostra=texto[:12]):
                with self.assertRaises(SegredoDetectado) as ctx:
                    escanear_segredos(texto, "rotulo")
                self.assertIn("IC-4", str(ctx.exception))
        # Contraprova: conteudo comum nao pode virar segredo.
        escanear_segredos(b"texto qualquer sem credencial", "rotulo")

    # --- D. memoria -----------------------------------------------------

    def test_memoria_sem_fonte_ou_validade_e_recusada(self):
        for entrada in ({}, {"fonte": "x"}, {"validade": "y"},
                        {"texto": "sem nada"}):
            with self.subTest(entrada=entrada):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.registrar_memoria(entrada, None)
                self.assertIn("exige fonte e validade", str(ctx.exception))

    # --- contraprovas ---------------------------------------------------

    def test_workunit_bem_formada_e_registrada(self):
        # Contraprova geral: sem ela, um kernel que recusasse sempre
        # passaria em todos os testes acima.
        wu = self._wu_valida(_id="wu-ok")
        evento = self.kernel.registrar_work_unit(wu, None)
        self.assertEqual(evento.tipo, "work-unit")
        self.assertIn("wu-ok", self.kernel.work_units)

    def test_pacote_integro_e_lido(self):
        ref = self.kernel.cas.gravar(
            canonico({"work_unit_id": "wu-a", "entradas": []}))
        self.assertEqual(self.kernel.ler_pacote(ref, "wu-a")["work_unit_id"],
                         "wu-a")

    def test_memoria_com_fonte_e_validade_e_registrada(self):
        evento = self.kernel.registrar_memoria(
            {"fonte": "decisao-x", "validade": "2026-12-31", "texto": "nota"},
            None)
        self.assertEqual(evento.tipo, "memoria")

    def test_id_legitimo_atravessa(self):
        from ssc_p0.kernel import _validar_id
        for bom in ("0" * 32, "a1b2c3d4" * 4, "deadbeef" * 4):
            with self.subTest(id=bom):
                _validar_id(bom, "rotulo")


if __name__ == "__main__":
    unittest.main()
