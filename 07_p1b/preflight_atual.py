"""Preflight ATUAL da frota real — SSC+ P1-B (experimental, sem autoridade).

Executar SOMENTE via entry point da capsula (P1-B.01, ordem 1):

    python 06_p1a/capsula.py python 07_p1b/preflight_atual.py

Executa o pipeline de preflight da P1-A (`06_p1a/preflight`) contra os 5
CLIs de assinatura DESTA estacao, AGORA, e persiste o relatorio em JSON.
Somente sondas de DIAGNOSTICO (versao/login/modelos): NENHUMA chamada de
modelo e feita; custo variavel = 0 por construcao (billing subscription).

Portoes herdados da P1-A/P1-A.1 (nao reimplementados aqui):
- toda sonda passa por `sensor_subprocess` com `ambiente_sanitizado`
  (credenciais PAYG nunca entram no subprocesso — `adaptadores.py:86`);
- violacao economica/auth bloqueia ANTES de qualquer sonda de modelo;
- google e grok tem teto SUPERVISED; ausencia de evidencia = unknown.

CAPSULA (P1-B.01, ordem 1). Ate aqui a garantia acima alcancava SOMENTE
as sondas-filho: o processo pai auditava e classificava `dict(os.environ)`
CRU, e `06_p1a/capsula.py` — ratificada na P1-A.2 — nunca era importada.
Uma chave PAYG de outro provedor visivel na estacao entrava em
`env_outras` (`pipeline.py:126-127`) e o runner degradava em silencio.
Passam a valer as duas metades da capsula, como no runner ratificado da
P1-A (`06_p1a/preflight_capsula.py:161`):

- ENTRADA: `exigir_capsula_limpa()` na primeira linha util de `main()` —
  fora da capsula o processo ABORTA antes do lease, antes de qualquer
  sonda e antes de qualquer escrita (`capsula.py:71`);
- AMBIENTE: o que o pipeline audita e classifica e `ambiente_capsula()`
  (`capsula.py:52`), nao `os.environ` cru — nenhum nome reprovado por
  `_nome_payg` chega a `env_outras`, por construcao e nao por confianca
  no portao de entrada.

O ambiente global/HKCU do usuario nunca e lido para alteracao, alterado
ou persistido: a decisao da P1-A.2 (`capsula.py:3-6`) continua valendo —
credencial de terceiro PODE existir no ambiente global; o SSC+ nao a
remove, apenas nao a deixa entrar na capsula.

TIERS DECLARADOS (P1-B.01, ordem 4). As declaracoes de tier do
proprietario (`06_p1a/tiers_declarados.json`) sao carregadas e repassadas
ao pipeline. Sem isso a trilha SHADOW_ELIGIBLE da emenda P1-A.3 item 1
era inalcancavel a partir daqui. Declaracao VENCIDA e reportada como
esta (`DeclaracaoExpirada`); renovar e ato do proprietario, nunca do
runner.

Escritor unico: antes de escrever a evidencia, este script VERIFICA o
lease `locks/<sessao>.lease` — a sessao vem de `SSC_LOCK_SESSAO`, com o
default historico `p1b-ops`. O lock e detido pelo processo titular da
sessao operacional; se o lease estiver morto ou o titular tiver sido
substituido, o script aborta SEM escrever (parada: lock perdido).

Redacao: o nome do usuario local nunca persiste — caminhos do home sao
gravados como <USUARIO>. Nenhum valor de config persistida e gravado:
`auditar_config` recebe o dict parseado em memoria e reporta somente
NOMES de campos violadores.
"""

import json
import os
import shlex
import sys
from datetime import datetime, timezone

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, "05_p0"))
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a"))
# `evidencias/` entra no path para que o escritor unico use a
# verificacao CANONICA (`contencao.verificar_lock`) em vez de uma quarta
# copia propria — ver `_verificar_lock_vivo`.
sys.path.insert(0, os.path.join(_RAIZ, "06_p1a", "evidencias"))

import leitor_tiers  # noqa: E402
import leitores_config  # noqa: E402
from capsula import (ambiente_capsula, exigir_capsula_limpa,  # noqa: E402
                     verificar_capsula)
