#!/usr/bin/env python3
"""Revisao read-only da P1-A.11 por provider distinto — SSC+ (experimental).

DERIVADO MECANICAMENTE de `revisao_p1a10.py`. A MAQUINARIA e copiada
VERBATIM — capsula, vigilancia, redacao, mesmos bytes aos dois
revisores, lease automatico do proprio despachante e a reverificacao
do lease imediatamente antes de persistir. O que muda, e SO isto:

  1. `SESSAO_LOCK` -> p1a11-ops; `SAIDA` -> revisao-p1a11; `tipo` ->
     revisao-p1a11;
  2. `ALVO` passa a ser o HEAD desta missao (`3ff94e6`), porque os dois
     documentos que os REGISTROS_DE_CORRECAO citam so existem a partir
     dele — nao ha commit mais antigo que sirva sem reintroduzir o
     defeito que a P1-A.10 corrigiu (registro pinado num commit onde o
     texto ainda nao existia);
  3. `REGISTROS_DE_CORRECAO` cai de nove documentos para DOIS: o proprio
     registro dos residuos (`99_correcao-residuos-p1a10.md`) e o
     registro da decisao que arbitrou os quatro ids divididos
     (`99_decisao-p1a10.md`, com os DOIS pareceres da P1-A.10 e a
     arbitragem do Fundador) — sao os dois documentos que decidem se os
     tres ids reabertos fecham agora;
  4. o bloco `DECLARACOES`, reescrito para o escopo desta missao: DOIS
     revisores ja julgaram 6/P1A4-2/P1A4-4 UMA vez (NAO-FECHADO, pela
     mesma razao nos dois pareceres) e a correcao sob julgamento agora e
     a que veio DEPOIS daquele pacote — isto e a SEGUNDA rodada sobre os
     MESMOS tres ids, e a DECLARACAO diz isso explicitamente;
  5. `montar_prompt`, com a pergunta reduzida a TRES ids (nao mais nove)
     e sem pedir CONTAGEM-DISTINTA global — essa pergunta ja convergiu
     na P1-A.10 (SEIS, pelos dois revisores, com as mesmas fusoes) e
     reabri-la aqui seria o MESMO erro que o handoff de 2026-08-09
     corrigiu ao proibir "numero pre-definido": pedir de novo uma conta
     ja fechada por dois pareceres independentes.

DECLARADO: quem despacha esta revisao e a MESMA sessao que corrigiu os
residuos. O conflito e estrutural e esta na cara do revisor nas
DECLARACOES, como em todas as rodadas anteriores.

Nao ha ainda tentativa alguma desta rodada: nenhum arquivo em
`revisao-p1a11/` antes da primeira chamada real.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a11"

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       Vigilancia, redigir, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a11-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")

# Commit ALVO do pacote — os registros de correcao vem DELE, nunca da
# arvore de trabalho. HEAD desta missao: e onde os dois documentos
# abaixo existem no seu texto final.
ALVO = "3ff94e6"

REGISTROS_DE_CORRECAO = (
    "06_p1a/99_correcao-residuos-p1a10.md",
    "06_p1a/99_decisao-p1a10.md",
)

DECLARACOES = """\
DECLARACOES OBRIGATORIAS — SSC+ P1-A.11

Voce recebe estes fatos porque o autor do pacote e OBRIGADO a
transmiti-los. Varios sao contra o interesse dele. Julgar sem le-los e
julgar contra premissa falsa.

== 0. O CONFLITO ESTRUTURAL, PRIMEIRO ==

Quem corrigiu os residuos, quem montou este pacote e quem o despacha e
a MESMA sessao (2026-08-12/13). A regra do acervo — quem corrige nao
certifica — existe exatamente para este caso: NADA do que esta aqui
fecha sem o seu parecer. Desconte o interesse do autor em tudo que ler.

== 1. OS TRES IDS EM JULGAMENTO, E POR QUE SO TRES ==

A P1-A.10 julgou nove ids, por DOIS revisores independentes (codex e
kimi), e os dois convergiram: CINCO fechados (N1, P1A4-1, P1A4-3,
P1A4-5 por consenso; P1A4-6 pela regra de um revisor — o codex o julgou
no merito, o kimi declarou o proprio escopo sem contradizer o merito).
UM permanece aberto POR DECISAO do Fundador e NAO esta em julgamento
aqui: N5, mantido como lembrete permanente de que a sentinela e
deteccao, nunca impedimento — nao julgue N5 nesta rodada.

