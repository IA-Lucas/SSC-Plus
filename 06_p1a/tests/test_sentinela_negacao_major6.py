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


class ComparacaoContraConstrutorEhNegada(_ArvoreSintetica):
    """O residuo da P1-A.10: contorno SEM fragmento do vocabulario.

    Na atribuicao ele continua invisivel (limite declarado); no ponto de
    DECISAO nao ha como não comparar, e ali a negacao dispensa o portao
    de vocabulario.
    """

    FORMAS = {
        "chr-encadeado": 'if r == chr(83) + chr(72) + sufixo(dado):\n',
        "join-sobre-literal": 'if r == "".join(pedacos(dado)):\n',
        "decode-de-literal": 'if r == b"\\x53\\x48".decode() + resto(dado):\n',
    }

    def test_cada_forma_de_contorno_cego_vira_negacao(self):
        for forma, condicao in sorted(self.FORMAS.items()):
            with self.subTest(forma=forma):
                caminho = self.escrever(
                    f"07_p1b/cego_{forma.replace('-', '_')}.py",
                    "def usar(r, dado, sufixo, pedacos, resto):\n"
                    f"    {condicao}"
                    "        return 1\n"
                    "    return 0\n")
                achados = self.varrer()
                negados = [a.replace("\\", "/")
                           for a in achados["nao_resolvidos"]]
                self.assertTrue(
                    any(f"cego_{forma.replace('-', '_')}.py" in n
                        for n in negados),
                    f"contorno cego {forma} atravessou: {negados}")
                os.remove(caminho)

    def test_comparacao_comum_nao_e_negada(self):
        self.escrever("06_p1a/logica.py",
                      'def decide(a, b, nome, extensao):\n'
                      '    if a + b > 10:\n'
                      '        return 1\n'
                      '    if nome == extensao:\n'
                      '        return 2\n'
                      '    if nome == "constante.txt":\n'
                      '        return 3\n'
                      '    return 0\n')
        achados = self.varrer()
        self.assertEqual(achados["nao_resolvidos"], [])


class ComparacaoContraAliasOuDecodeNaoLiteralEhNegada(_ArvoreSintetica):
    """O residuo da P1-A.11: os DOIS angulos que os dois revisores
    independentes convergiram contra o mesmo pacote (`99_decisao-
    p1a11.md`) — construtor atribuido a VARIAVEL antes da comparacao
    (achado do codex), e `decode()` sobre receptor NAO LITERAL, nome ou
    chamada (achado do kimi). Autorizado pela arbitragem do Fundador
    (mesmo registro, secao "ARBITRAGEM DO FUNDADOR").
    """

    def test_construtor_atribuido_a_variavel_e_negado(self):
        # A citacao exata do codex: `x = "".join(partes); if resposta
        # == x:` — o EXEMPLO que a P1-A.11 devolveu como NAO-FECHADO.
        caminho = self.escrever(
            "07_p1b/alias_join.py",
            "def usar(resposta, partes):\n"
            '    x = "".join(partes)\n'
            "    if resposta == x:\n"
            "        return 1\n"
            "    return 0\n")
        achados = self.varrer()
        negados = [a.replace("\\", "/") for a in achados["nao_resolvidos"]]
        self.assertTrue(any("alias_join.py" in n for n in negados),
                        f"construtor atribuido a variavel atravessou: "
                        f"{negados}")
        os.remove(caminho)

    def test_decode_sobre_nome_nao_literal_e_negado(self):
        # A citacao exata do kimi: `if r == payload.decode():`.
        caminho = self.escrever(
            "07_p1b/decode_sobre_nome.py",
            "def usar(r, payload):\n"
            "    if r == payload.decode():\n"
            "        return 1\n"
            "    return 0\n")
        achados = self.varrer()
        negados = [a.replace("\\", "/") for a in achados["nao_resolvidos"]]
        self.assertTrue(any("decode_sobre_nome.py" in n for n in negados),
                        f"decode() sobre nome atravessou: {negados}")
        os.remove(caminho)

    def test_base64_encadeado_com_decode_e_negado(self):
        # A citacao exata do kimi: `if r ==
        # base64.b64decode("...").decode():` — o vetor "base64" que o
        # residuo original ja nomeava e que sobreviveu a P1-A.10.
        caminho = self.escrever(
            "07_p1b/base64_decode.py",
            "import base64\n"
            "def usar(r, dado):\n"
            "    if r == base64.b64decode(dado).decode():\n"
            "        return 1\n"
            "    return 0\n")
        achados = self.varrer()
        negados = [a.replace("\\", "/") for a in achados["nao_resolvidos"]]
        self.assertTrue(any("base64_decode.py" in n for n in negados),
                        f"base64...decode() encadeado atravessou: "
                        f"{negados}")
        os.remove(caminho)

    def test_parametro_homonimo_em_funcao_diferente_fica_limpo(self):
        # O falso positivo que a PRIMEIRA tentativa desta correcao
        # produziu, medido e revertido: rastrear por ARQUIVO em vez de
        # por ESCOPO fazia um `join()` legitimo numa funcao marcar o
        # parametro `alvos` de OUTRA funcao, sem relacao nenhuma entre
        # os dois. Duas funcoes no MESMO arquivo, nome de variavel
        # IGUAL, escopos DIFERENTES — a segunda tem de ficar limpa.
        caminho = self.escrever(
            "07_p1b/escopos_nao_vazam.py",
            "def monta_rotulo(coisas):\n"
            '    alvos = "-".join(coisas)\n'
            "    return alvos\n"
            "\n"
            "def esta_vazio(alvos=None):\n"
            "    if alvos is None:\n"
            "        return True\n"
            "    return False\n")
        achados = self.varrer()
        negados = [a.replace("\\", "/") for a in achados["nao_resolvidos"]]
        self.assertFalse(
            any("escopos_nao_vazam.py" in n for n in negados),
            f"parametro homonimo de outra funcao foi negado por engano: "
            f"{negados}")
        os.remove(caminho)

    def test_decode_isolado_nao_semeia_alias(self):
        # Decisao declarada no proprio `_semente_de_alias_nao_resolvido`:
        # `decode()` amplia o construtor DIRETO, mas NAO semeia
        # rastreamento de variavel — `saida.decode(...)` seguido de
        # checar substring no texto e o padrao mais comum de processar
        # saida de subprocesso, e semear com ele inundou o acervo real
        # (medido: 7 achados, revertido). A comparacao aqui e DIRETA
        # (a variavel NAO e comparada, o resultado do decode e usado so
        # para montar `texto`) — deve ficar limpa.
        caminho = self.escrever(
            "07_p1b/decode_nao_semeia.py",
            "def usar(saida, esperado):\n"
            '    texto = saida.decode("utf-8", "replace")\n'
            '    if esperado in texto:\n'
            "        return 1\n"
            "    return 0\n")
        achados = self.varrer()
        negados = [a.replace("\\", "/") for a in achados["nao_resolvidos"]]
        self.assertFalse(
            any("decode_nao_semeia.py" in n for n in negados),
            f"decode() isolado semeou alias por engano: {negados}")
        os.remove(caminho)


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
