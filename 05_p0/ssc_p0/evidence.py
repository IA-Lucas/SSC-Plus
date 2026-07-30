"""Evidence Plane (D6 §2.6): memoria dos fatos.

SOMENTE LEITURA E PROJECAO sobre o EventLog (+ CAS para payloads).
NUNCA escreve no log nem no CAS: este modulo nao recebe nenhuma referencia
de escrita — so EventLog.verificar e CAS.ler.
"""

import json
import os

from .cas import CAS
from .eventlog import EventLog


class EvidencePlane:
    def __init__(self, raiz, sessao_id: str):
        self.raiz = os.path.realpath(str(raiz))
        self.sessao_id = sessao_id
        with open(os.path.join(self.raiz, "sessoes",
                               f"{sessao_id}.envelope.json"), "rb") as f:
            self.envelope = json.loads(f.read())
        from .canonico import sha256_de
        self.hash_genese = sha256_de(self.envelope)
        self.cas = CAS(os.path.join(self.raiz, "cas"))

    def _log_path(self) -> str:
        return os.path.join(self.raiz, "logs", f"{self.sessao_id}.jsonl")

    def eventos(self) -> list:
        """Le a cadeia verificada; devolve [{'evento', 'hash', 'payload'}]."""
        registros = EventLog.verificar(self._log_path(), self.hash_genese)
        saida = []
        for reg in registros:
            evento = reg["evento"]
            payload = json.loads(self.cas.ler(evento.payload_ref))
            saida.append({"evento": evento.to_dict(), "hash": reg["hash"],
                          "payload": payload})
        return saida

    def projetar(self) -> dict:
        """Projecoes descartaveis: telemetria, placar, divergencias.

        Custos/latencias sao medidos nos attempts (rotulo 'simulado' na P0);
        nunca estimado apresentado como medicao.
        """
        eventos = self.eventos()
        attempts = []
        divergencias = []
        vereditos = []
        escalacoes = []
        retries = []
        fallbacks = []
        workunits = {}
        decisoes = {}
        custo_total = 0.0
        tokens_total = 0
        for item in eventos:
            ev, payload = item["evento"], item["payload"]
            acao = payload.get("acao")
            if ev["tipo"] == "attempt" and acao in ("criar", "despachar",
                                                    "concluir", "orfao"):
                attempts = [a for a in attempts
                            if a["attempt_id"] != payload["attempt"]["attempt_id"]]
                attempts.append(payload["attempt"])
            elif ev["tipo"] == "attempt" and acao == "divergencia-observada":
                divergencias.append(payload)
            elif ev["tipo"] == "veredito" and acao == "registrar":
                vereditos.append(payload["veredito"])
            elif ev["tipo"] == "escalation":
                escalacoes.append(payload["escalacao"])
            elif ev["tipo"] == "retry":
                retries.append(payload["retry"])
            elif ev["tipo"] == "fallback":
                fallbacks.append(payload["fallback"])
            elif ev["tipo"] == "work-unit" and acao == "registrar":
                wu = payload["work_unit"]
                workunits[wu["work_unit_id"]] = wu
            elif ev["tipo"] == "work-unit" and acao == "transicao":
                workunits[payload["work_unit_id"]]["estado"] = payload["para"]
            elif ev["tipo"] == "routing" and acao == "registrar":
                dec = payload["decisao"]
                decisoes[dec["decisao_id"]] = dec
        placar = {}
        for a in attempts:
            if a.get("resultado") is None:
                continue
            resolvido = a.get("executor_resolvido", {})
            chave = f"{resolvido.get('provedor')}/{resolvido.get('modelo')}"
            p = placar.setdefault(chave, {"attempts": 0, "sucesso": 0,
                                          "custo_simulado": 0.0,
                                          "latencias_simuladas_ms": []})
            p["attempts"] += 1
            if a["resultado"] == "sucesso":
                p["sucesso"] += 1
            custo = a.get("custo_medido") or {}
            p["custo_simulado"] = round(
                p["custo_simulado"] + custo.get("valor", 0.0), 6)
            custo_total = round(custo_total + custo.get("valor", 0.0), 6)
            tokens_total += custo.get("tokens", 0)
        return {
            "sessao_id": self.sessao_id,
            "linhagem_id": self.envelope["linhagem_id"],
            "n_eventos": len(eventos),
            "work_units": workunits,
            "decisoes": decisoes,
            "attempts": attempts,
            "vereditos": vereditos,
            "escalacoes": escalacoes,
            "retries": retries,
            "fallbacks": fallbacks,
            "divergencias_observado_resolvido": divergencias,
            "placar_por_executor": placar,
            "custo_total": {"valor": custo_total, "rotulo": "simulado"},
            "tokens_total": {"valor": tokens_total, "rotulo": "simulado"},
        }
