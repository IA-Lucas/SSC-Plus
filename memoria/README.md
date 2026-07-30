---
id: SSC-IDX-MEM
titulo: Memoria do Laboratorio SSC+
tipo: indice-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Memoria do SSC+

Memoria local do laboratorio — isolada de `memory/` do canonico (Manifesto D2 §3).

## Regras

1. Toda entrada tem fonte verificavel e data (principio da memoria legada).
2. Validade por tipo: falha de ferramenta/provedor = curta (7d); veredito e
   decisao de missao = longa (365d). Esquecer = lapide append-only, nunca delete.
3. Memoria do laboratorio **nao orienta o canonico**; sobe, quando couber, como
   evidencia pelo protocolo D8.

## Entradas

| Data | Tipo | Validade | Entrada | Fonte |
|---|---|---|---|---|
| 2026-07-30 | decisao de missao | 365d | Missao 0.1 encerrada com READY-FOR-SSC-0.2; 8 entregaveis + snapshots v1–v3 | `99_decisao-ssc-01.md` |
| 2026-07-30 | risco observado | 365d | Canonico sofre escrita concorrente de missoes paralelas; snapshot unico nao e garantia — fixar baseline por hash no inicio e revalidar no fim | `logs/2026-07-30_missao-ssc-01.md` item 6 |
| 2026-07-30 | estado de fonte | 365d | Legado `lucaX`: HEAD fraco (334 mudancas locais); hash de working tree e a referencia | D3 §1 nota de proveniencia |
