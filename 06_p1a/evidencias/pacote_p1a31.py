#!/usr/bin/env python3
"""Gerador deterministico do pacote de revisao da P1-A.3.1 — SSC+ (experimental).

A P1-A.3.1 fecha a unica lacuna da P1-A.3: o commit final (HEAD 677c585)
contem correcoes POSTERIORES ao ultimo pacote revisado (SHA-256 2c8061c0...
nas evidencias codex-20260731T031305Z e kimi-20260731T031551Z). Este
script monta, a partir do HEAD e SOMENTE de conteudo versionado, um unico
pacote de revisao com:

- identidade do commit/tree (HEAD, pai, tree);
- diff integral contra o pai;
- conteudo completo de todos os arquivos funcionais/politicos/testes
  alterados no commit;
- resultados das suites reexecutadas nesta missao (texto estatico);
- threat review da P1-A.3.1 (texto estatico);
- hashes SHA-256 das evidencias relevantes da P1-A.3.

DETERMINISMO: nenhum timestamp, nenhum caminho absoluto, nenhum dado de
ambiente entra no pacote; toda a leitura e via `git show`/`git diff`
(conteudo versionado, LF) e as listas sao ordenadas. Duas geracoes
devem produzir SHA-256 identico. O usuario local (forma longa e 8.3) e
redigido. Nenhum segredo ou valor de ambiente entra no pacote: a fonte
e exclusivamente o conteudo git (ja varrido pela ZeroPii na P1-A.3) e
hashes de evidencias.

Uso: python 06_p1a/evidencias/pacote_p1a31.py <saida.txt>
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

HEAD = "677c5853cf3d504696e7d2e326287cc1a8a37f38"
PAI = "c4fa5a0615d834ee33561a5ec9c93b2b8d95430f"
PACOTE_ANTERIOR_SHA256 = (
    "2c8061c0a5aaa52e23a6710e42b1384433135e9a30579cafee7033a188316016")

USUARIO = os.path.basename(os.path.expanduser("~"))
USUARIO_CURTO = ("".join(c for c in USUARIO.upper() if c.isalnum())[:6]
                 + "~1")

# Arquivos funcionais/politicos/testes alterados no commit 677c585,
# embutidos POR INTEIRO no pacote (conteudo do HEAD, via git show).
ARQUIVOS_COMPLETOS = [
    "06_p1a/preflight/__init__.py",
    "06_p1a/preflight/adaptadores.py",
    "06_p1a/preflight/economia.py",
    "06_p1a/preflight/frota_real.py",
    "06_p1a/preflight/pipeline.py",
    "06_p1a/preflight/sombra.py",
    "06_p1a/preflight_capsula.py",
    "06_p1a/tiers_declarados.json",
    "06_p1a/tests/apoio.py",
    "06_p1a/tests/test_adaptadores.py",
    "06_p1a/tests/test_capsula_p1a2.py",
    "06_p1a/tests/test_economia.py",
    "06_p1a/tests/test_emendas_p1a3.py",
    "06_p1a/tests/test_estabilizacao_p1a1.py",
    "06_p1a/tests/test_falhas_obrigatorias.py",
    "06_p1a/tests/test_pipeline.py",
    "06_p1a/tests/test_preflight.py",
]

# Evidencias relevantes da P1-A.3: entram SOMENTE os hashes (o conteudo
# ja foi revisado nas 5 rodadas; o pacote final revisa o estado exato).
EVIDENCIAS_HASHEADAS = [
    "06_p1a/evidencias/revisao-p1a3/codex-20260731T020226Z.json",
    "06_p1a/evidencias/revisao-p1a3/codex-20260731T021442Z.json",
    "06_p1a/evidencias/revisao-p1a3/codex-20260731T023445Z.json",
    "06_p1a/evidencias/revisao-p1a3/codex-20260731T025443Z.json",
    "06_p1a/evidencias/revisao-p1a3/codex-20260731T031305Z.json",
    "06_p1a/evidencias/revisao-p1a3/kimi-20260731T021718Z.json",
    "06_p1a/evidencias/revisao-p1a3/kimi-20260731T023822Z.json",
    "06_p1a/evidencias/revisao-p1a3/kimi-20260731T025833Z.json",
    "06_p1a/evidencias/revisao-p1a3/kimi-20260731T031551Z.json",
    "06_p1a/evidencias/p1a3-preflight-20260731T032516Z.json",
    "06_p1a/tiers_declarados.json",
]

SUITES = """\
Resultados das suites reexecutadas nesta missao (P1-A.3.1, sobre o HEAD
677c585, antes da montagem deste pacote):

