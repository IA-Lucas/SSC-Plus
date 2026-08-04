#!/usr/bin/env python3
"""Revisao read-only da P1-A.4 por provider distinto — SSC+ (experimental).

Missao probatoria: submeter o ESTADO ATUAL (`3f24085`) a revisao
independente. Quem corrigiu nao certifica — o fechamento de cada um dos
DOZE MAJOR e dos QUATRO achados da P2 depende de pronunciamento explicito
do revisor. Esta missao nao altera codigo, teste nem politica; ela monta,
declara, envia e registra.

O pacote NAO e montado aqui. Ele e gerado por `pacote_p1a37.py`
(deterministico; duas geracoes em diretorios INDEPENDENTES com bytes e
SHA-256 identicos, mais regeneracao em clone limpo de OUTRO commit e sob
mutacao deliberada de dois arquivos julgados na arvore) e os MESMOS BYTES
sao copiados para o descartavel de cada revisor — nenhuma remontagem
entre revisores.

AS DECLARACOES OBRIGATORIAS VIVEM NESTE FONTE, e nao no pacote. O pacote
e funcao exclusiva de commits (e essa e a correcao do MAJOR #5); as
declaracoes sao ato desta missao, posterior ao ALVO, e nenhum gerador
ancorado em commit poderia carrega-las sem deixar de ser funcao dos
commits. Elas vao para o descartavel de cada revisor como
`declaracoes-obrigatorias.txt`, com SHA-256 registrado na evidencia e
conferido pelo proprio revisor — MESMOS BYTES para os dois, pela mesma
razao que o pacote.

Herda integralmente as correcoes ja ratificadas do instrumento da
P1-A.3.6:
- MAJOR #3 (isolamento): codex com `--sandbox read-only --ephemeral`;
  kimi sem sandbox de filesystem no CLI — restricao parcial mais
  DETECCAO por manifesto SHA-256 da arvore antes/depois. Mutacao fora do
  descartavel REPROVA a corrida (returncode 3), nao apenas aparece;
- MAJOR #4 (lease): `verificar_lock` com fence esperado IMEDIATAMENTE
  antes da persistencia, e nao so na abertura.

O tier declarado precisa estar VALIDO no instante da chamada; expirado =
PARADA (somente o proprietario renova). Executa DENTRO da capsula.

Uso: python 06_p1a/evidencias/revisao_p1a4.py codex|kimi <pacote.txt>
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
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a4"

sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       Vigilancia, redigir, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a4-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")

DECLARACOES = """\
DECLARACOES OBRIGATORIAS — SSC+ P1-A.4
=======================================
Transmitidas pelo autor do pacote ao revisor, por ordem do proprietario
do repositorio. Varias sao CONTRA o interesse de quem envia. Julgar sem
le-las e julgar contra premissa falsa.

--- 1. ACHADO A — read-only nao restringia o CLI ---
Medido em 2026-08-03 (`08_p2/99_achados-divergencias-20260803.md`):
`read-only` era rotulo, nao mecanismo. Nenhuma restricao de filesystem
chegava ao CLI invocado, o diretorio de trabalho do processo filho era
herdado do terminal — a RAIZ do repositorio — e `efeito_externo:
"nenhum"` era gravado POR DECLARACAO, sem que nada olhasse o disco.
Severidade ALTA, familia (F): o guarda AFIRMAVA a propriedade em vez de
EXERCE-LA.

CORRIGIDO NO MECANISMO A PARTIR DE `abc75e8` (missao P2.3): o codex passa
a receber `--sandbox read-only --cd <descartavel> --skip-git-repo-check
--ephemeral`, o processo filho corre no descartavel, a `Vigilancia` abre
e fecha em volta da invocacao, e o efeito externo do recibo passa a ser
MEDIDO por manifesto SHA-256 antes e depois.

O ACHADO A SEGUE ABERTO. Quem corrige nao certifica: ele so fecha quando
um revisor independente disser que fechou. Voce e esse revisor.

--- 2. ACHADO C — a receita das medicoes ---
Estava aberto porque `08_p2/medidor.py` nao tinha entrada de linha de
comando e os numeros da fronteira sairam de script de sessao ausente do
repositorio: o revisor recebia o resultado e nao a receita. Desde a P2.4
a receita esta VERSIONADA (`08_p2/receitas/`), com comando
(`python 08_p2/medidor.py --todas`) que refaz as cinco medicoes e confere
30 de 30 campos contra as evidencias.

