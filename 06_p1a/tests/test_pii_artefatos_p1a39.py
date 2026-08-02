"""PII nos artefatos, com CONTROLE POSITIVO — SSC+ P1-A.3.9.

MECANISMO (c) da FASE 2 da P1-A.3.8, guarda `P1A-45`. A linha da
remedicao e literal:

    varre a arvore real, porem SEM CONTROLE POSITIVO: nao ha teste que
    plante PII e exija deteccao, nem guarda de "a varredura realmente le
    arquivos". O irmao `ZeroSegredoNosArtefatos` tem OS DOIS. Um padrao
    quebrado passaria em silencio.
    Remedio: copiar as duas metades do irmao.

`ZeroPiiNosArtefatos` (`test_estabilizacao_p1a1.py:379`) NAO foi editado
— registro aditivo. Ele continua valendo; o que este arquivo acrescenta
sao as duas metades que faltavam, mais duas correcoes de escopo que a
medicao desta missao encontrou.

## As duas correcoes de escopo, medidas

**1. Os alvos eram LITERAIS.** O guarda antigo procura por
`"IA " + "Lucas"` e `"IA" + "LUCA"` — o nome desta estacao, escrito a
mao no teste. E o mesmo padrao do defeito vivo 2 da P1-A.3.8: uma lista
que nada prende. Numa estacao com outro usuario o guarda continua verde
procurando um nome que nao existe — cego por construcao, e sem ruido
nenhum que denuncie. Aqui os alvos saem de `contencao._USUARIO_LOCAL` e
de `contencao.forma_8_3`, que sao a fonte que a REDACAO usa: os dois
lados da mesma politica passam a olhar o mesmo nome.

**2. A varredura via SO `06_p1a`.** `05_p0` e `07_p1b` ficavam de fora,
e `07_p1b` e justamente onde moram as evidencias de preflight gravadas
por um runner. MEDIDO nesta missao: as tres raizes estao limpas hoje —
o que faltava era medir, nao consertar.

## O que NAO entra na varredura, e por que

O prefixo de caminho local (`E:\\LucasIA`) **nao** e alvo deste guarda.
Ele existe DE PROPOSITO no fonte versionado — `preflight_capsula._GITBASH`
e `preflight_atual._GITBASH` — e e a REDACAO que o remove na saida para
o revisor (exercida por `test_redacao_operacao_p1a39` e
`test_redacao_geradores_p1a39`). Confundir as duas politicas faria este
guarda acusar operacao normal, e um guarda que acusa operacao normal e
desligado por ruido.

## O QUE ESTES TESTES NAO COBREM, declarado

- **so as extensoes de texto declaradas** (`.py`, `.md`, `.json`,
  `.txt`, `.sh`): binario, `.db`, `.jsonl` e qualquer outra extensao
  passam sem serem lidos;
- **so o usuario DESTA estacao e e-mail**: nome de maquina, IP, numero
  de serie e PII de terceiro nao sao alvo;
- **a forma 8.3 e a que o Windows produziria** para o nome atual — um
  nome historico diferente, ja gravado num artefato antigo, nao e
  procurado;
- **nao se afirma nada sobre o que ainda nao foi gravado**: e varredura
  do estado do disco, nao propriedade dos escritores. Quem prova os
  escritores e a redacao no ponto de chamada.
"""

import os
import re
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (ajusta sys.path da suite)

_DIR_TESTS = os.path.dirname(os.path.abspath(__file__))
_DIR_P1A = os.path.dirname(_DIR_TESTS)
_RAIZ_REPO = os.path.dirname(_DIR_P1A)
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

PADRAO_EMAIL = re.compile(
    "[A-Za-z0-9._%+-]+" "@" "[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")

EXTENSOES = (".py", ".md", ".json", ".txt", ".sh")
IGNORADOS = ("__pycache__", ".pytest_cache", ".git")

# As tres raizes do acervo. `07_p1b` entra porque e onde um runner grava
# evidencia de preflight, e ficava de fora do guarda antigo.
RAIZES = tuple(os.path.join(_RAIZ_REPO, n)
               for n in ("05_p0", "06_p1a", "07_p1b"))


def alvos_de_usuario() -> dict:
    """Rotulo -> token, derivados da MESMA fonte que a redacao usa.

    Nao ha literal nenhum aqui: numa estacao com outro usuario o guarda
    procura o nome DAQUELA estacao. Era essa a cegueira do guarda antigo.
    """
    usuario = contencao._USUARIO_LOCAL
    curto = contencao.forma_8_3(usuario)
    return {"usuario-local": usuario,
            "usuario-local-8.3": curto,
            "usuario-local-8.3-sem-sufixo": curto.replace("~1", "")}


def varrer(raiz: str) -> tuple:
    """(achados, arquivos_lidos) — PII de usuario e e-mail sob a raiz."""
    alvos = alvos_de_usuario()
    achados = []
    lidos = []
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in IGNORADOS]
        for nome in sorted(arquivos):
            if not nome.lower().endswith(EXTENSOES):
                continue
            caminho = os.path.join(base, nome)
            try:
                with open(caminho, encoding="utf-8", errors="replace") as f:
                    texto = f.read()
            except OSError:
                continue
            rel = os.path.relpath(caminho, raiz)
            lidos.append(rel)
            for rotulo, token in alvos.items():
                if token in texto:
                    achados.append(f"{rel}: {rotulo}")
            if PADRAO_EMAIL.search(texto):
                achados.append(f"{rel}: email")
    return achados, lidos


