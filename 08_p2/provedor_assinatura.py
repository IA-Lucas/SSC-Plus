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

import locale
import subprocess
import tempfile
import time

import caminhos  # (insere 05_p0/06_p1a/08_p2/evidencias no sys.path)

from contencao import Vigilancia, manifesto, mutacoes
from preflight.adaptadores import argv_de, quota_esgotada
from preflight.frota_real import MARCA_DESCARTAVEL, rotulo_restricao
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


def decodificar(bruto: bytes) -> str:
    """Bytes de um CLI -> texto, tentando as codificacoes que ocorrem.

    ACHADO DA PRIMEIRA CORRIDA REAL DA P2 (2026-08-03). O sensor decodava
    com `encoding="utf-8", errors="replace"` fixo, e a primeira resposta
    em portugues voltou assim:

        "O teste que afirma uma propriedade s� confirma..."

    Cada acento virou U+FFFD, e o dano nao e de exibicao: o texto
    corrompido foi para o CAS, entrou na cadeia de hashes e virou o
    artefato final da WorkUnit. Perda irreversivel, gravada como se fosse
    a resposta.

    A causa e o console do Windows: o CLI escreve na page de codigo do
    sistema (cp1252 nesta estacao), nao em UTF-8. Forcar UTF-8 e a
    suposicao; medir e tentar em ordem.

    A ordem importa e e fail-safe, nao fail-closed — aqui o pior desfecho
    nao e aceitar demais, e sim PERDER conteudo:

    1. **utf-8 estrito**: se casar, casou; e a codificacao correta e a
       mais provavel num CLI moderno;
    2. **a page de codigo local** (`locale.getpreferredencoding`), que e o
       que o Windows de fato entrega;
    3. **cp1252 explicito**, para a estacao cuja locale nao seja ela;
    4. **utf-8 com `replace`**, ultimo recurso: so entao se aceita perder
       caractere, e nunca antes de ter tentado.

    Latin-1 NAO entra: ele decodifica qualquer byte sem erro, entao
    colocado antes do fim engoliria os candidatos seguintes e produziria
    texto plausivel e errado, em silencio. Um decodificador que nunca
    falha e um decodificador que nunca avisa.
    """
    if not bruto:
        return ""
    tentativas = ["utf-8"]
    local = locale.getpreferredencoding(False)
    if local and local.lower() not in tentativas:
        tentativas.append(local)
    if "cp1252" not in [t.lower() for t in tentativas]:
        tentativas.append("cp1252")
    for codificacao in tentativas:
        try:
            return bruto.decode(codificacao)
        except (UnicodeDecodeError, LookupError):
            continue
    return bruto.decode("utf-8", errors="replace")


def sensor_subprocess(argv, env=None, timeout: int = TIMEOUT_PADRAO_S,
                      cwd: str | None = None):
    """Sensor real: subprocesso sanitizado, sem shell, com teto de parede.

    Captura stdout/stderr sem ecoa-los. `shell=False` (implicito na forma
    de lista) e o que torna literais os metacaracteres dos argumentos: o
    prompt de uma tarefa pode conter qualquer coisa, inclusive `|`, `&` e
    aspas, e nada disso pode virar comando.

    Captura em BYTES e decodifica com `decodificar`: deixar o `subprocess`
    decodar por nos fixa uma codificacao unica, e foi assim que a primeira
    resposta real em portugues chegou com todo acento trocado por U+FFFD.

    `cwd` EXPLICITO desde a P2.3 (achado A). Ate aqui o argumento estava
    ausente da chamada, e ausente nao e neutro: o filho herdava o
    diretorio do runner, que herdava o do terminal, que o passo 3 do
    `08_p2/README.md` deixa na RAIZ DESTE REPOSITORIO. Qualquer caminho
    relativo que o filho escrevesse caia sobre o proprio acervo —
    inclusive sobre `locks/`, de onde os guardas leem.
    """
    ambiente = ambiente_sanitizado(env)
    try:
        proc = subprocess.run(list(argv), env=ambiente, capture_output=True,
                              timeout=timeout, cwd=cwd)
    except subprocess.TimeoutExpired:
        return (RC_TIMEOUT, "", f"timeout de {timeout}s na invocacao")
    except (FileNotFoundError, OSError) as exc:
        # NAO propaga: o Execution Gateway espera uma RespostaProvedor, e
        # uma excecao aqui derrubaria a sessao inteira em vez de produzir
        # o attempt registrado que a evidencia exige.
        return (127, "", f"{type(exc).__name__}: executavel indisponivel")
    return (proc.returncode, decodificar(proc.stdout),
            decodificar(proc.stderr))


