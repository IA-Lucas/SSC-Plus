"""O executor real da P2, exercido — inclusive contra subprocesso de verdade.

Este e o primeiro modulo do laboratorio que invoca modelo. A tentacao
obvia era prova-lo so com sensor falso, e isso mediria o parser e nada
mais: `sensor_subprocess` — quem sanitiza o ambiente, quem impede shell,
quem aplica o teto de parede — ficaria inteiramente por exercer, afirmado
por docstring. E a familia do MAJOR #3 deste acervo.

O CAMINHO QUE A OPERACAO PERCORRE, sem gastar franquia: a classe
`SubprocessoDeVerdade` usa `sys.executable` como executavel do CLI e
`("-c",)` como modo headless. O argv fica `[python, "-c", <prompt>]`, e o
prompt e um programa Python. E subprocesso real, com env real, teto real
e captura real — so que o "modelo" e o interpretador que ja esta na
maquina. **Zero chamada de modelo, zero custo variavel, zero franquia.**

O vizinho recusado: `subprocess.run` mockado. Ele provaria que chamamos
`subprocess.run`, que e exatamente o que ja se le no fonte, e nao provaria
nem a sanitizacao, nem o `shell=False`, nem o timeout.

O QUE ESTES TESTES NAO COBREM, declarado:
- **nao exercitam codex nem kimi de verdade.** Que `codex exec <prompt>`
  aceite o prompt como argumento posicional, e que `kimi -p` o aceite
  como valor da flag, e leitura de especificacao — nao foi medido contra
  os CLIs. A primeira corrida real e que mede isso;
- **nao medem contagem de token**, porque o CLI nao reporta nenhuma. O
  campo sai `None`, e o que a EvidencePlane faz com essa ausencia esta
  registrado como divergencia na ordem, nao corrigido aqui;
- **nao cobrem divergencia de executor**: `executor_observado` e sempre
  `None`, entao o guarda 0.2.1-9 do Execution Gateway nao dispara para a
  P2. Limite declarado, medido por teste proprio, e nao propriedade;
- **nao cobrem prompt em stdin.** A P2 passa o prompt por argv; um CLI
  que exigisse stdin nao seria alcancado por este executor;
- a lista `_MARCADORES_TRANSITORIOS` e enumerada. Erro transitorio com
  texto fora dela cai em `falha-contrato` — fail-closed de proposito
  (retry contra falha determinista queima franquia), mas e teto conhecido.
"""

import dataclasses
import json
import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", "08_p2", os.path.join("06_p1a", "evidencias")):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import contencao  # noqa: E402
import provedor_assinatura as pa  # noqa: E402
from preflight.frota_real import espec_de  # noqa: E402
from ssc_p0 import contratos as ct  # noqa: E402
from ssc_p0.frota import (AdaptadorAssinatura,  # noqa: E402
                          PoliticaEconomicaViolada)
from ssc_p0.providers import RespostaProvedor  # noqa: E402


class SensorFalso:
    """Sensor injetavel que REGISTRA e nunca executa nada.

    Registra tambem o `cwd` recebido: desde a P2.3 ele faz parte do
    contrato do sensor, e um sensor falso que o ignorasse deixaria de
    poder falsear a afirmacao *"o filho corre no descartavel"*.
    """

    def __init__(self, rc=0, out="", err=""):
        self.resposta = (rc, out, err)
        self.chamadas = []

    def __call__(self, argv, env=None, timeout=None, cwd=None,
                 entrada_stdin=None):
        self.chamadas.append({"argv": list(argv), "env": env,
                              "timeout": timeout, "cwd": cwd,
                              "entrada_stdin": entrada_stdin})
        rc, out, err = self.resposta
        if rc == 0 and "kimi" in str(argv[0]).lower():
            out = json.dumps({"role": "assistant", "content": out})
        return rc, out, err


def vigia_estreita():
    """`Vigilancia` sobre uma arvore de brinquedo, e nao sobre o acervo.

    O executor constroi a vigilancia REAL quando ninguem a injeta — e ha
    teste proprio para esse default. Aqui ela e estreitada por um motivo
    de custo do TESTE: fotografar as duas raizes reais custa ~1,3 s por
    invocacao, e esta suite invoca dezenas de vezes.
    """
    return contencao.Vigilancia(tempfile.mkdtemp(prefix="p2-vigia-teste-"),
                                "sessao-de-teste", alvos=())


def provedor(espec, **kw):
    """`ProvedorAssinaturaReal` com a vigilancia estreitada por default."""
    kw.setdefault("vigia", vigia_estreita())
    modelos_teste = {
        "codex": "gpt-5.6-sol", "kimi": "kimi-code/k3",
        "claude": "claude-fable-5[1m]",
        "google": "gemini-3.6-flash-high",
    }
    kw.setdefault("model_id", ("modelo-teste" if espec.executavel ==
                                sys.executable else
                                modelos_teste[espec.provider_id]))
    return pa.ProvedorAssinaturaReal(espec, **kw)


