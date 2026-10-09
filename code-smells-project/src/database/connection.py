import logging
import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash

from src.config.constants import TIPO_ADMIN, TIPO_CLIENTE

logger = logging.getLogger(__name__)

HASH_PREFIXES = ("scrypt:", "pbkdf2:")

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER REFERENCES usuarios(id),
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER REFERENCES pedidos(id),
        produto_id INTEGER REFERENCES produtos(id),
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

SEED_PRODUTOS = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

# Usuários de demonstração; as senhas são gravadas apenas como hash.
SEED_USUARIOS = (
    ("Admin", "admin@loja.com", "admin123", TIPO_ADMIN),
    ("João Silva", "joao@email.com", "123456", TIPO_CLIENTE),
    ("Maria Santos", "maria@email.com", "senha123", TIPO_CLIENTE),
)


def _connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """Conexão da requisição atual, aberta sob demanda e fechada no teardown."""
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE_PATH"])
    return g.db


def get_readonly_db():
    """Conexão somente leitura, usada pela consulta administrativa."""
    uri = Path(current_app.config["DATABASE_PATH"]).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def _create_schema(conn):
    for statement in SCHEMA:
        conn.execute(statement)
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)")
    except sqlite3.IntegrityError:
        logger.warning("Há e-mails duplicados em usuarios; índice UNIQUE não criado")


def _seed_if_empty(conn):
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        SEED_PRODUTOS,
    )
    conn.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in SEED_USUARIOS],
    )


def _hash_plaintext_passwords(conn):
    rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    legado = [row for row in rows if row["senha"] and not row["senha"].startswith(HASH_PREFIXES)]
    for row in legado:
        conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(row["senha"]), row["id"]))
    if legado:
        logger.info("%d senha(s) em texto puro convertida(s) para hash", len(legado))


def init_db(app):
    app.teardown_appcontext(close_db)
    conn = _connect(app.config["DATABASE_PATH"])
    try:
        with conn:
            _create_schema(conn)
            _seed_if_empty(conn)
            _hash_plaintext_passwords(conn)
    finally:
        conn.close()
