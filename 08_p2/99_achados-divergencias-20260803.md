---
id: SSC-ACH-P2-DIV-20260803
titulo: Quatro divergencias texto-codigo, registradas como achados
tipo: registro-de-achados (NAO e atestado, NAO e missao)
versao: 1.0.0
origem: laboratorio-ssc-plus
autoridade: nenhuma
normativo: nao
criado_em: 2026-08-03
---

# Achados — divergencias entre o que o texto promete e o que o codigo faz

> **NADA IMPEDE A ESCRITA HOJE.** Medido no codigo: o SSC+ nao passa
> nenhuma restricao de filesystem ao CLI invocado, nao troca o diretorio
> de trabalho, nao vigia a arvore durante a corrida e registra
> `efeito_externo: "nenhum"` **por declaracao**, sem olhar o disco. O
> processo do provedor herda o diretorio do terminal — a **raiz deste
> repositorio** — e o token do usuario do Windows.
>
> Registro **aditivo**: nenhum documento anterior foi aberto para escrita.
> Nenhum achado e corrigido aqui, nenhuma missao e aberta, nenhum provedor
> foi invocado. Custo variavel: **zero**.

## 1. A medicao de (a) — mecanismo, nao intencao

### 1.1 O que a capsula restringe DE FATO

Somente **nomes de variavel de ambiente**. `capsula.verificar_capsula`
(`06_p1a/capsula.py:43`) devolve os nomes que `economia._nome_payg`
reprova; `ambiente_capsula` (`:52`) copia o ambiente sem eles e reaudita o
resultado. `frota.ambiente_sanitizado` (`05_p0/ssc_p0/frota.py:76`) repete
a filtragem no subprocesso — defesa em profundidade, do mesmo eixo.

**Nao ha uma linha sobre filesystem em nenhum dos dois.** A capsula nao
cria diretorio, nao muda permissao, nao usa token restrito, nao define
`cwd`. Ela impede **credencial paga**, e so.

### 1.2 O diretorio de trabalho do processo filho

Herdado duas vezes, medido no fonte:

| elo | chamada | `cwd` |
|---|---|---|
| capsula → runner | `capsula.py:111` `iniciar_em_capsula(sys.argv[1:])` | parametro `cwd` fica `None` (`:87`, `:98`) → herda o terminal |
| runner → CLI | `provedor_assinatura.py:140` `subprocess.run(list(argv), env=…, capture_output=True, timeout=…)` | **argumento `cwd` ausente** → herda o runner |

Pelo passo 3 do `08_p2/README.md`, o terminal esta em
`E:\LucasIA\Projetos\SSC-Plus`. Logo o CLI roda **na raiz do repositorio**,
com o token do usuario do Windows — sem rebaixamento de privilegio em
nenhum ponto da cadeia.

### 1.3 O argv nao carrega restricao

`ProvedorAssinaturaReal.argv` (`provedor_assinatura.py:210`) monta
`argv_de(espec, list(espec.headless) + [prompt])`, e
`frota_real.py:64` declara `headless=("exec",)`. O comando efetivo e:

    <caminho do codex.exe>  exec  <a tarefa>

Sem `--sandbox`, sem `--cd`, sem `--ephemeral`, sem
`--skip-git-repo-check`.

### 1.4 O MESMO acervo faz certo no outro caminho — e e isso que classifica

A P1-A ja resolveu este problema, e a P2 nao herdou nada:

| protecao | P1-A (`prova_minima.py:46`, `revisao_p1a3/31/33/36`) | P2 (`runner_p2.py`) |
|---|---|---|
| flag de sandbox | `--sandbox read-only` | **ausente** |
| diretorio descartavel | `--cd <tmp>` + `cwd=tmp` (`revisao_p1a36.py:187`) | **ausente** — herda a raiz |
| efemero | `--ephemeral` | **ausente** |
| vigilancia da arvore | `Vigilancia(RAIZ, sessao)` abre e fecha em volta da invocacao e devolve `mutacoes_fora_do_descartavel` (`contencao.py:285`) | **ausente** — `Vigilancia` tem **zero** usos em `08_p2/` e `07_p1b/` |
| arquivos deixados | `dir_descartavel_arquivos_restantes` listado na evidencia | **nao existe campo** |

A P1-A tambem vigiava seis caminhos fora do repositorio
(`contencao.py:87`): `~/.codex/auth.json`, `~/.codex/config.toml`,
`~/.claude/settings.json`, `~/.kimi-code/config.toml`,
`~/.gemini/settings.json`, `~/.grok`. A P2 nao vigia nenhum.

### 1.5 Nem depois se mede — e aqui esta a familia (F)

`classificar` (`provedor_assinatura.py:153`) devolve
`efeito_externo = "nenhum"` para **todo** `rc == 0`, e a propria docstring
diz por que: *"porque a P2 opera em modo read-only por envelope"*. O
envelope declara read-only (`comum.py:81`, `pode_escrever: False`); a
classificacao repete a declaracao; o recibo grava `"efeito_externo":
"nenhum"` — **sem que nada tenha olhado o disco**.

O registro confirma a suposicao que o produziu. E o MAJOR #3 na forma
literal: a propriedade e **afirmada**, nunca **exercida**.

