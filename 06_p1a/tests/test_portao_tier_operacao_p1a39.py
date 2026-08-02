"""O portao de tier no CAMINHO DA OPERACAO — SSC+ P1-A.3.9.

MECANISMO (a) da FASE 2 da P1-A.3.8, ultimos dois guardas: `P1A-09` e
`P1A-10`. A linha da remedicao e literal:

    2/2 ramos, JSON real em disco — porem `test_portao_tier_p1a35`
    chama `mod._verificar_tier("kimi")` DIRETO. Que `main()` o chame
    ANTES de invocar provedor nao e exercido.
    Remedio: rodar `main()` com reviewer falso e declaracao vencida,
    exigindo ZERO chamada ao reviewer.

E o remedio que este arquivo executa. O guarda nao e "a funcao recusa
declaracao vencida" — isso `test_portao_tier_p1a35` ja prova, e continua
valendo. O guarda e **a corrida para antes de gastar a chamada**, e a
unica maneira de exercer isso e rodar `main()` e contar as invocacoes.

## A lista que nada prendia — o mesmo padrao de CHAVES_PROIBIDAS

`test_portao_tier_p1a35._RUNNERS` e uma tupla de DOIS runners escrita a
mao. MEDIDO nesta missao: `revisao_p1a36.py` implementa o MESMO portao
(`_verificar_tier`, linha 95) e **nunca entrou naquela tupla** — o
portao do runner mais recente nao era exercido por ninguem. E o
mecanismo dos achados 7, 10 e 14 outra vez, e o mesmo defeito vivo 2 da
P1-A.3.8 (lista de constante que nada prende) aplicado a um corpus de
teste.

Aqui o corpus e DESCOBERTO por AST: todo runner de `06_p1a/evidencias`
que define `_verificar_tier` entra sozinho, e runner sem prova reprova
com o proprio nome.

## ZERO CHAMADA — o que exatamente se conta

Duas contagens independentes, porque uma so nao basta:

1. o construtor de argv de `COMANDOS[provider]` — se ele nao rodou, nem
   o comando chegou a ser montado;
2. `subprocess.run` — o ponto onde a chamada de fato sairia.

Com declaracao vencida as duas precisam ficar em ZERO. Com declaracao
valida as duas precisam ser exercidas: sem essa contraprova um portao
que parasse SEMPRE passaria em tudo acima, e a corrida nunca aconteceria.

## O QUE ESTES TESTES NAO COBREM, declarado

- **nenhum CLI real e invocado, nem quando a declaracao e valida**:
  `subprocess.run` esta trocado por um espiao. O que se prova e a ORDEM
  (portao antes da chamada), nunca o comportamento do provedor;
- nao se prova nada sobre a corretude do relogio nem sobre fuso: as
  declaracoes sao montadas com deslocamento explicito em horas sobre
  `datetime.now(timezone.utc)`;
- nao se afirma que o tier declarado seja VERDADEIRO — o portao confere
  validade e declarante, jamais o plano real na conta do provedor. Essa
  e a mesma limitacao ja declarada na emenda P1-A.3 item 1;
- a prova nao cobre o portao de LOCK, que roda antes do de tier: um
  lease morto para a corrida ainda mais cedo, e isso e objeto de
  `test_p1b_lease_p1a35` e `test_persistencia_lock_p1a37`.
"""

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)
_DIR_EVID = os.path.join(_DIR_P1A, "evidencias")
sys.path.insert(0, _DIR_EVID)

import contencao  # noqa: E402

# Runner -> sessao de lock que ele exige viva ANTES do portao de tier.
RUNNERS_COM_PORTAO = {
    "revisao_p1a31": "p1a31-ops",
    "revisao_p1a33": "p1a33-ops",
    "revisao_p1a36": "p1a36-ops",
}


def _runners_com_portao_na_arvore() -> set:
    """Todo runner de evidencias que DEFINE `_verificar_tier` — por AST."""
    achados = set()
    for nome in sorted(os.listdir(_DIR_EVID)):
        if not nome.startswith("revisao_") or not nome.endswith(".py"):
            continue
        with open(os.path.join(_DIR_EVID, nome), encoding="utf-8") as f:
            try:
                arvore = ast.parse(f.read())
            except SyntaxError:
                continue
        if any(isinstance(no, ast.FunctionDef) and no.name == "_verificar_tier"
               for no in ast.walk(arvore)):
            achados.add(nome[:-3])
    return achados


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


class _Espiao:
    """Conta invocacoes e devolve uma corrida falsa bem-sucedida."""

    def __init__(self):
        self.n = 0

    def __call__(self, *a, **k):
        self.n += 1
        return subprocess.CompletedProcess(args=["falso"], returncode=0,
                                           stdout="revisao falsa", stderr="")


