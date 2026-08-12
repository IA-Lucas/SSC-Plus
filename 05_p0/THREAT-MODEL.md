# Threat Model — SSC+ P0/P2

> Declaração explícita do que os mecanismos de integridade da P0 **fazem** e
> **não fazem**. Escopo: laboratório offline, isolado, sem rede, sem
> credenciais, providers falsos. Este documento é exigência do item 13 do
> hardening 0.2.1.

## 1. O que o hash/HMAC local cobre

- **CAS (sha256 endereçado por conteúdo)**: detecta **corrupção casual** de
  objetos (bitflip, truncamento, edição acidental, disco/filesystem falho).
  Leitura sempre re-verifica o hash; divergência = `CorrupcaoDetectada`
  (falha fechada).
- **EventLog (cadeia `prev_event_hash` + linha canônica)**: detecta
  **corrupção casual e edição acidental** do log — evento duplicado, fora de
  ordem, truncado ou adulterado quebra a verificação (IP-2/IP-4).
- **Selo HMAC (`chave_selo.bin`) do envelope e dos checkpoints**: detecta
  modificação casual/acidental desses artefatos por processos que **não**
  conhecem a chave.

## 2. O que NÃO está coberto (declarado)

- **Um atacante com acesso à `chave_selo.bin` ressela qualquer artefato.**
  O HMAC local **não** defende contra adversário com acesso à chave — a
  chave vive no mesmo diretório dos dados, por construção da P0.
- **Um atacante com escrita no disco do laboratório** pode reescrever log,
  CAS e checkpoints de forma consistente e indetectável pelos mecanismos
  locais (recomputa hashes e selos). A defesa contra isso é o **isolamento
  do laboratório** (Manifesto de Isolamento), não criptografia.
- **Não há autenticidade de origem**: nada aqui prova *quem* escreveu um
  evento — apenas que a cadeia é internamente consistente desde a gênese.
- **Scanner IC-4 é lista fechada de padrões**: detecção de segredo é
  best-effort determinística, **não** é prova de ausência de segredo.
- **Hash/HMAC não é controle de acesso**: o escritor único (lock + fencing)
  previne *corrupção por concorrência*, não *uso malicioso* por quem detém
  o lock.

## 3. Credenciais futuras — regra dura

Quando a P1+ introduzir providers reais, credenciais entram **somente por
referência/cofre** (ex.: nome de segredo em gerenciador externo, variável de
ambiente lida no momento do uso):

- **NUNCA** em objeto do CAS (imutável e replicável por construção);
- **NUNCA** em ContextPackage (vai para o provider e para a evidência);
- **NUNCA** em payload de evento (fica durável no EventLog para sempre);
- o scanner IC-4 permanece como **última linha** (recusa), não como
  mecanismo primário de proteção.

## 4. Resumo operacional

| Mecanismo | Detecta | NÃO detecta |
|---|---|---|
| CAS sha256 | corrupção casual de bytes | reescrita consistente por atacante |
| Cadeia prev_event_hash | adulteração casual do log | reescrita total da cadeia |
| HMAC selo | edição por quem não tem a chave | atacante com a chave |
| Lock + fencing token | escritor concorrente/obsoleto | titular malicioso do lock |
| Scanner IC-4 | padrões conhecidos de segredo | segredos fora dos padrões |

## 5. Extensao P2 (2026-08-11)

- O scanner IC-4 roda sobre a **entrada integral** antes do primeiro
  attempt, sobre a **saida integral** antes do CAS e dentro do proprio
  `CAS.gravar`. O resumo de 4.000 caracteres da WorkUnit nao e fronteira
  de seguranca.
- Entrada e saida produtivas tem teto de 1 MiB. A captura do subprocesso
  drena stdout/stderr em paralelo, conserva no maximo 1 MiB por canal e
  devolve falha de contrato quando excede o teto.
- Recibos rastreados nao persistem texto da resposta: somente tamanho e
  SHA-256. O CAS do lab ainda persiste conteudo aceito em claro, dentro de
  `08_p2/saidas/`, ignorado pelo Git. **Nao ha criptografia em repouso.**
- O preflight tem schema fechado e HMAC SHA-256 com chave local em
  `locks/preflight-hmac.key`; a janela nunca excede 24 h. Isso detecta
  edicao casual ou por processo sem a chave. Nao autentica contra outro
  processo do mesmo usuario, que pode ler a chave.
- Um mutex de arquivo separado serializa runners P2, e nomes incluem
  microssegundos mais aleatoriedade. Isso evita colisao/concorrencia
  acidental; nao impede um titular malicioso do mesmo usuario.
- `--tarefa-arquivo` aceita somente arquivo contido na raiz real do
  repositorio e recusa symlink/junction. Texto passado diretamente pela
  CLI continua visivel ao sistema operacional e ao historico do shell;
  para conteudo sensivel, a P2 nao oferece canal seguro e deve ser parada.
