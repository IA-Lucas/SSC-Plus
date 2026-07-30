---
id: SSC-DEC-01
titulo: Decisao da Missao SSC+ 0.1
tipo: decisao-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Decisao da Missao SSC+ 0.1

> Registro de validacao e decisao. Nao e FIT, nao e ADR, nao e ato soberano —
> e o fechamento experimental do laboratorio, sujeito a revisao humana.

## DECISAO: **READY-FOR-SSC-0.2**

O SSC+ pode avancar como prototipo (camada P0 do Plano de Prova: contratos com
providers falsos), **nunca decidindo a frente da arquitetura canonica**.

## 1. Checklist de validacao exigido pela missao

| # | Exigencia | Resultado | Evidencia |
|---|---|---|---|
| 1 | Zero escrita fora do SSC+ | **PASS** | Todas as escritas da sessao em `E:/LucasIA/Projetos/SSC-Plus`; as alteracoes canonicas observadas tem mtimes de processo externo e jamais passaram por ferramenta desta missao (§2) |
| 2 | Fontes intactas | **PASS com achado** | Nenhuma fonte alterada **pela missao**. O canonico foi alterado **por processo externo** durante a janela (7 arquivos + 1 novo) — registrado, com snapshots v1/v2/v3; nucleo normativo (`foundation/`, templates) intacto em v1→v3 |
| 3 | Hashes reproduziveis | **PASS** | Snapshot v3 de fechamento: **98/98 OK** verificado imediatamente; v1→v2 diff integralmente explicado (§2); hashes do legado em D3 §1 reproduziveis sobre a working tree documentada |
| 4 | Rastreabilidade fonte → decisao → destino | **PASS** | D3 (fonte) → D4 (classificacao por ativo, com evidencia por linha) → D5/D6 (destino: contrato/componente) → D8 (Goal consumidor); D6 §5 traz tabela decisao × origem |
| 5 | Nenhuma dependencia oculta | **PASS** | Fase sem codigo e sem dependencias; dependencias conceituais herdadas listadas em D4 por ativo; isolamento e vetores de contaminacao em D2 §8 |
| 6 | Revisao arquitetural e de seguranca | **PASS com lacuna** | Revisao interna registrada em §3; **sem revisor independente nesta fase** — lacuna L1, mitigacao exigida antes da 0.2 |
| 7 | Lacunas explicitas | **PASS** | §4 |
| 8 | Proximo passo compativel com Goals 1.13–1.20 | **PASS** | §5 |

## 2. Incidente: escrita concorrente no canonico (nao causada pela missao)

- **Fato:** durante a janela da missao (2026-07-29 22:05 → 2026-07-30 01:32,
  horario local da maquina), um processo externo — com assinatura de fechamento da
  Missao 1.13 (Specifications) — alterou no canonico:
  `decisions/ADR-0021-framework-de-specifications.md`, `decisions/README.md`,
  `rfcs/README.md`, `governance/README.md`, `governance/artifact-registry.md`,
  `memory/README.md`, `README.md` (7 alterados) e criou
  `governance/relatorio-transicao-2026-07-29-specifications.md` (1 novo).
- **Evidencia de nao-autoria:** nenhuma ferramenta desta missao escreveu fora de
  `SSC-Plus`; os mtimes dos arquivos (22:21–01:32) sao de processo com padrao de
  escrita de missao canonica (registro, indice, transicao), e o conteudo alterado
  e de governanca — materia fora do escopo SSC+.
- **Impacto nos entregaveis:** as citacoes de ADR-0021/RFC-0017 em D1, D4, D8 e na
  investigacao canonica referem-se aos bytes do snapshot v1. A posicao estrategica
  usada ("Goals 1.14–1.19 sem framework canonico; Specs incriaveis sem Produto")
  nao depende das linhas alteradas, mas **a releitura e obrigatoria na abertura
  da 0.2** (acao A2, §6).
- **Aprendizado:** confirma em tempo real o aviso B-04 da A4. Regra adotada
  (memoria/): snapshot no inicio **e** revalidacao no fim de toda missao.

## 3. Revisao arquitetural e de seguranca (interna)

