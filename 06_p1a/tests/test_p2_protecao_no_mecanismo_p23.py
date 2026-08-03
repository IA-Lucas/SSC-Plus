"""A protecao sai do texto e entra no mecanismo — SSC+ P2.3 (achado A).

O achado A (`08_p2/99_achados-divergencias-20260803.md`) mediu que NADA
impedia escrita: o SSC+ nao passava restricao de filesystem ao CLI, nao
trocava o diretorio de trabalho, nao vigiava a arvore durante a corrida e
gravava `efeito_externo: "nenhum"` **por declaracao**, sem olhar o disco.
Esta suite exerce as quatro correcoes, e cada classe abaixo responde a
pergunta que a REGRA DE PROVA obriga — *o teste exerce o caminho que a
operacao percorre, ou um vizinho?*

O CAMINHO QUE A OPERACAO PERCORRE, sem gastar franquia:

- o argv sob teste e o que `ProvedorAssinaturaReal.argv` monta, nunca um
  argv que o teste desenhe (a licao da P1-A.3.4: `argv_kimi` correto com
  chamador errado continua quebrado);
- o `cwd` e provado com SUBPROCESSO DE VERDADE, escrevendo em CAMINHO
  RELATIVO — que e a forma pela qual um filho cai na raiz do repositorio.
  Um teste que so olhasse o argumento passado a `subprocess.run` mediria
  a fiacao, e nao o efeito;
- a `Vigilancia` e provada DISPARANDO sobre escrita plantada, nunca por
  estar importada;
- o CLI real do codex e exercido em `CliRealDoCodex`, com `CODEX_HOME` e
  `HOME` isolados: cada invocacao morre em **401 Unauthorized**, sem
  credencial alcancavel e portanto sem franquia gasta. E a mesma excecao
  declarada que a P1-A.3.4 abriu para o kimi, pela mesma razao — afirmar
  o que uma interface externa aceita nao e medi-la.

O QUE ESTA SUITE NAO COBRE, declarado:

- **o que o `--sandbox read-only` FAZ dentro do turno do modelo.** Aqui
  se mede que o CLI aceita a flag e ecoa `sandbox: read-only` no proprio
  cabecalho; que ele recuse uma escrita pedida pelo modelo e propriedade
  do CLI externo e exigiria invocacao com credencial — **NAO MEDIDO**;
- **as nove corridas anteriores.** Rodaram sem fotografia de antes e
  depois. Nenhum teste daqui diz o que elas fizeram, e nada aqui autoriza
  afirmar que o passado esta limpo;
- **config do codex fora deste repositorio.** Os testes de CLI real usam
  `CODEX_HOME` isolado justamente para nao depender dela; o efeito da
  config real do usuario sobre `exec` segue **NAO MEDIDO**;
- **efeito do outro lado da rede.** A medicao e de DISCO, dentro das
  raizes vigiadas. Escrita que o provedor faca no proprio servico nao
  aparece em nenhuma fotografia local.
"""

import dataclasses
import json
import os
import shutil
import subprocess
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

import caminhos  # noqa: E402
import contencao  # noqa: E402
import provedor_assinatura as pa  # noqa: E402
import runner_p2  # noqa: E402
from preflight.frota_real import (MARCA_DESCARTAVEL,  # noqa: E402
                                  espec_de, rotulo_restricao)
from test_p2_runner_p2 import (SensorObrigatorio,  # noqa: E402
                               preflight_real)

_FLAGS_ESPERADAS_CODEX = ("--sandbox", "read-only", "--cd",
                          "--skip-git-repo-check", "--ephemeral")


class SensorQueEscreve:
    """Sensor falso que ESCREVE onde mandarem, e devolve sucesso.

    E o instrumento da prova (c): recibo que nao pega escrita plantada nao
    mede nada. Ele planta no diretorio que recebe — o descartavel do
    filho, quando `alvo=None`, ou um caminho fixo fora dele.
    """

    def __init__(self, alvo=None, nome="escrita-plantada.txt", rc=0,
                 out="ok", err=""):
        self.alvo = alvo
        self.nome = nome
        self.resposta = (rc, out, err)
        self.chamadas = []

    def __call__(self, argv, env=None, timeout=None, cwd=None):
        self.chamadas.append({"argv": list(argv), "cwd": cwd})
        destino = self.alvo or cwd
        with open(os.path.join(destino, self.nome), "w",
                  encoding="utf-8") as f:
            f.write("escrita do filho")
        return self.resposta


