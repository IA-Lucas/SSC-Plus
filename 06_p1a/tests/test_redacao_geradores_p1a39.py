"""Redacao no ponto de chamada dos GERADORES de pacote — SSC+ P1-A.3.9.

MECANISMO (a), segunda metade. `P1A-31` e `P1A-32` cairam na regra dura
com a mesma frase: *"so equivalencia de PRIMITIVA com a canonica
(`RedacaoDosGeradores`); o ponto de chamada nao e varrido nem por AST"*.

MEDIDO nesta missao, e e pior do que a linha dizia: `montar_pacote()` JA
e executado de verdade pelo acervo — `test_pacote_p1a33.py:63`,
`test_correcoes_p1a32.py:584`, `test_pacote_autoinclusao_p1a37.py:82` —
e **nenhum desses arquivos olha o texto produzido a procura de PII**.
Busca por `USUARIO`, `forma_8_3` ou `CAMINHO-LOCAL` nos tres devolve
zero. O pacote e montado, hasheado, comparado consigo mesmo e enviado ao
revisor; o que ninguem faz e perguntar se ele saiu limpo.

## O CASO QUE OCORRE, medido e nao suposto

Os geradores embutem `06_p1a/preflight_capsula.py` INTEIRO, e aquele
fonte carrega um caminho local literal (`_GITBASH`). Medido nesta
missao, montando os QUATRO de verdade com a redacao neutralizada: os
quatro pacotes CRUS carregam `E:\\LucasIA`, e os quatro pacotes limpos
nao. O proprio docstring de `pacote_p1a31._redigir` ja dizia isso; o que
faltava era exercer.

O DISCRIMINADOR e medido a cada corrida, nao herdado: cada gerador roda
DUAS vezes — uma normal e uma com a redacao NEUTRALIZADA. A corrida
neutralizada precisa carregar o caminho local; a normal precisa nao
carregar. Sem a primeira metade, um gerador que produzisse texto vazio
passaria.

ACHADO DESTA MISSAO, medido ao exercer. A metade `<USUARIO>` da redacao
dos geradores **nao tem caso que ocorra hoje**: os quatro pacotes CRUS
nao carregam o nome do usuario em forma nenhuma, porque sao montados a
partir de conteudo VERSIONADO e `ZeroPiiNosArtefatos` mantem o
versionado livre dele. O marcador `<USUARIO>` que aparece no pacote
limpo vem de LITERAIS nos fontes embutidos (docstrings que citam
`<USUARIO>`), nao da redacao — um teste que procurasse o marcador para
provar a redacao estaria provando o vizinho. A metade fica como defesa
em profundidade, presa a canonica por `RedacaoDosGeradores`, e o fato
esta gravado num teste que fica vermelho no dia em que deixar de valer.

## O corpus tambem aqui e descoberto

Todo modulo do acervo que chama a redacao e, ou um escritor de evidencia
JSON com prova em `test_redacao_operacao_p1a39.py`, ou um gerador com
prova aqui. `TodoModuloQueRedigeTemProva` fecha a soma: nao ha terceira
gaveta onde uma copia possa ficar para tras — que e o mecanismo dos
achados 7, 10 e 14.

Os auxiliares vem importados daquele arquivo, nunca copiados: duplicar
`_sem_pii` aqui seria o defeito que estes dois arquivos existem para
fechar.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nao se afirma que o pacote esteja completo nem correto** — so que
  nao carrega as tres formas que a canonica conhece;
- outra PII (nome de maquina, IP, e-mail) nao e alvo deste mecanismo e
  nao e verificada;
- `autoinclusao.secao_do_gerador` e exercida SOMENTE pelo caminho de
  `pacote_p1a37`, o unico chamador de producao; o parametro
  `redigir=None` continua existindo e continua devolvendo fonte cru para
  quem o omitir — o guarda abaixo exige que nenhum chamador de producao
  o omita, nao que a assinatura mude;
- os geradores leem commits FIXOS do repositorio: sem git, ou com o
  commit ausente, os testes sao pulados em vez de mentir.
"""

import ast
import importlib.util
import inspect
import os
import subprocess
import sys
import unittest
from unittest import mock

import apoio  # noqa: F401  (insere 06_p1a no sys.path)
from test_redacao_operacao_p1a39 import (EXERCIDOS,  # noqa: E402
                                         _e_chamada_de_redacao,
                                         _escritores_descobertos,
                                         _RAIZES_DO_ACERVO, _sem_pii)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

import contencao  # noqa: E402

# `pacote_p1a37` monta o pacote de um par de commits declarado; os
# demais tem o alvo fixo dentro do proprio fonte. Os dois SHA sao os de
# `test_pacote_autoinclusao_p1a37.py`, para nao criar uma segunda
# declaracao que possa divergir.
_BASE_P1A37 = "30107bd"
_ALVO_P1A37 = "7d25bc7"

