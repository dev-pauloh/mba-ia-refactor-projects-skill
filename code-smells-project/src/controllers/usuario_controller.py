import logging

from src.config.constants import TIPO_ADMIN
from src.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from src.models import usuario_model
from src.services import token_service, usuario_service

logger = logging.getLogger(__name__)


def listar():
    return usuario_model.listar()


def buscar(usuario_id, solicitante):
    if solicitante["tipo"] != TIPO_ADMIN and solicitante["id"] != usuario_id:
        raise ForbiddenError("Acesso negado aos dados de outro usuário")
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    usuario = usuario_service.validar_cadastro(dados)
    if usuario_model.email_existe(usuario["email"]):
        raise ConflictError("Email já cadastrado")
    novo_id = usuario_model.criar(**usuario)
    logger.info("Usuário criado id=%s", novo_id)
    return {"id": novo_id}


def login(dados):
    email, senha = usuario_service.validar_credenciais(dados)
    usuario = usuario_model.autenticar(email, senha)
    if usuario is None:
        logger.info("Login falhou")
        raise UnauthorizedError("Email ou senha inválidos")
    logger.info("Login bem-sucedido usuario_id=%s", usuario["id"])
    return usuario, token_service.emitir(usuario["id"])
