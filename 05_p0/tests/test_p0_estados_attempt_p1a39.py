"""`ESTADOS_ATTEMPT` presa pela MAQUINA e pelo ciclo real — P1-A.3.9.

ORDEM 2 do ato. A varredura de listas [15/N] mediu `contratos.ESTADOS_
ATTEMPT` como **SOLTA — 4 de 4 membros sem exercicio**: remover
`criado`, `despachado`, `concluido` ou `orfao` deixava as duas suites
inteiras verdes.

## O DIAGNOSTICO, que e pior que "lista sem teste"

`ESTADOS_ATTEMPT` **nao e consumida em lugar nenhum**. Nao ha um unico
`_enum(..., ESTADOS_ATTEMPT, ...)` em `contratos.py`, nem leitura dela
em `estados.py` ou no `kernel.py` — ao contrario de `ESTADOS_WORK_UNIT`,
que ao menos alimenta a construcao de `estados.WORKUNIT`.

Ela e **declaracao pura**: diz quais sao os estados do attempt e nao
governa nada. A maquina de verdade e outra — `estados.ATTEMPT` mais
`estados.ATTEMPT_RETOMADA` —, e as duas podiam divergir em silencio, que
e exatamente o mecanismo do achado do `_VIA_GITBASH` duplicado.

Nao se resolve isso "exercendo o consumidor", porque nao ha consumidor.
Resolve-se **acoplando a declaracao a maquina**, e exercendo cada estado
pelo ciclo que a operacao percorre.

## CORPUS DE OUTRA CAMADA, nao da propria lista

O conjunto esperado sai das TABELAS DE TRANSICAO, que nao mudam quando
`ESTADOS_ATTEMPT` muda:

    {destino de toda transicao de ATTEMPT} | {de ATTEMPT_RETOMADA}

Iterar `ESTADOS_ATTEMPT` para conferir que ela contem o que contem seria
a tautologia do MAJOR #3 — e foi assim que `TERMINAIS_WORK_UNIT` passou
por presa na varredura antiga.

## O CASO QUE OCORRE, nao o vizinho

O vizinho seria chamar `transitar_attempt` a seco com pares de estado. O
que a operacao percorre e o ciclo inteiro, e e ele que esta aqui:

| estado | como e alcancado neste arquivo |
|---|---|
| `criado` | `kernel.criar_attempt` com `ExecutionAttempt` real |
| `despachado` | `kernel.despachar_attempt` |
| `concluido` | `apoio.fluxo_sucesso` — o ExecutionGateway de verdade |
| `orfao` | checkpoint, `_simular_crash` e `SessionKernel.retomar` |

`orfao` merece nota: e o unico que **nao** tem caminho normal — so a
retomada apos queda o produz (D6 §4). Exercer a marcacao de orfao pela
retomada real, e nao por `marcar_orfao` a seco, e o que separa este teste
do vizinho dele.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nao afirmam que os quatro estados sejam os CERTOS**: medem que a
  declaracao e a maquina concordam e que cada estado ocorre em operacao,
  jamais que a maquina de attempt esteja bem desenhada;
- **remocao SIMULTANEA do estado na lista E na tabela** passa: quem
  apagar `("criado", "despachado")` de `ATTEMPT` junto com `criado` de
  `ESTADOS_ATTEMPT` fica verde. E o mesmo limite estrutural declarado na
  FASE 1.2 da P1-A.3.8, e o remedio seria uma terceira fonte;
- **`ESTADOS_ATTEMPT` continua sem consumidor de validacao.** Este
  arquivo a prende, mas NAO a torna um enum exercido por
  `FleetEntry`/`ExecutionAttempt.validate` — nenhum campo de contrato e
  validado contra ela. Acrescentar essa validacao mudaria comportamento
  de producao e nao cabe numa correcao de guarda;
- **ACRESCIMO nao e medido** — so remocao. Um quinto estado inventado na
  tabela E na lista passaria pelo teste de igualdade;
- **nada aqui exercita CLI, rede ou provedor real.**
"""

import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0 import estados
from ssc_p0.canonico import novo_id
from ssc_p0.kernel import SessionKernel


def _estados_da_maquina() -> set:
    """Estados que as TABELAS nomeiam — corpus independente da lista."""
    alcancados = set()
    for de, para in estados.ATTEMPT | estados.ATTEMPT_RETOMADA:
        if de is not None:
            alcancados.add(de)
        alcancados.add(para)
    return alcancados


