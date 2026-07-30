"""Testes de schema e round-trip de TODOS os contratos D5 (item: contratos)."""

import unittest

import apoio  # noqa: F401  (sys.path)
from ssc_p0 import contratos as ct
from ssc_p0.canonico import novo_id


def _exemplos():
    h = "ab" * 32
    return {
        "SessionEnvelope": ct.SessionEnvelope(
            sessao_id=novo_id(), linhagem_id=novo_id(), linhagem_origem=None,
            criado_em="2026-07-30T00:00:00Z", encerrado_em=None, estado="ativa",
            escopo={"repo_alvo": "/x", "modo": "read-only", "fronteiras": []},
            permissoes={"pode_escrever": False, "pode_executar": True,
                        "pode_rede": False, "conectores_com_escrita": []},
            orcamento={"teto_custo": 1.0, "consumido_custo": 0.0},
            politica_ref=h, catalogo_ref=h,
            integridade={"assinatura_insumos": h, "selo": h},
            contexto_ativo_ref=None, memoria_ref=None,
            resumo_aprovacao={"custo": h, "autonomia": h}),
        "WorkUnit": ct.WorkUnit(
            work_unit_id=novo_id(), sessao_id=novo_id(), linhagem_id=novo_id(),
            parent_work_unit=None, tipo="ato", tipo_decisao="tipo-2",
            intencao="fazer algo", criterios_aceite_ref=h,
            nivel_capacidade="L1",
            perfil_capacidade={"modalidade": "texto", "ferramentas": [],
                               "formato_saida": "livre",
                               "contexto_max_tokens": 100, "dominio": "geral",
                               "privacidade": "local-only",
                               "latencia_max_ms": None,
                               "orcamento_max_custo": None},
            classe_governanca="C0", contexto_ref=h, depende_de=[],
            estado="proposta", resultado_ref=None, custo_medido=None),
        "ContextPackage": ct.ContextPackage(
            contexto_id=novo_id(), work_unit_id=novo_id(),
            entradas=[{"origem": "/a.txt", "sha256": h, "papel": "evidencia",
                       "inclusao": "verbatim"}],
            politica_inclusao={"verbatim_ate": 204800,
                               "memoria_por_hash": True},
            custo_contexto_linhas=3, exclusoes=["x: irrelevante"],
            hash_pacote=h),
        "RoutingDecision": ct.RoutingDecision(
            decisao_id=novo_id(), work_unit_id=novo_id(), hash_pacote=h,
            classificacao={"rota": "padrao", "confianca": "alta",
                           "metodo": "declarado"},
            selecao={"ferramenta": "fake-cli", "provedor": "prov-a",
                     "modelo": "modelo-x", "effort": "alto",
                     "modo": "read-only", "controle": "confirma-no-gasto"},
            nivel_capacidade_atendido="L2", alternativas=[],
            vinculos={"hash_envelope": h, "hash_politica": h,
                      "hash_permissoes": h, "hash_aprovacao": h,
                      "hash_catalogo": h, "hash_contexto": h},
            custo_previsto={"valor": 0.01, "rotulo": "estimado"},
            aprovacao_custo={"modelos_permitidos": ["prov-a/modelo-x"],
                             "efforts_permitidos": ["alto"], "teto_custo": 1.0,
                             "modo": "read-only",
                             "validade": "2027-01-01T00:00:00Z",
                             "fallback_autorizado": True},
            motivo="teste", supersede=None),
        "ExecutionAttempt": ct.ExecutionAttempt(
            attempt_id=novo_id(), work_unit_id=novo_id(), decisao_id=novo_id(),
            linhagem_id=novo_id(),
            selecao_solicitada={"provedor": "prov-a", "modelo": "modelo-x"},
            executor_resolvido={"provedor": "prov-a", "modelo": "modelo-x",
                                "effort": "alto", "hash_catalogo": h,
                                "alias_usado": False},
            executor_observado=None, vinculos={"hash_envelope": h},
            inicio=None, fim=None, captura={}, resultado=None,
            efeito_externo=None, custo_medido=None, artefato_ref=None),
        "RetryEvent": ct.RetryEvent(
            retry_id=novo_id(), attempt_id=novo_id(), work_unit_id=novo_id(),
            tentativa_n=2, backoff_ms=1000, respeitou_retry_after=True,
            idempotency_key="k", motivo="429"),
        "FallbackEvent": ct.FallbackEvent(
            fallback_id=novo_id(), attempt_id=novo_id(), work_unit_id=novo_id(),
            de_executor={"provedor": "a", "modelo": "x", "effort": "alto"},
            para_executor={"provedor": "b", "modelo": "y", "effort": "alto"},
            motivo="falha-contrato"),
        "EscalationEvent": ct.EscalationEvent(
            escalacao_id=novo_id(), work_unit_id=novo_id(),
            motivo="orcamento", destino="humano", detalhe="estouro"),
        "ValidationVerdict": ct.ValidationVerdict(
            veredito_id=novo_id(),
            alvo={"work_unit_id": novo_id(), "artefato_ref": h,
                  "attempt_id": novo_id()},
            camada="deterministica", verificador={"nome": "juiz1"},
            pacote_juiz={"provedor": "local", "modelo": "det", "effort": "n/a",
                         "rubrica_ref": h, "seed": None, "hash_catalogo": h},
            criterios_ref=h, contexto_ref=h,
            independencia={"provedor_distinto_do_executor": True,
                           "modelo_distinto": True, "motivos": []},
            resultado="aprovado",
            criterios=[{"criterio": "c", "evidencia": "e", "passou": True}],
            efeitos={"artefato_ref": h}),
        "Checkpoint": ct.Checkpoint(
            checkpoint_id=novo_id(), sessao_id=novo_id(), linhagem_id=novo_id(),
            estado_refs={"envelope": h, "ultimo_evento_hash": h, "seq": 7},
            ponto_de_retomada={"pendentes": []},
            validacao={"aprovado": True, "falhas": []}, selo=h),
        "Evento": ct.Evento(
            evento_id=novo_id(), seq=1, ts="2026-07-30T00:00:00Z",
            schema_version=ct.SCHEMA_VERSION, linhagem_id=novo_id(),
            tipo="sessao", causado_por=None, idempotency_key="k",
            prev_event_hash=h, payload_ref=h),
    }


