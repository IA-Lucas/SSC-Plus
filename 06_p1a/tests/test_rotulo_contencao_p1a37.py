"""O rotulo nao pode exceder o mecanismo — SSC+ P1-A.3.7, achado N3.

O DEFEITO, na voz do revisor independente: *"o rotulo 'deteccao
integral' EXCEDE o mecanismo, que fotografa so a arvore do repositorio e
exclui `locks/`"*. O atestado classificou N3 como *(F) mesma familia — e
e a familia do MAJOR #3 no sentido literal*: a propriedade afirmada em
prosa, nao exercida pela interface.

Ja existia um guarda desta forma — `test_enforcement_nao_afirma_sandbox_
que_nao_existe` proibe o rotulo de afirmar sandbox inexistente. Ele
cobria a palavra *sandbox*; a palavra *integral* nunca foi coberta. O
atestado registrou isso como "classe medida no principio, nao no caso",
e este arquivo e o caso.

O CAMINHO QUE A OPERACAO PERCORRE. O rotulo nao e comentario: ele e
gravado na evidencia de toda corrida de revisao, no campo
`enforcement_read_only`, e e o que um revisor independente le para
julgar o isolamento. Estes testes verificam o VALOR que sai da funcao —
nao a prosa do fonte — e o comparam com os objetos que o mecanismo
realmente usa.

ACOPLAMENTO POR CONSTRUCAO, e nao por lembranca. O rotulo passou a ser
montado a partir de `ALVOS_VIGIADOS_FORA_DO_REPOSITORIO` e de
`NAO_VIGIADO`. Foi por a frase e o mecanismo serem objetos independentes
que um pode ter passado o outro por tres missoes; os testes de
acoplamento abaixo reprovam a divergencia em vez de espera-la.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao provam que o alcance DECLARADO seja suficiente — provam que o
  declarado e o medido coincidem. Suficiencia e julgamento de revisor;
- a lista de palavras de alcance total e enumerada, e enumeracao nunca e
  exaustiva: um rotulo poderia exagerar com palavra fora da lista;
- os geradores de pacote (`pacote_p1a33.py`, `pacote_p1a36.py`) NAO sao
  varridos, e ha razao: eles produzem artefatos cujo SHA-256 esta
  publicado (`87f41503…`, `5ab35a6c…`) e alterar seu texto quebraria a
  reprodutibilidade de um hash ja submetido a revisor. As tabelas de
  threat review deles ainda carregam a frase antiga, e isso fica
  REGISTRADO como limite, nao corrigido em silencio;
- nenhum CLI e invocado.
"""

import os
import sys
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

# Instrumentos VIVOS — os que uma corrida de revisao executa. Os
# geradores de pacote ficam de fora, e o porque esta no docstring.
INSTRUMENTOS_VIVOS = ("contencao.py", "revisao_p1a3.py", "revisao_p1a31.py",
                      "revisao_p1a33.py", "revisao_p1a36.py")


class RotuloNaoExcedeOMecanismo(unittest.TestCase):

    def setUp(self):
        self.rotulo = contencao.enforcement_kimi()
        self.baixo = self.rotulo.lower()

    def test_rotulo_nao_afirma_alcance_total(self):
        # O irmao do guarda que ja proibia "sandbox".
        for palavra in contencao.PALAVRAS_DE_ALCANCE_TOTAL:
            with self.subTest(palavra=palavra):
                self.assertNotIn(palavra, self.baixo)

    def test_rotulo_declara_o_que_NAO_detecta(self):
        # Declarar o alcance nao basta: o rotulo tem de dizer o que fica
        # de fora, senao o leitor completa a frase por conta propria.
        self.assertIn("nao detecta", self.baixo)
        self.assertIn(contencao.NAO_VIGIADO, self.rotulo)

    def test_rotulo_nomeia_cada_alvo_realmente_vigiado(self):
        # Acoplamento: alvo vigiado que o rotulo nao nomeia e cobertura
        # que ninguem sabe que existe; nome sem alvo e o defeito N3.
        for alvo in contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO:
            with self.subTest(alvo=alvo):
                self.assertIn(alvo, self.rotulo)

    def test_rotulo_acompanha_a_cobertura_quando_ela_muda(self):
        # A prova de que o acoplamento e por CONSTRUCAO: mexer na lista
        # muda o rotulo sem que ninguem reescreva a frase.
        from unittest import mock
        with mock.patch.object(contencao,
                               "ALVOS_VIGIADOS_FORA_DO_REPOSITORIO",
                               ("~/.fonte-nova/config.json",)):
            novo = contencao.enforcement_kimi()
        self.assertIn("~/.fonte-nova/config.json", novo)
        self.assertNotIn("~/.fonte-nova/config.json", self.rotulo)

    def test_rotulo_declara_a_atribuicao_e_nao_so_a_deteccao(self):
        self.assertIn("atribuicao", self.baixo)
        self.assertIn("escritor esperado", self.baixo)

    def test_rotulo_continua_afirmando_o_que_e_verdade(self):
        # Contraprova: um rotulo vazio passaria em tudo acima. O que o
        # mecanismo TEM continua dito — sem sandbox, e ha manifesto.
        self.assertIn("sem sandbox de filesystem", self.baixo)
        self.assertIn("manifesto", self.baixo)
        self.assertIn("--skills-dir", self.rotulo)


class NenhumInstrumentoVivoAfirmaAlcanceTotal(unittest.TestCase):
    """A prosa dos instrumentos tambem deixou de exceder o mecanismo."""

    # Frases que descrevem O MECANISMO DE DETECCAO com alcance total.
    # "diff integral" e "herda integralmente" nao entram: falam do
    # pacote e da heranca de correcoes, nao da deteccao.
    FRASES_PROIBIDAS = ("deteccao integral", "manifesto sha-256 da arvore "
                        "inteira", "arvore inteira antes")

    def test_nenhuma_frase_de_alcance_total_sobre_a_deteccao(self):
        base = os.path.join(_DIR_P1A, "evidencias")
        for nome in INSTRUMENTOS_VIVOS:
            with open(os.path.join(base, nome), encoding="utf-8") as f:
                fonte = f.read().lower()
            for frase in self.FRASES_PROIBIDAS:
                with self.subTest(instrumento=nome, frase=frase):
                    self.assertNotIn(frase, fonte)

    def test_a_evidencia_da_corrida_declara_as_raizes_e_o_nao_vigiado(self):
        # O campo `contencao` da evidencia e o que o revisor le. Ele
        # precisa carregar as duas coisas: onde se olhou e onde nao.
        import tempfile
        with tempfile.TemporaryDirectory() as raiz:
            vig = contencao.Vigilancia(raiz, "sessao-x",
                                       alvos=("~/.alvo-de-teste.json",))
            vig.abrir()
            medida = vig.fechar()
        self.assertEqual(medida["nao_vigiado"], contencao.NAO_VIGIADO)
        self.assertIn("fora: ~/.alvo-de-teste.json",
                      medida["raizes_vigiadas"])
        for palavra in contencao.PALAVRAS_DE_ALCANCE_TOTAL:
            with self.subTest(palavra=palavra):
                self.assertNotIn(palavra, str(medida).lower())


if __name__ == "__main__":
    unittest.main()
