import hmac
from functools import wraps

from flask import current_app, request

from src.errors import UnauthorizedError


def require_admin(view):
    """Exige header X-Admin-Token igual a ADMIN_TOKEN; sem ADMIN_TOKEN configurado, nega sempre."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        fornecido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(fornecido.encode(), esperado.encode()):
            raise UnauthorizedError("Acesso administrativo requer X-Admin-Token válido")
        return view(*args, **kwargs)

    return wrapper
