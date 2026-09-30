import re
from datetime import datetime, timezone

from config.constants import DATE_FORMAT

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def utcnow():
    """UTC atual como datetime naive, compatível com as colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def is_valid_color(color):
    return isinstance(color, str) and COLOR_PATTERN.match(color) is not None


def parse_int(value):
    """Converte para int; devolve None se o valor não for um inteiro válido."""
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_date(value):
    """Converte 'YYYY-MM-DD' em datetime; devolve None se o formato for inválido."""
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        return None
