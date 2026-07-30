Análise completa. Rodei a suíte (91 passed, 50 subtests), li os 13 pontos no código e nos testes, e sondei caminhos adversariais. Segue a revisão.

---

## Identidade
Sou **Claude Opus 4.8** (`claude-opus-4-8`), da Anthropic. Revisor independente; não sou o autor (Kimi).

## Achados

Nenhum **CRÍTICO** nem **MAIOR**. O hardening é genuinamente sólido: os mecanismos fazem o que declaram e os testes, em sua maioria, provam (não apenas exercitam). Os achados abaixo são todos **MENOR** ou nota.

**1. MENOR — `except Exception` genérico no fallback**
`05_p0/ssc_p0/execution.py:211` — `try: self.router.rerotear(...) except Exception as exc:` captura *qualquer* exceção (não só `RotaVetada`/`FalhaContrato`) e a rotula como "nova decisao de fallback vetada nos portoes". É **fail-closed** (escala para humano, a WU não avança), então não é vazamento de segurança — mas conflaciona veto legítimo de Policy com bug de programação (KeyError, AttributeError), reduzindo diagnosticabilidade. A missão pediu explicitamente para caçar `except` genérico; este é o único relevante. Recomendo estreitar para `(RotaVetada, ct.FalhaContrato)`.

**2. MENOR — invariante do item 1 não re-verificada após fallback**
`05_p0/ssc_p0/execution.py:67` chama `decisao_canonica` **apenas** para a primeira decisão. Após um fallback (linha 238, `decisao = nova_decisao`), as iterações seguintes reconstroem `executores` a partir do objeto local `nova_decisao` retornado por `rerotear`, sem re-passar por `decisao_canonica`. Na prática `nova_decisao` é igual à cópia canônica recém-registrada (nada a mutou), então não há divergência explorável no fluxo single-thread atual. É lacuna de *defesa-em-profundidade*, não bug ativo: a garantia "execução usa só a cópia canônica" é reforçada na 1ª decisão, presumida nas de fallback.

**3. MENOR — `_ler_fence` devolve 0 em qualquer erro**
`05_p0/ssc_p0/writelock.py:63-68` — `except (OSError, ValueError): return 0`. Em `adquirir` (linha 88), `token = _ler_fence() + 1`, então corrupção/ilegibilidade do arquivo de fence reseta o token para 1, permitindo reuso de token. Mitigado por: (a) o lock do SO garante escritor único de fato, sendo o fencing defesa secundária; (b) o THREAT-MODEL declara explicitamente corrupção de disco fora de escopo. Aceitável, mas vale um comentário no código apontando a dependência do lock do SO.

**4. MENOR/nota — comentário impreciso**
`05_p0/ssc_p0/kernel.py:235` diz `# reducer validado em copia`, mas `_aplicar` muta o estado **real** e reverte via snapshot (`_restaurar_estado`) em falha. O comportamento está correto (nada rejeitado fica durável — provado no teste 3), mas a descrição "em copia" está errada e pode enganar mantenedores.

**5. NOTA — item 5 no adaptador é eco/registro, não dedup**
`FakeProvider.invocar` (`providers.py:88-95`) só **registra e ecoa** a `idempotency_key`; não há dedup real no adaptador. Correto para provider falso P0 (não há efeito externo a deduplicar), mas o teste `test_idempotency_key_propagada_ao_provider` prova apenas *propagação* (`assertIn(...chaves_recebidas)`), não *idempotência de efeito*. A idempotência de verdade vive no EventLog (fingerprint por `payload_ref`), que **é** bem provada no teste 5. Sem ressalva de correção — apenas registro de que a garantia de idempotência é a do log, não a do provider.

## Verificação dos 13 itens

1. **OK** — `decisao_canonica` recomputa `sha256_de(dec.to_dict())` vs `_hashes_decisao`; execução refetch pela cópia canônica (`executar:67`). Teste muta 5 campos (seleção, custo, aprovação, alternativas, vínculos) → todos `DecisaoMutada`.
2. **OK** — `registrar_veredito` valida attempt↔WU (`attempt.work_unit_id != wu_id`), decisão↔WU, linhagem, `criterios_ref`, `contexto_ref`, `artefato_ref`. Teste prova que attempt de A não conclui B (B fica `aguardando-validacao`).
3. **OK** — snapshot deepcopy + rollback em `BaseException`; append só após `_aplicar`. Teste confirma bytes do log e `seq` inalterados e estado restaurado. (ver achado 4).
4. **OK** — `writelock.py` lock do SO + fencing monotônico; `test_hardening` tem 3 testes reais: 2º processo `spawn` recusado, crash+retomada com `token==2`, escritor obsoleto (`EscritorObsoleto`). Sem vazamento de lock (falha em `retomar`/`anexar_existente` chama `fechar()`).
5. **OK** — `EventoConflitoIdempotencia` por fingerprint (`payload_ref`); reentrega idêntica devolve `criado=False`; chave propagada ao provider. (ver nota 5).
6. **OK** — fallback chama `router.rerotear` → nova `RoutingDecision` com `supersede`, re-passa Policy (veto) e envelope; teste prova 2 decisões, seleção real `modelo-y`, `supersede==d1`, sem veto.
7. **OK** — `montar_contexto` liga a `work_unit_id` real (`_validar_id`), grava `bytes_ref` por entrada; `ler_pacote` falha fechada em ausência/corrupção/vínculo cruzado, sem catch que devolve vazio. Testes de corrupção, ausência e WU alheia.
8. **OK** — `_retomar_interno` ancora checkpoints por `(ultimo_evento_hash, seq)` na cadeia e escolhe `max(..., key=seq)`. Teste renomeia cp antigo para ordenar por último (armadilha de UUID) e confirma escolha de `cp2` por seq.
9. **OK** — `divergente` (modelo/provedor/effort observado≠resolvido) → `registrar_divergencia_executor` + escala; WU **não** avança. Teste com effort mentido: `escalonado`, 0 retries, WU `em-execucao`.
10. **OK** — `_validar_id` (`^[0-9a-f]{32}$`) em todos os caminhos; `EvidencePlane` usa `CAS(somente_leitura=True)` sem criar dirs. Testes de IDs ruins e de "nenhum diretório criado" + `PermissionError` na escrita.
11. **OK** — `causado_por` validado contra `_eventos_vistos` na emissão e no replay (`_replay_de_zero:893`). Teste recusa evento fora da cadeia e aceita cadeia válida.
12. **OK** — `RetryEvent.validate` impõe `1..3` e backoff `0..60000`; execução aplica teto (`min(..., BACKOFF_TETO_MS)`) e `indeterminado`/`incerto` nunca faz retry. Testes de limites e de retry-after gigante (teto, `respeitou_retry_after=False`) + timeout sem retry.
13. **OK** — `05_p0/THREAT-MODEL.md` presente e honesto: declara o que HMAC/hash/lock/scanner cobrem e **não** cobrem (atacante com a chave, escrita no disco, IC-4 lista fechada, lock não é controle de acesso) e a regra dura de credenciais para P1+.

## Veredito
**APROVADO-COM-RESSALVAS** — os 13 itens estão implementados e majoritariamente bem provados; as ressalvas são todas MENOR/defesa-em-profundidade (except genérico fail-closed em `execution.py:211`, invariante do item 1 não re-verificada pós-fallback, `_ler_fence`→0), nenhuma reabrindo caminho fail-open ou quebrando invariante declarada.
