#!/usr/bin/env python3
"""Entrada operacional do fluxo controlado, sempre dentro da capsula."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import caminhos
import fluxo_controlado as fluxo
import runner_p2
from capsula import exigir_capsula_limpa, verificar_capsula
from contencao import redigir, verificar_lock
from seguranca_artefatos import gravar_json_atomico


DIR_EVIDENCIAS = Path(caminhos.RAIZ) / "08_p2" / "evidencias"
DIR_ESTADO = Path(caminhos.RAIZ) / "locks" / "fluxos"
SESSAO = os.environ.get("SSC_LOCK_SESSAO", caminhos.SESSAO_LOCK)


def _id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _sha(texto: str | None) -> str | None:
    if texto is None:
        return None
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _documento_redigido(documento: dict) -> dict:
    """Redige o documento integral antes de qualquer persistencia publica."""
    return json.loads(redigir(json.dumps(documento, ensure_ascii=False)))


def _publico(registro: dict, etapa: str, provedor: str) -> dict:
    saida = registro.get("saida")
    return {
        "etapa": etapa,
        "provedor_exigido": provedor,
        "status": registro.get("status"),
        "detalhe": registro.get("detalhe"),
        "work_unit_id": registro.get("work_unit_id"),
        "sessao_id": registro.get("sessao_id"),
        "attempts": registro.get("attempts", []),
        "contexto_workspace": registro.get("contexto_workspace"),
        "efeito_externo_medido": registro.get("efeito_externo_medido", []),
        "saida_bytes": len(saida.encode("utf-8")) if saida else 0,
        "saida_sha256": _sha(saida),
        "conteudo_saida_persistido": False,
    }


def preparar(args) -> int:
    exigir_capsula_limpa()
    abertura = verificar_lock(caminhos.RAIZ, SESSAO)
    fence = abertura.get("fence")
    preflight = runner_p2.carregar_preflight(args.preflight, args.validade_h)
    registros_publicos = []

    def despachar(**pedido):
        registro = runner_p2.executar(
            tarefa=pedido["tarefa"], criterio=pedido["criterio"],
            preflight=preflight, provedor=pedido["provedor"],
            papel=pedido["papel"], timeout=args.timeout,
            contexto_workspace=True)
        registros_publicos.append(_publico(
            registro, pedido["etapa"], pedido["provedor"]))
        return registro

    def testar(patch):
        return fluxo.testar_patch_isolado(patch, caminhos.RAIZ)

    try:
        resultado = fluxo.executar_fluxo(
            args.operacao, args.tarefa, despachar, testar)
    except fluxo.FluxoRecusado as exc:
        verificar_lock(caminhos.RAIZ, SESSAO, fence)
        falha_id = _id()
        recibo_falha = {
            "tipo": "fluxo-controlado-ssc-plus",
            "fluxo_id": falha_id,
            "status": "recusado",
            "motivo": str(exc),
            "operacao": args.operacao,
            "pedido_sha256": _sha(args.tarefa),
            "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
            "preflight_origem": str(Path(args.preflight).name),
            "preflight_idade_s": preflight["_idade_s"],
            "capsula_violacoes": verificar_capsula(os.environ),
            "lease": {"sessao": SESSAO, "fence": fence},
            "registros_etapas": registros_publicos,
            "qualidade_aprovada": False,
            "aplicado": False,
        }
        DIR_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
        caminho_falha = DIR_EVIDENCIAS / f"fluxo-{falha_id}-recusado.json"
        gravar_json_atomico(caminho_falha, _documento_redigido(recibo_falha))
        print(f"FLUXO RECUSADO: {exc}")
        print(f"evidencia da parada: {caminho_falha}")
        return 2
    verificar_lock(caminhos.RAIZ, SESSAO, fence)

    token = None
    estado_dir = None
    if resultado["pronto_para_aprovacao_explicita"]:
        estado_dir, token = fluxo.preparar_aprovacao(
            resultado, caminhos.RAIZ, DIR_ESTADO)

    recibo = {k: v for k, v in resultado.items() if k != "patch"}
    recibo.update({
        "tipo": "fluxo-controlado-ssc-plus",
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "preflight_origem": str(Path(args.preflight).name),
        "preflight_idade_s": preflight["_idade_s"],
        "capsula_violacoes": verificar_capsula(os.environ),
        "lease": {"sessao": SESSAO, "fence": fence},
        "registros_etapas": registros_publicos,
        "estado_aprovacao": str(estado_dir) if estado_dir else None,
        "token_persistido": False,
    })
    DIR_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    caminho = DIR_EVIDENCIAS / f"fluxo-{resultado['fluxo_id']}.json"
    gravar_json_atomico(caminho, _documento_redigido(recibo))
    print(f"fluxo concluido e registrado: {caminho}")
    if token:
        print("PATCH TESTADO, REVISADO E JULGADO; AINDA NAO APLICADO.")
        print(f"fluxo_id: {resultado['fluxo_id']}")
        print(f"token de aprovacao (nao sera persistido): {token}")
        print("Para aplicar, execute novamente e forneca esse fluxo_id e token.")
    else:
        print("Operacao somente leitura concluida; nenhuma alteracao para aplicar.")
    return 0


def aplicar(args) -> int:
    exigir_capsula_limpa()
    if not args.token:
        raise SystemExit("PARADA: aplicar exige --token de aprovacao explicita")
    abertura = verificar_lock(caminhos.RAIZ, SESSAO)
    fence = abertura.get("fence")
    if not args.aplicar_fluxo.replace("-", "").isalnum():
        raise SystemExit("PARADA: fluxo_id invalido")
    pasta = (DIR_ESTADO / args.aplicar_fluxo).resolve()
    if pasta.parent != DIR_ESTADO.resolve():
        raise SystemExit("PARADA: fluxo_id fora do diretorio de estado")
    verificar_lock(caminhos.RAIZ, SESSAO, fence)
    estado = fluxo.aplicar_patch_aprovado(pasta, args.token, caminhos.RAIZ)
    teste = subprocess.run(
        [sys.executable, "scripts/verificar.py", "--rapido"],
        cwd=caminhos.RAIZ, capture_output=True, text=True)
    estado["teste_pos_aplicacao"] = {
        "returncode": teste.returncode,
        "stdout_sha256": _sha(teste.stdout),
        "stderr_sha256": _sha(teste.stderr),
        "stdout_final": teste.stdout[-2000:],
        "stderr_final": teste.stderr[-2000:],
    }
    verificar_lock(caminhos.RAIZ, SESSAO, fence)
    evidencia = DIR_EVIDENCIAS / f"aplicacao-{args.aplicar_fluxo}-{_id()}.json"
    gravar_json_atomico(evidencia, _documento_redigido(estado))
    print(f"patch aplicado; evidencia: {evidencia}")
    if teste.returncode:
        print("ATENCAO: verificacao pos-aplicacao falhou; consulte a evidencia.")
        return teste.returncode
    print("verificacao pos-aplicacao: OK")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fluxo multi-provider controlado")
    p.add_argument("--preflight")
    p.add_argument("--operacao", choices=tuple(fluxo.OPERACOES))
    p.add_argument("--tarefa")
    p.add_argument("--timeout", type=int, default=runner_p2.TIMEOUT_PADRAO_S)
    p.add_argument("--validade-h", type=int,
                   default=runner_p2.VALIDADE_PREFLIGHT_H)
    p.add_argument("--aplicar-fluxo")
    p.add_argument("--token")
    args = p.parse_args(argv)
    if args.aplicar_fluxo:
        return aplicar(args)
    if not args.preflight or not args.operacao or not args.tarefa:
        p.error("preparar exige --preflight, --operacao e --tarefa")
    return preparar(args)


if __name__ == "__main__":
    raise SystemExit(main())
