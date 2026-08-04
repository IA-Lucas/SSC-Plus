"""Texto de procedencia externa -> o que o console aceita. Um lugar so.

O CASO QUE OCORREU EM OPERACAO, na P2.2, e a razao de este modulo
existir: a resposta do codex trouxe `→` (U+2192), o console da estacao
codifica cp1252, e `print` levantou `UnicodeEncodeError` na linha que
exibia a saida — que ficava ANTES do bloco que reverifica o lease e
persiste a evidencia. O attempt havia dado **sucesso**: a franquia foi
gasta, a cadeia ficou gravada no laboratorio, e o artefato de registro em
`08_p2/evidencias/` nao existiu. Um caractere que o console nao sabe
desenhar decidiu se a corrida foi registrada.

Ate a P2.3 a funcao vivia dentro de `runner_p2`. A P2.4 deu um comando de
linha ao medidor (achado C), e esse comando imprime texto que vem de
ARQUIVO — rotulo de receita, motivo de testemunho —, exposto a mesma
falha. Copia-la seria a segunda copia de um guarda neste acervo, e a
varredura de guardas ja contou quatro copias de um outro, das quais so
uma tinha o conserto.
"""

import sys


def no_codec_do_console(texto: str) -> str:
    """Degradacao de EXIBICAO, declarada.

    Caractere fora do codec do console sai como substituto; o byte
    gravado em disco nao e tocado — a mesma separacao que o achado 5.3
    da P2.1 mediu (dano de exibicao, nunca perda gravada). Console que
    SABE desenhar o caractere continua recebendo o caractere: substituir
    sempre seria dano gratuito passando por conserto.
    """
    codec = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        return texto.encode(codec, errors="replace").decode(codec,
                                                            errors="replace")
    except LookupError:                     # codec do console desconhecido
        return texto.encode("ascii", errors="replace").decode("ascii")
