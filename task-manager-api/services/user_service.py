import logging

from sqlalchemy import func, select

from config.constants import ROLE_USER
from database import db
from models.task import Task
from models.user import User
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)


def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_users_with_task_count():
    stmt = (
        select(User, func.count(Task.id))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
    )
    return db.session.execute(stmt).all()


def list_tasks_of(user_id):
    return db.session.scalars(select(Task).where(Task.user_id == user_id).order_by(Task.id)).all()


def _ensure_email_available(email, user_id=None):
    existing = db.session.scalar(select(User).where(User.email == email))
    if existing is not None and existing.id != user_id:
        raise ConflictError('Email já cadastrado')


def create_user(fields):
    _ensure_email_available(fields['email'])
    user = User(name=fields['name'], email=fields['email'], role=fields.get('role', ROLE_USER))
    user.set_password(fields['password'])
    db.session.add(user)
    db.session.commit()
    logger.info('Usuário criado id=%s', user.id)
    return user


def update_user(user_id, fields):
    user = get_user(user_id)
    if 'email' in fields:
        _ensure_email_available(fields['email'], user_id)
    for attr in ('name', 'email', 'role', 'active'):
        if attr in fields:
            setattr(user, attr, fields[attr])
    if 'password' in fields:
        user.set_password(fields['password'])
    db.session.commit()
    logger.info('Usuário atualizado id=%s', user.id)
    return user


def delete_user(user_id):
    """Remove o usuário e, na mesma transação, as tasks dele (cascade do relacionamento + FK)."""
    user = get_user(user_id)
    db.session.delete(user)
    db.session.commit()
    logger.info('Usuário removido id=%s', user_id)


def authenticate(email, password):
    user = db.session.scalar(select(User).where(User.email == email))
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')
    return user
