"""O runner da P1-B dentro da capsula — SSC+ P1-B.01 (ordens 1 a 4).

A P1-A.3.5 mediu que `07_p1b/preflight_atual.py` tinha ZERO linha
executada pelas duas suites; o achado 7 fechou o portao do escritor unico
dessa copia. Esta missao fecha as quatro afirmacoes seguintes, que o
runner fazia sem cobrir:

1. o pipeline auditava e classificava `dict(os.environ)` CRU — a capsula
   ratificada da P1-A.2 nunca era importada, e executar o runner FORA da
   capsula degradava em silencio;
2. o sumario final filtrava so ELIGIBLE, de modo que os outros tres
   resultados do enum (`pipeline.py:31`) sumiam da ultima linha impressa;
3. o caminho de bloqueio imediato (`pipeline.py:139-140`) devolvia
   `origem_credencial`/`quota` no padrao da dataclass, com cara de campo
   observado;
4. `carregar_declaracoes` nao aparecia no runner, e a chamada omitia
   `tiers_declarados` — a trilha SHADOW_ELIGIBLE inteira era inalcancavel
   a partir daqui.

POR QUE ESTE ARQUIVO VIVE NA SUITE P1-A. Mesma razao de
`test_p1b_lease_p1a35.py`: criar `07_p1b/tests/` daria um guarda que
nenhuma suite roda — exatamente o defeito que estes testes corrigem.

CUSTO ZERO POR CONSTRUCAO. `executar_preflight` e substituido, de modo
que nenhum CLI e invocado e nenhuma sonda real roda; `HOME` aponta para
um descartavel, de modo que nenhuma config real do usuario e lida.

NOMES, NUNCA VALORES. Os ambientes de teste carregam um valor fabricado
e evidente (`_VALOR_FALSO`); nenhuma variavel real do usuario e lida ou
registrada, e as asercoes falam sempre de NOMES.
"""

import importlib.util
import io
import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

import apoio  # noqa: F401  (ajusta sys.path da suite)

import leitor_tiers  # noqa: E402
from capsula import ViolacaoCapsula  # noqa: E402
from preflight.pipeline import (RESULTADOS, RelatorioPreflight,  # noqa: E402
                                executar_preflight)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P1A)

# Nome com cara de credencial de PROVEDOR (bloqueia e e reprovado por
# `_nome_payg`); o valor e fabricado e nao existe em lugar nenhum.
_NOME_PAYG = "OPENAI_API_KEY"
_VALOR_FALSO = "valor-fabricado-de-teste-nao-e-credencial"


class _SaidaMuda(io.StringIO):
    def reconfigure(self, **kwargs):
        return None


