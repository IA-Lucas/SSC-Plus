"""Bytecode compilado FORA da arvore vigiada — SSC+ P1-A.5.1, ordem 2.

A outra metade do `pytest.ini`, e pela mesma razao medida: das quatro
mutacoes que a contencao acusou contra a propria sessao na P1-A.4, DUAS
eram `__pycache__/*.pyc` reescritos porque a sessao havia tocado um
fonte. Nao sao escrita do operador nem do revisor: sao subproduto do
interpretador, dentro da arvore que o manifesto SHA-256 fotografa.

`sys.pycache_prefix` manda o interpretador gravar o bytecode noutro
lugar. Ele vale para os modulos importados DEPOIS de ser atribuido — e
este `conftest.py` da raiz e carregado pelo pytest antes de qualquer
modulo de teste ou modulo do acervo, que sao exatamente os que apareciam
no manifesto. Medido, nao suposto: com esta linha, `contencao.mutacoes`
devolve lista VAZIA depois de tocar um fonte e rodar a suite; sem ela,
devolve o `.pyc`.

O DESTINO E CALCULADO EM TEMPO DE EXECUCAO, e isso e parte do conserto:
escrever um caminho absoluto aqui gravaria o nome do usuario local num
arquivo versionado — o oposto do que a redacao de PII do acervo faz. O
diretorio temporario do sistema e perguntado ao SO, nunca fixado.

O QUE ISTO NAO FAZ, declarado:
- **nao e a porta.** A quarta mutacao da P1-A.4 — a sessao editando
  `test_redacao_operacao_p1a39.py` enquanto o codex lia o pacote — nao e
  subproduto e nao e alcancada por realocacao nenhuma. Ela continua
  aberta, com dono e gatilho em `06_p1a/99_decisao-p1a51.md` §3;
- **nao muda politica, nem guarda, nem criterio.** O bytecode e cache: o
  fonte e a verdade, e nada no acervo le `.pyc`;
- **nao alcanca processo que nao passe por aqui.** Um `python` invocado
  fora do pytest volta a compilar dentro da arvore, e isso e limite do
  mecanismo, nao propriedade dele.
"""

import os
import sys
import tempfile

sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "ssc-plus-pycache")
