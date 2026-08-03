"""Medidor da tese — a proxy que substitui a contagem de token que nao ha.

A P2 existe para provar UMA coisa: que despachar para a assinatura poupa
token de outro canal. Ate aqui isso era **inferencia declarada**
(`99_registro-p2.md` §6.4), e nenhum dos dois CLIs reporta contagem de
token — `custo.tokens_reportados` sai `None`, por honestidade, em toda
invocacao (`provedor_assinatura.py:256`).

Sem contador, resta uma PROXY. Este modulo a define, a implementa e —
principalmente — carrega junto o que ela NAO captura. A regra que este
acervo pagou caro para aprender e que **proxy declarada vale; proxy
silenciosa e a familia do MAJOR #3**: o artefato que AFIRMA a propriedade
em vez de exerce-la. Por isso `NAO_CAPTURA` nao e paragrafo de README que
alguem esquece de ler: ele viaja DENTRO de toda saida de `comparar`, e ha
guarda que mede membro a membro se a lista prende.

## A proxy: CARGA DE FRONTEIRA

Conta-se o que ATRAVESSA a fronteira de um canal, nos dois sentidos, em
duas unidades declaradas (`bytes_utf8` e `caracteres`). Duas, e nao uma,
porque escolher uma sozinha esconderia a escolha: acento custa 1 caractere
e 2 bytes, e foi precisamente uma confusao de bytes-versus-texto que
produziu o achado 4.3 desta mesma fase.

Tres numeros, nunca dois — e o terceiro e o que quase todo argumento de
economia omite:

| numero | o que e |
|---|---|
| `assinatura` | tudo que atravessou a fronteira do CLI de assinatura, **somando TODAS as tentativas** — o fallback custa duas vezes, e quem conta so a que deu certo esta contando o desfecho, nao o gasto |
| `alternativo` | o que o outro canal teria ingerido e emitido para a MESMA tarefa, feita por ele |
| `residual_do_despachante` | o que o outro canal **continua pagando** mesmo despachando: ele redige o prompt e le a resposta de volta |

    poupanca = alternativo - residual_do_despachante

O residual e o coracao da medicao. Tratar despacho como gratuito faz
qualquer tese de economia fechar por construcao — e seria exatamente o
guarda que afirma em vez de exercer. Se o residual for quase igual ao
`alternativo`, a proxy responde **nao houve economia na fronteira**, e
essa resposta e um resultado, nao uma falha do instrumento.

## De onde saem os numeros do lado da assinatura

Da CADEIA VERIFICADA, nunca da memoria do processo que executou: o
medidor le por `EvidencePlane`, que so projeta sobre o EventLog
verificado mais o CAS (`evidence.py:1-6`). E a mesma disciplina que o
runner ja aplica ao placar. Um medidor que lesse do proprio processo
mediria o que ele acha que enviou, e nao o que ficou gravado.
"""

import os

import caminhos  # noqa: F401  (insere 05_p0/06_p1a/08_p2 no sys.path)

from ssc_p0.evidence import EvidencePlane

PROXY = "carga-de-fronteira"
UNIDADES = ("bytes_utf8", "caracteres")

# Teto de `workunit.intencao` no contrato da P0 (`contratos.py:201`). O
# runner envia a tarefa INTEGRAL ao CLI (`entrada=tarefa.encode(...)`) e
# registra na WorkUnit apenas `tarefa[:4000]` (`runner_p2.py:189`). Acima
# desse tamanho a cadeia guarda menos do que de fato atravessou, e uma
# medicao lida so da cadeia SUB-CONTA a entrada. Medido no contrato, nao
# suposto pelo nome do campo.
TETO_INTENCAO_CHARS = 4000

