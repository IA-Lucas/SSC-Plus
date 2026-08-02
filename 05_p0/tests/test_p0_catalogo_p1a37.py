"""P0-05 `catalogo.Catalogo` — os tres ramos que faltavam. FASE 3.

A varredura mediu **1 de 4 ramos alcancados**: `resolver()` era dirigido
por `router`/`execution` no fluxo feliz, e as recusas ficavam fora.

O CASO QUE OCORRE. O catalogo e FECHADO: ele existe para que nenhum
executor entre no acervo sem estar declarado. Os quatro ramos:
- alias que aponta para fora do catalogo — recusado na CONSTRUCAO, e
  isto importa porque um catalogo mal formado nao pode nascer;
- executor fora do catalogo;
- provedor que diverge do catalogo para a mesma chave — o caso de quem
  pede `provedor-a/modelo-x` quando `modelo-x` pertence a outro;
- effort nao suportado pelo executor.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem `atende()`, que classifica capacidade e nao recusa
  executor — e outro ponto, com cobertura em `test_policy.py`;
- nao afirmam que o catalogo REAL do laboratorio esteja correto: o que
  se mede e o comportamento da classe, com catalogos montados no teste;
- `hash_catalogo` e usado como identidade, e a sua estabilidade e
  medida aqui apenas de forma incidental.
"""

import unittest

import apoio  # noqa: F401  (insere 05_p0 no sys.path)
from ssc_p0.catalogo import Catalogo, ExecutorDesconhecido

EXECUTORES = [
    {"executor_id": "prov-a/modelo-x", "provedor": "prov-a",
     "modelo": "modelo-x", "ferramenta": "falsa", "efforts": ["alto", "baixo"]},
    {"executor_id": "prov-b/modelo-y", "provedor": "prov-b",
     "modelo": "modelo-y", "ferramenta": "falsa", "efforts": ["alto"]},
]


def catalogo(aliases=None) -> Catalogo:
    return Catalogo([dict(e) for e in EXECUTORES], aliases)


class RecusasDoCatalogoFechado(unittest.TestCase):

    def test_alias_para_fora_do_catalogo_nao_deixa_o_catalogo_nascer(self):
        # Recusar na construcao e mais forte que recusar no uso: um
        # catalogo mal formado nunca chega a resolver nada.
        with self.assertRaises(ExecutorDesconhecido) as ctx:
            catalogo({"apelido": "prov-z/modelo-inexistente"})
        self.assertIn("aponta fora do catalogo", str(ctx.exception))

    def test_executor_fora_do_catalogo_e_recusado(self):
        with self.assertRaises(ExecutorDesconhecido) as ctx:
            catalogo().resolver({"provedor": "prov-z", "modelo": "modelo-q",
                                 "effort": "alto"})
        self.assertIn("fora do catalogo", str(ctx.exception))

    def test_provedor_que_diverge_do_catalogo_e_recusado(self):
        # `modelo-y` existe, mas pertence a `prov-b`. Pedir por `prov-a`
        # e o caso em que um executor seria usado sob outro provedor —
        # e a evidencia de proveniencia ficaria errada.
        cat = catalogo()
        cat.executores["prov-a/modelo-y"] = {
            "executor_id": "prov-a/modelo-y", "provedor": "prov-b",
            "modelo": "modelo-y", "ferramenta": "falsa", "efforts": ["alto"]}
        with self.assertRaises(ExecutorDesconhecido) as ctx:
            cat.resolver({"provedor": "prov-a", "modelo": "modelo-y",
                          "effort": "alto"})
        self.assertIn("diverge do catalogo", str(ctx.exception))

    def test_effort_nao_suportado_e_recusado(self):
        for effort in ("maximo", None, "", "ALTO"):
            with self.subTest(effort=repr(effort)):
                with self.assertRaises(ExecutorDesconhecido) as ctx:
                    catalogo().resolver({"provedor": "prov-b",
                                         "modelo": "modelo-y",
                                         "effort": effort})
                self.assertIn("nao suportado", str(ctx.exception))

    def test_resolucao_legitima_atravessa(self):
        # Contraprova: sem ela, um catalogo que recusasse sempre passaria
        # em todos os testes acima.
        resolvido, alias_usado = catalogo().resolver(
            {"provedor": "prov-a", "modelo": "modelo-x", "effort": "alto"})
        self.assertFalse(alias_usado)
        self.assertEqual(resolvido["executor_id"], "prov-a/modelo-x")
        self.assertEqual(resolvido["effort"], "alto")

    def test_alias_registrado_resolve_e_se_declara(self):
        # A outra metade: alias legitimo tem de funcionar E aparecer como
        # alias — usar um alias sem dizer que usou esconde proveniencia.
        cat = catalogo({"apelido-x": "prov-a/modelo-x"})
        resolvido, alias_usado = cat.resolver(
            {"provedor": "prov-a", "modelo": "apelido-x", "effort": "baixo"})
        self.assertTrue(alias_usado)
        self.assertEqual(resolvido["modelo"], "modelo-x")


if __name__ == "__main__":
    unittest.main()
