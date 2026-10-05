import logging

from config.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, USER_ROLES
from controllers.validation import ensure_self_or_admin, require_body, require_name
from database import db
from middlewares.error_handler import (
    ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError,
)
from models.task import Task
from models.user import User
from utils.helpers import is_valid_email, utcnow

logger = logging.getLogger(__name__)

PRIVILEGED_FIELDS = ('role', 'active')


def _validate_email(email, current_user_id=None):
    if not is_valid_email(email):
        raise ValidationError('Email inválido')
    existing = User.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')
    return email


def _validate_password(password, message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return password


def _validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


class UserController:
    def __init__(self, token_service):
        self.token_service = token_service

    def list_users(self):
        task_counts = Task.count_by('user_id')
        result = []
        for user in User.list_all():
            data = user.to_dict()
            data['task_count'] = task_counts.get(user.id, 0)
            result.append(data)
        return result

    def get_user(self, user_id, current_user):
        ensure_self_or_admin(user_id, current_user)
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
        return data

    def create_user(self, data):
        require_body(data)
        if not data.get('name'):
            raise ValidationError('Nome é obrigatório')
        if not data.get('email'):
            raise ValidationError('Email é obrigatório')
        if not data.get('password'):
            raise ValidationError('Senha é obrigatória')

        name = require_name(data['name'])
        if not is_valid_email(data['email']):
            raise ValidationError('Email inválido')
        password = _validate_password(
            data['password'], f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        email = _validate_email(data['email'])
        role = _validate_role(data.get('role', DEFAULT_ROLE))

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        logger.info('Usuário criado: id=%s', user.id)
        return user.to_dict()

    def update_user(self, user_id, data, current_user):
        ensure_self_or_admin(user_id, current_user)
        user = self._get_or_404(user_id)
        require_body(data)

        if not current_user.is_admin() and any(field in data for field in PRIVILEGED_FIELDS):
            raise ForbiddenError('Apenas administradores podem alterar role ou status')

        if 'name' in data:
            user.name = require_name(data['name'])
        if 'email' in data:
            user.email = _validate_email(data['email'], current_user_id=user_id)
        if 'password' in data:
            user.set_password(_validate_password(data['password'], 'Senha muito curta'))
        if 'role' in data:
            user.role = _validate_role(data['role'])
        if 'active' in data:
            if not isinstance(data['active'], bool):
                raise ValidationError('Campo active deve ser booleano')
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        Task.delete_by_user(user_id)
        db.session.delete(user)
        db.session.commit()
        logger.info('Usuário deletado: id=%s', user_id)

    def list_user_tasks(self, user_id):
        self._get_or_404(user_id)
        now = utcnow()
        return [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'created_at': str(task.created_at),
                'due_date': str(task.due_date) if task.due_date else None,
                'overdue': task.is_overdue(now),
            }
            for task in Task.list_by_user(user_id)
        ]

    def login(self, data):
        require_body(data)
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = User.find_by_email(email) if isinstance(email, str) else None
        if user is None or not isinstance(password, str) or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        return {'user': user.to_dict(), 'token': self.token_service.issue(user.id)}

    @staticmethod
    def _get_or_404(user_id):
        user = User.get(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user
