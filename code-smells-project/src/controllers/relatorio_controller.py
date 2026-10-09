from src.models import relatorio_model
from src.services import relatorio_service


def vendas():
    return relatorio_service.montar_relatorio_vendas(relatorio_model.agregados_vendas())
