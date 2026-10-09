import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


def init_db(app):
    import models  # noqa: F401  registra as tabelas antes do create_all

    db.init_app(app)
    with app.app_context():
        event.listen(db.engine, 'connect', _enable_sqlite_foreign_keys)
        db.create_all()
