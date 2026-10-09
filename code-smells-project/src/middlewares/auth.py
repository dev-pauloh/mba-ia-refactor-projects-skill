from functools import wraps

from flask import g, request

from src.config.constants import TIPO_ADMIN
from src.errors import ForbiddenError, UnauthorizedError
from src.models import usuario_model
from src.services import token_service


def _usuario_do_request():
    cabecalho = request.headers.get("Authorization", "")
    esquema, _, token = cabecalho.partition(" ")
    if esquema.lower() != "bearer" or not token:
        raise UnauthorizedError("Autenticação necessária: envie Authorization: Bearer <token>")
    usuario_id = token_service.verificar(token.strip())
    usuario = usuario_model.buscar_por_id(usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise UnauthorizedError("Token inválido ou expirado")
    return usuario


def usuario_atual():
    return g.usuario


def eh_admin(usuario):
    return usuario["tipo"] == TIPO_ADMIN


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.usuario = _usuario_do_request()
        return view(*args, **kwargs)
    return wrapper


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.usuario = _usuario_do_request()
        if not eh_admin(g.usuario):
            raise ForbiddenError("Acesso restrito a administradores")
        return view(*args, **kwargs)
    return wrapper