- P0:   python -m unittest discover -s 05_p0/tests   -> Ran 100 tests, OK (100/100)
- P1-A: python -m unittest discover -s 06_p1a/tests  -> Ran 307 tests, OK (307/307)
- Prova central: python 05_p0/cenarios/prova_central.py -> 18 assercoes, OK (18/18)
  (o JSON da prova contem UUIDs por corrida; o arquivo versionado foi
  restaurado apos a reexecucao — a arvore permanece limpa)
"""

THREAT_REVIEW = """\
Threat review da P1-A.3.1 (revisao do estado final exato):

| Ameaca | Mitigacao | Estado |
|---|---|---|
| Commit 677c585 ocorreu apos a liberacao do lease da P1-A.3: uma corrida teria alterado o estado revisado | Identidade HEAD/pai/arvore verificada na abertura desta missao; nenhuma corrida observada; regra prospectiva: staging, commit e pos-verificacao SEMPRE sob lease vivo | mitigado (verificacao + regra prospectiva) |
| Pacote reconstruido entre revisores (bytes divergentes) | Geracao unica e deterministica (executada 2x, SHA-256 identico exigido); os MESMOS bytes sao copiados para os dois diretorios descartaveis; cada reviewer declara o SHA-256 do pacote recebido; divergencia de hash interrompe a missao | coberto por construcao |
| Pacote vaza PII, caminho local ou segredo | Fonte exclusivamente de conteudo git (varrido pela ZeroPii na P1-A.3); redacao do usuario local (forma longa e 8.3); evidencias entram SOMENTE como hashes; zero valor de ambiente | coberto por construcao |
| Reviewer escreve fora do diretorio descartavel | codex: `--sandbox read-only --ephemeral`; kimi: sem modo read-only headless — cwd descartavel vazio + instrucao explicita de somente leitura + politica `auto` com regras estaticas de deny; arquivos restantes registrados como evidencia | mitigado (declarado) |
| Chamada extra de modelo ou custo variavel | UMA chamada por provider, via assinatura OAuth; a capsula remove TODA credencial de modelo do env-filho (ambiente global/HKCU intacto) | coberto por construcao |
| Tier declarado expirado no instante da chamada | Validade verificada antes de cada chamada (declaracoes expiram 2026-08-01T01:31:00Z); se expirado, PARADA — somente o proprietario renova | verificado nesta missao |
| Lock morre durante a mutacao Git | Renovador dedicado (30 s, lease 120 s) cobre staging, commit e pos-verificacao; o lease so e liberado apos arvore limpa comprovada | coberto por construcao |
| Micro-commit tocar codigo/teste/config/historico | Diff do staging verificado como exclusivamente probatorio (atestado novo, decisao nova, evidencias de revisao novas, ferramentas da missao) ANTES do commit; `99_decisao-p1a3.md` intocada | coberto por verificacao |
"""

PERGUNTAS = """\
Avalie com olhar adversarial, citando arquivo/trecho. Este pacote revisa
o ESTADO FINAL EXATO da P1-A.3 (commit 677c585): a ultima revisao
incidiu sobre um pacote anterior a correcoes finais.

1. O diff integral contra o pai contem algo que enfraqueca os bloqueios
   economicos (PAYG, capsula subscription-only, conflito env x login,
   quota esgotada) ou a politica NVIDIA? As mudancas posteriores a
   ultima revisao sao estritamente fail-closed (mais restritivas, nunca
   mais permissivas)?
2. A trilha SHADOW_ELIGIBLE pode virar ELIGIBLE em algum caminho, subir
   o teto de algum provider SUPERVISED, ou autorizar P2/execucao
   autonoma?
3. Testes: alguma expectativa foi enfraquecida alem do que a decisao
   soberana rebaixou (claude ELIGIBLE -> SUPERVISED; google/grok sem
   sondas)? A cobertura acompanha o codigo?
