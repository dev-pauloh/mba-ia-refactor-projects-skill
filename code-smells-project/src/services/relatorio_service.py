"""Regras de domínio do relatório de vendas."""
from src.config.constants import FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0


def montar_relatorio_vendas(agregados):
    total_pedidos = agregados["total_pedidos"]
    faturamento = agregados["faturamento"]
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": agregados["pendentes"],
        "pedidos_aprovados": agregados["aprovados"],
        "pedidos_cancelados": agregados["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
