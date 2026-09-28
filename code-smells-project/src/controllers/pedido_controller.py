from src.config.constants import STATUS_CANCELADO, STATUS_PEDIDO_VALIDOS
from src.errors import NotFoundError, ValidationError
from src.models import pedido_model, produto_model
from src.services import notification_service


def _is_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_itens(itens):
    if not isinstance(itens, list) or not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict) or not _is_inteiro(item.get("produto_id")):
            raise ValidationError("Cada item deve ter produto_id inteiro")
        if not _is_inteiro(item.get("quantidade")) or item["quantidade"] <= 0:
            raise ValidationError("Cada item deve ter quantidade inteira maior que zero")


def criar(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    _validar_itens(itens)

    produtos = produto_model.buscar_por_ids(item["produto_id"] for item in itens)
    total = 0
    itens_pedido = []
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado", com_sucesso=True)
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError("Estoque insuficiente para " + produto["nome"], com_sucesso=True)
        total = total + produto["preco"] * item["quantidade"]
        itens_pedido.append({
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": produto["preco"],
            "nome": produto["nome"],
        })

    pedido_id = pedido_model.criar(usuario_id, itens_pedido, total)
    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_por_usuario(usuario_id):
    return pedido_model.listar_por_usuario(usuario_id)


def listar_todos():
    return pedido_model.listar_todos()


def atualizar_status(pedido_id, dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")

    pedido = pedido_model.buscar_por_id(pedido_id)
    if not pedido:
        raise NotFoundError("Pedido não encontrado")

    devolver_estoque = novo_status == STATUS_CANCELADO and pedido["status"] != STATUS_CANCELADO
    pedido_model.atualizar_status(pedido_id, novo_status, devolver_estoque)
    notification_service.pedido_status_alterado(pedido_id, novo_status)
