import logging

from config.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, USER_ROLES
from middlewares.error_handler import (
    ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError,
)
from models.task import Task
from models.user import User
from utils.helpers import is_valid_email

logger = logging.getLogger(__name__)


def validate_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Nome é obrigatório')
    return name


def validate_email(email):
    if not is_valid_email(email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    return password


def validate_role(role):
    if role not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def ensure_email_available(email, current_user_id=None):
    existing = User.get_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def ensure_admin(acting_user, message):
    if acting_user is None or not acting_user.is_admin():
        raise ForbiddenError(message)


class UserController:
    def __init__(self, token_service):
        self.token_service = token_service

    def list_users(self):
        result = []
        for user, task_count, _completed in User.list_with_task_stats():
            data = user.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.list_by_user(user.id)]
        return data

    def create_user(self, data, acting_user=None):
        if not data:
            raise ValidationError('Dados inválidos')
        if not data.get('name'):
            raise ValidationError('Nome é obrigatório')
        if not data.get('email'):
            raise ValidationError('Email é obrigatório')
        if not data.get('password'):
            raise ValidationError('Senha é obrigatória')

        name = validate_name(data['name'])
        email = validate_email(data['email'])
        password = validate_password(data['password'])
        ensure_email_available(email)
        role = validate_role(data.get('role', DEFAULT_ROLE))
        if role != DEFAULT_ROLE:
            ensure_admin(acting_user, 'Apenas administradores podem definir o role')

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        user.save()
        logger.info('Usuário criado id=%s', user.id)
        return user.to_dict()

    def update_user(self, user_id, data, acting_user=None):
        user = self._get_or_404(user_id)
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = validate_name(data['name'])
        if 'email' in data:
            email = validate_email(data['email'])
            ensure_email_available(email, current_user_id=user.id)
            user.email = email
        if 'password' in data:
            user.set_password(validate_password(data['password']))
        if 'role' in data:
            role = validate_role(data['role'])
            if role != user.role:
                ensure_admin(acting_user, 'Apenas administradores podem alterar o role')
            user.role = role
        if 'active' in data:
            if not isinstance(data['active'], bool):
                raise ValidationError('Active deve ser true ou false')
            if data['active'] != user.active:
                ensure_admin(acting_user, 'Apenas administradores podem ativar/desativar usuários')
            user.active = data['active']

        user.save()
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        user.delete()  # tasks do usuário removidas na mesma transação (cascade)
        logger.info('Usuário deletado id=%s', user_id)

    def list_user_tasks(self, user_id):
        user = self._get_or_404(user_id)
        return [task.to_summary_dict() for task in Task.list_by_user(user.id)]

    def login(self, data):
        if not data:
            raise ValidationError('Dados inválidos')
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = User.get_by_email(email) if isinstance(email, str) else None
        if user is None or not isinstance(password, str) or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self.token_service.issue(user.id),
        }

    @staticmethod
    def _get_or_404(user_id):
        user = User.get_by_id(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user
