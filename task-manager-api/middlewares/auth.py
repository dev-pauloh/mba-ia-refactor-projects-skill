from functools import wraps

from flask import current_app, g, request

from middlewares.error_handler import ForbiddenError, UnauthorizedError
from models.user import User


def current_user():
    """Usuário autenticado pelo header 'Authorization: Bearer <token>', ou None se ausente.

    Token presente mas inválido/expirado gera 401.
    """
    if 'current_user' in g:
        return g.current_user

    user = None
    header = request.headers.get('Authorization', '')
    if header:
        scheme, _, token = header.partition(' ')
        if scheme.lower() != 'bearer' or not token:
            raise UnauthorizedError('Token inválido')
        user_id = current_app.extensions['token_service'].verify(token)
        user = User.get_by_id(user_id) if user_id is not None else None
        if user is None or not user.active:
            raise UnauthorizedError('Token inválido ou expirado')

    g.current_user = user
    return user


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            raise UnauthorizedError('Autenticação necessária')
        if not user.is_admin():
            raise ForbiddenError('Acesso restrito a administradores')
        return view(*args, **kwargs)
    return wrapper