A COBERTURA E DECLARADA E DESIGUAL, e o proprio comando a imprime: no
conjunto 79% dos bytes sao recontados do repositorio e 21% sao
TESTEMUNHO. Por classe: classe (a) 89,7% recontada; classe (b) 17,3%.
Citar o `2,766` da classe (b) e citar, sobretudo, testemunho. A resposta
do canal alternativo nunca foi gravada em nenhuma das cinco corridas, e
uma das cinco nao tem recibo (`UnicodeEncodeError` no console derrubou o
processo depois do sucesso do attempt).

O ACHADO C SEGUE ABERTO pela mesma regra.

--- 3. ACHADOS B e D — INTOCADOS ---
B (severidade BAIXA, fora das duas familias): o README da raiz promete
invocacao produtiva por `codex` E `kimi`, e o kimi nunca completou uma
corrida — `falha-quota` em 2026-08-03T02:38Z e 2026-08-03T11:56Z.
Remedio especificado e NAO executado: o README cita o que foi medido.

D (severidade BAIXA, fora das duas familias): o indice da raiz lista so
`08_p2/99_registro-p2.md`; os registros da P2.1 e da P2.2 — de onde vem
os numeros da fronteira — nao aparecem. Remedio especificado e NAO
executado: indice atualizado.

Nenhum dos dois foi tocado. Nao ha correcao para julgar; ha divergencia
viva, declarada.

--- 4. AS NOVE CORRIDAS ANTERIORES RODARAM SEM FOTOGRAFIA ---
As nove corridas da P2.0, P2.1 e P2.2 sao anteriores a `abc75e8` e
rodaram SEM manifesto de antes e depois. NAO SE SABE se alguma escreveu
em algum lugar. A correcao do ACHADO A nao alcanca o passado, e nada
neste pacote autoriza dizer que o passado esta limpo. A resposta honesta
sobre elas e "nao se sabe" — nem "escreveu", nem "nao escreveu".

--- 5. `--ephemeral` NAO IMPEDE ESCRITA EM `CODEX_HOME` ---
Medido durante a P2.3: com `CODEX_HOME` isolado, uma corrida recusada por
401 deixou `state_*.sqlite`, `logs_*.sqlite`, `installation_id` e outros
no diretorio. Fora das seis fontes vigiadas essa escrita NAO E DETECTADA
por este mecanismo. Limite conhecido, declarado aqui como limite — nunca
como propriedade. Vale para a corrida que produz a SUA revisao.

--- 6. OS DOZE MAJOR ABERTOS, COM O REMEDIO DE CADA ---
Abertos pelas revisoes independentes da P1-A.3.1 (seis) e da P1-A.3.6
(seis novos). Nenhum foi fechado por revisor. Tres pares (3/N3, 6/N5,
5/N6) tratam do mesmo objeto por lados diferentes: ficam com o MESMO
remedio e CONTAGEM SEPARADA — fundi-los transformaria doze em nove e
produziria aparencia de progresso.

Os seis NAO FECHADOS (numeracao original da P1-A.3.1):
 MAJOR-1  config do grok em SQLite. Remedio: alcancar a config, ou
          devolver INDETERMINADO em vez de `{}` — nunca classificar como
          limpo o que nao foi lido.
 MAJOR-2  teto de custo zero ancorado em prefixo textual. Remedio:
          ancorar `_ZERO` no VALOR NUMERICO parseado; casos `.0`, `00`,
          `0.00`, `0,0` no teste, e contraprova com franquia real.
 MAJOR-3  `contencao.py:isolamento` — o rotulo "deteccao integral"
          excede o mecanismo, que fotografa so a arvore do repositorio e
          exclui `locks/`. Remedio: separar ATRIBUICAO de DETECCAO;
          cobrir alem de `RAIZ` ou retirar a palavra "integral" do
          rotulo, com teste que reprove o rotulo excedente.
 MAJOR-4  `revisao_p1a2.main` persistia sem reverificar o lease.
          Remedio: `_verificar_lock(fence_esperado=...)` imediatamente
          antes da persistencia, com teste NO CAMINHO DE PERSISTENCIA.
 MAJOR-5  o pacote pedia julgamento sobre o proprio gerador e nao o
          incluia. Remedio: o gerador embute o proprio fonte com o
          SHA-256 ao lado, OU o pacote para de pedir esse julgamento.
 MAJOR-6  sentinela anti-P2 nao cobria `07_p1b` e nao resolvia alias,
          import nem concatenacao. Remedio: cobrir, resolver — ou NEGAR
          quando nao conseguir resolver.