def vigia_de(raiz):
    return contencao.Vigilancia(raiz, "sessao-de-teste", alvos=())


class RestricaoNoArgv(unittest.TestCase):
    """ORDEM 1 — o argv que a operacao monta carrega a restricao."""

    def argv_de_producao(self, provider_id="codex"):
        """O argv como o EXECUTOR o monta, com o descartavel dele.

        Passa por `invocar`, e nao por `argv`, para que a fiacao entre no
        escopo: montador certo com chamador que nao o usa continuaria
        montando `codex exec <tarefa>` como antes do achado A.
        """
        tmp = tempfile.mkdtemp(prefix="p23-vigiado-")
        self.addCleanup(shutil.rmtree, tmp, True)
        sensor = SensorObrigatorio(**{provider_id: (0, "ok", "")})
        p = pa.ProvedorAssinaturaReal(espec_de(provider_id), sensor=sensor,
                                      vigia=vigia_de(tmp))
        p.invocar(b"a tarefa")
        return sensor.chamadas[0]["argv"], sensor.chamadas[0]["cwd"], p

    def test_o_codex_recebe_as_QUATRO_restricoes_antes_do_prompt(self):
        # `codex exec` toma o prompt como POSICIONAL: flag depois dele
        # seria parte do prompt. Por isso a posicao entra na assercao.
        argv, _, _ = self.argv_de_producao()
        for flag in _FLAGS_ESPERADAS_CODEX:
            with self.subTest(flag=flag):
                self.assertIn(flag, argv, f"{flag} ausente do argv de "
                                          "producao: a protecao voltou a "
                                          "viver so no texto")
                self.assertLess(argv.index(flag), argv.index("a tarefa"),
                                f"{flag} depois do prompt vira parte dele")
        self.assertEqual(argv[-1], "a tarefa")

    def test_o_valor_de_cd_e_o_cwd_do_filho_e_o_diretorio_EXISTE(self):
        # As duas metades juntas: `--cd` diz ao AGENTE onde trabalhar,
        # `cwd` diz ao PROCESSO. Divergir seria restringir um e nao o
        # outro; apontar para diretorio inexistente seria restringir
        # nenhum, porque o CLI morre antes de comecar.
        argv, cwd, _ = self.argv_de_producao()
        valor_cd = argv[argv.index("--cd") + 1]
        self.assertEqual(valor_cd, cwd)
        self.assertTrue(os.path.isdir(cwd), f"descartavel inexistente: {cwd}")
        self.assertNotEqual(os.path.abspath(cwd),
                            os.path.abspath(caminhos.RAIZ))

    def test_o_marcador_nao_sobrevive_a_montagem(self):
        # O marcador e da especificacao estatica. Chegar ao CLI significa
        # que a troca pelo descartavel nao aconteceu.
        argv, _, _ = self.argv_de_producao()
        self.assertNotIn(MARCA_DESCARTAVEL, argv)

    def test_cada_invocacao_tem_o_SEU_descartavel(self):
        # Reaproveitar o diretorio faria a fotografia da segunda chamada
        # herdar o que a primeira deixou — e a medicao do efeito passaria
        # a acusar a corrida anterior.
        _, cwd1, p = self.argv_de_producao()
        p.invocar(b"outra tarefa")
        self.assertNotEqual(p.medicoes[0]["dir_descartavel"],
                            p.medicoes[1]["dir_descartavel"])
        self.assertEqual(p.medicoes[0]["dir_descartavel"], cwd1)

    def test_o_kimi_nao_ganha_flag_que_o_CLI_nao_tem(self):
        # Medido na P1-A.3.4: `--sandbox` e `unknown option` no kimi.
        # Emitir a flag nao restringiria a corrida — a IMPEDIRIA.
        argv, cwd, _ = self.argv_de_producao("kimi")
        self.assertEqual(argv[1:], ["-p", "a tarefa"])
        # O que o kimi TEM continua valendo: o filho corre no descartavel.
        self.assertTrue(os.path.isdir(cwd))
        self.assertNotEqual(os.path.abspath(cwd),
                            os.path.abspath(caminhos.RAIZ))


