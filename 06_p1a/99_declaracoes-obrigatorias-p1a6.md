---
id: SSC-DECL-P1A6
titulo: Declaracoes obrigatorias aos dois revisores — preparadas e conferidas na P1-A.6, NAO enviadas
tipo: insumo-de-missao
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-05
---

# Declaracoes obrigatorias — P1-A.6

> **Isto e DADO, nao codigo, e nao foi enviado a ninguem.** A missao
> P1-A.6 fechou em **BLOCKED** no portao de abertura
> (`99_decisao-p1a6.md`): sem tier declarado nao ha trilha
> `SHADOW_ELIGIBLE`, e os dois revisores saem `BLOCKED` do preflight.

## Por que este arquivo existe, e por que NAO e um runner

O instrumento vigente guarda as declaracoes **no fonte do runner**, nunca
no pacote — o pacote e funcao exclusiva de commits, e essa e a correcao
do MAJOR #5. Elas viajam para o descartavel de cada revisor como
`declaracoes-obrigatorias.txt`, com SHA-256 registrado e **os mesmos
bytes para os dois**.

**Um `revisao_p1a6.py` NAO foi escrito, e a omissao e deliberada.** Com o
portao fechado ele nasceria sem nunca ter rodado — que e exatamente a
classe dos achados **7, 10 e 14** da P1-A.3.5: *a copia que ninguem
exercita fica para tras*. Um runner nao exercitado e defeito novo
disfarcado de adiantamento de trabalho.

O que se pode adiantar sem esse risco e o **conteudo**, que e dado
verificavel. Cada item abaixo traz a **fonte no acervo** que o sustenta,
para que a missao seguinte o embarque sem reconferir do zero — e
**reconferir mesmo assim**, porque quem prepara nao certifica.

## 1. Os MAJOR abertos, com o remedio de cada

**Nove, nao oito.** A divergencia esta medida e argumentada em
`99_decisao-p1a6.md` §5, e **a escolha do denominador e do Fundador**.
Enquanto ela nao for feita, declarar aos revisores os **nove**, com a
nota de que `N1` e `P1A4-1` sao o mesmo defeito visto de dois angulos.

| # | Objeto | Familia | Remedio especificado | Fonte |
|---|---|---|---|---|
| **6** | sentinela contornavel por `%`/`.format`/`join`/import dinamico **sem negacao** | (N) | a varredura precisa **negar** o que nao resolve | P1-A.5 §5.2 |
| **N1** | escritor unico existia e **nao estava em uso** | fora de ambas | adotar no caminho operacional — **feito** na P1-A.5 ordem 2, **nao fechado** | P1-A.5 §5.2 |
| **N5** | formas deliberadas de contorno invisiveis e **nao negadas** | (N) | mesmo objeto do MAJOR-6 | P1-A.5 §5.2 |
| `P1A4-1` | `escritor_repositorio.py:adocao` — falha de **integracao** | fora de ambas | idem N1 — **tratado**, nao fechado | P1-A.5 §5.1 |
| `P1A4-2` | `tests/sentinela_antip2.py:resolucao` | **(N)** | construcao nao resolvida = **reprova**, nao = ignora | P1-A.5 §5.1 |
| `P1A4-3` | `08_p2/provedor_assinatura.py:efeito-externo` | **(F)** | declarar o **alcance** do que o recibo vigia — **tratado** na P1-A.5 ordem 3, nao fechado | P1-A.5 §4.1 |
| `P1A4-4` | `08_p2/medidor.py:reprodutibilidade` | fora de ambas | **gravar a evidencia bruta** que falta, ou declarar a classe nao-reproduzivel | P1-A.5 §5.1 |
| `P1A4-5` | `08_p2/runner_p2.py:persistencia` | fora de ambas | mover `relatar` para **depois** da reverificacao e da gravacao | P1-A.5 §5.1 |
| `P1A4-6` | `tests/test_config_real_p1a39.py:acoplamento` | **(F)** | **exercer** o leitor real, nao recontar a tabela — **tratado** na P1-A.5 ordem 3, nao fechado | P1-A.5 §4.2 |

**Declarar junto, sem suavizar:** MAJOR-6, N5 e `P1A4-2` sao **um objeto
so visto de tres angulos** — a sentinela que deixa passar sem negar.
Contam separado pela regra da P1-A.3.6 §9.4, e o remedio e comum.

## 2. ACHADO A — read-only nao restringia o CLI

**Corrigido no mecanismo a partir de `abc75e8`** (*"SSC+ P2.3 [1/3] a
protecao sai do texto e entra no argv, no cwd e na medicao"* — commit
conferido nesta missao), e **ABERTO**: quem corrige nao certifica.

O argv passou de `<codex.exe> exec <tarefa>` para
`<codex.exe> exec --sandbox read-only --cd <descartavel>
--skip-git-repo-check --ephemeral <tarefa>` (`08_p2/99_registro-p23.md`).

**Declarar o limite junto com o conserto:** `--ephemeral` **nao impede
escrita em `CODEX_HOME`**, e isso foi **medido**, nao suposto. A protecao
no argv restringe o alcance; ela nao torna verdadeira a afirmacao
`efeito_externo: nenhum` do recibo — que e precisamente o `P1A4-3`.

## 3. ACHADO C — a receita e a cobertura, com a fracao que incomoda

Receita **versionada desde a P2.4**. Cobertura recontada, medida e
publicada em toda corrida:

