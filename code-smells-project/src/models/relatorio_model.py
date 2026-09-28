from src.database.connection import get_db


def resumo_pedidos():
    """Total de pedidos, faturamento e contagem por status em uma única query."""
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS quantidade, COALESCE(SUM(total), 0) AS faturamento FROM pedidos GROUP BY status"
    ).fetchall()
    por_status = {row["status"]: row["quantidade"] for row in rows}
    return {
        "total_pedidos": sum(por_status.values()),
        "faturamento": sum(row["faturamento"] for row in rows),
        "por_status": por_status,
    }
