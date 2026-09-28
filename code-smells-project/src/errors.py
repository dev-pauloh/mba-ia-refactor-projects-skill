class AppError(Exception):
    """Erro de domínio; o error handler central traduz para resposta HTTP."""

    status_code = 500

    def __init__(self, message, *, com_sucesso=False):
        super().__init__(message)
        self.message = message
        # Algumas respostas de erro da API original incluem "sucesso": false; mantém o contrato.
        self.com_sucesso = com_sucesso


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404
