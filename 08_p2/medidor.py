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

import argparse
import glob
import json
import os
import sys

import caminhos  # (insere 05_p0/06_p1a/08_p2/evidencias no sys.path)

from console import no_codec_do_console
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


def compor_assinatura(entrada_unitaria: dict, tentativas: list, *,
                      fonte: str, procedencia_entrada: str,
                      sessao_id=None, work_unit_id=None,
                      truncamento: dict | None = None) -> dict:
    """A ARITMETICA do lado da assinatura, uma vez so.

    Extraida de `medir_assinatura` na P2.4 e usada pelos DOIS caminhos —
    o que le a cadeia verificada e o que reproduz a corrida a partir de
    insumos versionados (`reproduzir`). Duas somas em modulos vizinhos
    seriam a duplicacao de leitor que este acervo ja tem em aberto: a
    receita poderia passar a devolver um numero que a cadeia nao devolve,
    e o revisor nao teria como saber qual das duas mudou.

    Ela nao sabe de onde vieram os numeros. Quem sabe e a `procedencia`
    que cada chamador declara, e ela viaja na saida.
    """
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
        "fonte": fonte,
        "procedencia_entrada": procedencia_entrada,
        "entrada_unitaria": dict(entrada_unitaria),
        "truncamento": truncamento,
        "tentativas": tentativas,
        "n_tentativas": len(tentativas),
        "total": _somar(entrada_total, saida_total),
        "total_entrada": entrada_total,
        "total_saida": saida_total,
        # O residual sai da MESMA fonte: prompt redigido uma vez, resposta
        # lida uma vez. As tentativas repetidas ficam com a assinatura.
        "residual_do_despachante": _somar(entrada_unitaria, lida_de_volta),
    }


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

    return compor_assinatura(
        entrada_unitaria, tentativas,
        fonte="cadeia-verificada (EventLog + CAS via EvidencePlane)",
        procedencia_entrada=procedencia_entrada,
        sessao_id=sessao_id, work_unit_id=work_unit_id,
        truncamento={
            "teto_chars": TETO_INTENCAO_CHARS,
            "possivel": da_cadeia["caracteres"] >= TETO_INTENCAO_CHARS,
            "divergencia_medida": divergencia,
        })


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


# --- A RECEITA: reproduzir uma medicao publicada (P2.4, achado C) -------------
#
# ACHADO C, medido em 2026-08-03: *"`08_p2/medidor.py` nao tem entrada de
# linha de comando; os numeros da fronteira sairam de script de sessao
# ausente do repositorio. O revisor recebe `medicao-p2*.json` e nao a
# receita."* E o mesmo defeito do MAJOR #5 / N6 — pacote que pede
# julgamento e omite o objeto julgado.
#
# O que a receita PODE e o que ela NAO PODE fazer, medido antes de
# escrita uma linha de codigo:
#
# | insumo | reproduzivel? |
# |---|---|
# | turno interno (arquivo do repositorio) | **SIM** — recontado do disco |
# | resposta da assinatura | **SIM em 4 das 5**, do recibo versionado |
# | prompt | **so na classe (c)**, recuperado do unico lab sobrevivente |
# | resposta do canal alternativo | **NAO** — nunca foi gravada |
#
# Por isso cada insumo declara ORIGEM, e o comando publica quantos bytes
# da comparacao foram RECONTADOS e quantos sao TESTEMUNHO. Um relatorio
# que dissesse apenas "confere" esconderia que parte do "confere" e a
# propria testemunha se conferindo — e essa e a familia (F).

DIR_RECEITAS = os.path.join(caminhos.RAIZ, "08_p2", "receitas")

ORIGENS = ("arquivo", "recibo", "testemunho")


class ReceitaInvalida(Exception):
    """Insumo que a receita declara e o repositorio nao sustenta."""


