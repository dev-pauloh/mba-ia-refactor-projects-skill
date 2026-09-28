from collections import defaultdict

from src.config.constants import STATUS_PENDENTE
from src.database.connection import get_db
from src.errors import ValidationError

CAMPOS = ("id", "usuario_id", "status", "total", "criado_em")


def _listar(where="", params=()):
    """Pedidos com seus itens em 2 queries (sem N+1)."""
    db = get_db()
    pedidos = db.execute(f"SELECT * FROM pedidos {where}", params).fetchall()
    if not pedidos:
        return []
    ids = [pedido["id"] for pedido in pedidos]
    placeholders = ",".join("?" * len(ids))
    itens = db.execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
               COALESCE(p.nome, 'Desconhecido') AS produto_nome
        FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN ({placeholders})
        ORDER BY i.id
        """,
        ids,
    ).fetchall()
    itens_por_pedido = defaultdict(list)
    for item in itens:
        itens_por_pedido[item["pedido_id"]].append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"],
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })
    return [
        {**{campo: pedido[campo] for campo in CAMPOS}, "itens": itens_por_pedido[pedido["id"]]}
        for pedido in pedidos
    ]


def listar_todos():
    return _listar()


def listar_por_usuario(usuario_id):
    return _listar("WHERE usuario_id = ?", (usuario_id,))


def buscar_por_id(pedido_id):
    row = get_db().execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return {campo: row[campo] for campo in CAMPOS} if row else None


def criar(usuario_id, itens, total):
    """Grava pedido, itens e baixa de estoque numa única transação.

    `itens`: lista de dicts com produto_id, quantidade, preco_unitario e nome.
    """
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        )
        pedido_id = cursor.lastrowid
        for item in itens:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            baixados = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if baixados == 0:
                raise ValidationError("Estoque insuficiente para " + item["nome"], com_sucesso=True)
    return pedido_id


def atualizar_status(pedido_id, novo_status, devolver_estoque=False):
    db = get_db()
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        if devolver_estoque:
            db.execute(
                """
                UPDATE produtos SET estoque = estoque + (
                    SELECT SUM(i.quantidade) FROM itens_pedido i
                    WHERE i.pedido_id = ? AND i.produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