Os TRES restantes sao o objeto desta missao:

MAJOR-6  | NAO-FECHADO nos dois pareceres da P1-A.10. Razao dada pelos
         | dois revisores: a negacao dependia de fragmento do
         | vocabulario (chr, base64, dado externo); construcao SEM
         | fragmento continuava invisivel na atribuicao. Residuo
         | declarado pelo proprio autor no pacote anterior.
P1A4-2   | MESMO defeito do 6 nos dois pareceres — %/.format/join sem
         | negacao no ponto de decisao.
P1A4-4   | NAO-FECHADO nos dois pareceres. Razao dada: reconta-se so o
         | redigido (originais seguem testemunhais) e o fluxo nao
         | exporta.

A CORRECAO SOB JULGAMENTO AGORA (leia `registros-de-correcao.txt`,
item 2 do documento `99_correcao-residuos-p1a10.md`, e item 3 do
mesmo documento):

  - para 6/P1A4-2 (e, de caminho, N5 — que NAO se rejulga aqui):
    `comparacoes_nao_resolvidas` nega comparacao contra construtor
    textual nao resolvido NO PONTO DE DECISAO, nao mais so na
    atribuicao. Limite declarado pelo proprio autor: decisao sem
    `ast.Compare` (despacho por dict indexado pela string construida)
    continua fora do alcance — julgue se este limite e aceitavel ou se
    e o MESMO buraco com outro nome;
  - para P1A4-4: `executar_fluxo` passa a exportar brutos por etapa, e
    a receita `bruto` ganha ancora cruzada (`recibo` + `trilha`, hash
    tem de coincidir com `sha256_original`). Limites declarados: o
    original nao se recupera, corridas historicas seguem testemunhais,
    e `trilha` so percorre dicionarios — julgue se a prova
    comportamental declarada (test_p1a44_*, corrida real seguinte como
    exercicio de ponta a ponta) basta para fechar SEM essa corrida real
    ja ter acontecido.

Isto e a SEGUNDA rodada sobre os MESMOS tres ids. Se voce fechar algum,
sera o PRIMEIRO fechamento deles em qualquer parecer.

== 2. O QUE MAIS MUDOU DESDE O PACOTE QUE OS DOIS REVISORES DA P1-A.10
VIRAM, FORA DOS TRES IDS ==

- o TOCTOU que o codex encontrou (MAJOR novo, estreia, janela entre
  checagem e abertura em `montar_snapshot`) foi fechado no mecanismo
  (item 1 de `99_correcao-residuos-p1a10.md`) — nao esta em julgamento
  aqui como id numerado, mas o registro esta no pacote e voce pode
  apontar se a leitura contida realmente fecha o buraco;
- o pacote da P1-A.10 foi julgado pelos dois revisores INTACTO — nenhum
  deles viu as correcoes de residuo. O parecer do kimi (2026-08-13,
  484,8 s) leu O MESMO pacote.sha256 que o codex, nao um atualizado;
- ha um commit NOVO, FORA do escopo dos tres ids: `3ff94e6` acrescenta
  `usuario_e_infraestrutura()` em `contencao.py` — os guardas de
  propriedade da estacao (dono, config instalada) param de disparar
  quando DUAS provas coincidem (`GITHUB_ACTIONS=true` E conta nominal
  de infraestrutura tipo `runneradmin`). Motivo: o runner do GitHub
  roda como `runneradmin`, e sem este guardio o guarda de PII/
  propriedade da estacao vira ruido em CI. Este commit NAO tem registro
  `99_*.md` proprio — a justificativa vive so no docstring do proprio
  codigo, que esta LIDO no pacote como diff. Julgue-o tambem: ele nao
  fecha nenhum dos tres ids, e o autor o inclui aqui porque esta no
  diff entre o BASE e o ALVO e omiti-lo do julgamento seria omissao.

== 3. ACHADOS NOVOS QUE O AUTOR DECLARA CONTRA SI ==

