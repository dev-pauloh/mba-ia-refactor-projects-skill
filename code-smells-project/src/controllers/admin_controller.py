import logging

from src.errors import ForbiddenError, ValidationError
from src.models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco():
    admin_model.resetar_banco()
    logger.warning("Banco de dados resetado via endpoint administrativo")


def executar_query(dados, sql_habilitado):
    if not sql_habilitado:
        raise ForbiddenError("Execução de SQL administrativo desabilitada (ENABLE_ADMIN_SQL)")
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not isinstance(sql, str) or not sql:
        raise ValidationError("Query não informada")
    logger.warning("SQL administrativo executado")
    return admin_model.executar_sql(sql)
