from flask import Blueprint, current_app, jsonify, request

from src.controllers import admin_controller
from src.middlewares.auth import require_admin

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.post("/reset-db")
@require_admin
def reset_database():
    admin_controller.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@bp.post("/query")
@require_admin
def executar_query():
    dados = admin_controller.executar_consulta(
        request.get_json(silent=True), current_app.config["ENABLE_ADMIN_SQL"]
    )
    return jsonify({"dados": dados, "sucesso": True}), 200