a) o BASE deste pacote (`f799883`) e o MESMO commit usado como ALVO dos
   REGISTROS na P1-A.10 — ou seja, o diff que voce ve inclui tambem os
   PROPRIOS instrumentos da revisao anterior (gerador, despachante,
   DECLARACOES daquela rodada) como conteudo LIDO ou ANCORADO. Isso e
   esperado (o gerador nao pode excluir nada por conveniencia — o
   CRITERIO DE INCLUSAO do proprio pacote proibe), mas alonga o que
   voce precisa ler antes de chegar aos tres ids que importam agora;
b) dois pareceres JA disseram NAO-FECHADO para os tres ids com a MESMA
   razao. Um terceiro NAO-FECHADO nao seria uma novidade — seria a
   confirmacao de que a correcao de residuo tambem nao bastou. O autor
   declara que nao ha garantia de fechamento aqui, so a tentativa mais
   recente;
c) o commit `3ff94e6` (item 2 acima) foi escrito e commitado pela MESMA
   sessao que agora monta e despacha este pacote, sem revisao
   independente previa — e o segundo commit desta janela sem revisor,
   depois dos residuos do item 2 da secao 1.

== 4. O QUE ESTE ACERVO NAO MEDE, E NAO SE PRESUME ==

- o VEREDITO VIGENTE do acervo e REPROVADO (P1-A.4); nenhuma missao
  posterior o moveu; nada aqui o move sem o seu parecer;
- a tese central segue nao medida em token (proxy de bytes);
- as corridas historicas da P2 (p21, p22-*) seguem com evidencia bruta
  DESTRUIDA (P1-A.6) — o mecanismo novo (item 2 acima) vale para
  frente, nao para tras;
- plataforma desta missao: Python 3.14.3, pytest 9.1.1, autocrlf true,
  usuario da estacao declarado por descricao (8 caracteres) porque os
  guardas ZeroPii derivam o alvo dele.
