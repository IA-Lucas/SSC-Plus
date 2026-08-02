"""P0-21 FASE 3 [5/6] — as duas recusas de `montar_contexto`.

  L718 IC-2/IC-3: conteudo externo nao entra como instrucao executavel
  L725 verbatim acima do teto: RECUSA, nunca resumo

Sao as duas recusas que decidem o que entra no contexto de uma chamada
— e, portanto, o que o modelo le. Sao guardas de CONTENCAO, nao de
formato.

**L718 e a fronteira entre citar e obedecer.** Um arquivo lido do disco
com `papel="contrato"` e `inclusao` diferente de `referencia` entraria
no pacote como texto que o executor pode tratar como instrucao. E a
injecao por documento: quem escreve o arquivo passa a escrever a ordem.
A regra da P0 e que conteudo externo entra como EVIDENCIA ou
NORMA-CITADA, nunca como instrucao executavel.

**L725 e a recusa que se recusa a resumir.** Acima do teto o kernel
NAO resume, nao trunca e nao escolhe: para. Truncar silenciosamente
seria pior que falhar — o pacote continuaria parecendo completo, e a
proveniencia registraria um hash de algo que ninguem decidiu cortar.

O CASO QUE OCORRE. As duas recusas sao exercidas **lendo arquivo de
verdade do disco**, dentro das raizes declaradas (IC-5), pelo mesmo
caminho que o `ExecutionGateway` usa para montar o pacote de uma
WorkUnit. Nenhuma delas e alcancada passando `conteudo` inline — esse
seria o vizinho, porque o ramo de L718 so existe no caminho de arquivo.

O QUE ESTES TESTES NAO COBREM, declarado:
- o teto `verbatim_ate` e um DADO de politica; nada aqui afirma que o
  valor padrao seja o valor certo. O que se mede e que ele e respeitado
  e que a decisao acima dele e recusar;
- a lista de papeis que caracterizam instrucao executavel e enumerada
  (`("contrato",)`): um papel novo com a mesma semantica passaria, e
  isso e limite do guarda, nao do teste;
- IC-5 (fuga de caminho) e IC-4 (segredo) sao outros guardas, ja
  cobertos em `test_seguranca.py` e `test_p0_kernel_p1a37.py`;
- nada aqui prova que o executor de fato trate `evidencia` de forma
  diferente de `contrato` — a P0 nao invoca modelo.
"""

import os
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import novo_id
from ssc_p0.kernel import VERBATIM_ATE_DEFAULT


