from flask import Blueprint, current_app, jsonify, request

from src.controllers import admin_controller
from src.middlewares.auth import require_admin

bp = Blueprint("admin", __name__)


@bp.post("/admin/reset-db")
@require_admin
def reset_database():
    admin_controller.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@bp.post("/admin/query")
@require_admin
def executar_query():
    resultado = admin_controller.executar_query(
        request.get_json(silent=True), current_app.config["ENABLE_ADMIN_SQL"]
    )
    if resultado is None:
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    return jsonify({"dados": resultado, "sucesso": True}), 200