| Classe | Cobertura | Fonte |
|---|---|---|
| (a) | **89,7 %** | `08_p2/99_registro-p24.md:94`, `08_p2/README.md:254` |
| (b) | **17,3 %** | `08_p2/99_registro-p24.md:95`, `08_p2/README.md:255` |

**Declarar sem arredondar para cima:** a classe (b) tem **17,3 %**
recontado — o resto e testemunho. `P1A4-4` continua **aberto** e o
remedio e gravar a evidencia bruta que falta.

**Agravante desta missao, que precisa ir aos revisores:** a P1-A.6
**destruiu** o unico lab de P2 que existia
(`08_p2/saidas/labs/20260803T135101Z/`), ao limpar `saidas/labs` sem
copia datada. Com ele foram **1 teste e 5 subtests** — a comparacao mais
forte entre receita e cadeia deixou de ser verificavel, e a perda e
**irreversivel** (`99_decisao-p1a6.md` §4). Isto **piora o `P1A4-4`** e
precisa ser julgado como tal, nao omitido por ser autoinfligido.

## 4. ACHADOS B e D — intocados

| # | Objeto | Situacao |
|---|---|---|
| **B** | `README.md:provedores-produtivos` — o README promete codex e kimi, e o **kimi nunca completou uma corrida** | **intocado** |
| **D** | `README.md:indice-P2` — o indice da raiz omite os registros **P2.1 e P2.2**, que os numeros publicados usam | **intocado** |

## 5. Escritor unico — ADOTADO na P1-A.5, com as tres provas

Um lock para o **repositorio** (`locks/repositorio.lock`), qualquer que
seja o nome da missao; o nome deixa de escolher o arquivo e passa a ser o
**titular** registrado no lease.

As tres provas, como a P1-A.5 §3.4 as registrou: dois **processos reais**;
**cinco pontos de chamada** mais um `main()` real; e o preflight na
capsula. Mutante M4 (atribuicao sem titular): **3 vermelhos**. Segunda
missao de outro nome: **returncode 3**, sem adquirir e sem escrever.

**Exercido de novo nesta missao**, e vale declarar: lease `p1a6-ops`,
fences **9** e **10**, verificado imediatamente antes de cada
persistencia, e **expirado sozinho** apos a morte do renovador — medido,
nao afirmado.

**Nao fechado.** `N1` e `P1A4-1` so fecham por revisor independente.

## 6. Cache fora da arvore, e a porta que NAO foi construida

**P1-A.5.1**: `pytest.ini` (`-p no:cacheprovider`) e `conftest.py` da raiz
(`sys.pycache_prefix`). Medido: **0 mutacoes** no manifesto em quatro
condicoes; reversao vermelha M7 devolve **3** `.pyc` mais **2** do cache
numa corrida que falha — **cinco** ao todo.

**Tres das quatro** classes de mutacao que a contencao acusou na P1-A.4
somem sem porta nenhuma. **A quarta — a sessao editando um fonte — nao e
alcancada por realocacao e continua aberta.**

**A porta esta REGISTRADA e NAO construida**, com o modo de falha que a
desaconselha hoje: morte do processo entre fechar e reverter deixa a
arvore **inescrevivel**, sem reversao automatica, porque a permissao e
estado do sistema de arquivos e sobrevive ao processo. **O PC do Fundador
desligou duas vezes na semana da P1-A.5.1**, e este repositorio ja tem o
precedente exato — a queda que deixou dois mutantes na arvore viva.

**A assimetria, que precisa ir escrita:** mutante esquecido deixa a
arvore **alterada mas funcional**, e a suite o denuncia. Porta esquecida
deixa a arvore **intacta e travada**, e nenhuma suite roda para denunciar
— o instrumento de deteccao morre junto com o acesso.

**E a ressalva:** a porta **impede**, nao **atribui**. Ela nao responde
*"quem escreveu este byte?"*; torna a pergunta irrelevante **dentro** da
janela e a deixa intacta fora dela.

## 7. As nove corridas anteriores rodaram sem fotografia

Nas **nove corridas anteriores a `abc75e8`** nao havia manifesto SHA-256
antes/depois. **Nao se sabe se elas escreveram** na arvore.

Lacuna **historica e irrecuperavel**: nao e propriedade de guarda, e
**nenhum conserto futuro a alcanca**. Declarada como OBS, nao como
achado, e nao se pede aos revisores que a fechem — pede-se que registrem
que a leram.

## 8. O que exigir de cada revisor

1. **Pronunciamento explicito por MAJOR** — fechado ou nao fechado, um a
   um, sem agregado;
2. **se as correcoes introduziram defeito novo**;
3. **CLASSIFICACAO POR FAMILIA** de cada achado — **(F)** afirma em vez
   de exercer; **(N)** classe que a varredura dos 86 guardas nao media;
   ou **fora de ambas**. **Sem ela o criterio de parada (b) nao pode ser
   aferido**, e relatorio que a omita nao serve para decidir a parada.

## 9. O que NAO declarar, porque nao foi medido

- **nada sobre quota.** O preflight devolveu `desconhecida` nos cinco, e
  no portao a quota nao e mensuravel;
- **nada sobre o estado de aprovacao.** O veredito vigente do acervo e
  **REPROVADO** (P1-A.4) e esta missao nao o move;
- **nada como fechado.** A P1-A.5 e a P1-A.5.1 corrigiram; **quem corrige
  nao certifica**.