def _resolver_insumo(spec: dict, raiz: str | None = None) -> dict:
    """Um insumo declarado -> tamanhos + de onde eles vieram.

    Fail-closed: origem desconhecida, arquivo ausente ou testemunho sem
    numero levantam. Insumo que nao se resolve nao vira zero — zero
    silencioso mudaria o resultado sem mudar o relatorio.
    """
    base = raiz or caminhos.RAIZ
    origem = spec.get("origem")
    if origem not in ORIGENS:
        raise ReceitaInvalida(f"origem invalida: {origem!r}; use {ORIGENS}")

    if origem == "arquivo":
        caminho = os.path.join(base, spec["caminho"])
        if not os.path.isfile(caminho):
            raise ReceitaInvalida(f"insumo ausente do repositorio: "
                                  f"{spec['caminho']}")
        with open(caminho, "rb") as f:
            medida = tamanhos(f.read())
        return {"rotulo": spec.get("rotulo") or spec["caminho"],
                "procedencia": "medido-arquivo", "reproduzido": True,
                "fonte": spec["caminho"], **medida}

    if origem == "recibo":
        caminho = os.path.join(base, spec["caminho"])
        if not os.path.isfile(caminho):
            raise ReceitaInvalida(f"recibo ausente: {spec['caminho']}")
        with open(caminho, encoding="utf-8") as f:
            recibo = json.load(f)
        texto = recibo.get(spec.get("campo", "saida"))
        if texto is None:
            raise ReceitaInvalida(
                f"{spec['caminho']}: campo {spec.get('campo', 'saida')!r} "
                "ausente — o recibo nao carrega a resposta")
        return {"rotulo": spec.get("rotulo") or spec["caminho"],
                "procedencia": "medido-recibo", "reproduzido": True,
                "fonte": spec["caminho"], **tamanhos(texto)}

    # testemunho: o numero publicado, sem objeto no repositorio que o
    # sustente. Ele entra na conta e NAO entra na cobertura reproduzida.
    faltando = [u for u in UNIDADES if not isinstance(spec.get(u), int)]
    if faltando:
        raise ReceitaInvalida(
            f"testemunho sem {faltando}: numero declarado precisa das duas "
            "unidades, ou a conta fecha com zero inventado")
    if not spec.get("porque"):
        raise ReceitaInvalida(
            "testemunho sem `porque`: um numero que ninguem pode recontar "
            "tem de dizer por que nao pode")
    return {"rotulo": spec.get("rotulo") or "testemunho",
            "procedencia": "testemunho-nao-reproduzivel", "reproduzido": False,
            "porque": spec["porque"],
            **{u: int(spec[u]) for u in UNIDADES}}


def _tentativas_da_receita(spec: dict, entrada_unitaria: dict,
                           raiz: str | None = None):
    """As tentativas do lado da assinatura, do recibo ou por testemunho.

    LIMITE MEDIDO, e por isso fail-closed no caminho do recibo: ele guarda
    UMA `saida` — a final — e a lista de attempts. Numa corrida com
    fallback, a saida da tentativa que falhou nao esta la, e a conta
    sub-contaria o gasto. As cinco corridas publicadas tem
    `n_tentativas = 1`; qualquer outra levanta, em vez de devolver um
    numero menor que o real.

    O caminho do TESTEMUNHO existe por um fato desta fase: a corrida (c)
    da P2.2 **nao tem recibo** (sessao `dd4567c7…` nao aparece em
    `08_p2/evidencias/`). Foi ela que caiu no `UnicodeEncodeError` do
    console medido na propria P2.2 — o attempt deu sucesso, a franquia foi
    gasta, e o artefato de registro nunca existiu. A resposta dela vive
    apenas no lab, que nao e versionado. Declarar isso e o unico caminho
    honesto; inventar o texto para caber em 438 B seria o oposto.
    """
    base = raiz or caminhos.RAIZ
    if spec.get("origem") == "testemunho":
        saida = _resolver_insumo(spec, base)
        return [{
            "attempt_id": None,
            "executor": spec.get("executor"),
            "resultado": "sucesso",
            "final": True,
            "entrada": dict(entrada_unitaria),
            "saida": {u: saida[u] for u in UNIDADES},
            "procedencia_saida": saida["procedencia"],
            "fonte_saida": None,
        }], saida
    caminho = os.path.join(base, spec["caminho"])
    with open(caminho, encoding="utf-8") as f:
        recibo = json.load(f)
    concluidos = [a for a in recibo.get("attempts", [])
                  if a.get("resultado") is not None]
    if len(concluidos) != 1:
        raise ReceitaInvalida(
            f"{spec['caminho']}: {len(concluidos)} tentativas concluidas. O "
            "recibo carrega SO a saida final; com fallback a receita "
            "sub-contaria o gasto da assinatura")
    saida = _resolver_insumo(spec, base)
    att = concluidos[0]
    resolvido = att.get("executor_resolvido") or {}
    return [{
        "attempt_id": att.get("attempt_id"),
        "executor": f"{resolvido.get('provedor')}/{resolvido.get('modelo')}",
        "resultado": att.get("resultado"),
        "final": att.get("resultado") == "sucesso",
        "entrada": dict(entrada_unitaria),
        "saida": {u: saida[u] for u in UNIDADES},
        "procedencia_saida": saida["procedencia"],
        "fonte_saida": saida.get("fonte"),
    }], saida


