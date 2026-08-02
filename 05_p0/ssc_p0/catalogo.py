"""Catalogo de executores (falsos) com perfil de capacidade (D6 §3).

Cada executor declara nivel (L1/L2/L3) e perfil com as 8 dimensoes:
modalidade, ferramentas, formato_saida, contexto_max_tokens, dominio,
privacidade, latencia_max_ms, orcamento_max_custo.

Aliases sao registrados; a resolucao de alias fica gravada na decisao/attempt.
ALIAS NAO PROVA IDENTIDADE (D5 §5): o que vale para evidencia e o observado.
"""

from .canonico import sha256_de

_ORDEM_NIVEL = {"L1": 1, "L2": 2, "L3": 3}


class ExecutorDesconhecido(Exception):
    """Executor (ou alias) fora do catalogo: falha fechada."""


class Catalogo:
    """Catalogo fechado de executores falsos + aliases."""

    def __init__(self, executores: list, aliases: dict | None = None):
        self.executores = {e["executor_id"]: dict(e) for e in executores}
        for e in self.executores.values():
            e.setdefault("aliases_registrados", [])
        self.aliases = dict(aliases or {})
        for alias, alvo in self.aliases.items():
            if alvo not in self.executores:
                raise ExecutorDesconhecido(f"alias {alias!r} aponta fora do catalogo")

    def hash_catalogo(self) -> str:
        return sha256_de(self.to_dict())

    def to_dict(self) -> dict:
        return {"executores": self.executores, "aliases": self.aliases}

    def resolver(self, selecao: dict) -> tuple[dict, bool]:
        """Resolve selecao {provedor, modelo, effort} no catalogo.

        Devolve (executor, alias_usado). Modelo pode ser alias registrado.
        """
        provedor = selecao["provedor"]
        modelo = selecao["modelo"]
        alias_usado = False
        chave = f"{provedor}/{modelo}"
        if chave not in self.executores and modelo in self.aliases:
            chave = self.aliases[modelo]
            alias_usado = True
        executor = self.executores.get(chave)
        if executor is None:
            raise ExecutorDesconhecido(f"executor fora do catalogo: {chave!r}")
        if executor["provedor"] != provedor and not alias_usado:
            raise ExecutorDesconhecido(
                f"provedor {provedor!r} diverge do catalogo para {chave!r}"
            )
        if selecao.get("effort") not in executor.get("efforts", []):
            raise ExecutorDesconhecido(
                f"effort {selecao.get('effort')!r} nao suportado por {chave!r}"
            )
        resolvido = {
            "ferramenta": executor["ferramenta"],
            "provedor": executor["provedor"],
            "modelo": executor["modelo"],
            "effort": selecao.get("effort"),
            "executor_id": executor["executor_id"],
        }
        return resolvido, alias_usado

    def atende(self, executor: dict, nivel_req: str, perfil_req: dict) -> tuple[bool, list]:
        """Regra de casamento D6 §3: nivel >= exigido e TODAS as dimensoes.

        Devolve (atende, motivos_de_falha).
        """
        motivos = []
        if _ORDEM_NIVEL[executor["nivel"]] < _ORDEM_NIVEL[nivel_req]:
            motivos.append(
                f"nivel {executor['nivel']} < exigido {nivel_req}"
            )
        perfil = executor["perfil"]
        if perfil_req.get("modalidade") not in perfil.get("modalidades", []):
            motivos.append("modalidade nao atendida")
        faltantes = set(perfil_req.get("ferramentas", [])) - set(perfil.get("ferramentas", []))
        if faltantes:
            motivos.append(f"ferramentas ausentes: {sorted(faltantes)}")
        if perfil_req.get("formato_saida") not in perfil.get("formatos", []):
            motivos.append("formato_saida nao atendido")
        if perfil.get("contexto_max_tokens", 0) < perfil_req.get("contexto_max_tokens", 0):
            motivos.append("contexto_max_tokens insuficiente")
        dominio = perfil_req.get("dominio")
        if dominio and dominio not in perfil.get("dominios", []) and "*" not in perfil.get("dominios", []):
            motivos.append(f"dominio {dominio!r} nao atendido")
        if perfil_req.get("privacidade") == "local-only" and perfil.get("privacidade") != "local-only":
            motivos.append("privacidade local-only exigida (executor remoto)")
        lat = perfil_req.get("latencia_max_ms")
        if lat is not None and perfil.get("latencia_base_ms", 0) > lat:
            motivos.append("latencia base acima do teto exigido")
        teto = perfil_req.get("orcamento_max_custo")
        if teto is not None and perfil.get("custo_base", 0) > teto:
            motivos.append("custo base acima do teto exigido")
        return (not motivos, motivos)


