# Contexto, conclusao semantica e lancador unico — 2026-08-11

Status: implementado e medido; **nao certificado**. Quem corrigiu nao fecha o
proprio achado.

## Caso operacional que abriu a correcao

A corrida `execucao-20260811T231843552530Z-442f725fe5e5.json` recebeu codigo
zero do Codex, mas a resposta dizia que o workspace estava inacessivel e que o
sandbox local nao iniciara. Mesmo assim o attempt e a corrida foram publicados
como `sucesso`. A causa tinha duas metades: o `ContextPackage` era vazio/ignorado
e codigo zero era tratado como conclusao da tarefa.

## Correcao exercida

1. `contexto_workspace.montar_snapshot` seleciona ate 384 KiB de arquivos de
   texto, prioriza fontes centrais, rejeita links/binarios/arquivos grandes e
   omite por inteiro qualquer arquivo que dispare a politica de segredos.
2. O snapshot entra no `ContextPackage` ligado a WorkUnit e na entrada efetiva
   do provedor. O recibo persiste caminhos, hashes, bytes e exclusoes, nunca o
   conteudo.
3. Codex e Claude recebem o prompt grande por stdin. Google e Kimi recebem um
   `contexto-ssc.txt` dentro do diretorio descartavel e apenas uma instrucao
   curta no argv. Isso evita o limite de linha de comando do Windows.
4. A resposta precisa conter exatamente `SSC_STATUS: SUCESSO` e
   `SSC_RESPOSTA:`, ou `SSC_STATUS: BLOQUEADO` e `SSC_MOTIVO:`. Marcador
   ausente, ambiguo, bloqueado ou resposta vazia vira `falha-contrato` e segue
   pelo fallback ja existente.
5. `ssc_plus.py` detem e renova o lease, reutiliza/gera preflight e chama a
   capsula/runner. `SSC-Plus.cmd` e a entrada de duplo clique/uma linha. Tier
   vencido ainda exige o ato humano `SIM`; o lancador nao inventa confirmacao.

## Prova real

`08_p2/evidencias/execucao-20260811T233326678425Z-9f925dfcd3cf.json` repetiu
uma analise de riscos pelo lancador unico. Resultado medido:

- lease automatico `ssc-plus-ui`, fence 21;
- Codex `gpt-5.6-sol`, um attempt, sucesso;
- snapshot read-only de 393.053 bytes, 39 arquivos incluidos e 206 excluidos;
- prompt de 393.529 bytes transportado por stdin, fora do argv;
- resposta fundamentada em caminhos do snapshot;
- zero mutacoes fora do descartavel dentro do alcance vigiado.

## Reversoes controladas

Cada mutante foi registrado em `scratchpad/MUTANTE-ATIVO.txt`, medido vermelho,
restaurado e medido verde antes da remocao do marcador:

| guarda removido temporariamente | vermelho | verde restaurado |
|---|---:|---:|
| snapshot ligado por padrao ao caminho operacional | 1 | 1 |
| contrato semantico na fabrica real do runner | 1 | 1 |
| prompt grande do Codex transportado por stdin | 1 | 1 |
| renovacao de lease pelo lancador | 1 | 1 |

## Regressao

- focada final: 174 testes e 102 subtestes;
- P1-A/P2 completa: 966 testes, 1 ignorado e 1.270 subtestes;
- P0 completa: 347 testes e 256 subtestes;
- `scripts/verificar.py`: codigo zero; prova central com 18 assercoes e
  20 eventos; cinco receitas P2 conferidas.

A primeira passagem integral encontrou contaminacao de
`SSC_LOCK_SESSAO` no teste do lancador e uma leitura indevida do veredito pelo
lancador. Ambos foram corrigidos: o componente de lease nao muda o ambiente
global, e somente `runner_p2` interpreta a classificacao da frota.

## Nao cobertura

- O snapshot e selecao limitada, nao acesso completo ao repositorio. Arquivos
  fora do orcamento podem conter fatos relevantes.
- `SSC_STATUS: SUCESSO` prova que o provedor declarou conclusao e impede a
  recusa textual acidental de virar sucesso; nao prova qualidade ou verdade.
  Julgamento independente continua uma etapa futura.
- Google/Kimi precisam ler o arquivo do descartavel com suas ferramentas. Se
  nao conseguirem, devem declarar bloqueio; a suite nao prova todas as versoes
  futuras desses CLIs.
- O scanner cobre os padroes conhecidos de segredo, nao todo formato possivel.
- O lancador automatiza a operacao local, mas nao remove a confirmacao humana
  de tier nem habilita escrita no repositorio.
