"""As nove falhas: classe COM TESTE, nao classe com o nome — P1-A.3.9.

MECANISMO (c) da FASE 2 da P1-A.3.8, guarda `P1A-54`. A linha da
remedicao e literal:

    metade forte: os nove tipos de erro sao OBJETOS REAIS importados,
    com codigo estavel e unico. Metade fraca: *"uma classe por falha"*
    confere CONVENCAO DE NOME (`Falha\\d{2}\\w+`), nao que a falha seja
    exercida. Uma classe VAZIA com o nome certo satisfaz.
    Remedio: exigir >= 1 metodo `test_*` por classe.

`CoberturaDasNoveFalhas` (`test_falhas_obrigatorias.py:422`) NAO foi
editado — registro aditivo. A metade forte dele continua valendo; este
arquivo substitui a metade fraca por tres perguntas que uma classe
vazia nao responde.

## As tres perguntas

1. **cada classe tem metodo de teste**, contado pelo LOADER do unittest
   — nao por AST, nao por convencao de nome: o que o loader colhe e o
   que de fato roda;
2. **cada classe cita o CODIGO da falha que diz cobrir.** Uma classe com
   um `test_nada(self): pass` satisfaz a pergunta 1 e nao exerce nada. O
   codigo tipado (`P1A-...`) e o unico elo entre a classe e a falha;
3. **a uniao dos codigos citados pelas nove classes e o conjunto dos
   nove codigos.** Sem esta, tres classes poderiam citar o mesmo codigo
   e seis falhas ficariam sem dono — o buraco que uma contagem por nome
   nao ve.

## Por que o codigo, e nao a contagem de assercoes

Contar `assert` premiaria teste inchado. Contar linhas premiaria
verbosidade. O codigo tipado e o unico identificador que liga a classe a
falha obrigatoria, e ele ja e o eixo da metade forte do guarda antigo —
que importa os nove TIPOS reais e exige codigo estavel e unico.

## O QUE ESTES TESTES NAO COBREM, declarado

- **citar o codigo nao e exercer a falha.** Uma classe que citasse o
  codigo numa string sem asserir nada passaria. O que este guarda fecha
  e o caso da classe VAZIA e o da falha SEM DONO, nao a qualidade da
  assercao — para isso valem os proprios testes das nove classes;
- **so as classes `Falha\\d{2}\\w+` de `test_falhas_obrigatorias`** sao
  o objeto; outras falhas do acervo nao entram;
- **nada se afirma sobre a suficiencia das nove**: que sejam as falhas
  certas e decisao de politica, registrada na P1-A, e nao medicao;
- o guarda nao roda as classes: ele as inspeciona. Quem as roda e a
  propria suite, na mesma corrida.
"""

import re
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
import test_falhas_obrigatorias as falhas
from preflight import (BillingDesconhecido, ChavePaygDetectada,
                       CliIndisponivel, ConfigPaygPersistida,
                       ConflitoAmbienteLogin, ModeloRemovido, OAuthAusente,
                       PlanoNaoReconhecido, QuotaEsgotada)

PADRAO_CLASSE = re.compile(r"Falha\d{2}\w+")

TIPOS = (ChavePaygDetectada, ConfigPaygPersistida, OAuthAusente,
         PlanoNaoReconhecido, QuotaEsgotada, BillingDesconhecido,
         CliIndisponivel, ModeloRemovido, ConflitoAmbienteLogin)

CODIGOS = frozenset(tipo.codigo for tipo in TIPOS)


def classes_de_falha() -> dict:
    """Nome -> classe, colhidas do MODULO real, nao de uma lista."""
    return {nome: obj for nome, obj in vars(falhas).items()
            if isinstance(obj, type) and PADRAO_CLASSE.fullmatch(nome)}


def _fonte_da_classe(classe) -> str:
    """Fonte da classe, para procurar os codigos que ela cita."""
    import inspect
    return inspect.getsource(classe)


def codigos_citados(classe) -> set:
    fonte = _fonte_da_classe(classe)
    return {codigo for codigo in CODIGOS if codigo in fonte}


def metodos_de_teste(classe) -> list:
    """O que o LOADER do unittest de fato colhe — nao o que o nome promete."""
    return unittest.TestLoader().getTestCaseNames(classe)


