"""O sentinela nao e mais contornavel de proposito — SSC+ P1-A.3.7, N5.

O ACHADO, na voz do revisor independente: *"o sentinela AST e
explorável"* — mais exatamente, *"so reconhece literais exatos e aliases
atribuidos no mesmo arquivo, de modo que concatenacao, constante
importada (`RESULTADOS`) ou propagacao por booleano CONTORNAM
`_portoes_de_execucao`"*.

O atestado classificou N5 como **(N) classe que a varredura nao media**
quanto a este ponto: *"a varredura classificava guardas; nao media se um
guarda podia ser contornado DE PROPOSITO"*. E a diferenca entre "o
guarda esta verde" e "o guarda resiste a quem quer passar por ele".

TRES CONTORNOS NOMEADOS, e um quarto que o remedio exige:

1. CONCATENACAO — `"SHADOW" + "_ELIGIBLE"` nao e `ast.Constant` igual a
   nenhum termo. `dobrar_constante` dobra o que o interpretador dobraria;
2. CONSTANTE IMPORTADA — `from preflight.pipeline import RESULTADOS`. O
   nome nao e atribuido no arquivo. O modulo de origem passa a ser
   localizado, parseado, e os apelidos dele entram;
3. PROPAGACAO POR BOOLEANO — `apto = (r == "SHADOW_ELIGIBLE")` e depois
   `if apto:`. O nome recebe a DECISAO, nao o literal. Ponto fixo;
4. **OU NEGA QUANDO NAO CONSEGUE RESOLVER** — a segunda metade literal
   do remedio do §9.4. Import de modulo do repositorio que nao parseia
   vira achado, e nao silencio.

O CAMINHO QUE A OPERACAO PERCORRE. Todos os casos abaixo passam por
`sentinela_antip2.varrer`, a MESMA funcao que roda contra a arvore real
do repositorio — com raiz, caminhada de diretorios e classificador. Nao
ha assercao sobre `dobrar_constante` isolada a nao ser uma, e ela esta
marcada como fixacao do eixo.

O QUE ESTES TESTES NAO COBREM, declarado:
- a resolucao de modulo e por SUFIXO de caminho, nao pelo `sys.path` do
  interpretador — reproduzi-lo exigiria executar os arquivos. Sufixo
  ambiguo resolve pela UNIAO dos candidatos: erra para o lado de
  reconhecer apelidos DEMAIS, o que produz achado a mais e nunca ponto
  cego. Um import que so o `sys.path` real resolveria pode escapar;
- `%`, `.format` e `str.join` NAO sao dobrados. Um consumidor que monte
  o termo por `"%s_ELIGIBLE" % "SHADOW"` passa. A enumeracao de formas
  de dobra nao e exaustiva, e isto e limite, nao propriedade;
- import dinamico (`importlib`, `__import__`, `getattr` sobre modulo)
  nao e seguido nem negado;
- a analise segue import entre modulos, mas NAO segue dataflow: um
  valor que atravessa uma funcao de outro modulo nao e rastreado;
- nada disto prova que a P1-B nao consuma o veredito por meio que nao
  seja o fonte versionado.
"""

import ast
import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sentinela_antip2 as sentinela  # noqa: E402

CLASSIFICADOR_REL = "06_p1a/preflight/pipeline.py"

FONTE_CLASSIFICADOR = '''
RESULTADOS = ("ELIGIBLE", "SHADOW_ELIGIBLE", "SUPERVISED", "BLOCKED")


def classificar(teto):
    return teto
'''


