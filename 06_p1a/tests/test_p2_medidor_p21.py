"""O medidor da tese, exercido contra a cadeia que a operacao produz.

A pergunta da REGRA DE PROVA — *"o teste exerce o caminho que a operacao
percorre, ou um vizinho?"* — tem resposta explicita aqui: os testes de
`medir_assinatura` **nao** montam EventLog a mao. Eles chamam
`runner_p2.executar`, o MESMO ponto de entrada da operacao, com sensor
falso injetado, e medem o laboratorio que sair de la. Uma fixture de
cadeia escrita a mao seria o vizinho: mediria o formato que o teste
imagina, e ficaria verde no dia em que o runner passasse a gravar outro.

Nenhum teste daqui invoca codex ou kimi; nenhum consome franquia.

O QUE ESTES TESTES NAO COBREM, declarado:

- **nao provam que a proxy corresponda a token.** Nada aqui converte byte
  em token, e o item `bytes-nao-sao-tokens` de `NAO_CAPTURA` diz por que
  isso nao e possivel com os dois CLIs de hoje. A suite prende o
  INSTRUMENTO e a honestidade da declaracao — nunca a validade da proxy
  como preditor de fatura;
- **nao medem o canal alternativo.** `medir_alternativo` recebe razonete
  declarado; nenhum teste verifica que o razonete corresponda ao que o
  canal alternativo de fato consumiu, porque esse canal nao grava cadeia;
- **nao cobrem concorrencia** entre dois medidores sobre o mesmo lab;
- **nao cobrem laboratorio com cadeia corrompida.** `EvidencePlane`
  levanta na verificacao, e esse comportamento e da P0, exercido la;
- **nao cobrem tarefa acima de 4000 chars EM OPERACAO REAL.** O
  truncamento e exercido pela via de `entrada_real`, que mede a
  divergencia; a corrida real com tarefa gigante nao foi feita.
"""

import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", os.path.join("05_p0", "cenarios"), "08_p2",
           os.path.join("06_p1a", "evidencias")):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import medidor  # noqa: E402
import runner_p2  # noqa: E402
from test_p2_runner_p2 import SensorObrigatorio, preflight_real  # noqa: E402

# Os NOVE limites, ESCRITOS AQUI a mao. Nao se importa `NAO_CAPTURA` para
# compara-la consigo mesma: isso seria tautologia — o guarda que afirma a
# propriedade em vez de exerce-la, a familia do MAJOR #3 que este acervo
# ja pagou tres vezes. Com a lista literal, apagar um membro do modulo
# fica VERMELHO aqui.
#
# O nono entrou na P2.2, por medicao: a poupanca decompoe em turno interno
# mais diferenca de verbosidade, e na classe sem turno interno o segundo
# termo era a poupanca inteira.
CODIGOS_ESPERADOS = {
    "bytes-nao-sao-tokens",
    "contexto-do-canal-nao-atravessa-a-fronteira",
    "raciocinio-nao-emitido",
    "cache-nao-e-visto",
    "turnos-internos-so-contam-se-declarados",
    "qualidade-nao-e-medida",
    "entrada-da-cadeia-e-truncada-em-4000-chars",
    "uma-corrida-nao-e-tendencia",
    "verbosidade-do-canal-entra-na-poupanca",
}


class Tamanhos(unittest.TestCase):
    """As duas unidades existem porque uma sozinha esconde a escolha."""

    def test_ascii_tem_as_duas_unidades_iguais(self):
        self.assertEqual(medidor.tamanhos("pronto"),
                         {"bytes_utf8": 6, "caracteres": 6})

    def test_acento_separa_byte_de_caractere(self):
        # O caso que motivou medir as duas: em utf-8 o acento custa 2
        # bytes e 1 caractere. Reportar so bytes faria texto em portugues
        # parecer 20% maior que o mesmo texto em ingles.
        t = medidor.tamanhos("função")
        self.assertEqual(t["caracteres"], 6)
        self.assertEqual(t["bytes_utf8"], 8)

    def test_bytes_entram_pelo_tamanho_cru(self):
        # O CAS guarda BYTES. Medir o que o CAS guardou e medir bytes.
        self.assertEqual(medidor.tamanhos("função".encode("utf-8")),
                         {"bytes_utf8": 8, "caracteres": 6})

    def test_vazio_e_zero_nas_duas(self):
        for vazio in ("", b"", None):
            with self.subTest(vazio=vazio):
                self.assertEqual(medidor.tamanhos(vazio),
                                 {"bytes_utf8": 0, "caracteres": 0})


