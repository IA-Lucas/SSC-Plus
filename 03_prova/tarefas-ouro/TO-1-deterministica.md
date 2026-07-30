---
id: SSC-TO-01
titulo: TO-1 — Deterministica (L1)
tipo: tarefa-ouro
versao: 0.1.0
status: pre-registrada
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# TO-1 — Deterministica: transformacao com saida exata

- **Entrada:** texto fixo conhecido (`fixtures/to1/entrada.txt`, gravado no CAS
  da corrida) + instrucao "converter para maiusculas ASCII e ordenar as linhas".
- **Criterio de aceite (congelado):** `saida_final` byte-a-byte igual ao oraculo
  pre-computado (`fixtures/to1/oraculo.txt`). Qualquer divergencia = reprovado.
- **Metodo de verificacao:** Juiz 1 (camada deterministica) compara sha256 da
  saida com sha256 do oraculo. Nenhuma camada LLM envolvida.
- **Evidencia esperada:** ValidationVerdict `deterministica` com
  `criterios_ref` = hash deste criterio; ExecutionAttempt com
  `executor_observado` registrado; custo/latencia simulados rotulados.
- **N declarado:** 3 sementes de provider falso (`seed ∈ {11, 22, 33}`), 1
  executor L1 por semente. Esperado: 3/3 aprovados — o barato (L1) basta.
- **Mede:** se a rota mais barata que atende ao perfil resolve a tarefa; se a
  captura estruturada preserva bytes exatos.
