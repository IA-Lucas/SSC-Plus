"""Artefatos operacionais autenticados e persistidos atomicamente.

A chave HMAC e estado local (``locks/`` e ignorado pelo Git). Ela prova que
o preflight foi emitido por um processo que tinha acesso ao estado local da
estacao; nao protege contra outro processo executando como o mesmo usuario.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import uuid
from pathlib import Path


SCHEMA_PREFLIGHT = "ssc-plus/preflight-p1b/v1"
ALGORITMO = "hmac-sha256"

CHAVES_RAIZ = {
    "schema", "tipo", "gerado_em_utc", "lock_escritor_unico",
    "lock_verificado_antes_da_persistencia", "custo_variavel",
    "chamadas_de_modelo", "nota", "emenda_p1a3_item_1", "capsula",
    "sondas_medidas", "violacoes_ambiente_nomes",
    "env_sanitizado_remove_nomes", "frota", "atestacao",
}
CHAVES_FROTA = {
    "provider_id", "resultado", "caminho", "versao", "plano",
    "origem_credencial", "quota", "modelos", "sombra", "erros",
}
CHAVES_ERRO = {"tipo", "codigo", "detalhe", "alvo"}
CHAVES_SOMBRA = {
    "tier_declarado", "declarado_por", "declarado_em_utc",
    "expira_em_utc", "autorizacao",
}
CHAVES_ATESTACAO = {"algoritmo", "chave_id", "mac"}
CHAVES_LOCK = {"sessao", "pid_titular", "fence", "expira_em"}
CHAVES_EMENDA = {"tiers_declarados", "limite", "nota"}
CHAVES_CAPSULA = {
    "mecanismo", "violacoes_no_env_do_processo",
    "violacoes_no_env_classificado", "politica",
}


class ArtefatoInvalido(ValueError):
    pass


def _canonico(documento: dict) -> bytes:
    sem_atestacao = dict(documento)
    sem_atestacao.pop("atestacao", None)
    return json.dumps(sem_atestacao, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def caminho_chave_padrao(raiz: str | os.PathLike[str]) -> Path:
    return Path(raiz) / "locks" / "preflight-hmac.key"


def obter_ou_criar_chave(caminho: str | os.PathLike[str]) -> bytes:
    """Cria a chave somente no produtor; consumidores nunca a inventam."""
    alvo = Path(caminho)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    try:
        chave_existente = alvo.read_bytes()
    except FileNotFoundError:
        chave = secrets.token_bytes(32)
        try:
            fd = os.open(alvo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return ler_chave_existente(alvo)
        with os.fdopen(fd, "wb") as arquivo:
            arquivo.write(chave)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        return chave
    if len(chave_existente) < 32:
        raise ArtefatoInvalido("chave local de atestacao invalida")
    return chave_existente


def ler_chave_existente(caminho: str | os.PathLike[str]) -> bytes:
    try:
        chave = Path(caminho).read_bytes()
    except OSError as exc:
        raise ArtefatoInvalido("chave local de atestacao ausente") from exc
    if len(chave) < 32:
        raise ArtefatoInvalido("chave local de atestacao invalida")
    return chave


def assinar_preflight(documento: dict, chave: bytes) -> dict:
    resultado = dict(documento)
    resultado["schema"] = SCHEMA_PREFLIGHT
    mac = hmac.new(chave, _canonico(resultado), hashlib.sha256).hexdigest()
    resultado["atestacao"] = {
        "algoritmo": ALGORITMO,
        "chave_id": hashlib.sha256(chave).hexdigest()[:16],
        "mac": mac,
    }
    return resultado


def _exigir_chaves(valor: object, esperadas: set[str], local: str) -> dict:
    if not isinstance(valor, dict) or set(valor) != esperadas:
        presentes = set(valor) if isinstance(valor, dict) else set()
        raise ArtefatoInvalido(
            f"schema fechado violado em {local}: "
            f"faltam={sorted(esperadas - presentes)} "
            f"sobram={sorted(presentes - esperadas)}")
    return valor


def validar_schema_preflight(documento: object) -> dict:
    raiz = _exigir_chaves(documento, CHAVES_RAIZ, "raiz")
    if raiz["schema"] != SCHEMA_PREFLIGHT:
        raise ArtefatoInvalido("schema de preflight desconhecido")
    if raiz["tipo"] != "preflight-atual-p1b":
        raise ArtefatoInvalido("tipo de artefato incorreto")
    _exigir_chaves(raiz["lock_escritor_unico"], CHAVES_LOCK,
                   "lock_escritor_unico")
    emenda = _exigir_chaves(raiz["emenda_p1a3_item_1"], CHAVES_EMENDA,
                            "emenda_p1a3_item_1")
    capsula = _exigir_chaves(raiz["capsula"], CHAVES_CAPSULA, "capsula")
    if not isinstance(emenda["tiers_declarados"], dict):
        raise ArtefatoInvalido("tiers_declarados nao e objeto")
    if not all(isinstance(k, str) and isinstance(v, str)
               for k, v in emenda["tiers_declarados"].items()):
        raise ArtefatoInvalido("tiers_declarados tem tipo invalido")
    if not all(isinstance(capsula[k], list) for k in (
            "violacoes_no_env_do_processo",
            "violacoes_no_env_classificado")):
        raise ArtefatoInvalido("listas da capsula invalidas")
    if not isinstance(raiz["sondas_medidas"], dict) or not all(
            isinstance(k, str) and isinstance(v, int) and v >= 0
            for k, v in raiz["sondas_medidas"].items()):
        raise ArtefatoInvalido("sondas_medidas invalido")
    for campo in ("violacoes_ambiente_nomes",
                  "env_sanitizado_remove_nomes"):
        if not isinstance(raiz[campo], list) or not all(
                isinstance(v, str) for v in raiz[campo]):
            raise ArtefatoInvalido(f"{campo} invalido")
    if not isinstance(raiz["frota"], list):
        raise ArtefatoInvalido("frota nao e lista")
    _exigir_chaves(raiz["atestacao"], CHAVES_ATESTACAO, "atestacao")
    for indice, relatorio in enumerate(raiz["frota"]):
        f = _exigir_chaves(relatorio, CHAVES_FROTA, f"frota[{indice}]")
        if not isinstance(f["provider_id"], str) or not isinstance(
                f["resultado"], str):
            raise ArtefatoInvalido(f"tipos invalidos em frota[{indice}]")
        if not isinstance(f["modelos"], list) or not isinstance(f["erros"], list):
            raise ArtefatoInvalido(f"listas invalidas em frota[{indice}]")
        if f["sombra"] is not None:
            _exigir_chaves(f["sombra"], CHAVES_SOMBRA,
                           f"frota[{indice}].sombra")
        for j, erro in enumerate(f["erros"]):
            _exigir_chaves(erro, CHAVES_ERRO,
                           f"frota[{indice}].erros[{j}]")
    return raiz


def verificar_preflight(documento: object, chave: bytes) -> dict:
    raiz = validar_schema_preflight(documento)
    atestacao = raiz["atestacao"]
    if atestacao["algoritmo"] != ALGORITMO:
        raise ArtefatoInvalido("algoritmo de atestacao desconhecido")
    chave_id = hashlib.sha256(chave).hexdigest()[:16]
    if not hmac.compare_digest(str(atestacao["chave_id"]), chave_id):
        raise ArtefatoInvalido("preflight assinado por outra chave")
    esperado = hmac.new(chave, _canonico(raiz), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(atestacao["mac"]), esperado):
        raise ArtefatoInvalido("assinatura do preflight nao confere")
    return raiz


def gravar_json_atomico(caminho: str | os.PathLike[str], documento: object) -> None:
    """Publica JSON completo por troca atomica; nunca deixa arquivo parcial."""
    alvo = Path(caminho)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    temporario = alvo.with_name(f".{alvo.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporario.open("x", encoding="utf-8", newline="\n") as arquivo:
            json.dump(documento, arquivo, ensure_ascii=False, indent=2,
                      sort_keys=True)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, alvo)
    finally:
        try:
            temporario.unlink()
        except FileNotFoundError:
            pass