# O QUE A PROXY NAO CAPTURA. Cada item existe por um fato deste acervo ou
# por uma propriedade conhecida dos canais, nunca por precaucao generica.
# Viaja embutido em toda saida de `comparar`.
NAO_CAPTURA = (
    {"codigo": "bytes-nao-sao-tokens",
     "porque": "tokenizador nao e linear em byte, e os dois canais nem "
               "usam o mesmo. Razao de bytes NAO e razao de tokens; serve "
               "para ordem de grandeza, jamais para faturamento."},
    {"codigo": "contexto-do-canal-nao-atravessa-a-fronteira",
     "porque": "prompt de sistema, historico de conversa e definicao de "
               "ferramenta sao reenviados a cada turno do canal "
               "alternativo, e o CLI de assinatura injeta os seus. Nenhum "
               "dos dois aparece na fronteira medida."},
    {"codigo": "raciocinio-nao-emitido",
     "porque": "token de raciocinio e cobrado e nunca cruza a fronteira. "
               "E justamente onde a economia deveria estar, e e o que "
               "esta proxy nao alcanca."},
    {"codigo": "cache-nao-e-visto",
     "porque": "cache de prompt muda o preco por token sem mudar um byte. "
               "Dois numeros iguais nesta proxy podem custar diferente."},
    {"codigo": "turnos-internos-so-contam-se-declarados",
     "porque": "o canal alternativo fazendo a tarefa sozinho abre N "
               "leituras e chamadas de ferramenta. So entra o que o "
               "razonete declarar: leitura nao declarada e leitura nao "
               "contada, e o vies favorece 'nao houve economia'."},
    {"codigo": "qualidade-nao-e-medida",
     "porque": "resposta mais barata e errada nao e economia. A proxy nao "
               "olha o conteudo, e a P2 nunca acionou juiz-llm "
               "(`99_registro-p2.md` §6.1)."},
    {"codigo": "entrada-da-cadeia-e-truncada-em-4000-chars",
     "porque": "`workunit.intencao` tem teto de contrato e o CLI recebe a "
               "tarefa integral. Acima do teto a leitura da cadeia "
               "sub-conta o que atravessou."},
    {"codigo": "uma-corrida-nao-e-tendencia",
     "porque": "n=1 mede a corrida que ocorreu. Nada aqui autoriza "
               "extrapolar para a proxima tarefa, outro modelo ou outra "
               "estacao."},
    {"codigo": "verbosidade-do-canal-entra-na-poupanca",
     "porque": "a poupanca decompoe, por identidade, em turno interno MAIS "
               "a diferenca de tamanho entre as duas respostas — e o "
               "segundo termo nao vem de despachar, vem de um canal "
               "responder mais curto que o outro. Medido na P2.2 em tres "
               "corridas: 837, 811 e 890 bytes, praticamente constante e "
               "independente da classe da tarefa. Na tarefa SEM turno "
               "interno ele foi a poupanca INTEIRA (890 de 890), e a razao "
               "caiu de 2,766 para 1,000 ao medir com a mesma resposta nos "
               "dois lados. Quem cita a poupanca sem separar os dois "
               "termos esta creditando ao despacho a brevidade do outro."},
)

PAPEIS = ("entrada", "saida", "interno")


class MedicaoAmbigua(Exception):
    """Mais de uma WorkUnit no laboratorio e nenhuma escolhida.

    Fail-closed de proposito: escolher a primeira produziria um numero
    plausivel sobre a tarefa errada, que e pior que numero nenhum.
    """


def tamanhos(conteudo) -> dict:
    """Texto ou bytes -> as duas unidades declaradas.

    `bytes` entra pelo tamanho cru (e o que o CAS guardou) e o numero de
    caracteres sai da decodificacao utf-8 tolerante — aqui `replace` nao
    perde medicao, so nao promete fidelidade de conteudo.
    """
    if isinstance(conteudo, (bytes, bytearray)):
        brutos = bytes(conteudo)
        texto = brutos.decode("utf-8", errors="replace")
    else:
        texto = str(conteudo or "")
        brutos = texto.encode("utf-8")
    return {"bytes_utf8": len(brutos), "caracteres": len(texto)}


def _somar(*parcelas) -> dict:
    return {u: sum(int(p.get(u, 0)) for p in parcelas) for u in UNIDADES}


def _escalar(parcela: dict, fator: int) -> dict:
    return {u: int(parcela.get(u, 0)) * int(fator) for u in UNIDADES}


def item_de_texto(texto, papel: str, rotulo: str,
                  procedencia: str = "medido-processo") -> dict:
    """Uma linha do razonete do canal alternativo, medida de um texto."""
    if papel not in PAPEIS:
        raise ValueError(f"papel invalido: {papel!r}; use {PAPEIS}")
    return {"rotulo": rotulo, "papel": papel, "procedencia": procedencia,
            **tamanhos(texto)}


def item_de_arquivo(caminho: str, papel: str, rotulo: str | None = None,
                    raiz: str | None = None) -> dict:
    """Uma linha do razonete medida de um ARQUIVO REAL do disco.

    Procedencia `medido-arquivo`: o numero sai do arquivo que o canal
    alternativo teve mesmo de ler, nao de uma estimativa de quanto ele
    talvez tenha lido. O rotulo e o caminho relativo a raiz do
    repositorio, para que o razonete continue legivel noutra estacao.
    """
    with open(caminho, "rb") as f:
        brutos = f.read()
    base = raiz or caminhos.RAIZ
    try:
        nome = os.path.relpath(caminho, base).replace("\\", "/")
    except ValueError:                      # unidades diferentes no Windows
        nome = os.path.basename(caminho)
    return {"rotulo": rotulo or nome, "papel": papel,
            "procedencia": "medido-arquivo", **tamanhos(brutos)}


