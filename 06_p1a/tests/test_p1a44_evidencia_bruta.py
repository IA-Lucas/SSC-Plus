"""A evidencia bruta sai do lab e vira objeto recontavel — P1A4-4.

O DEFEITO, na voz do revisor: *"a receita recompoe numeros com insumos
TESTEMUNHAIS; nao permite recontar respostas alternativas nem a corrida
sem recibo. Remedio: gravar a evidencia bruta que falta"*. A raiz: a
evidencia vivia SO no lab, runtime que o Git ignora — e a P1-A.6 provou
que lab morre (destruiu o unico da P2, com 1 teste e 5 subtests).

O CAMINHO QUE A OPERACAO PERCORRE: o runner REAL com sensor falso
produz a cadeia (EventLog + CAS), e `exportar_bruto` le DELA — a mesma
`EvidencePlane` da medicao. O vizinho recusado seria montar o manifesto
a mao e testar o parser dele.

O QUE ESTES TESTES NAO COBREM, declarado:

- a corrida contra provedor real (o sensor e falso; o conteudo real ja
  atravessou este caminho nas corridas de 2026-08-12);
- o fluxo controlado NAO exporta brutos (so o caminho de medicao liga o
  parametro) — ausencia declarada, nao esquecida;
- os tamanhos ORIGINAIS no manifesto sao declaracao assinada pelo
  processo que exportou, nao recontagem: o que se reconta e o objeto
  REDIGIDO. O delta esta no manifesto para quem quiser a conta.
"""

import getpass
import hashlib
import json
import os
import sys
import tempfile
import unittest

import apoio  # noqa: F401  (insere 06_p1a no sys.path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for _d in ("05_p0", "08_p2", os.path.join("06_p1a", "evidencias")):
    _c = os.path.join(_RAIZ, _d)
    if _c not in sys.path:
        sys.path.insert(0, _c)

import contencao  # noqa: E402
import medidor  # noqa: E402
import runner_p2  # noqa: E402
from test_p2_runner_p2 import SensorObrigatorio, preflight_real  # noqa: E402


class _CorridaExportada(unittest.TestCase):
    """Uma corrida real do runner (sensor falso) com export ligado."""

    RESPOSTA = ("resposta com o usuario {usuario} e o caminho "
                "C:\\Users\\{usuario}\\segredo.txt dentro dela")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="p1a44-")
        self.addCleanup(self._tmp.cleanup)
        self.raiz_lab = os.path.join(self._tmp.name, "lab")
        self.destino = os.path.join(self._tmp.name, "brutos")
        vigia_arvore = os.path.join(self._tmp.name, "vigiado")
        os.makedirs(vigia_arvore)
        usuario = getpass.getuser()
        sensor = SensorObrigatorio(
            codex=(0, self.RESPOSTA.format(usuario=usuario), ""))
        self.registro = runner_p2.executar(
            tarefa="responda com a palavra pronto",
            criterio="resposta nao vazia",
            preflight=preflight_real(),
            raiz_lab=self.raiz_lab, sensor=sensor,
            vigia=contencao.Vigilancia(vigia_arvore, "sessao-de-teste",
                                       alvos=()),
            contexto_workspace=False,
            exportar_brutos=self.destino)

    def manifesto(self) -> tuple:
        dir_export = os.path.join(self.destino,
                                  self.registro["work_unit_id"])
        with open(os.path.join(dir_export, "manifesto.json"),
                  encoding="utf-8") as f:
            return dir_export, json.load(f)


