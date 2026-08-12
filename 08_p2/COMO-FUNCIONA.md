---
id: SSC-P2-COMO-FUNCIONA
titulo: SSC+ — como funciona, para quem nao programa
tipo: explicacao-experimental (NAO e atestado)
versao: 1.0.0
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# SSC+ — o que e isso, em portugues

> **O que muda decisao, primeiro:** ele funciona, mas **ninguem de fora
> conferiu**. A promessa central — *despachar poupa token* — **nao esta
> medida em token**: os CLIs nao informam contagem, e o que existe e uma
> medicao aproximada em bytes. E ha **12 defeitos graves corrigidos e
> nenhum fechado**, porque quem conserta nao assina o proprio laudo.

Traduzindo de uma vez: **CLI** = programa de linha de comando; **provedor**
= cada assinatura de IA que voce ja paga (codex, kimi, claude, google,
grok); **frota** = os provedores disponiveis numa corrida.

## 1. O que ele faz

Voce escreve uma tarefa numa linha de comando; o SSC+ escolhe qual das suas
assinaturas vai executa-la, chama o programa dela, guarda a resposta e grava
um recibo. Ele resolve **quem faz e como provar que fez** — quem estava
apto, o que falhou, o que voltou. Ele **nao** resolve a qualidade da
resposta (nenhum juiz avalia o que voltou) e nao aplica nada: responde,
nunca edita seu codigo. Serve para **voce**, dono das assinaturas, quando
quer tirar uma tarefa do canal caro e por na franquia ja paga.

## 2. Como funciona, do pedido ate a resposta

1. **Voce declara o tier** — escreve num arquivo qual e seu plano em cada
   assinatura. O programa **nunca adivinha**, e a declaracao vale 24 h.
   *Impede* supor plano que voce nao tem; vencida, a frota trava sozinha.
2. **Capsula** — o SSC+ so roda num "ambiente-filho" de onde toda chave de
   API paga foi retirada; suas chaves no Windows ficam intactas, apenas
   **nao entram**. *Impede* que a tarefa vire cobranca por API paga. Se
   sobrar chave visivel, o processo aborta antes da primeira sonda.
3. **Lease** — "senha de vez": um terminal segura o direito de escrever e o
   renova a cada 30 s. *Impede* duas sessoes escreverem uma sobre a outra;
   o direito e reconferido antes de gravar o recibo.
4. **Preflight** — a checagem previa: versao, login, modelos existentes,
   franquia acabou. **Zero chamada de modelo**; grava um arquivo com o
   veredito. *Impede* despachar para assinatura deslogada, sem modelo ou
   zerada — quem nao passa sai `BLOCKED`/`SUPERVISED`, com motivo escrito.
5. **Montagem da frota** — o veredito vira rotas; so `ELIGIBLE` e
   `SHADOW_ELIGIBLE` habilitam. *Impede* rota inventada: modelo que o CLI
   nao mostrou vira descarte com motivo — nada some do relatorio.
6. **Portoes** — sua preferencia (`--capacidade`) reordena a fila, e tres
   portoes vetam: economia (custo variavel zero), canal (login de
   assinatura, nunca chave de API) e automacao. Veto = o CLI **nem chega a
   ser aberto**.
7. **Invocacao** — o CLI vencedor e chamado sem terminal interativo, com sua
   tarefa como texto puro. *Impede* que `|` ou `&` no texto virem comando.
8. **O que da errado sozinho** — franquia esgotada: troca de assinatura.
   Falha passageira: ate 3 tentativas. Estouro de tempo (15 min): para **sem
   repetir** — tarefa que talvez tenha rodado nao roda de novo sozinha.
   Ninguem apto: para, e **nunca** migra para API paga.
9. **Recibo** — a resposta e impressa e gravada em `08_p2/evidencias/`, com
   seus caminhos pessoais apagados.

## 3. O que voce digita

Abra `H:\SSC-Plus` no Explorer e de duplo clique em `SSC-Plus.cmd`. Ou use
uma unica linha no PowerShell:

```powershell
.\SSC-Plus.cmd
```

O programa pergunta a tarefa e o tipo de trabalho. Lease, tier, preflight,
capsula, snapshot do workspace, selecao do provedor e recibo acontecem
automaticamente. Se os tiers venceram, o programa mostra os tres planos e so
renova depois de voce digitar `SIM`.

Tambem e possivel passar a tarefa em uma linha:

```powershell
python .\ssc_plus.py --tarefa "Analise os riscos do SSC Plus"
```

**Confira:** `status: sucesso`, o bloco `--- saida ---` e a ultima linha
`evidencia: ...execucao-<data>.json`.

### Os tres erros mais provaveis

| Aparece | Significa | Faca |
|---|---|---|
| tiers vencidos | passou das 24 h — **e o mecanismo funcionando** | confirme com `SIM` no lancador |
| preflight vencido | veredito de ontem nao autoriza gasto de hoje | o lancador gera outro automaticamente |
| escritor unico ocupado | outra operacao SSC+ ainda esta aberta | encerre a operacao anterior e abra novamente |

**Isto NAO e erro:** `attempt kimi/...: falha-quota` seguido de
`attempt codex/...: sucesso` — a franquia do kimi acabou e a maquina trocou
de assinatura sozinha. Medido duas vezes em 2026-08-03.

