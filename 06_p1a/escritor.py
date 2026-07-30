"""Escritor unico das operacoes P1 (SSC+ P1-A.1): lease + fencing sobre o
writelock da camada P0.

Integra o `LockSessao` da P0 (05_p0/ssc_p0/writelock.py) no ponto de
entrada das operacoes P1: qualquer operacao que escreva evidencia ou
invoque provedor precisa adquirir o escritor ANTES. Uma segunda sessao
falha na aquisicao (LockIndisponivel) — antes de escrever um byte ou
invocar qualquer provedor.

- Lease: arquivo `<sessao>.lease` (JSON: sessao, pid, token, renovado_em,
  expira_em) gravado na aquisicao e estendido por `renovar()`. Lease
  vencido = escritor considerado morto.
- Fencing: token monotonico da P0, verificado por `verificar()` antes de
  cada escrita; escritor com token defasado e recusado
  (EscritorObsoleto).
- Recuperacao de lock expirado: a morte do processo libera o lock do SO;
  o sucessor adquire, incrementa o fence e o escritor antigo nunca mais
  escreve — mesmo que "acorde" depois.

Estado de lock e RUNTIME: o diretorio de locks e ignorado pelo Git.
Nenhum conteudo sensivel nos arquivos (token inteiro, pid, timestamps).
"""

import json
import os
import time

from ssc_p0.writelock import EscritorObsoleto, LockIndisponivel, LockSessao

__all__ = ["LEASE_PADRAO_S", "EscritorP1", "EscritorObsoleto",
           "LockIndisponivel"]

# Maior que o timeout de 300 s da prova minima: o lease cobre a execucao
# mais longa prevista sem exigir renovacao durante o subprocesso.
LEASE_PADRAO_S = 900


class EscritorP1:
    """Lease + fencing token do escritor unico das operacoes P1."""

    def __init__(self, diretorio_locks, sessao: str = "p1-ops",
                 lease_s: float = LEASE_PADRAO_S):
        self.dir = str(diretorio_locks)
        self.sessao = str(sessao)
        self.lease_s = float(lease_s)
        self._lock = LockSessao(
            os.path.join(self.dir, f"{self.sessao}.lock"),
            os.path.join(self.dir, f"{self.sessao}.fence"))
        self.caminho_lease = os.path.join(self.dir, f"{self.sessao}.lease")

    @property
    def token(self):
        """Fencing token vigente (None antes da aquisicao)."""
        return self._lock.token

    def adquirir(self) -> int:
        """Lock exclusivo + fence incrementado + primeira concessao do lease.

        Levanta LockIndisponivel se outra sessao detem o lock — o chamador
        deve abortar ANTES de escrever ou invocar provedor. Se o lock do
        SO esta livre (lease anterior expirado, escritor morto), esta
        aquisicao E a recuperacao: o fence incrementado invalida para
        sempre o token do escritor anterior.
        """
        os.makedirs(self.dir, exist_ok=True)
        token = self._lock.adquirir()
        self._gravar_lease()
        return token

    def renovar(self) -> None:
        """Estende o lease — somente o escritor vivo (fencing valido)."""
        self._lock.verificar()
        self._gravar_lease()

    def verificar(self) -> None:
        """Fencing + lease validos; chamar antes de CADA escrita."""
        self._lock.verificar()
        if self.lease_expirado(self.caminho_lease):
            raise EscritorObsoleto(
                "lease expirado sem renovacao: readquirir o escritor")

    def liberar(self) -> None:
        """Fechamento limpo do escritor (handoff explicito)."""
        self._lock.liberar()

    def _gravar_lease(self) -> None:
        agora = time.time()
        dados = {"sessao": self.sessao, "pid": os.getpid(),
                 "token": self._lock.token, "renovado_em": agora,
                 "expira_em": agora + self.lease_s}
        tmp = self.caminho_lease + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.caminho_lease)

    @staticmethod
    def lease_expirado(caminho_lease, agora: float | None = None) -> bool:
        """True se o lease esta vencido; arquivo ausente/ilegivel = morto."""
        try:
            with open(caminho_lease, encoding="utf-8") as f:
                expira = float(json.load(f)["expira_em"])
        except (OSError, ValueError, KeyError, TypeError):
            return True
        return (time.time() if agora is None else agora) >= expira
