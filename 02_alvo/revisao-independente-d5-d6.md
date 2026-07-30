---
id: SSC-REV-02
titulo: Revisao independente de D5/D6 (PORTAO 1 da Missao SSC+ 0.2)
tipo: revisao-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# PORTAO 1 — Revisao independente de D5 (contratos) e D6 (arquitetura)

> Auditoria de `02_alvo/05_contratos-alvo.md` e `02_alvo/06_arquitetura-alvo.md`
> (ambos v0.1.0), exigida como portao bloqueante antes de qualquer codigo P0.
> Veredito ao final: **CONTRACTS-REVIEW-PASSED** (apos correcoes aplicadas como
> versao local v0.2.0 — sem as correcoes, o veredito seria REVIEW-BLOCKED).

## 1. Identidade e independencia do revisor

| Item | Declaracao |
|---|---|
| Revisor | Invocacao independente de LLM (Kimi, Moonshot AI), sessao nova, sem nenhum contexto compartilhado com a sessao autora da Missao SSC+ 0.1 |
| Autor de D5/D6 | Sessao da Missao SSC+ 0.1 (modelo nao declarado nos artefatos — lacuna de proveniencia registrada) |
| Distincao | Garantida por construcao: este revisor nao escreveu, nao viu e nao influenciou D5/D6 v0.1.0; primeiro contato com os documentos ocorreu nesta auditoria, ja nesta missao |
| Familia de modelo | **Nao atestavel.** A missao pede "invocacao independente de outra familia de modelo" **ou** revisor humano. A familia do autor da 0.1 nao consta nos artefatos; logo nao posso provar familia distinta. O que e fato: invocacao e contexto independentes. **Limitacao L1-02:** o Soberano pode exigir revisao humana complementar; ela nao e bloqueante porque a missao admite invocacao independente, mas fica registrada |

Metodo: leitura integral de D5/D6 v0.1.0; confronto com os 12 itens de correcao
mandados pela missao (checklist do Soberano); achados proprios adicionais (§3);
verificacao, apos a reescrita, de que cada correcao efetivamente consta em
v0.2.0 (§4). Nenhum codigo foi escrito antes deste veredito.

## 2. Achados sobre os 12 itens mandados (v0.1.0 → correcao em v0.2.0)

