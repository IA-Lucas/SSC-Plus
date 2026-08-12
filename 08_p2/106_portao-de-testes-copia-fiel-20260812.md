# O portao de testes media uma copia que nao existe — 2026-08-12

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica.

## O defeito latente que as cinco etapas verdes revelaram

Na quinta corrida real do dia (`fluxo-20260812T135319263030Z-recusado.json`),
**as cinco etapas passaram** — Kimi, Codex (plano e implementacao),
Claude e, pela primeira vez, o julgamento do Google (1806 bytes) — e o
fluxo caiu no ultimo portao: *"testes reprovaram com codigo 1"*.

O portao (`testar_patch_isolado`) copiava o workspace **sem `.git`**.
Essa copia nao e o estado em que a operacao roda, e a suite completa nao
tem como passar nela:

- os testes ancorados em historico (blobs por commit) **pulam** quando
  detectam ausencia de git — mas um gerador de pacote
  (`pacote_p1a36.montar_pacote`) da **`SystemExit`** ao nao achar o
  commit alvo, e SystemExit **mata o unittest no meio, sem sumario**;
- dezenas de outros testes devolvem ERROR na mesma condicao.

O portao era, portanto, **irrealizavel por construcao** para operacoes
sobre este repositorio — e nunca tinha sido alcancado numa corrida real,
porque todas as anteriores morriam antes.

## A correcao, e a prova

`_ignorar_copia` deixa de excluir `.git` (3,3 MB): o portao passa a
medir a suite num **checkout fiel descartavel** — exatamente o estado
que a P1-A.8 declarou como onde o SSC+ se mede, e que a medicao do
P1A9-a provou verde em clone limpo hoje de manha.

- teste novo (`CopiaFielParaOPortaoDeTestes`) exerce a interface real do
  portao: `copytree` com `_ignorar_copia` sobre arvore com git de
  verdade, exigindo o MESMO `HEAD` na copia e a ausencia de `locks/`,
  `__pycache__` e `.pyc`;
- portao real medido apos a correcao: `testar_patch_isolado(None)` →
  **returncode 0, 994 testes, 1 pulado**, na copia fiel.

## Achado para revisao, declarado

**`SystemExit` num modulo de evidencia aborta a suite inteira sem
sumario.** O gerador tem razao de parar sozinho (portao de identidade),
mas a suite nao deveria morrer sem relatorio por causa dele. Fica como
achado de infraestrutura de teste, **fora de ambas** as familias, para a
proxima revisao independente — esta missao nao mexeu nos geradores.

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
