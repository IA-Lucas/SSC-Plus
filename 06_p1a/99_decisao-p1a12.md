# P1-A.12 — terceira rodada sobre 6/P1A4-2: os dois revisores recomendam limite permanente

> Registro da missao que despachou a revisao. Quem corrige nao
> certifica; os fechamentos abaixo sao **do revisor**, nao do autor. Os
> DOIS pareceres chegaram na mesma sessao de despacho. **A palavra
> final e do Fundador** — esta missao NAO arbitra.

## O que mudou desde a P1-A.11

A P1-A.11 mediu CONSENSO NAO-FECHADO nos dois revisores para 6/P1A4-2,
com diagnostico preciso: negacao no ponto de decisao so cobria
construtor DIRETO/literal. A arbitragem do Fundador autorizou uma
TERCEIRA tentativa (`99_correcao-p1a11.md`), com a ressalva explicita
de que, se ela tambem residuasse na mesma familia, a pergunta do
proximo ciclo seria se o padrao vira limite PERMANENTE.

Esta missao e esse terceiro ciclo. Pacote: BASE `3ff94e6` (o mesmo
ALVO julgado na P1-A.11) → ALVO `74b9448` (HEAD desta missao), 9
caminhos no diff (4+1 lidos, 4 ancorados, 0 sobra). `sha256` do
pacote: `35aeac10...faf93d`.

## MAJOR-6 (fundido com P1A4-2), pelos dois pareceres

| id | codex | kimi | Consenso |
|---|---|---|---|
| **6/P1A4-2** | NAO-FECHADO | NAO-FECHADO | **NAO-FECHADO por ambos, TERCEIRA vez** |

**Os dois revisores encontraram vetores DIFERENTES que ainda
atravessam** — nenhum dos dois repete o vetor do outro nem o das
rodadas anteriores:

- **codex**: a correcao deliberadamente EXCLUI `decode()` da semente de
  rastreamento de alias (decisao registrada em
  `_semente_de_alias_nao_resolvido`, para evitar a explosao de falsos
  positivos medida no processo). Isso significa que `x =
  payload.decode(); if r == x:` — a COMPOSICAO EXATA dos dois vetores
  que os dois pareceres anteriores nomearam separadamente (decode +
  alias) — continua invisivel. E o mesmo buraco reaparecendo pela
  combinacao dos dois remendos anteriores.
- **kimi**: `variaveis_de_construtor_nao_resolvido` so coleta
  `ast.Assign`/`ast.AnnAssign` com valor direto. Tres formas sintaticas
  comuns escapam, nenhuma declarada como limite: `x += chr(80)`
  (`ast.AugAssign` nao entra na lista de atribuicoes), `x = "".join(p)
  if c else ""` (o valor e `ast.IfExp`, a semente so aceita `ast.Call`
  direto), e desempacotamento `a, b = "t", "".join(p)` (valor
  `ast.Tuple`).

**O padrao, medido em tres rodadas**: cada correcao fecha exatamente os
exemplos apontados na rodada anterior — os testes provam isso, e a
reversao vermelha confirma — e a familia reabre pelo vizinho sintatico
seguinte. Nenhuma das tres rodadas fechou por antecipar o proximo
vizinho.

## CORRECAO (`99_correcao-p1a11.md` como um todo)

- **codex: SUSTENTADA** (com ressalva) — fecha os tres exemplos exatos
  das rodadas anteriores, os testes exercem esses casos diretamente,
  os limites declarados correspondem ao codigo — mas esses MESMOS
  limites sao o que impede o fechamento do id;
- **kimi: NAO-SUSTENTADA** — o mecanismo funciona nos casos exercidos e
  a reversao vermelha e critivel, mas a secao "Limite declarado, o que
  SOBREVIVE" se apresenta como enumerativa e OMITE vizinhos comuns da
  mesma familia (AugAssign, IfExp, tupla) que o proprio kimi encontrou
  "em uma leitura de minutos" — a ressalva generica "outro vizinho nao
  foi buscado" cobre o espirito, nao a enumeracao que o registro
  afirmava.

## PROXIMO-PASSO — os dois convergem, com a MESMA palavra

