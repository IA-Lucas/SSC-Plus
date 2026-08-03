"""A sentinela anti-P2 depois da emenda — o que passa a valer, medido.

O ato soberano de 2026-08-03 (`08_p2/00_ato-soberano-p2.md`) abriu a P2.
A sentinela deixou de proibir consumidor NENHUM e passou a exigir
consumidor DECLARADO NOMINALMENTE. Uma emenda dessas tem duas maneiras
obvias de dar errado, e cada uma tem controle aqui:

1. **afrouxar demais** — a allowlist virar um interruptor que desliga a
   varredura, ou casar por prefixo/diretorio, de modo que qualquer
   arquivo novo em `08_p2/` entre de carona. Medido em
   `AllowlistNaoAfrouxa`;
2. **fazer achado sumir** — o portao do consumidor autorizado deixar de
   existir no relatorio, em vez de mudar de campo. Um acervo que passou
   tres missoes corrigindo guardas que AFIRMAM em vez de EXERCER nao
   pode fechar uma emenda transformando evidencia em silencio. Medido em
   `NadaSomeDoRelatorio`.

O CAMINHO QUE A OPERACAO PERCORRE. `sentinela.varrer` e a MESMA funcao
nos dois usos: o teste do acervo a chama com a raiz real e a allowlist
real; os controles a chamam com arvores sinteticas em disco que CONTEM o
consumidor. Nao ha versao de teste da varredura.

O vizinho recusado: montar a arvore sintetica SEM o arquivo declarado e
verificar que `portoes` esta vazio. Isso passa por construcao — a
allowlist nunca e exercida, e o teste fica verde afirmando o que nao
mediu. Toda arvore aqui contem o arquivo em questao.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao provam que o consumidor autorizado esteja CORRETO. Autorizado
  quer dizer "esperado neste lugar", nunca "faz a coisa certa": os
  portoes economicos que o governam sao medidos noutros testes;
- nao cobrem consumo do veredito por fora do fonte versionado
  (configuracao, dado, prompt) — limite herdado, nao fechado aqui;
- `PRIMITIVAS_EXECUCAO` continua enumerada: primitiva de execucao fora
  da lista nao e reconhecida como execucao, nem dentro nem fora da
  allowlist;
- nada aqui mede se a lista `CONSUMIDORES_DECLARADOS` foi editada por
  quem tinha autoridade. A sentinela sabe o que esta escrito nela; quem
  escreveu e materia do registro de commit, nao do AST.
"""

import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sentinela_antip2 as sentinela  # noqa: E402

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REAL = os.path.dirname(_DIR_P1A)

CLASSIFICADOR_REL = "06_p1a/preflight/pipeline.py"

FONTE_CLASSIFICADOR = '''
RESULTADOS = ("ELIGIBLE", "SHADOW_ELIGIBLE", "SUPERVISED", "BLOCKED")


def classificar(teto, sombra):
    resultado = teto
    if sombra is not None and resultado == "ELIGIBLE":
        resultado = "SHADOW_ELIGIBLE"
    return resultado
'''

# Um consumidor de verdade: decide sobre o veredito E deixa a decisao
# governar execucao. E a forma exata que a metade (B) persegue.
FONTE_CONSUMIDOR = '''
import subprocess


def despachar(relatorio, argv):
    if relatorio["resultado"] == "SHADOW_ELIGIBLE":
        return subprocess.run(argv)
    return None
'''


