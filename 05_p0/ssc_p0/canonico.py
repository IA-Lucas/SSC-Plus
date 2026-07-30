"""Serializacao canonica, hashes, ids e relogio injetavel (D5 §0.1).

JSON canonico: UTF-8, chaves ordenadas, separadores compactos, sem NaN/Infinity.
sha256 sempre sobre a serializacao canonica. Ids locais opacos = UUID-4 hex.
O relogio NAO e autoridade de ordem (a seq do EventLog e); ts e informativo.
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone


class ErroCanonico(ValueError):
    """Objeto nao serializavel na forma canonica."""


def canonico(obj) -> bytes:
    """Serializa obj na forma canonica e devolve bytes UTF-8."""
    try:
        texto = json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ErroCanonico(f"objeto nao canonizavel: {exc}") from exc
    return texto.encode("utf-8")


def sha256_bytes(dados: bytes) -> str:
    """sha256 hex de bytes crus."""
    return hashlib.sha256(dados).hexdigest()


def sha256_de(obj) -> str:
    """sha256 hex da serializacao canonica de obj."""
    return sha256_bytes(canonico(obj))


def novo_id() -> str:
    """Identificador local opaco (UUID-4 hex, nao canonico)."""
    return uuid.uuid4().hex


class Relogio:
    """Interface de relogio injetavel. ts e informativo, nunca ordena."""

    def agora(self) -> str:
        raise NotImplementedError

    def espiar(self) -> str:
        """Leitura sem efeito colateral (para validacoes)."""
        return self.agora()


class RelogioReal(Relogio):
    """Relogio de wall-clock UTC (so para uso interativo)."""

    def agora(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RelogioDeterministico(Relogio):
    """Relogio monotonico por passo fixo; default das corridas e testes."""

    def __init__(self, inicio: str = "2026-07-30T00:00:00Z", passo_segundos: int = 1):
        self._atual = datetime.fromisoformat(inicio.replace("Z", "+00:00"))
        self._passo = timedelta(seconds=passo_segundos)

    def agora(self) -> str:
        ts = self._atual.isoformat().replace("+00:00", "Z")
        self._atual += self._passo
        return ts

    def espiar(self) -> str:
        return self._atual.isoformat().replace("+00:00", "Z")
