from flask import Blueprint, jsonify, request

from config.constants import ROLE_ADMIN, ROLE_MANAGER
from controllers import category_controller
from middlewares.auth import login_required, roles_required

category_bp = Blueprint('categories', __name__)


@category_bp.get('/categories')
@login_required
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.post('/categories')
@roles_required(ROLE_ADMIN, ROLE_MANAGER)
def create_category():
    return jsonify(category_controller.create_category(request.get_json(silent=True))), 201


@category_bp.put('/categories/<int:cat_id>')
@roles_required(ROLE_ADMIN, ROLE_MANAGER)
def update_category(cat_id):
    return jsonify(category_controller.update_category(cat_id, request.get_json(silent=True))), 200


@category_bp.delete('/categories/<int:cat_id>')
@roles_required(ROLE_ADMIN, ROLE_MANAGER)
def delete_category(cat_id):
    return jsonify(category_controller.delete_category(cat_id)), 200
