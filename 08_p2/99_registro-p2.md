---
id: SSC-REG-P2-99
titulo: Registro da missao SSC+ P2.0 — o consumidor da frota
tipo: registro-experimental (NAO e atestado)
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Registro — Missao SSC+ P2.0

> Laboratorio experimental. Registro **aditivo**: nenhum documento
> anterior foi aberto para escrita. As paradas de 30/07 e os registros da
> P1-B.01/P1-B.02 permanecem intactos e continuam verdadeiros sobre as
> corridas que os produziram.
>
> **Este documento NAO e atestado de aprovacao.** Quem construiu nao
> certifica.

## 0. Medicao de partida e de fechamento

| Item | Abertura | Fechamento |
|---|---|---|
| HEAD | `7bdb499` | este commit |
| `git status --porcelain` | vazio | vazio |
| Suite `05_p0/tests` | **344/344 OK** | **344/344 OK** |
| Suite `06_p1a/tests` | **704/704 OK** | **799/799 OK** (704 + 95) |
| Escritor unico | `p2-ops`, fence **1**, pid 39312, adquirido ANTES da primeira escrita | mesmo lease, mesmo fence |
| Chamadas de modelo na historia do laboratorio | **0** | **3** (todas registradas) |

## 1. A colisao, e como ela foi tratada

O pedido — "finalizar o SSC+ para comecar a usar" — exigia um consumidor
do veredito, proibido por tres regras escritas do proprio repositorio
(`tiers_declarados.json:4`, `sentinela_antip2.py:24-27`, `README.md:55`).
A sessao **nao obedeceu nem recusou em silencio**: apontou as tres com
endereco e devolveu o tradeoff. O Fundador decidiu abrir a P2 completa.
Ato em [`00_ato-soberano-p2.md`](00_ato-soberano-p2.md).

## 2. Seis ordens, seis commits

| # | Ordem | O que entregou |
|---|---|---|
| 0 | ato + tiers | ato soberano; declaracoes renovadas com backup datado; README emendado com data e escopo |
| 1 | sentinela | allowlist nominal; o autorizado MIGRA de campo e nao some |
| 2 | executor real | `ProvedorAssinaturaReal`, interface identica a do `FakeProvider` |
| 3 | ponte | `frota_medida`: FleetEntry com procedencia declarada campo a campo |
| 4 | runner | consumidor completo, do preflight datado a evidencia redigida |
| 5 | corrida real | primeira invocacao produtiva + os dois defeitos que so ela achou |
| 6 | registro | este documento e o manual de uso |

## 3. O que foi MEDIDO em operacao real

Tres corridas, dentro da capsula, lease vivo, sobre preflight fresco
(`preflight-20260803T022852Z.json`: codex e kimi SHADOW_ELIGIBLE; claude,
google e grok SUPERVISED):

| evidencia | medido |
|---|---|
| `execucao-20260803T022952Z.json` | codex/`gpt-5.6-sol` — sucesso |
| `execucao-20260803T023110Z.json` | kimi falhou; **a maquina rerroteou sozinha** para codex, que concluiu |
| `execucao-20260803T023846Z.json` | kimi `falha-quota` TIPADA; codex sucesso; acentuacao integra |

**O fallback entre assinaturas foi exercido contra falha REAL**, nao
programada por `FakeProvider`. E a primeira vez que o mecanismo 0.2.1-6
atravessa um erro que nao foi escrito por quem o testa.

`custo_variavel: 0` nas tres. `capsula.violacoes_no_env_do_processo: []`
nas tres. Nenhuma escrita fora do laboratorio.

## 4. Achados desta missao

### 4.1 O teto zero nunca tinha sido exercido — familia (F)

`envelope_de_frota` declara `teto_custo: 0.0`, que e o
`external_variable_cost_cap = 0` da politica imutavel. Rodando com ele de
verdade, **nenhuma tarefa sai**: o default do Router estima
`{"valor": 0.01, "rotulo": "estimado"}`, numero simulado da P0, e o portao
de orcamento escalona antes do primeiro attempt.

Nunca apareceu porque `test_frota.py:47` monta o laboratorio com
`teto_custo=1.0` enquanto passa `envelope_de_frota()` — cujo teto e 0.0 —
a Policy. **O teto era DECLARADO no envelope e nunca EXERCIDO contra o
orcamento da sessao.** E a familia do MAJOR #3: o guarda afirmava a
propriedade em vez de exerce-la.

Remedio aplicado sem afrouxar: `executar_com_frota` ganha
`custo_previsto` (default `None` preserva o comportamento; 344/344 da P0
seguem verdes) e o runner declara `0.0` — sob assinatura o custo variavel
externo e zero por fato, nao por estimativa.

### 4.2 Esgotamento real lido como falha de contrato — familia (N)

Classe que nenhuma varredura anterior media, porque exigia um CLI com a
franquia de fato acabada. Com ela acabada, o kimi escreveu *"You've
reached your usage limit"*; a lista tinha *"usage limit reached"* — a
mesma frase na ordem inversa. `registrar_quota_exhausted` nunca correu, a
entrada ficou `disponivel` na frota, e a WorkUnit seguinte da mesma sessao
gastaria outra tentativa nela.

