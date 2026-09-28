from src.config.constants import FAIXAS_DESCONTO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from src.models import relatorio_model


def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0


def vendas():
    resumo = relatorio_model.resumo_pedidos()
    total_pedidos = resumo["total_pedidos"]
    faturamento = resumo["faturamento"]
    por_status = resumo["por_status"]
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get(STATUS_PENDENTE, 0),
        "pedidos_aprovados": por_status.get(STATUS_APROVADO, 0),
        "pedidos_cancelados": por_status.get(STATUS_CANCELADO, 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
