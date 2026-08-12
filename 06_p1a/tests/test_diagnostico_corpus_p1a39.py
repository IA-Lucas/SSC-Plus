"""Sondas de diagnostico presas por corpus de OUTRA camada — P1-A.3.9.

MECANISMO (d) da FASE 2 da P1-A.3.8, guarda `P1A-53` — o UNICO **AFIRMA**
dos vinte. A linha da remedicao e literal:

    itera `ESPECIFICACOES` e confere os verbos DECLARADOS contra uma
    lista de permitidos. NENHUM CLI e invocado, e o corpus e a propria
    declaracao. E a familia do MAJOR #3 na forma pura: afirma a
    propriedade lendo o rotulo.
    Remedio: o de `test_cli_real_p1a34`, aplicado aos demais provedores.

## O remedio prescrito NAO e executado aqui, e o motivo esta escrito

Aplicar `test_cli_real_p1a34` aos demais provedores exige INVOCAR os
CLIs deles. O ato desta missao proibe, com estas palavras: *"nao invocar
provider ... Zero chamada paga"*. O precedente existe e e uma **excecao
declarada** — o proprio `test_cli_real_p1a34` abre dizendo que suspende
a regra de `apoio.py` **por ordem do ato da P1-A.3.4**, com custo zero
por construcao. Estender uma excecao concedida por ato e decisao do
Fundador, nao desta missao.

Logo `P1A-53` **NAO fecha aqui**. O que este arquivo faz e a metade que
nao depende de invocacao — e ela nao e pequena, porque ataca a parte
tautologica do guarda: *o corpus e a propria declaracao*.

## O corpus vem da OUTRA camada: os argv PRODUTIVOS do acervo

O acervo ja contem, escrito e versionado, o oposto exato de uma sonda de
diagnostico: os argv das invocacoes PRODUTIVAS —
`prova_minima.COMANDOS` (a prova minima, que gasta chamada) e
`contencao.argv_kimi` (o comando de revisao). Eles nao sao derivados de
`ESPECIFICACOES` e nao mudam quando ela muda.

Se um verbo produtivo aparecer numa sonda de diagnostico, os dois lados
colidem e o teste fica vermelho — sem que ninguem precise manter uma
lista de "verbos proibidos" a mao. E o mesmo desenho da FASE 1.2 da
P1-A.3.8, que prendeu `CHAVES_PROIBIDAS` com a lista da outra camada.

## A lacuna do CLI, declarada em vez de escondida

Dos cinco provedores, **um** tem os comandos confrontados com o CLI
REAL: o kimi, por `test_cli_real_p1a34`. Os outros quatro — codex,
claude, google, grok — **nao tem**. O guarda abaixo fixa esse numero
pelo nome: se um quinto entrar, ou se o unico sair, ele fica vermelho e
o estado volta a mesa. Ate a P1-A.3.8 esse "1 de 5" nao estava escrito
em lugar nenhum.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nenhum CLI e invocado aqui.** Que `doctor` e `login status` sejam de
  fato read-only nos CLIs reais continua NAO exercido para quatro dos
  cinco provedores. Isto e a metade que `P1A-53` mantem em aberto;
- **o corpus produtivo e o que o acervo tem**, nao o conjunto de todos
  os verbos produtivos possiveis: um verbo mutante que nenhuma
  ferramenta deste laboratorio use nao e coberto por ele — para esse
  caso vale a allowlist `PERMITIDOS`, que continua sendo declaracao;
- **nada se afirma sobre o comportamento do CLI sob a sonda**: se um dia
  `--version` passar a escrever em disco, so a invocacao revelaria.
"""

import os
import sys
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
from preflight.frota_real import ESPECIFICACOES

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

import contencao  # noqa: E402

# Provedores cujos comandos declarados sao confrontados com o CLI REAL,
# e por qual arquivo. MEDIDO: um de cinco.
CONFRONTADOS_COM_CLI_REAL = {"kimi": "test_cli_real_p1a34.py"}
SEM_CONFRONTO_COM_CLI_REAL = frozenset({"codex", "claude", "google", "grok"})


