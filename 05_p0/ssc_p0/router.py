"""Task Router (D6 §2.2): transforma intencao em trabalho roteavel.

PROPOE; nao executa, nao julga, nao grava no log (emite fatos ao Kernel).
Toda decisao passa pelo veto da Policy antes de ser registrada.
Classificacao e DECLARADA; confianca 'baixa' = falha fechada (escalona).
Reroteamento = nova RoutingDecision que supersede a anterior.
"""

from . import contratos as ct
from .canonico import canonico, novo_id, sha256_de
from .catalogo import Catalogo
from .kernel import ControlPlane, SessionKernel
from .policy import PolicyGateway


class RotaVetada(Exception):
    """Policy vetou a decisao antes de qualquer gasto."""

    def __init__(self, vetos):
        super().__init__("; ".join(vetos))
        self.vetos = list(vetos)


class FalhaFechadaClassificacao(Exception):
    """confianca 'baixa': julgamento humano ou decomposicao, nunca improviso."""


class TaskRouter:
    def __init__(self, kernel: SessionKernel, policy: PolicyGateway,
                 catalogo: Catalogo, control: ControlPlane):
        self.kernel = kernel
        self.policy = policy
        self.catalogo = catalogo
        self.control = control

    def forjar(self, intencao: str, criterios: dict, tipo: str = "ato",
               tipo_decisao: str = "tipo-2", nivel: str = "L1",
               perfil: dict | None = None, classe: str = "C0",
               parent: str | None = None, depende_de: list | None = None,
               contexto_ref: str | None = None,
               causado_por: str | None = None) -> ct.WorkUnit:
        """Intake: despacho cru -> WorkUnit com criterios CONGELADOS.

        IW-4: classe >= C2 ou tipo-1 nasce aguardando-aprovacao; C0/C1 e
        tipo-2 recebem aprovacao automatica registrada (sem humano).
        """
        if len(intencao) > 4000:
            raise ct.FalhaContrato("intencao acima do teto de 4000 chars")
        criterios_ref = self.kernel.cas.gravar(canonico(criterios))
        if contexto_ref is None:
            pacote_vazio = self.kernel.montar_contexto(
                "pendente", [], exclusoes=["sem entradas: contexto minimo"])
            contexto_ref = pacote_vazio.hash_pacote
        wu = ct.WorkUnit(
            work_unit_id=novo_id(),
            sessao_id=self.kernel.envelope.sessao_id,
            linhagem_id=self.kernel.envelope.linhagem_id,
            parent_work_unit=parent,
            tipo=tipo, tipo_decisao=tipo_decisao, intencao=intencao,
            criterios_aceite_ref=criterios_ref,
            nivel_capacidade=nivel,
            perfil_capacidade=perfil or {
                "modalidade": "texto", "ferramentas": [],
                "formato_saida": "livre", "contexto_max_tokens": 8000,
                "dominio": "geral", "privacidade": "remoto-permitido",
                "latencia_max_ms": None, "orcamento_max_custo": None,
            },
            classe_governanca=classe, contexto_ref=contexto_ref,
            depende_de=list(depende_de or []), estado="proposta",
            resultado_ref=None, custo_medido=None,
        ).validado()
        ev = self.kernel.registrar_work_unit(wu, causado_por)
        if classe in ("C2", "C3") or tipo_decisao == "tipo-1":
            self.kernel.transicionar_work_unit(
                wu.work_unit_id, "aguardando-aprovacao", ev.evento_id)
        else:
            self.kernel.transicionar_work_unit(
                wu.work_unit_id, "aprovada", ev.evento_id,
                detalhe={"aprovacao": "automatica registrada (C0/C1, tipo-2)"})
        return wu

    @staticmethod
    def validar_plano(filhos_spec: list) -> None:
        """Valida um plano de decomposicao ANTES de qualquer registro.

        Cada spec: {'id', 'depende_de', ...}. Ciclo no grafo proposto =
        recusa antes de qualquer execucao (falha fechada).
        """
        grafo = {s["id"]: list(s.get("depende_de", [])) for s in filhos_spec}
        for sid, deps in grafo.items():
            for dep in deps:
                if dep not in grafo:
                    raise ct.FalhaContrato(
                        f"plano: depende_de desconhecido {dep!r} em {sid!r}")
        visitando, visitado = set(), set()

        def dfs(no):
            if no in visitando:
                raise ct.FalhaContrato(f"plano: ciclo detectado em {no!r}")
            if no in visitado:
                return
            visitando.add(no)
            for prox in grafo.get(no, []):
                dfs(prox)
            visitando.discard(no)
            visitado.add(no)

        for sid in grafo:
            dfs(sid)

    def decompor(self, pai: ct.WorkUnit, filhos: list,
                 causado_por: str | None = None) -> list:
        """Decomposicao: filhos com parent_work_unit; DAG validado no Kernel."""
        if pai.tipo != "decomposicao":
            raise ct.FalhaContrato("so WorkUnit 'decomposicao' recebe filhos")
        criados = []
        for espec in filhos:
            criados.append(self.forjar(
                parent=pai.work_unit_id, causado_por=causado_por, **espec))
        return criados

    def propor_decisao(self, wu: ct.WorkUnit, rota: str, selecao: dict,
                       confianca: str = "alta", metodo: str = "declarado",
                       alternativas: list | None = None,
                       custo_previsto: dict | None = None,
                       aprovacao_custo: dict | None = None,
                       motivo: str = "",
                       causado_por: str | None = None) -> ct.RoutingDecision:
        """Emite RoutingDecision ANTES da execucao, com veto da Policy.

        confianca 'baixa' = falha fechada: EscalationEvent 'ambiguidade',
        nenhuma decisao registrada, zero attempts.
        """
        if confianca == "baixa":
            self.control.escalar(
                wu.work_unit_id, "ambiguidade", "humano",
                detalhe="classificacao com confianca baixa: falha fechada",
                causado_por=causado_por)
            raise FalhaFechadaClassificacao(
                "confianca baixa: escalonado para julgamento humano")
        from .catalogo import ExecutorDesconhecido
        try:
            resolvido, _ = self.catalogo.resolver(selecao)
            nivel_atendido = self.catalogo.executores[
                resolvido["executor_id"]]["nivel"]
        except ExecutorDesconhecido:
            # Executor desconhecido: a decisao e montada mesmo assim para a
            # Policy VETAR com evento (falha fechada antes de qualquer gasto).
            nivel_atendido = wu.nivel_capacidade
        decisao = ct.RoutingDecision(
            decisao_id=novo_id(),
            work_unit_id=wu.work_unit_id,
            hash_pacote=wu.contexto_ref,
            classificacao={"rota": rota, "confianca": confianca,
                           "metodo": metodo},
            selecao=dict(selecao),
            nivel_capacidade_atendido=nivel_atendido,
            alternativas=list(alternativas or []),
            vinculos=self.kernel.vinculos_correntes(wu.contexto_ref),
            custo_previsto=custo_previsto or {"valor": 0.01,
                                              "rotulo": "estimado"},
            aprovacao_custo=aprovacao_custo,
            motivo=motivo,
            supersede=self.kernel.vigente.get(wu.work_unit_id),
        ).validado()
        vetos = self.policy.verificar_decisao(decisao, wu)
        if vetos:
            self.kernel.registrar_veto(decisao.to_dict(), vetos, causado_por)
            raise RotaVetada(vetos)
        self.kernel.registrar_decisao(decisao, causado_por)
        return decisao

    def rerotear(self, wu: ct.WorkUnit, **kwargs) -> ct.RoutingDecision:
        """Reroteamento: nova decisao que supersede a vigente (mesma linhagem)."""
        if self.kernel.vigente.get(wu.work_unit_id) is None:
            raise ct.FalhaContrato("reroteamento exige decisao vigente previa")
        return self.propor_decisao(wu, **kwargs)

    def reparar(self, reprovada: ct.WorkUnit, contexto_erro: dict,
                causado_por: str | None = None) -> ct.WorkUnit:
        """Reparo: nova WorkUnit filha tipo 'etapa' com o erro no contexto.

        NAO repete a mesma chamada: e WorkUnit + RoutingDecision novos.
        A filha pendura na reprovada (nao e irma: evita anti-competicao).
        """
        if reprovada.estado != "reprovada":
            raise ct.FalhaContrato("reparo exige workunit 'reprovada'")
        ref_erro = self.kernel.cas.gravar(canonico(contexto_erro))
        pacote = self.kernel.montar_contexto(
            reprovada.work_unit_id,
            [{"origem": f"erro:{ref_erro[:12]}", "papel": "artefato-anterior",
              "inclusao": "referencia", "conteudo": canonico(contexto_erro)}],
            exclusoes=["demais artefatos: reparo foca no erro"])
        filha = self.forjar(
            intencao=f"reparo de {reprovada.work_unit_id[:8]}: "
                     f"{reprovada.intencao[:200]}",
            criterios={"reparo_de": reprovada.work_unit_id,
                       "criterios_originais_ref": reprovada.criterios_aceite_ref},
            tipo="etapa", tipo_decisao=reprovada.tipo_decisao,
            nivel=reprovada.nivel_capacidade,
            perfil=reprovada.perfil_capacidade,
            classe=reprovada.classe_governanca,
            parent=reprovada.work_unit_id,
            contexto_ref=pacote.hash_pacote,
            causado_por=causado_por)
        return filha
