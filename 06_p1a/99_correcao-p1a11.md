# Correcao de 6/P1A4-2 — SSC+ P1-A.11 (2026-08-14)

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica: o achado so fecha quando um revisor independente disser
> que fechou. Autorizada pela arbitragem do Fundador em
> `99_decisao-p1a11.md` ("ARBITRAGEM DO FUNDADOR", 2026-08-13) — o
> TERCEIRO ciclo sobre a mesma familia de defeito, declarado como tal
> na propria arbitragem.

## O residuo, na forma que os dois revisores da P1-A.11 mediram

`comparacoes_nao_resolvidas` (06_p1a/tests/sentinela_antip2.py) so
reconhecia construtor textual **DIRETO** no ponto de comparacao. Dois
angulos, dois revisores independentes, mesmo defeito:

- **codex**: `x = "".join(partes); if resposta == x:` — construtor
  atribuido a uma VARIAVEL antes da comparacao continuava invisivel;
- **kimi**: `if r == payload.decode():` e
  `if r == base64.b64decode(dado).decode():` — `.decode()` so era
  reconhecido sobre receptor `ast.Constant` (literal); receptor NOME ou
  CHAMADA atravessava.

## O que fecha

1. `_construtor_direto_nao_resolvido`: `.decode()` deixa de exigir
   receptor literal — cobre os dois exemplos do kimi;
2. `variaveis_de_construtor_nao_resolvido` (nova): ponto fixo, por
   ESCOPO de funcao, que marca nomes atribuidos a partir de `chr()` ou
   `.join()`/`.format()` sobre receptor literal (ou de outro nome ja
   marcado) — cobre o exemplo do codex;
3. `comparacoes_nao_resolvidas` consulta as duas: construtor DIRETO no
   proprio lado da comparacao, OU o lado ser um NOME marcado no MESMO
   escopo.

## DUAS TENTATIVAS MAIS AMPLAS, DUAS REVERTIDAS POR MEDICAO

A regra deste acervo e medir antes de ligar. As duas primeiras versoes
desta correcao mediram mal, e o registro fica porque o processo de
errar e corrigir e prova tanto quanto o resultado final:

1. **Rastrear alias por ARQUIVO INTEIRO, com QUALQUER construtor
   (incluindo BinOp/JoinedStr) como semente**: `python -c
   "import sentinela_antip2 as s; s.varrer('.', ...)"` contra o
   acervo real devolveu **360 achados**. Causa: f-string com QUALQUER
   variavel interpolada (`f"{os.sep}ssc_p0{os.sep}"`, onipresente em
   mensagem de erro) virava semente, e a propagacao por arquivo
   inteiro (sem nocao de escopo) espalhava a marca para toda
   comparacao POSTERIOR contra o mesmo nome, em qualquer funcao.
2. **Remover BinOp/JoinedStr da semente, mas manter `decode()` como
   semente de alias e o rastreamento por ARQUIVO**: caiu para
   **7 achados**. Dois tipos de causa, ambos genuinos: (a)
   `saida.decode("utf-8", "replace")` seguido de checar substring — o
   padrao mais comum de processar saida de subprocesso/arquivo em
   teste, sem nenhuma relacao com o vocabulario do veredito; (b)
   PARAMETROS HOMONIMOS de funcoes diferentes no MESMO arquivo
   (`alvos`, `valor`, `texto`) colidindo porque o rastreamento nao
   respeitava fronteira de funcao — um `", ".join(...)` legitimo numa
   funcao marcava o parametro de OUTRA funcao sem relacao nenhuma.

A versao final (i) tira `decode()` da semente de alias — continua
ampliado no construtor DIRETO, so nao propaga por variavel — e (ii)
torna o rastreamento de alias **por escopo de funcao**, nao por
arquivo. Medido depois das duas correcoes: **ZERO achados novos**
contra o acervo real (`nao_resolvidos: []`; os dois
`nao_resolvidos_reconhecidos` sao os instrumentos congelados de
sempre, inalterados).

**Por que este registro importa tanto quanto o codigo**: as duas
tentativas revertidas nao sao rascunho descartado — sao a evidencia de
que o limite final (`decode()` nao semeia; alias e por escopo) nao foi
escolhido por gosto, foi medido contra o fracasso das alternativas
mais amplas.

## Reversao vermelha, medida

