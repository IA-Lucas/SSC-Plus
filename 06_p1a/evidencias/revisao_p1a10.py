#!/usr/bin/env python3
"""Revisao read-only da P1-A.10 por provider distinto — SSC+ (experimental).

DERIVADO MECANICAMENTE de `revisao_p1a6.py`. A MAQUINARIA e copiada
VERBATIM — capsula, vigilancia, redacao, mesmos bytes aos dois
revisores, e a reverificacao do lease imediatamente antes de persistir
(o desenho que o MAJOR #4 impos). O que muda, e SO isto:

  1. `SESSAO_LOCK` -> p1a10-ops; `SAIDA` -> revisao-p1a10; `tipo` ->
     revisao-p1a10;
  2. o bloco `DECLARACOES`, que e ato DESTA missao e nao do pacote;
  3. `montar_prompt`, porque o acervo mudou — e porque o handoff de
     2026-08-09 ordenou que a pergunta da CONTAGEM fosse reaberta SEM
     dizer o numero: o prompt da P1-A.6 exigia "NOVE linhas" e proibia
     fundir, e o silencio do codex sobre a contagem foi obediencia, nao
     concordancia. Aqui cada id recebe veredito, a fusao e permitida
     por escrito, e a contagem e do revisor;
  4. NOVO, declarado: um TERCEIRO arquivo no descartavel,
     `registros-de-correcao.txt`, com os registros das correcoes sob
     julgamento montados por `git cat-file blob <ALVO>:<caminho>` —
     ancorados no commit, nunca na arvore. O pacote os ANCORA por hash
     (disposicao correta para registro); o revisor precisa LE-LOS para
     julgar fechamento, e este arquivo e o que os entrega;
  5. NOVO, declarado: o lease e adquirido e renovado pelo PROPRIO
     despachante (`ssc_plus.LeaseAutomatico`), em vez de assumir uma
     sessao de ops previa — o runner da P1-A.6 rodava dentro de uma
     missao que ja detinha o escritor.

DECLARADO: quem despacha esta revisao e a MESMA sessao que corrigiu.
O conflito e estrutural e esta na cara do revisor nas DECLARACOES.
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
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a10"

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       Vigilancia, redigir, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a10-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")

# Commit ALVO do pacote — os registros de correcao vem DELE, nunca da
# arvore de trabalho. Preso aqui porque o terceiro arquivo tem de ser
# byte-identico para os dois revisores mesmo que a arvore mude entre as
# duas chamadas.
ALVO = "f799883"

REGISTROS_DE_CORRECAO = (
    "06_p1a/99_correcao-p1a9a.md",
    "06_p1a/99_correcao-p1a9b.md",
    "06_p1a/99_correcao-majors-20260812.md",
    "08_p2/103_julgamento-google-add-dir-20260812.md",
    "08_p2/104_contrato-inline-kimi-20260812.md",
    "08_p2/105_ponteiro-sem-terminal-20260812.md",
    "08_p2/106_portao-de-testes-copia-fiel-20260812.md",
    "08_p2/107_portao-hermetico-20260812.md",
    "08_p2/108_remocao-mode-plan-20260812.md",
)

DECLARACOES = """\
DECLARACOES OBRIGATORIAS — SSC+ P1-A.10

Voce recebe estes fatos porque o autor do pacote e OBRIGADO a
transmiti-los. Varios sao contra o interesse dele. Julgar sem le-los e
julgar contra premissa falsa.

== 0. O CONFLITO ESTRUTURAL, PRIMEIRO ==

Quem corrigiu, quem montou este pacote e quem o despacha e a MESMA
sessao (2026-08-12). A regra do acervo — quem corrige nao certifica —
existe exatamente para este caso: NADA do que esta aqui fecha sem o seu
parecer. Desconte o interesse do autor em tudo que ler.

== 1. OS IDS EM JULGAMENTO, COM O ESTADO QUE O AUTOR DECLARA ==

A P1-A.6 julgou nove ids: 6, N1, N5, P1A4-1, P1A4-2, P1A4-3, P1A4-4,
P1A4-5, P1A4-6. Sobre a CONTAGEM ha divergencia registrada e nao
resolvida (N1/P1A4-1 podem ser o mesmo defeito; o trio 6/N5/P1A4-2
tambem se discute). Ha UM parecer de revisor sobre isso, nao dois — o
prompt anterior proibia fundir, e o silencio do outro revisor foi
obediencia. A contagem e SUA: funda ou separe como julgar certo, e diga
quantos defeitos distintos os ids representam.

Estado declarado pelo autor (interesse dele — confira contra o pacote):

MAJOR-6  | sentinela: contorno por construcao nao resolvida. CORRIGIDO
         | NESTA MISSAO: negacao de %/.format/join/f-string com
         | fragmento do vocabulario e de todo import dinamico
         | (`sentinela_antip2.construcoes_nao_resolvidas`). Reversao
         | vermelha por ramo medida. LIMITE: construcao sem fragmento
         | nenhum continua invisivel, de proposito.
