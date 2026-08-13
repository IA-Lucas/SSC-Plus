# Correcao dos residuos apontados pelo parecer da P1-A.10 — 2026-08-12

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica: cada item volta ao revisor.

## 1. TOCTOU do snapshot (MAJOR novo, estreia) — FECHADO NO MECANISMO

`montar_snapshot` lia com `open()` cru apos checagens separadas. Passa
pela MESMA primitiva do runner (`ler_arquivo_contido`: contencao na
raiz + `(st_dev, st_ino)` do descritor + realpath pos-abertura), que
tambem fecha o buraco de **junction do Windows** que `os.path.islink`
nao ve. Controle com `mklink /J` real apontando para fora da raiz
(passa sem privilegios); reversao vermelha: `open()` cru de volta →
1 failed. Limite declarado no teste: a corrida em si nao se simula —
exercita-se o guarda que a fecha contra o vizinho reproduzivel.

## 2. Residuo do MAJOR-6/N5/P1A4-2 — negacao no PONTO DE DECISAO

O contorno SEM fragmento do vocabulario (chr, base64, dado externo) era
invisivel por desenho na atribuicao. No ponto de decisao ele deixa de
ser: **comparacao contra construtor textual nao resolvido e negada sem
portao de vocabulario** (`comparacoes_nao_resolvidas`). Medido no
acervo inteiro antes de ligar: UMA ocorrencia legitima
(`05_p0/cenarios/cobertura.py`), refatorada com o icamento de uma
f-string — nenhuma entrada nova de reconhecimento, que continua so com
instrumentos congelados. Controles: chr encadeado, join sobre literal e
decode de literal negados; comparacao comum (aritmetica, nome==nome,
nome==constante) segue limpa. **Limite declarado:** decisao sem
`ast.Compare` (despacho por dict indexado pela string construida)
continua fora do alcance.

## 3. Residuo do P1A4-4 — fluxo exporta, e o original ganha segunda ancora

- `executar_fluxo` passa a exportar brutos POR ETAPA
  (`08_p2/evidencias/brutos/`) — "o fluxo nem exporta" deixa de valer a
  partir da proxima corrida real; a fiacao e um argumento e a prova
  comportamental do export e a do runner (`test_p1a44_*`), com a
  corrida real seguinte como exercicio de ponta a ponta, declarado;
- a receita `bruto` aceita **ancora cruzada**: `recibo` + `trilha`
  apontam um recibo independente cujo hash tem de COINCIDIR com o
  `sha256_original` do manifesto — o original deixa de ser declaracao
  solitaria do exportador; divergencia reprova (testado nos dois
  sentidos). Limite: `trilha` percorre dicionarios, nao listas.

## 4. Os demais itens do parecer

- `num_turns` booleano recusado no schema google (bool e subclasse de
  int; caso no teste de recusa);
- errata no `99_correcao-p1a9a.md` (`--rapido` OMITE prova central) e
  na tabela da decisao P1-A.10 (p1a9b → p1a9a);
- os instrumentos da P1-A.10 entraram nos tres corpora de prova
  (portao de tier, redacao de runner, redacao de gerador), com o seam
  `_blob_do_alvo` declarado nos dois harnesses;
- **declarado contra o autor:** o commit `76f1694` foi empurrado com a
  suite VERMELHA — um `| tail` engoliu o exit code do `verificar.py`.
  O commit seguinte declara e conserta; as verificacoes desta missao
  passaram a conferir `rc` sem pipe.

## Plataforma — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
`verificar.py --rapido`: OK, rc=0 conferido sem pipe.
