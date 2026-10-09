"""Autenticação por token Bearer assinado e autorização por papel."""
from functools import wraps

from flask import current_app, g, request

from database import db
from models.user import User
from utils.errors import ForbiddenError, UnauthorizedError


def _authenticate():
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        raise UnauthorizedError('Token de acesso ausente')
    user_id = current_app.extensions['token_service'].verify(token.strip())
    user = db.session.get(User, user_id) if user_id is not None else None
    if user is None or not user.active:
        raise UnauthorizedError('Token inválido ou expirado')
    g.current_user = user
    return user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        _authenticate()
        return view(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """Exige usuário autenticado com um dos papéis informados."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _authenticate()
            if not user.has_role(*roles):
                raise ForbiddenError('Acesso negado')
            return view(*args, **kwargs)
        return wrapper
    return decorator


def self_or_roles(*roles):
    """Exige que o usuário autenticado seja o dono do recurso (<user_id>) ou tenha um dos papéis."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _authenticate()
            if user.id != kwargs.get('user_id') and not user.has_role(*roles):
                raise ForbiddenError('Acesso negado')
            return view(*args, **kwargs)
        return wrapper
    return decorator