class ExportaDaCadeiaVerificada(_CorridaExportada):
    def test_manifesto_carrega_entrada_e_saida_com_as_duas_medidas(self):
        self.assertEqual(self.registro["status"], "sucesso")
        _, manifesto = self.manifesto()
        papeis = sorted(o["papel"] for o in manifesto["objetos"].values())
        self.assertEqual(papeis, ["entrada", "saida"])
        for nome, objeto in manifesto["objetos"].items():
            with self.subTest(objeto=nome):
                for campo in ("sha256_original", "tamanhos_originais",
                              "sha256_redigido", "tamanhos_redigidos",
                              "delta_redacao"):
                    self.assertIn(campo, objeto)

    def test_o_bruto_versionavel_nao_carrega_o_usuario_da_estacao(self):
        # O guarda ZeroPii deriva o alvo de quem roda; um export com o
        # usuario dentro reprovaria o acervo no primeiro commit.
        dir_export, manifesto = self.manifesto()
        usuario = getpass.getuser()
        for objeto in manifesto["objetos"].values():
            with self.subTest(arquivo=objeto["arquivo"]):
                with open(os.path.join(dir_export, objeto["arquivo"]),
                          encoding="utf-8") as f:
                    conteudo = f.read()
                self.assertNotIn(usuario, conteudo)

    def test_o_hash_do_manifesto_e_o_do_arquivo_gravado(self):
        dir_export, manifesto = self.manifesto()
        for objeto in manifesto["objetos"].values():
            with self.subTest(arquivo=objeto["arquivo"]):
                with open(os.path.join(dir_export, objeto["arquivo"]),
                          "rb") as f:
                    dados = f.read()
                self.assertEqual(hashlib.sha256(dados).hexdigest(),
                                 objeto["sha256_redigido"])

    def test_a_entrada_exportada_e_a_real_e_nao_a_truncada_da_cadeia(self):
        _, manifesto = self.manifesto()
        entrada = manifesto["objetos"]["entrada"]
        self.assertEqual(entrada["procedencia"], "medido-processo")


class ReceitaRecontaDoBruto(_CorridaExportada):
    def _spec_da_saida(self) -> tuple:
        dir_export, manifesto = self.manifesto()
        nome = next(n for n, o in manifesto["objetos"].items()
                    if o["papel"] == "saida")
        rel = os.path.relpath(os.path.join(dir_export, "manifesto.json"),
                              self._tmp.name)
        return ({"origem": "bruto", "manifesto": rel, "objeto": nome},
                dir_export, manifesto["objetos"][nome])

    def test_reconta_o_objeto_redigido_e_declara_o_original(self):
        spec, dir_export, objeto = self._spec_da_saida()
        insumo = medidor._resolver_insumo(spec, raiz=self._tmp.name)
        self.assertTrue(insumo["reproduzido"])
        self.assertEqual(insumo["procedencia"], "medido-bruto-redigido")
        self.assertEqual(
            {u: insumo[u] for u in medidor.UNIDADES},
            objeto["tamanhos_redigidos"],
            "a recontagem nao bate com o que o manifesto declara")
        self.assertEqual(insumo["originais_declarados"],
                         objeto["tamanhos_originais"])

    def test_objeto_adulterado_reprova_em_vez_de_recontar(self):
        spec, dir_export, objeto = self._spec_da_saida()
        caminho = os.path.join(dir_export, objeto["arquivo"])
        with open(caminho, "ab") as f:
            f.write(b"um byte a mais")
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo(spec, raiz=self._tmp.name)

    def test_ancora_de_recibo_corrobora_o_original_declarado(self):
        # Residuo da P1-A.10: o sha do original era declaracao solitaria
        # do exportador. Com um recibo independente carregando o mesmo
        # hash, viram DOIS artefatos que precisam concordar.
        spec, dir_export, objeto = self._spec_da_saida()
        recibo = os.path.join(self._tmp.name, "recibo.json")
        with open(recibo, "w", encoding="utf-8") as f:
            json.dump({"sha256": objeto["sha256_original"]}, f)
        spec["recibo"] = "recibo.json"
        spec["trilha"] = ["sha256"]
        insumo = medidor._resolver_insumo(spec, raiz=self._tmp.name)
        self.assertEqual(insumo["procedencia"],
                         "medido-bruto-redigido+ancora-recibo")

    def test_ancora_divergente_reprova_em_vez_de_recontar(self):
        spec, dir_export, objeto = self._spec_da_saida()
        recibo = os.path.join(self._tmp.name, "recibo.json")
        with open(recibo, "w", encoding="utf-8") as f:
            json.dump({"sha256": "0" * 64}, f)
        spec["recibo"] = "recibo.json"
        spec["trilha"] = ["sha256"]
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo(spec, raiz=self._tmp.name)

    def test_objeto_ausente_do_manifesto_reprova(self):
        spec, _, _ = self._spec_da_saida()
        spec["objeto"] = "nao-existe"
        with self.assertRaises(medidor.ReceitaInvalida):
            medidor._resolver_insumo(spec, raiz=self._tmp.name)


if __name__ == "__main__":
    unittest.main()
