"""Execution Gateway (D6 §2.4): o braco.

EXECUTA; nao decide rota, nao se julga, nao grava no log (emite fatos ao
Kernel). Aplica a maquina de recuperacao (D5 §6 / D6 §4):

- retry: so falha transitoria, max 3, backoff com teto, respeitando
  Retry-After, e SO sob IR-1 (idempotency_key ou efeito nao-aplicado);
- fallback: proximo executor da ordem declarada, DENTRO do envelope;
- indeterminado (efeito incerto): SEM retry automatico, escalona (IR-2);
- 4xx de contrato: zero retry;
- esgotamento: EscalationEvent.
"""

from . import contratos as ct
from .canonico import canonico, novo_id, sha256_bytes
from .catalogo import Catalogo
from .kernel import ControlPlane, SessionKernel
from .policy import OrcamentoEstourado, PolicyGateway
from .providers import FakeProvider


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
                 control: ControlPlane):
        """providers: {(provedor, modelo): FakeProvider}."""
        self.kernel = kernel
        self.policy = policy
        self.catalogo = catalogo
        self.providers = providers
        self.control = control

    def _pacote(self, wu: ct.WorkUnit) -> dict:
        try:
            dados = self.kernel.cas.ler(wu.contexto_ref)
            import json
            return json.loads(dados)
        except Exception:
            return {}

    def executar(self, wu: ct.WorkUnit, decisao: ct.RoutingDecision,
                 idempotency_key: str | None = None,
                 entrada: bytes = b"") -> ResultadoExecucao:
        """Materializa attempts ate sucesso, fallback esgotado ou escalonamento."""
        k = self.kernel
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
                selecao_solicitada=dict(decisao.selecao),
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
            resposta = provider.invocar(entrada, pacote)
            # Captura estruturada OBRIGATORIA (D5 §5), mesmo em falha.
            saida_ref = k.cas.gravar(resposta.saida or b"")
            captura = {
                "saida_estruturada_ref": saida_ref,
                "saida_final_ref": saida_ref if resposta.ok else None,
            }
            observado = resposta.executor_observado
            if observado and (
                observado.get("modelo") != resolvido["modelo"]
                or observado.get("provedor") != resolvido["provedor"]
                or observado.get("effort") != resolvido["effort"]
            ):
                k.registrar_divergencia_executor(
                    attempt.attempt_id, resolvido, observado,
                    ev_desp.evento_id)
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

            if resultado == "falha-transitoria" and retries_feitos < 3:
                # IR-1: so se idempotente ou comprovadamente nao aplicada.
                if idempotency_key or resposta.efeito_externo == "nao-aplicado":
                    retries_feitos += 1
                    retry_after = resposta.retry_after_ms or 0
                    backoff = max(1000 * (2 ** (retries_feitos - 1)),
                                  retry_after)
                    retry = ct.RetryEvent(
                        retry_id=novo_id(),
                        attempt_id=attempt.attempt_id,
                        work_unit_id=wu.work_unit_id,
                        tentativa_n=retries_feitos + 1,
                        backoff_ms=backoff,
                        respeitou_retry_after=backoff >= retry_after,
                        idempotency_key=idempotency_key,
                        motivo="falha transitoria (429/5xx)",
                    ).validado()
                    ev_retry = k.registrar_retry(retry, ev_conc.evento_id)
                    causador = ev_retry.evento_id  # novo attempt aponta o retry
                    continue
                # IR-1 violado: sem retry; cai no caminho de fallback/escalona.

            # Fallback: proximo executor da ordem declarada, dentro do envelope.
            if idx + 1 < len(executores):
                proximo = executores[idx + 1]
                if self.policy.verificar_fallback_envelope(decisao, proximo):
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
                        motivo=f"{resultado} em {resolvido['modelo']}",
                    ).validado()
                    ev_fb = k.registrar_fallback(fallback, ev_conc.evento_id)
                    idx += 1
                    retries_feitos = 0
                    causador = ev_fb.evento_id
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
