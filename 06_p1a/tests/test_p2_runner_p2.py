"""O runner da P2 de ponta a ponta — a frota inteira, sem gastar franquia.

Esta e a suite que mede o consumidor: preflight datado -> frota medida ->
RoutingDecision -> attempt -> fallback por quota -> veredito -> evidencia.
Toda invocacao passa por um sensor falso injetado; **nenhum teste daqui
invoca codex ou kimi, e nenhum consome assinatura**.

O RISCO PROPRIO DESTA SUITE, e como ele e contido: se o parametro
`sensor` deixasse de ser propagado, os testes passariam a chamar os CLIs
de verdade — e passariam, silenciosamente, queimando franquia a cada
corrida da suite. `SensorObrigatorio` levanta se for chamado sem que o
teste tenha programado resposta, e `test_o_default_da_operacao_e_o_sensor_
real` prende o outro lado: em operacao, sem sensor declarado, o executor
usa `sensor_subprocess`.

O QUE ESTES TESTES NAO COBREM, declarado:
- **nao provam que codex ou kimi respondam** ao argv que a especificacao
  declara. Isso e leitura ate a primeira corrida real;
- **nao cobrem `main()`**: a funcao de linha de comando exige capsula e
  lease vivos, e monta-los num teste unitario reproduziria a operacao pela
  metade. O que ela orquestra esta coberto por `executar`,
  `carregar_preflight` e os portoes;
- **nao medem concorrencia** entre dois runners da P2 ao mesmo tempo. O
  escritor unico e o mecanismo herdado, exercido na suite da P0;
- **nao cobrem tarefa que exija escrita**: o envelope nasce read-only, e
  nenhum teste aqui pede patch.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", os.path.join("05_p0", "cenarios"), "08_p2",
           os.path.join("06_p1a", "evidencias")):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import provedor_assinatura as pa  # noqa: E402
import runner_p2  # noqa: E402
from ssc_p0.frota import STOP_WAIT_RESET  # noqa: E402

EVIDENCIA_REAL = os.path.join(
    _RAIZ, "07_p1b", "evidencias", "preflight-20260801T235521Z.json")


def preflight_real() -> dict:
    with open(EVIDENCIA_REAL, encoding="utf-8") as f:
        return json.load(f)


class SensorObrigatorio:
    """Sensor falso que responde por provedor — e acusa o que nao previu.

    Chamada sem resposta programada levanta em vez de devolver algo
    plausivel: um default silencioso aqui esconderia justamente o caso em
    que o runner invocou quem nao devia.
    """

    def __init__(self, **por_provedor):
        self.por_provedor = por_provedor
        self.chamadas = []

    def __call__(self, argv, env=None, timeout=None):
        exe = str(argv[0]).lower()
        for pid, resposta in self.por_provedor.items():
            if pid in exe:
                self.chamadas.append({"provedor": pid, "argv": list(argv)})
                return resposta
        raise AssertionError(f"sensor chamado para executavel nao previsto: "
                             f"{exe}")

    def provedores_chamados(self) -> list:
        return [c["provedor"] for c in self.chamadas]


class _ComLab(unittest.TestCase):
    """Cada corrida monta o laboratorio numa raiz temporaria propria."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p2-runner-")
        self.addCleanup(self._tmp.cleanup)
        self.raiz_lab = os.path.join(self._tmp.name, "lab")

    def executar(self, sensor, **kw):
        base = dict(tarefa="responda com a palavra pronto",
                    criterio="resposta nao vazia",
                    preflight=preflight_real(),
                    raiz_lab=self.raiz_lab, sensor=sensor)
        base.update(kw)
        return runner_p2.executar(**base)