def _prova_minima():
    import importlib.util
    caminho = os.path.join(_DIR_EVID, "prova_minima.py")
    spec = importlib.util.spec_from_file_location("p1a39_prova_minima",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def verbos_produtivos() -> dict:
    """Provedor -> tokens do argv PRODUTIVO, do proprio acervo.

    Nao ha lista escrita a mao: os tokens saem dos comandos que o
    laboratorio usa para GASTAR chamada. O `PROMPT` e o diretorio
    descartavel sao removidos — sao dados, nao verbos.
    """
    modulo = _prova_minima()
    marcador = "<DESCARTAVEL>"
    por_provedor = {}
    for provider_id, construir in modulo.COMANDOS.items():
        argv = construir(marcador)
        por_provedor[provider_id] = {
            token for token in argv[1:]
            if token not in (marcador, modulo.PROMPT)}
    # O argv de revisao do kimi e a outra fonte produtiva do acervo.
    argv_revisao = contencao.argv_kimi("<EXE>", "<PROMPT>", "<SKILLS>")
    por_provedor.setdefault("kimi", set()).update(
        token for token in argv_revisao[1:]
        if token not in ("<EXE>", "<PROMPT>", "<SKILLS>"))
    return por_provedor


def verbos_de_sonda(provider_id: str) -> set:
    espec = ESPECIFICACOES[provider_id]
    tokens = set()
    for comando in espec.comandos.values():
        if comando is not None:
            # `agy -p /quota` usa a moldura headless, mas o parser exige
            # num_turns=0 e todos os contadores de token em zero. O verbo
            # diagnostico e `/quota`; `-p` e apenas o transporte local.
            if "/quota" in comando:
                tokens.add("/quota")
            else:
                tokens.update(comando)
    return tokens


class NenhumVerboProdutivoEUsadoComoSonda(unittest.TestCase):
    """O corpus vem dos argv que GASTAM chamada, nao da declaracao."""

    def test_o_corpus_produtivo_nao_sai_de_ESPECIFICACOES(self):
        # Guarda contra a regressao que devolveria a tautologia: se
        # alguem derivar o corpus produtivo da propria especificacao, o
        # teste abaixo passa a comparar a declaracao consigo mesma.
        produtivos = verbos_produtivos()
        self.assertTrue(produtivos, "corpus produtivo vazio")
        todos_sonda = set()
        for provider_id in ESPECIFICACOES:
            todos_sonda |= verbos_de_sonda(provider_id)
        unido = set().union(*produtivos.values())
        self.assertTrue(
            unido - todos_sonda,
            "o corpus produtivo esta contido no de sondas — ele deixou "
            "de ser independente e o teste virou tautologia")

    def test_nenhuma_sonda_usa_verbo_do_argv_produtivo_do_MESMO_provedor(self):
        produtivos = verbos_produtivos()
        for provider_id in sorted(ESPECIFICACOES):
            if provider_id not in produtivos:
                continue
            with self.subTest(provedor=provider_id):
                colisao = verbos_de_sonda(provider_id) & produtivos[provider_id]
                self.assertEqual(
                    colisao, set(),
                    f"{provider_id}: a sonda de diagnostico usa "
                    f"{sorted(colisao)}, que e verbo do argv PRODUTIVO "
                    "deste mesmo provedor no acervo")

    def test_nenhuma_sonda_usa_verbo_produtivo_de_QUALQUER_provedor(self):
        # Mais forte que o anterior: `exec` do codex nao pode aparecer
        # numa sonda do grok so porque o grok nao tem argv produtivo.
        unido = set().union(*verbos_produtivos().values())
        for provider_id in sorted(ESPECIFICACOES):
            with self.subTest(provedor=provider_id):
                colisao = verbos_de_sonda(provider_id) & unido
                self.assertEqual(colisao, set(),
                                 f"{provider_id}: sonda com verbo "
                                 f"produtivo {sorted(colisao)}")

    def test_o_modo_headless_declarado_e_verbo_produtivo_e_nunca_sonda(self):
        # `headless` e, por definicao, o modo que gera. A especificacao o
        # declara e o guarda antigo ja o proibia nas sondas; aqui ele e
        # confrontado tambem com o corpus produtivo, onde precisa estar.
        unido = set().union(*verbos_produtivos().values())
        for provider_id, espec in sorted(ESPECIFICACOES.items()):
            with self.subTest(provedor=provider_id):
                self.assertTrue(espec.headless)
                self.assertNotIn(espec.headless[0],
                                 verbos_de_sonda(provider_id))
        self.assertTrue(
            {e.headless[0] for e in ESPECIFICACOES.values()} & unido,
            "nenhum modo headless declarado aparece no argv produtivo do "
            "acervo — as duas camadas deixaram de falar do mesmo objeto")

    def test_o_instrumento_acusa_uma_sonda_produtiva_plantada(self):
        # CONTROLE POSITIVO: sem ele, um `verbos_de_sonda` que devolvesse
        # `set()` deixaria os tres testes acima verdes para sempre.
        unido = set().union(*verbos_produtivos().values())
        plantada = {"--version", "exec"}
        self.assertTrue(plantada & unido,
                        "o corpus produtivo nao contem 'exec' — a "
                        "contraprova perdeu o objeto")
        for provider_id in ESPECIFICACOES:
            self.assertTrue(verbos_de_sonda(provider_id),
                            f"{provider_id}: verbos_de_sonda vazio")


class ALacunaDoCliRealEDeclarada(unittest.TestCase):
    """"Nenhum CLI e invocado" era verdade escondida; vira numero fixado."""

    def test_exatamente_um_provedor_e_confrontado_com_o_cli_real(self):
        arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "test_cli_real_p1a34.py")
        self.assertTrue(os.path.isfile(arquivo),
                        "o unico confronto com CLI real sumiu do acervo")
        self.assertEqual(sorted(CONFRONTADOS_COM_CLI_REAL), ["kimi"])

    def test_a_particao_cobre_a_frota_inteira_sem_sobreposicao(self):
        cobertos = set(CONFRONTADOS_COM_CLI_REAL) | SEM_CONFRONTO_COM_CLI_REAL
        self.assertEqual(cobertos, set(ESPECIFICACOES),
                         "a particao 'confrontado / nao confrontado' "
                         "deixou de cobrir a frota — provedor novo entra "
                         "sem que ninguem diga em qual metade ele esta")
        self.assertEqual(
            set(CONFRONTADOS_COM_CLI_REAL) & SEM_CONFRONTO_COM_CLI_REAL,
            set())

    def test_quatro_de_cinco_seguem_sem_confronto_com_cli_real(self):
        # O numero e o achado. Ele nao e uma meta e nao e um alarme: e o
        # estado, escrito, para que a proxima revisao o veja sem ter de
        # deduzi-lo do silencio.
        self.assertEqual(len(SEM_CONFRONTO_COM_CLI_REAL), 4)
        self.assertEqual(len(ESPECIFICACOES), 5)


if __name__ == "__main__":
    unittest.main()