Os seis NOVOS (abertos pelo veredito da P1-A.3.6):
 MAJOR-N1 `writelock.py:escritor-unico` — nomes distintos permitem
          escritores concorrentes entre missoes; "a ordem manual do
          Fundador nao substitui exclusao mutua". Remedio: lock UNICO do
          repositorio e `liberar()` que expire o lease concedido, com
          teste de NOMES DISTINTOS nos dois lados.
 MAJOR-N2 `leitores_config.py:falha-fechada` — fonte ausente, ilegivel
          ou JSON invalido vira `{}`, indistinguivel de configuracao
          limpa. Remedio: distinguir no VALOR "ausente/ilegivel" de
          "lida e vazia", e `auditar_config` falhar fechada no primeiro.
 MAJOR-N3 mesmo objeto do MAJOR-3, visto do outro lado. Mesmo remedio.
 MAJOR-N4 `revisao_p1a2.py:credenciais-e-PII` — `dir_descartavel` e
          `argv_publico` recebiam o caminho temporario cru e o JSON nao
          passava por redacao integral. Remedio: `_redigir` nos dois
          pontos, com teste que reprove o caminho cru e varra OS CINCO
          runners de uma vez.
 MAJOR-N5 mesmo objeto do MAJOR-6. Mesmo remedio, acrescido da resolucao
          de alias/import/concatenacao.
 MAJOR-N6 mesmo objeto do MAJOR-5. Mesmo remedio.

As missoes P1-A.3.7, P1-A.3.8 e P1-A.3.9 trabalharam sobre esses doze e
DECLARARAM O PROPRIO CONSERTO SEM FECHA-LO. O diff que voce recebe e o
estado depois desse trabalho. Nenhuma delas emitiu atestado de
aprovacao, e nenhuma podia.

--- 7. O QUE MAIS ESTE PACOTE NAO ESTABELECE ---
- NENHUMA revisao independente passou pela P2 — nem P2.0, nem P2.1, nem
  P2.2, nem P2.3, nem P2.4;
- a tese central do projeto (despachar poupa token) segue NAO MEDIDA EM
  TOKEN: nenhum dos dois CLIs reporta contagem, `tokens_reportados` sai
  `None`, e o que existe e uma proxy de BYTES com nove limites
  declarados;
- `executor_observado` e sempre `None`: sabe-se qual modelo foi
  RESOLVIDO, nunca qual respondeu;
- a franquia do kimi estava esgotada nas medicoes de 2026-08-03, entao
  `kimi -p` nunca foi validado num caminho de sucesso;
- a ORDEM entre relatar e persistir no runner da P2 continua sem guarda:
  corrida cujo artefato nao apareceu em `08_p2/evidencias/` ainda pode
  ter ocorrido.
