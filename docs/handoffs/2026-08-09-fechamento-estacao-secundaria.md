# HANDOFF — fechamento da estacao secundaria, para a PRINCIPAL

> **Data:** 2026-08-09 · **Estacao:** secundaria (temporaria) · **Repo:**
> `SSC-Plus` em `HEAD` da branch `master`.
>
> Curado, nao dump. A transcricao bruta desta sessao (**2,7 MB**) **nao
> foi versionada** — versiona-la adicionaria mais que o push inteiro
> (1,63 MiB) e repetiria a licao do log de tunel que a P1-A.7 ordem 6 ja
> registrou. O que esta aqui e o que a proxima sessao precisa **saber**,
> nao o que esta sessao **pensou**.

## 0. A PRIMEIRA COISA — tres repositorios irmaos com trabalho NAO EMPURRADO

Medido nesta maquina, em 2026-08-09. **Isto nao e do SSC+, e e o item
mais urgente deste handoff**, porque a maquina e temporaria:

| Repositorio | Commits nao empurrados | Arquivos soltos |
|---|---|---|
| `E:/SSC-Plus` | **14** → **empurrados nesta missao** | 0 |
| `E:/LucaX-Enterprise-OS` | **8** | 0 |
| `E:/Research` | **25** | 1 (`docs/` nao rastreado) |
| `E:/lucaX` | 0 | **5 modificados** |

**Os 8 do `LucaX-Enterprise-OS` contem exatamente o material que esta
missao foi mandada resgatar** (§3). Se a maquina for desligada antes do
push deles, **o resgate se perde com ela**.

**Nao os empurrei, e a razao e de metodo:** eles nao foram varridos por
segredo, e empurrar para GitHub publico sem varredura e precisamente o
que a ordem 2 deste despacho proibe. Cada um leva um comando:

    git -C E:/LucaX-Enterprise-OS push origin HEAD
    git -C E:/Research push origin HEAD

## 1. O QUE FICOU FECHADO NESTA MAQUINA

Tres missoes, **20 commits**, todos empurrados:

| Missao | O que fechou |
|---|---|
| **P1-A.7** (ordens 1-5) | o gerador de pacote **descartava em silencio** todo caminho fora de 4 extensoes. Criterio novo (LIDO / ANCORADO / EXCLUIDO NOMEADO), completude **exercida**, manifesto de cobertura em todo pacote |
| **P1-A.8** | classificou as 9 falhas da suite: **8 CODIGO, 1 MISTA, 0 AMBIENTE puro**. Concluiu que **a maquina principal e que mascarava** |
| **P1-A.9** | fim de linha **fixado por medicao**; `p22-a` recarimbada; as 9 falhas **fecharam** |

**Suite P1-A: de 9 falhas para 0** nesta arvore de trabalho.

## 2. O QUE FICOU ABERTO — com dono e gatilho

### 2.1 Os nove MAJOR — intocados

**Nenhuma das tres missoes tocou MAJOR nenhum.** Seguem exatamente como
a P1-A.6 os deixou: `6`, `N1`, `N5`, `P1A4-1`..`P1A4-6`. A contagem
**oito ou nove** continua **do Fundador**.

> **Sobre a contagem, o que mudou:** o prompt enviado aos dois revisores
> (`prompt_sha256` `0a029c37…`) **dizia "NOVE linhas" e proibia fundir**.
> Logo o silencio do `codex` foi **obediencia, nao concordancia**: ha
> **um** parecer de revisor sobre a contagem (o do `kimi`, com razao
> propria), nao dois. Se a questao for reaberta, perguntar **sem** dizer
> o numero.

### 2.2 Achados novos destas tres missoes

| # | Achado | Familia | Gatilho |
|---|---|---|---|
| **P1A9-a** | `test_o_diretorio_de_locks_existe_de_fato_nesta_estacao` depende de `locks/`, que **nenhum clone carrega** | fora de ambas | **imediato** em maquina nova |
| **P1A9-b** | a regra dos **quatro campos de plataforma** e de processo e **nenhum teste a impoe** | **(F)** | proxima medicao publicada |
| **P1A9-c** | `18,475` no README (*"razao com a MESMA resposta"*) **nao tem instrumento** que o calcule; ficou marcado, nao resolvido | fora de ambas | ja ocorreu |
| **P1A4-4** | reprodutibilidade da receita — **agravado**: a P1-A.8 provou que os numeros publicados exigiam arvore **mista** | fora de ambas | missao de reproducao da P2 |

## 3. O QUE NAO VIAJA, E ONDE ESTA

