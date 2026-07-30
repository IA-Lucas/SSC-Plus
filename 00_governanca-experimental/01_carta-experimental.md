---
id: SSC-DOC-01
titulo: Carta Experimental do SSC+
tipo: carta-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D1 — Carta Experimental do SSC+

> Documento fundacional do laboratorio. Nao e Carta de Departamento, nao usa o
> contrato de ADR-0011 e nao cria componente canonico. Prefixos `SSC-*` sao locais.

## 1. Proposito

Criar a fundacao experimental do **SSC+ (Super Super Condutor Plus)**: uma
implementacao greenfield de **orquestracao por tarefa em uma sessao logica
persistente**, na qual a sessao mantem memoria, contexto, orcamento e permissoes, e
cada unidade de trabalho escolhe ferramenta, provedor, modelo, effort, modo e
controle — trocar de modelo cria uma nova invocacao na mesma linhagem, sem reiniciar
a sessao logica.

O SSC+ existe para **produzir evidencia e propostas** que alimentem os Goals
canonicos 1.14 a 1.20 (Skills, Tools & Models, Commands, Workflows, Agents,
Execution & Evaluation, Vertical Proof) e o Epico 2 (kernel tecnico), antes que o
canonico normatize esse terreno — que hoje **nao possui nenhum framework vigente**
para essas materias (verificado em 2026-07-30: o unico framework de execucao
vigente e o de Specifications, ADR-0021).

## 2. Escopo

- Engenharia reversa do SuperCondutor legado (inventario, classificacao de ativos).
- Especificacao de contratos-alvo e arquitetura-alvo (papel, sem implementacao).
- Definicao de plano de prova (tarefas-ouro, shadow mode, providers falsos, juiz
  independente, metricas de qualidade/custo/latencia).
- Definicao do protocolo de integracao com o canonico.
- Nas fases seguintes (SSC+ 0.2+): prototipo executavel **dentro deste repositorio**,
  com providers falsos e piloto read-only, conforme o Plano de Prova (D7).

## 3. Nao escopo

- Implementar runtime, integrar provedor real ou chamar API paga (fase 0.1).
- Instalar dependencias, executar codigo legado, criar agente oficial.
- Escrever, emendar ou propor emenda direta no LucaX Enterprise OS, no legado
  `lucaX`, no acervo `_SAIDA-COMPANY-OS` ou em `LucaX-Enterprise-Research`.
- Criar IDs canonicos, ocupar diretorios canonicos previstos e nao criados
  (`skills/`, `workflows/`, `tools/`, `projects/` — FND-03 §7.2) ou declarar
  entidades novas no Meta Model (Sessao/Tarefa/Execucao nao existem em FND-09 §5;
  cria-las no espaco canonico seria materia C3 com ratificacao do Soberano).
- Substituir, preceder ou decidir a frente da arquitetura canonica.

## 4. Autoridade

| Materia | Autoridade do SSC+ |
|---|---|
| Documentos deste repositorio | Escreve e versiona livremente (escopo local) |
| Fontes read-only | Le, mede e cita; **nunca** escreve |
| Canonico (norma) | **Nenhuma.** Propoe via protocolo de integracao (D8) |
| Promocao de qualquer ativo | **Nenhuma.** Admissao exige o portao G1–G5 de ADR-0007 §5.3 e decisao formal no Goal competente |

Todo artefato deste repositorio carrega `autoridade: nenhuma · normativo: nao`.
Evidencia externa ou legada citada aqui **nao vira norma nem adocao automatica** —
espelha a regra FR-03/FR-04 de ADR-0007 e o bloco `external-evidence` da A4
congelada.

## 5. Relacao com o LucaX Enterprise OS

- O **LucaX Enterprise OS** e a unica fonte normativa, na baseline de referencia
  **`BL-2026-07-29-08`** (164 artefatos · 46.353 linhas · impressao digital
  `8cf2143c7d20d4688f911f716a7a683bc82b72d155e7d424e3f4875c8b027a7f`), fixada por
  snapshot de hashes em `01_fontes/snapshots/canonico-BL-2026-07-29-08.sha256`.
- O SSC+ respeita como vinculantes, no seu proprio desenho: a fronteira
  greenfield/legado (ADR-0007), a classificacao de mudanca C0–C3 (FND-04 §2 — que o
  SSC+ **preserva** para governanca e nao reutiliza para capacidade), a regra de
  fonte unica e projecao declarada (FND-10 §2.6, PJ-01 a PJ-03) e a proibicao de
  autoverificacao (ADR-0005 — por isso o Plano de Prova exige Juiz independente).
