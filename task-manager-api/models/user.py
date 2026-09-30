from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import ADMIN_ROLE, DEFAULT_ROLE, DONE_STATUS
from database import db
from models.base import BaseModel
from models.task import Task
from utils.helpers import utcnow


class User(BaseModel):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self.role == ADMIN_ROLE

    @classmethod
    def get_by_email(cls, email):
        return db.session.execute(db.select(cls).where(cls.email == email)).scalar_one_or_none()

    @classmethod
    def list_with_task_stats(cls):
        """Lista (usuário, total de tasks, tasks concluídas) com uma única query."""
        completed = db.func.coalesce(db.func.sum(db.case((Task.status == DONE_STATUS, 1), else_=0)), 0)
        query = (
            db.select(cls, db.func.count(Task.id), completed)
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(query).all()
