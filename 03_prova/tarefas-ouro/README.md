---
id: SSC-TO-00
titulo: Tarefas-ouro — indice e regime de pre-registro
tipo: prova-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# Tarefas-ouro (TO-1 a TO-5) — pre-registro

> Conjunto fechado e versionado (D7 §2). **Pre-registradas antes de qualquer
> corrida da P0** (Missao 0.2, secao TESTES). Cada tarefa declara entrada,
> criterio de aceite, metodo de verificacao e evidencia esperada — disciplina
> SF-15 (ADR-0021) como vocabulario, sem conformidade canonica.
> Regra: criterio congelado aqui e o que entra em `criterios_aceite_ref` da
> WorkUnit correspondente; mudar criterio depois da corrida = nova versao da
> tarefa, nunca edicao retroativa.

| Tarefa | Familia (D7 §2) | Nivel | O que mede |
|---|---|---|---|
| [TO-1](TO-1-deterministica.md) | Deterministicas | L1 | O barato basta? Saida exata verificavel |
| [TO-2](TO-2-contextual.md) | Contextuais | L2 | ContextPackage: suficiente e so o suficiente |
| [TO-3](TO-3-julgamento.md) | Julgamento | L3 | Deteccao/falso-positivo **lidos** contra semente |
| [TO-4](TO-4-decomposicao.md) | Decomposicao | L1–L2 | DAG, ondas topologicas, anti-competicao |
| [TO-5](TO-5-adversarial.md) | Adversariais de roteamento | — | Falha fechada barata em vez de rota errada |

Na P0 todas correm contra **providers falsos deterministicos por seed**; numeros
produzidos sao **simulados** e rotulados como tal (D7 §3, MR-2). N declarado por
tarefa dentro de cada arquivo.
