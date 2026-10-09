"""Regras de domínio de usuário: cadastro e credenciais."""
import re

from src.errors import ValidationError
from src.services.validators import exigir_objeto

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _texto_obrigatorio(dados, campo):
    valor = dados.get(campo, "")
    return valor.strip() if isinstance(valor, str) else ""


def validar_cadastro(dados):
    exigir_objeto(dados)
    nome = _texto_obrigatorio(dados, "nome")
    email = _texto_obrigatorio(dados, "email")
    senha = dados.get("senha", "")
    if not nome or not email or not isinstance(senha, str) or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    return {"nome": nome, "email": email, "senha": senha}


def validar_credenciais(dados):
    if not isinstance(dados, dict):
        raise ValidationError("Email e senha são obrigatórios")
    email = _texto_obrigatorio(dados, "email")
    senha = dados.get("senha", "")
    if not email or not isinstance(senha, str) or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha
