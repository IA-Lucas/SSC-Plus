# Remocao da flag inerte `--mode plan` da restricao do Google — 2026-08-12

> **Decisao do Fundador, 2026-08-12** (opcao *a* do tradeoff declarado no
> registro 103): a flag sai da restricao headless. Missao executora desta
> decisao; quem corrige nao certifica.

## O que mudou, e o que NAO mudou

- **Saiu** `--mode plan` de `restricao_headless` do provedor google em
  `06_p1a/preflight/frota_real.py`. Sob `--disable-slash-commands` ela
  era inerte — aviso literal do CLI: *"--mode plan has no effect while
  slash command expansion is disabled"* (medido nas sondas A/B/E do
  registro 103). Mante-la seria rotular contencao que nao se exerce, a
  familia (F) que este acervo persegue.
- **Ficou** `--mode plan` no comando de LOGIN (`/quota`): la os slash
  commands estao ligados e a flag tem efeito. A remocao cega nos dois
  lugares teria tirado contencao de onde ela funciona.
- A contencao efetiva do turno produtivo permanece a que sempre foi de
  fato: `--sandbox`, permissoes auto-negadas em headless e a vigilancia
  por manifesto.

## Prova

- Sonda real sem a flag: `SUCCESS`, resposta correta, **stderr vazio** —
  o proprio aviso de inercia desapareceu com ela;
- suites de provedor/preflight/adaptadores: 111 passed, 104 subtests;
- o rotulo da restricao (`rotulo_restricao`) deriva da lista e se
  atualiza sozinho — nenhum texto afirmando plan sobrevive.

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
