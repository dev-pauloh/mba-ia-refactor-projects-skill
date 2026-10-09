from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_CLIENTE
from src.database.connection import get_db


def usuario_to_dict(row):
    """Representação pública do usuário — nunca inclui a senha."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [usuario_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return usuario_to_dict(row) if row else None


def email_existe(email):
    return get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def autenticar(email, senha):
    """Devolve o usuário se e-mail e senha conferem; senão None."""
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    usuario = usuario_to_dict(row)
    usuario.pop("criado_em")  # o login sempre devolveu só id, nome, email e tipo
    return usuario


def criar(nome, email, senha, tipo=TIPO_CLIENTE):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid
