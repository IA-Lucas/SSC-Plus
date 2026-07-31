#!/usr/bin/env python3
"""Gerador deterministico do pacote de revisao da P1-A.3.3 — SSC+ (experimental).

A P1-A.3.3 submete a revisao independente o ESTADO CORRIGIDO pela
P1-A.3.2: os seis MAJOR que a P1-A.3.1 deixou abertos foram corrigidos
em dois commits (`029ff44` e `ac03f3a`) e nenhum revisor ainda os viu.
`READY-FOR-REVIEW` nao e atestado — quem corrigiu nao certifica.

ALCANCE DO PACOTE. O alvo e `ac03f3a` (HEAD da P1-A.3.2), mas o diff
relevante NAO e o do par ALVO/PAI: seria apenas o segundo commit. O
conjunto que precisa de revisao e a correcao INTEIRA, de `BASE`
(`30107bd`, HEAD da P1-A.3.1, estado reprovado) ate `ALVO`. Por isso o
pacote publica os tres identificadores e o diff `BASE..ALVO`.

ANCORAGEM NO COMMIT (herdada do MAJOR #5, corrigido na P1-A.3.2). TODA
leitura vem do banco de objetos por `git cat-file blob <ALVO>:<path>` —
bytes exatos do blob, sem filtro de EOL e sem tocar o disco. Com
`core.autocrlf=true` os bytes em disco de um arquivo rastreado sao
funcao do historico de checkout, nao do commit; ler o disco foi o
defeito que reprovou a prova de ancoragem da P1-A.3.1. Consequencia
verificavel: o pacote e funcao dos commits e de mais nada — mutar a
arvore de trabalho nao muda um byte da saida, e um terceiro reproduz o
mesmo SHA-256 a partir de um checkout limpo.

O portao de identidade tambem e ancorado no commit, nunca no checkout:
exige que ALVO e BASE existam, que a paternidade ALVO->PAI confira e que
BASE seja ancestral de ALVO. O HEAD corrente e irrelevante — e o que
permite a um terceiro reproduzir o pacote depois de commits posteriores.

ORDEM, NORMALIZACAO E EXCLUSOES (declaradas, exigidas pelo ato):
- ORDEM: secoes em sequencia fixa escrita no codigo; `ARQUIVOS_COMPLETOS`
  na ordem literal da lista; `EVIDENCIAS_HASHEADAS` em `sorted()`.
- NORMALIZACAO: fonte unica sao os blobs (LF por construcao); saida
  gravada em UTF-8 sem BOM; nenhuma reconstrucao entre revisores.
- EXCLUSOES: nenhum timestamp, UUID, caminho absoluto, valor de
  ambiente, credencial, lock, cache ou runtime entra no pacote. As
  evidencias entram SOMENTE como hashes. O usuario local (forma longa e
  8.3) e o prefixo de caminho local sao redigidos.

Uso: python 06_p1a/evidencias/pacote_p1a33.py <saida.txt>
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Commit ALVO do pacote (HEAD da P1-A.3.2) e seu pai. Nome deliberado:
# nao e "HEAD" — o pacote e funcao DESTES commits, nao do checkout.
ALVO = "ac03f3a43a8ad5e1d2f54151450318b00ff7b859"
PAI = "029ff443f38da2ac2c8f89e08c2cf1a1a59b27c9"
# Estado reprovado pela P1-A.3.1: o inicio da correcao sob revisao.
BASE = "30107bd1ef30b07ab575ff5991e90d70345d702a"

# Pacote da rodada anterior (P1-A.3.1). Registrado para impedir
# equivalencia presumida: ele revisa 677c585 e NAO contem estas correcoes.
PACOTE_P1A31_SHA256 = (
    "c17b730ff8a060165332b08c35ba305f199021dc8b8cd90a55c53ad1a9141459")

USUARIO = os.path.basename(os.path.expanduser("~"))
USUARIO_CURTO = ("".join(c for c in USUARIO.upper() if c.isalnum())[:6]
                 + "~1")

# Os 9 arquivos alterados entre BASE e ALVO, embutidos POR INTEIRO
# (conteudo do blob em ALVO). Lista literal: sem glob, sem varredura de
# diretorio e sem `git status` — o conjunto do pacote nao pode depender
# do estado do disco.
ARQUIVOS_COMPLETOS = [
    "06_p1a/preflight_capsula.py",
    "06_p1a/preflight/adaptadores.py",
    "06_p1a/evidencias/contencao.py",
    "06_p1a/evidencias/pacote_p1a31.py",
    "06_p1a/evidencias/revisao_p1a3.py",
    "06_p1a/evidencias/revisao_p1a31.py",
    "06_p1a/tests/test_correcoes_p1a32.py",
    "06_p1a/tests/test_emendas_p1a3.py",
    "06_p1a/99_decisao-p1a32.md",
]

# Contexto nao alterado por esta correcao, mas necessario para julgar os
# bloqueios economicos e a trilha de tier declarado.
CONTEXTO_COMPLETO = [
    "06_p1a/tiers_declarados.json",
    "06_p1a/preflight/pipeline.py",
    "06_p1a/preflight/economia.py",
    "06_p1a/preflight/sombra.py",
    "06_p1a/escritor.py",
]

# Evidencias: entram SOMENTE como hashes do blob em ALVO.
EVIDENCIAS_HASHEADAS = [
    "06_p1a/99_decisao-p1a31.md",
    "06_p1a/99_decisao-p1a32.md",
    "06_p1a/evidencias/revisao-p1a31/codex-20260731T105702Z.json",
    "06_p1a/evidencias/revisao-p1a31/kimi-20260731T110318Z.json",
    "06_p1a/evidencias/revisao-p1a31/pacote-p1a31.txt",
    "06_p1a/evidencias/revisao-p1a31/registro-commit-p1a31.txt",
    "06_p1a/tiers_declarados.json",
]

SUITES = """\
Suites medidas pela P1-A.3.2 em CHECKOUT LIMPO do HEAD final ac03f3a
(worktree destacada — verde independentemente da copia de trabalho):

