from database import db


def commit():
    """Confirma a transação corrente; em falha desfaz tudo e propaga o erro."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


class BaseModel(db.Model):
    __abstract__ = True

    @classmethod
    def get_by_id(cls, obj_id):
        return db.session.get(cls, obj_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(db.func.count()).select_from(cls))

    @classmethod
    def delete_all(cls):
        db.session.execute(db.delete(cls))

    def save(self):
        db.session.add(self)
        commit()
        return self

    def delete(self):
        db.session.delete(self)
        commit()
