import logging
import sqlite3

from src.database.connection import get_db, get_readonly_db
from src.errors import ValidationError

logger = logging.getLogger(__name__)


def resetar_banco():
    """Apaga todos os dados numa única transação (filhos antes dos pais)."""
    db = get_db()
    with db:
        db.execute("DELETE FROM itens_pedido")
        db.execute("DELETE FROM pedidos")
        db.execute("DELETE FROM produtos")
        db.execute("DELETE FROM usuarios")


def consultar_somente_leitura(sql):
    """Executa uma única instrução numa conexão aberta em modo somente leitura."""
    conn = get_readonly_db()
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    except sqlite3.Error:
        logger.exception("Consulta administrativa falhou")
        raise ValidationError("Query inválida ou não permitida") from None
    finally:
        conn.close()
