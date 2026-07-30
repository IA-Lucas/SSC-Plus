"""Mini kernel de fixture para a tarefa-ouro TO-2."""
from hmac import compare_digest


def validar_selo_checkpoint(selo, esperado):
    """Confere o selo HMAC local do checkpoint."""
    return compare_digest(selo, esperado)


def contar_linhas(texto):
    return len(texto.splitlines())
