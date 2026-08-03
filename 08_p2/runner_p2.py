"""Runner da P2 — a tarefa sai da frota, e nao do bolso de ninguem.

CONSUMIDOR DECLARADO do veredito. Autorizado pelo ato soberano de
2026-08-03 (`08_p2/00_ato-soberano-p2.md`).

Executar SOMENTE pelo entry point da capsula, com lease de nome proprio:

    $env:SSC_LOCK_SESSAO = "p2-ops"
    python 06_p1a/capsula.py python 08_p2/runner_p2.py `
        --preflight 07_p1b/evidencias/<a corrida mais recente>.json `
        --tarefa "o que se quer feito"

POR QUE ELE EXIGE UM ARQUIVO DE PREFLIGHT, em vez de rodar o proprio.
A P1-B.01 registrou como divergencia em aberto que o runner da P1-B
mantem o proprio laco de classificacao, com a mesma forma do laco do
runner da P1-A. Um terceiro laco aqui seria a terceira copia do mesmo
guarda — e a varredura de guardas deste acervo ja contou quatro copias de
um outro, das quais so uma tinha o conserto. O veredito que esta corrida
consome e portanto um ARTEFATO DATADO, produzido pelo runner ratificado,
auditavel depois por quem nao estava aqui.

O preco disso e que a evidencia envelhece, e envelhecer em silencio seria
pior que a duplicacao: `--validade-h` recusa preflight velho demais
(padrao 24 h, a mesma janela da declaracao de tier). Preflight vencido =
PARADA, nunca execucao com veredito de ontem.

O QUE ESTE RUNNER NAO FAZ:

- **nao classifica provedor.** Le a classificacao pronta;
- **nao decide economia.** Os portoes sao os de `Frota`/`AdaptadorAssinatura`,
  ratificados na P0. Aqui so se le o motivo do veto e se imprime;
- **nao escreve no repositorio alvo.** O envelope nasce `read-only` e
  `pode_escrever: False`. A P2 le e responde; nao aplica patch;
- **nao gasta alem da assinatura.** `teto_custo = 0.0` no orcamento: um
  attempt que reportasse custo variavel positivo estoura o portao de
  orcamento ANTES do proximo attempt.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import caminhos

sys.path.insert(0, os.path.join(caminhos.RAIZ, "05_p0", "cenarios"))
sys.path.insert(0, os.path.join(caminhos.RAIZ, "06_p1a", "evidencias"))

import frota_medida                                          # noqa: E402
from capsula import exigir_capsula_limpa, verificar_capsula   # noqa: E402
from comum import Lab                                         # noqa: E402
from contencao import redigir, verificar_lock                 # noqa: E402
from preflight.frota_real import ESPECIFICACOES               # noqa: E402
from provedor_assinatura import (ProvedorAssinaturaReal,      # noqa: E402
                                 TIMEOUT_PADRAO_S)
from ssc_p0.evidence import EvidencePlane                     # noqa: E402
from ssc_p0.frota import (AdaptadorAssinatura, Frota,         # noqa: E402
                          STOP_WAIT_RESET, catalogo_de_frota,
                          envelope_de_frota, executar_com_frota,
                          politica_de_frota)

_SESSAO_LOCK = os.environ.get("SSC_LOCK_SESSAO", "p2-ops")
DIR_SAIDAS = os.path.join(caminhos.RAIZ, "08_p2", "evidencias")
DIR_LABS = os.path.join(caminhos.RAIZ, "08_p2", "saidas", "labs")
VALIDADE_PREFLIGHT_H = 24


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _no_codec_do_console(texto: str) -> str:
    """Texto de procedencia de MODELO, reduzido ao que o console aceita.

    Degradacao de EXIBICAO, declarada: caractere fora do codec do console
    sai como substituto. O byte gravado no CAS nao e tocado — a mesma
    separacao que o achado 5.3 da P2.1 mediu (dano de exibicao, nunca
    perda gravada).
    """
    codec = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        return texto.encode(codec, errors="replace").decode(codec,
                                                            errors="replace")
    except LookupError:                     # codec do console desconhecido
        return texto.encode("ascii", errors="replace").decode("ascii")


def relatar(registro: dict) -> None:
    """Imprime o desfecho da corrida SEM deixar o console decidir se ela existiu.

    MEDIDO NA P2.2, e a razao de esta funcao existir. A resposta do codex
    trouxe `→`; o console da estacao codifica cp1252; `print` levantou
    `UnicodeEncodeError` na linha que exibia a saida — e essa linha fica
    ANTES do bloco que reverifica o lease e persiste a evidencia. O attempt
    tinha dado **sucesso**: a franquia foi gasta, a cadeia ficou gravada no
    laboratorio, e o artefato de registro em `08_p2/evidencias/` nao
    existiu. Um caractere que o console nao sabe desenhar nao pode decidir
    se a corrida foi registrada.

    Todo texto de procedencia de modelo — `detalhe`, motivos de veto e a
    `saida` — passa por `_no_codec_do_console`. Os rotulos fixos sao ASCII
    e nao precisam, mas atravessam junto porque separa-los criaria dois
    caminhos de impressao e um deles voltaria a ser o cru.
    """
    for descarte in registro["montagem"]["descartes"]:
        print(_no_codec_do_console(
            f"  descartado {descarte['provider_id']}: {descarte['motivo']}"))
    for veto in registro["montagem"]["vetos"]:
        print(_no_codec_do_console(
            f"  VETADO {veto['provider_id']}/{veto['model_id']}: "
            f"{'; '.join(veto['motivos'])}"))
    for att in registro["attempts"]:
        ex = att["executor_resolvido"]
        print(_no_codec_do_console(
            f"  attempt {ex['provedor']}/{ex['modelo']}: {att['resultado']}"))

    print(_no_codec_do_console(
        f"\nstatus: {registro['status']}"
        + (f" ({registro['detalhe']})" if registro.get("detalhe") else "")))
    if registro.get("saida"):
        print("\n--- saida ---")
        print(_no_codec_do_console(registro["saida"]))


def carregar_preflight(caminho: str, validade_h: int,
                       agora: datetime | None = None) -> dict:
    """Le a evidencia do preflight e RECUSA o que nao serve.

    Cinco recusas, todas fail-closed — evidencia que o runner nao
    consegue validar nao pode virar autorizacao de gasto:

    1. arquivo ausente ou JSON ilegivel;
    2. sem o bloco `frota` (nao e evidencia de preflight);
    3. sem `gerado_em_utc` legivel — sem data nao ha como saber se venceu;
    4. datada no FUTURO: relogio que ainda nao chegou la nao verifica nada
       (a mesma regra de `sombra.declaracao_valida`);
    5. mais velha que a janela declarada.
    """
    instante = agora or agora_utc()
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"PARADA: preflight ilegivel ({type(exc).__name__})")
    if not isinstance(dados.get("frota"), list):
        raise SystemExit("PARADA: arquivo sem bloco `frota`; nao e evidencia "
                         "de preflight")
    try:
        gerado = datetime.fromisoformat(
            str(dados["gerado_em_utc"]).replace("Z", "+00:00"))
        if gerado.tzinfo is None:
            raise ValueError("timestamp sem fuso")
        gerado = gerado.astimezone(timezone.utc)
    except (KeyError, ValueError, TypeError, OverflowError):
        raise SystemExit("PARADA: preflight sem `gerado_em_utc` legivel")
    if gerado > instante:
        raise SystemExit(f"PARADA: preflight datado no futuro ({gerado})")
    if instante - gerado > timedelta(hours=validade_h):
        idade = instante - gerado
        raise SystemExit(
            f"PARADA: preflight de {gerado.isoformat()} tem {idade} de idade, "
            f"acima da janela de {validade_h}h. Rode o preflight de novo — "
            "veredito de ontem nao autoriza gasto de hoje.")
    dados["_idade_s"] = int((instante - gerado).total_seconds())
    return dados


def fabrica_de_provedores(frota: Frota, timeout: int, sensor=None):
    """Devolve a fabrica que `Lab` usa para montar cada executor.

    O objeto entregue ao `ExecutionGateway` e o `AdaptadorAssinatura`
    RATIFICADO da P0 envolvendo o executor real — nunca o executor
    sozinho. E assim que o portao economico continua sendo o mesmo objeto
    que a P0 testa: se a entrada violar economia, canal ou automacao, a
    construcao levanta `PoliticaEconomicaViolada` e o subprocesso jamais
    existe.

    `sensor` e injetavel pela MESMA razao do preflight: sem ele, todo
    teste de ponta a ponta deste runner invocaria os CLIs de verdade e
    queimaria franquia de assinatura a cada corrida da suite. `None` usa
    o sensor real — a operacao nao precisa declarar nada.
    """
    por_chave = {(e.provider_id, e.model_id): e for e in frota.entradas}

    def fabrica(executor_id, executor, resolvido):
        entrada = por_chave[(executor["provedor"], executor["modelo"])]
        espec = ESPECIFICACOES[entrada.provider_id]
        return AdaptadorAssinatura(
            entrada,
            ProvedorAssinaturaReal(espec, sensor=sensor, timeout=timeout))

    return fabrica


def executar(tarefa: str, criterio: str, preflight: dict,
             capacidade: str | None = None, papel: str = "autor",
             timeout: int = TIMEOUT_PADRAO_S, raiz_lab: str | None = None,
             idempotency_key: str | None = None, sensor=None) -> dict:
    """Uma tarefa, da frota medida ao veredito — devolve o registro."""
    montagem = frota_medida.frota_do_preflight(preflight["frota"],
                                               ESPECIFICACOES)
    if not montagem["entradas"]:
        return {"status": STOP_WAIT_RESET, "montagem": montagem,
                "detalhe": "nenhuma assinatura habilitada pelo preflight; "
                           "migrar para API paga e PROIBIDO"}

    # `--capacidade` precisa MUDAR a escolha, nao so decorar o perfil da
    # WorkUnit. `executar_com_frota` toma o PRIMEIRO elegivel, e
    # `Frota.elegiveis` preserva a ordem das entradas — entao a
    # preferencia se exerce ordenando a frota, sem tocar o codigo
    # ratificado da P0 e sem criar um segundo seletor ao lado do dela.
    #
    # Sem esta ordenacao a flag seria declaracao morta: aceita na linha de
    # comando, registrada na evidencia e sem efeito nenhum sobre quem
    # recebe a tarefa. E exatamente a familia que a P1-A.3.9 mediu.
    entradas = sorted(
        montagem["entradas"],
        key=lambda e: capacidade not in e.capability_profile.get(
            "capacidades", []))
    frota = Frota(entradas)
    elegiveis = frota.elegiveis(papel=papel)
    if not elegiveis:
        return {"status": STOP_WAIT_RESET, "montagem": montagem,
                "detalhe": "entradas construidas, mas TODAS vetadas pelos "
                           "portoes; ver `vetos`"}

    raiz_lab = raiz_lab or os.path.join(
        DIR_LABS, agora_utc().strftime("%Y%m%dT%H%M%SZ"))
    os.makedirs(raiz_lab, exist_ok=True)
    lab = Lab(raiz_lab,
              catalogo=catalogo_de_frota(frota),
              politica=politica_de_frota(frota),
              aprovacao=envelope_de_frota(frota),
              # external_variable_cost_cap = 0: custo variavel positivo
              # estoura o portao de orcamento ANTES do proximo attempt.
              teto_custo=0.0,
              fabrica_provider=fabrica_de_provedores(frota, timeout,
                                                     sensor))

    wu = lab.router.forjar(
        intencao=tarefa[:4000],
        criterios={"criterio": criterio, "verificacao": "humana"},
        tipo="ato", nivel="L2",
        perfil={"modalidade": "texto", "ferramentas": [],
                "formato_saida": "livre", "contexto_max_tokens": 128000,
                "dominio": capacidade or "geral",
                "privacidade": "remoto-permitido",
                "latencia_max_ms": None, "orcamento_max_custo": None},
        classe="C1")

    resultado = executar_com_frota(
        lab, frota, wu, papel=papel,
        idempotency_key=idempotency_key or f"p2:{wu.work_unit_id}",
        entrada=tarefa.encode("utf-8"),
        # Sob assinatura o custo variavel externo e zero POR FATO — a
        # franquia ja esta paga. O default do Router (0.01, rotulo
        # `estimado`) e numero simulado da P0, e contra o teto real de
        # 0.0 ele escalonaria antes do primeiro attempt.
        custo_previsto={"valor": 0.0,
                        "rotulo": "assinatura-sem-custo-variavel"})

    registro = {"status": resultado.status, "detalhe": resultado.detalhe,
                "montagem": montagem, "work_unit_id": wu.work_unit_id,
                "sessao_id": lab.envelope.sessao_id,
                "linhagem_id": lab.envelope.linhagem_id,
                "raiz_lab": raiz_lab, "saida": None, "attempts": []}

    for attempt_id, registro_attempt in lab.kernel.attempts.items():
        att = registro_attempt["attempt"]
        if att.work_unit_id != wu.work_unit_id:
            continue
        registro["attempts"].append({
            "attempt_id": attempt_id,
            "executor_resolvido": {
                "provedor": att.executor_resolvido.get("provedor"),
                "modelo": att.executor_resolvido.get("modelo")},
            "resultado": att.resultado,
            "efeito_externo": att.efeito_externo,
            "custo_medido": att.custo_medido,
        })

    if resultado.status == "sucesso" and resultado.resultado is not None:
        att = lab.kernel.attempts[resultado.resultado.attempt_id]["attempt"]
        if att.artefato_ref:
            registro["saida"] = lab.kernel.cas.ler(att.artefato_ref).decode(
                "utf-8", errors="replace")

    # A EvidencePlane SO le: o placar sai do log verificado, nunca da
    # memoria deste processo.
    lab.kernel.verificar_integridade()
    registro["placar"] = EvidencePlane(
        raiz_lab, lab.envelope.sessao_id).projetar()
    return registro


def main(argv=None) -> int:
    exigir_capsula_limpa()

    p = argparse.ArgumentParser(
        description="Executa uma tarefa pela frota de assinaturas do SSC+.")
    p.add_argument("--preflight", required=True,
                   help="evidencia JSON do preflight ratificado")
    p.add_argument("--tarefa", help="o que se quer feito")
    p.add_argument("--tarefa-arquivo",
                   help="arquivo com a tarefa (alternativa a --tarefa)")
    p.add_argument("--criterio", default="resposta util a tarefa declarada",
                   help="criterio de aceite, CONGELADO na WorkUnit")
    p.add_argument("--capacidade", default=None,
                   help="capacidade preferida (ex.: implementacao, volume)")
    p.add_argument("--papel", default="autor",
                   choices=("autor", "revisor", "juiz"))
    p.add_argument("--timeout", type=int, default=TIMEOUT_PADRAO_S)
    p.add_argument("--validade-h", type=int, default=VALIDADE_PREFLIGHT_H)
    args = p.parse_args(argv)

    if bool(args.tarefa) == bool(args.tarefa_arquivo):
        raise SystemExit("PARADA: informe --tarefa OU --tarefa-arquivo")
    if args.tarefa_arquivo:
        with open(args.tarefa_arquivo, encoding="utf-8") as f:
            tarefa = f.read()
    else:
        tarefa = args.tarefa

    # `verificar_capsula` devolve a LISTA de nomes proibidos presentes,
    # nunca um dicionario de diagnostico (capsula.py:43). O runner ja
    # abortou em `exigir_capsula_limpa`; esta chamada existe para que a
    # evidencia registre o que foi medido, e nao o que se supos.
    violacoes_capsula = verificar_capsula(os.environ)
    lock = verificar_lock(caminhos.RAIZ, _SESSAO_LOCK)
    fence = lock.get("fence")
    preflight = carregar_preflight(args.preflight, args.validade_h)

    print(f"capsula: violacoes={violacoes_capsula} | "
          f"lease={_SESSAO_LOCK} fence={fence} | "
          f"preflight com {preflight['_idade_s']}s de idade")

    registro = executar(tarefa, args.criterio, preflight,
                        capacidade=args.capacidade, papel=args.papel,
                        timeout=args.timeout)

    relatar(registro)

    # Escritor unico verificado DE NOVO, com o MESMO fence, imediatamente
    # antes de persistir: entre a verificacao de abertura e agora correram
    # invocacoes de modelo, que sao a parte lenta (MAJOR #4).
    verificar_lock(caminhos.RAIZ, _SESSAO_LOCK, fence)
    os.makedirs(DIR_SAIDAS, exist_ok=True)
    nome = f"execucao-{agora_utc().strftime('%Y%m%dT%H%M%SZ')}.json"
    caminho = os.path.join(DIR_SAIDAS, nome)
    persistido = dict(registro)
    persistido["montagem"] = {
        "entradas": [f"{e.provider_id}/{e.model_id}"
                     for e in registro["montagem"]["entradas"]],
        "descartes": registro["montagem"]["descartes"],
        "vetos": registro["montagem"]["vetos"]}
    persistido["lock_escritor_unico"] = {"sessao": _SESSAO_LOCK,
                                         "fence": fence}
    persistido["capsula"] = {"violacoes_no_env_do_processo": violacoes_capsula}
    persistido["preflight_consumido"] = {
        "caminho": redigir(os.path.abspath(args.preflight)),
        "gerado_em_utc": preflight.get("gerado_em_utc"),
        "idade_s": preflight["_idade_s"]}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(json.loads(redigir(json.dumps(persistido,
                                                ensure_ascii=False))),
                  f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\nevidencia: {caminho}")
    return 0 if registro["status"] == "sucesso" else 1


if __name__ == "__main__":
    raise SystemExit(main())
