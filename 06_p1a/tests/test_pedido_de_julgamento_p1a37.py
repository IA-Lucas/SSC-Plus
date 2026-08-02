"""Pedir julgamento e omitir o objeto e o defeito — SSC+ P1-A.3.7, N6.

O ACHADO, na formulacao do proprio registro da P1-A.3.6 (§3.4): *"Pedir
julgamento sobre um artefato ausente e defeito de composicao desta
missao"*, e o remedio e um OU exclusivo — incluir o gerador **ou** parar
de pedir o julgamento. *"As duas coisas juntas — pedir o julgamento e
omitir o objeto — e o defeito."*

N6 nao e um guarda do acervo que falhou: e defeito de COMPOSICAO, e o
objeto nem existia quando os 86 guardas foram varridos. Por isso a
correcao nao e "consertar um guarda", e sim **criar o portao que torna o
defeito inescrevivel**: `autoinclusao.conferir` roda na montagem, antes
de a saida existir, e recusa o pacote que pede sem carregar.

O CAMINHO QUE A OPERACAO PERCORRE. O defeito ocorre na MONTAGEM do
pacote, e o unico jeito de ele chegar a um revisor e o arquivo ser
gravado. O teste que importa, portanto, nao e "conferir levanta": e que
`main()` NAO CRIA O ARQUIVO quando o pacote esta defeituoso. Pacote
defeituoso que ja existe em disco pode ser enviado por engano.

ESTADO MEDIDO DOS GERADORES DO ACERVO, e nao presumido — a tabela abaixo
e conferida por teste a cada corrida:

    pacote_p1a31.py   pede=nao   autoinclui=nao   -> OU satisfeito
    pacote_p1a33.py   pede=nao   autoinclui=nao   -> OU satisfeito
    pacote_p1a36.py   pede=SIM   autoinclui=nao   -> DEFEITO (N6)
    pacote_p1a37.py   pede=SIM   autoinclui=SIM   -> corrigido

O QUE ESTES TESTES NAO COBREM, e o que fica REGISTRADO E NAO CORRIGIDO:
- `pacote_p1a36.py` continua com o defeito, DE PROPOSITO. Ele gerou o
  pacote `5ab35a6c…`, que um revisor real leu e julgou, e o registro da
  P1-A.3.6 publica esse hash como reproduzivel por terceiros. Alterar o
  texto do gerador quebraria essa reprodutibilidade — seria apagar a
  evidencia do defeito em vez de corrigi-lo. O achado permanece ABERTO
  contra ele; o que este commit garante e que o PROXIMO pacote nao
  possa nascer com ele;
- a deteccao de "pede julgamento" e por linha e por vocabulario
  enumerado de verbos. Um pedido escrito com outro verbo, ou partido em
  duas linhas, escapa — enumeracao nao e exaustiva, e isto e limite, nao
  propriedade;
- nada aqui envia pacote a revisor algum.
"""

import glob
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ = os.path.dirname(_DIR_P1A)
_EVIDENCIAS = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _EVIDENCIAS)

import autoinclusao  # noqa: E402

_GERADOR = os.path.join(_EVIDENCIAS, "pacote_p1a37.py")

# Geradores CONGELADOS: produziram pacotes cujo SHA-256 esta publicado.
# A exclusao e declarada, com razao, e o estado defeituoso de cada um e
# MEDIDO abaixo — nao afirmado.
CONGELADOS = {
    "pacote_p1a31.py": "gerou o pacote c17b730f, publicado",
    "pacote_p1a33.py": "gerou o pacote 87f41503, publicado",
    "pacote_p1a36.py": "gerou o pacote 5ab35a6c, lido por revisor real",
}

PEDIDO = ("4. O gerador DESTE pacote herda a mesma construcao — "
          "julgue-o tambem.")


class OPortaoRecusaPedirSemIncluir(unittest.TestCase):

    def test_pedir_e_omitir_e_recusado(self):
        with self.assertRaises(SystemExit) as ctx:
            autoinclusao.conferir("texto qualquer\n" + PEDIDO, _GERADOR)
        self.assertIn("pede julgamento sobre o gerador", str(ctx.exception))

    def test_nao_pedir_e_omitir_e_aceito(self):
        # A OUTRA metade do OU: um pacote que nao pede julgamento sobre o
        # gerador pode omiti-lo. Sem esta, o portao viraria "todo pacote
        # tem de embutir o gerador", que nao e o remedio especificado.
        autoinclusao.conferir("pacote sem pedido nenhum", _GERADOR)

    def test_pedir_e_incluir_e_aceito(self):
        texto = (autoinclusao.secao_do_gerador(_GERADOR) + "\n" + PEDIDO)
        autoinclusao.conferir(texto, _GERADOR)

    def test_incluir_o_fonte_sem_o_hash_nao_basta(self):
        # So o fonte deixaria o revisor sem como conferir que o arquivo
        # do repositorio e o mesmo que produziu o pacote.
        secao = autoinclusao.secao_do_gerador(_GERADOR)
        digest = autoinclusao.sha256_do_arquivo(_GERADOR)
        with self.assertRaises(SystemExit):
            autoinclusao.conferir(secao.replace(digest, "0" * 64) + PEDIDO,
                                  _GERADOR)

    def test_incluir_o_hash_sem_o_fonte_nao_basta(self):
        digest = autoinclusao.sha256_do_arquivo(_GERADOR)
        texto = (f"{autoinclusao.ROTULO_SECAO}\nsha256: {digest}\n"
                 "(fonte omitido)\n" + PEDIDO)
        with self.assertRaises(SystemExit):
            autoinclusao.conferir(texto, _GERADOR)


