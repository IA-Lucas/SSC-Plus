"""A capsula e a auditoria presas por corpus de OUTRA camada — P1-A.3.9.

MECANISMO (b) da FASE 2 da P1-A.3.8: *corpus derivado do proprio dado
que o guarda protege — iterar a lista para provar a lista*. Dois
guardas, e o remedio de ambos e o mesmo, ja executado uma vez pela FASE
1.2 na direcao contraria (P1-A corpus, P0 alvo):

- **`P1A-12`** — `economia.auditar_ambiente`. A remedicao mediu:
  *"`test_economia:74` prova os 'nomes conhecidos' iterando a propria
  `CHAVES_PAYG_CONHECIDAS`: encolher a lista encolhe o corpus"*. E a
  familia do MAJOR #3 na forma exata.
- **`P1A-01`** — `capsula.ambiente_capsula`. A remedicao mediu:
  *"o unico teste e `test_reauditoria_fail_closed`, que ENCENA a
  regressao do filtro. Em operacao o ramo nunca dispara"*, e prescreveu:
  *"prender a lista de proibidos por corpus de outra camada, como a
  FASE 1.2 fez para a P0"*.

  (Nota de medicao: a tabela §4.2 rotula `P1A-01` como mecanismo **(c)**
  enquanto o remedio que ela mesma prescreve e o de **(b)**; a contagem
  agregada da §3.1 — (b)=2, (c)=5 — so fecha se `P1A-01` for (b). Este
  arquivo trata os dois como (b), que e o que o remedio diz.)

## O que se corrige, e o que NAO se pretende corrigir

O ramo de reauditoria de `ambiente_capsula` **e inalcancavel por
construcao**, e isto e medido aqui, nao suposto: o filtro e a reauditoria
usam o MESMO predicado (`_nome_payg`), de modo que nenhum nome sobrevive
ao primeiro para chegar ao segundo. E o gemeo exato do terceiro ramo do
`AdaptadorAssinatura`, medido e declarado CORRETO pela FASE 1.2 da
P1-A.3.8 — e pelo mesmo motivo: transformar a reauditoria em bloqueio do
ambiente RECEBIDO faria toda estacao que exporte uma chave de API parar
de construir a capsula, e o desenho e FILTRAR.

O defeito que sobra, e que este arquivo fecha, e o outro: **nada, do
lado da P1-A, prendia o conteudo da lista ao exercicio da interface
real**. O corpus vem de `ssc_p0.frota.CHAVES_PROIBIDAS` — a lista que a
camada P0 mantem por conta propria.

## O QUE ESTES TESTES NAO COBREM, declarado

- **encolhimento SIMULTANEO das duas listas nao e pego.** O espelho
  compara uma com a outra; duas remocoes casadas passam. O remedio seria
  uma terceira fonte, e inventar uma seria politica nova, nao correcao.
  A limitacao ja estava declarada na FASE 1.2 e continua valendo;
- **nao se afirma que as oito chaves sejam as chaves CERTAS.** O corpus
  mede consistencia entre camadas, jamais suficiencia da politica;
- **nenhum valor de credencial aparece**: os testes usam a `SENTINELA`
  do acervo, que nunca foi credencial;
- **nada aqui prova comportamento de subprocesso real** — `iniciar_em_
  capsula` nao e invocada; o objeto e o ambiente derivado, nao o filho;
- o ramo de reauditoria segue **sem caso que ocorra**: ele e medido como
  inalcancavel, e inducao medida nao e o mesmo que ramo exercido.
"""

import os
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
from apoio import SENTINELA
from capsula import (ViolacaoCapsula, ambiente_capsula,  # noqa: E402
                     exigir_capsula_limpa, verificar_capsula)
from preflight.economia import (CHAVES_PAYG_CONHECIDAS,  # noqa: E402
                                ChavePaygDetectada, _nome_payg,
                                ambiente_sanitizado, auditar_ambiente)
from ssc_p0.frota import CHAVES_PROIBIDAS  # noqa: E402
from ssc_p0.frota import _PADRAO_CHAVE_PAYG as PADRAO_P0  # noqa: E402

