import logging

from src.errors import ForbiddenError, ValidationError
from src.models import admin_model

logger = logging.getLogger(__name__)


def resetar_banco():
    admin_model.resetar_banco()
    logger.warning("Banco de dados resetado")


def executar_consulta(dados, habilitada):
    if not habilitada:
        raise ForbiddenError("Consulta SQL administrativa desabilitada (ENABLE_ADMIN_SQL=false)")
    sql = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("Query não informada")
    if not sql.strip().upper().startswith("SELECT"):
        raise ValidationError("Somente uma instrução SELECT é permitida")
    return admin_model.consultar_somente_leitura(sql)
