"""Armazenamento enderecado por conteudo (D5 §8.1) + contencao de caminho (IC-5).

Layout: objetos/<2 hex>/<2 hex>/<sha256 completo>.
Escrita atomica: tmp no mesmo diretorio + fsync + rename (os.replace).
Leitura sempre re-verificada: divergencia = corrupcao, falha fechada.
Imutavel: nenhuma escrita sobre objeto existente.
Contencao: recusa symlink/junction e qualquer caminho fora da raiz declarada,
resolvendo por caminho real.
"""

import os

from .canonico import sha256_bytes


class CorrupcaoDetectada(Exception):
    """Bytes lidos divergem do hash enderecado."""


class FugaDeCaminho(Exception):
    """Caminho fora das raizes declaradas ou atravessando symlink/junction."""


def _fsync_arquivo(f) -> None:
    f.flush()
    os.fsync(f.fileno())


def _fsync_diretorio(caminho: str) -> None:
    """fsync do diretorio; em Windows nao ha fd de diretorio — ignorado."""
    if os.name == "nt":
        return
    try:
        fd = os.open(caminho, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def resolver_contido(caminho: str, raizes, resolvedor=os.path.realpath) -> str:
    """Resolve `caminho` por caminho real e exige contencao em `raizes`.

    Recusa: fuga por `..`/prefixo, e travessia de symlink/junction (detectada
    quando o caminho real diverge do caminho normalizado textual).
    """
    bruto = os.path.normpath(os.path.abspath(str(caminho)))
    real = os.path.normpath(resolvedor(str(caminho)))
    if os.path.normcase(real) != os.path.normcase(bruto):
        raise FugaDeCaminho(
            f"caminho atravessa symlink/junction: {caminho!r} -> {real!r}"
        )
    for raiz in raizes:
        raiz_real = os.path.normpath(resolvedor(str(raiz)))
        try:
            comum = os.path.commonpath([real, raiz_real])
        except ValueError:
            continue  # unidades distintas (Windows)
        if os.path.normcase(comum) == os.path.normcase(raiz_real):
            return real
    raise FugaDeCaminho(f"caminho fora das raizes declaradas: {caminho!r}")


def ler_arquivo_contido(caminho: str, raizes,
                        resolvedor=os.path.realpath) -> bytes:
    """Le arquivo DENTRO das raizes com reducao de TOCTOU.

    Apos a validacao de contencao e a abertura, compara (st_dev, st_ino) do
    descritor com os do caminho e re-resolve o caminho real: se o alvo mudou
    entre a validacao e a leitura, falha fechada.
    """
    resolvido = resolver_contido(caminho, raizes, resolvedor)
    fd = os.open(resolvido, os.O_RDONLY)
    try:
        st_fd = os.fstat(fd)
        st_caminho = os.stat(resolvido)
        if (st_fd.st_dev, st_fd.st_ino) != (st_caminho.st_dev,
                                            st_caminho.st_ino):
            raise FugaDeCaminho(
                f"TOCTOU: alvo trocado apos a validacao: {caminho!r}")
        if os.path.normcase(os.path.normpath(resolvedor(resolvido))) \
                != os.path.normcase(os.path.normpath(resolvido)):
            raise FugaDeCaminho(
                f"TOCTOU: caminho real mudou apos a abertura: {caminho!r}")
        arq = os.fdopen(fd, "rb")
        fd = None
        with arq:
            return arq.read()
    finally:
        if fd is not None:
            os.close(fd)


class CAS:
    """Armazenamento de objetos imutaveis enderecados por sha256.

    somente_leitura=True (Evidence Plane): nao cria diretorios e recusa
    qualquer gravacao (PermissionError).
    """

    def __init__(self, raiz_cas: str, somente_leitura: bool = False):
        self.raiz = os.path.realpath(str(raiz_cas))
        self.somente_leitura = bool(somente_leitura)
        if not self.somente_leitura:
            os.makedirs(os.path.join(self.raiz, "objetos"), exist_ok=True)

    def _caminho(self, hash_hex: str) -> str:
        if (not isinstance(hash_hex, str) or len(hash_hex) != 64
                or any(c not in "0123456789abcdef" for c in hash_hex)):
            raise FugaDeCaminho(f"hash invalido para o CAS: {hash_hex!r}")
        caminho = os.path.join(
            self.raiz, "objetos", hash_hex[:2], hash_hex[2:4], hash_hex
        )
        real = os.path.realpath(caminho)
        try:
            comum = os.path.commonpath([real, self.raiz])
        except ValueError:
            raise FugaDeCaminho(f"objeto fora da raiz do CAS: {hash_hex!r}")
        if os.path.normcase(comum) != os.path.normcase(self.raiz):
            raise FugaDeCaminho(f"objeto fora da raiz do CAS: {hash_hex!r}")
        return caminho

    def gravar(self, dados: bytes) -> str:
        """Grava bytes e devolve o sha256. Idempotente para mesmo conteudo."""
        if self.somente_leitura:
            raise PermissionError("CAS somente leitura (Evidence Plane)")
        if not isinstance(dados, (bytes, bytearray)):
            raise TypeError("CAS.gravar aceita apenas bytes")
        dados = bytes(dados)
        hash_hex = sha256_bytes(dados)
        destino = self._caminho(hash_hex)
        if os.path.islink(destino):
            raise FugaDeCaminho(f"objeto do CAS e symlink: {destino!r}")
        if os.path.exists(destino):
            # Mesmo hash ja gravado = idempotente; verifica antes de aceitar.
            self.ler(hash_hex)
            return hash_hex
        diretorio = os.path.dirname(destino)
        os.makedirs(diretorio, exist_ok=True)
        tmp = os.path.join(diretorio, f".tmp-{os.getpid()}-{id(dados):x}")
        with open(tmp, "wb") as f:
            f.write(dados)
            _fsync_arquivo(f)
        os.replace(tmp, destino)
        _fsync_diretorio(diretorio)
        return hash_hex

    def ler(self, hash_hex: str) -> bytes:
        """Le e re-verifica o sha256; divergencia = corrupcao (falha fechada)."""
        caminho = self._caminho(hash_hex)
        if os.path.islink(caminho):
            raise FugaDeCaminho(f"objeto do CAS e symlink: {caminho!r}")
        with open(caminho, "rb") as f:
            dados = f.read()
        if sha256_bytes(dados) != hash_hex:
            raise CorrupcaoDetectada(f"objeto corrompido no CAS: {hash_hex!r}")
        return dados

    def existe(self, hash_hex: str) -> bool:
        return os.path.exists(self._caminho(hash_hex))
