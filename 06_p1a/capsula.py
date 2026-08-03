"""Capsula subscription-only — SSC+ P1-A.2 (experimental, sem autoridade).

Decisao do Soberano (P1-A.2): `NVIDIA_API_KEY` e quaisquer credenciais de
outros projetos podem existir no ambiente global/HKCU do usuario — o SSC+
NAO as remove, altera ou persiste. Em vez disso, o SSC+ inicia dentro de
uma CAPSULA: um ambiente-filho derivado, sem nenhuma credencial de modelo.

Politica estrita DENTRO da capsula (adendo experimental — supera a
leitura manual da P1-A "NVIDIA fora da frota, so sanitiza"; os relatorios
historicos nao sao reescritos):

- qualquer nome com cara de credencial (`*_API_KEY`, `*_AUTH_TOKEN`,
  `*_ACCESS_TOKEN`, `*_API_SECRET`, `*_SECRET_KEY`, `*_BEARER_TOKEN`,
  variantes de caixa/separador e as chaves conhecidas de
  `economia.CHAVES_PAYG_CONHECIDAS`) e PROIBIDO no ambiente da capsula;
- `NVIDIA_API_KEY` injetada DENTRO da capsula bloqueia o preflight
  (familia de provedor tarifavel no escopo de bloqueio de
  `economia.auditar_ambiente`), mesmo sem provider NVIDIA na frota;
- a auditoria economica segue fail-closed: chave, endpoint PAYG, top-up,
  extra-usage, billing ou canal desconhecido = BLOCKED;
- todo subprocesso filho recebe NOVA copia sanitizada (defesa em
  profundidade: capsula -> `ambiente_sanitizado` no sensor);
- valores NUNCA sao registrados — somente nomes de variaveis.

O entry point (`iniciar_em_capsula`) gera o ambiente-filho ANTES de
carregar o SSC+ e inicia o processo com argv em LISTA e shell=False.
"""

import os
import subprocess
import sys

from preflight.economia import _nome_payg

__all__ = ["ViolacaoCapsula", "ambiente_capsula", "verificar_capsula",
           "iniciar_em_capsula", "exigir_capsula_limpa"]

# Raiz do repositorio, deduzida do proprio arquivo. O entry point da
# capsula passa a definir o `cwd` do filho AQUI (P2.3, achado A): ate a
# P2.2 o argumento ficava `None` e o processo do SSC+ herdava o diretorio
# do terminal, que herdava o de quem o abriu. Diretorio de trabalho por
# heranca nao e diretorio de trabalho escolhido — e o que estivesse la.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ViolacaoCapsula(Exception):
    """Credencial de modelo presente dentro da capsula (fail-closed)."""


def verificar_capsula(env: dict) -> list:
    """NOMES das variaveis proibidas presentes no ambiente dado.

    Comparacao case-insensitive e insensivel a separadores (mesma regra
    ampla de sanitizacao da P1-A.1). Nunca retorna valores.
    """
    return sorted(nome for nome in env if _nome_payg(nome))


def ambiente_capsula(env: dict | None = None) -> dict:
    """Copia do ambiente SEM nenhuma credencial de modelo.

    Nunca muta `os.environ` nem o dict recebido: o ambiente global/HKCU
    do usuario permanece intacto — as credenciais apenas nao entram na
    capsula. Apos a filtragem a funcao REAUDITA o resultado (fail-closed):
    se qualquer nome proibido sobreviver, levanta ViolacaoCapsula em vez
    de devolver um ambiente contaminado.
    """
    fonte = dict(os.environ if env is None else env)
    capsula = {k: v for k, v in fonte.items() if not _nome_payg(k)}
    restantes = verificar_capsula(capsula)
    if restantes:
        raise ViolacaoCapsula(
            "credenciais sobreviveram a filtragem da capsula: "
            + ", ".join(restantes))
    return capsula


def exigir_capsula_limpa(env: dict | None = None) -> None:
    """Guarda de entrada de um processo que EXIGE estar na capsula.

    O ponto de entrada do SSC+ chama isto na primeira linha: se qualquer
    credencial de modelo estiver visivel no proprio ambiente, o processo
    aborta ANTES de qualquer sonda ou escrita (politica estrita: chave
    visivel dentro da capsula = bloqueio).
    """
    viol = verificar_capsula(os.environ if env is None else env)
    if viol:
        raise ViolacaoCapsula(
            "processo fora da capsula: credencial(is) de modelo visivel(is): "
            + ", ".join(viol))


def iniciar_em_capsula(argv, timeout: int | None = None,
                       cwd: str | None = None) -> "subprocess.CompletedProcess":
    """Inicia um processo-filho DENTRO da capsula (entry point minimo).

    argv em LISTA, shell=False (nenhum metacaractere e interpretado),
    env = `ambiente_capsula()` fresco, saida capturada em memoria (nunca
    impressa). O ambiente global do pai permanece intocado.
    """
    if isinstance(argv, (str, bytes)):
        raise TypeError("argv deve ser LISTA (shell=False); str proibida")
    return subprocess.run(list(argv), shell=False, env=ambiente_capsula(),
                          capture_output=True, text=True, timeout=timeout,
                          cwd=cwd)


def main() -> int:
    """Entry point CLI: `python 06_p1a/capsula.py <argv do SSC+...>`.

    Gera o ambiente-filho sem credenciais ANTES de carregar o SSC+ e
    repassa o codigo de saida do filho.

    O `cwd` do filho e a RAIZ do repositorio, declarada e nao herdada: o
    SSC+ escreve evidencia por caminho absoluto, mas quem herda o
    diretorio do terminal herda tambem o de qualquer processo que o tenha
    aberto — e era esse diretorio, e nao um escolhido, que descia por dois
    elos ate o CLI do provedor.
    """
    if len(sys.argv) < 2:
        print("uso: python 06_p1a/capsula.py <argv-do-processo-filho...>",
              file=sys.stderr)
        return 2
    proc = iniciar_em_capsula(sys.argv[1:], cwd=RAIZ)
    sys.stdout.write(proc.stdout or "")
    sys.stderr.write(proc.stderr or "")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
