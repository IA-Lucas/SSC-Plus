"""`estados._NOMES` presa pelos helpers que nomeiam as maquinas — P1-A.3.9.

ORDEM 4 do ato, primeira metade. A varredura [15/N] mediu
`estados._NOMES` como **SOLTA — 3 de 3 sem exercicio**.

## O DIAGNOSTICO: nao e lista sem teste, e declaracao MORTA

`_NOMES = {"sessao": SESSAO, "workunit": WORKUNIT, "attempt": ATTEMPT}`
**nao e lida em lugar nenhum do repositorio**. Nao ha um unico
`_NOMES[...]` fora da propria linha que a define — nem em `estados.py`,
nem no `kernel`, nem na P1-A. E o segundo caso do padrao que
`ESTADOS_ATTEMPT` mostrou na `[17/N]`: uma declaracao que descreve o
sistema sem governar nada.

Aqui ele e mais agudo, porque `_NOMES` nao e sequer enum de contrato: e
uma tabela de consulta que ninguem consulta. **O remedio de verdade seria
apaga-la ou liga-la** — as duas coisas mudam producao, e por isso ficam
REGISTRADAS e nao feitas nesta correcao de guarda. O que este arquivo faz
e menor e honesto: impedir que ela apodreca em silencio.

## CORPUS DE OUTRA CAMADA: os helpers publicos

O conjunto esperado de nomes sai dos **helpers `transitar_*` do proprio
modulo**, descobertos por introspecao — nao de `_NOMES`:

    {nome depois de "transitar_" para todo atributo do modulo}

E outra camada porque nao muda quando `_NOMES` muda. Encolher `_NOMES`
deixa o mapa menor que o conjunto de helpers, e fica vermelho. Acrescentar
um `transitar_x` sem entrada em `_NOMES` tambem.

## O CASO QUE OCORRE, e o vizinho recusado

Nao existe caso que ocorra: `_NOMES` nao esta em caminho de operacao
nenhum, e afirmar o contrario seria a mentira que a regra (a) proibe. O
que se exerce e a EQUIVALENCIA que o mapa afirma — que
`_NOMES["sessao"]` e a MESMA tabela que `transitar_sessao` usa —, e essa
equivalencia e exercida pelo comportamento das duas rotas sobre os mesmos
pares, nunca por identidade de objeto.

Comparar `_NOMES["sessao"] is estados.SESSAO` seria o vizinho: passaria
com uma tabela errada desde que fosse o mesmo objeto errado.

## O QUE ESTE ARQUIVO NAO COBRE, declarado

- **nao liga `_NOMES` a producao.** Ela continua sem consumidor; o guarda
  impede divergencia, nao ressuscita a estrutura;
- **nao afirma que as tres maquinas sejam as CERTAS**, nem que devam ser
  tres;
- **`ATTEMPT_RETOMADA` nao tem entrada em `_NOMES`** e este arquivo NAO
  reclama disso: `marcar_orfao` nao e um `transitar_*`, entao o espelho
  nao o exige. Se a retomada virar um `transitar_orfao`, o espelho passa
  a exigir — e e essa a intencao;
- **remocao SIMULTANEA da entrada e do helper** passa;
- **ACRESCIMO de par as tabelas nao e medido** — so a correspondencia
  nome -> maquina.
"""

import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
from ssc_p0 import estados

# Pares LEGAIS e ILEGAIS escritos a mao, um por maquina. Nao saem de
# `_NOMES` nem das tabelas: se saissem, encolher a estrutura encolheria o
# corpus junto — a tautologia do MAJOR #3.
CASOS = {
    "sessao": {"legal": ("ativa", "suspensa"), "ilegal": ("encerrada", "ativa")},
    "workunit": {"legal": ("proposta", "aguardando-aprovacao"),
                 "ilegal": ("concluida", "proposta")},
    "attempt": {"legal": ("criado", "despachado"),
                "ilegal": ("criado", "concluido")},
}


def _nomes_dos_helpers() -> set:
    """Nomes de maquina que o modulo EXPOE — corpus independente do mapa."""
    return {a[len("transitar_"):] for a in dir(estados)
            if a.startswith("transitar_")}


class OMapaCobreExatamenteAsMaquinasExpostas(unittest.TestCase):

    def test_as_chaves_do_mapa_sao_as_dos_helpers(self):
        # Falha nos dois sentidos: chave removida do mapa, ou helper novo
        # sem entrada nele.
        self.assertEqual(set(estados._NOMES), _nomes_dos_helpers())

    def test_os_helpers_existem_de_verdade(self):
        # Guarda anti-espelho-vazio: sem helpers, a igualdade acima
        # ficaria verde com um mapa vazio.
        self.assertGreaterEqual(len(_nomes_dos_helpers()), 3)
        for nome in ("sessao", "workunit", "attempt"):
            with self.subTest(maquina=nome):
                self.assertTrue(callable(getattr(estados, f"transitar_{nome}")))


class CadaNomeApontaParaAMaquinaQueOHelperUsa(unittest.TestCase):
    """A equivalencia exercida por COMPORTAMENTO, nao por identidade."""

    def _confere(self, nome):
        tabela = estados._NOMES[nome]          # some se a chave sair: vermelho
        helper = getattr(estados, f"transitar_{nome}")
        de, para = CASOS[nome]["legal"]
        self.assertEqual(estados.transitar(tabela, de, para, nome), para)
        self.assertEqual(helper(de, para), para)
        de_mau, para_mau = CASOS[nome]["ilegal"]
        with self.assertRaises(estados.TransicaoIlegal):
            estados.transitar(tabela, de_mau, para_mau, nome)
        with self.assertRaises(estados.TransicaoIlegal):
            helper(de_mau, para_mau)

    def test_sessao(self):
        self._confere("sessao")

    def test_workunit(self):
        self._confere("workunit")

    def test_attempt(self):
        self._confere("attempt")

    def test_as_tres_maquinas_sao_DISTINTAS(self):
        # CONTRAPROVA: um mapa que apontasse os tres nomes para a MESMA
        # tabela passaria em tudo acima, porque cada par legal so e
        # exercido contra a sua propria maquina. Aqui isso morre.
        tabelas = [estados._NOMES[n] for n in ("sessao", "workunit", "attempt")]
        for i, a in enumerate(tabelas):
            for b in tabelas[i + 1:]:
                self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
