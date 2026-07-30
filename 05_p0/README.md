# 05_p0 — Camada P0 (contratos) do SSC+

Implementação executável dos contratos **D5 v0.2.0** e dos componentes
**D6 v0.2.0**, contra **providers falsos determinísticos por seed** (D7 §3).
Stdlib apenas, Python 3.14, zero rede, zero dependências externas, zero
escrita fora da raiz declarada de cada corrida.

**0.2.1 (hardening)**: as 13 correções da revisão independente estão
aplicadas — decisão canônica hasheada (mutação recusada), veredito com
cadeia completa, reducer validado antes do append, escritor único entre
processos (lock/lease + fencing token), idempotency key com fingerprint
(propagada ao provider), fallback com nova decisão, ContextPackage ligado
ao work_unit_id real com bytes no CAS, checkpoint por seq (nunca UUID),
divergência observado×resolvido fechada, IDs validados em caminhos,
`causado_por` na linhagem, retry 1..3 com teto de backoff e threat model
declarado em `THREAT-MODEL.md`.

## Como rodar

```bash
# a partir da raiz do repositório (E:/LucasIA/Projetos/SSC-Plus)
python -m unittest discover -s 05_p0/tests -v
python 05_p0/cenarios/prova_central.py
python 05_p0/cenarios/corridas_to.py
python 05_p0/cenarios/cobertura.py   # cobertura de linha (stdlib trace)
```

- Testes: **91 testes, 0 falhas, 0 skips** (o antigo skip de symlink foi
  substituído por prova REAL de junction/reparse point no Windows).
- Cobertura de linha medida com `trace` (stdlib): **2296/2296 linhas
  (100%)** dos módulos `ssc_p0`; relatório em `saidas/labs/cobertura/`.
- A prova central grava `05_p0/saidas/prova_central.json`.
- As corridas TO-1..TO-5 gravam `05_p0/saidas/to1.json`..`to5.json`.
- Laboratórios das corridas e dos testes (CAS, logs, checkpoints, locks)
  ficam em `05_p0/saidas/labs/` (pasta ignorada pelo Git). Todos os
  números são **simulados** e rotulados `simulado` (MR-2); nada aqui é
  medição real.

## Layout

```
05_p0/
├── ssc_p0/                 # pacote (stdlib only, identificadores sem acento)
│   ├── canonico.py         # JSON canônico, sha256, UUID-4, relógio injetável
│   ├── contratos.py        # dataclasses D5: to_dict/from_dict/validate
│   ├── estados.py          # 3 máquinas de estado; TransicaoIlegal
│   ├── cas.py              # CAS 2/2/sha256, escrita atômica, IC-5, read-only
│   ├── eventlog.py         # JSONL append-only, cadeia prev_event_hash, fingerprint
│   ├── writelock.py        # lock/lease + fencing token (escritor único entre processos)
│   ├── kernel.py           # SessionKernel (escritor único) + ControlPlane
│   ├── catalogo.py         # catálogo de executores falsos + aliases
│   ├── providers.py        # FakeProvider: bateria de falhas programável
│   ├── router.py           # TaskRouter (propõe; veto da Policy)
│   ├── policy.py           # PolicyGateway (veta; envelope de custo)
│   ├── execution.py        # ExecutionGateway (retry/fallback/escalonamento)
│   ├── judge.py            # Juiz1 determinístico (veta, IV-2) + Juiz2 falso
│   └── evidence.py         # EvidencePlane (SOMENTE leitura e projeção)
├── cenarios/
│   ├── comum.py            # montagem de lab em raiz declarada
│   ├── prova_central.py    # A PROVA: troca de modelo na mesma sessão/linhagem
│   ├── corridas_to.py      # TO-1..TO-5 conforme critérios pré-registrados
│   └── fixtures/           # to1 (entrada+oráculo), to2 (repo), to3 (diff+semente)
├── tests/                  # bateria unittest (nomes dizem o item coberto)
└── saidas/                 # evidências JSON + labs (gerado)
```

## O que está implementado (mapa para D5/D6)

- **Enums fechados** e round-trip exato de todos os 11 contratos
  (`contratos.py`); valor fora de enum = `FalhaContrato`, nunca coerção.
- **3 máquinas de estado** (Sessão §1.2, WorkUnit §2.1, Attempt §5.1);
  transição fora da tabela = `TransicaoIlegal`; órfão só via retomada.
- **Vínculos de 6 hashes** (`hash_envelope`, `hash_politica`,
  `hash_permissoes`, `hash_aprovacao`, `hash_catalogo`, `hash_contexto`):
  decisão ou attempt divergente/supersedado = recusa antes do gasto (RA-3).
- **Executor solicitado/resolvido/observado**: alias registrado não prova
  identidade; divergência observado ≠ resolvido = evento tipado e o juiz
  calcula independência sobre o **observado**.
- **CAS** (§8.1): layout 2/2, tmp+fsync+rename, leitura re-verificada,
  imutável, contenção por caminho real (recusa `..`, symlink/junction).
