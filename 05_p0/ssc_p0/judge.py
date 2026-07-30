"""Evaluation / Judge (D6 §2.8): o veredito independente.

JULGA; nao executa, nao grava no log (emite o veredito ao Kernel).

Juiz 1 (deterministica): schemas, invariantes, checkpoints e criterios
mecanicos. Seu 'reprovado' VETA e nao e anulavel (IV-2) — o Kernel recusa
qualquer veredito posterior de outra camada sobre o mesmo artefato.

Juiz 2 (juiz-llm FALSO, deterministico por seed na P0): pacote_juiz completo;
independencia calculada ANTES de julgar, sobre executor_observado quando
disponivel (senao resolvido, marcado como tal); fila minima de candidatos
declarada; quem executou nao verifica (IV-1).
"""

from . import contratos as ct
from .canonico import novo_id, sha256_bytes


class IndependenciaImpossivel(Exception):
    """Fila sem candidato independente do executor: falha fechada."""


class Juiz1:
    """Camada deterministica. Veta e nao e anulavel (IV-2)."""

    NOME = "juiz1-deterministico"

    @staticmethod
    def validar_checkpoint(corpo: dict) -> dict:
        """Veredito deterministico sobre o checkpoint ANTES de gravar."""
        falhas = []
        refs = corpo.get("estado_refs", {})
        for campo in ("envelope", "ultimo_evento_hash", "seq"):
            if refs.get(campo) in (None, ""):
                falhas.append(f"estado_refs.{campo} ausente")
        if not isinstance(refs.get("seq"), int) or refs.get("seq", 0) < 1:
            falhas.append("estado_refs.seq invalido")
        if "pendentes" not in corpo.get("ponto_de_retomada", {}):
            falhas.append("ponto_de_retomada sem 'pendentes'")
        return {"aprovado": not falhas, "falhas": falhas,
                "verificador": Juiz1.NOME, "camada": "deterministica"}

    @staticmethod
    def julgar(kernel, wu: ct.WorkUnit, attempt_id: str, avaliador,
               causado_por: str | None = None,
               conclui: bool = True) -> ct.ValidationVerdict:
        """Julga mecanicamente. `avaliador(saida_bytes, pacote, attempt)`
        devolve (criterios: list[dict], resultado: str).
        `conclui=False` mantem a WU aguardando a camada seguinte."""
        reg = kernel.attempts[attempt_id]
        attempt = reg["attempt"]
        saida = b""
        ref = attempt.captura.get("saida_final_ref") or attempt.captura.get(
            "saida_estruturada_ref")
        if ref:
            saida = kernel.cas.ler(ref)
        # 0.2.1-7: falha fechada — pacote ausente/corrompido/cruzado levanta.
        pacote = kernel.ler_pacote(wu.contexto_ref, wu.work_unit_id)
        criterios, resultado = avaliador(saida, pacote, attempt)
        if resultado not in ct.RESULTADOS_VEREDITO:
            raise ct.FalhaContrato(f"avaliador devolveu {resultado!r}")
        veredito = ct.ValidationVerdict(
            veredito_id=novo_id(),
            alvo={"work_unit_id": wu.work_unit_id,
                  "artefato_ref": attempt.artefato_ref,
                  "attempt_id": attempt_id},
            camada="deterministica",
            verificador={"nome": Juiz1.NOME, "tipo": "deterministico"},
            pacote_juiz={"provedor": "local", "modelo": "deterministico",
                         "effort": "n/a",
                         "rubrica_ref": wu.criterios_aceite_ref,
                         "seed": None,
                         "hash_catalogo": kernel.envelope.catalogo_ref},
            criterios_ref=wu.criterios_aceite_ref,
            contexto_ref=wu.contexto_ref,
            independencia={"provedor_distinto_do_executor": True,
                           "modelo_distinto": True,
                           "base": "n/a",
                           "motivos": ["camada deterministica nao e modelo"],
                           "fila": []},
            resultado=resultado,
            criterios=list(criterios),
            efeitos={"artefato_ref": attempt.artefato_ref,
                     "placar": {"camada": "deterministica"},
                     "memoria": "veredito registrado"},
        ).validado()
        kernel.registrar_veredito(veredito, causado_por,
                                  transicionar=conclui)
        return veredito