class CadaFalhaTemClasseQueRoda(unittest.TestCase):
    """A metade fraca de `P1A-54`, substituida por medicao."""

    def test_sao_nove_classes(self):
        # A metade que o guarda antigo ja tinha, mantida: sem ela as
        # perguntas abaixo poderiam ser satisfeitas por um conjunto
        # menor.
        nomes = sorted(classes_de_falha())
        self.assertEqual(len(nomes), 9, nomes)
        for n in range(1, 10):
            with self.subTest(falha=n):
                self.assertTrue(
                    any(nome.startswith(f"Falha{n:02d}") for nome in nomes),
                    f"falha obrigatoria {n} sem classe de teste")

    def test_toda_classe_tem_ao_menos_um_metodo_que_o_loader_colhe(self):
        # O REMEDIO da linha `P1A-54`. Classe vazia com o nome certo
        # deixa de satisfazer.
        for nome, classe in sorted(classes_de_falha().items()):
            with self.subTest(classe=nome):
                metodos = metodos_de_teste(classe)
                self.assertTrue(
                    metodos,
                    f"{nome} nao tem metodo test_* nenhum — e a classe "
                    "vazia com o nome certo que o guarda antigo aceitava")

    def test_toda_classe_cita_o_codigo_da_falha_que_cobre(self):
        # Segunda pergunta: um `test_nada(self): pass` satisfaz a
        # primeira e nao exerce nada.
        for nome, classe in sorted(classes_de_falha().items()):
            with self.subTest(classe=nome):
                self.assertTrue(
                    codigos_citados(classe),
                    f"{nome} nao cita nenhum codigo P1A- tipado: nada a "
                    "liga a uma falha obrigatoria")

    def test_a_uniao_dos_codigos_citados_cobre_as_nove_falhas(self):
        # Terceira pergunta: sem ela, tres classes poderiam citar o
        # mesmo codigo e seis falhas ficariam sem dono.
        citados = set()
        for classe in classes_de_falha().values():
            citados |= codigos_citados(classe)
        self.assertEqual(sorted(citados), sorted(CODIGOS),
                         f"falhas sem dono: {sorted(CODIGOS - citados)}")

    def test_os_nove_codigos_sao_estaveis_e_unicos(self):
        # A metade FORTE do guarda antigo, reafirmada aqui porque as
        # perguntas acima dependem dela: codigo repetido faria duas
        # falhas parecerem uma.
        self.assertEqual(len(TIPOS), 9)
        self.assertEqual(len(CODIGOS), 9, [t.codigo for t in TIPOS])
        for tipo in TIPOS:
            with self.subTest(tipo=tipo.__name__):
                self.assertTrue(tipo.codigo.startswith("P1A-"))
                self.assertTrue(issubclass(tipo, Exception))


class OInstrumentoRecusaOQueDeveRecusar(unittest.TestCase):
    """CONTROLE POSITIVO: o detector distingue os casos que ele julga."""

    def test_classe_vazia_com_o_nome_certo_nao_passa(self):
        vazia = type("Falha99Vazia", (unittest.TestCase,), {})
        self.assertEqual(metodos_de_teste(vazia), [])
        self.assertTrue(PADRAO_CLASSE.fullmatch("Falha99Vazia"))

    def test_classe_com_metodo_de_teste_passa(self):
        def test_algo(self):
            pass
        cheia = type("Falha98Cheia", (unittest.TestCase,),
                     {"test_algo": test_algo})
        self.assertEqual(metodos_de_teste(cheia), ["test_algo"])

    def test_metodo_que_nao_comeca_por_test_nao_conta(self):
        # O loader e a autoridade: um `verificar_algo` nao roda, e um
        # detector por AST que contasse `def` qualquer aceitaria a
        # classe vazia disfarcada.
        def verificar_algo(self):
            pass
        disfarcada = type("Falha97Disfarcada", (unittest.TestCase,),
                          {"verificar_algo": verificar_algo})
        self.assertEqual(metodos_de_teste(disfarcada), [])

    def test_o_detector_de_codigo_nao_acha_o_que_nao_ha(self):
        class SemCodigo(unittest.TestCase):
            def test_nada(self):
                pass
        self.assertEqual(codigos_citados(SemCodigo), set())

    def test_o_detector_de_codigo_acha_o_que_ha(self):
        # O detector le o FONTE da classe: uma classe que so referencie
        # o atributo (`ChavePaygDetectada.codigo`) nao cita o codigo, e
        # nao deve contar — medido ao escrever este arquivo. E o LITERAL
        # que liga a classe a falha, como as nove reais fazem ao passar
        # o codigo para `afirmar_bloqueio`.
        class ComCodigo(unittest.TestCase):
            def test_algo(self):
                self.assertEqual("P1A-PAYG-ENV", ChavePaygDetectada.codigo)

        class SoPeloAtributo(unittest.TestCase):
            def test_algo(self):
                self.assertTrue(ChavePaygDetectada.codigo)

        self.assertIn(ChavePaygDetectada.codigo, codigos_citados(ComCodigo))
        self.assertEqual(codigos_citados(SoPeloAtributo), set())


if __name__ == "__main__":
    unittest.main()