- P0:   python -m unittest discover -s 05_p0/tests   -> 100/100 OK
- P1-A: python -m unittest discover -s 06_p1a/tests  -> 342/342 OK
- Prova central: python 05_p0/cenarios/prova_central.py -> 18/18 OK

Linha de base medida na ABERTURA da P1-A.3.2 (HEAD 30107bd), registrada
pelo numero medido e nao pelo desejado:

- P0 100/100 OK | P1-A 306/307 FAILED | prova central 18/18 OK

A P1-A ja abria VERMELHA: o sentinela anti-P2 antigo acusava
`evidencias/pacote_p1a31.py`, arquivo que apenas MENCIONA o literal no
enunciado de uma pergunta. 342 = 307 anteriores + 35 novos.

A CONTAGEM E MEDIDA, NUNCA META. Conforme a §4.2.2 da
99_decisao-p1a31.md, `307/307` deixou de ser criterio de aceite valido:
o criterio e o sentinela medir comportamento, nao tamanho de lista.
"""

THREAT_REVIEW = """\
Threat review da P1-A.3.3 (revisao independente do estado corrigido):

| Ameaca | Mitigacao | Estado |
|---|---|---|
| Quem corrigiu certifica a propria correcao | A P1-A.3.2 emitiu READY-FOR-REVIEW, que explicitamente NAO e atestado; o fechamento de cada MAJOR depende de pronunciamento de revisor independente | coberto por construcao |
| Pacote reconstruido entre revisores (bytes divergentes) | Geracao unica e deterministica, executada 2x em diretorios descartaveis INDEPENDENTES, com bytes e SHA-256 identicos exigidos; os MESMOS bytes sao copiados para os dois descartaveis; cada revisor declara o SHA-256 recebido | coberto por construcao |
| Pacote nao reproduzivel a partir do commit (defeito que reprovou a P1-A.3.1) | Toda leitura via `git cat-file blob <ALVO>:<path>`; prova de ancoragem executada ANTES do envio: regeneracao em checkout limpo do commit deve bater com a geracao da arvore, e mutacao deliberada da arvore de trabalho NAO pode mudar o hash | verificado antes do envio |
| Pacote vaza PII, caminho local ou segredo | Fonte exclusivamente de conteudo git; evidencias somente como hashes; redacao do usuario local (forma longa e 8.3) e do prefixo de caminho local; zero valor de ambiente | coberto por construcao |
| Revisor escreve fora do diretorio descartavel | codex: `--sandbox read-only --ephemeral`; kimi: sem sandbox de filesystem no CLI (medido em `--help`) — restricao parcial (`--plan`, `--skills-dir` vazio, sem `-y/--yolo/--auto`) mais DETECCAO INTEGRAL por manifesto SHA-256 da arvore antes/depois, que REPROVA a corrida | mitigado; limite declarado |
| Chamada extra de modelo ou custo variavel | UMA chamada por provider, por assinatura; a capsula remove toda credencial de modelo do env-filho; nenhum PAYG, top-up, extra usage ou fallback pago | coberto por construcao |
| Tier declarado expirado no instante da chamada | Validade reverificada imediatamente antes de cada chamada; expirado = PARADA. Somente o proprietario renova | verificado nesta missao |
| Quota esgotada tratada como renovavel pela sessao | A quota do kimi encerrou em 403 na P1-A.3.1 e NAO e observavel ex ante no CLI 0.30.0 (medido: nenhum subcomando a expoe); a missao nao tenta via paga nem renovacao automatica | limite declarado |
| Lease morre durante a chamada longa ou a mutacao Git | Renovador dedicado (30 s, lease 120 s); `verificar_lock` com fence esperado IMEDIATAMENTE antes de cada persistencia; lease liberado somente apos arvore limpa pos-commit | coberto por construcao |
| Micro-commit tocar codigo, teste, politica ou historico | Missao probatoria: escritas restritas a evidencias, atestado e registro; staging explicito caminho a caminho; diff verificado antes do commit | coberto por verificacao |
"""

PERGUNTAS = """\
Avalie com olhar adversarial, citando arquivo e trecho.

