---
id: SSC-DOC-02
titulo: Manifesto de Isolamento do SSC+
tipo: manifesto-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D2 — Manifesto de Isolamento

> Registro das fronteiras fisicas e logicas do laboratorio. Violacao deste manifesto
> e condicao de encerramento por violacao (Carta §8, item 3).

## 1. Caminhos

| Papel | Caminho | Modo |
|---|---|---|
| **Raiz gravavel unica** | `E:/LucasIA/Projetos/SSC-Plus` | leitura + escrita |
| Fonte normativa (canonico) | `E:/LucasIA/Projetos/LucaX Enterprise OS` | **somente leitura** |
| SuperCondutor legado | `E:/LucasIA/Projetos/lucaX/My_WorkSpace/Meus_projetos/SuperCondutor` | **somente leitura** |
| Documentacao legada (ADRs, handoffs) | `E:/LucasIA/Projetos/lucaX/docs` | **somente leitura** |
| Contratos de especialista legados | `E:/LucasIA/Projetos/lucaX/agentes` | **somente leitura** |
| A4 congelada | `E:/LucasIA/Projetos/LucaX Enterprise OS/_SAIDA-COMPANY-OS` | **somente leitura** |
| Acervo de pesquisa A0 | `E:/LucasIA/Projetos/LucaX-Enterprise-Research/acervo-company-os` | **somente leitura** |

## 2. Permissoes e areas gravaveis

- **Gravavel:** apenas a arvore de `E:/LucasIA/Projetos/SSC-Plus`.
- **Proibido gravar:** qualquer caminho fora da raiz, incluindo os backups
  `_backup-*`, `_candidatos-*` e demais irmaos em `E:/LucasIA/Projetos`.
- **Proibido criar:** links simbolicos (para dentro ou para fora), junctions,
  hardlinks, mounts ou qualquer forma de alias que faca uma fonte read-only
  aparecer dentro do laboratorio ou vice-versa.
- **Proibido importar:** codigo das fontes por copia de arquivo, `import`,
  `sys.path`, submodule, subtree ou include. Referencia e **citacao por caminho +
  hash**, nunca por vinculo executavel. (Espelha FR-03 de ADR-0007: o que entrar
  fora do portao e nulo.)

## 3. Estado, Git e memoria isolados

- **Git proprio:** `E:/LucasIA/Projetos/SSC-Plus/.git`, inicializado em 2026-07-30,
  com `user.name`/`user.email` locais (`SSC-Plus Lab`), sem remotos configurados.
  Nenhuma operacao de Git toca outro repositorio: o canonico **nao e** repositorio
  Git (verificado) e o legado `lucaX` e lido apenas (`git rev-parse HEAD` =
  `bf8a407c2d2fbd492f4ba4abeed522d345b5b786`, registrado para proveniencia).
- **Estado:** nenhum estado compartilhado com as fontes — sem leitura de
  `sessoes/` do legado como entrada operacional (e estado de producao de terceiro;
  lido somente como evidencia, nunca escrito, nunca executado).
- **Memoria:** a memoria do laboratorio vive em `memoria/` deste repositorio.
  Nenhuma escrita em `memory/` do canonico nem em `kb/` do legado.
- **Logs:** em `logs/` deste repositorio. Nenhum append em `runtime/logs` do legado.

## 4. Segredos

- **Nenhum segredo e necessario nesta fase** (zero chamada de API).
- O repositorio nao armazena segredos: `.gitignore` bloqueia `.env`,
  `*.secret.json`, `*.key`, `*.pem`, `secrets/`, `*.local.json` (padrao herdado da
  higiene do legado, que mantinha `perfil.local.json` e `.chave_sessao` fora do Git).
- Se uma fase futura exigir credencial (piloto com provider real), ela entra por
  variavel de ambiente, nunca por arquivo versionado, e a missao que a introduzir
  deve atualizar este manifesto **antes** do uso — mais a autorizacao explicita do
  Soberano, por envolver custo (R4 da Carta).

## 5. Rede

