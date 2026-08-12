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
| — | [99_decisao-ssc-01.md](00_governanca-experimental/99_decisao-ssc-01.md) | Validacao da missao e decisao (READY-FOR-SSC-0.2 / ADJUST / BLOCKED / STOP) |

## Fase P2 — frota supervisionada ativa

| Documento | Conteudo |
|---|---|
| [08_p2/00_ato-soberano-p2.md](08_p2/00_ato-soberano-p2.md) | O ato que autoriza a P2, com o que segue PROIBIDO |
| [08_p2/README.md](08_p2/README.md) | **Como usar**: declarar tier → lease + preflight → despachar tarefa |
| [08_p2/99_registro-p2.md](08_p2/99_registro-p2.md) | Registro da missao, achados por familia e limites declarados |

O mecanismo admite `codex`, `claude`, `kimi` e `google` dentro da capsula,
em modo supervisionado e somente leitura, com custo variavel externo
**zero**. Em **2026-08-11**, tiers e preflight foram renovados e Claude e
Google tiveram caminho produtivo medido. Renovar declaracoes continua sendo
ato do proprietario; codigo nenhum o faz por conta propria. `grok` permanece
`SUPERVISED`, fora da rota automatica. Nenhuma revisao independente
certificou este hardening — quem corrigiu nao certifica.

Entrada recomendada no Windows: duplo clique em `SSC-Plus.cmd` ou, no
PowerShell, `.\SSC-Plus.cmd`. O lancador administra lease, validade de tiers,
preflight, snapshot read-only do workspace, roteamento e recibo; confirmacao de
tier vencido continua sendo ato humano explicito.

O menu agora expoe quatro operacoes: analisar projeto, corrigir problema,
implementar funcionalidade e revisar alteracao. O fluxo usa Kimi para contexto
extenso, Codex como autor, Claude como revisor e Google como juiz, seguido de
testes locais. Mudancas sao propostas e testadas em copia; a aplicacao exige
aprovacao explicita separada por token.

## Verificacao unica

```powershell
python scripts/verificar.py
```

O comando registra os quatro campos de plataforma, roda P0 e P1-A/P2 em
processos separados, executa a prova central e confere as cinco receitas.
Python suportado: `>=3.14,<3.15`; dependencias de teste estao fixadas em
`requirements-dev.txt`. A mesma entrada e usada pela CI do repositorio.

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
   P2 e libera runtime e invocacao produtiva na capsula, em modo
   supervisionado. Confirmacao operacional do proprietario em 2026-08-11
   acrescentou `claude` e `google` a `codex` e `kimi`; `grok` continua fora.
   **Chamada de API paga continua PROIBIDA** — a politica economica nao foi
   tocada.
4. Nenhum ID canonico (FND/ADR/RFC/CAP/DEP/...) e criado aqui. Prefixos `SSC-*` sao
   locais e nao existem no espaco canonico.
5. Nada experimental sobe para o canonico automaticamente — ver D8.
