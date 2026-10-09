from flask import Blueprint, g, jsonify, request

from config.constants import ROLE_ADMIN, ROLE_MANAGER
from controllers import user_controller
from middlewares.auth import roles_required, self_or_roles

user_bp = Blueprint('users', __name__)


@user_bp.get('/users')
@roles_required(ROLE_ADMIN, ROLE_MANAGER)
def get_users():
    return jsonify(user_controller.list_users()), 200


@user_bp.get('/users/<int:user_id>')
@self_or_roles(ROLE_ADMIN, ROLE_MANAGER)
def get_user(user_id):
    return jsonify(user_controller.get_user(user_id)), 200


@user_bp.post('/users')
@roles_required(ROLE_ADMIN)
def create_user():
    return jsonify(user_controller.create_user(request.get_json(silent=True))), 201


@user_bp.put('/users/<int:user_id>')
@self_or_roles(ROLE_ADMIN)
def update_user(user_id):
    data = request.get_json(silent=True)
    return jsonify(user_controller.update_user(user_id, data, g.current_user)), 200


@user_bp.delete('/users/<int:user_id>')
@roles_required(ROLE_ADMIN)
def delete_user(user_id):
    return jsonify(user_controller.delete_user(user_id)), 200


@user_bp.get('/users/<int:user_id>/tasks')
@self_or_roles(ROLE_ADMIN, ROLE_MANAGER)
def get_user_tasks(user_id):
    return jsonify(user_controller.list_user_tasks(user_id)), 200


@user_bp.post('/login')
def login():
    return jsonify(user_controller.login(request.get_json(silent=True))), 200
