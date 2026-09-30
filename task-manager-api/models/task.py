from sqlalchemy.orm import joinedload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, DONE_STATUS
from database import db
from models.base import BaseModel
from utils.helpers import utcnow

SUMMARY_FIELDS = ('id', 'title', 'description', 'status', 'priority', 'created_at', 'due_date')


class Task(BaseModel):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    # Apagar um usuário apaga suas tasks; apagar uma categoria desvincula as tasks (ver Category.delete).
    user = db.relationship('User', backref=db.backref('tasks', cascade='all, delete-orphan'))
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

    def to_summary_dict(self):
        data = self.to_dict()
        summary = {field: data[field] for field in SUMMARY_FIELDS}
        summary['overdue'] = self.is_overdue()
        return summary

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    def touch(self):
        self.updated_at = utcnow()

    @classmethod
    def list_with_relations(cls):
        query = db.select(cls).options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        query = db.select(cls).where(cls.user_id == user_id).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls)
        if text:
            pattern = f'%{text}%'
            query = query.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query.order_by(cls.id)).scalars().all()

    @classmethod
    def list_overdue(cls, now):
        query = (
            db.select(cls)
            .where(cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_STATUSES))
            .order_by(cls.id)
        )
        return db.session.execute(query).scalars().all()

    @classmethod
    def count_by_status(cls):
        rows = db.session.execute(db.select(cls.status, db.func.count()).group_by(cls.status)).all()
        return dict(rows)

    @classmethod
    def count_by_priority(cls):
        rows = db.session.execute(db.select(cls.priority, db.func.count()).group_by(cls.priority)).all()
        return dict(rows)

    @classmethod
    def count_created_since(cls, since):
        return db.session.scalar(db.select(db.func.count()).where(cls.created_at >= since))

    @classmethod
    def count_done_since(cls, since):
        query = db.select(db.func.count()).where(cls.status == DONE_STATUS, cls.updated_at >= since)
        return db.session.scalar(query)
