#!/usr/bin/env python3
"""Revisao read-only da P1-A.12 por provider distinto — SSC+ (experimental).

DERIVADO MECANICAMENTE de `revisao_p1a11.py`. A MAQUINARIA e copiada
VERBATIM. O que muda, e SO isto:

  1. `SESSAO_LOCK` -> p1a12-ops; `SAIDA` -> revisao-p1a12; `tipo` ->
     revisao-p1a12;
  2. `ALVO` passa a ser o HEAD desta missao (`74b9448`), onde a
     correcao sob julgamento e os dois registros que a documentam
     existem no texto final;
  3. `REGISTROS_DE_CORRECAO` passa a ser o registro da P1-A.11
     (`99_decisao-p1a11.md`, os DOIS pareceres e a arbitragem do
     Fundador) e o registro desta correcao (`99_correcao-p1a11.md`,
     que inclui as DUAS tentativas mais amplas revertidas por medicao
     e a reversao vermelha);
  4. `DECLARACOES`, reescrito para o escopo desta missao: UM id em
     julgamento (6, fundido com P1A4-2 pela convergencia ja
     estabelecida nas duas rodadas anteriores), nao mais tres — N5
     permanece aberto por decisao permanente do Fundador e P1A4-4
     segue numa trilha separada (aguarda corrida real, nao corrigido
     nesta missao). Esta e a TERCEIRA rodada sobre a MESMA familia de
     defeito, e a arbitragem que autorizou esta correcao ja declarou o
     numero do ciclo por escrito;
  5. `montar_prompt`, com a pergunta reduzida a UM id e uma pergunta
     NOVA, explicita: se a correcao NAO fechar, o revisor e convidado
     a dizer se o padrao deve virar limite PERMANENTE (como N5) em vez
     de uma quarta tentativa — a arbitragem da P1-A.11 ja registrou por
     escrito que essa e a pergunta do proximo ciclo caso este residue.

DECLARADO: quem despacha esta revisao e a MESMA sessao que corrigiu.
O conflito e estrutural e esta na cara do revisor nas DECLARACOES, como
em todas as rodadas anteriores.
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
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a12"

sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       Vigilancia, redigir, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a12-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")

# Commit ALVO do pacote — os registros de correcao vem DELE, nunca da
# arvore de trabalho. HEAD desta missao: e onde os dois documentos
# abaixo existem no seu texto final.
ALVO = "74b9448"

REGISTROS_DE_CORRECAO = (
    "06_p1a/99_decisao-p1a11.md",
    "06_p1a/99_correcao-p1a11.md",
)

DECLARACOES = """\
DECLARACOES OBRIGATORIAS — SSC+ P1-A.12

Voce recebe estes fatos porque o autor do pacote e OBRIGADO a
transmiti-los. Varios sao contra o interesse dele. Julgar sem le-los e
julgar contra premissa falsa.

== 0. O CONFLITO ESTRUTURAL, PRIMEIRO ==

Quem corrigiu, quem montou este pacote e quem o despacha e a MESMA
sessao (2026-08-13/14). A regra do acervo — quem corrige nao certifica
— existe exatamente para este caso: NADA do que esta aqui fecha sem o
seu parecer. Desconte o interesse do autor em tudo que ler.

== 1. O ID EM JULGAMENTO, E POR QUE E O TERCEIRO CICLO ==

6 (fundido com P1A4-2, pela MESMA convergencia que os dois revisores da
P1-A.10 e da P1-A.11 ja estabeleceram — funda ou separe como julgar
certo, mas a fusao NAO e uma pergunta nova). Historico dos DOIS
pareceres anteriores, os DOIS por revisor distinto de codex e de kimi:

  P1-A.10 (primeira correcao): DIVIDIDO — codex NAO-FECHADO (residuo
  pos-ALVO que ele nao viu), kimi FECHADO (lendo correcoes fora do
  pacote). Arbitragem: aguarda o proximo ciclo.

  P1-A.11 (segunda correcao — negacao no ponto de decisao, so
  construtor DIRETO e ancorado em literal): CONSENSO NAO-FECHADO —
  OS DOIS revisores, pela MESMA razao: construtor atribuido a
  VARIAVEL antes da comparacao (achado do codex) e `decode()` sobre
  receptor NAO literal — nome ou chamada, como
  `base64.b64decode(dado).decode()` (achado do kimi) — atravessavam.
  Arbitragem: TERCEIRA tentativa de correcao AUTORIZADA, com a
  ressalva explicita de que, se esta tambem residuar na MESMA familia,
  o proximo ciclo confronta se "mais uma tentativa" ainda e a resposta
  certa ou se o padrao vira limite PERMANENTE — como N5 ja e.

