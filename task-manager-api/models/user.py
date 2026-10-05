from werkzeug.security import check_password_hash, generate_password_hash

from config.constants import ADMIN_ROLE, DEFAULT_ROLE
from database import db
from utils.helpers import utcnow


class User(db.Model):
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

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == ADMIN_ROLE

    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).where(cls.email == email)).scalar_one_or_none()

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()