MAJOR-N1 | escritor unico existia e nao era usado. TRATADO na P1-A.5.
P1A4-1   | mesmo objeto do N1, por outro angulo. TRATADO na P1-A.5.
MAJOR-N5 | formas deliberadas de contorno nao negadas. REDUZIDO NESTA
         | MISSAO (mesma correcao do 6); residuo declarado.
P1A4-2   | %/.format/join sem negacao. MESMA correcao do 6.
P1A4-3   | recibo afirmava "efeito nenhum" com alcance parcial. TRATADO
         | na P1-A.5 (alcance declarado no recibo).
P1A4-4   | receita com insumos testemunhais. CORRIGIDO NO MECANISMO
         | NESTA MISSAO: `exportar_bruto` (conteudo redigido +
         | manifesto com hash/tamanhos do original e do redigido) e
         | origem `bruto` recontavel na receita. LIMITES: original nao
         | se recupera; corridas historicas seguem testemunhais; fluxo
         | nao exporta.
P1A4-5   | relatar antes de gravar. TRATADO pelo hardening de
         | 2026-08-11 (recibo atomico antes do relato) — o mapeamento
         | correcao->MAJOR e desta missao, nao do hardening.
P1A4-6   | teste afirmava buraco sem exercer interface. TRATADO na
         | P1-A.5.

== 2. AS CORRECOES DE HOJE FORA DOS MAJOR ==

Leia `registros-de-correcao.txt` no diretorio atual: P1A9-a (teste que
dependia de locks/ preexistente), P1A9-b (guarda dos quatro campos de
plataforma), e os registros 103-108 (permissao de leitura do agy,
contrato semantico inline, ponteiro sem terminal, copia fiel do portao
de testes, portao hermetico, remocao da flag inerte --mode plan por
decisao do Fundador). Cada um com reversao vermelha medida e limites
declarados.

== 3. ACHADOS NOVOS QUE O AUTOR DECLARA CONTRA SI ==

a) a medicao registrada no docstring da P1-A.3.9 ("com `!locks/*.lease`
   este arquivo fica vermelho") NAO REPRODUZ: a mutacao e inerte por
   semantica do git (nao ha re-inclusao sob diretorio excluido).
   Registrado em 99_correcao-p1a9a.md, texto original preservado.
b) `SystemExit` de gerador de pacote (`pacote_p1a36.montar_pacote`)
   MATA a suite unittest sem sumario quando o historico git falta.
   Medido no portao de testes (registro 106). Nao corrigido.
c) o gerador de pacote da P1-A.3.7 PARA na primeira rename do acervo
   (le dois campos onde `git diff -z` manda tres). Esta revisao foi
   gerada por `pacote_p1a10.py`, copia com a divergencia declarada no
   proprio fonte — julgue-o: ele esta no pacote, autoincluido.
d) seis fluxos reais recusados em 2026-08-12 antes do primeiro
   aprovado, um deles por mutacao concorrente CAUSADA PELO PROPRIO
   AUTOR (commit durante a corrida — registro 104 §1).

== 4. O QUE ESTE ACERVO NAO MEDE, E NAO SE PRESUME ==

- o VEREDITO VIGENTE do acervo e REPROVADO (P1-A.4); nenhuma missao
  posterior o moveu; nada aqui o move sem o seu parecer;
- a tese central segue nao medida em token (proxy de bytes);
- as corridas historicas da P2 (p21, p22-*) seguem com evidencia bruta
  DESTRUIDA (P1-A.6) — o mecanismo novo vale para frente;
- plataforma desta missao: Python 3.14.3, pytest 9.1.1, autocrlf true,
  usuario da estacao declarado por descricao (8 caracteres) porque os
  guardas ZeroPii derivam o alvo dele.
