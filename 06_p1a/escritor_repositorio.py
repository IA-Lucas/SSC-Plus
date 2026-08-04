"""Escritor unico POR REPOSITORIO — o MECANISMO VIVO desde a P1-A.5.

O DEFEITO, aberto desde a `99_achados-governanca-20260731.md` §7,
elevado a MAJOR por revisor independente na P1-A.3.6 e mantido
NAO-FECHADO na P1-A.4 (achado `P1A4-1`):

    `LockSessao` tranca `locks/<sessao_id>.lock`. Duas missoes de NOMES
    DIFERENTES trancam ARQUIVOS DIFERENTES, e nenhuma exclui a outra. O
    escritor unico entre missoes NAO EXISTE — o que existe e escritor
    unico por nome de sessao, que e outra propriedade.

E a frase do revisor que fecha o ponto: *"a ordem manual do Fundador nao
substitui exclusao mutua"*.

ESTE MODULO E O ESCRITOR EM USO. Ate a P1-A.4 ele existia em ISOLADO —
implementado, testado e commitado sem nenhum consumidor — por ordem
expressa: trocar o escritor no meio de uma missao de correcao seria
mudar o chao enquanto se anda sobre ele. O revisor da P1-A.4 mediu
exatamente esse estado e o chamou de **falha de integracao**: *"declara e
testa que o lock unico novo nao esta em uso; o mecanismo vivo continua
permitindo escritores de nomes distintos"*. A troca foi autorizada na
P1-A.5, ordem 2, e esta feita: o renovador, a prova minima e a
verificacao canonica (`contencao.verificar_lock`) passam por aqui.

O QUE MUDOU, em duas linhas:

1. UM LOCK PARA O REPOSITORIO. O arquivo trancado e sempre
   `locks/repositorio.lock`, qualquer que seja o nome da missao. O nome
   deixa de escolher o arquivo e passa a ser apenas o TITULAR
   registrado no lease — que e o que ele sempre deveria ter sido.
2. `liberar()` EXPIRA O LEASE QUE CONCEDEU. `EscritorP1.liberar` solta o
   lock do SO e deixa o `.lease` com validade futura: quem le o lease
   depois ve um escritor vivo que ja saiu. Um lease que sobrevive ao seu
   detentor e pior que nenhum — ele afirma o que nao ha.

LIMITE DECLARADO. A exclusao vale para quem passa por AQUI. Um processo
que escreva no repositorio sem adquirir este escritor nao e barrado por
nada — o mecanismo e cooperativo, como todo lock de arquivo, e nenhum
teste deste modulo afirma o contrario. Em particular, `git commit` nao
consulta lease nenhum, e a P1-A.3.9 mediu isso
(`tests/test_fronteira_escritor_p1a39.py`): a troca de mecanismo NAO
move essa fronteira.

`EscritorP1` continua existindo e continua correto no que sempre
garantiu — exclusao dentro de UM nome. Ele deixa de ser o escritor das
operacoes; nao foi apagado, e a prova cruzada dos testes depende dele
para medir o ACHADO 4 em vez de cita-lo.
"""

import json
import os
import time

from escritor import LEASE_PADRAO_S, EscritorP1
from ssc_p0.writelock import EscritorObsoleto, LockIndisponivel, LockSessao

__all__ = ["NOME_DO_LOCK", "EscritorObsoleto", "EscritorRepositorio",
           "LockIndisponivel", "caminho_fence", "caminho_lease",
           "lease_expirado", "titular_atual"]

# Nome UNICO do lock do repositorio. Nao e configuravel de proposito:
# tornar isto um parametro reabriria o ACHADO 4 pela porta dos fundos —
# bastaria cada missao passar um nome proprio.
NOME_DO_LOCK = "repositorio"

# Uma implementacao so da leitura de validade, partilhada com o escritor
# por sessao. Copiar esta funcao para ca reabriria o mecanismo dos
# achados 7, 10 e 14 — a copia que ninguem exercita fica para tras. Ela
# nao depende do NOME do lease: le `expira_em` do caminho que receber.
lease_expirado = EscritorP1.lease_expirado


def _caminho(diretorio_locks, sufixo: str) -> str:
    return os.path.join(str(diretorio_locks), f"{NOME_DO_LOCK}{sufixo}")


def caminho_lease(diretorio_locks) -> str:
    """Caminho CANONICO do lease do repositorio.

    Existe para que nenhum outro modulo volte a montar
    `f"{sessao}.lease"` por conta propria: era assim que o nome da missao
    escolhia o arquivo, e e exatamente o ACHADO 4. Quem precisa do
    caminho pede aqui.
    """
    return _caminho(diretorio_locks, ".lease")


def caminho_fence(diretorio_locks) -> str:
    """Caminho CANONICO do fence do repositorio — ver `caminho_lease`."""
    return _caminho(diretorio_locks, ".fence")


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