- **codex**: **LIMITE-PERMANENTE** — "apos a terceira tentativa,
  permanece um desvio trivial na mesma familia... continuar enumerando
  formas sintaticas nao oferece criterio estavel de fechamento e o
  alcance deveria ser assumido como limite permanente, a maneira de
  N5";
- **kimi**: **LIMITE-PERMANENTE** — "heuristica estatica sobre AST nao
  fecha essa classe (sempre havera `getattr(x, "de"+"code")()`, `+=`,
  IfExp, parametro, walrus...). O padrao deve virar limite declarado
  como N5 — a sentinela e deteccao, nunca impedimento — em vez de uma
  quarta tentativa."

**Convergencia independente, por vetores diferentes, na MESMA
recomendacao.** Nenhum dos dois foi instruido a preferir esta resposta
— o prompt perguntou neutro ("vale a pena tentar de novo, ou o padrao
deveria virar limite declarado?").

## Achados novos

**DEFEITO-NOVO, os dois SIM, em OBJETOS DIFERENTES:**

- **codex**: `variaveis_de_construtor_nao_resolvido` marca por NOME,
  insensivel a ORDEM/sobrescrita — `x = "".join(partes); x = "fixo"; if
  resposta == x:` continua classificando `x` como construtor nao
  resolvido mesmo depois de reatribuido a um literal seguro. Risco na
  direcao OPOSTA (falso positivo), nao na direcao que mantem o id
  aberto;
- **kimi**: as tres formas sintaticas do achado principal (AugAssign,
  IfExp, Tuple) — falso NEGATIVO, na mesma familia que mantem o id
  aberto.

**DECLARADO-a** (historico do terceiro ciclo): CONFIRMO pelos dois.

**DECLARADO-b** (as duas tentativas revertidas, 360/7 achados):
DIVIDIDO — **codex NAO-CONFIRMO** (as medicoes aparecem so narradas
pelo autor; o pacote nao contem os mutantes/saidas que permitiriam
conferir); **kimi CONFIRMO** (documentadas de forma consistente no
docstring, no registro e nas declaracoes; fato de processo
auto-reportado, internamente coerente, ainda que nao verificavel por
fora). Divergencia de PADRAO DE VERIFICACAO, nao de fato.

**DECLARADO-c** (`revisao_p1a11.py` fora dos corpora por quase um dia):
CONFIRMO pelos dois; kimi observa que a lacuna fica fechada para a
frente pelos proprios diffs deste pacote.

**Achados adicionais do kimi** (todos AREA JA REVISADA, nenhuma
ESTREIA): `_mapa_de_pais` construido duas vezes por varredura (MINOR,
desempenho); `99_correcao-p1a11.md` repete o vicio "alcance descrito
maior que o exercido" que a P1-A.11 ja tinha nomeado no proprio registro
anterior (MINOR); os cinco testes novos exercem as citacoes EXATAS dos
dois revisores anteriores, conferido palavra a palavra (OBS, verificacao
POSITIVA).

**Achados adicionais do codex**: nenhum alem do DEFEITO-NOVO e do
achado sobre `variaveis_de_construtor_nao_resolvido` ja listados acima
(que ele tambem cataloga como MAJOR em area ja revisada) e um MINOR
sobre `99_correcao-p1a11.md:medicoes-revertidas` em ESTREIA (mesmo
objeto do DECLARADO-b acima, agora como achado formal).

## VEREDITO

**REPROVADO pelos dois.** Nenhuma condicao de aprovacao, com ou sem
ressalvas — os dois leem MAJOR-6 aberto e recomendam, sem terem sido
perguntados na mesma frase, a mesma saida: parar de tentar corrigir por
enumeracao e declarar limite permanente.

## O que isto NAO decide

Esta missao despachou e registrou; nao arbitra. A decisao sobre se
6/P1A4-2 vira limite permanente (como N5) ou se ha uma quarta tentativa
— e, se limite permanente, como ele se registra e se isso muda o
veredito vigente do acervo (REPROVADO desde a P1-A.4) — e do Fundador.

## Plataforma — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao). Ambos os
pareceres com contencao limpa (`mutacoes_fora_do_descartavel: []`);
codex ecoou os hashes declarados (sem ferramenta), kimi computou os
tres com `sha256sum` e todos bateram.
