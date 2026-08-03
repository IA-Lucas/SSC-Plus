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

**1) Renovar a declaracao de plano (vale 24 h):**

```powershell
cd E:\LucasIA\Projetos\SSC-Plus
Copy-Item 06_p1a\tiers_declarados.json `
  "06_p1a\evidencias\backups\tiers_declarados-$(Get-Date -Format 'yyyy-MM-dd')-pre-renovacao.json"
python -c "import datetime;print(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
```

Copie o instante impresso para os dois campos `declarado_em_utc` de
`06_p1a\tiers_declarados.json`. **Confira:** os dois com a data de hoje.

**2) Segurar a vez — terminal proprio, deixe aberto:**

```powershell
python 06_p1a\evidencias\renovador_lock.py p2-ops
```

**Confira:** ele nao volta ao prompt. Se voltou, nao ha vez.

**3) A checagem previa — noutro terminal:**

```powershell
cd E:\LucasIA\Projetos\SSC-Plus
$env:SSC_LOCK_SESSAO = "p2-ops"
python 06_p1a\capsula.py python 07_p1b\preflight_atual.py
```

**Confira:** a linha `evidencia: 07_p1b/evidencias/preflight-<data>.json`
(guarde o caminho) e `SHADOW_ELIGIBLE: ['codex', 'kimi']` no resumo. Se os
dois sairem `BLOCKED`, pare: o passo 1 nao pegou.

**4) Despachar:**

```powershell
python 06_p1a\capsula.py python 08_p2\runner_p2.py `
  --preflight 07_p1b\evidencias\preflight-<data>.json `
  --tarefa "o que voce quer feito" `
  --criterio "como saber se ficou bom"
```

**Confira:** `status: sucesso`, o bloco `--- saida ---` e a ultima linha
`evidencia: ...execucao-<data>.json`. **Se a linha da evidencia nao
apareceu, a corrida ainda pode ter ocorrido** — ver limite 3 da secao 5.

### Os tres erros mais provaveis

| Aparece | Significa | Faca |
|---|---|---|
| `erros=P1A-DECLARACAO-EXPIRADA`, provedores em `BLOCKED` | passou das 24 h — **e o mecanismo funcionando** | refaca o passo 1 |
| `PARADA: preflight ... acima da janela de 24h` | checagem velha; veredito de ontem nao autoriza gasto de hoje | refaca o passo 3 |
| `PARADA: lease da sessao operacional morto` | o terminal do passo 2 fechou ou nunca abriu | reabra o passo 2 |

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

**Custa uma tentativa perdida** pedir `--capacidade volume`,
`contexto-extenso` ou `engenharia-reversa`: puxam o kimi, cuja franquia
acabou.

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
4. **A franquia do kimi esta esgotada** — `kimi -p` nunca foi validado num
   caminho de sucesso. Na pratica, a frota e **so codex**.
5. **Nao ha contagem de token** — nenhum CLI reporta; o campo sai vazio e o
   placar interno conta ausencia como zero, rotulando o total `simulado`.
6. **Voce sabe qual modelo foi escolhido, nao qual respondeu** — o CLI nao
   ecoa isso, e o guarda de divergencia nao dispara.
7. **claude, google e grok nao entram**; google e grok nunca foram sondados.
8. **A tarefa vai sozinha** — nenhum contexto adicional acompanha o prompt.

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
| `08_p2/medidor.py` | a medicao em bytes, com os 9 limites embutidos |
| `08_p2/README.md` | a fronteira medida, antes dos comandos |
| `08_p2/evidencias/` · `07_p1b/evidencias/` | recibos de corridas e preflights |

## 7. Onde o texto promete mais que o codigo entrega

1. **"read-only" e sobre o SSC+, nao sobre o CLI.** O envelope interno nasce
   `pode_escrever: False` e o runner nunca aplica patch. Mas o SSC+ **nao
   passa nenhuma restricao de escrita ao programa invocado**: o comando e
   `<executavel> exec <sua tarefa>`, rodando na pasta do repositorio. Se o
   CLI resolver escrever arquivo, nada aqui o impede.
2. **O README da raiz promete codex *e* kimi; a medicao entrega so codex.**
   Ele nao registra que o kimi jamais completou uma corrida; o README da P2
   registra.
3. **Nao existe comando para reproduzir a medicao.** `08_p2/medidor.py` e
   biblioteca, sem entrada de linha de comando; os numeros sairam de script
   de sessao que **nao esta no repositorio**. Os `medicao-p2*.json` guardam
   o resultado, nao a receita.
4. **O indice da raiz esta desatualizado** — lista so
   `08_p2/99_registro-p2.md`, e os registros da P2.1 e da P2.2, de onde vem
   os numeros da fronteira, nao aparecem.

> Documento descritivo: nao certifica, nao corrige, nao abre missao.
> Nenhum provedor foi invocado para escreve-lo; custo variavel zero.
