"""Cobertura de linha da bateria P0 medida com ferramenta STDLIB (trace).

A missao proibe dependencias externas; `trace` (stdlib) fornece cobertura
de linha real, sem percentual inventado. Roda a bateria unittest inteira
sob rastreamento e resume a cobertura dos modulos `ssc_p0`.

Saida: saidas/labs/cobertura/ (pasta ignorada do laboratorio) + resumo no
stdout. Uso: python 05_p0/cenarios/cobertura.py
"""

import os
import sys
import trace
import unittest

_DIR = os.path.dirname(os.path.abspath(__file__))
_DIR_P0 = os.path.dirname(_DIR)
sys.path.insert(0, _DIR_P0)
sys.path.insert(0, os.path.join(_DIR_P0, "tests"))

DIR_COBERTURA = os.path.join(_DIR_P0, "saidas", "labs", "cobertura")


def _rodar_bateria() -> bool:
    suite = unittest.TestLoader().discover(os.path.join(_DIR_P0, "tests"))
    resultado = unittest.TextTestRunner(verbosity=0).run(suite)
    return resultado.wasSuccessful()


def main() -> None:
    os.makedirs(DIR_COBERTURA, exist_ok=True)
    trac = trace.Trace(count=1, trace=0, countfuncs=0, countcallers=0,
                       ignoredirs=[sys.prefix, sys.exec_prefix])
    ok = trac.runfunc(_rodar_bateria)
    resultados = trac.results()
    resultados.write_results(show_missing=True, summary=True,
                             coverdir=DIR_COBERTURA)
    # Resumo por modulo ssc_p0: linhas executaveis x executadas.
    contagens = resultados.counts  # {(arquivo, linha): hits}
    por_modulo = {}
    for (arquivo, _linha), hits in contagens.items():
        if f"{os.sep}ssc_p0{os.sep}" not in arquivo:
            continue
        modulo = os.path.basename(arquivo)
        executadas, total = por_modulo.get(modulo, (0, 0))
        por_modulo[modulo] = (executadas + (1 if hits else 0), total + 1)
    print("\n=== Cobertura de linha (stdlib trace) — ssc_p0 ===")
    soma_exec = soma_total = 0
    for modulo in sorted(por_modulo):
        executadas, total = por_modulo[modulo]
        soma_exec += executadas
        soma_total += total
        pct = 100.0 * executadas / total if total else 0.0
        print(f"  {modulo:<16} {executadas:>4}/{total:<4} linhas  {pct:5.1f}%")
    pct_total = 100.0 * soma_exec / soma_total if soma_total else 0.0
    print(f"  {'TOTAL':<16} {soma_exec:>4}/{soma_total:<4} linhas  "
          f"{pct_total:5.1f}%")
    print(f"  bateria: {'OK' if ok else 'COM FALHAS'}; "
          f"detalhes (linhas perdidas) em {DIR_COBERTURA}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