class _Arvore(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a37-n5-")
        self.raiz = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.classificador = os.path.join(self.raiz,
                                          *CLASSIFICADOR_REL.split("/"))
        self.escrever(CLASSIFICADOR_REL, FONTE_CLASSIFICADOR)

    def escrever(self, rel: str, fonte: str) -> str:
        caminho = os.path.join(self.raiz, *rel.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(fonte)
        return caminho

    def varrer(self) -> dict:
        return sentinela.varrer(self.raiz, self.classificador)

    def assertAcusa(self, chave="portoes"):
        achados = self.varrer()
        self.assertTrue(achados[chave],
                        f"contorno NAO acusado; achados: {achados}")
        return achados


class ContornoPorConcatenacao(_Arvore):

    def test_soma_de_constantes_e_reconhecida(self):
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(r):\n'
                      '    if r == "SHADOW" + "_ELIGIBLE":\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_soma_de_tres_partes_e_reconhecida(self):
        self.escrever("07_p1b/consumidor.py",
                      'def usar(r):\n'
                      '    return r == "SHA" + "DOW" + "_ELIGIBLE"\n')
        self.assertAcusa("decisoes_fora")

    def test_fstring_sem_interpolacao_e_reconhecida(self):
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(r):\n'
                      '    if r == f"BLOCKED":\n'
                      '        return None\n'
                      '    subprocess.run(["kimi"])\n')
        # O `else` implicito nao existe aqui; o portao esta no corpo do
        # `if`, que retorna. A decisao, porem, e acusada.
        self.assertAcusa("decisoes_fora")

    def test_o_eixo_da_dobra_fixado(self):
        # Unica assercao sobre a primitiva, e ela existe para fixar o
        # eixo: o mesmo VALOR em formas diferentes tem de dobrar igual.
        for fonte in ('"SHADOW_ELIGIBLE"', '"SHADOW" + "_ELIGIBLE"',
                      'f"SHADOW_ELIGIBLE"', '"SHA" "DOW_ELIGIBLE"'):
            with self.subTest(fonte=fonte):
                no = ast.parse(fonte, mode="eval").body
                self.assertEqual(sentinela.dobrar_constante(no),
                                 "SHADOW_ELIGIBLE")
        # E o que NAO e constante nao vira texto por acidente.
        no = ast.parse('"SHADOW" + sufixo', mode="eval").body
        self.assertIsNone(sentinela.dobrar_constante(no))


class ContornoPorConstanteImportada(_Arvore):

    def test_from_import_de_constante_do_classificador(self):
        # O contorno que o revisor nomeou pelo nome: `RESULTADOS`.
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n'
                      'from preflight.pipeline import RESULTADOS\n\n\n'
                      'def usar(r):\n'
                      '    if r in RESULTADOS:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_import_de_modulo_e_referencia_por_atributo(self):
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n'
                      'import preflight.pipeline as p\n\n\n'
                      'def usar(r):\n'
                      '    if r in p.RESULTADOS:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_import_estrela_traz_os_apelidos(self):
        self.escrever("07_p1b/consumidor.py",
                      'from preflight.pipeline import *\n\n\n'
                      'def usar(r):\n'
                      '    return r in RESULTADOS\n')
        self.assertAcusa("decisoes_fora")

    def test_import_em_dois_saltos_e_seguido(self):
        # `consumidor` importa de `ponte`, que importa do classificador.
        self.escrever("06_p1a/ponte.py",
                      'from preflight.pipeline import RESULTADOS\n\n'
                      'TERMOS = RESULTADOS\n')
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n'
                      'from ponte import TERMOS\n\n\n'
                      'def usar(r):\n'
                      '    if r in TERMOS:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_import_de_stdlib_nao_vira_apelido(self):
        # Contraprova: se todo import virasse apelido, qualquer `if` com
        # qualquer nome seria portao e o guarda reprovaria sempre.
        self.escrever("07_p1b/consumidor.py",
                      'import os\n'
                      'import subprocess\n\n\n'
                      'def usar(caminho):\n'
                      '    if os.path.isfile(caminho):\n'
                      '        subprocess.run(["kimi"])\n')
        achados = self.varrer()
        self.assertEqual(achados["portoes"], [])
        self.assertEqual(achados["decisoes_fora"], [])


class ContornoPorPropagacaoBooleana(_Arvore):

    def test_booleano_intermediario_e_alcancado(self):
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(r):\n'
                      '    apto = (r == "SHADOW_ELIGIBLE")\n'
                      '    if apto:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_cadeia_de_booleanos_e_alcancada(self):
        # Uma passada unica pegaria `apto` e perderia `ok`. O ponto fixo
        # e o que fecha a cadeia.
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(r):\n'
                      '    apto = (r == "SHADOW_ELIGIBLE")\n'
                      '    ok = apto\n'
                      '    liberado = ok\n'
                      '    if liberado:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_booleano_de_constante_importada(self):
        # Os tres contornos combinados num so arquivo.
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n'
                      'from preflight.pipeline import RESULTADOS\n\n\n'
                      'def usar(r):\n'
                      '    apto = r in RESULTADOS\n'
                      '    if apto:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertAcusa()

    def test_booleano_sem_relacao_com_o_veredito_nao_acusa(self):
        # Contraprova do ponto fixo: sem ela, todo booleano do
        # repositorio viraria apelido e o guarda reprovaria sempre.
        self.escrever("07_p1b/consumidor.py",
                      'import subprocess\n\n\n'
                      'def usar(n):\n'
                      '    grande = n > 10\n'
                      '    if grande:\n'
                      '        subprocess.run(["kimi"])\n')
        self.assertEqual(self.varrer()["portoes"], [])


class NegaQuandoNaoConsegueResolver(_Arvore):
    """A segunda metade literal do remedio do §9.4."""

    def test_import_de_modulo_do_repositorio_que_nao_parseia(self):
        self.escrever("06_p1a/quebrado.py", "def (:\n")
        self.escrever("07_p1b/consumidor.py",
                      'from quebrado import ALGO\n\n\n'
                      'def usar(r):\n'
                      '    return r in ALGO\n')
        achados = self.varrer()
        self.assertTrue(achados["nao_resolvidos"],
                        "import irresolvivel saiu como arquivo limpo")
        self.assertTrue(any("quebrado.py" in m
                            for m in achados["nao_resolvidos"]))

    def test_import_estrela_de_modulo_irresolvivel_tambem_nega(self):
        self.escrever("06_p1a/quebrado.py", "class (:\n")
        self.escrever("07_p1b/consumidor.py",
                      'from quebrado import *\n\n\n'
                      'def usar(r):\n'
                      '    return r == "algo"\n')
        self.assertTrue(self.varrer()["nao_resolvidos"])

    def test_arvore_sem_import_irresolvivel_nao_nega(self):
        # Contraprova: negar sempre seria trocar ponto cego por ruido.
        self.escrever("07_p1b/consumidor.py",
                      'from preflight.pipeline import RESULTADOS\n\n\n'
                      'def contar():\n'
                      '    return len(RESULTADOS)\n')
        self.assertEqual(self.varrer()["nao_resolvidos"], [])

    def test_o_ciclo_de_import_nao_vira_recursao_infinita(self):
        self.escrever("06_p1a/a.py", "from b import X\n\nY = X\n")
        self.escrever("06_p1a/b.py", "from a import Y\n\nX = Y\n")
        self.escrever("07_p1b/consumidor.py",
                      'from a import Y\n\n\n'
                      'def usar(r):\n'
                      '    return r == Y\n')
        self.varrer()   # nao pode estourar a pilha


class AArvoreRealSegueLimpaSobAResolucaoNova(unittest.TestCase):

    def test_o_repositorio_real_nao_ganha_achado_nem_negacao(self):
        # A resolucao nova ve MAIS coisas. Se ela produzisse achado sobre
        # a arvore real, isso seria defeito a tratar — e nao ruido a
        # tolerar. Medido: nao produz.
        dir_p1a = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raiz = os.path.dirname(dir_p1a)
        achados = sentinela.varrer(
            raiz, os.path.join(raiz, *CLASSIFICADOR_REL.split("/")))
        self.assertEqual(achados["ilegiveis"], [])
        self.assertEqual(achados["portoes"], [])
        self.assertEqual(achados["decisoes_fora"], [])
        self.assertEqual(achados["nao_resolvidos"], [])

    def test_a_resolucao_por_import_alcanca_o_runner_da_p1b(self):
        # Sem esta medicao, "limpo" poderia significar "a resolucao nem
        # chegou a 07_p1b". `preflight_atual.py` importa RESULTADOS do
        # classificador de verdade: o apelido tem de aparecer.
        dir_p1a = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raiz = os.path.dirname(dir_p1a)
        caminho = os.path.join(raiz, "07_p1b", "preflight_atual.py")
        with open(caminho, encoding="utf-8") as f:
            arvore = ast.parse(f.read(), filename=caminho)
        apelidos, nao_resolvidos = sentinela.apelidos_do_veredito(
            arvore, sentinela.indice_de_modulos(raiz))
        self.assertIn("RESULTADOS", apelidos,
                      "a constante importada do classificador nao foi "
                      "resolvida: o contorno do N5 segue aberto")
        self.assertEqual(nao_resolvidos, [])


if __name__ == "__main__":
    unittest.main()