def espec_codex():
    return espec_de("codex")


def espec_python(headless=("-c", "import sys;exec(sys.argv[-1])")):
    """O interpretador local no lugar do CLI — e SEM a restricao do codex.

    `restricao_headless=()` nao e conveniencia: as flags declaradas para o
    codex sao do codex. Herda-las aqui faria o argv virar
    `[python, "-c", <ponte>, "--model", <id>, <prompt>]`, e a ponte
    executa somente o ultimo argumento. Assim o caminho operacional tambem
    exercita o vinculo obrigatorio de modelo sem fingir que Python entende
    a flag de um provedor.
    teste passaria a ser outro. Provedor sem restricao declarada e
    exatamente o que esta espec representa.
    """
    return dataclasses.replace(espec_de("codex"),
                               executavel=sys.executable,
                               headless=headless, restricao_headless=())


def classificar(rc, texto, mutacoes=()):
    """`pa.classificar` com a medicao VAZIA — o caso 'nada mudou'.

    O terceiro parametro e obrigatorio na funcao de producao de proposito
    (P2.3): um default la deixaria um chamador esquecido devolvendo
    `nenhum` sem medir, que e o defeito corrigido. O default vive AQUI,
    no teste, onde a ausencia de mutacao e a hipotese sob exame.
    """
    return pa.classificar(rc, texto, mutacoes)


class ArgvNaoInterativo(unittest.TestCase):
    """O argv usa `headless` — o campo que a P1-A declarou e nunca usou."""

    def test_codex_usa_exec_e_o_prompt_e_posicional(self):
        # Desde a P2.3 a restricao entra ENTRE o modo headless e o prompt:
        # `codex exec` toma o prompt como posicional, e flag depois dele
        # seria lida como parte do prompt. O que este teste prende e a
        # MOLDURA — `exec` na frente, prompt no fim, um argumento so.
        sensor = SensorFalso()
        p = provedor(espec_codex(), sensor=sensor)
        p.invocar(b"some o dois numeros")
        argv = sensor.chamadas[0]["argv"]
        self.assertEqual(argv[1], "exec")
        self.assertEqual(argv[-1], "some o dois numeros")
        self.assertEqual(argv.count("some o dois numeros"), 1)

    def test_kimi_usa_p(self):
        sensor = SensorFalso()
        p = provedor(espec_de("kimi"), sensor=sensor)
        p.invocar(b"tarefa")
        self.assertEqual(sensor.chamadas[0]["argv"][1:],
                         ["-p", "tarefa", "-m", "kimi-code/k3",
                          "--output-format", "stream-json"])

    def test_quatro_clis_fixam_o_modelo_resolvido_no_argv(self):
        modelos = {"codex": "gpt-5.6-sol", "claude": "claude-fable-5[1m]",
                   "kimi": "kimi-code/k3",
                   "google": "gemini-3.6-flash-high"}
        for provider_id, modelo in modelos.items():
            with self.subTest(provider_id=provider_id):
                sensor = SensorFalso()
                p = provedor(espec_de(provider_id), sensor=sensor,
                             model_id=modelo)
                p.invocar(b"tarefa")
                argv = sensor.chamadas[0]["argv"]
                flag = espec_de(provider_id).flag_modelo
                indice = argv.index(flag[0])
                self.assertEqual(argv[indice + len(flag)], modelo)

    def test_google_coloca_prompt_logo_apos_p_e_flags_depois(self):
        sensor = SensorFalso(out=json.dumps({
            "status": "SUCCESS", "num_turns": 1, "response": "ok",
            "usage": {"total_tokens": 1}}))
        p = provedor(espec_de("google"), sensor=sensor,
                     model_id="gemini-3.1-pro-high")
        r = p.invocar(b"tarefa")
        argv = sensor.chamadas[0]["argv"]
        self.assertEqual(argv[1:3], ["-p", "tarefa"])
        self.assertGreater(argv.index("--model"), argv.index("tarefa"))
        self.assertTrue(r.ok)
        self.assertEqual(r.saida, b"ok")
        self.assertEqual(r.custo["tokens_reportados"], 1)

    def test_kimi_coloca_prompt_logo_apos_p_antes_do_modelo(self):
        sensor = SensorFalso()
        p = provedor(espec_de("kimi"), sensor=sensor,
                     model_id="kimi-code/k3")
        p.invocar(b"tarefa")
        argv = sensor.chamadas[0]["argv"]
        indice = argv.index("-p")
        self.assertEqual(argv[indice + 1], "tarefa")
        self.assertGreater(argv.index("-m"), indice + 1)
        self.assertEqual(argv[-2:], ["--output-format", "stream-json"])

    def test_sem_modelo_observado_recusa_antes_do_sensor(self):
        sensor = SensorFalso()
        p = provedor(espec_codex(), sensor=sensor, model_id=None)
        with self.assertRaises(ValueError):
            p.invocar(b"tarefa")
        self.assertEqual(sensor.chamadas, [])

    def test_til_do_executavel_e_expandido_e_o_home_nao_vaza_da_espec(self):
        # A regra e a MESMA de `argv_de` (P1-A, F-1): expande so o `~` do
        # executavel, no momento da montagem. A especificacao permanece
        # sem diretorio de usuario dentro.
        sensor = SensorFalso()
        p = provedor(espec_de("kimi"), sensor=sensor)
        p.invocar(b"x")
        exe = sensor.chamadas[0]["argv"][0]
        self.assertNotIn("~", exe)
        self.assertTrue(os.path.isabs(exe))
        self.assertIn("~", espec_de("kimi").executavel)

    def test_prompt_com_metacaractere_continua_UM_argumento(self):
        # `shell=False` e a forma de lista sao o que impede um prompt de
        # virar comando. O prompt de uma tarefa real contem qualquer coisa.
        sensor = SensorFalso()
        p = provedor(espec_codex(), sensor=sensor)
        veneno = 'a | rm -rf / & echo "x" ; $(whoami)'
        p.invocar(veneno.encode("utf-8"))
        argv = sensor.chamadas[0]["argv"]
        self.assertEqual(argv.count(veneno), 1,
                         "o prompt envenenado deixou de ser UM argumento")
        self.assertEqual(argv[-1], veneno)


