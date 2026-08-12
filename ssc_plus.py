#!/usr/bin/env python3
"""Entrada unica e interativa do SSC Plus para Windows.

Gerencia o escritor/lease dentro deste processo, reutiliza ou gera preflight,
pede confirmacao humana quando tiers venceram e chama o runner na capsula. O
operador nao precisa montar comandos PowerShell nem manter dois terminais.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
from pathlib import Path


RAIZ = Path(__file__).resolve().parent
SESSAO_PADRAO = "ssc-plus-ui"
CAPACIDADES = {
    "1": None,
    "2": "implementacao",
    "3": "arquitetura",
    "4": "contexto-extenso",
    "5": "julgamento-transversal",
}
OPERACOES = {
    "1": "analisar",
    "2": "corrigir",
    "3": "implementar",
    "4": "revisar",
}


def _preparar_imports(sessao: str) -> None:
    for relativo in ("05_p0", "06_p1a", "08_p2", "06_p1a/evidencias"):
        caminho = str(RAIZ / relativo)
        if caminho not in sys.path:
            sys.path.insert(0, caminho)


class LeaseAutomatico:
    """Escritor unico renovado em thread, liberado mesmo sob Ctrl+C."""

    def __init__(self, sessao: str, dir_locks: str | Path | None = None,
                 renovacao_s: float = 30, lease_s: float = 120):
        _preparar_imports(sessao)
        from escritor_repositorio import EscritorRepositorio
        self.escritor = EscritorRepositorio(
            dir_locks or RAIZ / "locks", sessao=sessao, lease_s=lease_s)
        self.renovacao_s = float(renovacao_s)
        self.parar = threading.Event()
        self.erros: list[BaseException] = []
        self.thread: threading.Thread | None = None

    def __enter__(self):
        token = self.escritor.adquirir()

        def renovar():
            while not self.parar.wait(self.renovacao_s):
                try:
                    self.escritor.renovar()
                except BaseException as exc:
                    self.erros.append(exc)
                    self.parar.set()
                    return

        self.thread = threading.Thread(target=renovar,
                                       name="ssc-plus-renovador",
                                       daemon=True)
        self.thread.start()
        return token

    def conferir(self) -> None:
        if self.erros:
            raise RuntimeError(f"renovacao do lease falhou: {self.erros[0]}")
        self.escritor.verificar()

    def __exit__(self, exc_type, exc, traceback):
        self.parar.set()
        if self.thread is not None:
            self.thread.join(timeout=max(1.0, self.renovacao_s + 1))
        self.escritor.liberar()
        return False


def _ambiente(sessao: str) -> dict:
    env = dict(os.environ)
    env["SSC_LOCK_SESSAO"] = sessao
    return env


def _rodar_capsula(script: Path, argumentos: list[str], sessao: str) -> int:
    argv = [sys.executable, str(RAIZ / "06_p1a" / "capsula.py"),
            sys.executable, str(script)] + list(argumentos)
    return subprocess.run(argv, cwd=RAIZ, env=_ambiente(sessao),
                          check=False).returncode


def _tiers_validos() -> bool:
    import leitor_tiers
    from preflight.sombra import declaracao_valida
    declaracoes = leitor_tiers.carregar_tiers()
    return set(declaracoes) == {"codex", "kimi", "google"} and all(
        declaracao_valida(declaracoes[p]) for p in declaracoes)


def _renovar_tiers_interativo(sessao: str) -> None:
    from preflight.frota_real import espec_de
    print("\nAs declaracoes de plano venceram ou estao ausentes.", flush=True)
    for pid in ("codex", "kimi", "google"):
        print(f"  {pid}: {espec_de(pid).plano_esperado}", flush=True)
    resposta = input("Esses tres planos continuam ativos? Digite SIM: ").strip()
    if resposta.upper() != "SIM":
        raise SystemExit("PARADA: tiers nao renovados sem confirmacao do proprietario")
    args = ["--confirmo-proprietario"]
    for pid in ("codex", "kimi", "google"):
        args.extend([f"--{pid}-tier", espec_de(pid).plano_esperado])
    rc = _rodar_capsula(RAIZ / "06_p1a" / "renovar_tiers.py", args, sessao)
    if rc:
        raise SystemExit(f"PARADA: renovacao de tiers falhou (codigo {rc})")


def _preflight_valido_mais_recente() -> Path | None:
    import runner_p2
    candidatos = sorted((RAIZ / "07_p1b" / "evidencias").glob(
        "preflight-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for caminho in candidatos:
        try:
            dados = runner_p2.carregar_preflight(str(caminho))
        except SystemExit:
            continue
        # O lancador verifica autenticidade e idade; nunca interpreta o
        # veredito. Somente `runner_p2` e consumidor declarado da frota.
        return caminho
    return None


def _obter_preflight(sessao: str) -> Path:
    atual = _preflight_valido_mais_recente()
    if atual is not None:
        print(f"preflight reutilizado: {atual.name}", flush=True)
        return atual
    print("gerando preflight atual (somente diagnostico, sem turno de modelo)...",
          flush=True)
    rc = _rodar_capsula(RAIZ / "07_p1b" / "preflight_atual.py", [], sessao)
    if rc:
        raise SystemExit(f"PARADA: preflight falhou (codigo {rc})")
    atual = _preflight_valido_mais_recente()
    if atual is None:
        raise SystemExit("PARADA: nenhum preflight autenticado habilitou a frota")
    return atual


def construir_argv_runner(preflight: Path, tarefa: str, criterio: str,
                          capacidade: str | None, papel: str,
                          sem_contexto: bool = False) -> list[str]:
    argv = ["--preflight", str(preflight), "--tarefa", tarefa,
            "--criterio", criterio, "--papel", papel]
    if capacidade:
        argv.extend(["--capacidade", capacidade])
    if sem_contexto:
        argv.append("--sem-contexto-workspace")
    return argv


def construir_argv_fluxo(preflight: Path, operacao: str,
                         tarefa: str) -> list[str]:
    return ["--preflight", str(preflight), "--operacao", operacao,
            "--tarefa", tarefa]


def _escolher_operacao() -> str:
    print("\nO que voce quer fazer?", flush=True)
    print("  1 - Analisar projeto", flush=True)
    print("  2 - Corrigir problema", flush=True)
    print("  3 - Implementar funcionalidade", flush=True)
    print("  4 - Revisar alteracao", flush=True)
    escolha = input("Escolha [1]: ").strip() or "1"
    if escolha not in OPERACOES:
        raise SystemExit("PARADA: escolha de operacao invalida")
    return OPERACOES[escolha]


def _escolher_capacidade() -> str | None:
    print("\nPreferencia de trabalho:", flush=True)
    print("  1 - automatico", flush=True)
    print("  2 - implementacao (Codex)", flush=True)
    print("  3 - arquitetura/revisao (Claude)", flush=True)
    print("  4 - contexto extenso (Kimi)", flush=True)
    print("  5 - julgamento transversal (Google)", flush=True)
    escolha = input("Escolha [1]: ").strip() or "1"
    if escolha not in CAPACIDADES:
        raise SystemExit("PARADA: escolha de capacidade invalida")
    return CAPACIDADES[escolha]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Abre e opera o SSC Plus sem comandos manuais de lease/preflight.")
    parser.add_argument("--tarefa")
    parser.add_argument("--criterio", default="resposta fundamentada no snapshot")
    parser.add_argument("--capacidade", choices=tuple(
        v for v in CAPACIDADES.values() if v is not None))
    parser.add_argument("--papel", choices=("autor", "revisor", "juiz"),
                        default="autor")
    parser.add_argument("--operacao",
                        choices=("analisar", "corrigir", "implementar", "revisar"),
                        help="usa o fluxo completo multi-provider")
    parser.add_argument("--aplicar-fluxo",
                        help="ID de um fluxo ja testado, revisado e julgado")
    parser.add_argument("--token",
                        help="token de aprovacao explicita do fluxo")
    parser.add_argument("--sem-contexto-workspace", action="store_true")
    parser.add_argument("--sessao", default=SESSAO_PADRAO)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    os.environ["SSC_LOCK_SESSAO"] = args.sessao
    _preparar_imports(args.sessao)
    try:
        with LeaseAutomatico(args.sessao) as fence:
            print(f"SSC Plus aberto | lease automatico fence={fence}", flush=True)
            if args.aplicar_fluxo:
                argumentos = ["--aplicar-fluxo", args.aplicar_fluxo]
                if args.token:
                    argumentos.extend(["--token", args.token])
                return _rodar_capsula(
                    RAIZ / "08_p2" / "executar_fluxo.py",
                    argumentos, args.sessao)
            if not _tiers_validos():
                _renovar_tiers_interativo(args.sessao)
            preflight = _obter_preflight(args.sessao)
            operacao = args.operacao
            if args.tarefa is None and operacao is None:
                operacao = _escolher_operacao()
            tarefa = args.tarefa or input("\nDescreva o pedido: ").strip()
            if not tarefa:
                raise SystemExit("PARADA: tarefa vazia")
            if operacao:
                argumentos = construir_argv_fluxo(
                    preflight, operacao, tarefa)
                return _rodar_capsula(
                    RAIZ / "08_p2" / "executar_fluxo.py",
                    argumentos, args.sessao)
            capacidade = args.capacidade
            if args.tarefa is None and capacidade is None:
                capacidade = _escolher_capacidade()
            argumentos = construir_argv_runner(
                preflight, tarefa, args.criterio, capacidade, args.papel,
                args.sem_contexto_workspace)
            rc = _rodar_capsula(RAIZ / "08_p2" / "runner_p2.py",
                                argumentos, args.sessao)
            return rc
    except KeyboardInterrupt:
        print("\nSSC Plus encerrado pelo operador.")
        return 130
    except Exception as exc:
        # Erros de mecanismo ficam visiveis sem traceback hostil para quem
        # abriu por duplo clique; SystemExit continua preservado pelo Python.
        print(f"PARADA: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
