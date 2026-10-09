import logging

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from config.constants import (
    CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING, TASK_STATUSES,
)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.errors import NotFoundError
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError('Task não encontrada')
    return task


def list_tasks_with_relations():
    stmt = select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
    return db.session.scalars(stmt).all()


def search_tasks(q='', status='', priority=None, user_id=None):
    stmt = select(Task)
    if q:
        stmt = stmt.where(or_(Task.title.like(f'%{q}%'), Task.description.like(f'%{q}%')))
    if status:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if user_id is not None:
        stmt = stmt.where(Task.user_id == user_id)
    return db.session.scalars(stmt.order_by(Task.id)).all()


def _ensure_references_exist(fields):
    if fields.get('user_id') and db.session.get(User, fields['user_id']) is None:
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and db.session.get(Category, fields['category_id']) is None:
        raise NotFoundError('Categoria não encontrada')


def create_task(fields):
    _ensure_references_exist(fields)
    task = Task(
        title=fields['title'],
        description=fields.get('description', ''),
        status=fields.get('status', STATUS_PENDING),
        priority=fields.get('priority', DEFAULT_PRIORITY),
        user_id=fields.get('user_id'),
        category_id=fields.get('category_id'),
        due_date=fields.get('due_date'),
        tags=fields.get('tags') or None,
    )
    db.session.add(task)
    db.session.commit()
    logger.info('Task criada id=%s', task.id)
    return task


def update_task(task_id, fields):
    task = get_task(task_id)
    _ensure_references_exist(fields)
    for attr, value in fields.items():
        setattr(task, attr, value)
    task.updated_at = utcnow()
    db.session.commit()
    logger.info('Task atualizada id=%s', task.id)
    return task


def delete_task(task_id):
    task = get_task(task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info('Task removida id=%s', task_id)


def count_by_status():
    rows = db.session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
    counts = dict(rows)
    return {status: counts.get(status, 0) for status in TASK_STATUSES}


def overdue_filter(now):
    return (Task.due_date.is_not(None), Task.due_date < now, Task.status.not_in(CLOSED_STATUSES))


def stats():
    total = db.session.scalar(select(func.count(Task.id)))
    by_status = count_by_status()
    overdue = db.session.scalar(select(func.count(Task.id)).where(*overdue_filter(utcnow())))
    return {
        'total': total,
        **by_status,
        'overdue': overdue,
        'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
    }
