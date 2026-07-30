---
id: SSC-TO-02
titulo: TO-2 — Contextual (L2)
tipo: tarefa-ouro
versao: 0.1.0
status: pre-registrada
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# TO-2 — Contextual: responder com citacao de arquivo/linha

- **Entrada:** repo-fixture minimo (`fixtures/to2/`, 3 arquivos, < 60 linhas no
  total) montado em ContextPackage + pergunta: "qual funcao valida o selo do
  checkpoint e em que arquivo/linha ela esta?". A resposta correta e plantada no
  fixture (`kernel.py`, linha conhecida).
- **Criterio de aceite (congelado):** a resposta cita o arquivo correto **e** um
  intervalo de linhas que contem a funcao plantada (verificacao contra o
  fixture). E o ContextPackage inclui o arquivo necessario **sem** incluir os
  arquivos marcados como irrelevantes (lista de exclusao declarada).
- **Metodo de verificacao:** Juiz 1 deterministico: (a) localiza a citacao na
  resposta; (b) confere contra o fixture; (c) audita `entradas` do pacote
  contra a lista de exclusao.
- **Evidencia esperada:** ContextPackage com proveniencia completa (IC-1) e
  `custo_contexto_linhas` medido; veredito com evidencia por criterio.
- **N declarado:** 3 sementes (`{12, 23, 34}`), executor falso L2 que responde
  corretamente **somente se** o arquivo certo estiver no pacote (comportamento
  programado do falso: sem o contexto, responde sem citacao → reprovado).
- **Mede:** se a montagem do ContextPackage carrega o suficiente — e so o
  suficiente (exclusoes respeitadas, linhas medidas).