- O SSC+ **nao** herda departamentos, capabilities ou papéis canonicos. Referencias
  a `DEP-*`, `CAP-*` e Goals 1.13–1.20 em documentos deste repositorio sao citacoes
  de destino (quem consumiria a proposta), nao exercicio de papel.
- A escala L1/L2/L3 usada nos contratos-alvo e **vocabulario experimental do
  laboratorio**: o canonico nao define L1/L2/L3 (a maturidade canonica e o eixo de
  sete valores de FND-08 §3.3). Nenhuma afirmacao deste repositorio atribui essa
  escala ao framework canonico.

## 6. Riscos

| # | Risco | Mitigacao |
|---|---|---|
| R1 | Contaminacao do canonico ou do legado por escrita acidental | Manifesto de Isolamento (D2); validacao "zero escrita fora" ao fim de cada missao; fontes tratadas como read-only |
| R2 | Prototipo virar "norma de fato" e decidir a frente da arquitetura canonica | Carta §4; protocolo D8 (nada sobe automaticamente); rotulo `experimental` em todo artefato |
| R3 | Herdar defeitos conhecidos do legado (classificador por regex fragil, perda de dado em CLI sem captura estruturada, quota nao classificada) | Baseline D3 registra divergencias e riscos; matriz D4 marca o destino de cada ativo; contratos D5 tratam os pontos como requisitos |
| R4 | Custo nao autorizado (API paga) | Restricao de fase: zero chamada paga em 0.1; portao de custo bloqueante e requisito herdado (ADR-054 legado) e vive no Execution Gateway (D6) |
| R5 | Evidencia externa (A4) tomada como fato verificado | Regra da A4: consumo seletivo com ordem obrigatoria; fonte original so diante de duvida material, com reconferencia de hash (B-04); alegacoes V7/nao verificadas marcadas como tais |
| R6 | "Kimi K3" lido como adocao presumida | Registrado como **candidato a piloto, nao verificado**, sem endosso canonico (preferencia de modelo do Soberano e `unknown` — MEM-EST-0001 AF-29); avaliacao so no piloto do Plano de Prova |
| R7 | Divergencia entre o snapshot de referencia e o canonico vivo | Toda citacao normativa carrega baseline + hash; re-snapshot a cada missao; divergencia e achado, nunca motivo para editar fonte |

## 7. Responsaveis

| Papel | Quem | Alcance |
|---|---|---|
| Soberano | Lucas (humano) | Autoridade final e indelegavel sobre qualquer promocao ao canonico; unico que pode transformar proposta do SSC+ em materia canonica |
| Executor do laboratorio | Sessao SSC+ (agente de IA sob instrucao do Soberano) | Produz documentos, mede, classifica, propoe; nao aprova, nao promove, nao escreve fora |
| Revisor (futuro, SSC+ 0.2) | Juiz independente, provedor distinto do executor | Veredito sobre artefatos de prova (D7); quem executa nao verifica (GV-04) |

## 8. Condicoes de encerramento

O laboratorio se encerra (decisao `STOP` do protocolo) quando qualquer uma ocorrer:

1. **Encerramento por sucesso** — a materia de orquestracao por tarefa for
   normatizada no canonico (frameworks dos Goals 1.14–1.19 / Epico 2) e as propostas
   uteis do SSC+ tiverem sido promovidas ou explicitamente rejeitadas.
2. **Encerramento por inutilidade** — as provas mostrarem que o desenho-alvo nao
   agrega sobre o que o canonico ja decidir; o repositorio e arquivado com memoria
   do que foi medido (aprendizado sobe como evidencia, nao como norma).
3. **Encerramento por violacao** — qualquer escrita fora do isolamento, chamada de
   API paga nao autorizada ou contaminacao de fonte: a missao para, o incidente e
   registrado em `logs/` e a continuacao exige decisao explicita do Soberano.
4. **Encerramento por decisao** — o Soberano pode encerrar a qualquer tempo, sem
   justificativa; silencio nao prorroga.

## 9. Condicoes de sucesso da fase 0.1

- Os 8 entregaveis existem, sao rastreaveis fonte → decisao → destino.
- Zero escrita fora deste repositorio (validado por ferramenta, ver `99_decisao-ssc-01.md`).
- Hashes das fontes reproduziveis; lacunas explicitas; nenhuma dependencia oculta.
- Decisao final registrada: READY-FOR-SSC-0.2 | ADJUST | BLOCKED | STOP.