"""


def _redigir(texto: str) -> str:
    """Redige usuario local e caminho local — delega a UNICA implementacao.

    ACHADO 10 da P1-A.3.5: havia nove copias desta redacao em tres
    forcas, nenhuma com teste. Copia local aqui reintroduziria o achado.
    """
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
    """Modelo efetivo quando o CLI o expoe no banner; senao, DESCONHECIDO."""
    m = re.search(r"^\s*model:\s*(\S+)", err or "", re.MULTILINE)
    return m.group(1) if m else "DESCONHECIDO (nao exposto pelo CLI)"


def _verificar_lock(fence_esperado: int | None = None) -> dict:
    return verificar_lock(RAIZ, SESSAO_LOCK, fence_esperado)


def _verificar_tier(provider: str) -> dict:
    """Tier declarado precisa estar valido NO INSTANTE da chamada."""
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


def montar_prompt() -> str:
    """Prompt curto (argv): pacote e declaracoes vao em arquivo."""
    return (
        "Revise em modo SOMENTE LEITURA o estado atual do laboratorio "
        "SSC+. No diretorio atual ha DOIS arquivos, e voce precisa ler "
        "OS DOIS POR INTEIRO antes de avaliar:\n"
        "  ./pacote-revisao.txt          — o estado sob julgamento\n"
        "  ./declaracoes-obrigatorias.txt — sete fatos que o autor do "
        "pacote e OBRIGADO a lhe transmitir, varios contra o proprio "
        "interesse dele\n\n"
        "Comece pelas declaracoes. Elas dizem quais achados seguem "
        "abertos, o que foi corrigido no mecanismo e nao foi certificado, "
        "e o que este acervo NAO mede. Julgar sem le-las e julgar contra "
        "premissa falsa.\n\n"
        "Contexto: a revisao independente da P1-A.3.1 REPROVOU este "
        "trabalho com SEIS MAJOR; a revisao da P1-A.3.6 pronunciou-se "
        "sobre os seis (NAO-FECHADO nos seis) e abriu SEIS NOVOS. Sao "
        "DOZE MAJOR abertos. O pacote que voce recebe e o estado DEPOIS "
        "do trabalho das missoes P1-A.3.7, P1-A.3.8 e P1-A.3.9 sobre "
        "eles, e depois da fase P2 inteira. Quem corrigiu nao certifica: "
        "e voce quem diz se cada um fechou. Uma correcao nao fecha por "
        "ter sido feita.\n\n"
        "Voce NAO pode escrever nada: responda apenas com a revisao em "
        "texto.\n\n"
        "Sua resposta precisa conter, NESTA ORDEM:\n"
        "1. as linhas PROVIDER, MODELO-OBSERVADO, CANAL, PACOTE-SHA256 "
        "(compute o SHA-256 de ./pacote-revisao.txt), DECLARACOES-SHA256 "
        "(idem para ./declaracoes-obrigatorias.txt) e ESCOPO;\n"
        "2. DOZE linhas, uma por MAJOR, exatamente nesta forma:\n"
        "   'MAJOR-<id>: FECHADO | NAO-FECHADO — <justificativa "
        "apontavel>', com <id> em 1,2,3,4,5,6,N1,N2,N3,N4,N5,N6. Nao "
        "funda os pares 3/N3, 6/N5 e 5/N6: sao doze linhas;\n"
        "3. QUATRO linhas, uma por achado da P2:\n"
        "   'ACHADO-<A|B|C|D>: FECHADO | NAO-FECHADO — <justificativa>';\n"
        "4. a linha 'DEFEITO-NOVO: SIM | NAO — <o que, onde>', que "
        "responde se as CORRECOES introduziram defeito novo;\n"
        "5. os achados, um por linha, prefixados por CRITICAL | MAJOR | "
        "MINOR | OBS, com arquivo:tema e descricao curta. CADA achado "
        "precisa terminar com a sua FAMILIA, obrigatoriamente, numa "
        "destas tres formas:\n"
        "   'FAMILIA: (F)' — o guarda AFIRMA a propriedade (docstring, "
        "rotulo, lista) em vez de EXERCER a interface real;\n"
        "   'FAMILIA: (N)' — classe que a varredura por alcance de linha "
        "nao media;\n"
        "   'FAMILIA: fora-de-ambas' — nem uma nem outra, com o motivo.\n"
        "   Sem a familia o criterio de parada deste repositorio nao pode "
        "ser aferido, e o relatorio nao serve para decidir. Para cada "
        "MINOR diga tambem se e bloqueante, com motivo. Se nao houver "
        "achado num nivel, NAO o invente;\n"
        "6. a linha final 'VEREDITO: APROVADO | APROVADO-COM-RESSALVAS | "
        "REPROVADO'.")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a4.py codex|kimi <pacote.txt>",
              file=sys.stderr)
        return 2
    provider = sys.argv[1]
    sys.stdout.reconfigure(errors="replace")
    lock = _verificar_lock()
    tier = _verificar_tier(provider)

    dados_pacote = Path(sys.argv[2]).read_bytes()
    pacote_sha256 = hashlib.sha256(dados_pacote).hexdigest()
    dados_decl = DECLARACOES.encode("utf-8")
    decl_sha256 = hashlib.sha256(dados_decl).hexdigest()

    env = ambiente_capsula()
    removidas = sorted(set(os.environ) - set(env))
    tmp = tempfile.mkdtemp(prefix=f"p1a4-revisao-{provider}-")
    skills = tempfile.mkdtemp(prefix=f"p1a4-skills-vazio-{provider}-")
    # MESMOS BYTES para os dois revisores: copia verbatim, sem remontagem.
    with open(os.path.join(tmp, "pacote-revisao.txt"), "wb") as f:
        f.write(dados_pacote)
    with open(os.path.join(tmp, "declaracoes-obrigatorias.txt"), "wb") as f:
        f.write(dados_decl)
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
    # MAJOR #4: lease reverificado AQUI, com o MESMO fence da abertura.
    lock = _verificar_lock(fence_esperado=lock["fence"])
    meta = {
        "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a4",
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
                      "declaracoes_sha256": decl_sha256,
                      "modelo_efetivo": meta["modelo_efetivo_no_banner"],
                      "contencao_violada": bool(fora_do_descartavel),
                      "resposta_inicio": meta["resposta"][:400]},
                     ensure_ascii=False, indent=2))
    if fora_do_descartavel:
        print("PARADA: contencao violada — mutacao fora do descartavel: "
              + "; ".join(fora_do_descartavel[:20]), file=sys.stderr)
        return 3
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
