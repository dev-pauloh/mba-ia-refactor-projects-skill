from datetime import datetime, timezone


def utcnow():
    """UTC atual como datetime naive, compatível com as colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
