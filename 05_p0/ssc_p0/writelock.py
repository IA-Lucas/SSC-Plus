"""Escritor unico ENTRE processos: lock/lease de arquivo + fencing token.

Um lock por sessao (`locks/<sessao_id>.lock`) sobre primitiva do SO
(msvcrt no Windows, fcntl no POSIX). O fencing token
(`locks/<sessao_id>.fence`) e um inteiro monotonico incrementado a cada
aquisicao: um escritor antigo (crashado ou substituido) tem token defasado
e e recusado na proxima escrita (EscritorObsoleto).

- Morte de processo libera o lock do SO; o sucessor incrementa o fence.
- Guarda intra-processo impede dois kernels vivos na mesma sessao no
  mesmo processo (o lock do SO nao distingue handles do mesmo processo).
- Stdlib apenas; nenhum conteudo sensivel nos arquivos (token e inteiro).
"""

import os

if os.name == "nt":
    import msvcrt
else:
    import fcntl


class LockIndisponivel(Exception):
    """Outro processo (ou kernel vivo) detem o lock da sessao."""


class EscritorObsoleto(Exception):
    """Fencing token defasado: este escritor foi substituido ou liberou."""


_DETIDOS = {}  # caminho_lock (normcase/realpath) -> token (intra-processo)


def _travar(arq) -> None:
    if os.name == "nt":
        arq.seek(0)
        msvcrt.locking(arq.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(arq.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _destravar(arq) -> None:
    try:
        if os.name == "nt":
            arq.seek(0)
            msvcrt.locking(arq.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(arq.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


class LockSessao:
    """Lock exclusivo + fencing token de uma sessao logica."""

    def __init__(self, caminho_lock: str, caminho_fence: str):
        self.caminho_lock = str(caminho_lock)
        self.caminho_fence = str(caminho_fence)
        self.token: int | None = None
        self._arq = None
        self._ativo = False

    def _ler_fence(self) -> int:
        # Arquivo ausente/ilegivel = 0 (token inicial). A unicidade do
        # escritor NAO depende desta leitura: quem a garante e o lock do SO;
        # o fencing e defesa secundaria contra escritor obsoleto
        # (THREAT-MODEL §2: corrupcao de disco esta fora de escopo).
        try:
            with open(self.caminho_fence, "rb") as f:
                return int(f.read().decode("ascii").strip())
        except (OSError, ValueError):
            return 0

    def adquirir(self) -> int:
        """Adquire o lock (nao bloqueante) e incrementa o fencing token."""
        chave = os.path.normcase(os.path.realpath(self.caminho_lock))
        if chave in _DETIDOS:
            raise LockIndisponivel(
                f"kernel vivo ja detem o lock da sessao: {chave}")
        novo = not os.path.exists(self.caminho_lock)
        arq = open(self.caminho_lock, "a+b")
        try:
            if novo:
                arq.write(b"\0")
                arq.flush()
            _travar(arq)
        except OSError as exc:
            arq.close()
            raise LockIndisponivel(
                f"lock da sessao detido por outro processo: {exc}") from exc
        self._arq = arq
        self.token = self._ler_fence() + 1
        tmp = self.caminho_fence + ".tmp"
        with open(tmp, "wb") as f:
            f.write(str(self.token).encode("ascii"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.caminho_fence)
        self._ativo = True
        _DETIDOS[chave] = self.token
        return self.token

    def verificar(self) -> None:
        """Fencing: chamado antes de CADA escrita no EventLog."""
        if not self._ativo or self.token is None:
            raise EscritorObsoleto("escritor sem lock ativo na sessao")
        if self._ler_fence() != self.token:
            raise EscritorObsoleto(
                "fencing token defasado: escritor substituido por outro "
                "processo")

    def _soltar(self) -> None:
        chave = os.path.normcase(os.path.realpath(self.caminho_lock))
        _DETIDOS.pop(chave, None)
        if self._arq is not None:
            _destravar(self._arq)
            self._arq.close()
            self._arq = None
        self._ativo = False

    def liberar(self) -> None:
        """Fechamento limpo do escritor (handoff explicito)."""
        self._soltar()

    def __del__(self):
        # Rede final para objetos abandonados por excecao/retomada. Nao
        # substitui `liberar`, mas impede que o descritor sobreviva ate o
        # coletor e produza ResourceWarning.
        try:
            self._soltar()
        except Exception:
            pass

    def simular_crash(self) -> None:
        """Morte de processo (so teste): solta o lock do SO sem aviso.

        O token deste escritor fica defasado assim que outro escritor
        adquirir o lock; qualquer escrita posterior deste objeto e
        recusada pelo fencing (EscritorObsoleto).
        """
        self._soltar()
