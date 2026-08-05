#!/usr/bin/env python3
"""Revisao read-only da P1-A.6 por provider distinto — SSC+ (experimental).

DERIVADO MECANICAMENTE de `revisao_p1a4.py`. A MAQUINARIA e copiada
VERBATIM — capsula, vigilancia, lease com fence, redacao, mesmos bytes
aos dois revisores, e a reverificacao do lease imediatamente antes de
persistir (o desenho que o MAJOR #4 impos). O que muda, e SO isto:

  1. `SESSAO_LOCK` -> p1a6-ops; `SAIDA` -> revisao-p1a6; `tipo` ->
     revisao-p1a6;
  2. o bloco `DECLARACOES`, que e ato DESTA missao e nao do pacote;
  3. `montar_prompt`, porque o acervo mudou: sao NOVE MAJOR abertos, com
     outros ids, e nao mais os doze da P1-A.4.

POR QUE COPIA E NAO IMPORT. Cada missao congela o instrumento com que
julgou — e por isso o acervo tem revisao_p1a2, p1a3, p1a31, p1a33, p1a36
e p1a4. O que os achados 7, 10 e 14 punem e a copia que DIVERGE EM
SILENCIO, nao o snapshot declarado. O que diverge esta listado acima, e
nada alem disso diverge.

DECLARADO: este runner NAO foi escrito enquanto o portao estava fechado.
Codigo que ninguem roda e o defeito que este repositorio ja pagou tres
vezes; ele nasceu no momento em que podia ser exercitado.
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
SAIDA = RAIZ / "06_p1a" / "evidencias" / "revisao-p1a6"

sys.path.insert(0, str(RAIZ / "06_p1a"))
sys.path.insert(0, str(RAIZ / "05_p0"))
sys.path.insert(0, str(RAIZ / "06_p1a" / "evidencias"))

from capsula import ambiente_capsula  # noqa: E402
from contencao import (argv_kimi, enforcement_kimi,  # noqa: E402
                       Vigilancia, redigir, verificar_lock)

SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1a6-ops")
_KIMI_EXE = os.path.expanduser("~/.kimi-code/bin/kimi")

DECLARACOES = """\
DECLARACOES OBRIGATORIAS — SSC+ P1-A.6

Voce recebe estes fatos porque o autor do pacote e OBRIGADO a transmiti-los.
Varios sao contra o interesse dele. Julgar sem le-los e julgar contra
premissa falsa.

== 1. OS NOVE MAJOR ABERTOS, COM O REMEDIO DE CADA ==

O despacho desta missao fala em OITO. O acervo tem NOVE, e a divergencia
esta declarada e nao absorvida: N1 e P1A4-1 sao o MESMO defeito visto de
dois angulos, e fundi-los daria oito. A regra de contagem do acervo
(P1-A.3.6 secao 9.4, citada na P1-A.5 secao 5.2) mantem separado o trio
MAJOR-6/N5/P1A4-2, que tambem e um objeto so. Aplicada ao par, da NOVE.
Julgue os nove; se achar que sao oito, diga-o.

MAJOR-6  | sentinela contornavel por %/.format/join/import dinamico SEM
         | negacao. FAMILIA (N). Remedio: a varredura precisa NEGAR o que
         | nao consegue resolver. ABERTO, INTOCADO.
MAJOR-N1 | o escritor unico existia e NAO estava em uso. Remedio: adotar
         | no caminho operacional. FEITO na P1-A.5 ordem 2 — NAO FECHADO.
MAJOR-N5 | ha formas deliberadas de contorno ainda invisiveis e NAO
         | negadas. FAMILIA (N). Mesmo objeto do MAJOR-6. ABERTO, INTOCADO.
P1A4-1   | escritor_repositorio.py:adocao — o escritor correto existia SO
         | ISOLADAMENTE; falha de INTEGRACAO. Mesmo defeito do N1.
         | TRATADO na P1-A.5 ordem 2 — NAO FECHADO.
P1A4-2   | tests/sentinela_antip2.py:resolucao — %/.format/join e imports
         | dinamicos atravessam sem negacao. FAMILIA (N). Remedio:
         | construcao nao resolvida = REPROVA, nao = ignora. ABERTO.
P1A4-3   | 08_p2/provedor_assinatura.py:efeito-externo — o recibo afirma
         | "nenhum" apesar do alcance parcial e da escrita conhecida em
         | CODEX_HOME. FAMILIA (F). Remedio: declarar o ALCANCE do que o
         | recibo vigia. TRATADO na P1-A.5 ordem 3 — NAO FECHADO.
P1A4-4   | 08_p2/medidor.py:reprodutibilidade — a receita recompoe numeros
         | com insumos TESTEMUNHAIS; nao permite recontar respostas
         | alternativas nem a corrida sem recibo. Remedio: gravar a
         | evidencia bruta que falta. ABERTO — E PIORADO POR ESTA MISSAO,
         | ver secao 3.
