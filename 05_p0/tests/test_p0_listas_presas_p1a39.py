"""Listas de constante da P0 presas pelo CONSUMIDOR real — P1-A.3.9.

ORDEM EXTRA do ato desta missao: *"o guarda de CHAVES_PROIBIDAS ja foi
corrigido com corpus de outra camada. Verificar se o mesmo padrao —
lista que nada prende — existe em outras listas de constante do
repositorio. Remover um item e ver se a suite fica verde E O TESTE QUE
PEGA ISSO."*

A varredura foi feita num CLONE do repositorio, nunca na arvore viva:
para cada lista candidata, removeu-se UM item e rodaram-se as DUAS
suites inteiras. Lista cuja remocao deixa tudo verde e uma lista que
NADA PRENDE — o defeito vivo 2 da P1-A.3.8, em que remover
`GOOGLE_APPLICATION_CREDENTIALS` deixava 793/793 verdes.

## As duas listas SOLTAS da camada P0, medidas

| lista | item removido | vermelhos ANTES desta correcao |
|---|---|---|
| `contratos.AUTH_MODES` | `desconhecido` | **0** |
| `estados.TERMINAIS_WORK_UNIT` | `cancelada` | **0** |

E o que cada remocao custava, em comportamento e nao em abstrato:

- **`AUTH_MODES` sem `desconhecido`**: o valor deixa de ser aceito por
  `FleetEntry.validate`, e com isso o ramo `auth_mode desconhecido =
  DENY` de `frota.verificar_economia` fica INALCANCAVEL — a regra
  fail-closed que existe justamente para o canal nao identificado
  deixaria de ter entrada possivel, sem um unico teste vermelho;
- **`TERMINAIS_WORK_UNIT` sem `cancelada`**: `estados.WORKUNIT` e
  montada como *"qualquer NAO-terminal -> cancelada"*. Tirar um estado
  de `TERMINAIS` acrescenta transicoes SAINDO dele — com `concluida`
  fora da lista, uma WorkUnit **concluida poderia ser cancelada**. A
  tabela cresce em silencio, e crescer e a direcao perigosa.

## REVERSAO VERMELHA MEDIDA (um mutante por vez, suite P0 inteira)

Verde de partida: **315/315 OK**. Cada mutante foi aplicado sozinho, a
suite inteira rodada, e o mutante revertido antes do proximo.

| mutante | vermelhos ANTES | vermelhos DEPOIS |
|---|---|---|
| `AUTH_MODES` sem `desconhecido` | 0 | **1** |
| `TERMINAIS_WORK_UNIT` sem `cancelada` | 0 | **3** |
| `TERMINAIS_WORK_UNIT` sem `concluida` | 1 | **4** |

REFINAMENTO MEDIDO, contra o que a varredura sugeria: a lista
`TERMINAIS_WORK_UNIT` era **meio solta**, nao solta. A varredura remove
o ULTIMO item, e o ultimo era `cancelada` — esse nao prendia nada. Tirar
`concluida` ja deixava vermelho um teste ANTERIOR a esta missao
(`test_estados.test_cancelamento_de_qualquer_estado_nao_terminal`). O
saldo de 0 medido na varredura vale para o item removido, jamais para a
lista toda, e afirmar o contrario seria a mesma troca de "alcance" por
"exercicio" que o achado N1 pegou.

## O que estes testes fazem, e por que nao e a lista provando a lista

Cada membro e exercido pelo CONSUMIDOR REAL — `FleetEntry.validate` e
`verificar_economia` para o primeiro, `estados.transitar` para o
segundo —, e a propriedade afirmada e sobre o EFEITO, nao sobre a
pertinencia: *nao sai transicao de estado terminal*, *canal nao
identificado e negado*. Iterar a lista para conferir que ela contem o
que contem seria a tautologia do MAJOR #3 outra vez.

## O QUE ESTES TESTES NAO COBREM, declarado

- **remocao SIMULTANEA de um membro e do seu consumidor** nao e pega:
  quem apagar o ramo `desconhecido = DENY` junto com o valor passa. E o
  mesmo limite declarado na FASE 1.2 da P1-A.3.8, e o remedio seria uma
  terceira fonte que este laboratorio nao tem;
- **nao se afirma que os membros sejam os CERTOS**: mede-se que cada um
  tem efeito exercido, jamais que a politica esteja completa;
- **a varredura cobriu 24 listas de constante**, escolhidas por
  carregarem politica; as demais constantes do repositorio nao foram
  varridas e nao ha afirmacao sobre elas;
- **a varredura remove UM item por vez, o ULTIMO**: remocoes multiplas e
  ACRESCIMOS nao foram medidos, e acrescimo e a direcao em que uma
  allowlist se afrouxa.
"""