class ADeclaracaoEAMaquinaConcordam(unittest.TestCase):
    """`ESTADOS_ATTEMPT` presa pelas tabelas, nao por ela mesma."""

    def test_a_lista_e_exatamente_o_que_as_tabelas_nomeiam(self):
        # O acoplamento. Encolher a lista sem mexer nas tabelas fica
        # vermelho AQUI, e e este o teste que a varredura pedia.
        self.assertEqual(set(ct.ESTADOS_ATTEMPT), _estados_da_maquina())

    def test_as_tabelas_de_attempt_tem_alcance_real(self):
        # Guarda anti-tabela-vazia: sem ele, duas tabelas vazias
        # satisfariam a igualdade acima com uma lista vazia.
        self.assertGreaterEqual(len(estados.ATTEMPT), 3)
        self.assertGreaterEqual(len(estados.ATTEMPT_RETOMADA), 2)
        self.assertIn((None, "criado"), estados.ATTEMPT)

    def test_orfao_nao_tem_caminho_no_fluxo_normal(self):
        # A propriedade que separa as DUAS tabelas: `orfao` e exclusivo
        # da retomada. Se ele vazasse para ATTEMPT, o fluxo normal
        # poderia declarar um attempt orfao sem crash nenhum.
        self.assertNotIn("orfao", {p for _d, p in estados.ATTEMPT})
        for origem in ("criado", "despachado"):
            with self.subTest(de=origem):
                with self.assertRaises(estados.TransicaoIlegal):
                    estados.transitar_attempt(origem, "orfao")

    def test_transicao_que_pula_o_despacho_e_ilegal(self):
        # CONTRAPROVA da maquina: uma tabela que aceitasse qualquer par
        # passaria nos testes acima.
        with self.assertRaises(estados.TransicaoIlegal):
            estados.transitar_attempt("criado", "concluido")


class OsQuatroEstadosOcorremEmOperacao(unittest.TestCase):
    """Cada estado alcancado pelo ciclo real, um por um e a mao."""

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.k = self.lab.kernel

    def tearDown(self):
        apoio.limpar_lab(self.lab)

    def _attempt_despachado(self):
        wu = self.lab.router.forjar(
            intencao="tarefa que percorre o ciclo do attempt",
            criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="ciclo do attempt")
        attempt = ct.ExecutionAttempt(
            attempt_id=novo_id(), work_unit_id=wu.work_unit_id,
            decisao_id=d.decisao_id,
            linhagem_id=self.k.envelope.linhagem_id,
            selecao_solicitada=d.selecao,
            executor_resolvido={"provedor": "prov-a", "modelo": "modelo-x",
                                "effort": "alto",
                                "hash_catalogo": self.k.envelope.catalogo_ref,
                                "alias_usado": False},
            executor_observado=None,
            vinculos=self.k.vinculos_correntes(d.hash_pacote),
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo=None, custo_medido=None, artefato_ref=None)
        ev = self.k.criar_attempt(attempt, None)
        return attempt, ev

    def test_criado_e_o_estado_do_attempt_recem_registrado(self):
        attempt, _ev = self._attempt_despachado()
        self.assertEqual(self.k.attempts[attempt.attempt_id]["estado"],
                         "criado")
        self.assertIn("criado", ct.ESTADOS_ATTEMPT)

    def test_despachado_e_o_estado_apos_o_despacho(self):
        attempt, ev = self._attempt_despachado()
        self.k.despachar_attempt(attempt.attempt_id, ev.evento_id)
        self.assertEqual(self.k.attempts[attempt.attempt_id]["estado"],
                         "despachado")
        self.assertIn("despachado", ct.ESTADOS_ATTEMPT)

    def test_concluido_e_o_estado_ao_fim_do_gateway_real(self):
        # O ponto de chamada da operacao: quem conclui e o
        # ExecutionGateway, nao o teste.
        _wu, _d, resultado, _v = apoio.fluxo_sucesso(self.lab)
        self.assertEqual(self.k.attempts[resultado.attempt_id]["estado"],
                         "concluido")
        self.assertIn("concluido", ct.ESTADOS_ATTEMPT)

    def test_orfao_e_o_estado_que_so_a_retomada_apos_queda_produz(self):
        attempt, ev = self._attempt_despachado()
        self.k.despachar_attempt(attempt.attempt_id, ev.evento_id)
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        self.k._simular_crash()
        k2 = SessionKernel.retomar(self.lab.raiz, sessao,
                                   relogio=self.lab.relogio)
        self.assertEqual(k2.attempts[attempt.attempt_id]["estado"], "orfao")
        self.assertIn("orfao", ct.ESTADOS_ATTEMPT)

    def test_retomada_limpa_nao_inventa_orfao(self):
        # CONTRAPROVA do anterior: uma retomada que marcasse tudo como
        # orfao passaria no teste acima.
        apoio.fluxo_sucesso(self.lab)
        self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        self.k._simular_crash()
        k2 = SessionKernel.retomar(self.lab.raiz, sessao,
                                   relogio=self.lab.relogio)
        self.assertFalse([r for r in k2.attempts.values()
                          if r["estado"] == "orfao"])


if __name__ == "__main__":
    unittest.main()
