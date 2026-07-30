---
id: SSC-TO-03
titulo: TO-3 — Julgamento (L3): diff plantado com defeitos
tipo: tarefa-ouro
versao: 0.1.0
status: pre-registrada
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# TO-3 — Julgamento: taxa de deteccao lida, nunca assumida

- **Entrada:** diff plantado (`fixtures/to3/diff.patch`) com **5 defeitos
  conhecidos** (semente declarada em `fixtures/to3/semente.json`: id, arquivo,
  linha, tipo) e 0 defeitos adicionais reais.
- **Criterio de aceite (congelado):** o revisor (executor falso L3) reporta
  exatamente os 5 defeitos da semente: deteccao 5/5, falso-positivo 0. A tarefa
  registra **taxa lida** ainda que imperfeita — o numero medido e o resultado,
  nao a expectativa (contra-exemplo A4: scanner sem taxa lida = instrumento nao
  calibrado).
- **Metodo de verificacao:** Juiz 1 deterministico casa os achados reportados
  com a semente (por arquivo+linha+tipo) e computa deteccao e FP. Juiz-llm falso
  (camada 2) julga a qualidade da redacao dos achados — com `pacote_juiz`
  completo e independencia calculada; **nao pode anular** a contagem
  deterministica (IV-2).
- **Evidencia esperada:** veredito deterministico com taxa lida; veredito
  juiz-llm com `independencia` preenchida; tentativa de anular falha
  deterministica via LLM registrada como invalida (prova IV-2).
- **N declarado:** 3 sementes de executor (`{13, 24, 35}`) programadas para
  detectar {5, 4, 3} dos 5 defeitos → taxas lidas esperadas 1.0, 0.8, 0.6 com
  FP {0, 1, 0}.
- **Mede:** deteccao/FP por executor; separacao de camadas do Judge.