import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)
from ssc_p0 import contratos as ct
from ssc_p0 import estados
from ssc_p0.contratos import FalhaContrato
from ssc_p0.frota import verificar_economia

# Valor ficticio; nunca foi credencial.
SENTINELA = "SENTINELA-VALOR-FICTICIO-NAO-E-CREDENCIAL"


def _entrada(**sobre) -> ct.FleetEntry:
    campos = {"provider_id": "prov-a", "model_id": "modelo-x",
              "capability_profile": {}, "auth_mode": "subscription-oauth",
              "billing_mode": "subscription", "quota_state": "disponivel",
              "quota_reset": None, "automation_permission": "allow",
              "terms_profile": {"oauth_profile": "oauth:prov-a"},
              "variable_cost": 0, "papeis_preferidos": [],
              "canal_oficial": True}
    campos.update(sobre)
    return ct.FleetEntry(**campos)


class TodoAuthModeEAceitoEJulgado(unittest.TestCase):
    """`AUTH_MODES` presa por `FleetEntry.validate` + `verificar_economia`."""

    def test_todo_membro_e_aceito_pela_validacao_do_contrato(self):
        for modo in sorted(ct.AUTH_MODES):
            with self.subTest(auth_mode=modo):
                _entrada(auth_mode=modo).validate()

    def test_valor_fora_da_lista_e_recusado_pela_validacao(self):
        # CONTRAPROVA: sem ela, uma validacao que aceitasse tudo passaria
        # no teste acima e o enum seria decoracao.
        with self.assertRaises(FalhaContrato):
            _entrada(auth_mode="modo-que-nao-existe").validate()

    def test_todo_membro_recebe_veredito_economico_definido(self):
        # O consumidor REAL. Cada modo produz veto ou nao-veto; nenhum
        # cai num limbo silencioso.
        for modo in sorted(ct.AUTH_MODES):
            with self.subTest(auth_mode=modo):
                vetos = verificar_economia(_entrada(auth_mode=modo))
                self.assertIsInstance(vetos, list)

    def test_o_canal_nao_identificado_e_NEGADO(self):
        # O caso cuja remocao era invisivel. `desconhecido` existe na
        # lista para que o ramo fail-closed de `verificar_economia` tenha
        # entrada possivel: sem o valor no enum, o ramo fica inalcancavel.
        entrada = _entrada(auth_mode="desconhecido")
        entrada.validate()
        vetos = verificar_economia(entrada)
        self.assertTrue([v for v in vetos if "desconhecido" in v],
                        f"canal nao identificado nao foi negado: {vetos}")

    def test_o_canal_pago_por_chamada_e_NEGADO(self):
        # O irmao do anterior, mantido junto: os dois modos de negacao
        # do enum precisam continuar produzindo veto.
        vetos = verificar_economia(_entrada(auth_mode="payg-api"))
        self.assertTrue([v for v in vetos if "payg" in v.lower()], vetos)

    def test_o_canal_de_assinatura_NAO_e_negado(self):
        # CONTRAPROVA do outro lado: um `verificar_economia` que negasse
        # sempre passaria nos dois testes acima e bloquearia a frota.
        self.assertEqual(verificar_economia(_entrada()), [])