## 4. Quando usar, e quando nao vale

**Despache** tarefa em que a IA precisa **ler coisa sua** — abrir arquivo,
varrer diretorio, examinar codigo. E o unico caso em que a poupanca medida e
majoritariamente real: na maior corrida, 94 % dela era o arquivo que a
assinatura leu sozinha e o outro canal nunca precisou engolir.

**Nao despache** pergunta autocontida, sem consultar nada: descontando a
diferenca de tamanho das respostas, a economia dessa classe e **zero**
(razao 1,000).

**A vantagem acompanha o tamanho do que foi lido**, nao o tipo da tarefa: a
mesma tarefa deu 8,78x com arquivo de 6 KB e 19,56x com um de 13 KB.

**Desconte isto da expectativa.** Uma fatia do numero anunciado **nao vem de
despachar**: vem de o codex responder mais curto que o outro canal (usou 3-4
das 8 linhas permitidas; o outro usou 8). Ela ficou quase constante — **597
a 890 bytes** nas cinco corridas — e independe do tipo de tarefa: em tarefa
grande some no meio, em tarefa pequena **e** o numero inteiro. E resposta
curta nao e resposta melhor: a medicao nao olha o conteudo.

Se uma capacidade preferida apontar para uma assinatura sem quota, ela pode
custar uma tentativa antes do fallback. O preflight atual, e nao a medicao
historica de 2026-08-03, define essa disponibilidade.

## 5. O que ele ainda nao e

1. **12 defeitos graves em aberto** — seis apontados por revisor
   independente que nunca fecharam, mais seis abertos depois. Os doze
   **foram corrigidos**, com prova; nenhum **fechou**, porque quem conserta
   nao assina o laudo. Aberto = *consertado e nao conferido por terceiro*.
2. **Ninguem de fora certificou a P2** — nem o codigo, nem o instrumento de
   medicao, nem os numeros deste documento. Nao existe atestado.
3. **O recibo pode faltar sem a corrida ter faltado.** Ja aconteceu: um
   caractere que o terminal nao sabia desenhar derrubou o processo depois da
   resposta e antes de gravar — franquia gasta, recibo inexistente. Foi
   consertado, mas a ordem entre "imprimir" e "gravar" segue sem guarda:
   outro imprevisto no mesmo ponto abre o mesmo buraco.
4. **A evidencia de sucesso do Kimi continua faltando** — as corridas de
   2026-08-03 encontraram quota esgotada; isso nao descreve a quota atual.
5. **Nao ha metrica de token comparavel** — Google reporta sua telemetria;
   Codex, Claude e Kimi nao entregam aqui o mesmo campo estruturado.
6. **Voce sabe qual modelo foi escolhido, nao qual respondeu** — o CLI nao
   ecoa isso, e o guarda de divergencia nao dispara.
7. **Claude e Google entram automaticamente em modo supervisionado e
   somente leitura**; Grok continua fora da rota automatica.
8. **O snapshot e parcial** — tem teto de 384 KiB e declara quais arquivos
   entraram ou ficaram de fora; nao equivale a acesso integral ao disco.

## 6. Onde vive cada coisa

| Arquivo | Papel |
|---|---|
| `06_p1a/tiers_declarados.json` | onde voce declara seu plano; vale 24 h |
| `06_p1a/capsula.py` | tira as chaves de API do ambiente |
| `06_p1a/evidencias/renovador_lock.py` | segura a "vez" de escrever |
| `07_p1b/preflight_atual.py` | a checagem previa; escreve o veredito |
| `08_p2/frota_medida.py` | veredito → rotas, com o que ficou de fora |
| `08_p2/provedor_assinatura.py` | chama o CLI e classifica a falha |
| `08_p2/runner_p2.py` | o comando que voce digita; grava o recibo |
| `ssc_plus.py` / `SSC-Plus.cmd` | lancador unico: lease, preflight e runner |
| `08_p2/contexto_workspace.py` | snapshot read-only limitado e redigido |
| `08_p2/medidor.py` | a medicao em bytes, com os 9 limites embutidos |
| `08_p2/README.md` | a fronteira medida, antes dos comandos |
| `08_p2/evidencias/` · `07_p1b/evidencias/` | recibos de corridas e preflights |

## 7. Onde a garantia ainda termina

1. **A restricao nao e uniforme.** Codex recebe sandbox read-only; Claude,
   plan mode; Google, plan+sandbox. O Kimi medido nao oferece flag equivalente
   e depende do diretorio descartavel e da vigilancia por manifesto.
2. **Modelo escolhido nao e modelo atestado.** O SSC+ fixa o ID no argv, mas
   Claude e Google nao devolvem uma identidade estruturada do modelo realmente
   servido.
3. **O contexto tem orcamento.** Arquivo fora dos 384 KiB selecionados, acima
   do limite individual, binario ou recusado por segredo nao chega ao modelo.
4. **Nao existe certificacao independente.** Testes, reversoes e corridas
   comprovam o comportamento observado; nao fecham os achados por autoridade.

> Documento descritivo: nao certifica, nao corrige, nao abre missao.
> Nenhum provedor foi invocado para escreve-lo; custo variavel zero.
