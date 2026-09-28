from src.database.connection import get_db

TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


def resetar_banco():
    db = get_db()
    with db:
        for tabela in TABELAS_RESET:
            db.execute(f"DELETE FROM {tabela}")


def executar_sql(sql):
    """Executa SQL administrativo; retorna linhas para SELECT, None para escrita."""
    db = get_db()
    with db:
        cursor = db.execute(sql)
        if sql.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()]
    return None
