---
id: SSC-REG-P24-99
titulo: Registro da missao SSC+ P2.4 — a receita das medicoes no repositorio
tipo: registro-experimental (NAO e atestado)
versao: 1.0.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Registro — Missao SSC+ P2.4

> Laboratorio experimental. Registro **aditivo**: nenhum documento
> anterior foi aberto para escrita. As medicoes publicadas pela P2.1 e
> pela P2.2 **nao foram tocadas** — esta missao produz a receita que as
> reproduz, e uma receita que editasse o publicado nao reproduziria nada.
>
> **Este documento NAO e atestado de aprovacao.** O achado C segue
> **ABERTO**: quem corrige nao fecha o proprio conserto.

## 0. Medicao de partida e de fechamento

| Item | Abertura | Fechamento |
|---|---|---|
| HEAD | `8ffcceb` | este commit |
| `git status --porcelain` | vazio | vazio |
| `scratchpad/MUTANTE-ATIVO.txt` | **ausente** (lido antes de qualquer medicao) | ausente (apagado apos reverter o controle positivo) |
| Suite `05_p0/tests` | **344/344 OK** | **344/344 OK** |
| Suite `06_p1a/tests` | **867/867 OK** | **894/894 OK** (867 + 27) |
| `05_p0/cenarios/prova_central.py` | OK, 18 assercoes / 20 eventos | idem |
| Escritor unico | — | `p24-ops`, fence **1**, pid 65824 |
| Chamadas **pagas** de modelo nesta missao | — | **ZERO** |
| Declaracao de tier | **nao renovada** | **nao renovada** |

## 1. O comando (ORDEM 1)

```powershell
python 08_p2/medidor.py --todas
python 08_p2/medidor.py --receita p22-a
python 08_p2/medidor.py --todas --json saida.json
```

Codigo de saida **1** quando qualquer corrida diverge do publicado. A
receita nao existe para dizer "confere": existe para que a divergencia
apareca sozinha, sem depender de alguem conferir a olho.

Cinco receitas versionadas em [`08_p2/receitas/`](receitas/), uma por
corrida publicada. Cada insumo declara ORIGEM — `arquivo` (recontado do
disco), `recibo` (recontado da evidencia versionada) ou `testemunho`
(numero publicado sem objeto que o sustente).

## 2. O que e reproduzivel, medido antes de escrever codigo

| insumo | reproduzivel? | como |
|---|---|---|
| turno interno | **SIM**, nas 4 corridas que tem | `eventlog.py`, `execution.py` e `estados.py` estao versionados e **continuam com o tamanho publicado** (6.184, 13.508 e 2.987 B) |
| resposta da assinatura | **SIM em 4 de 5** | campo `saida` de `08_p2/evidencias/execucao-*.json`, casado por `sessao_id` |
| prompt | **SIM em 1 de 5** | recuperado do unico lab sobrevivente e versionado em `08_p2/receitas/prompt-p22-c.txt` |
| resposta do canal alternativo | **NAO**, em nenhuma | nunca foi gravada: o canal alternativo nao tem EventLog nem recibo aqui |

**A conferencia que autorizou usar o recibo como fonte.** O campo `saida`
do recibo passa por `redigir` antes de ser gravado, e usar um texto
redigido para recontar bytes exigiria saber que a redacao nao mexeu em
nada. Medido, nao suposto: para a corrida `c-repeticao`, cujo lab
sobreviveu, o campo `saida` do recibo e **byte a byte igual** ao artefato
do CAS (466 B nos dois lados). Ha teste que compara os dois caminhos
inteiros — cadeia verificada contra receita — e ele fica `skip`, alto,
onde o lab nao existir.

**A corrida (c) da P2.2 nao tem recibo.** A sessao
`dd4567c703d3497fae7269ebfd5d1ca7` **nao aparece** em
`08_p2/evidencias/`. Foi ela que caiu no `UnicodeEncodeError` do console
medido na propria P2.2: o attempt deu **sucesso**, a franquia foi gasta,
e o artefato de registro nunca existiu. A resposta dela e **testemunho**,
e a receita declara isso em vez de inventar um texto que pesasse 438 B.

**Uma consistencia observada, que NAO e recuperacao.** O registro da P2.2
afirma que os tres prompts diferem so no nome do arquivo. Trocando
`estados.py` por `execution.py` no prompt recuperado, o tamanho cai
exatamente em 226 B — o publicado da classe (a). E consistente com o
registro e **nao prova o texto**: coincidencia de tamanho nao e
recuperacao, e por isso o prompt da classe (a) permanece testemunho.

## 3. O comando reproduz os numeros publicados (ORDEM 2)

Corrida de `python 08_p2/medidor.py --todas`, sem nenhum ajuste ao
comando para caber no publicado:

| receita | razao recalculada | razao publicada | residual recalc. | residual publ. | cobertura recontada |
|---|---|---|---|---|---|
| `p21` | **8,776** | 8,776 | **872** | 872 | 82,3 % |
| `p22-a` | **19,558** | 19,558 | **773** | 773 | 89,7 % |
| `p22-b` | **2,766** | 2,766 | **504** | 504 | 17,3 % |
| `p22-c` | **6,737** | 6,737 | **662** | 662 | 65,6 % |
| `p22-c-repeticao` | **6,464** | 6,464 | **690** | 690 | 74,6 % |

