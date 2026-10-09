from flask import Blueprint, jsonify, request

from src.controllers import produto_controller
from src.middlewares.auth import require_admin, require_auth

bp = Blueprint("produtos", __name__)


@bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": produto_controller.listar(), "sucesso": True}), 200


@bp.get("/produtos/busca")
@require_auth
def buscar_produtos():
    resultados = produto_controller.pesquisar(
        request.args.get("q", ""),
        request.args.get("categoria"),
        request.args.get("preco_min"),
        request.args.get("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.buscar(produto_id), "sucesso": True}), 200


@bp.post("/produtos")
@require_admin
def criar_produto():
    dados = produto_controller.criar(request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True, "mensagem": "Produto criado"}), 201


@bp.put("/produtos/<int:produto_id>")
@require_admin
def atualizar_produto(produto_id):
    produto_controller.atualizar(produto_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@bp.delete("/produtos/<int:produto_id>")
@require_admin
def deletar_produto(produto_id):
    produto_controller.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
