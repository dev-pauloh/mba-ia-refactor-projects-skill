from sqlalchemy.orm import joinedload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS, DONE_STATUS
from database import db
from utils.helpers import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    # ---- consultas -------------------------------------------------------

    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all(cls, with_relations=False):
        query = db.select(cls).order_by(cls.id)
        if with_relations:
            query = query.options(joinedload(cls.user), joinedload(cls.category))
        return db.session.execute(query).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        query = db.select(cls).where(cls.user_id == user_id).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls).order_by(cls.id)
        if text:
            pattern = f'%{text}%'
            query = query.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    @classmethod
    def count_by(cls, column_name):
        """{valor: quantidade} agrupando por uma coluna (uma única query GROUP BY)."""
        column = getattr(cls, column_name)
        rows = db.session.execute(db.select(column, db.func.count(cls.id)).group_by(column)).all()
        return dict(rows)

    @classmethod
    def count_by_user_and_status(cls):
        """{(user_id, status): quantidade}."""
        rows = db.session.execute(
            db.select(cls.user_id, cls.status, db.func.count(cls.id)).group_by(cls.user_id, cls.status)
        ).all()
        return {(user_id, status): total for user_id, status, total in rows}

    @classmethod
    def count_created_since(cls, since):
        return db.session.execute(
            db.select(db.func.count(cls.id)).where(cls.created_at >= since)
        ).scalar_one()

    @classmethod
    def count_completed_since(cls, since):
        return db.session.execute(
            db.select(db.func.count(cls.id)).where(cls.status == DONE_STATUS, cls.updated_at >= since)
        ).scalar_one()

    @classmethod
    def list_open_with_due_date_before(cls, moment):
        query = (
            db.select(cls)
            .where(cls.due_date.is_not(None), cls.due_date < moment, cls.status.not_in(CLOSED_STATUSES))
            .order_by(cls.id)
        )
        return db.session.execute(query).scalars().all()

    @classmethod
    def delete_by_user(cls, user_id):
        db.session.execute(db.delete(cls).where(cls.user_id == user_id))

    @classmethod
    def detach_category(cls, category_id):
        db.session.execute(db.update(cls).where(cls.category_id == category_id).values(category_id=None))
