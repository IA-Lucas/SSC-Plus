# Ativacao supervisionada de Claude e Google — 2026-08-11

Status: implementado e medido; **nao certificado**. Este registro e produzido
por quem realizou a alteracao e nao substitui revisao independente.

## Resultado operacional

Claude e Google passam a participar da selecao e do fallback automaticos da
P2, junto de Codex e Kimi. A automacao permanece `supervised`, com envelope
sem escrita e custo variavel externo zero. Grok permanece `SUPERVISED`, sem
rota automatica.

| provedor | preferencia inicial | fonte do modelo | restricao produtiva |
|---|---|---|---|
| Codex | implementacao, operacao do repositorio | `codex doctor` | sandbox read-only + diretorio descartavel |
| Claude | arquitetura, specs, revisao profunda | config persistida oficial | `permission-mode plan`, sem persistencia e sem slash commands |
| Kimi | engenharia reversa, contexto extenso, volume | `kimi provider list` | diretorio descartavel; o CLI nao oferece sandbox equivalente medido |
| Google | multimodal, julgamento transversal | `agy models` | `mode plan`, sandbox, JSON e slash commands desativados |

`autor`, `revisor` e `juiz` sao papeis dinamicos, nao cargos permanentes. Em
trabalho critico, autor e revisor/juiz precisam divergir em provedor **e**
modelo. Sem `--capacidade`, a ordem do preflight prevalece; a capacidade
somente reordena a fila.

## Evidencia medida

- preflight atual, assinado e aceito pelo consumidor canonico:
  `07_p1b/evidencias/preflight-20260811T211742052426Z.json`;
- Claude produtivo: `08_p2/evidencias/execucao-20260811T211906332774Z-246966fa00ef.json`;
- Google produtivo final: `08_p2/evidencias/execucao-20260811T212209047035Z-1bee9d32a050.json`;
- primeira tentativa Google, preservada como evidencia negativa:
  `08_p2/evidencias/execucao-20260811T211923450839Z-ebb5e1d66480.json`;
- preflight anterior bloqueado, tambem preservado:
  `07_p1b/evidencias/preflight-20260811T211636268624Z.json`.

O Claude respondeu pelo caminho `claude -p --model ...` em modo plan. O
Google respondeu pelo `agy` oficial com o marcador exato pedido, um turno
produtivo e telemetria estruturada. A vigilancia do repositorio nao mediu
mutacao em nenhuma das duas corridas.

## Defeito encontrado durante a ativacao

Na primeira chamada Google, as flags foram colocadas antes do texto passado a
`-p`. O processo terminou com sucesso, mas o texto indicou outro modelo, sinal
de que o CLI havia tratado o restante do argv de forma diferente do esperado.
Uma comparacao sem turno produtivo com `/model` mostrou que o `agy` exige o
prompt imediatamente depois de `-p`. O montador ganhou uma regra explicita por
provedor; a chamada final fixou `--model gemini-3.1-pro-high` depois do prompt.

## Reversoes controladas

Cada mutante foi marcado em `scratchpad/MUTANTE-ATIVO.txt`, medido vermelho,
restaurado e medido verde antes da remocao do marcador:

| guarda removido temporariamente | vermelho | verde apos restauracao |
|---|---:|---:|
| prompt Google imediatamente apos `-p` | 1 | 1 |
| modelo Google obrigatorio no argv | 1 | 2 testes + 4 subtestes |
| recusa de sucesso Google com `num_turns = 0` | 1 subteste | 1 teste + 2 subtestes |
| remocao de `ORCA_*` no preflight e executor | 2 | 2 |

## Nao cobertura e validade

- O JSON produtivo do `agy` nao informa a identidade do modelo realmente
  servido. O que se prova e modelo exato no argv, aceite do CLI e `/model` em
  uma sonda sem turno; nao ha atestado independente do lado do servidor.
- Claude tambem nao fornece identidade estruturada do modelo servido. A prova
  combina config oficial, modelo fixado no argv e resposta medida.
- A vigilancia mede o repositorio e caminhos declarados, nao o estado remoto
  do provedor nem todo o home usado pelos CLIs.
- As flags `plan`/sandbox sao propriedades dos CLIs externos. A suite prova
  presenca, ordem e recusa de formas invalidas, nao a inexistencia de todo
  escape concebivel dentro desses programas.
- A rota continua somente leitura: ela produz resposta e recibo; nao aplica
  patch automaticamente.
- As declaracoes de tier expiram em 24 horas; o consumidor da P2 ainda aplica
  sua janela maxima de preflight. Ao vencer, renovar tier e refazer preflight.

## Decisao ainda externa

Este trabalho nao fecha achados nem certifica o SSC+. A revisao independente
do mecanismo, das evidencias e dos limites continua pendente.
