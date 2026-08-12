"""Policy Gateway (D6 §2.3): o portao que bloqueia.

Veta; nao julga merito, nao executa. Verifica toda RoutingDecision contra a
politica vigente e contra o ENVELOPE de aprovacao de custo (D5 §4): modelo
fora da lista permitida = veto, mesmo estando na politica. Verifica orcamento
antes de cada attempt: estouro = EscalationEvent, nunca estouro silencioso.
"""

from datetime import datetime, timezone

from .catalogo import Catalogo, ExecutorDesconhecido
from .canonico import Relogio


class OrcamentoEstourado(Exception):
    """consumido + previsto acima do teto: escalonar, nunca seguir."""


class PolicyGateway:
    def __init__(self, politica: dict, catalogo: Catalogo, relogio: Relogio):
        self.politica = politica
        self.catalogo = catalogo
        self.relogio = relogio

    def verificar_decisao(self, decisao, workunit) -> list:
        """Devolve lista de vetos (vazia = decisao permitida)."""
        vetos = []
        rota = decisao.classificacao.get("rota")
        if rota not in self.politica.get("rotas_permitidas", []):
            vetos.append(f"rota {rota!r} fora da politica")
        selecao = decisao.selecao
        chave = f"{selecao['provedor']}/{selecao['modelo']}"
        permitidos = self.politica.get("executores", [])
        catalogo = self.catalogo
        # Alias registrado resolve para executor da politica.
        if chave not in permitidos and selecao["modelo"] in catalogo.aliases:
            chave = catalogo.aliases[selecao["modelo"]]
        if chave not in permitidos:
            vetos.append(f"executor {chave!r} fora da politica")
        else:
            try:
                resolvido, _ = catalogo.resolver(selecao)
                executor = catalogo.executores[resolvido["executor_id"]]
                atende, motivos = catalogo.atende(
                    executor, workunit.nivel_capacidade,
                    workunit.perfil_capacidade)
                if not atende:
                    vetos.append("perfil de capacidade nao atendido: "
                                 + "; ".join(motivos))
            except ExecutorDesconhecido as exc:
                vetos.append(str(exc))
        modos = self.politica.get("classe_modos", {}).get(
            workunit.classe_governanca, [])
        if modos and selecao.get("modo") not in modos:
            vetos.append(
                f"modo {selecao.get('modo')!r} incoerente com "
                f"classe {workunit.classe_governanca}")
        # O envelope autoriza a ROTA inteira, nao apenas a cobranca. Custo
        # zero, controle autonomo e fallback continuam sujeitos a modelo,
        # effort, modo, validade e teto. Caso contrario um chamador podia
        # escolher exatamente esses rotulos para contornar a aprovacao.
        custo = decisao.custo_previsto or {}
        vetos.extend(self._vetos_envelope(
            decisao.aprovacao_custo, chave, selecao, custo,
            tem_fallback=bool(decisao.alternativas)))
        return vetos

    def _expirado_ou_invalido(self, validade) -> bool:
        try:
            limite = datetime.fromisoformat(
                str(validade).replace("Z", "+00:00"))
            if limite.tzinfo is None:
                return True
            atual = datetime.fromisoformat(
                str(self.relogio.espiar()).replace("Z", "+00:00"))
            if atual.tzinfo is None:
                atual = atual.replace(tzinfo=timezone.utc)
            return atual.astimezone(timezone.utc) >= limite.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return True

    def _vetos_envelope(self, ap, chave, selecao, custo,
                        tem_fallback=False) -> list:
        if not isinstance(ap, dict):
            return ["aprovacao_custo (envelope) obrigatoria e ausente "
                    "(portao bloqueante)"]
        vetos = []
        if chave not in ap.get("modelos_permitidos", []):
            vetos.append(f"modelo {chave!r} fora do envelope aprovado "
                         "(mesmo estando na politica)")
        if selecao.get("effort") not in ap.get("efforts_permitidos", []):
            vetos.append(f"effort {selecao.get('effort')!r} fora do envelope")
        valor = custo.get("valor", 0)
        if not isinstance(valor, (int, float)) or valor < 0:
            vetos.append("custo previsto invalido no envelope")
        elif valor > ap.get("teto_custo", -1):
            vetos.append("custo previsto acima do teto do envelope")
        if selecao.get("modo") != ap.get("modo"):
            vetos.append("modo divergente do envelope aprovado")
        if self._expirado_ou_invalido(ap.get("validade")):
            vetos.append("envelope de aprovacao expirado ou invalido")
        if tem_fallback and not ap.get("fallback_autorizado"):
            vetos.append("fallback nao autorizado no envelope")
        return vetos

    def verificar_fallback_envelope(self, decisao, para_executor: dict) -> bool:
        """Fallback so dentro do envelope aprovado (D5 §6).

        Fora do envelope = escalonamento, nao tentativa.
        """
        ap = decisao.aprovacao_custo
        modelo = para_executor["modelo"]
        if modelo in self.catalogo.aliases:
            chave = self.catalogo.aliases[modelo]
        else:
            chave = f"{para_executor['provedor']}/{modelo}"
        return not self._vetos_envelope(
            ap, chave, para_executor, decisao.custo_previsto or {},
            tem_fallback=True)

    def verificar_orcamento(self, orcamento: dict, custo_previsto: dict | None) -> None:
        """Estouro = OrcamentoEstourado (o Execution emite EscalationEvent)."""
        consumido = orcamento.get("consumido_custo", 0.0)
        previsto = (custo_previsto or {}).get("valor", 0.0)
        if consumido + previsto > orcamento.get("teto_custo", float("inf")):
            raise OrcamentoEstourado(
                f"consumido {consumido} + previsto {previsto} > teto "
                f"{orcamento.get('teto_custo')}")


def politica_padrao() -> dict:
    """Politica falsa da P0 (hash entra no envelope como politica_ref)."""
    return {
        "nome": "politica-p0",
        "rotas_permitidas": ["padrao", "barata", "especializada"],
        "executores": [
            "prov-a/modelo-l1", "prov-a/modelo-x", "prov-b/modelo-y",
            "prov-b/modelo-l3", "prov-c/modelo-juiz",
        ],
        "classe_modos": {
            "C0": ["read-only", "worktree", "escrita-aprovada"],
            "C1": ["read-only", "worktree", "escrita-aprovada"],
            "C2": ["worktree", "escrita-aprovada"],
            "C3": ["escrita-aprovada"],
        },
    }


def envelope_aprovacao_padrao() -> dict:
    """Envelope de custo aprovado pelo humano (D5 §4)."""
    return {
        "modelos_permitidos": [
            "prov-a/modelo-l1", "prov-a/modelo-x", "prov-b/modelo-y",
            "prov-b/modelo-l3",
        ],
        "efforts_permitidos": ["baixo", "alto"],
        "teto_custo": 1.0,
        "modo": "read-only",
        "validade": "2027-01-01T00:00:00Z",
        "fallback_autorizado": True,
    }