class Juiz2:
    """Juiz-llm FALSO, deterministico por seed (mesmo regime dos providers)."""

    def __init__(self, candidatos: list, seed: int):
        """candidatos: fila declarada de {'provedor','modelo','effort'}."""
        if not candidatos:
            raise IndependenciaImpossivel("fila de candidatos vazia")
        self.candidatos = list(candidatos)
        self.seed = int(seed)

    def _independencia(self, attempt: ct.ExecutionAttempt) -> tuple[dict, dict]:
        """Calcula ANTES de julgar. Usa o OBSERVADO quando disponivel."""
        if attempt.executor_observado:
            alvo = attempt.executor_observado
            base = "observado"
        else:
            alvo = attempt.executor_resolvido
            base = "resolvido"
        for cand in self.candidatos:
            prov_ok = cand["provedor"] != alvo.get("provedor")
            mod_ok = cand["modelo"] != alvo.get("modelo")
            if prov_ok and mod_ok:
                return ({
                    "provedor_distinto_do_executor": True,
                    "modelo_distinto": True,
                    "base": base,
                    "motivos": [
                        f"candidato {cand['provedor']}/{cand['modelo']} "
                        f"distinto do executor ({base})",
                    ],
                    "fila": [f"{c['provedor']}/{c['modelo']}"
                             for c in self.candidatos],
                }, cand)
        return ({
            "provedor_distinto_do_executor": False,
            "modelo_distinto": False,
            "base": base,
            "motivos": ["nenhum candidato independente do executor"],
            "fila": [f"{c['provedor']}/{c['modelo']}" for c in self.candidatos],
        }, None)

    def julgar(self, kernel, wu: ct.WorkUnit, attempt_id: str, avaliador,
               rubrica_ref: str | None = None,
               causado_por: str | None = None) -> ct.ValidationVerdict:
        """Julga com pacote_juiz completo; independencia ANTES de julgar."""
        attempt = kernel.attempts[attempt_id]["attempt"]
        independencia, cand = self._independencia(attempt)
        if cand is None:
            raise IndependenciaImpossivel(
                "fila sem candidato independente: falha fechada")
        saida = b""
        ref = attempt.captura.get("saida_final_ref") or attempt.captura.get(
            "saida_estruturada_ref")
        if ref:
            saida = kernel.cas.ler(ref)
        if avaliador is not None:
            criterios, resultado = avaliador(saida, attempt)
        else:
            # Falso deterministico por seed: veredito derivado do hash.
            h = sha256_bytes(f"{self.seed}|{attempt_id}".encode("utf-8"))
            resultado = "aprovado" if int(h[:4], 16) % 10 < 8 else "inconclusivo"
            criterios = [{"criterio": "qualidade-simulada",
                          "evidencia": h[:12], "passou": resultado == "aprovado"}]
        veredito = ct.ValidationVerdict(
            veredito_id=novo_id(),
            alvo={"work_unit_id": wu.work_unit_id,
                  "artefato_ref": attempt.artefato_ref,
                  "attempt_id": attempt_id},
            camada="juiz-llm",
            verificador={"provedor": cand["provedor"], "modelo": cand["modelo"]},
            pacote_juiz={"provedor": cand["provedor"], "modelo": cand["modelo"],
                         "effort": cand.get("effort", "baixo"),
                         "rubrica_ref": rubrica_ref or wu.criterios_aceite_ref,
                         "seed": self.seed,
                         "hash_catalogo": kernel.envelope.catalogo_ref},
            criterios_ref=wu.criterios_aceite_ref,
            contexto_ref=wu.contexto_ref,
            independencia=independencia,
            resultado=resultado,
            criterios=list(criterios),
            efeitos={"artefato_ref": attempt.artefato_ref,
                     "placar": {"camada": "juiz-llm"},
                     "memoria": "veredito registrado"},
        ).validado()
        kernel.registrar_veredito(veredito, causado_por)
        return veredito


def fila_juizes_padrao() -> list:
    """Fila minima declarada: >= 2 candidatos independentes (D7 §8)."""
    return [
        {"provedor": "prov-b", "modelo": "modelo-l3", "effort": "alto"},
        {"provedor": "prov-c", "modelo": "modelo-juiz", "effort": "alto"},
    ]
