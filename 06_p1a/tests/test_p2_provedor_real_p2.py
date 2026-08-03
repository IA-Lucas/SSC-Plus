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
import os
import sys
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", "08_p2"):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import provedor_assinatura as pa  # noqa: E402
from preflight.frota_real import espec_de  # noqa: E402
from ssc_p0 import contratos as ct  # noqa: E402
from ssc_p0.frota import (AdaptadorAssinatura,  # noqa: E402
                          PoliticaEconomicaViolada)
from ssc_p0.providers import RespostaProvedor  # noqa: E402


class SensorFalso:
    """Sensor injetavel que REGISTRA e nunca executa nada."""

    def __init__(self, rc=0, out="", err=""):
        self.resposta = (rc, out, err)
        self.chamadas = []

    def __call__(self, argv, env=None, timeout=None):
        self.chamadas.append({"argv": list(argv), "env": env,
                              "timeout": timeout})
        return self.resposta


def espec_codex():
    return espec_de("codex")


class ArgvNaoInterativo(unittest.TestCase):
    """O argv usa `headless` — o campo que a P1-A declarou e nunca usou."""

    def test_codex_usa_exec_e_o_prompt_e_posicional(self):
        sensor = SensorFalso()
        p = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor)
        p.invocar(b"some o dois numeros")
        argv = sensor.chamadas[0]["argv"]
        self.assertEqual(argv[1:], ["exec", "some o dois numeros"])

    def test_kimi_usa_p(self):
        sensor = SensorFalso()
        p = pa.ProvedorAssinaturaReal(espec_de("kimi"), sensor=sensor)
        p.invocar(b"tarefa")
        self.assertEqual(sensor.chamadas[0]["argv"][1:], ["-p", "tarefa"])

    def test_til_do_executavel_e_expandido_e_o_home_nao_vaza_da_espec(self):
        # A regra e a MESMA de `argv_de` (P1-A, F-1): expande so o `~` do
        # executavel, no momento da montagem. A especificacao permanece
        # sem diretorio de usuario dentro.
        sensor = SensorFalso()
        p = pa.ProvedorAssinaturaReal(espec_de("kimi"), sensor=sensor)
        p.invocar(b"x")
        exe = sensor.chamadas[0]["argv"][0]
        self.assertNotIn("~", exe)
        self.assertTrue(os.path.isabs(exe))
        self.assertIn("~", espec_de("kimi").executavel)

    def test_prompt_com_metacaractere_continua_UM_argumento(self):
        # `shell=False` e a forma de lista sao o que impede um prompt de
        # virar comando. O prompt de uma tarefa real contem qualquer coisa.
        sensor = SensorFalso()
        p = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor)
        veneno = 'a | rm -rf / & echo "x" ; $(whoami)'
        p.invocar(veneno.encode("utf-8"))
        argv = sensor.chamadas[0]["argv"]
        self.assertEqual(len(argv), 3)
        self.assertEqual(argv[2], veneno)


