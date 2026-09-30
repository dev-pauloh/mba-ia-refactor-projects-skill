from config.constants import DEFAULT_CATEGORY_COLOR
from database import db
from models.base import BaseModel, commit
from models.task import Task
from utils.helpers import utcnow


class Category(BaseModel):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_CATEGORY_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    def delete(self):
        """Desvincula as tasks da categoria e a remove na mesma transação."""
        db.session.execute(db.update(Task).where(Task.category_id == self.id).values(category_id=None))
        db.session.delete(self)
        commit()

    @classmethod
    def list_with_task_counts(cls):
        query = (
            db.select(cls, db.func.count(Task.id))
            .outerjoin(Task, Task.category_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(query).all()