CONTEXTO. A revisao anterior (P1-A.3.1) REPROVOU este trabalho com seis
MAJOR. Este pacote e o estado DEPOIS da correcao. Quem corrigiu nao
certifica: cabe a voce dizer se cada MAJOR fechou.

PARTE 1 — OS SEIS MAJOR, UM PRONUNCIAMENTO EXPLICITO PARA CADA UM.
Responda exatamente uma linha por item, no formato
`MAJOR-<n>: FECHADO | NAO-FECHADO — <justificativa curta citando trecho>`.

MAJOR-1 `06_p1a/preflight_capsula.py` — o atalho manual de google/grok
  montava relatorio SUPERVISED sem chamar `executar_preflight` nem
  `_config_persistida`, pulando as auditorias economicas. Corrigido por
  `classificar_frota`. A frota inteira passa mesmo pelas auditorias?
  Chave, endpoint PAYG ou auto-topup persistidos agora bloqueiam? A
  propriedade de zero sondas para google/grok foi preservada?
MAJOR-2 `06_p1a/preflight/adaptadores.py` — formatos como
  `0.0 tokens available` e `0% quota available` escapavam das regexes de
  esgotamento e casavam o sinal positivo, classificando quota zero como
  disponivel (fail-open). Corrigido por `_ZERO`. As duas ancoras estao
  corretas? Ha forma de quota zerada que ainda escape, ou franquia
  disponivel que agora bloqueie indevidamente?
MAJOR-3 `06_p1a/evidencias/contencao.py` + os dois runners — o cwd
  descartavel e a instrucao textual nao restringem o filesystem, e a
  lista de arquivos restantes so olhava DENTRO do descartavel. Corrigido
  por restricao parcial do CLI mais manifesto SHA-256 da arvore inteira.
  A deteccao tem ponto cego? A unica exclusao (`locks`) e legitima? O
  rotulo de enforcement afirma algo que o CLI nao sustenta?
MAJOR-4 `contencao.verificar_lock` e os chamadores — o lease era
  verificado so na abertura, e a chamada de provider excede a janela
  (256 s observados contra 120 s de lease). Corrigido com verificacao
  imediatamente antes de cada persistencia, com fence esperado. Ha
  caminho de gravacao que escape da verificacao?