class ClassificacaoDoResultado(unittest.TestCase):
    """A precedencia, cada degrau pelo seu proprio motivo."""

    def test_sucesso(self):
        self.assertEqual(pa.classificar(0, "tudo certo"), (None, "nenhum"))

    def test_timeout_vence_tudo_e_o_efeito_e_incerto(self):
        # Enviou e nao houve resposta: IR-2 proibe retry automatico, e o
        # que autoriza essa proibicao e o efeito INCERTO.
        falha, efeito = pa.classificar(pa.RC_TIMEOUT,
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
                falha, efeito = pa.classificar(1, texto)
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
                self.assertEqual(pa.classificar(1, texto)[0], "falha-quota")

    def test_cli_ausente_e_contrato_para_o_fallback_trocar_de_assinatura(self):
        falha, _ = pa.classificar(127, "FileNotFoundError: executavel "
                                       "indisponivel")
        self.assertEqual(falha, "falha-contrato")

    def test_transitorio_por_marcador(self):
        for texto in ("HTTP 503 service unavailable", "rate limit exceeded",
                      "connection reset by peer"):
            with self.subTest(texto=texto):
                falha, efeito = pa.classificar(1, texto)
                self.assertEqual(falha, "falha-transitoria")
                self.assertEqual(efeito, "nao-aplicado")

    def test_erro_desconhecido_e_contrato_nunca_transitorio(self):
        # Fail-closed. Erro que ninguem reconheceu virando transitorio por
        # otimismo geraria retry contra falha determinista — tres vezes o
        # mesmo erro, tres vezes a mesma franquia.
        falha, _ = pa.classificar(2, "erro que ninguem enumerou")
        self.assertEqual(falha, "falha-contrato")


class RespostaCompativelComAMaquinaDaP0(unittest.TestCase):
    """Trocar simulado por real e trocar o objeto, nao a maquina."""

    def test_resposta_e_uma_RespostaProvedor_com_todos_os_campos(self):
        sensor = SensorFalso(0, "resultado")
        r = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor).invocar(
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
        r = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor).invocar(
            b"t")
        self.assertFalse(r.ok)
        self.assertIn(b"motivo real da falha", r.saida)

    def test_custo_e_medido_e_a_ausencia_de_token_e_None_nunca_zero(self):
        r = pa.ProvedorAssinaturaReal(espec_codex(),
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
        r = pa.ProvedorAssinaturaReal(
            espec_codex(), sensor=SensorFalso(0, "ok"),
            relogio=lambda: next(marcas)).invocar(b"t")
        self.assertEqual(r.latencia_ms, 250)
        self.assertEqual(r.latencia_rotulo, "medido")

    def test_executor_observado_e_None_e_isso_e_limite_declarado(self):
        # O CLI nao ecoa qual modelo serviu a chamada. Afirmar o resolvido
        # aqui fabricaria a confirmacao que o guarda 0.2.1-9 usa para
        # detectar divergencia — o guarda passaria a se auto-confirmar.
        r = pa.ProvedorAssinaturaReal(espec_codex(),
                                      sensor=SensorFalso(0, "ok")).invocar(b"t")
        self.assertIsNone(r.executor_observado)

    def test_idempotency_key_e_registrada_e_ecoada(self):
        p = pa.ProvedorAssinaturaReal(espec_codex(), sensor=SensorFalso())
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
        real = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor)
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(self.entrada(auth_mode="payg-api"), real,
                                env={})
        self.assertEqual(sensor.chamadas, [],
                         "houve sonda apos veto economico: o bloqueio "
                         "precisa vir ANTES da invocacao")

    def test_custo_variavel_positivo_bloqueia_antes_da_invocacao(self):
        sensor = SensorFalso()
        real = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor)
        with self.assertRaises(PoliticaEconomicaViolada):
            AdaptadorAssinatura(self.entrada(variable_cost=0.01), real, env={})
        self.assertEqual(sensor.chamadas, [])

    def test_entrada_aprovada_delega_ao_executor_real(self):
        # O outro lado do portao: aprovado, a invocacao chega ao executor.
        sensor = SensorFalso(0, "saida real")
        real = pa.ProvedorAssinaturaReal(espec_codex(), sensor=sensor)
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

    def espec_python(self, headless=("-c",)):
        return dataclasses.replace(espec_de("codex"),
                                   executavel=sys.executable,
                                   headless=headless)

    def test_env_payg_e_removido_do_processo_filho(self):
        # A chave existe no env oferecido e NAO pode chegar ao filho. Este
        # e o teste que so o subprocesso real pode dar: com sensor falso, a
        # sanitizacao nunca roda.
        env = {"PATH": os.environ.get("PATH", ""),
               "OPENAI_API_KEY": "valor-fabricado-de-teste",
               "SSC_MARCA_BENIGNA": "presente"}
        p = pa.ProvedorAssinaturaReal(self.espec_python(), env=env)
        r = p.invocar(b"import os;"
                      b"print('OPENAI_API_KEY' in os.environ,"
                      b"os.environ.get('SSC_MARCA_BENIGNA'))")
        self.assertTrue(r.ok, r.saida)
        self.assertIn(b"False presente", r.saida,
                      "chave PAYG vazou para o subprocesso, ou a variavel "
                      "benigna foi removida junto")

    def test_saida_e_codigo_de_retorno_sao_capturados(self):
        p = pa.ProvedorAssinaturaReal(self.espec_python())
        r = p.invocar(b"import sys;sys.stderr.write('erro');sys.exit(3)")
        self.assertFalse(r.ok)
        self.assertEqual(r.falha, "falha-contrato")
        self.assertIn(b"erro", r.saida)

    def test_metacaractere_nao_vira_comando_no_subprocesso_real(self):
        # Se houvesse shell, `;` separaria comandos. Aqui o prompt inteiro
        # e UM argumento, e o programa imprime a string literal.
        p = pa.ProvedorAssinaturaReal(self.espec_python())
        r = p.invocar(b"print('antes'); print('depois & | $(x)')")
        self.assertTrue(r.ok, r.saida)
        self.assertIn(b"depois & | $(x)", r.saida)

    def test_timeout_real_vira_indeterminado_com_efeito_incerto(self):
        p = pa.ProvedorAssinaturaReal(self.espec_python(), timeout=1)
        r = p.invocar(b"import time;time.sleep(30)")
        self.assertEqual(r.falha, "indeterminado")
        self.assertEqual(r.efeito_externo, "incerto")

    def test_executavel_inexistente_nao_derruba_a_sessao(self):
        # Excecao aqui derrubaria a sessao inteira em vez de produzir o
        # attempt registrado que a evidencia exige.
        espec = dataclasses.replace(
            espec_de("codex"),
            executavel=os.path.join(_RAIZ, "nao-existe-este-cli"))
        r = pa.ProvedorAssinaturaReal(espec).invocar(b"t")
        self.assertFalse(r.ok)
        self.assertEqual(r.falha, "falha-contrato")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
