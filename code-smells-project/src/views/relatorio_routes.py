from flask import Blueprint, jsonify

from src.controllers import relatorio_controller
from src.middlewares.auth import require_admin

bp = Blueprint("relatorios", __name__)


@bp.get("/relatorios/vendas")
@require_admin
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.vendas(), "sucesso": True}), 200