def carregar_receita(caminho: str) -> dict:
    """Le uma receita do disco. `caminho` pode ser o id (`p22-a`)."""
    if not os.path.isfile(caminho):
        candidato = os.path.join(DIR_RECEITAS, f"{caminho}.json")
        if os.path.isfile(candidato):
            caminho = candidato
        else:
            raise ReceitaInvalida(f"receita nao encontrada: {caminho}")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def reproduzir(receita: dict, raiz: str | None = None) -> dict:
    """Refaz uma medicao publicada a partir dos insumos versionados.

    Devolve a comparacao recalculada, os numeros publicados, a conferencia
    campo a campo e — o campo que impede a leitura ingenua — a
    **cobertura reproduzida**: quantos dos bytes comparados foram
    RECONTADOS do repositorio, e quantos sao testemunho que so pode ser
    aceito ou recusado.
    """
    base = raiz or caminhos.RAIZ
    entrada = _resolver_insumo(receita["entrada"], base)
    entrada_unitaria = {u: entrada[u] for u in UNIDADES}

    tentativas, saida_assinatura = _tentativas_da_receita(
        receita["resposta_assinatura"], entrada_unitaria, base)

    assinatura = compor_assinatura(
        entrada_unitaria, tentativas,
        fonte="insumos versionados do repositorio (receita)",
        procedencia_entrada=entrada["procedencia"],
        sessao_id=receita.get("sessao_id"),
        work_unit_id=receita.get("work_unit_id"),
        truncamento={"teto_chars": TETO_INTENCAO_CHARS,
                     "possivel": entrada["caracteres"] >= TETO_INTENCAO_CHARS,
                     "divergencia_medida": None})

    internos = [_resolver_insumo(x, base)
                for x in receita.get("turno_interno") or []]
    alternativa = _resolver_insumo(receita["resposta_alternativo"], base)
    itens = ([{**entrada, "papel": "entrada"}]
             + [{**x, "papel": "interno"} for x in internos]
             + [{**alternativa, "papel": "saida"}])
    alternativo = medir_alternativo(itens)
    comparacao = comparar(assinatura, alternativo)

    insumos = [entrada, saida_assinatura, alternativa] + internos
    recontados = sum(x["bytes_utf8"] for x in insumos if x["reproduzido"])
    testemunho = sum(x["bytes_utf8"] for x in insumos if not x["reproduzido"])

    publicado = {}
    caminho_publicado = receita.get("publicado")
    if caminho_publicado:
        with open(os.path.join(base, caminho_publicado), encoding="utf-8") as f:
            publicado = json.load(f)

    return {
        "id": receita.get("id"),
        "titulo": receita.get("titulo"),
        "publicado": caminho_publicado,
        "insumos": insumos,
        "assinatura": assinatura,
        "alternativo": alternativo,
        "comparacao": comparacao,
        "cobertura_reproduzida": {
            "bytes_recontados_do_repositorio": recontados,
            "bytes_de_testemunho": testemunho,
            "fracao": round(recontados / (recontados + testemunho), 4)
            if (recontados + testemunho) else None,
            "porque_importa": "testemunho nao se verifica sozinho. O que "
                              "esta linha diz e quanto do 'confere' foi "
                              "RECONTADO e quanto foi aceito",
        },
        "conferencia": conferir(comparacao, assinatura, publicado),
    }


# Os campos conferidos contra a medicao publicada. Cada um e um numero que
# o README ou o registro CITAM — conferir o que ninguem cita provaria que
# o programa e determinista, e nao que ele reproduz o publicado.
CAMPOS_CONFERIDOS = (
    ("razao", ("comparacao", "razao_alternativo_sobre_residual")),
    ("residual_bytes", ("comparacao", "residual_do_despachante",
                        "bytes_utf8")),
    ("poupanca_bytes", ("comparacao", "poupanca", "bytes_utf8")),
    ("alternativo_bytes", ("comparacao", "alternativo_sozinho",
                           "bytes_utf8")),
    ("assinatura_bytes", ("comparacao", "assinatura_absorveu", "bytes_utf8")),
    ("saida_assinatura_bytes", ("assinatura", "total_saida", "bytes_utf8")),
)


def _cavar(dados: dict, trilha: tuple):
    for chave in trilha:
        if not isinstance(dados, dict) or chave not in dados:
            return None
        dados = dados[chave]
    return dados


