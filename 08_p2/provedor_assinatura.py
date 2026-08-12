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

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time

import caminhos  # (insere 05_p0/06_p1a/08_p2/evidencias no sys.path)

from contencao import LAR_DO_CLI, Vigilancia, manifesto, mutacoes
from preflight.adaptadores import argv_de, quota_esgotada
from preflight.frota_real import MARCA_DESCARTAVEL, rotulo_restricao
from processo_arvore import (decodificar_saida, encerrar_arvore,
                             opcoes_nova_arvore)
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
RC_SAIDA_EXCEDIDA = 125
RC_SAIDA_INVALIDA = 126
MAX_CAPTURA_BYTES = 1024 * 1024

STATUS_SUCESSO = "SSC_STATUS: SUCESSO"
STATUS_BLOQUEADO = "SSC_STATUS: BLOQUEADO"
MARCADOR_RESPOSTA = "SSC_RESPOSTA:"
MARCADOR_MOTIVO = "SSC_MOTIVO:"


def montar_prompt_semantico(prompt: str) -> str:
    """Acrescenta um contrato de conclusao que pode ser medido.

    Codigo de saida zero prova que o CLI respondeu; nao prova que a tarefa foi
    feita. O provedor precisa declarar SUCESSO ou BLOQUEADO em forma fechada.
    Ausencia/ambiguidade vira falha de contrato e habilita fallback.
    """
    return (
        "CONTRATO DE RESULTADO SSC+ (obrigatorio):\n"
        "- Se concluir a tarefa, responda com a primeira linha exata "
        f"`{STATUS_SUCESSO}`, depois `{MARCADOR_RESPOSTA}` e a resposta.\n"
        "- Se nao conseguir concluir por acesso, ferramenta, permissao, "
        "contexto ou qualquer bloqueio, responda com a primeira linha exata "
        f"`{STATUS_BLOQUEADO}`, depois `{MARCADOR_MOTIVO}` e o motivo.\n"
        "- Nunca declare SUCESSO quando apenas explicar por que nao executou.\n"
        "- Nao envolva os marcadores em bloco de codigo.\n\n"
        "PEDIDO:\n" + prompt
    )


def normalizar_resultado_semantico(texto: str) -> tuple[bool, str, str]:
    """(concluiu, resposta, motivo) para o contrato textual fechado."""
    linhas = (texto or "").replace("\r\n", "\n").split("\n")
    indices = [i for i, linha in enumerate(linhas)
               if linha.strip() in (STATUS_SUCESSO, STATUS_BLOQUEADO)]
    if len(indices) != 1:
        return False, "", "marcador de status ausente ou ambiguo"
    indice = indices[0]
    status = linhas[indice].strip()
    resto = linhas[indice + 1:]
    if status == STATUS_BLOQUEADO:
        if not resto or not resto[0].strip().startswith(MARCADOR_MOTIVO):
            return False, "", "bloqueio sem SSC_MOTIVO"
        primeiro = resto[0].strip()[len(MARCADOR_MOTIVO):].strip()
        motivo = "\n".join(([primeiro] if primeiro else []) + resto[1:]).strip()
        return False, "", motivo or "provedor declarou bloqueio sem detalhe"
    # Mesma regra do ramo de MOTIVO: o marcador pode vir sozinho na linha
    # ou seguido da resposta. O contrato do prompt ("depois `SSC_RESPOSTA:`
    # e a resposta") permite as duas leituras, e o kimi-code/k3 real
    # devolveu a inline em 2026-08-12; exigir so uma delas reprovava
    # resposta que cumpre o contrato como escrito.
    if not resto or not resto[0].strip().startswith(MARCADOR_RESPOSTA):
        return False, "", "sucesso sem SSC_RESPOSTA"
    primeiro = resto[0].strip()[len(MARCADOR_RESPOSTA):].strip()
    resposta = "\n".join(([primeiro] if primeiro else []) + resto[1:]).strip()
    if not resposta:
        return False, "", "sucesso com resposta vazia"
    return True, resposta, ""

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
    return decodificar_saida(bruto)