class _ComCorrida(unittest.TestCase):
    """Cada teste roda o RUNNER e mede o laboratorio que ele gravou."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p21-medidor-")
        self.addCleanup(self._tmp.cleanup)
        self.raiz_lab = os.path.join(self._tmp.name, "lab")

    def corrida(self, sensor, tarefa="responda com a palavra pronto", **kw):
        return runner_p2.executar(
            tarefa=tarefa, criterio="resposta nao vazia",
            preflight=preflight_real(), raiz_lab=self.raiz_lab,
            sensor=sensor, **kw)


class LadoAssinatura(_ComCorrida):
    """A carga de fronteira sai da cadeia verificada, nao do processo."""

    def test_sucesso_simples_conta_prompt_e_resposta(self):
        r = self.corrida(SensorObrigatorio(codex=(0, "pronto", "")),
                         tarefa="responda pronto")
        self.assertEqual(r["status"], "sucesso", r.get("detalhe"))
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertEqual(m["n_tentativas"], 1)
        self.assertEqual(m["total_entrada"]["bytes_utf8"],
                         len("responda pronto".encode("utf-8")))
        self.assertEqual(m["total_saida"]["bytes_utf8"],
                         len("pronto".encode("utf-8")))
        self.assertEqual(m["total"]["bytes_utf8"],
                         m["total_entrada"]["bytes_utf8"]
                         + m["total_saida"]["bytes_utf8"])

    def test_a_fonte_declarada_e_a_cadeia(self):
        # A propriedade que separa este medidor de um contador ingenuo: os
        # numeros vem do EventLog verificado + CAS, e o campo diz isso a
        # quem ler a evidencia depois.
        r = self.corrida(SensorObrigatorio(codex=(0, "ok", "")))
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertIn("cadeia-verificada", m["fonte"])
        self.assertEqual(m["procedencia_entrada"], "medido-cadeia")

    def test_acento_da_resposta_conta_bytes_e_caracteres_diferentes(self):
        # Amarra a medicao ao achado 4.3 da P2.0: a resposta em portugues
        # vive no CAS em bytes utf-8, e as duas unidades tem de divergir.
        r = self.corrida(SensorObrigatorio(codex=(0, "função", "")))
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertEqual(m["total_saida"]["caracteres"], 6)
        self.assertEqual(m["total_saida"]["bytes_utf8"], 8)

    def test_fallback_cobra_o_prompt_DUAS_vezes(self):
        # O caso que a operacao percorre e que um contador ingenuo erra: o
        # mesmo prompt atravessou a fronteira do codex E a do kimi. Contar
        # uma vez seria medir o desfecho em vez do gasto.
        sensor = SensorObrigatorio(codex=(1, "", "0 requests remaining"),
                                   kimi=(0, "feito pelo kimi", ""))
        r = self.corrida(sensor, tarefa="responda pronto")
        self.assertEqual(r["status"], "sucesso", r.get("detalhe"))
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertEqual(m["n_tentativas"], 2)
        unitaria = m["entrada_unitaria"]["bytes_utf8"]
        self.assertEqual(m["total_entrada"]["bytes_utf8"], unitaria * 2)
        self.assertEqual([t["executor"].split("/")[0] for t in m["tentativas"]],
                         ["codex", "kimi"])

    def test_a_saida_da_tentativa_que_FALHOU_tambem_conta(self):
        # Falha ocupa fronteira: o texto do erro atravessou e esta no CAS.
        sensor = SensorObrigatorio(codex=(1, "", "0 requests remaining"),
                                   kimi=(0, "ok", ""))
        r = self.corrida(sensor)
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        falhada = [t for t in m["tentativas"] if t["resultado"] != "sucesso"]
        self.assertTrue(falhada)
        self.assertGreater(falhada[0]["saida"]["bytes_utf8"], 0)

    def test_o_residual_NAO_cobra_o_fallback_ao_despachante(self):
        # A distincao que faz a medicao valer alguma coisa: a assinatura
        # absorve a tentativa perdida; o despachante redigiu o prompt uma
        # vez e leu a resposta final uma vez. Se o residual crescesse com
        # o fallback, a poupanca sumiria por artefato do instrumento.
        sensor = SensorObrigatorio(codex=(1, "", "0 requests remaining"),
                                   kimi=(0, "feito pelo kimi", ""))
        r = self.corrida(sensor, tarefa="responda pronto")
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        esperado = (len("responda pronto".encode("utf-8"))
                    + len("feito pelo kimi".encode("utf-8")))
        self.assertEqual(m["residual_do_despachante"]["bytes_utf8"], esperado)
        self.assertLess(m["residual_do_despachante"]["bytes_utf8"],
                        m["total"]["bytes_utf8"])

    def test_sem_sucesso_o_despachante_ainda_le_o_motivo_da_parada(self):
        # Fronteira nao e so a resposta boa. O operador le por que parou.
        sensor = SensorObrigatorio(codex=(1, "", "0 requests remaining"),
                                   kimi=(1, "", "quota exhausted"))
        r = self.corrida(sensor)
        self.assertNotEqual(r["status"], "sucesso")
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertGreater(m["residual_do_despachante"]["bytes_utf8"], 0)

    def test_entrada_real_expoe_a_divergencia_com_a_cadeia(self):
        # O caso que ocorre em operacao acima do teto: o CLI recebeu a
        # tarefa integral e a cadeia guardou `tarefa[:4000]`. Medir so pela
        # cadeia sub-conta, e o instrumento tem de DIZER quanto.
        r = self.corrida(SensorObrigatorio(codex=(0, "ok", "")),
                         tarefa="responda pronto")
        integral = "responda pronto" + ("x" * 100)
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"],
                                     entrada_real=integral)
        self.assertEqual(m["procedencia_entrada"], "medido-processo")
        self.assertEqual(m["truncamento"]["divergencia_medida"]["caracteres"],
                         100)

    def test_intencao_no_teto_levanta_a_bandeira_de_truncamento(self):
        # 4000 chars exatos e a assinatura do corte: o runner fatia em
        # `[:4000]`, entao bater no teto e o sinal de que pode haver mais
        # do lado de fora da cadeia.
        r = self.corrida(SensorObrigatorio(codex=(0, "ok", "")),
                         tarefa="a" * 5000)
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertEqual(m["entrada_unitaria"]["caracteres"],
                         medidor.TETO_INTENCAO_CHARS)
        self.assertTrue(m["truncamento"]["possivel"])

    def test_tarefa_curta_nao_levanta_bandeira(self):
        # Contraprova: a bandeira nao pode subir sempre, senao nao informa.
        r = self.corrida(SensorObrigatorio(codex=(0, "ok", "")))
        m = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        self.assertFalse(m["truncamento"]["possivel"])

    def test_work_unit_inexistente_e_falha_fechada(self):
        r = self.corrida(SensorObrigatorio(codex=(0, "ok", "")))
        with self.assertRaises(medidor.MedicaoAmbigua):
            medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"],
                                     work_unit_id="0" * 32)

    def test_duas_corridas_no_mesmo_lab_nao_se_misturam(self):
        # MEDIDO, nao suposto: cada `executar` abre SESSAO propria, e a
        # `EvidencePlane` le uma sessao por vez. Duas corridas na mesma
        # raiz nao produzem cadeia ambigua — produzem duas cadeias. Por
        # isso `work_unit_id=None` e seguro na operacao de hoje, e a
        # medicao de uma corrida nunca contamina a outra.
        r1 = self.corrida(SensorObrigatorio(codex=(0, "ok", "")),
                          tarefa="primeira")
        r2 = self.corrida(SensorObrigatorio(codex=(0, "ok", "")),
                          tarefa="segunda tarefa")
        self.assertNotEqual(r1["sessao_id"], r2["sessao_id"])
        m1 = medidor.medir_assinatura(r1["raiz_lab"], r1["sessao_id"])
        m2 = medidor.medir_assinatura(r2["raiz_lab"], r2["sessao_id"])
        self.assertEqual(m1["entrada_unitaria"]["bytes_utf8"], len("primeira"))
        self.assertEqual(m2["entrada_unitaria"]["bytes_utf8"],
                         len("segunda tarefa"))

    def test_cadeia_com_DUAS_work_units_exige_escolha(self):
        # DECLARADO: este e o unico teste do arquivo que NAO passa pelo
        # runner, porque o runner de hoje nao consegue produzir o caso —
        # uma WorkUnit por sessao. O guarda existe para a cadeia que
        # `decompor` ja sabe gerar, e para o dia em que uma sessao servir
        # mais de uma tarefa; sem ele, o medidor escolheria a primeira e
        # devolveria numero plausivel sobre a tarefa errada.
        from comum import Lab
        raiz = os.path.join(self._tmp.name, "lab-duas")
        lab = Lab(raiz)
        for intencao in ("primeira", "segunda"):
            lab.router.forjar(
                intencao=intencao,
                criterios={"criterio": "x", "verificacao": "humana"},
                tipo="ato", nivel="L2",
                perfil={"modalidade": "texto", "ferramentas": [],
                        "formato_saida": "livre", "contexto_max_tokens": 1000,
                        "dominio": "geral", "privacidade": "remoto-permitido",
                        "latencia_max_ms": None, "orcamento_max_custo": None},
                classe="C1")
        sessao = lab.envelope.sessao_id
        with self.assertRaises(medidor.MedicaoAmbigua):
            medidor.medir_assinatura(raiz, sessao)
        # ...e, declarada, mede a que se pediu.
        alvo = [wid for wid, wu in
                medidor.EvidencePlane(raiz, sessao).projetar()[
                    "work_units"].items() if wu["intencao"] == "segunda"][0]
        m = medidor.medir_assinatura(raiz, sessao, work_unit_id=alvo)
        self.assertEqual(m["entrada_unitaria"]["bytes_utf8"], len("segunda"))
        self.assertEqual(m["n_tentativas"], 0)


class LadoAlternativo(unittest.TestCase):
    """Razonete declarado — e o aviso quando ele tem forma de incompleto."""

    def test_item_de_arquivo_mede_o_arquivo_de_verdade(self):
        alvo = os.path.join(_RAIZ, "08_p2", "medidor.py")
        item = medidor.item_de_arquivo(alvo, "interno")
        self.assertEqual(item["procedencia"], "medido-arquivo")
        self.assertEqual(item["bytes_utf8"], os.path.getsize(alvo))
        self.assertEqual(item["rotulo"], "08_p2/medidor.py")

    def test_papel_invalido_e_recusado_nos_dois_construtores(self):
        with self.assertRaises(ValueError):
            medidor.item_de_texto("x", "chute", "r")
        with self.assertRaises(ValueError):
            medidor.medir_alternativo([{"papel": "chute", "bytes_utf8": 1}])

    def test_totais_saem_separados_por_papel(self):
        m = medidor.medir_alternativo([
            medidor.item_de_texto("abc", "entrada", "prompt"),
            medidor.item_de_texto("de", "interno", "leitura"),
            medidor.item_de_texto("f", "saida", "resposta")])
        self.assertEqual(m["por_papel"]["entrada"]["bytes_utf8"], 3)
        self.assertEqual(m["por_papel"]["interno"]["bytes_utf8"], 2)
        self.assertEqual(m["por_papel"]["saida"]["bytes_utf8"], 1)
        self.assertEqual(m["total"]["bytes_utf8"], 6)

    def test_razonete_sem_turno_interno_AVISA(self):
        # A economia que a tese afirma mora nos turnos internos. Um
        # razonete sem nenhum nao prova ausencia de economia — so nao a
        # mediu, e a saida precisa dizer isso a quem for citar o numero.
        m = medidor.medir_alternativo([
            medidor.item_de_texto("abc", "entrada", "prompt"),
            medidor.item_de_texto("f", "saida", "resposta")])
        self.assertIn("sem-turno-interno-declarado",
                      [a["codigo"] for a in m["avisos"]])

    def test_razonete_completo_nao_avisa(self):
        # Contraprova: o aviso nao pode sair sempre, senao vira ruido.
        m = medidor.medir_alternativo([
            medidor.item_de_texto("abc", "entrada", "prompt"),
            medidor.item_de_texto("de", "interno", "leitura"),
            medidor.item_de_texto("f", "saida", "resposta")])
        self.assertEqual(m["avisos"], [])

    def test_razonete_vazio_avisa_das_duas_coisas(self):
        m = medidor.medir_alternativo([])
        self.assertEqual(
            sorted(a["codigo"] for a in m["avisos"]),
            ["sem-saida-declarada", "sem-turno-interno-declarado"])


class Comparacao(_ComCorrida):
    """A poupanca, e os limites colados nela."""

    def _par(self, itens, tarefa="responda pronto", saida="pronto"):
        r = self.corrida(SensorObrigatorio(codex=(0, saida, "")), tarefa=tarefa)
        assinatura = medidor.medir_assinatura(r["raiz_lab"], r["sessao_id"])
        return medidor.comparar(assinatura, medidor.medir_alternativo(itens))

    def test_poupanca_e_alternativo_menos_residual(self):
        # A conta que define a tese: o que o outro canal gastaria sozinho,
        # menos o que ele CONTINUA gastando ao despachar.
        c = self._par([medidor.item_de_texto("a" * 1000, "interno", "leitura"),
                       medidor.item_de_texto("resposta", "saida", "r")])
        residual = c["residual_do_despachante"]["bytes_utf8"]
        self.assertEqual(c["poupanca"]["bytes_utf8"], 1008 - residual)
        self.assertGreater(c["poupanca"]["bytes_utf8"], 0)
        self.assertIn("MENOS", c["veredito_da_fronteira"])

    def test_despacho_mais_caro_sai_como_MAIS_e_nao_como_economia(self):
        # A propriedade que impede o instrumento de fechar a tese por
        # construcao: quando o despacho custa mais, ele DIZ que custou
        # mais. Um medidor que so soubesse anunciar economia nao mediria
        # nada — afirmaria.
        c = self._par([medidor.item_de_texto("x", "saida", "r"),
                       medidor.item_de_texto("y", "interno", "leitura")],
                      saida="resposta bem mais longa que o razonete inteiro")
        self.assertLess(c["poupanca"]["bytes_utf8"], 0)
        self.assertIn("MAIS", c["veredito_da_fronteira"])

    def test_sem_turno_interno_e_resposta_IGUAL_a_poupanca_e_ZERO(self):
        # A FRONTEIRA que a P2.2 mediu e escreveu no README da P2, presa
        # aqui para nao virar afirmacao sem guarda. Tarefa sem turno
        # interno, e as duas respostas do mesmo tamanho: nao ha o que
        # poupar na fronteira, e o instrumento tem de DIZER empate — nunca
        # anunciar economia onde a estrutura da tarefa nao permite nenhuma.
        c = self._par([medidor.item_de_texto("responda pronto", "entrada",
                                             "prompt"),
                       medidor.item_de_texto("pronto", "saida", "r")])
        self.assertEqual(c["poupanca"]["bytes_utf8"], 0)
        self.assertEqual(c["razao_alternativo_sobre_residual"], 1.0)
        self.assertIn("empate", c["veredito_da_fronteira"])

    def test_a_poupanca_decompoe_em_turno_interno_MAIS_verbosidade(self):
        # A identidade medida nas tres classes da P2.2:
        #     poupanca == turno_interno + (saida_alt - saida_assinatura)
        # O segundo termo nao vem de despachar. Sem este guarda, um
        # medidor que somasse os dois num numero so continuaria verde, e
        # quem citasse a poupanca creditaria ao despacho a brevidade do
        # outro canal.
        interno = "z" * 500
        alheia = "resposta bem mais longa que a da assinatura"
        c = self._par([medidor.item_de_texto("responda pronto", "entrada",
                                             "prompt"),
                       medidor.item_de_texto(interno, "interno", "leitura"),
                       medidor.item_de_texto(alheia, "saida", "r")])
        verbosidade = len(alheia.encode("utf-8")) - len("pronto".encode())
        self.assertEqual(c["poupanca"]["bytes_utf8"], 500 + verbosidade)
        self.assertGreater(verbosidade, 0)   # o termo existe nesta corrida

    def test_os_NOVE_limites_viajam_dentro_do_numero(self):
        # Proxy declarada vale; proxy silenciosa vira o defeito. A lista
        # esperada esta escrita a mao no topo deste arquivo, entao apagar
        # um membro de `NAO_CAPTURA` fica VERMELHO aqui — o guarda exerce
        # a propriedade em vez de compara-la consigo mesma.
        c = self._par([medidor.item_de_texto("x", "saida", "r")])
        codigos = {x["codigo"] for x in c["nao_captura"]}
        self.assertEqual(codigos, CODIGOS_ESPERADOS)
        for esperado in CODIGOS_ESPERADOS:
            with self.subTest(limite=esperado):
                self.assertIn(esperado, codigos)

    def test_cada_limite_declara_o_PORQUE_e_nao_so_o_nome(self):
        # Rotulo sem razao e a forma mais barata de parecer honesto. Um
        # `porque` vazio passaria por declaracao e nao ensinaria nada a
        # quem lesse a evidencia seis meses depois.
        c = self._par([medidor.item_de_texto("x", "saida", "r")])
        for limite in c["nao_captura"]:
            with self.subTest(limite=limite["codigo"]):
                self.assertGreaterEqual(len(limite.get("porque", "")), 40)

    def test_os_avisos_do_razonete_sobem_para_a_comparacao(self):
        # O aviso nasce no razonete e precisa chegar em quem le a
        # comparacao: e la que o numero vai ser citado.
        c = self._par([medidor.item_de_texto("x", "saida", "r")])
        self.assertIn("sem-turno-interno-declarado",
                      [a["codigo"] for a in c["avisos"]])

    def test_a_comparacao_declara_n_igual_a_um(self):
        # Uma corrida nao e tendencia, e o numero tem de carregar o proprio
        # `n` — senao a citacao seguinte o trata como media.
        c = self._par([medidor.item_de_texto("x", "saida", "r")])
        self.assertEqual(c["n_corridas"], 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
