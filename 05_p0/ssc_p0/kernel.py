"""Session Kernel (D6 §2.1) + Control Plane minimo (D6 §2.5).

O Kernel e o UNICO escritor do EventLog. Router, Policy, Execution, Judge e
Control Plane emitem fatos ao Kernel; o Evidence Plane apenas le.

Responsabilidades: SessionEnvelope, ContextPackage (IC-1..IC-5), memoria,
Checkpoint (IP-1..IP-4), EventLog, CAS, maquinas de estado, vinculos (6
hashes), scanner deterministico de segredos (IC-4), attempt orfao na
retomada (D6 §4).

Control Plane: ciclo de vida da sessao, escalonamento e aprovacao humana
(ato explicito, datado, hasheado; silencio nunca aprova). Apresenta e
registra; nao decide rota.
"""

import copy
import hashlib
import hmac as hmac_mod
import json
import os
import re
import threading

from . import contratos as ct
from .canonico import Relogio, RelogioReal, canonico, novo_id, sha256_bytes, sha256_de
from .cas import CAS, CorrupcaoDetectada, ler_arquivo_contido
from .estados import (TransicaoIlegal, marcar_orfao, transitar_attempt,
                      transitar_sessao, transitar_workunit)
from .eventlog import EventLog, EventoAdulterado, hash_evento
from .writelock import LockSessao


class SegredoDetectado(Exception):
    """IC-4: padrao de segredo detectado em payload de evento ou contexto."""


class VinculoDivergente(ct.FalhaContrato):
    """Attempt/decisao com vinculos divergentes do estado corrente (RA-3)."""


class DecisaoMutada(ct.FalhaContrato):
    """RoutingDecision alterada apos o registro: execucao recusada (0.2.1-1)."""


class CheckpointInvalido(Exception):
    """IP-2: checkpoint invalido, cadeia quebrada ou selo divergente."""


# IDs locais sao UUID-4 hex (novo_id); usados em nomes de arquivo, nunca
# interpolados sem validacao (0.2.1-10).
_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def _validar_id(valor, rotulo: str) -> None:
    if not isinstance(valor, str) or not _ID_RE.match(valor):
        raise ct.FalhaContrato(f"{rotulo}: id invalido para uso em caminho")


# Scanner deterministico de segredos (IC-4). Deteccao = recusa, nunca redacao.
PADROES_SEGREDO = [
    re.compile(p) for p in (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"AKIA[0-9A-Z]{16}",
        r"ghp_[A-Za-z0-9]{30,}",
        r"sk-[A-Za-z0-9]{20,}",
        r"xox[baprs]-[A-Za-z0-9-]{10,}",
        r"(?i)(api[_-]?key|secret|senha|password|passwd)[\"'\s]*[:=]"
        r"[\"'\s]*[A-Za-z0-9_./+\-]{8,}",
    )
]


def escanear_segredos(dados: bytes, rotulo: str) -> None:
    texto = dados.decode("utf-8", errors="replace")
    for padrao in PADROES_SEGREDO:
        if padrao.search(texto):
            raise SegredoDetectado(f"IC-4: segredo detectado em {rotulo}")


def _similaridade(a: str, b: str) -> float:
    """Jaccard de tokens para a regra anti-competicao (IW-3)."""
    ta = {t for t in re.split(r"[^a-z0-9]+", a.lower()) if t}
    tb = {t for t in re.split(r"[^a-z0-9]+", b.lower()) if t}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


LIMIAR_ANTI_COMPETICAO = 0.6
MAX_FILHOS_DECOMPOSICAO = 12
VERBATIM_ATE_DEFAULT = 200 * 1024


