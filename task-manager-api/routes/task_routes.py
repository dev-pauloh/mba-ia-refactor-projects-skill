from flask import Blueprint, jsonify, request

from controllers import task_controller
from middlewares.auth import login_required

task_bp = Blueprint('tasks', __name__)


@task_bp.get('/tasks')
@login_required
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.get('/tasks/<int:task_id>')
@login_required
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.post('/tasks')
@login_required
def create_task():
    return jsonify(task_controller.create_task(request.get_json(silent=True))), 201


@task_bp.put('/tasks/<int:task_id>')
@login_required
def update_task(task_id):
    return jsonify(task_controller.update_task(task_id, request.get_json(silent=True))), 200


@task_bp.delete('/tasks/<int:task_id>')
@login_required
def delete_task(task_id):
    return jsonify(task_controller.delete_task(task_id)), 200


@task_bp.get('/tasks/search')
@login_required
def search_tasks():
    return jsonify(task_controller.search_tasks(request.args)), 200


@task_bp.get('/tasks/stats')
@login_required
def task_stats():
    return jsonify(task_controller.task_stats()), 200
