---
id: SSC-ATO-P2-00
titulo: Ato soberano que autoriza a P2 — o consumidor da frota
tipo: ato-experimental
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Ato soberano — abertura da P2

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Registro **aditivo**: nenhum documento anterior foi aberto
> para escrita. As paradas de 30/07, os registros da P1-B.01/P1-B.02 e
> as evidencias datadas permanecem intactos e continuam verdadeiros
> sobre as corridas que os produziram.

## 1. O que foi perguntado, e o que foi respondido

A sessao mediu o estado do laboratorio e encontrou uma **colisao entre o
pedido e tres regras escritas do proprio repositorio**. Nao obedeceu nem
recusou em silencio: apontou as regras, com endereco, e devolveu o
tradeoff ao Fundador.

As tres regras, como estavam no HEAD `7bdb499`:

| # | Onde | O que dizia |
|---|---|---|
| R1 | `06_p1a/tiers_declarados.json:4` | a declaracao de tier "habilita SOMENTE SHADOW_ELIGIBLE ... **NAO autoriza P2 nem execucao autonoma**" |
| R2 | `06_p1a/tests/sentinela_antip2.py:24-27` | metade (B): em **nenhum** arquivo do repositorio uma decisao sobre o veredito pode governar execucao |
| R3 | `README.md:55` | "Proibidos nesta fase: runtime, integracao com provedor, chamada de API paga ... agente oficial" |

**Resposta do Fundador, registrada:** abrir a **P2 completa dentro do
SSC+** — adaptador de assinatura real no lugar do `FakeProvider`, frota
`codex` + `kimi`, `RoutingDecision` viva, fallback por quota e juiz
independente. Renovar as duas declaracoes de tier.

## 2. O que este ato autoriza — e o que NAO autoriza

**Autoriza:**

1. **um consumidor do veredito**: codigo que le a classificacao do
   preflight e, com base nela, despacha trabalho a um CLI de assinatura;
2. **invocacao produtiva de modelo** pelos CLIs `codex` e `kimi`, em modo
   nao-interativo, dentro da capsula ratificada da P1-A.2;
3. **emenda a R2** — a sentinela anti-P2 deixa de proibir todo consumidor
   e passa a exigir que o consumidor seja **declarado nominalmente**.

**NAO autoriza, e cada item segue valendo como estava:**

1. **nenhuma mudanca na politica economica.** `POLITICA_ECONOMICA`
   permanece imutavel; `payg_api = DENY`, `extra_usage = DENY`,
   `auto_topup = DENY`, `external_variable_cost_cap = 0`. Custo variavel
   externo continua **zero**: a assinatura ja esta paga, e migrar para
   API paga, creditos extras ou saldo pre-pago segue **PROIBIDO**;
2. **nenhuma mudanca na capsula.** O SSC+ continua nascendo sem nenhuma
   credencial de modelo no ambiente; `HKCU\Environment` nao e tocado;
   `nvidia` continua no escopo de bloqueio de `economia.py:53`;
3. **nenhuma promocao ao canonico.** O LucaX Enterprise OS segue como
   unica fonte normativa; nada daqui sobe automaticamente (D8);
4. **claude, google e grok continuam SUPERVISED.** O teto de
   especificacao nao foi emendado. A P2 opera com `codex` e `kimi`, os
   dois unicos com OAuth de assinatura observado E declaracao valida;
5. **execucao desacompanhada (`unattended`) continua fora.** O modo de
   execucao da P2 e `supervised`;
6. **R1 nao foi alterada, porque continua verdadeira.** A *declaracao de
   tier* segue sem autorizar P2 — quem autoriza e **este ato**. A linha
   `limites` do `tiers_declarados.json` fica como esta, de proposito: o
   mecanismo automatico nao deve ganhar poder que so o Fundador tem.

## 3. R3 — o que muda no README

A regra dura 3 do `README.md` descreve "esta fase", e a fase que ela
descrevia era a das Missoes SSC+ 0.1/0.2. Este ato **abre uma fase nova**
e nao apaga a anterior: o texto do README ganha a data em que a proibicao
de runtime deixou de valer, e para qual escopo — nunca uma borracha sobre
o que valia antes.

## 4. A emenda a sentinela (R2), em termos exatos

A sentinela **nao e desligada**. Ela e convertida:

| | antes deste ato | depois |
|---|---|---|
| metade (A) | nenhum arquivo decide sobre o veredito fora do classificador | **inalterada** |
| metade (B) | **nenhum** arquivo pode ter decisao de veredito governando execucao | somente **consumidor declarado** pode; qualquer outro continua sendo achado |
| o que some | — | **nada**: portao de consumidor declarado sai em campo proprio (`portoes_autorizados`), visivel, nunca suprimido |

O perigo que a sentinela existia para impedir era **P2 por acidente** —
um consumidor aparecendo sem que ninguem tivesse decidido. Uma allowlist
nominal preserva exatamente essa propriedade: o consumidor precisa ter
sido escrito no fonte da sentinela por um ato, e continua sendo o unico.

## 5. Condicoes de operacao que este ato impoe

1. **capsula obrigatoria** — o consumidor aborta fora dela, antes do
   lease e antes de qualquer invocacao;
2. **escritor unico** — lease de nome proprio verificado antes de cada
   persistencia, como nas missoes anteriores;
3. **portao economico ANTES da invocacao** — `verificar_economia` +
   `verificar_canal` + `verificar_automacao` correm antes de existir
   subprocesso; veto = zero chamadas;
4. **quota esgotada = nova decisao**, nunca PAYG; sem assinatura capaz =
   `STOP_WAIT_RESET`;
5. **toda invocacao produtiva e registrada** no EventLog com captura
   estruturada, mesmo em falha;
6. **custo medido, nunca simulado** — a P2 nao pode rotular `simulado` o
   que de fato ocorreu, e nao pode inventar contagem de token que o CLI
   nao reportou: ausencia de numero e `None`, nunca zero por conveniencia.

## 6. Quem constroi nao certifica

Esta missao escreve o codigo, os testes e a evidencia da P2. Ela **nao
emite atestado de aprovacao**. A verificacao independente segue pendente,
como manda o `CLAUDE.md` deste repositorio.