class ZeroPiiNasTresRaizes(unittest.TestCase):
    """A propriedade afirmada, agora sobre o acervo inteiro."""

    def test_nenhuma_raiz_do_acervo_carrega_pii(self):
        for raiz in RAIZES:
            with self.subTest(raiz=os.path.basename(raiz)):
                achados, _ = varrer(raiz)
                self.assertEqual(achados, [], f"PII em: {achados}")


class AVarreduraDetectaOQuePlanta(unittest.TestCase):
    """CONTROLE POSITIVO — a metade que `P1A-45` nao tinha."""

    def _com_arquivo(self, nome: str, conteudo: str):
        tmp = tempfile.TemporaryDirectory(prefix="p1a39-pii-")
        self.addCleanup(tmp.cleanup)
        with open(os.path.join(tmp.name, nome), "w", encoding="utf-8") as f:
            f.write(conteudo)
        return varrer(tmp.name)[0]

    def test_usuario_local_plantado_e_detectado_nas_tres_formas(self):
        for rotulo, token in alvos_de_usuario().items():
            with self.subTest(forma=rotulo):
                achados = self._com_arquivo(
                    "artefato.md", f"caminho do lab: {token}/projeto\n")
                self.assertTrue(achados, f"forma {rotulo} NAO detectada")

    def test_email_plantado_e_detectado(self):
        # Montado por concatenacao para que este arquivo nao case com o
        # proprio padrao que ele varre — o mesmo cuidado do irmao.
        amostra = "contato" + "@" + "exemplo" + ".org"
        self.assertTrue(self._com_arquivo("artefato.txt", amostra))

    def test_texto_limpo_nao_gera_achado(self):
        # CONTRAPROVA: uma varredura que acusasse sempre passaria em
        # todos os testes acima e reprovaria o acervo inteiro.
        self.assertEqual(
            self._com_arquivo("artefato.md",
                              "provider=codex resultado=SUPERVISED\n"), [])

    def test_extensao_fora_da_lista_nao_e_lida(self):
        # O limite declarado, exercido: se um dia `.jsonl` passar a ser
        # varrido, este teste fica vermelho e o limite muda com registro.
        token = alvos_de_usuario()["usuario-local"]
        self.assertEqual(self._com_arquivo("bruto.jsonl", token), [])

    def test_o_marcador_de_redacao_nao_e_confundido_com_pii(self):
        # `<USUARIO>` e o resultado CORRETO da redacao e aparece em
        # dezenas de artefatos. Se a varredura o acusasse, o guarda
        # reprovaria justamente os arquivos bem redigidos.
        self.assertEqual(
            self._com_arquivo("artefato.json",
                              '{"dir": "C:\\\\Users\\\\<USUARIO>\\\\x"}'), [])


class AVarreduraRealmenteLeArquivos(unittest.TestCase):
    """CONTROLE POSITIVO, segunda metade — guarda anti-varredura-vazia."""

    # Pisos MEDIDOS nesta missao, nao escolhidos: `07_p1b` e a raiz
    # pequena (10 arquivos de texto hoje), e um piso unico de 10 a
    # deixaria de fora pelo proprio tamanho.
    PISOS = {"05_p0": 30, "06_p1a": 50, "07_p1b": 5}

    def test_cada_raiz_le_um_numero_real_de_arquivos(self):
        for raiz in RAIZES:
            nome = os.path.basename(raiz)
            with self.subTest(raiz=nome):
                _, lidos = varrer(raiz)
                self.assertGreater(len(lidos), self.PISOS[nome])

    def test_arquivos_nominais_estao_entre_os_lidos(self):
        # Raiz errada, filtro amplo demais ou excecao engolida deixariam
        # a lista vazia e `assertEqual(achados, [])` verde para sempre.
        esperados = {"05_p0": os.path.join("ssc_p0", "kernel.py"),
                     "06_p1a": os.path.join("preflight", "economia.py"),
                     "07_p1b": "preflight_atual.py"}
        for raiz in RAIZES:
            nome = os.path.basename(raiz)
            with self.subTest(raiz=nome):
                _, lidos = varrer(raiz)
                self.assertIn(esperados[nome], lidos)

    def test_os_alvos_saem_da_mesma_fonte_que_a_redacao_usa(self):
        # A correcao de escopo 1, exercida: se alguem voltar a escrever
        # o nome a mao, os dois lados da politica podem divergir e o
        # guarda fica cego sem ruido.
        alvos = alvos_de_usuario()
        self.assertEqual(alvos["usuario-local"], contencao._USUARIO_LOCAL)
        self.assertEqual(alvos["usuario-local-8.3"],
                         contencao.forma_8_3(contencao._USUARIO_LOCAL))
        self.assertEqual(contencao._USUARIO_LOCAL,
                         os.path.basename(os.path.expanduser("~")))

    def test_a_varredura_alcanca_as_evidencias_gravadas_da_p1b(self):
        # `07_p1b/evidencias` e onde um runner grava de verdade: se a
        # raiz nova nao alcancasse os artefatos, ela seria decoracao.
        _, lidos = varrer(os.path.join(_RAIZ_REPO, "07_p1b"))
        self.assertTrue([r for r in lidos
                         if r.startswith("evidencias" + os.sep)],
                        "a varredura nao alcanca 07_p1b/evidencias")


if __name__ == "__main__":
    unittest.main()