class _ArvoreSintetica(unittest.TestCase):
    """Arvore com a MESMA forma do acervo, montada em disco."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p2-sent-")
        self.raiz = self._tmp.name
        self.addCleanup(self._tmp.cleanup)
        self.classificador = self.escrever(CLASSIFICADOR_REL,
                                           FONTE_CLASSIFICADOR)

    def escrever(self, rel: str, fonte: str) -> str:
        caminho = os.path.join(self.raiz, *rel.split("/"))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(fonte)
        return caminho

    def varrer(self, consumidores=None) -> dict:
        return sentinela.varrer(self.raiz, self.classificador, consumidores)

    def relativos(self, achados, campo) -> list:
        return sorted(a.split(":")[0].replace("\\", "/")
                      for a in achados[campo])


class AllowlistNaoAfrouxa(_ArvoreSintetica):
    """A emenda nao pode virar interruptor: quem nao foi declarado, cai."""

    def test_consumidor_nao_declarado_continua_sendo_achado(self):
        # O controle positivo da emenda. A allowlist declara UM arquivo; o
        # violador esta em OUTRO, no mesmo diretorio.
        self.escrever("08_p2/runner_p2.py", FONTE_CONSUMIDOR)
        self.escrever("08_p2/clandestino.py", FONTE_CONSUMIDOR)
        achados = self.varrer(("08_p2/runner_p2.py",))
        self.assertEqual(self.relativos(achados, "portoes"),
                         ["08_p2/clandestino.py"],
                         "consumidor NAO declarado precisa continuar sendo "
                         "achado — a allowlist nao pode desligar a metade (B)")
        self.assertEqual(self.relativos(achados, "decisoes_fora"),
                         ["08_p2/clandestino.py"])

    def test_allowlist_e_caminho_exato_nunca_prefixo(self):
        # Se a comparacao fosse por prefixo/diretorio, um arquivo com nome
        # parecido entraria de carona — e "08_p2/" inteiro viraria zona
        # franca, que e o afrouxamento que esta emenda nao pode produzir.
        self.escrever("08_p2/runner_p2.py", FONTE_CONSUMIDOR)
        self.escrever("08_p2/runner_p2_extra.py", FONTE_CONSUMIDOR)
        achados = self.varrer(("08_p2/runner_p2.py",))
        self.assertEqual(self.relativos(achados, "portoes"),
                         ["08_p2/runner_p2_extra.py"])

    def test_lista_vazia_restaura_o_comportamento_anterior_a_emenda(self):
        # O MESMO arquivo, a MESMA arvore: so a allowlist muda. Com `()`,
        # o consumidor declarado volta a ser achado — prova de que a
        # autorizacao vem da lista, e nao de alguma propriedade do arquivo
        # (nome, diretorio, conteudo).
        self.escrever("08_p2/runner_p2.py", FONTE_CONSUMIDOR)
        achados = self.varrer(())
        self.assertEqual(self.relativos(achados, "portoes"),
                         ["08_p2/runner_p2.py"])
        self.assertEqual(achados["portoes_autorizados"], [])

    def test_autorizacao_nao_cobre_o_fail_closed_de_ilegivel(self):
        # Arquivo autorizado que nao parseia continua ILEGIVEL. A
        # autorizacao diz "esperamos consumidor aqui", jamais "confie no
        # que nao conseguiu ler".
        self.escrever("08_p2/runner_p2.py", "def quebrado(:\n")
        achados = self.varrer(("08_p2/runner_p2.py",))
        self.assertEqual(len(achados["ilegiveis"]), 1)
        self.assertIn("runner_p2.py", achados["ilegiveis"][0])
        self.assertEqual(achados["portoes_autorizados"], [])


class NadaSomeDoRelatorio(_ArvoreSintetica):
    """O autorizado muda de campo — nunca de existencia."""

    def test_portao_autorizado_migra_de_campo_e_permanece_visivel(self):
        self.escrever("08_p2/runner_p2.py", FONTE_CONSUMIDOR)
        achados = self.varrer(("08_p2/runner_p2.py",))
        self.assertEqual(achados["portoes"], [],
                         "consumidor declarado nao pode reprovar a suite")
        self.assertEqual(self.relativos(achados, "portoes_autorizados"),
                         ["08_p2/runner_p2.py"],
                         "o portao autorizado precisa APARECER: achado que "
                         "vira silencio e o defeito que este acervo corrige")
        self.assertTrue(achados["portoes_autorizados"][0].endswith("-> run()"),
                        "o campo autorizado carrega a MESMA informacao do "
                        "campo de achado, inclusive a primitiva")

    def test_decisao_autorizada_migra_de_campo_e_permanece_visivel(self):
        self.escrever("08_p2/frota_medida.py",
                      'def elegiveis(rs):\n'
                      '    return [r for r in rs '
                      'if r["resultado"] != "BLOCKED"]\n')
        achados = self.varrer(("08_p2/frota_medida.py",))
        self.assertEqual(achados["decisoes_fora"], [])
        self.assertEqual(self.relativos(achados, "decisoes_autorizadas"),
                         ["08_p2/frota_medida.py"])

    def test_os_dois_campos_novos_existem_sempre(self):
        # Chave ausente e diferente de lista vazia: um consumidor do
        # relatorio que faca `achados["portoes_autorizados"]` nao pode
        # estourar KeyError na arvore limpa.
        achados = self.varrer(())
        self.assertEqual(achados["portoes_autorizados"], [])
        self.assertEqual(achados["decisoes_autorizadas"], [])


class AllowlistDoAcervo(unittest.TestCase):
    """A lista real, contra a arvore real."""

    def varrer_acervo(self):
        return sentinela.varrer(
            _RAIZ_REAL,
            os.path.join(_DIR_P1A, "preflight", "pipeline.py"))

    def test_acervo_nao_tem_consumidor_alem_dos_declarados(self):
        achados = self.varrer_acervo()
        self.assertEqual(achados["ilegiveis"], [])
        self.assertEqual(
            achados["portoes"], [],
            "CONSUMIDOR NAO DECLARADO: decisao sobre o veredito governando "
            "execucao fora da allowlist do ato soberano")
        self.assertEqual(
            achados["decisoes_fora"], [],
            "decisao sobre o veredito fora do classificador e fora da "
            "allowlist")
        self.assertEqual(achados["nao_resolvidos"], [])

    def test_todo_consumidor_declarado_existe_no_disco(self):
        # Allowlist com caminho morto e autorizacao que ninguem exerce —
        # e, pior, esconde renomeacao: o arquivo muda de nome, deixa de
        # ser autorizado, e a lista continua verde afirmando que ele e.
        #
        # Este teste nasceu junto com o PRIMEIRO nome na lista (ordem 3).
        # Enquanto ela estava vazia ele teria iterado sobre nada e ficado
        # verde sem medir — o guarda vazio que este acervo persegue.
        self.assertTrue(sentinela.CONSUMIDORES_DECLARADOS,
                        "allowlist vazia: este teste nao mede nada")
        for rel in sentinela.CONSUMIDORES_DECLARADOS:
            with self.subTest(consumidor=rel):
                self.assertTrue(
                    os.path.isfile(os.path.join(_RAIZ_REAL, *rel.split("/"))),
                    f"consumidor declarado inexistente: {rel}")

    def test_o_executor_nao_esta_na_allowlist(self):
        # A propriedade de desenho: quem invoca o CLI recebe FleetEntry ja
        # aprovada e NUNCA le veredito. No dia em que
        # `provedor_assinatura.py` precisar entrar nesta lista, o executor
        # passou a decidir — e a sentinela deve acusar, nao acomodar.
        self.assertNotIn("08_p2/provedor_assinatura.py",
                         sentinela.CONSUMIDORES_DECLARADOS)

    def test_o_consumidor_real_produz_achado_quando_nao_autorizado(self):
        # O controle que fecha o circulo: sem a allowlist, o arquivo REAL
        # da P2 — nao um sintetico — e acusado pela sentinela. E a prova de
        # que a autorizacao esta cobrindo um consumidor de verdade, e nao
        # um nome que por acaso nao produz achado nenhum.
        achados = sentinela.varrer(
            _RAIZ_REAL,
            os.path.join(_DIR_P1A, "preflight", "pipeline.py"),
            consumidores=())
        acusados = {a.split(":")[0].replace("\\", "/")
                    for a in achados["decisoes_fora"]}
        for rel in sentinela.CONSUMIDORES_DECLARADOS:
            with self.subTest(consumidor=rel):
                self.assertIn(
                    rel, acusados,
                    f"{rel} esta na allowlist mas nao decide sobre o "
                    "veredito: autorizacao sem consumidor e caminho morto")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
