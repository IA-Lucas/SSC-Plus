"""Execution Gateway (D6 §2.4): o braco.

EXECUTA; nao decide rota, nao se julga, nao grava no log (emite fatos ao
Kernel). Aplica a maquina de recuperacao (D5 §6 / D6 §4):

- retry: so falha transitoria, max 3, backoff com teto, respeitando
  Retry-After, e SO sob IR-1 (idempotency_key ou efeito nao-aplicado);
- fallback (0.2.1-6): NOVA RoutingDecision (todos os portoes de novo:
  Catalogo + Policy + envelope), registra a selecao REAL e permanece
  dentro do envelope aprovado;
- divergencia modelo/effort observado x resolvido (0.2.1-9): falha fechada
  — EscalationEvent 'divergencia-executor', a WorkUnit nao avanca;
- indeterminado (efeito incerto): SEM retry automatico, escalona (IR-2);
- 4xx de contrato: zero retry;
- esgotamento: EscalationEvent.

0.2.1-1: a execucao usa SOMENTE a copia canonica da RoutingDecision
registrada no log (kernel.decisao_canonica); objeto mutado = recusado.
"""

from . import contratos as ct
from .canonico import novo_id
from .catalogo import Catalogo
from .confidencialidade import SegredoDetectado, escanear_segredos
from .kernel import ControlPlane, SessionKernel
from .policy import OrcamentoEstourado, PolicyGateway
from .router import RotaVetada


class ResultadoExecucao:
    """Resumo do que aconteceu numa rodada de execucao."""

    def __init__(self, status: str, attempt_id: str | None, detalhe: str = ""):
        self.status = status  # sucesso|escalonado|indeterminado
        self.attempt_id = attempt_id
        self.detalhe = detalhe

    def __repr__(self):
        return f"ResultadoExecucao({self.status!r}, {self.attempt_id!r})"