def _terminais_derivados() -> set:
    """Estados SEM saida na tabela NOMEADA — corpus independente.

    DEFEITO ACHADO AO MEDIR, nesta missao. A primeira versao destes
    testes iterava `TERMINAIS_WORK_UNIT` para provar `TERMINAIS_WORK_
    UNIT`: com `cancelada` fora da lista, o corpus encolhia junto e a
    suite ficava VERDE — a tautologia do MAJOR #3 construida dentro da
    propria correcao que existe para desfaze-la. Medido: 313 testes,
    zero vermelhos, com o item removido.

    O corpus passa a sair de `_WORKUNIT_NOMEADAS`, a tabela de
    transicoes explicitas, que nao muda quando `TERMINAIS` muda: um
    estado e terminal se nenhuma transicao NOMEADA parte dele.
    """
    origens = {de for de, _para in estados._WORKUNIT_NOMEADAS
               if de is not None}
    return {e for e in ct.ESTADOS_WORK_UNIT if e not in origens}


class NenhumaTransicaoSaiDeEstadoTerminal(unittest.TestCase):
    """`TERMINAIS_WORK_UNIT` presa pela TABELA, nao por ela mesma."""

    def test_a_lista_de_terminais_e_a_que_a_tabela_nomeada_implica(self):
        # O acoplamento. Encolher `TERMINAIS` sem mexer na tabela
        # nomeada fica vermelho AQUI, e e este o teste que a varredura
        # de listas soltas pedia.
        self.assertEqual(set(estados.TERMINAIS_WORK_UNIT),
                         _terminais_derivados())

    def test_nenhum_estado_terminal_DERIVADO_tem_transicao_de_saida(self):
        # A propriedade, sobre a tabela REAL e com corpus independente:
        # para cada terminal derivado e cada destino possivel,
        # `transitar` levanta.
        derivados = _terminais_derivados()
        self.assertTrue(derivados, "nenhum estado terminal derivado")
        for terminal in sorted(derivados):
            for destino in sorted(ct.ESTADOS_WORK_UNIT):
                with self.subTest(de=terminal, para=destino):
                    with self.assertRaises(estados.TransicaoIlegal):
                        estados.transitar_workunit(terminal, destino)

    def test_uma_workunit_concluida_nao_pode_ser_cancelada(self):
        # O caso concreto que a remocao de um terminal abriria. Escrito
        # a parte porque e o que se perde, e nao a regra abstrata.
        with self.assertRaises(estados.TransicaoIlegal):
            estados.transitar_workunit("concluida", "cancelada")

    def test_uma_workunit_cancelada_nao_transita_para_lugar_nenhum(self):
        # O item exato que a varredura mediu como SOLTO: com `cancelada`
        # fora de `TERMINAIS`, a tabela ganha o laco
        # `cancelada -> cancelada` e ninguem via.
        for destino in sorted(ct.ESTADOS_WORK_UNIT):
            with self.subTest(para=destino):
                with self.assertRaises(estados.TransicaoIlegal):
                    estados.transitar_workunit("cancelada", destino)

    def test_todo_estado_NAO_terminal_pode_ser_cancelado(self):
        # CONTRAPROVA: sem ela, uma tabela VAZIA passaria nos testes
        # acima — nenhuma transicao sairia de lugar nenhum.
        nao_terminais = ct.ESTADOS_WORK_UNIT - _terminais_derivados()
        self.assertTrue(nao_terminais)
        for estado in sorted(nao_terminais):
            with self.subTest(de=estado):
                self.assertEqual(
                    estados.transitar_workunit(estado, "cancelada"),
                    "cancelada")

    def test_os_terminais_sao_estados_de_workunit_de_verdade(self):
        # Guarda contra terminal fantasma: um nome que nao esta em
        # `ESTADOS_WORK_UNIT` nao restringe tabela nenhuma.
        self.assertTrue(estados.TERMINAIS_WORK_UNIT <= ct.ESTADOS_WORK_UNIT)
        self.assertTrue(estados.TERMINAIS_WORK_UNIT)

    def test_a_tabela_de_workunit_tem_alcance_real(self):
        # Guarda anti-tabela-vazia com numero: a tabela precisa conter
        # as transicoes nomeadas MAIS as de cancelamento.
        self.assertGreater(len(estados.WORKUNIT), 12)
        self.assertIn((None, "proposta"), estados.WORKUNIT)
        self.assertGreater(len(estados._WORKUNIT_NOMEADAS), 10)


if __name__ == "__main__":
    unittest.main()