MAJOR-5 `06_p1a/evidencias/pacote_p1a31.py` — o bloco de hashes de
  evidencia lia os bytes da ARVORE DE TRABALHO; com `core.autocrlf=true`
  4 de 11 hashes divergiam do conteudo versionado, e a prova de
  ancoragem falhou. Corrigido para `git cat-file blob`. O portao de
  identidade foi TROCADO (deixou de exigir `rev-parse HEAD == ALVO` e
  passou a exigir existencia do par e paternidade): isso e afrouxamento
  de guarda ou substituicao de um guarda que ficou vacuo? Justifique.
MAJOR-6 `06_p1a/tests/test_emendas_p1a3.py` — o sentinela anti-P2
  comparava CONJUNTO DE CAMINHOS com allowlist fixa; falhava nos dois
  sentidos (falso positivo por mencao documental, falso negativo para
  consumidor escrito dentro da allowlist). Reescrito para medir
  comportamento por AST em duas metades. A analise por AST tem furo
  explorável? A metade (A) deveria cobrir `07_p1b` tambem?

PARTE 2 — DEFEITO NOVO INTRODUZIDO PELA CORRECAO.
As correcoes introduziram defeito novo, regressao, ou enfraqueceram
alguma garantia que existia antes? Responda uma linha:
`DEFEITO-NOVO: SIM | NAO — <o que, onde>`. Olhe em especial para o que
foi TROCADO e nao apenas acrescentado.

PARTE 3 — EIXOS DE AVALIACAO DO ESTADO EXATO.
Avalie e reporte achados nestes eixos: (1) cobranca e custo variavel;
(2) credenciais e vazamento; (3) falha fechada; (4) tier declarado e sua
janela; (5) descoberta de modelo; (6) quotas; (7) anti-P2 — a trilha de
observacao-sombra nao pode virar autorizacao plena, subir o teto de
provider supervisionado nem habilitar execucao autonoma; (8) isolamento
do revisor; (9) escritor unico, lease e fencing; (10) evidencia e sua
ancoragem; (11) testes — a cobertura acompanha o codigo, e alguma
expectativa foi enfraquecida?; (12) autorizacao de P1-B em modo sombra:
este estado autoriza reabrir a P1-B-02 em observacao-sombra, ou nao?