# Protegida SO pela lista: o padrao de sufixo nao a alcanca, porque o
# nome nao termina em credencial — termina em CREDENTIALS, que e um
# CAMINHO DE ARQUIVO de credencial. Medido na FASE 1.2 da P1-A.3.8:
# remove-la de CHAVES_PROIBIDAS deixava 793/793 verdes.
SO_PELA_LISTA = "GOOGLE_APPLICATION_CREDENTIALS"

# O corpus. Vem da P0 — a camada que NAO e o alvo destes testes.
CORPUS = tuple(sorted(CHAVES_PROIBIDAS))


class OCorpusVemDaOutraCamada(unittest.TestCase):
    """Se o corpus virasse a propria lista da P1-A, isto aqui reprova."""

    def test_o_corpus_nao_e_a_lista_que_a_p1a_mantem(self):
        # Guarda contra a regressao mais provavel deste arquivo: alguem
        # trocar o import de `ssc_p0.frota` por `preflight.economia`
        # "para simplificar" e devolver a tautologia do MAJOR #3.
        self.assertIsNot(CHAVES_PROIBIDAS, CHAVES_PAYG_CONHECIDAS)
        self.assertEqual({k.lower() for k in CORPUS},
                         set(CHAVES_PAYG_CONHECIDAS))

    def test_o_corpus_tem_alcance_real(self):
        self.assertGreaterEqual(len(CORPUS), 8)

    def test_ha_nome_no_corpus_que_SO_a_lista_protege(self):
        # DISCRIMINADOR. Sem ele os testes abaixo poderiam passar de
        # graca pelo padrao de sufixo, e a lista poderia esvaziar sem
        # ruido nenhum.
        so_lista = [n for n in CORPUS if not PADRAO_P0.search(n)]
        self.assertIn(SO_PELA_LISTA, so_lista)

    def test_as_outras_seguem_cobertas_pelo_padrao(self):
        # A outra metade da medicao: e ela que torna o discriminador
        # acima uma medicao, e nao uma escolha de gosto.
        pelo_padrao = [n for n in CORPUS if PADRAO_P0.search(n)]
        self.assertEqual(len(pelo_padrao), len(CORPUS) - 1)


class ACapsulaFiltraTodoNomeDoCorpus(unittest.TestCase):
    """`P1A-01` — a INTERFACE REAL da capsula, nome por nome do corpus."""

    def test_nenhum_nome_do_corpus_entra_no_ambiente_da_capsula(self):
        for nome in CORPUS:
            with self.subTest(chave=nome):
                dentro = ambiente_capsula({"PATH": "/bin", nome: SENTINELA})
                self.assertNotIn(nome, dentro)
                self.assertEqual(dentro.get("PATH"), "/bin")

    def test_verificar_capsula_acusa_todo_nome_do_corpus(self):
        for nome in CORPUS:
            with self.subTest(chave=nome):
                self.assertEqual(verificar_capsula({nome: SENTINELA}), [nome])

    def test_o_portao_de_entrada_aborta_com_todo_nome_do_corpus(self):
        # `exigir_capsula_limpa` e a PRIMEIRA linha util dos dois runners
        # de preflight: e por ela que "chave visivel dentro da capsula =
        # bloqueio" acontece de fato.
        for nome in CORPUS:
            with self.subTest(chave=nome):
                with self.assertRaises(ViolacaoCapsula) as ctx:
                    exigir_capsula_limpa({"PATH": "/bin", nome: SENTINELA})
                self.assertIn(nome, str(ctx.exception))
                self.assertNotIn(SENTINELA, str(ctx.exception))

    def test_a_chave_protegida_so_pela_lista_e_barrada_nos_tres_pontos(self):
        # O caso cuja remocao era invisivel, exercido nos tres pontos de
        # chamada da capsula — nao na primitiva `_nome_payg`.
        env = {"PATH": "/bin", SO_PELA_LISTA: SENTINELA}
        self.assertNotIn(SO_PELA_LISTA, ambiente_capsula(env))
        self.assertEqual(verificar_capsula(env), [SO_PELA_LISTA])
        with self.assertRaises(ViolacaoCapsula):
            exigir_capsula_limpa(env)

    def test_nome_fora_da_lista_e_do_padrao_atravessa(self):
        # CONTRAPROVA: uma capsula que devolvesse `{}` passaria em tudo
        # acima e destruiria o ambiente do processo filho.
        dentro = ambiente_capsula({"PATH": "/bin", "LANG": "pt_BR"})
        self.assertEqual(dentro, {"PATH": "/bin", "LANG": "pt_BR"})

    def test_a_capsula_nao_muta_o_ambiente_recebido_nem_o_do_processo(self):
        # A decisao da P1-A.2 e explicita: o ambiente global do usuario
        # NAO e alterado; as credenciais apenas nao entram na capsula.
        recebido = {"PATH": "/bin", SO_PELA_LISTA: SENTINELA}
        copia = dict(recebido)
        antes = dict(os.environ)
        ambiente_capsula(recebido)
        self.assertEqual(recebido, copia)
        self.assertEqual(dict(os.environ), antes)


