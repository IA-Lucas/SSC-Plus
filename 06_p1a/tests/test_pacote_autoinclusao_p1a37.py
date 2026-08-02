"""O gerador embute o proprio codigo-fonte — SSC+ P1-A.3.7, MAJOR #5.

O DEFEITO, levantado pelo revisor independente e aceito por inteiro pelo
registro da P1-A.3.6 (§3.4): o pacote mandava julgar a construcao do
gerador — *"O gerador DESTE pacote herda a mesma construcao — julgue-a
tambem"* — e **nao incluia o codigo do gerador**. Pedir julgamento sobre
artefato ausente.

O remedio especificado no §9.4 e um OU exclusivo: o gerador embute o
proprio fonte com o SHA-256 ao lado, OU o pacote para de pedir o
julgamento. Este arquivo prova a primeira metade.

O CAMINHO QUE A OPERACAO PERCORRE. Um gerador de pacote e exercido de um
jeito so: rodando `montar_pacote` contra commits REAIS deste
repositorio e olhando os bytes que saem. E o que se faz aqui — dois
commits reais, saida em descartavel, e as assercoes sobre o TEXTO
PRODUZIDO. Nao ha assercao sobre a forma do fonte do gerador.

O vizinho recusado: conferir que `secao_do_gerador` devolve um bloco com
um hash dentro. Isso e a primitiva; foi assim que o MAJOR #4 ficou
aberto uma missao inteira. O que se afirma aqui e que o PACOTE — o
artefato que vai ao revisor — carrega o gerador.

O QUE ESTES TESTES NAO COBREM, declarado:
- nenhum pacote e ENVIADO a revisor: a missao que os escreve nao reabre
  revisao. O que se prova e a propriedade do artefato, nao que algum
  revisor o tenha lido;
- `pacote_p1a33.py` e `pacote_p1a36.py` NAO sao corrigidos nem varridos
  por este arquivo: os hashes que eles produzem estao publicados
  (`87f41503…`, `5ab35a6c…`) e alterar seu texto quebraria a
  reprodutibilidade de um artefato ja submetido. O limite esta
  registrado em `test_pedido_de_julgamento_p1a37.py`, com a razao;
- a determinismo e medido entre duas corridas na MESMA estacao e no
  mesmo instante logico; nada se afirma sobre outra maquina;
- nada se afirma sobre o pacote CABER em algum revisor: isso e medicao
  de missao de revisao, e ela nao ocorre aqui.
"""

import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import autoinclusao  # noqa: E402

_GERADOR = os.path.join(_DIR_P1A, "evidencias", "pacote_p1a37.py")

# Dois commits REAIS deste repositorio. `30107bd` e o ultimo estado que
# um revisor de fato leu e julgou (§2.1 da 99_decisao-p1a36.md).
BASE = "30107bd"
ALVO = "7d25bc7"


def _carregar_gerador():
    spec = importlib.util.spec_from_file_location("pacote_p1a37_sob_teste",
                                                  _GERADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _tem_git() -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", ALVO],
                          cwd=_RAIZ, capture_output=True).returncode == 0


@unittest.skipUnless(_tem_git(), "repositorio git indisponivel")
class OPacoteCarregaOProprioGerador(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar_gerador()
        cls.texto = cls.modulo.montar_pacote(BASE, ALVO)

    def test_o_pacote_contem_o_fonte_do_gerador_e_o_seu_sha256(self):
        self.assertTrue(
            autoinclusao.contem_o_gerador(self.texto, _GERADOR),
            "o pacote nao carrega o fonte do gerador com o seu SHA-256 — "
            "e o MAJOR #5 intacto")

    def test_o_sha256_declarado_e_o_do_arquivo_do_repositorio(self):
        # O revisor confere com `sha256sum` sobre o arquivo que tem em
        # maos. Se o hash publicado no pacote nao for o do arquivo, a
        # secao vira decoracao.
        with open(_GERADOR, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        self.assertIn(digest, self.texto)

    def test_o_pacote_pede_o_julgamento_do_gerador(self):
        # A metade que da sentido a auto-inclusao: incluir sem pedir
        # tambem satisfaria o OU, mas nao e o que este gerador faz.
        self.assertTrue(
            autoinclusao.pede_julgamento_do_gerador(self.texto))

    def test_o_fonte_embutido_sai_redigido(self):
        usuario = os.path.basename(os.path.expanduser("~"))
        self.assertNotIn(usuario, self.texto)
        self.assertNotIn("E:\\LucasIA", self.texto)
        self.assertNotIn("E:/LucasIA", self.texto)


@unittest.skipUnless(_tem_git(), "repositorio git indisponivel")
class AncoragemHerdadaDoMajor5(unittest.TestCase):
    """A metade do MAJOR #5 que ja estava certa nao pode regredir."""

    def test_duas_montagens_produzem_os_mesmos_bytes(self):
        modulo = _carregar_gerador()
        um = modulo.montar_pacote(BASE, ALVO).encode("utf-8")
        dois = modulo.montar_pacote(BASE, ALVO).encode("utf-8")
        self.assertEqual(hashlib.sha256(um).hexdigest(),
                         hashlib.sha256(dois).hexdigest())

    def test_arvore_de_trabalho_mutada_nao_muda_o_pacote(self):
        # A prova que reprovou a P1-A.3.1: o gerador nao pode ler o
        # disco. Muta-se um arquivo que ESTA nas listas do pacote e o
        # hash tem de ficar parado. O gerador em si e a unica excecao
        # declarada — ele e lido do disco de proposito.
        modulo = _carregar_gerador()
        antes = modulo.montar_pacote(BASE, ALVO)
        alvo = os.path.join(_RAIZ, "06_p1a", "leitores_config.py")
        with open(alvo, "rb") as f:
            original = f.read()
        try:
            with open(alvo, "ab") as f:
                f.write(b"\n# MUTACAO DELIBERADA DO TESTE\n")
            depois = modulo.montar_pacote(BASE, ALVO)
        finally:
            with open(alvo, "wb") as f:
                f.write(original)
        self.assertEqual(antes, depois)
        with open(alvo, "rb") as f:
            self.assertEqual(f.read(), original,
                             "o teste nao restaurou o arquivo mutado")

    def test_base_que_nao_e_ancestral_para_a_montagem(self):
        modulo = _carregar_gerador()
        with self.assertRaises(SystemExit):
            modulo.montar_pacote(ALVO, BASE)   # invertidos de proposito

    def test_commit_inexistente_para_a_montagem(self):
        modulo = _carregar_gerador()
        with self.assertRaises(SystemExit):
            modulo.montar_pacote(BASE, "0" * 40)


@unittest.skipUnless(_tem_git(), "repositorio git indisponivel")
class MainGravaOArquivo(unittest.TestCase):

    def test_main_grava_e_o_arquivo_carrega_o_gerador(self):
        modulo = _carregar_gerador()
        with tempfile.TemporaryDirectory(prefix="p1a37-pacote-") as tmp:
            saida = os.path.join(tmp, "pacote.txt")
            rc = modulo.main([BASE, ALVO, saida])
            self.assertEqual(rc, 0)
            with open(saida, encoding="utf-8") as f:
                texto = f.read()
        self.assertTrue(autoinclusao.contem_o_gerador(texto, _GERADOR))

    def test_argumentos_faltando_nao_gravam_nada(self):
        modulo = _carregar_gerador()
        self.assertEqual(modulo.main([]), 2)


if __name__ == "__main__":
    unittest.main()
