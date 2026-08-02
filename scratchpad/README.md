# `scratchpad/` — estado de instrumento, nunca de produto

Diretorio de **runtime de medicao**, na mesma classe de `locks/` e
`05_p0/saidas/labs/`: o que vive aqui e instrumento, jamais artefato.

## `MUTANTE-ATIVO.txt` — o registro obrigatorio

Gravado pela regra de **reversao vermelha** do `CLAUDE.md` da raiz. Uma
queda de energia no meio da P1-A.3.9 deixou dois mutantes aplicados na
arvore viva (`contratos.AUTH_MODES` sem `desconhecido` e
`estados.TERMINAIS_WORK_UNIT` sem `cancelada`), e a arvore alterada
parecia correcao incompleta quando era o oposto: restos de instrumento.

**Por que na RAIZ do repositorio, e nao no scratchpad da sessao.** A
regra diz *"toda retomada apos queda le esse arquivo ANTES de qualquer
medicao"* — e a sessao que retoma **nao e** a que caiu. O scratchpad de
sessao fica sob um caminho com o id da sessao, que a proxima sessao nao
tem como adivinhar. Registro que a sucessora nao acha nao cumpre a
propria regra; por isso o caminho e fixo e relativo ao repositorio:

    scratchpad/MUTANTE-ATIVO.txt

Formato livre, mas precisa responder tres coisas — **arquivo, linha,
valor original** — e uma quarta que a queda ensinou: **o que a mutacao
degrada enquanto estiver aplicada**.

    arquivo: 05_p0/ssc_p0/contratos.py
    linha:   60
    original: "desconhecido",
    degrada: enum fail-closed da frota — o ramo `auth_mode desconhecido
             = DENY` fica INALCANCAVEL enquanto o mutante estiver ativo
    missao:  P1-A.3.9

Apagar **so depois** de reverter e a suite voltar verde.

O arquivo e ignorado pelo Git de proposito: e estado de execucao. Este
README e versionado porque a convencao precisa sobreviver a limpeza do
diretorio.
