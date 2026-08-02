"""Sentinela anti-P2 — a maquinaria, extraida para poder ser exercida.

Este modulo nao contem testes: e a maquinaria que `test_emendas_p1a3.py`
usava embutida no proprio arquivo, e que agora vive separada por uma
razao medida. Enquanto ela era codigo dentro do teste, a UNICA forma de
exerce-la era varrer o repositorio real e esperar que estivesse limpo —
isto e, o guarda nunca era exercido contra um violador. Ele so podia
falhar em producao, e nunca num controle positivo.

Extraida, a varredura vira uma funcao que recebe a RAIZ. O teste do
acervo a chama com a raiz real (o caso que a operacao percorre) e os
testes novos a chamam com arvores sinteticas que CONTEM o violador — e
e assim que se mede que ela pega, em vez de supor.

DUAS METADES, ambas medidas por AST (achado #6 da 99_decisao-p1a31.md):

(A) fora do CLASSIFICADOR, nenhum arquivo DO REPOSITORIO decide sobre o
    veredito. Ate a P1-A.3.6 esta metade cobria somente `06_p1a/`, e o
    achado 13 da varredura mediu a consequencia: `07_p1b` decidia sobre
    o veredito fora do classificador e NAO era visto. MAJOR #6 do
    revisor independente: *"a metade (A) segue sem cobrir `07_p1b`"*.
    Agora a raiz da metade (A) e a mesma da metade (B): o repositorio.

(B) em NENHUM arquivo do repositorio uma decisao sobre o veredito
    governa execucao — nem dentro do proprio classificador.

Produzir a classificacao e trabalho legitimo do classificador; decidir
sobre ela fora dele e o primeiro passo de um consumidor.
"""

import ast
import os

VOCABULARIO_VEREDITO = frozenset(
    {"ELIGIBLE", "SHADOW_ELIGIBLE", "SUPERVISED", "BLOCKED"})

# Primitivas que EXECUTAM algo: subprocesso, interpretacao dinamica e as
# juntas de sonda do proprio pacote. Um consumidor nao precisa chamar
# `subprocess.run` — basta acionar a sonda do adaptador.
PRIMITIVAS_EXECUCAO = frozenset({
    "run", "Popen", "call", "check_call", "check_output",
    "system", "popen", "startfile",
    "execv", "execve", "execl", "execlp", "execvp",
    "spawnv", "spawnve", "spawnl",
    "eval", "exec", "run_path", "run_module",
    "sonda", "detectar_versao", "consultar_login", "descobrir_modelos",
    "executar_preflight", "sensor_subprocess", "iniciar_em_capsula",
})

DIRS_IGNORADOS = ("__pycache__", "tests", ".git", "node_modules", ".venv")


def fontes_py(raiz):
    """Arquivos .py sob `raiz`, fora de runtime, testes e do .git."""
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = sorted(d for d in dirs if d not in DIRS_IGNORADOS)
        for nome in sorted(arquivos):
            if nome.endswith(".py"):
                yield os.path.join(base, nome)


def tem_literal_do_veredito(no) -> bool:
    """Subarvore contem um literal EXATAMENTE igual a um termo do enum."""
    return any(isinstance(f, ast.Constant) and isinstance(f.value, str)
               and f.value in VOCABULARIO_VEREDITO
               for f in ast.walk(no))


def apelidos_do_veredito(arvore) -> set:
    """Nomes ligados, NO PROPRIO ARQUIVO, a um termo do vocabulario.

    Cobre `resultado = "SHADOW_ELIGIBLE"` e tambem
    `RESULTADOS = ("ELIGIBLE", ...)`. Sem isto, a comparacao indireta
    (`alvo = "SHADOW_ELIGIBLE"` ... `if r == alvo:`) escaparia do
    detector — o consumidor so precisaria de uma variavel.
    """
    apelidos = set()
    for no in ast.walk(arvore):
        if not isinstance(no, (ast.Assign, ast.AnnAssign)):
            continue
        if no.value is None or not tem_literal_do_veredito(no.value):
            continue
        alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
        for alvo in alvos:
            for parte in ast.walk(alvo):
                if isinstance(parte, ast.Name):
                    apelidos.add(parte.id)
                elif isinstance(parte, ast.Attribute):
                    apelidos.add(parte.attr)
    return apelidos


