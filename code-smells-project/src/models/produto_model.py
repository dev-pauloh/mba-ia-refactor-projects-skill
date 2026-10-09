from src.database.connection import get_db


def produto_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [produto_to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return produto_to_dict(row) if row else None


def buscar_por_ids(produto_ids):
    if not produto_ids:
        return {}
    placeholders = ", ".join("?" for _ in produto_ids)
    rows = get_db().execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", list(produto_ids)).fetchall()
    return {row["id"]: produto_to_dict(row) for row in rows}


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    clauses, params = [], []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)
    where = " AND ".join(clauses) or "1=1"
    rows = get_db().execute(f"SELECT * FROM produtos WHERE {where}", params).fetchall()
    return [produto_to_dict(row) for row in rows]


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


def possui_itens_pedido(produto_id):
    row = get_db().execute("SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)).fetchone()
    return row is not None


def deletar(produto_id):
    db = get_db()
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