class OArquivoDefeituosoNaoChegaAExistir(unittest.TestCase):
    """O que importa em operacao: o pacote ruim nao vira arquivo."""

    def _carregar(self):
        spec = importlib.util.spec_from_file_location("p1a37_portao",
                                                      _GERADOR)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo

    def test_main_nao_grava_quando_o_pacote_pede_sem_incluir(self):
        modulo = self._carregar()
        with tempfile.TemporaryDirectory(prefix="p1a37-portao-") as tmp:
            saida = os.path.join(tmp, "pacote.txt")
            with mock.patch.object(modulo, "montar_pacote",
                                   lambda base, alvo: "conteudo\n" + PEDIDO):
                with self.assertRaises(SystemExit):
                    modulo.main(["BASE", "ALVO", saida])
            self.assertFalse(
                os.path.exists(saida),
                "pacote defeituoso virou arquivo: em disco, ele pode ser "
                "enviado por engano")

    def test_main_grava_quando_o_pacote_pede_e_inclui(self):
        # Contraprova: sem ela, um portao que recusasse sempre passaria
        # no teste acima.
        modulo = self._carregar()
        bom = (autoinclusao.secao_do_gerador(_GERADOR) + "\n" + PEDIDO)
        with tempfile.TemporaryDirectory(prefix="p1a37-portao-ok-") as tmp:
            saida = os.path.join(tmp, "pacote.txt")
            with mock.patch.object(modulo, "montar_pacote",
                                   lambda base, alvo: bom), \
                    mock.patch("sys.stdout", _SaidaMuda()):
                self.assertEqual(modulo.main(["BASE", "ALVO", saida]), 0)
            self.assertTrue(os.path.exists(saida))


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


class EstadoMedidoDosGeradoresDoAcervo(unittest.TestCase):
    """A tabela do docstring, conferida — nunca afirmada."""

    def _fonte(self, nome):
        with open(os.path.join(_EVIDENCIAS, nome), encoding="utf-8") as f:
            return f.read()

    def test_todo_gerador_novo_passa_pelo_portao(self):
        # A enumeracao e do DISCO: um gerador acrescentado amanha cai
        # aqui sozinho, sem ninguem lembrar de o inscrever.
        for caminho in sorted(glob.glob(os.path.join(_EVIDENCIAS,
                                                     "pacote_*.py"))):
            nome = os.path.basename(caminho)
            if nome in CONGELADOS:
                continue
            with self.subTest(gerador=nome):
                fonte = self._fonte(nome)
                self.assertIn(
                    "conferir", fonte,
                    f"{nome} nao passa pelo portao de auto-inclusao")

    def test_o_defeito_do_gerador_congelado_e_medido_e_nao_suposto(self):
        # O registro do limite tem de valer pelo que se mede. Se um dia
        # `pacote_p1a36.py` deixar de pedir o julgamento, isto fica
        # vermelho e o registro precisa ser reescrito.
        fonte = self._fonte("pacote_p1a36.py")
        self.assertTrue(autoinclusao.pede_julgamento_do_gerador(fonte),
                        "pacote_p1a36 deixou de pedir o julgamento")
        self.assertNotIn("secao_do_gerador", fonte,
                         "pacote_p1a36 passou a se auto-incluir")

    def test_os_outros_dois_congelados_satisfazem_o_OU(self):
        # p1a31 e p1a33 nao pedem julgamento sobre o gerador; omitir o
        # fonte, neles, nao e o defeito N6. Registrado por medicao.
        for nome in ("pacote_p1a31.py", "pacote_p1a33.py"):
            with self.subTest(gerador=nome):
                self.assertFalse(autoinclusao.pede_julgamento_do_gerador(
                    self._fonte(nome)))

    def test_a_lista_de_congelados_nomeia_arquivos_que_existem(self):
        for nome in CONGELADOS:
            with self.subTest(gerador=nome):
                self.assertTrue(
                    os.path.isfile(os.path.join(_EVIDENCIAS, nome)),
                    "exclusao declarada para arquivo inexistente e "
                    "exclusao sem objeto")


if __name__ == "__main__":
    unittest.main()
