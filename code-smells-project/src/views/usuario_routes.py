from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller
from src.middlewares.auth import require_admin, require_auth, usuario_atual

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
@require_admin
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar(), "sucesso": True}), 200


@bp.get("/usuarios/<int:usuario_id>")
@require_auth
def buscar_usuario(usuario_id):
    usuario = usuario_controller.buscar(usuario_id, usuario_atual())
    return jsonify({"dados": usuario, "sucesso": True}), 200


@bp.post("/usuarios")
@require_admin
def criar_usuario():
    dados = usuario_controller.criar(request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True}), 201


@bp.post("/login")
def login():
    usuario, token = usuario_controller.login(request.get_json(silent=True))
    return jsonify({"dados": usuario, "token": token, "sucesso": True, "mensagem": "Login OK"}), 200