- **Fase 0.1:** nenhuma chamada de rede a provedor de IA. Nenhuma API paga.
- Uso de rede permitido e limitado a: leitura de documentacao publica para pesquisa
  (quando o Soberano pedir), sem envio de dados das fontes.
- Proibido: enviar conteudo de qualquer fonte read-only a servicos externos
  (espelha o gate LGPD do legado — upload/transcricao externa bloqueados).

## 6. Custo

- **Orcamento desta fase: R$ 0,00 de API.** O unico custo e o da sessao de trabalho
  ja autorizada pelo Soberano.
- Qualquer fase futura com custo variavel exige: estimativa antes, aprovacao
  explicita, telemetria medida depois — o padrao do portao de custo bloqueante do
  legado (ADR-054/121), adotado como requisito do Execution Gateway (D6).
- Metricas de custo sao **medidas, nunca estimadas nem inventadas** (CE-02/CE-04 de
  FND-10 como disciplina do laboratorio). Onde nao houver medicao, escreve-se
  `nao medido`.

## 7. Backup

- O proprio Git local e a primeira copia (historico versionado por missao).
- Copia de seguranca adicional: a criterio do Soberano, espelho em
  `E:/LucasIA/Projetos/_backups` — **saida** do laboratorio, nunca entrada; nao e
  criada nesta fase por decisao de escopo (regra do Soberano: "Sem copia, nao roda"
  — MEM-EST-0001 AF-35 — aplicada antes do primeiro risco irreversivel; nesta fase
  todo o conteudo e regeneravel a partir das fontes intactas + este Git).
- Rollback de qualquer documento: `git checkout` da versao anterior; nenhum
  documento deste repositorio e imutavel por contrato (diferente do M1 canonico).

## 8. Prevencao de contaminacao

| Vetor | Controle |
|---|---|
| Escrita acidental em fonte | Validacao ao fim de cada missao: `git status` do legado deve permanecer limpo e os hashes do snapshot canonico devem reproduzir (`sha256sum -c`) |
| Dependencia oculta | Nenhum codigo nesta fase; fases futuras declaram em D3/D4 toda dependencia conceitual herdada do legado |
| Copia de codigo legado | Baseline (D3) descreve comportamento **sem copiar codigo**; engenharia reversa produz especificacao, nao transplant |
| IDs canonicos espurios | Prefixo local `SSC-*`; proibido emitir `FND/ADR/RFC/CAP/DEP/MEM/FIT/...` novos; contadores canonicos pertencem a DEP-GOV (FND-03 §2.3) |
| Estado fantasma | Nenhum arquivo de estado fora de `memoria/` e `logs/`; sessoes do legado nunca abertas para escrita |
| Subagente fora da fronteira | Todo subagente de exploracao recebe a lista de caminhos read-only e a proibicao de escrita/execucao no briefing |

## 9. Verificacao deste manifesto (fase 0.1)

Executada em 2026-07-30 e registrada em `99_decisao-ssc-01.md`:

1. **Snapshot canonico em duas versoes** (`01_fontes/snapshots/`): v1 (22:05) e v2
   (01:32), porque um **processo externo escreveu no canonico durante a missao** —
   7 arquivos alterados e 1 novo, todos de registro/indice/transicao, nenhum deles
   `foundation/` ou template. O nucleo normativo permaneceu intacto. Detalhes e
   lista de arquivos: `99_decisao-ssc-01.md` §2.
2. **Legado `lucaX` com working tree suja pre-existente** (334 arquivos
   modificados, mtimes anteriores ao inicio da missao, ex.: 2026-07-29 00:40) —
   registrado como estado encontrado; a missao nao alterou nada la. O controle e:
   hashes do SuperCondutor referem-se **a working tree encontrada** sobre HEAD
   `bf8a407c…b5b786` (D3 §1).
3. Nenhum link simbolico na arvore do SSC+ (`find -type l` = 0 — medido).
4. Nenhum arquivo fora de `E:/LucasIA/Projetos/SSC-Plus` criado ou modificado pela
   missao — todas as escritas da sessao foram dentro da raiz gravavel (rastreavel
   pelo registro da sessao).