**Arquitetura.** (a) Separacao de componentes sem sobreposicao de decisao: Router
decide rota, Policy veta, Execution executa, Judge julga, Kernel persiste,
Control Plane escala — nenhum componente decide e verifica o mesmo objeto.
(b) Eixos L1–L3 × C0–C3 declarados independentes (D6 §3), sem emprestar
autoridade ao vocabulario experimental. (c) Toda recuperacao e evento tipado;
nenhuma retentativa silenciosa. (d) Riscos Altos herdados do legado (captura de
CLI; worktree e2e) viraram provas obrigatorias (D7 §5, §7), nao suposicoes.
**Fragilidade aceita:** D5/D6 sao especificacao de papel; contradicoes internas
so aparecerao na implementacao P0 — e o criterio de saida da P0 existe para isso.

**Seguranca.** (a) Nenhum segredo no repositorio; `.gitignore` ativo; nenhuma
chave lida ou copiada das fontes (o handoff legado sobre a chave NVIDIA exposta
foi registrado como evidencia, nao reproduzido). (b) Vetor perfil-como-codigo
fechado por desenho (allowlist de binarios, D6 §2.7). (c) Conteudo externo nunca
executavel (D2 §2, D5 IC-2). (d) Nenhuma superficie de rede criada.
(e) `sessoes/` do legado (estado de producao com dados reais) lido apenas como
evidencia; nenhum dado pessoal copiado para o laboratorio.

## 4. Lacunas explicitas

- **L1 — Sem revisao independente.** Todos os artefatos foram produzidos e
  revisados pela mesma sessao (violacao controlada de "quem executa nao verifica",
  declarada). **Mitigacao obrigatoria antes de codigo na 0.2:** revisao humana do
  Soberano ou juiz independente sobre D5/D6.
- **L2 — Canonico movel.** ADR-0021 e os indices mudaram durante a missao;
  citacoes = snapshot v1. Releitura obrigatoria na abertura da 0.2.
- **L3 — Legado sem baseline commitada.** Hashes de D3 sao da working tree suja;
  se o operador commitar/limpar, o baseline muda — recapturar na 0.2.
- **L4 — Kimi K3 nao verificado.** Candidato de evidencia externa; nenhuma
  alegacao sobre ele e fato nesta fase; preferencia de modelo do Soberano e
  `unknown` (MEM-EST-0001 AF-29).
- **L5 — Roteamento de Goals nao normativo.** O mapa 1.13–1.20/Epico 2 vem da A4
  (evidencia externa); o destino canonico real sera o que o canonico disser.
- **L6 — Zero fontes originais abertas.** Nao houve duvida material; se surgir,
  reabrir so a fonte especifica com reconferencia de hash (regra B-04).
- **L7 — Metricas: nenhuma.** Este documento nao reporta nenhum numero de
  qualidade/custo/latencia — so definicoes (D7 §10). Resultados existirao a
  partir da P0/P2, medidos.

## 5. Proximo passo (compatibilidade com Goals 1.13–1.20)

**SSC+ 0.2 — camada P0 do Plano de Prova:** implementar, dentro deste
repositorio e sem rede, os contratos D5 com providers falsos deterministicos e a
bateria de falhas injetadas; criterio de saida P0 ja definido (D7 §11).
Compatibilidade: alimenta **1.15** (Tools & Models: adapters, roteamento,
metricas de custo), **1.17** (Workflows: WorkUnit/decomposicao), **1.18**
(Agents: contratos de especialista via ContextPackage), **1.19** (Execution &
Evaluation: attempts, eventos, juiz) e **Epico 2** (kernel: sessao, memoria,
EventLog). Nenhum trabalho da 0.2 escreve no canonico; promocao futura segue D8.
Pre-condicoes de abertura da 0.2: mitigar L1 (revisao) e executar A2 (releitura).

## 6. Apos deixadas para a 0.2

- **A1** Revisao humana/independente de D5 + D6 (mitiga L1).
- **A2** Releitura de ADR-0021, RFC-0017 e indices alterados; re-snapshot do
  canonico; atualizar citacoes se necessario (mitiga L2).
- **A3** Recaptura dos hashes do SuperCondutor se a working tree mudar (L3).
- **A4** Criar `03_prova/tarefas-ouro/` com as cinco familias TO-1 a TO-5 e seus
  criterios de aceite pre-registrados.

## 7. Alternativas consideradas (e por que nao)

- **ADJUST** — seria a decisao se algum entregavel faltasse ou se a contaminacao
  fosse nossa. Os 8 entregaveis existem, e o incidente e externo e documentado.
- **BLOCKED** — nao ha impedimento: isolamento provado, fontes acessiveis, nenhum
  insumo faltante para a P0.
- **STOP** — nenhuma condicao de encerramento da Carta §8 ocorreu; o achado de
  escrita concorrente e risco gerenciado (R7), nao violacao do laboratorio.
