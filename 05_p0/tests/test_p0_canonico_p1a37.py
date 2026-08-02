"""P0-01 `canonico.canonico` — o ramo de recusa, alcancado. FASE 3.

A varredura de guardas da P1-A.3.5 classificou este ponto SEM-TESTE, com
a medicao ao lado: *"nenhuma linha de recusa alcancada; nenhum teste
nomeia ErroCanonico"*. A P1-A.3.5 pulou os 16 pontos da P0 por volume
(§5, P3), e este e o primeiro deles.

O CASO QUE OCORRE. `canonico` e a serializacao de TODO objeto que vira
hash, id de evento ou payload do EventLog. O ramo de recusa ocorre
quando um objeto nao-serializavel chega ate ali — o que acontece de
verdade quando um campo de contrato recebe um valor que o autor supunha
JSON e nao e (um `set`, um `bytes`, um `datetime`, um objeto qualquer) —
e quando um float nao-finito entra num campo numerico. As duas familias
sao exercidas por VALOR, com a funcao de producao, nao por um duplo.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem `json.dumps` levantando por PROFUNDIDADE (recursao) nem por
  ciclo de referencia: o Python levanta `RecursionError` e `ValueError`
  respectivamente, e so o segundo cai em `ErroCanonico`;
- nao afirmam nada sobre a ORDEM canonica alem do que ja e coberto por
  `test_contratos.py`; o objeto aqui e o ramo de RECUSA;
- nao cobrem `sha256_de` sobre objeto invalido por outro caminho que
  nao `canonico`.
"""

import math
import unittest
from datetime import datetime, timezone

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0.canonico import ErroCanonico, canonico, sha256_de


class RecusaDoCanonico(unittest.TestCase):

    def test_objeto_nao_serializavel_levanta_erro_canonico(self):
        class Qualquer:
            pass

        for valor in (Qualquer(), {1, 2}, b"bytes",
                      datetime(2026, 8, 1, tzinfo=timezone.utc)):
            with self.subTest(tipo=type(valor).__name__):
                with self.assertRaises(ErroCanonico) as ctx:
                    canonico({"campo": valor})
                self.assertIn("nao canonizavel", str(ctx.exception))

    def test_float_nao_finito_levanta_erro_canonico(self):
        # `allow_nan=False` existe para que NaN/Infinity nao entrem no
        # log: eles nao tem representacao em JSON estrito e quebrariam a
        # releitura por terceiro.
        for valor in (float("nan"), math.inf, -math.inf):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ErroCanonico):
                    canonico({"custo": valor})

    def test_chave_de_tipo_misto_levanta_erro_canonico(self):
        # `sort_keys=True` sobre chaves de tipos incomparaveis: o
        # `json.dumps` levanta TypeError, e o guarda o converte.
        with self.assertRaises(ErroCanonico):
            canonico({1: "a", "b": 2})

    def test_erro_canonico_e_um_value_error(self):
        # A hierarquia importa: quem captura ValueError na borda continua
        # capturando este erro, e nao ha caminho em que ele escape como
        # excecao nao tratada de outra familia.
        self.assertTrue(issubclass(ErroCanonico, ValueError))

    def test_a_causa_original_e_preservada(self):
        # `from exc`: sem a causa, o operador ve "nao canonizavel" e nao
        # sabe qual campo quebrou.
        with self.assertRaises(ErroCanonico) as ctx:
            canonico(object())
        self.assertIsNotNone(ctx.exception.__cause__)

    def test_sha256_de_propaga_a_recusa(self):
        # `sha256_de` e o ponto de chamada real: quase todo hash do
        # acervo passa por ele, nao por `canonico` direto.
        with self.assertRaises(ErroCanonico):
            sha256_de({"campo": {1, 2}})

    def test_objeto_valido_serializa_e_e_estavel(self):
        # Contraprova: sem ela, um `canonico` que levantasse sempre
        # passaria em tudo acima.
        obj = {"b": 1, "a": [1, 2, {"z": None, "y": True}]}
        self.assertEqual(canonico(obj),
                         b'{"a":[1,2,{"y":true,"z":null}],"b":1}')
        self.assertEqual(sha256_de(obj), sha256_de(dict(obj)))


if __name__ == "__main__":
    unittest.main()