P1A4-5   | 08_p2/runner_p2.py:persistencia — relatar(registro) vem ANTES
         | da reverificacao e da gravacao; nova falha de saida consome
         | franquia e perde o recibo. Remedio: mover relatar para DEPOIS.
         | ABERTO, INTOCADO.
P1A4-6   | tests/test_config_real_p1a39.py:acoplamento — o teste calcula
         | "auditados" so por FONTES, embora config_persistida("codex")
         | leia e mescle ~/.codex/config.toml: AFIRMA UM BURACO
         | INEXISTENTE SEM EXERCER A INTERFACE REAL. FAMILIA (F).
         | TRATADO na P1-A.5 ordem 3 — NAO FECHADO.

== 2. ACHADO A — read-only nao restringia o CLI ==

Corrigido NO MECANISMO a partir do commit abc75e8 ("a protecao sai do
texto e entra no argv, no cwd e na medicao"). O argv passou de

  <codex.exe> exec <tarefa>

para

  <codex.exe> exec --sandbox read-only --cd <descartavel>
              --skip-git-repo-check --ephemeral <tarefa>

ABERTO — quem corrige nao certifica.

LIMITE MEDIDO, declarado junto com o conserto: --ephemeral NAO IMPEDE
ESCRITA EM CODEX_HOME. A protecao no argv restringe o alcance; ela nao
torna verdadeira a afirmacao "efeito_externo: nenhum" do recibo — que e
exatamente o P1A4-3.

== 3. ACHADO C — a receita, a cobertura, e o dano que esta missao causou ==

Receita VERSIONADA desde a P2.4. Cobertura recontada e publicada em toda
corrida: classe (a) 89,7 % — classe (b) 17,3 %. O resto e testemunho.

DANO AUTOINFLIGIDO, e nao omitido por ser autoinfligido: esta missao
DESTRUIU 08_p2/saidas/labs/20260803T135101Z/, o UNICO lab de P2 que
existia, ao executar a limpeza de saidas/labs sem copia datada. Com ele
foram 1 TESTE e 5 SUBTESTS — a comparacao mais forte entre receita e
cadeia deixou de ser verificavel. A perda e IRREVERSIVEL: o caminho e
ignorado pelo Git, nunca esteve em commit, a lixeira nao o tem, e
regenerar exige refazer a corrida contra provedor.

A suite P1-A caiu de 914 passed / 1241 subtests para 913 passed /
1 skipped / 1236 subtests, e essa e a assinatura do dano.

Isto PIORA o P1A4-4, cujo remedio especificado e justamente GRAVAR a
evidencia bruta. Julgue-o como tal.

== 4. ACHADOS B e D — INTOCADOS ==

B | README.md:provedores-produtivos — o README promete codex e kimi, e o
  | kimi NUNCA completou uma corrida (quatro tentativas, todas mortas em
  | cota antes da leitura).
D | README.md:indice-P2 — o indice da raiz omite os registros P2.1 e P2.2,
  | que os numeros publicados usam.

== 5. ESCRITOR UNICO — ADOTADO na P1-A.5, com as tres provas ==

Um lock para o REPOSITORIO (locks/repositorio.lock), qualquer que seja o
nome da missao; o nome deixa de escolher o ARQUIVO e passa a ser o
TITULAR registrado no lease.

As tres provas: dois PROCESSOS REAIS; cinco pontos de chamada mais um
main() real; e o preflight na capsula. Mutante M4 (atribuicao sem
titular): 3 vermelhos. Segunda missao de outro nome: returncode 3, sem
adquirir e sem escrever.

EXERCIDO DE NOVO nesta missao: lease p1a6-ops, fences 9, 10 e 11,
verificado imediatamente antes de cada persistencia, e EXPIRADO SOZINHO
apos a morte do renovador — medido, nao afirmado.

NAO FECHADO: N1 e P1A4-1 so fecham por revisor independente.

== 6. CACHE FORA DA ARVORE, E A PORTA QUE NAO FOI CONSTRUIDA ==

P1-A.5.1: pytest.ini (-p no:cacheprovider) e conftest.py da raiz
(sys.pycache_prefix). Medido: 0 mutacoes no manifesto em quatro
condicoes; reversao vermelha M7 devolve 3 .pyc mais 2 do cache numa
corrida que falha — cinco ao todo.

TRES das quatro classes de mutacao que a contencao acusou na P1-A.4 somem
sem porta nenhuma. A QUARTA — a sessao editando um fonte — NAO e
alcancada por realocacao e CONTINUA ABERTA.

A PORTA esta REGISTRADA e NAO CONSTRUIDA, com o modo de falha que a
desaconselha hoje: morte do processo entre fechar e reverter deixa a
arvore INESCREVIVEL, sem reversao automatica, porque a permissao e estado
do sistema de arquivos e sobrevive ao processo. O PC do proprietario
desligou duas vezes na semana da P1-A.5.1, e o acervo ja tem o precedente
exato — a queda que deixou dois mutantes na arvore viva.

ASSIMETRIA, que precisa estar escrita: mutante esquecido deixa a arvore
ALTERADA MAS FUNCIONAL, e a suite o denuncia. Porta esquecida deixa a
arvore INTACTA E TRAVADA, e nenhuma suite roda para denunciar — o
instrumento de deteccao morre junto com o acesso.

RESSALVA: a porta IMPEDE, nao ATRIBUI. Ela nao responde "quem escreveu
este byte?"; torna a pergunta irrelevante DENTRO da janela e a deixa
intacta fora dela.

== 7. AS NOVE CORRIDAS ANTERIORES RODARAM SEM FOTOGRAFIA ==

Nas NOVE corridas anteriores a abc75e8 nao havia manifesto SHA-256
antes/depois. NAO SE SABE SE ELAS ESCREVERAM na arvore.

Lacuna HISTORICA e IRRECUPERAVEL: nao e propriedade de guarda, e nenhum
conserto futuro a alcanca. Nao se pede que voce a feche; pede-se que
registre que a leu.

== 8. O QUE ESTE ACERVO NAO MEDE, E NAO SE PRESUME ==

- QUOTA: o preflight devolveu "desconhecida" nos cinco provedores. No
  portao a quota NAO E MENSURAVEL. Nada afirma que haja cota.
- A TESE CENTRAL SEGUE NAO MEDIDA EM TOKEN: o acervo mede proxy de bytes,
  e executor_observado permanece None.
- O VEREDITO VIGENTE DO ACERVO E REPROVADO (P1-A.4), e nenhuma missao
  posterior o moveu.
- QUEM CORRIGE NAO CERTIFICA: P1-A.5 e P1-A.5.1 corrigiram. Nada nelas
  fecha nada.
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
        "  ./pacote-revisao.txt           — o estado sob julgamento\n"
        "  ./declaracoes-obrigatorias.txt — os fatos que o autor do "
        "pacote e OBRIGADO a lhe transmitir, varios contra o proprio "
        "interesse dele\n\n"
        "Comece pelas declaracoes. Elas dizem quais achados seguem "
        "abertos, o que foi corrigido no mecanismo e NAO foi certificado, "
        "que dano a propria missao causou, e o que este acervo NAO mede. "
        "Julgar sem le-las e julgar contra premissa falsa.\n\n"
        "Contexto: o veredito vigente do acervo e REPROVADO (P1-A.4). "
        "Estao abertos NOVE MAJOR. O pacote que voce recebe e o estado "
        "DEPOIS do trabalho das missoes P1-A.5 e P1-A.5.1 sobre eles. "
        "Quem corrigiu NAO certifica: e voce quem diz se cada um fechou. "
        "Uma correcao nao fecha por ter sido feita.\n\n"
        "Voce NAO pode escrever nada: responda apenas com a revisao em "
        "texto.\n\n"
        "Sua resposta precisa conter, NESTA ORDEM:\n"
        "1. as linhas PROVIDER, MODELO-OBSERVADO, CANAL, PACOTE-SHA256 "
        "(compute o SHA-256 de ./pacote-revisao.txt), DECLARACOES-SHA256 "
        "(idem para ./declaracoes-obrigatorias.txt) e ESCOPO;\n"
        "2. NOVE linhas, uma por MAJOR, exatamente nesta forma:\n"
        "   'MAJOR-<id>: FECHADO | NAO-FECHADO — <justificativa "
        "apontavel>', com <id> em 6, N1, N5, P1A4-1, P1A4-2, P1A4-3, "
        "P1A4-4, P1A4-5, P1A4-6. NAO funda N1 com P1A4-1, nem o trio "
        "6/N5/P1A4-2: sao nove linhas. Se julgar que a contagem correta "
        "e outra, diga-o em linha separada, com o motivo;\n"
        "3. QUATRO linhas, uma por achado da P2:\n"
        "   'ACHADO-<A|B|C|D>: FECHADO | NAO-FECHADO — <justificativa>';\n"
        "4. a linha 'DEFEITO-NOVO: SIM | NAO — <o que, onde>', que "
        "responde se as CORRECOES das missoes P1-A.5 e P1-A.5.1 "
        "introduziram defeito novo;\n"
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
        "6. para cada achado NOVO, diga se ele esta em AREA JA REVISADA "
        "ou em ESTREIA — e, se disser estreia, declare QUAL pacote "
        "anterior nao a continha. Sem essa declaracao ele conta como area "
        "ja revisada;\n"
        "7. a linha final 'VEREDITO: APROVADO | APROVADO-COM-RESSALVAS | "
        "REPROVADO'.")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in COMANDOS:
        print("uso: revisao_p1a6.py codex|kimi <pacote.txt>",
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
        "provider": provider, "ts_utc": ts, "tipo": "revisao-p1a6",
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