class SessionKernel:
    """Coracao da sessao logica. Nao roteia, nao executa, nao julga."""

    def __init__(self, raiz, relogio: Relogio | None = None,
                 raizes_fontes=None, resolvedor=os.path.realpath):
        self.raiz = os.path.realpath(str(raiz))
        os.makedirs(self.raiz, exist_ok=True)
        for sub in ("logs", "checkpoints", "sessoes", "locks"):
            os.makedirs(os.path.join(self.raiz, sub), exist_ok=True)
        self.cas = CAS(os.path.join(self.raiz, "cas"))
        self.relogio = relogio or RelogioReal()
        self.resolvedor = resolvedor
        self.raizes_fontes = [self.raiz] + [
            os.path.normpath(resolvedor(str(r))) for r in (raizes_fontes or [])
        ]
        self._lock = threading.RLock()
        self.chave_selo = self._carregar_chave()
        # Escritor unico entre processos (0.2.1-4): lock/lease + fencing.
        self._lock_sessao: LockSessao | None = None
        # Estado vivo (reconstruivel pelo log, IP-4).
        self.log: EventLog | None = None
        self.envelope: ct.SessionEnvelope | None = None
        self.work_units: dict[str, ct.WorkUnit] = {}
        self.decisoes: dict[str, ct.RoutingDecision] = {}
        self.vigente: dict[str, str] = {}       # work_unit_id -> decisao_id
        self.attempts: dict[str, dict] = {}     # attempt_id -> {attempt, estado}
        self.memoria: list = []
        self.memoria_ref: str | None = None
        self.vereditos: list = []
        self.vereditos_recusados: list = []
        self.escalacoes: list = []
        self.retries: list = []
        self.fallbacks: list = []
        self.recusas: list = []
        self.checkpoints: list = []
        self._evento_routing: dict[str, str] = {}  # decisao_id -> evento_id
        self._hashes_decisao: dict[str, str] = {}  # decisao_id -> sha256 canonico
        self._eventos_vistos: set = set()          # cadeia causal da sessao

    # -- infraestrutura interna -------------------------------------------

    def _carregar_chave(self) -> bytes:
        caminho = os.path.join(self.raiz, "chave_selo.bin")
        if os.path.exists(caminho):
            with open(caminho, "rb") as f:
                return f.read()
        chave = os.urandom(32)
        tmp = caminho + ".tmp"
        with open(tmp, "wb") as f:
            f.write(chave)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho)
        return chave

    def _selo(self, dados_canonicos: bytes) -> str:
        return hmac_mod.new(self.chave_selo, dados_canonicos,
                            hashlib.sha256).hexdigest()

    def _log_path(self, sessao_id: str) -> str:
        _validar_id(sessao_id, "sessao_id")
        return os.path.join(self.raiz, "logs", f"{sessao_id}.jsonl")

    # -- escritor unico entre processos (0.2.1-4) ----------------------------

    def _adquirir_lock(self, sessao_id: str) -> None:
        _validar_id(sessao_id, "sessao_id")
        base = os.path.join(self.raiz, "locks", sessao_id)
        self._lock_sessao = LockSessao(base + ".lock", base + ".fence")
        self._lock_sessao.adquirir()

    def fechar(self) -> None:
        """Libera o lock da sessao (handoff limpo e explicito do escritor)."""
        if self._lock_sessao is not None:
            self._lock_sessao.liberar()

    def _simular_crash(self) -> None:
        """SO TESTE: morte do processo. O escritor fica obsoleto (fencing)."""
        if self._lock_sessao is not None:
            self._lock_sessao.simular_crash()

    # -- snapshot do estado vivo (reducer validado antes do append, 0.2.1-3) --

    _ESTADO_MUTAVEL = (
        "envelope", "work_units", "decisoes", "vigente", "attempts",
        "memoria", "memoria_ref", "vereditos", "vereditos_recusados",
        "escalacoes", "retries", "fallbacks", "recusas", "checkpoints",
        "_evento_routing", "_hashes_decisao", "_eventos_vistos",
    )

    def _snapshot_estado(self) -> dict:
        return {nome: copy.deepcopy(getattr(self, nome))
                for nome in self._ESTADO_MUTAVEL}

    def _restaurar_estado(self, backup: dict) -> None:
        for nome, valor in backup.items():
            setattr(self, nome, valor)

    def _garantir_ativa(self) -> None:
        """retomada -> ativa na primeira operacao pos-retomada (D5 §1.2)."""
        if self.envelope is not None and self.envelope.estado == "retomada":
            self._emitir("sessao", {"acao": "reativar",
                                    "sessao_id": self.envelope.sessao_id},
                         causado_por=None, _sem_garantia=True)

    def _emitir(self, tipo: str, payload: dict, causado_por,
                idempotency_key: str | None = None,
                _sem_garantia: bool = False) -> tuple[ct.Evento, bool]:
        """Unico caminho de escrita no EventLog (escritor unico).

        0.2.1-3: o reducer (_aplicar) e validado ANTES do append; se a fold
        ou o append falham, nada fica duravel e o estado vivo e restaurado.
        0.2.1-4: fencing token verificado a cada escrita.
        0.2.1-11: causado_por precisa existir na cadeia desta sessao.
        """
        with self._lock:
            if not _sem_garantia:
                self._garantir_ativa()
            if causado_por is not None \
                    and causado_por not in self._eventos_vistos:
                raise ct.FalhaContrato(
                    f"causado_por fora da cadeia da sessao: {causado_por!r}")
            if self._lock_sessao is not None:
                self._lock_sessao.verificar()  # fencing (escritor unico)
            dados = canonico(payload)
            escanear_segredos(dados, f"payload de evento {tipo}")  # IC-4
            payload_ref = self.cas.gravar(dados)
            evento = ct.Evento(
                evento_id=novo_id(),
                seq=self.log.proxima_seq(),
                ts=self.relogio.agora(),
                schema_version=ct.SCHEMA_VERSION,
                linhagem_id=self.envelope.linhagem_id,
                tipo=tipo,
                causado_por=causado_por,
                idempotency_key=idempotency_key or novo_id(),
                prev_event_hash=self.log.ultimo_hash(),
                payload_ref=payload_ref,
            )
            backup = self._snapshot_estado()
            try:
                # Reducer executado ANTES do append; se a fold ou o append
                # falham, o estado vivo e restaurado e nada fica duravel.
                self._aplicar(evento, payload)
                criado = self.log.anexar(evento)
            except BaseException:
                self._restaurar_estado(backup)
                raise
            if not criado:
                # Reentrega identica (idempotencia): aceita, sem efeito.
                self._restaurar_estado(backup)
            return evento, criado

    # -- abertura / ciclo de vida ------------------------------------------

    def abrir_sessao(self, escopo: dict, permissoes: dict, orcamento: dict,
                     politica_ref: str, catalogo_ref: str,
                     resumo_aprovacao: dict,
                     linhagem_origem: str | None = None,
                     linhagem_id: str | None = None,
                     causado_por: str | None = None) -> ct.SessionEnvelope:
        """Abertura aprovada (portao de custo/autonomia ja passou fora)."""
        sessao_id = novo_id()
        if linhagem_id is None:
            linhagem_id = sessao_id  # primeira sessao da linhagem (D5 §1.1)
        base = {
            "sessao_id": sessao_id, "linhagem_id": linhagem_id,
            "linhagem_origem": linhagem_origem,
            "criado_em": self.relogio.agora(), "encerrado_em": None,
            "estado": "ativa", "escopo": escopo, "permissoes": permissoes,
            "orcamento": orcamento, "politica_ref": politica_ref,
            "catalogo_ref": catalogo_ref,
            "contexto_ativo_ref": None, "memoria_ref": None,
            "resumo_aprovacao": resumo_aprovacao,
        }
        integridade = {
            "assinatura_insumos": sha256_de({
                "repo_alvo": escopo.get("repo_alvo"),
                "politica_ref": politica_ref, "catalogo_ref": catalogo_ref,
                "permissoes": permissoes,
            }),
            "selo": self._selo(canonico(base)),
        }
        envelope = ct.SessionEnvelope(integridade=integridade, **base).validado()
        hash_genese = sha256_de(envelope.to_dict())
        self._adquirir_lock(sessao_id)  # escritor unico (0.2.1-4)
        self.log = EventLog(self._log_path(sessao_id), hash_genese)
        caminho_env = os.path.join(self.raiz, "sessoes", f"{sessao_id}.envelope.json")
        tmp = caminho_env + ".tmp"
        with open(tmp, "wb") as f:
            f.write(canonico(envelope.to_dict()))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, caminho_env)
        self.envelope = envelope  # _aplicar('abrir') reatribui o mesmo objeto
        self._emitir("sessao", {"acao": "abrir", "envelope": envelope.to_dict()},
                     causado_por=causado_por, _sem_garantia=True)
        return envelope

    def evento_de_decisao(self, decisao_id: str) -> str | None:
        return self._evento_routing.get(decisao_id)

    # -- vinculos (D5 §4, RA-3) ---------------------------------------------

    def _envelope_estavel(self) -> dict:
        """Envelope sem campos volateis (estado, consumidos, refs de cabeca)."""
        dados = self.envelope.to_dict()
        dados.pop("estado")
        dados.pop("contexto_ativo_ref")
        dados.pop("memoria_ref")
        dados["orcamento"] = {k: v for k, v in dados["orcamento"].items()
                              if not k.startswith("consumido_")}
        return dados

    def vinculos_correntes(self, hash_contexto: str) -> dict:
        return {
            "hash_envelope": sha256_de(self._envelope_estavel()),
            "hash_politica": self.envelope.politica_ref,
            "hash_permissoes": sha256_de(self.envelope.permissoes),
            "hash_aprovacao": sha256_de(self.envelope.resumo_aprovacao),
            "hash_catalogo": self.envelope.catalogo_ref,
            "hash_contexto": hash_contexto,
        }

    # -- WorkUnits -----------------------------------------------------------

    def _filhos_de(self, parent_id: str | None) -> list:
        return [w for w in self.work_units.values()
                if w.parent_work_unit == parent_id]

    def _checar_ciclo(self, wu: ct.WorkUnit) -> None:
        """Grafo aciclico: cadeia de pais e arestas depende_de (IW/D5 §2)."""
        # Cadeia de pais
        atual = wu.parent_work_unit
        while atual is not None:
            if atual == wu.work_unit_id:
                raise ct.FalhaContrato("ciclo via parent_work_unit")
            pai = self.work_units.get(atual)
            atual = pai.parent_work_unit if pai else None
        # Ciclo em depende_de (DFS a partir das dependencias da nova WU)
        grafo = {wid: list(w.depende_de) for wid, w in self.work_units.items()}
        grafo[wu.work_unit_id] = list(wu.depende_de)
        visitando, visitado = set(), set()

        def dfs(no):
            if no in visitando:
                raise ct.FalhaContrato(f"ciclo via depende_de em {no!r}")
            if no in visitado:
                return
            visitando.add(no)
            for prox in grafo.get(no, []):
                dfs(prox)
            visitando.discard(no)
            visitado.add(no)

        dfs(wu.work_unit_id)

    def registrar_work_unit(self, wu: ct.WorkUnit,
                            causado_por: str | None) -> ct.Evento:
        """Forja/decomposicao. Valida DAG, <=12 filhos, anti-competicao."""
        wu.validate()
        if wu.estado != "proposta":
            raise ct.FalhaContrato("workunit nasce em 'proposta'")
        if wu.sessao_id != self.envelope.sessao_id:
            raise ct.FalhaContrato("workunit de outra sessao")
        if wu.linhagem_id != self.envelope.linhagem_id:
            raise ct.FalhaContrato("workunit de outra linhagem (IS-1)")
        if wu.work_unit_id in self.work_units:
            raise ct.FalhaContrato("work_unit_id duplicado")
        # 0.2.1-7: o ContextPackage precisa existir no CAS, integro, ligado
        # a ESTA work_unit_id — falha fechada, nunca pacote vazio.
        self.ler_pacote(wu.contexto_ref, wu.work_unit_id)
        for dep in wu.depende_de:
            if dep not in self.work_units:
                raise ct.FalhaContrato(f"depende_de desconhecido: {dep!r}")
        if wu.parent_work_unit is not None:
            pai = self.work_units.get(wu.parent_work_unit)
            if pai is None:
                raise ct.FalhaContrato("parent_work_unit desconhecido")
            if len(self._filhos_de(pai.work_unit_id)) >= MAX_FILHOS_DECOMPOSICAO:
                self._registrar_recusa("work-unit", wu.to_dict(),
                                       "IW-2: decomposicao com mais de 12 filhos",
                                       causado_por)
                raise ct.FalhaContrato("IW-2: mais de 12 filhos diretos")
            for irma in self._filhos_de(pai.work_unit_id):
                sim = _similaridade(wu.intencao, irma.intencao)
                if sim >= LIMIAR_ANTI_COMPETICAO:
                    self._registrar_recusa(
                        "work-unit", wu.to_dict(),
                        f"IW-3: intencao sobreposta com {irma.work_unit_id} "
                        f"(similaridade {sim:.2f})", causado_por)
                    raise ct.FalhaContrato(
                        f"IW-3: anti-competicao com {irma.work_unit_id}")
        try:
            self._checar_ciclo(wu)
        except ct.FalhaContrato as exc:
            self._registrar_recusa("work-unit", wu.to_dict(), str(exc),
                                   causado_por)
            raise
        evento, _ = self._emitir(
            "work-unit", {"acao": "registrar", "work_unit": wu.to_dict()},
            causado_por=causado_por)
        return evento

    def _registrar_recusa(self, tipo: str, objeto: dict, motivo: str,
                          causado_por: str | None) -> None:
        """Recusa com evento, quando ha contexto suficiente (D5 §2.1)."""
        if self.log is None:
            return
        self._emitir(tipo, {"acao": "recusa", "objeto": objeto, "motivo": motivo},
                     causado_por=causado_por)

    def transicionar_work_unit(self, work_unit_id: str, para: str,
                               causado_por: str | None,
                               detalhe: dict | None = None) -> ct.Evento:
        wu = self.work_units[work_unit_id]
        transitar_workunit(wu.estado, para)
        if para == "em-execucao" and wu.estado == "aprovada":
            for dep in wu.depende_de:
                if self.work_units[dep].estado != "concluida":
                    raise ct.FalhaContrato(
                        f"dependencia {dep!r} nao concluida (ordem topologica)")
            if self.vigente.get(work_unit_id) is None:
                raise ct.FalhaContrato("IW-1: sem RoutingDecision vigente")
        evento, _ = self._emitir(
            "work-unit",
            {"acao": "transicao", "work_unit_id": work_unit_id,
             "de": wu.estado, "para": para, "detalhe": detalhe},
            causado_por=causado_por)
        return evento

    # -- RoutingDecision -----------------------------------------------------

    def registrar_decisao(self, decisao: ct.RoutingDecision,
                          causado_por: str | None) -> ct.Evento:
        decisao.validate()
        if decisao.work_unit_id not in self.work_units:
            raise ct.FalhaContrato("decisao para workunit desconhecida")
        esperados = self.vinculos_correntes(decisao.hash_pacote)
        if decisao.vinculos != esperados:
            raise VinculoDivergente(
                "vinculos da decisao divergem do estado corrente")
        atual = self.vigente.get(decisao.work_unit_id)
        if atual is not None and decisao.supersede != atual:
            raise ct.FalhaContrato(
                "reroteamento exige supersede = decisao vigente")
        evento, _ = self._emitir(
            "routing", {"acao": "registrar", "decisao": decisao.to_dict()},
            causado_por=causado_por)
        return evento

    def registrar_veto(self, decisao_dict: dict, vetos: list,
                       causado_por: str | None) -> ct.Evento:
        evento, _ = self._emitir(
            "routing", {"acao": "veto", "decisao": decisao_dict, "vetos": vetos},
            causado_por=causado_por)
        return evento

    def decisao_canonica(self, decisao_id: str) -> ct.RoutingDecision:
        """A UNICA copia executavel da decisao: a registrada no log (0.2.1-1).

        A decisao completa e persistida (payload no CAS) e hasheada no
        registro. Qualquer mutacao posterior — selecao, alternativas, custo,
        hashes, aprovacao — diverge do hash registrado e e recusada.
        """
        dec = self.decisoes.get(decisao_id)
        if dec is None:
            raise ct.FalhaContrato(f"decisao desconhecida: {decisao_id!r}")
        if sha256_de(dec.to_dict()) != self._hashes_decisao.get(decisao_id):
            raise DecisaoMutada(
                f"RoutingDecision {decisao_id[:8]} mutada apos o registro: "
                "a execucao usa somente a copia canonica registrada")
        return dec

    # -- Attempts --------------------------------------------------------------

    def criar_attempt(self, attempt: ct.ExecutionAttempt,
                      causado_por: str | None) -> ct.Evento:
        attempt.validate()
        wu = self.work_units[attempt.work_unit_id]
        if attempt.linhagem_id != self.envelope.linhagem_id:
            raise VinculoDivergente("attempt de outra linhagem (IS-1)")
        # 0.2.1-1: a decisao do attempt e a copia canonica registrada;
        # mutacao posterior = recusa antes de qualquer gasto.
        decisao = self.decisao_canonica(attempt.decisao_id)
        if self.vigente.get(attempt.work_unit_id) != attempt.decisao_id:
            self._registrar_recusa(
                "attempt", attempt.to_dict(),
                "decisao supersedada: attempt recusado antes do gasto (RA-3)",
                causado_por)
            raise VinculoDivergente(
                "RoutingDecision supersedada: attempt recusado antes do gasto")
        esperados = self.vinculos_correntes(decisao.hash_pacote)
        if attempt.vinculos != esperados:
            self._registrar_recusa(
                "attempt", attempt.to_dict(),
                "vinculos divergentes do estado corrente (RA-3)", causado_por)
            raise VinculoDivergente("vinculos do attempt divergentes")
        if wu.estado == "aprovada":
            self.transicionar_work_unit(wu.work_unit_id, "em-execucao",
                                        causado_por)
        elif wu.estado == "em-execucao":
            # Novo attempt na mesma WU (retry/fallback/reroteamento autorizado)
            self.transicionar_work_unit(wu.work_unit_id, "em-execucao",
                                        causado_por)
        else:
            raise TransicaoIlegal(
                f"workunit {wu.estado!r} nao aceita attempt")
        evento, _ = self._emitir(
            "attempt", {"acao": "criar", "attempt": attempt.to_dict()},
            causado_por=causado_por)
        return evento

    def despachar_attempt(self, attempt_id: str,
                          causado_por: str | None) -> ct.Evento:
        reg = self.attempts[attempt_id]
        transitar_attempt(reg["estado"], "despachado")
        attempt = reg["attempt"]
        attempt.inicio = self.relogio.agora()
        evento, _ = self._emitir(
            "attempt", {"acao": "despachar", "attempt": attempt.to_dict()},
            causado_por=causado_por)
        return evento

    def concluir_attempt(self, attempt_id: str, resultado: str,
                         efeito_externo: str, captura: dict,
                         executor_observado: dict | None,
                         custo_medido: dict | None,
                         artefato_ref: str | None,
                         causado_por: str | None) -> ct.Evento:
        reg = self.attempts[attempt_id]
        transitar_attempt(reg["estado"], "concluido")
        if resultado not in ct.RESULTADOS_ATTEMPT:
            raise ct.FalhaContrato(f"resultado fora do enum: {resultado!r}")
        if efeito_externo == "incerto" and resultado != "indeterminado":
            raise ct.FalhaContrato(
                "efeito_externo=incerto => resultado=indeterminado (D5 §5)")
        attempt = reg["attempt"]
        attempt.fim = self.relogio.agora()
        attempt.resultado = resultado
        attempt.efeito_externo = efeito_externo
        attempt.captura = captura
        attempt.executor_observado = executor_observado
        attempt.custo_medido = custo_medido
        attempt.artefato_ref = artefato_ref
        attempt.validate()
        evento, _ = self._emitir(
            "attempt", {"acao": "concluir", "attempt": attempt.to_dict()},
            causado_por=causado_por)
        if custo_medido:
            self._emitir(
                "orcamento",
                {"acao": "consumo",
                 "custo": custo_medido.get("valor", 0.0),
                 "tokens": custo_medido.get("tokens", 0),
                 "rotulo": custo_medido.get("rotulo", "simulado"),
                 "attempt_id": attempt_id},
                causado_por=evento.evento_id)
        return evento

    def registrar_divergencia_executor(self, attempt_id: str,
                                       resolvido: dict, observado: dict,
                                       causado_por: str | None) -> ct.Evento:
        """Evento tipado: observado != resolvido (alias nao prova identidade)."""
        evento, _ = self._emitir(
            "attempt",
            {"acao": "divergencia-observada", "attempt_id": attempt_id,
             "resolvido": resolvido, "observado": observado},
            causado_por=causado_por)
        return evento

    # -- Recuperacao (D5 §6) ----------------------------------------------------

    def registrar_retry(self, retry: ct.RetryEvent,
                        causado_por: str | None) -> ct.Evento:
        # 0.2.1-12: tentativa_n em 1..3 e backoff com teto — impostos pelo
        # contrato (RetryEvent.validate), falha fechada fora dos limites.
        retry.validate()
        evento, _ = self._emitir("retry", {"acao": "registrar",
                                           "retry": retry.to_dict()},
                                 causado_por=causado_por)
        return evento

    def registrar_fallback(self, fallback: ct.FallbackEvent,
                           causado_por: str | None) -> ct.Evento:
        fallback.validate()
        evento, _ = self._emitir("fallback", {"acao": "registrar",
                                              "fallback": fallback.to_dict()},
                                 causado_por=causado_por)
        return evento

    def registrar_escalacao(self, escalacao: ct.EscalationEvent,
                            causado_por: str | None) -> ct.Evento:
        escalacao.validate()
        evento, _ = self._emitir("escalation", {"acao": "registrar",
                                                "escalacao": escalacao.to_dict()},
                                 causado_por=causado_por)
        return evento

    # -- Vereditos (D5 §7) --------------------------------------------------------

    def registrar_veredito(self, veredito: ct.ValidationVerdict,
                           causado_por: str | None,
                           transicionar: bool = True) -> ct.Evento:
        """Registra o veredito. `transicionar=False` mantem a WU em
        aguardando-validacao (ha camada de julgamento seguinte)."""
        veredito.validate()
        attempt_id = veredito.alvo.get("attempt_id")
        if not attempt_id or attempt_id not in self.attempts:
            raise ct.FalhaContrato(
                "veredito sem attempt_id valido e invalido (D5 §7)")
        reg = self.attempts[attempt_id]
        if reg["estado"] != "concluido":
            raise ct.FalhaContrato(
                "veredito exige attempt concluido (mesma cadeia)")
        attempt = reg["attempt"]
        wu_id = veredito.alvo.get("work_unit_id")
        wu = self.work_units.get(wu_id)
        if wu is None:
            raise ct.FalhaContrato("veredito para workunit desconhecida")
        # 0.2.1-2: attempt, WorkUnit, decisao, contexto, criterios e artefato
        # precisam pertencer a MESMA cadeia; attempt de A nunca conclui B.
        if attempt.work_unit_id != wu_id:
            raise ct.FalhaContrato(
                "veredito cruzado: o attempt pertence a outra WorkUnit")
        decisao = self.decisoes.get(attempt.decisao_id)
        if decisao is None or decisao.work_unit_id != wu_id:
            raise ct.FalhaContrato(
                "decisao do attempt fora da cadeia da WorkUnit")
        if attempt.linhagem_id != self.envelope.linhagem_id \
                or wu.linhagem_id != self.envelope.linhagem_id:
            raise ct.FalhaContrato("veredito fora da linhagem da sessao")
        if veredito.criterios_ref != wu.criterios_aceite_ref:
            raise ct.FalhaContrato(
                "IV-3: criterios_ref divergente do congelado da WorkUnit")
        if veredito.alvo.get("artefato_ref") != attempt.artefato_ref:
            raise ct.FalhaContrato(
                "artefato do veredito fora da cadeia do attempt")
        if veredito.contexto_ref != wu.contexto_ref:
            raise ct.FalhaContrato(
                "contexto_ref do veredito diverge do da WorkUnit")
        # IV-2: reprovado deterministico NAO e anulavel sobre o mesmo artefato.
        for v in self.vereditos:
            if (v.alvo.get("attempt_id") == attempt_id
                    and v.camada == "deterministica"
                    and v.resultado == "reprovado"):
                self._registrar_recusa(
                    "veredito", veredito.to_dict(),
                    "IV-2: veto deterministico nao anulavel por "
                    f"{veredito.camada} sobre o mesmo artefato", causado_por)
                self.vereditos_recusados.append(veredito.to_dict())
                raise ct.FalhaContrato(
                    "IV-2: veto deterministico nao anulavel")
        if veredito.camada == "juiz-llm":
            passou_det = any(
                v.alvo.get("attempt_id") == attempt_id
                and v.camada == "deterministica" and v.resultado == "aprovado"
                for v in self.vereditos)
            if not passou_det:
                raise ct.FalhaContrato(
                    "juiz-llm so julga o que passou na camada deterministica")
            indep = veredito.independencia
            if not (indep.get("provedor_distinto_do_executor")
                    and indep.get("modelo_distinto")):
                raise ct.FalhaContrato("IV-1: juiz sem independencia")
        if wu.estado != "aguardando-validacao":
            raise TransicaoIlegal(
                f"veredito com workunit em {wu.estado!r}")
        evento, _ = self._emitir("veredito", {"acao": "registrar",
                                              "veredito": veredito.to_dict()},
                                 causado_por=causado_por)
        if not transicionar:
            return evento
        if veredito.resultado == "aprovado":
            self.transicionar_work_unit(wu_id, "concluida", evento.evento_id)
        elif veredito.resultado == "reprovado":
            self.transicionar_work_unit(wu_id, "reprovada", evento.evento_id)
        return evento

    # -- Memoria da sessao ---------------------------------------------------------

    def registrar_memoria(self, entrada: dict,
                          causado_por: str | None) -> ct.Evento:
        """Append-only; cada entrada com fonte e validade (D5 §1)."""
        if "fonte" not in entrada or "validade" not in entrada:
            raise ct.FalhaContrato("memoria exige fonte e validade por entrada")
        evento, _ = self._emitir("memoria", {"acao": "registrar",
                                             "entrada": entrada},
                                 causado_por=causado_por)
        return evento

    # -- ContextPackage (D5 §3, IC-1..IC-5) -----------------------------------------

    def montar_contexto(self, work_unit_id: str, entradas: list,
                        exclusoes: list | None = None,
                        politica_inclusao: dict | None = None) -> ct.ContextPackage:
        """Monta ContextPackage com proveniencia completa e contencao.

        0.2.1-7: nasce ligado a um work_unit_id REAL (formato de id local) e
        os BYTES de cada entrada ficam no CAS (`bytes_ref` por entrada).
        Cada entrada: {'origem', 'papel', 'inclusao'} + opcional 'conteudo'
        (str/bytes) para origens nao-caminho (memoria por ID=SHA256, dados
        inline). Sem 'conteudo', 'origem' e resolvida como caminho DENTRO das
        raizes declaradas (IC-5) com reducao de TOCTOU. Tudo passa pelo
        scanner de segredos (IC-4).
        """
        _validar_id(work_unit_id, "contexto.work_unit_id")
        politica = dict(politica_inclusao or {})
        verbatim_ate = politica.get("verbatim_ate", VERBATIM_ATE_DEFAULT)
        politica.setdefault("verbatim_ate", verbatim_ate)
        politica.setdefault("memoria_por_hash", True)
        montadas = []
        linhas = 0
        for espec in entradas:
            origem = espec["origem"]
            papel = espec["papel"]
            inclusao = espec["inclusao"]
            if "conteudo" in espec:
                dados = espec["conteudo"]
                if isinstance(dados, str):
                    dados = dados.encode("utf-8")
            else:
                # Fontes read-only entram como evidencia/norma-citada (IC-2).
                if papel in ("contrato",) and inclusao != "referencia":
                    raise ct.FalhaContrato(
                        "IC-2/IC-3: conteudo externo nao entra como instrucao "
                        "executavel; use papel evidencia/norma-citada")
                dados = ler_arquivo_contido(origem, self.raizes_fontes,
                                            self.resolvedor)
            escanear_segredos(dados, f"entrada de contexto {origem!r}")  # IC-4
            if inclusao == "verbatim" and len(dados) > verbatim_ate:
                raise ct.FalhaContrato(
                    f"verbatim acima de {verbatim_ate} bytes: recusa, "
                    "nunca resume (D5 §3)")
            linhas += dados.count(b"\n") + (1 if dados else 0)
            montadas.append({
                "origem": origem, "sha256": sha256_bytes(dados),
                "bytes_ref": self.cas.gravar(dados),
                "papel": papel, "inclusao": inclusao,
            })
        pacote = ct.ContextPackage(
            contexto_id=novo_id(), work_unit_id=work_unit_id,
            entradas=montadas, politica_inclusao=politica,
            custo_contexto_linhas=linhas, exclusoes=list(exclusoes or []),
            hash_pacote="",
        )
        corpo = pacote.to_dict()
        corpo.pop("hash_pacote")
        pacote.hash_pacote = sha256_de(corpo)
        pacote.validate()
        # O objeto do CAS e o corpo SEM o campo hash_pacote: seu sha256 e
        # exatamente o hash_pacote (enderecamento por conteudo consistente).
        self.cas.gravar(canonico(corpo))
        return pacote

    def ler_pacote(self, contexto_ref: str,
                   work_unit_id: str | None = None) -> dict:
        """Le o ContextPackage do CAS com falha fechada (0.2.1-7).

        Corrupcao (hash divergente), ausencia do pacote ou dos bytes de
        qualquer entrada, ou vinculo com outro work_unit_id = FalhaContrato.
        NUNCA devolve pacote vazio/substituto.
        """
        try:
            dados = self.cas.ler(contexto_ref)
        except FileNotFoundError as exc:
            raise ct.FalhaContrato(
                f"ContextPackage ausente no CAS: {contexto_ref!r}") from exc
        pacote = json.loads(dados)
        if not pacote.get("work_unit_id"):
            raise ct.FalhaContrato("ContextPackage sem work_unit_id")
        if work_unit_id is not None \
                and pacote["work_unit_id"] != work_unit_id:
            raise ct.FalhaContrato(
                "ContextPackage ligado a outro work_unit_id")
        for entrada in pacote.get("entradas", []):
            ref = entrada.get("bytes_ref")
            if ref is None or not self.cas.existe(ref):
                raise ct.FalhaContrato(
                    "bytes de entrada de contexto ausentes no CAS: "
                    f"{entrada.get('origem')!r}")
        return pacote

    # -- Checkpoint / retomada (D5 §8.3, IP-1..IP-4) ---------------------------------

    def _estado_refs(self) -> dict:
        return {
            "envelope": sha256_de(self._envelope_estavel()),
            "work_units_abertas": {
                wid: wu.estado for wid, wu in sorted(self.work_units.items())
                if wu.estado not in ("concluida", "cancelada")
            },
            "memoria_cabeca": self.memoria_ref,
            "orcamento_consumido": {
                k: v for k, v in sorted(self.envelope.orcamento.items())
                if k.startswith("consumido_")
            },
            "ultimo_evento_hash": self.log.ultimo_hash(),
            "seq": self.log.seq_atual(),
        }

    def _ponto_de_retomada(self) -> dict:
        """Proxima acao pendente, ordenada por consequencia (custo zero)."""
        pendentes = []
        for wid, wu in sorted(self.work_units.items()):
            if wu.estado in ("aguardando-aprovacao", "aguardando-validacao",
                             "aprovada", "em-execucao", "proposta"):
                pendentes.append({"work_unit_id": wid, "estado": wu.estado})
        return {"pendentes": pendentes}

    def gravar_checkpoint(self) -> ct.Checkpoint:
        """Grava checkpoint validado por Juiz 1 deterministico (D5 §8.3)."""
        from .judge import Juiz1  # import tardio: juiz nao escreve no log
        estado_refs = self._estado_refs()
        corpo = {
            "checkpoint_id": novo_id(),
            "sessao_id": self.envelope.sessao_id,
            "linhagem_id": self.envelope.linhagem_id,
            "estado_refs": estado_refs,
            "ponto_de_retomada": self._ponto_de_retomada(),
        }
        validacao = Juiz1.validar_checkpoint(corpo)
        if not validacao["aprovado"]:
            raise CheckpointInvalido(
                f"checkpoint reprovado pelo Juiz 1: {validacao['falhas']}")
        selo = self._selo(canonico(corpo))
        checkpoint = ct.Checkpoint(validacao=validacao, selo=selo,
                                   **corpo).validado()
        diretorio = os.path.join(self.raiz, "checkpoints",
                                 self.envelope.sessao_id)
        os.makedirs(diretorio, exist_ok=True)
        destino = os.path.join(diretorio, f"{checkpoint.checkpoint_id}.json")
        tmp = destino + ".tmp"
        with open(tmp, "wb") as f:
            f.write(canonico(checkpoint.to_dict()))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destino)
        evento, _ = self._emitir("checkpoint",
                                 {"acao": "gravar",
                                  "checkpoint": checkpoint.to_dict()},
                                 causado_por=None)
        return checkpoint

    def suspender(self) -> ct.Evento:
        """ativa -> suspensa, so apos checkpoint validado gravado (IP-1)."""
        if not self.checkpoints:
            raise CheckpointInvalido("suspensao exige checkpoint gravado")
        evento, _ = self._emitir("sessao",
                                 {"acao": "suspender",
                                  "sessao_id": self.envelope.sessao_id},
                                 causado_por=None, _sem_garantia=True)
        return evento

    def encerrar(self, motivo: str, causado_por: str | None = None) -> ct.Evento:
        evento, _ = self._emitir("sessao",
                                 {"acao": "encerrar", "motivo": motivo,
                                  "sessao_id": self.envelope.sessao_id},
                                 causado_por=causado_por, _sem_garantia=True)
        return evento

    # -- replay / retomada ------------------------------------------------------

    @classmethod
    def anexar_existente(cls, raiz, sessao_id: str,
                         relogio: Relogio | None = None,
                         raizes_fontes=None,
                         resolvedor=os.path.realpath) -> "SessionKernel":
        """Reabre a sessao por replay deterministico do log (IP-4)."""
        k = cls(raiz, relogio, raizes_fontes=raizes_fontes, resolvedor=resolvedor)
        k._adquirir_lock(sessao_id)  # escritor unico (0.2.1-4)
        try:
            k._replay_de_zero(sessao_id)
        except BaseException:
            k.fechar()  # falha fechada sem vazar o lock
            raise
        return k

    def _replay_de_zero(self, sessao_id: str) -> None:
        _validar_id(sessao_id, "sessao_id")
        caminho_env = os.path.join(self.raiz, "sessoes",
                                   f"{sessao_id}.envelope.json")
        with open(caminho_env, "rb") as f:
            envelope = ct.SessionEnvelope.from_dict(json.loads(f.read()))
        selo_esperado = self._selo(canonico({
            k: v for k, v in envelope.to_dict().items() if k != "integridade"
        }))
        if not hmac_mod.compare_digest(selo_esperado,
                                       envelope.integridade.get("selo", "")):
            raise CheckpointInvalido("selo do envelope divergente")
        hash_genese = sha256_de(envelope.to_dict())
        caminho_log = self._log_path(sessao_id)
        registros = EventLog.verificar(caminho_log, hash_genese)  # IP-2
        self.log = EventLog(caminho_log, hash_genese)
        for registro in registros:
            evento = registro["evento"]
            # 0.2.1-11: mesma linhagem, causado_por na cadeia e payload
            # existente/integro no CAS — tudo falha fechada no replay.
            if evento.linhagem_id != envelope.linhagem_id:
                raise EventoAdulterado(
                    f"evento de outra linhagem na seq {evento.seq}")
            if evento.causado_por is not None \
                    and evento.causado_por not in self._eventos_vistos:
                raise EventoAdulterado(
                    f"causado_por fora da cadeia na seq {evento.seq}")
            try:
                payload = json.loads(self.cas.ler(evento.payload_ref))
            except FileNotFoundError as exc:
                raise CorrupcaoDetectada(
                    f"payload ausente no CAS: {evento.payload_ref}") from exc
            self._aplicar(evento, payload)

    @classmethod
    def retomar(cls, raiz, sessao_id: str, relogio: Relogio | None = None,
                raizes_fontes=None,
                resolvedor=os.path.realpath) -> "SessionKernel":
        """IP-1: retomar = checkpoint valido + log verificado; nunca inferencia.

        IP-2: checkpoint invalido, cadeia quebrada ou selo divergente =
        sessao nao retoma (CheckpointInvalido); o chamador escalona.
        Attempts sem conclusao viram orfaos -> indeterminado (D6 §4).
        0.2.1-8: o checkpoint e escolhido pelo ULTIMO evento valido/seq
        ancorado na cadeia — nunca pelo nome (UUID) do arquivo.
        """
        k = cls(raiz, relogio, raizes_fontes=raizes_fontes, resolvedor=resolvedor)
        k._adquirir_lock(sessao_id)  # escritor unico (0.2.1-4)
        try:
            return k._retomar_interno(sessao_id)
        except BaseException:
            k.fechar()  # falha fechada sem vazar o lock
            raise

    def _retomar_interno(self, sessao_id: str) -> "SessionKernel":
        k = self
        _validar_id(sessao_id, "sessao_id")
        diretorio = os.path.join(k.raiz, "checkpoints", sessao_id)
        if not os.path.isdir(diretorio):
            raise CheckpointInvalido("nenhum checkpoint para a sessao")
        # Candidatos: parse + schema + selo HMAC validos.
        candidatos = []
        for nome in os.listdir(diretorio):
            if not nome.endswith(".json"):
                continue
            try:
                with open(os.path.join(diretorio, nome), "rb") as f:
                    dados = json.loads(f.read())
                cp = ct.Checkpoint.from_dict(dados)
                cp.validate()
            except (OSError, UnicodeDecodeError, json.JSONDecodeError,
                    ct.FalhaContrato):
                continue  # ilegivel/fora de schema: nao e candidato
            corpo = {c: v for c, v in cp.to_dict().items()
                     if c not in ("validacao", "selo")}
            if not hmac_mod.compare_digest(k._selo(canonico(corpo)), cp.selo):
                continue  # IP-2: selo divergente, descartado
            candidatos.append(cp)
        if not candidatos:
            raise CheckpointInvalido(
                "nenhum checkpoint com selo valido para a sessao")
        k._replay_de_zero(sessao_id)  # levanta em cadeia quebrada/adulterada
        registros = EventLog.verificar(k._log_path(sessao_id),
                                       k.log.hash_genese)
        ancorados = [
            cp for cp in candidatos
            if any(r["hash"] == cp.estado_refs["ultimo_evento_hash"]
                   and r["evento"].seq == cp.estado_refs["seq"]
                   for r in registros)
        ]
        if not ancorados:
            raise CheckpointInvalido(
                "IP-2: ultimo_evento_hash/seq do checkpoint fora da cadeia")
        # Ultimo evento valido/seq — ordem por seq, nunca por UUID (0.2.1-8).
        checkpoint = max(ancorados, key=lambda c: c.estado_refs["seq"])
        # suspensa -> retomada
        ev_retomada, _ = k._emitir(
            "sessao", {"acao": "retomar", "sessao_id": sessao_id,
                       "checkpoint_id": checkpoint.checkpoint_id},
            causado_por=None, _sem_garantia=True)
        # Attempts orfaos: sem evento de conclusao apos o crash (D6 §4).
        for attempt_id, reg in list(k.attempts.items()):
            if reg["estado"] in ("criado", "despachado"):
                marcar_orfao(reg["estado"])
                attempt = reg["attempt"]
                attempt.resultado = "indeterminado"
                attempt.efeito_externo = "incerto"
                k._emitir("attempt",
                          {"acao": "orfao", "attempt": attempt.to_dict(),
                           "motivo": "sem conclusao persistida apos crash; "
                                     "nunca assumido como sucesso (IR-2)"},
                          causado_por=ev_retomada.evento_id)
        return k

    def estado_snapshot(self) -> dict:
        """Estado derivado completo, comparavel entre kernels (IP-4)."""
        return {
            "envelope": self.envelope.to_dict() if self.envelope else None,
            "work_units": {k: w.to_dict() for k, w in
                           sorted(self.work_units.items())},
            "decisoes": {k: d.to_dict() for k, d in
                         sorted(self.decisoes.items())},
            "vigente": dict(sorted(self.vigente.items())),
            "attempts": {k: {"attempt": r["attempt"].to_dict(),
                             "estado": r["estado"]}
                         for k, r in sorted(self.attempts.items())},
            "memoria": list(self.memoria),
            "memoria_ref": self.memoria_ref,
            "vereditos": [v.to_dict() for v in self.vereditos],
            "escalacoes": [e.to_dict() for e in self.escalacoes],
            "retries": [r.to_dict() for r in self.retries],
            "fallbacks": [f.to_dict() for f in self.fallbacks],
        }

    def verificar_integridade(self) -> list:
        """Verifica a cadeia inteira do log da sessao corrente."""
        return EventLog.verificar(self._log_path(self.envelope.sessao_id),
                                  self.log.hash_genese)

    # -- fold do replay (mesma funcao usada na escrita) -------------------------

    def _aplicar(self, evento: ct.Evento, payload: dict) -> None:
        tipo, acao = evento.tipo, payload.get("acao")
        if tipo == "sessao":
            if acao == "abrir":
                self.envelope = ct.SessionEnvelope.from_dict(payload["envelope"])
            elif acao == "suspender":
                transitar_sessao(self.envelope.estado, "suspensa")
                self.envelope.estado = "suspensa"
            elif acao == "retomar":
                transitar_sessao(self.envelope.estado, "retomada")
                self.envelope.estado = "retomada"
            elif acao == "reativar":
                transitar_sessao(self.envelope.estado, "ativa")
                self.envelope.estado = "ativa"
            elif acao == "encerrar":
                transitar_sessao(self.envelope.estado, "encerrada")
                self.envelope.encerrado_em = evento.ts
                self.envelope.estado = "encerrada"
        elif tipo == "work-unit":
            if acao == "registrar":
                wu = ct.WorkUnit.from_dict(payload["work_unit"])
                self.work_units[wu.work_unit_id] = wu
            elif acao == "transicao":
                wu = self.work_units[payload["work_unit_id"]]
                transitar_workunit(wu.estado, payload["para"])
                wu.estado = payload["para"]
            elif acao == "recusa":
                self.recusas.append(payload)
        elif tipo == "routing":
            if acao == "registrar":
                dec = ct.RoutingDecision.from_dict(payload["decisao"])
                self.decisoes[dec.decisao_id] = dec
                self.vigente[dec.work_unit_id] = dec.decisao_id
                self._evento_routing[dec.decisao_id] = evento.evento_id
                # Hash da decisao completa no registro (0.2.1-1).
                self._hashes_decisao[dec.decisao_id] = sha256_de(dec.to_dict())
            elif acao in ("veto", "recusa"):
                self.recusas.append(payload)
        elif tipo == "attempt":
            if acao == "criar":
                attempt = ct.ExecutionAttempt.from_dict(payload["attempt"])
                self.attempts[attempt.attempt_id] = {
                    "attempt": attempt, "estado": "criado"}
            elif acao == "despachar":
                attempt = ct.ExecutionAttempt.from_dict(payload["attempt"])
                reg = self.attempts[attempt.attempt_id]
                transitar_attempt(reg["estado"], "despachado")
                reg["attempt"] = attempt
                reg["estado"] = "despachado"
            elif acao == "concluir":
                attempt = ct.ExecutionAttempt.from_dict(payload["attempt"])
                reg = self.attempts[attempt.attempt_id]
                transitar_attempt(reg["estado"], "concluido")
                reg["attempt"] = attempt
                reg["estado"] = "concluido"
            elif acao == "orfao":
                attempt = ct.ExecutionAttempt.from_dict(payload["attempt"])
                reg = self.attempts[attempt.attempt_id]
                marcar_orfao(reg["estado"])
                reg["attempt"] = attempt
                reg["estado"] = "orfao"
            elif acao == "recusa":
                self.recusas.append(payload)
        elif tipo == "retry":
            self.retries.append(ct.RetryEvent.from_dict(payload["retry"]))
        elif tipo == "fallback":
            self.fallbacks.append(ct.FallbackEvent.from_dict(payload["fallback"]))
        elif tipo == "escalation":
            self.escalacoes.append(
                ct.EscalationEvent.from_dict(payload["escalacao"]))
        elif tipo == "veredito":
            if acao == "registrar":
                self.vereditos.append(
                    ct.ValidationVerdict.from_dict(payload["veredito"]))
            elif acao == "recusa":
                self.recusas.append(payload)
        elif tipo == "memoria":
            self.memoria.append(payload["entrada"])
            self.memoria_ref = sha256_de(self.memoria)
            if self.envelope is not None:
                self.envelope.memoria_ref = self.memoria_ref
        elif tipo == "orcamento":
            self.envelope.orcamento["consumido_custo"] = round(
                self.envelope.orcamento.get("consumido_custo", 0.0)
                + payload.get("custo", 0.0), 6)
            self.envelope.orcamento["consumido_tokens"] = (
                self.envelope.orcamento.get("consumido_tokens", 0)
                + payload.get("tokens", 0))
        elif tipo == "checkpoint":
            self.checkpoints.append(
                ct.Checkpoint.from_dict(payload["checkpoint"]))
        # Cadeia causal da sessao (0.2.1-11): causado_por validado contra
        # este conjunto a cada emissao e no replay.
        self._eventos_vistos.add(evento.evento_id)


