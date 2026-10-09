from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenService:
    """Emite e valida tokens de acesso assinados com a SECRET_KEY e com expiração."""

    _SALT = 'auth-token'

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=self._SALT)
        self._max_age = max_age

    def issue(self, user_id):
        return self._serializer.dumps({'uid': user_id})

    def verify(self, token):
        """Retorna o id do usuário do token, ou None se inválido/expirado."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        user_id = payload.get('uid') if isinstance(payload, dict) else None
        return user_id if isinstance(user_id, int) else None
