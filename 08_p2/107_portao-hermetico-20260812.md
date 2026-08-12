# O portao herdava a sessao do operador — 2026-08-12

> Missao de correcao, experimental e sem autoridade. Quem corrige nao
> certifica.

## O defeito, medido duas vezes antes de entendido

A setima corrida real (`fluxo-20260812T160301092940Z-recusado.json`)
caiu no portao de testes — o MESMO portao que havia medido **994 OK**
isolado duas horas antes. A diferenca nao era a copia: era o
**ambiente**. O launcher exporta `SSC_LOCK_SESSAO=ssc-plus-ui`, a suite
na copia herda, e o codigo de producao dentro dos testes de escritor
unico reivindica a sessao do operador:

    PARADA: o escritor unico do repositorio e de 'p1a6-ops',
    nao de 'ssc-plus-ui'

Reproduzido fora do fluxo com a variavel exportada: **30 falhas + 16
erros**. Sem a variavel: 994 OK. O portao verde isolado e vermelho no
fluxo era a mesma suite sob dois ambientes.

## A correcao, e a prova

`testar_patch_isolado` passa a rodar a suite **hermetica**: o
subprocesso recebe o ambiente sem `SSC_LOCK_SESSAO`. O portao mede a
suite como o `verificar.py` a define, nao como o fluxo a cerca.

- teste novo (`PortaoHermetico`) exerce o caso que ocorreu: exporta a
  variavel, roda o portao real com um comando que devolve 1 se ela
  vazar, e exige 0;
- portao real com a variavel exportada, depois da correcao:
  **returncode 0**.

## Limite declarado

So a variavel medida e removida. Outras variaveis ambientais do
operador continuam herdadas — remover mais do que se mediu seria
afirmar hermetismo que nao se provou. Se outra vazar e quebrar, ela
aparece como este caso apareceu, e entra aqui com medicao propria.

## Plataforma da medicao — os quatro campos

interpretador Python 3.14.3 · pytest 9.1.1 · `core.autocrlf` true ·
usuario: o historico do acervo (8 caracteres, por descricao).