from preflight.adaptadores import sensor_subprocess  # noqa: E402
from preflight.economia import ambiente_sanitizado, auditar_ambiente  # noqa: E402
from preflight.frota_real import frota_real  # noqa: E402
from preflight.pipeline import RESULTADOS, executar_preflight  # noqa: E402

_GITBASH = r"E:\LucasIA\Git\bin\bash.exe"
# Cada missao opera sob lease de NOME PROPRIO (condicao operativa do
# ACHADO 4): reusar o `.lease`/`.fence` da missao anterior confunde o
# titular. O default historico permanece para nao mudar o comportamento
# de quem nao declara sessao.
_SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p1b-ops")
# CLIs npm sem executavel Windows direto: a sonda vai pelo Git Bash.
_VIA_GITBASH = ("google", "grok")

# Teto da sonda via Git Bash. ERA 120 e passa a 60 na P1-A.3.9, alinhado
# com `06_p1a/preflight_capsula`. Escolhido por MEDICAO: o teto canonico
# da camada partilhada e `adaptadores.TIMEOUT_PADRAO = 20`, e a partida do
# Git Bash nesta estacao custa 0,35 s (5 corridas de `bash -lc true`; min
# 0,31, max 0,41) — a camada extra justifica ~21 s, e os 120 daqui
# carregavam ~99 s sem fundamento escrito. O timeout e fail-closed
# (rc 124 -> CliIndisponivel): encurtar nao transforma falha em passagem,
# so faz o portao decidir mais cedo, que e o que se quer de um preflight.
TIMEOUT_GITBASH = 60


def _redigir(texto: str) -> str:
    """ACHADO 10: era uma das TRES redacoes mais fracas do acervo —
    redigia so a forma longa do usuario e deixava passar a forma 8.3,
    que e a que `ZeroPiiNosArtefatos` procura. Delega a canonica."""
    from contencao import redigir
    return redigir(texto)


def _verificar_lock_vivo(fence_esperado: int | None = None) -> dict:
    """Lease vivo + fence do titular; aborta antes de gravar um byte.

    ACHADO 7 da P1-A.3.5 — o MAJOR #4 nunca alcancou esta copia. Esta
    funcao tinha TRES defeitos que a irma da P1-A ja nao tinha:

    1. nao aceitava `fence_esperado`, de modo que troca de titular entre
       a sonda e a gravacao passava despercebida;
    2. `main()` a chamava UMA unica vez, na abertura, e gravava depois
       das sondas reais — que e o defeito exato descrito pelo MAJOR #4
       (256 s de sonda observados contra 120 s de lease);
    3. a leitura do fence nao estava protegida, de modo que fence
       ilegivel virava excecao crua em vez de PARADA tipada.

    A verificacao passa a ser a CANONICA (`contencao.verificar_lock`),
    em vez de uma quarta copia divergente: a varredura de guardas contou
    quatro implementacoes do mesmo guarda, e esta era a unica sem o
    conserto. `expira_em` continua no retorno para nao mudar a forma das
    evidencias ja gravadas em `07_p1b/evidencias/`.
    """
    from contencao import verificar_lock
    estado = verificar_lock(_RAIZ, _SESSAO_LOCK, fence_esperado)
    caminho = os.path.join(_RAIZ, "locks", f"{_SESSAO_LOCK}.lease")
    try:
        with open(caminho, encoding="utf-8") as f:
            estado["expira_em"] = json.load(f)["expira_em"]
    except (OSError, ValueError, KeyError):
        # O lease acabou de ser validado; se sumiu entre uma leitura e
        # outra, a ausencia do campo informativo nao pode ser tratada
        # como sucesso silencioso.
        raise SystemExit("PARADA: lease desapareceu durante a verificacao")
    return estado


class _ContadorDeSondas:
    """Conta as sondas REAIS disparadas, por provedor (ordem 5).

    A evidencia precisa dizer quantas sondas correram, e sonda esperada
    nao substitui sonda medida: "google e grok tem zero sondas
    automaticas" e propriedade da especificacao, nao observacao desta
    corrida. O contador envolve o sensor real e conta invocacoes — o que
    o pipeline de fato executou. Nao le, nao guarda e nao registra argv,
    ambiente nem saida: somente a contagem.
    """

    def __init__(self, provedores=()):
        self.por_provedor = {pid: 0 for pid in provedores}

    def envolver(self, provider_id: str, sensor):
        def contado(*args, **kwargs):
            self.por_provedor[provider_id] = \
                self.por_provedor.get(provider_id, 0) + 1
            return sensor(*args, **kwargs)
        return contado