def referencia_veredito(no, apelidos) -> bool:
    """Subarvore toca o veredito: literal exato, nome ou atributo ligado."""
    for f in ast.walk(no):
        if isinstance(f, ast.Constant) and isinstance(f.value, str) \
                and f.value in VOCABULARIO_VEREDITO:
            return True
        if isinstance(f, ast.Name) and f.id in apelidos:
            return True
        if isinstance(f, ast.Attribute) and f.attr in apelidos:
            return True
    return False


def decisoes_sobre_veredito(arvore, apelidos) -> list:
    """Linhas onde o fonte DECIDE sobre o veredito.

    Decidir e comparar (`==`, `!=`, `in`, `not in`) ou casar um `case`.
    Produzir o veredito (atribuir, devolver, declarar no enum) nao e
    decidir — e o trabalho legitimo do classificador.
    """
    linhas = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Compare) \
                and referencia_veredito(no, apelidos):
            linhas.append(no.lineno)
        elif isinstance(no, ast.match_case) \
                and referencia_veredito(no.pattern, apelidos):
            linhas.append(no.pattern.lineno)
    return sorted(set(linhas))


def execucoes_em(no) -> list:
    """Chamadas a primitiva de execucao dentro da subarvore."""
    achadas = []
    for f in ast.walk(no):
        if not isinstance(f, ast.Call):
            continue
        alvo = f.func
        nome = alvo.attr if isinstance(alvo, ast.Attribute) else (
            alvo.id if isinstance(alvo, ast.Name) else None)
        if nome in PRIMITIVAS_EXECUCAO:
            achadas.append((f.lineno, nome))
    return achadas


def portoes_de_execucao(arvore, apelidos) -> list:
    """Decisoes sobre o veredito que GOVERNAM execucao.

    Para cada ramo cujo TESTE toca o veredito, procura primitiva de
    execucao no corpo — e no `else`, igualmente governado pela mesma
    decisao. Cobre `if`, `while`, expressao condicional, `match`/`case`
    e o `if` de compreensao.
    """
    portoes = []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.If, ast.While, ast.IfExp)):
            if not referencia_veredito(no.test, apelidos):
                continue
            ramos = [no.body, no.orelse]
        elif isinstance(no, ast.match_case):
            if not referencia_veredito(no.pattern, apelidos):
                continue
            ramos = [no.body]
        elif isinstance(no, (ast.ListComp, ast.SetComp, ast.GeneratorExp,
                             ast.DictComp)):
            if not any(referencia_veredito(condicao, apelidos)
                       for gerador in no.generators
                       for condicao in gerador.ifs):
                continue
            ramos = [[no.key, no.value]] if isinstance(no, ast.DictComp) \
                else [no.elt]
        else:
            continue
        for ramo in ramos:
            for parte in (ramo if isinstance(ramo, list) else [ramo]):
                portoes.extend(execucoes_em(parte))
    return sorted(set(portoes))


def varrer(raiz_repo, classificador) -> dict:
    """A varredura inteira sobre uma raiz — a operacao e o controle.

    Devolve `{"ilegiveis": [...], "portoes": [...], "decisoes_fora":
    [...]}`, cada item na forma `caminho-relativo:linha`.

    METADE (A), o que mudou na P1-A.3.7 (MAJOR #6): a raiz de (A) e a
    RAIZ DO REPOSITORIO, nao mais so o diretorio da P1-A. Enquanto ela
    era `06_p1a`, um consumidor escrito em `07_p1b` ficava invisivel —
    achado 13 da varredura de guardas, confirmado pelo revisor.
    """
    raiz_repo = os.path.abspath(str(raiz_repo))
    classificador = os.path.realpath(str(classificador))
    ilegiveis, decisoes_fora, portoes = [], [], []
    for caminho in fontes_py(raiz_repo):
        try:
            with open(caminho, encoding="utf-8") as f:
                arvore = ast.parse(f.read(), filename=caminho)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            # Fail-closed: fonte que o detector nao consegue ler nao pode
            # ser declarado limpo por omissao.
            ilegiveis.append(f"{caminho}: {type(exc).__name__}")
            continue
        apelidos = apelidos_do_veredito(arvore)
        rel = os.path.relpath(caminho, raiz_repo)
        for linha, primitiva in portoes_de_execucao(arvore, apelidos):
            portoes.append(f"{rel}:{linha} -> {primitiva}()")
        if os.path.realpath(caminho) != classificador:
            for linha in decisoes_sobre_veredito(arvore, apelidos):
                decisoes_fora.append(f"{rel}:{linha}")
    return {"ilegiveis": ilegiveis, "portoes": portoes,
            "decisoes_fora": decisoes_fora}
