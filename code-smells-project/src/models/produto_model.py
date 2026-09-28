from src.database.connection import get_db

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


def listar():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row) if row else None


def buscar_por_ids(produto_ids):
    """Retorna {id: produto} para os ids informados, em uma única query."""
    ids = list(set(produto_ids))
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    rows = get_db().execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids).fetchall()
    return {row["id"]: _to_dict(row) for row in rows}


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    clausulas, params = [], []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clausulas.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clausulas.append("preco <= ?")
        params.append(preco_max)
    where = " AND ".join(clausulas) or "1=1"
    rows = get_db().execute(f"SELECT * FROM produtos WHERE {where}", params).fetchall()
    return [_to_dict(row) for row in rows]


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def deletar(produto_id):
    db = get_db()
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def contar():
    return get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