class ControlPlane:
    """Ciclo de vida e voz humana (D6 §2.5). Apresenta e registra; nao roteia."""

    def __init__(self, kernel: SessionKernel):
        self.kernel = kernel

    def abrir_sessao(self, **kwargs) -> ct.SessionEnvelope:
        return self.kernel.abrir_sessao(**kwargs)

    def escalar(self, work_unit_id: str | None, motivo: str, destino: str,
                detalhe: str | None = None,
                causado_por: str | None = None) -> ct.Evento:
        """Escalonamento sempre termina em decisao humana registrada."""
        escalacao = ct.EscalationEvent(
            escalacao_id=novo_id(), work_unit_id=work_unit_id,
            motivo=motivo, destino=destino, detalhe=detalhe).validado()
        return self.kernel.registrar_escalacao(escalacao, causado_por)

    def aprovar_work_unit(self, work_unit_id: str, ato_humano: dict,
                          causado_por: str | None = None) -> ct.Evento:
        """Ato humano explicito, datado, hasheado; silencio nunca aprova."""
        k = self.kernel
        wu = k.work_units[work_unit_id]
        if wu.estado != "aguardando-aprovacao":
            raise TransicaoIlegal(
                f"aprovacao humana com workunit em {wu.estado!r}")
        ato = dict(ato_humano)
        ato["ts"] = k.relogio.agora()
        ato["hash"] = sha256_de(ato)
        return k.transicionar_work_unit(work_unit_id, "aprovada", causado_por,
                                        detalhe={"ato_humano": ato})

    def encerrar(self, motivo: str, causado_por: str | None = None) -> ct.Evento:
        return self.kernel.encerrar(motivo, causado_por)