Mutante: `git stash` de `06_p1a/tests/sentinela_antip2.py` (reverte
para o HEAD pre-P1-A.11), registrado em `scratchpad/MUTANTE-ATIVO.txt`
antes de aplicar, apagado depois de `git stash pop` e suite verde de
novo.

Suite `test_sentinela_negacao_major6.py::
ComparacaoContraAliasOuDecodeNaoLiteralEhNegada` (5 testes, cada um
exercendo o CASO QUE OCORRE — os exemplos EXATOS citados pelos dois
revisores, nao vizinhos):

| Teste | Com o fix | Sem o fix (mutante) |
|---|---|---|
| `test_construtor_atribuido_a_variavel_e_negado` | passa | **falha** |
| `test_decode_sobre_nome_nao_literal_e_negado` | passa | **falha** |
| `test_base64_encadeado_com_decode_e_negado` | passa | **falha** |
| `test_parametro_homonimo_em_funcao_diferente_fica_limpo` | passa | passa (prova ausencia de falso positivo, nao depende do fix) |
| `test_decode_isolado_nao_semeia_alias` | passa | passa (idem) |

**3 failed, 8 passed** com o mutante (suite inteira do arquivo,
11 testes) — exatamente os tres que exercem o fechamento, nem mais nem
menos. Suite volta a **11 passed** com o fix restaurado.

## O QUE ESTES TESTES NAO COBREM, declarado

- `test_parametro_homonimo_em_funcao_diferente_fica_limpo` e
  `test_decode_isolado_nao_semeia_alias` provam AUSENCIA de falso
  positivo NOS DOIS CASOS MEDIDOS; nao provam ausencia de falso
  positivo em geral — sao os dois vizinhos que a tentativa anterior
  mediu errado, nao uma varredura do espaco inteiro de nomes genericos;
  o corpus real (acervo inteiro, `verificar.py --rapido`) e quem
  sustenta a alegacao geral: zero achado novo, medido, nao suposto;
- a varredura do acervo real que mediu ZERO achado novo cobre o
  ESTADO ATUAL do acervo, no COMMIT desta missao — nao e garantia
  permanente; codigo novo pode introduzir um padrao que o alias por
  escopo ainda confunda entre duas funcoes com o MESMO nome de
  variavel dentro do MESMO escopo aninhado (closure), caso que os
  testes atuais nao exercem.

## Limite declarado, o que SOBREVIVE a esta correcao

O MESMO que a P1-A.10 ja declarava, mais os que esta correcao mediu e
nao resolveu:

1. decisao sem `ast.Compare` — despacho por dict de funcoes indexado
   pela string construida — continua fora do alcance;
2. `join()`/`format()` continuam so sobre receptor LITERAL — ampliar
   colide com `os.path.join` (medido: falso positivo real em
   `contencao.py:232`, revertido);
3. construtor aninhado como ARGUMENTO de uma chamada NAO relacionada ao
   comparando (`subprocess.run([...], f"{BASE}:{rel}")` cujo
   `.returncode` e comparado) continua fora do alcance — tentativa de
   caminhar a subarvore inteira do comparando pegou ZERO caso novo
   genuino e arrastou 3 falsos positivos do proprio acervo
   (`pacote_p1a36.py` duas vezes, `preflight/adaptadores.py` uma vez),
   revertida;
4. a passagem de PARAMETRO entre funcoes nao propaga a marca de
   variavel nao resolvida; funcao ANINHADA (closure) tem escopo
   proprio e nao herda a marca de quem a declara;
5. atribuicao por `:=` (walrus) dentro da propria comparacao nao entra
   no rastreamento de variaveis.

## O que isto NAO fecha

A arbitragem do Fundador autorizou a TENTATIVA, nao prometeu
fechamento — quem corrige nao certifica. Os limites (1)-(3) acima sao
a MESMA classe de contorno que motivou o residuo original (decisao sem
`ast.Compare`; construtor fora do alcance sintatico reconhecido), so
que agora com o alcance sintatico maior. Se um proximo revisor
encontrar OUTRO vizinho — por exemplo, `getattr(x, "de" + "code")()`
para escapar do nome literal `decode` — este registro declara que ele
nao foi buscado, nao que foi fechado.

## Plataforma — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
`scripts/verificar.py --rapido`: `VERIFICACAO SSC+: OK`, rc=0,
1020 testes, 1 skip (P2 fechada por desenho).
