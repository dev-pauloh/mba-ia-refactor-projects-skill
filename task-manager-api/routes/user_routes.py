from flask import Blueprint, g, jsonify, request

from middlewares.auth import require_auth


def create_user_blueprint(controller):
    bp = Blueprint('users', __name__)

    @bp.get('/users')
    @require_auth(admin=True)
    def get_users():
        return jsonify(controller.list_users()), 200

    @bp.get('/users/<int:user_id>')
    @require_auth()
    def get_user(user_id):
        return jsonify(controller.get_user(user_id, g.current_user)), 200

    @bp.post('/users')
    @require_auth(admin=True)
    def create_user():
        return jsonify(controller.create_user(request.get_json(silent=True))), 201

    @bp.put('/users/<int:user_id>')
    @require_auth()
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json(silent=True), g.current_user)), 200

    @bp.delete('/users/<int:user_id>')
    @require_auth(admin=True)
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @bp.get('/users/<int:user_id>/tasks')
    def get_user_tasks(user_id):
        return jsonify(controller.list_user_tasks(user_id)), 200

    @bp.post('/login')
    def login():
        result = controller.login(request.get_json(silent=True))
        return jsonify({'message': 'Login realizado com sucesso', **result}), 200

    return bp
