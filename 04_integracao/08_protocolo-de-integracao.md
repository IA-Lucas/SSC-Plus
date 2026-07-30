---
id: SSC-DOC-08
titulo: Protocolo de Integracao SSC+ ↔ Canonico
tipo: protocolo-experimental
versao: 0.1.0
status: ativo
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-07-30
---

# D8 — Protocolo de Integracao

> O caminho pelo qual algo nascido no SSC+ pode, eventualmente, virar materia
> canonica. **Nada experimental sobe automaticamente.** Este protocolo obedece —
> e nunca contorna — ADR-0007 (fronteira greenfield/legado) e FND-04 (classes de
> mudanca).

## 1. O pipeline

```
[1] Snapshot canonico ──► [2] Experimento no SSC+ ──► [3] Evidencia/Proposta
        │                        │                         │
   baseline + hash          isolamento total          medida, com base
   (BL-AAAA-MM-DD-NN)       (Manifesto D2)            e metodo declarados
                                                           │
                    [5] Eventual promocao ◄── [4] Goal competente ◄──┘
                         (rito canonico)        (dono da materia)
```

1. **Snapshot canonico.** Toda missao do SSC+ abre fixando a referencia: baseline
   vigente + hash por arquivo (`01_fontes/snapshots/`). Citacao normativa sem
   baseline + hash e invalida no laboratorio. Se o canonico mudou desde o ultimo
   snapshot, registra-se a nova referencia — **nunca** se edita a fonte.
2. **Experimento no SSC+.** Trabalho dentro do isolamento (D2), sobre os contratos
   (D5) e a arquitetura (D6), provado pelo plano (D7).
3. **Evidencia/Proposta.** A saida do laboratorio e um documento de evidencia
   (o que foi medido, base, metodo, lacunas) e/ou uma proposta (o que o canonico
   poderia adotar, com fit-gap contra o vigente). Formato livre local; ao ser
   enderecada a um Goal, a proposta deve ja trazer os insumos do portao G1–G5
   (abaixo).
4. **Goal competente.** A proposta e entregue **a** quem detem a materia no
   canonico — nunca aplicada pelo laboratorio. Roteamento (evidencia externa A4,
   nao normativo; o destino final e o que o canonico disser quando a materia for
   aberta):
   - Contratos de sessao/memoria/eventos, adapters → **Epico 2** (kernel tecnico);
   - Roteamento de modelos, politica, metricas de custo → **Goal 1.15** (Tools &
     Models), incluindo eventual ficha `TOL-modelo-*` para Kimi K3 se o piloto o
     recomendar (ficha exige finalidade, custo, dependencia, alternativa e
     criterio de descarte);
   - Decomposicao, work units, ondas → **Goal 1.17** (Workflows);
   - Contratos de especialista/contexto → **Goal 1.18** (Agents);
   - Juiz, vereditos, metricas, prova de execucao → **Goal 1.19** (Execution &
     Evaluation);
   - Prova vertical de ponta a ponta → **Goal 1.20** (Vertical Proof).
5. **Eventual promocao.** So pelo rito canonico: o Goal competente classifica a
   mudanca (C0–C3 × Tipo 1/2), produz os instrumentos (RFC/ADR), e — se Tipo 1 ou
   C3 — o Soberano ratifica. O SSC+ nao participa da aprovacao: quem propoe nao
   aprova (GV-04).

## 2. Portao de admissao (G1–G5, ADR-0007 §5.3) — insumos que a proposta deve trazer

| Condicao | O que o SSC+ entrega |
|---|---|
| **G1 Proveniencia declarada** | Secao "Fontes" com caminho + hash + data de observacao de cada origem (ja praticado em D3/D4) |
| **G2 Fit-gap contra o vigente** | Tabela: o que o canonico ja tem que responde a mesma pergunta e onde diverge (ex.: FND-09 §5 nao tem Sessao/Tarefa; FND-08 §3.3 nao tem L1–L3) |
| **G3 Classificacao declarada** | Uma de ADOPT/ADAPT/REWRITE/RETIRE por item, com motivo |
| **G4 Validacao independente** | Vereditos de Juiz independente do laboratorio (D7 §8) como evidencia preliminar — a validacao canonica (DEP-QAR) e separada e posterior |
| **G5 Decisao formal** | Fora do SSC+: instrumento da classe, produzido no Goal competente |

## 3. Regras duras do protocolo

- **PR-1 Nada sobe automaticamente.** Nenhum evento, metrica, script ou documento
  do SSC+ escreve no canonico, em nenhuma hipotese, por nenhum mecanismo.
- **PR-2 Copia nao e promocao.** Promover nunca e copiar codigo do laboratorio:
  e decidir materia no rito canonico. (Espelha FR-03: conteudo que entrar fora do
  portao e nulo.)
- **PR-3 Rejeitado fica registrado.** Proposta recusada pelo Goal competente
  permanece no laboratorio com o motivo — registro de rejeicao e ativo (principio
  `AC-03-VID-011` da evidencia externa: tentativas rejeitadas como parte do
  ativo).
- **PR-4 Uma proposta por vez.** O portao canonico opera um candidato por vez
  (FR-07); o SSC+ enfileira, nao empacota em massa.
- **PR-5 Sem atalho por familiaridade.** O SSC+ herdar conceitos do SuperCondutor
  legado **nao** lhe confere precedente: funcionar no legado nao e argumento de
  autoridade (FR-05).
- **PR-6 O SSC+ nunca decide a frente da arquitetura canonica.** Se o canonico
  normatizar a materia de forma divergente do desenho do laboratorio, o desenho do
  laboratorio e que converge — ou e aposentado (Carta §8, item 2).

## 4. Estado das fontes consumidas (proveniencia desta missao)

| Fonte | Referencia fixada | Uso nesta missao |
|---|---|---|
| Canonico LucaX Enterprise OS | `BL-2026-07-29-08` · 164 artefatos · impressao `8cf2143c…b027a7f` · snapshots de 97 arquivos (v1, 22:05) e 98 (v2, 01:32) em `01_fontes/snapshots/` — **processo externo alterou 7 arquivos de registro/indice e criou 1 durante a missao** (nenhum `foundation/` ou template); ver `99_decisao-ssc-01.md` §2 | Restricoes (FND-03/04/08/09/10, ADR-0007, ADR-0021) e Goals 1.13–1.20 |
| SuperCondutor legado | git `bf8a407c…b5b786` · hashes de 7 arquivos + 4 agregados em D3 §1 | Baseline e matriz de engenharia reversa |
| A4 congelada | `_SAIDA-COMPANY-OS` (RESEARCH-READY-FROZEN) · resumo executivo → pacote → candidatos → fichas, na ordem obrigatoria | Candidatos, padroes, lacunas e o roteamento de Goals; **zero fontes originais abertas** (nenhuma duvida material) |
| Acervo A0 | `LucaX-Enterprise-Research/acervo-company-os` | Confirmacao de inventario/hashes; nao usado como fonte de avaliacao |

Nenhuma fonte original do acervo de pesquisa foi aberta: nao houve duvida
material. Se surgir, a regra e: reabrir so a fonte especifica, reconferir hash
(B-04 — o acervo sofre escrita concorrente) e registrar a reabertura em `logs/`.