def medir_assinatura(raiz_lab: str, sessao_id: str,
                     work_unit_id: str | None = None,
                     entrada_real=None) -> dict:
    """A carga de fronteira do lado da assinatura, lida da cadeia.

    `entrada_real` e OPCIONAL e existe para uma razao medida: a cadeia
    guarda `intencao` truncada em `TETO_INTENCAO_CHARS`, e o CLI recebeu a
    tarefa integral. Passando o texto que de fato foi despachado, a funcao
    reporta a divergencia em vez de esconde-la; sem ele, a leitura e a da
    cadeia e o campo `truncamento.possivel` avisa quando a intencao bateu
    exatamente no teto.

    A entrada e contada UMA VEZ POR TENTATIVA: num fallback o mesmo prompt
    atravessa a fronteira do codex e a do kimi. Contar uma so vez seria
    medir a rota que deu certo, nao o que foi gasto.
    """
    plano = EvidencePlane(raiz_lab, sessao_id)
    projecao = plano.projetar()

    unidades = projecao["work_units"]
    if work_unit_id is None:
        if len(unidades) != 1:
            raise MedicaoAmbigua(
                f"{len(unidades)} WorkUnits no laboratorio; declare "
                "work_unit_id — escolher sozinho mediria a tarefa errada")
        work_unit_id = next(iter(unidades))
    if work_unit_id not in unidades:
        raise MedicaoAmbigua(f"WorkUnit {work_unit_id!r} nao esta na cadeia")

    intencao = unidades[work_unit_id].get("intencao") or ""
    da_cadeia = tamanhos(intencao)
    if entrada_real is None:
        entrada_unitaria = da_cadeia
        procedencia_entrada = "medido-cadeia"
        divergencia = None
    else:
        entrada_unitaria = tamanhos(entrada_real)
        procedencia_entrada = "medido-processo"
        divergencia = {u: entrada_unitaria[u] - da_cadeia[u] for u in UNIDADES}

    tentativas = []
    for att in projecao["attempts"]:
        if att.get("work_unit_id") != work_unit_id:
            continue
        if att.get("resultado") is None:
            continue                        # criado e nao concluido
        ref = (att.get("captura") or {}).get("saida_estruturada_ref")
        saida = tamanhos(plano.cas.ler(ref)) if ref else tamanhos(b"")
        resolvido = att.get("executor_resolvido") or {}
        tentativas.append({
            "attempt_id": att.get("attempt_id"),
            "executor": f"{resolvido.get('provedor')}/"
                        f"{resolvido.get('modelo')}",
            "resultado": att.get("resultado"),
            "final": bool((att.get("captura") or {}).get("saida_final_ref")),
            "entrada": dict(entrada_unitaria),
            "saida": saida,
        })

    saida_total = _somar(*[t["saida"] for t in tentativas]) if tentativas \
        else _somar()
    entrada_total = _escalar(entrada_unitaria, len(tentativas))

    # O que o DESPACHANTE le de volta: a resposta final. Nao existindo
    # nenhuma final (todas as tentativas falharam), ele ainda le a ultima
    # saida — o motivo da parada tambem ocupa fronteira.
    finais = [t for t in tentativas if t["final"]]
    lida_de_volta = (finais[-1]["saida"] if finais
                     else (tentativas[-1]["saida"] if tentativas
                           else _somar()))

    return {
        "lado": "assinatura",
        "proxy": PROXY,
        "sessao_id": sessao_id,
        "work_unit_id": work_unit_id,
        "fonte": "cadeia-verificada (EventLog + CAS via EvidencePlane)",
        "procedencia_entrada": procedencia_entrada,
        "entrada_unitaria": dict(entrada_unitaria),
        "truncamento": {
            "teto_chars": TETO_INTENCAO_CHARS,
            "possivel": da_cadeia["caracteres"] >= TETO_INTENCAO_CHARS,
            "divergencia_medida": divergencia,
        },
        "tentativas": tentativas,
        "n_tentativas": len(tentativas),
        "total": _somar(entrada_total, saida_total),
        "total_entrada": entrada_total,
        "total_saida": saida_total,
        # O residual sai da MESMA cadeia: prompt redigido uma vez, resposta
        # lida uma vez. As tentativas repetidas ficam com a assinatura.
        "residual_do_despachante": _somar(entrada_unitaria, lida_de_volta),
    }