class ExecutionGateway:
    def __init__(self, kernel: SessionKernel, policy: PolicyGateway,
                 catalogo: Catalogo, providers: dict,
                 control: ControlPlane, router=None):
        """providers: {(provedor, modelo): FakeProvider}.
        router: TaskRouter — obrigatorio para fallback com nova decisao."""
        self.kernel = kernel
        self.policy = policy
        self.catalogo = catalogo
        self.providers = providers
        self.control = control
        self.router = router

    def _pacote(self, wu: ct.WorkUnit) -> dict:
        """ContextPackage do CAS, ligado a ESTA WorkUnit (0.2.1-7).

        Falha fechada: ausencia/corrupcao/vinculo cruzado levantam — nunca
        devolve pacote vazio.
        """
        return self.kernel.ler_pacote(wu.contexto_ref, wu.work_unit_id)

    def executar(self, wu: ct.WorkUnit, decisao: ct.RoutingDecision,
                 idempotency_key: str | None = None,
                 entrada: bytes = b"") -> ResultadoExecucao:
        """Materializa attempts ate sucesso, fallback esgotado ou escalonamento."""
        k = self.kernel
        if len(entrada) > 1024 * 1024:
            raise ct.FalhaContrato("entrada excede o teto de 1 MiB")
        # O scanner recebe a entrada INTEGRAL; a intencao resumida da WU
        # nunca substitui os bytes que efetivamente irao ao provedor.
        escanear_segredos(entrada, "entrada integral do provider")
        # 0.2.1-1: somente a copia canonica registrada e executada.
        decisao = k.decisao_canonica(decisao.decisao_id)
        executores = [dict(decisao.selecao)] + [
            dict(a) for a in decisao.alternativas
        ]
        pacote = self._pacote(wu)
        idx = 0
        retries_feitos = 0
        causador = k.evento_de_decisao(decisao.decisao_id)
        attempt = None

        while True:
            # Portao de orcamento bloqueante antes de CADA attempt.
            try:
                self.policy.verificar_orcamento(
                    k.envelope.orcamento, decisao.custo_previsto)
            except OrcamentoEstourado as exc:
                self.control.escalar(wu.work_unit_id, "orcamento", "humano",
                                     detalhe=str(exc),
                                     causado_por=causador)
                return ResultadoExecucao("escalonado", None, "orcamento")
            selecao = executores[idx]
            resolvido, alias_usado = self.catalogo.resolver(selecao)
            resolvido = dict(resolvido)
            resolvido["hash_catalogo"] = k.envelope.catalogo_ref
            resolvido["alias_usado"] = alias_usado
            attempt = ct.ExecutionAttempt(
                attempt_id=novo_id(),
                work_unit_id=wu.work_unit_id,
                decisao_id=decisao.decisao_id,
                linhagem_id=k.envelope.linhagem_id,
                selecao_solicitada=dict(selecao),
                executor_resolvido=resolvido,
                executor_observado=None,
                vinculos=k.vinculos_correntes(decisao.hash_pacote),
                inicio=None, fim=None, captura={}, resultado=None,
                efeito_externo=None, custo_medido=None, artefato_ref=None,
            ).validado()
            ev_criar = k.criar_attempt(attempt, causador)
            ev_desp = k.despachar_attempt(attempt.attempt_id,
                                          ev_criar.evento_id)
            provider = self.providers[(resolvido["provedor"],
                                       resolvido["modelo"])]
            # 0.2.1-5: a idempotency_key e propagada ao Provider Adapter.
            resposta = provider.invocar(entrada, pacote,
                                        idempotency_key=idempotency_key)
            try:
                if len(resposta.saida or b"") > 1024 * 1024:
                    raise SegredoDetectado("saida do provider acima de 1 MiB")
                escanear_segredos(resposta.saida or b"",
                                  "saida integral do provider")
            except SegredoDetectado:
                # O attempt ja foi despachado: conclui com um artefato fixo
                # seguro, preservando auditoria sem persistir nem ecoar o
                # conteudo recusado.
                resposta.saida = b"[saida bloqueada pela politica de confidencialidade]"
                resposta.ok = False
                resposta.falha = "falha-contrato"
            # Captura estruturada OBRIGATORIA (D5 §5), mesmo em falha.
            saida_ref = k.cas.gravar(resposta.saida or b"")
            captura = {
                "saida_estruturada_ref": saida_ref,
                "saida_final_ref": saida_ref if resposta.ok else None,
            }
            observado = resposta.executor_observado
            divergente = bool(observado) and (
                observado.get("modelo") != resolvido["modelo"]
                or observado.get("provedor") != resolvido["provedor"]
                or observado.get("effort") != resolvido["effort"]
            )
            if resposta.ok:
                resultado = "sucesso"
                artefato_ref = saida_ref
            else:
                resultado = resposta.falha
                artefato_ref = None
            ev_conc = k.concluir_attempt(
                attempt.attempt_id, resultado, resposta.efeito_externo,
                captura, observado, resposta.custo, artefato_ref,
                ev_desp.evento_id)

            if divergente:
                # 0.2.1-9: observado != resolvido = falha fechada. O evento
                # tipado fica registrado e a WorkUnit NAO avanca — escala.
                k.registrar_divergencia_executor(
                    attempt.attempt_id, resolvido, observado,
                    ev_conc.evento_id)
                self.control.escalar(
                    wu.work_unit_id, "divergencia-executor", "humano",
                    detalhe="modelo/effort observado diverge do resolvido: "
                            "falha fechada, execucao nao conclui a WorkUnit",
                    causado_por=ev_conc.evento_id)
                return ResultadoExecucao("escalonado", attempt.attempt_id,
                                         "divergencia-executor")

            if resultado == "sucesso":
                k.transicionar_work_unit(wu.work_unit_id,
                                         "aguardando-validacao",
                                         ev_conc.evento_id)
                return ResultadoExecucao("sucesso", attempt.attempt_id)

            if resultado == "indeterminado":
                # IR-2: efeito externo incerto => SEM retry automatico.
                self.control.escalar(
                    wu.work_unit_id, "indeterminado", "humano",
                    detalhe="efeito externo incerto; retry automatico "
                            "bloqueado (IR-1/IR-2)",
                    causado_por=ev_conc.evento_id)
                return ResultadoExecucao("indeterminado", attempt.attempt_id)

            if resultado == "falha-transitoria" \
                    and retries_feitos < ct.RETRY_MAX_TENTATIVAS:
                # IR-1: so se idempotente ou comprovadamente nao aplicada.
                if idempotency_key or resposta.efeito_externo == "nao-aplicado":
                    retries_feitos += 1
                    retry_after = resposta.retry_after_ms or 0
                    # 0.2.1-12: backoff exponencial com TETO absoluto.
                    backoff = min(
                        max(1000 * (2 ** (retries_feitos - 1)), retry_after),
                        ct.BACKOFF_TETO_MS)
                    retry = ct.RetryEvent(
                        retry_id=novo_id(),
                        attempt_id=attempt.attempt_id,
                        work_unit_id=wu.work_unit_id,
                        tentativa_n=retries_feitos,
                        backoff_ms=backoff,
                        respeitou_retry_after=backoff >= retry_after,
                        idempotency_key=idempotency_key,
                        motivo="falha transitoria (429/5xx)",
                    ).validado()
                    ev_retry = k.registrar_retry(retry, ev_conc.evento_id)
                    causador = ev_retry.evento_id  # novo attempt aponta o retry
                    continue
                # IR-1 violado: sem retry; cai no caminho de fallback/escalona.

            # Fallback (0.2.1-6): NOVA RoutingDecision com a selecao real —
            # repete TODOS os portoes (Catalogo + Policy + envelope).
            if idx + 1 < len(executores):
                proximo = executores[idx + 1]
                if self.router is not None \
                        and self.policy.verificar_fallback_envelope(
                            decisao, proximo):
                    try:
                        nova_decisao = self.router.rerotear(
                            wu,
                            rota=decisao.classificacao.get("rota"),
                            selecao=proximo,
                            confianca=decisao.classificacao.get(
                                "confianca", "alta"),
                            metodo=decisao.classificacao.get(
                                "metodo", "declarado"),
                            alternativas=executores[idx + 2:],
                            custo_previsto=decisao.custo_previsto,
                            aprovacao_custo=decisao.aprovacao_custo,
                            motivo=f"fallback de {resolvido['modelo']} "
                                   f"apos {resultado}",
                            causado_por=ev_conc.evento_id)
                    except (RotaVetada, ct.FalhaContrato) as exc:
                        # Veto legitimo dos portoes = escalonamento; qualquer
                        # outra excecao e bug e sobe (nunca rotulada de veto).
                        self.control.escalar(
                            wu.work_unit_id, "sem-alternativa", "humano",
                            detalhe="nova decisao de fallback vetada nos "
                                    f"portoes: {exc}",
                            causado_por=ev_conc.evento_id)
                        return ResultadoExecucao("escalonado",
                                                 attempt.attempt_id,
                                                 "fallback-fora-do-envelope")
                    fallback = ct.FallbackEvent(
                        fallback_id=novo_id(),
                        attempt_id=attempt.attempt_id,
                        work_unit_id=wu.work_unit_id,
                        de_executor={
                            "provedor": resolvido["provedor"],
                            "modelo": resolvido["modelo"],
                            "effort": resolvido["effort"],
                        },
                        para_executor={
                            "provedor": proximo["provedor"],
                            "modelo": proximo["modelo"],
                            "effort": proximo["effort"],
                        },
                        motivo=f"{resultado} em {resolvido['modelo']}; "
                               f"nova decisao {nova_decisao.decisao_id[:8]}",
                    ).validado()
                    ev_fb = k.registrar_fallback(fallback, ev_conc.evento_id)
                    # 0.2.1-1: a decisao de fallback TAMBEM so executa pela
                    # copia canonica registrada (re-verificada aqui).
                    decisao = k.decisao_canonica(nova_decisao.decisao_id)
                    executores = [dict(decisao.selecao)] + [
                        dict(a) for a in decisao.alternativas
                    ]
                    idx = 0
                    retries_feitos = 0
                    causador = k.evento_de_decisao(decisao.decisao_id)
                    continue
                self.control.escalar(
                    wu.work_unit_id, "sem-alternativa", "humano",
                    detalhe="proximo executor fora do envelope aprovado: "
                            "fallback vetado, escalonamento em vez de tentativa",
                    causado_por=ev_conc.evento_id)
                return ResultadoExecucao("escalonado", attempt.attempt_id,
                                         "fallback-fora-do-envelope")

            self.control.escalar(
                wu.work_unit_id, "sem-alternativa", "humano",
                detalhe=f"alternativas esgotadas apos {resultado}",
                causado_por=ev_conc.evento_id)
            return ResultadoExecucao("escalonado", attempt.attempt_id,
                                     "sem-alternativa")

    def encerrar_com_falha(self, wu: ct.WorkUnit,
                           causado_por: str | None = None) -> None:
        """Falha nao-transitoria esgotada: WU segue para julgamento (D5 §2.1)."""
        self.kernel.transicionar_work_unit(
            wu.work_unit_id, "aguardando-validacao", causado_por)