class ClassificacaoDoResultado(unittest.TestCase):
    """A precedencia, cada degrau pelo seu proprio motivo."""

    def test_sucesso(self):
        self.assertEqual(classificar(0, "tudo certo"), (None, "nenhum"))

    def test_timeout_vence_tudo_e_o_efeito_e_incerto(self):
        # Enviou e nao houve resposta: IR-2 proibe retry automatico, e o
        # que autoriza essa proibicao e o efeito INCERTO.
        falha, efeito = classificar(pa.RC_TIMEOUT,
                                       "0 requests remaining\n429")
        self.assertEqual((falha, efeito), ("indeterminado", "incerto"))

    def test_quota_vence_transitorio_na_MESMA_saida(self):
        # O caso que motiva a precedencia: um 429 ao lado de franquia
        # zerada e esgotamento, nao congestionamento. Classificar como
        # transitorio faria o retry queimar a franquia que ja acabou.
        #
        # A primeira medicao desta ordem encontrou a precedencia presa por
        # UM caso so. Um caso prova que AQUELE texto classifica certo,
        # jamais que a regra vale — a mesma licao que a P1-A.3.9 registrou
        # sobre listas ("remover o ultimo item e ficar verde" nao prova que
        # a lista esta solta). Cada combinacao abaixo tem marcador
        # transitorio E sinal de esgotamento no MESMO texto.
        combinacoes = (
            "HTTP 429\n0 requests remaining",
            "rate limit exceeded; usage limit reached",
            "503 service unavailable\nno calls left",
            "connection reset\nquota: 0",
            "too many requests (429)\n0/100 requests remaining",
            "try again later\n0.0 tokens available",
        )
        for texto in combinacoes:
            with self.subTest(texto=texto):
                falha, efeito = classificar(1, texto)
                self.assertEqual(
                    falha, "falha-quota",
                    "esgotamento lido como congestionamento: o retry "
                    "queimaria a franquia que ja acabou")
                self.assertEqual(efeito, "nenhum")

    def test_quota_usa_o_detector_do_preflight_e_nao_uma_segunda_lista(self):
        # Grafias de zero que o detector numerico do preflight cobre sem
        # enumeracao — se a P2 tivesse copiado a lista, estas escapariam.
        for texto in ("0.0 tokens available", "00 requests left",
                      "no calls left", "usage limit reached"):
            with self.subTest(texto=texto):
                self.assertEqual(classificar(1, texto)[0], "falha-quota")

    def test_cli_ausente_e_contrato_para_o_fallback_trocar_de_assinatura(self):
        falha, _ = classificar(127, "FileNotFoundError: executavel "
                                       "indisponivel")
        self.assertEqual(falha, "falha-contrato")

    def test_transitorio_por_marcador(self):
        for texto in ("HTTP 503 service unavailable", "rate limit exceeded",
                      "connection reset by peer"):
            with self.subTest(texto=texto):
                falha, efeito = classificar(1, texto)
                self.assertEqual(falha, "falha-transitoria")
                self.assertEqual(efeito, "nao-aplicado")

    def test_erro_desconhecido_e_contrato_nunca_transitorio(self):
        # Fail-closed. Erro que ninguem reconheceu virando transitorio por
        # otimismo geraria retry contra falha determinista — tres vezes o
        # mesmo erro, tres vezes a mesma franquia.
        falha, _ = classificar(2, "erro que ninguem enumerou")
        self.assertEqual(falha, "falha-contrato")

    def test_google_recusa_sucesso_sem_json_ou_sem_turno_produtivo(self):
        for out in ("texto livre", json.dumps({
                "status": "SUCCESS", "num_turns": 0, "response": "ok",
                "usage": {"total_tokens": 0}})):
            with self.subTest(out=out[:20]):
                rc, saida, err, telemetria = pa.normalizar_saida(
                    "google", 0, out, "")
                self.assertEqual(rc, pa.RC_SAIDA_INVALIDA)
                self.assertEqual(saida, "")
                self.assertIn("invalida", err)
                self.assertIsNone(telemetria)


