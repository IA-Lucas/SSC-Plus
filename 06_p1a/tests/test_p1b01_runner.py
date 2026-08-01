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
registrada, e as asserções falam sempre de NOMES.
"""

import importlib.util
import io
import json
import os
import tempfile
import time
import unittest
from unittest import mock

import apoio  # noqa: F401  (ajusta sys.path da suite)

from capsula import ViolacaoCapsula  # noqa: E402
from preflight.pipeline import RelatorioPreflight  # noqa: E402

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

    def __init__(self, resultado="SUPERVISED"):
        self.n = 0
        self.envs = []
        self.tiers = []
        self.resultado = resultado

    def __call__(self, espec, sensores=None, env=None, config_persistida=None,
                 tiers_declarados=None, agora=None):
        self.n += 1
        self.envs.append(dict(env or {}))
        self.tiers.append(tiers_declarados)
        return RelatorioPreflight(provider_id=espec.provider_id,
                                  resultado=self.resultado)


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


if __name__ == "__main__":
    unittest.main()