FORMATO DA RESPOSTA (obrigatorio, nesta ordem).
Primeiro, uma linha cada:
PROVIDER: <seu provider>
MODELO-OBSERVADO: <o modelo que voce observa ser; se nao observavel, escreva DESCONHECIDO>
CANAL: <canal de acesso>
PACOTE-SHA256: <SHA-256 de ./pacote-revisao.txt — compute-o>
ESCOPO: <o que voce revisou>
Depois as seis linhas `MAJOR-<n>:` da PARTE 1, a linha `DEFEITO-NOVO:`
da PARTE 2, e entao um achado por linha, prefixado por severidade
CRITICAL | MAJOR | MINOR | OBS, com arquivo:tema e descricao curta.
Para cada MINOR, classifique bloqueante ou nao-bloqueante, com motivo.
Se nao houver achado num nivel, nao o invente.
Termine com: VEREDITO: APROVADO | APROVADO-COM-RESSALVAS | REPROVADO
"""


def _redigir(texto: str) -> str:
    """Redige usuario local (longa e 8.3) e o prefixo de caminho local.

    A redacao atinge SOMENTE o pacote; o repositorio permanece intacto.
    O codigo versionado contem um caminho local em `preflight_capsula`,
    que nao pode vazar para o revisor.
    """
    return ((texto or "").replace(USUARIO, "<USUARIO>")
            .replace(USUARIO_CURTO, "<USUARIO>")
            .replace("E:\\LucasIA", "<CAMINHO-LOCAL>")
            .replace("E:/LucasIA", "<CAMINHO-LOCAL>"))


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True).stdout


def _blob(rel: str) -> bytes:
    """Bytes EXATOS do blob versionado em ALVO — nunca o disco.

    Esta funcao e a ancoragem do pacote: `git cat-file blob` devolve o
    objeto cru, sem passar pelo filtro de EOL e sem depender de
    `core.autocrlf`. Trocar por leitura de arquivo reintroduz o MAJOR #5.
    """
    return subprocess.run(
        ["git", "cat-file", "blob", f"{ALVO}:{rel}"], cwd=RAIZ,
        capture_output=True, check=True).stdout


def _conteudo_alvo(rel: str) -> str:
    return _blob(rel).decode("utf-8", errors="replace")


def montar_pacote() -> str:
    # Portao de identidade ANCORADO NOS COMMITS, nao no checkout.
    try:
        pai_de_alvo = _git("rev-parse", f"{ALVO}^").strip()
        tree = _git("rev-parse", f"{ALVO}^{{tree}}").strip()
        _git("rev-parse", "--verify", f"{BASE}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"PARADA: commit alvo {ALVO} ou base {BASE} ausente") from exc
    if pai_de_alvo != PAI:
        raise SystemExit(
            f"PARADA: pai inesperado de {ALVO}: {pai_de_alvo} != {PAI}")
    if subprocess.run(["git", "merge-base", "--is-ancestor", BASE, ALVO],
                      cwd=RAIZ).returncode != 0:
        raise SystemExit(
            f"PARADA: {BASE} nao e ancestral de {ALVO}")

    sujeito_alvo = _git("log", "-1", "--format=%s", ALVO).strip()
    sujeito_pai = _git("log", "-1", "--format=%s", PAI).strip()
    sujeito_base = _git("log", "-1", "--format=%s", BASE).strip()
    diff = _git("diff", BASE, ALVO)
    partes = [
        "PACOTE DE REVISAO — SSC+ P1-A.3.3 (laboratorio experimental, "
        "sem autoridade)\n",
        "Missao: revisao INDEPENDENTE do estado corrigido pela P1-A.3.2. "
        "A revisao anterior (P1-A.3.1) reprovou com SEIS MAJOR; este "
        "pacote e o estado depois da correcao. `READY-FOR-REVIEW` nao e "
        "atestado: quem corrigiu nao certifica. Correcao nao fecha por "
        "ter sido feita — fecha por revisor dizer que fechou.\n",
        "\n=== Identidade dos commits ===\n",
        f"ALVO (HEAD revisado): {ALVO}\n",
        f"  sujeito: {sujeito_alvo}\n",
        f"PAI do alvo:          {PAI}\n",
        f"  sujeito: {sujeito_pai}\n",
        f"BASE (estado reprovado pela P1-A.3.1): {BASE}\n",
        f"  sujeito: {sujeito_base}\n",
        f"tree do ALVO:         {tree}\n",
        "sem tag e sem remoto (verificado na abertura da missao)\n",
        "O diff abaixo e BASE..ALVO: a correcao INTEIRA dos seis MAJOR, "
        "distribuida em dois commits. O par ALVO/PAI sozinho mostraria "
        "apenas o segundo.\n",
        "\n=== Pacote da rodada anterior (NAO equivale a este) ===\n",
        f"SHA-256 do pacote da P1-A.3.1: {PACOTE_P1A31_SHA256}\n",
        "Aquele pacote revisa o commit 677c585 e NAO contem nenhuma "
        "destas correcoes. Nenhuma equivalencia pode ser presumida.\n",
        "\n=== Suites ===\n", SUITES,
        "\n=== Threat review ===\n", THREAT_REVIEW,
        "\n=== Perguntas de revisao ===\n", PERGUNTAS,
        "\n=== Hashes SHA-256 das evidencias (blob em ALVO) ===\n",
    ]
    for rel in sorted(EVIDENCIAS_HASHEADAS):
        partes.append(f"{hashlib.sha256(_blob(rel)).hexdigest()}  {rel}\n")
    partes.append("\n=== Diff integral BASE..ALVO ===\n")
    partes.append(diff)
    partes.append("\n=== Arquivos alterados — conteudo completo em ALVO "
                  "===\n")
    for rel in ARQUIVOS_COMPLETOS:
        partes.append(f"\n--- {rel} ---\n")
        partes.append(_conteudo_alvo(rel))
    partes.append("\n=== Contexto nao alterado — conteudo completo em "
                  "ALVO ===\n")
    for rel in CONTEXTO_COMPLETO:
        partes.append(f"\n--- {rel} ---\n")
        partes.append(_conteudo_alvo(rel))
    return _redigir("".join(partes))


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: pacote_p1a33.py <saida.txt>", file=sys.stderr)
        return 2
    dados = montar_pacote().encode("utf-8")
    Path(sys.argv[1]).write_bytes(dados)
    print(hashlib.sha256(dados).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