class ContratoSemantico(unittest.TestCase):
    def test_sucesso_exige_marcador_e_resposta_nao_vazia(self):
        self.assertEqual(
            pa.normalizar_resultado_semantico(
                f"{pa.STATUS_SUCESSO}\n{pa.MARCADOR_RESPOSTA}\nfeito"),
            (True, "feito", ""))
        for texto in ("feito sem marcador",
                      f"{pa.STATUS_SUCESSO}\n{pa.MARCADOR_RESPOSTA}"):
            with self.subTest(texto=texto):
                ok, _, motivo = pa.normalizar_resultado_semantico(texto)
                self.assertFalse(ok)
                self.assertTrue(motivo)

    def test_bloqueio_expresso_nunca_vira_sucesso(self):
        ok, resposta, motivo = pa.normalizar_resultado_semantico(
            f"{pa.STATUS_BLOQUEADO}\n{pa.MARCADOR_MOTIVO} workspace inacessivel")
        self.assertFalse(ok)
        self.assertEqual(resposta, "")
        self.assertIn("workspace inacessivel", motivo)

    def test_executor_com_contrato_converte_recusa_em_falha(self):
        sensor = SensorFalso(out=(f"{pa.STATUS_BLOQUEADO}\n"
                                  f"{pa.MARCADOR_MOTIVO} sem acesso"))
        p = provedor(espec_codex(), sensor=sensor,
                     contrato_semantico=True)
        r = p.invocar(b"tarefa")
        self.assertFalse(r.ok)
        self.assertEqual(r.falha, "falha-contrato")
        self.assertIn(b"tarefa nao concluida", r.saida)

    def test_kimi_recompoe_fragmentos_assistant_do_jsonl(self):
        bruto = "\n".join([
            json.dumps({"role": "assistant", "content": "vou ler"}),
            json.dumps({"role": "tool", "content": "arquivo"}),
            json.dumps({"role": "assistant", "content": "resposta final"}),
        ])
        rc, out, err, telemetria = pa.normalizar_saida(
            "kimi", 0, bruto, "")
        self.assertEqual((rc, out, err),
                         (0, "vou ler\nresposta final", ""))
        self.assertEqual(telemetria["mensagens_assistente"], 2)

    def test_kimi_preserva_contrato_repartido_em_eventos(self):
        bruto = "\n".join([
            json.dumps({"role": "assistant", "content": pa.STATUS_SUCESSO}),
            json.dumps({"role": "assistant", "content": pa.MARCADOR_RESPOSTA}),
            json.dumps({"role": "assistant", "content": "resultado"}),
        ])
        rc, out, err, _ = pa.normalizar_saida("kimi", 0, bruto, "")
        self.assertEqual((rc, err), (0, ""))
        self.assertEqual(pa.normalizar_resultado_semantico(out),
                         (True, "resultado", ""))

    def test_kimi_recusa_texto_livre_quando_stream_json_foi_exigido(self):
        rc, out, err, telemetria = pa.normalizar_saida(
            "kimi", 0, "texto sem estrutura", "")
        self.assertEqual(rc, pa.RC_SAIDA_INVALIDA)
        self.assertEqual(out, "")
        self.assertIn("Kimi", err)
        self.assertIsNone(telemetria)

    def test_prompt_grande_codex_vai_por_stdin_e_nao_pelo_argv(self):
        sensor = SensorFalso(out=(f"{pa.STATUS_SUCESSO}\n"
                                  f"{pa.MARCADOR_RESPOSTA}\nfeito"))
        p = provedor(espec_codex(), sensor=sensor,
                     contrato_semantico=True)
        p.invocar(("contexto-" + "x" * 100_000).encode())
        chamada = sensor.chamadas[0]
        self.assertGreater(len(chamada["entrada_stdin"]), 100_000)
        self.assertLess(max(map(len, chamada["argv"])), 1000,
                        "prompt grande voltou para a linha de comando")
        self.assertEqual(p.medicoes[0]["transporte_prompt"], "stdin")

    def test_google_recebe_prompt_curto_e_contexto_em_arquivo_descartavel(self):
        observado = {}

        def sensor(argv, env=None, timeout=None, cwd=None,
                   entrada_stdin=None):
            observado["argv"] = list(argv)
            observado["stdin"] = entrada_stdin
            with open(os.path.join(cwd, "contexto-ssc.txt"),
                      encoding="utf-8") as arquivo:
                observado["contexto"] = arquivo.read()
            semantico = (f"{pa.STATUS_SUCESSO}\n"
                         f"{pa.MARCADOR_RESPOSTA}\nfeito")
            return 0, json.dumps({
                "status": "SUCCESS", "num_turns": 1,
                "response": semantico,
                "usage": {"total_tokens": 1}}), ""

        p = provedor(espec_de("google"), sensor=sensor,
                     contrato_semantico=True)
        p.invocar(("contexto-" + "y" * 100_000).encode())
        self.assertIsNone(observado["stdin"])
        self.assertIn("y" * 1000, observado["contexto"])
        self.assertLess(max(map(len, observado["argv"])), 1000)
        self.assertEqual(p.medicoes[0]["transporte_prompt"],
                         "arquivo-no-descartavel")

    def test_google_workspace_cobre_o_descartavel_com_add_dir(self):
        """O `--add-dir` do argv aponta para o MESMO descartavel do arquivo.

        Medido em 2026-08-12: sem o descartavel no workspace, a leitura
        de `contexto-ssc.txt` cai na permissao `command`, que o headless
        auto-nega, e o turno termina `SUCCESS` com `response` vazia — o
        julgamento vazio dos recibos `fluxo-20260812T0111*/0119*`. O que
        este teste NAO cobre, declarado: o que o CLI real faz com a flag
        e propriedade dele; a leitura de fato foi medida por sonda real
        (registro da correcao), nao por esta suite, que nao chama modelo.
        """
        observado = {}

        def sensor(argv, env=None, timeout=None, cwd=None,
                   entrada_stdin=None):
            observado["argv"] = list(argv)
            observado["cwd"] = cwd
            observado["contexto_existe"] = os.path.isfile(
                os.path.join(cwd, "contexto-ssc.txt"))
            semantico = (f"{pa.STATUS_SUCESSO}\n"
                         f"{pa.MARCADOR_RESPOSTA}\nfeito")
            return 0, json.dumps({
                "status": "SUCCESS", "num_turns": 1,
                "response": semantico,
                "usage": {"total_tokens": 1}}), ""

        p = provedor(espec_de("google"), sensor=sensor,
                     contrato_semantico=True)
        p.invocar(b"tarefa de julgamento")
        argv = observado["argv"]
        self.assertIn("--add-dir", argv,
                      "o descartavel ficou FORA do workspace do agy")
        valor = argv[argv.index("--add-dir") + 1]
        self.assertEqual(valor, observado["cwd"],
                         "--add-dir nao aponta para o descartavel da "
                         "invocacao")
        self.assertTrue(observado["contexto_existe"],
                        "contexto-ssc.txt nao estava no descartavel no "
                        "instante da chamada")
        self.assertNotIn("<DESCARTAVEL>", argv,
                         "marcador nao foi trocado pelo diretorio real")


