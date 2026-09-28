from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_USUARIO_PADRAO
from src.database.connection import get_db

# A senha (hash) nunca sai deste módulo.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def _to_dict(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def criar(nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def autenticar(email, senha):
    """Retorna os dados públicos do usuário se email/senha conferem, senão None."""
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    return _to_dict(row, CAMPOS_LOGIN)


def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
