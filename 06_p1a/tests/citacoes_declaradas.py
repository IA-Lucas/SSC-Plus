"""Citacao forense declarada — SSC+ P1-A.9, ordem 3.

O DEFEITO, medido na P1-A.8 §1.5 e nomeado pelo despacho da P1-A.9:

    Uma guarda que varre a arvore inteira por substring literal torna o
    acervo INCAPAZ DE DOCUMENTAR A PROPRIA GUARDA. Todo registro que a
    discuta e, por construcao, uma violacao dela.

A conta que fecha o argumento: `ZeroPiiNosArtefatos` denunciava **11**
ocorrencias, e **7 delas estavam no registro que explicava o defeito**.
O instrumento contava a si mesmo — a sexta vez que este acervo encontra
esse padrao.

## A DISTINCAO QUE O GUARDA NAO FAZIA, e que este modulo faz

Ha duas coisas diferentes debaixo de "PII num arquivo":

1. **ARTEFATO GERADO que carrega PII** — vazamento. Um pacote, uma
   evidencia, um log escrito por um escritor. Aqui a politica e
   **REDIGIR**, e quem prova isso sao as provas comportamentais dos
   escritores (`test_redacao_operacao_p1a39`,
   `test_redacao_geradores_p1a39`). Tolerancia **zero**, e nada neste
   modulo a afrouxa.
2. **REGISTRO que CITA a PII para documenta-la** — o oposto de
   vazamento: e o acervo dizendo o que achou. Redigir aqui destruiria a
   unica explicacao que o Fundador tem do defeito, e foi por essa mesma
   razao que a ordem 6 recusou redigir os valores casados na propria
   evidencia de varredura.

A politica vigente ate aqui tratava as duas como uma so, e por isso
**crescia a cada missao que a documentava**.

## COMO SE DECLARA, e por que isto NAO e uma lista frouxa

Uma entrada aqui **autoriza um arquivo NOMEADO a citar**, com o motivo
por escrito. Tres propriedades a impedem de virar tapete:

- **arquivo nao declarado com uma so ocorrencia REPROVA.** O default
  continua sendo zero;
- **declaracao que nao casa mais REPROVA** (`declaracoes_mortas`). Um
  caminho que deixou de existir, ou que deixou de conter o token, e uma
  declaracao decorativa — e este acervo ja pagou pela classe "declaracao
  que ninguem exercita" nos achados 7, 10 e 14 da P1-A.3.5;
- **o motivo e obrigatorio** e vai no proprio dicionario, nao num
  comentario solto.

## O QUE ESTE MODULO **NAO** FAZ, declarado

- **nao afrouxa a redacao de artefato gerado.** Nenhum escritor passa a
  poder gravar PII: os guardas de redacao seguem intactos e nao leem
  este arquivo;
- **nao conta ocorrencias dentro de arquivo declarado.** Autoriza a
  citacao, nao um numero. Um vazamento real ESCONDIDO dentro de um
  registro declarado passaria — e o preco esta declarado aqui em vez de
  descoberto depois. A contencao dessa brecha e que a lista e curta,
  nominal, e so contem registros de decisao;
- **nao decide o que e PII.** Os alvos continuam onde estavam, em cada
  guarda.
"""

import os

# --------------------------------------------------------------------
# PII — o nome de usuario HISTORICO desta fabrica, citado para ser
# documentado. Caminhos relativos a `06_p1a/`.
# --------------------------------------------------------------------
REGISTROS_QUE_CITAM_PII = {
    "99_decisao-p1a7.md":
        "registro da P1-A.7: a ordem 6 transcreveu o caminho do blob "
        "orfao (§6.2) ao medir que ele NAO viaja no push, e a Parte II "
        "descreve a regressao que isso causou nas guardas",
    "99_decisao-p1a8.md":
        "registro da P1-A.8: classifica as nove falhas e precisa nomear "
        "o alvo literal para mostrar que ele nao depende da estacao",
}

# `99_decisao-p1a9.md` NAO esta na lista acima, e a ausencia foi MEDIDA,
# nao esquecida. Ele foi declarado primeiro e a suite o reprovou como
# **declaracao decorativa**: o registro da P1-A.9 explica a guarda
# escrevendo o alvo na forma CONCATENADA (`"IA " + "Lucas"`), que e como
# o proprio teste o monta — e por isso o texto nunca contem o literal.
# Da a licao mais util desta ordem: **documentar a guarda sem
# reproduzir o token e possivel**, e quando e possivel, e melhor que
# declarar a citacao. A declaracao existe para quando NAO for.

# --------------------------------------------------------------------
# SEGREDO — valores de FIXTURE que a varredura da P1-A.7 ordem 6 ecoa
# por desenho, e os documentos que os citam pelo nome.
# --------------------------------------------------------------------
ARTEFATOS_QUE_CITAM_FIXTURE = {
    "evidencias/p1a7-varredura-segredo-20260805T210650Z.json":
        "evidencia da varredura de segredo: ecoa o VALOR LITERAL de cada "
        "casamento de proposito. A ordem 6 recusou redigi-los com razao "
        "medida — o valor literal e o que permite a um terceiro conferir "
        "que aquilo e fixture, e evidencia que esconde o que achou pede fe",
    "evidencias/varredura_segredo_p1a7.py":
        "o proprio varredor: carrega as 34 regras, e uma delas cita a "
        "fixture no comentario que explica por que a regra so-alfanumerica "
        "nao bastava",
    "99_decisao-p1a7.md":
        "registro da P1-A.7: a §5 da Parte I nomeia as nove familias de "
        "fixture uma a uma, que e o que sustenta o veredito PUSH LIBERADO",
}


def nao_declarados(por_arquivo, autorizados) -> list:
    """Achados em arquivo que NINGUEM autorizou. O default e zero."""
    return sorted(rel for rel in por_arquivo if rel not in autorizados)


def declaracoes_mortas(por_arquivo, autorizados, raiz) -> list:
    """Declaracao que nao casa mais — decorativa, e por isso REPROVA.

    Duas formas de morrer: o arquivo sumiu, ou ele existe e ja nao
    contem o que a declaracao diz que ele contem.
    """
    mortas = []
    for rel in sorted(autorizados):
        if not os.path.exists(os.path.join(raiz, rel.replace("/", os.sep))):
            mortas.append(f"{rel}: caminho nao existe")
        elif rel not in por_arquivo:
            mortas.append(f"{rel}: ja nao casa — declaracao decorativa")
    return mortas
