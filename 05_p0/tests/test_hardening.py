"""Regressoes do hardening 0.2.1 — um teste por item obrigatorio.

1  decisao mutada apos o registro e recusada (copia canonica)
2  veredito cruzado: attempt de A nunca conclui B
3  reducer validado antes do append: evento rejeitado nao fica duravel
4  escritor unico entre processos: lock/lease + fencing (2 processos reais,
   crash de processo, retomada e lock obsoleto)
5  idempotency key com fingerprint: reentrega identica aceita; payload
   diferente com a mesma chave = conflito; chave propagada ao Provider
6  fallback gera NOVA decisao (todos os portoes) com selecao real no envelope
7  ContextPackage ligado ao work_unit_id real; bytes no CAS; corrupcao/
   ausencia falha fechada
8  checkpoint escolhido pelo ultimo evento valido/seq, nunca por UUID
9  divergencia modelo/effort observado x resolvido falha fechado (escala)
10 IDs validados em caminhos; Evidence Plane read-only sem criar diretorios
11 causado_por validado na cadeia da sessao
12 RetryEvent em 1..3 e teto de backoff; indeterminado nunca repete
13 (threat model: documento 05_p0/THREAT-MODEL.md — verificado no fechamento)
"""

import json
import multiprocessing as mp
import os
import time
import unittest

import apoio
from ssc_p0 import contratos as ct
from ssc_p0.canonico import canonico, novo_id
from ssc_p0.cas import CorrupcaoDetectada
from ssc_p0.eventlog import EventoConflitoIdempotencia
from ssc_p0.kernel import DecisaoMutada, SessionKernel
from ssc_p0.writelock import EscritorObsoleto

_DIR_P0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _filho_tenta_anexar(raiz, sessao_id, dir_p0, resultado_path):
    """Processo filho: tenta assumir a sessao com o lock detido pelo pai."""
    import sys
    sys.path.insert(0, dir_p0)
    try:
        from ssc_p0.kernel import SessionKernel as SK
        k = SK.anexar_existente(raiz, sessao_id)
        k.fechar()
        resultado = {"erro": "anexou-sem-lock"}
    except Exception as exc:
        resultado = {"erro": type(exc).__name__}
    with open(resultado_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f)


def _filho_abre_sessao_e_dorme(raiz, dir_p0, sessao_path, pronto_path):
    """Processo filho: abre sessao propria, sinaliza e dorme (sera morto)."""
    import sys
    sys.path.insert(0, dir_p0)
    from ssc_p0.canonico import sha256_de
    from ssc_p0.kernel import SessionKernel as SK
    k = SK(raiz)
    envelope = k.abrir_sessao(
        escopo={"repo_alvo": raiz, "modo": "read-only", "fronteiras": []},
        permissoes={"pode_escrever": False},
        orcamento={"teto_custo": 1.0, "consumido_custo": 0.0},
        politica_ref=sha256_de({"politica": "filho"}),
        catalogo_ref=sha256_de({"catalogo": "filho"}),
        resumo_aprovacao={"custo": sha256_de({"aprovacao": "filho"})})
    with open(sessao_path, "w", encoding="utf-8") as f:
        f.write(envelope.sessao_id)
    with open(pronto_path, "w", encoding="utf-8") as f:
        f.write("pronto")
    time.sleep(120)