class TestContratos(unittest.TestCase):
    def test_roundtrip_todos_os_contratos(self):
        for nome, obj in _exemplos().items():
            with self.subTest(contrato=nome):
                obj.validate()
                dados = obj.to_dict()
                clone = type(obj).from_dict(dados)
                self.assertEqual(clone.to_dict(), dados)
                clone.validate()

    def test_schema_fechado_campo_desconhecido_recusado(self):
        dados = _exemplos()["WorkUnit"].to_dict()
        dados["campo_estranho"] = 1
        with self.assertRaises(ct.FalhaContrato):
            ct.WorkUnit.from_dict(dados)

    def test_schema_campo_ausente_recusado(self):
        dados = _exemplos()["WorkUnit"].to_dict()
        del dados["intencao"]
        with self.assertRaises(ct.FalhaContrato):
            ct.WorkUnit.from_dict(dados)

    def test_enum_fora_da_lista_e_falha_de_contrato(self):
        ex = _exemplos()
        casos = []
        wu = ex["WorkUnit"].to_dict(); wu["estado"] = "rodando"
        casos.append((ct.WorkUnit, wu))
        at = ex["ExecutionAttempt"].to_dict(); at["resultado"] = "ok"
        casos.append((ct.ExecutionAttempt, at))
        vd = ex["ValidationVerdict"].to_dict(); vd["camada"] = "magica"
        casos.append((ct.ValidationVerdict, vd))
        es = ex["EscalationEvent"].to_dict(); es["motivo"] = "outro"
        casos.append((ct.EscalationEvent, es))
        ev = ex["Evento"].to_dict(); ev["tipo"] = "estranho"
        casos.append((ct.Evento, ev))
        rd = ex["RoutingDecision"].to_dict()
        rd["classificacao"]["confianca"] = "media"
        casos.append((ct.RoutingDecision, rd))
        for cls, dados in casos:
            with self.subTest(contrato=cls.__name__):
                with self.assertRaises(ct.FalhaContrato):
                    cls.from_dict(dados).validate()

    def test_sem_coercao_de_enum(self):
        wu = _exemplos()["WorkUnit"].to_dict()
        wu["nivel_capacidade"] = "l1"  # minusculo NAO vira L1
        with self.assertRaises(ct.FalhaContrato):
            ct.WorkUnit.from_dict(wu).validate()

    def test_intencao_acima_de_4000_recusada(self):
        wu = _exemplos()["WorkUnit"].to_dict()
        wu["intencao"] = "x" * 4001
        with self.assertRaises(ct.FalhaContrato):
            ct.WorkUnit.from_dict(wu).validate()

    def test_captura_obrigatoria_quando_resultado_presente(self):
        at = _exemplos()["ExecutionAttempt"].to_dict()
        at["resultado"] = "sucesso"
        at["captura"] = {}
        with self.assertRaises(ct.FalhaContrato):
            ct.ExecutionAttempt.from_dict(at).validate()


if __name__ == "__main__":
    unittest.main()
