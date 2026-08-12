"""P0-21 FASE 3 [6/6] — checkpoint, suspensao e retomada (IP-1 / IP-2).

  L817 checkpoint reprovado pelo Juiz 1        INALCANCAVEL (medido)
  L841 suspensao exige checkpoint gravado      ALCANCAVEL
  L883 selo do envelope divergente             ALCANCAVEL
  L893 evento de outra linhagem no replay      ALCANCAVEL
  L897 causado_por fora da cadeia no replay    ALCANCAVEL
  L902 payload ausente no CAS                  ALCANCAVEL
  L931 nenhum checkpoint para a sessao         ALCANCAVEL
  L963 ancora do checkpoint fora da cadeia     ALCANCAVEL

Estes sao os guardas de RETOMADA. Eles decidem se uma sessao que caiu
pode voltar — e a regra IP-1 e que retomar exige checkpoint valido MAIS
log verificado, **nunca inferencia**. IP-2 diz o que fazer quando algo
nao bate: a sessao **nao retoma**, e o chamador escalona. Um kernel que
retomasse "do jeito que der" produziria uma linhagem que ninguem pode
reconstruir — e a P0 inteira existe para que um terceiro possa.

## O CASO QUE OCORRE: corrupcao no disco, feita no disco

Nenhuma destas recusas e alcancada por objeto montado em memoria. Todas
partem de uma sessao REAL que rodou o fluxo inteiro, gravou checkpoint,
suspendeu e caiu (`_simular_crash`), e entao **o disco e mutado**:

- **L883**: o `.envelope.json` e reescrito com `politica_ref` trocado.
  O selo HMAC deixa de bater e a sessao nao retoma;
- **L893/L897**: o `.jsonl` e **reescrito inteiro**, com a cadeia
  `prev_event_hash` RECOMPUTADA linha a linha. Isto e importante: a
  cadeia do EventLog e SHA-256, nao HMAC — quem tem o arquivo pode
  refazer a cadeia. Os dois guardas sao exatamente a defesa contra isso:
  a cadeia ficar integra e o CONTEUDO nao pertencer a esta sessao;
- **L902**: o objeto do CAS referenciado pelo primeiro evento e
  APAGADO. E a corrupcao parcial — o log intacto apontando para bytes
  que sumiram;
- **L963**: o checkpoint e reescrito com uma ancora que nao existe na
  cadeia **e re-selado com a chave local**. Sem re-selar, quem recusa e
  o selo (outro guarda) e este ramo nunca e alcancado — a chave de selo
  e local, de modo que re-selar e o que um adversario com acesso ao
  disco faria. Registrar essa distincao e o que separa medir de supor;
- **L841/L931**: suspender sem checkpoint, e retomar sem checkpoint.

## O INALCANCAVEL, medido

`L817` levanta quando o Juiz 1 REPROVA o checkpoint que o proprio
kernel acabou de montar. Medido: numa sessao real
`gravar_checkpoint()` e sempre APROVADO — `_estado_refs()` preenche
`envelope`, `ultimo_evento_hash` e `seq` a partir do estado corrente, e
`seq` ja vale 1 na abertura, de modo que as tres condicoes do Juiz 1
estao satisfeitas por construcao. E defesa em profundidade contra
`_estado_refs` regredir. O que se exerce aqui e a invariante: um
checkpoint recem-gravado sai APROVADO e com `seq >= 1`.

O QUE ESTES TESTES NAO COBREM, declarado:
- nao cobrem `EventoTruncado`/`EventoAdulterado` vindos de
  `EventLog.verificar` — sao guardas do P0-15, ja cobertos;
- a re-selagem de L963 usa `kernel._selo`, que e o mesmo que ter a
  `chave_selo.bin` local. Nada aqui prova o que aconteceria se a chave
  fosse remota ou de hardware;
- attempts orfaos (`indeterminado`/`incerto`) sao consequencia da
  retomada bem-sucedida e nao sao destes ramos;
- nao se cobre retomada concorrente da mesma sessao (o lock de escritor
  unico e P0-26);
- nao se afirma nada sobre durabilidade real apos queda de energia.
"""

import glob
import json
import os
import unittest

import apoio
from ssc_p0.canonico import canonico, sha256_bytes
from ssc_p0.judge import Juiz1
from ssc_p0.kernel import (CheckpointInvalido, CorrupcaoDetectada,
                           EventoAdulterado, SessionKernel)