def _sensor_de(provider_id: str):
    """Sensor real; google/grok (npm) rodam via Git Bash na estacao."""
    if provider_id not in _VIA_GITBASH:
        return sensor_subprocess

    def sensor_gitbash(argv, env=None, timeout=TIMEOUT_GITBASH):
        comando = shlex.join([os.path.expanduser(str(a)) for a in argv])
        return sensor_subprocess([_GITBASH, "-lc", comando], env=env,
                                 timeout=timeout)
    return sensor_gitbash


# Leitores de config: implementacao UNICA em `leitores_config`, a mesma
# do runner da P1-A. Esta copia carregava OS DOIS defeitos que as
# correcoes 1 e 3 da P1-A.3.5 fecharam do outro lado — cegueira
# incondicional para grok e a allowlist de duas chaves no codex — porque
# a correcao alcancou so a copia que a suite exercita. Mesmo mecanismo
# do ACHADO 7 e do achado 10.
_config_persistida = leitores_config.config_persistida

# ORDEM 4: este runner tinha ZERO ocorrencia de `carregar_declaracoes` e
# omitia `tiers_declarados` na chamada ao pipeline, onde o parametro vale
# None (`pipeline.py:97`). Efeito medido: a trilha SHADOW_ELIGIBLE
# inteira — ratificada na emenda P1-A.3 item 1 — era inalcancavel a
# partir daqui MESMO com declaracao valida no disco. O leitor e o UNICO
# do acervo (`06_p1a/leitor_tiers.py`), partilhado com o runner da P1-A.
carregar_tiers = leitor_tiers.carregar_tiers