4. Ha segredo, PII ou caminho local vazando para qualquer arquivo do
   changeset, excecao ou artefato?
5. A declaracao de tiers (validade maxima 24 h, janela efetiva
   min(declarada, 24 h)) e fail-closed contra timestamp ilegivel,
   futuro, expirado e fronteira exata?
6. O threat review da P1-A.3.1 (acima) cobre as ameacas desta missao de
   revisao? Alguma ameaca sem mitigacao?
"""


def _redigir(texto: str) -> str:
    """Redige usuario local (longa e 8.3) e caminhos locais da maquina.

    A redacao atinge SOMENTE o pacote (o repositorio permanece intacto);
    o codigo versionado contem `E:\\LucasIA\\Git\\...` (preflight_capsula),
    um caminho local que nao pode vazar para o reviewer.
    """
    return ((texto or "").replace(USUARIO, "<USUARIO>")
            .replace(USUARIO_CURTO, "<USUARIO>")
            .replace("E:\\LucasIA", "<CAMINHO-LOCAL>")
            .replace("E:/LucasIA", "<CAMINHO-LOCAL>"))


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True).stdout


def _conteudo_head(rel: str) -> str:
    return _git("show", f"{HEAD}:{rel}")


def montar_pacote() -> str:
    head = _git("rev-parse", "HEAD").strip()
    pai = _git("rev-parse", "HEAD^").strip()
    tree = _git("rev-parse", "HEAD^{tree}").strip()
    if head != HEAD or pai != PAI:
        raise SystemExit(
            f"PARADA: HEAD/pai inesperados: {head} / {pai}")
    sujeito = _git("log", "-1", "--format=%s", HEAD).strip()
    diff = _git("diff", PAI, HEAD)
    partes = [
        "PACOTE DE REVISAO — SSC+ P1-A.3.1 (laboratorio experimental, "
        "sem autoridade)\n",
        "Missao: revisar o ESTADO FINAL EXATO da P1-A.3. O commit final "
        "contem correcoes posteriores ao ultimo pacote revisado; testes "
        "verdes e direcao fail-closed nao substituem a revisao do estado "
        "exato. Esta missao NAO altera codigo e NAO abre a P1-B-02.\n",
        "=== Identidade do commit/tree ===\n",
        f"HEAD:   {head}\n",
        f"pai:    {pai}\n",
        f"tree:   {tree}\n",
        f"sujeito: {sujeito}\n",
        "sem tag e sem remoto (verificado na abertura da missao)\n",
        "\n=== Pacote anterior revisado (NAO equivale a este) ===\n",
        f"SHA-256 do pacote da ultima rodada da P1-A.3: "
        f"{PACOTE_ANTERIOR_SHA256}\n",
        "Registrado nas evidencias codex-20260731T031305Z e "
        "kimi-20260731T031551Z. O commit 677c585 contem correcoes "
        "posteriores a esse pacote; este pacote e a revisao do estado "
        "final exato e substitui qualquer equivalencia presumida.\n",
        "\n=== Suites reexecutadas ===\n", SUITES,
        "\n=== Threat review ===\n", THREAT_REVIEW,
        "\n=== Perguntas de revisao ===\n", PERGUNTAS,
        "\n=== Hashes SHA-256 das evidencias relevantes (P1-A.3) ===\n",
    ]
    for rel in sorted(EVIDENCIAS_HASHEADAS):
        dados = (RAIZ / rel).read_bytes()
        partes.append(f"{hashlib.sha256(dados).hexdigest()}  {rel}\n")
    partes.append("\n=== Diff integral contra o pai ===\n")
    partes.append(diff)
    partes.append("\n=== Arquivos funcionais/politicos/testes "
                  "(conteudo completo no HEAD) ===\n")
    for rel in ARQUIVOS_COMPLETOS:
        partes.append(f"\n--- {rel} ---\n")
        partes.append(_conteudo_head(rel))
    return _redigir("".join(partes))


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: pacote_p1a31.py <saida.txt>", file=sys.stderr)
        return 2
    pacote = montar_pacote()
    dados = pacote.encode("utf-8")
    Path(sys.argv[1]).write_bytes(dados)
    print(hashlib.sha256(dados).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
