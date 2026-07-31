#!/usr/bin/env python3
"""Contencao real do reviewer e escritor unico — SSC+ P1-A.3.2.

Duas correcoes da revisao P1-A.3.1, compartilhadas pelas ferramentas de
revisao (`revisao_p1a3.py` e `revisao_p1a31.py`), que ate aqui repetiam
o mesmo defeito em copias separadas.

MAJOR #3 — isolamento do kimi. `cwd` descartavel e instrucao textual no
prompt NAO restringem o filesystem: o processo filho herda as permissoes
do usuario e escreve onde quiser; e a lista de "arquivos restantes" so
olha DENTRO do descartavel, de modo que uma escrita fora dele nao
aparece em lugar nenhum. As duas metades do conserto vivem aqui:

- restricao REAL do alcance do CLI (`argv_kimi`), com as flags que o
  proprio CLI oferece — medidas em `kimi --help`, nao presumidas;
- DETECCAO de qualquer mutacao fora do descartavel (`manifesto` +
  `mutacoes`): SHA-256 de cada arquivo da arvore antes e depois da
  chamada. O que a instrucao textual nao impede, o manifesto acusa.

CORRECAO P1-A.3.4 — a primeira metade acima estava INEXECUTAVEL. A
P1-A.3.3 (§4) mediu, invocando o CLI de verdade, que o kimi 0.30.0
recusa `--plan` junto com `-p/--prompt`:

    error: Cannot combine --prompt with --plan.

`--plan` era, portanto, restricao NENHUMA: ele nao restringia a corrida,
ele a IMPEDIA por inteiro — desde a P1-A.3.2 nenhuma chamada headless ao
kimi era possivel por esta ferramenta. `argv_kimi` deixa de emiti-lo.

Por que `kimi --help` nao bastou para pegar isso: `--help` lista as
flags ISOLADAMENTE e as duas existem de fato; a incompatibilidade so
aparece na COMBINACAO, que so a invocacao revela. Medir o cardapio nao e
exercer a interface — e a mesma classe do achado #6.

Plan mode nao tem substituto headless em 0.30.0: `--plan` e eixo de
sessao interativa. O que resta de restricao REAL pelo CLI e o modo de
permissao — o binario declara `Use one of: yolo / manual / auto` —, do
qual `-y/--yolo` e `--auto` sao justamente os dois nao-restritivos. Nao
passa-los e a restricao que sobra, e ela e verificada por teste.

A honestidade do rotulo faz parte do conserto: o kimi NAO tem sandbox de
filesystem como o `--sandbox read-only` do codex. O que se afirma aqui e
o que se mede — restricao parcial pelo CLI mais deteccao integral por
manifesto —, nunca isolamento equivalente.

MAJOR #4 — o lease era verificado apenas ANTES do trabalho. Uma chamada
de provider excede a janela do lease (256 s observados contra 120 s de
lease na P1-A.3.1), de modo que a gravacao podia ocorrer com lease ja
morto ou com titular ja substituido. `verificar_lock` aceita
`fence_esperado` e deve ser chamada IMEDIATAMENTE ANTES de cada
persistencia, nunca so na abertura.
"""

import hashlib
import os

# `locks/` e runtime do escritor unico: o renovador dedicado reescreve o
# lease a cada 30 s por construcao. Incluir esse diretorio no manifesto
# produziria alarme falso em toda corrida. Exclusao DECLARADA — a unica —
# e nao silenciosa: tudo mais da arvore entra, inclusive `.git`.
EXCLUIDOS_DO_MANIFESTO = ("locks",)

# Restricoes REAIS que o CLI do kimi oferece em modo headless (`-p`),
# medidas EXERCENDO o CLI 0.30.0, nao lendo `--help`: NAO existe
# `--sandbox read-only` como no codex.
#   --skills-dir DIR  carrega skills SOMENTE de DIR; apontado para um
#                     diretorio vazio, impede que skills do usuario ou do
#                     projeto sejam carregadas e ajam.
# O que NAO se passa importa tanto quanto: `-y/--yolo` e `--auto`
# auto-aprovariam chamadas de ferramenta sem perguntar. A ausencia deles
# e deliberada e verificada por teste.
FLAGS_DE_AUTO_APROVACAO = ("-y", "--yolo", "--auto")

# Flags que o CLI RECUSA em combinacao com `-p/--prompt` — medido, nao
# presumido (P1-A.3.3 §4; reexercido pelo teste de CLI real da P1-A.3.4).
# Emitir qualquer uma delas aborta a corrida na validacao de argumentos,
# antes da rede: o efeito e impedir a chamada, nunca restringi-la.
FLAGS_INCOMPATIVEIS_COM_PROMPT = ("--plan",)

