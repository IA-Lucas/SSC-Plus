"""Contratos D5 v0.2.0 como dataclasses tipadas.

Cada contrato tem to_dict / from_dict / validate com round-trip exato.
Enum = lista fechada: valor fora da lista = falha de contrato, nunca coercao.
Falha de validacao e fechada: objeto que nao valida nao entra no EventLog.
"""

from dataclasses import dataclass, field, fields, asdict
from typing import Any, Optional

SCHEMA_VERSION = "ssc-p0/1"

# --- Enums fechados (D5) ---------------------------------------------------

ESTADOS_SESSAO = frozenset({"ativa", "suspensa", "retomada", "encerrada"})
ESTADOS_WORK_UNIT = frozenset({
    "proposta", "aguardando-aprovacao", "aprovada", "em-execucao",
    "aguardando-validacao", "concluida", "reprovada", "cancelada",
})
ESTADOS_ATTEMPT = frozenset({"criado", "despachado", "concluido", "orfao"})
RESULTADOS_ATTEMPT = frozenset({
    "sucesso", "falha-transitoria", "falha-contrato", "falha-quota",
    "falha-desconhecida", "indeterminado", "recusa",
})
EFEITOS_EXTERNO = frozenset({"nenhum", "aplicado", "nao-aplicado", "incerto"})
TIPOS_WORK_UNIT = frozenset({"ato", "decomposicao", "etapa", "revisao"})
TIPOS_DECISAO = frozenset({"tipo-1", "tipo-2"})
NIVEIS_CAPACIDADE = frozenset({"L1", "L2", "L3"})
CLASSES_GOVERNANCA = frozenset({"C0", "C1", "C2", "C3"})
CAMADAS_VEREDITO = frozenset({"deterministica", "juiz-llm", "humana"})
RESULTADOS_VEREDITO = frozenset({"aprovado", "reprovado", "inconclusivo"})
TIPOS_EVENTO = frozenset({
    "sessao", "work-unit", "routing", "attempt", "retry", "fallback",
    "escalation", "veredito", "checkpoint", "memoria", "orcamento",
})
MOTIVOS_ESCALONAMENTO = frozenset({
    "sem-alternativa", "orcamento", "ambiguidade", "aprovacao-humana",
    "juiz-reprovou", "indeterminado",
})
DESTINOS_ESCALONAMENTO = frozenset({"humano", "decompor", "abandonar"})
MODOS = frozenset({"read-only", "worktree", "escrita-aprovada"})
CONTROLES = frozenset({"autonomo", "confirma-no-gasto", "humano-no-loop"})
CONFIANCAS = frozenset({"alta", "baixa"})
METODOS_CLASSIFICACAO = frozenset({"declarado", "sensor", "llm"})
PAPEIS_ENTRADA = frozenset({
    "contrato", "evidencia", "memoria", "artefato-anterior", "norma-citada",
})
INCLUSOES = frozenset({"verbatim", "recorte", "referencia"})
MODALIDADES = frozenset({"texto", "codigo", "dados", "mista"})
FORMATOS_SAIDA = frozenset({"livre", "json-schema", "patch"})
PRIVACIDADES = frozenset({"local-only", "remoto-permitido"})


class FalhaContrato(ValueError):
    """Violacao de contrato: enum fora da lista, campo ausente, schema quebrado."""


def _enum(valor: Any, permitidos, caminho: str) -> None:
    if valor not in permitidos:
        raise FalhaContrato(f"{caminho}: valor fora do enum fechado: {valor!r}")


def _obrigatorio(valor: Any, caminho: str) -> None:
    if valor is None:
        raise FalhaContrato(f"{caminho}: campo obrigatorio ausente (None)")


def _tipo(valor: Any, tipos, caminho: str) -> None:
    if not isinstance(valor, tipos):
        raise FalhaContrato(f"{caminho}: tipo invalido ({type(valor).__name__})")


class ContratoBase:
    """Base: to_dict / from_dict com schema fechado e round-trip exato."""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, dados: dict):
        _tipo(dados, dict, cls.__name__)
        conhecidos = {f.name for f in fields(cls)}
        desconhecidos = set(dados) - conhecidos
        if desconhecidos:
            raise FalhaContrato(
                f"{cls.__name__}: campos fora do schema: {sorted(desconhecidos)}"
            )
        faltantes = conhecidos - set(dados)
        if faltantes:
            raise FalhaContrato(
                f"{cls.__name__}: campos ausentes: {sorted(faltantes)}"
            )
        return cls(**dados)

    def validate(self) -> None:
        raise NotImplementedError

    def validado(self):
        self.validate()
        return self


# --- SessionEnvelope (D5 §1) ------------------------------------------------

