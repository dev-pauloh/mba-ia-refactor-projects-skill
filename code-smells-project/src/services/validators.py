"""Checagens de tipo reutilizadas pelos services de domínio."""
from src.errors import ValidationError


def exigir_objeto(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def inteiro_positivo(valor, mensagem):
    if not eh_inteiro(valor) or valor <= 0:
        raise ValidationError(mensagem)
    return valor


def texto(valor, mensagem):
    if not isinstance(valor, str):
        raise ValidationError(mensagem)
    return valor.strip()


def float_opcional(valor, mensagem):
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValidationError(mensagem) from None
