from flask import current_app

from controllers import validation
from services import user_service
from utils.errors import ForbiddenError
from utils.helpers import utcnow

ADMIN_ONLY_FIELDS = ('role', 'active')
USER_TASK_FIELDS = ('id', 'title', 'description', 'status', 'priority', 'created_at', 'due_date')


def list_users():
    return [
        {**user.to_dict(), 'task_count': task_count}
        for user, task_count in user_service.list_users_with_task_count()
    ]


def get_user(user_id):
    user = user_service.get_user(user_id)
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in user_service.list_tasks_of(user_id)]}


def create_user(data):
    fields = validation.validate_user(data)
    return user_service.create_user(fields).to_dict()


def update_user(user_id, data, current_user):
    user_service.get_user(user_id)
    fields = validation.validate_user(data, partial=True)
    if any(field in fields for field in ADMIN_ONLY_FIELDS) and not current_user.is_admin():
        raise ForbiddenError('Apenas admin pode alterar role ou active')
    return user_service.update_user(user_id, fields).to_dict()


def delete_user(user_id):
    user_service.delete_user(user_id)
    return {'message': 'Usuário deletado com sucesso'}


def list_user_tasks(user_id):
    user_service.get_user(user_id)
    now = utcnow()
    tasks = user_service.list_tasks_of(user_id)
    return [
        {**{field: task.to_dict()[field] for field in USER_TASK_FIELDS}, 'overdue': task.is_overdue(now)}
        for task in tasks
    ]


def login(data):
    email, password = validation.validate_credentials(data)
    user = user_service.authenticate(email, password)
    token = current_app.extensions['token_service'].issue(user.id)
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': token}