@dataclass
class SessionEnvelope(ContratoBase):
    sessao_id: str
    linhagem_id: str
    linhagem_origem: Optional[str]
    criado_em: str
    encerrado_em: Optional[str]
    estado: str
    escopo: dict
    permissoes: dict
    orcamento: dict
    politica_ref: str
    catalogo_ref: str
    integridade: dict
    contexto_ativo_ref: Optional[str]
    memoria_ref: Optional[str]
    resumo_aprovacao: dict

    def validate(self) -> None:
        _enum(self.estado, ESTADOS_SESSAO, "envelope.estado")
        _obrigatorio(self.sessao_id, "envelope.sessao_id")
        _obrigatorio(self.linhagem_id, "envelope.linhagem_id")
        _tipo(self.escopo, dict, "envelope.escopo")
        _enum(self.escopo.get("modo"), MODOS, "envelope.escopo.modo")
        _tipo(self.permissoes, dict, "envelope.permissoes")
        _tipo(self.orcamento, dict, "envelope.orcamento")
        _obrigatorio(self.politica_ref, "envelope.politica_ref")
        _obrigatorio(self.catalogo_ref, "envelope.catalogo_ref")
        _tipo(self.integridade, dict, "envelope.integridade")
        _tipo(self.resumo_aprovacao, dict, "envelope.resumo_aprovacao")


# --- WorkUnit (D5 §2) --------------------------------------------------------

@dataclass
class WorkUnit(ContratoBase):
    work_unit_id: str
    sessao_id: str
    linhagem_id: str
    parent_work_unit: Optional[str]
    tipo: str
    tipo_decisao: str
    intencao: str
    criterios_aceite_ref: str
    nivel_capacidade: str
    perfil_capacidade: dict
    classe_governanca: str
    contexto_ref: str
    depende_de: list
    estado: str
    resultado_ref: Optional[str]
    custo_medido: Optional[dict]

    def validate(self) -> None:
        _enum(self.tipo, TIPOS_WORK_UNIT, "workunit.tipo")
        _enum(self.tipo_decisao, TIPOS_DECISAO, "workunit.tipo_decisao")
        _enum(self.nivel_capacidade, NIVEIS_CAPACIDADE, "workunit.nivel_capacidade")
        _enum(self.classe_governanca, CLASSES_GOVERNANCA, "workunit.classe_governanca")
        _enum(self.estado, ESTADOS_WORK_UNIT, "workunit.estado")
        _tipo(self.intencao, str, "workunit.intencao")
        if len(self.intencao) > 4000:
            raise FalhaContrato("workunit.intencao: acima do teto de 4000 chars")
        _obrigatorio(self.criterios_aceite_ref, "workunit.criterios_aceite_ref")
        _obrigatorio(self.contexto_ref, "workunit.contexto_ref")
        _tipo(self.depende_de, list, "workunit.depende_de")
        perfil = self.perfil_capacidade
        _tipo(perfil, dict, "workunit.perfil_capacidade")
        _enum(perfil.get("modalidade"), MODALIDADES, "perfil.modalidade")
        _enum(perfil.get("formato_saida"), FORMATOS_SAIDA, "perfil.formato_saida")
        _enum(perfil.get("privacidade"), PRIVACIDADES, "perfil.privacidade")
        _tipo(perfil.get("ferramentas"), list, "perfil.ferramentas")


# --- ContextPackage (D5 §3) --------------------------------------------------

@dataclass
class ContextPackage(ContratoBase):
    contexto_id: str
    work_unit_id: str
    entradas: list
    politica_inclusao: dict
    custo_contexto_linhas: int
    exclusoes: list
    hash_pacote: str

    def validate(self) -> None:
        _obrigatorio(self.contexto_id, "contexto.contexto_id")
        _obrigatorio(self.work_unit_id, "contexto.work_unit_id")
        _tipo(self.entradas, list, "contexto.entradas")
        for i, entrada in enumerate(self.entradas):
            _tipo(entrada, dict, f"contexto.entradas[{i}]")
            _obrigatorio(entrada.get("origem"), f"contexto.entradas[{i}].origem")
            _obrigatorio(entrada.get("sha256"), f"contexto.entradas[{i}].sha256")
            _enum(entrada.get("papel"), PAPEIS_ENTRADA, f"contexto.entradas[{i}].papel")
            _enum(entrada.get("inclusao"), INCLUSOES, f"contexto.entradas[{i}].inclusao")
        _tipo(self.politica_inclusao, dict, "contexto.politica_inclusao")
        _tipo(self.custo_contexto_linhas, int, "contexto.custo_contexto_linhas")
        _tipo(self.exclusoes, list, "contexto.exclusoes")
        _obrigatorio(self.hash_pacote, "contexto.hash_pacote")


# --- RoutingDecision (D5 §4) -------------------------------------------------

