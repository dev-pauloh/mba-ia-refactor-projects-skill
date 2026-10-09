import logging

from sqlalchemy import func, select, update

from config.constants import DEFAULT_COLOR
from database import db
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError

logger = logging.getLogger(__name__)


def get_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_with_task_count():
    stmt = (
        select(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
    )
    return db.session.execute(stmt).all()


def create_category(fields):
    category = Category(
        name=fields['name'],
        description=fields.get('description', ''),
        color=fields.get('color', DEFAULT_COLOR),
    )
    db.session.add(category)
    db.session.commit()
    logger.info('Categoria criada id=%s', category.id)
    return category


def update_category(category_id, fields):
    category = get_category(category_id)
    for attr, value in fields.items():
        setattr(category, attr, value)
    db.session.commit()
    return category


def delete_category(category_id):
    """Desvincula as tasks da categoria e a remove na mesma transação."""
    category = get_category(category_id)
    db.session.execute(
        update(Task).where(Task.category_id == category_id).values(category_id=None),
        execution_options={'synchronize_session': False},
    )
    db.session.delete(category)
    db.session.commit()
    logger.info('Categoria removida id=%s', category_id)
