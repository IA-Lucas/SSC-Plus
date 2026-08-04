"""A receita das medicoes, exercida — SSC+ P2.4 (achado C).

O achado C mediu: *"`08_p2/medidor.py` nao tem entrada de linha de
comando; os numeros da fronteira sairam de script de sessao ausente do
repositorio. O revisor recebe `medicao-p2*.json` e nao a receita."* E o
mesmo defeito do MAJOR #5 / N6 — pacote que pede julgamento e omite o
objeto julgado.

O QUE ESTA SUITE EXERCE, e o que ela recusa exercer:

- **o comando de verdade**, por `medidor.main(...)`, com as receitas
  versionadas e o codigo de saida que a operacao veria. O vizinho
  recusado seria chamar `reproduzir` direto e declarar o comando
  coberto: o achado C e sobre a AUSENCIA DO COMANDO, e um teste que
  pulasse o `main` mediria tudo menos o achado;
- **o controle positivo** (ORDEM 3): insumo trocado, numero diferente.
  Receita que devolve o mesmo numero com insumo diferente nao reproduz
  nada — mede constante. Os controles usam COPIAS em diretorio
  temporario: alterar arquivo do acervo para testar seria aplicar
  mutante sem necessidade, e o repositorio tem regra propria sobre isso;
- **a cobertura declarada**: quantos bytes foram RECONTADOS e quantos
  sao testemunho. Um relatorio que so dissesse "confere" esconderia que
  parte do "confere" e a testemunha se conferindo — familia (F).

O QUE ESTA SUITE NAO COBRE, declarado:

- **nao prova que os numeros publicados estao certos.** Prova que eles
  sao reproduziveis a partir dos insumos que o repositorio guarda. Insumo
  de testemunho — prompt de quatro das cinco corridas, resposta do canal
  alternativo em todas, resposta da assinatura na corrida (c) — nao se
  verifica sozinho, e a cobertura publica exatamente isso;
- **nao mede corrida com fallback.** As cinco publicadas tem uma
  tentativa so; o recibo carrega apenas a saida final, e a receita
  levanta em vez de sub-contar (ha teste);
- **nao roda provedor nenhum.** Zero chamada de modelo, zero franquia.
"""

import io
import json
import os
import shutil
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

import medidor  # noqa: E402

DIR_EVIDENCIAS = os.path.join(_RAIZ, "08_p2", "evidencias")


def receitas() -> list:
    return medidor.receitas_do_repositorio()


def ids_das_receitas() -> list:
    return [os.path.splitext(os.path.basename(c))[0] for c in receitas()]


