"""Preflight da frota real (SSC+ P1-A — experimental, sem autoridade).

Diagnostico read-only dos CLIs de assinatura: auditoria economica
pre-invocacao, deteccao de CLI, status de login/auth, descoberta de
modelos e classificacao ELIGIBLE | SHADOW_ELIGIBLE | SUPERVISED |
BLOCKED. Nunca executa chamada produtiva a modelo, nunca solicita
pagamento, nunca altera arquivos do projeto.
"""

from .adaptadores import AdaptadorPreflight, extrair_modelos, \
    plano_reconhecido, sensor_subprocess
from .economia import (POLITICA_ECONOMICA, BillingDesconhecido,
                       ChavePaygDetectada, CliIndisponivel,
                       ConfigPaygPersistida, ConflitoAmbienteLogin,
                       DeclaracaoExpirada, ErroPreflight, ModeloRemovido,
                       OAuthAusente, PlanoNaoReconhecido, QuotaEsgotada,
                       ambiente_sanitizado, auditar_ambiente,
                       auditar_config, auditar_status)
from .frota_real import ESPECIFICACOES, EspecProvedor, espec_de, frota_real
from .pipeline import RESULTADOS, RelatorioPreflight, executar_preflight
from .sombra import (VALIDADE_MAXIMA_HORAS, DeclaracaoTier,
                     carregar_declaracoes, declaracao_valida, expira_em)

__all__ = [
    "AdaptadorPreflight", "BillingDesconhecido", "ChavePaygDetectada",
    "CliIndisponivel", "ConfigPaygPersistida", "ConflitoAmbienteLogin",
    "DeclaracaoExpirada", "DeclaracaoTier", "ESPECIFICACOES",
    "ErroPreflight", "EspecProvedor", "ModeloRemovido",
    "OAuthAusente", "POLITICA_ECONOMICA", "PlanoNaoReconhecido",
    "QuotaEsgotada", "RESULTADOS", "RelatorioPreflight",
    "VALIDADE_MAXIMA_HORAS",
    "ambiente_sanitizado", "auditar_ambiente", "auditar_config",
    "auditar_status", "carregar_declaracoes", "declaracao_valida",
    "espec_de", "executar_preflight", "expira_em", "extrair_modelos",
    "frota_real", "plano_reconhecido", "sensor_subprocess",
]