@dataclass
class RoutingDecision(ContratoBase):
    decisao_id: str
    work_unit_id: str
    hash_pacote: str
    classificacao: dict
    selecao: dict
    nivel_capacidade_atendido: str
    alternativas: list
    vinculos: dict
    custo_previsto: Optional[dict]
    aprovacao_custo: Optional[dict]
    motivo: str
    supersede: Optional[str]

    def validate(self) -> None:
        _obrigatorio(self.decisao_id, "decisao.decisao_id")
        _obrigatorio(self.work_unit_id, "decisao.work_unit_id")
        _obrigatorio(self.hash_pacote, "decisao.hash_pacote")
        _enum(self.classificacao.get("confianca"), CONFIANCAS, "decisao.classificacao.confianca")
        _enum(self.classificacao.get("metodo"), METODOS_CLASSIFICACAO, "decisao.classificacao.metodo")
        _obrigatorio(self.classificacao.get("rota"), "decisao.classificacao.rota")
        _tipo(self.selecao, dict, "decisao.selecao")
        for campo in ("ferramenta", "provedor", "modelo", "effort"):
            _obrigatorio(self.selecao.get(campo), f"decisao.selecao.{campo}")
        _enum(self.selecao.get("modo"), MODOS, "decisao.selecao.modo")
        _enum(self.selecao.get("controle"), CONTROLES, "decisao.selecao.controle")
        _enum(self.nivel_capacidade_atendido, NIVEIS_CAPACIDADE, "decisao.nivel_capacidade_atendido")
        _tipo(self.alternativas, list, "decisao.alternativas")
        _tipo(self.vinculos, dict, "decisao.vinculos")
        for campo in ("hash_envelope", "hash_politica", "hash_permissoes",
                      "hash_aprovacao", "hash_catalogo", "hash_contexto"):
            _obrigatorio(self.vinculos.get(campo), f"decisao.vinculos.{campo}")
        if self.aprovacao_custo is not None:
            ap = self.aprovacao_custo
            _tipo(ap.get("modelos_permitidos"), list, "aprovacao_custo.modelos_permitidos")
            _tipo(ap.get("efforts_permitidos"), list, "aprovacao_custo.efforts_permitidos")
            _obrigatorio(ap.get("teto_custo"), "aprovacao_custo.teto_custo")
            _enum(ap.get("modo"), MODOS, "aprovacao_custo.modo")
            _obrigatorio(ap.get("validade"), "aprovacao_custo.validade")
            _tipo(ap.get("fallback_autorizado"), bool, "aprovacao_custo.fallback_autorizado")
        _tipo(self.motivo, str, "decisao.motivo")


# --- ExecutionAttempt (D5 §5) -------------------------------------------------

@dataclass
class ExecutionAttempt(ContratoBase):
    attempt_id: str
    work_unit_id: str
    decisao_id: str
    linhagem_id: str
    selecao_solicitada: dict
    executor_resolvido: dict
    executor_observado: Optional[dict]
    vinculos: dict
    inicio: Optional[str]
    fim: Optional[str]
    captura: dict
    resultado: Optional[str]
    efeito_externo: Optional[str]
    custo_medido: Optional[dict]
    artefato_ref: Optional[str]

    def validate(self) -> None:
        _obrigatorio(self.attempt_id, "attempt.attempt_id")
        _obrigatorio(self.work_unit_id, "attempt.work_unit_id")
        _obrigatorio(self.decisao_id, "attempt.decisao_id")
        _obrigatorio(self.linhagem_id, "attempt.linhagem_id")
        _tipo(self.selecao_solicitada, dict, "attempt.selecao_solicitada")
        _tipo(self.executor_resolvido, dict, "attempt.executor_resolvido")
        _tipo(self.vinculos, dict, "attempt.vinculos")
        if self.resultado is not None:
            _enum(self.resultado, RESULTADOS_ATTEMPT, "attempt.resultado")
        if self.efeito_externo is not None:
            _enum(self.efeito_externo, EFEITOS_EXTERNO, "attempt.efeito_externo")
        if self.resultado is not None:
            captura = self.captura
            _tipo(captura, dict, "attempt.captura")
            _obrigatorio(captura.get("saida_estruturada_ref"),
                         "attempt.captura.saida_estruturada_ref (obrigatoria)")

    def estado_terminal(self) -> bool:
        return self.resultado is not None


# --- Eventos de recuperacao (D5 §6) -------------------------------------------

@dataclass
class RetryEvent(ContratoBase):
    retry_id: str
    attempt_id: str
    work_unit_id: str
    tentativa_n: int
    backoff_ms: int
    respeitou_retry_after: bool
    idempotency_key: Optional[str]
    motivo: str

    def validate(self) -> None:
        _obrigatorio(self.retry_id, "retry.retry_id")
        _obrigatorio(self.attempt_id, "retry.attempt_id")
        _tipo(self.tentativa_n, int, "retry.tentativa_n")
        _tipo(self.backoff_ms, int, "retry.backoff_ms")
        _tipo(self.respeitou_retry_after, bool, "retry.respeitou_retry_after")


