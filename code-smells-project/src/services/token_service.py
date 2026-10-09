"""Tokens de acesso assinados com a SECRET_KEY (itsdangerous já vem com o Flask)."""
from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

_SALT = "auth-token"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def emitir(usuario_id):
    return _serializer().dumps({"uid": usuario_id})


def verificar(token):
    """Devolve o id do usuário do token, ou None se inválido/expirado."""
    try:
        payload = _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE"])
    except BadSignature:
        return None
    return payload.get("uid") if isinstance(payload, dict) else None