# O texto EXATO que o `kimi` devolveu na primeira corrida real da P2
# (2026-08-03), com a franquia da assinatura de fato acabada. Copiado da
# evidencia, nao parafraseado: parafrasear seria escrever o caso que se
# quer pegar em vez do caso que ocorreu.
SAIDA_REAL_KIMI_SEM_QUOTA = (
    "\nerror: failed to run prompt: provider.api_error: 403 You've reached "
    "your usage limit for this billing cycle. Your quota will be refreshed "
    "in the next cycle. To continue now, purchase extra usage or upgrade "
    "your plan: https://www.kimi.com/code/#pricing\n"
    "See log: C:/Users/<USUARIO>/.kimi-code/logs/kimi-code.log\n")


class QuotaRealDoKimi(unittest.TestCase):
    """O achado da primeira corrida real, preso pelo texto que a produziu.

    A lista de marcadores tinha "usage limit reached"; o CLI escreveu
    "reached your usage limit" — a MESMA frase na ordem inversa. O
    esgotamento saiu como `falha-contrato`, `registrar_quota_exhausted`
    nunca correu, e a entrada do kimi permaneceu `disponivel` na frota: a
    WorkUnit seguinte da mesma sessao gastaria outra tentativa nele.
    """

    def test_a_saida_real_e_classificada_como_falha_quota(self):
        falha, efeito = classificar(1, SAIDA_REAL_KIMI_SEM_QUOTA)
        self.assertEqual(falha, "falha-quota",
                         "esgotamento real lido como falha de contrato: a "
                         "frota nao marca a quota e tenta de novo depois")
        self.assertEqual(efeito, "nenhum")

    def test_o_detector_canonico_do_preflight_tambem_a_reconhece(self):
        # A correcao foi feita no detector CANONICO, nao numa lista
        # paralela da P2 — entao o preflight passa a enxergar o mesmo
        # esgotamento, e nao so o executor.
        from preflight.adaptadores import quota_esgotada
        self.assertTrue(quota_esgotada(SAIDA_REAL_KIMI_SEM_QUOTA))

    def test_as_quatro_formas_da_familia(self):
        # Cada uma vinda de um pedaco da saida real, generalizada o
        # minimo: verbo-primeiro, promessa de renovacao e convite a pagar.
        for texto in ("You've reached your usage limit for this cycle",
                      "you have reached the monthly limit",
                      "Your quota will be refreshed in the next cycle",
                      "purchase extra usage or upgrade your plan",
                      "buy more credits to continue"):
            with self.subTest(texto=texto):
                self.assertEqual(classificar(1, texto)[0], "falha-quota")

    def test_o_convite_a_pagar_nao_vira_pagamento(self):
        # O CLI oferece "purchase extra usage" — o caminho que
        # `extra_usage = DENY` e `auto_topup = DENY` PROIBEM. Reconhecer o
        # convite serve para TROCAR DE ASSINATURA, nunca para aceita-lo:
        # o efeito e `nenhum` e a falha e tipada, o que leva ao fallback.
        falha, efeito = classificar(1, SAIDA_REAL_KIMI_SEM_QUOTA)
        self.assertEqual((falha, efeito), ("falha-quota", "nenhum"))

    def test_texto_com_limite_disponivel_nao_vira_esgotamento(self):
        # Contraprova: os padroes novos nao podem transformar qualquer
        # mencao a "limit" em franquia acabada, senao a frota trocaria de
        # assinatura sem motivo.
        for texto in ("rate limit: 1000 requests remaining",
                      "within limit", "usage limit: 500 left"):
            with self.subTest(texto=texto):
                self.assertNotEqual(classificar(1, texto)[0],
                                    "falha-quota")