| # | Item mandado | Estado em v0.1.0 | Correcao aplicada (v0.2.0) |
|---|---|---|---|
| 1 | Separar `aguardando-aprovacao` de `aguardando-validacao`; tabela de estados | **Ausente.** WorkUnit tinha `aguardando-juiz` unico, ambiguo entre espera de humano e de juiz; nenhuma tabela de transicoes | Estados novos `aguardando-aprovacao` (humano) e `aguardando-validacao` (juiz); tabelas de transicao completas para Sessao (D5 §1.2), WorkUnit (D5 §2.1) e Attempt (D5 §5.1) |
| 2 | Tipo 1/2 e `criterios_aceite_ref` congelados na WorkUnit | **Parcial.** IW-4 citava "Tipo 1" sem o campo existir; criterios de aceite so apareciam indiretos no ValidationVerdict | Campos `tipo_decisao` (`tipo-1`\|`tipo-2`, semantica FND-04) e `criterios_aceite_ref` (sha256, congelado na `proposta`; mudar = nova WorkUnit) — D5 §2 |
| 3 | Decisao/tentativa vinculadas aos hashes de envelope, politica, permissoes, aprovacao, catalogo e contexto | **Ausente.** RoutingDecision tinha so `hash_pacote`; attempt nao vinculava nada | Objeto `vinculos` com os 6 hashes em RoutingDecision (D5 §4) e ExecutionAttempt (D5 §5); Kernel recusa attempt cuja decisao nao e vigente ou cujo vinculo diverge do estado corrente |
| 4 | Modelo/effort solicitado, resolvido e observado; alias nao prova identidade | **Ausente.** v0.1.0 tinha so `executor` "efetivo" | `selecao_solicitada` (da decisao), `executor_resolvido` (apos catalogo/alias, com `hash_catalogo`) e `executor_observado` (reportado pelo provedor; `null` honesto); divergencia observado≠resolvido gera evento e contamina o veredito — D5 §5 |
| 5 | L1–L3 complementados com modalidade, ferramentas, saida, contexto, dominio, privacidade, latencia e orcamento | **Ausente.** L1–L3 eram escala nua | `perfil_capacidade` na WorkUnit e no catalogo, com as 8 dimensoes; regra de casamento (executor atende todas as dimensoes exigidas) — D5 §2, D6 §3 |
| 6 | Armazenamento local enderecado por conteudo | **Ausente** (so "referencia sha256") | CAS definido: layout `objetos/<2>/<2>/<sha256>`, escrita atomica (tmp+rename+fsync), verificacao na leitura, imutavel, sem seguir symlink/junction — D5 §8.1 |
| 7 | EventLog: escritor unico, sequencia, schema_version, causalidade, idempotency_key, prev_event_hash | **Ausente.** v0.1.0 tinha so evento_id/ts/tipo/payload_ref e "streaming por offset" | Campos `seq`, `schema_version`, `causado_por`, `idempotency_key`, `prev_event_hash`; escritor unico = Session Kernel; offset vira otimizacao, a cadeia de hash e a prova — D5 §8.2; D6 §2.1/§2.6 |
| 8 | Retry so idempotente ou comprovadamente nao aplicada; efeito incerto = resultado-indeterminado | **Parcial.** Retry tipado existia, mas sem criterio de efeito externo | Regra IR-1/IR-2: retry exige `idempotency_key` ou prova de nao-aplicacao; `resultado=indeterminado` no attempt bloqueia retry automatico e escalona — D5 §5/§6 |
| 9 | Veredito vinculado a tentativa, criterios, contexto e pacote do juiz; falha deterministica inanulavel por LLM | **Parcial.** Verificador declarado existia; vinculo com attempt/criterios/contexto nao | Campos `attempt_id`, `criterios_ref`, `contexto_ref`, `pacote_juiz` (provedor/modelo/effort/hash da rubrica/seed); invariante IV-2 de precedencia: camada deterministica veta e nenhuma camada superior a anula sem novo artefato — D5 §7 |
| 10 | sessao_id × linhagem_id; bloquear symlink/junction, fuga de caminho e segredo em evento/contexto | **Parcial.** linhagem imutavel existia, mas sem semantica de heranca; nada sobre caminho/segredo | §1.1: sessao = vida logica (suspensao/retomada mantem `sessao_id`); linhagem atravessa sessoes so por `linhagem_origem` declarada; IC-4 (scanner de segredos na montagem do pacote e antes de gravar evento) e IC-5 (contencao de caminho, resolucao sem seguir symlink/junction) — D5 §1.1/§3 |
| 11 | Fluxo Router → Policy → Execution; Kernel escreve o EventLog, Evidence Plane so le/projeta | **Inconsistente.** Diagrama D6 §1 mostrava Policy → Router; Evidence Plane tinha "telemetria append-only por evento" (escritor paralelo) | Diagrama e §2 corrigidos: Router propoe, Policy veta, Execution executa; **somente o Kernel escreve** no EventLog; Evidence Plane consome por leitura e projeta — D6 §1/§2.6, D5 §8.2 |
| 12 | Aprovacao de custo = envelope (modelos, effort, teto, modo, validade, fallback), nao modelo fixo | **Ausente.** v0.1.0 amarrava `aprovacao_custo_ref` a uma selecao | `aprovacao_custo` como objeto-envelope: `modelos_permitidos`, `efforts_permitidos`, `teto_custo`, `modo`, `validade` (expira), `fallback_autorizado`; reroteamento dentro do envelope nao exige nova aprovacao — D5 §4 |

## 3. Achados proprios do revisor (alem dos 12 mandados)

- **RA-1 — Base de hash indefinida.** v0.1.0 dizia "sha256" sem dizer sha256 *de
  que bytes*. Corrigido: serializacao canonica JSON (UTF-8, chaves ordenadas,
  separadores compactos, sem NaN) definida em D5 §0.1; todo `*_ref` aponta para
  bytes do CAS (correcao 6).
- **RA-2 — Relogio nao e autoridade de ordem.** v0.1.0 ordenava por `ts`.
  Corrigido junto com o item 7: `seq` monotonica e a ordem; `ts` e informativo.
- **RA-3 — Attempt contra decisao supersedada.** IW-1 garantia decisao vigente
  "antes de em-execucao", mas nada impedia attempt referenciando decisao ja
  supersedada. Corrigido com o item 3 (Kernel valida vigencia + vinculos).
- **F-Aceito (sem correcao, registrado):** `custo_previsto` nao define moeda;
  fica para o catalogo da P0 declarar unidade por provedor, rotulado `estimado`.
  Nao bloqueia contratos.

## 4. Verificacao pos-correcao

Cada linha da tabela do §2 foi conferida contra o texto de D5 v0.2.0 e D6 v0.2.0
aplicados (secao citada na coluna "Correcao"). Diffs completos:
`02_alvo/diffs/d5-v0.1.0-v0.2.0.diff` e `02_alvo/diffs/d6-v0.1.0-v0.2.0.diff`
(gerados por `git diff` sobre a working tree do laboratorio, sem commit nesta
missao).

## 5. Veredito

**CONTRACTS-REVIEW-PASSED** — D5 v0.2.0 e D6 v0.2.0 estao aptos a basear a
implementacao P0. Limitacoes: L1-02 (familia de modelo nao atestavel, §1);
revisao de papel — contradicoes residuais so a implementacao revela (fragilidade
ja aceita na decisao 0.1 §3); nenhuma metrica produzida nesta revisao (so
definicoes, como manda L7 da decisao 0.1).
