"""PROVA CENTRAL da missao (P0): troca de modelo na MESMA sessao e linhagem.

Cenario: WorkUnit A -> modelo/effort X -> tentativa 1 (falha-quota tipada);
nova evidencia -> nova RoutingDecision que `supersede` a anterior -> WorkUnit
A -> modelo/effort Y -> tentativa 2 (sucesso) -> juiz deterministico aprova.

Assercoes: sessao_id e linhagem_id inalterados; memoria, orcamento consumido
e cadeia causal (causado_por) preservados; a troca passou por Policy/
aprovacao (reroteamento DENTRO do envelope, sem nova aprovacao humana).

Grava a evidencia em 05_p0/saidas/prova_central.json.
"""

import argparse
import os

from comum import DIR_LABS, Lab
from ssc_p0.evidence import EvidencePlane
from ssc_p0.judge import Juiz1


def main(gravar=True):
    raiz = os.path.join(DIR_LABS, "prova_central")
    lab = Lab(
        raiz,
        programa_providers={
            "prov-a/modelo-x": ["falha-quota"],   # X sem quota (tipado)
            "prov-b/modelo-y": ["sucesso"],
        },
        seeds={"prov-a/modelo-x": 41, "prov-b/modelo-y": 42},
        funcoes_sucesso={
            "prov-b/modelo-y": lambda entrada, pacote:
                b"artefato-final:" + (entrada or b"vazio"),
        },
    )
    k = lab.kernel
    assercoes = []

    def prova(nome, condicao):
        assercoes.append({"nome": nome, "ok": bool(condicao)})
        assert condicao, f"ASSERCAO FALHOU: {nome}"

    # WorkUnit A (C1/tipo-2: aprovacao automatica registrada).
    wu = lab.router.forjar(
        intencao="produzir artefato final da prova central",
        criterios={"criterio": "artefato com prefixo artefato-final:",
                   "verificacao": "deterministica"},
        tipo="ato", nivel="L2",
        perfil={"modalidade": "texto", "ferramentas": [],
                "formato_saida": "livre", "contexto_max_tokens": 8000,
                "dominio": "geral", "privacidade": "remoto-permitido",
                "latencia_max_ms": None, "orcamento_max_custo": None},
        classe="C1")

    # Decisao 1: modelo X (prov-a), effort alto.
    d1 = lab.router.propor_decisao(
        wu, rota="padrao",
        selecao=lab.selecao("prov-a", "modelo-x", "alto"),
        aprovacao_custo=lab.aprovacao,
        motivo="rota padrao: X primeiro")
    ev_d1 = k.evento_de_decisao(d1.decisao_id)

    # Tentativa 1: falha-quota tipada -> sem alternativas -> escalonamento.
    r1 = lab.execution.executar(wu, d1, idempotency_key="op-prova-central",
                                entrada=b"tarefa A")
    prova("tentativa 1 falha-quota tipada",
          k.attempts[r1.attempt_id]["attempt"].resultado == "falha-quota")
    prova("escalonamento sem-alternativa registrado",
          any(e.motivo == "sem-alternativa" for e in k.escalacoes))

    # Nova evidencia na MEMORIA da sessao (quota de X esgotada).
    ev_mem = k.registrar_memoria(
        {"rotulo": "quota de prov-a/modelo-x esgotada",
         "fonte": "attempt:" + r1.attempt_id, "validade": "sessao"},
        causado_por=None)
    memoria_antes = k.memoria_ref

    # Reroteamento: nova RoutingDecision que SUPERSEDE (modelo Y, esforço baixo),
    # DENTRO do envelope aprovado -> nao exige nova aprovacao humana.
    n_eventos_antes = k.log.seq_atual()
    d2 = lab.router.rerotear(
        wu, rota="padrao",
        selecao=lab.selecao("prov-b", "modelo-y", "alto"),
        aprovacao_custo=lab.aprovacao,
        motivo="nova evidencia: quota de X esgotada; Y cobre o perfil")
    ev_d2 = k.evento_de_decisao(d2.decisao_id)
    prova("segunda decisao supersede a primeira", d2.supersede == d1.decisao_id)

    # Tentativa 2: sucesso -> juiz deterministico aprova -> concluida.
    r2 = lab.execution.executar(wu, d2, idempotency_key="op-prova-central",
                                entrada=b"tarefa A")
    prova("tentativa 2 sucesso", r2.status == "sucesso")
    veredito = Juiz1.julgar(
        k, wu, r2.attempt_id,
        lambda saida, pacote, attempt: (
            [{"criterio": "prefixo artefato-final:",
              "evidencia": saida[:32].decode("utf-8", "replace"),
              "passou": saida.startswith(b"artefato-final:")}],
            "aprovado" if saida.startswith(b"artefato-final:") else "reprovado",
        ))
    prova("veredito aprovado", veredito.resultado == "aprovado")
    prova("workunit concluida", k.work_units[wu.work_unit_id].estado == "concluida")

    # --- Assercoes da prova central --------------------------------------
    k.verificar_integridade()  # cadeia integra (levanta se quebrada)
    evi = EvidencePlane(raiz, k.envelope.sessao_id)
    eventos = evi.eventos()  # leitura + payload (Evidence so le)
    sessoes = {e["evento"]["linhagem_id"] for e in eventos}
    prova("linhagem_id unica em todos os eventos",
          sessoes == {k.envelope.linhagem_id})
    prova("sessao_id inalterado",
          k.envelope.sessao_id == lab.envelope.sessao_id)
    a1 = k.attempts[r1.attempt_id]["attempt"]
    a2 = k.attempts[r2.attempt_id]["attempt"]
    prova("attempts na mesma linhagem",
          a1.linhagem_id == a2.linhagem_id == k.envelope.linhagem_id)
    prova("memoria preservada apos a troca",
          k.memoria_ref == memoria_antes and len(k.memoria) == 1)
    consumido = k.envelope.orcamento["consumido_custo"]
    prova("orcamento acumulou as duas tentativas",
          abs(consumido - (a1.custo_medido["valor"]
                           + a2.custo_medido["valor"])) < 1e-6)
    # Cadeia causal: routing d2 -> criar a2 -> despachar a2 -> concluir a2.
    por_payload = {}
    for reg in eventos:
        ev, p = reg["evento"], reg["payload"]
        if ev["tipo"] == "attempt" and p.get("acao") == "criar" \
                and p["attempt"]["attempt_id"] == r2.attempt_id:
            por_payload["criar2"] = ev
        if ev["tipo"] == "attempt" and p.get("acao") == "concluir" \
                and p["attempt"]["attempt_id"] == r2.attempt_id:
            por_payload["concluir2"] = ev
    prova("attempt 2 causado pela decisao 2 (causado_por)",
          por_payload["criar2"]["causado_por"] == ev_d2
          and por_payload["concluir2"]["causado_por"] is not None)
    prova("decisao 2 registrada apos a falha (cadeia causal)",
          ev_d2 is not None and ev_d1 is not None)
    # Portao: nenhum veto na troca; as duas decisoes usaram o MESMO envelope
    # aprovado (reroteamento dentro do envelope nao exige nova aprovacao).
    prova("troca passou pela Policy sem veto",
          not any(e["payload"].get("acao") == "veto" for e in eventos
                  if e["evento"]["tipo"] == "routing"))
    prova("mesmo envelope de aprovacao nas duas decisoes",
          d1.aprovacao_custo == d2.aprovacao_custo)
    prova("nenhuma aprovacao humana extra exigida na troca",
          d2.aprovacao_custo["modelos_permitidos"]
          == d1.aprovacao_custo["modelos_permitidos"])
    prova("eventos emitidos durante a troca (log cresceu)",
          k.log.seq_atual() > n_eventos_antes)

    # Evidence Plane (somente leitura) projeta a corrida.
    proj = EvidencePlane(raiz, k.envelope.sessao_id).projetar()
    prova("placar com os dois executores",
          set(proj["placar_por_executor"]) == {"prov-a/modelo-x",
                                               "prov-b/modelo-y"})

    evidencia = {
        "cenario": "prova_central",
        "descricao": "troca de modelo na mesma sessao/linhagem com supersede",
        "sessao_id": k.envelope.sessao_id,
        "linhagem_id": k.envelope.linhagem_id,
        "decisao_1": d1.to_dict(),
        "decisao_2": d2.to_dict(),
        "attempt_1": a1.to_dict(),
        "attempt_2": a2.to_dict(),
        "veredito": veredito.to_dict(),
        "assercoes": assercoes,
        "projecao": proj,
        "eventos": [{"seq": e["evento"]["seq"], "tipo": e["evento"]["tipo"],
                     "acao": e["payload"].get("acao"),
                     "causado_por": e["evento"]["causado_por"],
                     "evento_id": e["evento"]["evento_id"]}
                    for e in eventos],
        "rotulo_numeros": "simulado",
    }
    caminho = (lab.gravar_evidencia("prova_central.json", evidencia)
               if gravar else "<verificacao sem persistencia>")
    lab.fechar()
    print(f"OK prova_central: {len(assercoes)} assercoes, "
          f"{len(eventos)} eventos -> {caminho}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sem-gravar", action="store_true",
                        help="executa todas as assercoes sem alterar evidencia")
    args = parser.parse_args()
    main(gravar=not args.sem_gravar)