def sensor_subprocess(argv, env=None, timeout: int = TIMEOUT_PADRAO_S,
                      cwd: str | None = None,
                      entrada_stdin: bytes | None = None):
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
        proc = subprocess.Popen(list(argv), env=ambiente,
                                stdin=(subprocess.PIPE if entrada_stdin is not None
                                       else subprocess.DEVNULL),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=cwd,
                                **opcoes_nova_arvore())
    except (FileNotFoundError, OSError) as exc:
        # NAO propaga: o Execution Gateway espera uma RespostaProvedor, e
        # uma excecao aqui derrubaria a sessao inteira em vez de produzir
        # o attempt registrado que a evidencia exige.
        return (127, "", f"{type(exc).__name__}: executavel indisponivel")
    capturas = {"stdout": bytearray(), "stderr": bytearray()}
    excedeu = {"stdout": False, "stderr": False}

    def drenar(nome, fluxo):
        while True:
            bloco = fluxo.read(65536)
            if not bloco:
                break
            restante = MAX_CAPTURA_BYTES - len(capturas[nome])
            if restante > 0:
                capturas[nome].extend(bloco[:restante])
            if len(bloco) > restante:
                excedeu[nome] = True

    def alimentar_stdin():
        try:
            proc.stdin.write(entrada_stdin or b"")
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    threads = [threading.Thread(target=drenar, args=(nome, fluxo), daemon=True)
               for nome, fluxo in (("stdout", proc.stdout),
                                   ("stderr", proc.stderr))]
    if entrada_stdin is not None:
        threads.append(threading.Thread(target=alimentar_stdin, daemon=True))
    for thread in threads:
        thread.start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        encerrar_arvore(proc)
        for thread in threads:
            thread.join()
        proc.stdout.close()
        proc.stderr.close()
        return (RC_TIMEOUT, "", f"timeout de {timeout}s na invocacao")
    for thread in threads:
        thread.join()
    proc.stdout.close()
    proc.stderr.close()
    if any(excedeu.values()):
        return (RC_SAIDA_EXCEDIDA, "",
                f"saida do CLI excedeu o teto de {MAX_CAPTURA_BYTES} bytes")
    return (proc.returncode, decodificar(bytes(capturas["stdout"])),
            decodificar(bytes(capturas["stderr"])))


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

    `nenhum` E VALOR DE CONTRATO, NAO AFIRMACAO DE AUSENCIA (P1-A.5,
    ordem 3 — achado `P1A4-3`). `EFEITOS_EXTERNO` e o enum ratificado da
    P0 (`nenhum/aplicado/nao-aplicado/incerto`) e esta funcao nao o
    alarga: com a lista vazia ela devolve `nenhum`, que ali significa
    *sem efeito DENTRO DO ALCANCE MEDIDO*. Quem publica esse valor e o
    recibo, e e la — em `alcance_da_medicao` — que o alcance fica dito
    caminho por caminho, inclusive o lar do CLI, onde a escrita e
    CONHECIDA e nao vigiada. Ler `nenhum` como "nada foi escrito" era
    exatamente o que o revisor da P1-A.4 recusou.
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


def normalizar_saida(provider_id: str, rc: int, out: str, err: str):
    """Saida util + telemetria comprovada do CLI, fail-closed.

    O Antigravity e invocado com `--output-format json`; aceitar stdout
    livre significaria aceitar que a flag foi ignorada (o defeito medido
    quando o prompt estava na posicao errada). Em sucesso, exige um turno
    produtivo, status SUCCESS, resposta textual e contadores numericos.
    """
    if rc != 0:
        return rc, out, err, None
    if provider_id == "kimi":
        try:
            respostas = []
            for linha in out.splitlines():
                if not linha.strip():
                    continue
                dados = json.loads(linha)
                mensagem = dados.get("message") \
                    if isinstance(dados.get("message"), dict) else dados
                papel = mensagem.get("role") or dados.get("role") \
                    or dados.get("type")
                if papel not in ("assistant", "message.assistant"):
                    continue
                conteudo = mensagem.get("content")
                if isinstance(conteudo, str) and conteudo.strip():
                    respostas.append(conteudo)
                elif isinstance(conteudo, list):
                    textos = [p.get("text") for p in conteudo
                              if isinstance(p, dict)
                              and isinstance(p.get("text"), str)]
                    if textos:
                        respostas.append("\n".join(textos))
            if not respostas:
                raise ValueError("sem mensagem assistant")
            # `stream-json` pode repartir uma unica resposta logica em
            # varios eventos assistant. Reter apenas o ultimo amputava o
            # contrato quando SSC_STATUS e SSC_RESPOSTA vinham separados.
            return rc, "\n".join(respostas), err, {
                "mensagens_assistente": len(respostas),
                "formato": "stream-json"}
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
            return (RC_SAIDA_INVALIDA, "",
                    "saida estruturada invalida do Kimi", None)
    if provider_id != "google":
        return rc, out, err, None
    try:
        dados = json.loads(out)
        uso = dados.get("usage")
        resposta = dados.get("response")
        if dados.get("status") != "SUCCESS" \
                or not isinstance(dados.get("num_turns"), int) \
                or dados["num_turns"] < 1 \
                or not isinstance(resposta, str) or not resposta.strip() \
                or not isinstance(uso, dict) or not uso \
                or not all(isinstance(v, (int, float))
                           and not isinstance(v, bool) and v >= 0
                           for v in uso.values()):
            raise ValueError("schema de sucesso incompleto")
        telemetria = {"num_turns": dados["num_turns"],
                      "total_tokens": uso.get("total_tokens")}
        return rc, resposta, err, telemetria
    except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
        return (RC_SAIDA_INVALIDA, "",
                "saida estruturada invalida do Antigravity", None)


