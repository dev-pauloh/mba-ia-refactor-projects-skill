import re
from datetime import datetime, timezone

from config.constants import EMAIL_PATTERN


def utcnow():
    """UTC atual como datetime naive, compatível com as colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def is_valid_email(email):
    return isinstance(email, str) and re.match(EMAIL_PATTERN, email) is not None


def is_valid_color(color):
    return isinstance(color, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', color) is not None
