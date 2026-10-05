"""Validações de entrada compartilhadas pelos controllers."""
from middlewares.error_handler import ForbiddenError, ValidationError


def require_body(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')


def require_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValidationError('Nome é obrigatório')
    return name


def parse_int(value, message):
    if isinstance(value, bool):
        raise ValidationError(message)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(message) from None


def ensure_self_or_admin(user_id, current_user):
    if current_user.id != user_id and not current_user.is_admin():
        raise ForbiddenError('Acesso negado a dados de outro usuário')
