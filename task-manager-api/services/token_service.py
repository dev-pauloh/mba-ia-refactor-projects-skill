from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenService:
    """Emite e valida tokens de acesso assinados com a SECRET_KEY."""

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age

    def issue(self, user_id):
        return self._serializer.dumps({'uid': user_id})

    def user_id_from(self, token):
        """Retorna o id do usuário do token, ou None se inválido/expirado."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        return payload.get('uid')
