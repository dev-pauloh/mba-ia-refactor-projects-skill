from flask import Blueprint, jsonify, request

from middlewares.auth import require_auth


def create_category_blueprint(controller):
    bp = Blueprint('categories', __name__)

    @bp.get('/categories')
    @require_auth()
    def get_categories():
        return jsonify(controller.list_categories()), 200

    @bp.post('/categories')
    @require_auth()
    def create_category():
        return jsonify(controller.create_category(request.get_json(silent=True))), 201

    @bp.put('/categories/<int:category_id>')
    @require_auth()
    def update_category(category_id):
        return jsonify(controller.update_category(category_id, request.get_json(silent=True))), 200

    @bp.delete('/categories/<int:category_id>')
    @require_auth()
    def delete_category(category_id):
        controller.delete_category(category_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return bp