"""


def _redigir(texto: str) -> str:
    return redigir(texto)


COMANDOS = {
    # codex SEM prompt posicional: ele vem por STDIN, com os documentos
    # inline — o sandbox de ferramentas esta quebrado nesta estacao
    # (setup.exe ausente) e leitura de arquivo morreria. E o mesmo
    # transporte do fluxo P2, que funciona.
    "codex": lambda tmp, skills, prompt: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral"],
    "kimi": lambda tmp, skills, prompt: argv_kimi(_KIMI_EXE, prompt, skills),
}

ENFORCEMENT = {
    "codex": "--sandbox read-only --ephemeral (CLI)",
    "kimi": enforcement_kimi(),
}


def _modelo_efetivo(err: str) -> str:
    m = re.search(r"^\s*model:\s*(\S+)", err or "", re.MULTILINE)
    return m.group(1) if m else "DESCONHECIDO (nao exposto pelo CLI)"


def _verificar_lock(fence_esperado: int | None = None) -> dict:
    return verificar_lock(RAIZ, SESSAO_LOCK, fence_esperado)


def _verificar_tier(provider: str) -> dict:
    dados = json.loads((RAIZ / "06_p1a" / "tiers_declarados.json")
                       .read_text(encoding="utf-8"))
    teto = float(dados["validade_maxima_horas"])
    agora = datetime.now(timezone.utc)
    for decl in dados["declaracoes"]:
        if decl["provider_id"] != provider:
            continue
        em = datetime.strptime(decl["declarado_em_utc"],
                               "%Y-%m-%dT%H:%M:%SZ").replace(
                                   tzinfo=timezone.utc)
        expira = em.timestamp() + min(float(decl["validade_horas"]),
                                      teto) * 3600
        if agora.timestamp() >= expira:
            expira_iso = datetime.fromtimestamp(
                expira, timezone.utc).isoformat()
            raise SystemExit(
                f"PARADA: tier declarado de {provider} EXPIRADO em "
                f"{expira_iso} — somente o proprietario renova")
        return {"provider_id": provider, "tier": decl["tier"],
                "declarado_por": decl["declarado_por"],
                "declarado_em_utc": decl["declarado_em_utc"],
                "expira_em_utc": datetime.fromtimestamp(
                    expira, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "valido_no_instante": True}
    raise SystemExit(f"PARADA: sem declaracao de tier para {provider}")


def _blob_do_alvo(rel: str) -> bytes:
    """Um registro pelo blob do ALVO — o seam que a prova de corpus troca.

    Os guardas de redacao/tier rodam o `main()` REAL numa raiz de prova
    sem git; ali nao ha blob a ler, e ESTA funcao e o unico ponto que a
    prova substitui — o resto do caminho permanece o da operacao.
    """
    return subprocess.run(
        ["git", "-c", f"safe.directory={RAIZ.as_posix()}", "cat-file",
         "blob", f"{ALVO}:{rel}"], cwd=RAIZ, capture_output=True,
        check=True).stdout


def montar_registros() -> bytes:
    """O terceiro arquivo, montado por blob do ALVO — nunca da arvore."""
    partes = [f"REGISTROS DE CORRECAO SOB JULGAMENTO — blobs de {ALVO}\n"]
    for rel in REGISTROS_DE_CORRECAO:
        blob = _blob_do_alvo(rel)
        partes.append(f"\n{'=' * 72}\n--- {rel} "
                      f"(sha256 {hashlib.sha256(blob).hexdigest()}) ---\n")
        partes.append(blob.decode("utf-8", errors="replace"))
    return _redigir("\n".join(partes)).encode("utf-8")


def montar_prompt(inline: bool = False) -> str:
    if inline:
        abertura = (
            "Revise em modo SOMENTE LEITURA o estado atual do laboratorio "
            "SSC+. Os TRES documentos seguem INLINE nesta mesma entrada, "
            "apos estas instrucoes, cada um com o seu SHA-256 DECLARADO "
            "no cabecalho (voce nao tem ferramentas; ecoe os declarados "
            "nas linhas exigidas em vez de computa-los):\n"
            "  1. pacote-revisao.txt           — o estado sob julgamento\n"
            "  2. declaracoes-obrigatorias.txt — fatos que o autor e "
            "OBRIGADO a transmitir, varios contra o interesse dele\n"
            "  3. registros-de-correcao.txt    — os dois registros da "
            "correcao sob julgamento, ancorados no commit ALVO\n\n")
    else:
        abertura = (
            "Revise em modo SOMENTE LEITURA o estado atual do laboratorio "
            "SSC+. No diretorio atual ha TRES arquivos, e voce precisa ler "
            "OS TRES POR INTEIRO antes de avaliar:\n"
            "  ./pacote-revisao.txt           — o estado sob julgamento\n"
            "  ./declaracoes-obrigatorias.txt — fatos que o autor e "
            "OBRIGADO a transmitir, varios contra o interesse dele\n"
            "  ./registros-de-correcao.txt    — os dois registros da "
            "correcao sob julgamento, ancorados no commit ALVO\n\n")
    return abertura + (
        "Comece pelas declaracoes. Quem corrigiu, montou e despachou e a "
        "MESMA sessao: nada fecha sem o seu parecer.\n\n"
        "Contexto: o veredito vigente do acervo e REPROVADO (P1-A.4). Dois "
        "revisores independentes ja julgaram 6/P1A4-2/P1A4-4 NAO-FECHADO "
        "uma vez, contra o pacote ANTERIOR a esta correcao de residuo. "
        "Esta e a SEGUNDA rodada sobre os MESMOS tres ids.\n\n"
        "Voce NAO pode escrever nada: responda apenas com a revisao em "
        "texto.\n\n"
        "IMPORTANTE: leia e julgue VOCE MESMO, num unico turno, sem "
        "despachar subagentes e sem aguardar processos paralelos — o seu "
        "ambiente encerra em 10 minutos e parecer inacabado nao e "
        "parecer. Se o tempo nao der para tudo, priorize as linhas "
        "exigidas abaixo, nesta ordem, e diga o que ficou sem conferir.\n\n"
        "Sua resposta precisa conter, NESTA ORDEM:\n"
        "1. as linhas PROVIDER, MODELO-OBSERVADO, CANAL, PACOTE-SHA256, "
        "DECLARACOES-SHA256 e REGISTROS-SHA256 (compute-os dos arquivos "
        "se tiver ferramentas; ecoe os DECLARADOS nos cabecalhos se nao "
        "tiver, dizendo qual dos dois fez) e ESCOPO;\n"
        "2. UMA linha por id — 6, P1A4-2, P1A4-4 — exatamente na forma "
        "'MAJOR-<id>: FECHADO | NAO-FECHADO — <justificativa "
        "apontavel>'. Se voce julgar que dois ou mais ids sao o MESMO "
        "defeito, diga-o na linha de cada um; a fusao e permitida e nao "
        "ha contagem certa esperada. NAO julgue N5 — ele fica aberto por "
        "decisao do Fundador e nao esta em julgamento nesta rodada;\n"
        "3. UMA linha por item do registro de residuos — os itens 1, 2 e "
        "3 de `99_correcao-residuos-p1a10.md` — na forma 'ITEM-<numero>: "
        "SUSTENTADO | NAO-SUSTENTADO — <motivo>' (sustentado = a "
        "correcao fecha o que diz fechar, o teste exerce o caso que "
        "ocorre e os limites declarados sao os reais);\n"
        "4. UMA linha sobre o commit fora de escopo (secao 2 das "
        "declaracoes, `contencao.py:usuario_e_infraestrutura`) na forma "
        "'FORA-DE-ESCOPO: SUSTENTADO | NAO-SUSTENTADO — <motivo>';\n"
        "5. UMA linha por achado novo declarado — a, b, c da secao 3 das "
        "declaracoes — na forma 'DECLARADO-<letra>: CONFIRMO | "
        "NAO-CONFIRMO — <motivo>', com a FAMILIA ao final;\n"
        "6. a linha 'DEFEITO-NOVO: SIM | NAO — <o que, onde>' sobre as "
        "correcoes desta rodada;\n"
        "7. os seus achados, um por linha, prefixados por CRITICAL | "
        "MAJOR | MINOR | OBS, com arquivo:tema e descricao curta, e CADA "
        "um terminando com a FAMILIA obrigatoria:\n"
        "   'FAMILIA: (F)' — guarda que AFIRMA em vez de EXERCER;\n"
        "   'FAMILIA: (N)' — classe que a varredura por alcance de linha "
        "nao media;\n"
        "   'FAMILIA: fora-de-ambas' — com o motivo.\n"
        "   Sem familia o criterio de parada nao se afere. Para cada "
        "achado NOVO diga se esta em AREA JA REVISADA ou em ESTREIA — e, "
        "se estreia, QUAL pacote anterior nao a continha;\n"
        "8. a linha final 'VEREDITO: APROVADO | APROVADO-COM-RESSALVAS | "
        "REPROVADO'.")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a11.py codex|kimi <pacote.txt>",
              file=sys.stderr)
        return 2
    provider = sys.argv[1]
    sys.stdout.reconfigure(errors="replace")

    from ssc_plus import LeaseAutomatico
    with LeaseAutomatico(SESSAO_LOCK, dir_locks=RAIZ / "locks"):
        lock = _verificar_lock()
        tier = _verificar_tier(provider)

        dados_pacote = Path(sys.argv[2]).read_bytes()
        pacote_sha256 = hashlib.sha256(dados_pacote).hexdigest()
        dados_decl = DECLARACOES.encode("utf-8")
        decl_sha256 = hashlib.sha256(dados_decl).hexdigest()
        dados_registros = montar_registros()
        registros_sha256 = hashlib.sha256(dados_registros).hexdigest()

        env = ambiente_capsula()
        removidas = sorted(set(os.environ) - set(env))
        tmp = tempfile.mkdtemp(prefix=f"p1a11-revisao-{provider}-")
        skills = tempfile.mkdtemp(prefix=f"p1a11-skills-vazio-{provider}-")
        with open(os.path.join(tmp, "pacote-revisao.txt"), "wb") as f:
            f.write(dados_pacote)
        with open(os.path.join(tmp, "declaracoes-obrigatorias.txt"),
                  "wb") as f:
            f.write(dados_decl)
        with open(os.path.join(tmp, "registros-de-correcao.txt"), "wb") as f:
            f.write(dados_registros)
        prompt = montar_prompt(inline=(provider == "codex"))
        entrada_stdin = None
        if provider == "codex":
            # Documentos INLINE por stdin — o transporte do fluxo P2, que
            # funciona onde o sandbox de ferramentas nao inicia.
            entrada_stdin = "\n".join([
                prompt,
                f"\n{'=' * 72}\n=== DOCUMENTO 1/3: pacote-revisao.txt "
                f"(sha256 declarado: {pacote_sha256}) ===\n",
                dados_pacote.decode("utf-8", errors="replace"),
                f"\n{'=' * 72}\n=== DOCUMENTO 2/3: "
                f"declaracoes-obrigatorias.txt "
                f"(sha256 declarado: {decl_sha256}) ===\n",
                dados_decl.decode("utf-8", errors="replace"),
                f"\n{'=' * 72}\n=== DOCUMENTO 3/3: "
                f"registros-de-correcao.txt "
                f"(sha256 declarado: {registros_sha256}) ===\n",
                dados_registros.decode("utf-8", errors="replace"),
            ])
        argv = COMANDOS[provider](tmp, skills, prompt)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        vigilancia = Vigilancia(RAIZ, SESSAO_LOCK)
        vigilancia.abrir()
        inicio = time.monotonic()
        try:
            proc = subprocess.run(
                argv, cwd=tmp, env=env, capture_output=True, text=True,
                timeout=3600, encoding="utf-8", errors="replace",
                input=entrada_stdin)
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            rc, out = "TIMEOUT", (e.stdout or "")
            err = (e.stderr or "") + "\nTIMEOUT apos 3600s"
        duracao = round(time.monotonic() - inicio, 3)
        contencao_medida = vigilancia.fechar()
        fora_do_descartavel = contencao_medida["mutacoes_fora_do_descartavel"]
        restantes = [str(p.relative_to(tmp)) for p in Path(tmp).rglob("*")
                     if p.is_file()]
        lock = _verificar_lock(fence_esperado=lock["fence"])
        meta = {
            "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a11",
            "chamadas_de_modelo": 1, "custo_variavel": 0,
            "rotulo": "assinatura-oauth; UMA chamada; enforcement read-only",
            "enforcement_read_only": ENFORCEMENT[provider],
            "tier_declarado_no_instante": tier,
            "lock_escritor_unico": lock,
            "argv_publico": ["<PROMPT>" if a == prompt else a for a in argv],
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "transporte_documentos": ("stdin-inline" if entrada_stdin
                                      else "arquivos-no-descartavel"),
            "stdin_sha256": (hashlib.sha256(
                entrada_stdin.encode("utf-8")).hexdigest()
                if entrada_stdin else None),
            "pacote_sha256": pacote_sha256,
            "pacote_bytes_entregues": len(dados_pacote),
            "declaracoes_sha256": decl_sha256,
            "declaracoes_bytes_entregues": len(dados_decl),
            "registros_sha256": registros_sha256,
            "registros_bytes_entregues": len(dados_registros),
            "registros_alvo_commit": ALVO,
            "dir_descartavel": _redigir(tmp),
            "dir_descartavel_arquivos_restantes": restantes,
            "contencao": contencao_medida,
            "lock_verificado_antes_da_persistencia": True,
            "env_vars_removidas_nomes": removidas,
            "returncode": rc, "duracao_s": duracao,
            "modelo_efetivo_no_banner": _modelo_efetivo(err),
            "resposta": _redigir((out or "").strip()),
            "stderr_resumo": _redigir((err or "").strip()[:4000]),
            "quota_observavel": "nao-exposta-pelo-cli",
        }
        SAIDA.mkdir(parents=True, exist_ok=True)
        texto = _redigir(json.dumps(meta, ensure_ascii=False, indent=2))
        (SAIDA / f"{provider}-{ts}.json").write_text(texto + "\n",
                                                     encoding="utf-8")
        print(json.dumps({"provider": provider, "returncode": rc,
                          "duracao_s": duracao,
                          "pacote_sha256": pacote_sha256,
                          "registros_sha256": registros_sha256,
                          "modelo_efetivo":
                              meta["modelo_efetivo_no_banner"],
                          "contencao_violada": bool(fora_do_descartavel),
                          "resposta_inicio": meta["resposta"][:400]},
                         ensure_ascii=False, indent=2))
        if fora_do_descartavel:
            print("PARADA: contencao violada — mutacao fora do "
                  "descartavel: " + "; ".join(fora_do_descartavel[:20]),
                  file=sys.stderr)
            return 3
        return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