def main() -> int:
    # ORDEM 1(b): PRIMEIRA linha util. Fora da capsula o runner aborta
    # aqui — antes do lease, antes da primeira sonda e antes de qualquer
    # escrita —, em vez de degradar em silencio. Politica estrita da
    # P1-A.2: credencial de modelo visivel DENTRO da capsula = bloqueio.
    exigir_capsula_limpa()
    lock = _verificar_lock_vivo()
    # Declaracao VENCIDA nao e filtrada nem renovada aqui: ela chega ao
    # pipeline e sai como DeclaracaoExpirada no relatorio. Renovar e ato
    # do proprietario, nunca do runner.
    tiers = carregar_tiers()
    agora = datetime.now(timezone.utc)
    # ORDEM 1(a): ambiente de CAPSULA, derivado uma unica vez e usado
    # tanto na auditoria do relatorio quanto na classificacao de cada
    # provedor. `ambiente_capsula` reaudita o proprio resultado
    # (fail-closed): nenhum nome reprovado por `_nome_payg` sobrevive, e
    # portanto nenhum chega a `env_outras` no pipeline.
    ambiente = ambiente_capsula(os.environ)
    viol_ambiente = auditar_ambiente(ambiente)
    especs = list(frota_real())
    contador = _ContadorDeSondas(e.provider_id for e in especs)
    relatorios = []
    for espec in especs:
        rel = executar_preflight(
            espec,
            sensores=contador.envolver(espec.provider_id,
                                       _sensor_de(espec.provider_id)),
            env=ambiente,
            config_persistida=_config_persistida(espec.provider_id),
            tiers_declarados=tiers)
        relatorios.append(rel.to_dict())

    # ACHADO 7 / MAJOR #4: as sondas acima invocam os CLIs reais e podem
    # exceder a janela do lease (120 s). O escritor e reverificado AQUI,
    # imediatamente antes da persistencia, e o fence precisa ser o MESMO
    # da abertura — lease morto ou titular substituido = PARADA sem
    # gravar. Verificar so na abertura permitia gravar com lease morto.
    lock_persistencia = _verificar_lock_vivo(fence_esperado=lock["fence"])

    documento = {
        "tipo": "preflight-atual-p1b",
        "gerado_em_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lock_escritor_unico": lock_persistencia,
        "lock_verificado_antes_da_persistencia": True,
        "custo_variavel": 0,
        "chamadas_de_modelo": 0,
        "nota": "somente sondas de diagnostico (versao/login/modelos); "
                "nenhuma invocacao de modelo; env das sondas sanitizado "
                "pela canonica preflight.economia.ambiente_sanitizado",
        "emenda_p1a3_item_1": {
            "tiers_declarados": {pid: d.tier
                                 for pid, d in sorted(tiers.items())},
            "limite": "SHADOW_ELIGIBLE somente; validade maxima 24 h; "
                      "NAO autoriza P2 nem execucao autonoma",
            "nota": "declaracao vencida e reportada como esta "
                    "(DeclaracaoExpirada); renovar e ato do proprietario",
        },
        "capsula": {
            "mecanismo": "entrada por capsula.iniciar_em_capsula + guarda "
                         "exigir_capsula_limpa no processo + ambiente "
                         "derivado por capsula.ambiente_capsula",
            "violacoes_no_env_do_processo": verificar_capsula(dict(os.environ)),
            "violacoes_no_env_classificado": verificar_capsula(ambiente),
            "politica": "subscription-only; qualquer credencial de modelo "
                        "visivel dentro da capsula = bloqueio",
        },
        # Ordem 5: contagem MEDIDA de sondas por provedor nesta corrida —
        # nao a contagem que a especificacao faz esperar.
        "sondas_medidas": dict(sorted(contador.por_provedor.items())),
        "violacoes_ambiente_nomes": sorted(
            {v.alvo for v in viol_ambiente if v.alvo}),
        # Medido sobre o ambiente da CAPSULA (o que o pipeline recebe), e
        # nao sobre `os.environ` cru: dentro da capsula a sanitizacao das
        # sondas-filho nao tem mais nada a remover, e a lista vazia e o
        # resultado correto — nao um campo que deixou de ser medido.
        "env_sanitizado_remove_nomes": sorted(
            set(ambiente) - set(ambiente_sanitizado(ambiente))),
        "frota": relatorios,
    }
    texto = _redigir(json.dumps(documento, indent=2, ensure_ascii=False,
                                default=str))
    dir_saida = os.path.join(_RAIZ, "07_p1b", "evidencias")
    os.makedirs(dir_saida, exist_ok=True)
    nome = f"preflight-{agora.strftime('%Y%m%dT%H%M%SZ')}.json"
    caminho = os.path.join(dir_saida, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto + "\n")
        f.flush()
        os.fsync(f.fileno())

    print(f"evidencia: 07_p1b/evidencias/{nome}")
    for rel in relatorios:
        erros = ",".join(e["codigo"] for e in rel["erros"]) or "-"
        sombra = f" sombra={rel['sombra']['tier_declarado']}" \
            if rel.get("sombra") else ""
        # Largura 15: "SHADOW_ELIGIBLE" nao cabia em 10 e a coluna
        # seguinte saia desalinhada exatamente na trilha que a emenda
        # P1-A.3 item 1 criou.
        print(f"  {rel['provider_id']:7s} {rel['resultado']:15s} "
              f"plano={rel['plano'] or '-'} quota={rel['quota']} "
              f"sondas={contador.por_provedor.get(rel['provider_id'], 0)} "
              f"modelos={len(rel['modelos'])} erros={erros}{sombra}")

    # ORDEM 2: o sumario engolia tres dos quatro resultados. A ultima
    # linha impressa era `ELIGIBLE: []` — que com google e grok saindo
    # SUPERVISED (emenda P1-A.3 item 5) se le como "nenhum provedor
    # passou", quando o medido e outro. Os QUATRO resultados do enum
    # (`pipeline.RESULTADOS`) saem sempre, inclusive vazios: ausencia de
    # linha nao pode ser confundida com ausencia de provedor.
    por_resultado = {resultado: [] for resultado in RESULTADOS}
    fora_do_enum = []
    for rel in relatorios:
        por_resultado.get(rel["resultado"], fora_do_enum).append(
            rel["provider_id"])
    for resultado in RESULTADOS:
        print(f"{resultado}: {por_resultado[resultado]}")
    # A dataclass ja recusa resultado fora do enum; se um relatorio
    # chegar aqui por outro caminho, ele aparece — nunca desaparece na
    # particao.
    if fora_do_enum:
        print(f"FORA-DO-ENUM: {fora_do_enum}")
    print(f"total classificado: {sum(len(v) for v in por_resultado.values())}"
          f"+{len(fora_do_enum)} de {len(relatorios)} provedor(es)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
