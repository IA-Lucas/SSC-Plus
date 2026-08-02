"""Zero de franquia e VALOR, nao prefixo de texto — SSC+ P1-A.3.7, MAJOR #2.

O DEFEITO que o revisor independente mediu para NAO FECHAR o MAJOR #2:
*"`adaptadores._ZERO` aceita somente um zero inicial; `.0 tokens
available` e `00 tokens available` escapam e ainda casam `available` —
fail-open mantido"*.

`_ZERO` era um padrao TEXTUAL: exigia o digito `0` na primeira posicao
do numeral. Reconhecia as grafias que alguem tinha enumerado e nada
mais. A correcao troca o eixo: os padroes agora CAPTURAM o numeral e
`_valor_zero` o PARSEIA — `0`, `00`, `.0`, `0.0`, `0.00`, `0,0`,
`000,000` e qualquer grafia futura de zero sao o mesmo caso, sem lista.

O CAMINHO QUE A OPERACAO PERCORRE. Em operacao a franquia e classificada
dentro de `_resultado`, sobre o texto que o CLI devolveu na sonda de
login, e o resultado governa `QuotaEsgotada` no pipeline. Estes testes
atacam os dois niveis: `_quota_de` importado da producao (a funcao que
`_resultado` chama) e `executar_preflight` fim a fim, com a grafia
entrando pela saida do sensor — que e por onde a saida do CLI entra.

O vizinho recusado: afirmar sobre `_NUMERO` ou `_valor_zero` isolados.
Eles aparecem aqui apenas em `test_o_zero_e_decidido_por_valor`, para
fixar o eixo da correcao; TODO o resto exerce a classificacao inteira.

O QUE ESTES TESTES NAO COBREM, declarado:
- as grafias continuam AUTORAIS. O achado B (`P1A-58`, INDETERMINADO)
  segue aberto e esta correcao NAO o fecha: nenhuma saida real de CLI
  com franquia esgotada foi observada, e a P1-A.3.5 ja registrou que 9
  das 11 formas eram invencao da sessao. O que mudou e que a decisao
  deixou de depender da grafia — nao que as grafias tenham sido medidas;
- nao cobrem franquia expressa sem numeral nem negacao reconhecida
  (ex.: "your balance is empty"), que continua caindo em "desconhecida";
- nao cobrem numeral em outro sistema de escrita, nem separador de
  milhar interpretado como decimal ("1,000" e lido como 1.0 — o
  resultado, franquia disponivel, e o mesmo, mas pelo valor errado);
- nao invocam CLI algum: o texto entra por sensor falso.
"""

import os
import sys
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)
from preflight import espec_de
from preflight.adaptadores import _NUMERO, _quota_de, _valor_zero
from preflight.pipeline import executar_preflight

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# As duas grafias que o revisor nomeou, mais as quatro que o remedio
# especificado exige (`.0`, `00`, `0.00`, `0,0`).
ESGOTADAS_QUE_ESCAPAVAM = (
    ".0 tokens available",        # zero sem digito inicial — nomeado
    "00 tokens available",        # zero com digito repetido — nomeado
    "0.00 requests remaining",
    "0,0 calls left",
    "000 requests remaining",
    "00.00 tokens available",
    ".00 quota available",
    "0,00 tokens available",
    "available: .0",
    "quota: 00",
    "00/100 requests remaining",
    "0 of 100 requests remaining",
)

# Franquia REAL disponivel: a correcao nao pode trocar fail-open por
# fail-closed indevido. Sem estas, um classificador que dissesse
# "esgotada" sempre passaria em tudo acima.
DISPONIVEIS = (
    "10.0 tokens available",
    "0.5 calls left",
    "100 requests remaining",
    "1000 tokens available",
    "95% quota available",
    "50/100 requests remaining",
    "0.001 tokens available",
    "10 of 100 requests remaining",
)


class ZeroDecididoPeloValor(unittest.TestCase):

    def test_grafias_que_escapavam_sao_esgotada(self):
        for texto in ESGOTADAS_QUE_ESCAPAVAM:
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, True), "esgotada")

    def test_franquia_real_nao_vira_esgotada(self):
        for texto in DISPONIVEIS:
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, True), "disponivel")

    def test_o_zero_e_decidido_por_valor(self):
        # O eixo da correcao, fixado: o mesmo valor em grafias
        # diferentes precisa dar a mesma decisao.
        for grafia in ("0", "00", ".0", "0.0", "0,0", "0.00", "000,000"):
            with self.subTest(grafia=grafia):
                self.assertTrue(_valor_zero(grafia))
        for grafia in ("0.5", "10.0", "100", "0.001"):
            with self.subTest(grafia=grafia):
                self.assertFalse(_valor_zero(grafia))

    def test_numeral_e_delimitado_sem_partir_numero_maior(self):
        import re
        rx = re.compile(_NUMERO)
        self.assertEqual([m.group(1) for m in rx.finditer("10.0 e 0.5")],
                         ["10.0", "0.5"])
        self.assertEqual([m.group(1) for m in rx.finditer("v2 tem .0")],
                         [".0"])

    def test_zero_em_qualquer_ocorrencia_vence(self):
        # Decidir pela PRIMEIRA ocorrencia classificaria como disponivel
        # uma franquia que ja acabou.
        self.assertEqual(
            _quota_de("10 tokens available; 0 requests left", True),
            "esgotada")
        self.assertEqual(
            _quota_de("0 requests left; 10 tokens available", True),
            "esgotada")

    def test_sem_login_nenhuma_grafia_vira_disponivel(self):
        for texto in DISPONIVEIS:
            with self.subTest(texto=texto):
                self.assertEqual(_quota_de(texto, False), "desconhecida")


class PipelineBloqueiaAsGrafiasNovas(unittest.TestCase):
    """Fim a fim: a grafia entra pela saida do sensor, como o CLI a dá."""

    def _preflight(self, linha_de_quota):
        sensores, _, _ = apoio.sensores_dict(
            "codex",
            login="Logged in using ChatGPT (plan: ChatGPT Pro 5x)\n"
                  + linha_de_quota)
        return executar_preflight(espec_de("codex"), sensores, env={})

    def test_ponto_zero_bloqueia_no_pipeline(self):
        rel = self._preflight(".0 tokens available")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA",
                      [e.codigo for e in rel.erros])
        self.assertEqual(rel.quota, "esgotada")

    def test_zero_zero_bloqueia_no_pipeline(self):
        rel = self._preflight("00 tokens available")
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-QUOTA-ESGOTADA",
                      [e.codigo for e in rel.erros])

    def test_franquia_real_atravessa_o_pipeline(self):
        # Contraprova fim a fim: sem ela, a correcao poderia bloquear a
        # frota inteira e todos os testes acima continuariam verdes.
        rel = self._preflight("100 requests remaining")
        self.assertEqual(rel.resultado, "ELIGIBLE")
        self.assertEqual(rel.quota, "disponivel")
        self.assertEqual(rel.erros, [])


if __name__ == "__main__":
    unittest.main()