def _carregar_p1b():
    caminho = os.path.join(_RAIZ_REPO, "07_p1b", "preflight_atual.py")
    if not os.path.isfile(caminho):
        raise unittest.SkipTest("runner da P1-B ausente")
    spec = importlib.util.spec_from_file_location("preflight_atual_p1b01",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _escrever_lock(dir_locks, sessao, fence, expira_em):
    os.makedirs(dir_locks, exist_ok=True)
    with open(os.path.join(dir_locks, f"{sessao}.lease"), "w",
              encoding="utf-8") as f:
        json.dump({"sessao": sessao, "pid": os.getpid(), "token": fence,
                   "renovado_em": expira_em - 120, "expira_em": expira_em}, f)
    with open(os.path.join(dir_locks, f"{sessao}.fence"), "w",
              encoding="ascii") as f:
        f.write(str(fence))


class _EspiaoPreflight:
    """Substitui `executar_preflight`: conta chamadas e guarda o env."""

    def __init__(self, resultado="SUPERVISED", por_pid=None, sombra=None):
        self.n = 0
        self.envs = []
        self.tiers = []
        self.resultado = resultado
        self.por_pid = dict(por_pid or {})
        self.sombra = sombra

    def __call__(self, espec, sensores=None, env=None, config_persistida=None,
                 tiers_declarados=None, agora=None):
        self.n += 1
        self.envs.append(dict(env or {}))
        self.tiers.append(tiers_declarados)
        resultado = self.por_pid.get(espec.provider_id, self.resultado)
        return RelatorioPreflight(
            provider_id=espec.provider_id, resultado=resultado,
            sombra=self.sombra if resultado == "SHADOW_ELIGIBLE" else None)


class BaseRunnerP1B(unittest.TestCase):
    """Raiz de mentira, lease vivo e nenhuma sonda real."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _carregar_p1b()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1b01-")
        self.raiz = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.lar = os.path.join(self.raiz, "lar-vazio")
        os.makedirs(self.lar)
        _escrever_lock(os.path.join(self.raiz, "locks"), self.mod._SESSAO_LOCK,
                       7, time.time() + 600)

    def _env(self, sujo=False) -> dict:
        env = {"USERPROFILE": self.lar, "HOME": self.lar,
               "PATH": os.environ.get("PATH", "")}
        if sujo:
            env[_NOME_PAYG] = _VALOR_FALSO
        return env

    def _rodar_main(self, espiao, sujo=False, sem_guarda=False,
                    saida=None):
        contextos = [
            mock.patch.dict(os.environ, self._env(sujo), clear=True),
            mock.patch.object(self.mod, "_RAIZ", self.raiz),
            mock.patch.object(self.mod, "executar_preflight", espiao),
            mock.patch("sys.stdout", saida if saida is not None
                       else _SaidaMuda()),
        ]
        if sem_guarda:
            # Isola a ordem 1(a) da ordem 1(b): o ambiente classificado
            # precisa ser o da capsula POR CONSTRUCAO, e nao por confianca
            # no portao de entrada.
            contextos.append(mock.patch.object(self.mod,
                                               "exigir_capsula_limpa",
                                               lambda *a, **k: None))
        with contextos[0], contextos[1], contextos[2], contextos[3]:
            if sem_guarda:
                with contextos[4]:
                    return self.mod.main()
            return self.mod.main()

    def _gravados(self):
        saida = os.path.join(self.raiz, "07_p1b", "evidencias")
        return sorted(os.listdir(saida)) if os.path.isdir(saida) else []


class Ordem1CapsulaDoRunner(BaseRunnerP1B):
    """O runner passa a operar DENTRO da capsula ratificada."""

    def test_fora_da_capsula_aborta_antes_de_sonda_e_de_escrita(self):
        # O defeito: com credencial de provedor visivel no ambiente, o
        # runner seguia adiante, sondava e gravava — a "capsula" alcancava
        # so as sondas-filho.
        espiao = _EspiaoPreflight()
        with self.assertRaises(ViolacaoCapsula) as ctx:
            self._rodar_main(espiao, sujo=True)
        self.assertIn("fora da capsula", str(ctx.exception))
        self.assertIn(_NOME_PAYG, str(ctx.exception))
        self.assertNotIn(_VALOR_FALSO, str(ctx.exception),
                         "a mensagem carrega NOME, jamais valor")
        self.assertEqual(espiao.n, 0, "nenhuma sonda pode ter ocorrido")
        self.assertEqual(self._gravados(), [], "nada pode ter sido gravado")

    def test_o_portao_vem_antes_do_lease(self):
        # Discriminador de ordem: sem lease nenhum, um runner que
        # verificasse o escritor primeiro pararia com "lease ilegivel".
        # O portao da capsula tem de falar antes.
        os.remove(os.path.join(self.raiz, "locks",
                               f"{self.mod._SESSAO_LOCK}.lease"))
        with self.assertRaises(ViolacaoCapsula):
            self._rodar_main(_EspiaoPreflight(), sujo=True)

    def test_o_ambiente_classificado_e_o_da_capsula(self):
        # Ordem 1(a), isolada do portao: mesmo com o ambiente sujo, o que
        # chega ao pipeline nao pode conter nome reprovado por
        # `_nome_payg` — nada dele alcanca `env_outras`.
        espiao = _EspiaoPreflight()
        rc = self._rodar_main(espiao, sujo=True, sem_guarda=True)
        self.assertEqual(rc, 0)
        self.assertEqual(espiao.n, 5, "os cinco provedores classificados")
        for env in espiao.envs:
            self.assertNotIn(_NOME_PAYG, env)
            self.assertEqual(self.mod.verificar_capsula(env), [])
            self.assertIn("PATH", env, "o resto do ambiente permanece")

    def test_a_evidencia_registra_a_capsula_por_nomes(self):
        espiao = _EspiaoPreflight()
        self.assertEqual(self._rodar_main(espiao), 0)
        gravados = self._gravados()
        self.assertEqual(len(gravados), 1)
        with open(os.path.join(self.raiz, "07_p1b", "evidencias",
                               gravados[0]), encoding="utf-8") as f:
            doc = json.load(f)
        self.assertEqual(doc["capsula"]["violacoes_no_env_classificado"], [])
        self.assertIn("ambiente_capsula", doc["capsula"]["mecanismo"])
        self.assertIn("exigir_capsula_limpa", doc["capsula"]["mecanismo"])

    def test_o_ambiente_global_do_processo_nunca_e_mutado(self):
        # A P1-A.2 decidiu que credencial de terceiro PODE existir no
        # ambiente global e que o SSC+ NAO a remove: a capsula filtra a
        # copia, nunca a fonte.
        espiao = _EspiaoPreflight()
        with mock.patch.dict(os.environ, self._env(sujo=True), clear=True):
            with mock.patch.object(self.mod, "_RAIZ", self.raiz), \
                    mock.patch.object(self.mod, "executar_preflight", espiao), \
                    mock.patch.object(self.mod, "exigir_capsula_limpa",
                                      lambda *a, **k: None), \
                    mock.patch("sys.stdout", _SaidaMuda()):
                self.mod.main()
            self.assertIn(_NOME_PAYG, os.environ,
                          "a fonte permanece intacta; so a copia e filtrada")

    def test_o_leitor_de_ambiente_e_o_canonico_e_nao_uma_copia_local(self):
        # Achado 7 / achado 10, mesmo mecanismo: a copia que ninguem
        # exercita fica para tras. Se alguem reescrever aqui um filtro
        # local em vez de chamar a capsula ratificada, isto reprova.
        import capsula
        with open(os.path.join(_RAIZ_REPO, "07_p1b", "preflight_atual.py"),
                  encoding="utf-8") as f:
            fonte = f.read()
        self.assertIn("from capsula import", fonte)
        self.assertIs(self.mod.ambiente_capsula, capsula.ambiente_capsula)
        self.assertIs(self.mod.exigir_capsula_limpa,
                      capsula.exigir_capsula_limpa)


class Ordem2SumarioDosQuatroResultados(BaseRunnerP1B):
    """O sumario deixa de engolir tres dos quatro resultados do enum."""

    def _sumario(self, espiao) -> str:
        saida = _SaidaMuda()
        self.assertEqual(self._rodar_main(espiao, saida=saida), 0)
        return saida.getvalue()

    def test_os_quatro_resultados_saem_no_sumario(self):
        # O defeito: com google e grok em SUPERVISED, a ultima linha
        # impressa era "ELIGIBLE: []" — que se le como "nenhum provedor
        # passou". Os outros tres resultados nao existiam na saida.
        texto = self._sumario(_EspiaoPreflight(
            por_pid={"codex": "ELIGIBLE", "kimi": "SHADOW_ELIGIBLE",
                     "claude": "BLOCKED"},
            sombra={"tier_declarado": "Allegretto"}))
        for resultado in RESULTADOS:
            self.assertIn(f"{resultado}:", texto,
                          f"{resultado} sumiu do sumario")
        self.assertIn("ELIGIBLE: ['codex']", texto)
        self.assertIn("SHADOW_ELIGIBLE: ['kimi']", texto)
        self.assertIn("BLOCKED: ['claude']", texto)
        self.assertIn("SUPERVISED: ['google', 'grok']", texto)

    def test_resultado_vazio_aparece_como_linha_e_nao_como_ausencia(self):
        # Contraprova do formato: sem esta, um sumario que imprimisse
        # apenas os resultados nao vazios passaria no teste acima.
        texto = self._sumario(_EspiaoPreflight(resultado="SUPERVISED"))
        self.assertIn("ELIGIBLE: []", texto)
        self.assertIn("SHADOW_ELIGIBLE: []", texto)
        self.assertIn("BLOCKED: []", texto)
        self.assertIn("SUPERVISED: ['codex', 'claude', 'kimi', 'google', "
                      "'grok']", texto)

    def test_nenhum_provedor_desaparece_na_particao(self):
        espiao = _EspiaoPreflight(por_pid={"codex": "ELIGIBLE",
                                           "claude": "BLOCKED"})
        texto = self._sumario(espiao)
        self.assertIn(f"total classificado: {espiao.n}+0 de {espiao.n} "
                      "provedor(es)", texto)
        for pid in ("codex", "claude", "kimi", "google", "grok"):
            # Cada provedor aparece na linha por-provedor E em exatamente
            # uma das quatro listas do sumario.
            listas = [linha for linha in texto.splitlines()
                      if linha.startswith(tuple(f"{r}:" for r in RESULTADOS))
                      and f"'{pid}'" in linha]
            self.assertEqual(len(listas), 1, f"{pid} em {len(listas)} listas")

    def test_shadow_eligible_cabe_na_coluna_do_relatorio(self):
        # "SHADOW_ELIGIBLE" tem 15 caracteres e a coluna tinha 10: a
        # trilha criada pela emenda P1-A.3 item 1 era justamente a que
        # saia desalinhada.
        texto = self._sumario(_EspiaoPreflight(
            por_pid={"kimi": "SHADOW_ELIGIBLE"},
            sombra={"tier_declarado": "Allegretto"}))
        linha = next(ln for ln in texto.splitlines()
                     if ln.startswith("  kimi"))
        self.assertIn("SHADOW_ELIGIBLE ", linha)
        self.assertIn("plano=", linha)
        self.assertIn("sombra=Allegretto", linha)


class Ordem3CampoNaoObservadoNoBloqueioImediato(unittest.TestCase):
    """O relatorio para de afirmar credencial que ninguem olhou."""

    def _bloqueio_imediato(self, provider_id="codex"):
        # Chave PAYG de OUTRO provedor: cai em `env_outras` e bloqueia
        # ANTES de qualquer sonda (`pipeline.py:139-140`).
        sens, sensor_exec, sensor_modelos = apoio.sensores_dict(provider_id)
        rel = executar_preflight(
            apoio.espec_de(provider_id), sensores=sens,
            env={"NVIDIA_API_KEY": apoio.SENTINELA, "PATH": "x"},
            config_persistida={})
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertEqual(sensor_exec.n, 0, "bloqueio e ANTES da sonda")
        self.assertEqual(sensor_modelos.n, 0)
        return rel

    def test_origem_e_quota_saem_marcadas_como_nao_sondadas(self):
        # O defeito: sem sonda alguma, o relatorio saia com
        # origem_credencial="ausente" e quota="desconhecida" — os mesmos
        # valores que o pipeline usa para dizer "consultamos o login e
        # nao havia credencial" / "a franquia e incerta".
        for provider_id in ("codex", "claude", "kimi", "google", "grok"):
            with self.subTest(provedor=provider_id):
                rel = self._bloqueio_imediato(provider_id)
                self.assertEqual(rel.origem_credencial, "nao-sondada")
                self.assertEqual(rel.quota, "nao-sondada")

    def test_o_marcador_e_o_mesmo_do_caminho_vizinho_de_zero_sondas(self):
        # O caminho de zero sondas (`pipeline.py:154`) ja resolvia isso;
        # o de bloqueio imediato ficara para tras. Mesmo vocabulario,
        # senao quem le a evidencia precisa saber de qual ramo veio.
        zero_sondas = executar_preflight(
            apoio.espec_de("grok"), sensores=apoio.sensores_dict("grok")[0],
            env={}, config_persistida={})
        self.assertEqual(zero_sondas.origem_credencial,
                         self._bloqueio_imediato("grok").origem_credencial)

    def test_o_campo_observado_continua_observado(self):
        # Contraprova: sem ela, marcar TUDO como "nao-sondada" passaria.
        # Com o login realmente consultado, a origem observada permanece.
        sens, sensor_exec, _ = apoio.sensores_dict("codex")
        rel = executar_preflight(apoio.espec_de("codex"), sensores=sens,
                                 env={}, config_persistida={})
        self.assertGreater(sensor_exec.n, 0)
        self.assertEqual(rel.origem_credencial, "subscription-oauth")
        self.assertEqual(rel.quota, "desconhecida")
        self.assertNotEqual(rel.origem_credencial, "nao-sondada")

    def test_o_marcador_atravessa_o_roundtrip_do_relatorio(self):
        # O campo so serve se sobreviver ate a evidencia em disco.
        rel = self._bloqueio_imediato("kimi")
        dados = rel.to_dict()
        self.assertEqual(dados["origem_credencial"], "nao-sondada")
        self.assertEqual(dados["quota"], "nao-sondada")
        self.assertEqual(RelatorioPreflight.from_dict(dados), rel)
        self.assertNotIn(apoio.SENTINELA, json.dumps(dados),
                         "erro carrega NOME, jamais valor")


class Ordem4DeclaracoesDeTierNoRunner(BaseRunnerP1B):
    """O runner passa a carregar e repassar as declaracoes de tier."""

    def _declaracao(self, provider_id="kimi", tier="Allegretto",
                    horas_atras=1, declarado_por="proprietario") -> dict:
        instante = datetime.now(timezone.utc) - timedelta(hours=horas_atras)
        return {"declaracoes": [{
            "provider_id": provider_id, "tier": tier,
            "declarado_por": declarado_por,
            "declarado_em_utc": instante.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "validade_horas": 24}]}

    def _arquivo(self, conteudo) -> str:
        caminho = os.path.join(self.raiz, "tiers.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(conteudo, f)
        return caminho

    def test_o_pipeline_recebe_as_declaracoes_carregadas(self):
        # O defeito: `tiers_declarados` era omitido e valia None
        # (`pipeline.py:97`) — a trilha SHADOW_ELIGIBLE era inalcancavel
        # a partir deste runner mesmo com declaracao valida em disco.
        caminho = self._arquivo(self._declaracao())
        espiao = _EspiaoPreflight()
        with mock.patch.object(self.mod, "carregar_tiers",
                               lambda: leitor_tiers.carregar_tiers(caminho)):
            self.assertEqual(self._rodar_main(espiao), 0)
        self.assertEqual(espiao.n, 5)
        for tiers in espiao.tiers:
            self.assertIsNotNone(tiers, "tiers_declarados chegou como None")
            self.assertIn("kimi", tiers)
            self.assertEqual(tiers["kimi"].tier, "Allegretto")

    def test_a_trilha_sombra_fica_alcancavel_de_ponta_a_ponta(self):
        # Prova de alcance real, sem espiao no pipeline: com OAuth
        # observado, plano nao observavel no CLI e declaracao valida do
        # proprietario, o resultado e SHADOW_ELIGIBLE.
        tiers = leitor_tiers.carregar_tiers(self._arquivo(self._declaracao()))
        rel = executar_preflight(
            apoio.espec_de("kimi"), sensores=apoio.sensores_dict(
                "kimi", login="managed:kimi-code type=kimi source=oauth")[0],
            env={}, config_persistida={}, tiers_declarados=tiers)
        self.assertEqual(rel.resultado, "SHADOW_ELIGIBLE")
        self.assertEqual(rel.sombra["tier_declarado"], "Allegretto")
        # Contraprova: sem as declaracoes, o mesmo cenario e BLOCKED —
        # que e exatamente o que o runner produzia ao omitir o parametro.
        sem = executar_preflight(
            apoio.espec_de("kimi"), sensores=apoio.sensores_dict(
                "kimi", login="managed:kimi-code type=kimi source=oauth")[0],
            env={}, config_persistida={}, tiers_declarados=None)
        self.assertEqual(sem.resultado, "BLOCKED")
        self.assertIn("P1A-PLANO-DESCONHECIDO", apoio.codigos(sem))

    def test_declaracao_vencida_e_reportada_como_esta_e_nao_renovada(self):
        # A missao proibe renovar declaracao (ato do proprietario). O
        # vencido tem de SAIR no relatorio, nao ser silenciado.
        tiers = leitor_tiers.carregar_tiers(
            self._arquivo(self._declaracao(horas_atras=48)))
        self.assertIn("kimi", tiers, "o leitor nao filtra o vencido")
        rel = executar_preflight(
            apoio.espec_de("kimi"), sensores=apoio.sensores_dict(
                "kimi", login="managed:kimi-code type=kimi source=oauth")[0],
            env={}, config_persistida={}, tiers_declarados=tiers)
        self.assertEqual(rel.resultado, "BLOCKED")
        self.assertIn("P1A-DECLARACAO-EXPIRADA", apoio.codigos(rel))

    def test_fonte_ausente_ou_ilegivel_e_fail_closed(self):
        self.assertEqual(
            leitor_tiers.carregar_tiers(os.path.join(self.raiz, "nao-existe")),
            {})
        caminho = os.path.join(self.raiz, "lixo.json")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("{isto nao e json")
        self.assertEqual(leitor_tiers.carregar_tiers(caminho), {})

    def test_a_evidencia_registra_o_tier_e_o_limite_da_emenda(self):
        caminho = self._arquivo(self._declaracao())
        with mock.patch.object(self.mod, "carregar_tiers",
                               lambda: leitor_tiers.carregar_tiers(caminho)):
            self.assertEqual(self._rodar_main(_EspiaoPreflight()), 0)
        with open(os.path.join(self.raiz, "07_p1b", "evidencias",
                               self._gravados()[0]), encoding="utf-8") as f:
            doc = json.load(f)
        emenda = doc["emenda_p1a3_item_1"]
        self.assertEqual(emenda["tiers_declarados"], {"kimi": "Allegretto"})
        self.assertIn("SHADOW_ELIGIBLE somente", emenda["limite"])
        self.assertIn("NAO autoriza P2", emenda["limite"])

    def test_o_leitor_de_tiers_e_unico_nos_dois_runners(self):
        # Achados 7, 10 e 14, mesmo mecanismo: copiar o leitor para o
        # segundo runner deixaria uma das copias para tras na proxima
        # correcao. Se alguem reintroduzir uma copia local, isto reprova.
        import preflight_capsula
        self.assertIs(self.mod.carregar_tiers, leitor_tiers.carregar_tiers)
        self.assertIs(preflight_capsula._carregar_tiers,
                      leitor_tiers.carregar_tiers)
        with open(os.path.join(_RAIZ_REPO, "07_p1b", "preflight_atual.py"),
                  encoding="utf-8") as f:
            self.assertIn("leitor_tiers", f.read())


if __name__ == "__main__":
    unittest.main()
