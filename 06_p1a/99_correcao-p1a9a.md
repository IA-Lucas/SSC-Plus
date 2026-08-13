# Registro de correcao — P1A9-a (2026-08-12)

> Missao de correcao, experimental e sem autoridade. **Quem corrige nao
> certifica**: este registro e material para revisao independente, e o
> achado `P1A9-a` permanece ABERTO ate que um revisor o feche.

## O achado, como a P1-A.9 o deixou

`test_gitignore_efetivo_p1a39::test_o_diretorio_de_locks_existe_de_fato_nesta_estacao`
dependia de `locks/`, que **nenhum clone carrega**. A suite era verde na
estacao que ja rodou algo e vermelha em maquina nova. Familia: fora de
ambas. Gatilho: imediato, qualquer clone novo.

## O que mudou, e quem mudou

A sessao de 2026-08-11/12 (commit `a818af1`) substituiu o teste por
`test_estado_de_lock_real_criado_agora_fica_ignorado`: a propria prova
**cria** um objeto de runtime (`locks/prova-p1a39-runtime.lease`),
pergunta ao Git pelo efeito (`check-ignore`, a interface real) e remove
o objeto. O resultado deixou de ser propriedade da estacao.

O discriminador que o teste antigo dizia proteger — *"sem objeto, a
propriedade seria verdadeira por ausencia de estado"* — e preservado:
o objeto agora existe **porque o teste o cria**, nao porque uma corrida
anterior o deixou.

Esta sessao (2026-08-12) **nao alterou o teste**: mediu a prova que a
regra do repositorio exige e a registra aqui.

## 1. O teste exerce o caminho que a operacao percorre?

**Sim, e foi medido no caso que ocorre** — clone limpo, sem `locks/`:

| Onde | O que | Resultado |
|---|---|---|
| clone limpo de `a818af1` (scratchpad, `--no-hardlinks`), **sem `locks/`** | arquivo novo | **6 passed, 14 subtests** |
| mesmo clone, versao ANTIGA do teste (de `9ad6db3`) | contraprova | **1 failed** — exatamente `test_o_diretorio_de_locks_existe_de_fato_nesta_estacao` |
| arvore de trabalho desta estacao (com `locks/` vivo) | arquivo novo | 6 passed, 14 subtests |

A contraprova reproduz o achado literal (o `1 failed, 920 passed` do
registro da P1-A.9) e mostra que o instrumento distingue os dois
estados.

## 2. Reversao vermelha, medida

Mutacao aplicada **somente no clone descartavel** — a arvore viva nunca
foi mutada, e por isso `scratchpad/MUTANTE-ATIVO.txt` nao foi usado: o
risco que aquele registro conte (mutante esquecido apos queda) nao
existe quando o mutante vive numa copia que se apaga.

| Mutacao no clone | Resultado do arquivo de teste |
|---|---|
| remover a linha `locks/` do `.gitignore` | **7 failed** (3 testes + 4 subtests), incluindo o teste novo |
| restaurar a linha | 6 passed, 14 subtests |

O guarda prende: reverter a regra que ele protege o poe vermelho.

### Medicao registrada que NAO reproduz, declarada com a razao ao lado

O docstring do arquivo de teste afirma, como medido na P1-A.3.9:
*"com essa linha acrescentada* [`!locks/*.lease`] *o acervo inteiro
fica VERDE e este arquivo fica vermelho"*. **Hoje essa mutacao e
inerte**: o `.gitignore` da epoca (commit `4434bb6`) ja excluia o
diretorio `locks/`, e o Git nao re-inclui arquivo sob diretorio
excluido — `check-ignore` segue devolvendo ignorado, a propriedade nao
quebra e o arquivo segue verde **corretamente**. Medido em 2026-08-12
no clone descartavel: com `!locks/*.lease` acrescentada, 6 passed.
O texto original do docstring fica como esta (e registro da epoca);
a nao-reproducao fica AQUI, classificada **fora de ambas** (registro de
medicao, nao alcance de guarda), para a revisao independente.

## 3. O que o teste NAO cobre, declarado

- ele cria **um** objeto (`.lease`) e exerce a criacao real só para
  ele; `lock`, `fence` e os demais caminhos de runtime sao perguntados
  ao `check-ignore` por caminho, sem criacao;
- ele prova o **efeito da regra**, nao o estado da estacao: nada aqui
  afirma que os locks reais de uma estacao que ja rodou estao integros
  ou corretos — e por desenho, porque depender do estado da estacao era
  o proprio defeito;
- historico continua fora do alcance: arquivo de lock ja commitado
  seguiria rastreado (coberto por outro teste do mesmo arquivo, via
  `ls-files`, mas so para `locks/`);
- as medicoes deste registro foram feitas numa unica plataforma
  (abaixo); clone limpo em outro SO ou outro Git nao foi medido.

## Plataforma da medicao — os quatro campos

| Campo | Valor |
|---|---|
| interpretador | Python 3.14.3 |
| pytest | 9.1.1 |
| `core.autocrlf` | true |
| usuario da estacao | o historico do acervo (8 caracteres, com espaco) — **nao escrito literal**, porque os guardas `ZeroPii` derivam o alvo dele e reprovam o nome em artefato rastreado; declara-se por descricao, como o handoff de 2026-08-09 ja fazia |

Suite de verificacao rapida nesta estacao, apos as medicoes e com a
arvore restaurada: `python scripts/verificar.py --rapido` → **OK, 986
testes, 1 ignorado, 108,0 s** (P0 e prova central incluidos pelo
proprio script).

> **ERRATA (2026-08-12, achado do revisor da P1-A.10, familia F).** O
> parentese acima afirma alcance maior que o exercido: `--rapido`
> roda P0 e P1-A/P2 e **OMITE** prova central e receitas — elas so
> entram na verificacao completa. Os numeros medidos nao mudam; o
> alcance descrito muda. A frase original fica riscada pelo contexto,
> nao apagada, porque apagar esconderia o achado.

## O que fica aberto

- `P1A9-a` so fecha com revisor independente — este registro e o
  insumo, nao o fechamento;
- `P1A9-b` (nenhum teste impoe os quatro campos de plataforma, familia
  **F**) e `P1A9-c` (`18,475` sem instrumento) **nao foram tocados**;
- a nao-reproducao do docstring (§2) e achado novo desta medicao e
  entra na proxima revisao com a classificacao proposta acima.
