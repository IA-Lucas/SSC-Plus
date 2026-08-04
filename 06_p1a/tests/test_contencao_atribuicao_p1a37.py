"""Deteccao separada de atribuicao, e cobertura alem de RAIZ — MAJOR #3.

O DEFEITO, na voz do revisor independente que o manteve NAO-FECHADO:
*"`contencao.manifesto` cobre apenas `RAIZ` e exclui todo `locks/`; o
kimi segue capaz de alterar arquivos fora do repositorio, ou locks nao
verificados, sem aparecer em `mutacoes`"*.

E o achado que a propria P1-A.3.6 levantou contra o instrumento (§6):
`manifesto` NAO distingue escritor — qualquer mutacao na janela da
chamada era imputada ao revisor, e a corrida do codex foi reprovada por
escrita do OPERADOR. O instrumento era *cego para fora* e
*indiscriminado para dentro*.

O remedio especificado tem duas metades, e as duas estao aqui:
(a) ATRIBUICAO — `atribuir` separa o que tem escritor esperado (o lease
    da sessao operacional, reescrito a cada 30 s por construcao) do que
    nao tem. So o NAO ATRIBUIDO reprova;
(b) COBERTURA alem de `RAIZ` — `locks/` deixa de ser excluido e as
    fontes de config que a auditoria economica consome passam a ser
    fotografadas.

O CAMINHO QUE A OPERACAO PERCORRE. Em operacao quem fotografa e
`Vigilancia`, construida dentro do `main()` de cada runner de revisao, e
o valor que reprova a corrida e `contencao["violada"]`. Esta suite:
- exerce `Vigilancia` diretamente sobre arvores reais em disco;
- roda `revisao_p1a31.main()` DE VERDADE com reviewer falso, que e o
  unico caminho em que a reprovacao da corrida (`rc == 3`) acontece;
- varre os QUATRO runners exigindo que apontem para a MESMA classe.

A varredura dos quatro existe por causa do N4: primitiva corrigida nao
cobre ponto de chamada. Quatro copias do protocolo `manifesto`/
`mutacoes` foi o que havia antes, e e o mecanismo dos achados 7, 10 e 14.

O QUE ESTES TESTES NAO COBREM, declarado:
- a atribuicao e por CONVENCAO de caminho E de titular (P1-A.5, ordem
  2), nao prova de autoria. Um revisor que sobrescrevesse
  `locks/repositorio.lease` MANTENDO dentro dele o nome da sessao
  operacional ainda seria atribuido ao renovador. Isto e limite
  declarado no fonte e aqui, nao propriedade provada. O que deixou de
  passar — e ha teste — e o intruso que se nomeia, e o lease vencido;
- a cobertura fora do repositorio alcanca as fontes de config
  declaradas, e MAIS NADA. Escrita do revisor em qualquer outro caminho
  do disco continua invisivel — e o `NAO_VIGIADO` que o rotulo cita;
- nenhum CLI real e invocado: o "reviewer" e um `python -c`;
- nada aqui prova que o kimi respeite restricao alguma; prova-se
  deteccao e atribuicao, que e o que o mecanismo faz.
"""

import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

import apoio  # (insere 06_p1a no sys.path e traz `escrever_lock`)

_DIR_P1A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_DIR_P1A, "evidencias"))

import contencao  # noqa: E402

RUNNERS = ("revisao_p1a3", "revisao_p1a31", "revisao_p1a33",
           "revisao_p1a36")