class DecodificacaoDaSaida(unittest.TestCase):
    """Acento perdido nao volta: o texto corrompido vira o artefato final.

    Na primeira corrida real a resposta do codex chegou como "propriedade
    s� confirma" — cada acento trocado por U+FFFD, gravado no CAS, na
    cadeia de hashes e no artefato da WorkUnit.
    """

    def test_utf8_e_lido_como_utf8(self):
        self.assertEqual(pa.decodificar("função anotação".encode("utf-8")),
                         "função anotação")

    def test_cp1252_nao_vira_caractere_de_substituicao(self):
        # O caso exato do achado: o CLI escreve na page de codigo do
        # Windows, e forcar utf-8 destroi todo acento.
        bruto = "propriedade só confirma".encode("cp1252")
        lido = pa.decodificar(bruto)
        self.assertEqual(lido, "propriedade só confirma")
        self.assertNotIn("\ufffd", lido)

    def test_vazio_e_vazio(self):
        self.assertEqual(pa.decodificar(b""), "")

    def test_bytes_invalidos_em_toda_codificacao_nao_levantam(self):
        # Ultimo recurso: aceita perder caractere, mas so depois de ter
        # tentado — e nunca levanta, porque uma excecao aqui derrubaria a
        # sessao em vez de registrar o attempt.
        lido = pa.decodificar(b"\xf0\x28\x8c\x28 texto")
        self.assertIn("texto", lido)

    def test_o_sensor_real_devolve_acento_intacto(self):
        # Exercicio de ponta a ponta pelo subprocesso de verdade: o
        # interpretador escreve bytes utf-8 e eles precisam voltar iguais.
        p = provedor(espec_python())
        r = p.invocar("import sys;"
                      "sys.stdout.buffer.write('função ção'.encode('utf-8'))"
                      .encode("utf-8"))
        self.assertTrue(r.ok, r.saida)
        self.assertEqual(r.saida.decode("utf-8"), "função ção")

    def test_o_sensor_real_devolve_acento_intacto_de_um_CLI_EM_CP1252(self):
        """O caso que OCORREU, e que o teste vizinho nao alcancava.

        MEDIDO na P2.1 (ordem 3). A reversao vermelha de `decodificar`
        derrubava 1 teste, mas trocar o PONTO DE CHAMADA — fazer
        `sensor_subprocess` decodificar com utf-8 fixo, como antes da
        correcao — derrubava ZERO. O guarda existia so na primitiva.

        A causa e que o teste acima escreve bytes UTF-8, e utf-8 fixo
        decodifica utf-8 sem erro nenhum: ele exercia o vizinho. O achado
        4.3 da P2.0 nasceu de um CLI escrevendo na PAGE DE CODIGO DO
        WINDOWS, e e essa a unica forma que separa os dois caminhos —
        cp1252 e justamente o que utf-8 estrito NAO consegue decodificar.

        E a licao N4 da P1-A.3.7, paga de novo: *primitiva corrigida nao
        cobre ponto de chamada*.
        """
        p = provedor(espec_python())
        r = p.invocar("import sys;"
                      "sys.stdout.buffer.write("
                      "'propriedade só confirma'.encode('cp1252'))"
                      .encode("utf-8"))
        self.assertTrue(r.ok, r.saida)
        lido = r.saida.decode("utf-8")
        self.assertEqual(lido, "propriedade só confirma")
        self.assertNotIn("�", lido,
                         "acento perdido no PONTO DE CHAMADA: o texto "
                         "corrompido vai para o CAS e para a cadeia de "
                         "hashes como se fosse a resposta")


