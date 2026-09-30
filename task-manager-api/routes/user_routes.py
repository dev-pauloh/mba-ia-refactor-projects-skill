from flask import Blueprint, jsonify, request

from middlewares.auth import current_user, require_admin


def create_user_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.get('/users')
    def get_users():
        return jsonify(controller.list_users()), 200

    @user_bp.get('/users/<int:user_id>')
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @user_bp.post('/users')
    def create_user():
        data = request.get_json(silent=True)
        return jsonify(controller.create_user(data, acting_user=current_user())), 201

    @user_bp.put('/users/<int:user_id>')
    def update_user(user_id):
        data = request.get_json(silent=True)
        return jsonify(controller.update_user(user_id, data, acting_user=current_user())), 200

    @user_bp.delete('/users/<int:user_id>')
    @require_admin
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @user_bp.get('/users/<int:user_id>/tasks')
    def get_user_tasks(user_id):
        return jsonify(controller.list_user_tasks(user_id)), 200

    @user_bp.post('/login')
    def login():
        return jsonify(controller.login(request.get_json(silent=True))), 200

    return user_bp
