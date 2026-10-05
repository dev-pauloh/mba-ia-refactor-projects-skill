from functools import wraps

from flask import current_app, g, request

from middlewares.error_handler import ForbiddenError, UnauthorizedError
from models.user import User


def _authenticate():
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise UnauthorizedError('Token de acesso ausente')

    user_id = current_app.extensions['token_service'].user_id_from(token.strip())
    user = User.get(user_id) if user_id is not None else None
    if user is None or not user.active:
        raise UnauthorizedError('Token inválido ou expirado')
    return user


def require_auth(admin=False):
    """Exige `Authorization: Bearer <token>`; com admin=True exige também role admin.

    O usuário autenticado fica em `g.current_user`.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _authenticate()
            if admin and not user.is_admin():
                raise ForbiddenError('Acesso restrito a administradores')
            g.current_user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator
