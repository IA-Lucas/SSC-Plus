"""Zero escrita FORA da raiz — com testemunha, nao com `os.walk` — P1-A.3.9.

MECANISMO (c) da FASE 2 da P1-A.3.8: *sem controle positivo / escopo
menor que a propriedade afirmada — o guarda passaria mesmo cego*. Guarda
`P0-28`, e a linha da remedicao e literal:

    `os.walk` e real, mas percorre SO `base` — o proprio pai do lab.
    Uma escrita FORA de `base` e invisivel, e a propriedade afirmada e
    "zero escrita externa".
    Remedio: instantaneo SHA-256 de um diretorio-testemunha antes/depois,
    o padrao que `test_isolamento.VarreduraNaoTocaOSistemaDeArquivos`
    ja usa.

O guarda historico (`test_seguranca.test_zero_escrita_externa_tudo_sob_a
_raiz`) NAO foi editado — registro aditivo. Ele prova o que sempre
provou: todo arquivo criado DENTRO de `base` esta sob a raiz declarada.
O que faltava, e o que este arquivo mede, e o outro lado: nada foi
escrito FORA.

## O que a testemunha pode e o que ela nao pode

Nenhum teste prova "zero escrita no disco inteiro" — varrer o disco e
inviavel, e afirmar a propriedade sem medir e exatamente o que o
mecanismo (c) descreve. O que se mede aqui e um conjunto de raizes
DECLARADO, e o alcance de cada uma esta dito por extenso:

1. **o PAI inteiro, menos o laboratorio da corrida** — com um diretorio
   testemunha semeado dentro dele. Pega a fuga mais provavel: caminho
   relativo que sobe um nivel (`..`) e escreve ao lado. E exatamente o
   que um `os.walk` restrito a `base` nao pode ver;
2. **`05_p0/ssc_p0`** — a arvore de fontes da propria camada. Pega o
   caso em que a sessao escreve de volta no codigo;
3. **`05_p0/saidas`, exceto `labs/`** — os relatorios versionados.
   `labs/` fica de fora porque e justamente onde a corrida DEVE
   escrever.

**FORA DO ALCANCE, declarado**: todo o resto do disco. Uma escrita em
`C:\\Windows`, no home do usuario ou em qualquer caminho fora das tres
raizes acima NAO e detectada por este mecanismo. E limite conhecido, e
nao propriedade — a mesma honestidade de rotulo que `contencao.
NAO_VIGIADO` ja pratica do outro lado.

## CONTROLE POSITIVO

O irmao `ZeroSegredoNosArtefatos` tem duas metades que `P0-28` nao
tinha: um caso plantado que PRECISA ser detectado, e um guarda de que a
varredura tem alcance real. As duas estao aqui. Sem elas, um instantaneo
que devolvesse `{}` — por raiz errada, por filtro amplo demais, por
excecao engolida — passaria em silencio, que e a definicao do mecanismo
(c).

## O QUE ESTES TESTES NAO COBREM, declarado

- **so o alcance declarado acima**; fora dele nada e afirmado;
- **escrita e leitura sao coisas diferentes**: nada aqui diz que a
  sessao nao LEU arquivo externo — isso e objeto de `resolver_contido` e
  de `test_seguranca`;
- **arquivo criado e apagado dentro da mesma corrida e invisivel** ao
  instantaneo antes/depois, por construcao;
- **metadados nao entram**: o instantaneo e do CONTEUDO (SHA-256), nao
  de mtime nem de permissao;
- nada se afirma sobre concorrencia: se outro processo escrever numa das
  raizes durante a corrida, o teste acusa — e acusar e o comportamento
  correto de um guarda de escrita externa.
"""

import hashlib
import os
import subprocess
import unittest
import uuid

import apoio
from ssc_p0.kernel import SessionKernel

_DIR_P0 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAIZ_REPO = os.path.dirname(_DIR_P0)