class TestHardening(unittest.TestCase):
    def setUp(self):
        self.lab = apoio.novo_lab()
        self.k = self.lab.kernel

    def tearDown(self):
        apoio.limpar_lab(self.lab)

    # -- 1. decisao mutada ------------------------------------------------------

    def test_decisao_mutada_recusada(self):
        wu = self.lab.router.forjar(
            intencao="tarefa com decisao que sera adulterada",
            criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        for campo, valor in (("selecao", dict(d.selecao, modelo="modelo-l3")),
                             ("custo_previsto", {"valor": 0.0}),
                             ("aprovacao_custo", None),
                             ("alternativas", [dict(d.selecao)]),
                             ("vinculos", dict(d.vinculos,
                                               hash_aprovacao="0" * 64))):
            canonica = self.k.decisoes[d.decisao_id]
            original = getattr(canonica, campo)
            setattr(canonica, campo, valor)  # mutacao posterior ao registro
            try:
                with self.assertRaises(DecisaoMutada, msg=campo):
                    self.lab.execution.executar(wu, d, idempotency_key="m")
            finally:
                setattr(canonica, campo, original)
        # Integra: a copia canonica executa normalmente.
        r = self.lab.execution.executar(wu, d, idempotency_key="m-ok")
        self.assertEqual(r.status, "sucesso")

    # -- 2. veredito cruzado ------------------------------------------------------

    def test_veredito_cruzado_attempt_de_A_nao_conclui_B(self):
        wu_a, _d, r_a, _v = apoio.fluxo_sucesso(
            self.lab, intencao="tarefa A concluida")
        wu_b = self.lab.router.forjar(
            intencao="tarefa B distinta", criterios={"tipo": "x"},
            tipo="ato", nivel="L2", classe="C1")
        d_b = self.lab.router.propor_decisao(
            wu_b, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        r_b = self.lab.execution.executar(wu_b, d_b, idempotency_key="op-b")
        attempt_a = self.k.attempts[r_a.attempt_id]["attempt"]
        veredito_cruzado = ct.ValidationVerdict(
            veredito_id=novo_id(),
            alvo={"work_unit_id": wu_b.work_unit_id,      # B...
                  "attempt_id": attempt_a.attempt_id,      # ...com attempt de A
                  "artefato_ref": attempt_a.artefato_ref},
            camada="deterministica", verificador={"nome": "j"},
            pacote_juiz={}, criterios_ref=wu_b.criterios_aceite_ref,
            contexto_ref=wu_b.contexto_ref, independencia={},
            resultado="aprovado", criterios=[], efeitos={})
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.k.registrar_veredito(veredito_cruzado, None)
        self.assertIn("cruzado", str(ctx.exception))
        self.assertEqual(self.k.work_units[wu_b.work_unit_id].estado,
                         "aguardando-validacao")  # B NAO foi concluida

    # -- 3. append rejeitado nao fica duravel -------------------------------------

    def test_reducer_rejeitado_nada_duravel(self):
        apoio.fluxo_sucesso(self.lab)
        log_path = os.path.join(self.k.raiz, "logs",
                                f"{self.k.envelope.sessao_id}.jsonl")
        with open(log_path, "rb") as f:
            bytes_antes = f.read()
        seq_antes = self.k.log.seq_atual()
        n_wus = len(self.k.work_units)
        with self.assertRaises(Exception):
            self.k._emitir("work-unit",
                           {"acao": "transicao",
                            "work_unit_id": "workunit-que-nao-existe",
                            "de": "proposta", "para": "concluida"},
                           causado_por=None)
        with open(log_path, "rb") as f:
            self.assertEqual(f.read(), bytes_antes)  # nada duravel
        self.assertEqual(self.k.log.seq_atual(), seq_antes)
        self.assertEqual(len(self.k.work_units), n_wus)  # estado restaurado

    # -- 4. escritor unico entre processos -----------------------------------------

    def test_lock_segundo_processo_recusado(self):
        base = os.path.dirname(self.k.raiz)
        resultado_path = os.path.join(base, "resultado_filho.json")
        ctx = mp.get_context("spawn")
        filho = ctx.Process(
            target=_filho_tenta_anexar,
            args=(self.k.raiz, self.k.envelope.sessao_id, _DIR_P0,
                  resultado_path))
        filho.start()
        filho.join(timeout=60)
        if filho.is_alive():
            filho.terminate()
            filho.join()
            self.fail("filho nao terminou (lock nao recusou?)")
        with open(resultado_path, encoding="utf-8") as f:
            resultado = json.load(f)
        self.assertEqual(resultado["erro"], "LockIndisponivel",
                         "segundo processo NAO foi recusado pelo lock")

    def test_crash_de_processo_retomada_por_outro_processo(self):
        base = os.path.dirname(self.k.raiz)
        sessao_path = os.path.join(base, "sessao_filho.txt")
        pronto_path = os.path.join(base, "filho_pronto.txt")
        ctx = mp.get_context("spawn")
        filho = ctx.Process(
            target=_filho_abre_sessao_e_dorme,
            args=(self.k.raiz, _DIR_P0, sessao_path, pronto_path))
        filho.start()
        limite = time.time() + 60
        while not os.path.exists(pronto_path) and time.time() < limite:
            time.sleep(0.1)
        self.assertTrue(os.path.exists(pronto_path),
                        "filho nao abriu a sessao a tempo")
        with open(sessao_path, encoding="utf-8") as f:
            sessao_filho = f.read().strip()
        filho.terminate()  # crash real: o SO libera o lock do processo
        filho.join(timeout=30)
        # Outro processo (este) assume: lock livre + fencing incrementado.
        k2 = SessionKernel.anexar_existente(self.k.raiz, sessao_filho,
                                            relogio=self.lab.relogio)
        try:
            self.assertEqual(k2._lock_sessao.token, 2)
            ev, criado = k2._emitir(
                "memoria",
                {"acao": "registrar",
                 "entrada": {"fonte": "retomada", "validade": "sessao"}},
                causado_por=None)
            self.assertTrue(criado)  # o sucessor escreve normalmente
        finally:
            k2.fechar()

    def test_lock_obsoleto_fencing_token(self):
        sessao = self.k.envelope.sessao_id
        self.k._simular_crash()  # processo "morre" sem fechar
        k2 = SessionKernel.anexar_existente(self.k.raiz, sessao,
                                            relogio=self.lab.relogio)
        try:
            with self.assertRaises(EscritorObsoleto):
                self.k._emitir("memoria",
                               {"acao": "registrar",
                                "entrada": {"fonte": "fantasma",
                                            "validade": "sessao"}},
                               causado_por=None)
        finally:
            k2.fechar()

    # -- 5. idempotency key com fingerprint -----------------------------------------

    def test_idempotencia_reentrega_aceita_payload_diferente_conflito(self):
        payload_a = {"acao": "registrar",
                     "entrada": {"fonte": "t", "validade": "s", "n": 1}}
        payload_b = {"acao": "registrar",
                     "entrada": {"fonte": "t", "validade": "s", "n": 2}}
        _ev1, criado1 = self.k._emitir("memoria", payload_a, causado_por=None,
                                       idempotency_key="chave-X")
        self.assertTrue(criado1)
        _ev2, criado2 = self.k._emitir("memoria", payload_a, causado_por=None,
                                       idempotency_key="chave-X")
        self.assertFalse(criado2)  # reentrega identica: aceita, sem efeito
        self.assertEqual(len(self.k.memoria), 1)
        with self.assertRaises(EventoConflitoIdempotencia):
            self.k._emitir("memoria", payload_b, causado_por=None,
                           idempotency_key="chave-X")
        self.assertEqual(len(self.k.memoria), 1)  # conflito nao grava nada

    def test_idempotency_key_propagada_ao_provider(self):
        wu = self.lab.router.forjar(
            intencao="tarefa com chave de idempotencia",
            criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        self.lab.execution.executar(wu, d, idempotency_key="op-prop-1")
        provider = self.lab.providers[("prov-a", "modelo-x")]
        self.assertIn("op-prop-1", provider.chaves_recebidas)

    # -- 6. fallback com nova decisao -------------------------------------------------

    def test_fallback_gera_nova_decisao_selecao_real_no_envelope(self):
        lab = apoio.novo_lab(
            programa_providers={"prov-a/modelo-x": ["falha-quota"]})
        try:
            wu = lab.router.forjar(
                intencao="tarefa com fallback", criterios={"tipo": "x"},
                tipo="ato", nivel="L2", classe="C1")
            d1 = lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=lab.selecao("prov-a", "modelo-x"),
                alternativas=[lab.selecao("prov-b", "modelo-y")],
                aprovacao_custo=lab.aprovacao, motivo="t")
            r = lab.execution.executar(wu, d1, idempotency_key="op-fb-nova")
            self.assertEqual(r.status, "sucesso")
            # NOVA RoutingDecision registrada, supersede a anterior.
            self.assertEqual(len(lab.kernel.decisoes), 2)
            d2 = lab.kernel.decisoes[lab.kernel.vigente[wu.work_unit_id]]
            self.assertEqual(d2.supersede, d1.decisao_id)
            # Selecao REAL registrada na decisao e no attempt.
            self.assertEqual(d2.selecao["modelo"], "modelo-y")
            attempt = lab.kernel.attempts[r.attempt_id]["attempt"]
            self.assertEqual(attempt.decisao_id, d2.decisao_id)
            self.assertEqual(attempt.selecao_solicitada["modelo"], "modelo-y")
            # FallbackEvent com a selecao real; mesmo envelope aprovado.
            self.assertEqual(lab.kernel.fallbacks[0].para_executor["modelo"],
                             "modelo-y")
            self.assertEqual(d2.aprovacao_custo, d1.aprovacao_custo)
            # Todos os portoes repetidos: decisao passou pela Policy sem veto.
            self.assertFalse(any(rec.get("acao") == "veto"
                                 for rec in lab.kernel.recusas))
        finally:
            apoio.limpar_lab(lab)

    # -- 7. contexto ligado, bytes no CAS, falha fechada -------------------------------

    def test_contexto_corrompido_ou_ausente_falha_fechada(self):
        wu = self.lab.router.forjar(
            intencao="tarefa com contexto no CAS", criterios={"tipo": "x"},
            tipo="ato", nivel="L2", classe="C1")
        d = self.lab.router.propor_decisao(
            wu, rota="padrao", selecao=self.lab.selecao("prov-a", "modelo-x"),
            aprovacao_custo=self.lab.aprovacao, motivo="t")
        caminho_pacote = self.k.cas._caminho(wu.contexto_ref)
        with open(caminho_pacote, "rb") as f:
            original = f.read()
        with open(caminho_pacote, "wb") as f:
            f.write(b"corrupcao" + original[9:])  # corrompe DEPOIS do registro
        with self.assertRaises(CorrupcaoDetectada):
            self.lab.execution.executar(wu, d, idempotency_key="op-corr")
        os.remove(caminho_pacote)  # ausencia: tambem falha fechada
        with self.assertRaises(ct.FalhaContrato):
            self.lab.execution.executar(wu, d, idempotency_key="op-aus")

    def test_contexto_ligado_a_outra_workunit_recusado(self):
        pacote = self.k.montar_contexto(
            novo_id(), [], exclusoes=["pacote de outra WU"])
        with self.assertRaises(ct.FalhaContrato) as ctx:
            self.lab.router.forjar(
                intencao="tarefa com contexto alheio", criterios={"tipo": "x"},
                tipo="ato", nivel="L2", classe="C1",
                contexto_ref=pacote.hash_pacote, wu_id=novo_id())
        self.assertIn("work_unit_id", str(ctx.exception))

    # -- 8. checkpoint por seq, nunca por UUID --------------------------------------------

    def test_checkpoint_escolhido_por_seq_nao_por_uuid(self):
        apoio.fluxo_sucesso(self.lab)
        cp1 = self.k.gravar_checkpoint()
        self.k.registrar_memoria(
            {"fonte": "t", "validade": "sessao", "rotulo": "depois-cp1"}, None)
        cp2 = self.k.gravar_checkpoint()
        self.k.suspender()
        sessao = self.k.envelope.sessao_id
        # Renomeia o checkpoint ANTIGO para ordenar por ultimo (armadilha
        # de UUID): a escolha correta e por seq, nao por nome.
        diretorio = os.path.join(self.k.raiz, "checkpoints", sessao)
        os.rename(os.path.join(diretorio, f"{cp1.checkpoint_id}.json"),
                  os.path.join(diretorio, f"zzzz{cp1.checkpoint_id}.json"))
        self.k._simular_crash()
        k2 = SessionKernel.retomar(self.k.raiz, sessao,
                                   relogio=self.lab.relogio)
        try:
            from ssc_p0.evidence import EvidencePlane
            eventos = EvidencePlane(self.k.raiz, sessao).eventos()
            retomadas = [e for e in eventos
                         if e["payload"].get("acao") == "retomar"]
            self.assertEqual(retomadas[-1]["payload"]["checkpoint_id"],
                             cp2.checkpoint_id)
        finally:
            k2.fechar()

    # -- 9. divergencia observado x resolvido ------------------------------------------------

    def test_divergencia_modelo_effort_falha_fechada(self):
        lab = apoio.novo_lab(observados={
            "prov-a/modelo-x": {"provedor": "prov-a", "modelo": "modelo-x",
                                "effort": "baixo"}})  # effort divergente
        try:
            wu = lab.router.forjar(
                intencao="tarefa com executor que mente o effort",
                criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
            d = lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=lab.selecao("prov-a", "modelo-x", "alto"),
                aprovacao_custo=lab.aprovacao, motivo="t")
            r = lab.execution.executar(wu, d, idempotency_key="op-div")
            self.assertEqual(r.status, "escalonado")
            self.assertEqual(r.detalhe, "divergencia-executor")
            self.assertTrue(any(e.motivo == "divergencia-executor"
                                for e in lab.kernel.escalacoes))
            self.assertEqual(len(lab.kernel.retries), 0)
            self.assertEqual(lab.kernel.work_units[wu.work_unit_id].estado,
                             "em-execucao")  # NAO avancou para validacao
        finally:
            apoio.limpar_lab(lab)

    # -- 10. ids em caminhos + Evidence read-only ---------------------------------------------

    def test_ids_invalidos_em_caminhos_recusados(self):
        from ssc_p0.evidence import EvidencePlane
        for ruim in ("../fora", "x" * 31, "zz" * 16, "a/b", ""):
            with self.subTest(id=ruim):
                with self.assertRaises(ct.FalhaContrato):
                    SessionKernel.anexar_existente(self.k.raiz, ruim)
                with self.assertRaises(ct.FalhaContrato):
                    SessionKernel.retomar(self.k.raiz, ruim)
                with self.assertRaises(ValueError):
                    EvidencePlane(self.k.raiz, ruim)

    def test_evidence_plane_readonly_sem_criar_diretorios(self):
        apoio.fluxo_sucesso(self.lab)
        from ssc_p0.evidence import EvidencePlane
        antes = {b for b, _d, _f in os.walk(self.k.raiz)}
        evi = EvidencePlane(self.k.raiz, self.k.envelope.sessao_id)
        depois = {b for b, _d, _f in os.walk(self.k.raiz)}
        self.assertEqual(antes, depois)  # nenhum diretorio criado
        with self.assertRaises(PermissionError):
            evi.cas.gravar(b"escrita proibida")
        evi.projetar()  # leitura funciona normalmente

    # -- 11. causado_por na cadeia -----------------------------------------------------------

    def test_causado_por_fora_da_cadeia_recusado(self):
        with self.assertRaises(ct.FalhaContrato):
            self.k._emitir("memoria",
                           {"acao": "registrar",
                            "entrada": {"fonte": "t", "validade": "s"}},
                           causado_por="evento-que-nao-existe-nesta-sessao")
        ev = self.k.registrar_memoria(
            {"fonte": "t", "validade": "s", "rotulo": "ok"}, None)
        # Cadeia valida funciona.
        self.k.registrar_memoria(
            {"fonte": "t", "validade": "s", "rotulo": "filho"},
            ev.evento_id)

    # -- 12. retry 1..3 e teto de backoff -----------------------------------------------------

    def test_retry_fora_dos_limites_recusado(self):
        base = dict(retry_id=novo_id(), attempt_id=novo_id(),
                    work_unit_id=novo_id(), respeitou_retry_after=True,
                    idempotency_key=None, motivo="t")
        for tentativa_n in (0, 4, 99):
            with self.subTest(tentativa_n=tentativa_n):
                with self.assertRaises(ct.FalhaContrato):
                    ct.RetryEvent(tentativa_n=tentativa_n, backoff_ms=1000,
                                  **base).validado()
        with self.assertRaises(ct.FalhaContrato):
            ct.RetryEvent(tentativa_n=1,
                          backoff_ms=ct.BACKOFF_TETO_MS + 1, **base).validado()
        # Limites inclusos passam.
        ct.RetryEvent(tentativa_n=3, backoff_ms=ct.BACKOFF_TETO_MS,
                      **base).validado()

    def test_backoff_teto_aplicado_e_indeterminado_nao_repete(self):
        lab = apoio.novo_lab(programa_providers={"prov-a/modelo-x": [
            {"comportamento": "falha-transitoria", "retry_after_ms": 999999},
            "sucesso"]})
        try:
            wu = lab.router.forjar(
                intencao="tarefa com retry-after gigante",
                criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
            d = lab.router.propor_decisao(
                wu, rota="padrao",
                selecao=lab.selecao("prov-a", "modelo-x"),
                aprovacao_custo=lab.aprovacao, motivo="t")
            lab.execution.executar(wu, d, idempotency_key="op-teto")
            retry = lab.kernel.retries[0]
            self.assertEqual(retry.backoff_ms, ct.BACKOFF_TETO_MS)  # teto
            self.assertFalse(retry.respeitou_retry_after)  # registrado, nao escondido
        finally:
            apoio.limpar_lab(lab)
        lab2 = apoio.novo_lab(
            programa_providers={"prov-a/modelo-x": ["timeout"]})
        try:
            wu2 = lab2.router.forjar(
                intencao="tarefa com timeout apos envio",
                criterios={"tipo": "x"}, tipo="ato", nivel="L2", classe="C1")
            d2 = lab2.router.propor_decisao(
                wu2, rota="padrao",
                selecao=lab2.selecao("prov-a", "modelo-x"),
                aprovacao_custo=lab2.aprovacao, motivo="t")
            r2 = lab2.execution.executar(wu2, d2, idempotency_key="op-ind")
            self.assertEqual(r2.status, "indeterminado")
            self.assertEqual(len(lab2.kernel.retries), 0)  # nunca repete
        finally:
            apoio.limpar_lab(lab2)


if __name__ == "__main__":
    unittest.main()