def conferir(comparacao: dict, assinatura: dict, publicado: dict) -> dict:
    """Recalculado x publicado, campo a campo, sem ajustar nada.

    A regra da ordem: **nao ajustar o comando para caber no numero
    publicado**. Por isso esta funcao so COMPARA — ela nao tem margem, nao
    tem tolerancia e nao arredonda nada que nao esteja ja arredondado na
    fonte. Divergencia sai como divergencia.
    """
    recalculado = {"comparacao": comparacao, "assinatura": assinatura}
    linhas = []
    for nome, trilha in CAMPOS_CONFERIDOS:
        obtido = _cavar(recalculado, trilha)
        esperado = _cavar(publicado, trilha) if publicado else None
        linhas.append({"campo": nome, "recalculado": obtido,
                       "publicado": esperado,
                       "confere": (esperado is not None and obtido == esperado)})
    return {
        "confere": bool(linhas) and all(x["confere"] for x in linhas),
        "campos": linhas,
    }


def receitas_do_repositorio() -> list:
    """Todas as receitas versionadas, em ordem estavel."""
    return sorted(glob.glob(os.path.join(DIR_RECEITAS, "*.json")))


def relatar(resultado: dict) -> None:
    """Uma corrida reproduzida, em texto que cabe num terminal.

    TUDO passa por `no_codec_do_console`, e nao so o que parece
    arriscado. O que este relato imprime vem de ARQUIVO — titulo de
    receita, rotulo de insumo, motivo de testemunho —, e arquivo carrega
    o caractere que alguem escreveu nele. Foi um `→` vindo de fora que
    derrubou a corrida da P2.2 depois de a franquia ja ter sido gasta.
    Separar "o que precisa" de "o que nao precisa" criaria dois caminhos
    de impressao, e um deles voltaria a ser o cru.
    """
    conf = resultado["conferencia"]
    cob = resultado["cobertura_reproduzida"]
    marca = "CONFERE" if conf["confere"] else "DIVERGE"
    eco = lambda texto: print(no_codec_do_console(texto))   # noqa: E731
    eco(f"\n[{marca}] {resultado['id']} — {resultado['titulo']}")
    eco(f"  publicado: {resultado['publicado']}")
    for linha in conf["campos"]:
        sinal = "ok " if linha["confere"] else "!! "
        eco(f"    {sinal}{linha['campo']:<24} recalculado="
            f"{linha['recalculado']!s:<10} publicado={linha['publicado']}")
    eco(f"  cobertura: {cob['bytes_recontados_do_repositorio']} B "
        f"recontados do repositorio, {cob['bytes_de_testemunho']} B de "
        f"testemunho ({cob['fracao']:.1%} recontado)")
    for insumo in resultado["insumos"]:
        if not insumo["reproduzido"]:
            eco(f"    testemunho: {insumo['rotulo']} "
                f"({insumo['bytes_utf8']} B) — {insumo['porque']}")


def main(argv=None) -> int:
    """Entry point CLI — o objeto do achado C.

        python 08_p2/medidor.py --todas
        python 08_p2/medidor.py --receita p22-a
        python 08_p2/medidor.py --todas --json saida.json

    Codigo de saida **1** quando qualquer corrida diverge do publicado. A
    receita nao existe para dizer "confere": existe para que a divergencia
    apareca sozinha, sem depender de alguem conferir a olho.
    """
    p = argparse.ArgumentParser(
        description="Reproduz as medicoes de fronteira publicadas a partir "
                    "dos insumos versionados neste repositorio.")
    grupo = p.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--receita", help="id (ex.: p22-a) ou caminho")
    grupo.add_argument("--todas", action="store_true",
                       help="todas as receitas de 08_p2/receitas/")
    p.add_argument("--json", dest="json_saida",
                   help="grava o resultado completo neste caminho")
    args = p.parse_args(argv)

    caminhos_receitas = (receitas_do_repositorio() if args.todas
                         else [args.receita])
    if not caminhos_receitas:
        print(f"nenhuma receita em {DIR_RECEITAS}", file=sys.stderr)
        return 2

    resultados = []
    for caminho in caminhos_receitas:
        resultado = reproduzir(carregar_receita(caminho))
        relatar(resultado)
        resultados.append(resultado)

    if args.json_saida:
        with open(args.json_saida, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2,
                      sort_keys=True)
        print(f"\njson: {args.json_saida}")

    divergem = [r["id"] for r in resultados if not r["conferencia"]["confere"]]
    total_recontado = sum(
        r["cobertura_reproduzida"]["bytes_recontados_do_repositorio"]
        for r in resultados)
    total_testemunho = sum(
        r["cobertura_reproduzida"]["bytes_de_testemunho"] for r in resultados)
    print(f"\n{len(resultados)} receita(s); {len(divergem)} divergente(s)"
          + (f": {divergem}" if divergem else ""))
    print(f"no conjunto: {total_recontado} B recontados do repositorio, "
          f"{total_testemunho} B de testemunho")
    return 1 if divergem else 0


if __name__ == "__main__":
    raise SystemExit(main())