class AAuditoriaAcusaTodoNomeDoCorpus(unittest.TestCase):
    """`P1A-12` — `auditar_ambiente` com corpus que nao e a propria lista."""

    def test_todo_nome_do_corpus_vira_exatamente_uma_violacao(self):
        for nome in CORPUS:
            with self.subTest(chave=nome):
                violacoes = auditar_ambiente({nome: SENTINELA})
                self.assertEqual(len(violacoes), 1)
                self.assertIsInstance(violacoes[0], ChavePaygDetectada)
                self.assertEqual(violacoes[0].alvo, nome)

    def test_nenhuma_violacao_carrega_o_valor(self):
        # Valores NUNCA sao registrados — somente nomes. A `SENTINELA`
        # existe no acervo exatamente para medir isto.
        for nome in CORPUS:
            with self.subTest(chave=nome):
                for violacao in auditar_ambiente({nome: SENTINELA}):
                    self.assertNotIn(SENTINELA, violacao.detalhe)
                    self.assertNotIn(SENTINELA, str(violacao.alvo))

    def test_a_chave_protegida_so_pela_lista_e_acusada(self):
        violacoes = auditar_ambiente({SO_PELA_LISTA: SENTINELA})
        self.assertEqual([v.alvo for v in violacoes], [SO_PELA_LISTA])

    def test_ambiente_sem_chave_do_corpus_nao_gera_violacao(self):
        # CONTRAPROVA: um auditor que acusasse sempre passaria em tudo
        # acima e bloquearia a frota inteira.
        self.assertEqual(auditar_ambiente({"PATH": "/bin",
                                           "LANG": "pt_BR"}), [])


class AReauditoriaEInalcancavelPorConstrucao(unittest.TestCase):
    """Fixa o comportamento CORRETO de `P1A-01`: filtrar, nunca bloquear.

    Medicao, nao afirmacao: o gemeo desta reauditoria — o terceiro ramo
    do `AdaptadorAssinatura` — foi medido e declarado correto pela FASE
    1.2 da P1-A.3.8, com exaustao sobre a mesma lista.
    """

    def test_nenhum_nome_do_corpus_sobrevive_ao_filtro(self):
        # Exaustao: `restantes` e sempre vazio, logo `raise
        # ViolacaoCapsula` na reauditoria e inalcancavel para qualquer
        # entrada — o ramo NAO tem caso que ocorra.
        sobreviventes = [n for n in CORPUS
                         if verificar_capsula(ambiente_capsula(
                             {n: SENTINELA}))]
        self.assertEqual(sobreviventes, [])

    def test_o_filtro_e_a_reauditoria_usam_o_MESMO_predicado(self):
        # A razao estrutural da inalcancabilidade, medida sobre o corpus
        # e sobre nomes que NAO estao nele: se algum dia os dois lados
        # divergirem, este teste fica vermelho e o ramo passa a ter caso.
        for nome in CORPUS + ("api_key", "apiKey", "X_ACCESS_TOKEN",
                              "PATH", "LANG"):
            with self.subTest(chave=nome):
                self.assertEqual(_nome_payg(nome),
                                 bool(verificar_capsula({nome: "v"})))

    def test_a_capsula_e_o_sanitizador_concordam_sobre_o_corpus(self):
        # As duas portas da mesma politica, exercidas com o mesmo corpus
        # de outra camada: divergencia entre elas e regressao.
        for nome in CORPUS:
            with self.subTest(chave=nome):
                env = {"PATH": "/bin", nome: SENTINELA}
                self.assertNotIn(nome, ambiente_capsula(env))
                self.assertNotIn(nome, ambiente_sanitizado(env))


if __name__ == "__main__":
    unittest.main()