class RespostaCompativelComAMaquinaDaP0(unittest.TestCase):
    """Trocar simulado por real e trocar o objeto, nao a maquina."""

    def test_resposta_e_uma_RespostaProvedor_com_todos_os_campos(self):
        sensor = SensorFalso(0, "resultado")
        r = provedor(espec_codex(), sensor=sensor).invocar(
            b"t", idempotency_key="idem-1")
        self.assertIsInstance(r, RespostaProvedor)
        self.assertTrue(r.ok)
        self.assertEqual(r.saida, b"resultado")
        self.assertIsNone(r.falha)
        self.assertEqual(r.idempotency_key, "idem-1")

    def test_em_falha_a_saida_carrega_stderr(self):
        # Licao F-2 da P1-A.2: o motivo costuma sair em stderr, e um
        # relatorio que so guardasse stdout registraria falha sem causa.
        sensor = SensorFalso(1, "", "motivo real da falha")
        r = provedor(espec_codex(), sensor=sensor).invocar(
            b"t")
        self.assertFalse(r.ok)
        self.assertIn(b"motivo real da falha", r.saida)

    def test_custo_e_medido_e_a_ausencia_de_token_e_None_nunca_zero(self):
        r = provedor(espec_codex(),
                                      sensor=SensorFalso(0, "ok")).invocar(b"t")
        self.assertEqual(r.custo["valor"], 0.0)
        self.assertEqual(r.custo["rotulo"], "medido-assinatura")
        self.assertNotEqual(r.custo["rotulo"], "simulado",
                            "a P2 nao pode rotular simulado o que ocorreu")
        self.assertIsNone(r.custo["tokens_reportados"])
        self.assertNotIn("tokens", r.custo,
                         "token que o CLI nao reportou nao vira numero")

    def test_latencia_e_medida_no_relogio_injetado(self):
        # Relogio injetavel: a medicao e determinista no teste e real na
        # operacao, sem dois caminhos de codigo.
        marcas = iter([10.0, 10.25])
        r = provedor(
            espec_codex(), sensor=SensorFalso(0, "ok"),
            relogio=lambda: next(marcas)).invocar(b"t")
        self.assertEqual(r.latencia_ms, 250)
        self.assertEqual(r.latencia_rotulo, "medido")

    def test_executor_observado_e_None_e_isso_e_limite_declarado(self):
        # O CLI nao ecoa qual modelo serviu a chamada. Afirmar o resolvido
        # aqui fabricaria a confirmacao que o guarda 0.2.1-9 usa para
        # detectar divergencia — o guarda passaria a se auto-confirmar.
        r = provedor(espec_codex(),
                                      sensor=SensorFalso(0, "ok")).invocar(b"t")
        self.assertIsNone(r.executor_observado)

    def test_idempotency_key_e_registrada_e_ecoada(self):
        p = provedor(espec_codex(), sensor=SensorFalso())
        p.invocar(b"t", idempotency_key="k1")
        p.invocar(b"t", idempotency_key=None)
        self.assertEqual(p.chaves_recebidas, ["k1", None])
        self.assertEqual(p.chamadas, 2)


class PortaoEconomicoAntesDoSubprocesso(unittest.TestCase):
    """Veto = o subprocesso nunca chega a existir."""

    def entrada(self, **kw):
        base = dict(provider_id="codex", model_id="gpt-5-codex",
                    capability_profile={"capacidades": ["implementacao"]},
                    auth_mode="subscription-oauth", billing_mode="subscription",
                    quota_state="disponivel", quota_reset=None,
                    automation_permission="allow",
                    terms_profile={"oauth_profile": "oauth:codex"},
                    variable_cost=0.0, papeis_preferidos=["autor"],
                    canal_oficial=True)
        base.update(kw)
        return ct.FleetEntry(**base)

    def test_payg_bloqueia_ANTES_de_qualquer_sonda(self):
        sensor = SensorFalso()
        real = provedor(espec_codex(), sensor=sensor)
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(self.entrada(auth_mode="payg-api"), real,
                                env={})
        self.assertEqual(sensor.chamadas, [],
                         "houve sonda apos veto economico: o bloqueio "
                         "precisa vir ANTES da invocacao")

    def test_custo_variavel_positivo_bloqueia_antes_da_invocacao(self):
        sensor = SensorFalso()
        real = provedor(espec_codex(), sensor=sensor)
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(self.entrada(variable_cost=0.01), real, env={})
        self.assertEqual(sensor.chamadas, [])

    def test_entrada_aprovada_delega_ao_executor_real(self):
        # O outro lado do portao: aprovado, a invocacao chega ao executor.
        sensor = SensorFalso(0, "saida real")
        real = provedor(espec_codex(), sensor=sensor)
        adaptador = AdaptadorAssinatura(self.entrada(), real, env={})
        r = adaptador.invocar(b"tarefa", None, idempotency_key="k")
        self.assertEqual(r.saida, b"saida real")
        self.assertEqual(len(sensor.chamadas), 1)


