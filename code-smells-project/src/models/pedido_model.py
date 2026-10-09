from collections import defaultdict

from src.config.constants import PRODUTO_NAO_ENCONTRADO_NOME, STATUS_PENDENTE
from src.database.connection import get_db
from src.errors import ValidationError


def listar(usuario_id=None):
    """Pedidos com itens em 2 queries (sem N+1); filtra por usuário quando informado."""
    db = get_db()
    filtro, params = ("WHERE usuario_id = ?", (usuario_id,)) if usuario_id is not None else ("", ())
    pedidos = db.execute(f"SELECT * FROM pedidos {filtro}", params).fetchall()
    itens = db.execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
               COALESCE(p.nome, ?) AS produto_nome
        FROM itens_pedido i
        LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN (SELECT id FROM pedidos {filtro})
        ORDER BY i.id
        """,
        (PRODUTO_NAO_ENCONTRADO_NOME, *params),
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
        {
            "id": pedido["id"],
            "usuario_id": pedido["usuario_id"],
            "status": pedido["status"],
            "total": pedido["total"],
            "criado_em": pedido["criado_em"],
            "itens": itens_por_pedido[pedido["id"]],
        }
        for pedido in pedidos
    ]


def existe(pedido_id):
    return get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def criar(usuario_id, itens, total):
    """Grava pedido, itens e débito de estoque numa única transação.

    `itens` traz produto_id, nome, quantidade e preco_unitario. O débito é condicional
    (estoque >= quantidade); se algum produto não tiver estoque, tudo é desfeito.
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
            debitado = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if debitado == 0:
                raise ValidationError("Estoque insuficiente para " + item["nome"])
    return pedido_id


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
