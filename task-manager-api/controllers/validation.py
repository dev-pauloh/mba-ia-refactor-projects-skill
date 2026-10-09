"""Validação única das entradas da API: presença, tipo, faixa e formato."""
import re
from datetime import datetime

from config.constants import (
    DATE_FORMAT, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PASSWORD_LENGTH, MIN_PRIORITY,
    MIN_TITLE_LENGTH, TASK_STATUSES, USER_ROLES,
)
from utils.errors import ValidationError

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


def require_object(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError('Dados inválidos')
    return data


def parse_int(value, message):
    if isinstance(value, bool):
        raise ValidationError(message)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip('-').isdigit():
        return int(value)
    raise ValidationError(message)


def optional_id(value, message):
    if value is None:
        return None
    return parse_int(value, message)


def non_empty_string(value, message, type_message=None):
    if value is not None and not isinstance(value, str):
        raise ValidationError(type_message or message)
    if not value or not value.strip():
        raise ValidationError(message)
    return value.strip()


def optional_string(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


# ---------------------------------------------------------------- tasks

def _title(value):
    title = non_empty_string(value, 'Título é obrigatório', 'Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def _status(value):
    if value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def priority(value):
    number = parse_int(value, 'Prioridade inválida')
    if not MIN_PRIORITY <= number <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return number


def _due_date(value):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD') from None


def _tags(value):
    if value is None:
        return None
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise ValidationError('Tags inválidas')
        return ','.join(value)
    if isinstance(value, str):
        return value
    raise ValidationError('Tags inválidas')


_TASK_FIELDS = {
    'title': _title,
    'description': lambda v: optional_string(v, 'Descrição inválida'),
    'status': _status,
    'priority': priority,
    'user_id': lambda v: optional_id(v, 'user_id inválido'),
    'category_id': lambda v: optional_id(v, 'category_id inválido'),
    'due_date': _due_date,
    'tags': _tags,
}


def validate_task(data, partial=False):
    """Retorna só os campos presentes, já convertidos; no create aplica obrigatoriedade e defaults."""
    require_object(data)
    if not partial and not data.get('title'):
        raise ValidationError('Título é obrigatório')
    return {field: parse(data[field]) for field, parse in _TASK_FIELDS.items() if field in data}


# ---------------------------------------------------------------- users

def _email(value):
    email = non_empty_string(value, 'Email é obrigatório', 'Email inválido')
    if not EMAIL_PATTERN.match(email):
        raise ValidationError('Email inválido')
    return email


def _password(value):
    if value is not None and not isinstance(value, str):
        raise ValidationError('Senha inválida')
    if not value:
        raise ValidationError('Senha é obrigatória')
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    return value


def _role(value):
    if value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def _active(value):
    if not isinstance(value, bool):
        raise ValidationError('Active deve ser booleano')
    return value


_USER_FIELDS = {
    'name': lambda v: non_empty_string(v, 'Nome é obrigatório', 'Nome inválido'),
    'email': _email,
    'password': _password,
    'role': _role,
    'active': _active,
}


def validate_user(data, partial=False):
    require_object(data)
    if not partial:
        for field, message in (('name', 'Nome é obrigatório'), ('email', 'Email é obrigatório'),
                               ('password', 'Senha é obrigatória')):
            if not data.get(field):
                raise ValidationError(message)
    return {field: parse(data[field]) for field, parse in _USER_FIELDS.items() if field in data}


def validate_credentials(data):
    require_object(data)
    email, password = data.get('email'), data.get('password')
    if not isinstance(email, str) or not email or not isinstance(password, str) or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return email, password


# ---------------------------------------------------------------- categories

def _color(value):
    if not isinstance(value, str) or not COLOR_PATTERN.match(value):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return value


_CATEGORY_FIELDS = {
    'name': lambda v: non_empty_string(v, 'Nome é obrigatório', 'Nome inválido'),
    'description': lambda v: optional_string(v, 'Descrição inválida'),
    'color': _color,
}


def validate_category(data, partial=False):
    require_object(data, allow_empty=partial)
    if not partial and not data.get('name'):
        raise ValidationError('Nome é obrigatório')
    return {field: parse(data[field]) for field, parse in _CATEGORY_FIELDS.items() if field in data}


# ---------------------------------------------------------------- search

def validate_search(args):
    filters = {'q': args.get('q', ''), 'status': args.get('status', '')}
    filters['priority'] = parse_int(args['priority'], 'Prioridade inválida') if args.get('priority') else None
    filters['user_id'] = parse_int(args['user_id'], 'user_id inválido') if args.get('user_id') else None
    return filters