A CORRECAO SOB JULGAMENTO AGORA (leia `registros-de-correcao.txt`,
`99_correcao-p1a11.md` inteiro — ele documenta a correcao E o processo
de chegar nela):

  - `_construtor_direto_nao_resolvido`: `.decode()` deixa de exigir
    receptor literal — fecha os dois exemplos exatos do kimi;
  - `variaveis_de_construtor_nao_resolvido` (nova): ponto fixo POR
    ESCOPO de funcao que marca nomes atribuidos a partir de `chr()` ou
    `.join()`/`.format()` sobre receptor LITERAL (ou de outro nome ja
    marcado) — fecha o exemplo exato do codex;
  - DUAS tentativas MAIS AMPLAS foram tentadas e REVERTIDAS por
    medicao propria, ANTES desta versao: semear alias com QUALQUER
    construtor (incluindo f-string) e propagar por ARQUIVO INTEIRO
    devolveu 360 falsos positivos contra o acervo real; tirar a
    f-string mas manter `decode()` como semente, ainda por arquivo,
    devolveu 7. A versao final: `decode()` so amplia o construtor
    DIRETO (nao semeia alias), e o rastreamento e por ESCOPO de
    funcao. Medido depois: ZERO achados novos contra o acervo real.

LIMITES DECLARADOS PELO PROPRIO AUTOR, o que SOBREVIVE a esta correcao:
decisao sem `ast.Compare`; `join()`/`format()` continuam so sobre
receptor literal (ampliar colidiu com `os.path.join`, medido); um
construtor aninhado como ARGUMENTO de uma chamada NAO relacionada ao
comparando continua fora do alcance (tentativa de caminhar a subarvore
inteira do comparando pegou ZERO caso novo genuino e arrastou 3 falsos
positivos do proprio acervo, revertida); passagem de PARAMETRO entre
funcoes; atribuicao por `:=` (walrus) dentro da propria comparacao.

== 2. O QUE O REGISTRO DA P1-A.11 TAMBEM DECLARA ==

`99_decisao-p1a11.md` (o outro arquivo em `registros-de-correcao.txt`)
e o registro dos DOIS pareceres anteriores E da arbitragem que
autorizou esta correcao — leia-o para o contexto completo de como se
chegou aqui, inclusive um erro factual que o proprio autor cometeu
naquela DECLARACAO (secao "Errata do autor" daquele registro) e que o
codex corrigiu.

== 3. ACHADOS NOVOS QUE O AUTOR DECLARA CONTRA SI ==

a) esta e a TERCEIRA tentativa sobre a MESMA familia de defeito. As
   duas primeiras nao fecharam. Nao ha garantia de que esta feche —
   so a medicao de que, desta vez, o teste exerce os DOIS exemplos
   EXATOS que os dois revisores anteriores deram, e a reversao
   vermelha confirma que os testes caem sem o fix (3 de 11 na suite
   do arquivo);
b) o proprio processo de correcao errou DUAS vezes antes de convergir
   — as duas tentativas mais amplas nao foram descobertas por revisor
   nenhum, foram medidas pelo proprio autor DEPOIS de escreve-las. Um
   revisor mais cauteloso poderia ter pedido a mesma medicao e nao a
   recebido, se o autor nao a tivesse feito por conta propria;
c) `revisao_p1a11.py` — o despachante da rodada anterior — ficou FORA
   dos tres corpora de prova de redacao de PII por quase um dia
   inteiro (criado antes da arbitragem, registrado so nesta missao,
   junto com a correcao). Nenhum dado vazou (o despachante nunca
   rodou sem registro — foi so a PROVA que faltava, nao a operacao),
   mas e o mesmo padrao de "lista que nada prende" que este acervo ja
   tem tres missoes de trilha corrigindo, agora contra o proprio
   instrumento de revisao.

== 4. O QUE ESTE ACERVO NAO MEDE, E NAO SE PRESUME ==

