"""EventLog append-only (D5 §8.2).

Um evento por linha (JSONL canonico). Cadeia prev_event_hash com genesis =
hash do envelope. seq inteiro monotonico por sessao (autoridade de ordem).
Dedup por idempotency_key: reentrega com mesma chave = ignorada.
Verificacao de integridade detecta: duplicado, fora de ordem, truncado,
adulterado — sempre falha fechada (IP-2/IP-4).

O escritor unico e o Session Kernel; este modulo so implementa o arquivo.
"""

import json
import os

from .canonico import canonico, sha256_bytes, sha256_de
from .contratos import Evento, FalhaContrato


class EventoDuplicado(Exception):
    """Mesma idempotency_key (ou evento_id) ja presente na cadeia verificada."""


class EventoForaDeOrdem(Exception):
    """seq regressiva ou com buraco."""


class EventoTruncado(Exception):
    """Linha incompleta / JSON invalido (cauda corrompida)."""


class EventoAdulterado(Exception):
    """Quebra da cadeia prev_event_hash."""


def hash_evento(evento: Evento) -> str:
    """Hash canonico do evento completo (base da cadeia)."""
    return sha256_de(evento.to_dict())


class EventLog:
    """Arquivo JSONL de uma sessao. Construir re-verifica o arquivo existente."""

    def __init__(self, caminho: str, hash_genese: str):
        self.caminho = str(caminho)
        self.hash_genese = hash_genese
        self._seq = 0
        self._ultimo_hash = hash_genese
        self._chaves = {}  # idempotency_key -> evento_id
        if os.path.exists(self.caminho):
            for registro in self.verificar(self.caminho, hash_genese):
                evento = registro["evento"]
                self._seq = evento.seq
                self._ultimo_hash = registro["hash"]
                self._chaves[evento.idempotency_key] = evento.evento_id

    def proxima_seq(self) -> int:
        return self._seq + 1

    def seq_atual(self) -> int:
        return self._seq

    def ultimo_hash(self) -> str:
        return self._ultimo_hash

    def chave_vista(self, idempotency_key: str) -> bool:
        return idempotency_key in self._chaves

    def anexar(self, evento: Evento) -> bool:
        """Anexa o evento. Devolve False se a idempotency_key ja existia
        (reentrega ignorada, D5 §8.2). O chamador (Kernel) serializa."""
        evento.validate()
        if evento.idempotency_key in self._chaves:
            return False
        if evento.seq != self._seq + 1:
            raise EventoForaDeOrdem(
                f"seq {evento.seq} fora de ordem (esperada {self._seq + 1})"
            )
        if evento.prev_event_hash != self._ultimo_hash:
            raise EventoAdulterado("prev_event_hash diverge da ponta da cadeia")
        linha = canonico(evento.to_dict()) + b"\n"
        with open(self.caminho, "ab") as f:
            f.write(linha)
            f.flush()
            os.fsync(f.fileno())
        self._seq = evento.seq
        self._ultimo_hash = hash_evento(evento)
        self._chaves[evento.idempotency_key] = evento.evento_id
        return True

    @staticmethod
    def verificar(caminho: str, hash_genese: str) -> list:
        """Verifica a cadeia inteira e devolve [{'evento', 'hash'}, ...].

        Falha fechada em qualquer anomalia: truncado, fora de ordem,
        duplicado, adulterado.
        """
        registros = []
        anterior = hash_genese
        vistos_id = set()
        vistos_chave = set()
        with open(caminho, "rb") as f:
            bruto = f.read()
        if not bruto:
            return registros
        linhas = bruto.split(b"\n")
        if linhas and linhas[-1] == b"":
            linhas = linhas[:-1]
        else:
            raise EventoTruncado("ultima linha sem terminador (cauda truncada)")
        for i, linha in enumerate(linhas, start=1):
            try:
                dados = json.loads(linha.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EventoTruncado(f"linha {i} invalida: {exc}") from exc
            try:
                evento = Evento.from_dict(dados)
                evento.validate()
            except FalhaContrato as exc:
                raise EventoTruncado(f"linha {i} fora de schema: {exc}") from exc
            # A linha crua deve ser a serializacao canonica do evento: qualquer
            # edicao local muda o hash da linha e quebra a cadeia adiante.
            hash_linha = sha256_bytes(linha)
            if hash_linha != hash_evento(evento):
                raise EventoAdulterado(f"linha {i} nao canonica")
            if evento.seq != i:
                raise EventoForaDeOrdem(
                    f"seq {evento.seq} na posicao {i} (regressiva ou buraco)"
                )
            if evento.prev_event_hash != anterior:
                raise EventoAdulterado(
                    f"cadeia quebrada na seq {evento.seq} (prev_event_hash)"
                )
            if evento.evento_id in vistos_id or evento.idempotency_key in vistos_chave:
                raise EventoDuplicado(f"evento duplicado na seq {evento.seq}")
            vistos_id.add(evento.evento_id)
            vistos_chave.add(evento.idempotency_key)
            registros.append({"evento": evento, "hash": hash_linha})
            anterior = hash_linha
        return registros
