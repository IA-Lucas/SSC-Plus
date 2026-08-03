# SSC+ P2 — usar a frota (experimental, sem autoridade)

> Laboratorio experimental. Nada aqui e norma. A P2 foi aberta pelo ato
> soberano de 2026-08-03 ([`00_ato-soberano-p2.md`](00_ato-soberano-p2.md)),
> que autoriza invocacao produtiva por **codex** e **kimi**, dentro da
> capsula, em modo supervisionado. **Chamada de API paga continua
> PROIBIDA** — a politica economica nao foi tocada.

## LEIA ANTES DE RODAR — tres limites que valem hoje

Estao aqui, e nao no rodape, porque quem vem usar a P2 segue os tres
passos abaixo e pode nunca rolar ate o fim. Os tres sao **medidos**, com
data e evidencia; nenhum e precaucao generica.

### 1. A economia de TOKEN nao esta medida

Nenhum dos dois CLIs reporta contagem de token. `tokens_reportados` sai
`None` em toda invocacao — por honestidade, jamais zero por conveniencia.

O que existe e uma **proxy**, que nao e a medicao: `08_p2/medidor.py`
conta a **carga de fronteira** em bytes e caracteres. **Uma** corrida
comparada, em 2026-08-03 (`08_p2/evidencias/medicao-p21-*.json`) — ler o
arquivo `05_p0/ssc_p0/eventlog.py` e resumi-lo em ate 8 linhas:

| | bytes utf-8 |
|---|---|
| o que o despachante pagou ao despachar | **872** |
| o que o outro canal gastaria fazendo a MESMA tarefa sozinho | **7.653** |
| poupanca na fronteira | **6.781** — razao **8,78x** |

A poupanca e, quase inteira, o turno interno: os 6.184 B do arquivo que a
assinatura leu por conta propria e o despachante nao precisou ingerir.

**Nao cite esse 8,78x sozinho.** Byte nao e token; `n = 1`; e a proxy
declara **oito** coisas que nao captura — entre elas raciocinio, contexto
reenviado e cache, que e onde a economia de verdade mora. Os oito viajam
DENTRO da saida de `comparar`, de proposito: o numero nao circula sem os
proprios limites.

A tese central do projeto — despachar para a assinatura poupa token de
outro canal — segue **NAO MEDIDA em token**. O que ha e uma corrida, numa
proxy declarada, apontando na direcao dela.

### 2. A frota e codex-only enquanto a franquia do kimi estiver esgotada

Medido em **2026-08-03T11:56Z**
(`08_p2/evidencias/execucao-20260803T115622Z.json`): com `--capacidade
volume`, que puxa o kimi primeiro, o kimi devolveu `falha-quota` e a
maquina rerroteou sozinha para o codex, que concluiu. Mesma medicao de
2026-08-03T02:38Z, agora repetida.

Consequencia pratica: **`kimi -p` nunca foi validado num caminho de
sucesso**. Sabe-se que o argv chega ao provedor — o erro veio do
provedor, nao do parser — e nada alem disso. Enquanto isso valer, pedir
`--capacidade volume`, `contexto-extenso` ou `engenharia-reversa` custa
uma tentativa perdida antes do fallback; nao e erro, e o preco do
mecanismo funcionando.

### 3. Ninguem certificou a P2

Quem construiu nao certifica — regra do `CLAUDE.md` da raiz. A P2.0
escreveu o codigo, os testes e a propria evidencia; a P2.1 escreveu o
medidor e mediu as corridas acima. **Nenhuma revisao independente passou
por nada disso.** Nao existe atestado de aprovacao da P2, e este README
nao e um.

## Os tres passos, em PowerShell

### 1. Declarar o tier (ato do proprietario, vale 24 h)

O codigo **nunca** infere o tier. Edite `06_p1a/tiers_declarados.json` e
ponha o instante atual em `declarado_em_utc` das duas declaracoes:

```powershell
cd E:\LucasIA\Projetos\SSC-Plus
Copy-Item 06_p1a\tiers_declarados.json `
  "06_p1a\evidencias\backups\tiers_declarados-$(Get-Date -Format 'yyyy-MM-dd')-pre-renovacao.json"