Seis campos conferidos por receita (razao, residual, poupanca,
alternativo, assinatura e saida da assinatura): **30 de 30 conferem**.
`5 receita(s); 0 divergente(s)`, codigo de saida 0.

No conjunto: **28.057 B recontados do repositorio contra 7.409 B de
testemunho** — 79,1 % recontado.

**A cobertura importa mais que o "confere".** A classe (b) tem **17,3 %**
recontado: sem turno interno, os dois maiores termos dela — prompt e
resposta do canal alternativo — sao testemunho. Dizer que a (b) "confere"
sem dizer isso seria a testemunha se conferindo, que e a familia (F). O
comando publica a fracao em toda corrida, e ha teste exigindo que
nenhuma receita tenha cobertura zero.

## 4. Controle positivo (ORDEM 3)

Receita que devolve o mesmo numero com insumo diferente nao reproduz
nada — mede constante. Duas formas, porque provam coisas diferentes.

### 4.1 Sobre o arquivo VIVO do repositorio, com mutante registrado

Um unico byte (`#`) acrescentado a `05_p0/ssc_p0/estados.py`
(2.987 → 2.988 B), registrado em `scratchpad/MUTANTE-ATIVO.txt` antes de
aplicar:

| receita | antes | com o mutante |
|---|---|---|
| `p21` | 8,776 CONFERE | 8,776 **CONFERE** (nao usa `estados.py`) |
| `p22-a` | 19,558 CONFERE | 19,558 **CONFERE** (nao usa `estados.py`) |
| `p22-b` | 2,766 CONFERE | 2,766 **CONFERE** (nao tem turno interno) |
| `p22-c` | 6,737 CONFERE | **6,739 DIVERGE** |
| `p22-c-repeticao` | 6,464 CONFERE | **6,465 DIVERGE** |

`5 receita(s); 2 divergente(s)`, codigo de saida **1**. Revertido em
seguida; suite verde de novo; registro do mutante apagado.

As tres que **nao** se moveram sao metade da prova: um comando que
divergisse em tudo ao mudar qualquer coisa nao estaria lendo insumo
nenhum — estaria reagindo ao relogio ou ao acaso.

### 4.2 Na suite, com copias em diretorio temporario

Quatro controles permanentes (`ControlePositivo`), sobre copias para nao
mutar o acervo a cada corrida da suite:

- turno interno maior **move a razao** e faz a conferencia falhar;
- **um byte** a mais ja aparece no total (4.461 em vez de 4.460): se so
  uma mudanca grande movesse o numero, a receita estaria arredondando o
  insumo em vez de conta-lo;
- resposta da assinatura diferente **move o residual**, exatamente pelo
  numero de bytes acrescentados;
- prompt diferente **move os DOIS lados** — ele e entrada da assinatura e
  entrada do canal alternativo, e a corrida real o paga duas vezes.

## 5. O guarda que impede o achado C de voltar

`test_toda_medicao_publicada_TEM_receita` varre
`08_p2/evidencias/medicao-*.json` e exige receita para cada uma.
Publicar numero novo sem a receita que o produz deixa a suite
**vermelha**. Sem ele o defeito voltaria na proxima medicao — que e
exatamente como ele apareceu.

## 6. O que continua NAO REPRODUZIVEL

- **as respostas do canal alternativo**, nas cinco corridas (1.236,
  1.384, 1.181, 1.249 e 1.249 B). Elas nunca foram gravadas; o canal
  alternativo nao tem EventLog nem recibo neste repositorio. Sao
  **testemunho**, e um revisor so pode aceita-las ou recusa-las;
- **os prompts de quatro das cinco corridas** (233, 226, 213 e 224 B da
  primeira (c)). Morreram com os labs — `08_p2/saidas/` nao e versionado
  porque carrega saida crua de modelo, e as missoes seguintes limpam
  `labs/` antes de cada corrida;
- **a resposta da assinatura da corrida (c)** (438 B), pela ausencia de
  recibo descrita no §2;
- **as nove corridas da P2.0/P2.1/P2.2 nao tem fotografia de antes e
  depois** — limite herdado, declarado na P2.3 e nao alterado aqui;
- **corrida com fallback nao e reproduzivel por recibo.** O recibo guarda
  so a saida final; com duas tentativas a receita **levanta** em vez de
  sub-contar. As cinco publicadas tem uma tentativa so;
- **o lab que sobreviveu nao e insumo da receita.** Ele nao e versionado:
  serve para a conferencia extra do §2 nesta estacao, e o teste que o usa
  fica `skip` em qualquer outra.

## 7. Classificacao por familia

Obrigatoria pelo `CLAUDE.md` da raiz. Esta missao **nao produziu
achados** — corrige um:

| achado | familia | estado |
|---|---|---|
| **C** | fora de ambas | **receita no repositorio, NAO fechado**: falta revisao independente |
| A | (F) | corrigido no mecanismo na P2.3, **segue aberto** |
| B, D | fora de ambas | **intocados**, por ordem expressa |

## 8. O que esta missao NAO e

Nao e revisao independente e nao e atestado. Ela nao prova que os numeros
publicados estao **certos**: prova que sao **reproduziveis** a partir do
que o repositorio guarda, e diz, corrida a corrida, quanto disso e
recontagem e quanto e testemunho. O achado C permanece **ABERTO** ate que
um revisor que nao escreveu este codigo diga que fechou.