def classificar(rc: int, texto: str, mutacoes_medidas) -> tuple:
    """(falha, efeito_externo) a partir do que o CLI devolveu E do que o disco mostrou.

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

    `mutacoes_medidas` E A CORRECAO DO ACHADO A (P2.3), e o parametro e
    OBRIGATORIO por isso. Ate aqui esta funcao devolvia `efeito_externo =
    "nenhum"` para TODO `rc == 0`, e a razao escrita era *"porque a P2
    opera em modo read-only por envelope"*: o envelope declarava
    read-only, a classificacao repetia a declaracao, e o recibo gravava
    `"nenhum"` sem que nada tivesse olhado o disco. O registro confirmava
    a suposicao que o produziu — MAJOR #3 na forma literal.

    Agora quem decide e a lista de mutacoes que o chamador MEDIU (o
    manifesto SHA-256 do descartavel e das raizes vigiadas, antes e
    depois da chamada). Lista vazia continua produzindo `nenhum`, mas
    `nenhum` passou a ser MEDICAO em vez de eco do envelope; lista nao
    vazia produz `aplicado`, e o recibo diz quais caminhos.

    Obrigatorio, e nao opcional com default: um default deixaria o
    chamador esquecido devolvendo `nenhum` de novo — o defeito voltaria
    por omissao, calado, que e exatamente como ele existia.

    O QUE A MEDICAO NAO COBRE, e por isso `nao-aplicado` no degrau
    transitorio NAO virou medicao: ela ve DISCO, dentro das raizes
    vigiadas. Se a chamada teve efeito do outro lado da rede — uma
    escrita no servico do provedor —, nenhuma fotografia local a mostra.
    O `nao-aplicado` do transitorio segue sendo o que sempre foi, uma
    afirmacao sobre o lado remoto, e o `incerto` do timeout tambem: a
    medicao local nao pode contradizer nem confirmar o remoto, e por isso
    nao o sobrescreve.
    """
    if rc == RC_TIMEOUT:
        return ("indeterminado", "incerto")
    # Mutacao MEDIDA vence a classificacao textual: houve escrita, e
    # chamar isso de `nenhum` seria a mesma declaracao de antes com um
    # medidor ligado ao lado.
    medido = "aplicado" if mutacoes_medidas else None
    if rc == 0:
        return (None, medido or "nenhum")
    low = texto.lower()
    if quota_esgotada(low):
        return ("falha-quota", medido or "nenhum")
    if any(m in low for m in _MARCADORES_CLI_INDISPONIVEL):
        return ("falha-contrato", medido or "nenhum")
    if any(m in low for m in _MARCADORES_TRANSITORIOS):
        return ("falha-transitoria", medido or "nao-aplicado")
    return ("falha-contrato", medido or "nenhum")


