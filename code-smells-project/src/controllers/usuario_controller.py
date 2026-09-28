import logging

from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def _campo_texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


def listar():
    return usuario_model.listar()


def buscar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    nome = _campo_texto(dados, "nome")
    email = _campo_texto(dados, "email")
    senha = _campo_texto(dados, "senha")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    usuario_id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado id=%s", usuario_id)
    return {"id": usuario_id}


def login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = _campo_texto(dados, "email")
    senha = _campo_texto(dados, "senha")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou")
        raise UnauthorizedError("Email ou senha inválidos", com_sucesso=True)
    logger.info("Login bem-sucedido usuario_id=%s", usuario["id"])
    return usuario
