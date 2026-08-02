"""Escritor unico POR REPOSITORIO — SSC+ P1-A.3.7, ACHADO 4 / N1.

O DEFEITO, aberto desde a `99_achados-governanca-20260731.md` §7 e
elevado a MAJOR por revisor independente na P1-A.3.6:

    `LockSessao` tranca `locks/<sessao_id>.lock`. Duas missoes de NOMES
    DIFERENTES trancam ARQUIVOS DIFERENTES, e nenhuma exclui a outra. O
    escritor unico entre missoes NAO EXISTE — o que existe e escritor
    unico por nome de sessao, que e outra propriedade.

E a frase do revisor que fecha o ponto: *"a ordem manual do Fundador nao
substitui exclusao mutua"*. Enquanto isto nao for corrigido, o escritor
unico do acervo e garantido por ordem, nunca por mecanismo.

ESTE MODULO NAO ESTA EM USO. Ele e implementado, testado e commitado em
ISOLADO, por ordem expressa: trocar o mecanismo vivo no meio de uma
missao de correcao seria mudar o chao enquanto se anda sobre ele, e a
troca e decisao atendida do Fundador. Nenhum runner do acervo o importa;
o teste e o unico consumidor, e ha guarda medindo isso.

O QUE MUDA, em duas linhas:

1. UM LOCK PARA O REPOSITORIO. O arquivo trancado e sempre
   `locks/repositorio.lock`, qualquer que seja o nome da missao. O nome
   deixa de escolher o arquivo e passa a ser apenas o TITULAR
   registrado no lease — que e o que ele sempre deveria ter sido.
2. `liberar()` EXPIRA O LEASE QUE CONCEDEU. Hoje `EscritorP1.liberar`
   solta o lock do SO e deixa o `.lease` com validade futura: quem le o
   lease depois ve um escritor vivo que ja saiu. Um lease que sobrevive
   ao seu detentor e pior que nenhum — ele afirma o que nao ha.

LIMITE DECLARADO. A exclusao vale para quem passa por AQUI. Um processo
que escreva no repositorio sem adquirir este escritor nao e barrado por
nada — o mecanismo e cooperativo, como todo lock de arquivo, e nenhum
teste deste modulo afirma o contrario.
"""

import json
import os
import time

from escritor import LEASE_PADRAO_S
from ssc_p0.writelock import EscritorObsoleto, LockIndisponivel, LockSessao

__all__ = ["NOME_DO_LOCK", "EscritorObsoleto", "EscritorRepositorio",
           "LockIndisponivel", "titular_atual"]

# Nome UNICO do lock do repositorio. Nao e configuravel de proposito:
# tornar isto um parametro reabriria o ACHADO 4 pela porta dos fundos —
# bastaria cada missao passar um nome proprio.
NOME_DO_LOCK = "repositorio"


def _caminho(diretorio_locks, sufixo: str) -> str:
    return os.path.join(str(diretorio_locks), f"{NOME_DO_LOCK}{sufixo}")


def titular_atual(diretorio_locks, agora: float | None = None) -> dict | None:
    """Titular VIVO do repositorio, ou None — le sem adquirir nada.

    Devolve `{"sessao", "pid", "token", "expira_em"}`. Lease ausente,
    ilegivel ou VENCIDO devolve None: um lease vencido nao tem titular,
    e dizer que tem seria o defeito que o `liberar()` daqui corrige.
    """
    try:
        with open(_caminho(diretorio_locks, ".lease"), encoding="utf-8") as f:
            lease = json.load(f)
        expira = float(lease["expira_em"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if (time.time() if agora is None else agora) >= expira:
        return None
    return lease


class EscritorRepositorio:
    """Escritor unico do REPOSITORIO — um lock, muitos nomes possiveis."""

    def __init__(self, diretorio_locks, sessao: str,
                 lease_s: float = LEASE_PADRAO_S):
        if not str(sessao).strip():
            raise ValueError("sessao sem nome: o titular precisa ser nomeado")
        self.dir = str(diretorio_locks)
        self.sessao = str(sessao)
        self.lease_s = float(lease_s)
        self.caminho_lease = _caminho(self.dir, ".lease")
        self._lock = LockSessao(_caminho(self.dir, ".lock"),
                                _caminho(self.dir, ".fence"))

    @property
    def token(self):
        return self._lock.token

    def adquirir(self) -> int:
        """Lock do REPOSITORIO + fence + lease nomeado.

        Levanta `LockIndisponivel` se QUALQUER outra sessao — de
        qualquer nome — detem o escritor. O chamador deve abortar ANTES
        de escrever ou invocar provedor.
        """
        os.makedirs(self.dir, exist_ok=True)
        token = self._lock.adquirir()
        self._gravar_lease(time.time() + self.lease_s)
        return token

    def renovar(self) -> None:
        """Estende o lease — somente o titular vivo."""
        self.verificar()
        self._gravar_lease(time.time() + self.lease_s)

    def verificar(self) -> None:
        """Fencing + lease vivo + TITULAR e esta sessao.

        A terceira condicao e nova e nao e redundante: sem ela, uma
        sessao poderia gravar sob o lease de outra se o fence coincidir
        — e o nome no lease deixaria de significar alguma coisa.
        """
        self._lock.verificar()
        titular = titular_atual(self.dir)
        if titular is None:
            raise EscritorObsoleto(
                "lease do repositorio expirado: readquirir o escritor")
        if titular.get("sessao") != self.sessao:
            raise EscritorObsoleto(
                f"titular do repositorio e {titular.get('sessao')!r}, "
                f"nao {self.sessao!r}")

    def liberar(self) -> None:
        """Solta o lock E EXPIRA o lease que concedeu.

        A segunda metade e o remedio do §9.4, N1. `EscritorP1.liberar`
        solta o lock e deixa o `.lease` com validade futura: quem le o
        lease depois ve um escritor vivo que ja saiu, e um lease que
        sobrevive ao detentor afirma o que nao ha. Aqui o lease sai
        VENCIDO, com `liberado_em` registrado — some-lo apagaria a
        evidencia de que houve titular.
        """
        try:
            self._gravar_lease(time.time(), liberado=True)
        finally:
            self._lock.liberar()

    def _gravar_lease(self, expira_em: float, liberado: bool = False) -> None:
        dados = {"sessao": self.sessao, "pid": os.getpid(),
                 "token": self._lock.token, "renovado_em": time.time(),
                 "expira_em": expira_em}
        if liberado:
            dados["liberado_em"] = dados["renovado_em"]
        tmp = self.caminho_lease + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.caminho_lease)