### 1.6 Onde o provedor poderia escrever

Qualquer lugar em que o usuario do Windows escreve. Caminho relativo cai
na raiz do repositorio — inclusive sobre o estado de que os proprios
guardas dependem:

| alvo | por que importa |
|---|---|
| `locks/*.lease`, `locks/*.fence` | e o escritor unico; e o que `verificar_lock` le para decidir se pode gravar |
| `06_p1a/tiers_declarados.json` | a declaracao do proprietario, que o codigo jura nunca inferir |
| `07_p1b/evidencias/`, `08_p2/evidencias/` | os recibos — a unica prova de que a corrida existiu |
| `scratchpad/MUTANTE-ATIVO.txt` | o registro que toda retomada apos queda le antes de medir |
| `05_p0/`, `06_p1a/`, `08_p2/` | o fonte dos guardas |
| `E:/LucasIA/Projetos/LucaX Enterprise OS` | a fonte canonica, somente-leitura **por carta**, nao por mecanismo |

### 1.7 O que NAO foi medido

- **O que o `codex exec` faz por conta propria.** Medir exigiria invocacao
  real, e a ordem proibiu queimar franquia para isto. Registrado como
  **NAO MEDIDO**. Nota de contexto: a P1-A **nao dependeu** desse padrao —
  passou a flag explicitamente.
- **Config do CLI, lida fora do repositorio** (`~/.codex/config.toml`, 138
  linhas): nao ha `sandbox_mode` nem `approval_policy`. Ha `[windows]
  sandbox = "elevated"` (`:89`), que nao e restricao de leitura, e uma
  lista `projects.*.trust_level` que **nao inclui**
  `e:\lucasia\projetos\ssc-plus` — mas **inclui**
  `e:\lucasia\projetos\lucax enterprise os`. O efeito desses campos sobre
  `exec` e propriedade do CLI externo: **NAO MEDIDO**. E, seja qual for,
  vive num arquivo fora deste repositorio que qualquer processo altera —
  nao e mecanismo que o SSC+ controle.
- **Se alguma corrida ja escreveu.** As nove corridas correram sem
  `Vigilancia`; nao ha fotografia de antes e depois. Nao ha como afirmar
  nem negar.

## 2. Os quatro achados

Classificacao por familia conforme o `CLAUDE.md` da raiz: **(F)** afirma
em vez de exercer · **(N)** classe que a varredura dos 86 guardas nao
media · **fora de ambas**.

| # | Achado | Severidade | Familia | Dono | Gatilho |
|---|---|---|---|---|---|
| **A** | `read-only` nao restringe o CLI invocado: sem flag de sandbox, sem diretorio descartavel, sem vigilancia, e `efeito_externo: "nenhum"` gravado por declaracao | **ALTA** | **(F)** | missao de correcao da P2 | **ja disparado** — vale em toda corrida do runner |
| **B** | README da raiz (`:48`) promete invocacao produtiva por `codex` **e** `kimi`; o kimi nunca completou uma corrida (`falha-quota` em 02:38Z e 11:56Z de 2026-08-03) | BAIXA | fora de ambas | missao que tocar o README da raiz | proxima edicao do README da raiz, ou a primeira corrida de sucesso do kimi — o que vier antes |
| **C** | `08_p2/medidor.py` nao tem entrada de linha de comando; os numeros da fronteira sairam de script de sessao ausente do repositorio. O revisor recebe `medicao-p2*.json` e nao a receita | MEDIA | fora de ambas | missao que entregar medicao a revisor | montagem do proximo pacote de revisao independente |
| **D** | Indice da raiz lista so `08_p2/99_registro-p2.md`; os registros da P2.1 e da P2.2 — de onde vem os numeros da fronteira — nao aparecem | BAIXA | fora de ambas | missao que tocar o indice da raiz | proxima leitura do repositorio por terceiro |

**Remedio especificado, nao executado:**

- **A** — passar ao codex `--sandbox read-only --cd <descartavel>
  --skip-git-repo-check --ephemeral`, rodar com `cwd` no descartavel, e
  envolver a invocacao em `Vigilancia`. Para o **kimi** a flag nao existe
  (`--sandbox` = `unknown option`, medido na P1-A.3.4), entao ali o remedio
  e rotulo honesto + `Vigilancia`, jamais afirmar sandbox inexistente. E
  `classificar` para de devolver `efeito_externo: "nenhum"` sem medicao.
- **B** — o README da raiz cita o que foi medido, ou aponta para o item 2
  do `08_p2/README.md`.
- **C** — o comando que produz a medicao entra no repositorio, com o
  proprio fonte referenciado na evidencia. **E o mesmo defeito do MAJOR #5
  / N6** — pacote que pede julgamento e omite o objeto julgado.
- **D** — indice atualizado.

## 3. O que este registro NAO e

Esta sessao escreveu o `COMO-FUNCIONA.md` e achou estas quatro
divergencias na mesma leitura: **nao e revisao independente**, e o
criterio de parada fala da proxima revisao independente. A contagem, para
constar: **1 em (F)**, **0 em (N)**, **3 fora de ambas** — nenhum criterio
disparado ((a) exige 6+, (b) exige 4+ em (F)).

Nenhum dos quatro fecha aqui. Quem mede nao certifica.
