"""Politica unica de deteccao de segredos antes de persistencia ou envio."""

import re


class SegredoDetectado(Exception):
    """Padrao de segredo detectado; o valor nunca entra na mensagem."""


PADROES_SEGREDO = tuple(re.compile(p) for p in (
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"(?i)(api[_-]?key|secret|senha|password|passwd)[\"'\s]*[:=]"
    r"[\"'\s]*[A-Za-z0-9_./+\-]{8,}",
))


def escanear_segredos(dados: bytes, rotulo: str) -> None:
    if not isinstance(dados, (bytes, bytearray)):
        raise TypeError("scanner de segredos aceita apenas bytes")
    texto = bytes(dados).decode("utf-8", errors="replace")
    for padrao in PADROES_SEGREDO:
        if padrao.search(texto):
            raise SegredoDetectado(f"IC-4: segredo detectado em {rotulo}")
