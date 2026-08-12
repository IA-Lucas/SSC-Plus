# Fluxo controlado multi-provider — 2026-08-11

Status: implementado, provado offline e exercitado contra os CLIs reais. Este
registro nao certifica respostas vazias de provedores como aprovacao.

## Contrato

O lancador oferece quatro intencoes simples:

1. Analisar projeto;
2. Corrigir problema;
3. Implementar funcionalidade;
4. Revisar alteracao.

Todas percorrem `contextualizar -> planejar -> implementar -> revisar ->
julgar -> testar`. O contexto extenso e atribuido ao Kimi, plano e proposta ao
Codex, revisao ao Claude e julgamento transversal ao Google. O provedor e
exigido por etapa: nao existe fallback silencioso entre papeis.

Para corrigir/implementar, o Codex produz somente uma proposta de unified diff.
O patch e aplicado e testado numa copia descartavel do workspace. Mesmo com
Claude e Google aprovando e a suite verde, a arvore real permanece inalterada.
O sistema gera um token nao persistido; aplicar exige `fluxo_id` + token,
reconfere o hash do patch e os hashes dos arquivos-alvo, e recusa qualquer
deriva ocorrida depois do teste.

## Dois portoes que nao se confundem

`SHADOW_ELIGIBLE` voltou a significar apenas admissibilidade tecnica sombra.
Ele nao autoriza P2. A frota exige separadamente um ato operacional P2 e grava
na `FleetEntry` o ID, modo e fonte desse ato. Declaracao de tier nao pode ocupar
esse campo.

Do mesmo modo, `SSC_STATUS: SUCESSO` comprova somente o transporte. O fluxo
exige exatamente um marcador por papel (`SSC_PLANO`, `SSC_IMPLEMENTACAO`,
`SSC_REVISAO`, `SSC_JULGAMENTO`), reprova em qualquer marcador negativo e ainda
exige testes locais verdes.

## Isolamento do Kimi

O Kimi participa somente da contextualizacao ampla, recebe o snapshot por
`contexto-ssc.txt` no diretorio descartavel e e instruido a nao procurar fora
dele. Como seu CLI nao oferece sandbox de filesystem equivalente ao Codex, a
vigilancia e fail-closed: qualquer mutacao medida fora do descartavel invalida
a resposta, que vira falha de contrato e nao alimenta o plano.

No modo headless, o Kimi tambem e exigido a produzir `stream-json`. Os eventos
`assistant` sao recompostos antes da verificacao do contrato; texto livre,
JSON invalido ou uma escrita externa continuam recusados.

Isso reforca a contencao dentro do alcance medido, mas nao inventa um sandbox:
o lar completo do CLI e o lado remoto continuam fora do alcance declarado.

## Prova offline antes da primeira operacao

- testes focados de autorizacao e runner: 70 verdes;
- fluxo/aprovacao: 8 verdes;
- protecao P2.3, incluindo mutacao externa do Kimi: 36 verdes;
- `python scripts/verificar.py --rapido`: codigo zero em 2026-08-11;
  P1-A/P2 com 981 testes, 1 ignorado; verificacao total em 222,4 s.

Arquivos centrais: `08_p2/fluxo_controlado.py`,
`08_p2/executar_fluxo.py`, `08_p2/frota_medida.py`, `08_p2/runner_p2.py` e
`ssc_plus.py`.

## Operacao real controlada — 2026-08-12

Foram feitas operacoes reais em modo `analisar`, sempre sem patch e sem
aplicacao. O recibo amplo em
`08_p2/evidencias/fluxo-20260812T011132038677Z-recusado.json` registra
Kimi, Codex (plano e implementacao sem alteracao) e Claude como sucesso; o
Google devolveu JSON `SUCCESS` sem conteudo de resposta e o fluxo recusou o
julgamento. A repeticao compacta em
`08_p2/evidencias/fluxo-20260812T011927316485Z-recusado.json` mediu o mesmo
desfecho.

Uma reproducao isolada confirmou que o CLI Google responde corretamente a uma
sonda curta, mas devolve `response` vazia para o contexto de julgamento. O
gate nao faz fallback de juiz, nao aceita o status sozinho e nao executa os
testes apos esse julgamento invalido. Todos os recibos publicos passam pela
redacao integral; nenhuma mudanca de modelo foi aplicada.