def _utc(delta_horas: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=delta_horas)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")


def _carregar(nome: str):
    caminho = os.path.join(_DIR_EVID, f"{nome}.py")
    spec = importlib.util.spec_from_file_location(f"p1a39_tier_{nome}",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _env_minimo() -> dict:
    return {k: os.environ[k] for k in
            ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC", "PATHEXT")
            if k in os.environ}


class PortaoDeTierParaAntesDaChamada(unittest.TestCase):
    """`main()` REAL; o que se mede sao as invocacoes que NAO aconteceram."""

    def _corrida(self, nome: str, declaracoes, teto=24):
        """Roda `main()` e devolve (excecao|None, argv_montados, subprocessos).

        Nada aqui e simulado alem do provedor: o lease e real em disco, a
        declaracao de tier e um JSON real, o argv sai do `COMANDOS` do
        proprio runner.
        """
        espec_sessao = RUNNERS_COM_PORTAO[nome]
        contagem = {"argv": 0}
        espiao = _Espiao()
        with tempfile.TemporaryDirectory(prefix="p1a39-tier-") as bruto:
            raiz = Path(bruto)
            locks = raiz / "locks"
            locks.mkdir(parents=True)
            (locks / f"{espec_sessao}.lease").write_text(
                json.dumps({"sessao": espec_sessao, "pid": os.getpid(),
                            "token": 5, "renovado_em": time.time(),
                            "expira_em": time.time() + 600}),
                encoding="utf-8")
            (locks / f"{espec_sessao}.fence").write_text("5", encoding="ascii")
            destino = raiz / "06_p1a"
            destino.mkdir(parents=True, exist_ok=True)
            (destino / "tiers_declarados.json").write_text(
                json.dumps({"validade_maxima_horas": teto,
                            "declaracoes": declaracoes}), encoding="utf-8")
            pacote = raiz / "pacote.txt"
            pacote.write_bytes(b"pacote de prova")
            saida = raiz / "saida"
            modulo = _carregar(nome)

            def montar_argv(*a):
                contagem["argv"] += 1
                return [sys.executable, "-c", "pass"]

            erro = None
            with mock.patch.object(modulo, "RAIZ", raiz), \
                    mock.patch.object(modulo, "SAIDA", saida), \
                    mock.patch.object(modulo, "COMANDOS",
                                      {"kimi": montar_argv}), \
                    mock.patch.object(
                        contencao, "ALVOS_VIGIADOS_FORA_DO_REPOSITORIO",
                        ()), \
                    mock.patch.object(subprocess, "run", espiao), \
                    mock.patch.dict(os.environ, _env_minimo(), clear=True), \
                    mock.patch.object(sys, "argv",
                                      ["runner.py", "kimi", str(pacote)]), \
                    mock.patch("sys.stdout", _SaidaMuda()):
                try:
                    modulo.main()
                except SystemExit as exc:
                    erro = exc
            gravados = (sorted(p for p in saida.iterdir() if p.is_file())
                        if saida.is_dir() else [])
            self._evidencia = (gravados[0].read_text(encoding="utf-8")
                               if gravados else None)
            return erro, contagem["argv"], espiao.n

    def _valida(self):
        return [{"provider_id": "kimi", "tier": "allegretto",
                 "declarado_por": "proprietario",
                 "declarado_em_utc": _utc(-1), "validade_horas": 24}]

    def test_declaracao_vencida_para_a_corrida_sem_gastar_chamada(self):
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                erro, argv, subprocessos = self._corrida(nome, [{
                    "provider_id": "kimi", "tier": "allegretto",
                    "declarado_por": "proprietario",
                    "declarado_em_utc": _utc(-30), "validade_horas": 24}])
                self.assertIsNotNone(erro, f"{nome}: main() NAO parou")
                self.assertIn("EXPIRADO", str(erro))
                self.assertEqual(argv, 0, f"{nome}: argv do reviewer montado")
                self.assertEqual(subprocessos, 0,
                                 f"{nome}: reviewer INVOCADO com tier "
                                 "vencido — a chamada foi gasta")

    def test_sem_declaracao_para_o_provider_nao_gasta_chamada(self):
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                erro, argv, subprocessos = self._corrida(nome, [{
                    "provider_id": "codex", "tier": "chatgpt pro 5x",
                    "declarado_por": "proprietario",
                    "declarado_em_utc": _utc(-1), "validade_horas": 24}])
                self.assertIsNotNone(erro)
                self.assertIn("sem declaracao de tier", str(erro))
                self.assertEqual((argv, subprocessos), (0, 0))

    def test_o_teto_vence_validade_maior_declarada_sem_gastar_chamada(self):
        # A propriedade mais fragil do portao: `validade_horas: 999` nao
        # pode sobreviver ao teto de 24 h. Aqui ela e exercida NO
        # CAMINHO DA OPERACAO, e nao chamando a funcao a seco.
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                erro, argv, subprocessos = self._corrida(nome, [{
                    "provider_id": "kimi", "tier": "allegretto",
                    "declarado_por": "proprietario",
                    "declarado_em_utc": _utc(-30), "validade_horas": 999}],
                    teto=24)
                self.assertIsNotNone(erro)
                self.assertIn("EXPIRADO", str(erro))
                self.assertEqual((argv, subprocessos), (0, 0))

    def test_a_fronteira_exata_do_vencimento_ja_esta_fora(self):
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                erro, argv, subprocessos = self._corrida(nome, [{
                    "provider_id": "kimi", "tier": "allegretto",
                    "declarado_por": "proprietario",
                    "declarado_em_utc": _utc(-24), "validade_horas": 24}],
                    teto=24)
                self.assertIsNotNone(erro)
                self.assertIn("EXPIRADO", str(erro))
                self.assertEqual((argv, subprocessos), (0, 0))

    def test_declaracao_valida_deixa_a_corrida_chegar_ao_reviewer(self):
        # CONTRAPROVA. Sem ela um portao que parasse SEMPRE passaria nos
        # quatro testes acima, e "zero chamada" seria trivialmente
        # verdadeiro porque nenhuma corrida jamais aconteceria.
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                erro, argv, subprocessos = self._corrida(nome, self._valida())
                self.assertIsNone(erro, f"{nome}: parou com tier VALIDO")
                self.assertEqual(argv, 1)
                self.assertEqual(subprocessos, 1)

    def test_a_evidencia_gravada_registra_o_tier_do_instante(self):
        # O portao nao e so recusa: quando passa, ele GRAVA o que passou.
        # Sem isto, um `_verificar_tier` que devolvesse `{}` seria
        # indistinguivel de um que verificou.
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                erro, _, _ = self._corrida(nome, self._valida())
                self.assertIsNone(erro)
                self.assertIsNotNone(self._evidencia,
                                     f"{nome}: nada foi gravado")
                tier = json.loads(
                    self._evidencia)["tier_declarado_no_instante"]
                self.assertEqual(tier["provider_id"], "kimi")
                self.assertEqual(tier["declarado_por"], "proprietario")
                self.assertTrue(tier["valido_no_instante"])
                self.assertIn("expira_em_utc", tier)

    def test_nada_e_gravado_quando_o_portao_para(self):
        # A outra ponta: parada de tier nao pode deixar evidencia
        # parcial no disco — um arquivo gravado diria que a corrida
        # aconteceu.
        for nome in sorted(RUNNERS_COM_PORTAO):
            with self.subTest(runner=nome):
                self._corrida(nome, [{
                    "provider_id": "kimi", "tier": "allegretto",
                    "declarado_por": "proprietario",
                    "declarado_em_utc": _utc(-30), "validade_horas": 24}])
                self.assertIsNone(self._evidencia)


class OCorpusDeRunnersEDescoberto(unittest.TestCase):
    """Prende o corpus a arvore — `revisao_p1a36` ficou fora de _RUNNERS."""

    def test_todo_runner_com_portao_de_tier_e_exercido_por_main(self):
        na_arvore = _runners_com_portao_na_arvore()
        faltando = sorted(na_arvore - set(RUNNERS_COM_PORTAO))
        self.assertEqual(
            faltando, [],
            f"runner com _verificar_tier sem prova no caminho da "
            f"operacao: {faltando}. Foi assim que revisao_p1a36 ficou "
            "fora de test_portao_tier_p1a35._RUNNERS")

    def test_nenhum_runner_registrado_sumiu_da_arvore(self):
        self.assertEqual(
            sorted(set(RUNNERS_COM_PORTAO) - _runners_com_portao_na_arvore()),
            [])

    def test_a_descoberta_tem_alcance_real(self):
        self.assertGreaterEqual(len(_runners_com_portao_na_arvore()), 3)

    def test_o_detector_nao_confunde_chamada_com_definicao(self):
        # CONTROLE POSITIVO: um runner que apenas CHAMASSE _verificar_tier
        # sem defini-lo nao implementa o portao, e um detector que os
        # confundisse incharia o corpus com nomes que nao tem guarda.
        def tem(fonte):
            arvore = ast.parse(fonte)
            return any(isinstance(no, ast.FunctionDef)
                       and no.name == "_verificar_tier"
                       for no in ast.walk(arvore))
        self.assertTrue(tem("def _verificar_tier(p):\n    return {}\n"))
        self.assertFalse(tem("def main():\n    _verificar_tier('kimi')\n"))


if __name__ == "__main__":
    unittest.main()
