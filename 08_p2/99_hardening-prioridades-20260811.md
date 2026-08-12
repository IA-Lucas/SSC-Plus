# Hardening das prioridades — 2026-08-11

> Missao de correcao, experimental e sem autoridade. Quem corrigiu nao
> certifica. O proprietario confirmou os tiers em 2026-08-11 e um preflight
> novo autenticado abriu tecnicamente Codex e Kimi por no maximo 24 h; isso
> nao e autorizacao implicita para executar uma tarefa produtiva.

## Resultado por prioridade

| # | Correcao | Estado | Familia do achado de origem |
|---|---|---|---|
| 1 | preflight com schema fechado, HMAC local, gravacao atomica e teto fixo de 24 h | implementada | (N) — autenticidade/estrutura nao era medida |
| 2 | envelope validado em custo zero, autonomo e fallback, inclusive validade | implementada | (F) — o portao declarava envelope, mas nao exercia esses caminhos |
| 3 | scanner sobre entrada/saida integrais e CAS; teto de 1 MiB; recibo sem texto | implementada | (F) no corte de 4.000; (N) na retencao do recibo |
| 4 | recibo atomico antes do relato | implementada | fora de ambas — ordenacao de efeitos |
| 5 | fechamento explicito/finalizador, pipes fechados e descartavel removido | implementada | fora de ambas — ciclo de vida |
| 6 | mutex global do runner e IDs com microssegundos + UUID | implementada | fora de ambas — concorrencia/colisao |
| 7 | `python scripts/verificar.py`, versoes declaradas e CI Windows | implementada | fora de ambas — reproducibilidade |
| 8 | renovar tiers, gerar preflight e reabrir P2 | **executada**: codex/kimi `SHADOW_ELIGIBLE` | fora de ambas — ato factual confirmado pelo proprietario |

## Prova que exerce o caso operacional

- `ValidadeDoPreflight` escreve um preflight completo assinado, adultera o
  resultado depois da assinatura e passa pelo mesmo `carregar_preflight`
  usado pelo runner. Tambem exerce campo extra assinado e `validade_h=1000`.
- `TestPolicy` chama o `TaskRouter` real com custo zero/controle autonomo e
  chama o portao real de fallback depois de expirar o envelope.
- `CorridaDePontaAPonta` coloca o segredo depois do caractere 5.000 e passa
  pela maquina real ate a fronteira de execucao; o sensor acusa qualquer
  chamada. A saida com segredo atravessa o provider e e recusada antes do
  CAS.
- `test_recibo_ja_existe_se_o_relato_falhar` usa `publicar_recibo`, a mesma
  primitiva chamada por `main`, e faz o relator levantar depois da escrita.
- Os testes de subprocesso usam o interpretador local, nao mock, para timeout,
  captura e teto. Os testes do runner rodam com `ResourceWarning` promovido.
- `ConcorrenciaENomes` tenta entrar duas vezes no decorador operacional da
  P2 no mesmo processo e exige parada do segundo; 100 IDs no mesmo instante
  precisam ser distintos.
- `RenovacaoDoProprietario` exerce o comando real em copia temporaria: sem
  confirmacao nao altera nem cria backup; tier divergente para antes do
  lock; o caminho aceito guarda backup integral e publica sob o mesmo fence;
  perder o fence depois do backup preserva a declaracao anterior.

Resposta exigida pela regra de prova: os testes acima exercem os pontos de
chamada e interfaces que a operacao percorre; nao apenas primitivas vizinhas.

## Reversao vermelha medida

Cada mutante foi registrado antes em `scratchpad/MUTANTE-ATIVO.txt`, aplicado
ao fonte de producao, medido, revertido e seguido de verde focado:

