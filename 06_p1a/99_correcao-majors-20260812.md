# Correcao dos MAJOR abertos — 2026-08-12

> Missao de correcao autorizada pelo Fundador em 2026-08-12 ("pode
> atacar os majors e corrigi-los"). Experimental e sem autoridade:
> **quem corrige nao certifica** — cada item abaixo so fecha por revisor
> independente. Este registro e o insumo da revisao.

## O mapa dos nove, e o que esta missao fez com cada um

| MAJOR | Estado antes | O que esta missao fez |
|---|---|---|
| **6** | ABERTO, INTOCADO | **corrigido** — negacao de construcao nao resolvida (§1) |
| **N5** | ABERTO, INTOCADO | **corrigido** — mesmo objeto do 6 (§1) |
| **P1A4-2** | ABERTO | **corrigido** — mesmo objeto do 6 (§1) |
| **P1A4-4** | ABERTO, agravado pela P1-A.6 | **corrigido no mecanismo** (§2) |
| **P1A4-5** | ABERTO, INTOCADO | **verificado como ja tratado** pelo hardening de 2026-08-11 (§3) |
| **N1 / P1A4-1** | TRATADOS na P1-A.5 | nada — aguardam revisor |
| **P1A4-3** | TRATADO na P1-A.5 | nada — aguarda revisor |
| **P1A4-6** | TRATADO na P1-A.5 | nada — aguarda revisor |

## §1 — MAJOR-6 / N5 / P1A4-2: construcao nao resolvida vira NEGACAO

**O defeito**, na voz do revisor: *"%/.format/join e imports dinamicos
atravessam sem negacao; remedio: construcao nao resolvida = REPROVA,
nao = ignora"*. Medido nesta missao: o dobrador da sentinela ja
recusava essas formas, mas a recusa virava silencio — e **o proprio
docstring afirmava a negacao que codigo nenhum fazia** (familia F
dentro do remedio declarado).

**A correcao** (`sentinela_antip2.py`): `construcoes_nao_resolvidas`
nega `%`, concatenacao nao dobravel, f-string interpolada, `.format` e
`.join` **quando carregam fragmento do vocabulario** (portao que impede
a negacao de inundar o repositorio), e **todo import dinamico**
(`import_module`/`__import__`), com ou sem fragmento. Reconhecimento
NOMINAL (`NAO_RESOLVIDOS_RECONHECIDOS`) para os dois unicos achados
reais — ambos em instrumentos congelados de missoes ja julgadas — no
mesmo desenho da emenda P2: **migra de campo visivel, nunca some**.

**Prova** (`test_sentinela_negacao_major6.py`): as sete formas nomeadas
negadas contra violador sintetico; string dinamica sem vocabulario
continua limpa; a lista declarada casa exatamente com a varredura real
(item morto reprova). **Reversao vermelha por ramo**, em clone
descartavel:

| Mutante | Guarda |
|---|---|
| sem `%` | 2 failed |
| sem concatenacao | 2 failed |
| sem f-string | 2 failed |
| sem import dinamico | 3 failed |
| sem format/join | 2 failed |
| negacao inteira desligada | **9 failed** |
| controle restaurado | verde |

**Limite declarado:** construcao SEM fragmento nenhum do vocabulario
(chr(), base64, dado externo) continua invisivel — negacao sem o portao
acusaria milhares de linhas legitimas e enterraria o achado real. N5
("formas ainda invisiveis") fica REDUZIDO, nao extinto, e o revisor
julga se o residuo fecha o achado.

## §2 — P1A4-4: a evidencia bruta sai do lab

**O defeito**: a receita recompoe numeros com insumos testemunhais; a
evidencia bruta vivia so no lab (runtime ignorado pelo Git), e a P1-A.6
provou que lab morre.

**A correcao** (`medidor.py`, `runner_p2.py`): `exportar_bruto` le da
cadeia verificada (a MESMA `EvidencePlane` da medicao) e grava, em
diretorio versionavel (`08_p2/evidencias/brutos/<wu>/`): o conteudo
**redigido** de entrada e de cada saida, e um `manifesto.json` com
sha256 e tamanhos do original E do redigido, delta declarado. O runner
de medicao exporta com a **entrada real** (a cadeia trunca em 4.000
chars) antes de fechar o lab. A receita ganha origem **`bruto`**:
reconta o objeto redigido com hash conferido — adulteracao reprova.

**Prova** (`test_p1a44_evidencia_bruta.py`, 7 testes): corrida real do
runner com sensor falso; o export nao carrega o usuario da estacao
(guardas ZeroPii exercidos com o usuario DENTRO da resposta do sensor);
hash do manifesto = hash do arquivo; entrada exportada e a real.
**Reversao vermelha**: sem redacao → 1 failed (o teste de PII); sem
conferencia de hash → 1 failed (adulteracao passaria); sem export → 7
failed. Controle verde.

**Limites declarados:**
- o original nao se recupera do export: tamanhos originais sao
  DECLARACAO do manifesto, com o delta ao lado; o que se reconta e o
  objeto redigido;
- o fluxo controlado NAO exporta (so o caminho de medicao) — ausencia
  declarada;
- as corridas HISTORICAS (p21, p22-a/b/c) continuam testemunhais: o lab
  delas morreu e nenhum mecanismo novo ressuscita evidencia destruida.
  O mecanismo vale da proxima corrida em diante.

## §3 — P1A4-5: ja tratado, e o mapeamento que faltava

O remedio do P1A4-5 era *"mover `relatar` para DEPOIS da gravacao"*. O
hardening de 2026-08-11 (prioridade 4, `99_hardening-prioridades`)
implementou exatamente isso — `publicar_recibo` grava atomico e SO
depois relata, com teste que faz o relator levantar apos a escrita
(`test_recibo_ja_existe_se_o_relato_falhar`). O documento do hardening
**nao mapeava** a correcao ao MAJOR; este registro faz o mapeamento, e
o revisor julga o fechamento com os dois documentos na mao.

## Plataforma das medicoes — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
`verificar.py --rapido`: OK apos cada uma das duas correcoes.
