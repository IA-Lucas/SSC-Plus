---
titulo: DECLARACAO MORTA — familia propria, medida e nao corrigida (SSC+ P1-A.3.9)
data: 2026-08-02
tipo: registro (NAO e missao, NAO e atestado)
evidencia: 06_p1a/evidencias/p1a39-declaracoes-mortas.json
---

# Declaracao morta

## 1. A familia, e por que nao e "guarda solto"

A trilha das listas soltas encontrou, ao corrigir `ESTADOS_ATTEMPT`
(`[17/N]`) e `estados._NOMES` (`[19/N]`), um defeito que **nao e** o que
a varredura procurava. As duas nao eram listas sem teste:

- **`contratos.ESTADOS_ATTEMPT`** — nao ha um unico
  `_enum(..., ESTADOS_ATTEMPT, ...)`, nem leitura dela em `estados.py`
  ou `kernel.py`. A maquina real e `estados.ATTEMPT` mais
  `ATTEMPT_RETOMADA`;
- **`estados._NOMES`** — nao existe **nenhum** `_NOMES[...]` fora da
  linha que o define.

A distincao importa porque muda o remedio:

| | guarda solto | **declaracao morta** |
|---|---|---|
| onde vive | **no** caminho de operacao | **fora** de qualquer caminho |
| defeito | existe e nao e exercido | nao existe como comportamento |
| quem engana | quem confia na suite | **quem le o codigo** |
| remedio | exercer o consumidor | **apagar ou ligar** |

O dano proprio da declaracao morta e de LEITURA: alguem abre
`contratos.py`, ve o enum dos estados do attempt e conclui que ha um
enum governando o ciclo de vida. Nao ha. E uma afirmacao sobre o sistema
que o sistema nao cumpre — e a mesma raiz do MAJOR #3, deslocada do teste
para o codigo.

**Prende-las foi correto e nao resolve o defeito de fundo.** As duas
estao presas desde `[17/N]` e `[19/N]`: divergencia deixou de ser
silenciosa. Nenhuma das duas passou a governar coisa alguma.

## 2. A varredura: quantas existem

Criterio: atribuicao de MODULO em arquivo de **producao** cujo nome nunca
aparece como leitura em nenhum arquivo de producao — nem no proprio
modulo. **Consumo apenas por teste conta como morta em producao**, que e
exatamente o caso das duas ja conhecidas.

Alcance: 46 arquivos de producao (`05_p0/ssc_p0`, `05_p0/cenarios`,
`06_p1a`, `06_p1a/preflight`, `06_p1a/evidencias`, `07_p1b`), 187
declaracoes de modulo.

**Vivas: 180. MORTAS: 7.**

| arquivo:linha | nome | consumo em TESTE |
|---|---|---|
| `05_p0/ssc_p0/contratos.py:24` | `ESTADOS_ATTEMPT` | preso na `[17/N]` |
| `05_p0/ssc_p0/estados.py:63` | `_NOMES` | preso na `[19/N]` |
| `06_p1a/evidencias/contencao.py:112` | `FLAGS_DE_AUTO_APROVACAO` | 3 arquivos |
| `06_p1a/evidencias/contencao.py:118` | `FLAGS_INCOMPATIVEIS_COM_PROMPT` | 2 arquivos |
| `06_p1a/evidencias/contencao.py:126` | `PREFIXO_ERRO_DE_ARGUMENTO` | **nenhum** |
| `06_p1a/evidencias/contencao.py:127` | `MARCADOR_ARGV_ACEITO` | 1 arquivo |
| `06_p1a/evidencias/contencao.py:357` | `PALAVRAS_DE_ALCANCE_TOTAL` | 1 arquivo |

**Cinco das sete estao no mesmo arquivo** — `evidencias/contencao.py`, a
camada de contencao do argv. Concentracao nao e coincidencia e merece
olhar proprio: e o modulo onde a P1-A.3.2/3.3 descobriu o MAJOR #3.

**Uma e morta em TODO lugar**: `PREFIXO_ERRO_DE_ARGUMENTO` nao e lida por
producao **nem por teste**. E a unica das sete que nenhuma linha do
repositorio consome.

**NADA FOI CORRIGIDO.** Por ordem do ato: registrar quantas, sem missao.

## 3. Limites desta contagem, declarados

- **consumo dinamico nao e visto**: `getattr(modulo, nome)` com nome
  montado em tempo de execucao passaria por morta. Mitigado em parte —
  o varredor conta strings literais como leitura —, nunca resolvido;
- **so atribuicoes de MODULO com valor literal ou construido**;
  funcoes e classes mortas nao entram nesta contagem;
- **producao e definida por diretorio**, e `06_p1a/evidencias/` foi
  contado como producao porque `contencao.py` e importado pelos runners.
  Quem discordar desse enquadramento le cinco das sete de outro jeito;
- **morta nao e sinonimo de errada.** Uma declaracao pode existir por
  contrato documental deliberado. A medicao diz que ninguem consome, e
  jamais que deva ser apagada;
- **a contagem e desta sessao, que tambem corrige.** Quem corrige nao
  certifica.

## 4. Pendencias MANTIDAS ABERTAS, sem acao

1. **O teste tautologico da `[9/N]`** —
   `test_config_real_p1a39.py:197`, `test_host_payg_plantado_em_cada_
   grafia_e_acusado` — itera `_CHAVES_ENDPOINT` para provar
   `_CHAVES_ENDPOINT`. Segue no acervo, **verde e inutil como vinculo**.
   A `[18/N]` acrescentou corpus autoral ao lado; nao removeu este.
2. **`_VIA_GITBASH` segue duplicada** em `preflight_capsula` e
   `preflight_atual`. Os wrappers foram alinhados na `[22/N]`; a
   constante nao foi unificada, por ordem. Remedio: implementacao unica
   de `_sensor_de`, no desenho de `leitor_tiers` e `leitores_config`.
3. **O alinhamento da `[22/N]` nao foi validado contra CLI real** — que
   60 s bastem para as sondas de `google` e `grok` nao foi medido, por
   restricao de cota. Confirmar na primeira corrida real do preflight.
4. **`base_url` e `baseurl` nao sao exercidas isoladamente** (`[18/N]`):
   colapsam no mesmo token normalizado, e o vinculo delas e de
   declaracao.
5. **Quatro dos vinte seguem abertos** — `P1A-04`, `P1A-19`, `P1A-43`,
   `P1A-53` —, todos do mecanismo (d), cada um declarado NAO FECHA no
   proprio commit.
