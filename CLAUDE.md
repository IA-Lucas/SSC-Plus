# SSC+ — instrucoes do repositorio

> Laboratorio experimental. Nada aqui e norma; nada foi promovido ao
> canonico. Este arquivo registra decisoes do Fundador que valem para
> QUALQUER sessao que trabalhe neste repositorio.

## CRITERIO DE PARADA DA TRILHA DE CORRECAO

**Decisao do Fundador, gravada na missao P1-A.3.7.**

A trilha de correcao **PARA** se a proxima revisao independente devolver
qualquer uma destas duas condicoes:

| # | Condicao |
|---|---|
| **(a)** | **SEIS OU MAIS defeitos NOVOS** |
| **(b)** | **QUATRO OU MAIS na familia do MAJOR #3** — guarda que AFIRMA a propriedade em vez de EXERCER a interface real |

**Disparado o criterio:** nao abrir nova missao de correcao. Retornar ao
Fundador com a **medicao** e a **classificacao por familia**.

**Fundamento, medido e nao suposto:** tres ciclos de correcao com saldo
**zero** nos seis MAJOR originais; e, na ultima rodada (P1-A.3.6),
**quatro de seis** achados novos eram da mesma familia.

### Classificacao por familia e OBRIGATORIA

Todo relatorio de revisao deste repositorio **precisa** classificar cada
achado por familia. **Sem ela o criterio (b) nao pode ser aferido**, e um
relatorio que a omita nao serve para decidir a parada — o que equivale a
manter a trilha aberta por falta de medicao, que e exatamente o que este
criterio existe para impedir.

As familias em uso, na definicao do atestado da P1-A.3.6 (§9.2):

- **(F)** mesma familia do MAJOR #3 — o guarda **afirma** a propriedade
  (docstring, rotulo, lista) em vez de **exercer** a interface real;
- **(N)** classe que a varredura dos 86 guardas **nao media** — o eixo
  daquela varredura era alcance de linha, e ha propriedades que ele nao
  podia ver;
- **fora de ambas** — quando o objeto nao e guarda do acervo (por
  exemplo, defeito de composicao de um pacote de revisao).

## REGRA DE PROVA (endurecida na P1-A.3.7)

Toda correcao neste repositorio exige, por escrito:

1. **teste que exerce o CASO QUE OCORRE em operacao**, nunca o vizinho
   dele — e a resposta explicita a pergunta *"o teste exerce o caminho
   que a operacao percorre, ou um vizinho?"*;
2. **reversao vermelha medida** — reverter o guarda e registrar quantos
   testes ficam vermelhos;
3. **declaracao explicita do que o teste NAO cobre**.

Quatro coisas que **nao** contam como prova, cada uma aprendida num
achado real:

- **alcance de linha nao prova exercicio** (achado N1: o guarda saiu
  `EXERCE` por alcance, e o caso exercido nao era o que ocorre);
- **primitiva corrigida nao cobre ponto de chamada** (achado N4);
- **principio nao cobre caso** (achado N3: havia teste contra a palavra
  "sandbox" e nenhum contra a palavra "integral");
- **escopo nao cobre explorabilidade** (achado N5: o guarda era
  contornavel de proposito).

## QUEM CORRIGE NAO CERTIFICA

Nenhuma missao fecha o proprio conserto. Um achado so fecha quando um
**revisor independente** diz que fechou. Missao de correcao registra o
que fez e declara os limites; nao emite atestado de aprovacao.