"""


def _redigir(texto: str) -> str:
    return redigir(texto)


COMANDOS = {
    "codex": lambda tmp, skills, prompt: [
        "codex", "exec", "--sandbox", "read-only", "--cd", tmp,
        "--skip-git-repo-check", "--ephemeral", prompt],
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


def montar_registros() -> bytes:
    """O terceiro arquivo, montado por blob do ALVO — nunca da arvore."""
    partes = [f"REGISTROS DE CORRECAO SOB JULGAMENTO — blobs de {ALVO}\n"]
    for rel in REGISTROS_DE_CORRECAO:
        blob = subprocess.run(
            ["git", "-c", f"safe.directory={RAIZ.as_posix()}", "cat-file",
             "blob", f"{ALVO}:{rel}"], cwd=RAIZ, capture_output=True,
            check=True).stdout
        partes.append(f"\n{'=' * 72}\n--- {rel} "
                      f"(sha256 {hashlib.sha256(blob).hexdigest()}) ---\n")
        partes.append(blob.decode("utf-8", errors="replace"))
    return _redigir("\n".join(partes)).encode("utf-8")


def montar_prompt() -> str:
    return (
        "Revise em modo SOMENTE LEITURA o estado atual do laboratorio "
        "SSC+. No diretorio atual ha TRES arquivos, e voce precisa ler "
        "OS TRES POR INTEIRO antes de avaliar:\n"
        "  ./pacote-revisao.txt           — o estado sob julgamento\n"
        "  ./declaracoes-obrigatorias.txt — fatos que o autor e OBRIGADO "
        "a transmitir, varios contra o interesse dele\n"
        "  ./registros-de-correcao.txt    — os registros das correcoes "
        "sob julgamento, ancorados no commit ALVO\n\n"
        "Comece pelas declaracoes. Quem corrigiu, montou e despachou e a "
        "MESMA sessao: nada fecha sem o seu parecer.\n\n"
        "Contexto: o veredito vigente do acervo e REPROVADO (P1-A.4). O "
        "pacote e o estado DEPOIS das missoes de 2026-08-11/12.\n\n"
        "Voce NAO pode escrever nada: responda apenas com a revisao em "
        "texto.\n\n"
        "Sua resposta precisa conter, NESTA ORDEM:\n"
        "1. as linhas PROVIDER, MODELO-OBSERVADO, CANAL, PACOTE-SHA256 "
        "(compute o SHA-256 de ./pacote-revisao.txt), DECLARACOES-SHA256 "
        "e REGISTROS-SHA256 (idem para os outros dois) e ESCOPO;\n"
        "2. UMA linha por id — 6, N1, N5, P1A4-1, P1A4-2, P1A4-3, "
        "P1A4-4, P1A4-5, P1A4-6 — exatamente na forma "
        "'MAJOR-<id>: FECHADO | NAO-FECHADO — <justificativa "
        "apontavel>'. Se voce julgar que dois ou mais ids sao o MESMO "
        "defeito, diga-o na linha de cada um; a fusao e permitida e nao "
        "ha contagem certa esperada;\n"
        "3. a linha 'CONTAGEM-DISTINTA: <numero> — <criterio que voce "
        "usou>', com QUANTOS defeitos distintos os nove ids representam "
        "NA SUA contagem;\n"
        "4. UMA linha por registro de correcao de hoje — P1A9-a, P1A9-b, "
        "103, 104, 105, 106, 107, 108 — na forma "
        "'REGISTRO-<id>: SUSTENTADO | NAO-SUSTENTADO — <motivo>' "
        "(sustentado = a correcao fecha o que diz fechar, o teste exerce "
        "o caso que ocorre e os limites declarados sao os reais);\n"
        "5. UMA linha por achado novo declarado — a, b, c, d da secao 3 "
        "das declaracoes — na forma 'DECLARADO-<letra>: CONFIRMO | "
        "NAO-CONFIRMO — <motivo>', com a FAMILIA ao final;\n"
        "6. a linha 'DEFEITO-NOVO: SIM | NAO — <o que, onde>' sobre as "
        "correcoes de 2026-08-11/12;\n"
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
        print("uso: revisao_p1a10.py codex|kimi <pacote.txt>",
              file=sys.stderr)
        return 2
    provider = sys.argv[1]
    sys.stdout.reconfigure(errors="replace")

    from ssc_plus import LeaseAutomatico
    with LeaseAutomatico(SESSAO_LOCK):
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
        tmp = tempfile.mkdtemp(prefix=f"p1a10-revisao-{provider}-")
        skills = tempfile.mkdtemp(prefix=f"p1a10-skills-vazio-{provider}-")
        with open(os.path.join(tmp, "pacote-revisao.txt"), "wb") as f:
            f.write(dados_pacote)
        with open(os.path.join(tmp, "declaracoes-obrigatorias.txt"),
                  "wb") as f:
            f.write(dados_decl)
        with open(os.path.join(tmp, "registros-de-correcao.txt"), "wb") as f:
            f.write(dados_registros)
        prompt = montar_prompt()
        argv = COMANDOS[provider](tmp, skills, prompt)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        vigilancia = Vigilancia(RAIZ, SESSAO_LOCK)
        vigilancia.abrir()
        inicio = time.monotonic()
        try:
            proc = subprocess.run(
                argv, cwd=tmp, env=env, capture_output=True, text=True,
                timeout=3600, encoding="utf-8", errors="replace")
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
            "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a10",
            "chamadas_de_modelo": 1, "custo_variavel": 0,
            "rotulo": "assinatura-oauth; UMA chamada; enforcement read-only",
            "enforcement_read_only": ENFORCEMENT[provider],
            "tier_declarado_no_instante": tier,
            "lock_escritor_unico": lock,
            "argv_publico": ["<PROMPT>" if a == prompt else a for a in argv],
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
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