| Reversao temporaria | Vermelhos medidos |
|---|---:|
| ignorar MAC do preflight | 1 de 1 |
| restaurar a condicao antiga do envelope (so custo positivo e nao autonomo) | 2 de 2 |
| remover scanner da entrada integral | 1 de 1; o sensor foi alcancado |
| relatar antes de persistir recibo | 1 de 1; recibo ausente |
| remover mutex global do runner | 1 de 1 |
| reter o diretorio descartavel | 1 de 1 |
| tratar chave ausente como invalida (estado defeituoso medido na passagem final) | 13 erros na suite; 3 de 3 verdes apos restaurar o ramo de criacao |
| remover a confirmacao explicita do proprietario na renovacao | 1 de 1 |
| publicar tiers sem reverificar o mesmo fence depois do backup | 1 de 1 |
| remover `05_p0` do caminho do comando isolado de renovacao | 1 de 1; reproduziu `ModuleNotFoundError: ssc_p0` |

Nao permaneceu registro de mutante ativo depois das restauracoes.

## O que a prova NAO cobre

- HMAC local nao resiste a processo do mesmo usuario com leitura da chave.
- O scanner e uma lista fechada e nao prova ausencia de dado confidencial;
  o CAS aceito continua em claro no lab ignorado pelo Git.
- O teto drena stdout/stderr sem crescimento de memoria, mas nao limita bytes
  que um CLI possa escrever por conta propria no seu diretorio antes de sair.
- O mutex foi exercido no mesmo processo; `LockSessao` tem testes entre
  processos na P0, mas esta missao nao fez uma corrida produtiva concorrente.
- A CI foi criada, nao observada num runner remoto nesta missao.
- Nenhum teste prova disponibilidade, quota ou identidade atual dos CLIs.
- Os testes da renovacao usam copias temporarias: provam as guardas e a ordem
  de publicacao, nao que os nomes de plano informados ainda sejam verdadeiros.
- O proprietario confirmou os nomes de plano no dialogo e a sonda comprovou
  login/modelo, mas os CLIs continuam sem expor o plano; por isso o resultado
  correto e `SHADOW_ELIGIBLE`, nao `ELIGIBLE`.
- O preflight faz somente diagnostico. Nao prova quota produtiva nem sucesso
  de resposta; nenhuma chamada de modelo foi feita na abertura.

## Estado de abertura

Em 2026-08-11T20:20:42Z, o proprietario confirmou `ChatGPT Pro 5x` e
`Allegretto`. `06_p1a/renovar_tiers.py` publicou a declaracao por 24 h sob
fence 4 e guardou a anterior em
`06_p1a/evidencias/backups/tiers_declarados-20260811T202042693946Z-pre-renovacao.json`.
O primeiro ensaio operacional parou antes dessa publicacao ao revelar que o
comando isolado nao alcancava `ssc_p0`; a correcao ganhou teste em subprocesso
limpo e reversao vermelha.

O preflight autenticado
`07_p1b/evidencias/preflight-20260811T202042972286Z.json` foi aceito pelo
mesmo `carregar_preflight` do runner: Codex/`gpt-5.6-sol` e
Kimi/`kimi-code/k3` sairam `SHADOW_ELIGIBLE`; Claude, Google e Grok ficaram
`SUPERVISED`; `BLOCKED` ficou vazio. O lease foi readquirido com fence 5 e
liberado na auditoria final. A P2 esta tecnicamente disponivel ate o primeiro
dos vencimentos (no maximo 2026-08-12T20:20:42Z), sempre exigindo novo lease
por corrida. Nenhuma tarefa produtiva foi executada.

## Medicao final local

`python scripts/verificar.py` terminou com codigo zero em 212,8 s:

- plataforma: CPython 3.14.3; pytest 9.1.1; `core.autocrlf=true`;
  usuario `IA Lucas`;
- P0: 347 testes, 3 skips;
- P1-A/P2: 943 testes, 1 skip, 1.265 subtests;
- prova central: 18 assercoes, 20 eventos;
- receitas P2: 5 conferem, 0 divergem.

O comando promove `ResourceWarning` a erro, propaga `safe.directory` apenas
ao ambiente dos subprocessos e roda a prova central com `--sem-gravar`, para
que verificar nao altere a evidencia publicada.
