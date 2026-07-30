REVISAO INDEPENDENTE — SSC+ 0.2.1 (hardening da P0)

Voce e um revisor INDEPENDENTE. O autor do codigo e outro agente (Kimi).
Seja adversarial e cetic: sua funcao e encontrar falhas, nao aprovar.

CONTEXTO
- Repo: laboratorio experimental offline (Python 3.14, stdlib apenas, sem
  rede, sem credenciais, providers falsos deterministicos).
- O commit 33bc963 e o baseline "experimental baseline — ADJUST".
- A working tree atual contem o hardening 0.2.1. O diff completo esta em
  logs/diff-0.2.1-hardening.patch (3079 linhas, 29 arquivos).
- Codigo: 05_p0/ssc_p0/*.py; testes: 05_p0/tests/*.py.

A MISSAO EXIGIU 13 CORRECOES. Verifique CADA UMA no codigo e nos testes:
1. RoutingDecision persistida e hasheada; Execution usa so a copia canonica;
   mutacao posterior (selecao, alternativas, custo, hashes, aprovacao) recusada.
2. ValidationVerdict prova que attempt, WorkUnit, decisao, contexto, criterios
   e artefato pertencem a mesma cadeia (attempt de A nunca conclui B).
3. Reducer (_aplicar) validado antes do append; evento rejeitado nao duravel.
4. Escritor unico entre processos com lock/lease e fencing token; testes de
   dois processos, crash, retomada e lock obsoleto (05_p0/ssc_p0/writelock.py,
   05_p0/tests/test_hardening.py).
5. Idempotency key guarda fingerprint: reentrega identica aceita; mesma chave
   com payload diferente = conflito; chave propagada ao Provider Adapter.
6. Fallback gera NOVA RoutingDecision (repete todos os portoes), registra a
   selecao real, permanece no envelope aprovado.
7. ContextPackage nasce ligado ao work_unit_id real; bytes de cada entrada no
   CAS; corrupcao/ausencia falha fechada; sem catches que devolvem pacote vazio.
8. Checkpoint escolhido pelo ultimo evento valido/seq, nunca por UUID.
9. Divergencia modelo/effort observado x resolvido falha fechado ou escala.
10. IDs validados em caminhos; Evidence Plane usa CAS read-only sem criar dirs.
11. causado_por validado na mesma linhagem; existencia/hash de payloads CAS no
    replay.
12. RetryEvent limitado a 1..3 e teto de backoff; indeterminado nunca repete
    automaticamente.
13. Threat model declarado (05_p0/THREAT-MODEL.md).

VERIFIQUE TAMBEM
- Caminhos fail-open restantes (except generico, retorno vazio silencioso).
- Bugs reais: condicoes de corrida, TOCTOU, vazamento de lock em excecao,
  fencing token contornavel, restauracao de estado incompleta em _emitir.
- Se os testes novos realmente provam o que dizem (ou so exercitam codigo).

NAO EDITE NENHUM ARQUIVO. Responda em portugues, neste formato exato:
## Identidade
(modelo/versao que voce e, se souber)
## Achados
(numerados; para cada um: severidade CRITICO/MAIOR/MENOR, arquivo:linha,
descricao, por que e problema)
## Verificacao dos 13 itens
(item a item: OK / FALHA / PARCIAL + uma linha de justificativa)
## Veredito
APROVADO / APROVADO-COM-RESSALVAS / REPROVADO (uma frase)