class RotuloConstruidoPeloMecanismo(unittest.TestCase):
    """ORDEM 1 — o rotulo nao pode exceder o mecanismo (achado N3)."""

    def test_o_rotulo_do_kimi_NAO_afirma_sandbox(self):
        rotulo = rotulo_restricao(espec_de("kimi")).lower()
        for palavra in ("sandbox", "read-only", "somente leitura", "isolad"):
            with self.subTest(palavra=palavra):
                self.assertNotIn(palavra, rotulo,
                                 "o rotulo afirma restricao que o CLI do "
                                 "kimi nao oferece — MAJOR #3 na forma "
                                 "literal")

    def test_o_rotulo_do_codex_cita_as_flags_QUE_SERAO_EMITIDAS(self):
        rotulo = rotulo_restricao(espec_de("codex"))
        for flag in _FLAGS_ESPERADAS_CODEX:
            with self.subTest(flag=flag):
                self.assertIn(flag, rotulo)

    def test_tirar_a_flag_do_mecanismo_TIRA_do_rotulo(self):
        # A prova de que o rotulo e construido, e nao escrito: uma
        # especificacao sem a flag produz um rotulo sem a flag, sem que
        # ninguem reescreva frase nenhuma.
        sem_sandbox = dataclasses.replace(
            espec_de("codex"),
            restricao_headless=("--cd", MARCA_DESCARTAVEL, "--ephemeral"))
        rotulo = rotulo_restricao(sem_sandbox)
        self.assertNotIn("--sandbox", rotulo)
        self.assertIn("--ephemeral", rotulo)

    def test_restricao_vazia_diz_por_extenso_que_nao_ha_restricao(self):
        vazia = dataclasses.replace(espec_de("codex"), restricao_headless=())
        self.assertIn("NAO oferece restricao de filesystem",
                      rotulo_restricao(vazia))


class DiretorioDeTrabalhoDoFilho(unittest.TestCase):
    """ORDEM 3 (a) — o caso que OCORRE: caminho RELATIVO escrito pelo filho.

    Esta e a forma pela qual uma escrita cai sobre o acervo, e por isso e
    a forma exercida aqui. O vizinho recusado: afirmar que
    `subprocess.run` recebeu `cwd=...`. Isso mede a fiacao, nao o destino
    do byte — e o destino do byte e o achado.

    Subprocesso REAL, com o interpretador local no lugar do CLI: zero
    chamada de modelo, zero franquia.
    """

    NOME = "PROVA-P23-ESCRITA-RELATIVA.txt"

    def setUp(self):
        self.vigiado = tempfile.mkdtemp(prefix="p23-vigiado-")
        self.addCleanup(shutil.rmtree, self.vigiado, True)
        # Se a restricao for revertida, o arquivo nasce na raiz do
        # repositorio: o proprio teste limpa o que o mutante criar.
        self.na_raiz = os.path.join(caminhos.RAIZ, self.NOME)
        self.addCleanup(lambda: os.path.exists(self.na_raiz)
                        and os.remove(self.na_raiz))

    def espec_python(self):
        return dataclasses.replace(espec_de("codex"),
                                   executavel=sys.executable,
                                   headless=("-c",), restricao_headless=())

    def test_escrita_relativa_do_filho_NAO_cai_na_raiz_do_repositorio(self):
        p = pa.ProvedorAssinaturaReal(self.espec_python(),
                                      vigia=vigia_de(self.vigiado))
        r = p.invocar(f"open({self.NOME!r}, 'w').write('do filho')"
                      .encode("utf-8"))
        self.assertTrue(r.ok, r.saida)

        self.assertFalse(
            os.path.exists(self.na_raiz),
            "o filho escreveu na RAIZ DO REPOSITORIO: e o achado A, e o "
            "alvo pode ser `locks/`, o fonte dos guardas ou a evidencia")
        descartavel = p.medicoes[0]["dir_descartavel"]
        self.assertTrue(os.path.exists(os.path.join(descartavel, self.NOME)),
                        "a escrita nao caiu no descartavel: ou o filho nao "
                        "escreveu, ou escreveu em lugar nao medido")

    def test_o_filho_confirma_o_proprio_cwd(self):
        # Contraprova direta, pela boca do filho: ele imprime onde esta.
        p = pa.ProvedorAssinaturaReal(self.espec_python(),
                                      vigia=vigia_de(self.vigiado))
        r = p.invocar(b"import os;print(os.getcwd())")
        self.assertTrue(r.ok, r.saida)
        visto = r.saida.decode("utf-8").strip()
        self.assertEqual(os.path.realpath(visto),
                         os.path.realpath(p.medicoes[0]["dir_descartavel"]))
        self.assertNotEqual(os.path.realpath(visto),
                            os.path.realpath(caminhos.RAIZ))