class ValidadeDoPreflight(unittest.TestCase):
    """Veredito de ontem nao autoriza gasto de hoje."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p2-pf-")
        self.addCleanup(self._tmp.cleanup)

    def escrever(self, dados) -> str:
        caminho = os.path.join(self._tmp.name, "pf.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f)
        return caminho

    def test_arquivo_ausente_e_parada(self):
        with self.assertRaises(SystemExit):
            runner_p2.carregar_preflight(
                os.path.join(self._tmp.name, "nao-existe.json"), 24)

    def test_json_ilegivel_e_parada(self):
        caminho = os.path.join(self._tmp.name, "quebrado.json")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("{ nao e json")
        with self.assertRaises(SystemExit):
            runner_p2.carregar_preflight(caminho, 24)

    def test_arquivo_sem_bloco_frota_e_parada(self):
        with self.assertRaises(SystemExit):
            runner_p2.carregar_preflight(
                self.escrever({"gerado_em_utc": "2026-08-03T00:00:00Z"}), 24)

    def test_sem_data_legivel_e_parada(self):
        # Sem data nao ha como saber se venceu — e "nao sei" nao pode
        # virar "esta valido".
        for dados in ({"frota": []},
                      {"frota": [], "gerado_em_utc": "ontem"},
                      {"frota": [], "gerado_em_utc": None},
                      {"frota": [], "gerado_em_utc": "2026-08-03T00:00:00"}):
            with self.subTest(dados=dados):
                with self.assertRaises(SystemExit):
                    runner_p2.carregar_preflight(self.escrever(dados), 24)

    def test_datado_no_futuro_e_parada(self):
        # Mesma regra de `sombra.declaracao_valida`: relogio que ainda nao
        # chegou la nao verifica nada.
        agora = datetime(2026, 8, 3, tzinfo=timezone.utc)
        futuro = (agora + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.assertRaises(SystemExit):
            runner_p2.carregar_preflight(
                self.escrever({"frota": [], "gerado_em_utc": futuro}), 24,
                agora=agora)

    def test_velho_demais_e_parada_com_a_idade_no_texto(self):
        agora = datetime(2026, 8, 3, tzinfo=timezone.utc)
        velho = (agora - timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.assertRaises(SystemExit) as ctx:
            runner_p2.carregar_preflight(
                self.escrever({"frota": [], "gerado_em_utc": velho}), 24,
                agora=agora)
        self.assertIn("acima da janela", str(ctx.exception))

    def test_dentro_da_janela_passa_e_registra_a_idade(self):
        agora = datetime(2026, 8, 3, tzinfo=timezone.utc)
        recente = (agora - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        dados = runner_p2.carregar_preflight(
            self.escrever({"frota": [], "gerado_em_utc": recente}), 24,
            agora=agora)
        self.assertEqual(dados["_idade_s"], 7200)


class CorridaDePontaAPonta(_ComLab):
    """A tarefa atravessa a maquina inteira da P0 com executores reais."""

    def test_sucesso_no_primeiro_executor(self):
        sensor = SensorObrigatorio(codex=(0, "pronto", ""))
        r = self.executar(sensor)
        self.assertEqual(r["status"], "sucesso", r.get("detalhe"))
        self.assertEqual(r["saida"], "pronto")
        self.assertEqual(sensor.provedores_chamados(), ["codex"],
                         "kimi foi invocado sem necessidade: o fallback so "
                         "existe para falha")
        self.assertEqual(len(r["attempts"]), 1)
        self.assertEqual(r["attempts"][0]["resultado"], "sucesso")

    def test_o_prompt_chega_ao_argv_do_CLI(self):
        sensor = SensorObrigatorio(codex=(0, "ok", ""))
        self.executar(sensor, tarefa="conte ate tres")
        self.assertIn("conte ate tres", sensor.chamadas[0]["argv"])

    def test_custo_variavel_e_zero_e_o_rotulo_nao_e_simulado(self):
        r = self.executar(SensorObrigatorio(codex=(0, "ok", "")))
        custo = r["attempts"][0]["custo_medido"]
        self.assertEqual(custo["valor"], 0.0)
        self.assertEqual(custo["rotulo"], "medido-assinatura")
        self.assertIsNone(custo["tokens_reportados"])

    def test_a_cadeia_de_eventos_fica_integra_e_o_placar_e_projetado(self):
        # `verificar_integridade` levanta se a cadeia quebrar, e a
        # EvidencePlane SO le: o placar sai do log verificado, nunca da
        # memoria do processo.
        r = self.executar(SensorObrigatorio(codex=(0, "ok", "")))
        self.assertIn("placar", r)
        self.assertTrue(r["work_unit_id"])
        self.assertTrue(r["linhagem_id"])


class FallbackEntreAssinaturas(_ComLab):
    """QUOTA_EXHAUSTED troca de assinatura — nunca de canal economico."""

    def test_quota_no_codex_leva_a_tarefa_ao_kimi(self):
        sensor = SensorObrigatorio(
            codex=(1, "", "0 requests remaining"),
            kimi=(0, "feito pelo kimi", ""))
        r = self.executar(sensor)
        self.assertEqual(r["status"], "sucesso", r.get("detalhe"))
        self.assertEqual(r["saida"], "feito pelo kimi")
        self.assertEqual(sensor.provedores_chamados(), ["codex", "kimi"])

    def test_o_attempt_de_quota_fica_registrado_com_o_tipo_certo(self):
        # A evidencia precisa dizer POR QUE trocou. `falha-quota` tipada e
        # o que dispara `registrar_quota_exhausted` na frota.
        sensor = SensorObrigatorio(
            codex=(1, "", "0 requests remaining"),
            kimi=(0, "feito pelo kimi", ""))
        r = self.executar(sensor)
        por_provedor = {a["executor_resolvido"]["provedor"]: a["resultado"]
                        for a in r["attempts"]}
        self.assertEqual(por_provedor.get("codex"), "falha-quota")
        self.assertEqual(por_provedor.get("kimi"), "sucesso")

    def test_quota_nos_dois_para_em_STOP_WAIT_RESET_e_nao_migra(self):
        sensor = SensorObrigatorio(
            codex=(1, "", "0 requests remaining"),
            kimi=(1, "", "quota exhausted"))
        r = self.executar(sensor)
        self.assertNotEqual(r["status"], "sucesso")
        self.assertEqual(sorted(set(sensor.provedores_chamados())),
                         ["codex", "kimi"])
        # A propriedade que importa nao e o rotulo do status: e que
        # NENHUMA rota paga apareceu como alternativa.
        modelos = {a["executor_resolvido"]["modelo"] for a in r["attempts"]}
        self.assertEqual(modelos, {"gpt-5.6-sol", "kimi-code/k3"})

    def test_indeterminado_nao_gera_retry_automatico(self):
        # IR-2: efeito externo incerto e escalonamento, nao nova tentativa
        # no mesmo executor. Uma tarefa que talvez tenha rodado nao pode
        # rodar de novo por conta propria.
        sensor = SensorObrigatorio(codex=(pa.RC_TIMEOUT, "", "timeout"))
        r = self.executar(sensor)
        self.assertEqual(r["status"], "indeterminado")
        self.assertEqual(sensor.provedores_chamados(), ["codex"])


class FrotaVaziaNaoViraPagamento(_ComLab):
    """Sem assinatura capaz = parada. Migrar para PAYG e PROIBIDO."""

    def test_preflight_sem_habilitados_para_em_STOP_WAIT_RESET(self):
        preflight = preflight_real()
        for relatorio in preflight["frota"]:
            relatorio["resultado"] = "BLOCKED"
        sensor = SensorObrigatorio()   # qualquer chamada levanta
        r = self.executar(sensor, preflight=preflight)
        self.assertEqual(r["status"], STOP_WAIT_RESET)
        self.assertIn("PROIBIDO", r["detalhe"])
        self.assertEqual(sensor.chamadas, [],
                         "houve invocacao com a frota vazia")

    def test_entradas_todas_vetadas_param_antes_de_invocar(self):
        # Entradas construidas, mas sem canal provado: `Frota.elegiveis`
        # devolve vazio e o runner para ANTES de montar o laboratorio.
        preflight = preflight_real()
        for relatorio in preflight["frota"]:
            relatorio["origem_credencial"] = "nao-sondada"
        sensor = SensorObrigatorio()
        r = self.executar(sensor, preflight=preflight)
        self.assertEqual(r["status"], STOP_WAIT_RESET)
        self.assertTrue(r["montagem"]["vetos"])
        self.assertEqual(sensor.chamadas, [])


class OSensorRealEOPadraoDaOperacao(unittest.TestCase):
    """O outro lado do contencao: em operacao ninguem declara sensor."""

    def test_o_default_da_operacao_e_o_sensor_real(self):
        # Se esta propriedade se perder, a operacao para de invocar CLI —
        # e se o `sensor=` sumir da cadeia, os testes acima passam a
        # invocar CLI de verdade. Os dois lados precisam de guarda.
        p = pa.ProvedorAssinaturaReal(
            __import__("preflight.frota_real", fromlist=["espec_de"])
            .espec_de("codex"))
        self.assertIs(p.sensor, pa.sensor_subprocess)

    def test_a_fabrica_propaga_o_sensor_ate_o_executor(self):
        import frota_medida
        from preflight.frota_real import ESPECIFICACOES
        montagem = frota_medida.frota_do_preflight(
            preflight_real()["frota"], ESPECIFICACOES)
        from ssc_p0.frota import Frota
        frota = Frota(montagem["entradas"])
        marcador = SensorObrigatorio(codex=(0, "x", ""))
        fabrica = runner_p2.fabrica_de_provedores(frota, 10, marcador)
        entrada = montagem["entradas"][0]
        adaptador = fabrica(
            f"{entrada.provider_id}/{entrada.model_id}",
            {"provedor": entrada.provider_id, "modelo": entrada.model_id},
            {"provedor": entrada.provider_id, "modelo": entrada.model_id,
             "effort": "alto"})
        self.assertIs(adaptador.provedor_fake.sensor, marcador)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