class RetomadaEIntegridade(unittest.TestCase):

    def setUp(self):
        self.lab = apoio.novo_lab()
        self.addCleanup(apoio.limpar_lab, self.lab)
        self.kernel = self.lab.kernel
        self.sid = self.lab.envelope.sessao_id
        self.raiz = self.lab.raiz

    # --- caminhos que nao dependem de corromper nada -------------------

    def test_suspender_sem_checkpoint_e_recusado(self):
        # IP-1: suspender sem ponto de retomada seria perder a sessao.
        with self.assertRaises(CheckpointInvalido) as ctx:
            self.kernel.suspender()
        self.assertIn("exige checkpoint gravado", str(ctx.exception))

    def test_retomar_sessao_sem_checkpoint_e_recusado(self):
        apoio.fluxo_sucesso(self.lab)
        self.kernel.fechar()
        with self.assertRaises(CheckpointInvalido) as ctx:
            SessionKernel.retomar(self.raiz, self.sid, relogio=self.lab.relogio)
        self.assertIn("nenhum checkpoint para a sessao", str(ctx.exception))

    def test_checkpoint_recem_gravado_sai_aprovado_pelo_juiz1(self):
        # A invariante de onde sai a inalcancabilidade de L817.
        apoio.fluxo_sucesso(self.lab)
        checkpoint = self.kernel.gravar_checkpoint()
        self.assertTrue(checkpoint.validacao["aprovado"])
        self.assertEqual(checkpoint.validacao["falhas"], [])
        self.assertGreaterEqual(checkpoint.estado_refs["seq"], 1)
        # E o proprio Juiz 1, reexecutado sobre o corpo, concorda.
        corpo = {c: v for c, v in checkpoint.to_dict().items()
                 if c not in ("validacao", "selo")}
        self.assertTrue(Juiz1.validar_checkpoint(corpo)["aprovado"])

    # --- corrupcao FEITA NO DISCO --------------------------------------

    def _sessao_caida(self):
        """Fluxo real + checkpoint + suspensao + queda."""
        apoio.fluxo_sucesso(self.lab)
        self.kernel.gravar_checkpoint()
        self.kernel.suspender()
        self.kernel._simular_crash()

    def _retomar(self):
        return SessionKernel.retomar(self.raiz, self.sid,
                                     relogio=self.lab.relogio)

    def _caminho_log(self) -> str:
        return os.path.join(self.raiz, "logs", f"{self.sid}.jsonl")

    def _caminho_envelope(self) -> str:
        return os.path.join(self.raiz, "sessoes",
                            f"{self.sid}.envelope.json")

    def test_retomada_legitima_funciona(self):
        # Contraprova, e ela vem PRIMEIRO: sem ela, tudo abaixo passaria
        # com um `retomar` que sempre levantasse.
        self._sessao_caida()
        k2 = self._retomar()
        self.addCleanup(k2.fechar)
        self.assertEqual(k2.envelope.sessao_id, self.sid)
        self.assertTrue(k2.work_units)

    def test_envelope_adulterado_nao_retoma(self):
        self._sessao_caida()
        with open(self._caminho_envelope(), "rb") as fluxo:
            dados = json.loads(fluxo.read())
        dados["politica_ref"] = "0" * 64
        with open(self._caminho_envelope(), "wb") as f:
            f.write(canonico(dados))
        with self.assertRaises(CheckpointInvalido) as ctx:
            self._retomar()
        self.assertIn("selo do envelope divergente", str(ctx.exception))

    def test_payload_apagado_do_cas_nao_retoma(self):
        self._sessao_caida()
        with open(self._caminho_log(), "rb") as fluxo:
            primeira = fluxo.read().split(b"\n")[0]
        ref = json.loads(primeira)["payload_ref"]
        alvo = os.path.join(self.raiz, "cas", "objetos", ref[:2], ref[2:4],
                            ref)
        self.assertTrue(os.path.exists(alvo), "o payload nem existia")
        os.remove(alvo)
        with self.assertRaises(CorrupcaoDetectada) as ctx:
            self._retomar()
        self.assertIn("payload ausente no CAS", str(ctx.exception))

    def _reescrever_log(self, muta) -> None:
        """Reescreve o log com a cadeia prev_event_hash RECOMPUTADA.

        A cadeia do EventLog e SHA-256, nao HMAC: quem tem o arquivo
        pode refaze-la. Isto encena exatamente esse adversario.
        """
        caminho = self._caminho_log()
        with open(caminho, "rb") as fluxo:
            linhas = fluxo.read().split(b"\n")
        linhas = [linha for linha in linhas if linha]
        eventos = [json.loads(linha) for linha in linhas]
        anterior = eventos[0]["prev_event_hash"]  # genese, preservada
        saida = []
        for i, evento in enumerate(eventos):
            muta(i, evento)
            evento["prev_event_hash"] = anterior
            linha = canonico(evento)
            saida.append(linha)
            anterior = sha256_bytes(linha)
        with open(caminho, "wb") as f:
            f.write(b"\n".join(saida) + b"\n")

    def test_evento_de_outra_linhagem_com_cadeia_integra_nao_retoma(self):
        self._sessao_caida()
        self._reescrever_log(
            lambda i, ev: ev.__setitem__("linhagem_id", "linhagem-alheia"))
        with self.assertRaises(EventoAdulterado) as ctx:
            self._retomar()
        self.assertIn("outra linhagem", str(ctx.exception))

    def test_causado_por_fora_da_cadeia_com_cadeia_integra_nao_retoma(self):
        self._sessao_caida()

        def apontar_para_o_nada(i, ev):
            if i >= 1:
                ev["causado_por"] = "evento-que-nunca-existiu"

        self._reescrever_log(apontar_para_o_nada)
        with self.assertRaises(EventoAdulterado) as ctx:
            self._retomar()
        self.assertIn("causado_por fora da cadeia", str(ctx.exception))

    def test_checkpoint_re_selado_com_ancora_falsa_nao_retoma(self):
        # O ramo so e alcancado com o checkpoint RE-SELADO: sem isso quem
        # recusa e o selo, que e outro guarda. A chave de selo e LOCAL,
        # de modo que re-selar e o que um adversario com o disco faria.
        self._sessao_caida()
        arquivo = glob.glob(os.path.join(self.raiz, "checkpoints", self.sid,
                                         "*.json"))[0]
        with open(arquivo, "rb") as fluxo:
            checkpoint = json.loads(fluxo.read())
        checkpoint["estado_refs"]["ultimo_evento_hash"] = "f" * 64
        corpo = {c: v for c, v in checkpoint.items()
                 if c not in ("validacao", "selo")}
        checkpoint["selo"] = self.kernel._selo(canonico(corpo))
        with open(arquivo, "wb") as f:
            f.write(canonico(checkpoint))
        with self.assertRaises(CheckpointInvalido) as ctx:
            self._retomar()
        self.assertIn("fora da cadeia", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