- **EventLog** (§8.2): escritor único (Kernel), seq monotônica,
  `schema_version`, `causado_por`, dedup por `idempotency_key`, cadeia
  `prev_event_hash`; detecção fechada de duplicado/fora de ordem/truncado/
  adulterado; replay determinístico do zero (IP-4, provado por teste).
- **Checkpoint** (§8.3): selo HMAC local, validação do Juiz 1 antes de gravar,
  retomada = checkpoint válido + cadeia verificada (IP-1); selo/conteúdo/
  cadeia divergente = não retoma (`CheckpointInvalido`, o chamador escalona,
  IP-2); attempt sem conclusão após crash = `orfao` → `indeterminado`.
- **Recuperação** (§6, D6 §4): retry (só transitório, máx. 3, IR-1:
  `idempotency_key` ou efeito `nao-aplicado`, Retry-After respeitado),
  fallback (ordem declarada, **dentro** do envelope; fora = escalonamento),
  reroteamento (nova decisão `supersede`), reparo (nova WorkUnit `etapa`),
  escalonamento (sempre para humano); `indeterminado` sem retry (IR-2).
- **Juiz**: determinístico veta e não é anulável (IV-2, com recusa
  registrada); juiz-llm falso por seed com `pacote_juiz` completo,
  independência calculada **antes** de julgar, fila mínima declarada;
  veredito exige `attempt_id` e `criterios_ref` == congelado (IV-3);
  juiz-llm só julga o que passou na determinística.
- **Policy**: portão de custo como **envelope** (modelo fora da lista = veto
  mesmo estando na política; reroteamento dentro do envelope sem nova
  aprovação; validade, esforço, modo, teto); orçamento verificado antes de
  cada attempt (estouro = `EscalationEvent orcamento`, zero chamadas depois).
- **IC-4**: scanner determinístico de segredos sobre todo payload de evento
  e toda entrada de contexto — detecção = recusa, nunca redação.
- **EvidencePlane**: consome o log verificado + CAS, projeta placar, custos
  e divergências; não possui nenhuma referência de escrita.

## Decisões de implementação

- **Control Plane mínimo vive em `kernel.py`** (classe `ControlPlane`): o
  contrato de entrega listava os demais módulos; a separação de autoridade é
  preservada (ele apenas emite fatos ao Kernel: escalonamentos, aprovações,
  ciclo de vida).
- **`hash_envelope`** cobre identidade/escopo/permissões/tetos, **excluindo**
  campos voláteis (`estado`, `consumido_*`, `contexto_ativo_ref`,
  `memoria_ref`) — senão cada consumo invalidaria os vínculos das decisões
  vigentes e o reroteamento dentro do envelope seria impossível.
- **Payloads de eventos no CAS**: o log guarda só `payload_ref` (D5 §8.2);
  replay e Evidence leem o CAS. O objeto do pacote de contexto é gravado sem
  o campo `hash_pacote`, de modo que seu sha256 é exatamente o `hash_pacote`.
- **Anti-competição (IW-3)**: similaridade de Jaccard sobre tokens da
  `intencao` entre irmãs, limiar 0,6 — determinístico e barato (validação
  antes de pagar, como manda a regra herdada).
- **Ciclo em decomposição**: validado em dois níveis — `validar_plano`
  (Router, recusa o plano antes de qualquer registro, usado pela TO-4) e
  `_checar_ciclo` (Kernel, defesa em profundidade sobre `depende_de`/pai).
- **Juiz 1 com duas camadas**: quando há camada seguinte (TO-3), o cenário
  chama `Juiz1.julgar(..., conclui=False)` e a WU permanece
  `aguardando-validacao` até o veredito final — a máquina de estados não é
  afrouxada: a transição só ocorre por veredito, como na tabela.
- **Relógio determinístico** por padrão (corridas reproduzíveis); `ts` é
  informativo, a ordem causal é a `seq`.
- **Chave do selo HMAC** gerada por raiz de laboratório (`chave_selo.bin`,
  32 bytes aleatórios locais) — necessária para retomada entre processos;
  nunca sai da raiz.
- **Testes usam `tempfile` do sistema** para os laboratórios efêmeros (o
  teste de "zero escrita externa" prova que, dentro do tmp, tudo fica sob a
  raiz declarada). Artefatos permanentes (fixtures, evidências, labs) ficam
  todos sob `05_p0/`.

## Limitações conhecidas

- Providers são falsos por definição da camada P0; custos/latências são
  simulados e rotulados. Nenhuma conclusão sobre qualidade/custo real pode
  ser tirada destes números (D7 §3, MR-2/MR-4).
- Single-processo: o escritor único é garantido por lock em processo; não há
  locking de arquivo entre processos (fora de escopo da P0).
- `fsync` de diretório é ignorado no Windows (não há fd de diretório).
- O scanner IC-4 é uma lista fechada de padrões determinísticos; não é um
  detector de segredos de propósito geral.
- `encerrada`, herança de linhagem entre sessões (`linhagem_origem`) e o modo
  `worktree` estão modelados nos contratos/máquinas, mas não exercidos por
  cenário próprio na P0.
- O skip do teste de symlink real no Windows é esperado sem privilégio de
  desenvolvedor/admin; o comportamento é coberto pelo teste com mock do
  resolvedor.