Corrigido no detector **canonico**, com o texto exato da evidencia como
fixture. Reversao vermelha: **8**.

### 4.3 Acento perdido virou o artefato final — familia (N)

A resposta em portugues chegou com todo acento trocado por U+FFFD, e o
texto corrompido foi para o CAS, para a cadeia de hashes e para o
artefato da WorkUnit. Perda irreversivel gravada como se fosse a
resposta. Causa: decodificacao fixa em utf-8 contra um CLI que escreve na
page de codigo do Windows. Reversao vermelha: **1**.

### 4.4 Uma flag que afirmava sem exercer, pega antes de sair

`--capacidade` entrava so no perfil da WorkUnit e **nao mudava quem
recebia a tarefa**. Declaracao morta em nascenca — a familia que a
P1-A.3.9 mediu. Corrigida na mesma ordem, com contraprova (capacidade
inexistente nao esvazia a frota: preferencia e preferencia).

### 4.5 Uma medicao falsa, refeita

O primeiro mutante da ordem 5 saiu MALFORMADO e devolveu **10
vermelhos**. A verificacao de sanidade acusou (`no calls left -> False`,
que deveria ser `True` mesmo antes da correcao) e a medicao foi refeita:
**8**. O numero 10 nao entra no registro. Fica escrito porque medicao que
ninguem confere e a mesma coisa que guarda que ninguem exerce.

## 5. Divergencias REGISTRADAS, nao corrigidas por conta propria

1. **`evidence.py:106` soma `custo.get("tokens", 0)`** e `:120` rotula os
   totais `simulado`. Com a P2, um attempt real sem contagem entra como
   zero num total rotulado simulado — verificavel em
   `execucao-20260803T022952Z.json`. Remedio: EvidencePlane distinguir
   `nao-reportado` de zero. E codigo P0 ratificado;
2. **o payload `sombra` diz "NAO autoriza P2"** em toda evidencia de
   preflight, e continua dizendo depois do ato. A frase segue verdadeira
   sobre a DECLARACAO (quem autoriza e o ato), mas le-se mal ao lado de
   uma corrida P2. Remedio: o payload citar o ato quando ele existir;
3. **o laco de classificacao segue duplicado** entre os runners da P1-A e
   da P1-B (divergencia da P1-B.01, ainda aberta). A P2 **nao criou a
   terceira copia**: consome artefato datado;
4. **`_VIA_GITBASH` segue duplicada**, como a P1-A.3.9 registrou. A P2
   nao tocou;
5. **os quatro guardas abertos** — `P1A-04`, `P1A-19`, `P1A-43`,
   `P1A-53` — seguem abertos. Esta missao nao os tocou.

## 6. O que a P2 NAO estabelece

1. **nao estabelece qualidade de resposta.** Tres corridas triviais
   mediram o CANO, nunca o conteudo. Nenhum juiz-llm foi acionado;
2. **nao estabelece que `kimi -p` responda tarefa.** A franquia estava
   acabada nesta estacao: sabe-se que o argv chega ao provedor, porque o
   erro veio do provedor e nao do parser;
3. **nao estabelece nada sobre claude, google e grok.** Teto SUPERVISED
   intacto; google e grok seguem com zero sondas na historia inteira;
4. **nao estabelece economia de token medida.** Nenhum dos dois CLIs
   reporta contagem. Que despachar para a assinatura poupe token de outro
   canal e **inferencia**, nao medicao desta missao;
5. **nao estabelece deteccao de divergencia de executor.**
   `executor_observado` e sempre `None`: o guarda 0.2.1-9 nao dispara
   para a P2. Sabe-se qual modelo foi RESOLVIDO, nao qual respondeu;
6. **nao estabelece comportamento sob concorrencia** de dois runners P2;
7. **nao estabelece que o ambiente de outra estacao se comporte assim.**
   Medida ESTA estacao, AGORA.

## 7. Criterio de parada da trilha de correcao

O `CLAUDE.md` manda classificar por familia todo achado, e parar a trilha
se uma revisao independente devolver **6+ defeitos novos** ou **4+ na
familia (F)**.

Esta missao **nao e revisao independente** — e a missao que construiu.
Ainda assim, a medicao, para que a proxima revisao a tenha:

| familia | quantos | quais |
|---|---|---|
| **(F)** afirma em vez de exercer | **2** | 4.1 (teto zero declarado e nunca exercido), 4.4 (flag que nao roteava) |
| **(N)** classe que a varredura nao media | **2** | 4.2 (quota real), 4.3 (codificacao) |
| fora de ambas | **1** | 4.5 (mutante malformado — defeito de instrumento, nao de guarda) |

**Nenhum criterio de parada foi disparado.** Mas os dois achados (F)
vieram do mesmo lugar: propriedade economica DECLARADA num artefato e
nunca exercida contra o caminho de operacao. Vale como aviso a proxima
revisao.

## 8. Quem constroi nao certifica

Esta sessao escreveu o ato, o codigo, os testes, as correcoes e este
registro. Ela **nao emite atestado de aprovacao** e nao fecha nenhum
achado por conta propria. A verificacao independente segue **pendente**.