@dataclass
class FallbackEvent(ContratoBase):
    fallback_id: str
    attempt_id: str
    work_unit_id: str
    de_executor: dict
    para_executor: dict
    motivo: str

    def validate(self) -> None:
        _obrigatorio(self.fallback_id, "fallback.fallback_id")
        _obrigatorio(self.attempt_id, "fallback.attempt_id")
        _tipo(self.de_executor, dict, "fallback.de_executor")
        _tipo(self.para_executor, dict, "fallback.para_executor")
        _tipo(self.motivo, str, "fallback.motivo")


@dataclass
class EscalationEvent(ContratoBase):
    escalacao_id: str
    work_unit_id: Optional[str]
    motivo: str
    destino: str
    detalhe: Optional[str]

    def validate(self) -> None:
        _obrigatorio(self.escalacao_id, "escalacao.escalacao_id")
        _enum(self.motivo, MOTIVOS_ESCALONAMENTO, "escalacao.motivo")
        _enum(self.destino, DESTINOS_ESCALONAMENTO, "escalacao.destino")


# --- ValidationVerdict (D5 §7) -------------------------------------------------

@dataclass
class ValidationVerdict(ContratoBase):
    veredito_id: str
    alvo: dict
    camada: str
    verificador: dict
    pacote_juiz: dict
    criterios_ref: str
    contexto_ref: str
    independencia: dict
    resultado: str
    criterios: list
    efeitos: dict

    def validate(self) -> None:
        _obrigatorio(self.veredito_id, "veredito.veredito_id")
        _tipo(self.alvo, dict, "veredito.alvo")
        _enum(self.camada, CAMADAS_VEREDITO, "veredito.camada")
        _tipo(self.verificador, dict, "veredito.verificador")
        _tipo(self.pacote_juiz, dict, "veredito.pacote_juiz")
        _obrigatorio(self.criterios_ref, "veredito.criterios_ref")
        _obrigatorio(self.contexto_ref, "veredito.contexto_ref")
        _tipo(self.independencia, dict, "veredito.independencia")
        _enum(self.resultado, RESULTADOS_VEREDITO, "veredito.resultado")
        _tipo(self.criterios, list, "veredito.criterios")
        _tipo(self.efeitos, dict, "veredito.efeitos")


# --- Checkpoint (D5 §8.3) -------------------------------------------------------

@dataclass
class Checkpoint(ContratoBase):
    checkpoint_id: str
    sessao_id: str
    linhagem_id: str
    estado_refs: dict
    ponto_de_retomada: dict
    validacao: dict
    selo: str

    def validate(self) -> None:
        _obrigatorio(self.checkpoint_id, "checkpoint.checkpoint_id")
        _obrigatorio(self.sessao_id, "checkpoint.sessao_id")
        _obrigatorio(self.linhagem_id, "checkpoint.linhagem_id")
        _tipo(self.estado_refs, dict, "checkpoint.estado_refs")
        _obrigatorio(self.estado_refs.get("ultimo_evento_hash"),
                     "checkpoint.estado_refs.ultimo_evento_hash")
        _obrigatorio(self.estado_refs.get("seq"), "checkpoint.estado_refs.seq")
        _tipo(self.ponto_de_retomada, dict, "checkpoint.ponto_de_retomada")
        _tipo(self.validacao, dict, "checkpoint.validacao")
        _obrigatorio(self.selo, "checkpoint.selo")


# --- Evento do EventLog (D5 §8.2) ------------------------------------------------

@dataclass
class Evento(ContratoBase):
    evento_id: str
    seq: int
    ts: str
    schema_version: str
    linhagem_id: str
    tipo: str
    causado_por: Optional[str]
    idempotency_key: str
    prev_event_hash: str
    payload_ref: str

    def validate(self) -> None:
        _obrigatorio(self.evento_id, "evento.evento_id")
        _tipo(self.seq, int, "evento.seq")
        if self.seq < 1:
            raise FalhaContrato("evento.seq: deve ser inteiro >= 1")
        _obrigatorio(self.ts, "evento.ts")
        if self.schema_version != SCHEMA_VERSION:
            raise FalhaContrato(
                f"evento.schema_version: esperado {SCHEMA_VERSION!r}, "
                f"veio {self.schema_version!r}"
            )
        _obrigatorio(self.linhagem_id, "evento.linhagem_id")
        _enum(self.tipo, TIPOS_EVENTO, "evento.tipo")
        _obrigatorio(self.idempotency_key, "evento.idempotency_key")
        _obrigatorio(self.prev_event_hash, "evento.prev_event_hash")
        _obrigatorio(self.payload_ref, "evento.payload_ref")