def catalogo_padrao() -> Catalogo:
    """Catalogo falso da P0: >= 2 provedores (independencia do juiz, D7 §6)."""
    executores = [
        {
            "executor_id": "prov-a/modelo-l1",
            "ferramenta": "fake-cli",
            "provedor": "prov-a",
            "modelo": "modelo-l1",
            "efforts": ["baixo", "alto"],
            "nivel": "L1",
            "perfil": {
                "modalidades": ["texto"],
                "ferramentas": [],
                "formatos": ["livre"],
                "contexto_max_tokens": 8000,
                "dominios": ["geral"],
                "privacidade": "local-only",
                "latencia_base_ms": 50,
                "custo_base": 0.001,
            },
        },
        {
            "executor_id": "prov-a/modelo-x",
            "ferramenta": "fake-cli",
            "provedor": "prov-a",
            "modelo": "modelo-x",
            "efforts": ["baixo", "alto"],
            "nivel": "L2",
            "perfil": {
                "modalidades": ["texto", "codigo"],
                "ferramentas": [],
                "formatos": ["livre", "json-schema"],
                "contexto_max_tokens": 64000,
                "dominios": ["geral", "codigo"],
                "privacidade": "remoto-permitido",
                "latencia_base_ms": 200,
                "custo_base": 0.01,
            },
        },
        {
            "executor_id": "prov-b/modelo-y",
            "ferramenta": "fake-openai-compat",
            "provedor": "prov-b",
            "modelo": "modelo-y",
            "efforts": ["baixo", "alto"],
            "nivel": "L2",
            "perfil": {
                "modalidades": ["texto", "codigo"],
                "ferramentas": [],
                "formatos": ["livre", "json-schema"],
                "contexto_max_tokens": 64000,
                "dominios": ["geral", "codigo"],
                "privacidade": "remoto-permitido",
                "latencia_base_ms": 250,
                "custo_base": 0.012,
            },
        },
        {
            "executor_id": "prov-b/modelo-l3",
            "ferramenta": "fake-openai-compat",
            "provedor": "prov-b",
            "modelo": "modelo-l3",
            "efforts": ["baixo", "alto"],
            "nivel": "L3",
            "perfil": {
                "modalidades": ["texto", "codigo", "mista"],
                "ferramentas": [],
                "formatos": ["livre", "json-schema", "patch"],
                "contexto_max_tokens": 128000,
                "dominios": ["*"],
                "privacidade": "remoto-permitido",
                "latencia_base_ms": 800,
                "custo_base": 0.08,
            },
        },
        {
            "executor_id": "prov-c/modelo-juiz",
            "ferramenta": "fake-openai-compat",
            "provedor": "prov-c",
            "modelo": "modelo-juiz",
            "efforts": ["baixo", "alto"],
            "nivel": "L3",
            "perfil": {
                "modalidades": ["texto", "codigo", "mista"],
                "ferramentas": [],
                "formatos": ["livre", "json-schema"],
                "contexto_max_tokens": 128000,
                "dominios": ["*"],
                "privacidade": "remoto-permitido",
                "latencia_base_ms": 900,
                "custo_base": 0.09,
            },
        },
    ]
    aliases = {"barato": "prov-a/modelo-l1", "forte": "prov-b/modelo-l3"}
    return Catalogo(executores, aliases)
