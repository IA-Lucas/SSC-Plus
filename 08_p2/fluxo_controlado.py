"""Fluxo supervisionado: contexto -> plano -> proposta -> revisao -> juiz -> teste.

Os modelos operam somente em leitura. Para tarefas que mudam codigo, o autor
produz um patch; esse patch e testado numa copia isolada e fica pendente. A
arvore real so pode ser alterada por ``aplicar_patch_aprovado`` com um token
explicito, depois de todos os gates terem passado.

``SSC_STATUS: SUCESSO`` pertence ao contrato de transporte do provedor. Aqui
ele nunca basta: cada papel tem um marcador de qualidade proprio, e ainda ha
revisao, julgamento e teste locais independentes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


OPERACOES = {
    "analisar": {"rotulo": "Analisar projeto", "altera": False},
    "corrigir": {"rotulo": "Corrigir problema", "altera": True},
    "implementar": {"rotulo": "Implementar funcionalidade", "altera": True},
    "revisar": {"rotulo": "Revisar alteracao", "altera": False},
}

ETAPAS = (
    ("contextualizar", "kimi", "autor"),
    ("planejar", "codex", "autor"),
    ("implementar", "codex", "autor"),
    ("revisar", "claude", "revisor"),
    ("julgar", "google", "juiz"),
)

MARCADORES = {
    "contextualizar": ("SSC_CONTEXTO", {"PRONTO"}),
    "planejar": ("SSC_PLANO", {"PRONTO"}),
    "implementar": ("SSC_IMPLEMENTACAO", {"PROPOSTA", "SEM_ALTERACAO"}),
    "revisar": ("SSC_REVISAO", {"APROVADA", "REPROVADA"}),
    "julgar": ("SSC_JULGAMENTO", {"APROVADO", "REPROVADO"}),
}


class FluxoRecusado(RuntimeError):
    """Uma etapa ou gate recusou continuar."""


def _sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _marcador_unico(saida: str, nome: str, aceitos: set[str]) -> str:
    padrao = re.compile(rf"(?m)^\s*{re.escape(nome)}:\s*([A-Z_]+)\s*$")
    valores = padrao.findall(saida or "")
    if len(valores) != 1:
        raise FluxoRecusado(
            f"{nome} deve aparecer exatamente uma vez; observado={valores}")
    if valores[0] not in aceitos:
        raise FluxoRecusado(
            f"{nome} fora do contrato: {valores[0]!r}")
    return valores[0]


def extrair_patch(saida: str) -> str:
    """Extrai um unified diff depois de SSC_PATCH, sem aceitar prosa como patch."""
    marcador = "SSC_PATCH:"
    if (saida or "").count(marcador) != 1:
        raise FluxoRecusado("a proposta deve conter um unico SSC_PATCH:")
    trecho = saida.split(marcador, 1)[1].strip()
    cercado = re.fullmatch(r"```(?:diff|patch)?\s*\n([\s\S]*?)\n```", trecho)
    patch = (cercado.group(1) if cercado else trecho).strip() + "\n"
    if not patch.startswith("diff --git a/"):
        raise FluxoRecusado("SSC_PATCH nao contem unified diff git")
    validar_caminhos_patch(patch)
    return patch


def caminhos_do_patch(patch: str) -> list[str]:
    caminhos = []
    for linha in patch.splitlines():
        if not linha.startswith("+++ "):
            continue
        valor = linha[4:].split("\t", 1)[0]
        if valor == "/dev/null":
            continue
        if not valor.startswith("b/"):
            raise FluxoRecusado(f"caminho de patch sem prefixo b/: {valor}")
        caminhos.append(valor[2:])
    if not caminhos:
        raise FluxoRecusado("patch sem caminho de destino")
    return sorted(set(caminhos))


def validar_caminhos_patch(patch: str) -> None:
    for relativo in caminhos_do_patch(patch):
        p = Path(relativo)
        if p.is_absolute() or ".." in p.parts or not relativo.strip():
            raise FluxoRecusado(f"patch tenta sair do workspace: {relativo}")
        if p.parts and p.parts[0] in {".git", "locks"}:
            raise FluxoRecusado(f"patch toca estado de controle: {relativo}")


def _prompt(etapa: str, operacao: str, pedido: str,
            anteriores: dict[str, str]) -> tuple[str, str]:
    contexto = "\n\n".join(
        f"--- SAIDA {nome.upper()} ---\n{texto}"
        for nome, texto in anteriores.items())
    comum = (
        f"Operacao: {OPERACOES[operacao]['rotulo']}\n"
        f"Pedido do operador: {pedido}\n\n"
        "Trabalhe somente em leitura. Nao altere arquivos, configuracao ou "
        "estado externo. Fundamente em caminhos e fatos do snapshot.\n"
        "Todo marcador SSC_* deve ocupar uma linha propria, sem negrito, "
        "sem crase e sem bloco de codigo ao redor.\n")
    instrucoes = {
        "contextualizar": (
            "Mapeie o contexto amplo, riscos, arquivos relevantes e lacunas. "
            "Use somente o snapshot fornecido; nao procure arquivos fora do "
            "contexto-ssc.txt. Termine com a linha SSC_CONTEXTO: PRONTO."),
        "planejar": (
            "Produza um plano verificavel a partir do contexto. Termine com "
            "a linha SSC_PLANO: PRONTO."),
        "implementar": (
            "Atue como autor. Para corrigir/implementar, proponha um unico "
            "unified diff git depois de SSC_PATCH: e declare "
            "SSC_IMPLEMENTACAO: PROPOSTA. Para analisar/revisar, nao invente "
            "patch e declare SSC_IMPLEMENTACAO: SEM_ALTERACAO."),
        "revisar": (
            "Revise criticamente plano e proposta. Procure falhas, regressao, "
            "seguranca e testes ausentes. Termine com exatamente "
            "SSC_REVISAO: APROVADA ou SSC_REVISAO: REPROVADA."),
        "julgar": (
            "Julgue transversalmente a tarefa, proposta e revisao. Nao aceite "
            "por deferencia nem por SSC_STATUS. Termine com exatamente "
            "SSC_JULGAMENTO: APROVADO ou SSC_JULGAMENTO: REPROVADO."),
    }
    tarefa = comum + instrucoes[etapa]
    if contexto:
        tarefa += "\n\n" + contexto
    criterio = f"contrato estruturado de {etapa} e evidencia verificavel"
    return tarefa, criterio


def executar_fluxo(operacao: str, pedido: str, despachar: Callable,
                   testar: Callable[[str | None], dict]) -> dict:
    """Executa as cinco etapas e o teste; nao aplica qualquer alteracao."""
    if operacao not in OPERACOES:
        raise ValueError(f"operacao desconhecida: {operacao}")
    if not pedido.strip():
        raise ValueError("pedido vazio")

    id_fluxo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    saidas: dict[str, str] = {}
    evidencias = []
    patch = None

    for etapa, provedor, papel in ETAPAS:
        tarefa, criterio = _prompt(etapa, operacao, pedido, saidas)
        registro = despachar(
            etapa=etapa, provedor=provedor, papel=papel,
            tarefa=tarefa, criterio=criterio)
        if registro.get("status") != "sucesso" or not registro.get("saida"):
            raise FluxoRecusado(
                f"{etapa}/{provedor} nao concluiu: {registro.get('detalhe')}")
        saida = registro["saida"]
        nome, aceitos = MARCADORES[etapa]
        valor = _marcador_unico(saida, nome, aceitos)

        if etapa == "implementar":
            esperado = "PROPOSTA" if OPERACOES[operacao]["altera"] \
                else "SEM_ALTERACAO"
            if valor != esperado:
                raise FluxoRecusado(
                    f"implementacao declarou {valor}; esperado {esperado}")
            if valor == "PROPOSTA":
                patch = extrair_patch(saida)
        elif etapa == "revisar" and valor != "APROVADA":
            raise FluxoRecusado("Claude reprovou a proposta")
        elif etapa == "julgar" and valor != "APROVADO":
            raise FluxoRecusado("Google reprovou a proposta")

        saidas[etapa] = saida
        evidencias.append({
            "etapa": etapa, "provedor_exigido": provedor, "papel": papel,
            "marcador": f"{nome}: {valor}", "saida_sha256": _sha256_texto(saida),
            "attempts": registro.get("attempts", []),
        })

    teste = testar(patch)
    if teste.get("returncode") != 0:
        raise FluxoRecusado(
            f"testes reprovaram com codigo {teste.get('returncode')}")

    return {
        "fluxo_id": id_fluxo,
        "operacao": operacao,
        "pedido_sha256": _sha256_texto(pedido),
        "sequencia": [e[0] for e in ETAPAS] + ["testar"],
        "etapas": evidencias,
        "teste": teste,
        "patch": patch,
        "patch_sha256": _sha256_texto(patch) if patch else None,
        "qualidade_aprovada": True,
        "aplicado": False,
        "pronto_para_aprovacao_explicita": bool(patch),
    }


def _ignorar_copia(_base: str, nomes: list[str]) -> set[str]:
    return {n for n in nomes if n in {
        ".git", "locks", "__pycache__", ".venv", "node_modules",
    } or n.endswith(".pyc")}


def testar_patch_isolado(patch: str | None, raiz: str | Path,
                         comando: list[str] | None = None) -> dict:
    """Testa o estado atual ou aplica o patch somente numa copia descartavel."""
    raiz = Path(raiz).resolve()
    comando = comando or [sys.executable, "scripts/verificar.py", "--rapido"]
    with tempfile.TemporaryDirectory(prefix="ssc-fluxo-teste-") as tmp:
        copia = Path(tmp) / "workspace"
        shutil.copytree(raiz, copia, ignore=_ignorar_copia)
        if patch:
            arquivo_patch = Path(tmp) / "proposta.patch"
            arquivo_patch.write_text(patch, encoding="utf-8", newline="\n")
            checagem = subprocess.run(
                ["git", "apply", "--check", str(arquivo_patch)], cwd=copia,
                capture_output=True, text=True)
            if checagem.returncode:
                return {"returncode": checagem.returncode,
                        "fase": "git-apply-check",
                        "stdout_sha256": _sha256_texto(checagem.stdout),
                        "stderr": checagem.stderr[-4000:]}
            aplicada = subprocess.run(
                ["git", "apply", str(arquivo_patch)], cwd=copia,
                capture_output=True, text=True)
            if aplicada.returncode:
                return {"returncode": aplicada.returncode,
                        "fase": "git-apply",
                        "stdout_sha256": _sha256_texto(aplicada.stdout),
                        "stderr": aplicada.stderr[-4000:]}
        resultado = subprocess.run(comando, cwd=copia, capture_output=True,
                                   text=True)
        return {
            "returncode": resultado.returncode,
            "fase": "suite-isolada" if patch else "suite-atual",
            "comando": list(comando),
            "stdout_sha256": _sha256_texto(resultado.stdout),
            "stderr_sha256": _sha256_texto(resultado.stderr),
            "stdout_final": resultado.stdout[-2000:],
            "stderr_final": resultado.stderr[-2000:],
        }


def _hash_arquivo(caminho: Path) -> str | None:
    if not caminho.exists():
        return None
    if not caminho.is_file() or caminho.is_symlink():
        raise FluxoRecusado(f"alvo nao e arquivo regular: {caminho}")
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def preparar_aprovacao(resultado: dict, raiz: str | Path,
                       dir_estado: str | Path) -> tuple[Path, str]:
    """Persiste proposta aprovada pelos gates e devolve token uma unica vez."""
    patch = resultado.get("patch")
    if not patch or not resultado.get("qualidade_aprovada"):
        raise FluxoRecusado("fluxo sem patch aprovado pelos gates")
    raiz = Path(raiz).resolve()
    destino = Path(dir_estado).resolve() / resultado["fluxo_id"]
    destino.mkdir(parents=True, exist_ok=False)
    token = secrets.token_urlsafe(18)
    alvos = {p: _hash_arquivo(raiz / p) for p in caminhos_do_patch(patch)}
    estado = {
        "fluxo_id": resultado["fluxo_id"],
        "patch_sha256": _sha256_texto(patch),
        "token_sha256": _sha256_texto(token),
        "alvos_antes": alvos,
        "qualidade_aprovada": True,
        "aplicado": False,
    }
    (destino / "proposta.patch").write_text(
        patch, encoding="utf-8", newline="\n")
    (destino / "estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    return destino, token


def aplicar_patch_aprovado(dir_fluxo: str | Path, token: str,
                            raiz: str | Path) -> dict:
    """Aplica somente apos token explicito, gates verdes e arvore sem deriva."""
    dir_fluxo = Path(dir_fluxo).resolve()
    raiz = Path(raiz).resolve()
    estado_path = dir_fluxo / "estado.json"
    estado = json.loads(estado_path.read_text(encoding="utf-8"))
    patch_path = dir_fluxo / "proposta.patch"
    patch = patch_path.read_text(encoding="utf-8")
    if estado.get("aplicado") or not estado.get("qualidade_aprovada"):
        raise FluxoRecusado("fluxo ja aplicado ou sem qualidade aprovada")
    if not secrets.compare_digest(_sha256_texto(token),
                                  estado.get("token_sha256", "")):
        raise FluxoRecusado("aprovacao explicita invalida")
    if _sha256_texto(patch) != estado.get("patch_sha256"):
        raise FluxoRecusado("patch divergiu depois dos testes")
    for relativo, esperado in estado["alvos_antes"].items():
        if _hash_arquivo(raiz / relativo) != esperado:
            raise FluxoRecusado(f"alvo mudou depois dos testes: {relativo}")

    checagem = subprocess.run(
        ["git", "apply", "--check", str(patch_path)], cwd=raiz,
        capture_output=True, text=True)
    if checagem.returncode:
        raise FluxoRecusado("git apply --check recusou: " + checagem.stderr)
    aplicada = subprocess.run(["git", "apply", str(patch_path)], cwd=raiz,
                              capture_output=True, text=True)
    if aplicada.returncode:
        raise FluxoRecusado("git apply recusou: " + aplicada.stderr)
    estado["aplicado"] = True
    estado["aplicado_em_utc"] = datetime.now(timezone.utc).isoformat()
    estado_path.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    return estado
