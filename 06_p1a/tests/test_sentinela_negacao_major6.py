"""A negacao do que a sentinela NAO resolve — MAJOR #6 / N5 / P1A4-2.

O DEFEITO, na voz do revisor: *"%/.format/join e imports dinamicos
atravessam sem negacao. Remedio: construcao nao resolvida = REPROVA,
nao = ignora"*. O dobrador (`dobrar_constante`) ja recusava essas
formas — mas a recusa virava SILENCIO, e silencio saia como arquivo
limpo. O proprio docstring do dobrador AFIRMAVA que o recusado entrava
em `nao_resolvidos`, sem que codigo nenhum o fizesse: a familia (F)
dentro do remedio declarado.

O CAMINHO QUE A OPERACAO PERCORRE: `sentinela_antip2.varrer`, com raiz,
caminhada e classificador — a mesma funcao da operacao real, contra
arvores sinteticas que CONTEM o violador (o desenho da P1-A.3.7).

O QUE ESTES TESTES NAO COBREM, declarado:

- construcao SEM fragmento nenhum do vocabulario (chr(), base64, dado
  externo) continua invisivel — o portao de vocabulario e o que impede
  a negacao de acusar milhares de linhas legitimas, e este e o limite
  declarado da correcao, nao propriedade;
- o reconhecimento nominal so foi exercido aqui contra a forma exata
  `caminho:linha motivo`; divergencia de forma volta para
  `nao_resolvidos`, que e o lado fechado do portao.
"""

import os
import sys
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sentinela_antip2 as sentinela  # noqa: E402
from test_sentinela_antip2_p1a37 import _ArvoreSintetica  # noqa: E402


class ConstrucaoNaoResolvidaEhNegada(_ArvoreSintetica):
    """Cada forma nomeada pelo revisor, exercida contra violador."""

    FORMAS = {
        "concatenacao": 'v = "SHADOW_" + sufixo\n',
        "interpolacao-porcento": 'v = "%s_ELIGIBLE" % origem\n',
        "f-string": 'v = f"SHADOW_{sufixo}"\n',
        "format": 'v = "{}_ELIGIBLE".format(origem)\n',
        "join": 'v = "_".join(["SHADOW", sufixo])\n',
        "import-dinamico-import_module":
            'import importlib\nm = importlib.import_module(nome)\n',
        "import-dinamico-dunder": 'm = __import__(nome)\n',
    }

    def test_cada_forma_nomeada_vira_negacao(self):
        for forma, corpo in sorted(self.FORMAS.items()):
            with self.subTest(forma=forma):
                # o arquivo do violador e removido ao fim do subTest para
                # que uma forma nao herde a sujeira da anterior.
                caminho = self.escrever(
                    f"07_p1b/violador_{forma.replace('-', '_')}.py",
                    f"def montar(sufixo, origem, nome):\n"
                    + "".join(f"    {linha}\n"
                              for linha in corpo.strip().splitlines())
                    + "    return v if 'v' in dir() else m\n")
                achados = self.varrer()
                negados = [a.replace("\\", "/")
                           for a in achados["nao_resolvidos"]]
                self.assertTrue(
                    any(f"violador_{forma.replace('-', '_')}.py" in n
                        for n in negados),
                    f"a forma {forma} atravessou sem negacao: {negados}")
                os.remove(caminho)

    def test_string_dinamica_sem_vocabulario_continua_limpa(self):
        # O portao de vocabulario: negacao sem ele acusaria o repositorio
        # inteiro e enterraria o achado real.
        self.escrever("06_p1a/relatorio.py",
                      'def resumo(total, itens, nome):\n'
                      '    a = "%s de %d bytes" % (nome, total)\n'
                      '    b = f"lidos {total} arquivos"\n'
                      '    c = ", ".join(itens)\n'
                      '    d = "{} processados".format(total)\n'
                      '    return a + b + c + d\n')
        achados = self.varrer()
        self.assertEqual(achados["nao_resolvidos"], [])
        self.assertEqual(achados["nao_resolvidos_reconhecidos"], [])


class ReconhecimentoNominal(_ArvoreSintetica):
    """O achado reconhecido MIGRA de campo; nunca some, nunca fecha o
    portao para o vizinho nao reconhecido."""

    def test_reconhecido_migra_e_nao_reconhecido_fica(self):
        self.escrever("07_p1b/congelado.py",
                      'def montar(sufixo):\n'
                      '    return "SHADOW_" + sufixo\n')
        self.escrever("07_p1b/novo.py",
                      'def montar(sufixo):\n'
                      '    return "%s_ELIGIBLE" % sufixo\n')
        cru = sentinela.varrer(self.raiz, self.classificador,
                               reconhecidos=())
        negados_crus = [a.replace("\\", "/")
                        for a in cru["nao_resolvidos"]]
        alvo = next(n for n in negados_crus if "congelado.py" in n)

        com_reconhecimento = sentinela.varrer(
            self.raiz, self.classificador, reconhecidos=(alvo,))
        restantes = [a.replace("\\", "/")
                     for a in com_reconhecimento["nao_resolvidos"]]
        migrados = [a.replace("\\", "/")
                    for a in com_reconhecimento[
                        "nao_resolvidos_reconhecidos"]]
        self.assertEqual(migrados, [alvo],
                         "o reconhecido nao migrou para o campo visivel")
        self.assertTrue(any("novo.py" in r for r in restantes),
                        "o reconhecimento de um fechou o portao do outro")
        self.assertFalse(any("congelado.py" in r for r in restantes))

    def test_a_lista_declarada_cobre_exatamente_o_que_o_acervo_tem(self):
        # A operacao real: raiz do repositorio, lista declarada. Todo
        # item declarado precisa CASAR com um achado real — declaracao
        # morta e o guarda vazio contra o qual ha tres missoes de trilha.
        dir_p1a = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raiz_real = os.path.dirname(dir_p1a)
        achados = sentinela.varrer(
            raiz_real, os.path.join(dir_p1a, "preflight", "pipeline.py"))
        reconhecidos = sorted(
            a.replace("\\", "/")
            for a in achados["nao_resolvidos_reconhecidos"])
        self.assertEqual(
            reconhecidos, sorted(sentinela.NAO_RESOLVIDOS_RECONHECIDOS),
            "a lista declarada e o que a varredura reconhece divergem — "
            "ha declaracao morta ou achado novo nao reconhecido")


if __name__ == "__main__":
    unittest.main()