def _carregar(nome):
    caminho = os.path.join(_DIR_P1A, "evidencias", f"{nome}.py")
    spec = importlib.util.spec_from_file_location(f"{nome}_sob_teste",
                                                  caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class _SaidaMuda:
    def write(self, *a, **k):
        return 0

    def flush(self):
        pass

    def reconfigure(self, *a, **k):
        pass


# P1-A.5, ordem 2: a copia local morreu; ver `apoio.escrever_lock`.
_escrever_lock = apoio.escrever_lock


class CoberturaAlemDaRaiz(unittest.TestCase):
    """(b) — `locks/` e as fontes de config deixam de ser ponto cego."""

    def test_escrita_em_locks_aparece_no_manifesto(self):
        with tempfile.TemporaryDirectory() as raiz:
            os.makedirs(os.path.join(raiz, "locks"))
            vig = contencao.Vigilancia(raiz, "sessao-x", alvos=())
            vig.abrir()
            with open(os.path.join(raiz, "locks", "outra.lease"), "w") as f:
                f.write("lease de outra sessao")
            medida = vig.fechar()
            self.assertTrue(medida["violada"])
            self.assertIn("criado: repositorio/locks/outra.lease",
                          medida["mutacoes_fora_do_descartavel"])

    def test_escrita_em_fonte_de_config_fora_do_repositorio_aparece(self):
        with tempfile.TemporaryDirectory() as raiz, \
                tempfile.TemporaryDirectory() as lar:
            alvo = os.path.join(lar, "settings.json")
            with open(alvo, "w", encoding="utf-8") as f:
                f.write("{}")
            vig = contencao.Vigilancia(raiz, "sessao-x", alvos=(alvo,))
            vig.abrir()
            with open(alvo, "w", encoding="utf-8") as f:
                f.write('{"api_key": "plantada"}')
            medida = vig.fechar()
            self.assertTrue(medida["violada"])
            self.assertEqual(medida["mutacoes_fora_do_descartavel"],
                             [f"alterado: fora/{alvo}"])

    def test_criacao_de_fonte_ausente_e_detectada(self):
        # Alvo AUSENTE entra como `<ausente>`: some-lo do manifesto
        # deixaria a CRIACAO de uma config PAYG passar sem alarme.
        with tempfile.TemporaryDirectory() as raiz, \
                tempfile.TemporaryDirectory() as lar:
            alvo = os.path.join(lar, "nao-existe.json")
            vig = contencao.Vigilancia(raiz, "sessao-x", alvos=(alvo,))
            self.assertEqual(vig.abrir()[f"fora/{alvo}"], "<ausente>")
            with open(alvo, "w", encoding="utf-8") as f:
                f.write('{"auto_topup": true}')
            medida = vig.fechar()
            self.assertTrue(medida["violada"])
            self.assertEqual(medida["mutacoes_fora_do_descartavel"],
                             [f"alterado: fora/{alvo}"])

    def test_a_lista_vigiada_cobre_as_fontes_que_a_auditoria_le(self):
        # Acoplamento: se `auditar_config` passar a ler uma fonte nova e
        # a lista vigiada nao acompanhar, isto fica vermelho — sem isso
        # a cobertura derivaria em silencio, que e o achado 7 outra vez.
        import leitores_config
        declaradas = set()
        for tipo, caminho in leitores_config.FONTES.values():
            declaradas.add(caminho)
            if tipo == "json" and caminho == "~/.codex/auth.json":
                declaradas.add("~/.codex/config.toml")  # segunda fonte
        self.assertEqual(set(contencao.ALVOS_VIGIADOS_FORA_DO_REPOSITORIO),
                         declaradas)

    def test_o_que_nao_e_vigiado_esta_declarado(self):
        with tempfile.TemporaryDirectory() as raiz, \
                tempfile.TemporaryDirectory() as fora:
            vig = contencao.Vigilancia(raiz, "sessao-x", alvos=())
            vig.abrir()
            with open(os.path.join(fora, "invisivel.txt"), "w") as f:
                f.write("escrita nao vigiada")
            medida = vig.fechar()
            self.assertFalse(medida["violada"])
            self.assertIn("fora do repositorio", medida["nao_vigiado"])


class AtribuicaoSeparadaDaDeteccao(unittest.TestCase):
    """(a) — detectar nao e imputar."""

    def test_lease_do_renovador_e_detectado_e_atribuido(self):
        with tempfile.TemporaryDirectory() as raiz:
            base = os.path.join(raiz, "locks")
            _escrever_lock(base, "p1a-ops", 1, time.time() + 600)
            vig = contencao.Vigilancia(raiz, "p1a-ops", alvos=())
            vig.abrir()
            _escrever_lock(base, "p1a-ops", 1, time.time() + 900)
            medida = vig.fechar()
            # DETECTADO — nao foi apagado por exclusao...
            self.assertIn("alterado: repositorio/locks/repositorio.lease",
                          medida["mutacoes_detectadas"])
            # ...e ATRIBUIDO, de modo que nao reprova a corrida.
            self.assertIn(
                "alterado: repositorio/locks/repositorio.lease",
                medida["mutacoes_atribuidas_ao_renovador"])
            self.assertEqual(medida["titular_do_escritor_no_fechamento"],
                             "p1a-ops")
            self.assertFalse(medida["violada"])

    def test_lease_reescrito_em_nome_de_OUTRA_sessao_nao_e_atribuido(self):
        # P1-A.5, ordem 2. Com um lease UNICO, atribuir so por caminho
        # abriria o buraco que este teste fecha: bastaria ao intruso
        # sobrescrever `repositorio.lease` para nao reprovar a corrida.
        # Aqui ele sobrescreve, no CAMINHO ESPERADO, e a corrida reprova
        # — porque o titular medido no fechamento nao e a sessao vigiada.
        with tempfile.TemporaryDirectory() as raiz:
            base = os.path.join(raiz, "locks")
            _escrever_lock(base, "p1a-ops", 1, time.time() + 600)
            vig = contencao.Vigilancia(raiz, "p1a-ops", alvos=())
            vig.abrir()
            _escrever_lock(base, "intrusa-ops", 1, time.time() + 600)
            medida = vig.fechar()
            self.assertEqual(medida["titular_do_escritor_no_fechamento"],
                             "intrusa-ops")
            self.assertTrue(medida["violada"])
            self.assertIn("alterado: repositorio/locks/repositorio.lease",
                          medida["mutacoes_fora_do_descartavel"])
            self.assertEqual(medida["mutacoes_atribuidas_ao_renovador"], [])

    def test_lease_que_morre_na_janela_nao_atribui_nada(self):
        # O outro ramo fail-closed: titular VENCIDO nao e titular. Sem
        # ele, uma janela em que o renovador morreu continuaria
        # atribuindo escrita a um escritor que ja nao existe.
        with tempfile.TemporaryDirectory() as raiz:
            base = os.path.join(raiz, "locks")
            _escrever_lock(base, "p1a-ops", 1, time.time() + 600)
            vig = contencao.Vigilancia(raiz, "p1a-ops", alvos=())
            vig.abrir()
            _escrever_lock(base, "p1a-ops", 1, time.time() - 1)
            medida = vig.fechar()
            self.assertIsNone(medida["titular_do_escritor_no_fechamento"])
            self.assertTrue(medida["violada"])
            self.assertEqual(medida["mutacoes_atribuidas_ao_renovador"], [])

    def test_atribuir_nao_engole_escrita_no_resto_do_repositorio(self):
        self.assertEqual(
            contencao.atribuir(
                ["criado: repositorio/codigo/backdoor.py",
                 "alterado: repositorio/locks/repositorio.lease"],
                "s", titular="s"),
            {"do_renovador":
                ["alterado: repositorio/locks/repositorio.lease"],
             "nao_atribuidas": ["criado: repositorio/codigo/backdoor.py"]})

    def test_atribuir_sem_titular_medido_nao_atribui_nada(self):
        # O default e fail-closed de proposito: quem nao mede o titular
        # nao atribui. Sem isto, um chamador que esquecesse o argumento
        # novo voltaria silenciosamente a atribuir so por caminho.
        self.assertEqual(
            contencao.atribuir(
                ["alterado: repositorio/locks/repositorio.lease"], "s"),
            {"do_renovador": [],
             "nao_atribuidas":
                ["alterado: repositorio/locks/repositorio.lease"]})


class OsQuatroRunnersUsamOMesmoProtocolo(unittest.TestCase):
    """N4 aplicado ao MAJOR #3: primitiva nao cobre ponto de chamada."""

    def test_todo_runner_aponta_para_a_mesma_classe(self):
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                modulo = _carregar(nome)
                self.assertIs(modulo.Vigilancia, contencao.Vigilancia)

    def test_nenhum_runner_guarda_copia_do_protocolo_antigo(self):
        # `manifesto`/`mutacoes` continuam existindo em `contencao` (a
        # `Vigilancia` os usa), mas nenhum runner pode chama-los direto:
        # e assim que as quatro copias divergiram.
        for nome in RUNNERS:
            with self.subTest(runner=nome):
                modulo = _carregar(nome)
                self.assertFalse(hasattr(modulo, "manifesto"))
                self.assertFalse(hasattr(modulo, "mutacoes"))


class FimAFimAReprovacaoDaCorrida(unittest.TestCase):
    """O que reprova a corrida e `rc == 3` — e so o NAO ATRIBUIDO."""

    def _revisao(self, raiz, corpo_do_reviewer, sessao_extra=None):
        from pathlib import Path
        modulo = _carregar("revisao_p1a31")
        _escrever_lock(os.path.join(raiz, "locks"), modulo.SESSAO_LOCK, 4,
                       time.time() + 600)
        os.makedirs(os.path.join(raiz, "06_p1a"), exist_ok=True)
        agora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(os.path.join(raiz, "06_p1a", "tiers_declarados.json"),
                  "w", encoding="utf-8") as f:
            json.dump({"validade_maxima_horas": 24,
                       "declaracoes": [{"provider_id": "kimi",
                                        "tier": "allegretto",
                                        "declarado_por": "proprietario",
                                        "declarado_em_utc": agora,
                                        "validade_horas": 24}]}, f)
        pacote = os.path.join(raiz, "pacote.txt")
        with open(pacote, "wb") as f:
            f.write(b"pacote de mentira\n")
        saida = Path(raiz) / "06_p1a" / "evidencias" / "revisao-p1a31"
        env_minimo = {k: os.environ[k] for k in
                      ("PATH", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
                       "PATHEXT") if k in os.environ}
        with mock.patch.dict(os.environ, env_minimo, clear=True), \
                mock.patch.object(contencao,
                                  "ALVOS_VIGIADOS_FORA_DO_REPOSITORIO",
                                  ()), \
                mock.patch.object(modulo, "RAIZ", Path(raiz)), \
                mock.patch.object(modulo, "SAIDA", saida), \
                mock.patch.object(modulo, "COMANDOS", {
                    "kimi": lambda tmp, skills, prompt: [
                        sys.executable, "-c", corpo_do_reviewer]}), \
                mock.patch.object(sys, "argv",
                                  ["revisao_p1a31.py", "kimi", pacote]), \
                mock.patch("sys.stdout", _SaidaMuda()):
            rc = modulo.main()
        gravados = sorted(os.listdir(saida))
        with open(os.path.join(saida, gravados[0]), encoding="utf-8") as f:
            return rc, json.load(f)

    def test_escrita_em_locks_agora_reprova_a_corrida(self):
        # O caso que a exclusao de `locks/` deixava passar: um reviewer
        # que planta um lease e nao aparecia em lugar nenhum.
        with tempfile.TemporaryDirectory() as raiz:
            os.makedirs(os.path.join(raiz, "locks"), exist_ok=True)
            alvo = os.path.join(raiz, "locks", "plantado.lease").replace(
                "\\", "\\\\")
            rc, evidencia = self._revisao(
                raiz, f"open(r'{alvo}', 'w').write('{{}}')")
            self.assertEqual(rc, 3)
            self.assertTrue(evidencia["contencao"]["violada"])
            self.assertIn(
                "criado: repositorio/locks/plantado.lease",
                evidencia["contencao"]["mutacoes_fora_do_descartavel"])

    def test_renovacao_do_lease_durante_a_janela_nao_reprova(self):
        # Contraprova da atribuicao: o renovador reescreve o lease no
        # meio da chamada — e isso NAO pode reprovar a corrida. Sem ela,
        # remover a exclusao de `locks/` teria trocado ponto cego por
        # alarme falso permanente.
        with tempfile.TemporaryDirectory() as raiz:
            from escritor_repositorio import caminho_lease
            caminho = caminho_lease(os.path.join(raiz, "locks")).replace(
                "\\", "\\\\")
            corpo = ("import json, time\n"
                     f"caminho = r'{caminho}'\n"
                     "d = json.load(open(caminho))\n"
                     "d['renovado_em'] = time.time()\n"
                     "d['expira_em'] = time.time() + 1200\n"
                     "json.dump(d, open(caminho, 'w'))\n")
            rc, evidencia = self._revisao(raiz, corpo)
            self.assertEqual(rc, 0)
            self.assertFalse(evidencia["contencao"]["violada"])
            self.assertTrue(
                evidencia["contencao"]["mutacoes_atribuidas_ao_renovador"],
                "a renovacao precisa ter sido DETECTADA e atribuida")

    def test_reviewer_bem_comportado_continua_nao_reprovando(self):
        with tempfile.TemporaryDirectory() as raiz:
            rc, evidencia = self._revisao(
                raiz, "open('rascunho.txt', 'w').write('dentro do tmp')")
            self.assertEqual(rc, 0)
            self.assertFalse(evidencia["contencao"]["violada"])
            self.assertEqual(
                evidencia["contencao"]["mutacoes_fora_do_descartavel"], [])


if __name__ == "__main__":
    unittest.main()