class RecusasDaMontagemDeContexto(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel
        self.wid = novo_id()
        # Arquivo REAL, dentro das raizes de fontes declaradas do lab.
        self.fonte = os.path.join(self.kernel.raizes_fontes[-1], "to1",
                                  "entrada.txt")
        self.assertTrue(os.path.isfile(self.fonte),
                        "fixture de entrada ausente: o teste mediria nada")

    # --- L718: citar nao e obedecer ------------------------------------

    def test_arquivo_externo_como_contrato_executavel_e_recusado(self):
        for inclusao in ("verbatim", "resumo"):
            with self.subTest(inclusao=inclusao):
                with self.assertRaises(ct.FalhaContrato) as ctx:
                    self.kernel.montar_contexto(
                        self.wid,
                        [{"origem": self.fonte, "papel": "contrato",
                          "inclusao": inclusao}])
                self.assertIn("IC-2/IC-3", str(ctx.exception))
                self.assertIn("instrucao executavel", str(ctx.exception))

    def test_o_mesmo_arquivo_como_evidencia_atravessa(self):
        # A outra metade da regra, e a contraprova de L718: o arquivo nao
        # e proibido — o PAPEL e que decide. Sem ela, um guarda que
        # recusasse toda leitura de disco passaria no teste acima.
        pacote = self.kernel.montar_contexto(
            self.wid, [{"origem": self.fonte, "papel": "evidencia",
                             "inclusao": "verbatim"}])
        self.assertEqual(len(pacote.entradas), 1)
        self.assertEqual(pacote.entradas[0]["papel"], "evidencia")
        self.assertTrue(pacote.entradas[0]["bytes_ref"])

    def test_contrato_por_referencia_atravessa(self):
        # A excecao declarada na propria regra: `contrato` e permitido
        # quando entra por REFERENCIA — citado, nunca executavel.
        pacote = self.kernel.montar_contexto(
            self.wid, [{"origem": self.fonte, "papel": "contrato",
                             "inclusao": "referencia"}])
        self.assertEqual(pacote.entradas[0]["inclusao"], "referencia")

    def test_nada_vai_para_o_CAS_quando_a_montagem_e_recusada(self):
        # A recusa corre ANTES de a entrada ser gravada. Um pacote
        # recusado que ja tivesse deixado bytes no CAS seria proveniencia
        # de algo que nunca entrou em contexto nenhum.
        antes = self._objetos_no_cas()
        with self.assertRaises(ct.FalhaContrato):
            self.kernel.montar_contexto(
                self.wid, [{"origem": self.fonte, "papel": "contrato",
                                 "inclusao": "verbatim"}])
        self.assertEqual(self._objetos_no_cas(), antes)

    def _objetos_no_cas(self) -> int:
        raiz = os.path.join(self.kernel.raiz, "cas")
        if not os.path.isdir(raiz):
            return 0
        return sum(len(arqs) for _, _, arqs in os.walk(raiz))

    # --- L725: acima do teto, recusa — nunca resumo --------------------

    def test_verbatim_acima_do_teto_e_recusado_e_nao_resumido(self):
        grande = b"L" * (VERBATIM_ATE_DEFAULT + 1)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.montar_contexto(
                self.wid, [{"origem": "inline:grande",
                                 "papel": "evidencia", "inclusao": "verbatim",
                                 "conteudo": grande}])
        self.assertIn("recusa", str(ctx.exception))
        self.assertIn("nunca resume", str(ctx.exception))

    def test_o_teto_e_configuravel_e_a_recusa_o_respeita(self):
        # Mede que o guarda le a POLITICA, e nao uma constante embutida:
        # com um teto menor, o mesmo conteudo que passava e recusado.
        conteudo = b"L" * 64
        pacote = self.kernel.montar_contexto(
            self.wid, [{"origem": "inline:medio", "papel": "evidencia",
                             "inclusao": "verbatim", "conteudo": conteudo}])
        self.assertEqual(len(pacote.entradas), 1)
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.kernel.montar_contexto(
                self.wid, [{"origem": "inline:medio",
                                 "papel": "evidencia", "inclusao": "verbatim",
                                 "conteudo": conteudo}],
                politica_inclusao={"verbatim_ate": 32})
        self.assertIn("32 bytes", str(ctx.exception))

    def test_no_limite_exato_o_conteudo_atravessa(self):
        # A fronteira e fechada do lado certo: `> teto` recusa, `== teto`
        # passa. Sem esta medicao, um erro de um byte ficaria invisivel.
        no_limite = b"L" * VERBATIM_ATE_DEFAULT
        pacote = self.kernel.montar_contexto(
            self.wid, [{"origem": "inline:limite", "papel": "evidencia",
                             "inclusao": "verbatim", "conteudo": no_limite}])
        self.assertEqual(len(pacote.entradas), 1)

    def test_acima_do_teto_por_REFERENCIA_atravessa(self):
        # Contraprova de L725: o teto e do VERBATIM. A mesma massa de
        # bytes entra por referencia sem recusa — o guarda nao e um
        # limite de tamanho geral.
        grande = b"L" * (VERBATIM_ATE_DEFAULT + 1)
        pacote = self.kernel.montar_contexto(
            self.wid, [{"origem": "inline:grande", "papel": "evidencia",
                             "inclusao": "referencia", "conteudo": grande}])
        self.assertEqual(len(pacote.entradas), 1)


if __name__ == "__main__":
    unittest.main()