def _tem_git() -> bool:
    try:
        return subprocess.run(["git", "rev-parse", "--git-dir"],
                              cwd=_RAIZ_REPO,
                              capture_output=True).returncode == 0
    except OSError:
        return False


def _nao_rastreados_em(relativo: str) -> list:
    """Caminhos NAO RASTREADOS sob `relativo`, na visao do Git.

    `labs/` esta no `.gitignore`, de modo que a escrita legitima da
    corrida nao aparece aqui e a escrita externa aparece — a medicao
    independe da ordem em que os testes rodam.
    """
    saida = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--",
         relativo], cwd=_RAIZ_REPO, capture_output=True, text=True)
    return sorted(linha[3:].strip().strip('"')
                  for linha in saida.stdout.splitlines()
                  if linha.startswith("??"))

# Raizes testemunhas FORA do laboratorio da corrida. `labs/` sai da
# terceira porque e onde a corrida deve escrever.
RAIZ_FONTES = os.path.join(_DIR_P0, "ssc_p0")
RAIZ_SAIDAS = os.path.join(_DIR_P0, "saidas")
IGNORADOS = ("__pycache__", "labs")


def _instantaneo(raiz: str, excluir: str | None = None) -> dict:
    """Caminho relativo -> sha256 de todo arquivo sob a raiz.

    `excluir` tira UM subdiretorio da varredura pelo nome — usado para
    deixar de fora o laboratorio da propria corrida, que e onde escrever
    e correto.
    """
    estado = {}
    if not os.path.isdir(raiz):
        return estado
    for base, dirs, arquivos in os.walk(raiz):
        dirs[:] = [d for d in dirs
                   if d not in IGNORADOS and d != excluir]
        for nome in sorted(arquivos):
            caminho = os.path.join(base, nome)
            try:
                with open(caminho, "rb") as fh:
                    dados = fh.read()
            except OSError:
                # Arquivo que sumiu entre o listar e o ler entra no
                # instantaneo como AUSENTE, nunca como inexistente: um
                # erro engolido aqui e cegueira, que e o defeito.
                estado[os.path.relpath(caminho, raiz)] = "<ILEGIVEL>"
                continue
            estado[os.path.relpath(caminho, raiz)] = \
                hashlib.sha256(dados).hexdigest()
    return estado