`C:\Users\<USUARIO>\.claude\` **nao viaja**. Inventariado item a item:

| Item pedido | Onde esta REALMENTE | Acao |
|---|---|---|
| lista longa do **NUNCA APAGAR** e a **custodia** | `E:/LucaX-Enterprise-OS`, em `docs/memoria-da-estacao-espelho/` | **ja commitado la** — falta **push** |
| **pacote-para-a-principal-m02** | idem (e um ponteiro em `E:/lucaX`) | **ja commitado la** — falta **push** |
| **relatorio da M-01** | idem, `m-01-relatorio-so-na-transcricao.md` | **ja commitado la** — falta **push** |
| **RETOMADA-M-01** | idem, `retomada-m-01-2026-08-08.md`. **Nao esta em `%TEMP%`** — procurado, zero ocorrencias | **ja commitado la** — falta **push** |
| **MEMORY.md e o que ele indexa** | `E:/LucaX-Enterprise-OS/memory/` (29 arquivos) | **ja commitado la** — falta **push** |

> **Nada disso foi copiado para o `SSC-Plus`, e a razao e que nao e
> dele.** Sao artefatos do programa **LucaX Enterprise OS**. Copia-los
> para ca criaria duas fontes da mesma verdade em repositorios
> diferentes — que e o defeito que o proprio `NUNCA APAGAR` existe para
> impedir. **O SSC+ nao tem memoria em `.claude`**: o diretorio
> `projects/E--SSC-Plus/` contem **so a transcricao desta sessao**.

**Credencial encontrada, NAO lida e NAO copiada:** existe
`C:\Users\<USUARIO>\.claude\.credentials.json` (509 B). Registram-se
**localizacao e tipo apenas**, conforme o protocolo do `CLAUDE.md`. Ela
**nao entrou em commit nenhum** e **nao viaja** — mas **fica nesta
maquina**, e se a maquina for descartada ou repassada, **e um item de
higiene, nao de backup**.

## 4. OS NUMEROS QUE SAO DESTA ESTACAO — NAO HERDAR

**Plataforma desta maquina**, que a P1-A.9 tornou obrigatorio declarar:

| Campo | Aqui | No registro do acervo |
|---|---|---|
| Interpretador | **Python 3.11.9** | `3.14.3` (coleta de 2026-07-30) |
| `pytest` | **9.1.1** (instalado nesta sessao; nao havia) | **nunca registrado** |
| `core.autocrlf` | **true** | nunca registrado |
| Usuario | **curto** (nome de 5 letras) | historico, de 8 |

**Numeros desta estacao, que NAO devem ser herdados:**

- **P1-A: 921 passed, 6 skipped, 1210 subtests, 0 failed** — mas
  **1 failed em clone limpo** (§5);
- **P0: 344 de 344, 256 subtests** — este **reproduziu identico** ao
  registro, e e o numero mais forte do acervo;
- **prova central: 18 assercoes, 20 eventos** — tambem **reproduziu
  identico**. (Par, nunca fracao.)

**O `914 passed, 1241 subtests` que circulava NAO reproduz**, e a causa
esta medida: no **mesmo commit** `53704b0`, esta estacao devolve
**902 passed, 8 failed, 6 skipped, 1179 subtests**. O `914` era
verdadeiro **sobre um estado que nao se reconstroi** — arvore de
trabalho mista, `locks/` de corridas anteriores, e usuario diferente.

## 5. O QUE FOI MEDIDO AQUI E **NAO** REPRODUZ LA — e vice-versa

| Fato | Aqui | Na principal (deducao de mecanismo, **nao medida**) |
|---|---|---|
| Fim de linha dos insumos da P2 | **pinado** por `05_p0/ssc_p0/.gitattributes` | **igual** — o pino e do repositorio, nao da estacao. **Conferido em clone limpo sob `autocrlf` true E false** |
| As 5 receitas | **5 CONFERE, 0 divergente** | **igual**, pelo mesmo motivo |
| `ZeroPiiNasTresRaizes` | verde | **pode achar arquivos diferentes** — o alvo deriva do usuario da estacao. **Isto e desenho, nao defeito** |
| `test_…locks_existe…` | **verde aqui** (o `locks/` existe porque a P1-A.7 o criou) | **vermelho em clone limpo** — `P1A9-a` |

> **A suite esta verde NESTA ARVORE e NAO em clone limpo.** Em clone novo
> do mesmo commit: **1 failed, 920 passed**. A falha e sempre a mesma
> (`locks/`). **Nao anuncie "suite verde" sem esta ressalva.**

## 6. O QUE A PRINCIPAL TEM QUE FAZER PRIMEIRO

Nesta ordem, e as duas primeiras antes de qualquer trabalho novo:

1. **`git pull` no `SSC-Plus`** — sao **20 commits** novos, e tres deles
   mudam regra no `CLAUDE.md` (fim de linha, plataforma de quatro
   campos, copia datada antes de limpar labs);
2. **empurrar os irmaos desta maquina enquanto ela existe**, ou aceitar
   a perda — `LucaX-Enterprise-OS` (**8 commits, com o resgate da
   memoria**) e `Research` (**25 commits**). Ver §0;
3. **rodar as duas suites na principal e declarar a plataforma** — sera
   a primeira medicao de la sob a regra dos quatro campos, e a primeira
   chance de confirmar por **corrida** o que este handoff afirma por
   **mecanismo**;
4. **conferir se `P1A9-a` reproduz la** — se o `locks/` existir na
   principal por corridas antigas, a falha fica invisivel de novo, e e
   exatamente o tipo de mascara que a P1-A.8 encontrou;
5. **decidir a contagem 8/9**, com a ressalva da §2.1 na mao.

## 7. O QUE ESTE HANDOFF **NAO** DIZ

- **nao certifica nada.** Tres missoes corrigiram, e `QUEM CORRIGE NAO
  CERTIFICA` vale inteiro. Suite verde **nao** e acervo certificado;
- **nao mediu a maquina principal.** Tudo sobre ela aqui e **deducao de
  mecanismo** sobre bytes versionados;
- **nao fechou MAJOR nenhum**;
- **nao varreu os repositorios irmaos** por segredo — por isso nao os
  empurrou.
