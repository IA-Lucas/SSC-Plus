"""Executor REAL de assinatura — o backend que substitui o FakeProvider.

Autorizado pelo ato soberano de 2026-08-03
(`08_p2/00_ato-soberano-p2.md`). Ate aqui todo o SSC+ rodava contra
`FakeProvider`; este modulo e o primeiro do laboratorio que invoca modelo
de verdade, e por isso quase tudo nele e sobre NAO fazer isso errado.

O QUE ELE NAO FAZ, e cada ausencia e deliberada:

- **nao le veredito.** Recebe uma `FleetEntry` que ja passou pelos
  portoes e uma `EspecProvedor`; nao sabe o que e ELIGIBLE. E por isso
  que ele NAO esta em `CONSUMIDORES_DECLARADOS` da sentinela anti-P2: o
  dia em que precisar estar e o dia em que o executor passou a decidir;
- **nao decide economia.** Quem veta e `frota.AdaptadorAssinatura`, o
  portao ratificado da P0, que envolve este objeto. Veto = este codigo
  nunca chega a existir como subprocesso;
- **nao monta argv por conta propria.** Usa `adaptadores.argv_de`, a
  MESMA regra do preflight (expande so o `~` do executavel, sem shell,
  sem expandvars, argumentos literais em lista);
- **nao inventa numero.** Custo variavel de assinatura e 0.0 porque a
  assinatura ja esta paga — isso e fato, nao estimativa. Contagem de
  token o CLI nao reporta: sai `tokens_reportados: None`, jamais zero por
  conveniencia;
- **nao rotula `simulado`.** A P0 rotula assim porque la tudo era
  simulado. Aqui a latencia foi medida no relogio e o rotulo diz
  `medido`.

TODA execucao externa passa por um sensor injetavel
`sensor(argv, env, timeout) -> (rc, stdout, stderr)`, como no preflight.
Nos testes, sensores falsos substituem qualquer subprocesso: nenhum teste
desta missao invoca CLI real, e nenhum gasta franquia de assinatura.
"""

import subprocess
import time

import caminhos  # noqa: F401  (insere 05_p0/06_p1a/08_p2 no sys.path)

from preflight.adaptadores import argv_de, quota_esgotada
from ssc_p0.frota import ambiente_sanitizado
from ssc_p0.providers import RespostaProvedor

# Teto de parede de uma invocacao produtiva. Generoso de proposito: uma
# tarefa de codigo real e ordens de grandeza mais lenta que as sondas de
# diagnostico do preflight (20 s). Estourar o teto NAO e falha do modelo —
# e efeito externo INCERTO (IR-2), sem retry automatico.
TIMEOUT_PADRAO_S = 900

# Codigo que o sensor devolve quando o teto de parede estourou. Mesmo
# valor do sensor de preflight, pela mesma razao: 124 e o codigo que
# `timeout(1)` usa, e reusa-lo evita inventar um dialeto proprio.
RC_TIMEOUT = 124

# Marcadores de falha TRANSITORIA (429/5xx/rede). Retry so acontece sob
# IR-1 — com idempotency_key ou efeito comprovadamente nao-aplicado — e o
# Execution Gateway e quem aplica essa regra, nao este modulo.
_MARCADORES_TRANSITORIOS = (
    "429", "rate limit", "rate_limit", "too many requests",
    "500", "502", "503", "504", "internal server error",
    "bad gateway", "service unavailable", "gateway timeout",
    "temporarily unavailable", "connection reset", "connection refused",
    "econnreset", "etimedout", "timed out", "try again",
)

# Marcadores de CLI ausente/quebrado. Nao e falha do modelo: e o
# executavel que nao respondeu. Classifica como `falha-contrato` (zero
# retry) de proposito, para que o fallback leve a tarefa a OUTRA
# assinatura em vez de insistir num CLI que nao existe.
_MARCADORES_CLI_INDISPONIVEL = (
    "no such file", "not found", "command not found",
    "is not recognized", "permission denied",
)