class ZeroEscritaForaDaRaizDeclarada(unittest.TestCase):
    """Instantaneo SHA-256 das raizes testemunhas, antes e depois."""

    @classmethod
    def setUpClass(cls):
        # DEFEITO ACHADO AO MEDIR, nesta missao. A primeira versao deste
        # arquivo tirava o instantaneo "antes" DENTRO de cada teste. Uma
        # escrita externa plantada em `gravar_checkpoint` escapou: o
        # metodo que roda antes na ordem alfabetica ja a criava, de modo
        # que ela ja estava no "antes" e a segunda gravacao, de conteudo
        # identico, nao mudava o SHA. MEDIDO: fuga para `05_p0/saidas`
        # ficava 299/299 VERDE.
        #
        # As raizes que NAO dependem do descartavel da corrida passam a
        # ter a linha de base tirada UMA vez, antes de qualquer corrida
        # desta classe.
        cls.base_externa = {"ssc_p0": _instantaneo(RAIZ_FONTES),
                            "saidas": _instantaneo(RAIZ_SAIDAS)}

    def setUp(self):
        self.pai = os.path.join(apoio.DIR_TESTS, uuid.uuid4().hex)
        self.base = os.path.join(self.pai, "lab-da-corrida")
        self.testemunha = os.path.join(self.pai, "testemunha")
        os.makedirs(self.testemunha, exist_ok=True)
        os.makedirs(os.path.join(self.testemunha, "sub"), exist_ok=True)
        for rel, dados in (("marco.txt", b"testemunha do P1-A.3.9"),
                           ("vazio.bin", b""),
                           (os.path.join("sub", "fundo.txt"), b"nivel 2")):
            with open(os.path.join(self.testemunha, rel), "wb") as f:
                f.write(dados)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.pai, ignore_errors=True)

    def _corrida_completa(self):
        """O MESMO fluxo que o guarda historico exerce, sem atalho.

        Fluxo feliz + checkpoint + suspensao + crash + retomada: e o
        caminho mais longo que a sessao percorre, e portanto o que mais
        toca o disco. Devolve `(raiz_do_lab, instantaneo_de_base)` — o
        instantaneo e tirado ANTES da limpeza, que apaga `base` inteiro.
        """
        lab = apoio.novo_lab(self.base)
        try:
            apoio.fluxo_sucesso(lab)
            lab.kernel.gravar_checkpoint()
            lab.kernel.suspender()
            lab.kernel._simular_crash()
            k2 = SessionKernel.retomar(lab.raiz, lab.envelope.sessao_id,
                                       relogio=lab.relogio)
            k2.fechar()
            return lab.raiz, _instantaneo(self.base)
        finally:
            apoio.limpar_lab(lab)

    def test_a_corrida_nao_toca_nenhuma_raiz_testemunha(self):
        # O pai e por-teste (o descartavel nasce e morre aqui); as duas
        # raizes fixas comparam contra a linha de base da CLASSE, tirada
        # antes de qualquer corrida — ver a nota em `setUpClass`.
        pai_antes = _instantaneo(self.pai, os.path.basename(self.base))
        self._corrida_completa()
        self.assertEqual(
            _instantaneo(self.pai, os.path.basename(self.base)), pai_antes,
            "escrita FORA do laboratorio, dentro do pai — a fuga por "
            "caminho relativo que o os.walk restrito a base nao ve")
        for rotulo, raiz in (("ssc_p0", RAIZ_FONTES),
                             ("saidas", RAIZ_SAIDAS)):
            with self.subTest(raiz=rotulo):
                self.assertEqual(
                    _instantaneo(raiz), self.base_externa[rotulo],
                    f"escrita FORA da raiz declarada em {rotulo} ({raiz})")

    def test_nenhum_arquivo_novo_aparece_sob_saidas_fora_de_labs(self):
        # Terceira medicao, INDEPENDENTE de ordem de teste: o Git ve
        # arquivo novo em `05_p0/saidas` como NAO RASTREADO, e `labs/`
        # esta no .gitignore — logo a corrida legitima nao aparece e uma
        # escrita externa aparece, tenha ela acontecido em que metodo
        # for. Modificacao de arquivo JA rastreado nao e objeto aqui: o
        # ruido conhecido de `prova_central.json` e dessa classe.
        if not _tem_git():
            self.skipTest("repositorio git indisponivel")
        self._corrida_completa()
        novos = _nao_rastreados_em("05_p0/saidas")
        self.assertEqual(novos, [], f"arquivo novo fora de labs/: {novos}")

    def test_o_git_enxerga_arquivo_novo_sob_saidas(self):
        # CONTROLE POSITIVO da medicao acima: sem ele, um `git status`
        # que devolvesse vazio por caminho errado ou por erro engolido
        # deixaria o guarda cego para sempre.
        if not _tem_git():
            self.skipTest("repositorio git indisponivel")
        plantado = os.path.join(RAIZ_SAIDAS, "intruso-p1a39.json")
        with open(plantado, "w", encoding="utf-8") as f:
            f.write("{}")
        try:
            self.assertIn("05_p0/saidas/intruso-p1a39.json",
                          _nao_rastreados_em("05_p0/saidas"))
        finally:
            os.remove(plantado)
        self.assertEqual(_nao_rastreados_em("05_p0/saidas"), [])

    def test_labs_nao_aparece_para_o_git_e_por_isso_nao_gera_alarme(self):
        # A outra ponta do controle positivo: se `labs/` deixasse de ser
        # ignorado, a medicao acima acusaria toda corrida legitima e
        # seria desligada por ruido — que e como um guarda morre.
        if not _tem_git():
            self.skipTest("repositorio git indisponivel")
        self._corrida_completa()
        self.assertTrue(os.path.isdir(os.path.join(RAIZ_SAIDAS, "labs")),
                        "labs/ nao existe — a corrida nao escreveu nada")
        self.assertEqual(_nao_rastreados_em("05_p0/saidas/labs"), [])

    def test_a_corrida_escreve_de_fato_dentro_do_laboratorio(self):
        # DISCRIMINADOR. Sem ele, uma corrida que nao fizesse nada
        # passaria no teste acima — "zero escrita externa" seria
        # trivialmente verdadeiro porque nao houve escrita nenhuma.
        antes = _instantaneo(self.base)
        raiz_lab, depois = self._corrida_completa()
        self.assertNotEqual(depois, antes)
        self.assertTrue(depois, "a corrida nao gravou um unico arquivo")
        for rel in depois:
            caminho = os.path.realpath(os.path.join(self.base, rel))
            self.assertTrue(
                os.path.normcase(caminho).startswith(
                    os.path.normcase(os.path.realpath(raiz_lab))),
                f"arquivo fora da raiz declarada: {rel}")

    def test_o_instantaneo_detecta_arquivo_plantado(self):
        # CONTROLE POSITIVO, primeira metade — a que `P0-28` nao tinha.
        antes = _instantaneo(self.testemunha)
        plantado = os.path.join(self.testemunha, "intruso.txt")
        with open(plantado, "wb") as f:
            f.write(b"escrita externa simulada")
        self.assertNotEqual(_instantaneo(self.testemunha), antes)
        os.remove(plantado)
        self.assertEqual(_instantaneo(self.testemunha), antes)

    def test_o_instantaneo_detecta_conteudo_alterado_e_arquivo_removido(self):
        # Criar arquivo e o caso facil. Um guarda que so comparasse a
        # LISTA de nomes passaria na alteracao de conteudo, e um que so
        # olhasse os nomes presentes passaria na remocao.
        antes = _instantaneo(self.testemunha)
        alvo = os.path.join(self.testemunha, "marco.txt")
        with open(alvo, "ab") as f:
            f.write(b" alterado")
        self.assertNotEqual(_instantaneo(self.testemunha), antes)
        os.remove(alvo)
        depois = _instantaneo(self.testemunha)
        self.assertNotEqual(depois, antes)
        self.assertNotIn("marco.txt", depois)

    def test_a_varredura_das_raizes_tem_alcance_real(self):
        # CONTROLE POSITIVO, segunda metade: guarda anti-varredura-vazia,
        # no padrao de `ZeroSegredoNosArtefatos.test_a_varredura_
        # realmente_le_arquivos`. Raiz errada devolve `{}` e todo
        # `assertEqual` acima ficaria verde para sempre.
        self.assertEqual(len(_instantaneo(self.testemunha)), 3)
        fontes = _instantaneo(RAIZ_FONTES)
        self.assertGreater(len(fontes), 10)
        self.assertIn("kernel.py", fontes)
        self.assertIn("frota.py", fontes)

    def test_labs_fica_fora_da_terceira_raiz_de_proposito(self):
        # O escopo declarado, exercido: `saidas/labs/` e onde a corrida
        # DEVE escrever, e incluir-lo faria o guarda acusar operacao
        # normal. Sem esta assercao a exclusao seria invisivel e
        # poderia crescer sem ninguem ver.
        saidas = _instantaneo(RAIZ_SAIDAS)
        self.assertFalse([rel for rel in saidas
                          if rel.split(os.sep)[0] == "labs"])
        self.assertTrue(saidas, "a terceira raiz testemunha esta vazia")


if __name__ == "__main__":
    unittest.main()
