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

EMENDA DA P2 (ato soberano de 2026-08-03, `08_p2/00_ato-soberano-p2.md`).
Ate aqui as duas metades proibiam consumidor NENHUM, e essa era a forma
certa enquanto ninguem tinha decidido abrir a P2. O Fundador decidiu. A
sentinela NAO foi desligada — foi convertida:

- o consumidor precisa estar DECLARADO NOMINALMENTE em
  `CONSUMIDORES_DECLARADOS`, no fonte desta sentinela. Um consumidor novo
  so passa se alguem o escrever aqui, que e um ato, nunca um acidente —
  e a propriedade que a sentinela existia para garantir (nada de P2 por
  acidente) fica preservada inteira;
- o que e permitido NAO SOME: sai em `portoes_autorizados` e
  `decisoes_autorizadas`, visivel em toda varredura. Achado que vira
  silencio e como guarda que afirma em vez de exercer — o defeito que
  este acervo passou tres missoes corrigindo.

`varrer(raiz, classificador, consumidores=())` devolve o comportamento
ANTERIOR a emenda, e e assim que os controles positivos medem que a
sentinela continua pegando quem nao foi declarado.
"""

import ast
import os

VOCABULARIO_VEREDITO = frozenset(
    {"ELIGIBLE", "SHADOW_ELIGIBLE", "SUPERVISED", "BLOCKED"})

# Consumidores do veredito AUTORIZADOS pelo ato soberano da P2. Caminhos
# relativos a raiz do repositorio. Esta tupla e a superficie inteira da
# autorizacao: qualquer outro arquivo que decida sobre o veredito — ou que
# deixe essa decisao governar execucao — continua sendo achado.
#
# `08_p2/provedor_assinatura.py` NAO entra aqui, e a ausencia e
# deliberada: quem invoca o CLI recebe uma FleetEntry ja aprovada e nunca
# le veredito. Se um dia ele precisar entrar nesta lista, e sinal de que o
# executor passou a decidir — exatamente o que a sentinela deve acusar.
#
# A lista nasce VAZIA e ganha um nome na MESMA ordem que cria o arquivo
# correspondente. Declarar antes deixaria aqui um caminho morto — e o
# teste que percorre a lista ficaria verde sem medir nada, que e o guarda
# vazio contra o qual este acervo tem tres missoes de trilha.
CONSUMIDORES_DECLARADOS = (
    "08_p2/frota_medida.py",
    "08_p2/runner_p2.py",
)

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


# Profundidade maxima ao seguir imports entre modulos do repositorio.
# Nao e economia: e o corte que impede ciclo de import virar recursao
# infinita. Cadeia mais longa que isto conta como NAO RESOLVIDA — e o
# sentinela NEGA, em vez de declarar limpo o que nao conseguiu seguir.
PROFUNDIDADE_MAXIMA_DE_IMPORT = 12


def dobrar_constante(no):
    """Valor textual de uma expressao CONSTANTE, ou None.

    ACHADO N5. O detector so reconhecia `ast.Constant` exato, de modo que
    `"SHADOW" + "_ELIGIBLE"` — concatenacao de duas constantes — nao era
    igual a nenhum termo do vocabulario e passava batido. O revisor
    independente nomeou a concatenacao como uma das tres formas de
    contornar o sentinela DE PROPOSITO.

    Dobra o que o proprio interpretador dobraria: constante textual,
    soma de constantes textuais e f-string sem interpolacao. NAO dobra
    `%`, `.format`, `str.join` nem valor vindo de chamada — e o que nao
    se consegue dobrar entra na lista de NAO RESOLVIDOS de `varrer`, em
    vez de sumir em silencio.
    """
    if isinstance(no, ast.Constant):
        return no.value if isinstance(no.value, str) else None
    if isinstance(no, ast.BinOp) and isinstance(no.op, ast.Add):
        esquerda = dobrar_constante(no.left)
        direita = dobrar_constante(no.right)
        if esquerda is not None and direita is not None:
            return esquerda + direita
        return None
    if isinstance(no, ast.JoinedStr):
        partes = []
        for parte in no.values:
            valor = dobrar_constante(parte)
            if valor is None:
                return None
            partes.append(valor)
        return "".join(partes)
    return None


def tem_literal_do_veredito(no) -> bool:
    """Subarvore contem um literal — DOBRADO — igual a um termo do enum."""
    for f in ast.walk(no):
        valor = dobrar_constante(f)
        if valor is not None and valor in VOCABULARIO_VEREDITO:
            return True
    return False


def _nomes_atribuidos(no) -> set:
    alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
    nomes = set()
    for alvo in alvos:
        for parte in ast.walk(alvo):
            if isinstance(parte, ast.Name):
                nomes.add(parte.id)
            elif isinstance(parte, ast.Attribute):
                nomes.add(parte.attr)
    return nomes


def indice_de_modulos(raiz_repo) -> dict:
    """`preflight.pipeline` -> caminho do arquivo, para os .py da raiz.

    A resolucao e por SUFIXO de caminho: um modulo importado como
    `preflight.pipeline` casa qualquer `.../preflight/pipeline.py` sob a
    raiz. Nao reproduz o `sys.path` do interpretador — reproduzi-lo
    exigiria executar os arquivos, que e justamente o que um sentinela
    estatico nao faz. Sufixo que casa MAIS DE UM arquivo devolve TODOS
    os candidatos, e `_apelidos_de_modulo` os une — escolher um exigiria
    o `sys.path`; unir erra para o lado de reconhecer apelidos demais, o
    que produz achado a mais e nunca ponto cego.
    """
    indice = {}
    for caminho in fontes_py(raiz_repo):
        rel = os.path.relpath(caminho, raiz_repo).replace(os.sep, "/")
        partes = rel[:-3].split("/")
        for corte in range(len(partes)):
            dotted = ".".join(partes[corte:])
            indice.setdefault(dotted, [])
            if caminho not in indice[dotted]:
                indice[dotted].append(caminho)
    return {k: tuple(v) for k, v in indice.items()}


def _apelidos_de_modulo(caminhos, indice, profundidade, visitados):
    """Apelidos exportados por um modulo, seguindo os imports dele.

    Quando o sufixo casa MAIS DE UM arquivo (`kernel` existe em
    `ssc_p0/` e numa fixture), a saida e a UNIAO dos candidatos, nunca a
    escolha de um. Escolher exigiria reproduzir o `sys.path` do
    interpretador, que um sentinela estatico nao faz; a uniao erra para
    o lado de reconhecer apelidos DEMAIS, que produz achado a mais e
    nunca ponto cego.
    """
    apelidos, nao_resolvidos = set(), []
    for caminho in caminhos:
        if caminho in visitados:
            continue                      # ciclo de import ja percorrido
        if profundidade <= 0:
            nao_resolvidos.append(
                f"{caminho}: cadeia de import acima do limite")
            continue
        try:
            with open(caminho, encoding="utf-8") as f:
                arvore = ast.parse(f.read(), filename=caminho)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            nao_resolvidos.append(f"{caminho}: {type(exc).__name__}")
            continue
        de_la, faltou = apelidos_do_veredito(
            arvore, indice, profundidade - 1, visitados | {caminho})
        apelidos |= de_la
        nao_resolvidos.extend(faltou)
    return apelidos, nao_resolvidos


def apelidos_do_veredito(arvore, indice=None, profundidade=None,
                         visitados=frozenset()):
    """Nomes ligados a um termo do vocabulario — no arquivo E por import.

    Devolve `(apelidos, nao_resolvidos)`.

    Tres formas de contorno, todas nomeadas pelo revisor independente, e
    todas fechadas aqui:

    1. ALIAS local — `alvo = "SHADOW_ELIGIBLE"` ... `if r == alvo:`. Ja
       estava coberto;
    2. CONSTANTE IMPORTADA — `from preflight.pipeline import RESULTADOS`.
       O nome nao e atribuido no arquivo, e o detector antigo nao o via.
       Agora o modulo de origem e localizado sob a raiz, parseado, e os
       seus proprios apelidos entram. `import X` tambem conta, porque a
       referencia por ATRIBUTO (`X.RESULTADOS`) casa pelo nome do
       atributo;
    3. PROPAGACAO POR BOOLEANO — `apto = (r == "SHADOW_ELIGIBLE")` ...
       `if apto:`. O nome nao recebe o literal, recebe a DECISAO. O laco
       de ponto fixo abaixo o alcanca, e alcanca tambem a cadeia
       (`ok = apto`), que uma passada unica deixaria escapar.

    NEGA QUANDO NAO CONSEGUE RESOLVER: import de modulo do repositorio
    que nao parseia, `import *` de modulo irresolvivel, modulo ambiguo e
    cadeia acima da profundidade maxima entram em `nao_resolvidos`, e
    `varrer` os reporta como achado. Declarar limpo o que nao se
    conseguiu seguir seria o defeito, nao a economia.
    """
    profundidade = (PROFUNDIDADE_MAXIMA_DE_IMPORT if profundidade is None
                    else profundidade)
    apelidos, nao_resolvidos = set(), []

    # (2) constantes vindas de outro modulo do repositorio.
    if indice is not None:
        for no in ast.walk(arvore):
            if isinstance(no, ast.ImportFrom):
                modulo = no.module or ""
                if modulo not in indice:
                    continue           # stdlib ou pacote externo: fora
                de_la, faltou = _apelidos_de_modulo(
                    indice[modulo], indice, profundidade, visitados)
                nao_resolvidos.extend(faltou)
                for alias in no.names:
                    if alias.name == "*":
                        apelidos |= de_la
                    elif alias.name in de_la:
                        apelidos.add(alias.asname or alias.name)
            elif isinstance(no, ast.Import):
                for alias in no.names:
                    if alias.name not in indice:
                        continue
                    de_la, faltou = _apelidos_de_modulo(
                        indice[alias.name], indice, profundidade, visitados)
                    nao_resolvidos.extend(faltou)
                    apelidos |= de_la

    # (1) e (3): ponto fixo sobre as atribuicoes do proprio arquivo.
    atribuicoes = [no for no in ast.walk(arvore)
                   if isinstance(no, (ast.Assign, ast.AnnAssign))
                   and no.value is not None]
    while True:
        antes = len(apelidos)
        for no in atribuicoes:
            if tem_literal_do_veredito(no.value) \
                    or referencia_veredito(no.value, apelidos):
                apelidos |= _nomes_atribuidos(no)
        if len(apelidos) == antes:
            return apelidos, nao_resolvidos


def referencia_veredito(no, apelidos) -> bool:
    """Subarvore toca o veredito: literal exato, nome ou atributo ligado."""
    for f in ast.walk(no):
        valor = dobrar_constante(f)
        if valor is not None and valor in VOCABULARIO_VEREDITO:
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


def varrer(raiz_repo, classificador, consumidores=None) -> dict:
    """A varredura inteira sobre uma raiz — a operacao e o controle.

    Devolve `{"ilegiveis": [...], "portoes": [...], "decisoes_fora":
    [...], "nao_resolvidos": [...], "portoes_autorizados": [...],
    "decisoes_autorizadas": [...]}`, cada item na forma
    `caminho-relativo:linha`.

    METADE (A), o que mudou na P1-A.3.7 (MAJOR #6): a raiz de (A) e a
    RAIZ DO REPOSITORIO, nao mais so o diretorio da P1-A. Enquanto ela
    era `06_p1a`, um consumidor escrito em `07_p1b` ficava invisivel —
    achado 13 da varredura de guardas, confirmado pelo revisor.

    EMENDA DA P2: `consumidores` sao caminhos RELATIVOS a raiz, e o que
    eles produzem migra para os campos `*_autorizados` — nunca some.
    `None` usa `CONSUMIDORES_DECLARADOS`; `()` devolve o comportamento
    anterior a emenda, que e como os controles positivos a medem.
    """
    raiz_repo = os.path.abspath(str(raiz_repo))
    classificador = os.path.realpath(str(classificador))
    declarados = (CONSUMIDORES_DECLARADOS if consumidores is None
                  else consumidores)
    autorizados = {os.path.realpath(os.path.join(raiz_repo, str(c)))
                   for c in declarados}
    indice = indice_de_modulos(raiz_repo)
    ilegiveis, decisoes_fora, portoes, nao_resolvidos = [], [], [], []
    portoes_autorizados, decisoes_autorizadas = [], []
    for caminho in fontes_py(raiz_repo):
        try:
            with open(caminho, encoding="utf-8") as f:
                arvore = ast.parse(f.read(), filename=caminho)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            # Fail-closed: fonte que o detector nao consegue ler nao pode
            # ser declarado limpo por omissao.
            ilegiveis.append(f"{caminho}: {type(exc).__name__}")
            continue
        rel = os.path.relpath(caminho, raiz_repo)
        apelidos, faltou = apelidos_do_veredito(arvore, indice)
        # NEGA quando nao consegue resolver (achado N5): import que o
        # sentinela nao conseguiu seguir e ponto cego, e ponto cego nao
        # pode sair como arquivo limpo.
        nao_resolvidos.extend(f"{rel}: {m}" for m in faltou)
        # Consumidor DECLARADO pelo ato soberano: o que ele produz muda de
        # campo, nao de existencia. Um arquivo autorizado que ilegivel
        # continua ilegivel — a autorizacao nunca cobre o fail-closed.
        autorizado = os.path.realpath(caminho) in autorizados
        destino_portoes = portoes_autorizados if autorizado else portoes
        destino_decisoes = (decisoes_autorizadas if autorizado
                            else decisoes_fora)
        for linha, primitiva in portoes_de_execucao(arvore, apelidos):
            destino_portoes.append(f"{rel}:{linha} -> {primitiva}()")
        if os.path.realpath(caminho) != classificador:
            for linha in decisoes_sobre_veredito(arvore, apelidos):
                destino_decisoes.append(f"{rel}:{linha}")
    return {"ilegiveis": ilegiveis, "portoes": portoes,
            "decisoes_fora": decisoes_fora,
            "nao_resolvidos": sorted(set(nao_resolvidos)),
            "portoes_autorizados": portoes_autorizados,
            "decisoes_autorizadas": decisoes_autorizadas}