python -c "import datetime;print(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
```

Declaracao vencida = `P1A-DECLARACAO-EXPIRADA` e a frota volta a BLOCKED,
sozinha. Isso e o mecanismo funcionando, nao defeito.

### 2. Segurar o lease e rodar o preflight

O lease e **escritor unico** e precisa ficar vivo durante toda a operacao.
Abra um terminal so para ele:

```powershell
python 06_p1a\evidencias\renovador_lock.py p2-ops
```

Noutro terminal, o preflight — so diagnostico, zero chamada de modelo:

```powershell
$env:SSC_LOCK_SESSAO = "p2-ops"
python 06_p1a\capsula.py python 07_p1b\preflight_atual.py
```

Ele imprime o caminho da evidencia. Guarde-o.

### 3. Despachar a tarefa

```powershell
python 06_p1a\capsula.py python 08_p2\runner_p2.py `
  --preflight 07_p1b\evidencias\preflight-<data>.json `
  --tarefa "o que voce quer feito" `
  --criterio "como saber se ficou bom"
```

| flag | efeito |
|---|---|
| `--tarefa` / `--tarefa-arquivo` | o prompt (um dos dois, nunca os dois) |
| `--criterio` | criterio de aceite, **CONGELADO** na WorkUnit |
| `--capacidade` | preferencia de rota: `implementacao`/`operacao-repo` puxam codex; `volume`/`contexto-extenso`/`engenharia-reversa` puxam kimi |
| `--papel` | `autor` (padrao), `revisor`, `juiz` |
| `--timeout` | teto de parede por invocacao (padrao 900 s) |
| `--validade-h` | idade maxima do preflight (padrao 24 h) |

## O que acontece sozinho

- **quota esgotada** num provedor → nova `RoutingDecision` para o outro,
  dentro do envelope, com a linhagem preservada. Sem assinatura capaz =
  `STOP_WAIT_RESET`. **Nunca** migra para API paga;
- **falha transitoria** → retry com backoff, no maximo 3, e so sob IR-1
  (idempotency key ou efeito comprovadamente nao aplicado);
- **timeout** → `indeterminado`, escalonamento, **sem** retry automatico:
  uma tarefa que talvez tenha rodado nao roda de novo por conta propria;
- **preflight velho** → PARADA. Veredito de ontem nao autoriza gasto de
  hoje.

Cada corrida grava evidencia redigida em `08_p2/evidencias/` (caminho do
usuario vira `<CAMINHO-LOCAL>`) e um laboratorio proprio em
`08_p2/saidas/labs/` (fora do Git — carrega saida crua de modelo).

## Limites que voce precisa saber antes de confiar

1. **claude, google e grok nao entram.** Teto `SUPERVISED` de
   especificacao; google e grok nunca foram sequer sondados;
2. **`executor_observado` e sempre `None`.** O CLI nao ecoa qual modelo
   serviu a chamada, entao o guarda de divergencia da P0 (0.2.1-9) **nao
   dispara** para a P2. Voce sabe qual modelo foi *resolvido*, nao qual
   respondeu;
3. **nao ha contagem de token.** Nenhum dos dois CLIs reporta, e o campo
   sai `None`. O placar da EvidencePlane conta ausencia como zero e rotula
   o total `simulado` — divergencia registrada, nao corrigida. A P2.1 nao
   corrigiu isso: ela construiu uma PROXY de bytes ao lado
   (`08_p2/medidor.py`), com os proprios limites declarados. Ver o item 1
   do bloco no topo;
4. **o contexto nao e enviado.** O prompt e a `--tarefa`; o
   `ContextPackage` da WorkUnit nao vai ao CLI;
5. **read-only.** O envelope nasce `pode_escrever: False`. A P2 responde;
   nao aplica patch;
6. **a franquia do kimi estava ACABADA** nas medicoes de 2026-08-03
   (02:38Z e 11:56Z), entao `kimi -p` nunca foi validado num caminho de
   sucesso. Ver o item 2 do bloco no topo;
7. **quem construiu nao certificou.** Nenhuma revisao independente foi
   feita sobre a P2 — nem sobre a P2.0, nem sobre a P2.1. Ver o item 3
   do bloco no topo;
8. **dois guardas da P2.0 estavam pela metade**, medido pela reversao
   vermelha da P2.1: o teto de custo zero podia ser AFROUXADO sem
   vermelho nenhum, e a correcao de codificacao prendia a primitiva
   `decodificar` mas nao o ponto de chamada `sensor_subprocess`. Os dois
   foram fechados com teste, sem tocar producao. O que isso ensina sobre
   o resto do acervo — quantos outros guardas estao na mesma condicao —
   **nao foi medido**.
