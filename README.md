---
id: SSC-IDX-00
titulo: SSC+ — Indice do Laboratorio
tipo: indice-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# SSC+ (Super Super Condutor Plus)

> Laboratorio experimental greenfield de orquestracao por tarefa em sessao logica
> persistente. Produz evidencias e propostas. **Nao tem autoridade normativa e nao
> escreve em nenhum projeto canonico.**

## O que e

Repositorio proprio, isolado, criado pela Missao SSC+ 0.1 (2026-07-30). E laboratorio
do **LucaX Enterprise OS** (`E:/LucasIA/Projetos/LucaX Enterprise OS`), que permanece
a **unica fonte normativa**. Nada aqui e norma, adocao ou decisao: todo artefato deste
repositorio e `experimental / provisorio / sem autoridade`.

## Documentos (entregaveis da Missao SSC+ 0.1)

| # | Documento | Conteudo |
|---|---|---|
| D1 | [00_governanca-experimental/01_carta-experimental.md](00_governanca-experimental/01_carta-experimental.md) | Proposito, escopo, autoridade, riscos, encerramento |
| D2 | [00_governanca-experimental/02_manifesto-de-isolamento.md](00_governanca-experimental/02_manifesto-de-isolamento.md) | Caminhos, permissoes, segredos, rede, custo, anti-contaminacao |
| D3 | [01_fontes/03_baseline-supercondutor.md](01_fontes/03_baseline-supercondutor.md) | Inventario do SuperCondutor legado, com hashes e divergencias |
| D4 | [01_fontes/04_matriz-engenharia-reversa.md](01_fontes/04_matriz-engenharia-reversa.md) | Classificacao ADAPT / REWRITE / REFERENCE / RETIRE |
| D5 | [02_alvo/05_contratos-alvo.md](02_alvo/05_contratos-alvo.md) | SessionEnvelope, WorkUnit, ContextPackage, RoutingDecision etc. |
| D6 | [02_alvo/06_arquitetura-alvo.md](02_alvo/06_arquitetura-alvo.md) | Session Kernel, Task Router, Policy Gateway, Execution Gateway... |
| D7 | [03_prova/07_plano-de-prova.md](03_prova/07_plano-de-prova.md) | Tarefas-ouro, shadow mode, providers falsos, juiz independente |
| D8 | [04_integracao/08_protocolo-de-integracao.md](04_integracao/08_protocolo-de-integracao.md) | Snapshot canonico → SSC+ → evidencia → Goal competente → promocao |
| — | [99_decisao-ssc-01.md](99_decisao-ssc-01.md) | Validacao da missao e decisao (READY-FOR-SSC-0.2 / ADJUST / BLOCKED / STOP) |

## Fontes (somente leitura)

| Fonte | Caminho | Papel |
|---|---|---|
| LucaX Enterprise OS (canonico) | `E:/LucasIA/Projetos/LucaX Enterprise OS` | Unica fonte normativa; baseline `BL-2026-07-29-08` |
| SuperCondutor legado | `E:/LucasIA/Projetos/lucaX/My_WorkSpace/Meus_projetos/SuperCondutor` | Objeto de engenharia reversa |
| A4 congelada | `E:/LucasIA/Projetos/LucaX Enterprise OS/_SAIDA-COMPANY-OS` | Evidencia externa (RESEARCH-READY-FROZEN) |
| Acervo de pesquisa A0 | `E:/LucasIA/Projetos/LucaX-Enterprise-Research/acervo-company-os` | Trilha de inventario/hashes |

Snapshots de hash reproduziveis em [01_fontes/snapshots/](01_fontes/snapshots/).

## Regras duras

1. Escrita permitida **somente** dentro deste repositorio.
2. Proibidos: links simbolicos, imports diretos, estado compartilhado com as fontes.
3. Proibidos **nas fases 0.1/0.2**: runtime, integracao com provedor, chamada de
   API paga, instalacao de dependencias, execucao de codigo legado, agente
   oficial. **Emendado em 2026-08-03** pelo ato soberano
   [08_p2/00_ato-soberano-p2.md](08_p2/00_ato-soberano-p2.md), que abre a fase
   P2 e libera runtime e invocacao produtiva **somente** por `codex` e `kimi`,
   somente dentro da capsula, somente em modo supervisionado. **Chamada de API
   paga continua PROIBIDA** — a politica economica nao foi tocada.
4. Nenhum ID canonico (FND/ADR/RFC/CAP/DEP/...) e criado aqui. Prefixos `SSC-*` sao
   locais e nao existem no espaco canonico.
5. Nada experimental sobe para o canonico automaticamente — ver D8.