class ProvedorAssinaturaReal:
    """Invoca o CLI de assinatura em modo nao-interativo.

    Interface identica a do `FakeProvider` — `invocar(entrada, pacote,
    idempotency_key) -> RespostaProvedor` —, de proposito: o
    `ExecutionGateway` ratificado nao muda uma linha para executar de
    verdade. Trocar simulado por real e trocar o objeto, nao a maquina.
    """

    def __init__(self, espec, sensor=None, timeout: int = TIMEOUT_PADRAO_S,
                 env=None, relogio=time.monotonic, vigia=None,
                 sessao_lock: str | None = None,
                 raiz_descartaveis: str | None = None,
                 model_id: str | None = None,
                 contrato_semantico: bool = False):
        self.espec = espec
        self.model_id = model_id
        self.contrato_semantico = bool(contrato_semantico)
        self.sensor = sensor or sensor_subprocess
        self.timeout = int(timeout)
        self.env = dict(env) if env is not None else None
        self.relogio = relogio
        self.sessao_lock = sessao_lock or caminhos.SESSAO_LOCK
        self.raiz_descartaveis = raiz_descartaveis or os.path.join(
            caminhos.RAIZ, "locks", "descartaveis-p2")
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

    def _alcance(self, descartavel: str, relatorio: dict) -> dict:
        """O que esta fotografia MEDIU, e o que ela nao mediu — por nome.

        A CORRECAO DO `P1A4-3`. O recibo publicava `efeito_externo:
        "nenhum"` e, ao lado, a frase *"fotografia sem nenhuma mutacao —
        `nenhum` aqui e medicao"*. As duas coisas juntas leem como
        ausencia de efeito no disco, e nao e isso que foi medido: a
        fotografia cobre o descartavel e as raizes vigiadas, e o lar do
        proprio CLI fica de fora POR DECISAO — o codex grava sessao e log
        em `~/.codex/` durante a chamada, e `--ephemeral` nao impede
        isso. O revisor da P1-A.4 chamou pelo nome: afirmar ausencia
        sobre o que nao se vigia.

        Aqui nao se alarga a vigilancia — se alarga a DECLARACAO. Os dois
        campos saem do relatorio real da `Vigilancia`, nao de prosa
        fixa: `medido` e o que ela fotografou, `nao_medido` e o que ela
        declara nao alcancar, mais o lar do CLI nomeado.

        Provedor sem lar declarado NAO produz silencio: sai
        `<lar do CLI NAO DECLARADO para '<id>'>`, que e pior de ler e
        melhor de auditar — a ausencia da declaracao aparece no recibo em
        vez de virar um `nenhum` sem ressalva.
        """
        pid = self.espec.provider_id
        lar = LAR_DO_CLI.get(pid)
        lar_dito = (f"o lar do CLI ({lar}), onde a escrita e CONHECIDA e "
                    "nao vigiada" if lar else
                    f"<lar do CLI NAO DECLARADO para {pid!r}>")
        return {
            "medido": [f"diretorio descartavel desta invocacao "
                       f"({descartavel})"] + list(relatorio["raizes_vigiadas"]),
            "nao_medido": [relatorio["nao_vigiado"], lar_dito,
                           "o lado REMOTO do provedor: efeito no servico "
                           "nao aparece em fotografia local"],
            "lar_do_cli": lar_dito,
        }

    def argv(self, prompt: str | None, descartavel: str) -> list:
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
        flag_modelo = list(getattr(self.espec, "flag_modelo", ()) or ())
        if not flag_modelo or not isinstance(self.model_id, str) \
                or not self.model_id.strip():
            raise ValueError(
                f"modelo nao vinculavel para {self.espec.provider_id}: "
                "toda rota automatica exige flag e model_id observado")
        vinculo_modelo = flag_modelo + [self.model_id]
        formato_saida = list(getattr(
            self.espec, "formato_saida_headless", ()) or ())
        restricao = [descartavel if arg == MARCA_DESCARTAVEL else arg
                     for arg in self.espec.restricao_headless]
        if prompt is None:
            comando = (list(self.espec.headless) + vinculo_modelo
                       + restricao + formato_saida)
        elif getattr(self.espec, "prompt_antes_das_flags", False):
            comando = (list(self.espec.headless) + [prompt]
                       + vinculo_modelo + restricao + formato_saida)
        else:
            comando = (list(self.espec.headless) + vinculo_modelo
                       + restricao + formato_saida + [prompt])
        return argv_de(self.espec, comando)

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
        prompt_original = (entrada or b"").decode("utf-8", errors="replace")
        prompt_completo = (montar_prompt_semantico(prompt_original)
                           if self.contrato_semantico else prompt_original)

        # Diretorio descartavel POR INVOCACAO: e o `--cd` do CLI e o `cwd`
        # do processo filho ao mesmo tempo. Dois elos herdavam o diretorio
        # do terminal ate a P2.3 (`capsula.py:111` e a chamada de
        # `subprocess.run` daqui), e caminho relativo escrito pelo filho
        # caia na raiz deste repositorio.
        os.makedirs(self.raiz_descartaveis, exist_ok=True)
        descartavel = tempfile.mkdtemp(
            prefix=f"p2-{self.espec.provider_id}-",
            dir=self.raiz_descartaveis)
        entrada_stdin = None
        arquivo_contexto = None
        if self.contrato_semantico:
            arquivo_contexto = os.path.join(descartavel, "contexto-ssc.txt")
            with open(arquivo_contexto, "x", encoding="utf-8", newline="\n") as f:
                f.write(prompt_completo)
                f.flush()
                os.fsync(f.fileno())
            if getattr(self.espec, "prompt_via_stdin", False):
                prompt_argv = None
                entrada_stdin = prompt_completo.encode("utf-8")
                transporte_prompt = "stdin"
            else:
                prompt_argv = (
                    "Leia integralmente o arquivo contexto-ssc.txt no "
                    "diretorio atual e execute o pedido e o contrato nele. "
                    "Nao procure contexto fora desse arquivo.")
                transporte_prompt = "arquivo-no-descartavel"
        else:
            prompt_argv = prompt_completo
            transporte_prompt = "argumento"
        argv = self.argv(prompt_argv, descartavel)

        # As DUAS fotografias de antes. O descartavel responde *o filho
        # escreveu no proprio espaco?*; a `Vigilancia` responde *escreveu
        # fora dele?* — e sao perguntas diferentes, com respostas
        # diferentes no recibo.
        antes = manifesto(descartavel)
        vigia = self._vigilancia()
        vigia.abrir()

        inicio = self.relogio()
        try:
            rc, out, err = self.sensor(argv, self.env, self.timeout,
                                       cwd=descartavel,
                                       entrada_stdin=entrada_stdin)
        except BaseException:
            # Sensores injetados podem levantar; o sensor real converte as
            # falhas esperadas em resultado. Em ambos os casos, nenhuma
            # excecao pode deixar vigilancia/descartavel abertos.
            try:
                vigia.fechar()
            finally:
                shutil.rmtree(descartavel, ignore_errors=True)
            raise
        latencia_ms = int(round((self.relogio() - inicio) * 1000))
        rc, out, err, telemetria = normalizar_saida(
            self.espec.provider_id, rc, out, err)
        if rc == 0 and self.contrato_semantico:
            concluiu, resposta_util, motivo = normalizar_resultado_semantico(out)
            if concluiu:
                out = resposta_util
            else:
                rc = RC_SAIDA_INVALIDA
                out = ""
                err = "tarefa nao concluida: " + motivo

        relatorio_vigilancia = vigia.fechar()
        no_descartavel = mutacoes(antes, manifesto(descartavel))
        fora = list(relatorio_vigilancia["mutacoes_fora_do_descartavel"])
        # Mutacao do renovador de lease NAO entra: ela tem escritor
        # esperado por construcao, e conta-la como efeito do provedor
        # faria toda corrida longa parecer escrita externa.
        medidas = [f"descartavel: {m}" for m in no_descartavel] + fora

        # O Kimi nao oferece sandbox de filesystem equivalente ao Codex.
        # Por isso sua resposta NUNCA e aceita quando a vigilancia observa
        # escrita fora do descartavel. Antes, a mutacao aparecia no recibo
        # como `aplicado`, mas rc=0 ainda virava sucesso e podia alimentar a
        # proxima etapa. Detectar sem bloquear nao e isolamento.
        isolamento_kimi_violado = (
            self.espec.provider_id == "kimi" and bool(fora))
        if isolamento_kimi_violado and rc == 0:
            rc = RC_SAIDA_INVALIDA
            out = ""
            err = ("isolamento Kimi violado: mutacao medida fora do "
                   "diretorio descartavel")

        texto = (out or "") + "\n" + (err or "")
        falha, efeito = classificar(rc, texto, medidas)
        ok = falha is None
        alcance = self._alcance(descartavel, relatorio_vigilancia)

        self.medicoes.append({
            "provider_id": self.espec.provider_id,
            "modelo_fixado_no_argv": self.model_id,
            "telemetria_cli": telemetria,
            "transporte_prompt": transporte_prompt,
            "prompt_bytes": len(prompt_completo.encode("utf-8")),
            "contexto_no_descartavel": bool(arquivo_contexto),
            "restricao": rotulo_restricao(self.espec),
            # O prompt e a tarefa do usuario: fora do recibo publico.
            "argv_publico": (["<PROMPT>" if a == prompt_argv else a
                              for a in argv]
                             + (["<PROMPT>"] if prompt_argv is None else [])),
            "dir_descartavel": descartavel,
            "cwd_do_filho": descartavel,
            "descartavel_existia_durante_invocacao": True,
            "medida": "manifesto SHA-256 do diretorio descartavel e das "
                      "raizes vigiadas, ANTES e DEPOIS da invocacao",
            "mutacoes_no_descartavel": no_descartavel,
            "mutacoes_fora_do_descartavel": fora,
            "isolamento_kimi_fail_closed": {
                "aplicavel": self.espec.provider_id == "kimi",
                "violado": isolamento_kimi_violado,
                "resposta_aceita": not isolamento_kimi_violado,
            },
            "mutacoes_atribuidas_ao_renovador":
                relatorio_vigilancia["mutacoes_atribuidas_ao_renovador"],
            "arquivos_no_manifesto_vigiado":
                relatorio_vigilancia["arquivos_no_manifesto"],
            "raizes_vigiadas": relatorio_vigilancia["raizes_vigiadas"],
            "nao_vigiado": relatorio_vigilancia["nao_vigiado"],
            "efeito_externo": efeito,
            "alcance_da_medicao": alcance,
            "efeito_externo_origem": (
                "timeout: o efeito do lado REMOTO e incerto, e a "
                "fotografia local nao o decide (IR-2)"
                if rc == RC_TIMEOUT else
                "mutacao medida no disco" if medidas else
                "fotografia sem nenhuma mutacao DENTRO DO ALCANCE "
                "MEDIDO (ver `alcance_da_medicao`) — `nenhum` aqui e "
                "medicao, nao eco do envelope. Fora do alcance nada foi "
                f"medido, inclusive {alcance['lar_do_cli']}: `nenhum` e "
                "o valor de contrato para 'sem efeito medido', jamais "
                "afirmacao de que nada foi escrito"),
        })

        resposta = RespostaProvedor(
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
                   "tokens_reportados": ((telemetria or {}).get(
                       "total_tokens"))},
            latencia_ms=latencia_ms,
            latencia_rotulo="medido",
            retry_after_ms=None,
            idempotency_key=idempotency_key,
        )
        shutil.rmtree(descartavel, ignore_errors=True)
        self.medicoes[-1]["descartavel_removido_apos_medicao"] = (
            not os.path.exists(descartavel))
        return resposta