def sensor_subprocess(argv, env=None, timeout: int = TIMEOUT_PADRAO_S):
    """Sensor real: subprocesso sanitizado, sem shell, com teto de parede.

    Captura stdout/stderr sem ecoa-los. `shell=False` (implicito na forma
    de lista) e o que torna literais os metacaracteres dos argumentos: o
    prompt de uma tarefa pode conter qualquer coisa, inclusive `|`, `&` e
    aspas, e nada disso pode virar comando.
    """
    ambiente = ambiente_sanitizado(env)
    try:
        proc = subprocess.run(list(argv), env=ambiente, capture_output=True,
                              text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return (RC_TIMEOUT, "", f"timeout de {timeout}s na invocacao")
    except (FileNotFoundError, OSError) as exc:
        # NAO propaga: o Execution Gateway espera uma RespostaProvedor, e
        # uma excecao aqui derrubaria a sessao inteira em vez de produzir
        # o attempt registrado que a evidencia exige.
        return (127, "", f"{type(exc).__name__}: executavel indisponivel")
    return (proc.returncode, proc.stdout or "", proc.stderr or "")


def classificar(rc: int, texto: str) -> tuple:
    """(falha, efeito_externo) a partir do que o CLI devolveu.

    Ordem de precedencia, e cada degrau tem razao propria:

    1. **timeout** vence tudo: enviou e nao houve resposta, entao o efeito
       e INCERTO. IR-2 proibe retry automatico daqui;
    2. **quota esgotada** vem antes de transitorio porque um "429" na
       mesma saida de um "0 requests remaining" e esgotamento, nao
       congestionamento — e confundir os dois faz o retry queimar a
       franquia que ja acabou. O detector e o do preflight, nao uma
       segunda lista;
    3. **CLI indisponivel** vira `falha-contrato` (zero retry) para que o
       fallback troque de assinatura em vez de insistir;
    4. **transitorio** por marcador explicito;
    5. **qualquer outro rc != 0** e `falha-contrato`: fail-closed. Erro
       que ninguem reconheceu NAO vira transitorio por otimismo — isso
       geraria retry contra uma falha determinista.

    `efeito_externo` e `nenhum` em tudo que nao seja timeout porque a P2
    opera em modo read-only por envelope. No dia em que houver escrita, e
    aqui que a distincao aplicado/nao-aplicado precisa nascer — e esta
    frase e o marco desse dia.
    """
    if rc == RC_TIMEOUT:
        return ("indeterminado", "incerto")
    if rc == 0:
        return (None, "nenhum")
    low = texto.lower()
    if quota_esgotada(low):
        return ("falha-quota", "nenhum")
    if any(m in low for m in _MARCADORES_CLI_INDISPONIVEL):
        return ("falha-contrato", "nenhum")
    if any(m in low for m in _MARCADORES_TRANSITORIOS):
        return ("falha-transitoria", "nao-aplicado")
    return ("falha-contrato", "nenhum")


class ProvedorAssinaturaReal:
    """Invoca o CLI de assinatura em modo nao-interativo.

    Interface identica a do `FakeProvider` — `invocar(entrada, pacote,
    idempotency_key) -> RespostaProvedor` —, de proposito: o
    `ExecutionGateway` ratificado nao muda uma linha para executar de
    verdade. Trocar simulado por real e trocar o objeto, nao a maquina.
    """

    def __init__(self, espec, sensor=None, timeout: int = TIMEOUT_PADRAO_S,
                 env=None, relogio=time.monotonic):
        self.espec = espec
        self.sensor = sensor or sensor_subprocess
        self.timeout = int(timeout)
        self.env = dict(env) if env is not None else None
        self.relogio = relogio
        self.chamadas = 0
        self.chaves_recebidas = []      # idempotency_keys propagadas (0.2.1-5)

    def argv(self, prompt: str) -> list:
        """argv nao-interativo: executavel + modo headless + prompt.

        `espec.headless` e o campo que a P1-A declarou e NUNCA usou —
        `codex exec`, `kimi -p`. A P2 e o primeiro uso dele, e passa a ser
        a razao de ele existir.
        """
        return argv_de(self.espec, list(self.espec.headless) + [prompt])

    def invocar(self, entrada: bytes, pacote: dict | None = None,
                idempotency_key: str | None = None) -> RespostaProvedor:
        """Uma invocacao produtiva, registrada mesmo quando falha.

        `pacote` (ContextPackage) NAO e enviado ao CLI nesta ordem: o
        prompt e `entrada`, e quem o compoe e o runner. Limite declarado,
        nao esquecimento — enviar contexto exige decidir formato e teto de
        tamanho, que e materia de outra ordem.
        """
        self.chaves_recebidas.append(idempotency_key)
        self.chamadas += 1
        prompt = (entrada or b"").decode("utf-8", errors="replace")

        inicio = self.relogio()
        rc, out, err = self.sensor(self.argv(prompt), self.env, self.timeout)
        latencia_ms = int(round((self.relogio() - inicio) * 1000))

        texto = (out or "") + "\n" + (err or "")
        falha, efeito = classificar(rc, texto)
        ok = falha is None

        return RespostaProvedor(
            ok=ok,
            # Em sucesso, a saida util e o stdout; em falha, os dois canais
            # combinados — o motivo costuma sair em stderr (a licao F-2 do
            # `codex login status`, que imprimia o status em stderr).
            saida=(out or "").encode("utf-8") if ok
            else texto.encode("utf-8"),
            falha=falha,
            # NUNCA reportado. O CLI nao ecoa qual modelo serviu a chamada,
            # e afirmar o resolvido aqui seria fabricar a confirmacao que o
            # Execution Gateway usa para detectar divergencia — o guarda
            # 0.2.1-9 passaria a se auto-confirmar. `None` e o valor
            # honesto, e o custo dele esta declarado no registro da ordem.
            executor_observado=None,
            efeito_externo=efeito,
            custo={"valor": 0.0, "rotulo": "medido-assinatura",
                   "tokens_reportados": None},
            latencia_ms=latencia_ms,
            latencia_rotulo="medido",
            retry_after_ms=None,
            idempotency_key=idempotency_key,
        )