# Marcador do erro de validacao de argumentos do kimi 0.30.0. O CLI
# distingue duas classes de falha, e so a segunda prova que o argv foi
# ACEITO: `error: <problema de argumento>` acontece ANTES de qualquer
# trabalho; `error: failed to run prompt: ...` so acontece DEPOIS de o
# parser aprovar o comando. O teste de CLI real usa exatamente essa
# fronteira para provar aceitacao sem gastar chamada de modelo.
PREFIXO_ERRO_DE_ARGUMENTO = "error: "
MARCADOR_ARGV_ACEITO = "failed to run prompt"


def manifesto(raiz, excluir=EXCLUIDOS_DO_MANIFESTO) -> dict:
    """Caminho relativo (com `/`) -> SHA-256, de tudo sob `raiz`.

    Arquivo ilegivel entra como `<ilegivel>`: some do manifesto seria
    declara-lo intacto por omissao.
    """
    raiz = os.path.abspath(str(raiz))
    excluidos = {e.replace(os.sep, "/") for e in excluir}
    saida = {}
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = sorted(
            d for d in dirs
            if os.path.relpath(os.path.join(base, d),
                               raiz).replace(os.sep, "/") not in excluidos)
        for nome in sorted(arquivos):
            caminho = os.path.join(base, nome)
            rel = os.path.relpath(caminho, raiz).replace(os.sep, "/")
            try:
                with open(caminho, "rb") as f:
                    saida[rel] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                saida[rel] = "<ilegivel>"
    return saida


def mutacoes(antes: dict, depois: dict) -> list:
    """Caminhos criados, removidos ou alterados entre dois manifestos."""
    mudou = []
    for rel in sorted(set(antes) | set(depois)):
        hash_antes, hash_depois = antes.get(rel), depois.get(rel)
        if hash_antes == hash_depois:
            continue
        if hash_antes is None:
            mudou.append(f"criado: {rel}")
        elif hash_depois is None:
            mudou.append(f"removido: {rel}")
        else:
            mudou.append(f"alterado: {rel}")
    return mudou


def argv_kimi(executavel: str, prompt: str, dir_skills: str) -> list:
    """Comando do kimi com a restricao maxima que o CLI oferece — e que ELE ACEITA.

    Sem `-y`, sem `--yolo` e sem `--auto` — ver FLAGS_DE_AUTO_APROVACAO.
    Sem `--plan` — ver FLAGS_INCOMPATIVEIS_COM_PROMPT: o CLI o recusa em
    combinacao com `-p`, e o comando inteiro morre na validacao.
    """
    return [executavel, "--skills-dir", dir_skills, "-p", prompt]


def enforcement_kimi() -> str:
    """Rotulo do enforcement do kimi — o que se mede, nao o que se quer."""
    return ("sem sandbox de filesystem no CLI (nao ha equivalente ao "
            "`--sandbox read-only` do codex) e sem plan mode em headless "
            "(o CLI recusa `--plan` com `-p`): restricao PARCIAL por "
            "`--skills-dir` vazio, sem `-y/--yolo/--auto`; "
            "cwd descartavel; e DETECCAO INTEGRAL por manifesto SHA-256 "
            "da arvore inteira antes/depois da chamada (mutacao fora do "
            "descartavel e registrada e reprova a corrida)")


def verificar_lock(raiz, sessao: str, fence_esperado: int | None = None,
                   agora: float | None = None) -> dict:
    """Lease vivo + fence do titular do escritor unico.

    MAJOR #4: chamar IMEDIATAMENTE ANTES DE CADA PERSISTENCIA, nao
    apenas na abertura do trabalho. Com `fence_esperado`, exige tambem
    que o titular NAO tenha sido substituido — fence diferente significa
    que outra sessao adquiriu o escritor no intervalo, e esta gravacao
    seria escrita de escritor obsoleto. Fail-closed nos tres casos
    (lease ilegivel, lease morto, fence divergente): PARADA sem gravar.
    """
    import json

    from escritor import EscritorP1

    base = os.path.join(str(raiz), "locks")
    caminho = os.path.join(base, f"{sessao}.lease")
    try:
        with open(caminho, encoding="utf-8") as f:
            lease = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: lease ilegivel/ausente: {exc}")
    if lease.get("sessao") != sessao or \
            EscritorP1.lease_expirado(caminho, agora):
        raise SystemExit("PARADA: lease da sessao operacional morto")
    try:
        with open(os.path.join(base, f"{sessao}.fence"),
                  encoding="ascii") as f:
            fence = int(f.read().strip())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: fence ilegivel/ausente: {exc}")
    if fence_esperado is not None and fence != fence_esperado:
        raise SystemExit(
            f"PARADA: titular do escritor substituido (fence {fence} != "
            f"{fence_esperado}); escritor obsoleto NAO grava")
    return {"sessao": lease["sessao"], "pid_titular": lease["pid"],
            "fence": fence}
