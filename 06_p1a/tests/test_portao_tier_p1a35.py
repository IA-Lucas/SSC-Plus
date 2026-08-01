"""O portao de tier expirado, exercido — SSC+ P1-A.3.5 (achado 9).

O pacote que foi a revisao declara este controle como verificado. A
tabela de threat review de `pacote_p1a33.py` diz, literalmente:

    "Tier declarado expirado no instante da chamada | Validade
     reverificada imediatamente antes de cada chamada; expirado =
     PARADA | verificado nesta missao"

A varredura de guardas da P1-A.3.5 mediu que **nenhuma** das linhas de
recusa de `_verificar_tier` e alcancada por teste algum, nos dois
runners que a implementam. "Verificado" descrevia um ato manual — e ato
manual nao protege contra regressao.

O portao tem tres propriedades, e a terceira e a que mais facilmente se
perde numa edicao futura: o **teto** de `validade_maxima_horas` precisa
vencer uma `validade_horas` maior declarada no proprio registro. Sem
ele, bastaria declarar `validade_horas: 999` para uma declaracao valer
para sempre — e o limite de 24 h da emenda P1-A.3 item 1 seria letra
morta.

Zero CLI, zero rede, zero modelo: o portao le um JSON e decide.
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

_RUNNERS = (("revisao_p1a31.py", "tier_p1a31"),
            ("revisao_p1a33.py", "tier_p1a33"))


def _carregar(nome: str, apelido: str):
    caminho = os.path.join(_DIR_EVID, nome)
    if not os.path.isfile(caminho):
        raise unittest.SkipTest(f"runner ausente: {nome}")
    spec = importlib.util.spec_from_file_location(apelido, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _utc(delta_horas: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=delta_horas)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")


class PortaoDeTierDeclarado(unittest.TestCase):
    """`_verificar_tier` nos DOIS runners que o implementam."""

    def _com_declaracoes(self, raiz, declaracoes, teto=24):
        destino = Path(raiz) / "06_p1a"
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "tiers_declarados.json").write_text(
            json.dumps({"validade_maxima_horas": teto,
                        "declaracoes": declaracoes}),
            encoding="utf-8")

    def _cada_runner(self):
        for nome, apelido in _RUNNERS:
            yield nome, _carregar(nome, apelido)

    def test_declaracao_expirada_para_a_corrida(self):
        # A propriedade que a tabela de threat review afirma e que
        # nenhum teste media.
        for nome, mod in self._cada_runner():
            with self.subTest(runner=nome):
                with tempfile.TemporaryDirectory() as raiz:
                    self._com_declaracoes(raiz, [{
                        "provider_id": "kimi", "tier": "allegretto",
                        "declarado_por": "proprietario",
                        "declarado_em_utc": _utc(-30),
                        "validade_horas": 24}])
                    with mock.patch.object(mod, "RAIZ", Path(raiz)):
                        with self.assertRaises(SystemExit) as ctx:
                            mod._verificar_tier("kimi")
                    self.assertIn("EXPIRADO", str(ctx.exception))
                    self.assertIn("somente o proprietario renova",
                                  str(ctx.exception))

    def test_sem_declaracao_para_o_provider_para_a_corrida(self):
        for nome, mod in self._cada_runner():
            with self.subTest(runner=nome):
                with tempfile.TemporaryDirectory() as raiz:
                    self._com_declaracoes(raiz, [{
                        "provider_id": "codex", "tier": "chatgpt pro 5x",
                        "declarado_por": "proprietario",
                        "declarado_em_utc": _utc(-1),
                        "validade_horas": 24}])
                    with mock.patch.object(mod, "RAIZ", Path(raiz)):
                        with self.assertRaises(SystemExit) as ctx:
                            mod._verificar_tier("kimi")
                    self.assertIn("sem declaracao de tier",
                                  str(ctx.exception))

    def test_o_teto_vence_uma_validade_maior_declarada(self):
        # A propriedade mais fragil: `validade_horas: 999` NAO pode
        # sobreviver ao teto de 24 h. Sem isto, o limite da emenda
        # P1-A.3 item 1 seria letra morta — bastaria declarar um numero
        # grande.
        for nome, mod in self._cada_runner():
            with self.subTest(runner=nome):
                with tempfile.TemporaryDirectory() as raiz:
                    self._com_declaracoes(raiz, [{
                        "provider_id": "kimi", "tier": "allegretto",
                        "declarado_por": "proprietario",
                        "declarado_em_utc": _utc(-30),
                        "validade_horas": 999}], teto=24)
                    with mock.patch.object(mod, "RAIZ", Path(raiz)):
                        with self.assertRaises(SystemExit) as ctx:
                            mod._verificar_tier("kimi")
                    self.assertIn("EXPIRADO", str(ctx.exception))

    def test_declaracao_valida_atravessa_e_declara_a_janela(self):
        # Contraprova: sem ela, um portao que parasse SEMPRE passaria
        # nos tres testes acima.
        for nome, mod in self._cada_runner():
            with self.subTest(runner=nome):
                with tempfile.TemporaryDirectory() as raiz:
                    self._com_declaracoes(raiz, [{
                        "provider_id": "kimi", "tier": "allegretto",
                        "declarado_por": "proprietario",
                        "declarado_em_utc": _utc(-1),
                        "validade_horas": 24}])
                    with mock.patch.object(mod, "RAIZ", Path(raiz)):
                        estado = mod._verificar_tier("kimi")
                    self.assertEqual(estado["tier"], "allegretto")
                    self.assertEqual(estado["declarado_por"], "proprietario")
                    self.assertTrue(estado["valido_no_instante"])
                    self.assertIn("expira_em_utc", estado)

    def test_os_dois_runners_gravam_a_MESMA_evidencia_de_tier(self):
        # ACHADO 15, encontrado por este proprio arquivo ao exercer o
        # portao nos dois de uma vez: `revisao_p1a31` omitia
        # `declarado_por` — o campo que diz QUEM declarou o tier, e que o
        # portao do pipeline exige ser o proprietario. Corrigido; este
        # teste impede que as duas copias voltem a divergir em silencio.
        chaves = []
        for nome, mod in self._cada_runner():
            with tempfile.TemporaryDirectory() as raiz:
                self._com_declaracoes(raiz, [{
                    "provider_id": "kimi", "tier": "allegretto",
                    "declarado_por": "proprietario",
                    "declarado_em_utc": _utc(-1), "validade_horas": 24}])
                with mock.patch.object(mod, "RAIZ", Path(raiz)):
                    chaves.append((nome, sorted(mod._verificar_tier("kimi"))))
        self.assertEqual(chaves[0][1], chaves[1][1],
                         f"{chaves[0][0]} e {chaves[1][0]} gravam campos "
                         "diferentes para o mesmo portao")
        self.assertIn("declarado_por", chaves[0][1])

    def test_a_fronteira_e_fechada_no_instante_do_vencimento(self):
        # `agora >= expira` e PARADA: o instante exato do vencimento ja
        # esta fora. Fronteira medida, nao presumida.
        for nome, mod in self._cada_runner():
            with self.subTest(runner=nome):
                with tempfile.TemporaryDirectory() as raiz:
                    self._com_declaracoes(raiz, [{
                        "provider_id": "kimi", "tier": "allegretto",
                        "declarado_por": "proprietario",
                        "declarado_em_utc": _utc(-24),
                        "validade_horas": 24}], teto=24)
                    with mock.patch.object(mod, "RAIZ", Path(raiz)):
                        with self.assertRaises(SystemExit) as ctx:
                            mod._verificar_tier("kimi")
                    self.assertIn("EXPIRADO", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