# Gerador -> nome do atributo de redacao a neutralizar na medicao do
# discriminador. `pacote_p1a37` usa a canonica importada, e nao uma
# copia local: por isso o nome difere.
GERADORES = {
    "pacote_p1a31": "_redigir",
    "pacote_p1a33": "_redigir",
    "pacote_p1a36": "_redigir",
    "pacote_p1a37": "redigir",
    "pacote_p1a10": "redigir",
}

# Modulo que redige mas nao monta pacote proprio: e exercido pelo
# caminho do unico chamador de producao que tem.
TRANSITIVOS = {"autoinclusao": "pacote_p1a37"}


def _tem_commit(sha: str) -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", f"{sha}^{{commit}}"],
                          cwd=_RAIZ_REAL, capture_output=True).returncode == 0


def _carregar(nome: str):
    caminho = os.path.join(_DIR_EVID, f"{nome}.py")
    spec = importlib.util.spec_from_file_location(f"p1a39_{nome}", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _montar(modulo):
    """Chama `montar_pacote` com a aridade que o gerador declara."""
    if len(inspect.signature(modulo.montar_pacote).parameters) == 0:
        return modulo.montar_pacote()
    return modulo.montar_pacote(_BASE_P1A37, _ALVO_P1A37)


def _modulos_que_redigem() -> set:
    """Todo modulo do acervo com uma chamada de redacao — por AST."""
    achados = set()
    for raiz, ignorados in _RAIZES_DO_ACERVO:
        if not os.path.isdir(raiz):
            continue
        for nome in sorted(os.listdir(raiz)):
            caminho = os.path.join(raiz, nome)
            if not os.path.isfile(caminho) or not nome.endswith(".py"):
                continue
            if nome in ignorados:
                continue
            with open(caminho, encoding="utf-8") as f:
                try:
                    arvore = ast.parse(f.read())
                except SyntaxError:
                    continue
            if any(_e_chamada_de_redacao(no) for no in ast.walk(arvore)):
                achados.add(nome[:-3])
    return achados


class TodoModuloQueRedigeTemProva(unittest.TestCase):
    """Fecha a soma: nao ha gaveta sem dono."""

    def test_a_uniao_dos_dois_corpora_cobre_todo_modulo_que_redige(self):
        todos = _modulos_que_redigem()
        cobertos = set(EXERCIDOS) | set(GERADORES) | set(TRANSITIVOS)
        orfaos = sorted(todos - cobertos)
        self.assertEqual(
            orfaos, [],
            f"modulo que redige sem prova comportamental: {orfaos}. Uma "
            "copia de redacao que ninguem exercita e o mecanismo dos "
            "achados 7, 10 e 14 — a copia que fica para tras")

    def test_nenhum_gerador_registrado_sumiu_da_arvore(self):
        todos = _modulos_que_redigem()
        self.assertEqual(sorted(set(GERADORES) - todos), [])
        self.assertEqual(sorted(set(TRANSITIVOS) - todos), [])

    def test_os_dois_corpora_nao_se_sobrepoem(self):
        # Escritor de JSON e gerador de pacote sao disjuntos por
        # construcao; sobreposicao significaria que a descoberta perdeu a
        # distincao e um dos dois lados deixou de medir o que diz medir.
        escritores = {nome for nome, _ in _escritores_descobertos()}
        self.assertEqual(sorted(escritores & set(GERADORES)), [])

    def test_o_alcance_da_varredura_e_real(self):
        self.assertGreaterEqual(len(_modulos_que_redigem()), 12)


@unittest.skipUnless(_tem_commit(_ALVO_P1A37) and _tem_commit(_BASE_P1A37),
                     "repositorio git ou commits do par indisponiveis")
class OsGeradoresProduzemPacoteRedigido(unittest.TestCase):
    """`montar_pacote()` REAL de cada gerador, e o TEXTO produzido."""

    @classmethod
    def setUpClass(cls):
        cls.limpos = {}
        cls.crus = {}
        for nome, atributo in sorted(GERADORES.items()):
            modulo = _carregar(nome)
            cls.limpos[nome] = _montar(modulo)
            with mock.patch.object(modulo, atributo, lambda t: t):
                cls.crus[nome] = _montar(modulo)

    def test_o_pacote_de_cada_gerador_nao_carrega_pii(self):
        for nome in sorted(GERADORES):
            with self.subTest(gerador=nome):
                _sem_pii(self, self.limpos[nome], nome)

    def test_sem_a_redacao_o_MESMO_pacote_carrega_caminho_local(self):
        # DISCRIMINADOR medido a cada corrida: e a reversao vermelha
        # embutida. Sem esta metade, um gerador que devolvesse texto
        # vazio passaria no teste acima. Os QUATRO pacotes CRUS carregam
        # `E:\LucasIA` — medido, nao presumido.
        for nome in sorted(GERADORES):
            with self.subTest(gerador=nome):
                self.assertTrue(
                    any(p in self.crus[nome]
                        for p in contencao.PREFIXOS_DE_CAMINHO_LOCAL),
                    f"{nome}: o pacote CRU nao carrega caminho local — a "
                    "prova de redacao perdeu o objeto")

    def test_a_redacao_deixou_marcador_onde_havia_caminho_local(self):
        for nome in sorted(GERADORES):
            with self.subTest(gerador=nome):
                self.assertIn("<CAMINHO-LOCAL>", self.limpos[nome])

    def test_a_metade_de_USUARIO_nao_tem_caso_que_ocorre_hoje(self):
        # MEDICAO, e nao propriedade desejada. Os quatro pacotes CRUS
        # nao carregam o nome do usuario em forma nenhuma: eles sao
        # montados a partir de conteudo VERSIONADO, e
        # `ZeroPiiNosArtefatos` (test_estabilizacao_p1a1.py) mantem o
        # versionado livre do usuario local. Logo a metade `<USUARIO>`
        # da redacao dos geradores e DEFESA EM PROFUNDIDADE: correta,
        # equivalente a canonica (`RedacaoDosGeradores`), e sem caso que
        # ocorra hoje para exerce-la.
        #
        # Registrado como teste, e nao como comentario, porque o dia em
        # que isto ficar vermelho e o dia em que a metade passa a ter
        # caso — e ai ela precisa de prova propria, nao desta nota.
        usuario = contencao._USUARIO_LOCAL
        curto = contencao.forma_8_3(usuario)
        for nome in sorted(GERADORES):
            with self.subTest(gerador=nome):
                cru = self.crus[nome]
                self.assertNotIn(usuario, cru)
                self.assertNotIn(curto, cru)

    def test_o_pacote_nao_encolheu_a_ponto_de_nao_provar_nada(self):
        # Guarda anti-teste-vazio, no padrao de
        # `ZeroSegredoNosArtefatos.test_a_varredura_realmente_le_arquivos`.
        for nome in sorted(GERADORES):
            with self.subTest(gerador=nome):
                self.assertGreater(len(self.limpos[nome]), 50_000)


class AAutoinclusaoNaoEntregaFonteCru(unittest.TestCase):
    """`secao_do_gerador(redigir=None)` devolve fonte CRU — por desenho.

    O default existe para teste, e o proprio docstring o declara. O risco
    e o de sempre: um chamador de producao que o omita publica o fonte do
    gerador sem redacao. O guarda e sobre os CHAMADORES, nao sobre a
    assinatura.
    """

    def _chamadas_de_producao(self):
        for nome in sorted(GERADORES):
            caminho = os.path.join(_DIR_EVID, f"{nome}.py")
            with open(caminho, encoding="utf-8") as f:
                arvore = ast.parse(f.read())
            for no in ast.walk(arvore):
                if (isinstance(no, ast.Call)
                        and isinstance(no.func, ast.Name)
                        and no.func.id == "secao_do_gerador"):
                    yield nome, no

    def test_todo_chamador_de_producao_passa_a_redacao(self):
        chamadas = list(self._chamadas_de_producao())
        self.assertTrue(chamadas, "nenhum chamador de secao_do_gerador — a "
                                  "autoinclusao do MAJOR #5 sumiu")
        for nome, no in chamadas:
            with self.subTest(gerador=nome):
                passou = (len(no.args) >= 2
                          or any(k.arg == "redigir" for k in no.keywords))
                self.assertTrue(
                    passou,
                    f"{nome}: secao_do_gerador sem redacao — o fonte do "
                    "gerador vai CRU para o revisor")

    def test_sem_redacao_a_secao_sai_crua_de_fato(self):
        # Contraprova do guarda acima: se `redigir=None` ja redigisse, o
        # guarda nao protegeria nada e poderia sumir sem custo. O alvo e
        # `preflight_capsula.py` porque ele carrega um caminho local
        # literal no proprio fonte (`_GITBASH`) — medido, nao presumido.
        import autoinclusao
        alvo = os.path.join(_DIR_P1A, "preflight_capsula.py")
        crua = autoinclusao.secao_do_gerador(alvo)
        limpa = autoinclusao.secao_do_gerador(alvo, contencao.redigir)
        self.assertTrue(any(p in crua
                            for p in contencao.PREFIXOS_DE_CAMINHO_LOCAL),
                        "o alvo deixou de carregar caminho local — a "
                        "contraprova perdeu o objeto")
        self.assertNotIn("<CAMINHO-LOCAL>", crua)
        self.assertIn("<CAMINHO-LOCAL>", limpa)


if __name__ == "__main__":
    unittest.main()