class CapsulaDefineOCwd(unittest.TestCase):
    """ORDEM 1 — o primeiro dos dois elos que herdavam o diretorio.

    Exercita o ENTRY POINT de verdade (`python 06_p1a/capsula.py ...`),
    lancado de um diretorio que nao e a raiz. Se o `cwd` voltar a ser
    herdado, o filho responde o diretorio de onde o teste o chamou.
    """

    def test_o_filho_da_capsula_corre_na_raiz_do_repositorio(self):
        fora = tempfile.mkdtemp(prefix="p23-fora-")
        self.addCleanup(shutil.rmtree, fora, True)
        proc = subprocess.run(
            [sys.executable, os.path.join(caminhos.RAIZ, "06_p1a",
                                          "capsula.py"),
             sys.executable, "-c", "import os;print(os.getcwd())"],
            cwd=fora, capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(os.path.realpath(proc.stdout.strip()),
                         os.path.realpath(caminhos.RAIZ))
        self.assertNotEqual(os.path.realpath(proc.stdout.strip()),
                            os.path.realpath(fora))


class EfeitoExternoMedido(unittest.TestCase):
    """ORDEM 2 e ORDEM 3 (c) — o recibo mede, e nao repete o envelope."""

    def setUp(self):
        self.vigiado = tempfile.mkdtemp(prefix="p23-vigiado-")
        self.addCleanup(shutil.rmtree, self.vigiado, True)

    def provedor(self, sensor):
        return pa.ProvedorAssinaturaReal(espec_de("codex"), sensor=sensor,
                                         vigia=vigia_de(self.vigiado))

    def test_classificar_EXIGE_a_medicao(self):
        # O guarda contra a volta do defeito por omissao: sem terceiro
        # argumento nao ha `nenhum` — ha TypeError. Um default aqui seria
        # o proprio achado A de novo, calado.
        with self.assertRaises(TypeError):
            pa.classificar(0, "tudo certo")

    def test_sem_mutacao_o_nenhum_passa_a_ser_MEDICAO(self):
        p = self.provedor(SensorObrigatorio(codex=(0, "ok", "")))
        r = p.invocar(b"t")
        self.assertEqual(r.efeito_externo, "nenhum")
        medicao = p.medicoes[0]
        self.assertEqual(medicao["mutacoes_no_descartavel"], [])
        self.assertEqual(medicao["mutacoes_fora_do_descartavel"], [])
        self.assertIn("fotografia", medicao["efeito_externo_origem"])
        self.assertIn("SHA-256", medicao["medida"])

    def test_escrita_plantada_no_descartavel_e_REGISTRADA_no_recibo(self):
        # Prova (c). Recibo que nao pega escrita plantada nao mede nada.
        sensor = SensorQueEscreve()
        p = self.provedor(sensor)
        r = p.invocar(b"t")
        medicao = p.medicoes[0]
        self.assertEqual(medicao["mutacoes_no_descartavel"],
                         ["criado: escrita-plantada.txt"])
        self.assertEqual(r.efeito_externo, "aplicado",
                         "houve escrita e o recibo disse `nenhum`: e o "
                         "registro confirmando a suposicao que o produziu")

    def test_escrita_plantada_FORA_do_descartavel_e_REGISTRADA(self):
        # A outra metade: a fotografia do descartavel nao ve o que cai
        # fora dele — foi por isso que a P1-A.3.2 precisou da Vigilancia.
        sensor = SensorQueEscreve(alvo=self.vigiado, nome="intrusa.txt")
        p = self.provedor(sensor)
        r = p.invocar(b"t")
        medicao = p.medicoes[0]
        self.assertEqual(medicao["mutacoes_no_descartavel"], [])
        self.assertTrue(
            any("intrusa.txt" in m
                for m in medicao["mutacoes_fora_do_descartavel"]),
            f"escrita fora do descartavel nao apareceu: {medicao}")
        self.assertEqual(r.efeito_externo, "aplicado")

    def test_falha_com_escrita_medida_nao_vira_nao_aplicado(self):
        # Fail-closed no outro sentido: uma falha transitoria devolve
        # `nao-aplicado`, que AUTORIZA retry (IR-1). Se o disco mostrou
        # escrita, chamar de nao-aplicado seria autorizar retry sobre
        # efeito que ja ocorreu.
        sensor = SensorQueEscreve(rc=1, out="", err="503 service unavailable")
        r = self.provedor(sensor).invocar(b"t")
        self.assertEqual(r.falha, "falha-transitoria")
        self.assertEqual(r.efeito_externo, "aplicado")

    def test_timeout_continua_incerto_mesmo_sem_mutacao_no_disco(self):
        # A medicao e de DISCO. O timeout fala do lado REMOTO, que
        # nenhuma fotografia local decide — e `incerto` e o que proibe o
        # retry automatico (IR-2).
        self.assertEqual(pa.classificar(pa.RC_TIMEOUT, "", []),
                         ("indeterminado", "incerto"))
        self.assertEqual(pa.classificar(pa.RC_TIMEOUT, "", ["criado: x"]),
                         ("indeterminado", "incerto"))


class VigilanciaDispara(unittest.TestCase):
    """ORDEM 3 (d) — nao basta estar importada."""

    def test_a_vigilancia_dispara_sobre_escrita_na_arvore_vigiada(self):
        vigiado = tempfile.mkdtemp(prefix="p23-vigiado-")
        self.addCleanup(shutil.rmtree, vigiado, True)
        sensor = SensorQueEscreve(alvo=vigiado, nome="disparo.txt")
        p = pa.ProvedorAssinaturaReal(espec_de("codex"), sensor=sensor,
                                      vigia=vigia_de(vigiado))
        p.invocar(b"t")
        medicao = p.medicoes[0]
        self.assertTrue(medicao["mutacoes_fora_do_descartavel"],
                        "a Vigilancia nao acusou escrita na arvore que ela "
                        "declara vigiar")
        self.assertIn("raizes_vigiadas", medicao)
        self.assertIn("nao_vigiado", medicao)

    def test_sem_injecao_a_vigilancia_e_a_REAL_sobre_este_repositorio(self):
        # O default de operacao. A suite injeta uma vigilancia estreita
        # por custo; sem este teste, a injecao seria o interruptor que
        # apaga o mecanismo em producao sem ninguem ver.
        p = pa.ProvedorAssinaturaReal(espec_de("codex"),
                                      sensor=SensorObrigatorio(
                                          codex=(0, "ok", "")))
        p.invocar(b"t")
        medicao = p.medicoes[0]
        self.assertGreater(
            medicao["arquivos_no_manifesto_vigiado"], 300,
            "a vigilancia default nao fotografou a arvore do repositorio")
        raizes = " ".join(medicao["raizes_vigiadas"])
        self.assertIn("repositorio", raizes)
        for fonte in contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO:
            with self.subTest(fonte=fonte):
                self.assertIn(fonte, raizes)

    def test_o_lease_do_renovador_e_ATRIBUIDO_e_nao_vira_efeito(self):
        # Separacao entre deteccao e atribuicao (P1-A.3.6 §6): o lease da
        # sessao operacional tem escritor esperado por construcao. Conta-lo
        # como efeito do provedor faria toda corrida longa parecer escrita
        # externa, e o recibo perderia o poder de acusar a de verdade.
        vigiado = tempfile.mkdtemp(prefix="p23-vigiado-")
        self.addCleanup(shutil.rmtree, vigiado, True)
        locks = os.path.join(vigiado, "locks")
        os.makedirs(locks)
        sensor = SensorQueEscreve(alvo=locks, nome="sessao-de-teste.lease")
        p = pa.ProvedorAssinaturaReal(espec_de("codex"), sensor=sensor,
                                      vigia=vigia_de(vigiado))
        r = p.invocar(b"t")
        medicao = p.medicoes[0]
        self.assertTrue(medicao["mutacoes_atribuidas_ao_renovador"])
        self.assertEqual(medicao["mutacoes_fora_do_descartavel"], [])
        self.assertEqual(r.efeito_externo, "nenhum")


class ReciboDaCorridaCarregaAMedicao(unittest.TestCase):
    """ORDEM 2 — a medicao chega ao registro que o revisor vai ler."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p23-recibo-")
        self.addCleanup(self._tmp.cleanup)
        self.vigiado = os.path.join(self._tmp.name, "vigiado")
        os.makedirs(self.vigiado)

    def corrida(self, sensor):
        return runner_p2.executar(
            tarefa="responda pronto", criterio="resposta nao vazia",
            preflight=preflight_real(),
            raiz_lab=os.path.join(self._tmp.name, "lab"),
            sensor=sensor, vigia=vigia_de(self.vigiado))

    def test_o_registro_traz_uma_medicao_por_invocacao(self):
        r = self.corrida(SensorObrigatorio(codex=(0, "pronto", "")))
        self.assertEqual(r["status"], "sucesso", r.get("detalhe"))
        medicoes = r["efeito_externo_medido"]
        self.assertEqual(len(medicoes), 1)
        self.assertEqual(medicoes[0]["provider_id"], "codex")
        self.assertEqual(medicoes[0]["efeito_externo"], "nenhum")
        self.assertIn("--sandbox", medicoes[0]["argv_publico"])
        self.assertEqual(r["attempts"][0]["efeito_externo"], "nenhum")

    def test_o_prompt_do_usuario_NAO_vai_no_argv_publico(self):
        # O argv entra no recibo; a tarefa e do usuario. `<PROMPT>` no
        # lugar dela e a mesma regra de `prova_minima.py:101`.
        r = self.corrida(SensorObrigatorio(codex=(0, "pronto", "")))
        publico = r["efeito_externo_medido"][0]["argv_publico"]
        self.assertIn("<PROMPT>", publico)
        self.assertNotIn("responda pronto", publico)

    def test_o_fallback_produz_DUAS_medicoes_na_ordem_das_invocacoes(self):
        # Quota no codex leva a tarefa ao kimi: duas invocacoes, duas
        # medicoes, cada uma com o seu descartavel.
        r = self.corrida(SensorObrigatorio(
            codex=(1, "", "0 requests remaining"), kimi=(0, "pronto", "")))
        medicoes = r["efeito_externo_medido"]
        self.assertEqual([m["provider_id"] for m in medicoes],
                         ["codex", "kimi"])
        self.assertNotEqual(medicoes[0]["dir_descartavel"],
                            medicoes[1]["dir_descartavel"])

    def test_a_medicao_sobrevive_a_serializacao_do_recibo(self):
        # O recibo e gravado como JSON redigido; medicao que nao
        # serializa nao chega a revisor nenhum.
        r = self.corrida(SensorObrigatorio(codex=(0, "pronto", "")))
        texto = contencao.redigir(json.dumps(r["efeito_externo_medido"],
                                             ensure_ascii=False))
        de_volta = json.loads(texto)
        self.assertEqual(de_volta[0]["efeito_externo"], "nenhum")
        self.assertNotIn(contencao.forma_8_3(
            os.path.basename(os.path.expanduser("~"))), texto)


def _codex_exe() -> str:
    """O MESMO executavel que o executor de producao invoca."""
    return os.path.expanduser(espec_de("codex").executavel)


def _codex_disponivel() -> bool:
    return os.path.isfile(_codex_exe())


@unittest.skipUnless(_codex_disponivel(),
                     f"CLI do codex ausente em {_codex_exe()} — sem CLI "
                     "real esta propriedade NAO e verificavel, e o skip "
                     "existe para dizer isso alto, nunca para dar a suite "
                     "por verde")
class CliRealDoCodex(unittest.TestCase):
    """ORDEM 3 (a) — a restricao exercida contra o CLI de verdade.

    EXCECAO DECLARADA a regra de `apoio.py`, a segunda do acervo e pela
    mesma razao da primeira (P1-A.3.4): afirmar que um CLI aceita um argv
    nao e medi-lo. O custo continua ZERO por construcao, verificado
    dentro do proprio teste:

    1. `CODEX_HOME`, `HOME` e `USERPROFILE` apontam para diretorios
       temporarios VAZIOS: nenhuma credencial OAuth do usuario e
       alcancavel, e a config real do usuario nao e lida;
    2. o ambiente do filho e montado por ALLOWLIST — nenhuma variavel
       `OPENAI_*`/`CODEX_*` sobrevive, entao nao ha chave por onde
       autenticar;
    3. a invocacao morre em **401 Unauthorized** — asseverado. Um 401 e
       chamada RECUSADA: nao ha turno de modelo, nao ha franquia gasta.
    """

    _ENV_HERDAVEL = ("PATH", "SYSTEMROOT", "SystemRoot", "TEMP", "TMP",
                     "COMSPEC", "PATHEXT", "WINDIR", "NUMBER_OF_PROCESSORS",
                     "PROCESSOR_ARCHITECTURE")
    _TIMEOUT_S = 180

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p23-cli-real-")
        self.addCleanup(self._tmp.cleanup)
        self.lar = os.path.join(self._tmp.name, "lar-vazio")
        self.codex_home = os.path.join(self._tmp.name, "codex-home-vazio")
        self.descartavel = os.path.join(self._tmp.name, "descartavel")
        for d in (self.lar, self.codex_home, self.descartavel):
            os.makedirs(d)

    def _sem_credencial_alcancavel(self):
        self.assertEqual(os.listdir(self.lar), [])
        self.assertEqual(os.listdir(self.codex_home), [],
                         "CODEX_HOME do teste nao esta vazio: haveria "
                         "credencial alcancavel e risco de chamada real")

    def _rodar(self, argv):
        env = {k: os.environ[k] for k in self._ENV_HERDAVEL
               if k in os.environ}
        env.update({"HOME": self.lar, "USERPROFILE": self.lar,
                    "HOMEDRIVE": self.lar[:2], "HOMEPATH": self.lar[2:],
                    "CODEX_HOME": self.codex_home})
        proc = subprocess.run(argv, env=env, cwd=self.descartavel,
                              capture_output=True, text=True,
                              timeout=self._TIMEOUT_S,
                              stdin=subprocess.DEVNULL, encoding="utf-8",
                              errors="replace")
        return proc.returncode, (proc.stdout or ""), (proc.stderr or "")

    def _argv_de_producao(self):
        """O argv que o EXECUTOR monta, com o descartavel deste teste."""
        p = pa.ProvedorAssinaturaReal(espec_de("codex"))
        return p.argv("responda apenas PONG", self.descartavel)

    def test_o_cli_real_ACEITA_o_argv_de_producao_e_ecoa_a_restricao(self):
        # Prova positiva de aceitacao — e mais que isso: o proprio CLI
        # imprime `sandbox:` e `workdir:` no cabecalho, entao o que se
        # verifica nao e so que ele nao reclamou, e sim o modo em que ele
        # DIZ que entrou.
        self._sem_credencial_alcancavel()
        rc, out, err = self._rodar(self._argv_de_producao())
        saida = out + err
        baixa = saida.lower()

        self.assertNotIn("unexpected argument", baixa, saida[:400])
        self.assertNotIn("invalid value", baixa, saida[:400])
        self.assertIn("sandbox: read-only", baixa,
                      "o CLI nao entrou em read-only com o argv de "
                      f"producao: {saida[:600]!r}")
        self.assertIn(os.path.basename(self.descartavel), saida,
                      "o CLI nao adotou o descartavel como workdir")
        # Custo zero comprovado pela propria saida, nao prometido.
        self.assertIn("401", saida,
                      "a corrida passou do ponto de recusa por credencial: "
                      "pode ter havido chamada de modelo")
        self.assertNotEqual(rc, 0)

    def test_o_cli_real_VALIDA_o_valor_de_sandbox(self):
        # Contraprova de que a flag e real e o valor tambem: um valor
        # vizinho e recusado, e o proprio CLI enumera os aceitos. Sem
        # isto, `--sandbox read-only` poderia ser string ignorada.
        self._sem_credencial_alcancavel()
        argv = self._argv_de_producao()
        argv[argv.index("read-only")] = "read-onlyX"
        rc, out, err = self._rodar(argv)
        baixa = (out + err).lower()
        self.assertIn("invalid value 'read-onlyx'", baixa)
        self.assertIn("read-only", baixa)
        self.assertNotEqual(rc, 0)

    def test_flag_inexistente_e_recusada_ANTES_de_qualquer_trabalho(self):
        # A fronteira que separa "argv aceito" de "argv recusado", medida
        # aqui para que o teste de aceitacao acima possa falhar de fato.
        self._sem_credencial_alcancavel()
        argv = self._argv_de_producao()
        argv.insert(2, "--flag-que-nao-existe")
        rc, out, err = self._rodar(argv)
        baixa = (out + err).lower()
        self.assertIn("unexpected argument", baixa)
        self.assertNotIn("sandbox: read-only", baixa,
                         "recusa de argumento nao pode chegar ao cabecalho")
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