class SubprocessoDeVerdade(unittest.TestCase):
    """`sensor_subprocess` exercido de verdade — com o interpretador local.

    Nao ha modelo aqui: o "CLI" e `sys.executable` e o "prompt" e um
    programa Python. E o unico jeito de medir sanitizacao, ausencia de
    shell e teto de parede sem gastar franquia de assinatura.
    """

    def espec_python(self, headless=("-c", "import sys;exec(sys.argv[-1])")):
        return espec_python(headless)

    def test_env_payg_e_removido_do_processo_filho(self):
        # A chave existe no env oferecido e NAO pode chegar ao filho. Este
        # e o teste que so o subprocesso real pode dar: com sensor falso, a
        # sanitizacao nunca roda.
        env = {"PATH": os.environ.get("PATH", ""),
               "OPENAI_API_KEY": "valor-fabricado-de-teste",
               "ORCA_AGENT_HOOK_PORT": "9999",
               "ORCA_AGENT_HOOK_TOKEN": "token-fabricado-de-teste",
               "SSC_MARCA_BENIGNA": "presente"}
        p = provedor(self.espec_python(), env=env)
        r = p.invocar(b"import os;"
                      b"print('OPENAI_API_KEY' in os.environ,"
                      b"any(k.startswith('ORCA_') for k in os.environ),"
                      b"os.environ.get('SSC_MARCA_BENIGNA'))")
        self.assertTrue(r.ok, r.saida)
        self.assertIn(b"False False presente", r.saida,
                      "chave PAYG vazou para o subprocesso, ou a variavel "
                      "benigna foi removida junto")

    def test_saida_e_codigo_de_retorno_sao_capturados(self):
        p = provedor(self.espec_python())
        r = p.invocar(b"import sys;sys.stderr.write('erro');sys.exit(3)")
        self.assertFalse(r.ok)
        self.assertEqual(r.falha, "falha-contrato")
        self.assertIn(b"erro", r.saida)

    def test_stdin_grande_chega_ao_subprocesso_sem_entrar_no_argv(self):
        carga = b"z" * 100_000
        argv = [sys.executable, "-c",
                "import sys;d=sys.stdin.buffer.read();print(len(d),d[:1].decode())"]
        rc, out, err = pa.sensor_subprocess(argv, timeout=10,
                                            entrada_stdin=carga)
        self.assertEqual(rc, 0, err)
        self.assertIn("100000 z", out)
        self.assertTrue(all(len(a) < 1000 for a in argv))

    def test_metacaractere_nao_vira_comando_no_subprocesso_real(self):
        # Se houvesse shell, `;` separaria comandos. Aqui o prompt inteiro
        # e UM argumento, e o programa imprime a string literal.
        p = provedor(self.espec_python())
        r = p.invocar(b"print('antes'); print('depois & | $(x)')")
        self.assertTrue(r.ok, r.saida)
        self.assertIn(b"depois & | $(x)", r.saida)

    def test_timeout_real_vira_indeterminado_com_efeito_incerto(self):
        p = provedor(self.espec_python(), timeout=1)
        r = p.invocar(b"import time;time.sleep(30)")
        self.assertEqual(r.falha, "indeterminado")
        self.assertEqual(r.efeito_externo, "incerto")

    def test_executavel_inexistente_nao_derruba_a_sessao(self):
        # Excecao aqui derrubaria a sessao inteira em vez de produzir o
        # attempt registrado que a evidencia exige.
        espec = dataclasses.replace(
            espec_de("codex"), restricao_headless=(),
            executavel=os.path.join(_RAIZ, "nao-existe-este-cli"))
        r = provedor(espec).invocar(b"t")
        self.assertFalse(r.ok)
        self.assertEqual(r.falha, "falha-contrato")

    def test_captura_grande_e_drenada_com_teto_sem_ecoar_conteudo(self):
        codigo = ("import sys;sys.stdout.buffer.write(b'x' * "
                  f"{pa.MAX_CAPTURA_BYTES + 1})")
        rc, out, err = pa.sensor_subprocess(
            [sys.executable, "-c", codigo], timeout=10,
            cwd=tempfile.gettempdir())
        self.assertEqual(rc, pa.RC_SAIDA_EXCEDIDA)
        self.assertEqual(out, "")
        self.assertIn("excedeu o teto", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