class ProvedorAssinaturaReal:
    """Invoca o CLI de assinatura em modo nao-interativo.

    Interface identica a do `FakeProvider` — `invocar(entrada, pacote,
    idempotency_key) -> RespostaProvedor` —, de proposito: o
    `ExecutionGateway` ratificado nao muda uma linha para executar de
    verdade. Trocar simulado por real e trocar o objeto, nao a maquina.
    """

    def __init__(self, espec, sensor=None, timeout: int = TIMEOUT_PADRAO_S,
                 env=None, relogio=time.monotonic, vigia=None,
                 sessao_lock: str | None = None):
        self.espec = espec
        self.sensor = sensor or sensor_subprocess
        self.timeout = int(timeout)
        self.env = dict(env) if env is not None else None
        self.relogio = relogio
        self.sessao_lock = sessao_lock or caminhos.SESSAO_LOCK
        # `vigia` injetavel pela mesma razao do sensor: em teste ela olha
        # uma arvore de brinquedo, em operacao a arvore de verdade. `None`
        # NAO desliga a vigilancia — constroi a real. Desligar por omissao
        # seria repor o defeito: quem esquecesse de passar o objeto
        # voltaria a invocar sem ninguem olhando o disco.
        self.vigia = vigia
        self.chamadas = 0
        self.chaves_recebidas = []      # idempotency_keys propagadas (0.2.1-5)
        # Uma entrada por invocacao, na ordem em que ocorreram: o que foi
        # restringido, onde o filho correu e o que o disco mostrou. E daqui
        # que o recibo tira a medicao do efeito externo.
        self.medicoes = []

    def _vigilancia(self):
        return self.vigia or Vigilancia(caminhos.RAIZ, self.sessao_lock)

    def argv(self, prompt: str, descartavel: str) -> list:
        """argv nao-interativo: executavel + headless + RESTRICAO + prompt.

        `espec.headless` e o campo que a P1-A declarou e NUNCA usou —
        `codex exec`, `kimi -p`. A P2 e o primeiro uso dele, e passa a ser
        a razao de ele existir.

        `espec.restricao_headless` entra ENTRE o modo headless e o prompt
        (P2.3, achado A), com `MARCA_DESCARTAVEL` trocado pelo diretorio
        descartavel desta invocacao. A ordem nao e estetica: `codex exec`
        toma o prompt como argumento POSICIONAL, e uma flag depois dele
        seria lida como parte do prompt ou recusada.

        Provedor sem restricao declarada monta o argv de sempre — e o
        rotulo (`rotulo_restricao`) diz isso por extenso, em vez de deixar
        a ausencia passar por protecao.
        """
        restricao = [descartavel if arg == MARCA_DESCARTAVEL else arg
                     for arg in self.espec.restricao_headless]
        return argv_de(self.espec,
                       list(self.espec.headless) + restricao + [prompt])

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

        # Diretorio descartavel POR INVOCACAO: e o `--cd` do CLI e o `cwd`
        # do processo filho ao mesmo tempo. Dois elos herdavam o diretorio
        # do terminal ate a P2.3 (`capsula.py:111` e a chamada de
        # `subprocess.run` daqui), e caminho relativo escrito pelo filho
        # caia na raiz deste repositorio.
        descartavel = tempfile.mkdtemp(
            prefix=f"p2-{self.espec.provider_id}-")
        argv = self.argv(prompt, descartavel)

        # As DUAS fotografias de antes. O descartavel responde *o filho
        # escreveu no proprio espaco?*; a `Vigilancia` responde *escreveu
        # fora dele?* — e sao perguntas diferentes, com respostas
        # diferentes no recibo.
        antes = manifesto(descartavel)
        vigia = self._vigilancia()
        vigia.abrir()

        inicio = self.relogio()
        rc, out, err = self.sensor(argv, self.env, self.timeout,
                                   cwd=descartavel)
        latencia_ms = int(round((self.relogio() - inicio) * 1000))

        relatorio_vigilancia = vigia.fechar()
        no_descartavel = mutacoes(antes, manifesto(descartavel))
        fora = list(relatorio_vigilancia["mutacoes_fora_do_descartavel"])
        # Mutacao do renovador de lease NAO entra: ela tem escritor
        # esperado por construcao, e conta-la como efeito do provedor
        # faria toda corrida longa parecer escrita externa.
        medidas = [f"descartavel: {m}" for m in no_descartavel] + fora

        texto = (out or "") + "\n" + (err or "")
        falha, efeito = classificar(rc, texto, medidas)
        ok = falha is None

        self.medicoes.append({
            "provider_id": self.espec.provider_id,
            "restricao": rotulo_restricao(self.espec),
            # O prompt e a tarefa do usuario: fora do recibo publico.
            "argv_publico": ["<PROMPT>" if a == prompt else a for a in argv],
            "dir_descartavel": descartavel,
            "cwd_do_filho": descartavel,
            "medida": "manifesto SHA-256 do diretorio descartavel e das "
                      "raizes vigiadas, ANTES e DEPOIS da invocacao",
            "mutacoes_no_descartavel": no_descartavel,
            "mutacoes_fora_do_descartavel": fora,
            "mutacoes_atribuidas_ao_renovador":
                relatorio_vigilancia["mutacoes_atribuidas_ao_renovador"],
            "arquivos_no_manifesto_vigiado":
                relatorio_vigilancia["arquivos_no_manifesto"],
            "raizes_vigiadas": relatorio_vigilancia["raizes_vigiadas"],
            "nao_vigiado": relatorio_vigilancia["nao_vigiado"],
            "efeito_externo": efeito,
            "efeito_externo_origem": (
                "timeout: o efeito do lado REMOTO e incerto, e a "
                "fotografia local nao o decide (IR-2)"
                if rc == RC_TIMEOUT else
                "mutacao medida no disco" if medidas else
                "fotografia sem nenhuma mutacao — `nenhum` aqui e "
                "medicao, nao eco do envelope"),
        })

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