def medir_alternativo(itens) -> dict:
    """O razonete do outro canal para a MESMA tarefa, feita por ele.

    Nao ha como ler isto de cadeia nenhuma: o canal alternativo nao grava
    EventLog. Entao cada linha declara `procedencia`, e a funcao avisa —
    por escrito, na saida — quando o razonete tem forma de razonete
    incompleto:

    - **sem turno interno declarado**: a economia inteira que a tese
      afirma mora nos turnos internos (leitura de arquivo, chamada de
      ferramenta). O aviso NAO distingue dois casos que a P2.2 mediu como
      diferentes: razonete que OMITIU o turno — e ai subconta o canal
      alternativo — e tarefa que nao TEM turno interno, e ai a ausencia e
      o fato da tarefa, a poupanca estrutural e zero, e o que sobra na
      conta e so a diferenca de verbosidade entre as duas respostas. Quem
      le o aviso tem de dizer qual dos dois e; a P2.1 escrevia aqui que
      razonete sem turno interno "nunca prova ausencia de economia", e a
      classe (b) da P2.2 e o contraexemplo medido;
    - **sem saida declarada**: o canal que faz a tarefa produz resposta.
      Razonete sem ela conta metade da fronteira.
    """
    linhas = list(itens or [])
    for i, linha in enumerate(linhas):
        if linha.get("papel") not in PAPEIS:
            raise ValueError(f"itens[{i}]: papel invalido "
                             f"{linha.get('papel')!r}; use {PAPEIS}")

    por_papel = {p: [x for x in linhas if x["papel"] == p] for p in PAPEIS}
    totais = {p: (_somar(*por_papel[p]) if por_papel[p] else _somar())
              for p in PAPEIS}

    avisos = []
    if not por_papel["interno"]:
        avisos.append({
            "codigo": "sem-turno-interno-declarado",
            "porque": "nenhuma leitura/chamada interna foi declarada. Se a "
                      "tarefa exigiu alguma, ela nao esta contada, e a "
                      "comparacao subestima o custo do canal alternativo."})
    if not por_papel["saida"]:
        avisos.append({
            "codigo": "sem-saida-declarada",
            "porque": "o canal que executa a tarefa emite resposta; "
                      "razonete sem `saida` conta metade da fronteira."})

    return {
        "lado": "alternativo",
        "proxy": PROXY,
        "itens": linhas,
        "por_papel": totais,
        "total": _somar(*linhas) if linhas else _somar(),
        "avisos": avisos,
    }


def comparar(assinatura: dict, alternativo: dict) -> dict:
    """Os tres numeros, a poupanca, e os limites colados nela.

    `nao_captura` sai SEMPRE, e a razao e a regra deste repositorio: o
    numero que viaja sem os proprios limites vira, na leitura seguinte,
    afirmacao que ninguem exerceu. Quem quiser citar a economia vai ter de
    carregar junto o que ela nao mede.

    `veredito` nao opina sobre a tese: diz apenas o que ESTA CORRIDA
    mostrou na fronteira, com o `n` na frente, porque uma corrida nao e
    tendencia.
    """
    residual = assinatura["residual_do_despachante"]
    total_alt = alternativo["total"]
    poupanca = {u: total_alt.get(u, 0) - residual.get(u, 0) for u in UNIDADES}
    base = residual.get("bytes_utf8", 0)
    razao = round(total_alt.get("bytes_utf8", 0) / base, 3) if base else None

    if poupanca["bytes_utf8"] > 0:
        veredito = ("na fronteira desta corrida o despacho custou MENOS "
                    "que o canal alternativo faria sozinho")
    elif poupanca["bytes_utf8"] < 0:
        veredito = ("na fronteira desta corrida o despacho custou MAIS "
                    "que o canal alternativo faria sozinho")
    else:
        veredito = "empate na fronteira desta corrida"

    return {
        "proxy": PROXY,
        "unidades": list(UNIDADES),
        "n_corridas": 1,
        "assinatura_absorveu": assinatura["total"],
        "alternativo_sozinho": total_alt,
        "residual_do_despachante": dict(residual),
        "poupanca": poupanca,
        "razao_alternativo_sobre_residual": razao,
        "veredito_da_fronteira": veredito,
        "avisos": list(alternativo.get("avisos") or []),
        "nao_captura": [dict(x) for x in NAO_CAPTURA],
    }
