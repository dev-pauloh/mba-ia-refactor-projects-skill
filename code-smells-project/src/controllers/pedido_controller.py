from src.config.constants import TIPO_ADMIN
from src.errors import ForbiddenError, NotFoundError, ValidationError
from src.models import pedido_model, produto_model, usuario_model
from src.services import notification_service, pedido_service


def _exigir_dono_ou_admin(usuario_id, solicitante, mensagem):
    if solicitante["tipo"] != TIPO_ADMIN and solicitante["id"] != usuario_id:
        raise ForbiddenError(mensagem)


def criar(dados, solicitante):
    usuario_id, itens = pedido_service.validar_pedido(dados)
    _exigir_dono_ou_admin(usuario_id, solicitante, "Não é permitido criar pedido para outro usuário")
    if usuario_model.buscar_por_id(usuario_id) is None:
        raise ValidationError("Usuário " + str(usuario_id) + " não encontrado")

    produtos = produto_model.buscar_por_ids({item["produto_id"] for item in itens})
    itens_precificados, total = pedido_service.precificar_itens(itens, produtos)
    pedido_id = pedido_model.criar(usuario_id, itens_precificados, total)

    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos():
    return pedido_model.listar()


def listar_do_usuario(usuario_id, solicitante):
    _exigir_dono_ou_admin(usuario_id, solicitante, "Acesso negado aos pedidos de outro usuário")
    return pedido_model.listar(usuario_id=usuario_id)


def atualizar_status(pedido_id, dados):
    novo_status = pedido_service.validar_status(dados)
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(pedido_id, novo_status)
    notification_service.status_pedido_alterado(pedido_id, novo_status)