class OComandoExiste(unittest.TestCase):
    """O objeto do achado C: `medidor.py` passa a ter linha de comando."""

    def test_todas_as_receitas_reproduzem_e_o_codigo_de_saida_e_zero(self):
        # O caminho que a operacao percorre: o comando inteiro, com as
        # receitas versionadas, exatamente como um revisor o roda.
        saida = io.StringIO()
        original, sys.stdout = sys.stdout, saida
        try:
            codigo = medidor.main(["--todas"])
        finally:
            sys.stdout = original
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn("0 divergente(s)", saida.getvalue())

    def test_uma_receita_por_id(self):
        saida = io.StringIO()
        original, sys.stdout = sys.stdout, saida
        try:
            codigo = medidor.main(["--receita", "p22-a"])
        finally:
            sys.stdout = original
        self.assertEqual(codigo, 0)
        self.assertIn("CONFERE", saida.getvalue())

    def test_divergencia_devolve_codigo_1_e_nao_passa_calada(self):
        # A receita nao existe para dizer "confere": existe para que a
        # divergencia apareca sozinha. Um comando que divergisse com
        # codigo 0 seria pior que nenhum comando — daria por conferido.
        tmp = tempfile.mkdtemp(prefix="p24-diverge-")
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(os.path.join(_RAIZ, "08_p2", "receitas", "p22-a.json"),
                  encoding="utf-8") as f:
            receita = json.load(f)
        # Insumo trocado por um arquivo de tamanho diferente.
        outro = os.path.join(tmp, "turno-diferente.txt")
        with open(outro, "w", encoding="utf-8") as f:
            f.write("x" * 999)
        receita["turno_interno"] = [{"origem": "arquivo", "caminho": outro}]
        caminho = os.path.join(tmp, "receita.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(receita, f)

        saida = io.StringIO()
        original, sys.stdout = sys.stdout, saida
        try:
            codigo = medidor.main(["--receita", caminho])
        finally:
            sys.stdout = original
        self.assertEqual(codigo, 1, saida.getvalue())
        self.assertIn("DIVERGE", saida.getvalue())

    def test_json_da_corrida_pode_ser_gravado_para_o_revisor(self):
        tmp = tempfile.mkdtemp(prefix="p24-json-")
        self.addCleanup(shutil.rmtree, tmp, True)
        destino = os.path.join(tmp, "reproducao.json")
        saida = io.StringIO()
        original, sys.stdout = sys.stdout, saida
        try:
            medidor.main(["--todas", "--json", destino])
        finally:
            sys.stdout = original
        with open(destino, encoding="utf-8") as f:
            dados = json.load(f)
        self.assertEqual(len(dados), len(receitas()))
        self.assertTrue(all(d["conferencia"]["confere"] for d in dados))


class ReproduzOsNumerosPublicados(unittest.TestCase):
    """Cada receita bate com a medicao que ela diz reproduzir."""

    def test_toda_receita_confere_campo_a_campo(self):
        for caminho in receitas():
            with self.subTest(receita=os.path.basename(caminho)):
                r = medidor.reproduzir(medidor.carregar_receita(caminho))
                for linha in r["conferencia"]["campos"]:
                    self.assertTrue(
                        linha["confere"],
                        f"{r['id']}/{linha['campo']}: recalculado "
                        f"{linha['recalculado']} != publicado "
                        f"{linha['publicado']}")

    def test_as_razoes_publicadas_no_README_sao_as_recalculadas(self):
        # Os numeros que o README e o registro CITAM, presos pelo nome.
        # Conferir campo que ninguem cita provaria determinismo, nao
        # reproducao do publicado.
        esperado = {"p21": 8.776, "p22-a": 19.558, "p22-b": 2.766,
                    "p22-c": 6.737, "p22-c-repeticao": 6.464}
        obtido = {}
        for caminho in receitas():
            r = medidor.reproduzir(medidor.carregar_receita(caminho))
            obtido[r["id"]] = r["comparacao"][
                "razao_alternativo_sobre_residual"]
        self.assertEqual(obtido, esperado)

    def test_os_residuais_publicados_sao_os_recalculados(self):
        esperado = {"p21": 872, "p22-a": 773, "p22-b": 504,
                    "p22-c": 662, "p22-c-repeticao": 690}
        obtido = {}
        for caminho in receitas():
            r = medidor.reproduzir(medidor.carregar_receita(caminho))
            obtido[r["id"]] = r["comparacao"][
                "residual_do_despachante"]["bytes_utf8"]
        self.assertEqual(obtido, esperado)

    def test_toda_medicao_publicada_TEM_receita(self):
        # O guarda do achado C propriamente dito: publicar numero novo sem
        # a receita que o produz deixa a suite vermelha. Sem ele, o defeito
        # volta na proxima medicao — que e exatamente como ele apareceu.
        publicadas = {os.path.basename(c) for c in
                      __import__("glob").glob(
                          os.path.join(DIR_EVIDENCIAS, "medicao-*.json"))}
        cobertas = set()
        for caminho in receitas():
            receita = medidor.carregar_receita(caminho)
            cobertas.add(os.path.basename(receita["publicado"]))
        self.assertEqual(
            publicadas - cobertas, set(),
            "medicao publicada sem receita: o revisor recebe o numero e "
            "nao a receita — e o achado C de novo")


class ControlePositivo(unittest.TestCase):
    """ORDEM 3 — insumo diferente, numero diferente.

    Receita que devolve o mesmo numero com insumo trocado nao reproduz
    nada: mede constante. Cada controle abaixo altera UM insumo e exige
    que o resultado se mova — e que o comando passe a DIVERGIR do
    publicado, porque e assim que a divergencia chegaria a um revisor.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p24-controle-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def receita(self, nome="p22-a"):
        return medidor.carregar_receita(
            os.path.join(_RAIZ, "08_p2", "receitas", f"{nome}.json"))

    def arquivo(self, conteudo: bytes, nome="insumo.txt") -> str:
        caminho = os.path.join(self.tmp, nome)
        with open(caminho, "wb") as f:
            f.write(conteudo)
        return caminho

    def test_turno_interno_maior_MOVE_a_razao(self):
        base = medidor.reproduzir(self.receita())
        razao_base = base["comparacao"]["razao_alternativo_sobre_residual"]

        receita = self.receita()
        original = os.path.join(_RAIZ, "05_p0", "ssc_p0", "execution.py")
        with open(original, "rb") as f:
            conteudo = f.read()
        receita["turno_interno"] = [{
            "origem": "arquivo",
            "caminho": self.arquivo(conteudo + b"# um byte a mais\n")}]
        movido = medidor.reproduzir(receita)

        self.assertNotEqual(
            movido["comparacao"]["razao_alternativo_sobre_residual"],
            razao_base,
            "turno interno maior e a MESMA razao: a receita nao esta "
            "lendo o arquivo, esta devolvendo constante")
        self.assertFalse(movido["conferencia"]["confere"])

    def test_UM_byte_a_mais_no_turno_interno_ja_aparece(self):
        # Sensibilidade fina: se so uma mudanca grande movesse o numero, a
        # receita poderia estar arredondando o insumo em vez de conta-lo.
        receita = self.receita()
        with open(os.path.join(_RAIZ, "05_p0", "ssc_p0", "execution.py"),
                  "rb") as f:
            conteudo = f.read()
        receita["turno_interno"] = [{"origem": "arquivo",
                                     "caminho": self.arquivo(conteudo + b"x")}]
        movido = medidor.reproduzir(receita)
        self.assertEqual(
            movido["comparacao"]["alternativo_sozinho"]["bytes_utf8"],
            15119, "um byte a mais no insumo nao apareceu no total")

    def test_resposta_da_assinatura_diferente_MOVE_o_residual(self):
        # O outro lado da conta. O residual e o coracao da medicao: se ele
        # nao se mover quando a resposta muda, a proxy nao esta medindo a
        # resposta.
        receita = self.receita()
        recibo_caminho = os.path.join(
            _RAIZ, receita["resposta_assinatura"]["caminho"])
        with open(recibo_caminho, encoding="utf-8") as f:
            recibo = json.load(f)
        recibo["saida"] = recibo["saida"] + "\nlinha acrescentada no controle"
        outro = os.path.join(self.tmp, "recibo.json")
        with open(outro, "w", encoding="utf-8") as f:
            json.dump(recibo, f, ensure_ascii=False)
        receita["resposta_assinatura"] = {"origem": "recibo",
                                          "caminho": outro, "campo": "saida"}
        movido = medidor.reproduzir(receita)
        self.assertEqual(
            movido["comparacao"]["residual_do_despachante"]["bytes_utf8"],
            773 + len("\nlinha acrescentada no controle".encode("utf-8")))
        self.assertFalse(movido["conferencia"]["confere"])

    def test_prompt_diferente_MOVE_os_DOIS_lados(self):
        # O prompt atravessa as duas fronteiras: ele e entrada da
        # assinatura e entrada do canal alternativo. Um controle que
        # movesse so um lado indicaria que a receita conta o prompt uma
        # vez so — e a corrida real o paga duas.
        receita = self.receita("p22-c-repeticao")
        base = medidor.reproduzir(receita)
        with open(os.path.join(_RAIZ, "08_p2", "receitas",
                               "prompt-p22-c.txt"), "rb") as f:
            prompt = f.read()
        receita = self.receita("p22-c-repeticao")
        receita["entrada"] = {"origem": "arquivo",
                              "caminho": self.arquivo(prompt + b" mais texto")}
        movido = medidor.reproduzir(receita)
        delta = len(b" mais texto")
        self.assertEqual(
            movido["comparacao"]["residual_do_despachante"]["bytes_utf8"],
            base["comparacao"]["residual_do_despachante"]["bytes_utf8"] + delta)
        self.assertEqual(
            movido["comparacao"]["alternativo_sozinho"]["bytes_utf8"],
            base["comparacao"]["alternativo_sozinho"]["bytes_utf8"] + delta)

    def test_o_prompt_VERSIONADO_e_o_que_a_receita_le(self):
        # Contraprova do controle acima: o insumo versionado tem o tamanho
        # que a corrida publicou. Se o arquivo do repositorio mudar, esta
        # assercao cai — que e o comportamento desejado, porque o numero
        # publicado deixaria de ser reproduzivel.
        caminho = os.path.join(_RAIZ, "08_p2", "receitas", "prompt-p22-c.txt")
        with open(caminho, "rb") as f:
            brutos = f.read()
        self.assertEqual(medidor.tamanhos(brutos),
                         {"bytes_utf8": 224, "caracteres": 224})


class InsumoQueNaoResolveNaoViraZero(unittest.TestCase):
    """Fail-closed: insumo ausente levanta, nunca vira zero silencioso."""

    def test_origem_desconhecida(self):
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo({"origem": "adivinhacao"})

    def test_arquivo_ausente(self):
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo({"origem": "arquivo",
                                      "caminho": "nao/existe.txt"})

    def test_testemunho_sem_numero(self):
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo({"origem": "testemunho",
                                      "porque": "x"})

    def test_testemunho_sem_porque(self):
        # Numero que ninguem pode recontar tem de dizer POR QUE nao pode.
        # Sem essa linha o testemunho passaria por medicao na leitura
        # seguinte — e e assim que a familia (F) nasce.
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo({"origem": "testemunho",
                                      "bytes_utf8": 1, "caracteres": 1})

    def test_recibo_sem_o_campo_da_resposta(self):
        tmp = tempfile.mkdtemp(prefix="p24-recibo-")
        self.addCleanup(shutil.rmtree, tmp, True)
        caminho = os.path.join(tmp, "recibo.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"status": "sucesso"}, f)
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo({"origem": "recibo", "caminho": caminho})

    def test_recibo_com_fallback_LEVANTA_em_vez_de_subcontar(self):
        # O recibo carrega SO a saida final. Com duas tentativas
        # concluidas, contar uma so sub-contaria o gasto da assinatura — e
        # sub-contar o gasto e o vies que favorece a tese.
        tmp = tempfile.mkdtemp(prefix="p24-fallback-")
        self.addCleanup(shutil.rmtree, tmp, True)
        caminho = os.path.join(tmp, "recibo.json")
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"saida": "resposta",
                       "attempts": [
                           {"attempt_id": "1", "resultado": "falha-quota",
                            "executor_resolvido": {"provedor": "kimi",
                                                   "modelo": "k"}},
                           {"attempt_id": "2", "resultado": "sucesso",
                            "executor_resolvido": {"provedor": "codex",
                                                   "modelo": "g"}}]}, f)
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._tentativas_da_receita(
                {"origem": "recibo", "caminho": caminho},
                {"bytes_utf8": 1, "caracteres": 1})


class CoberturaDeclarada(unittest.TestCase):
    """Quanto do 'confere' foi recontado, e quanto foi aceito."""

    def test_toda_receita_publica_a_fracao_recontada(self):
        for caminho in receitas():
            with self.subTest(receita=os.path.basename(caminho)):
                r = medidor.reproduzir(medidor.carregar_receita(caminho))
                cob = r["cobertura_reproduzida"]
                self.assertIsInstance(cob["bytes_recontados_do_repositorio"],
                                      int)
                self.assertGreater(cob["fracao"], 0.0,
                                   "receita sem NENHUM insumo recontado nao "
                                   "reproduz — apenas repete o publicado")

    def test_todo_testemunho_carrega_o_motivo_no_relatorio(self):
        for caminho in receitas():
            r = medidor.reproduzir(medidor.carregar_receita(caminho))
            for insumo in r["insumos"]:
                if not insumo["reproduzido"]:
                    with self.subTest(receita=r["id"],
                                      insumo=insumo["rotulo"]):
                        self.assertTrue(insumo.get("porque"))

    def test_a_corrida_sem_recibo_aparece_como_testemunho(self):
        # A corrida (c) da P2.2 nao tem recibo — caiu no UnicodeEncodeError
        # do console, medido na propria P2.2. Ela nao pode passar por
        # recontada: o relatorio tem de dizer que ali se aceita testemunho.
        r = medidor.reproduzir(medidor.carregar_receita(
            os.path.join(_RAIZ, "08_p2", "receitas", "p22-c.json")))
        testemunhos = [x["rotulo"] for x in r["insumos"]
                       if not x["reproduzido"]]
        self.assertTrue(any("codex" in x for x in testemunhos),
                        f"a resposta sem recibo nao esta declarada: "
                        f"{testemunhos}")


def _lab_da_repeticao() -> str:
    return os.path.join(_RAIZ, "08_p2", "saidas", "labs", "20260803T135101Z")


class UmaSomaSo(unittest.TestCase):
    """A receita e a cadeia passam pela MESMA aritmetica."""

    def test_medir_assinatura_compoe_pela_funcao_compartilhada(self):
        # Guarda estrutural: se `medir_assinatura` voltar a somar por
        # conta propria, a receita e a cadeia podem divergir sem que
        # nenhum teste de numero acuse — as duas continuariam internamente
        # coerentes.
        import ast
        import inspect
        arvore = ast.parse(inspect.getsource(medidor.medir_assinatura))
        chamadas = {n.func.id for n in ast.walk(arvore)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("compor_assinatura", chamadas)

    @unittest.skipUnless(
        os.path.isdir(_lab_da_repeticao()),
        "lab da corrida c-repeticao ausente (`08_p2/saidas/` nao e "
        "versionado). Sem ele esta comparacao NAO e verificavel, e o skip "
        "existe para dizer isso alto — nunca para dar a suite por verde")
    def test_a_receita_devolve_O_MESMO_que_a_cadeia_verificada(self):
        # A prova mais forte disponivel: para a UNICA corrida cujo lab
        # sobreviveu, o que a receita calcula a partir de insumos
        # versionados e identico ao que `EvidencePlane` projeta da cadeia.
        da_cadeia = medidor.medir_assinatura(
            _lab_da_repeticao(), "4bf725b0132d4bcc9c5f81392af09440")
        da_receita = medidor.reproduzir(medidor.carregar_receita(
            os.path.join(_RAIZ, "08_p2", "receitas",
                         "p22-c-repeticao.json")))["assinatura"]
        for campo in ("total", "total_entrada", "total_saida",
                      "residual_do_despachante", "entrada_unitaria"):
            with self.subTest(campo=campo):
                self.assertEqual(da_receita[campo], da_cadeia[campo])


class RelatoNaoDependeDoConsole(unittest.TestCase):
    """O console nao pode derrubar o comando depois do trabalho feito.

    O caso ocorreu em operacao na P2.2 com a resposta do codex; aqui a
    exposicao e a mesma por outro caminho: o relatorio imprime texto que
    vem de ARQUIVO — titulo de receita, motivo de testemunho —, e arquivo
    carrega o caractere que alguem escreveu nele.

    `io.TextIOWrapper(..., encoding="cp1252")` ENFORCA o codec e levanta
    igual ao console real; um `StringIO` aceitaria qualquer str e ficaria
    verde sob o defeito.
    """

    SETA = "titulo com seta →"

    def _relatar_em(self, resultado, codec) -> bytes:
        buffer = io.BytesIO()
        fluxo = io.TextIOWrapper(buffer, encoding=codec, newline="",
                                 write_through=True)
        original, sys.stdout = sys.stdout, fluxo
        try:
            medidor.relatar(resultado)
        finally:
            fluxo.flush()
            sys.stdout = original
        return buffer.getvalue()

    def resultado(self, **campos):
        base = medidor.reproduzir(medidor.carregar_receita(
            os.path.join(_RAIZ, "08_p2", "receitas", "p22-a.json")))
        base.update(campos)
        return base

    def test_titulo_com_caractere_fora_do_codec_nao_derruba_o_relato(self):
        brutos = self._relatar_em(self.resultado(titulo=self.SETA), "cp1252")
        self.assertIn(b"titulo com seta", brutos)
        self.assertIn(b"?", brutos)

    def test_motivo_de_testemunho_tambem_atravessa_o_codec(self):
        r = self.resultado()
        for insumo in r["insumos"]:
            if not insumo["reproduzido"]:
                insumo["porque"] = self.SETA
        brutos = self._relatar_em(r, "cp1252")
        self.assertIn(b"testemunho:", brutos)
        self.assertIn(b"?", brutos)

    def test_console_utf8_PRESERVA_o_caractere(self):
        # Tolerancia nao pode virar perda quando o console sabe desenhar.
        brutos = self._relatar_em(self.resultado(titulo=self.SETA), "utf-8")
        self.assertIn("→".encode("utf-8"), brutos)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
