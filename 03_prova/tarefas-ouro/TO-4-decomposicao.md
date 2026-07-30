---
id: SSC-TO-04
titulo: TO-4 — Decomposicao: DAG com ondas topologicas
tipo: tarefa-ouro
versao: 0.1.0
status: pre-registrada
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# TO-4 — Decomposicao: 3–6 filhos com dependencias reais

- **Entrada:** tarefa "produzir mini-relatorio" decomposta em 5 filhos:
  `coletar` → {`resumir-a`, `resumir-b`} → `consolidar` → `revisar`
  (dependencias em `depende_de`; `resumir-a` e `resumir-b` na mesma onda).
- **Criterio de aceite (congelado):** (a) o grafo e aceito como DAG (sem ciclo);
  (b) nenhum filho entra `em-execucao` antes de todos os `depende_de`
  `concluida` (ordem verificada pela `seq` do EventLog); (c) uma segunda
  decomposicao plantada com dois filhos de intencao sobreposta e **recusada**
  (IW-3, anti-competicao); (d) um grafo plantado com ciclo e **recusado** antes
  de qualquer execucao.
- **Metodo de verificacao:** Juiz 1 sobre o replay do EventLog: ordem de
  transicoes × `depende_de`; eventos de recusa presentes para (c) e (d).
- **Evidencia esperada:** WorkUnits com `parent_work_unit`; RoutingDecision por
  filho antes de execucao (IW-1); custo total medido (simulado) da decomposicao
  × custo da execucao unica equivalente, ambos registrados.
- **N declarado:** 1 DAG valido + 1 plantado com competicao + 1 plantado com
  ciclo; 2 sementes de executor (`{14, 25}`) para o DAG valido.
- **Mede:** anti-competicao, ordem topologica, custo de decompor × executar
  unico (simulado, rotulado).
