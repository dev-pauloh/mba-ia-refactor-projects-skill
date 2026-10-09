from flask import Blueprint, jsonify, request

from src.controllers import pedido_controller
from src.middlewares.auth import require_admin, require_auth, usuario_atual

bp = Blueprint("pedidos", __name__)


@bp.post("/pedidos")
@require_auth
def criar_pedido():
    resultado = pedido_controller.criar(request.get_json(silent=True), usuario_atual())
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@bp.get("/pedidos")
@require_admin
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.listar_todos(), "sucesso": True}), 200


@bp.get("/pedidos/usuario/<int:usuario_id>")
@require_auth
def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_controller.listar_do_usuario(usuario_id, usuario_atual())
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@bp.put("/pedidos/<int:pedido_id>/status")
@require_admin
def atualizar_status_pedido(pedido_id):
    pedido_controller.atualizar_status(pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