- o VEREDITO VIGENTE do acervo e REPROVADO (P1-A.4); nenhuma missao
  posterior o moveu; nada aqui o move sem o seu parecer;
- a tese central segue nao medida em token (proxy de bytes);
- as corridas historicas da P2 (p21, p22-*) seguem com evidencia bruta
  DESTRUIDA (P1-A.6) — fora de escopo desta rodada;
- P1A4-4 segue NAO-JULGADO nesta rodada — aguarda a corrida real
  ponta a ponta, por decisao separada do Fundador; nao o julgue aqui;
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
            "  3. registros-de-correcao.txt    — o registro da P1-A.11 "
            "(dois pareceres + arbitragem) e o registro desta correcao, "
            "ancorados no commit ALVO\n\n")
    else:
        abertura = (
            "Revise em modo SOMENTE LEITURA o estado atual do laboratorio "
            "SSC+. No diretorio atual ha TRES arquivos, e voce precisa ler "
            "OS TRES POR INTEIRO antes de avaliar:\n"
            "  ./pacote-revisao.txt           — o estado sob julgamento\n"
            "  ./declaracoes-obrigatorias.txt — fatos que o autor e "
            "OBRIGADO a transmitir, varios contra o interesse dele\n"
            "  ./registros-de-correcao.txt    — o registro da P1-A.11 "
            "(dois pareceres + arbitragem) e o registro desta correcao, "
            "ancorados no commit ALVO\n\n")
    return abertura + (
        "Comece pelas declaracoes. Quem corrigiu, montou e despachou e a "
        "MESMA sessao: nada fecha sem o seu parecer.\n\n"
        "Contexto: o veredito vigente do acervo e REPROVADO (P1-A.4). Esta "
        "e a TERCEIRA tentativa de fechar o id 6 (fundido com P1A4-2): "
        "P1-A.10 dividiu, P1-A.11 foi NAO-FECHADO por CONSENSO dos dois "
        "revisores. A arbitragem que autorizou esta correcao ja declarou "
        "por escrito que, se ela tambem residuar na mesma familia, a "
        "pergunta do proximo ciclo e se o padrao vira limite PERMANENTE "
        "em vez de uma quarta tentativa.\n\n"
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
        "2. a linha 'MAJOR-6: FECHADO | NAO-FECHADO — <justificativa "
        "apontavel>'. Se voce julgar que P1A4-2 e o MESMO defeito, diga-o "
        "na mesma linha; a fusao ja e convergencia estabelecida nas duas "
        "rodadas anteriores, nao uma pergunta nova. NAO julgue N5 (aberto "
        "por decisao permanente) nem P1A4-4 (trilha separada, fora de "
        "escopo aqui);\n"
        "3. a linha 'CORRECAO: SUSTENTADA | NAO-SUSTENTADA — <motivo>' "
        "sobre `99_correcao-p1a11.md` como um todo — a correcao fecha o "
        "que diz fechar, o teste exerce os casos QUE OCORRERAM (os "
        "exemplos exatos dos dois revisores anteriores) e os limites "
        "declarados sao os reais?;\n"
        "4. SE MAJOR-6 continuar NAO-FECHADO: a linha 'PROXIMO-PASSO: "
        "NOVA-TENTATIVA | LIMITE-PERMANENTE — <motivo>' — na sua leitura, "
        "vale a pena tentar de novo, ou o padrao deveria virar limite "
        "declarado como N5? A arbitragem anterior fez esta pergunta por "
        "escrito e pediu a opiniao do proximo revisor;\n"
        "5. UMA linha por achado novo declarado — a, b, c da secao 3 das "
        "declaracoes — na forma 'DECLARADO-<letra>: CONFIRMO | "
        "NAO-CONFIRMO — <motivo>', com a FAMILIA ao final;\n"
        "6. a linha 'DEFEITO-NOVO: SIM | NAO — <o que, onde>' sobre a "
        "correcao desta rodada;\n"
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
        print("uso: revisao_p1a12.py codex|kimi <pacote.txt>",
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
        tmp = tempfile.mkdtemp(prefix=f"p1a12-revisao-{provider}-")
        skills = tempfile.mkdtemp(prefix=f"p1a12-skills-vazio-{provider}-")
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
            "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a12",
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
